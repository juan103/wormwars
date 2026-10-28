"""M5's power calculation (docs/memory/M5-POWER-DESIGN.md): the reading it applies (section 1) and the simulation
(sections 2 to 6)."""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m5"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))

import m5_reading as MR  # noqa: E402

BALANCED = np.repeat(np.arange(5), 3)  # three hosts in each of the five ensembles
UNBALANCED = np.array([0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4])  # strata of 2, 3, 3, 3, 3


# ------------------------------------------------------------------------------------------------------------ reading
def test_the_stratified_bootstrap_resamples_within_each_ensemble():
    W, idx = MR.resample_weights(BALANCED, 200, seed=1, stratified=True, return_idx=True)
    for b in range(200):
        assert sorted(BALANCED[idx[b]].tolist()) == sorted(BALANCED.tolist())
    assert np.allclose(W.sum(1), 1.0)
    d = np.random.default_rng(2).normal(size=len(BALANCED))
    by_hand = np.array([sum(d[idx[b]][BALANCED[idx[b]] == e].mean() / 5 for e in range(5)) for b in range(200)])
    assert np.allclose(W @ d, by_hand)


def test_the_estimate_weights_each_ensemble_a_fifth():
    d = np.array([1.0, 1.0, 5.0, 5.0, 5.0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    assert MR.estimate(d, UNBALANCED) == pytest.approx((1.0 + 5.0) / 5)
    d2 = np.arange(15.0)
    assert MR.estimate(d2, BALANCED) == pytest.approx(d2.mean())


def test_the_balanced_t_is_m4es_t():
    import m4e_read as RD
    d = np.random.default_rng(3).normal(0.001, 0.003, len(BALANCED))
    assert MR.t_interval(d, BALANCED) == pytest.approx(RD.t_interval(d))


def test_the_plain_mode_reproduces_m4es_published_t_minus_k(monkeypatch):
    import m4e_read as RD
    monkeypatch.setattr(MR, "WELCH_TOO", False)  # M4e's reading had no Welch t in its balanced hull
    rec = json.loads((ROOT / "runs" / "memory-m4e" / "readings.json").read_text(encoding="utf-8"))["secondary"]["T - K"]
    d = np.array(rec["per_host"])
    ens = np.repeat(np.arange(5), 2)
    W = MR.resample_weights(ens, RD.B, seed=RD.SEED_BOOT, stratified=False)
    assert MR.interval(d, ens, W) == pytest.approx(rec["interval"], abs=1e-15)
    assert MR.estimate(d, ens) == pytest.approx(rec["D"])


def test_the_unbalanced_t_is_welchs_and_catches_variance_in_the_pair():
    d = np.zeros(len(UNBALANCED))
    d[:2] = [-0.01, 0.01]  # all the variance in the stratum of two (Astra's round-2 example)
    lo, hi = MR.t_interval(d, UNBALANCED)
    assert hi - lo == pytest.approx(2 * 0.025412, rel=1e-3)
    n = len(d)
    plain = stats.t.ppf(0.975, n - 1) * np.sqrt(d.var(ddof=1) * sum((1 / 5) ** 2 / k for k in (2, 3, 3, 3, 3)))
    assert (hi - lo) / 2 > 10 * plain


def test_the_welch_degrees_of_freedom():
    rng = np.random.default_rng(4)
    d = rng.normal(size=len(UNBALANCED))
    a = np.array([(1 / 5) ** 2 * d[UNBALANCED == e].var(ddof=1) / (UNBALANCED == e).sum() for e in range(5)])
    k = np.array([(UNBALANCED == e).sum() for e in range(5)])
    assert MR.welch_df(d, UNBALANCED) == pytest.approx(a.sum() ** 2 / (a ** 2 / (k - 1)).sum())


def test_an_ensemble_needs_two_hosts():
    with pytest.raises(ValueError):
        MR.t_interval(np.zeros(9), np.array([0, 1, 1, 2, 2, 3, 3, 4, 4]))


@pytest.mark.parametrize("ens", [np.repeat(np.arange(5), 2), np.array([0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 4, 4]),
                                 np.array([0, 0, 1, 1, 1, 2, 2, 3, 3, 4, 4])])
def test_the_envelope_contains_every_corner(ens):
    """The scalable envelope against the exhaustive enumeration of every assignment (H <= 12)."""
    ens = np.sort(ens)
    rng = np.random.default_rng(5)
    W = MR.resample_weights(ens, 400, seed=6, stratified=True)
    for _ in range(5):
        lo = rng.normal(0, 0.004, len(ens))
        hi = lo + rng.integers(0, 5, len(ens)) / 512
        elo, ehi = MR.envelope(lo, hi, ens, W)
        for corner in itertools.product(*zip(lo, hi)):
            clo, chi = MR.interval(np.array(corner), ens, W)
            assert elo <= clo + 1e-15 and chi <= ehi + 1e-15


def test_the_unbalanced_envelope_holds_astras_box():
    """Astra's round-2 box: equal ends, the variance in the stratum of two; the pooled bound misses it, Welch's not."""
    d = np.zeros(len(UNBALANCED))
    d[:2] = [-0.01, 0.01]
    W = MR.resample_weights(UNBALANCED, 400, seed=12)
    lo, hi = MR.envelope(d, d, UNBALANCED, W)
    ilo, ihi = MR.interval(d, UNBALANCED, W)
    assert lo <= ilo and ihi <= hi


def test_the_welch_proposal_widens_the_balanced_hull_and_keeps_the_envelope(monkeypatch):
    """The proposal under review (M5_WELCH_TOO): the balanced hull also holds the Welch t, and the envelope still
    contains every corner's interval."""
    ens = np.repeat(np.arange(5), 2)
    W = MR.resample_weights(ens, 400, seed=14)
    rng = np.random.default_rng(15)
    d = np.zeros(10)
    d[:2] = [-0.01, 0.01]
    monkeypatch.setattr(MR, "WELCH_TOO", False)  # the reading as first written
    base = MR.interval(d, ens, W)
    monkeypatch.setattr(MR, "WELCH_TOO", True)
    wl, wh = MR.welch_interval(d, ens)
    lo, hi = MR.interval(d, ens, W)
    assert lo <= min(base[0], wl) and hi >= max(base[1], wh) and hi - lo > base[1] - base[0]
    for _ in range(3):
        lo_d = rng.normal(0, 0.004, 10)
        hi_d = lo_d + rng.integers(0, 5, 10) / 512
        elo, ehi = MR.envelope(lo_d, hi_d, ens, W)
        for corner in itertools.product(*zip(lo_d, hi_d)):
            clo, chi = MR.interval(np.array(corner), ens, W)
            assert elo <= clo + 1e-15 and chi <= ehi + 1e-15


def test_direction():
    assert MR.direction((0.0001, 0.003)) == "raises"
    assert MR.direction((-0.003, -0.0001)) == "lowers"
    assert MR.direction((-0.001, 0.003)) == "direction unresolved"


def test_success_needs_all_six_readings():
    """Astra's round-2 example: the audit offsets the Rr-side unresolved sensitivity in their combination."""
    ok = (0.0001, 0.004)
    ivs = {k: ok for k in MR.READINGS}
    assert MR.unqualified_raises(ivs) is True
    for k in MR.READINGS[1:]:
        assert MR.unqualified_raises({**ivs, k: (-0.00005, 0.004)}) is False
    assert MR.qualification({**ivs, "unres_Rr": (-0.00005, 0.004)}) == "raises, qualified by the Rr-side unresolved sensitivity"
    assert MR.qualification({**ivs, "audit_unres_Rr": (-0.00005, 0.004)}) == "raises, qualified only in a combination"
    assert MR.qualification({**ivs, "raw": (-0.001, 0.004)}) == "direction unresolved"


def test_a_t_side_adjustment_can_remove_raises(monkeypatch):
    """Astra's round-3 example: adding T's unresolved genomes raises the estimate and widens the t past zero. Its
    numbers are the plain hull's, the reading as first written."""
    monkeypatch.setattr(MR, "WELCH_TOO", False)
    ens = np.repeat(np.arange(5), 3)
    n = 2 * 512
    counts = np.ones(15)
    counts[0] = 14
    unres_T = np.zeros(15)
    unres_T[0] = 5
    W = MR.resample_weights(ens, MR.B, seed=MR.SEED_BOOT)
    raw = MR.interval(counts / n, ens, W)
    t_side = MR.interval((counts + MR.R_BOUND * unres_T) / n, ens, W)
    assert raw[0] == pytest.approx(7.6675e-6, rel=1e-3) and raw[0] > 0
    assert t_side[0] == pytest.approx(-1.7606e-6, rel=1e-3) and t_side[0] < 0


# --------------------------------------------------------------------------------------------------------- simulation
@pytest.fixture(scope="module")
def P():
    import m5_power
    return m5_power


@pytest.fixture(scope="module")
def fitted(P):
    return P.fit()


def solved(P, fitted, **kw):
    return P.solve_scenario(fitted, P.Scenario(**kw))


def test_the_fit_reproduces_the_pilot(P, fitted):
    s = fitted["classes"]["S1"]
    assert s["sd"]["T"] == pytest.approx(0.487, abs=0.01) and s["sd_Rr_without_draw"] == pytest.approx(0.493, abs=0.01)
    assert s["count_var"]["T"] == pytest.approx(22.5) and s["count_corr"] == pytest.approx(0.70061, abs=1e-4)
    assert fitted["u_to_s"] == pytest.approx(1 / 153)
    tab = fitted["first_to_final"]
    assert sum(tab["T"].values()) == 42 and sum(tab["Rr"].values()) == 60 and sum(tab["K"].values()) == 51
    assert (tab["T"]["F"], tab["Rr"]["F"], tab["Rr"]["O"], tab["K"]["S"]) == (9, 12, 1, 1)
    ranges = {a: [r["U1"] for r in P.pilot_inputs()["panels"][a]] for a in P.ARMS}
    assert (min(ranges["T"]), max(ranges["T"]), min(ranges["Rr"]), max(ranges["Rr"])) == (0, 7, 0, 12)


def test_the_scenarios_solve_to_the_reviewers_values(P, fitted):
    assert solved(P, fitted, target="core").rho == pytest.approx(0.17, abs=0.03)
    assert solved(P, fitted, target="half").rho == pytest.approx(0.60, abs=0.03)
    above = solved(P, fitted, target="above")
    assert above.rho == 0.0 and 1.45 < above.scale < 1.65
    sd0 = fitted["classes"]["S1"]["sd_pooled"]
    assert P.host_component(fitted, P.RATE_RR, sd0, 1.0, fitted["sd_v"]) < 1e-10


def test_a_panel_is_coherent(P, fitted):
    m = P.make_model(fitted, solved(P, fitted, target="core"), (2, 512, 40))
    sim = P.simulate(m, np.random.default_rng(7), 200, 10)
    for a in P.ARMS:
        x = sim[a]
        total = x["S"] + x["U"] + x["Fun"] + x["aud"] - x["trans"]  # an audited transition is in S and in aud
        assert (total <= 2 * 512).all() and (x["S"] >= 0).all() and (x["trans"] <= x["aud"]).all()
        assert (x["hidden"] <= x["Fun"]).all()
        assert (x["aud"] <= 2 * 40).all()
        # the audit's ids are drawn from the whole panel, so about 98.6% of them are first-pass fading (M4e's)
        assert x["aud"].mean() / 80 == pytest.approx(0.986, abs=0.006)


def test_the_arms_share_their_host_effects(P, fitted):
    """The simulated host component of the contrast is the solved one: the core scenario's per-host contrast variance
    exceeds the central one's by about 1.52e-5."""
    var = {}
    for tg in ("min", "core"):
        m = P.make_model(fitted, P.replace(solved(P, fitted, target=tg), delta=0.0), (2, 512, 40))
        sim = P.simulate(m, np.random.default_rng(10), 400, 50)
        var[tg] = ((sim["T"]["S"] - sim["Rr"]["S"]) / 1024).var(1, ddof=1).mean()
    assert var["core"] - var["min"] == pytest.approx(1.52e-5, rel=0.2)


def test_an_incomplete_run_is_a_failure(P, fitted):
    m = P.make_model(fitted, solved(P, fitted, target="min"), (2, 512, 40))
    res = P.run_cell(m, 30, 500, "test-cap", cap=1.0)
    assert res["success"].sum() == 0 and res["raw_raises"].sum() == 0 and not res["complete"].any()


def test_the_interim_reads_stage_one_contrasts_only(P, fitted):
    m = P.make_model(fitted, solved(P, fitted, target="min"), (2, 512, 40))
    sim = P.simulate(m, np.random.default_rng(11), 20, 40)
    d1 = P.stage1_contrasts(sim, 25, 1024)
    assert d1.shape == (20, 25)
    assert np.array_equal(d1, (sim["T"]["S"][:, :25] - sim["Rr"]["S"][:, :25]) / 1024)


def test_the_vectorised_reading_is_m5_readings(P, monkeypatch):
    rng = np.random.default_rng(8)
    ens = np.arange(15) % 5
    W = P.weights(tuple(ens))
    d = rng.normal(0.001, 0.004, (6, 15))
    lo, hi = P.hull_batch(d, W)
    hi_d = d + rng.integers(0, 4, d.shape) / 1024
    elo, ehi = P.envelope_batch(d, hi_d, W)
    for r in range(6):
        assert (lo[r], hi[r]) == pytest.approx(MR.interval(d[r], ens, W))
        assert (elo[r], ehi[r]) == pytest.approx(MR.envelope(d[r], hi_d[r], ens, W))
    monkeypatch.setattr(MR, "WELCH_TOO", True)  # the proposal under review, vectorised the same way
    lo, hi = P.hull_batch(d, W)
    elo, ehi = P.envelope_batch(d, hi_d, W)
    for r in range(6):
        assert (lo[r], hi[r]) == pytest.approx(MR.interval(d[r], ens, W))
        assert (elo[r], ehi[r]) == pytest.approx(MR.envelope(d[r], hi_d[r], ens, W))
    monkeypatch.setattr(MR, "WELCH_TOO", False)
    keep = np.arange(15) != 4
    Wk = P.weights(tuple(ens[keep]))
    l2, h2 = P.welch_batch(d[:, keep], ens[keep], Wk)
    for r in range(6):
        assert (l2[r], h2[r]) == pytest.approx(MR.interval(d[r, keep], ens[keep], Wk))


def test_the_audit_adjustment_counts_nothing_twice(P):
    z = np.zeros((1, 5), int)
    arm = lambda S, aud, trans, fun: {"S": np.array([S]), "U": z + 0, "Fun": np.array([fun]), "aud": np.array([aud]),
                                      "trans": np.array([trans])}  # noqa: E731
    sim = {"T": arm([3, 1, 2, 0, 1], [40] * 5, [0] * 5, [470] * 5),
           "Rr": arm([1, 1, 1, 1, 1], [40, 40, 40, 40, 40], [1, 0, 0, 0, 0], [470] * 5)}
    num = P.contrasts(sim)
    assert num["raw"].tolist() == [[2, 0, 1, -1, 0]]  # the observed transition is already in Rr's raw count
    assert num["audit"] == pytest.approx(num["raw"] - 470 / 200)  # the rate 1/200 on the unaudited fading only
    assert num["audit_unres_Rr"] == pytest.approx(num["audit"])


@pytest.mark.parametrize("kw", [{}, {"spread": "proportional"}, {"spread": "sparse"}, {"tau": "Rr"},
                                {"latent": "Rr"}, {"delta": -0.002}])
def test_the_effect_is_calibrated_on_the_whole_protocol(P, fitted, kw):
    sc = P.replace(solved(P, fitted, target="core"), **kw)
    m = P.make_model(fitted, sc, (2, 512, 40))
    res = P.run_cell(m, 30, 8000, "test-calibration")
    se = res["protocol"].std() / np.sqrt(len(res["protocol"]))
    assert abs(res["protocol"].mean() - sc.delta) < 4 * se


@pytest.mark.parametrize("kw", [{"delta": 0.0}, {"spread": "proportional"}, {"tau": "Rr", "delta": 0.0},
                                {"spread": "pm", "delta": 0.0}, {"latent": "Rr"}])
def test_the_calibration_is_exact(P, fitted, kw):
    """The quadrature expectations against the mean over a million simulated hosts' first-pass probabilities."""
    sc = P.replace(solved(P, fitted, target="core"), **kw)
    m = P.make_model(fitted, sc, (2, 512, 40))
    rng = np.random.default_rng(13)
    R, H = 1000, 1000
    he = P.draw_hosts(m, rng, R, H)
    p = P.first_pass_probs(m, he, P.effect_weights(m, rng, R, H), rng, R, H, 1)
    for a in P.ARMS:
        x = p[a]
        pF = 1 - x["S"] - x["U"] - x["O"] - x["L"]
        per = (x["S"] + x["U"] * fitted["second"][a]["S"] + P.tau_of(m, a) * pF * 40 / 512).ravel()
        assert P.expected_raw(m, m.inc, a) == pytest.approx(per.mean(), abs=4 * per.std() / np.sqrt(per.size))
    target = 0.0 if sc.spread == "pm" else sc.delta
    assert P.expected_raw(m, m.inc, "T") - P.expected_raw(m, m.inc, "Rr") == pytest.approx(target, abs=1e-12)


def test_the_false_raises_rate_is_near_nominal(P, fitted):
    m = P.make_model(fitted, P.replace(solved(P, fitted, target="min"), delta=0.0), (2, 512, 40))
    res = P.run_cell(m, 30, 20_000, "test-null")
    rate = res["raw_raises"].mean()
    assert rate <= 0.025 + 3 * np.sqrt(0.025 * 0.975 / 20_000)
    assert res["success"].mean() <= rate


def test_power_rises_with_the_effect(P, fitted):
    sc = solved(P, fitted, target="min")
    pw = [P.run_cell(P.make_model(fitted, P.replace(sc, delta=d), (2, 512, 40)), 25, 4000, "test-mono")["success"].mean()
          for d in (0.0, 0.002, 0.004)]
    assert pw[0] < pw[1] < pw[2]


def test_the_interim_writes_only_s2_and_h(P):
    table = {"variance": [1e-5, 2e-5, 4e-5], "H": [25, 45, 90]}
    rng = np.random.default_rng(9)
    d = rng.normal(0.002, 0.004, (50, 25))
    out = P.interim(d, table, 25, 70)
    assert set(out) == {"s2", "H"}
    assert np.array_equal(out["H"], P.interim(d + 0.01, table, 25, 70)["H"])  # a common shift moves nothing
    assert ((out["H"] % 5 == 0) & (out["H"] >= 25) & (out["H"] <= 70)).all()
    big = P.interim(rng.normal(0, 0.02, (5, 25)), table, 25, 70)["H"]
    assert (big == 70).all()
    s75 = d.var(1, ddof=1) * 24 / stats.chi2.ppf(0.25, 24)
    expect = np.clip(np.ceil(np.interp(s75, table["variance"], table["H"]) / 5) * 5, 25, 70)
    assert np.array_equal(out["H"], expect)


# ------------------------------------------------------------------------------------- results review, round 1 fixes
def test_rrs_host_and_draw_parts_are_fitted_jointly(P, fitted):
    """Astra: Rr's host SD fitted without its draw term counted the draw twice. Jointly, the host SD and the draw SD
    reproduce both Rr's host-count variance and the pilot's draw component."""
    s = fitted["classes"]["S1"]
    sd_r, sd_v = s["sd"]["Rr"], fitted["sd_v"]
    rate = s["rate"]["Rr"]
    assert P.count_var(rate, sd_r, 1024, 2, sd_v) == pytest.approx(s["count_var"]["Rr"], rel=1e-6)
    assert sd_r == pytest.approx(0.478, abs=0.005) and sd_v == pytest.approx(0.192, abs=0.005)


def test_the_host_component_is_computed_by_quadrature(P, fitted):
    """Astra: the solver's host component sampled 200,000 hosts (1.5200e-5 against 1.5102e-5 by quadrature)."""
    sd0 = fitted["classes"]["S1"]["sd_pooled"]
    sc = solved(P, fitted, target="core")
    a = P.host_component(fitted, P.RATE_RR, sd0, sc.rho, fitted["sd_v"])
    b = P.host_component(fitted, P.RATE_RR, sd0, sc.rho, fitted["sd_v"], seed=99)
    assert a == b == pytest.approx(1.52e-5, rel=1e-6)  # no sampling: the seed changes nothing


def test_rule_c_leaves_invalid_hosts_out_and_stops_when_an_ensemble_runs_short(P, fitted):
    """Astra: run_c dropped `invalid`, so invalid hosts entered the interim and the reading."""
    table = {"variance": [1e-6, 1e-4], "H": [10, 15]}
    m = P.make_model(fitted, P.replace(solved(P, fitted, target="min"), invalid=1.0), (1, 512, 40))
    s = P.run_c({}, m, 10, 15, table, 50, "test-c-invalid", cap=1e12)
    assert s["complete"] == 0.0 and s["success"] == 0.0


def test_the_interim_ignores_invalid_hosts():
    import m5_power as P
    rng = np.random.default_rng(16)
    d = rng.normal(0.002, 0.004, (4, 20))
    table = {"variance": [1e-6, 1e-4], "H": [20, 60]}
    dm = d.copy()
    dm[:, 3] = np.nan  # an invalid host
    out = P.interim(dm, table, 20, 60)
    v = np.array([np.var(np.delete(r, 3), ddof=1) for r in d])
    assert out["s2"] == pytest.approx(v)
    s75 = v * 18 / stats.chi2.ppf(0.25, 18)
    assert np.array_equal(out["H"], np.clip(np.ceil(np.interp(s75, table["variance"], table["H"]) / 5) * 5, 20, 60))


def test_rule_c_reports_the_stage_one_audit_bound(P, fitted):
    table = {"variance": [1e-6, 1e-4], "H": [10, 15]}
    m = P.make_model(fitted, solved(P, fitted, target="min"), (1, 512, 40))
    s = P.run_c({}, m, 10, 15, table, 100, "test-c-stage1", cap=1e12)
    for a in P.ARMS:
        assert 0.0 <= s[f"cover_tau_stage1_{a}"] <= 1.0 and 0.0 <= s[f"cover_tau_{a}"] <= 1.0


def test_the_exclusion_survives_an_invalid_host(P, fitted):
    """Astra: with one invalid host the exclusion was never attempted, though every leave-one-out reading is valid."""
    m = P.make_model(fitted, solved(P, fitted, target="min"), (1, 512, 40))
    z = np.zeros((1, 20), int)
    arm = {"S": z + 3, "U": z + 1, "Fun": z + 470, "aud": z + 39, "trans": z + 0, "hidden": z + 0, "L": z + 0,
           "seconds": z + 1.0, "U1": z + 1, "uF": z + 0}
    sim = {"rejected": 0, "T": dict(arm), "Rr": dict(arm), "invalid": np.zeros((1, 20), bool)}
    sim["invalid"][0, 7] = True
    out = P.readings(sim, m, 20, cap=None, exclusion=True)
    assert out["exclusion"][0]


def test_the_simulation_reports_what_the_check_compares(P, fitted):
    """The first-to-final counts (first-pass unresolved, and those becoming fading) are in the simulation's output."""
    m = P.make_model(fitted, solved(P, fitted, target="min"), (2, 512, 40))
    sim = P.simulate(m, np.random.default_rng(17), 50, 10)
    for a in P.ARMS:
        assert (sim[a]["uF"] <= sim[a]["U1"]).all() and sim[a]["U1"].sum() > 0


def test_rule_cs_invalid_panel_sensitivities_are_run_at_the_nominated_policy(P, fitted, tmp_path, monkeypatch):
    """Astra, results round 1: report C's invalid-panel sensitivity. Descriptive, at the nominated policy and H_max."""
    monkeypatch.setattr(P, "OUT", tmp_path)
    sol = solved(P, fitted, target="core")
    alloc = (1, 512, 40)
    rec = {"fit": {"fitted": fitted, "scenarios": {f"core|pilot|{P.RATE_RR}": {"rho": sol.rho, "scale": sol.scale}}},
           "caps": {f"{alloc}|15": 1e12},
           "c": {"status": "confirmed", "nominated": str(alloc), "h1": 10, "hmax": 15,
                 "explore": {str(alloc): {"table": {"variance": [1e-6, 1e-4], "H": [10, 15]}}}}}
    P.stage_c_sens(rec, R=40)
    rows = rec["c"]["sensitivity"]
    assert set(rows) == {"invalid 1% per panel, core", "unequal ensemble spreads, 5% invalid, core"}
    for s in rows.values():
        assert s["runs"] == 40 and 0.0 <= s["complete"] <= 1.0 and 10 <= s["H"]["mean"] <= 15


# ------------------------------------------------------------------------------------- results review, round 2 fixes
def test_the_adopted_reading_holds_the_welch_t_by_default(monkeypatch):
    """D372: M5's reading adds the stratum-aware Welch t to the balanced hull (both reviewers, results round 2), by
    default and not through an environment flag (Fable)."""
    import importlib
    monkeypatch.delenv("M5_WELCH_TOO", raising=False)
    assert importlib.reload(MR).WELCH_TOO is True


def test_an_invalid_hosts_audit_cannot_change_the_valid_reading(P, fitted):
    """Astra, results round 2: an invalid host's audit entered the pooled rate, the audit bound and the hidden-count
    coverage. Changing only the invalid host's audit data must change nothing that is read."""
    m = P.make_model(fitted, solved(P, fitted, target="min"), (1, 512, 40))
    z = np.zeros((1, 20), int)

    def sim_with(trans, hidden):
        def arm(s):
            return {"S": z + s, "U": z + 1, "Fun": z + 470, "aud": z + 39, "trans": z + 0, "hidden": z + 0,
                    "L": z + 0, "seconds": z + 1.0, "U1": z + 1, "uF": z + 0}
        sim = {"rejected": 0, "T": arm(4), "Rr": arm(3), "invalid": np.zeros((1, 20), bool)}
        sim["invalid"][0, 7] = True
        sim["Rr"]["trans"][0, 7], sim["Rr"]["hidden"][0, 7] = trans, hidden
        return sim

    a = P.readings(sim_with(0, 0), m, 20, cap=None, exclusion=False)
    b = P.readings(sim_with(2, 30), m, 20, cap=None, exclusion=False)
    assert a["success"][0]
    for k in a:
        if k != "latent" and a[k] is not None:
            assert np.array_equal(a[k], b[k], equal_nan=True), k


def test_stage_ones_audit_bound_reads_stage_one_valid_hosts_only(P):
    """Fable, results round 2: the stage-1 bound's test only checked its range. Stage 2's transitions and an invalid
    stage-1 host's must not enter it."""
    aud = np.full((2, 20), 39)
    tr = np.zeros((2, 20), int)
    tr[:, 10:] = 39  # stage 2 carries transitions
    valid = np.ones((2, 20), bool)
    valid[1, 3] = False
    tr[1, 3] = 39  # an invalid stage-1 host's transitions
    ub = P.stage1_bound(aud, tr, valid, 10)
    assert ub == pytest.approx([stats.beta.ppf(0.95, 1, 390), stats.beta.ppf(0.95, 1, 351)])


def test_rule_c_keeps_its_cap_its_rescalings_and_its_own_cost_tail(P, fitted):
    """Fable and Astra, results round 2: C's rows carry the cap, the rescaled-draw count, and the share of runs over
    1.25 times C's own mean cost (over_125 is against the fixed-H reference mean)."""
    table = {"variance": [1e-6, 1e-4], "H": [10, 15]}
    m = P.make_model(fitted, solved(P, fitted, target="min"), (1, 512, 40))
    s = P.summarise_short(P.run_c({}, m, 10, 15, table, 60, "test-c-fields", cap=1e12))
    assert s["cap_seconds"] == 1e12 and s["capped_draws"] is not None and 0.0 <= s["over_125_own_mean"] <= 1.0


def test_each_reading_writes_to_its_own_folder_by_default(P):
    """Astra, results round 3: with the Welch reading the default, the bare command wrote into the folder of the reading
    as first written, whose cached allocation search stage C would reuse."""
    root = P.ROOT / "runs"
    assert P.default_out({}) == root / "memory-m5-power-welch"
    assert P.default_out({"M5_WELCH_TOO": "0"}) == root / "memory-m5-power"
    assert P.default_out({"M5_WELCH_TOO": "0", "M5_POWER_OUT": "x"}) == Path("x")
