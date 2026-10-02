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
            # W starts at the stimulus's last tick: stim + W - 1 ticks in all
            q_end = float(_after(genome, pc, asg[other[goal]], goal, stim, W - 1)[0, 0, pc.q])
            settable[goal] = {"q": q_end, "passed": abs(q_end - asg[goal]) <= TOL * sep}
        hold = {}
        for goal in ("A", "B"):
            ref_k, _ = _gate(genome, pc, goal, _settle_state(genome, pc, asg[goal]))
            end = _after(genome, pc, asg[goal], goal, stim, W - 1 + HOLD_TICKS)
            q_end = float(end[0, 0, pc.q])
            k_x, k_o = _gate(genome, pc, goal, end)
            hold[goal] = {"q": q_end, "K_D": k_x, "other": k_o, "K_D_at_fixed_point": ref_k,
                          "passed": (abs(q_end - asg[goal]) <= TOL * sep and k_x >= K_FLOOR
                                     and k_x >= HOLD_KEEP * ref_k and abs(k_o) <= RATIO * k_x)}
        res.update(states=asg, settable_detail=settable, hold_detail=hold,
                   settable=all(s["passed"] for s in settable.values()), hold=all(h["passed"] for h in hold.values()))
        res["class"] = "latch" if res["settable"] and res["hold"] else "bistable, not a latch"
        # descriptive for every bistable q, from each stable equilibrium
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


# ------------------------------------------------------------------ calibration (stage 5 and 13)

def stimulus_from(durations, fallback: int = 2) -> int:
    """The median level duration at confirmed visits, rounded half up, at least 1; the fallback if the
    pool is empty."""
    d = [int(x) for x in durations]
    if not d:
        return int(fallback)
    return max(1, int(math.floor(float(np.median(d)) + 0.5)))


def calibrate(genome, ext, iface, cfg, *, world_ids, run_seed: int, device="cpu") -> list[dict]:
    """Every strain of `genome` on the calibration worlds, together (32 strains x 256 worlds is the
    registered composition): per strain, its median q in each goal phase (None where the phase never
    occurs), its pooled level durations at confirmed visits (censored ones excluded), the stimulus they
    give, and its leg durations after the first confirmed visit."""
    ids = np.asarray(world_ids)
    n, S = len(ids), genome.n_strains
    strain_of = torch.arange(S, device=device).repeat_interleave(n).reshape(-1, 1)
    world = World(cfg, iface, Brain(genome), strain_of, run_seed=run_seed, world_ids=np.tile(ids, S), device=device)
    q = ext.index("E3_Q")
    a = world.assigns[0]
    flat = lambda v: v.reshape(a.n_strains * a.n_slots, -1)[a.slot_of]  # noqa: E731  [worlds, N]
    qs, goals = [], []
    for _ in range(int(cfg.world.max_ticks)):
        goals.append(world.shuttle_goal.clone().cpu())
        world.tick()
        qs.append(flat(world.v[0])[:, q].clone().cpu())
    qs, goals = torch.stack(qs).numpy(), torch.stack(goals).numpy()  # [ticks, S * n]
    ev = world.shuttle_events()
    out = []
    for s in range(S):
        cols = slice(s * n, (s + 1) * n)
        med = {}
        for name, g in (("A", 0), ("B", 1)):
            sel = qs[:, cols][goals[:, cols] == g]
            med[name] = float(np.median(sel)) if sel.size else None
        pool = [int(x) for x in ev["visit_level_ticks"][cols].reshape(-1) if x >= 0]
        legs = []
        for w in range(s * n, (s + 1) * n):
            v = [int(t) for t in ev["visit_tick"][w] if t >= 0]
            legs += [b - a_ for a_, b in zip(v[:-1], v[1:])]
        out.append({"median_q": med, "pool": len(pool), "stimulus": stimulus_from(pool), "durations": pool,
                    "legs_after_first_visit": legs, "visits": int(world.shuttle_visits[cols].sum())})
    return out


def hysteresis(genome, pc: P.ProbeContext, *, w_qq: float, b_q: float, ramp: int = 200) -> dict:
    """Descriptive (§6): from the "go to B" side (the lower stable state if bistable, else the release
    start), the A stimulus (RB) ramped 0 -> 3 over `ramp` ticks and back, then the B stimulus (RA)
    likewise; q at the end of each, and the drive at which q first crossed 0 on each up-ramp."""
    st = L.structure(w_qq, b_q)
    q0 = st.states[0] if st.kind == "bistable" else L.release_start(w_qq, b_q)
    brain = __import__("wormwars.brain", fromlist=["Brain"]).Brain(genome)
    v = pc.latch_state(genome, q0)
    out = {}
    for name, relay, sign in (("a", pc.rb, 1.0), ("b", pc.ra, -1.0)):
        crossing = None
        for t in range(2 * ramp):
            drive = P.STIMULUS * (t / (ramp - 1) if t < ramp else (2 * ramp - 1 - t) / (ramp - 1))
            cur = pc.noses(genome.n_strains, 0.05)
            cur[..., relay] = drive
            v = brain.step(v, cur)
            if crossing is None and t < ramp and sign * float(v[0, 0, pc.q]) > 0:
                crossing = drive
        out[f"q_after_{name}_ramp"] = float(v[0, 0, pc.q])
        out[f"{name}_crossing_drive"] = crossing
    return out


def leg_median(legs) -> int:
    """D: the median completed leg after the first confirmed visit, rounded half up."""
    if not legs:
        raise ValueError("no completed leg after a first confirmed visit: D is undefined")
    return int(math.floor(float(np.median(legs)) + 0.5))


def _contribution_weights(genome, ext, prefix: str) -> torch.Tensor:
    """[S, N]: for each neuron, its summed signed weight onto the 4 dorsal minus the 4 ventral turn
    neurons, nonzero only for the given module's comparators (E3_<prefix>_CL and _CR)."""
    from ..brain import BrainSpec
    from ..e4s import comparator as C
    spec = BrainSpec.from_connectome(ext)
    comps = {ext.index(f"E3_{prefix}_CL"), ext.index(f"E3_{prefix}_CR")}
    dors = {ext.index(n) for n in C.TURN_DORSAL}
    vent = {ext.index(n) for n in C.TURN_VENTRAL}
    w = torch.zeros(genome.n_strains, ext.n, device=genome.w.device)
    for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())):
        if i in comps and (j in dors or j in vent):
            w[:, i] += genome.w[:, p] * (1.0 if j in dors else -1.0)
    return w


def traces(genome, ext, iface, cfg, *, world_ids, run_seed: int, ticks: int | None = None, device="cpu") -> dict:
    """The per-tick logs (§3), float32 [strains, worlds, ticks]: q, RA, RB, the turn command u, and
    each module's turn contribution (its comparators' summed signed input current into the dorsal
    minus the ventral turn neurons, before their nonlinearity)."""
    from ..e4s import comparator as C
    ids = np.asarray(world_ids)
    n, S = len(ids), genome.n_strains
    T = int(ticks or cfg.world.max_ticks)
    strain_of = torch.arange(S, device=device).repeat_interleave(n).reshape(-1, 1)
    world = World(cfg, iface, Brain(genome), strain_of, run_seed=run_seed, world_ids=np.tile(ids, S), device=device)
    a = world.assigns[0]
    flat = lambda v: v.reshape(a.n_strains * a.n_slots, -1)[a.slot_of]  # noqa: E731
    idx = {k: ext.index(nm) for k, nm in (("q", "E3_Q"), ("ra", "E3_RA"), ("rb", "E3_RB"))}
    wa = _contribution_weights(genome, ext, "A").repeat_interleave(n, dim=0)
    wb = _contribution_weights(genome, ext, "B").repeat_interleave(n, dim=0)
    out = {k: np.zeros((S * n, T), dtype=np.float32) for k in ("q", "ra", "rb", "u", "contribution_A", "contribution_B")}
    for t in range(T):
        world.tick()
        v = flat(world.v[0])
        act = torch.tanh(v)
        for k, i in idx.items():
            out[k][:, t] = v[:, i].float().cpu().numpy()
        _, u = C.motor_commands(v.cpu(), iface, cfg)
        out["u"][:, t] = u.reshape(-1).numpy()
        out["contribution_A"][:, t] = (act * wa).sum(-1).float().cpu().numpy()
        out["contribution_B"][:, t] = (act * wb).sum(-1).float().cpu().numpy()
    return {k: v.reshape(S, n, T) for k, v in out.items()}
