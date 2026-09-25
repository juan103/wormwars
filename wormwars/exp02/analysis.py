"""Experiment 02 analysis: interaction, task contrast, paired bootstrap, variance components, and
the inputs to every tripwire.

Resampling units are whole replicate vectors. An N2 run, or an SH graph's run, carries its value
in every cell together, because every cell uses that unit's seed. SH graphs are resampled first,
then runs within each graph. Remaps are crossed with graphs, never nested. A cell a unit does not
have (SH runs its anchor cell in run 0 only) is skipped when averaging, never counted as missing.
"""

from __future__ import annotations

import json
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np

MATCHED = ("R1", "R2")
N_BOOT = 20_000
# D038, frozen before any N2 fitness data: a champion "meaningfully" depends on a capability when
# the interval of real minus ablated score lies above USE_THRESHOLD (score units, about a tenth
# of the scripted stereo or memory gain); a probe is valid when a controller that cannot use the
# capability moves by less than EQUIVALENCE, interval included.
USE_THRESHOLD = 0.10
EQUIVALENCE = 0.02


def _boot_mean(x: np.ndarray, n_boot: int = N_BOOT, seed: int = 0) -> dict:
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    means = x[rng.integers(0, len(x), size=(n_boot, len(x)))].mean(axis=1)
    return {"estimate": float(x.mean()), "lo": float(np.quantile(means, 0.025)),
            "hi": float(np.quantile(means, 0.975))}


def normalise(records, diagnostics) -> list[dict]:
    """Per-world score over the best scripted controller's score on that world; worlds where the
    best scripted score is zero are dropped. Not clipped: evolved brains may beat the scripts."""
    out = []
    for r in records:
        per = diagnostics[r["task"]]["per_seed_holdout"][str(r["run_seed"])]
        best = np.max(np.array(list(per.values())), axis=0)
        keep = best > 0
        r = dict(r)
        for tag in ("g00", "g39", "g79"):
            key = f"holdout_{tag}"
            if key in r:
                x = np.asarray(r[key])
                r[f"norm_{tag}"] = float(np.mean(x[keep] / best[keep])) if keep.any() else float("nan")
        out.append(r)
    return out


def units(records, measure: str):
    """N2 units {run: {cell: value}} and SH units {graph: {run: {cell: value}}}."""
    n2: dict = defaultdict(dict)
    sh: dict = defaultdict(lambda: defaultdict(dict))
    for r in records:
        if measure not in r:
            continue
        cell = (r["task"], r["mapping"])
        if r["graph"] == "N2":
            n2[r["run"]][cell] = r[measure]
        elif r["graph"].startswith("SH"):
            sh[r["graph"]][r["run"]][cell] = r[measure]
    return dict(n2), {g: dict(v) for g, v in sh.items()}


def _n2_mean(n2, cell):
    v = [u[cell] for u in n2.values() if cell in u]
    return float(np.mean(v)) if v else float("nan")


def _sh_mean(sh, cell):
    per_graph = [np.mean([u[cell] for u in runs.values() if cell in u])
                 for runs in sh.values() if any(cell in u for u in runs.values())]
    return float(np.mean(per_graph)) if per_graph else float("nan")


def advantage(n2, sh, cell) -> float:
    return _n2_mean(n2, cell) - _sh_mean(sh, cell)


def interaction(n2, sh, task: str) -> float:
    a0 = advantage(n2, sh, (task, "M0"))
    return a0 - float(np.mean([advantage(n2, sh, (task, m)) for m in MATCHED]))


def task_contrast(n2, sh) -> float:
    return interaction(n2, sh, "T1") - interaction(n2, sh, "T0")


def paired_bootstrap(n2, sh, stat, n_boot: int = N_BOOT, seed: int = 0) -> dict:
    return paired_bootstrap_many(n2, sh, {"_": stat}, n_boot, seed)["_"]


def paired_bootstrap_many(n2, sh, stats: dict, n_boot: int = N_BOOT, seed: int = 0) -> dict:
    """Every statistic on the same resamples: N2 runs with replacement; SH graphs with
    replacement, then runs within each drawn graph. Whole unit vectors travel together."""
    rng = np.random.default_rng(seed)
    n2_keys, graphs = list(n2), list(sh)
    samples = {k: np.empty(n_boot) for k in stats}
    for b in range(n_boot):
        rn2 = {i: n2[k] for i, k in enumerate(rng.choice(n2_keys, len(n2_keys)))}
        rsh = {}
        for j, gk in enumerate(rng.choice(graphs, len(graphs))):
            runs = list(sh[gk])
            rsh[f"g{j}"] = {i: sh[gk][r] for i, r in enumerate(rng.choice(runs, len(runs)))}
        for k, stat in stats.items():
            samples[k][b] = stat(rn2, rsh)
    return {k: {"estimate": float(stat(n2, sh)), "lo": float(np.nanquantile(samples[k], 0.025)),
                "hi": float(np.nanquantile(samples[k], 0.975)),
                "nan_share": float(np.isnan(samples[k]).mean())} for k, stat in stats.items()}


def _unit_contrast(u, task):
    return u[(task, "M0")] - np.mean([u[(task, m)] for m in MATCHED])


def variance_components(sh, task: str) -> dict:
    """One-way random-effects ANOVA on SH's per-unit mapping contrast: graphs x runs."""
    groups = [[_unit_contrast(u, task) for u in runs.values()] for runs in sh.values()]
    k, n = len(groups), len(groups[0])
    means = [np.mean(g) for g in groups]
    msb = n * np.var(means, ddof=1) if k > 1 else 0.0
    msw = np.mean([np.var(g, ddof=1) for g in groups]) if n > 1 else 0.0
    return {"between_graph": float(max((msb - msw) / n, 0.0)), "within_graph": float(max(msw, 0.0))}


def leave_one_graph_out(n2, sh, task: str) -> dict:
    return {g: interaction(n2, {k: v for k, v in sh.items() if k != g}, task) for g in sh}


def _family(graph: str) -> str:
    return "N2perm" if graph.startswith("N2perm") else "SH" if graph.startswith("SH") else graph


def late_cells(records, threshold_gen: int = 40) -> tuple[int, int]:
    """(cells whose mean checkpoint curve reaches 90% of its fitted asymptote after
    `threshold_gen`, cells with a usable curve). A cell is a graph family (N2, SH, N2perm) in a
    task and mapping, so different learning curves are not pooled. Fit: y = a - b * exp(-g / c)."""
    from scipy.optimize import OptimizeWarning, curve_fit

    curves = defaultdict(list)
    for r in records:
        if r.get("checkpoints"):
            curves[(_family(r.get("graph", "")), r["task"], r["mapping"])].append({int(g): v for g, v in r["checkpoints"]
                                                      if g < 40 and v is not None})
    late = n = 0
    for cs in curves.values():
        gens = sorted(set.intersection(*(set(c) for c in cs)))
        if len(gens) < 4:
            continue
        x = np.array(gens, dtype=float)
        y = np.array([np.mean([c[g] for c in cs]) for g in gens], dtype=float)
        n += 1
        try:
            with warnings.catch_warnings():
                # an exact fit leaves no residual to estimate a covariance from; the fit is fine
                warnings.simplefilter("ignore", OptimizeWarning)
                (a, b, c), _ = curve_fit(lambda g, a, b, c: a - b * np.exp(-g / c), x, y,
                                         p0=(y[-1], y[-1] - y[0], 10.0), maxfev=20000)
            g90 = -c * np.log(0.1) if (b > 0 and c > 0) else 0.0
        except RuntimeError:
            g90 = float("inf")
        late += int(g90 > threshold_gen)
    return late, n


def memory_vs_memoryless(diagnostics) -> dict:
    """Paired per-world difference, the nested memory controller M minus the tuned memoryless
    controller K, on T1 (keys as diagnostics.json writes them)."""
    diffs = []
    for per in diagnostics["T1"]["per_seed_holdout"].values():
        diffs.extend(np.asarray(per["M"]) - np.asarray(per["K"]))
    return _boot_mean(np.array(diffs))


def probe_valid(control_change: dict, gain_under: dict, gain_without: dict,
                margin: float = EQUIVALENCE) -> bool:
    """A probe is valid when the controller that cannot use the capability is unchanged within
    the equivalence margin (its whole interval), and the capable controller's gain over it falls:
    the gain's interval under the probe lies below its interval without."""
    return (-margin < control_change["lo"] and control_change["hi"] < margin
            and gain_under["hi"] < gain_without["lo"])


def classify_use(b: dict, threshold: float = USE_THRESHOLD) -> str:
    if b["lo"] > threshold:
        return "meaningful"
    if b["hi"] < threshold:
        return "below_threshold"
    return "inconclusive"


def champion_use(channels: dict, probe: str) -> dict:
    """One champion's paired per-world use of a capability: real minus ablated, with interval
    and class. Positive: the ablation hurts; negative: it helps."""
    sc = channels["scores"]
    b = _boot_mean(np.asarray(sc["real"]) - np.asarray(sc[probe]))
    return dict(b, cls=classify_use(b))


def attach_use(records, probes: dict, probe: str, snapshot: str) -> list[dict]:
    """Each record gains use_<probe>_<snapshot>: its champion's mean real minus ablated score
    over the probe worlds. Records without that probe (a mono task has no stereo ablation) are
    left without it, and units() skips them."""
    out = []
    for r in records:
        r = dict(r)
        ch = probes.get(r["key"], {}).get(snapshot, {}).get("channels")
        if ch and probe in ch["scores"]:
            r[f"use_{probe}_{snapshot}"] = float(np.mean(np.asarray(ch["scores"]["real"])
                                                         - np.asarray(ch["scores"][probe])))
        out.append(r)
    return out


def prediction_verdict(delta: dict, n2_use: dict, threshold: float = USE_THRESHOLD) -> str:
    """D038's registered prediction: N2 champions show greater, meaningful dependence on the
    capability than the sampled shuffles. Supported: the N2 - SH interval is above zero and N2's
    own use is meaningful. Challenged: N2's use is tightly below threshold, the contrast is
    reversed, or it straddles zero inside +-threshold. Anything else is inconclusive."""
    if delta["lo"] > 0 and n2_use["lo"] > threshold:
        return "supported"
    if n2_use["hi"] < threshold or delta["hi"] < 0 or (-threshold < delta["lo"] <= 0 and delta["hi"] < threshold):
        return "challenged"
    return "inconclusive"


def food_dependence(champions: dict, snapshot: str = "g39") -> dict:
    """Pooled over champions: real minus the constant food signal. A sanity check that evolved
    brains use the food signal at all; it says nothing about temporal or stereo use (D037)."""
    per = [float(np.mean(np.asarray(v[snapshot]["channels"]["scores"]["real"])
                         - np.asarray(v[snapshot]["channels"]["scores"]["food_constant"])))
           for v in champions.values() if snapshot in v]
    return _boot_mean(np.array(per))


def integrator_interactions(records, probes: dict) -> dict:
    """The interactions and task contrast recomputed from each integrator setting's rescoring.
    The shift between 32 and 128 substeps is compared with the shift a 1e-6 bias perturbation
    causes at 32 substeps (the chaos floor)."""
    out = {"I_T0": {}, "I_T1": {}, "task_contrast": {}}
    settings = ("s32", "s128", "s32_bias_perturbed")
    main = [r for r in records if r["task"] in ("T0", "T1") and r["mapping"] != "MS"
            and (r["graph"] == "N2" or r["graph"].startswith("SH"))]
    for s in settings:
        tagged = [dict(r, _v=float(np.mean(probes[r["key"]]["g39"]["integrator"][s])))
                  for r in main if "g39" in probes.get(r["key"], {})]
        n2, sh = units(tagged, "_v")
        out["I_T0"][s] = interaction(n2, sh, "T0")
        out["I_T1"][s] = interaction(n2, sh, "T1")
        out["task_contrast"][s] = task_contrast(n2, sh)
    stats = ("I_T0", "I_T1", "task_contrast")
    out["max_shift"] = float(max(abs(out[k]["s128"] - out[k]["s32"]) for k in stats))
    out["chaos_floor"] = float(max(abs(out[k]["s32_bias_perturbed"] - out[k]["s32"]) for k in stats))
    return out


def drive_check(records, calibration: dict, target: tuple) -> dict:
    """Achieved drive against the target: the calibration's independent validation seed, and each
    run's own generation-0 population."""
    def err(d):
        return max(abs(d["forward"] / target[0] - 1), abs(d["turn"] / target[1] - 1))

    validation = {g: err(c["validation_seed1"]) for g, c in calibration.items()}
    per_graph = defaultdict(list)
    for r in records:
        if "gen0_drive" in r:
            per_graph[r["graph"]].append(err(r["gen0_drive"]))
    gen0 = {g: float(np.mean(v)) for g, v in per_graph.items()}
    return {"validation": validation, "gen0_mean_error_per_graph": gen0,
            "max_validation_error": max(validation.values()),
            "max_gen0_error": max(gen0.values()) if gen0 else float("nan")}


def strength_contrast(records, measure: str) -> dict:
    """T1-M0: N2 with permuted strengths against N2, and against SH (plan review F9)."""
    def cell_units(prefix):
        u = defaultdict(list)
        for r in records:
            if (r["task"], r["mapping"]) == ("T1", "M0") and measure in r and (
                    r["graph"] == prefix if prefix == "N2" else r["graph"].startswith(prefix)):
                u[r["graph"]].append(r[measure])
        return u

    perm, n2, sh = cell_units("N2perm"), cell_units("N2"), cell_units("SH")
    rng = np.random.default_rng(0)

    def gmean(groups, resample):
        keys = list(groups)
        if resample:
            keys = list(rng.choice(keys, len(keys)))
        vals = []
        for k in keys:
            x = np.asarray(groups[k])
            vals.append((x[rng.integers(0, len(x), len(x))] if resample else x).mean())
        return float(np.mean(vals))

    est = {"perm_minus_n2": gmean(perm, False) - gmean(n2, False),
           "perm_minus_sh": gmean(perm, False) - gmean(sh, False)}
    samples = {k: [] for k in est}
    for _ in range(N_BOOT):
        p, a, s = gmean(perm, True), gmean(n2, True), gmean(sh, True)
        samples["perm_minus_n2"].append(p - a)
        samples["perm_minus_sh"].append(p - s)
    return {k: {"estimate": est[k], "lo": float(np.quantile(samples[k], 0.025)),
                "hi": float(np.quantile(samples[k], 0.975))} for k in est}


def sign_of_01b(path: Path) -> float:
    """01b's N2 minus SH final held-out score (mean over SH graph means), from its records."""
    recs = json.loads(Path(path).read_text(encoding="utf-8"))
    n2 = [r["holdout"] for r in recs if r["condition"] == "N2"]
    by = defaultdict(list)
    for r in recs:
        if r["condition"] == "SH":
            by[r["graph"]].append(r["holdout"])
    return float(np.mean(n2) - np.mean([np.mean(v) for v in by.values()]))


def _excludes_zero(b: dict) -> bool:
    return b["lo"] > 0 or b["hi"] < 0


def tripwires(summary: dict) -> list[dict]:
    """Each entry: name, fired, detail. Thresholds as pre-registered."""
    t = []
    fd = summary["food_dependence"]
    t.append({"name": "champions do not meaningfully depend on the food signal (real - constant)",
              "fired": not fd["lo"] > USE_THRESHOLD, "detail": fd})
    mem = summary["memory_vs_memoryless"]
    t.append({"name": "memory controller does not beat the tuned memoryless one on T1",
              "fired": not mem["lo"] > 0, "detail": mem})
    anc = summary["anchor"]
    t.append({"name": "anchor N2 - SH sign differs from 01b's",
              "fired": np.sign(anc["estimate"]) != np.sign(summary["sign_01b"]), "detail": anc})
    dr = summary["drive"]
    # 2048-genome validation sample: ~1.4% SE, so 4% is ~2 SE of the difference between two such
    # samples. Single runs' generation-0 drive (32 genomes, ~12% SE) is reported, not tripwired.
    t.append({"name": "achieved drive off target by more than 4% on the independent validation sample",
              "fired": dr["max_validation_error"] > 0.04, "detail": dr})
    ig = summary["integrator"]
    t.append({"name": "integrator moves the interaction more than the chaos floor (and by > 0.02)",
              "fired": ig["max_shift"] > ig["chaos_floor"] and ig["max_shift"] > 0.02, "detail": ig})
    late, n = summary["late_cells"]
    t.append({"name": "more than a third of cells reach 90% of asymptote after generation 40",
              "fired": n > 0 and late / n > 1 / 3, "detail": {"late": late, "cells": n}})
    for name, key in (("shortcut remap moves N2's advantage differently from matched remaps", "ms_vs_matched"),
                      ("R1 and R2 interactions differ", "r1_minus_r2"),
                      ("SH is not indifferent to the mapping", "sh_mapping")):
        t.append({"name": name, "fired": _excludes_zero(summary[key]), "detail": summary[key]})
    t.append({"name": "valence symmetry not exact without gap junctions",
              "fired": summary["valence_no_gap_max"] > 1e-5, "detail": summary["valence_no_gap_max"]})
    return t
