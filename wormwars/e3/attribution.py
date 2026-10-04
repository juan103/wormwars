"""E3b-2: where E3b-1's gain comes from (docs/E3/E3b-2-PLAN.md draft 2).

- `parameter_groups`: the two partitions of E3b-1's 65 mutable scalars (§4), as boolean masks over the
  genome's chemical edges, τ and biases. They are parameter groups defined from the seed's design, not
  isolated functions.
- `hybrid`: a genome taking each group's values from the champion or the seed (§5A).
- `shapley`, `dividends`, `rebuild`, `reversion`, `transplant`: exact attribution over a full table of
  coalition values (§5A). The allocations are exact for this baseline, partition and table, and they are
  signed.
- `EDGE_LESIONS`, `edge_lesion`, `latch_states`, `reflex_clamp`, `without_scent`, `HeldBrain`: §5C's lesions.
  `HeldBrain` starts each clamped neuron at its clamp value, so a clamp holds from the first tick.
- `SwitchTally`, `LatchRecorder`: §5D's in-maze latch reading, on the goal in force when q was computed.
"""

from __future__ import annotations

import dataclasses
import itertools
import math

import numpy as np
import torch

from ..brain import Brain, BrainSpec, Genome
from . import latch as L
from . import maze_organisms as MO
from . import organism as O
from . import tuning as T

FUNCTIONAL = ("sensing", "gating", "output", "latch")
SIDE = ("module_a", "module_b", "selector")
NOSES = ("E3_A_NL", "E3_A_NR", "E3_B_NL", "E3_B_NR")
SCENT = ("a_left", "a_right", "b_left", "b_right")
REFLEX_REST = -0.5  # W2's neurons have no chemical or gap inputs and a bias of −0.5 (D194)


def _side(name: str) -> str:
    return "module_a" if name.startswith("E3_A_") else "module_b"


def parameter_groups(ext, partition: str) -> dict:
    """{group: {"w": [n_chem], "tau": [n], "bias": [n]} boolean masks} over the mutable scalars only."""
    if partition not in ("functional", "side"):
        raise ValueError("the partitions are 'functional' and 'side'")
    spec = BrainSpec.from_connectome(ext)
    sc = T.scales(ext)
    names = ext.names
    keys = FUNCTIONAL if partition == "functional" else SIDE
    out = {k: {"w": torch.zeros(spec.n_chem if hasattr(spec, "n_chem") else len(spec.chem_i), dtype=torch.bool),
               "tau": torch.zeros(spec.n, dtype=torch.bool), "bias": torch.zeros(spec.n, dtype=torch.bool)}
           for k in keys}
    comps, relays = set(O.COMPARATORS), set(O.RELAYS)
    for p, (i, j) in enumerate(zip(spec.chem_i.tolist(), spec.chem_j.tolist())):
        if not float(sc["w"][p]) > 0:
            continue
        a, b = names[i], names[j]
        if a in NOSES and b in comps:
            g = "sensing" if partition == "functional" else _side(a)
        elif a in comps:
            g = "output" if partition == "functional" else _side(a)
        elif a == O.Q and b in comps:
            g = "gating" if partition == "functional" else "selector"
        elif b == O.Q and (a == O.Q or a in relays):
            g = "latch" if partition == "functional" else "selector"
        else:
            raise AssertionError(f"an unclassified mutable edge {a} → {b}")
        out[g]["w"][p] = True
    for k in range(spec.n):
        n = names[k]
        for kind in ("tau", "bias"):
            if not float(sc[kind][k]) > 0:
                continue
            if n == O.Q:
                g = "latch" if partition == "functional" else "selector"
            elif n in NOSES:
                g = "sensing" if partition == "functional" else _side(n)
            elif n in comps:
                g = ("sensing" if kind == "tau" else "gating") if partition == "functional" else _side(n)
            else:
                raise AssertionError(f"an unclassified mutable {kind} of {n}")
            out[g][kind][k] = True
    return out


def hybrid(seed: Genome, champion: Genome, groups: dict, take: set) -> Genome:
    """One strain: the seed's values everywhere, except the groups in `take`, which take the champion's."""
    w, tau, bias = seed.w.clone(), seed.tau.clone(), seed.bias.clone()
    for g in take:
        m = groups[g]
        w[:, m["w"]] = champion.w[:, m["w"]]
        tau[:, m["tau"]] = champion.tau[:, m["tau"]]
        bias[:, m["bias"]] = champion.bias[:, m["bias"]]
    return seed.with_params(w=w, tau=tau, bias=bias)


def coalitions(players) -> list:
    """Every subset, in a fixed order (by size, then by the players' order)."""
    return [frozenset(c) for k in range(len(players) + 1) for c in itertools.combinations(players, k)]


def shapley(values: dict, players) -> dict:
    """Exact Shapley values of a full table {frozenset: value}."""
    n = len(players)
    out = {}
    for i in players:
        tot = 0.0
        for S in coalitions([p for p in players if p != i]):
            wgt = math.factorial(len(S)) * math.factorial(n - len(S) - 1) / math.factorial(n)
            tot += wgt * (values[S | {i}] - values[S])
        out[i] = tot
    return out


def dividends(values: dict, players) -> dict:
    """Harsanyi dividends (the Möbius transform): d(S) = Σ_{T ⊆ S} (−1)^{|S|−|T|} v(T)."""
    return {S: sum((-1) ** (len(S) - len(Tt)) * values[Tt] for Tt in coalitions(sorted(S, key=list(players).index)))
            for S in coalitions(players)}


def rebuild(divs: dict, players) -> dict:
    """The table back from its dividends: v(S) = Σ_{T ⊆ S} d(T)."""
    return {S: sum(divs[Tt] for Tt in coalitions(sorted(S, key=list(players).index))) for S in coalitions(players)}


def reversion(values: dict, players) -> dict:
    """The champion with one group set back to the seed's values: v(all − i) − v(all)."""
    full = frozenset(players)
    return {i: values[full - {i}] - values[full] for i in players}


def transplant(values: dict, players) -> dict:
    """The seed given one group's champion values: v({i}) − v(∅)."""
    return {i: values[frozenset([i])] - values[frozenset()] for i in players}


# ------------------------------------------------------------------ lesions (§5C)

EDGE_LESIONS = {
    "input_cut": lambda a, b: b == O.Q and a in O.RELAYS,
    "gate_cut": lambda a, b: a == O.Q and b in O.COMPARATORS,
    "outputs_a": lambda a, b: a in ("E3_A_CL", "E3_A_CR") and not b.startswith("E3"),
    "outputs_b": lambda a, b: a in ("E3_B_CL", "E3_B_CR") and not b.startswith("E3"),
    "outputs_both": lambda a, b: a in O.COMPARATORS and not b.startswith("E3"),
}


def edge_lesion(genome: Genome, ext, name: str) -> Genome:
    spec = BrainSpec.from_connectome(ext)
    pick = EDGE_LESIONS[name]
    hit = torch.tensor([pick(ext.names[i], ext.names[j]) for i, j in zip(spec.chem_i.tolist(), spec.chem_j.tolist())])
    w = genome.w.clone()
    w[:, hit] = 0.0
    return genome.with_params(w=w)


def latch_states(genome: Genome, ext) -> tuple[float, float, float]:
    """(low, unstable middle, high) roots of −q + w·tanh q + b with the organism's own q self-weight and bias."""
    w = MO.named_edges(genome, ext)[(O.Q, O.Q)]
    b = float(genome.bias[0, ext.index(O.Q)])
    r = [q for q, _ in L.roots(w, b)]
    if len(r) != 3:
        raise ValueError(f"the latch has {len(r)} roots (w {w}, b {b}): no two stable states")
    return r[0], r[1], r[2]


def a_high(genome: Genome, ext) -> bool | None:
    """The intended coding from the relay → latch signs: an A visit drives q down (goal B low) if RA → Q < 0
    and RB → Q > 0, so goal A is the high state. None if the signs do not agree."""
    e = MO.named_edges(genome, ext)
    ra, rb = e[("E3_RA", O.Q)], e[("E3_RB", O.Q)]
    if ra < 0 < rb:
        return True
    if rb < 0 < ra:
        return False
    return None


def reflex_clamp(ext) -> dict:
    return {ext.index("E3B_WL"): REFLEX_REST, ext.index("E3B_WR"): REFLEX_REST}


def without_scent(iface):
    """The interface with the four A/B nose channels' gains at 0; everything else unchanged."""
    gain = np.array(iface.sensor_gain, dtype=np.float64).copy()
    for k, n in enumerate(iface.signal_names):
        if n in SCENT:
            gain[k] = 0.0
    return dataclasses.replace(iface, sensor_gain=gain.astype(np.asarray(iface.sensor_gain).dtype))


class HeldBrain(Brain):
    """A Brain whose clamped neurons start at their clamp values, so a clamp holds from the first tick."""

    def initial_state(self, n_weys: int):
        v = super().initial_state(n_weys)
        if self.clamp_mask is not None:
            v = v * self.clamp_mask + self.clamp_value
        return v


# ------------------------------------------------------------------ the latch reading (§5D)

class SwitchTally:
    """One organism's latch reading over its weys' ticks.

    `tick(q, goal_before, visited_before)`: q computed in a tick, the goal in force when it was computed, and
    whether the wey had made a confirmed visit before it. A change of goal between ticks starts a leg toward
    the new goal; the leg is crossed when q is on the new goal's side of the unstable root, and its latency is
    counted from the leg's first tick. A leg still open at the next change is not crossed; one open at the end
    is censored. Agreement counts decided ticks (outside the middle third between the two stable states) after
    the first visit, by goal, under the intended coding."""

    def __init__(self, *, mid: float, low: float, high: float, a_high: bool):
        self.mid, self.a_high = mid, a_high
        third = (high - low) / 3.0
        self.band = (low + third, high - third)
        self.prev_goal = None
        self.open = None  # (direction, start tick)
        self.t = 0
        self.sw = {d: {"legs": 0, "crossed": 0, "latency_sum": 0, "censored": 0} for d in ("to_a", "to_b")}
        self.agree = {"A": 0, "B": 0}
        self.decided = {"A": 0, "B": 0}
        self.undecided = 0

    def _on_side(self, q: float, goal: int) -> bool:
        high = q > self.mid
        return high == (goal == 0) if self.a_high else high == (goal == 1)

    def tick(self, *, q: float, goal_before: int, visited_before: bool) -> None:
        if self.prev_goal is not None and goal_before != self.prev_goal:
            if self.open is not None:
                pass  # the open leg ended without crossing
            d = "to_a" if goal_before == 0 else "to_b"
            self.sw[d]["legs"] += 1
            self.open = (d, self.t, goal_before)
        if self.open is not None and self._on_side(q, self.open[2]):
            d, t0, _ = self.open
            self.sw[d]["crossed"] += 1
            self.sw[d]["latency_sum"] += self.t - t0
            self.open = None
        if visited_before:
            if self.band[0] < q < self.band[1]:
                self.undecided += 1
            else:
                g = "A" if goal_before == 0 else "B"
                self.decided[g] += 1
                self.agree[g] += int(self._on_side(q, goal_before))
        self.prev_goal = goal_before
        self.t += 1

    def result(self) -> dict:
        sw = {d: dict(v) for d, v in self.sw.items()}
        if self.open is not None:
            sw[self.open[0]]["censored"] += 1
        return {"switches": sw, "agree": dict(self.agree), "decided": dict(self.decided), "undecided": self.undecided}


class LatchRecorder:
    """§5D on a maze world, vectorised over worlds and weys on the device; `genomes[s]` is strain s.

    Each tick (after the world's post-move update) it reads every wey's q in world and wey order, pairs it with
    the goal in force when q was computed (the goal before this tick's switch), and accumulates the same counts
    as `SwitchTally`, per world."""

    def __init__(self, ext, genomes: list):
        self.q_index = ext.index(O.Q)
        st = [latch_states(g, ext) for g in genomes]
        self.coding = [a_high(g, ext) for g in genomes]
        self.low = torch.tensor([s[0] for s in st], dtype=torch.float64)
        self.mid = torch.tensor([s[1] for s in st], dtype=torch.float64)
        self.high = torch.tensor([s[2] for s in st], dtype=torch.float64)
        self.last_q = None

    def attach(self, world) -> None:
        a = world.assigns[0]
        self.strain = (a.slot_of // a.n_slots).long()  # [worlds]
        dev = world.device
        W, B = world.n_worlds, world.n_weys
        per = lambda x: x.to(dev)[self.strain].view(W, 1)  # noqa: E731
        self.mid_w, low, high = per(self.mid), per(self.low), per(self.high)
        third = (high - low) / 3.0
        self.band_lo, self.band_hi = low + third, high - third
        coding = torch.tensor([c if c is not None else True for c in self.coding], device=dev)
        self.ahigh_w = coding[self.strain].view(W, 1)
        self.prev_goal = world.goal.clone()
        self.prev_visited = world.has_visited.clone()
        z = lambda: torch.zeros(W, dtype=torch.long, device=dev)  # noqa: E731
        self.c = {k: z() for k in ("agree_A", "agree_B", "decided_A", "decided_B", "undecided",
                                   "legs_to_a", "legs_to_b", "crossed_to_a", "crossed_to_b",
                                   "lat_to_a", "lat_to_b", "censored_to_a", "censored_to_b")}
        self.open = torch.zeros(W, B, dtype=torch.bool, device=dev)
        self.open_goal = torch.zeros(W, B, dtype=torch.long, device=dev)
        self.open_start = torch.zeros(W, B, dtype=torch.long, device=dev)
        self.t = 0
        self.world = world

    def _on_side(self, q, goal):
        high = q > self.mid_w
        return torch.where(self.ahigh_w, high == (goal == 0), high == (goal == 1))

    def record(self, world) -> None:
        q = world.assigns[0].from_brain(world.v[0], world.n_worlds, world.n_weys)[..., self.q_index].to(torch.float64)
        self.last_q = q.to(world.v[0].dtype)
        g = self.prev_goal  # the goal in force when q was computed
        # a leg starts on the tick after a switch: compare the goal in force now with the one a tick before
        if self.t > 0:
            new = g != self.goal_before_prev
            for d, gv in (("to_a", 0), ("to_b", 1)):
                self.c[f"legs_{d}"] += (new & (g == gv)).sum(1)
            self.open = torch.where(new, torch.ones_like(self.open), self.open)
            self.open_goal = torch.where(new, g, self.open_goal)
            self.open_start = torch.where(new, torch.full_like(self.open_start, self.t), self.open_start)
        hit = self.open & self._on_side(q, self.open_goal)
        for d, gv in (("to_a", 0), ("to_b", 1)):
            m = hit & (self.open_goal == gv)
            self.c[f"crossed_{d}"] += m.sum(1)
            self.c[f"lat_{d}"] += ((self.t - self.open_start) * m).sum(1)
        self.open = self.open & ~hit
        elig = self.prev_visited
        und = elig & (q > self.band_lo) & (q < self.band_hi)
        dec = elig & ~und
        self.c["undecided"] += und.sum(1)
        agree = self._on_side(q, g)
        for name, gv in (("A", 0), ("B", 1)):
            m = dec & (g == gv)
            self.c[f"decided_{name}"] += m.sum(1)
            self.c[f"agree_{name}"] += (m & agree).sum(1)
        self.goal_before_prev = g.clone()
        self.prev_goal = world.goal.clone()
        self.prev_visited = world.has_visited.clone()
        self.t += 1

    def result(self) -> list:
        """Per world: its strain and every count (censored = legs still open at the end)."""
        for d, gv in (("to_a", 0), ("to_b", 1)):
            self.c[f"censored_{d}"] = (self.open & (self.open_goal == gv)).sum(1)
        cpu = {k: v.cpu().numpy() for k, v in self.c.items()}
        strain = self.strain.cpu().numpy()
        return [{"strain": int(strain[w]), **{k: int(v[w]) for k, v in cpu.items()}} for w in range(len(strain))]
