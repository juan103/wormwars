"""Interaction estimates, the paired bootstrap and the tripwire inputs, on synthetic data with
known answers."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from wormwars.exp02 import analysis as A

CELLS = [("T0", "M0"), ("T0", "R1"), ("T0", "R2"), ("T1", "M0"), ("T1", "R1"), ("T1", "R2")]


def synth(effect_t1=0.2, unit_offset_sd=1.0, noise=0.0, seed=0):
    rng = np.random.default_rng(seed)
    n2, sh = {}, {}
    for r in range(4):
        off = rng.normal(0, unit_offset_sd)
        n2[r] = {c: off + (effect_t1 if c == ("T1", "M0") else 0.0) + rng.normal(0, noise) for c in CELLS}
    for k in range(6):
        sh[f"SH{k + 1}"] = {}
        for r in range(2):
            off = rng.normal(0, unit_offset_sd)
            sh[f"SH{k + 1}"][r] = {c: off + rng.normal(0, noise) for c in CELLS}
    return n2, sh


def test_interaction_recovers_the_planted_effect():
    n2, sh = synth(effect_t1=0.2, noise=0.0)
    assert abs(A.interaction(n2, sh, "T1") - 0.2) < 1e-9
    assert abs(A.interaction(n2, sh, "T0")) < 1e-9
    assert abs(A.task_contrast(n2, sh) - 0.2) < 1e-9


def test_unit_offsets_cancel_inside_the_bootstrap():
    # huge per-unit offsets, no noise: resampling whole unit vectors must leave the interaction exact
    n2, sh = synth(effect_t1=0.2, unit_offset_sd=10.0, noise=0.0)
    b = A.paired_bootstrap(n2, sh, lambda a, s: A.interaction(a, s, "T1"), n_boot=500)
    assert abs(b["lo"] - 0.2) < 1e-9 and abs(b["hi"] - 0.2) < 1e-9


def test_bootstrap_interval_covers_the_truth_under_noise():
    n2, sh = synth(effect_t1=0.2, unit_offset_sd=1.0, noise=0.05, seed=3)
    b = A.paired_bootstrap(n2, sh, lambda a, s: A.interaction(a, s, "T1"), n_boot=2000)
    assert b["lo"] < 0.2 < b["hi"]


def test_a_cell_present_in_only_some_runs_never_gives_nan():
    """Plan review F5: SH has the anchor cell in run 0 only; resampling run 1 twice must not
    produce NaN, it must skip that graph."""
    n2, sh = synth()
    for r in n2:
        n2[r][("A", "M0")] = 1.0
    for g in sh:
        sh[g][0][("A", "M0")] = 0.5
    b = A.paired_bootstrap(n2, sh, lambda a, s: A.advantage(a, s, ("A", "M0")), n_boot=500)
    assert np.isfinite([b["estimate"], b["lo"], b["hi"]]).all()
    assert abs(b["estimate"] - 0.5) < 1e-9


def test_normalise_drops_worlds_where_the_reference_is_zero():
    recs = [{"task": "T0", "run_seed": 1, "holdout_g00": [0.5, 0.4], "holdout_g39": [1.0, 0.8]}]
    diag = {"T0": {"per_seed_holdout": {"1": {"a": [1.0, 0.0], "b": [0.5, 0.0]}}}}
    out = A.normalise(recs, diag)
    assert out[0]["norm_g39"] == 1.0 and out[0]["norm_g00"] == 0.5
    diag0 = {"T0": {"per_seed_holdout": {"1": {"a": [0.0, 0.0]}}}}
    assert np.isnan(A.normalise(recs, diag0)[0]["norm_g39"])


def test_variance_components_are_non_negative_and_named():
    _, sh = synth(noise=0.1)
    v = A.variance_components(sh, "T1")
    assert set(v) == {"between_graph", "within_graph"} and min(v.values()) >= 0


def test_late_cells_counts_slow_curves_as_a_fraction():
    """Plan review F10: the threshold is a fraction of the cells actually counted."""
    fast = {"task": "T0", "mapping": "M0", "checkpoints": [(g, 1 - np.exp(-g / 3)) for g in (0, 10, 20, 30, 39)]}
    slow = {"task": "T1", "mapping": "M0", "checkpoints": [(g, 1 - np.exp(-g / 40)) for g in (0, 10, 20, 30, 39)]}
    late, n = A.late_cells([fast, slow])
    assert (late, n) == (1, 2)


def test_memory_versus_memoryless_is_a_paired_interval():
    """Plan review F4: a real interval from paired per-world scores, not a single number."""
    diag = {"T1": {"per_seed_holdout": {
        "1": {"M": [1.0, 1.2, 0.9], "K": [0.5, 0.6, 0.4]},
        "2": {"M": [1.1, 1.0, 1.3], "K": [0.6, 0.5, 0.7]}}}}
    b = A.memory_vs_memoryless(diag)
    assert b["lo"] < b["estimate"] < b["hi"] and b["lo"] > 0


def test_memory_versus_memoryless_reads_the_committed_diagnostics():
    """Astra's decision review, point 9: the report looked up keys the diagnostics never wrote.
    Read the real file so a schema drift fails here, not after the grid has run."""
    diag = json.loads((Path(__file__).parents[1] / "experiments/02-screening/diagnostics.json")
                      .read_text(encoding="utf-8"))
    b = A.memory_vs_memoryless(diag)
    assert b["lo"] > 0.5


def test_probe_validity_needs_equivalence_not_a_wide_interval():
    """Astra's decision review, point 4: an interval that merely contains zero is not evidence
    that a controller is unaffected; it must lie inside the equivalence margin."""
    gain = {"estimate": 1.0, "lo": 0.9, "hi": 1.1}
    left = {"estimate": 0.1, "lo": 0.0, "hi": 0.2}
    assert A.probe_valid({"estimate": 0.0, "lo": -0.01, "hi": 0.01}, left, gain)
    assert not A.probe_valid({"estimate": 0.0, "lo": -0.05, "hi": 0.05}, left, gain)
    assert not A.probe_valid({"estimate": 0.0, "lo": -0.01, "hi": 0.01}, {"lo": 0.8, "hi": 0.95}, gain)


def test_use_is_classified_against_the_threshold_with_an_inconclusive_middle():
    assert A.classify_use({"lo": 0.12, "hi": 0.3}) == "meaningful"
    assert A.classify_use({"lo": -0.05, "hi": 0.08}) == "below_threshold"
    assert A.classify_use({"lo": 0.05, "hi": 0.2}) == "inconclusive"


def _probe_records(n2_use, sh_use, snapshot="g39"):
    """Records and probe results where each champion's use of the bilateral mean is planted."""
    recs, probes = [], {}
    def add(graph, run, cell, use):
        key = f"{cell[0]}-{cell[1]}-{graph}-run{run:02d}"
        recs.append({"key": key, "task": cell[0], "mapping": cell[1], "graph": graph, "run": run})
        real = [2.0, 2.2, 1.8, 2.1]
        probes.setdefault(key, {})[snapshot] = {"channels": {"world_ids": [0, 1, 2, 3], "probe_seed": 1,
            "scores": {"real": real, "food_mean": [x - use for x in real]}}}
    for r in range(4):
        for c in CELLS:
            add("N2", r, c, n2_use.get(c, 0.0))
    for k in range(6):
        for r in range(2):
            for c in CELLS:
                add(f"SH{k + 1}", r, c, sh_use.get(c, 0.0))
    return recs, probes


def test_capability_use_is_attached_per_champion_and_per_snapshot():
    recs, probes = _probe_records({("T0", "M0"): 0.3}, {})
    out = A.attach_use(recs, probes, "food_mean", "g39")
    n2 = [r for r in out if r["graph"] == "N2" and (r["task"], r["mapping"]) == ("T0", "M0")]
    assert all(abs(r["use_food_mean_g39"] - 0.3) < 1e-9 for r in n2)
    assert "use_food_mean_g00" not in out[0]


def test_capability_contrast_recovers_a_planted_n2_advantage():
    recs, probes = _probe_records({("T0", "M0"): 0.3}, {("T0", "M0"): 0.05})
    n2, sh = A.units(A.attach_use(recs, probes, "food_mean", "g39"), "use_food_mean_g39")
    assert abs(A.advantage(n2, sh, ("T0", "M0")) - 0.25) < 1e-9
    assert abs(A.interaction(n2, sh, "T0") - 0.25) < 1e-9


def test_prediction_verdict_separates_support_challenge_and_inconclusive():
    ok = {"estimate": 0.3, "lo": 0.2, "hi": 0.4}
    assert A.prediction_verdict(ok, {"lo": 0.15, "hi": 0.4}) == "supported"
    assert A.prediction_verdict({"lo": -0.05, "hi": 0.05}, {"lo": 0.15, "hi": 0.4}) == "inconclusive"
    assert A.prediction_verdict(ok, {"lo": 0.0, "hi": 0.08}) == "challenged"
    assert A.prediction_verdict({"lo": -0.2, "hi": -0.15}, {"lo": 0.15, "hi": 0.4}) == "challenged"
    assert A.prediction_verdict({"lo": -0.05, "hi": 0.3}, {"lo": 0.15, "hi": 0.4}) == "inconclusive"


def test_late_cells_are_counted_per_graph_family():
    """Astra's decision review, point 11: pooling N2 and SH curves can hide different learning."""
    fast = [(g, 1 - np.exp(-g / 3)) for g in (0, 10, 20, 30, 39)]
    slow = [(g, 1 - np.exp(-g / 40)) for g in (0, 10, 20, 30, 39)]
    recs = [{"task": "T0", "mapping": "M0", "graph": "N2", "checkpoints": slow},
            {"task": "T0", "mapping": "M0", "graph": "SH1", "checkpoints": fast}]
    assert A.late_cells(recs) == (1, 2)


def test_integrator_interactions_are_recomputed_per_setting():
    """Plan review F2: compare the interaction under 32 vs 128 substeps with the chaos floor."""
    n2, sh = synth(effect_t1=0.2, noise=0.0)
    recs, probes = [], {}
    for r, cells in n2.items():
        for (task, mapping), v in cells.items():
            key = f"{task}-{mapping}-N2-run{r:02d}"
            recs.append({"key": key, "task": task, "mapping": mapping, "graph": "N2", "run": r})
            probes[key] = {"g39": {"integrator": {"s32": [v], "s128": [v], "s32_bias_perturbed": [v + 0.01]}}}
    for g, runs in sh.items():
        for r, cells in runs.items():
            for (task, mapping), v in cells.items():
                key = f"{task}-{mapping}-{g}-run{r:02d}"
                recs.append({"key": key, "task": task, "mapping": mapping, "graph": g, "run": r})
                probes[key] = {"g39": {"integrator": {"s32": [v], "s128": [v], "s32_bias_perturbed": [v]}}}
    out = A.integrator_interactions(recs, probes)
    assert abs(out["I_T1"]["s128"] - out["I_T1"]["s32"]) < 1e-9
    assert out["max_shift"] <= out["chaos_floor"] + 1e-12


def test_drive_tripwire_uses_the_large_validation_sample_not_single_runs():
    """A 32-genome generation-0 population scatters about +-12% in drive by sampling alone, so it
    cannot carry a 2% tripwire; the graph-level validation sample does (2048 genomes, 4%)."""
    base = {"food_dependence": {"lo": 1, "hi": 2, "estimate": 1},
            "memory_vs_memoryless": {"lo": 1, "hi": 2, "estimate": 1},
            "anchor": {"estimate": 1.0, "lo": 0.5, "hi": 1.5}, "sign_01b": 1.0,
            "integrator": {"max_shift": 0.0, "chaos_floor": 0.0}, "late_cells": (0, 8),
            "ms_vs_matched": {"lo": -1, "hi": 1}, "r1_minus_r2": {"lo": -1, "hi": 1},
            "sh_mapping": {"lo": -1, "hi": 1}, "valence_no_gap_max": 0.0}
    ok = dict(base, drive={"max_validation_error": 0.03, "max_gen0_error": 0.15})
    bad = dict(base, drive={"max_validation_error": 0.05, "max_gen0_error": 0.01})
    fired = lambda s: [t["fired"] for t in A.tripwires(s) if "drive" in t["name"]][0]  # noqa: E731
    assert fired(ok) is False and fired(bad) is True


def test_food_dependence_pools_champions_at_a_snapshot():
    ch = lambda real, const: {"channels": {"scores": {"real": real, "food_constant": const}}}  # noqa: E731
    champs = {f"k{i}": {"g39": ch([1.0 + i / 10, 1.2], [0.4, 0.5]), "g00": ch([0.5], [0.5])} for i in range(5)}
    b = A.food_dependence(champs, "g39")
    assert b["lo"] > A.USE_THRESHOLD and abs(A.food_dependence(champs, "g00")["estimate"]) < 1e-12


def test_many_statistics_share_one_resample_and_match_the_single_bootstrap():
    n2, sh = synth(effect_t1=0.2, noise=0.1)
    stats = {"I_T1": lambda a, s: A.interaction(a, s, "T1"), "I_T0": lambda a, s: A.interaction(a, s, "T0")}
    many = A.paired_bootstrap_many(n2, sh, stats, n_boot=300)
    one = A.paired_bootstrap(n2, sh, stats["I_T1"], n_boot=300)
    for k in ("estimate", "lo", "hi"):
        assert abs(many["I_T1"][k] - one[k]) < 1e-12


def test_verdict_does_not_challenge_a_small_positive_contrast():
    """Astra's pre-registration review, point 2: the equivalence branch tested a hypothesis the
    support rule never required; a contrast straddling zero is inconclusive, not challenged."""
    n2_use = {"lo": 0.20, "hi": 0.30}
    assert A.prediction_verdict({"lo": 0.001, "hi": 0.009}, n2_use) == "supported"
    assert A.prediction_verdict({"lo": -0.001, "hi": 0.009}, n2_use) == "inconclusive"


def test_variance_components_handle_unequal_runs_per_graph():
    """Astra's pre-registration review, point 7: a budget cut can leave some graphs with one run."""
    _, sh = synth(effect_t1=0.0, noise=0.1)
    del sh["SH5"][1], sh["SH6"][1]
    v = A.variance_components(sh, "T1")
    assert np.isfinite(v["between_graph"]) and np.isfinite(v["within_graph"])


def test_integrator_not_assessed_when_rescoring_was_dropped():
    """Astra's pre-registration review, point 4: a registered budget omission must read as
    'not assessed', never crash and never pass silently."""
    recs = [{"key": "k", "task": "T1", "mapping": "M0", "graph": "N2", "run": 0}]
    out = A.integrator_interactions(recs, {"k": {"g39": {"channels": {}}}})
    assert out["assessed"] is False
    base = {"food_dependence": {"lo": 1, "hi": 2, "estimate": 1},
            "memory_vs_memoryless": {"lo": 1, "hi": 2, "estimate": 1},
            "anchor": {"estimate": 1.0, "lo": 0.5, "hi": 1.5}, "sign_01b": 1.0,
            "drive": {"max_validation_error": 0.03}, "integrator": out, "late_cells": (0, 8),
            "ms_vs_matched": {"lo": -1, "hi": 1}, "r1_minus_r2": {"lo": -1, "hi": 1},
            "sh_mapping": {"lo": -1, "hi": 1}, "valence_no_gap_max": 0.0}
    tw = [t for t in A.tripwires(base) if "integrator" in t["name"]][0]
    assert tw["fired"] is None


def test_tripwires_serialise_with_plain_json():
    """Astra's pre-registration review, point 1: NumPy booleans broke the CLI's json.dumps."""
    base = {"food_dependence": {"lo": np.float64(1), "hi": 2, "estimate": 1},
            "memory_vs_memoryless": {"lo": 1, "hi": 2, "estimate": 1},
            "anchor": {"estimate": np.float64(1.0), "lo": 0.5, "hi": 1.5}, "sign_01b": np.float64(1.0),
            "drive": {"max_validation_error": 0.03},
            "integrator": {"assessed": True, "max_shift": np.float64(0.0), "chaos_floor": 0.0}, "late_cells": (0, 8),
            "ms_vs_matched": {"lo": -1, "hi": 1}, "r1_minus_r2": {"lo": -1, "hi": 1},
            "sh_mapping": {"lo": -1, "hi": 1}, "valence_no_gap_max": 0.0}
    json.dumps([{k: v for k, v in t.items() if k != "detail"} for t in A.tripwires(base)])


def test_late_cells_measure_the_share_of_improvement_not_of_the_score():
    """Astra's pre-registration review, point 6: the criterion is 90% of the fitted improvement
    from generation 0; a curve that starts near its asymptote but improves slowly is still late."""
    slow_small = {"task": "T0", "mapping": "M0", "graph": "N2",
                  "checkpoints": [(g, 3 - 0.1 * np.exp(-g / 100)) for g in (0, 10, 20, 30, 39)]}
    assert A.late_cells([slow_small]) == (1, 1)
    assert "improvement" in A.late_cells.__doc__
