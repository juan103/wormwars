"""Batch 8: the two crazy ideas of round 3, and Astra's join.
- Fable: the memory is an instability of the head-bending oscillator (RIA, RMD, SMD). If so, the unstable genomes'
  leading eigenvalue is complex more often than the others', and its eigenvector sits on RMD and SMD.
- Astra: a small head circuit with several history-selectable states. If so, the long-lived genomes settle to separate
  endpoints rather than fading or oscillating.
- Astra's join: are the radius-above-1 genomes, the settled ones and the big tick-30 contributors the same genomes?
  And the Jacobian at each history's own ramp-end state, not only at the midpoint (which may be a saddle).
Fresh CPU panels (seed 7500), 512 genomes, follow 300."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import spikes as S  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

N, SEED = 512, 7500
OUT = S.ROOT / "runs" / "memory-spikes"
names = list(S.CON.names)
CORE = [names.index(x) for x in json.load(open(OUT / "batch6.json"))["lists"]["top30_start"]]
RMD_SMD = [i for i, x in enumerate(names) if x.startswith(("RMD", "SMD"))]
RIA = [names.index(x) for x in ("RIAL", "RIAR")]
res = {}


def jacobian(brain, v, cur):
    s, _, n = v.shape
    J = torch.zeros(s, n, n, dtype=v.dtype)
    with torch.enable_grad():
        x = v.clone().requires_grad_(True)
        y = brain.step(x, cur)[:, 0, :]
        for i in range(n):
            (gi,) = torch.autograd.grad(y[:, i].sum(), x, retain_graph=True)
            J[:, i, :] = gi[:, 0, :]
    return J.double()


def leading(J):
    ev, vec = torch.linalg.eig(J)
    k = ev.abs().argmax(1)
    lam = ev[torch.arange(len(k)), k]
    v = vec[torch.arange(len(k)), :, k].abs() ** 2
    v = v / v.sum(1, keepdim=True)
    return lam.abs().numpy(), lam.imag.abs().numpy() > 1e-6, v.numpy()


for gname in ("N2", "SH-2010000", "SH-class-2030000"):
    t0 = time.time()
    con = S.graph(gname)
    g, cfg = S.genomes(con, N, SEED)
    h = S.probe(g, cfg, follow=300, keep_states=True)
    brain = Brain(g)
    food = (S.BANK["food_left"] + S.BANK["food_right"]) / 2
    cur = S._current(S.IFACE, cfg, dict(S.BANK, food_left=food, food_right=food), con.n, N, "cpu")
    v = h["ramp_end"]
    out = {}
    for tag, state in (("mid", v.mean(1, keepdim=True)), ("up", v[:, 0:1]), ("down", v[:, 1:2])):
        out[tag] = leading(jacobian(brain, state.contiguous(), cur))
    d = h["diff"]  # signed, [ticks, genomes]
    a0 = np.abs(d[0])
    ok = a0 >= 1e-3
    i30, i250 = S.TICKS.index(30), S.TICKS.index(250)
    r30 = np.abs(d[i30]) / np.maximum(a0, 1e-12)
    r300 = np.abs(d[-1]) / np.maximum(a0, 1e-12)
    flips = (np.diff(np.sign(d), axis=0) != 0).sum(0)
    settled = ok & (r300 > 0.1) & (np.abs(d[-1] - d[i250]) / np.maximum(a0, 1e-12) < 0.02)
    oscill = ok & (flips >= 3)
    rho_mid, cplx_mid, vec_mid = out["mid"]
    rho_end = np.maximum(out["up"][0], out["down"][0])
    unst = ok & (rho_mid > 1)
    unst_end = ok & (rho_end > 1)
    num30 = np.abs(d[i30])
    top = ok & (num30 >= np.quantile(num30[ok], 0.9))

    def frac(mask, of):
        return float((mask & of).sum() / max(of.sum(), 1))

    res[gname] = {
        "n_ok": int(ok.sum()), "share30": float(num30.mean() / a0.mean()),
        "frac_rho_mid_gt1": float(unst.mean()), "frac_rho_own_end_gt1": float(unst_end.mean()),
        "frac_settled_separated": float(settled.mean()), "frac_oscillating": float(oscill.mean()),
        "P_settled_given_rho_mid_gt1": frac(settled, unst), "P_settled_given_rho_mid_le1": frac(settled, ok & ~unst),
        "P_settled_given_rho_own_end_gt1": frac(settled, unst_end),
        "P_rho_mid_gt1_given_settled": frac(unst, settled),
        "numerator30_share_rho_mid_gt1": float(num30[unst].sum() / num30[ok].sum()),
        "numerator30_share_settled": float(num30[settled].sum() / num30[ok].sum()),
        "numerator30_share_top10pct": float(num30[top].sum() / num30[ok].sum()),
        "P_rho_mid_gt1_given_top10pct": frac(unst, top),
        "frac_complex_leading_rho_gt1": frac(cplx_mid, unst), "frac_complex_leading_rho_le1": frac(cplx_mid, ok & ~unst),
        "leading_vec_mass_core30_rho_gt1": float(vec_mid[unst][:, CORE].sum(1).mean()) if unst.any() else None,
        "leading_vec_mass_core30_rho_le1": float(vec_mid[ok & ~unst][:, CORE].sum(1).mean()),
        "leading_vec_mass_RMD_SMD_rho_gt1": float(vec_mid[unst][:, RMD_SMD].sum(1).mean()) if unst.any() else None,
        "leading_vec_mass_RMD_SMD_rho_le1": float(vec_mid[ok & ~unst][:, RMD_SMD].sum(1).mean()),
        "leading_vec_mass_RIA_rho_gt1": float(vec_mid[unst][:, RIA].sum(1).mean()) if unst.any() else None,
        "uniform_mass_core30": len(CORE) / con.n, "uniform_mass_RMD_SMD": len(RMD_SMD) / con.n,
        "median_r30_settled": float(np.median(r30[settled])) if settled.any() else None,
        "median_r300_settled": float(np.median(r300[settled])) if settled.any() else None,
        "seconds": round(time.time() - t0, 1)}
    print(gname, {k: (round(x, 3) if isinstance(x, float) else x) for k, x in res[gname].items()}, flush=True)
    json.dump(res, open(OUT / "batch8.json", "w"), indent=1)
print("done")
