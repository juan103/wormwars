"""Sabotage runs for M5's pilot tests (rule 9): each breaks one thing a test guards, and that test must then fail.
Prints one line per sabotage. Usage: python scripts/memory_m5/sabotage_m5_pilot.py"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ["MEMORY_M5P_OUT"] = tempfile.mkdtemp(prefix="m5p-sabotage-")
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
import numpy as np  # noqa: E402
import pytest  # noqa: E402

import m5_pilot as MP  # noqa: E402
import m5_pilot_read as RP  # noqa: E402

TESTS = "tests/test_memory_m5_pilot.py::"


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


rewire = MP.m4d.rewire


def restarted(hd):  # the continued block drawn from a fresh generator instead of the same chain
    Bn = MP.m4d.n2_block()
    B1, ch1 = rewire(Bn, np.random.default_rng(MP.SEED_RR + hd), keep_recip=True)
    B2, ch2 = rewire(B1, np.random.default_rng(MP.SEED_RR + hd), keep_recip=True)
    return B1.astype(np.float32), B2.astype(np.float32), {"first": ch1, "continued": ch2}


sim = MP.similarity


def unsplit(B, Bn):  # every shared edge counted as reciprocal
    s = sim(B, Bn)
    return {**s, "shared_reciprocal_edges": s["shared_edges"], "shared_nonreciprocal_edges": 0}


check_rr = MP.check_rr


def no_recip_check(B):  # the reciprocal-pair rule dropped
    s = MP.m4d.block_stats(B)
    if s["reciprocal"] != MP.N_RECIP:
        return
    check_rr(B)


def audited_too(recs):  # the pool keeps genomes an audit already touched
    pool = []
    for p, rec in enumerate(recs):
        pool += [(p, i) for i, x in enumerate(rec["class"]) if x == MP.FADING]
    return pool


split = RP.variance_split
sample = MP.audit_sample


def swapped(d, pa, pb, n):  # draw and genome parts exchanged
    v = split(d, pa, pb, n)
    return {**v, "draw": v["genome"], "genome": v["draw"]}


def from_start(gs, cfg, end, y, ticks):  # the oscillation rerun follows the whole hold, not the recorded tail
    run = MP.m4e.continue_hold(gs, cfg, end, ticks)
    run["y"] = y
    recs, _ = MP.P.full_classify(gs, cfg, run, compact=True, initial=end.to(run["pre_tail"].dtype),
                                 follow_ticks=ticks + MP.m4e.TAIL, tail_from=ticks + 1)
    return run["end"], recs


def classes_only(label, got, want, exact=False):
    return check_replay(label, [{"class": x["class"]} for x in got], [{"class": x["class"]} for x in want])


check_replay = MP.check_replay
replay = MP.replay


def alone(g, cfg, ids):  # no companion: a batch of one runs alone
    gs = g.select(list(ids))
    run = MP.P.probe_states(gs, cfg)
    sub = {"end": run["end"], "cur": run["cur"], "y": run["y"], "tail": run["tail"]}
    recs, _ = MP.P.full_classify(gs, cfg, sub, compact=True)
    return gs, run, recs, list(ids)


def ids_only(out, ids, cols, label):
    if out.get("ids") != ids:
        raise MP.Stop(label)


longer_report = RP.longer_report
check_out = MP.check_out
contrast = RP.contrast
validate_rr = MP.validate_rr


def lax_rr(rec, r, d, digest):  # the second-pass column lengths unchecked
    try:
        validate_rr(rec, r, d, digest)
    except MP.Stop as e:
        if "second-pass column" not in str(e):
            raise


def rule_anyway(rows, missing):
    out = longer_report(rows, [])
    return {**out, "complete": not missing}


results = [
    run("the Rr check disabled", [(MP, "check_rr", lambda B: None)], "test_the_rr_check_catches_each_rule"),
    run("the reciprocal-pair rule dropped", [(MP, "check_rr", no_recip_check)],
        "test_the_rr_check_catches_a_lost_reciprocal_pair"),
    run("the chain restarted, not continued", [(MP, "rr_blocks", restarted)], "test_the_chain_is_continued_not_restarted"),
    run("the similarity without its split", [(MP, "similarity", unsplit)],
        "test_the_similarity_splits_reciprocal_edges"),
    run("a pilot seed inside M4e's audit family", [(MP, "SEED_RR", 20261701)], "test_the_seed_families_do_not_meet_m4e"),
    run("the replay check disabled", [(MP, "check_replay", lambda label, got, want, exact=False: 0.0)],
        "test_the_replay_stops_on_a_different_output"),
    run("the replay comparing classes only", [(MP, "check_replay", classes_only)],
        "test_the_replay_stops_on_a_different_output"),
    run("the tolerance on the write amplitude too", [(MP, "ROOT_FIELDS", ("a",) + MP.ROOT_FIELDS)],
        "test_the_replay_stops_on_a_different_output"),
    run("the composition check not exact", [(MP, "check_replay", lambda label, got, want, exact=False:
                                             check_replay(label, got, want))],
        "test_the_replay_stops_on_a_different_output"),
    run("a batch of one replayed alone", [(MP, "replay", alone)],
        "test_a_batch_of_one_gets_a_discarded_companion"),
    run("the state check disabled", [(MP, "state_check", lambda g, cfg, part, run: [])],
        "test_the_state_check_compares_the_hold_with_the_chunk"),
    run("a stage file checked without its source", [(MP, "check_out", lambda out, ids, cols, label, expect=None,
                                                      rec=None: check_out(out, ids, cols, label))],
        "test_a_stage_file_is_checked_against_its_source"),
    run("the remedy continuing whatever the panel rerun gives", [(MP, "fallback_holds", lambda rerun, want: True)],
        "test_the_failure_remedy_continues_only_on_an_exact_panel_rerun"),
    run("no remedy: every failure stops", [(MP, "checked", lambda label, got, want, *a: check_replay(label, got,
                                                                                                    want))],
        "test_the_failure_remedy_continues_only_on_an_exact_panel_rerun"),
    run("the composition file trusted", [(MP, "check_composition_file", lambda obj, verified, recs: None)],
        "test_the_composition_file_must_be_the_plans_passed_check"),
    run("the reader's contrast with its arms reversed", [(RP, "contrast", lambda panels, a, b, n, hosts:
                                                           contrast(panels, b, a, n, hosts))],
        "test_the_reader_reproduces_m4es_t_minus_k"),
    run("the output folder unguarded", [(MP, "check_out_dir", lambda out: None)],
        "test_the_output_folder_cannot_be_m4e_or_m4d"),
    run("stage files skipped on their ids alone", [(MP, "check_out", ids_only)], "test_incomplete_records_are_refused"),
    run("an Rr record's second-pass columns unchecked", [(MP, "validate_rr", lax_rr)],
        "test_an_rr_record_without_its_second_pass_is_refused"),
    run("the genome part unpaired", [(RP, "variance_split", lambda d, pa, pb, n, p11=None: split(d, pa, pb, n))],
        "test_the_paired_genome_part_is_zero_for_identical_outcomes"),
    run("the horizon rule applied to an incomplete stage", [(RP, "longer_report", rule_anyway)],
        "test_the_horizon_rule_waits_for_a_complete_stage"),
    run("the audit pool keeping audited genomes", [(MP, "audit_pool", audited_too)],
        "test_the_audit_sample_is_unaudited_fading_and_fixed"),
    run("one generator for every arm's audit", [(MP, "audit_sample", lambda recs, arm, n=MP.BIG_AUDIT:
                                                  sample(recs, "T", n))],
        "test_the_audit_sample_is_unaudited_fading_and_fixed"),
    run("the horizon rule strict at 0.5", [(RP, "horizon_rule", lambda s: "continue to 100,000 ticks" if s > 0.5 else
                                            "keep 22,000 ticks")], "test_the_horizon_rule_at_its_boundary"),
    run("a two-sided bound in place of the one-sided", [(RP, "cp_upper", lambda x, n, level=0.95:
                                                          1.0 if n == 0 or x >= n else
                                                          float(RP.stats.beta.ppf(0.975, x + 1, n - x)))],
        "test_clopper_pearson_upper_bounds"),
    run("the variance's draw and genome parts swapped", [(RP, "variance_split", swapped)],
        "test_the_variance_split_recovers_known_components"),
    run("extend's rerun from the start of the hold", [(MP, "extend", from_start)],
        "test_extend_classifies_as_the_second_pass"),
]
print(f"{sum(results)} of {len(results)} sabotages fail as they must")
