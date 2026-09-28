"""03m: an exploratory look at what drives 03's P4, history dependence (experiments/03m-p4-mechanism/PLAN.md).

    python scripts/p4m.py tradeoff                 # no simulation: 03's and 03r's committed supplements
    python scripts/p4m.py lesions --device cuda    # N2 with each neuron, and each bilateral pair, deleted
    python scripts/p4m.py synapses --device cuda   # N2 with gap junctions off; weights permuted by type
    python scripts/p4m.py decay --device cuda      # a 300-tick window after the ramp: N2 and 16 graphs per ensemble
    python scripts/p4m.py weights --device cuda    # N2's wiring with 64 permutations of its weights
    python scripts/p4m.py <command> --smoke        # tiny sizes, the CPU, runs/p4m-smoke/

Exploratory: the analyses are declared in PLAN.md before they run, but nothing here is confirmatory.
Every measurement reuses 03's own code and inputs (`scripts/exp03.py`, instance "03"): its stimulus
bank, its N2 probe genomes (2 048, seeded per graph as 03 seeded them) and its P4 definition, the mean
|rising - falling| raw turn at the ramp's end over the mean |steady contrast|. The first thing each
simulating command does is reproduce 03's committed N2 numerator and denominator.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
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
PLAN = {
    "genomes": 2048,  # 03's P4 probe set
    "reproduce_tolerance": 1e-6,  # relative, on N2's numerator and denominator against 03's supplement
    "decay": {"after": 300, "every": 10, "graphs_per_ensemble": 16, "persist_fraction": 0.10},
    "weights": {"permutations": 64, "seed_base": 100},
    "null_reference": "03's five ensembles (per-graph values in its supplement)",
}
SMOKE = False


# ----------------------------------------------------------------------------- shared

def write(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(doc, indent=1))
        f.write("\n")


def supplement(instance="03") -> dict:
    return json.loads(SUPPLEMENTS[instance].read_text(encoding="utf-8"))["per_graph"]


def ensemble_rows(pg: dict, ens: str) -> list[dict]:
    return [v for k, v in pg.items() if k.startswith(ens + "-") and k[len(ens) + 1:].isdigit()]


def null_position(p4: float, den: float, pg: dict) -> dict:
    """Where a (P4, denominator) pair sits in each of 03's ensembles: the share of graphs below it."""
    out = {}
    for ens in ENSEMBLES:
        rows = ensemble_rows(pg, ens)
        a = np.array([r["P4_turn"] for r in rows])
        d = np.array([r["P4_turn_denominator"] for r in rows])
        out[ens] = {"P4_share_below": float((a < p4).mean()), "denominator_share_below": float((d < den).mean())}
    return out


def setup(device):
    con = load_connectome()
    bank = json.loads(X.PILOT.read_text(encoding="utf-8"))["bank"]
    remap_sets = json.loads(X.INPUT_FILES["remaps.json"].read_text(encoding="utf-8"))["sets"]
    iface = X.grid.interface_for(con, "M0", remap_sets)
    return con, bank, iface


def probe_genomes(con, name: str, device, graph=None, n=None) -> tuple[Genome, object]:
    """03's P4 probe genomes for `name`, exactly as `measure_graph` drew them."""
    graph = graph if graph is not None else X._load_graph(con, name)
    spec = BrainSpec.from_connectome(graph, device=device)
    cfg = X.grid.brain_config_for_graph(X.grid.task_config(X.Config(), "T1"), name)
    pg = torch.Generator(device=device).manual_seed(X._gseed(name) + 1)
    g = Genome.random(spec, cfg.brain, n or PLAN["genomes"], generator=pg, device=device)
    return g, cfg


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


def p4_of(h: dict) -> dict:
    num = float(np.abs(h["raw_turn"]["final"]).mean())
    den = float(np.abs(h["raw_turn"]["steady_contrast"]).mean())
    return {"numerator": num, "denominator": den, "P4": num / den if den >= 1e-4 else float("nan")}


def reproduce_n2(con, bank, iface, device) -> dict:
    """03's N2 numerator and denominator, recomputed; refuses to go on if they differ."""
    g, cfg = probe_genomes(con, "N2", device, n=8 if SMOKE else None)  # smoke: a token check only
    got = p4_of(M.history(g, cfg, iface, bank))
    want = supplement("03")["N2"]
    rel = {k: abs(got[k] - want[f"P4_turn_{k}"]) / abs(want[f"P4_turn_{k}"]) for k in ("numerator", "denominator")}
    ok = all(v <= PLAN["reproduce_tolerance"] for v in rel.values())
    if not ok and not SMOKE:
        raise SystemExit(f"N2's P4 terms do not reproduce 03's (relative differences {rel}); stopping")
    return {"got": got, "03": {k: want[f"P4_turn_{k}"] for k in ("numerator", "denominator")},
            "relative_difference": rel, "reproduced": ok}


# ----------------------------------------------------------------------------- tradeoff (no simulation)

def cmd_tradeoff(args):
    """Within each ensemble: Spearman(denominator, P4); N2's denominator against the ensemble; and N2's
    residual from a linear fit of P4 on log(denominator), in residual standard deviations. The last is
    an extrapolation beyond the ensembles' range (the outside review's reading, checked)."""
    out = {}
    for inst in SUPPLEMENTS:
        pg = supplement(inst)
        n2 = pg["N2"]
        rows_out = {}
        for ens in ENSEMBLES:
            rows = ensemble_rows(pg, ens)
            p4 = np.array([r["P4_turn"] for r in rows])
            den = np.array([r["P4_turn_denominator"] for r in rows])
            b = np.polyfit(np.log(den), p4, 1)
            resid = p4 - np.polyval(b, np.log(den))
            pred = float(np.polyval(b, np.log(n2["P4_turn_denominator"])))
            rows_out[ens] = {
                "graphs": len(rows), "spearman_denominator_P4": float(spearmanr(den, p4).statistic),
                "N2_denominator_over_median": float(n2["P4_turn_denominator"] / np.median(den)),
                "N2_denominator_over_max": float(n2["P4_turn_denominator"] / den.max()),
                "trend_at_N2": pred, "N2_residual_in_sd": float((n2["P4_turn"] - pred) / resid.std()),
                "N2_denominator_beyond_range": bool(n2["P4_turn_denominator"] > den.max())}
        perms = {k: {"P4": v["P4_turn"], "denominator": v["P4_turn_denominator"],
                     "denominator_over_SH_median": v["P4_turn_denominator"]
                     / float(np.median([r["P4_turn_denominator"] for r in ensemble_rows(pg, "SH")]))}
                 for k, v in pg.items() if k.startswith("N2perm") or k == "N2-rev"}
        out[inst] = {"N2": {"P4": n2["P4_turn"], "denominator": n2["P4_turn_denominator"]}, "ensembles": rows_out,
                     "N2_variants": perms}
    write(EXP / "tradeoff.json", {"what": "exploratory (PLAN.md Q1); no simulation", **out})
    for inst, d in out.items():
        print(inst, {e: (round(r["spearman_denominator_P4"], 2), round(r["N2_residual_in_sd"], 1))
                     for e, r in d["ensembles"].items()})


# ----------------------------------------------------------------------------- lesions

def pairs(names: list[str]) -> dict[str, list[int]]:
    """Bilateral pairs by name: XXXL with XXXR (for example RIAL, RIAR -> RIA)."""
    idx = {n: i for i, n in enumerate(names)}
    out = {}
    for n, i in idx.items():
        if n.endswith("L") and n[:-1] + "R" in idx:
            out[n[:-1]] = [i, idx[n[:-1] + "R"]]
    return out


def history_in_chunks(g: Genome, cfg, iface, bank, deletions: list[list[int]], per_chunk: int) -> list[dict]:
    """P4 terms of the probe genomes under each deletion list: every deletion applied to all genomes,
    in chunks of whole deletions."""
    n = g.n_strains
    out = []
    step = max(1, per_chunk // n)
    for lo in range(0, len(deletions), step):
        batch = deletions[lo:lo + step]
        big = Genome.cat([g] * len(batch))
        lists = [d for d in batch for _ in range(n)]
        h = M.history(delete_neurons(big, lists), cfg, iface, bank)
        for j in range(len(batch)):
            sl = slice(j * n, (j + 1) * n)
            out.append(p4_of({"raw_turn": {k: v[sl] for k, v in h["raw_turn"].items()}}))
    return out


def cmd_lesions(args):
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    g, cfg = probe_genomes(con, "N2", args.device, n=args.genomes)
    readout = set(iface.turn_plus) | set(iface.turn_minus) | set(iface.forward_plus) | set(iface.forward_minus)
    names = list(con.names)
    singles = [[i] for i in range(len(names)) if i not in readout]
    prs = {k: v for k, v in pairs(names).items() if not set(v) & readout}
    if SMOKE:
        singles, prs = singles[:3], dict(list(prs.items())[:2])
    t0 = time.perf_counter()
    with acct.category("probe"):
        rs = history_in_chunks(g, cfg, iface, bank, singles, args.per_chunk)
        rp = history_in_chunks(g, cfg, iface, bank, list(prs.values()), args.per_chunk)
    pg = supplement("03")
    rows = [{"deleted": names[d[0]], **r, "null_position": null_position(r["P4"], r["denominator"], pg)}
            for d, r in zip(singles, rs)]
    prow = [{"deleted": k, **r, "null_position": null_position(r["P4"], r["denominator"], pg)}
            for k, r in zip(prs, rp)]
    write(EXP / "lesions.json", {"what": "exploratory (PLAN.md Q2)", "plan": PLAN, "reproduce_N2": repro,
                                 "genomes": g.n_strains, "excluded_readout_neurons": sorted(names[i] for i in readout),
                                 "singles": rows, "pairs": prow, "seconds": time.perf_counter() - t0})
    for r in sorted(prow, key=lambda r: r["P4"])[:8]:
        print(f"{r['deleted']:6s} P4 {r['P4']:.3f} den {r['denominator']:.4f}")


# ----------------------------------------------------------------------------- synapse types

def cmd_synapses(args):
    """N2 with gap junctions off; and N2 with only the chemical, or only the gap, weight magnitudes
    permuted among existing edges (seed 1), so wiring stays and weight placement changes by type."""
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    g, cfg = probe_genomes(con, "N2", args.device, n=args.genomes)
    pg = supplement("03")
    rows = {"intact": p4_of(M.history(g, cfg, iface, bank)),
            "gap junctions off": p4_of(M.history(g.with_params(g=torch.zeros_like(g.g)), cfg, iface, bank))}
    for which, fields in (("chemical permuted", ("init_chem_magnitude",)), ("gaps permuted", ("init_gap_magnitude",))):
        c = cfg.copy()
        for f in fields:
            setattr(c.brain, f, "permuted")
        c.brain.init_permutation_seed = 1
        pgen = torch.Generator(device=args.device).manual_seed(X._gseed("N2") + 1)
        gm = Genome.random(g.spec, c.brain, g.n_strains, generator=pgen, device=args.device)
        rows[which] = p4_of(M.history(gm, c, iface, bank))
    for r in rows.values():
        r["null_position"] = null_position(r["P4"], r["denominator"], pg)
    write(EXP / "synapses.json", {"what": "exploratory (PLAN.md Q3)", "plan": PLAN, "reproduce_N2": repro,
                                  "genomes": g.n_strains, "conditions": rows})
    print({k: (round(v["P4"], 3), round(v["denominator"], 4)) for k, v in rows.items()})


# ----------------------------------------------------------------------------- decay

def history_curve(genome: Genome, cfg, iface, bank, after: int, every: int) -> np.ndarray:
    """[checkpoints, genomes]: rising minus falling raw turn at the ramp's end (t = 0) and every
    `every` ticks of the final input up to `after`. The same stimulus as `measures.history`."""
    brain = Brain(genome)
    s, n, dev = genome.n_strains, genome.spec.n, genome.device
    food = (bank["food_left"] + bank["food_right"]) / 2
    at = lambda lvl: M._current(iface, cfg, dict(bank, food_left=lvl, food_right=lvl), n, s, dev)  # noqa: E731
    traces = {}
    for name, start in (("rising", 0.25 * food), ("falling", 1.75 * food)):
        v = brain.initial_state(1)
        for _ in range(100):
            v = brain.step(v, at(start))
        for t in range(10):
            v = brain.step(v, at(start + (food - start) * (t + 1) / 10))
        rows = [M._readout(iface, cfg, v)[:, 1]]
        for t in range(1, after + 1):
            v = brain.step(v, at(food))
            if t % every == 0:
                rows.append(M._readout(iface, cfg, v)[:, 1])
        traces[name] = torch.stack(rows).cpu().numpy()
    return traces["rising"] - traces["falling"]


def decay_summary(diff: np.ndarray, every: int, persist: float) -> dict:
    a = np.abs(diff)
    start = a[0]
    frac = a[-1] / np.maximum(start, 1e-12)
    mean_curve = a.mean(axis=1)
    return {"mean_abs_difference": mean_curve.round(8).tolist(), "ticks": [i * every for i in range(len(mean_curve))],
            "mean_fraction_left_at_end": float(mean_curve[-1] / max(mean_curve[0], 1e-12)),
            "share_of_genomes_persisting": float((frac > persist).mean())}


def cmd_decay(args):
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    D = PLAN["decay"]
    k = 2 if SMOKE else D["graphs_per_ensemble"]
    names = ["N2"] + [f"{e}-{X.SEED_BASE[e] + i}" for e in ENSEMBLES for i in range(k)]
    rebuilt = ensure_graphs(names)
    out = {}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for name in names:
            g, cfg = probe_genomes(con, name, args.device, n=args.genomes)
            d = history_curve(g, cfg, iface, bank, D["after"], D["every"])
            out[name] = decay_summary(d, D["every"], D["persist_fraction"])
    write(EXP / "decay.json", {"what": "exploratory (PLAN.md Q4)", "plan": PLAN, "reproduce_N2": repro,
                               "graphs_rebuilt": rebuilt,
                               "graphs": out, "seconds": time.perf_counter() - t0})
    for n in names[:1] + names[1::k]:
        print(n, round(out[n]["mean_fraction_left_at_end"], 3), round(out[n]["share_of_genomes_persisting"], 3))


# ----------------------------------------------------------------------------- weights

def cmd_weights(args):
    """N2's wiring with its anatomical weight magnitudes permuted among its edges, 64 seeds: does N2's
    P4, and its large denominator, come from the wiring or from where the weights sit?"""
    con, bank, iface = setup(args.device)
    repro = reproduce_n2(con, bank, iface, args.device)
    W = PLAN["weights"]
    seeds = [W["seed_base"] + i for i in range(2 if SMOKE else W["permutations"])]
    pg = supplement("03")
    rows = {}
    t0 = time.perf_counter()
    with acct.category("probe"):
        for sd in seeds:
            name = f"N2perm{sd}"
            g, cfg = probe_genomes(con, name, args.device, graph=con, n=args.genomes)
            r = p4_of(M.history(g, cfg, iface, bank))
            rows[name] = {**r, "null_position": null_position(r["P4"], r["denominator"], pg)}
    p4 = np.array([r["P4"] for r in rows.values()])
    den = np.array([r["denominator"] for r in rows.values()])
    n2 = pg["N2"]
    summary = {"P4_median": float(np.median(p4)), "P4_share_below_N2": float((p4 < n2["P4_turn"]).mean()),
               "denominator_median": float(np.median(den)),
               "denominator_share_below_N2": float((den < n2["P4_turn_denominator"]).mean())}
    write(EXP / "weights.json", {"what": "exploratory (PLAN.md Q5)", "plan": PLAN, "reproduce_N2": repro,
                                 "summary": summary, "permutations": rows, "seconds": time.perf_counter() - t0})
    print(summary)


# ----------------------------------------------------------------------------- main

def main():
    global EXP, OUT, SMOKE
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["tradeoff", "lesions", "synapses", "decay", "weights"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--genomes", type=int, default=None, help="probe genomes (default: 03's 2 048)")
    ap.add_argument("--per-chunk", type=int, default=16384, help="lesions: strains per batch")
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, the CPU allowed, runs/p4m-smoke/")
    args = ap.parse_args()
    if args.smoke:
        SMOKE = True
        EXP = OUT = ROOT / "runs" / "p4m-smoke"
        args.genomes = args.genomes or 8
    {"tradeoff": cmd_tradeoff, "lesions": cmd_lesions, "synapses": cmd_synapses, "decay": cmd_decay,
     "weights": cmd_weights}[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("p4m-smoke" if smoke else "p4m")), default="probe", name="p4m")
