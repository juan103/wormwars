"""Sabotage runs for M5's power-calculation tests (rule 9; docs/memory/M5-POWER-DESIGN.md, section 7): each breaks
one thing a test guards, and that test must then fail. Prints one line per sabotage.
Usage: python scripts/memory_m5/sabotage_m5_power.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
import numpy as np  # noqa: E402
import pytest  # noqa: E402
from scipy import stats  # noqa: E402

import m5_power as P  # noqa: E402
import m5_reading as MR  # noqa: E402

TESTS = "tests/test_memory_m5_power.py::"


class Patch:
    def __init__(self, patch):
        self.patch, self.saved = patch, []

    def pytest_configure(self, config):
        for mod, k, v in self.patch:
            self.saved.append((mod, k, getattr(mod, k)))
            setattr(mod, k, v)

    def pytest_unconfigure(self, config):
        for mod, k, v in reversed(self.saved):
            setattr(mod, k, v)


def run(label, patch, test):
    rc = pytest.main(["-q", "-p", "no:cacheprovider", TESTS + test], plugins=[Patch(patch)])
    print(f"### {label}: {'fails, as it must' if rc != 0 else 'PASSES (the test does not guard it)'}", flush=True)
    return rc != 0


# ---------------------------------------------------------------------------------------------------- the reading
resample = MR.resample_weights


def across(ens, b=MR.B, seed=0, stratified=True, return_idx=False):  # the bootstrap resamples across ensembles
    return resample(ens, b, seed, stratified=False, return_idx=return_idx)


def plain_mean(d, ens):  # weights not 1/5 when the ensembles are unequal
    return float(np.mean(d))


def always_balanced(ens):  # the plain-s^2 t used after a deletion
    MR._groups(ens)
    return True


def envelope_min(lo_d, hi_d, ens, W, level=MR.LEVEL):  # an invalid bound: sum of min in place of sum of max
    lo_d, hi_d = np.asarray(lo_d, float), np.asarray(hi_d, float)
    blo, _ = MR.boot_interval(lo_d, W, level)
    _, bhi = MR.boot_interval(hi_d, W, level)
    mlo, mhi = MR.estimate(lo_d, ens), MR.estimate(hi_d, ens)
    c = (mlo + mhi) / 2
    se = np.sqrt(np.minimum((lo_d - c) ** 2, (hi_d - c) ** 2).sum() / (len(lo_d) - 1) / len(lo_d))
    t = stats.t.ppf(0.5 + level / 2, len(lo_d) - 1)
    return min(blo, mlo - t * se), max(bhi, mhi + t * se)


def envelope_pooled(lo_d, hi_d, ens, W, level=MR.LEVEL):  # the pooled bound used with Welch intervals
    lo_d, hi_d = np.asarray(lo_d, float), np.asarray(hi_d, float)
    blo, _ = MR.boot_interval(lo_d, W, level)
    _, bhi = MR.boot_interval(hi_d, W, level)
    mlo, mhi = MR.estimate(lo_d, ens), MR.estimate(hi_d, ens)
    c = (mlo + mhi) / 2
    groups = MR._groups(ens)
    bound = np.maximum((lo_d - c) ** 2, (hi_d - c) ** 2).sum() / (len(lo_d) - 1)
    se = np.sqrt(bound * sum(1.0 / (25 * len(g)) for g in groups))
    t = stats.t.ppf(0.5 + level / 2, len(lo_d) - 1)
    return min(blo, mlo - t * se), max(bhi, mhi + t * se)


NO_RR_UNRES = tuple(q for q in MR.QUALIFIERS if q[0] != "unres_Rr")  # the Rr-side unresolved check dropped


# ------------------------------------------------------------------------------------------------- the simulation
draw_hosts = P.draw_hosts


def unpaired(m, rng, R, H):  # the arms drawn from different hosts' propensities
    he = draw_hosts(m, rng, R, H)
    other = draw_hosts(m, rng, R, H)
    he["S"]["Rr"] = other["S"]["Rr"]
    return he


contrasts = P.contrasts


def twice(sim):  # an observed transition counted twice
    num = contrasts(sim)
    num = dict(num)
    num["audit"] = num["audit"] + sim["T"]["trans"] - sim["Rr"]["trans"]
    return num


def on_audited(sim):  # the adjustment applied to audited genomes too
    T, Rr = sim["T"], sim["Rr"]
    th = {a: np.where(sim[a]["aud"].sum(1) > 0, sim[a]["trans"].sum(1) / np.maximum(sim[a]["aud"].sum(1), 1), 0)
          for a in P.ARMS}
    num = dict(contrasts(sim))
    num["audit"] = (T["S"] + th["T"][:, None] * (T["Fun"] + T["aud"])) - (Rr["S"] + th["Rr"][:, None] * (Rr["Fun"] + Rr["aud"]))
    return num


def fading_only(rng, F1, G, A):  # audit ids drawn from the first-pass fading genomes only
    return np.minimum(F1, A)


def independent_counts(rng, G, probs):  # each class drawn on its own, so a panel can exceed G
    return tuple(rng.binomial(G, probs[..., i]) for i in range(5))


calibrate = P.calibrate


def uncalibrated(m):  # delta applied as the effect term directly
    return m.sc.delta


def first_pass_only(m):  # calibrated on the first pass only (audited transitions and the U->S path ignored)
    if m.sc.spread == "proportional":
        sd_tot = np.sqrt(m.sd ** 2 + m.sc.extra_w ** 2)
        return float(P.optimize.brentq(lambda b: P.mean_p(m.mu["S"]["T"] + b, sd_tot) - m.sc.rate_rr - m.sc.delta,
                                       -3.0, 3.0))
    return abs(m.sc.delta)


readings = P.readings


def drops_incomplete(sim, m, H, cap=None, exclusion=True):  # incomplete runs read as if complete
    return readings(sim, m, H, cap=None, exclusion=exclusion)


def with_stage2(sim, h1, n):  # the interim reads stage 2's hosts too
    return (sim["T"]["S"] - sim["Rr"]["S"]) / n


def arm_rates(sim, h1, n):  # the interim reads T's rates instead of the contrasts
    return sim["T"]["S"][:, :h1] / n


interim = P.interim


def with_mean(d1, table, h1, hmax):  # the interim writes the mean out
    out = interim(d1, table, h1, hmax)
    return {**out, "mean": np.asarray(d1).mean(-1)}


def main():
    ok = [
        run("bootstrap across ensembles", [(MR, "resample_weights", across)],
            "test_the_stratified_bootstrap_resamples_within_each_ensemble"),
        run("estimate's weights not 1/5", [(MR, "estimate", plain_mean)],
            "test_the_estimate_weights_each_ensemble_a_fifth"),
        run("plain-s2 t after a deletion", [(MR, "balanced", always_balanced)],
            "test_the_unbalanced_t_is_welchs_and_catches_variance_in_the_pair"),
        run("Rr-side unresolved check dropped", [(MR, "QUALIFIERS", NO_RR_UNRES)],
            "test_success_needs_all_six_readings"),
        run("envelope bound with sum of min", [(MR, "envelope", envelope_min)],
            "test_the_envelope_contains_every_corner"),
        run("pooled envelope bound with Welch", [(MR, "envelope", envelope_pooled)],
            "test_the_unbalanced_envelope_holds_astras_box"),
        run("arms unpaired", [(P, "draw_hosts", unpaired)], "test_the_arms_share_their_host_effects"),
        run("transition counted twice", [(P, "contrasts", twice)], "test_the_audit_adjustment_counts_nothing_twice"),
        run("adjustment on audited genomes", [(P, "contrasts", on_audited)],
            "test_the_audit_adjustment_counts_nothing_twice"),
        run("audit ids from fading genomes only", [(P, "audit_draw", fading_only)],
            "test_a_panel_is_coherent"),
        run("independent class counts", [(P, "first_pass_counts", independent_counts)], "test_a_panel_is_coherent"),
        run("effect uncalibrated", [(P, "calibrate", uncalibrated)],
            "test_the_effect_is_calibrated_on_the_whole_protocol"),
        run("calibrated on the first pass only", [(P, "calibrate", first_pass_only)],
            "test_the_effect_is_calibrated_on_the_whole_protocol"),
        run("incomplete runs dropped", [(P, "readings", drops_incomplete)], "test_an_incomplete_run_is_a_failure"),
        run("interim reads stage 2", [(P, "stage1_contrasts", with_stage2)],
            "test_the_interim_reads_stage_one_contrasts_only"),
        run("interim reads arm rates", [(P, "stage1_contrasts", arm_rates)],
            "test_the_interim_reads_stage_one_contrasts_only"),
        run("interim writes the mean", [(P, "interim", with_mean)], "test_the_interim_writes_only_s2_and_h"),
    ]
    print(f"{sum(ok)} of {len(ok)} sabotages fail by their tests")


if __name__ == "__main__":
    main()
