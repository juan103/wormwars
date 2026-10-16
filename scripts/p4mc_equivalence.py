"""03mc: the two-row history probe (`wormwars/exp03/twin.py`) against one-row references, on old inputs only.

    python scripts/p4mc_equivalence.py --set check --device cuda   # the pre-run check set -> equivalence-check.json
    python scripts/p4mc_equivalence.py --set panel --device cuda   # all of 03m's 80 panel graphs and N2
    python scripts/p4mc_equivalence.py --set check --smoke         # CPU, 8 genomes, runs/p4mc-equivalence-smoke/

Every input is 03's or 03m's: 03's genomes for N2 and 03m's panel graphs, N2 with gap junctions off, N2 with the
RIA pair deleted, and N2 paired with 03m's permutation seed 100. Nothing fresh is drawn. The references:
- 03m's per-genome arrays (`runs/p4m/*.npz`, local): the ramp-end difference, the steady contrast, the follow-up
  curve to tick 300, the settling ranges and the tanh slopes, and from them the settling labels;
- 03m's committed `decay.json`: each graph's retained share at tick 30 (an aggregate);
- 03's committed supplement: P4's numerator and denominator;
- the pre-tanh read-out, which 03m never recorded: a one-row sequential run written here (`one_row_pre`).
The tolerances are declared in TOL (DESIGN.md §5) and every comparison is marked passed or failed; the formal
pre-run check is this script's `check` set at the bound commit (Fable, Astra, design reviews v1-v2)."""

from __future__ import annotations

import argparse
import hashlib
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
from wormwars.brain import Brain  # noqa: E402
from wormwars.deletion import delete_neurons  # noqa: E402
from wormwars.exp03 import measures as M  # noqa: E402
from wormwars.exp03 import twin  # noqa: E402

_spec = importlib.util.spec_from_file_location("p4m_for_equivalence", ROOT / "scripts" / "p4m.py")
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

# Declared tolerances (DESIGN.md §5), relative: aggregates as |got - ref| / |ref|; per-genome arrays as the
# largest absolute difference over the largest |reference|. Settling labels: at most LABELS genomes of a graph
# may change any label (counted once per genome, whichever labels change; Astra, review v2.1); more indicates a
# fault, not rounding.
TOL = {"terms": 1e-5, "share30": 1e-5, "pre_terms": 1e-5,
       "final": 1e-4, "steady_contrast": 1e-4, "curve_tick30": 1e-4, "slope_hold": 1e-4, "slope_ramp": 1e-4,
       "pre_final": 1e-4, "pre_steady_contrast": 1e-4, "hold_state_range": 3e-4, "curve": 2e-3,
       "condition_final": 1e-4, "condition_steady_contrast": 1e-4, "condition_terms": 1e-5}
LABELS = 2
SETTLE, START_FLOOR, REMAINING = 1e-4, 1e-3, 0.10  # 03m's settling rule and "separation remaining" (PLAN.md Q4)
# The pre-run check set: N2, the first 4 graphs of each ensemble, and three more: SH-mirror-40015, the worst
# settling deviation in the first, 81-graph run; SH-10007, the most settled-with-separation genomes; and
# SH-recip-50015, kept from design v2, which misnamed it as the worst deviation (D287, D288).
EXTRA = ["SH-mirror-40015", "SH-10007", "SH-recip-50015"]
# The local reference arrays, as `power.json` hashed them at design time (Fable, review v2.1): the check refuses
# other references. `weights` is not in power.json; its hash is recorded, not asserted.
REFERENCE_SHA256 = {"synapses": "2196e3ba8d9ad92587409de63746ea9224c5bbb73a53e357f11397ce4ba999f2",
                    "decay": "c6a0ab6eefaff4d4ff118e01931cf8b205d9f8951589336bd5fe47608d6d2d92",
                    "lesions": "c46b330da17da4ac20a796d1094258165dfc4ddca09e757ca0ebd3a2316b372f"}


def rel(a, b) -> float:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return float(np.max(np.abs(a - b)) / max(float(np.max(np.abs(b))), 1e-30))


def rel1(a: float, b: float) -> float:
    return abs(a - b) / abs(b)


def terms(final, steady) -> dict:
    f, s = np.abs(np.asarray(final, np.float64)), np.abs(np.asarray(steady, np.float64))
    return {"numerator": float(f.mean()), "denominator": float(s.mean())}


def labels(diff, end_range) -> dict:
    """03m's labels per genome: settled, separation remaining (among those starting above the floor), both."""
    d = np.abs(np.asarray(diff, np.float64))
    settled = np.asarray(end_range) < SETTLE
    remaining = (d[0] >= START_FLOOR) & (d[-1] > REMAINING * d[0])
    return {"settled": settled, "remaining": remaining, "both": settled & remaining}


@acct.counted("probe")
def one_row_pre(genome, cfg, iface, bank, warm=100, span=10) -> dict:
    """The pre-tanh terms from two one-row runs, the way 03 ran its histories: the turn-plus neurons' mean state
    minus the turn-minus neurons', after the hold and at the ramp's end."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    food = (bank["food_left"] + bank["food_right"]) / 2
    at = lambda lv: M._current(iface, cfg, dict(bank, food_left=lv, food_right=lv), n, s, dev)  # noqa: E731
    plus, minus = list(iface.turn_plus), list(iface.turn_minus)
    out = {}
    for name, start in (("rising", 0.25 * food), ("falling", 1.75 * food)):
        v = brain.initial_state(1)
        for _ in range(warm):
            v = brain.step(v, at(start))
        hold = v[:, 0, plus].mean(-1) - v[:, 0, minus].mean(-1)
        for t in range(span):
            v = brain.step(v, at(start + (food - start) * (t + 1) / span))
        out[name] = (hold.cpu().numpy(), (v[:, 0, plus].mean(-1) - v[:, 0, minus].mean(-1)).cpu().numpy())
    return {"final": out["rising"][1] - out["falling"][1], "steady_contrast": out["falling"][0] - out["rising"][0]}


def label_changes(a: dict, b: dict) -> dict:
    """Genomes whose labels differ, per label and in all (`any`: a genome counted once, whichever labels change)."""
    out = {k: int((a[k] != b[k]).sum()) for k in a}
    out["any"] = int(np.logical_or.reduce([a[k] != b[k] for k in a]).sum())
    return out


def record_path(out_dir: Path, name: str) -> Path:
    """A bare file name inside the output folder, never an existing file, smoke or formal (Fable, review v2.1;
    Astra, prereg review: an absolute path or ".." could otherwise reach a formal record from a smoke run)."""
    if not name or Path(name).name != name or name in (".", "..") or not name.endswith(".json"):
        raise SystemExit(f"--record must be a bare .json file name, not {name!r}")
    path = out_dir / name
    if path.resolve().parent != out_dir.resolve():
        raise SystemExit(f"--record {name!r} leaves the output folder: refusing")
    if path.exists():
        raise SystemExit(f"{path.name} exists: a record is never overwritten; choose another --record")
    return path


def judge(row: dict) -> dict:
    """Mark each measured deviation against its declared tolerance, and the genomes with any changed label against
    LABELS."""
    fails = [k for k, v in row["deviation"].items() if k in TOL and v > TOL[k]]
    if row.get("label_changes", {}).get("any", 0) > LABELS:
        fails.append("labels.any")
    row["failed"] = fails
    row["passed"] = not fails
    return row


def main(argv=None):
    """`argv` lets the formal runner (`scripts/p4mc.py check`) call the check inside its own accounting."""
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--set", choices=["check", "panel"], default="check")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--record", default=None, help="the record's file name in the output folder (the formal pre-run "
                                                 "check writes prerun-check.json, keeping the design-time records)")
    args = ap.parse_args(argv)
    smoke = args.smoke
    dev = "cpu" if smoke else args.device
    n = 8 if smoke else None
    out_dir = ROOT / "runs" / "p4mc-equivalence-smoke" if smoke else ROOT / "experiments" / "03mc-p4-confirm"
    out_path = record_path(out_dir, args.record or f"equivalence-{args.set}.json")
    con, bank, iface = P.setup(dev)
    sup = P.supplement("03")
    decay = json.loads((ROOT / "experiments" / "03m-p4-mechanism" / "decay.json").read_text(encoding="utf-8"))["graphs"]
    load = lambda f: np.load(ROOT / "runs" / "p4m" / f"{f}-per-genome.npz", allow_pickle=False)  # noqa: E731
    ref_sha = {k: hashlib.sha256((ROOT / "runs" / "p4m" / f"{k}-per-genome.npz").read_bytes()).hexdigest()
               for k in ("synapses", "decay", "lesions", "weights")}
    wrong = {k: v for k, v in REFERENCE_SHA256.items() if ref_sha[k] != v}
    if wrong:
        raise SystemExit(f"the local reference arrays differ from those power.json hashed: {sorted(wrong)}")
    dec, syn, les, wts = load("decay"), load("synapses"), load("lesions"), load("weights")
    ref_ticks = [int(x) for x in dec["ticks"]]
    sl = slice(None) if n is None else slice(0, n)
    if args.set == "panel":
        names = P.panel_names(16)
    else:
        names = P.panel_names(4) + EXTRA
    if smoke:
        names = names[:2]
    doc = {"what": "03mc: the two-row probe against one-row references, old inputs only", "set": args.set,
           "stamp": P.stamp(), "reference_sha256": ref_sha, "device": dev, "genomes": n or 2048, "tolerances": TOL, "label_changes_allowed": LABELS,
           "graphs": {}, "conditions": {}}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for name in names:
            g, cfg = P.probe_genomes(con, name, dev, n=n)
            h = twin.history(g, cfg, iface, bank, follow=300, every=10, extra=(5,), window=10)
            pre = one_row_pre(g, cfg, iface, bank)
            key = name.replace("-", "_")
            ref_diff = dec[f"{key}|diff"][:, sl]
            t30, r30 = h["ticks"].index(30), ref_ticks.index(30)
            share = float(np.abs(h["diff"][t30]).astype(np.float64).mean() / np.abs(h["diff"][0]).astype(np.float64).mean())
            mad = decay[name]["mean_abs_difference"]
            got_t = terms(h["raw_turn"]["final"], h["raw_turn"]["steady_contrast"])
            got_pre = terms(h["pre_turn"]["final"], h["pre_turn"]["steady_contrast"])
            ref_pre = terms(pre["final"], pre["steady_contrast"])
            dev_ = {"final": rel(h["raw_turn"]["final"], ref_diff[0]),
                    "steady_contrast": rel(h["raw_turn"]["steady_contrast"], dec[f"{key}|steady_contrast"][sl]),
                    "curve": rel(h["diff"], ref_diff), "curve_tick30": rel(h["diff"][t30], ref_diff[r30]),
                    "hold_state_range": rel(h["hold_state_range"], dec[f"{key}|hold_state_range"][sl]),
                    "end_state_range": rel(h["end_state_range"], dec[f"{key}|end_state_range"][sl]),
                    "slope_hold": rel(h["slope_hold"], dec[f"{key}|slope_hold"][sl]),
                    "slope_ramp": rel(h["slope_ramp"], dec[f"{key}|slope_ramp"][sl]),
                    "pre_final": rel(h["pre_turn"]["final"], pre["final"]),
                    "pre_steady_contrast": rel(h["pre_turn"]["steady_contrast"], pre["steady_contrast"]),
                    "pre_terms": max(rel1(got_pre[k], ref_pre[k]) for k in got_pre)}
            if not smoke:
                dev_["terms"] = max(rel1(got_t["numerator"], sup[name]["P4_turn_numerator"]),
                                    rel1(got_t["denominator"], sup[name]["P4_turn_denominator"]))
                dev_["share30"] = rel1(share, mad[r30] / mad[0])
            a = labels(h["diff"], h["end_state_range"])
            b = labels(ref_diff, dec[f"{key}|end_state_range"][sl])
            row = {"ticks_match": list(h["ticks"]) == ref_ticks, "deviation": dev_,
                   "label_changes": label_changes(a, b),
                   "label_counts": {k: [int(a[k].sum()), int(b[k].sum())] for k in a},
                   "share30": [share, mad[r30] / mad[0]], "pre_P4": got_pre["numerator"] / got_pre["denominator"]}
            doc["graphs"][name] = judge(row)
            print(name, "passed" if row["passed"] else f"FAILED {row['failed']}",
                  {k: f"{v:.1e}" for k, v in dev_.items()}, row["label_changes"], flush=True)
        g, cfg = P.probe_genomes(con, "N2", dev, n=n)
        idx = {nm: i for i, nm in enumerate(con.names)}
        lab = list(les["labels"])
        conds = {
            "gap junctions off": (lambda: g.with_params(g=torch.zeros_like(g.g)), cfg,
                                  syn["gap junctions off|final"][sl], syn["gap junctions off|steady"][sl]),
            "pair RIA deleted": (lambda: delete_neurons(g, [[idx["RIAL"], idx["RIAR"]]] * g.n_strains), cfg,
                                 les["final"][lab.index("pair RIA")][sl], les["steady"][lab.index("pair RIA")][sl])}
        gp, cp = P.probe_genomes(con, "N2perm100", dev, graph=con, n=n, seed_name="N2")
        conds["N2perm100, paired"] = (lambda: gp, cp, wts["paired|N2perm100|final"][sl], wts["paired|N2perm100|steady"][sl])
        for label, (make, c, f_ref, s_ref) in conds.items():
            h = twin.history(make(), c, iface, bank, follow=5)
            got, ref = terms(h["raw_turn"]["final"], h["raw_turn"]["steady_contrast"]), terms(f_ref, s_ref)
            row = {"deviation": {"condition_final": rel(h["raw_turn"]["final"], f_ref),
                                 "condition_steady_contrast": rel(h["raw_turn"]["steady_contrast"], s_ref),
                                 "condition_terms": max(rel1(got[k], ref[k]) for k in got)}}
            doc["conditions"][label] = judge(row)
            print(label, "passed" if row["passed"] else f"FAILED {row['failed']}", row["deviation"], flush=True)
    worst = {}
    for rows in (doc["graphs"], doc["conditions"]):
        for name, row in rows.items():
            for k, v in row["deviation"].items():
                if v >= worst.get(k, (-1.0, ""))[0]:
                    worst[k] = (v, name)
            for k, v in row.get("label_changes", {}).items():
                if v >= worst.get(f"labels.{k}", (-1, ""))[0]:
                    worst[f"labels.{k}"] = (v, name)
    doc["worst"] = {k: {"value": v, "where": w} for k, (v, w) in sorted(worst.items())}
    doc["all_ticks_match"] = all(r["ticks_match"] for r in doc["graphs"].values())
    doc["passed"] = doc["all_ticks_match"] and all(r["passed"] for rr in (doc["graphs"], doc["conditions"])
                                                   for r in rr.values())
    doc["seconds"] = time.perf_counter() - t0
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(doc, indent=1, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["worst"], indent=1))
    print("PASSED" if doc["passed"] else "FAILED")
    if not doc["passed"] and not smoke:
        raise SystemExit("the two-row probe is outside a declared tolerance")


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("p4mc-equivalence-smoke" if smoke else "p4mc-equivalence")),
               default="probe", name="p4mc_equivalence")
