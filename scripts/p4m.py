"""03m: an exploratory look at what drives 03's P4, history dependence (experiments/03m-p4-mechanism/PLAN.md).

    python scripts/p4m.py tradeoff                  # no simulation: 03's and 03r's committed supplements
    python scripts/p4m.py tails --measures DIR      # no simulation: 03's local per-genome measures
    python scripts/p4m.py graphs                    # rebuild Q4's null panel from 03's record (CPU)
    python scripts/p4m.py synapses --device cuda    # N2 with gaps or chemical synapses off, or weights permuted by type
    python scripts/p4m.py weights --device cuda     # N2's wiring with 64 permutations of its weights, two designs
    python scripts/p4m.py decay --device cuda       # 300 ticks after the ramp: N2 and 16 graphs per ensemble
    python scripts/p4m.py lesions --device cuda     # N2 with each neuron, and each bilateral pair, deleted
    python scripts/p4m.py <command> --smoke         # tiny sizes, the CPU, runs/p4m-smoke/

Exploratory: the analyses are declared in PLAN.md before they run, but nothing here is confirmatory.
Every measurement reuses 03's own code and inputs (`scripts/exp03.py`, instance "03"): its stimulus
bank, its probe genomes (2 048, seeded per graph as 03 seeded them) and its P4 definition, the mean
|rising - falling| raw turn at the ramp's end over the mean |steady contrast|. Each simulating
command first reproduces 03's committed N2 numerator and denominator, in 03's batch composition
(2 048 strains, one row each), and every later batch keeps that composition. Formal runs need a
clean, pushed tree; a cap is checked before every batch; summaries and per-genome arrays are written
as each unit completes.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.deletion import delete_neurons  # noqa: E402
from wormwars.exp03 import measures as M  # noqa: E402

_spec = importlib.util.spec_from_file_location("exp03_frozen", ROOT / "scripts" / "exp03.py")
X = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X)
X.use_instance("03")

EXP = ROOT / "experiments" / "03m-p4-mechanism"
OUT = ROOT / "runs" / "p4m"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", "experiments/03m-p4-mechanism/PLAN.md"]
ENSEMBLES = ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip")
SUPPLEMENTS = {"03": ROOT / "experiments" / "03-generation0" / "supplement.json",
               "03r": ROOT / "experiments" / "03r-replication" / "supplement.json"}
DEN_FLOOR = 1e-4  # 03's exclusion floor for a P4 denominator
PRE_NAMED = ["RIA", "AIZ", "AIY", "AIB", "RIB", "RIM"]
PLAN = {
    "genomes": 2048,  # 03's P4 probe set
    "per_chunk": 2048,  # strains per batch: one probe set at a time, 03's composition (T1, D091)
    "reproduce_tolerance": 1e-6,  # relative, on 03's numerators and denominators
    "cap_gpu_hours": 5.0,  # every command together, counted by the accounting across attempts
    "lead": {"p4_below": "the pooled 95th percentile of 03's five ensembles",
             "response_below": "the pooled maximum of 03's five ensembles"},
    "follow_up_top": 5,  # valid single deletions with the lowest P4 and a response at least the pooled null median
    "decay": {"after": 300, "every": 10, "extra_ticks": [5], "graphs_per_ensemble": 16,
              "remaining_fraction": 0.10, "start_floor": 1e-3, "settle_tolerance": 1e-4, "settle_window": 10},
    "weights": {"permutations": 64, "seed_base": 100},
    "by_type_seeds": list(range(100, 108)),
}
SMOKE = False


# ----------------------------------------------------------------------------- shared

def fin(x):
    """A finite float, or None: JSON without NaN."""
    return float(x) if x is not None and math.isfinite(float(x)) else None


def write(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1, allow_nan=False))
        f.write("\n")
    os.replace(tmp, path)


def save_arrays(path: Path, arrays: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    os.replace(tmp, path)


def stamp(args=None) -> dict:
    p = reg.provenance(GUARDED)
    out = {k: p[k] for k in ("git_commit", "branch", "dirty", "python", "numpy", "torch", "cuda", "gpu",
                             "connectome_cache_sha256")}
    if args is not None:
        out.update(device=args.device, genomes=args.genomes or PLAN["genomes"], smoke=SMOKE)
    return out


def formal_guard(args) -> None:
    """Formal runs: a clean tree, pushed, on the registered GPU and environment (the shared guards),
    and 03's genome count."""
    if SMOKE:
        return
    if args.genomes not in (None, PLAN["genomes"]):
        raise SystemExit(f"formal outputs use 03's {PLAN['genomes']} probe genomes, not {args.genomes}")
    reg.require_formal(args.device, reg.provenance(GUARDED))


def clock() -> reg.CapClock:
    if (OUT / "compute").exists():
        acct.write_aggregate(OUT / "compute", OUT / "compute.json")
    return reg.CapClock(PLAN["cap_gpu_hours"], OUT / "compute.json")


def supplement(instance="03") -> dict:
    return json.loads(SUPPLEMENTS[instance].read_text(encoding="utf-8"))["per_graph"]


def in_ensemble(name: str, ens: str) -> bool:
    """Exact membership: `SH-10000` is in SH, `SH-route-20000` is not."""
    return name.startswith(ens + "-") and name[len(ens) + 1:].isdigit()


def ensemble_rows(pg: dict, ens: str) -> list[dict]:
    return [v for k, v in pg.items() if in_ensemble(k, ens)]


def pooled(pg: dict) -> tuple[np.ndarray, np.ndarray]:
    rows = [r for e in ENSEMBLES for r in ensemble_rows(pg, e)]
    return np.array([r["P4_turn"] for r in rows]), np.array([r["P4_turn_denominator"] for r in rows])


def thresholds(pg: dict) -> dict:
    p4, den = pooled(pg)
    return {"P4_pooled_95th": float(np.quantile(p4, 0.95)), "response_pooled_max": float(den.max()),
            "response_pooled_median": float(np.median(den))}


def null_position(r: dict, pg: dict) -> dict | None:
    """Where a valid (P4, denominator) pair sits in each of 03's ensembles: the share of graphs below
    it. None for an invalid measurement, which is never placed (Astra, review v1)."""
    if not r["valid"]:
        return None
    out = {}
    for ens in ENSEMBLES:
        rows = ensemble_rows(pg, ens)
        a = np.array([x["P4_turn"] for x in rows])
        d = np.array([x["P4_turn_denominator"] for x in rows])
        out[ens] = {"P4_share_below": float((a < r["P4"]).mean()), "denominator_share_below": float((d < r["denominator"]).mean())}
    return out


def lead_class(r: dict, pg: dict) -> str | None:
    """Against 03's pooled ensembles: P4 below the pooled 95th percentile, the response below the
    pooled maximum, both, or neither. None if invalid."""
    if not r["valid"]:
        return None
    t = thresholds(pg)
    lo_p4, lo_den = r["P4"] < t["P4_pooled_95th"], r["denominator"] < t["response_pooled_max"]
    return {(True, True): "both", (True, False): "P4 only", (False, True): "response only",
            (False, False): "neither"}[(bool(lo_p4), bool(lo_den))]


def setup(device):
    con = load_connectome()
    bank = json.loads(X.PILOT.read_text(encoding="utf-8"))["bank"]
    remap_sets = json.loads(X.INPUT_FILES["remaps.json"].read_text(encoding="utf-8"))["sets"]
    iface = X.grid.interface_for(con, "M0", remap_sets)
    return con, bank, iface


def probe_genomes(con, name: str, device, graph=None, n=None, cfg_name=None, seed_name=None) -> tuple[Genome, object]:
    """03's P4 probe genomes for `name`, exactly as `measure_graph` drew them. `cfg_name` and
    `seed_name` let the weight configuration and the genome draw come from different names (the
    paired permutation design)."""
    graph = graph if graph is not None else X._load_graph(con, name)
    spec = BrainSpec.from_connectome(graph, device=device)
    cfg = X.grid.brain_config_for_graph(X.grid.task_config(X.Config(), "T1"), cfg_name or name)
    pg = torch.Generator(device=device).manual_seed(X._gseed(seed_name or name) + 1)
    g = Genome.random(spec, cfg.brain, n or PLAN["genomes"], generator=pg, device=device)
    return g, cfg


def p4_of(h: dict) -> dict:
    """P4's terms, averaged in float64 as 03's supplement was; invalid below 03's floor or if not
    finite, and then never a ratio."""
    num = float(np.abs(np.asarray(h["raw_turn"]["final"], dtype=np.float64)).mean())
    den = float(np.abs(np.asarray(h["raw_turn"]["steady_contrast"], dtype=np.float64)).mean())
    valid = bool(math.isfinite(num) and math.isfinite(den) and den >= DEN_FLOOR)
    return {"numerator": fin(num), "denominator": fin(den), "P4": num / den if valid else None, "valid": valid}


def reproduce(name: str, got: dict) -> dict:
    """Relative differences from 03's committed numerator and denominator for `name`."""
    want = supplement("03")[name]
    rel = {k: (abs(got[k] - want[f"P4_turn_{k}"]) / abs(want[f"P4_turn_{k}"]) if got[k] is not None else None)
           for k in ("numerator", "denominator")}
    ok = all(v is not None and v <= PLAN["reproduce_tolerance"] for v in rel.values())
    return {"got": {k: got[k] for k in ("numerator", "denominator")},
            "03": {k: want[f"P4_turn_{k}"] for k in ("numerator", "denominator")}, "relative_difference": rel,
            "reproduced": ok}


def reproduce_n2(con, bank, iface, device) -> dict:
    """03's N2 numerator and denominator, recomputed in 03's composition; refuses to go on if they
    differ. Smoke runs a token check only."""
    g, cfg = probe_genomes(con, "N2", device, n=8 if SMOKE else None)
    r = reproduce("N2", p4_of(M.history(g, cfg, iface, bank)))
    if not r["reproduced"] and not SMOKE:
        raise SystemExit(f"N2's P4 terms do not reproduce 03's ({r['relative_difference']}); stopping")
    return r


def per_genome(h: dict) -> dict:
    return {"final": np.asarray(h["raw_turn"]["final"], dtype=np.float32),
            "steady": np.asarray(h["raw_turn"]["steady_contrast"], dtype=np.float32)}


# ----------------------------------------------------------------------------- Q1, no simulation

def cmd_tradeoff(args):
    """Within each ensemble: Spearman(denominator, P4); the log-log slope of the numerator on the
    denominator (P4's own log-log slope on the denominator is that slope minus 1: a restatement, not a
    separate component); P4 against the separately measured common turn response (the same 2 048
    genomes); N2's position; and N2's residual from a linear fit of P4 on log(denominator), a
    model-dependent description, not a significance score."""
    out = {}
    for inst in SUPPLEMENTS:
        pg = supplement(inst)
        n2 = pg["N2"]
        rows_out = {}
        for ens in ENSEMBLES:
            rows = ensemble_rows(pg, ens)
            p4 = np.array([r["P4_turn"] for r in rows])
            den = np.array([r["P4_turn_denominator"] for r in rows])
            num = np.array([r["P4_turn_numerator"] for r in rows])
            m0 = np.array([r["common_turn_M0"] for r in rows])
            b = np.polyfit(np.log(den), p4, 1)
            resid = p4 - np.polyval(b, np.log(den))
            pred = float(np.polyval(b, np.log(n2["P4_turn_denominator"])))
            rows_out[ens] = {
                "graphs": len(rows), "spearman_denominator_P4": float(spearmanr(den, p4).statistic),
                "loglog_slope_numerator_on_denominator": float(np.polyfit(np.log(den), np.log(num), 1)[0]),
                "spearman_common_turn_M0_P4": float(spearmanr(m0, p4).statistic),
                "N2_denominator_over_median": float(n2["P4_turn_denominator"] / np.median(den)),
                "N2_denominator_over_max": float(n2["P4_turn_denominator"] / den.max()),
                "graphs_with_P4_at_or_above_N2": int((p4 >= n2["P4_turn"]).sum()),
                "trend_at_N2": pred, "N2_residual_in_residual_sd": float((n2["P4_turn"] - pred) / resid.std()),
                "N2_denominator_beyond_range": bool(n2["P4_turn_denominator"] > den.max())}
        variants = {k: {"P4": v["P4_turn"], "denominator": v["P4_turn_denominator"],
                        "denominator_over_SH_median": v["P4_turn_denominator"]
                        / float(np.median([r["P4_turn_denominator"] for r in ensemble_rows(pg, "SH")]))}
                    for k, v in pg.items() if k.startswith("N2perm") or k == "N2-rev"}
        out[inst] = {"N2": {"P4": n2["P4_turn"], "numerator": n2["P4_turn_numerator"],
                            "denominator": n2["P4_turn_denominator"]}, "ensembles": rows_out, "N2_variants": variants}
    write(EXP / "tradeoff.json", {"what": "exploratory (PLAN.md Q1); no simulation", "stamp": stamp(), **out})
    for inst, d in out.items():
        print(inst, {e: (round(r["spearman_denominator_P4"], 2), round(r["spearman_common_turn_M0_P4"], 2),
                         r["graphs_with_P4_at_or_above_N2"]) for e, r in d["ensembles"].items()})


def tail_stats(f: np.ndarray, s: np.ndarray) -> dict:
    """Per graph, from per-genome |final| (f) and |steady contrast| (s): split halves; each term's
    top-5% share; the overlap of the two top-5% sets; P4 with the top 5% by numerator removed; and a
    cross-half pair (P4 from even genomes, response from odd)."""
    k = max(1, len(f) // 20)
    top_f, top_s = np.argsort(-f)[:k], np.argsort(-s)[:k]
    rest = np.setdiff1d(np.arange(len(f)), top_f)
    return {"P4_even": float(f[0::2].mean() / s[0::2].mean()), "P4_odd": float(f[1::2].mean() / s[1::2].mean()),
            "response_even": float(s[0::2].mean()), "response_odd": float(s[1::2].mean()),
            "top5pct_share_of_numerator": float(f[top_f].sum() / max(f.sum(), 1e-30)),
            "top5pct_share_of_denominator": float(s[top_s].sum() / max(s.sum(), 1e-30)),
            "top5pct_sets_overlap": float(len(np.intersect1d(top_f, top_s)) / k),
            "P4": float(f.mean() / s.mean()),
            "P4_without_top5pct_by_numerator": float(f[rest].mean() / max(s[rest].mean(), 1e-30))}


def cmd_tails(args):
    """From 03's local per-genome measures (not committed; their hashes are recorded): per ensemble,
    the split-half reliability of P4, a cross-half correlation of P4 with the response, the tail
    shares, and N2's rank on each (Fable, Astra, reviews v1-v2)."""
    d = Path(args.measures)
    names = ["N2"] + [f"{e}-{X.SEED_BASE[e] + i}" for e in ENSEMBLES for i in range(X.N_PER[e])]
    rows, hashes = {}, hashlib.sha256()
    for n in names:
        path = d / f"{n}.json"
        if not path.exists():
            continue
        raw = path.read_bytes()
        hashes.update(n.encode() + hashlib.sha256(raw).digest())
        h = json.loads(raw)["history"]["raw_turn"]
        rows[n] = tail_stats(np.abs(np.asarray(h["final"], dtype=np.float64)),
                             np.abs(np.asarray(h["steady_contrast"], dtype=np.float64)))
    n2 = rows.get("N2")
    out = {"N2": n2, "ensembles": {}}
    keys = ("top5pct_share_of_numerator", "top5pct_share_of_denominator", "top5pct_sets_overlap",
            "P4_without_top5pct_by_numerator")
    for e in ENSEMBLES:
        r = [v for k, v in rows.items() if in_ensemble(k, e)]
        if not r:
            continue
        col = lambda key: np.array([x[key] for x in r])  # noqa: E731
        out["ensembles"][e] = {
            "graphs": len(r), "split_half_correlation": float(np.corrcoef(col("P4_even"), col("P4_odd"))[0, 1]),
            "cross_half_spearman_P4even_response_odd": float(spearmanr(col("P4_even"), col("response_odd")).statistic),
            **{f"{key}_median": float(np.median(col(key))) for key in keys},
            **{f"{key}_max": float(col(key).max()) for key in keys},
            **({f"N2_{key}_share_of_graphs_below": float((col(key) < n2[key]).mean()) for key in keys} if n2 else {})}
    write(EXP / "tails.json", {"what": "exploratory (PLAN.md Q1b); no simulation; from 03's local per-genome measures",
                               "stamp": stamp(), "inputs": {"directory": "runs/exp03/measures (local)",
                                                            "files": len(rows), "sha256_of_name_and_file_hashes": hashes.hexdigest()},
                               **out})
    print({k: round(v, 3) for k, v in (n2 or {}).items()})
    print({e: (v["graphs"], round(v["split_half_correlation"], 3), round(v["top5pct_share_of_numerator_median"], 3),
               round(v.get("N2_top5pct_share_of_numerator_share_of_graphs_below", float("nan")), 3))
           for e, v in out["ensembles"].items()})


# ----------------------------------------------------------------------------- Q4's null panel

def panel_names(k: int) -> list[str]:
    return ["N2"] + [f"{e}-{X.SEED_BASE[e] + i}" for e in ENSEMBLES for i in range(k)]


def ensure_graphs(names: list[str]) -> dict:
    """03's graph files are not committed: rebuild any missing one from 03's record, and require its
    arrays to match 03's content manifest (D106). The runner's own load check then verifies it."""
    missing = [n for n in names if n != "N2" and not (X.GRAPHS / f"{n}.npz").exists()]
    if not missing:
        return {"rebuilt": 0}
    rep = X.rebuild_graphs(X.GRAPHS, only=missing, workers=1, windows_bytes=True)  # a pool cannot pickle this module
    if rep["content_mismatched"] or rep["mismatched"]:
        raise SystemExit(f"rebuilt graphs do not match 03's manifests: {rep}")
    return rep


def cmd_graphs(args):
    """Rebuild Q4's null panel before the GPU commands, so the rebuild does not run inside them."""
    rep = ensure_graphs(panel_names(2 if SMOKE else PLAN["decay"]["graphs_per_ensemble"]))
    print(rep)


# ----------------------------------------------------------------------------- Q3 synapse types

def cmd_synapses(args):
    """N2 with gap junctions off, chemical synapses off, and both off; and with only the chemical, or
    only the gap, weight magnitudes permuted among existing edges, over 8 seeds, paired with N2's
    genome draws (signs, biases and time constants unchanged)."""
    formal_guard(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    g, cfg = probe_genomes(con, "N2", args.device, n=args.genomes)
    pg = supplement("03")
    base = {"what": "exploratory (PLAN.md Q3)", "plan": PLAN, "stamp": stamp(args), "reproduce_N2": repro,
            "thresholds": thresholds(pg)}
    conds = [("intact", lambda: (g, cfg)),
             ("gap junctions off", lambda: (g.with_params(g=torch.zeros_like(g.g)), cfg)),
             ("chemical off", lambda: (g.with_params(w=torch.zeros_like(g.w)), cfg)),
             ("both off", lambda: (g.with_params(w=torch.zeros_like(g.w), g=torch.zeros_like(g.g)), cfg))]
    for which, field in (("chemical permuted", "init_chem_magnitude"), ("gaps permuted", "init_gap_magnitude")):
        for sd in PLAN["by_type_seeds"][:2 if SMOKE else None]:
            def make(field=field, sd=sd):
                c = cfg.copy()
                setattr(c.brain, field, "permuted")
                c.brain.init_permutation_seed = sd
                pgen = torch.Generator(device=args.device).manual_seed(X._gseed("N2") + 1)
                return Genome.random(g.spec, c.brain, g.n_strains, generator=pgen, device=args.device), c
            conds.append((f"{which}, seed {sd}", make))
    rows, arrays = {}, {}
    with acct.category("probe"):
        for label, make in conds:
            cap.check()
            gg, cc = make()
            h = M.history(gg, cc, iface, bank)
            r = p4_of(h)
            rows[label] = {**r, "null_position": null_position(r, pg), "class": lead_class(r, pg)}
            for k, v in per_genome(h).items():
                arrays[f"{label}|{k}"] = v
            write(EXP / "synapses-partial.json", {**base, "conditions": rows})
            save_arrays(OUT / "synapses-per-genome.npz", arrays)
    intact = rows["intact"]
    for r in rows.values():
        r["change_from_intact"] = ({"P4": r["P4"] - intact["P4"], "denominator": r["denominator"] - intact["denominator"]}
                                   if r["valid"] and intact["valid"] else None)
    write(EXP / "synapses.json", {**base, "conditions": rows})
    (EXP / "synapses-partial.json").unlink(missing_ok=True)
    print({k: (v["P4"] and round(v["P4"], 3), v["denominator"] and round(v["denominator"], 4)) for k, v in rows.items()})


# ----------------------------------------------------------------------------- Q5 weights

def cmd_weights(args):
    """N2's wiring with its anatomical weight magnitudes permuted among its edges, 64 seeds, in two
    designs: independent genome draws per permutation, as 03 drew its N2perm graphs; and paired,
    N2's own genome draws with only the magnitudes permuted (Astra, Fable, review v1)."""
    formal_guard(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    W = PLAN["weights"]
    seeds = [W["seed_base"] + i for i in range(2 if SMOKE else W["permutations"])]
    pg = supplement("03")
    base = {"what": "exploratory (PLAN.md Q5)", "plan": PLAN, "stamp": stamp(args), "reproduce_N2": repro,
            "thresholds": thresholds(pg)}
    rows, arrays = {"independent": {}, "paired": {}}, {}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for sd in seeds:
            name = f"N2perm{sd}"
            for design, seed_name in (("independent", name), ("paired", "N2")):
                cap.check()
                g, cfg = probe_genomes(con, name, args.device, graph=con, n=args.genomes, seed_name=seed_name)
                h = M.history(g, cfg, iface, bank)
                r = p4_of(h)
                rows[design][name] = {**r, "null_position": null_position(r, pg), "class": lead_class(r, pg)}
                for k, v in per_genome(h).items():
                    arrays[f"{design}|{name}|{k}"] = v
            write(EXP / "weights-partial.json", {**base, "permutations": rows})
            save_arrays(OUT / "weights-per-genome.npz", arrays)
    n2 = pg["N2"]
    p4_null, den_null = pooled(pg)
    summary = {}
    for design, rr in rows.items():
        v = [r for r in rr.values() if r["valid"]]
        p4 = np.array([r["P4"] for r in v])
        den = np.array([r["denominator"] for r in v])
        has = len(v) > 0
        summary[design] = {
            "valid": len(v), "invalid": len(rr) - len(v),
            "P4_median": float(np.median(p4)) if has else None,
            "P4_share_below_N2": float((p4 < n2["P4_turn"]).mean()) if has else None,
            "P4_share_above_pooled_null_95th": float((p4 > np.quantile(p4_null, 0.95)).mean()) if has else None,
            "denominator_median": float(np.median(den)) if has else None,
            "denominator_share_below_N2": float((den < n2["P4_turn_denominator"]).mean()) if has else None,
            "denominator_share_above_pooled_null_max": float((den > den_null.max()).mean()) if has else None,
            "per_ensemble": {e: {"P4_share_above_ensemble_95th": float((p4 > np.quantile(
                [x["P4_turn"] for x in ensemble_rows(pg, e)], 0.95)).mean()) if has else None} for e in ENSEMBLES}}
    write(EXP / "weights.json", {**base, "summary": summary, "permutations": rows, "seconds": time.perf_counter() - t0})
    (EXP / "weights-partial.json").unlink(missing_ok=True)
    print(json.dumps({d: {k: v for k, v in s.items() if k != "per_ensemble"} for d, s in summary.items()}, indent=1))


# ----------------------------------------------------------------------------- Q4 decay

class WindowRange:
    """The largest range (max minus min over the window's ticks, per unit, then the largest over
    units) of a quantity sampled at every tick of a window: an oscillation that returns to its start
    still shows its swing (Astra, review v2)."""

    def __init__(self):
        self.lo = self.hi = None

    def add(self, x: torch.Tensor) -> None:
        self.lo = x.clone() if self.lo is None else torch.minimum(self.lo, x)
        self.hi = x.clone() if self.hi is None else torch.maximum(self.hi, x)

    def value(self) -> np.ndarray:
        r = self.hi - self.lo
        return r.reshape(r.shape[0], -1).amax(dim=1).cpu().numpy()


def history_full(genome: Genome, cfg, iface, bank, after: int, every: int, extra=(5,), window=10) -> dict:
    """The same stimulus as `measures.history`, followed for `after` ticks of the final input.
    Returns the signed rising-minus-falling raw turn [ticks, genomes] at tick 0 (the ramp's end), the
    `extra` ticks and every `every` ticks; the steady contrast; over the last `window` ticks of each
    hold and of each trajectory's end, the range of the full state and of the turn read-out (settling);
    and the mean tanh slope of the turn read-out neurons at the holds' and the ramp's end
    (saturation)."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    food = (bank["food_left"] + bank["food_right"]) / 2
    at = lambda lvl: M._current(iface, cfg, dict(bank, food_left=lvl, food_right=lvl), n, s, dev)  # noqa: E731
    turn_idx = list(iface.turn_plus) + list(iface.turn_minus)
    ticks = sorted({0, *extra, *range(every, after + 1, every)})
    res = {}
    for name, start in (("rising", 0.25 * food), ("falling", 1.75 * food)):
        v = brain.initial_state(1)
        hold_state, hold_turn = WindowRange(), WindowRange()
        for t in range(1, 101):
            v = brain.step(v, at(start))
            if t > 100 - window:  # the last `window` ticks of the hold, every tick
                hold_state.add(v)
                hold_turn.add(M._readout(iface, cfg, v)[:, 1:2])
        steady = M._readout(iface, cfg, v)[:, 1]
        slope_hold = (1 - torch.tanh(v[:, 0, turn_idx]) ** 2).mean(-1)
        for t in range(10):
            v = brain.step(v, at(start + (food - start) * (t + 1) / 10))
        slope_ramp = (1 - torch.tanh(v[:, 0, turn_idx]) ** 2).mean(-1)
        rows = {0: M._readout(iface, cfg, v)[:, 1]}
        end_state, end_turn = WindowRange(), WindowRange()
        for t in range(1, after + 1):
            v = brain.step(v, at(food))
            if t in ticks:
                rows[t] = M._readout(iface, cfg, v)[:, 1]
            if t > after - window:  # the last `window` ticks, every tick
                end_state.add(v)
                end_turn.add(M._readout(iface, cfg, v)[:, 1:2])
        res[name] = {"curve": torch.stack([rows[t] for t in ticks]).cpu().numpy(), "steady": steady.cpu().numpy(),
                     "hold_state": hold_state.value(), "hold_turn": hold_turn.value(),
                     "end_state": end_state.value(), "end_turn": end_turn.value(),
                     "slope_hold": slope_hold.cpu().numpy(), "slope_ramp": slope_ramp.cpu().numpy()}
    both = lambda k: np.maximum(res["rising"][k], res["falling"][k])  # noqa: E731
    return {"ticks": ticks, "diff": res["rising"]["curve"] - res["falling"]["curve"],
            "steady_contrast": res["falling"]["steady"] - res["rising"]["steady"],
            "hold_state_range": both("hold_state"), "hold_turn_range": both("hold_turn"),
            "end_state_range": both("end_state"), "end_turn_range": both("end_turn"),
            "slope_hold": (res["rising"]["slope_hold"] + res["falling"]["slope_hold"]) / 2,
            "slope_ramp": (res["rising"]["slope_ramp"] + res["falling"]["slope_ramp"]) / 2}


def share(mask: np.ndarray, of: np.ndarray) -> dict:
    """A conditional share with its counts; None when nothing is eligible."""
    n = int(of.sum())
    return {"share": float((mask & of).sum() / n) if n else None, "count": int((mask & of).sum()), "of": n}


def decay_summary(h: dict) -> dict:
    D = PLAN["decay"]
    a = np.abs(h["diff"]).astype(np.float64)
    start, end = a[0], a[-1]
    eligible = start >= D["start_floor"]
    settled = h["end_state_range"] < D["settle_tolerance"]
    remaining = eligible & (end > D["remaining_fraction"] * start)
    everyone = np.ones_like(eligible)
    k = max(1, len(start) // 20)
    return {"ticks": h["ticks"], "mean_abs_difference": a.mean(axis=1).tolist(),
            "ratio_of_means_at_end": fin(a[-1].mean() / a[0].mean()) if a[0].mean() > 0 else None,
            "eligible": share(eligible, everyone),
            "separation_remaining_among_eligible": share(remaining, eligible),
            "settled_at_end": share(settled, everyone),
            "settled_among_remaining": share(settled, remaining),
            "holds_settled": share(h["hold_state_range"] < D["settle_tolerance"], everyone),
            "hold_turn_range_median": float(np.median(h["hold_turn_range"])),
            "top5pct_share_of_numerator": float(np.sort(start)[::-1][:k].sum() / max(start.sum(), 1e-30)),
            "mean_turn_readout_tanh_slope_hold": float(h["slope_hold"].mean()),
            "mean_turn_readout_tanh_slope_ramp": float(h["slope_ramp"].mean()),
            "numerator": float(start.mean()), "denominator": float(np.abs(h["steady_contrast"].astype(np.float64)).mean())}


def cmd_decay(args):
    """Q4 on N2 and the first 16 graphs of each ensemble; also each panel graph's P4 with gap junctions
    off (Fable, review v1), so Q3's gaps-off N2 has a matched null panel. Every panel graph's tick 0
    and steady contrast must reproduce 03's numerator and denominator."""
    formal_guard(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    D = PLAN["decay"]
    names = panel_names(2 if SMOKE else D["graphs_per_ensemble"])
    missing = [n for n in names if n != "N2" and not (X.GRAPHS / f"{n}.npz").exists()]
    if missing and not SMOKE:
        raise SystemExit(f"{len(missing)} panel graphs are missing: run `p4m.py graphs` first")
    ensure_graphs(names)
    base = {"what": "exploratory (PLAN.md Q4)", "plan": PLAN, "stamp": stamp(args), "reproduce_N2": repro}
    out, arrays = {}, {}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for name in names:
            cap.check()
            g, cfg = probe_genomes(con, name, args.device, n=args.genomes)
            h = history_full(g, cfg, iface, bank, D["after"], D["every"], D["extra_ticks"], D["settle_window"])
            s = decay_summary(h)
            s["reproduce_03"] = reproduce(name, {"numerator": s["numerator"], "denominator": s["denominator"]})
            if not s["reproduce_03"]["reproduced"] and not SMOKE:
                raise SystemExit(f"{name}: tick 0 does not reproduce 03 ({s['reproduce_03']['relative_difference']})")
            cap.check()
            s["gaps_off"] = p4_of(M.history(g.with_params(g=torch.zeros_like(g.g)), cfg, iface, bank))
            out[name] = s
            key = name.replace("-", "_")
            for k in ("diff", "steady_contrast", "hold_state_range", "hold_turn_range", "end_state_range",
                      "end_turn_range", "slope_hold", "slope_ramp"):
                arrays[f"{key}|{k}"] = np.asarray(h[k], dtype=np.float32)
            arrays["ticks"] = np.array(h["ticks"])
            write(EXP / "decay-partial.json", {**base, "graphs": out})
            save_arrays(OUT / "decay-per-genome.npz", arrays)
    write(EXP / "decay.json", {**base, "graphs": out, "seconds": time.perf_counter() - t0})
    (EXP / "decay-partial.json").unlink(missing_ok=True)
    for n in names:
        o = out[n]
        print(n, o["ratio_of_means_at_end"] and round(o["ratio_of_means_at_end"], 3),
              o["separation_remaining_among_eligible"]["share"], o["settled_at_end"]["share"])


# ----------------------------------------------------------------------------- Q2 lesions

def pairs(names: list[str]) -> dict[str, list[int]]:
    """Bilateral pairs by name: XXXL with XXXR (for example RIAL, RIAR -> RIA)."""
    idx = {n: i for i, n in enumerate(names)}
    return {n[:-1]: [i, idx[n[:-1] + "R"]] for n, i in idx.items() if n.endswith("L") and n[:-1] + "R" in idx}


def delete_edges(genome: Genome, per_strain: list[list[int]], kind: str) -> Genome:
    """Like `delete_neurons`, but only the chemical edges ("chemical") or only the gap junctions
    ("gap") touching the listed neurons; biases are kept."""
    spec = genome.spec
    w, g = genome.w.clone(), genome.g.clone()
    for s, ks in enumerate(per_strain):
        if not ks:
            continue
        k = torch.as_tensor(list(ks), device=genome.device)
        if kind == "chemical":
            w[s, torch.isin(spec.chem_i, k) | torch.isin(spec.chem_j, k)] = 0.0
        elif kind == "gap":
            g[s, torch.isin(spec.gap_i, k) | torch.isin(spec.gap_j, k)] = 0.0
        else:
            raise ValueError(kind)
    return genome.with_params(spec=spec, w=w, g=g)


def history_in_chunks(g: Genome, cfg, iface, bank, deletions: list[list[int]], per_chunk: int, check=None,
                      on_chunk=None, kind: str | None = None) -> list[dict]:
    """P4 terms of the probe genomes under each deletion list, in chunks of whole deletions
    (`per_chunk` strains). With `per_chunk` equal to the probe set, every deletion runs in 03's
    composition. `kind` restricts the deletion to one synapse type. Per-genome arrays are kept."""
    n = g.n_strains
    out = []
    step = max(1, per_chunk // n)
    for lo in range(0, len(deletions), step):
        if check is not None:
            check()
        batch = deletions[lo:lo + step]
        big = Genome.cat([g] * len(batch))
        lists = [d for d in batch for _ in range(n)]
        mod = delete_neurons(big, lists) if kind is None else delete_edges(big, lists, kind)
        h = M.history(mod, cfg, iface, bank)
        for j in range(len(batch)):
            sl = slice(j * n, (j + 1) * n)
            rt = {k: v[sl] for k, v in h["raw_turn"].items()}
            out.append({**p4_of({"raw_turn": rt}), "_final": rt["final"], "_steady": rt["steady_contrast"]})
        if on_chunk is not None:
            on_chunk(out)
    return out


def degrees(con, i: int) -> dict:
    chem = np.asarray(con.chem) != 0
    gap = np.asarray(con.gap) != 0
    return {"chem_in": int(chem[:, i].sum()), "chem_out": int(chem[i, :].sum()), "gap": int(gap[i, :].sum())}


def public(r: dict) -> dict:
    return {k: v for k, v in r.items() if not k.startswith("_")}


def lesion_entries(names: list[str], turn: set[int]) -> list[tuple[str, list[int]]]:
    """The empty deletion first; then the pre-named targets (pairs, then their singles), so a cap hit
    loses them last; then every other single; then every other pair."""
    idx = {n: i for i, n in enumerate(names)}
    prs = {k: v for k, v in pairs(names).items() if not set(v) & turn}
    first = [(f"pair {k}", prs[k]) for k in PRE_NAMED if k in prs]
    first += [(names[i], [i]) for k in PRE_NAMED if k in prs for i in prs[k]]
    for k in PRE_NAMED:  # an unpaired pre-named neuron, if any
        if k not in prs and k in idx and idx[k] not in turn:
            first.append((k, [idx[k]]))
    done = {tuple(d) for _, d in first}
    singles = [(names[i], [i]) for i in range(len(names)) if i not in turn and (i,) not in done]
    rest_pairs = [(f"pair {k}", v) for k, v in prs.items() if k not in PRE_NAMED]
    return [("intact", [])] + first + singles + rest_pairs


def cmd_lesions(args):
    formal_guard(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    g, cfg = probe_genomes(con, "N2", args.device, n=args.genomes)
    turn = set(iface.turn_plus) | set(iface.turn_minus)  # only the turn read-out: P4 reads turn alone
    names = list(con.names)
    entries = lesion_entries(names, turn)
    if SMOKE:
        entries = entries[:6]
    pg = supplement("03")
    th = thresholds(pg)
    p4_all, den_all = pooled(pg)
    b = np.polyfit(np.log(den_all), p4_all, 1)
    t0 = time.perf_counter()
    base = {"what": "exploratory (PLAN.md Q2)", "plan": PLAN, "stamp": stamp(args), "reproduce_N2": repro,
            "per_chunk": args.per_chunk, "composition": [args.per_chunk, 1, "direct brain steps, one row per strain"],
            "thresholds": th, "excluded_turn_readout_neurons": sorted(names[i] for i in turn)}
    state = {"intact": None}

    def row(label, dl, r):
        out = {"deleted": label, **public(r), "null_position": null_position(r, pg), "class": lead_class(r, pg)}
        if r["valid"]:
            out["residual_from_pooled_trend"] = float(r["P4"] - np.polyval(b, np.log(r["denominator"])))
            it = state["intact"]
            if it is not None and it["valid"]:
                out["change_from_intact"] = {"P4": r["P4"] - it["P4"], "denominator": r["denominator"] - it["denominator"]}
        if len(dl) == 1:
            out["degree"] = degrees(con, dl[0])
        return out

    def checkpoint(results, extra=None):
        if state["intact"] is None and results:
            state["intact"] = results[0]
            if not SMOKE and (results[0]["numerator"], results[0]["denominator"]) != (repro["got"]["numerator"],
                                                                                      repro["got"]["denominator"]):
                raise SystemExit("the empty deletion does not reproduce the intact brain in the same composition")
        write(EXP / "lesions-partial.json", {**base, "rows": [row(lbl, dl, r) for (lbl, dl), r in zip(entries, results)],
                                             **(extra or {})})
        if len(results) % 20 == 0 or len(results) == len(entries):
            save_arrays(OUT / "lesions-per-genome.npz", {"labels": np.array([lbl for lbl, _ in entries[:len(results)]]),
                                                         "final": np.stack([r["_final"] for r in results]),
                                                         "steady": np.stack([r["_steady"] for r in results])})

    with acct.category("probe"):
        res = history_in_chunks(g, cfg, iface, bank, [d for _, d in entries], args.per_chunk, cap.check, checkpoint)
    rows = [row(lbl, dl, r) for (lbl, dl), r in zip(entries, res)]
    # follow-up: the valid singles with the lowest P4 among those keeping at least the pooled null median response
    singles = [(lbl, dl, r) for (lbl, dl), r in zip(entries, res) if len(dl) == 1 and r["valid"]
               and r["denominator"] >= th["response_pooled_median"]]
    top = sorted(singles, key=lambda x: x[2]["P4"])[:PLAN["follow_up_top"]]
    follow, farr = {}, {}
    with acct.category("probe"):
        for kind in ("chemical", "gap"):
            rr = history_in_chunks(g, cfg, iface, bank, [dl for _, dl, _ in top], args.per_chunk, cap.check, kind=kind)
            follow[kind] = [row(lbl, dl, r) for (lbl, dl, _), r in zip(top, rr)]
            for (lbl, _, _), r in zip(top, rr):
                farr[f"{kind}|{lbl}|final"], farr[f"{kind}|{lbl}|steady"] = r["_final"], r["_steady"]
            save_arrays(OUT / "lesions-follow-up-per-genome.npz", farr)
            write(EXP / "lesions-partial.json", {**base, "rows": rows, "follow_up_by_synapse_type": follow})
    write(EXP / "lesions.json", {**base, "rows": rows, "follow_up_by_synapse_type": follow,
                                 "classes": {c: [r["deleted"] for r in rows if r["class"] == c]
                                             for c in ("both", "P4 only", "response only")},
                                 "seconds": time.perf_counter() - t0})
    (EXP / "lesions-partial.json").unlink(missing_ok=True)
    for r in sorted([r for r in rows if r["valid"]], key=lambda r: r["P4"])[:8]:
        print(f"{r['deleted']:10s} P4 {r['P4']:.3f} den {r['denominator']:.4f} {r['class']}")


# ----------------------------------------------------------------------------- main

def main():
    global EXP, OUT, SMOKE
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["tradeoff", "tails", "graphs", "lesions", "synapses", "decay", "weights"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--genomes", type=int, default=None, help="probe genomes (formal: 03's 2 048 only)")
    ap.add_argument("--per-chunk", type=int, default=PLAN["per_chunk"], help="lesions: strains per batch")
    ap.add_argument("--measures", default=str(ROOT / "runs" / "exp03" / "measures"), help="tails: 03's local measures")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, the CPU, runs/p4m-smoke/")
    args = ap.parse_args()
    if args.smoke:
        SMOKE = True
        EXP = OUT = ROOT / "runs" / "p4m-smoke"
        args.genomes = args.genomes or 8
        args.device = "cpu"
        args.per_chunk = args.genomes
    elif args.per_chunk != PLAN["per_chunk"]:
        raise SystemExit(f"formal lesions keep 03's composition: --per-chunk {PLAN['per_chunk']}")
    {"tradeoff": cmd_tradeoff, "tails": cmd_tails, "graphs": cmd_graphs, "lesions": cmd_lesions,
     "synapses": cmd_synapses, "decay": cmd_decay, "weights": cmd_weights}[args.command](args)


def export_compute_record(out: Path, exp: Path) -> None:
    """After the accounting has written this attempt (whether it succeeded or stopped), copy the
    aggregate beside the results (Astra, Fable, review v2)."""
    agg = out / "compute.json"
    if (out / "compute").exists():
        acct.write_aggregate(out / "compute", agg)
    if agg.exists():
        write(exp / "compute-record.json", json.loads(agg.read_text(encoding="utf-8")))


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("p4m-smoke" if smoke else "p4m")
    try:
        run_script(main, out_default=str(out_dir), default="probe", name="p4m")
    finally:
        if not smoke:
            export_compute_record(out_dir, EXP)
