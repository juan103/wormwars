"""E4's evaluation harness (docs/E4/E4-DESIGN.md v3 §2-§4).

- `link_sets`: the 32 cross-link slots and their named subsets: into A (B → A) and into B (16 each, the directional
  read), sensory (from a nose) and comparator (from a comparator; 16 each), and by source neuron (8 bundles of 4).
- `conditions`: one champion's condition genomes, by name: "intact", "cut_<set>" for every subset, and
  "meansub_all" (all 32 cut jointly, their mean drive moved into the targets' biases; needs the champion's source
  means from its validation play, `means.source_means`).
- `play`: every named genome, gated, on every maze under one trail condition ("shared", "own" or "none"), in one
  batch; per genome the per-maze colony means of visits and legs. With `q_flips`, the gating check's switches too:
  per maze and wey the latch's mode changes (`QFlips`) beside the visits, and the share of weys where they agree
  (each visit should switch the latch once; descriptive, §5).
"""

from __future__ import annotations

import numpy as np
import torch

from ..brain import Genome
from ..e3 import maze_measures as MM
from ..e3 import maze_runs as MR
from ..e3 import maze_world as MW
from ..e3 import organism as O
from . import arms as AR
from .train import gated_brain

TRAILS = ("shared", "own", "none")


SWITCH_TOLERANCE = 5  # ticks from a visit to its latch switch, matched in order (descriptive; §5's gating check)


class QFlips:
    """A `Brain.substep_hook`: per strain and wey, how often the mode [v_q >= 0] changes (per substep, as the gate
    acts), and the tick of each change (up to the maze world's tracked legs). The start is q = 0, mode A."""

    def __init__(self, q: int, substeps: int = 1, slots: int = MW.LEGS):
        self.q, self.k, self.L = int(q), int(substeps), int(slots)
        self.mode = self.flips = self.ticks = None
        self.calls = 0

    def __call__(self, v: torch.Tensor) -> None:
        mode = v[..., self.q] >= 0
        if self.mode is None:
            self.mode = torch.ones_like(mode)
            self.flips = torch.zeros(mode.shape, dtype=torch.int64, device=v.device)
            self.ticks = torch.full((*mode.shape, self.L), -1, dtype=torch.int64, device=v.device)
        changed = mode != self.mode
        pos = self.flips.clamp(max=self.L - 1).unsqueeze(-1)
        cur = self.ticks.gather(-1, pos)
        self.ticks.scatter_(-1, pos, torch.where(changed.unsqueeze(-1), torch.full_like(cur, self.calls // self.k), cur))
        self.flips += changed.to(torch.int64)
        self.mode = mode
        self.calls += 1

    def ticks_of_flips(self) -> list:
        """Per strain and wey, the ticks of its mode changes."""
        t, n = self.ticks.cpu().numpy(), self.flips.cpu().numpy()
        return [[t[s, b, :n[s, b]].tolist() for b in range(t.shape[1])] for s in range(t.shape[0])]


def switch_alignment(flip_ticks: np.ndarray, flips: np.ndarray, visit_ticks: np.ndarray) -> dict:
    """[mazes, weys, L] flip ticks (−1 padded), [mazes, weys] counts, [mazes, weys, L] visit ticks (−1 padded): a wey
    is aligned if it has one switch per visit and each switch follows its visit, in order, within the tolerance."""
    lat, aligned = [], []
    for m in range(flips.shape[0]):
        for b in range(flips.shape[1]):
            v = visit_ticks[m, b][visit_ticks[m, b] >= 0]
            f = flip_ticks[m, b][:flips[m, b]]
            ok = len(f) == len(v)
            if ok and len(v):
                d = f - v
                lat += d.tolist()
                ok = bool((d >= 0).all() and (d <= SWITCH_TOLERANCE).all())
            aligned.append(ok)
    lat = np.asarray(lat)
    return {"aligned_share": float(np.mean(aligned)), "latency_min": int(lat.min()) if lat.size else None,
            "latency_max": int(lat.max()) if lat.size else None,
            "latency_q99": float(np.quantile(lat, 0.99)) if lat.size else None}


def link_sets(cx) -> dict:
    spec, ext = cx["spec"], cx["org"].ext
    slots = AR.slot_indices(cx)
    pre = [ext.names[int(spec.chem_i[k])] for k in slots.tolist()]
    post = [ext.names[int(spec.chem_j[k])] for k in slots.tolist()]

    def pick(keep):
        return slots[torch.tensor([bool(keep(a, b)) for a, b in zip(pre, post)])]

    out = {"all": slots,
           "into_A": pick(lambda a, b: b.startswith("E3_A_")),
           "into_B": pick(lambda a, b: b.startswith("E3_B_")),
           "sensory": pick(lambda a, b: a.endswith(("_NL", "_NR"))),
           "comparator": pick(lambda a, b: a in O.COMPARATORS)}
    for n in O._module_neurons("A") + O._module_neurons("B"):
        out["from_" + n[3:]] = pick(lambda a, b, n=n: a == n)
    return out


def conditions(genome: Genome, cx, *, means: torch.Tensor | None = None, names=None) -> dict:
    sets = link_sets(cx)
    names = ("intact", *[f"cut_{k}" for k in sets], "meansub_all") if names is None else tuple(names)
    out = {}
    for name in names:
        if name == "intact":
            out[name] = genome.clone()
        elif name == "meansub_all":
            if means is None:
                raise ValueError("mean substitution needs the champion's source means")
            out[name] = AR.mean_substitute(genome, sets["all"], means)
        elif name.startswith("cut_") and name[4:] in sets:
            out[name] = AR.cut(genome, sets[name[4:]])
        else:
            raise ValueError(f"unknown condition {name!r}")
    return out


def play(cfg, org, genomes: dict, ids, run_seed, device="cpu", *, access: str = "shared", ticks=None,
         q_flips: bool = False) -> dict:
    if access not in TRAILS:
        raise ValueError(f"the trail conditions are {TRAILS}")
    if org.gate is None:
        raise ValueError("E4's organisms play gated: this organism has no output gate")
    names, ids = list(genomes), np.asarray(ids)
    batch = Genome.cat([genomes[n] for n in names])
    brain = gated_brain(batch, org.gate, device)
    hook = QFlips(org.gate["q"], batch.cfg.substeps) if q_flips else None
    brain.substep_hook = hook
    ev = MR.play_batch(cfg, org.iface, brain, np.arange(len(names)), ids, run_seed, device, access=access, ticks=ticks)
    vt, visits = np.asarray(ev["visit_tick"]), np.asarray(ev["visits"])
    legs = MM.legs(vt.reshape(-1, *vt.shape[2:])).reshape(vt.shape[0], vt.shape[1], -1)
    out = {n: {"visits": MM.colony_mean(visits[k]), "legs": MM.colony_mean(legs[k]), "visit_tick": vt[k]}
           for k, n in enumerate(names)}
    if hook is not None:
        flips = hook.flips.cpu().numpy().reshape(len(names), len(ids), -1)
        fticks = hook.ticks.cpu().numpy().reshape(len(names), len(ids), flips.shape[-1], -1)
        for k, n in enumerate(names):
            out[n]["switches"] = {"flips": flips[k], "visits": visits[k], "flip_ticks": fticks[k],
                                  "match_share": float((flips[k] == visits[k]).mean()),
                                  **switch_alignment(fticks[k], flips[k], vt[k])}
    return out
