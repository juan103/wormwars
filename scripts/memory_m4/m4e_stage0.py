"""M4e's stage 0 (docs/reviews/20261025-dense-block-design/; Fable's round-1 proposal, reported as background and
choosing nothing): sign-invariant summaries of every M4d block and a per-genome coupling predictor, against M4d's
committed classes. Exploratory and after the data: M4d's records are already read.

Per host and arm, with M = init_w_scale x the block's anatomical weights / the intact spec's chem_anat.mean() (the
paired construction's magnitudes, clamped at w_max as Genome.clamp_ does):
    S1 = sum M (off-diagonal), S2 = sum M^2 (off-diagonal), S3 = sqrt(spectral radius of M o M) (diagonal included).
Per genome, J = signs o M (the genome's signed block, M4d's sign matrix) and lam = the largest real part of J's
eigenvalues; lam_real = the largest purely real eigenvalue (-inf if none).

    python scripts/memory_m4/m4e_stage0.py      # needs the connectome and M4d's local blocks.json; minutes

Writes runs/memory-m4e/stage0.json. No simulation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import m4d  # noqa: E402

torch.set_grad_enabled(False)
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs" / "memory-m4e"
SEPARATE = {0, 1}  # census.CODES: separate states, with or without a read-out difference
UNRESOLVED = 4


def auc(score, label):
    """Mann-Whitney AUC of score for label True against False (ties counted half)."""
    score, label = np.asarray(score, float), np.asarray(label, bool)
    pos, neg = score[label], score[~label]
    if len(pos) == 0 or len(neg) == 0:
        return None
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    ranks = np.empty(len(order))
    allv = np.concatenate([pos, neg])[order]
    i = 0
    while i < len(allv):  # average ranks over ties
        j = i
        while j + 1 < len(allv) and allv[j + 1] == allv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return float((ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def summaries(M):
    off = ~np.eye(len(M), dtype=bool)
    return {"S1": float(M[off].sum()), "S2": float((M[off] ** 2).sum()),
            "S3": float(np.sqrt(np.abs(np.linalg.eigvals(M * M)).max()))}


def genome_lams(signs, M):
    J = signs * M[None]
    ev = np.linalg.eigvals(J)
    lam = ev.real.max(1)
    real = np.where(np.abs(ev.imag) < 1e-9, ev.real, -np.inf).max(1)
    return lam, real


def main():
    hosts = m4d.load_hosts()
    blocks = m4d.load_blocks()
    k = m4d.core_idx()
    per_block, rows = [], []
    for r, host in hosts:
        h = r["host"]
        g_host, _ = m4d.host_genomes(host, m4d.N_PANEL, m4d.GENOME_SEED + h)
        cfg = g_host.cfg  # the brain configuration, as paired_genome uses it
        signs = m4d.sign_matrix(g_host, m4d.N_PANEL, m4d.SEED_SIGN + h)
        scale = cfg.init_w_scale / float(g_host.spec.chem_anat.mean())
        bl = {"I": host.chem[np.ix_(k, k)].astype(np.float32), **{a: blocks[h][a] for a in ("D", "R", "Rr", "P", "T")}}
        for arm, B in bl.items():
            M = np.minimum(B.astype(np.float64) * scale, cfg.w_max)
            clamped = int((B.astype(np.float64) * scale > cfg.w_max).sum())
            lam, lam_real = genome_lams(signs, M)
            rec = m4d.panel_file(r, arm)
            cls = np.array(json.load(open(rec))["class"])
            per_block.append({"host": r["name"], "arm": arm, **summaries(M), "clamped": clamped,
                              "separate": int(np.isin(cls, list(SEPARATE)).sum()),
                              "unresolved": int((cls == UNRESOLVED).sum()),
                              "lam_median": float(np.median(lam)), "frac_lam_above_1": float((lam > 1).mean())})
            for x, y, cl in zip(lam, lam_real, cls):
                rows.append((arm, float(x), float(y), int(cl)))
        print(f"host {r['name']} done", flush=True)

    lam = np.array([x for _, x, _, _ in rows])
    lam_real = np.array([y for _, _, y, _ in rows])
    cls = np.array([cl for _, _, _, cl in rows])
    sep = np.isin(cls, list(SEPARATE))
    res = cls != UNRESOLVED
    finite_real = np.where(np.isfinite(lam_real), lam_real, -1e9)
    out = {"note": "exploratory, after the data; chooses nothing (M4e design round 1, Fable's stage 0)",
           "blocks": per_block,
           "genome_auc": {"lam_all": auc(lam, sep), "lam_resolved": auc(lam[res], sep[res]),
                          "lam_real_all": auc(finite_real, sep), "lam_real_resolved": auc(finite_real[res], sep[res])},
           "by_arm": {}}
    for arm in ("I", "D", "R", "Rr", "P", "T"):
        m = np.array([a == arm for a, _, _, _ in rows])
        bands = {}
        for lo, hi in ((-np.inf, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, np.inf)):
            s = m & (lam >= lo) & (lam < hi)
            bands[f"{lo}..{hi}"] = {"genomes": int(s.sum()), "separate": int((s & sep).sum())}
        out["by_arm"][arm] = {"lam_auc": auc(lam[m], sep[m]), "lam_bands": bands}
    allb = {}
    for lo, hi in ((-np.inf, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, np.inf)):
        s = (lam >= lo) & (lam < hi)
        allb[f"{lo}..{hi}"] = {"genomes": int(s.sum()), "separate": int((s & sep).sum()),
                               "unresolved": int((s & (cls == UNRESOLVED)).sum())}
    out["lam_bands_all"] = allb
    from scipy.stats import spearmanr
    blk = [b for b in per_block if b["arm"] != "I"]
    no_t = [b for b in blk if b["arm"] != "T"]
    out["S3_vs_separate_spearman"] = {
        "block_arms_with_T": float(spearmanr([b["S3"] for b in blk], [b["separate"] for b in blk])[0]),
        "block_arms_without_T": float(spearmanr([b["S3"] for b in no_t], [b["separate"] for b in no_t])[0])}
    s3 = {(b["host"], b["arm"]): b["S3"] for b in per_block}
    hosts = sorted({b["host"] for b in per_block})
    out["hosts_T_S3_above_R"] = int(sum(s3[(h, "T")] > s3[(h, "R")] for h in hosts))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "stage0.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k_: v for k_, v in out.items() if k_ != "blocks"}, indent=1))
    for b in per_block:
        print(f"{b['host']:18s} {b['arm']:3s} S1 {b['S1']:6.2f} S2 {b['S2']:6.3f} S3 {b['S3']:5.3f} "
              f"clamped {b['clamped']} sep {b['separate']:3d} unres {b['unresolved']:3d} "
              f"lam_med {b['lam_median']:.3f} lam>1 {b['frac_lam_above_1']:.3f}")


if __name__ == "__main__":
    main()
