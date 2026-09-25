"""Experiment 03's report enforces its registered rules (the team's review of the
pre-registration, D054): one validity mask per signal used everywhere, withholding when N2 or an
ensemble is incomplete, a P3 world profile from the registered ensemble graphs only, and the
secondary signals."""

from __future__ import annotations

import numpy as np
import pytest

from wormwars.exp03 import report as R

G, W, PG = 8, 4, 16


def fake(rng, shift=0.0, den=1.0):
    f = {k: rng.normal(1.0, 0.1, (G if k in ("T1-M0", "T1const-M0") else 4, W)).tolist()
         for k in ("T1-M0", "T1const-M0", "T1-R1", "T1-R2", "T0-M0")}
    f["T1-M0"] = (np.asarray(f["T1-M0"]) + shift).tolist()
    resp = {m: {"directional_turn_signed_raw": (rng.normal(shift, 0.01, PG)).tolist(),
                "directional_turn_raw": rng.uniform(0.01, 0.02, PG).tolist(),
                "common_turn_raw": (rng.uniform(0.9, 1.1, PG) * den).tolist(),
                "common_forward_raw": rng.uniform(0.01, 0.02, PG).tolist()} for m in R.RESPONSE_CONDITIONS}
    hist = {"raw_turn": {"final": rng.normal(0.8 + shift, 0.01, PG).tolist(),
                         "steady_contrast": rng.normal(1.0, 0.01, PG).tolist(),
                         "after": rng.normal(0.7, 0.01, PG).tolist()}}
    return {"fitness": f, "response": resp, "history": hist, "coverage": rng.integers(80, 120, (4, W)).tolist()}


def make(n_per=128, kinds=("A", "B"), n2_shift=0.0, n2_den=1.0, seed=0):
    rng = np.random.default_rng(seed)
    measures = {"N2": fake(rng, n2_shift, n2_den)}
    ens = {}
    for k in kinds:
        ens[k] = [f"{k}-{i}" for i in range(n_per)]
        for n in ens[k]:
            measures[n] = fake(rng)
    return measures, ens


def test_a_graph_with_a_tiny_denominator_is_excluded_everywhere_and_counted():
    measures, ens = make()
    for m in measures["A-3"]["response"].values():
        m["common_turn_raw"] = [1e-6] * PG
    out = R.build(measures, "N2", ens, n_boot=20)
    assert out["signals"]["P1"]["A"]["graphs"] == 127 and out["exclusions"]["P1"]["A"] == ["A-3"]
    assert np.isfinite(out["signals"]["P1"]["A"]["margin"])


def test_an_invalid_n2_withholds_that_signal_and_counts_as_p_one_in_holm():
    measures, ens = make(n2_den=1e-6)
    out = R.build(measures, "N2", ens, n_boot=20)
    assert out["signals"]["P1_summary"]["overall"] == "withheld"
    assert out["signals"]["P1_summary"]["p_max"] == 1.0


def test_an_incomplete_ensemble_withholds_the_verdict():
    measures, ens = make(n_per=119)
    out = R.build(measures, "N2", ens, n_boot=20)
    assert all(out["signals"][s + "_summary"]["overall"] == "withheld" for s in R.PRIMARY)


def test_the_p3_world_profile_ignores_n2_and_unregistered_files():
    measures, ens = make()
    a = R.build(measures, "N2", ens, n_boot=20)
    measures["N2"]["fitness"]["T1-M0"] = (np.asarray(measures["N2"]["fitness"]["T1-M0"]) + 5.0).tolist()
    measures["stray"] = measures["A-0"]
    b = R.build(measures, "N2", ens, n_boot=20)
    for e in ens:
        assert a["signals"]["P3"][e]["margin"] == pytest.approx(b["signals"]["P3"][e]["margin"])


def test_secondary_signals_are_reported():
    measures, ens = make()
    out = R.build(measures, "N2", ens, n_boot=20)
    sec = out["secondary"]
    assert {"P2", "T0_mean", "T0_top_decile", "coverage", "P1_by_condition", "P4_decay"} <= set(sec["N2"])
    assert set(sec["ensemble_mean_P2"]) == set(ens)
    assert set(out["ranks_descriptive"]) == set()  # no N2 variants in this synthetic set
