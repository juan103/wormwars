"""Scratch spike: the continuation with finished rows dropped from the batch, against the pilot's, on 96 SH-2010013
genomes and 100 N2 genomes: same verdicts? how much faster?"""
import sys
import time

import numpy as np
import torch

sys.path.insert(0, "scripts/memory_m2")
import pilot  # noqa: E402

K, E, c = pilot.K, pilot.E, pilot.c
orig = pilot.continuation


def compact(b64, start, roots, P32, cur, cap=pilot.CAP, substeps=None):
    """As pilot.continuation, but each strain leaves the batch when its rows are done (R = 1 here)."""
    S_, R, N = start.shape
    assert R == 1
    d0 = (start - roots).abs().amax(-1).numpy()
    win_d, win_f = np.zeros((S_, R, K.WINDOW)), np.zeros((S_, R, K.WINDOW))
    T = np.full((S_, R), cap)
    v_fin = start.clone()
    act = np.arange(S_)
    v, x = start.clone(), (start - roots).clone()
    rt, P, cu = roots, P32, cur
    sub = b64
    buf_d, buf_f = np.zeros((K.WINDOW, S_, R)), np.zeros((K.WINDOW, S_, R))
    below = np.zeros((S_, R), int)
    for t in range(1, cap + 1):
        v = sub.step(v, cu, substeps)
        x = torch.einsum("sij,srj->sri", P, x).clamp(-1e30, 1e30)
        k = (t - 1) % K.WINDOW
        buf_d[k][act] = (v - rt).abs().amax(-1).numpy()
        buf_f[k][act] = x.abs().amax(-1).numpy()
        below[act] = np.where(buf_f[k][act] < pilot.FORECAST_STOP * np.maximum(d0[act], 1e-300), below[act] + 1, 0)
        fin = (below[act, 0] >= 100) & (t >= pilot.MIN_T)
        if t == cap:
            fin[:] = True
        if fin.any():
            order = [(k + 1 + j) % K.WINDOW for j in range(K.WINDOW)]
            g = act[fin]
            win_d[g] = np.moveaxis(buf_d[order][:, g], 0, -1)
            win_f[g] = np.moveaxis(buf_f[order][:, g], 0, -1)
            T[g] = t
            v_fin[torch.from_numpy(g)] = v[torch.from_numpy(fin)]
            keep = ~fin
            if not keep.any():
                break
            kk = torch.from_numpy(np.where(keep)[0])
            act = act[keep]
            v, x, rt, P, cu = v[kk], x[kk], rt[kk], P[kk], cu[kk]
            sub = E.brain64(b64.genome.select(list(act)))
    return d0, T, T >= cap, win_d, win_f, v_fin


for gname in ("SH-2010013", "N2"):
    z = dict(np.load(pilot.OUT / f"main__{gname}.npz", allow_pickle=False))
    idx = [int(i) for i in z["idx"]]
    gs, cfg, n = pilot.graph_run(gname, idx)
    food = (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2
    cur = c.at(cfg, n, len(idx), [food]).double()
    end = torch.from_numpy(z["end"]).double()
    b64 = E.brain64(gs)
    out = {}
    for name, fn in (("pilot", orig), ("compact", compact)):
        pilot.continuation = fn
        t0 = time.time()
        res, roots = pilot.locate_and_reach(b64, end, cur)
        out[name] = (res, time.time() - t0)
    a, b = out["pilot"][0], out["compact"][0]
    same = (a["reach"] == b["reach"]).all() and (a["T"] == b["T"]).all()
    print(gname, f"pilot {out['pilot'][1]:.1f} s, compact {out['compact'][1]:.1f} s, same verdicts and T: {same}",
          flush=True)
