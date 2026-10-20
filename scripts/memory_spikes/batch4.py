"""Batch 4: where does the history difference live? (Batch 1 showed that erasing the 8 turn neurons at the ramp's
end leaves most of the memory: the read-out difference regrows from elsewhere.) Per-neuron persistence of the
state difference, its concentration, what predicts it across neurons and genomes (the tau lottery, Fable's
free-lesion regression), and erasure by group. Fresh CPU panels, 1024 genomes, seed 7100 (batch 1's panels)."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

N, SEED, FOLLOW = 1024, 7100, 30
OUT = S.ROOT / "runs" / "memory-spikes"
names = list(S.CON.names)
classes = np.array(S.CON.classes)
res = {}


def per_neuron_cycles(chem):
    A = (chem > 0).astype(np.int64)
    np.fill_diagonal(A, 0)
    A2 = A @ A
    c3 = np.diag(A2 @ A)  # 3-cycles through each neuron
    ff = (A2 * A).sum(1) + (A2 * A).sum(0) + np.einsum("ij,jk,ik->j", A, A, A)  # source, sink and middle roles
    return c3, ff, A.sum(0), A.sum(1)


def run(con, erase=None):
    g, cfg = S.genomes(con, N, SEED)
    brain = Brain(g)
    s, n = g.n_strains, g.spec.n
    food = (S.BANK["food_left"] + S.BANK["food_right"]) / 2

    def at(levels):
        return torch.cat([S._current(S.IFACE, cfg, dict(S.BANK, food_left=lv, food_right=lv), n, s, "cpu")
                          for lv in levels], 1)

    def raw(v):
        return torch.stack([S._readout(S.IFACE, cfg, v[:, r:r + 1])[:, 1] for r in range(2)], 1)

    starts = (0.25 * food, 1.75 * food)
    v = brain.initial_state(2)
    cur = at(starts)
    for _ in range(100):
        v = brain.step(v, cur)
    for t in range(10):
        v = brain.step(v, at([a + (food - a) * (t + 1) / 10 for a in starts]))
    r = raw(v)
    d0_intact = (r[:, 0] - r[:, 1]).abs().numpy()
    if erase is not None:
        v[:, :, erase] = v[:, :, erase].mean(1, keepdim=True)
    dv0 = (v[:, 0] - v[:, 1]).numpy().astype(np.float64)
    cur = at([food, food])
    for _ in range(FOLLOW):
        v = brain.step(v, cur)
    r = raw(v)
    d30 = (r[:, 0] - r[:, 1]).abs().numpy()
    dv30 = (v[:, 0] - v[:, 1]).numpy().astype(np.float64)
    return g, d0_intact, d30, dv0, dv30


def localise(key, con):
    t = time.time()
    g, d0, d30, dv0, dv30 = run(con)
    ok = d0 >= 1e-3
    ret = d30 / np.maximum(d0, 1e-12)
    E = np.abs(dv30).mean(0) / np.maximum(np.abs(dv0).mean(0), 1e-12)  # per-neuron persistence
    A30 = np.abs(dv30).mean(0)  # where the residual sits, in absolute terms
    x2 = dv30 ** 2
    pr = (x2.sum(1) ** 2) / np.maximum((x2 ** 2).sum(1), 1e-300)  # participation ratio of the residual
    top10 = np.sort(x2, 1)[:, -10:].sum(1) / np.maximum(x2.sum(1), 1e-300)
    state_ret = np.linalg.norm(dv30, axis=1) / np.maximum(np.linalg.norm(dv0, axis=1), 1e-12)
    c3, ff, indeg, outdeg = per_neuron_cycles(con.chem)
    logtau = torch.log(g.tau).numpy()
    bias = g.bias.numpy()
    carrier = np.argmax(x2, 1)
    tau_carrier = logtau[np.arange(len(carrier)), carrier]
    # free-lesion regression: which neuron's tau / bias predicts the read-out retention, genome by genome
    rho_tau = np.array([spearmanr(logtau[ok, j], ret[ok]).correlation for j in range(con.n)])
    rho_bias = np.array([spearmanr(bias[ok, j], ret[ok]).correlation for j in range(con.n)])
    order = np.argsort(-np.abs(rho_tau))[:10]
    carriers, counts = np.unique(carrier[ok & (ret > np.quantile(ret[ok], 0.9))], return_counts=True)
    top_car = carriers[np.argsort(-counts)][:10]
    res[key] = {
        "share30": float(d30.mean() / d0.mean()), "state_share30_median": float(np.median(state_ret)),
        "readout_vs_state_ret_spearman": float(spearmanr(ret[ok], state_ret[ok]).correlation),
        "residual_PR_median": float(np.median(pr)), "residual_top10_median": float(np.median(top10)),
        "PR_vs_ret_spearman": float(spearmanr(pr[ok], ret[ok]).correlation),
        "neuron_E_vs_c3_spearman": float(spearmanr(E, c3).correlation),
        "neuron_E_vs_ff_spearman": float(spearmanr(E, ff).correlation),
        "neuron_E_vs_indeg_spearman": float(spearmanr(E, indeg).correlation),
        "neuron_E_vs_outdeg_spearman": float(spearmanr(E, outdeg).correlation),
        "E_by_class": {c: float(np.median(E[classes == c])) for c in sorted(set(classes))},
        "top15_abs_residual_neurons": [(names[j], round(float(A30[j]), 4), classes[j]) for j in np.argsort(-A30)[:15]],
        "neuron_A30_vs_c3_spearman": float(spearmanr(A30, c3).correlation),
        "top15_E_neurons": [(names[j], round(float(E[j]), 3), classes[j]) for j in np.argsort(-E)[:15]],
        "tau_carrier_vs_ret_spearman": float(spearmanr(tau_carrier[ok], ret[ok]).correlation),
        "max_abs_rho_tau": float(np.nanmax(np.abs(rho_tau))), "max_abs_rho_bias": float(np.nanmax(np.abs(rho_bias))),
        "n_neurons_abs_rho_tau_gt_0.1": int((np.abs(rho_tau) > 0.1).sum()),
        "top_tau_neurons": [(names[j], round(float(rho_tau[j]), 3)) for j in order],
        "top_carriers_of_top10pct": [(names[j], int(c)) for j, c in zip(top_car, counts[np.argsort(-counts)][:10])],
        "seconds": round(time.time() - t, 1)}
    print(key, json.dumps(res[key]), flush=True)
    json.dump(res, open(OUT / "batch4.json", "w"), indent=1)
    return E, c3, A30


def erase(key, con, idx):
    t = time.time()
    _, d0, d30, _, _ = run(con, erase=list(idx))
    res[key] = {"share30_vs_intact": float(d30.mean() / d0.mean()), "n_erased": len(idx),
                "seconds": round(time.time() - t, 1)}
    print(key, res[key], flush=True)
    json.dump(res, open(OUT / "batch4.json", "w"), indent=1)


E_n2, c3_n2, A_n2 = localise("N2/localise", S.CON)
for gname in ("SH-2010000", "SH-class-2030000"):
    localise(f"{gname}/localise", S.graph(gname))
erase("N2/erase-none", S.CON, [])
for c in ("sensory", "inter", "motor", "pharyngeal", "other"):
    erase(f"N2/erase-class-{c}", S.CON, np.where(classes == c)[0])
erase("N2/erase-top30-c3", S.CON, np.argsort(-c3_n2)[:30])
erase("N2/erase-top30-E", S.CON, np.argsort(-E_n2)[:30])
erase("N2/erase-top30-abs-residual", S.CON, np.argsort(-A_n2)[:30])
rng = np.random.default_rng(3)
for k in range(3):
    erase(f"N2/erase-random30-{k}", S.CON, rng.choice(S.CON.n, 30, replace=False))
print("done")
