"""03mc: the two-row history probe (`wormwars/exp03/twin.py`) against 03m's one-row outputs, on old inputs only.

    python scripts/p4mc_equivalence.py --device cuda      # writes experiments/03mc-p4-confirm/equivalence.json
    python scripts/p4mc_equivalence.py --smoke            # CPU, 8 genomes, two graphs, runs/p4mc-equivalence-smoke/

Measured before the pre-registration, so its tolerances can be declared from measured deviations with a margin
(Fable and Astra, design review v1). Every input is 03's or 03m's: 03's genomes for N2 and the first 16 graphs
of each of 03's ensembles (03m's decay panel), N2 with gap junctions off, N2 with the RIA pair deleted, and N2
paired with 03m's permutation seed 100. Nothing fresh is drawn. Compared, per genome where 03m kept arrays:
the ramp-end difference, the steady contrast, the follow-up curve to tick 300, the settling ranges and the
tanh slopes; and P4's terms against 03's committed supplement."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.deletion import delete_neurons  # noqa: E402
from wormwars.exp03 import twin  # noqa: E402

_spec = importlib.util.spec_from_file_location("p4m_for_equivalence", ROOT / "scripts" / "p4m.py")
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def rel(a, b) -> float:
    """The largest absolute difference over the largest |reference|: one number per array."""
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return float(np.max(np.abs(a - b)) / max(float(np.max(np.abs(b))), 1e-30))


def terms(final, steady) -> dict:
    f, s = np.abs(np.asarray(final, np.float64)), np.abs(np.asarray(steady, np.float64))
    return {"numerator": float(f.mean()), "denominator": float(s.mean())}


def term_rel(got: dict, want: dict) -> dict:
    return {k: abs(got[k] - want[k]) / abs(want[k]) for k in ("numerator", "denominator")}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    smoke = args.smoke
    dev = "cpu" if smoke else args.device
    n = 8 if smoke else None
    out_path = (ROOT / "runs" / "p4mc-equivalence-smoke" / "equivalence.json" if smoke
                else ROOT / "experiments" / "03mc-p4-confirm" / "equivalence.json")
    con, bank, iface = P.setup(dev)
    sup = P.supplement("03")
    dec = np.load(ROOT / "runs" / "p4m" / "decay-per-genome.npz", allow_pickle=False)
    syn = np.load(ROOT / "runs" / "p4m" / "synapses-per-genome.npz", allow_pickle=False)
    les = np.load(ROOT / "runs" / "p4m" / "lesions-per-genome.npz", allow_pickle=False)
    wts = np.load(ROOT / "runs" / "p4m" / "weights-per-genome.npz", allow_pickle=False)
    sl = slice(None) if n is None else slice(0, n)
    doc = {"what": "03mc: the two-row probe against 03m's one-row outputs, old inputs only", "stamp": P.stamp(),
           "device": dev, "genomes": n or 2048, "graphs": {}, "conditions": {}}
    t0 = time.perf_counter()
    names = P.panel_names(1 if smoke else 16)
    with acct.category("probe"):
        for name in names:
            g, cfg = P.probe_genomes(con, name, dev, n=n)
            h = twin.history(g, cfg, iface, bank, follow=300, every=10, extra=(5,), window=10)
            key = name.replace("-", "_")
            ref_diff = dec[f"{key}|diff"][:, sl]
            row = {"ticks_match": list(h["ticks"]) == [int(x) for x in dec["ticks"]],
                   "final": rel(h["raw_turn"]["final"], ref_diff[0]),
                   "steady_contrast": rel(h["raw_turn"]["steady_contrast"], dec[f"{key}|steady_contrast"][sl]),
                   "curve": rel(h["diff"], ref_diff),
                   "curve_tick30": rel(h["diff"][h["ticks"].index(30)], ref_diff[list(dec["ticks"]).index(30)]),
                   "end_state_range": rel(h["end_state_range"], dec[f"{key}|end_state_range"][sl]),
                   "hold_state_range": rel(h["hold_state_range"], dec[f"{key}|hold_state_range"][sl]),
                   "slope_hold": rel(h["slope_hold"], dec[f"{key}|slope_hold"][sl]),
                   "slope_ramp": rel(h["slope_ramp"], dec[f"{key}|slope_ramp"][sl])}
            if not smoke:
                row["terms_vs_03_supplement"] = term_rel(terms(h["raw_turn"]["final"], h["raw_turn"]["steady_contrast"]),
                                                         {"numerator": sup[name]["P4_turn_numerator"],
                                                          "denominator": sup[name]["P4_turn_denominator"]})
            doc["graphs"][name] = row
            print(name, {k: (f"{v:.1e}" if isinstance(v, float) else v) for k, v in row.items() if k != "terms_vs_03_supplement"},
                  flush=True)
        g, cfg = P.probe_genomes(con, "N2", dev, n=n)
        idx = {nm: i for i, nm in enumerate(con.names)}
        conds = {
            "gap junctions off": (lambda: g.with_params(g=torch.zeros_like(g.g)), cfg,
                                  syn["gap junctions off|final"][sl], syn["gap junctions off|steady"][sl]),
            "pair RIA deleted": (lambda: delete_neurons(g, [[idx["RIAL"], idx["RIAR"]]] * g.n_strains), cfg,
                                 les["final"][list(les["labels"]).index("pair RIA")][sl],
                                 les["steady"][list(les["labels"]).index("pair RIA")][sl]),
        }
        gp, cp = P.probe_genomes(con, "N2perm100", dev, graph=con, n=n, seed_name="N2")
        conds["N2perm100, paired"] = (lambda: gp, cp, wts["paired|N2perm100|final"][sl], wts["paired|N2perm100|steady"][sl])
        for label, (make, c, f_ref, s_ref) in conds.items():
            h = twin.history(make(), c, iface, bank, follow=5)
            doc["conditions"][label] = {"final": rel(h["raw_turn"]["final"], f_ref),
                                        "steady_contrast": rel(h["raw_turn"]["steady_contrast"], s_ref),
                                        "terms": term_rel(terms(h["raw_turn"]["final"], h["raw_turn"]["steady_contrast"]),
                                                          terms(f_ref, s_ref))}
            print(label, doc["conditions"][label], flush=True)
    worst = {}
    for row in doc["graphs"].values():
        for k, v in row.items():
            if isinstance(v, float):
                worst[k] = max(worst.get(k, 0.0), v)
            elif isinstance(v, dict):
                for kk, vv in v.items():
                    worst[f"{k}.{kk}"] = max(worst.get(f"{k}.{kk}", 0.0), vv)
    for label, row in doc["conditions"].items():
        for k, v in row.items():
            if isinstance(v, float):
                worst[f"{label}.{k}"] = v
            else:
                for kk, vv in v.items():
                    worst[f"{label}.{k}.{kk}"] = vv
    doc["worst"] = worst
    doc["all_ticks_match"] = all(r["ticks_match"] for r in doc["graphs"].values())
    doc["seconds"] = time.perf_counter() - t0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(worst, indent=1))


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("p4mc-equivalence-smoke" if smoke else "p4mc-equivalence")),
               default="probe", name="p4mc_equivalence")
