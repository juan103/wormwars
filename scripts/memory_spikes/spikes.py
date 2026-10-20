"""Exploratory CPU spikes for the memory brainstorm's selection round (2026-10-20). Not registered; fresh CPU genomes.

A copy of 03mc's twin probe (wormwars/exp03/twin.py) with knobs: warm-up length, food scale, substeps, an erasure at
the ramp's end, and the ramp-end states returned for linearisation."""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.exp03.measures import _current, _readout  # noqa: E402

spec_ = importlib.util.spec_from_file_location("p4mc_for_spikes", ROOT / "scripts" / "p4mc.py")
P = importlib.util.module_from_spec(spec_)
spec_.loader.exec_module(P)
X = P.X
torch.set_grad_enabled(False)
CON, BANK, IFACE = P.setup("cpu")
TICKS = [0, 5] + list(range(10, 301, 10))


def graph(name):
    if name == "N2":
        return CON
    if name == "N2-rev":
        return CON.with_masks(CON.chem.T.copy(), CON.gap.copy(), "N2-rev")
    z = np.load(ROOT / "runs" / "p4mc" / "graphs" / f"{name}.npz", allow_pickle=False)
    return CON.with_masks(z["chem"], z["gap"], name)


def masks(chem, gap, name):
    return CON.with_masks(np.asarray(chem, np.float32), np.asarray(gap, np.float32), name)


def genomes(con, n, seed, substeps=None, cfg_name="N2"):
    spec = BrainSpec.from_connectome(con, device="cpu")
    cfg = X.grid.brain_config_for_graph(X.grid.task_config(Config(), "T1"), cfg_name)
    if substeps:
        cfg.brain.substeps = substeps
    g = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed), device="cpu")
    return g, cfg


def probe(g, cfg, warm=100, span=10, follow=300, food_scale=1.0, erase=None, keep_states=False):
    brain = Brain(g)
    s, n = g.n_strains, g.spec.n
    food = (BANK["food_left"] + BANK["food_right"]) / 2 * food_scale
    starts = (0.25 * food, 1.75 * food)

    def at(levels):
        return torch.cat([_current(IFACE, cfg, dict(BANK, food_left=lv, food_right=lv), n, s, "cpu") for lv in levels], 1)

    def raw(v):
        return torch.stack([_readout(IFACE, cfg, v[:, r:r + 1])[:, 1] for r in range(v.shape[1])], 1)

    v = brain.initial_state(2)
    cur = at(starts)
    for _ in range(warm):
        v = brain.step(v, cur)
    steady = raw(v)
    for t in range(span):
        v = brain.step(v, at([a + (food - a) * (t + 1) / span for a in starts]))
    out = {"ramp_end": v.clone()} if keep_states else {}
    if erase is not None:  # set the listed neurons of both rows to their midpoint
        mid = v[:, :, erase].mean(1, keepdim=True)
        v[:, :, erase] = mid
    rows = {}
    r = raw(v)
    rows[0] = r[:, 0] - r[:, 1]
    cur = at([food, food])
    for t in range(1, follow + 1):
        v = brain.step(v, cur)
        if t in TICKS:
            r = raw(v)
            rows[t] = r[:, 0] - r[:, 1]
    final = raw(out["ramp_end"]) if keep_states else None
    out.update({"diff": np.stack([rows[t].numpy() for t in TICKS if t <= follow]).astype(np.float64),
                "steady": (steady[:, 1] - steady[:, 0]).numpy().astype(np.float64)})
    return out


def summary(h, ref_diff0=None):
    d = np.abs(h["diff"])
    d0 = d[0] if ref_diff0 is None else np.abs(ref_diff0)  # erasure: normalise by the intact start
    i30 = TICKS.index(30)
    ok = d0 >= 1e-3
    per = d[i30, ok] / d0[ok]
    return {"share30": float(d[i30].mean() / d0.mean()), "share100": float(d[TICKS.index(100)].mean() / d0.mean()),
            "share300": float(d[-1].mean() / d0.mean()) if d.shape[0] == len(TICKS) else None,
            "median30": float(np.median(per)), "q75_30": float(np.quantile(per, 0.75)),
            "grow30": float((per > 1).mean()), "P4": float(d0.mean() / np.abs(h["steady"]).mean()),
            "corr_amp": float(np.corrcoef(np.log(d0[ok]), per)[0, 1])}


if __name__ == "__main__":
    t0 = time.time()
    g, cfg = genomes(CON, 256, 7001)
    h = probe(g, cfg)
    print("N2 256 genomes", round(time.time() - t0, 1), "s", {k: round(v, 3) for k, v in summary(h).items()})
