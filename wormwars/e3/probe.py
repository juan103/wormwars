"""E3a's probe and component tests (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §6).

The probe works open loop on the carrier, from a copy of the state under test, with q, RA and RB held
at their saved values (`Brain.clamp`). Both modules' noses get m; the probed module's left nose
m + d/2 and its right nose m − d/2. After 50 ticks, u is averaged over 10 more, and
K_D = (u(+d) − u(−d)) / (2d), signed so that a module steering toward its source has K_D > 0.

"Module" means a module's nose pair; its outputs, for the offset test, are its comparators' 16
output edges (for B-shared, the pair's 4 nose-to-comparator edges).
"""

from __future__ import annotations

import torch

from ..brain import Brain, BrainSpec, Genome
from ..e4s import comparator as C
from . import organism as O

LEVELS = (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35)
D = 1e-3
PRE, AVG = 50, 10
ACTIVE_MIN, INACTIVE_MAX, OFFSET_MAX = 30.0, 0.3, 0.02
STIMULUS = 3.0  # the relays' interface gain times a level of 1


class ProbeContext:
    def __init__(self, ext, iface, cfg, pairs: dict | None = None, outputs: dict | None = None, device="cpu"):
        self.ext, self.iface, self.cfg, self.device = ext, iface, cfg, device
        names = set(ext.names)
        if pairs is None:
            if "E3_A_NL" in names:
                pairs = {"A": ("E3_A_NL", "E3_A_NR"), "B": ("E3_B_NL", "E3_B_NR")}
            else:
                pairs = {"A": ("E3_S_AL", "E3_S_AR"), "B": ("E3_S_BL", "E3_S_BR")}
        self.pairs = {k: (ext.index(a), ext.index(b)) for k, (a, b) in pairs.items()}
        spec = BrainSpec.from_connectome(ext)
        pos = {(int(a), int(b)): p for p, (a, b) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist()))}
        n0 = int(ext.meta["worm_neurons"])
        if outputs is None:
            outputs = {}
            for k, (a, b) in pairs.items():
                if a.startswith("E3_S_"):  # B-shared: the pair's nose-to-comparator edges
                    outputs[k] = [pos[(ext.index(x), ext.index(c))] for x in (a, b) for c in ("E3_S_CL", "E3_S_CR")]
                else:  # E: the module's comparators' edges onto the worm
                    comps = [ext.index(a.replace("_NL", "_CL")), ext.index(a.replace("_NL", "_CR"))]
                    outputs[k] = [p for (i, j), p in pos.items() if i in comps and j < n0]
        self.outputs = outputs
        self.q, self.ra, self.rb = ext.index(O.Q), ext.index("E3_RA"), ext.index("E3_RB")
        self.n = ext.n

    def latch_state(self, genome: Genome, q, ra: float = 0.0, rb: float = 0.0) -> torch.Tensor:
        v = torch.zeros(genome.n_strains, 1, self.n, device=self.device)
        v[:, 0, self.q] = torch.as_tensor(q, dtype=v.dtype, device=self.device)
        v[:, 0, self.ra], v[:, 0, self.rb] = ra, rb
        return v

    def noses(self, S: int, m: float, key: str | None = None, d: float = 0.0) -> torch.Tensor:
        cur = torch.zeros(S, 1, self.n, device=self.device)
        for i, j in self.pairs.values():
            cur[..., i] = cur[..., j] = m
        if key is not None:
            i, j = self.pairs[key]
            cur[..., i], cur[..., j] = m + d / 2, m - d / 2
        return cur

    def turn(self, v: torch.Tensor) -> torch.Tensor:
        _, u = C.motor_commands(v.cpu(), self.iface, self.cfg)
        return u.reshape(-1)


def _held(pc: ProbeContext, state: torch.Tensor) -> list[dict]:
    return [{pc.q: float(state[s, 0, pc.q]), pc.ra: float(state[s, 0, pc.ra]), pc.rb: float(state[s, 0, pc.rb])}
            for s in range(state.shape[0])]


def _run(genome, pc, state, cur):
    brain = Brain(genome)
    brain.clamp(_held(pc, state))
    v, us = state.clone(), []
    for t in range(PRE + AVG):
        v = brain.step(v, cur)
        if t >= PRE:
            us.append(pc.turn(v))
    return torch.stack(us).mean(0), v


def k_d(genome: Genome, pc: ProbeContext, key: str, m: float, state: torch.Tensor, d: float = D,
        return_final: bool = False):
    S = genome.n_strains
    up, final = _run(genome, pc, state, pc.noses(S, m, key, d))
    down, _ = _run(genome, pc, state, pc.noses(S, m, key, -d))
    k = (up - down) / (2 * d)
    return (k, final) if return_final else k


def u_at(genome: Genome, pc: ProbeContext, m: float, state: torch.Tensor) -> torch.Tensor:
    u, _ = _run(genome, pc, state, pc.noses(genome.n_strains, m))
    return u


def without_outputs(genome: Genome, pc: ProbeContext, key: str) -> Genome:
    w = genome.w.clone()
    w[:, pc.outputs[key]] = 0.0
    return genome.with_params(w=w)


def offset_passes(u_with: float, u_without: float) -> bool:
    return abs(float(u_with) - float(u_without)) < OFFSET_MAX


def _free_run(genome, pc, state, ticks, relay: int | None, stim_ticks: int, m: float = 0.05):
    """The organism unclamped, noses at m, a level of `STIMULUS` into `relay` for `stim_ticks` ticks;
    the state after every tick."""
    brain = Brain(genome)
    v, out = state.clone(), []
    for t in range(ticks):
        cur = pc.noses(genome.n_strains, m)
        if relay is not None and t < stim_ticks:
            cur[..., relay] = STIMULUS
        v = brain.step(v, cur)
        out.append(v.clone())
    return out


def component_tests(genome: Genome, pc: ProbeContext, states: dict, levels=LEVELS, stim_ticks: int = 2) -> dict:
    """The registered component tests for a one-strain organism; `states` maps each goal ("A", "B")
    to its stable q."""
    other = {"A": "B", "B": "A"}
    relay_for = {"A": pc.rb, "B": pc.ra}  # the level of the other source sets a goal
    act, inact, off = {}, {}, {}
    for goal, q in states.items():
        st = pc.latch_state(genome, q)
        for m in levels:
            act[(goal, m)] = float(k_d(genome, pc, goal, m, st))
            inact[(goal, m)] = float(k_d(genome, pc, other[goal], m, st))
            off[(goal, m)] = (float(u_at(genome, pc, m, st)), float(u_at(without_outputs(genome, pc, other[goal]), pc, m, st)))
    switching = {}
    for goal, q in states.items():
        settled = float(k_d(genome, pc, goal, 0.05, pc.latch_state(genome, q)))
        start = pc.latch_state(genome, states[other[goal]])
        snaps = _free_run(genome, pc, start, stim_ticks + 10, relay_for[goal], stim_ticks)
        ks = [float(k_d(genome, pc, goal, 0.05, s)) for s in snaps[stim_ticks:]]
        switching[goal] = {"settled": settled, "after_level": ks, "passed": any(k >= 0.9 * settled for k in ks)}
    cue = _free_run(genome, pc, torch.zeros(1, 1, pc.n, device=pc.device), 16, pc.rb, 5)
    startup = {t: float(k_d(genome, pc, "A", 0.05, cue[t])) for t in range(5, 16)}
    res = {
        "active": {"values": {f"{g}@{m}": v for (g, m), v in act.items()}, "passed": all(v >= ACTIVE_MIN for v in act.values())},
        "inactive": {"values": {f"{g}@{m}": v for (g, m), v in inact.items()},
                     "passed": all(abs(v) <= INACTIVE_MAX for v in inact.values())},
        "offset": {"values": {f"{g}@{m}": v for (g, m), v in off.items()},
                   "passed": all(offset_passes(a, b) for a, b in off.values())},
        "switching": {"values": switching, "passed": all(s["passed"] for s in switching.values())},
        "startup": {"values": startup, "passed": all(startup[t] >= ACTIVE_MIN for t in range(10, 16))},
    }
    res["passed"] = all(r["passed"] for r in res.values())
    return res
