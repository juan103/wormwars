"""E3a's memory assays and classes (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §6).

Open loop (q, RA and RB form an autonomous subsystem once the levels are 0):
- settable: from each stable state, the stimulus for the other goal leaves q within 10% of the
  separation of the other state at the end of the window W = max(20, ⌈10·τ_q⌉);
- the hold: its own goal's stimulus, W, then 580 ticks with no levels; q within 10% of its fixed point,
  the active module's K_D at least 15 and 0.8 of its value at the fixed point, the inactive |K_D| at
  most 0.1 of the active;
- the release test: from q's equilibrium, the stimulus for goal X, D ticks with no levels; X's module
  K_D at least 15 and the other's |K_D| at most 0.1 of it, for both goals.

In the world:
- the clamp assays (q clamped to each state; the first entry into its goal in at least 90% of the
  worlds), with the state-to-goal assignment;
- the reset (a one-time write of q to "go to A", 10 ticks after `at_a` returns to 0 following the first
  confirmed visit).

The stimulus for goal X is the level of the other source (`at_b` → RB for A, `at_a` → RA for B).
"""

from __future__ import annotations

import math

import numpy as np
import torch

from ..brain import Brain
from ..evo.rollout import rollout_brain
from ..world import World
from . import latch as L
from . import probe as P

HOLD_TICKS = 580
TOL = 0.1
K_FLOOR = 15.0
RATIO = 0.1
HOLD_KEEP = 0.8
CLAMP_SHARE = 0.9
RESET_SHARE = 0.7
RESET_DELAY = 10
RESET_ELIGIBLE_BY = 500
WORKING = 0.8


def window(tau_q: float) -> int:
    return max(20, int(math.ceil(10.0 * float(tau_q) - 1e-12)))


def _relay(pc: P.ProbeContext, goal: str) -> int:
    return pc.rb if goal == "A" else pc.ra


def _settle_state(genome, pc, q):
    return pc.latch_state(genome, q)


def _after(genome, pc, q0, goal, stim, ticks):
    """The state after `stim` ticks of goal's stimulus then `ticks` with no levels, from q = q0."""
    snaps = P._free_run(genome, pc, _settle_state(genome, pc, q0), stim + ticks, _relay(pc, goal), stim)
    return snaps[-1]


def _gate(genome, pc, goal, state):
    other = "B" if goal == "A" else "A"
    return float(P.k_d(genome, pc, goal, 0.05, state)), float(P.k_d(genome, pc, other, 0.05, state))


def _release(genome, pc, start, stim, D):
    out = {}
    for goal in ("A", "B"):
        st = _after(genome, pc, start, goal, stim, D)
        k_x, k_o = _gate(genome, pc, goal, st)
        out[goal] = {"K_D": k_x, "other": k_o, "passed": k_x >= K_FLOOR and abs(k_o) <= RATIO * k_x}
    return out


def memory_assays(genome, pc: P.ProbeContext, *, w_qq: float, b_q: float, tau_q: float, stim: int, D: int,
                  assignment: dict | None) -> dict:
    """One strain's structure, assays and memory class. `assignment` maps "A" and "B" to its two
    stable states; None gives the higher state to A (E's convention)."""
    st = L.structure(w_qq, b_q)
    W = window(tau_q)
    res = {"structure": st.kind, "window": W, "stimulus": stim}
    if st.kind == "bistable":
        lo, hi = st.states
        sep = hi - lo
        asg = assignment or {"A": hi, "B": lo}
        other = {"A": "B", "B": "A"}
        settable = {}
        for goal in ("A", "B"):
            q_end = float(_after(genome, pc, asg[other[goal]], goal, stim, W)[0, 0, pc.q])
            settable[goal] = {"q": q_end, "passed": abs(q_end - asg[goal]) <= TOL * sep}
        hold = {}
        for goal in ("A", "B"):
            ref_k, _ = _gate(genome, pc, goal, _settle_state(genome, pc, asg[goal]))
            end = _after(genome, pc, asg[goal], goal, stim, W + HOLD_TICKS)
            q_end = float(end[0, 0, pc.q])
            k_x, k_o = _gate(genome, pc, goal, end)
            hold[goal] = {"q": q_end, "K_D": k_x, "other": k_o, "K_D_at_fixed_point": ref_k,
                          "passed": (abs(q_end - asg[goal]) <= TOL * sep and k_x >= K_FLOOR
                                     and k_x >= HOLD_KEEP * ref_k and abs(k_o) <= RATIO * k_x)}
        res.update(states=asg, settable_detail=settable, hold_detail=hold,
                   settable=all(s["passed"] for s in settable.values()), hold=all(h["passed"] for h in hold.values()))
        res["class"] = "latch" if res["settable"] and res["hold"] else "bistable, not a latch"
        if res["class"] != "latch":  # descriptive, from each stable equilibrium
            res["release_detail"] = {f"from {y}": _release(genome, pc, asg[y], stim, D) for y in ("A", "B")}
            res["release"] = all(v["passed"] for d in res["release_detail"].values() for v in d.values())
    else:
        start = L.release_start(w_qq, b_q)
        detail = _release(genome, pc, start, stim, D)
        res.update(start=start, release_detail=detail, release=all(v["passed"] for v in detail.values()))
        res["class"] = "slow trace" if res["release"] else "no memory"
    return res


# ------------------------------------------------------------------ in the world

def _first_entries(events) -> np.ndarray:
    """Per world: "A", "B" or "" for the first entry of the episode."""
    a, b = events["entry_a"][0, :, 0], events["entry_b"][0, :, 0]
    out = np.full(a.shape, "", dtype=object)
    out[(a >= 0) & ((b < 0) | (a < b))] = "A"
    out[(b >= 0) & ((a < 0) | (b < a))] = "B"
    return out


def assign(states: tuple, shares: dict) -> tuple[dict, bool]:
    """The one-to-one assignment of two states to A and B under which both clamp assays pass; if none,
    the larger summed first-entry share, ties giving the higher state to A."""
    lo, hi = sorted(states)
    cands = [{"A": hi, "B": lo}, {"A": lo, "B": hi}]
    passing = [c for c in cands if shares[(c["A"], "A")] >= CLAMP_SHARE and shares[(c["B"], "B")] >= CLAMP_SHARE]
    if passing:
        return passing[0], True
    s = [shares[(c["A"], "A")] + shares[(c["B"], "B")] for c in cands]
    return (cands[1] if s[1] > s[0] else cands[0]), False


def clamp_assays(genome, ext, iface, cfg, *, states: tuple, world_ids, run_seed: int, device="cpu",
                 applicable: bool = True) -> dict:
    if not applicable or abs(states[1] - states[0]) < TOL:
        return {"applicable": False, "passed": False}
    q = ext.index("E3_Q")
    shares, firsts = {}, {}
    for s in states:
        brain = Brain(genome.select([0]))
        brain.clamp([{q: float(s)}])
        r = rollout_brain(cfg, iface, brain, np.asarray(world_ids), run_seed, device=device)
        f = _first_entries(r.events)
        firsts[float(s)] = f.tolist()
        for goal in ("A", "B"):
            shares[(s, goal)] = float(np.mean(f == goal))
    asg, ok = assign(states, shares)
    return {"applicable": True, "assignment": asg, "passed": ok,
            "share": {"A": shares[(asg["A"], "A")], "B": shares[(asg["B"], "B")]},
            "first_entries": firsts}


def working(*, lower_bound: float, e_mean: float, clamp: dict) -> bool:
    return bool(clamp.get("applicable") and clamp.get("passed") and lower_bound >= WORKING * e_mean)


def reset_test(genome, ext, iface, cfg, *, go_to_a: float, world_ids, run_seed: int, device="cpu") -> dict:
    """The reset (G1): a one-time write of q to `go_to_a`, 10 ticks after `at_a` returns to 0 following
    the first confirmed visit. A world whose write never happens stays in the denominator and fails."""
    ids = np.asarray(world_ids)
    n = len(ids)
    brain = Brain(genome.select([0]))
    world = World(cfg, iface, brain, torch.zeros(n, 1, dtype=torch.long, device=device), run_seed=run_seed,
                  world_ids=ids, device=device)
    q = ext.index("E3_Q")
    rows = world.assigns[0].slot_of.reshape(-1).tolist()
    T = int(cfg.world.max_ticks)
    tv = [-1] * n  # first confirmed visit
    te = [-1] * n  # first tick after it with the head outside A
    tw = [-1] * n  # the write
    for t in range(T):
        for w in range(n):
            if te[w] >= 0 and tw[w] < 0 and t == te[w] + 1 + RESET_DELAY:
                world.v[0][0, rows[w], q] = go_to_a
                tw[w] = t
        world.tick()
        visit = world._sh_visit_log[:, t].tolist()
        inside_a = world._sh_inside_log[:, t, 0].tolist()
        for w in range(n):
            if tv[w] < 0 and visit[w]:
                tv[w] = t
            elif tv[w] >= 0 and te[w] < 0 and not inside_a[w]:
                te[w] = t
    ev = world.shuttle_events()
    labels = []
    for w in range(n):
        if tv[w] < 0 or tv[w] > RESET_ELIGIBLE_BY:
            labels.append("not eligible")
            continue
        if tw[w] < 0:
            labels.append("unwritten")
            continue
        ea = [x for x in ev["entry_a"][w] if x >= tw[w]]
        eb = [x for x in ev["entry_b"][w] if x >= tw[w]]
        first_a = ea[0] if ea else None
        ok = first_a is not None and (not eb or first_a < eb[0])
        ok = ok and any(v > first_a for v in ev["visit_tick"][w] if v >= 0)
        labels.append("passed" if ok else "failed")
    eligible = sum(lab != "not eligible" for lab in labels)
    passed_n = labels.count("passed")
    return {"eligible": eligible, "passed_worlds": passed_n, "per_world": labels,
            "passed": eligible > 0 and passed_n >= RESET_SHARE * eligible}
