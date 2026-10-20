"""M1, part B4's growers and forecast check (Fable; docs/memory/M1-PLAN.md, draft 8): the midpoint Jacobian at the
ramp's end (batch 3's method), an independent draw of 512 genomes (seed 7602), N2 and the first
random graph of each ensemble (6 panels). The fraction of
eligible genomes whose linear state norm grows over 10 ticks with spectral radius below 1, and their part of the
tick-30 numerator; the same for output growers (r(30) > 1); the Spearman between a tanh-consistent forecast,
|c_m' J^30 dv(0)| / a with c_m = c * (1 - tanh^2(m)), and the observed r(30), without the radius-above-1 genomes.
Writes runs/memory-m1/growers.json."""
import json
import sys
import time

import numpy as np
import torch
from scipy.stats import spearmanr

from common import (C, ENSEMBLES, GENOMES, OUT, SEED, START_FLOOR, S, at, diagnostic_available, dump, ensemble_of, follow,
                    panel_valid, ramp)
from wormwars import accounting as acct

torch.set_grad_enabled(False)
N = min(512, GENOMES)
GROWER_SEED = 7602  # an independent draw (Fable, round 7: seed 7600 would share the chemical signs with the panels)


def jacobian(brain, v, cur):  # batch 3's: J[s, i, j] = d v'_i / d v_j
    s, _, n = v.shape
    J = torch.zeros(s, n, n, dtype=v.dtype)
    with torch.enable_grad():
        x = v.clone().requires_grad_(True)
        y = brain.step(x, cur)[:, 0, :]
        for i in range(n):
            (gi,) = torch.autograd.grad(y[:, i].sum(), x, retain_graph=True)
            J[:, i, :] = gi[:, 0, :]
    return J.double()


rand = [g for g in json.load(open(OUT / "panel.json"))["random"]
        if json.load(open(OUT / "panels" / f"{g}__{SEED}.json"))["valid"]]  # valid panels only, as in summarise.py
graphs = ["N2"] + [x for x in (next((g for g in rand if ensemble_of(g) == e), None) for e in ENSEMBLES) if x]
res = {}
with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M1", script="growers.py",
                   argv=sys.argv[1:]):
    for gname in graphs:
        t0 = time.time()
        con = S.graph(gname)
        g, cfg = S.genomes(con, N, GROWER_SEED)
        brain, v, food, steady = ramp(g, cfg, with_steady=True)
        rec, _, _ = follow(brain, cfg, v, food, 30, record=(0, 30))
        a = rec[0]["dy"][:, 0].abs().numpy()
        d30 = rec[30]["dy"][:, 0].abs().numpy()
        obs30 = d30 / np.maximum(a, 1e-300)
        m = v.mean(1, keepdim=True).contiguous()
        J = jacobian(brain, m, at(cfg, con.n, N, [food]))
        rho = torch.linalg.eigvals(J).abs().max(1).values.numpy()
        cm = C.unsqueeze(0) * (1 - torch.tanh(m[:, 0].double()) ** 2)  # [S, N]
        x = rec[0]["dv"][:, 0].clone()
        n0 = x.norm(dim=1).numpy()
        for t in range(1, 31):
            x = torch.einsum("sij,sj->si", J, x)
            if t == 10:
                grow10 = x.norm(dim=1).numpy() / np.maximum(n0, 1e-300) > 1
        fore30 = (cm * x).sum(1).abs().numpy() / np.maximum(a, 1e-300)
        ok = a >= START_FLOOR
        if not diagnostic_available(a, steady, d30):  # this draw's own validity (Astra, round 5)
            res[gname] = {"eligible": int(ok.sum()), "available": False, "valid": panel_valid(a, steady, int(ok.sum())),
                          "numerator30": float(d30[ok].sum())}
            dump(res, "growers.json")
            continue
        stable = rho < 1
        num = d30[ok].sum()
        sg, og = ok & grow10 & stable, ok & (obs30 > 1)
        res[gname] = {"eligible": int(ok.sum()), "available": True, "frac_rho_gt1": float((ok & ~stable).sum() / ok.sum()),
                      "frac_state_grow10": float((ok & grow10).sum() / ok.sum()),
                      "frac_state_grow10_rho_lt1": float(sg.sum() / ok.sum()),
                      "numerator30_state_grow10_rho_lt1": float(d30[sg].sum() / num),
                      "frac_output_growers": float(og.sum() / ok.sum()),
                      "frac_output_growers_rho_lt1": float((og & stable).sum() / ok.sum()),
                      "numerator30_output_growers_rho_lt1": float(d30[og & stable].sum() / num),
                      "numerator30_rho_gt1": float(d30[ok & ~stable].sum() / num),
                      "spearman_forecast_obs30": float(spearmanr(fore30[ok], obs30[ok]).correlation),
                      "spearman_forecast_obs30_rho_lt1": float(spearmanr(fore30[ok & stable], obs30[ok & stable]).correlation),
                      "seconds": round(time.time() - t0, 1)}
        print(gname, {k: round(v, 3) for k, v in res[gname].items()}, flush=True)
        dump(res, "growers.json")
