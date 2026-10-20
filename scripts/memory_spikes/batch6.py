"""Batch 6: check batch 4's reframing on a held-out panel. Batch 4 found that the state difference decays alike in N2
and the nulls (median per-genome norm ratio 0.197 vs 0.192 and 0.200) and that N2's residual sits on the head-motor
circuit around the turn read-out; erasing the 30 neurons with the largest residual took N2 to the null level.
(a) Erasures on a fresh panel (seed 7400), with the neuron lists chosen on batch 4's panel (seed 7100): the top 30 by
    residual at tick 30, the top 30 by difference at the ramp's end (does erasing most of the start do the same?),
    the 8 turn neurons, and random 30s.
(b) Other read-outs: is N2's advantage specific to the turn read-out? The forward read-out, the head-motor set, and
    100 random signed 8-neuron read-outs, on N2 and four nulls."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

N, FOLLOW = 1024, 30
OUT = S.ROOT / "runs" / "memory-spikes"
names = list(S.CON.names)
res = {}


def states(con, seed, erase=None):
    g, cfg = S.genomes(con, N, seed)
    brain = Brain(g)
    s, n = g.n_strains, g.spec.n
    food = (S.BANK["food_left"] + S.BANK["food_right"]) / 2

    def at(levels):
        return torch.cat([S._current(S.IFACE, cfg, dict(S.BANK, food_left=lv, food_right=lv), n, s, "cpu")
                          for lv in levels], 1)

    starts = (0.25 * food, 1.75 * food)
    v = brain.initial_state(2)
    cur = at(starts)
    for _ in range(100):
        v = brain.step(v, cur)
    for t in range(10):
        v = brain.step(v, at([a + (food - a) * (t + 1) / 10 for a in starts]))
    v_intact = v.clone()
    if erase is not None:
        v[:, :, erase] = v[:, :, erase].mean(1, keepdim=True)
    v0 = v.clone()
    cur = at([food, food])
    for _ in range(FOLLOW):
        v = brain.step(v, cur)
    a = lambda x: torch.tanh(x).numpy().astype(np.float64)  # noqa: E731
    return a(v_intact[:, 0]) - a(v_intact[:, 1]), a(v0[:, 0]) - a(v0[:, 1]), a(v[:, 0]) - a(v[:, 1]), cfg


def share(c, d_ref, d30):  # ratio of means of |read-out difference|, the registered form
    return float(np.abs(d30 @ c).mean() / np.abs(d_ref @ c).mean())


def readout(plus, minus):
    c = np.zeros(S.CON.n)
    c[list(plus)] = 1 / len(plus)
    c[list(minus)] = -1 / len(minus)
    return c


TURN = readout(S.IFACE.turn_plus, S.IFACE.turn_minus)
FWD = readout(S.IFACE.forward_plus, S.IFACE.forward_minus)
TURN_IDX = list(S.IFACE.turn_plus) + list(S.IFACE.turn_minus)

# (a) neuron lists from batch 4's panel
t = time.time()
di, d0, d30, _ = states(S.CON, 7100)
top_res = list(np.argsort(-np.abs(d30).mean(0))[:30])
top_start = list(np.argsort(-np.abs(d0).mean(0))[:30])
res["lists"] = {"top30_residual": [names[j] for j in top_res], "top30_start": [names[j] for j in top_start],
                "overlap": len(set(top_res) & set(top_start)), "turn_share_check_7100": share(TURN, di, d30)}
print("lists", res["lists"], round(time.time() - t, 1), flush=True)
rng = np.random.default_rng(11)
arms = {"intact": None, "top30_residual": top_res, "top30_start": top_start, "turn8": TURN_IDX}
for k in range(3):
    arms[f"random30_{k}"] = list(rng.choice(S.CON.n, 30, replace=False))
for key, idx in arms.items():
    t = time.time()
    di, d0, d30, _ = states(S.CON, 7400, erase=idx)
    res[f"N2/7400/erase-{key}"] = {"turn_share30_vs_intact": share(TURN, di, d30),
                                   "state_norm_ratio_median": float(np.median(
                                       np.linalg.norm(d30, axis=1) / np.linalg.norm(di, axis=1))),
                                   "seconds": round(time.time() - t, 1)}
    print(key, res[f"N2/7400/erase-{key}"], flush=True)
    json.dump(res, open(OUT / "batch6.json", "w"), indent=1)

# (b) read-outs
HEAD = [names.index(x) for x in ("RIAL", "RIAR", "RIML", "RIMR", "AIBL", "AIBR", "RMDL", "RMDR")]
rng = np.random.default_rng(12)
rand = []
for _ in range(100):
    idx = rng.choice(S.CON.n, 8, replace=False)
    rand.append(readout(idx[:4], idx[4:]))
for gname in ("N2", "SH-2010000", "SH-2010001", "SH-class-2030000", "SH-mirror-2040000"):
    t = time.time()
    di, d0, d30, _ = states(S.graph(gname), 7400)
    r = np.array([share(c, di, d30) for c in rand])
    res[f"{gname}/readouts"] = {
        "turn": share(TURN, di, d30), "forward": share(FWD, di, d30),
        "head_set_mean_abs": float(np.abs(d30[:, HEAD]).mean() / np.abs(di[:, HEAD]).mean()),
        "all_neurons_mean_abs": float(np.abs(d30).mean() / np.abs(di).mean()),
        "random8_median": float(np.median(r)), "random8_q10": float(np.quantile(r, 0.1)),
        "random8_q90": float(np.quantile(r, 0.9)),
        "state_norm_ratio_median": float(np.median(np.linalg.norm(d30, axis=1) / np.linalg.norm(di, axis=1))),
        "seconds": round(time.time() - t, 1)}
    print(gname, {k: round(v, 3) for k, v in res[f"{gname}/readouts"].items()}, flush=True)
    json.dump(res, open(OUT / "batch6.json", "w"), indent=1)
print("done")
