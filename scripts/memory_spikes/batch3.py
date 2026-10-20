"""Batch 3: linearise the one-tick map at the ramp's end (midpoint of the two histories, final input) and ask which
family the decay belongs to: a slow eigenvalue (feedback nearly pays the leak), transient growth (non-normal), or
neither (nonlinear). Fresh CPU panels, 256 genomes per graph, follow 100."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

N, SEED = 256, 7300
GRAPHS = ["N2", "SH-2010000", "SH-mirror-2040000", "SH-recip-2050000"]
OUT = S.ROOT / "runs" / "memory-spikes"
names = list(S.CON.names)
TURN_P = [names.index(x) for x in ("RMDDL", "RMDDR", "SMDDL", "SMDDR")]
TURN_M = [names.index(x) for x in ("RMDVL", "RMDVR", "SMDVL", "SMDVR")]


def jacobian(brain, v, cur):  # v, cur: [S, 1, N] -> J [S, N, N] with J[s, i, j] = d v'_i / d v_j
    s, _, n = v.shape
    J = torch.zeros(s, n, n, dtype=v.dtype)
    with torch.enable_grad():
        x = v.clone().requires_grad_(True)
        y = brain.step(x, cur)[:, 0, :]
        for i in range(n):
            (gi,) = torch.autograd.grad(y[:, i].sum(), x, retain_graph=True)
            J[:, i, :] = gi[:, 0, :]
    return J


res = {}
for gname in GRAPHS:
    t0 = time.time()
    con = S.graph(gname)
    g, cfg = S.genomes(con, N, SEED)
    h = S.probe(g, cfg, follow=100, keep_states=True)
    brain = Brain(g)
    food = (S.BANK["food_left"] + S.BANK["food_right"]) / 2
    cur = S._current(S.IFACE, cfg, dict(S.BANK, food_left=food, food_right=food), con.n, N, "cpu")
    v = h["ramp_end"]
    dv0 = (v[:, 0] - v[:, 1]).double()  # [S, N]
    m = v.mean(1, keepdim=True)
    J = jacobian(brain, m, cur).double()
    ev = torch.linalg.eigvals(J)
    rho = ev.abs().max(1).values.numpy()
    fro2 = (J ** 2).sum((1, 2)).numpy()
    henrici = np.sqrt(np.maximum(fro2 - (ev.abs() ** 2).sum(1).numpy(), 0) / fro2)
    # linear forecast of the turn difference: the pre-tanh read-out direction (plus mean minus mean) at ramp end
    c = torch.zeros(con.n, dtype=torch.float64)
    c[TURN_P] = 1 / 4
    c[TURN_M] = -1 / 4
    x = dv0.clone()
    lin = {0: (x @ c).numpy()}
    norms = {0: x.norm(dim=1).numpy()}
    for t in range(1, 101):
        x = torch.einsum("sij,sj->si", J, x)
        if t in (5, 10, 30, 100):
            lin[t] = (x @ c).numpy()
            norms[t] = x.norm(dim=1).numpy()
    d = np.abs(h["diff"])
    ok = d[0] >= 1e-3
    obs30 = d[S.TICKS.index(30), ok] / d[0, ok]
    lin30 = np.abs(lin[30][ok]) / np.maximum(np.abs(lin[0][ok]), 1e-12)
    growth = norms[10] / norms[0]  # full-state transient growth over 10 ticks, linear
    spec30 = rho ** 30
    from scipy.stats import spearmanr
    res[gname] = {
        "share30_obs": float(d[S.TICKS.index(30)].mean() / d[0].mean()),
        "median_rho_tick": float(np.median(rho)), "q90_rho": float(np.quantile(rho, 0.9)),
        "frac_rho_above_0.95": float((rho > 0.95).mean()), "frac_rho_above_1": float((rho > 1).mean()),
        "median_henrici": float(np.median(henrici)),
        "median_state_growth10": float(np.median(growth)), "frac_state_grows10": float((growth > 1).mean()),
        "median_obs30": float(np.median(obs30)), "median_lin30": float(np.median(lin30)),
        "rho_obs30_spearman": float(spearmanr(rho[ok], obs30).correlation),
        "lin30_obs30_spearman": float(spearmanr(lin30, obs30).correlation),
        "rho30_vs_obs30_median_ratio": float(np.median(obs30 / np.maximum(spec30[ok], 1e-12))),
        "henrici_obs30_spearman": float(spearmanr(henrici[ok], obs30).correlation),
        "seconds": round(time.time() - t0, 1)}
    print(gname, {k: round(v, 3) for k, v in res[gname].items()}, flush=True)
    json.dump(res, open(OUT / "batch3.json", "w"), indent=1)
print("done")
