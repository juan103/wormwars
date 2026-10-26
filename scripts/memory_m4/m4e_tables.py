"""M4e's tables (docs/memory/M4E-PLAN.md, "Secondary"), written from the run's records and the local blocks file, no
simulation:
- blocks-summary.json: every host, draw and arm's block counts, weight, autapses, reciprocal pairs, degree ranges and
  the sign-invariant summaries S1, S2, S3 of its scaled magnitudes, with the local blocks.json's sha256 (blocks.json
  carries N2's block weights and stays local, rule 1); if a committed summary exists, the local file must match its
  digest (as m4d_tables does);
- tables.json: per arm, the per-genome predictor of stage 0 (the largest real part of the signed scaled block's
  eigenvalues) against the merged classes: its AUC for separate states and its bands.

    python scripts/memory_m4/m4e_tables.py      # needs the connectome and the local blocks.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import m4e  # noqa: E402
import m4e_read as RD  # noqa: E402
import m4e_stage0 as S0  # noqa: E402


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_digest(summary, d):
    if summary.get("blocks_sha256") != d:
        raise SystemExit("the local blocks.json differs from the one the committed summary describes")


def blocks_summary(verified):
    f = m4e.OUT / "blocks.json"
    d = digest(f)
    old = m4e.OUT / "blocks-summary.json"
    if old.exists():
        check_digest(json.load(open(old)), d)
    k = m4e.m4d.core_idx()
    rows = []
    for v in verified:
        g = v["g"]
        scale = g.cfg.init_w_scale / float(g.spec.chem_anat.mean())
        for a in m4e.arms():
            B = v["arms"][a][0].chem[np.ix_(k, k)].astype(np.float64)
            s = m4e.m4d.block_stats(B)
            rows.append({"host": v["rec"]["name"], "draw": v["draw"], "arm": a, "edges": s["edges"],
                         "weight": s["weight"], "autapses": s["autapses"], "reciprocal": s["reciprocal"],
                         "in_degree_range": [min(s["in_degree"]), max(s["in_degree"])],
                         "out_degree_range": [min(s["out_degree"]), max(s["out_degree"])],
                         **S0.summaries(np.minimum(B * scale, g.cfg.w_max))})
    out = {"blocks_sha256": d, "blocks": rows}
    old.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    return out


def predictor(verified, counts):
    """Per genome, the predictor and the class the reading uses (the reader's validated records and its global audit
    choice, Astra, round 2); per arm, its AUC, median and bands."""
    k = m4e.m4d.core_idx()
    lam = {a: [] for a in m4e.arms()}
    sep = {a: [] for a in m4e.arms()}
    genomes = []
    for v in verified:
        g = v["g"]
        scale = g.cfg.init_w_scale / float(g.spec.chem_anat.mean())
        for a in m4e.arms():
            B = v["arms"][a][0].chem[np.ix_(k, k)].astype(np.float64)
            x, _ = S0.genome_lams(v["signs"], np.minimum(B * scale, g.cfg.w_max))
            cls = np.array(RD.classes(counts, (v["rec"]["name"], v["draw"], a)))
            lam[a] += x.tolist()
            sep[a] += np.isin(cls, list(m4e.SEPARATE)).tolist()
            genomes.append({"host": v["rec"]["name"], "draw": v["draw"], "arm": a,
                            "lam": [round(float(z), 5) for z in x], "class": cls.tolist()})
    out = {"genomes": genomes, "arms": {}}
    for a in lam:
        x, s = np.array(lam[a]), np.array(sep[a])
        bands = {f"{lo}..{hi}": {"genomes": int(((x >= lo) & (x < hi)).sum()), "separate": int((s & (x >= lo) &
                                                                                               (x < hi)).sum())}
                 for lo, hi in ((-np.inf, 0.8), (0.8, 1.0), (1.0, 1.2), (1.2, np.inf))}
        out["arms"][a] = {"auc": S0.auc(x, s), "lam_median": float(np.median(x)), "bands": bands}
    return out


def main():
    verified = m4e.verify_run()
    counts = RD.load_counts(verified, m4e.arms())  # validates every panel and makes the audit's choice
    summ = blocks_summary(verified)
    tab = {"predictor": predictor(verified, counts), "second_pass_used": counts["use_second"],
           "note": "after the data; described, not read"}
    (m4e.OUT / "tables.json").write_text(json.dumps(tab, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in summ["blocks"]:
        print(f"{r['host']:18s} d{r['draw']} {r['arm']:5s} E {r['edges']:3d} W {r['weight']:7.1f} S1 {r['S1']:6.2f} "
              f"S2 {r['S2']:7.3f} S3 {r['S3']:5.3f}")
    for a, v in tab["predictor"]["arms"].items():
        print(a, v["auc"], v["lam_median"])


if __name__ == "__main__":
    main()
