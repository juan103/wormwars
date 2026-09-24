"""Interaction estimates, the paired bootstrap and the tripwire inputs, on synthetic data with
known answers."""

from __future__ import annotations

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
        "1": {"one_step_memory": [1.0, 1.2, 0.9], "level_kinesis": [0.5, 0.6, 0.4]},
        "2": {"one_step_memory": [1.1, 1.0, 1.3], "level_kinesis": [0.6, 0.5, 0.7]}}}}
    b = A.memory_vs_memoryless(diag)
    assert b["lo"] < b["estimate"] < b["hi"] and b["lo"] > 0


def test_temporal_check_needs_both_probes():
    """Plan review F11: T1 is temporal only if champions lose to the constant AND to the mirrored signal."""
    champs = {f"T1-M0-N2-run0{i}": {"channels": {"real": 1.0 + i / 10, "food_constant": 0.5,
                                                 "food_mirrored": 0.6}} for i in range(5)}
    champs["T0-M0-N2-run00"] = {"channels": {"real": 9.0, "food_constant": 0.0, "food_mirrored": 0.0}}
    t = A.temporal_check(champs)
    assert set(t) == {"real_minus_constant", "real_minus_mirrored"}
    assert t["real_minus_constant"]["lo"] > 0 and t["real_minus_mirrored"]["lo"] > 0
    assert abs(t["real_minus_constant"]["estimate"] - (1.2 - 0.5)) < 1e-9


def test_integrator_interactions_are_recomputed_per_setting():
    """Plan review F2: compare the interaction under 32 vs 128 substeps with the chaos floor."""
    n2, sh = synth(effect_t1=0.2, noise=0.0)
    recs, probes = [], {}
    for r, cells in n2.items():
        for (task, mapping), v in cells.items():
            key = f"{task}-{mapping}-N2-run{r:02d}"
            recs.append({"key": key, "task": task, "mapping": mapping, "graph": "N2", "run": r})
            probes[key] = {"integrator": {"s32": [v], "s128": [v], "s32_bias_perturbed": [v + 0.01]}}
    for g, runs in sh.items():
        for r, cells in runs.items():
            for (task, mapping), v in cells.items():
                key = f"{task}-{mapping}-{g}-run{r:02d}"
                recs.append({"key": key, "task": task, "mapping": mapping, "graph": g, "run": r})
                probes[key] = {"integrator": {"s32": [v], "s128": [v], "s32_bias_perturbed": [v]}}
    out = A.integrator_interactions(recs, probes)
    assert abs(out["I_T1"]["s128"] - out["I_T1"]["s32"]) < 1e-9
    assert out["max_shift"] <= out["chaos_floor"] + 1e-12
