"""Sabotage runs for M4e's tests (rule 9): each breaks one thing a test guards, and that test must then fail. Prints one
line per sabotage. Usage: python scripts/memory_m4/sabotage_m4e.py"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["MEMORY_M4E_OUT"] = tempfile.mkdtemp(prefix="m4e-sabotage-")
os.environ["MEMORY_M4E_SMOKE"] = "1"
os.environ["MEMORY_M4E_SMOKE_N"] = "8"
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import m4e  # noqa: E402
import m4e_read  # noqa: E402

P = m4e.P
TESTS = "tests/test_memory_m4e.py::"


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


draw = m4e.draw_blocks


def unnested(h, d, hb):  # the low support drawn on its own, not inside the high one
    out, info = draw(h, d, hb)
    off = ~np.eye(30, dtype=bool)
    pos = np.argwhere(off)
    lo = pos[np.random.default_rng(99).choice(len(pos), info["E_h"], replace=False)]
    for a in ("U_LL", "U_LH"):
        B = np.zeros((30, 30), np.float32)
        B[lo[:, 0], lo[:, 1]] = out[a][off & (out[a] > 0)][0]
        B[np.arange(30), np.arange(30)] = np.diag(out[a])
        out[a] = B
    info["low_support"] = lo.tolist()
    return out, info


def n2_diagonal(h, d, hb):  # N2's autapses in every arm
    out, info = draw(h, d, hb)
    Bn = m4e.m4d.n2_block()
    for a in out:
        out[a][np.arange(30), np.arange(30)] = np.diag(Bn)
    return out, info


cont = m4e.continue_hold


def pre_tail_late(gs, cfg, end, ticks, tail=200):  # the pre-tail state taken one tick late
    out = cont(gs, cfg, end, ticks, tail)
    out["pre_tail"] = cont(gs, cfg, end, ticks - tail + 1, 1)["end"].to(out["pre_tail"].dtype)
    return out


osc = P.oscillation_check
rc_ = m4e.match_recip
size = m4e_read.size
validate, check_host_list = m4e.validate, m4e.check_host_list


def old_slope(counts, n, x, iters=50):  # draft 1's: only an all-zero host has no slope
    y, x = np.asarray(counts, float), np.asarray(x, float)
    if y.sum() == 0:
        return None
    X = np.stack([np.ones_like(x), x], 1)
    beta = np.array([np.log(y.sum() / (n * len(y))), 0.0])
    for _ in range(iters):
        mu = n * np.exp(X @ beta)
        try:
            beta = beta + np.linalg.solve(X.T @ (X * mu[:, None]), X.T @ (y - mu))
        except np.linalg.LinAlgError:
            break  # its last value: the test's own check must catch it (Fable, round 2)
    return beta


def two_arm_rule(counts, n, x, iters=100):  # draft 2's: no slope with fewer than two switching arms
    if (np.asarray(counts) > 0).sum() < 2:
        return None
    return slope(counts, n, x, iters)


def pre_tail_shuffled(gs, cfg, end, ticks, tail=200):
    out = cont(gs, cfg, end, ticks, tail)
    out["pre_tail"] = out["pre_tail"].roll(1, 0)
    return out


def lax_second(rec, r, d, arm, digest):
    try:
        validate(rec, r, d, arm, digest)
    except m4e.Stop as e:
        if "second-pass" not in str(e):
            raise


def lax_hosts(recs):
    try:
        check_host_list(recs)
    except m4e.Stop as e:
        if "skipped" not in str(e):
            raise


def all_or_nothing(*a, **k):
    c = contrast(*a, **k)
    if c["size_before_bounds"] != c["envelope_size"]:
        c["size"] = [m4e_read.BY_UNRESOLVED]
    return c
contrast = m4e_read.contrast
slope = m4e_read.poisson_slope

results = [
    run("supports not nested", [(m4e, "draw_blocks", unnested)], "test_every_block_follows_the_plan"),
    run("N2's autapses in the U, W and K arms", [(m4e, "draw_blocks", n2_diagonal)], "test_every_block_follows_the_plan"),
    run("the block check disabled", [(m4e, "check_blocks", lambda b, i, h: None)],
        "test_the_block_check_catches_each_rule"),
    run("a reciprocal miss reported as matched", [(m4e, "match_recip", lambda W, t, rng: (rc_(W, t, rng)[0], {
        **rc_(W, t, rng)[1], "matched": True}))], "test_the_reciprocal_matching_records_a_miss"),
    run("the clamp check disabled", [(m4e, "check_clamp", lambda g, con: None)], "test_a_clamped_magnitude_stops"),
    run("the hold continued one tick too far", [(m4e, "continue_hold", lambda gs, cfg, end, ticks, tail=200:
                                                 cont(gs, cfg, end, ticks + 1, tail))],
        "test_the_hold_continued_from_tick_2000_equals_a_longer_probe"),
    run("the pre-tail state one tick late", [(m4e, "continue_hold", pre_tail_late)],
        "test_the_rerun_from_the_pre_tail_state_records_the_same_substeps"),
    run("the rerun recording the frozen ticks", [(P, "oscillation_check", lambda *a, **k: osc(*a, **{**k,
                                                                                                    "tail_from": 1801}))],
        "test_the_oscillation_rerun_follows_the_requested_horizon"),
    run("the rerun at the frozen length", [(P, "oscillation_check", lambda *a, **k: osc(*a, **{**k, "follow_ticks": 2000}))],
        "test_the_oscillation_rerun_follows_the_requested_horizon"),
    run("the merged classes from the first pass", [(m4e, "merged_classes", lambda rec: list(rec["class"]))],
        "test_merged_classes_and_the_audit"),
    run("the audit never failing", [(m4e, "audit_failed", lambda rec: False)], "test_merged_classes_and_the_audit"),
    run("the audit ids unseeded", [(m4e, "audit_ids", lambda h, d, a, n=None: sorted(
        int(x) for x in np.random.default_rng().choice(n or 8, 8, replace=False)))], "test_the_audit_ids_are_fixed"),
    run("the second pass not validated", [(m4e, "validate", lambda rec, r, d, a, dg: None)],
        "test_a_record_must_carry_the_planned_second_pass"),
    run("the direction at zero inclusive", [(m4e_read, "direction", lambda iv: "raises" if iv[0] >= 0 else
                                             ("lowers" if iv[1] < 0 else "direction unresolved"))],
        "test_the_two_fields_at_their_boundaries"),
    run("the single-host guard removed", [(m4e_read, "size", lambda iv, mx, exclusions_ok=True:
                                           size(iv, 0.0, exclusions_ok))], "test_the_two_fields_at_their_boundaries"),
    run("the coverage's response ignored", [(m4e_read, "size", lambda iv, mx, exclusions_ok=True: size(iv, mx, True))],
        "test_the_two_fields_at_their_boundaries"),
    run("the dose's MLE taken when it does not exist", [(m4e_read, "poisson_slope", old_slope)],
        "test_the_poisson_slope_recovers_a_known_dose"),
    run("the dose model keeping a host without a slope", [(m4e_read, "poisson_slope", old_slope)],
        "test_the_dose_model_leaves_out_a_host_without_a_slope"),
    run("a batch's pre-tail states out of order", [(m4e, "continue_hold", pre_tail_shuffled)],
        "test_a_batched_continuation_replays_one_genome_exactly"),
    run("second-pass codes and columns not checked", [(m4e, "validate", lax_second)],
        "test_a_second_pass_code_outside_the_classes_is_refused"),
    run("a fresh skipped seed accepted", [(m4e, "check_skips", lambda recs, used: None)],
        "test_a_fresh_skipped_seed_stops_the_hosts"),
    run("the tables taking the merged classes after a failed audit", [(m4e_read, "classes", lambda counts, key:
                                                                       m4e.merged_classes(counts["panels"][key]))],
        "test_a_failed_audit_puts_every_panel_back_on_its_first_pass"),
    run("the slope refused for an interior singleton", [(m4e_read, "poisson_slope", two_arm_rule)],
        "test_the_poisson_slope_recovers_a_known_dose"),
    run("a host seed jump unrecorded", [(m4e, "check_host_list", lax_hosts)], "test_a_host_seed_jump_must_be_recorded"),
    run("the reader's counts ignoring a failed audit", [(m4e, "audit_failed", lambda rec: False)],
        "test_a_failed_audit_puts_every_panel_back_on_its_first_pass"),
    run("a size sub-field dropped when the other differs", [(m4e_read, "contrast", all_or_nothing)],
        "test_a_size_field_holding_on_both_intervals_stands"),
    run("the envelope ignored", [(m4e_read, "contrast", lambda *a, **k: {**contrast(*a, **k), "direction": contrast(
        *a, **k)["direction_before_bounds"]})], "test_the_envelope_decides_when_the_unresolved_could"),
    run("one host read", [(m4e_read, "MIN_HOSTS", 1)], "test_the_reader_refuses_fewer_than_ten_hosts"),
    run("the Poisson model without its offset", [(m4e_read, "poisson_slope", lambda y, n, x, iters=50:
                                                  slope(y, 1, x, iters))], "test_the_poisson_slope_recovers_a_known_dose"),
    run("the reader without verify_run", [(m4e_read, "main", lambda: None)], "test_the_reader_checks_before_it_reads"),
]
print(f"{sum(results)} of {len(results)} sabotages fail as they must")
