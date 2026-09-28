"""03m: an exploratory look at what drives 03's P4, history dependence (experiments/03m-p4-mechanism/PLAN.md).

    python scripts/p4m.py tradeoff                  # no simulation: 03's and 03r's committed supplements
    python scripts/p4m.py tails --measures DIR      # no simulation: 03's local per-genome measures
    python scripts/p4m.py lesions --device cuda     # N2 with each neuron, and each bilateral pair, deleted
    python scripts/p4m.py synapses --device cuda    # N2 with gaps or chemical synapses off, or weights permuted by type
    python scripts/p4m.py decay --device cuda       # 300 ticks after the ramp: N2 and 16 graphs per ensemble
    python scripts/p4m.py weights --device cuda     # N2's wiring with 64 permutations of its weights, two designs
    python scripts/p4m.py <command> --smoke         # tiny sizes, the CPU, runs/p4m-smoke/

Exploratory: the analyses are declared in PLAN.md before they run, but nothing here is confirmatory.
Every measurement reuses 03's own code and inputs (`scripts/exp03.py`, instance "03"): its stimulus
bank, its probe genomes (2 048, seeded per graph as 03 seeded them) and its P4 definition, the mean
|rising - falling| raw turn at the ramp's end over the mean |steady contrast|. Each simulating
command first reproduces 03's committed N2 numerator and denominator, in 03's batch composition
(2 048 strains, one row each), and every later batch keeps that composition. A cap is checked
before every batch; results are written as they complete.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
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
ENSEMBLES = ("SH", "SH-route", "SH-class", "SH-mirror", "SH-recip")
SUPPLEMENTS = {"03": ROOT / "experiments" / "03-generation0" / "supplement.json",
               "03r": ROOT / "experiments" / "03r-replication" / "supplement.json"}
DEN_FLOOR = 1e-4  # 03's exclusion floor for a P4 denominator
PLAN = {
    "genomes": 2048,  # 03's P4 probe set
    "per_chunk": 2048,  # strains per batch: one probe set at a time, 03's composition (T1, D091)
    "reproduce_tolerance": 1e-6,  # relative, on N2's numerator and denominator against 03's supplement
    "cap_gpu_hours": 4.0,  # every command together, counted by the accounting across attempts
    "lead": {"p4_below": "the pooled 95th percentile of 03's five ensembles",
             "response_below": "the pooled maximum of 03's five ensembles"},
    "follow_up_top": 5,  # single deletions with the largest P4 drop: chemical-only and gap-only edge deletions
    "decay": {"after": 300, "every": 10, "extra_ticks": [5], "graphs_per_ensemble": 16,
              "remaining_fraction": 0.10, "start_floor": 1e-3, "settle_tolerance": 1e-4, "settle_window": 10},
    "weights": {"permutations": 64, "seed_base": 100},
    "by_type_seeds": list(range(100, 108)),
}
SMOKE = False


# ----------------------------------------------------------------------------- shared

def write(path: Path, doc) -> None:
    reg.write_json(path, doc, atomic=True)


def stamp() -> dict:
    p = reg.provenance(["wormwars", "scripts", "configs", "experiments/03m-p4-mechanism/PLAN.md"])
    return {k: p[k] for k in ("git_commit", "branch", "dirty", "python", "numpy", "torch", "cuda", "gpu",
                              "connectome_cache_sha256")}


def clock() -> reg.CapClock:
    if (OUT / "compute").exists():
        acct.write_aggregate(OUT / "compute", OUT / "compute.json")
    return reg.CapClock(PLAN["cap_gpu_hours"], OUT / "compute.json")


def supplement(instance="03") -> dict:
    return json.loads(SUPPLEMENTS[instance].read_text(encoding="utf-8"))["per_graph"]


def ensemble_rows(pg: dict, ens: str) -> list[dict]:
    return [v for k, v in pg.items() if k.startswith(ens + "-") and k[len(ens) + 1:].isdigit()]


def pooled(pg: dict) -> tuple[np.ndarray, np.ndarray]:
    rows = [r for e in ENSEMBLES for r in ensemble_rows(pg, e)]
    return np.array([r["P4_turn"] for r in rows]), np.array([r["P4_turn_denominator"] for r in rows])


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
    """Relative to 03's pooled ensembles: whether the deletion brings P4 below the pooled 95th
    percentile, the response below the pooled maximum, both, or neither. None if invalid."""
    if not r["valid"]:
        return None
    p4, den = pooled(pg)
    lo_p4, lo_den = r["P4"] < np.quantile(p4, 0.95), r["denominator"] < den.max()
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
    num = float(np.abs(h["raw_turn"]["final"]).mean())
    den = float(np.abs(h["raw_turn"]["steady_contrast"]).mean())
    valid = bool(math.isfinite(num) and math.isfinite(den) and den >= DEN_FLOOR)
    return {"numerator": num, "denominator": den, "P4": num / den if valid else None, "valid": valid}


def reproduce_n2(con, bank, iface, device) -> dict:
    """03's N2 numerator and denominator, recomputed in 03's composition; refuses to go on if they
    differ. Smoke runs a token check only."""
    g, cfg = probe_genomes(con, "N2", device, n=8 if SMOKE else None)
    got = p4_of(M.history(g, cfg, iface, bank))
    want = supplement("03")["N2"]
    rel = {k: abs(got[k] - want[f"P4_turn_{k}"]) / abs(want[f"P4_turn_{k}"]) for k in ("numerator", "denominator")}
    ok = all(v <= PLAN["reproduce_tolerance"] for v in rel.values())
    if not ok and not SMOKE:
        raise SystemExit(f"N2's P4 terms do not reproduce 03's (relative differences {rel}); stopping")
    return {"got": got, "03": {k: want[f"P4_turn_{k}"] for k in ("numerator", "denominator")},
            "relative_difference": rel, "reproduced": ok}


def require_formal_size(args) -> None:
    if not SMOKE and args.genomes not in (None, PLAN["genomes"]):
        raise SystemExit(f"formal outputs use 03's {PLAN['genomes']} probe genomes, not {args.genomes}")


def finish(name: str, doc: dict) -> None:
    write(EXP / f"{name}.json", doc)
    agg = OUT / "compute.json"
    if (OUT / "compute").exists():
        acct.write_aggregate(OUT / "compute", agg)
    if agg.exists() and not SMOKE:
        write(EXP / "compute-record.json", json.loads(agg.read_text(encoding="utf-8")))


# ----------------------------------------------------------------------------- Q1, no simulation

def cmd_tradeoff(args):
    """Within each ensemble: Spearman(denominator, P4); the scaling of the numerator with the
    denominator (a log-log slope below 1 lowers the ratio mechanically); P4 against the separately
    measured common turn response; N2's position; and N2's residual from a linear fit of P4 on
    log(denominator), a model-dependent description, not a significance score."""
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
        print(inst, {e: (round(r["spearman_denominator_P4"], 2), round(r["loglog_slope_numerator_on_denominator"], 2),
                         r["graphs_with_P4_at_or_above_N2"]) for e, r in d["ensembles"].items()})


def cmd_tails(args):
    """From 03's local per-genome measures (not committed): the split-half reliability of P4 over
    graphs (even against odd genomes), and how concentrated each graph's numerator is in its top 5%
    of genomes, for N2 against each ensemble (Fable, review v1)."""
    d = Path(args.measures)
    names = ["N2"] + [f"{e}-{X.SEED_BASE[e] + i}" for e in ENSEMBLES for i in range(X.N_PER[e])]
    rows = {}
    for n in names:
        path = d / f"{n}.json"
        if not path.exists():
            continue
        m = json.loads(path.read_text(encoding="utf-8"))
        h = m["history"]["raw_turn"]
        f, s = np.abs(np.asarray(h["final"])), np.abs(np.asarray(h["steady_contrast"]))
        top = np.sort(f)[::-1]
        k = max(1, len(f) // 20)
        rows[n] = {"P4_even": float(f[0::2].mean() / s[0::2].mean()), "P4_odd": float(f[1::2].mean() / s[1::2].mean()),
                   "top5pct_share_of_numerator": float(top[:k].sum() / max(f.sum(), 1e-30)),
                   "top5pct_share_of_denominator": float(np.sort(s)[::-1][:k].sum() / max(s.sum(), 1e-30))}
    out = {"N2": rows.get("N2"), "ensembles": {}}
    for e in ENSEMBLES:
        r = [v for k, v in rows.items() if k.startswith(e + "-")]
        if not r:
            continue
        ev, od = np.array([x["P4_even"] for x in r]), np.array([x["P4_odd"] for x in r])
        t = np.array([x["top5pct_share_of_numerator"] for x in r])
        out["ensembles"][e] = {"graphs": len(r), "split_half_correlation": float(np.corrcoef(ev, od)[0, 1]),
                               "top5pct_share_median": float(np.median(t)), "top5pct_share_max": float(t.max())}
    write(EXP / "tails.json", {"what": "exploratory (PLAN.md Q1b); no simulation; from 03's local per-genome measures",
                               "stamp": stamp(), **out})
    print(out["N2"], {e: (round(v["split_half_correlation"], 3), round(v["top5pct_share_median"], 3))
                      for e, v in out["ensembles"].items()})


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


def cmd_lesions(args):
    require_formal_size(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    g, cfg = probe_genomes(con, "N2", args.device, n=args.genomes)
    turn = set(iface.turn_plus) | set(iface.turn_minus)  # only the turn read-out: P4 reads turn alone
    names = list(con.names)
    singles = [[i] for i in range(len(names)) if i not in turn]
    prs = {k: v for k, v in pairs(names).items() if not set(v) & turn}
    if SMOKE:
        singles, prs = singles[:3], dict(list(prs.items())[:2])
    entries = [("intact", [])] + [(names[d[0]], d) for d in singles] + [(f"pair {k}", v) for k, v in prs.items()]
    pg = supplement("03")
    p4_all, den_all = pooled(pg)
    b = np.polyfit(np.log(den_all), p4_all, 1)
    t0 = time.perf_counter()
    base = {"what": "exploratory (PLAN.md Q2)", "plan": PLAN, "stamp": stamp(), "reproduce_N2": repro,
            "genomes": g.n_strains, "per_chunk": args.per_chunk,
            "composition": [args.per_chunk, 1, "direct brain steps, one row per strain"],
            "excluded_turn_readout_neurons": sorted(names[i] for i in turn)}

    def row(label, dl, r):
        out = {"deleted": label, **public(r), "null_position": null_position(r, pg), "class": lead_class(r, pg)}
        if r["valid"]:
            out["residual_from_pooled_trend"] = float(r["P4"] - np.polyval(b, np.log(r["denominator"])))
        if len(dl) == 1:
            out["degree"] = degrees(con, dl[0])
        return out

    def partial(results):
        write(EXP / "lesions-partial.json", {**base, "rows": [row(lbl, dl, r) for (lbl, dl), r in zip(entries, results)]})

    with acct.category("probe"):
        res = history_in_chunks(g, cfg, iface, bank, [d for _, d in entries], args.per_chunk, cap.check, partial)
    intact = res[0]
    if not SMOKE and (intact["numerator"], intact["denominator"]) != (repro["got"]["numerator"], repro["got"]["denominator"]):
        raise SystemExit("the empty deletion does not reproduce the intact brain in the same composition")
    rows = [row(lbl, dl, r) for (lbl, dl), r in zip(entries, res)]
    # follow-up: the singles with the largest P4 drop, by synapse type
    valid_singles = [(lbl, dl, r) for (lbl, dl), r in zip(entries[1:1 + len(singles)], res[1:1 + len(singles)]) if r["valid"]]
    top = sorted(valid_singles, key=lambda x: x[2]["P4"])[:PLAN["follow_up_top"]]
    follow = {}
    with acct.category("probe"):
        for kind in ("chemical", "gap"):
            rr = history_in_chunks(g, cfg, iface, bank, [dl for _, dl, _ in top], args.per_chunk, cap.check, kind=kind)
            follow[kind] = [row(lbl, dl, r) for (lbl, dl, _), r in zip(top, rr)]
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "lesions-per-genome.npz", labels=np.array([lbl for lbl, _ in entries]),
                        final=np.stack([r["_final"] for r in res]), steady=np.stack([r["_steady"] for r in res]))
    finish("lesions", {**base, "rows": rows, "follow_up_by_synapse_type": follow,
                       "classes": {c: [r["deleted"] for r in rows if r["class"] == c]
                                   for c in ("both", "P4 only", "response only")},
                       "seconds": time.perf_counter() - t0})
    (EXP / "lesions-partial.json").unlink(missing_ok=True)
    for r in sorted([r for r in rows if r["valid"]], key=lambda r: r["P4"])[:8]:
        print(f"{r['deleted']:10s} P4 {r['P4']:.3f} den {r['denominator']:.4f} {r['class']}")


# ----------------------------------------------------------------------------- Q3 synapse types

def cmd_synapses(args):
    """N2 with gap junctions off, chemical synapses off, and both off; and with only the chemical, or
    only the gap, weight magnitudes permuted among existing edges, over 8 seeds, paired with N2's
    genome draws (signs, biases and time constants unchanged)."""
    require_formal_size(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    g, cfg = probe_genomes(con, "N2", args.device, n=args.genomes)
    pg = supplement("03")
    conds = {"intact": g, "gap junctions off": g.with_params(g=torch.zeros_like(g.g)),
             "chemical off": g.with_params(w=torch.zeros_like(g.w)),
             "both off": g.with_params(w=torch.zeros_like(g.w), g=torch.zeros_like(g.g))}
    rows = {}
    with acct.category("probe"):
        for k, gg in conds.items():
            cap.check()
            rows[k] = p4_of(M.history(gg, cfg, iface, bank))
        for which, field in (("chemical permuted", "init_chem_magnitude"), ("gaps permuted", "init_gap_magnitude")):
            for sd in PLAN["by_type_seeds"][:2 if SMOKE else None]:
                cap.check()
                c = cfg.copy()
                setattr(c.brain, field, "permuted")
                c.brain.init_permutation_seed = sd
                pgen = torch.Generator(device=args.device).manual_seed(X._gseed("N2") + 1)
                gm = Genome.random(g.spec, c.brain, g.n_strains, generator=pgen, device=args.device)
                rows[f"{which}, seed {sd}"] = p4_of(M.history(gm, c, iface, bank))
    for r in rows.values():
        r["null_position"] = null_position(r, pg)
        r["class"] = lead_class(r, pg)
    finish("synapses", {"what": "exploratory (PLAN.md Q3)", "plan": PLAN, "stamp": stamp(), "reproduce_N2": repro,
                        "genomes": g.n_strains, "conditions": rows})
    print({k: (None if v["P4"] is None else round(v["P4"], 3), round(v["denominator"], 4)) for k, v in rows.items()})


# ----------------------------------------------------------------------------- Q4 decay

def history_full(genome: Genome, cfg, iface, bank, after: int, every: int, extra=(5,), window=10) -> dict:
    """The same stimulus as `measures.history`, followed for `after` ticks of the final input.
    Returns the signed rising-minus-falling raw turn [ticks, genomes] at tick 0 (the ramp's end),
    the `extra` ticks and every `every` ticks; the steady contrast; the largest state change over
    the last `window` ticks of each hold and of each trajectory's end (settling); and the mean
    tanh slope of the turn read-out neurons at the holds' and the ramp's end (saturation)."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    food = (bank["food_left"] + bank["food_right"]) / 2
    at = lambda lvl: M._current(iface, cfg, dict(bank, food_left=lvl, food_right=lvl), n, s, dev)  # noqa: E731
    turn_idx = list(iface.turn_plus) + list(iface.turn_minus)
    ticks = sorted({0, *extra, *range(every, after + 1, every)})
    res = {}
    for name, start in (("rising", 0.25 * food), ("falling", 1.75 * food)):
        v = brain.initial_state(1)
        for t in range(100):
            if t == 100 - window:
                v_hold = v.clone()
            v = brain.step(v, at(start))
        hold_change = (v - v_hold).abs().amax(dim=(1, 2))
        steady = M._readout(iface, cfg, v)[:, 1]
        slope_hold = (1 - torch.tanh(v[:, 0, turn_idx]) ** 2).mean(-1)
        for t in range(10):
            v = brain.step(v, at(start + (food - start) * (t + 1) / 10))
        slope_ramp = (1 - torch.tanh(v[:, 0, turn_idx]) ** 2).mean(-1)
        rows = {0: M._readout(iface, cfg, v)[:, 1]}
        for t in range(1, after + 1):
            if t == after - window:
                v_end = v.clone()
            v = brain.step(v, at(food))
            if t in ticks:
                rows[t] = M._readout(iface, cfg, v)[:, 1]
        end_change = (v - v_end).abs().amax(dim=(1, 2))
        res[name] = {"curve": torch.stack([rows[t] for t in ticks]).cpu().numpy(), "steady": steady.cpu().numpy(),
                     "hold_change": hold_change.cpu().numpy(), "end_change": end_change.cpu().numpy(),
                     "slope_hold": slope_hold.cpu().numpy(), "slope_ramp": slope_ramp.cpu().numpy()}
    return {"ticks": ticks, "diff": res["rising"]["curve"] - res["falling"]["curve"],
            "steady_contrast": res["falling"]["steady"] - res["rising"]["steady"],
            "hold_change": np.maximum(res["rising"]["hold_change"], res["falling"]["hold_change"]),
            "end_change": np.maximum(res["rising"]["end_change"], res["falling"]["end_change"]),
            "slope_hold": (res["rising"]["slope_hold"] + res["falling"]["slope_hold"]) / 2,
            "slope_ramp": (res["rising"]["slope_ramp"] + res["falling"]["slope_ramp"]) / 2}


def decay_summary(h: dict) -> dict:
    D = PLAN["decay"]
    a = np.abs(h["diff"])
    start, end = a[0], a[-1]
    eligible = start >= D["start_floor"]
    settled = h["end_change"] < D["settle_tolerance"]
    remaining = eligible & (end > D["remaining_fraction"] * start)
    f = np.abs(h["diff"][0])
    k = max(1, len(f) // 20)
    return {"ticks": h["ticks"], "mean_abs_difference": a.mean(axis=1).tolist(),
            "ratio_of_means_at_end": float(a[-1].mean() / max(a[0].mean(), 1e-30)),
            "share_eligible": float(eligible.mean()),
            "share_of_eligible_with_separation_remaining": float(remaining.sum() / max(eligible.sum(), 1)),
            "share_settled_at_end": float(settled.mean()),
            "share_of_remaining_that_settled": float((remaining & settled).sum() / max(remaining.sum(), 1)),
            "share_holds_settled": float((h["hold_change"] < D["settle_tolerance"]).mean()),
            "top5pct_share_of_numerator": float(np.sort(f)[::-1][:k].sum() / max(f.sum(), 1e-30)),
            "mean_turn_readout_tanh_slope_hold": float(h["slope_hold"].mean()),
            "mean_turn_readout_tanh_slope_ramp": float(h["slope_ramp"].mean()),
            "numerator": float(f.mean()), "denominator": float(np.abs(h["steady_contrast"]).mean())}


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


def cmd_decay(args):
    """Q4 on N2 and the first 16 graphs of each ensemble; also each panel graph's P4 with gap
    junctions off (Fable, review v1), so Q3's gaps-off N2 has a matched null panel."""
    require_formal_size(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    D = PLAN["decay"]
    k = 2 if SMOKE else D["graphs_per_ensemble"]
    names = ["N2"] + [f"{e}-{X.SEED_BASE[e] + i}" for e in ENSEMBLES for i in range(k)]
    rebuilt = ensure_graphs(names)
    pg = supplement("03")
    out, curves = {}, {}
    base = {"what": "exploratory (PLAN.md Q4)", "plan": PLAN, "stamp": stamp(), "reproduce_N2": repro,
            "graphs_rebuilt": rebuilt}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for name in names:
            cap.check()
            g, cfg = probe_genomes(con, name, args.device, n=args.genomes)
            h = history_full(g, cfg, iface, bank, D["after"], D["every"], D["extra_ticks"], D["settle_window"])
            s = decay_summary(h)
            ref = pg.get(name, {})
            if "P4_turn_numerator" in ref:  # tick 0 is 03's numerator: a per-graph reproduction check
                s["relative_difference_from_03_numerator"] = abs(s["numerator"] - ref["P4_turn_numerator"]) / ref["P4_turn_numerator"]
            s["gaps_off"] = p4_of(M.history(g.with_params(g=torch.zeros_like(g.g)), cfg, iface, bank))
            out[name] = s
            curves[name] = h["diff"].astype(np.float32)
            write(EXP / "decay-partial.json", {**base, "graphs": out})
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT / "decay-per-genome.npz", **{k.replace("-", "_"): v for k, v in curves.items()},
                        ticks=np.array(out[names[0]]["ticks"]))
    finish("decay", {**base, "graphs": out, "seconds": time.perf_counter() - t0})
    (EXP / "decay-partial.json").unlink(missing_ok=True)
    for n in names[:1] + names[1::k]:
        o = out[n]
        print(n, round(o["ratio_of_means_at_end"], 3), round(o["share_of_eligible_with_separation_remaining"], 3),
              round(o["share_settled_at_end"], 3))


# ----------------------------------------------------------------------------- Q5 weights

def cmd_weights(args):
    """N2's wiring with its anatomical weight magnitudes permuted among its edges, 64 seeds, in two
    designs: independent genome draws per permutation, as 03 drew its N2perm graphs; and paired,
    N2's own genome draws with only the magnitudes permuted (Astra, Fable, review v1)."""
    require_formal_size(args)
    cap = clock()
    cap.check()
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    W = PLAN["weights"]
    seeds = [W["seed_base"] + i for i in range(2 if SMOKE else W["permutations"])]
    pg = supplement("03")
    rows = {"independent": {}, "paired": {}}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for sd in seeds:
            name = f"N2perm{sd}"
            for design, seed_name in (("independent", name), ("paired", "N2")):
                cap.check()
                g, cfg = probe_genomes(con, name, args.device, graph=con, n=args.genomes, seed_name=seed_name)
                r = p4_of(M.history(g, cfg, iface, bank))
                rows[design][name] = {**r, "null_position": null_position(r, pg), "class": lead_class(r, pg)}
    n2 = pg["N2"]
    p4_null, den_null = pooled(pg)
    summary = {}
    for design, rr in rows.items():
        v = [r for r in rr.values() if r["valid"]]
        p4 = np.array([r["P4"] for r in v])
        den = np.array([r["denominator"] for r in v])
        summary[design] = {"valid": len(v), "invalid": len(rr) - len(v),
                           "P4_median": float(np.median(p4)) if len(v) else None,
                           "P4_share_below_N2": float((p4 < n2["P4_turn"]).mean()) if len(v) else None,
                           "P4_share_above_pooled_null_95th": float((p4 > np.quantile(p4_null, 0.95)).mean()) if len(v) else None,
                           "denominator_median": float(np.median(den)) if len(v) else None,
                           "denominator_share_below_N2": float((den < n2["P4_turn_denominator"]).mean()) if len(v) else None,
                           "denominator_share_above_pooled_null_max": float((den > den_null.max()).mean()) if len(v) else None,
                           "per_ensemble": {e: {"P4_share_above_ensemble_95th": float((p4 > np.quantile(
                               [x["P4_turn"] for x in ensemble_rows(pg, e)], 0.95)).mean()) if len(v) else None}
                               for e in ENSEMBLES}}
    finish("weights", {"what": "exploratory (PLAN.md Q5)", "plan": PLAN, "stamp": stamp(), "reproduce_N2": repro,
                       "summary": summary, "permutations": rows, "seconds": time.perf_counter() - t0})
    print(json.dumps({d: {k: v for k, v in s.items() if k != "per_ensemble"} for d, s in summary.items()}, indent=1))


# ----------------------------------------------------------------------------- main

def main():
    global EXP, OUT, SMOKE
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["tradeoff", "tails", "lesions", "synapses", "decay", "weights"])
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
    {"tradeoff": cmd_tradeoff, "tails": cmd_tails, "lesions": cmd_lesions, "synapses": cmd_synapses,
     "decay": cmd_decay, "weights": cmd_weights}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("p4m-smoke" if smoke else "p4m")), default="probe", name="p4m")
