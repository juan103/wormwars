"""M1, part B4's tau controls (docs/memory/M1-PLAN.md, draft 8). The equal-tau control: the panels' genomes (seed
7600) with each genome's taus all set to its geometric mean, on N2 and the valid random graphs. Intact and equal-tau
shares at tick 30 are computed on one population, the genomes eligible in both (Astra, round 4); the intact values come
from panels/. The tau-permutation diagnostic (not a kill; taus are drawn independently of the weights): taus permuted
across each genome's neurons (seed 7601), on N2 and the first valid random graph of each ensemble; the correlation of
r_i(30) between intact and permuted genomes. Writes runs/memory-m1/tau.json."""
import json
import sys
import time

import numpy as np
import torch
from scipy.stats import spearmanr

from common import ENSEMBLES, GENOMES, OUT, SEED, START_FLOOR, S, dump, ensemble_of, follow, panel_valid, ramp
from wormwars import accounting as acct

torch.set_grad_enabled(False)
MIN_PAIRED = 10


def probe(g, cfg):
    brain, v, food, steady = ramp(g, cfg, with_steady=True)
    rec, _, _ = follow(brain, cfg, v, food, 30, record=(0, 30))
    a, d = rec[0]["dy"][:, 0].abs().numpy(), rec[30]["dy"][:, 0].abs().numpy()
    valid = panel_valid(a, steady, int((a >= START_FLOOR).sum()))
    return a, d, valid


def paired(z, a, d):
    """Intact and controlled shares on the genomes eligible in both; None if fewer than MIN_PAIRED."""
    both = (z["a"] >= START_FLOOR) & (a >= START_FLOOR)
    if both.sum() < MIN_PAIRED:
        return None
    return {"paired_genomes": int(both.sum()), "intact": float(z["d30"][both].sum() / z["a"][both].sum()),
            "control": float(d[both].sum() / a[both].sum())}


def main():
    P = OUT / "panels"
    valid_panel = lambda g: json.load(open(P / f"{g}__{SEED}.json"))["valid"]  # noqa: E731
    rand_all = json.load(open(OUT / "panel.json"))["random"]
    rand = [g for g in rand_all if valid_panel(g)]
    res = {"excluded_invalid_panels": [g for g in ["N2"] + rand_all if not valid_panel(g)], "equal": {}, "permuted": {}}
    if not valid_panel("N2"):
        res["summary"] = {"reading_available": False}
        dump(res, "tau.json")
        return
    diag = ["N2"] + [x for x in (next((g for g in rand if ensemble_of(g) == e), None) for e in ENSEMBLES) if x]
    with acct.recorded(OUT / "compute", OUT / "compute.json", default="probe", experiment="memory-M1", script="tau.py",
                       argv=sys.argv[1:]):
        for gname in ["N2"] + rand:
            t0 = time.time()
            con = S.graph(gname)
            z = np.load(P / f"{gname}__{SEED}.npz", allow_pickle=False)
            g, cfg = S.genomes(con, GENOMES, SEED)
            g.tau.copy_(torch.exp(torch.log(g.tau).mean(1, keepdim=True)).expand_as(g.tau))
            a, d, valid = probe(g, cfg)
            pr = paired(z, a, d) if valid else None
            res["equal"][gname] = {"valid": valid, **(pr or {"available": False}), "seconds": round(time.time() - t0, 1)}
            if gname in diag:
                g, cfg = S.genomes(con, GENOMES, SEED)
                gen = torch.Generator().manual_seed(7601)
                perm = torch.stack([torch.randperm(g.spec.n, generator=gen) for _ in range(g.n_strains)])
                g.tau.copy_(torch.gather(g.tau, 1, perm))
                ap, dp, vp = probe(g, cfg)
                both = (z["a"] >= START_FLOOR) & (ap >= START_FLOOR)
                res["permuted"][gname] = ({"valid": vp, "paired_genomes": int(both.sum()),
                                           "spearman_r30_intact_vs_permuted": float(spearmanr(z["d30"][both] / z["a"][both],
                                                                                              dp[both] / ap[both]).correlation)}
                                          if vp and both.sum() >= MIN_PAIRED else {"valid": vp, "available": False})
            print(gname, res["equal"][gname], res["permuted"].get(gname), flush=True)
            dump(res, "tau.json")
    E = res["equal"]
    usable = [x for x in rand if "control" in E[x]]
    if "control" not in E["N2"] or not usable:
        res["summary"] = {"reading_available": False, "usable_reference_graphs": len(usable)}
    else:
        lead = lambda k: E["N2"][k] - float(np.median([E[x][k] for x in usable]))  # noqa: E731
        res["summary"] = {"reading_available": True, "usable_reference_graphs": len(usable),
                          "intact_lead": lead("intact"), "equal_lead": lead("control"),
                          "random_at_or_above_N2_equal": int(sum(E[x]["control"] >= E["N2"]["control"] for x in usable))}
    dump(res, "tau.json")
    print(res["summary"])


if __name__ == "__main__":
    main()
