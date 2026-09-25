"""Experiment 02's report, built from loaded inputs so a smoke test can run it on synthetic
records with the real diagnostics and calibration schema (Astra's decision review, point 9)."""

from __future__ import annotations

import numpy as np

from . import analysis as An
from .grid import MAIN, PROBE_IDS, TARGET_DRIVE, run_schedule

# D038: stereo ablations exist only on the stereo task; the history jitters and the constant
# food signal apply to both. food_mean on T0-M0 is the one primary mechanistic outcome.
CAPABILITY_PROBES = {"food_mean": ("T0",), "food_swapped": ("T0",), "mono": ("T0",),
                     "jitter1": ("T0", "T1"), "jitter3": ("T0", "T1"), "food_constant": ("T0", "T1")}
PRIMARY = ("food_mean", ("T0", "M0"))
SNAPSHOTS = ("g00", "g39")


def _cells(tasks):
    return [c for c in MAIN if c[0] in tasks]


def capability(records, champions, n_boot: int = An.N_BOOT) -> dict:
    """For every probe, snapshot and cell: N2's mean use, SH's mean use (equally weighted graph
    means) and their contrast Delta; per task, the mapping interaction of Delta; and the change
    of Delta from generation 0 to 39 (acquisition against starting advantage). All intervals
    come from the hierarchical bootstrap over whole unit vectors."""
    out = {}
    for probe, tasks in CAPABILITY_PROBES.items():
        res = {}
        for snap in SNAPSHOTS:
            n2, sh = An.units(An.attach_use(records, champions, probe, snap), f"use_{probe}_{snap}")
            if not n2 or not sh:
                continue
            stats = {}
            for c in _cells(tasks):
                name = f"{c[0]}-{c[1]}"
                stats[f"{name}/n2"] = lambda a, s, c=c: An._n2_mean(a, c)
                stats[f"{name}/sh"] = lambda a, s, c=c: An._sh_mean(s, c)
                stats[f"{name}/delta"] = lambda a, s, c=c: An.advantage(a, s, c)
            for t in tasks:
                stats[f"I/{t}"] = lambda a, s, t=t: An.interaction(a, s, t)
            b = An.paired_bootstrap_many(n2, sh, stats, n_boot)
            res[snap] = {"cells": {f"{c[0]}-{c[1]}": {k: b[f"{c[0]}-{c[1]}/{k}"] for k in ("n2", "sh", "delta")}
                                   for c in _cells(tasks)},
                         "interaction": {t: b[f"I/{t}"] for t in tasks}}
        # acquisition: Delta at generation 39 minus Delta at generation 0, per unit
        both = []
        for r in An.attach_use(An.attach_use(records, champions, probe, "g00"), champions, probe, "g39"):
            if f"use_{probe}_g00" in r and f"use_{probe}_g39" in r:
                both.append(dict(r, _acq=r[f"use_{probe}_g39"] - r[f"use_{probe}_g00"]))
        n2, sh = An.units(both, "_acq")
        if n2 and sh:
            res["acquisition"] = An.paired_bootstrap_many(
                n2, sh, {f"{c[0]}-{c[1]}": (lambda a, s, c=c: An.advantage(a, s, c)) for c in _cells(tasks)}, n_boot)
        out[probe] = res
    return out


def malformed_probes(champions) -> list[str]:
    """Probe entries whose scores cannot be paired with the real ones: wrong length or non-finite.
    attach_use skips them, and they are listed in the report."""
    bad = []
    for key, snaps in champions.items():
        for snap, v in snaps.items():
            sc = v.get("channels", {}).get("scores", {})
            real = np.asarray(sc.get("real", []), dtype=float)
            for probe, x in sc.items():
                x = np.asarray(x, dtype=float)
                if len(x) != len(PROBE_IDS) or len(real) != len(PROBE_IDS) or not np.isfinite(x).all():
                    bad.append(f"{key} {snap} {probe}")
    return bad


def primary_registered_units() -> dict:
    """The primary cell's registered records: every N2 run and every SH graph's run 0, with the
    seed each must carry. They are the schedule's first 16 batches (PREREGISTRATION section 4)."""
    probe, cell = PRIMARY
    return {r.key: r.run_seed for b in run_schedule() for r in b
            if (r.cell.task, r.cell.mapping) == cell and (r.graph == "N2" or (r.graph.startswith("SH") and r.run == 0))}


def primary_completeness(records, champions) -> list[str]:
    """Problems that withhold the primary verdict (Astra's pre-registration review and its
    confirmation pass, point 3): every registered unit present with its registered seed, and
    every present N2 or SH champion in the cell with finite primary scores on exactly the
    registered probe worlds and its run's seed. Empty means complete."""
    probe, cell = PRIMARY
    here = {r["key"]: r for r in records if (r["task"], r["mapping"]) == cell}
    problems = []
    for key, seed in primary_registered_units().items():
        if key not in here:
            problems.append(f"{key}: registered run missing")
        elif here[key].get("run_seed") != seed:
            problems.append(f"{key}: run seed {here[key].get('run_seed')} is not the registered {seed}")
    for key, r in here.items():
        if not (r["graph"] == "N2" or r["graph"].startswith("SH")):
            continue
        ch = champions.get(key, {}).get("g39", {}).get("channels")
        if ch is None:
            problems.append(f"{key}: no generation-39 probes")
            continue
        sc = ch.get("scores", {})
        ok = (ch.get("world_ids") == [int(i) for i in PROBE_IDS] and ch.get("probe_seed") == r.get("run_seed")
              and all(len(sc.get(k, [])) == len(PROBE_IDS) and np.isfinite(np.asarray(sc[k], dtype=float)).all()
                      for k in ("real", probe)))
        if not ok:
            problems.append(f"{key}: primary probe scores incomplete, non-finite or on the wrong worlds/seed")
    return problems


def primary(cap: dict, records, champions) -> dict:
    probe, cell = PRIMARY
    problems = primary_completeness(records, champions)
    c = cap.get(probe, {}).get("g39", {}).get("cells", {}).get(f"{cell[0]}-{cell[1]}")
    out = {"probe": probe, "cell": f"{cell[0]}-{cell[1]}", "complete": not problems, "problems": problems}
    if c is None:
        return dict(out, verdict="withheld")
    out.update(delta=c["delta"], n2_use=c["n2"], sh_use=c["sh"], n2_use_class=An.classify_use(c["n2"]),
               sh_use_class=An.classify_use(c["sh"]))
    out["verdict"] = An.prediction_verdict(c["delta"], c["n2"]) if not problems else "withheld"
    return out


def per_champion(records, champions) -> dict:
    """Every champion's own paired use of each capability, with its class, so individual graphs
    and runs are reported next to the group means."""
    out = {}
    for r in records:
        for snap in SNAPSHOTS:
            ch = champions.get(r["key"], {}).get(snap, {}).get("channels")
            if not ch:
                continue
            uses = {p: An.champion_use(ch, p) for p in CAPABILITY_PROBES if p in ch["scores"]}
            out.setdefault(r["key"], {})[snap] = {p: u for p, u in uses.items() if u is not None}
    return out


def sh_graphs_with_use(records, champions, probe: str, cell: tuple, snap: str = "g39") -> dict:
    """How many SH graphs show *detected* meaningful use under this procedure: per graph, the
    per-world difference averaged over its runs (the same probe worlds), with a bootstrap over
    worlds. It is conditional on the runs made, and a capable graph can stay inconclusive, so the
    count is a detection count, not a prevalence estimate (Astra's pre-registration review, 5)."""
    per = {}
    for r in records:
        if r["graph"].startswith("SH") and (r["task"], r["mapping"]) == cell:
            d = An.paired_diff(champions.get(r["key"], {}).get(snap, {}).get("channels"), probe)
            if d is not None:
                per.setdefault(r["graph"], []).append(d)
    out = {}
    for g, diffs in sorted(per.items()):
        b = An._boot_mean(np.mean(diffs, axis=0))
        out[g] = dict(b, cls=An.classify_use(b), runs=len(diffs))
    return {"per_graph": out, "detected_meaningful": sum(v["cls"] == "meaningful" for v in out.values()),
            "graphs": len(out)}


def build(raw_records, diagnostics, probes, calibration, sign_01b, n_boot: int = An.N_BOOT) -> dict:
    recs = An.normalise(raw_records, diagnostics)
    main_recs = [r for r in recs if r["task"] in ("T0", "T1")]
    out = {}
    for tag in ("norm_g00", "norm_g39"):
        n2, sh = An.units(main_recs, tag)
        stats = {"I_T0": lambda a, s: An.interaction(a, s, "T0"),
                 "I_T1": lambda a, s: An.interaction(a, s, "T1"),
                 "I_T1_minus_I_T0": An.task_contrast}
        for t, m in MAIN:
            stats[f"adv/{t}-{m}"] = lambda a, s, c=(t, m): An.advantage(a, s, c)
        b = An.paired_bootstrap_many(n2, sh, stats, n_boot)
        out[tag] = {
            "I_T0": b["I_T0"], "I_T1": b["I_T1"], "I_T1_minus_I_T0": b["I_T1_minus_I_T0"],
            "advantage": {f"{t}-{m}": b[f"adv/{t}-{m}"] for t, m in MAIN},
            "variance_T0": An.variance_components(sh, "T0"),
            "variance_T1": An.variance_components(sh, "T1"),
            "loo_T1": An.leave_one_graph_out(n2, sh, "T1"),
        }
    champs = probes["champions"]
    out["malformed_probes"] = malformed_probes(champs)
    cap = capability(main_recs, champs, n_boot)
    out["capability"] = cap
    out["primary"] = primary(cap, main_recs, champs)
    out["per_champion"] = per_champion(main_recs, champs)
    out["sh_graphs_with_stereo_use"] = sh_graphs_with_use(main_recs, champs, "food_mean", ("T0", "M0"))
    n2, sh = An.units(recs, "norm_g39")
    matched_adv = lambda a, s: float(np.mean([An.advantage(a, s, ("T1", m)) for m in An.MATCHED]))  # noqa: E731
    sh_matched = lambda s: float(np.mean([An._sh_mean(s, ("T1", m)) for m in An.MATCHED]))  # noqa: E731
    b = An.paired_bootstrap_many(n2, sh, {
        "anchor": lambda a, s: An.advantage(a, s, ("A", "M0")),
        "ms_vs_matched": lambda a, s: An.advantage(a, s, ("T1", "MS")) - matched_adv(a, s),
        "r1_minus_r2": lambda a, s: An.advantage(a, s, ("T1", "R1")) - An.advantage(a, s, ("T1", "R2")),
        "sh_mapping": lambda a, s: An._sh_mean(s, ("T1", "M0")) - sh_matched(s)}, n_boot)
    summary = {
        "food_dependence": An.food_dependence(champs),
        "memory_vs_memoryless": An.memory_vs_memoryless(diagnostics),
        "anchor": b["anchor"],
        "sign_01b": sign_01b,
        "drive": An.drive_check(recs, calibration, TARGET_DRIVE),
        "integrator": An.integrator_interactions(recs, champs),
        "late_cells": An.late_cells(recs),
        "ms_vs_matched": b["ms_vs_matched"],
        "r1_minus_r2": b["r1_minus_r2"],
        "sh_mapping": b["sh_mapping"],
        "valence_no_gap_max": max(v["max_abs_score_diff"] for v in probes["valence"] if not v["gaps"]),
        "strength": An.strength_contrast(recs, "norm_g39"),
        "pellet_share_g39": float(np.mean([r["pellet_share_g39"] for r in recs])),
        "max_ledger_error": max(r["ledger_error"] for r in recs),
    }
    out["summary"] = summary
    out["tripwires"] = An.tripwires(summary)
    return out
