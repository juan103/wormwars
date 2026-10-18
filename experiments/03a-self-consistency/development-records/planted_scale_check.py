"""Exploratory (03a code review round 1, Fable's finding 1; D309): can the search recover a partner set at N2's scale?

A planted problem with K = 301 candidates and the true partner counts of real N2 targets. Fitness is the number of
planted partners connected: a perfect, noiseless signal, so this is an upper bound on what the task-driven search can
do. A second, illustrative oracle adds Gaussian noise (each planted partner worth 0.1, noise SD 0.3 per evaluation),
with numbers chosen arbitrarily. For each of pilot-dev's four move settings (default ladder), 5 seeds and 200
generations, Q (the share of planted partners connected in the coldest replica) is recorded every 10 generations.
CPU only, no simulation. Run from the repository root: py -3.13 <this file> <out.json>"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e03a import reinsert as R  # noqa: E402
from wormwars.e03a import search as S  # noqa: E402

cfg = Config()
con = load_connectome()
TARGETS = ["AIYL", "RIAL", "AIZL"]
MOVES = [[1 / 3, 1], [1 / 3, 3], [0.6, 1], [0.6, 3]]
GENS, SEEDS = 200, 5


def oracle(planted, noise, rng):
    def f(asks):
        out = []
        for _, st, _ in asks:
            hit = sum((st.masks()[t].numpy() & planted[t]).sum(1) for t in R.TYPES).astype(float)
            out.append(hit if noise is None else 0.1 * hit + rng.normal(0, noise, size=len(hit)))
        return out
    return f


res = {"targets": {}, "moves": MOVES, "generations": GENS, "seeds": SEEDS,
       "temperatures": list(S.SearchConfig().temperatures)}
for name in TARGETS:
    x = con.index(name)
    truth = R.truth(con, x)
    counts = R.true_counts(con, x)
    pr = S.Problem(con.n - 1, counts, R.has_self_loop(con, x))
    tot = sum(counts.values())
    chance = sum(v * v for v in counts.values()) / pr.K / tot
    row = {"counts": counts, "chance_q": chance, "by_setting": {}}
    for pm, mm in MOVES:
        for label, noise in (("perfect", None), ("noisy", 0.3)):
            qs = []
            for seed in range(SEEDS):
                scfg = S.SearchConfig(generations=GENS, p_move=pm, p_weights=(1 - pm) / 2, p_tau_bias=(1 - pm) / 2,
                                      max_moves=mm)
                s = S.free_search(pr, scfg, cfg.brain, cfg.mutation, 1000 * seed + 7)
                S.run_lockstep([s], oracle(truth, noise, np.random.default_rng(seed)))
                q = [sum(int((m[t].numpy() & truth[t]).sum()) for t in R.TYPES) / tot
                     for m in s.trace.cold_masks[9::10]]
                qs.append(q)
            qs = np.array(qs)
            row["by_setting"][f"p_move={pm:.2f}, max_moves={mm}, {label}"] = {
                "q_mean_every_10": qs.mean(0).round(4).tolist(), "q_at_100": qs[:, 9].round(4).tolist(),
                "q_at_200": qs[:, 19].round(4).tolist()}
            print(name, pm, mm, label, "Q@100", qs[:, 9].mean().round(3), "Q@200", qs[:, 19].mean().round(3), flush=True)
    res["targets"][name] = row
Path(sys.argv[1]).write_text(json.dumps(res, indent=1), encoding="utf-8")
