"""Sabotage runs for M4d's tests (rule 9): each breaks one thing a test guards, and that test must then fail. Prints one
line per sabotage. Usage: python scripts/memory_m4/sabotage_m4d.py"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MEMORY_M4D_OUT", tempfile.mkdtemp(prefix="m4d-sabotage-"))
os.environ.setdefault("MEMORY_M4D_SMOKE", "1")
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "tests"))
import numpy as np  # noqa: E402
import pytest  # noqa: E402
import torch  # noqa: E402

import m4d  # noqa: E402
import m4d_read  # noqa: E402
import m4d_tables  # noqa: E402
import test_memory_m4d as T  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402


class MP:  # a minimal monkeypatch for the one test that takes it
    def __init__(self):
        self.saved = []

    def setattr(self, mod, k, v):
        self.saved.append((mod, k, getattr(mod, k)))
        setattr(mod, k, v)

    def undo(self):
        for mod, k, v in reversed(self.saved):
            setattr(mod, k, v)


def fails(fn):
    mp = MP()
    try:
        fn(mp) if fn.__code__.co_argcount else fn()
    except (AssertionError, SystemExit, pytest.fail.Exception):
        return True
    finally:
        mp.undo()
    return False


def run(label, patch, test):
    saved = [(mod, k, getattr(mod, k)) for mod, k, _ in patch]
    for mod, k, v in patch:
        setattr(mod, k, v)
    try:
        print(f"{label}: {'fails, as it must' if fails(test) else 'PASSES (the test does not guard it)'}", flush=True)
    finally:
        for mod, k, v in saved:
            setattr(mod, k, v)


def redrawn(g_host, con, signs):  # the arm genome drawn by Genome.random on the arm's graph
    spec = BrainSpec.from_connectome(con, device="cpu")
    return Genome.random(spec, g_host.cfg, g_host.n_strains, generator=torch.Generator().manual_seed(7998), device="cpu")


def fresh_signs(g_host, n, seed):  # the signs drawn fresh everywhere, the host's edges included
    k = m4d.core_idx()
    return np.where(np.random.default_rng(seed).random((n, len(k), len(k))) < 0.5, -1.0, 1.0)


orig_classify = m4d.classify_all


def with_floor(g, cfg):  # the census's eligibility floor restored
    cols, val = orig_classify(g, cfg)
    keep = [i for i, a in enumerate(cols["a"]) if a >= m4d.c.START_FLOOR]
    return {k: [v[i] for i in keep] for k, v in cols.items()}, val


def unconstrained(B, rng, keep_recip=False):  # R without the degree constraint: edges placed anywhere off the diagonal
    n = len(B)
    off = ~np.eye(n, dtype=bool)
    w = B[off & (B > 0)]
    pos = np.argwhere(off)
    take = pos[rng.choice(len(pos), len(w), replace=False)]
    out = np.zeros_like(B)
    out[take[:, 0], take[:, 1]] = rng.permutation(w)
    out[np.arange(n), np.arange(n)] = np.diag(B)
    return out, {"accepted": 20 * len(w), "attempted": 20 * len(w)}


orig_reading = m4d_read.reading


def no_margin(ti, tr, m=m4d_read.MARGIN):
    return orig_reading(ti, tr, 0.0)


def genome_resampled(d, idx):  # genomes resampled within hosts as well: binomial noise added to each resample
    rng = np.random.default_rng(0)
    m = (d[idx] + rng.normal(0, 0.003, idx.shape)).mean(1)
    return float(np.percentile(m, 5)), float(np.percentile(m, 95))


orig_read = m4d_read.read


orig_validate = m4d.validate


def hash_ignored(rec, r, arm, digest):
    return orig_validate({**rec, "arm_sha256": digest}, r, arm, digest)


def extremes_only(lo_d, hi_d, idx, use_t):  # the two all-one-way assignments, without the corners
    a = m4d_read.interval(lo_d, idx, use_t)
    b = m4d_read.interval(hi_d, idx, use_t)
    return min(a[0], b[0]), max(a[1], b[1])


def main_unverified():  # the reader reading the saved panels without verify_run
    import json
    raise SystemExit(json.dumps({"read": "without checks"}))


def unbounded(sep, unres, n, use_t, seed=m4d_read.SEED_BOOT):  # the unresolved bounds ignored
    out = orig_read(sep, unres, n, use_t, seed)
    out["robust"], out["reading"] = True, out["reading_before_bounds"]
    return out


if __name__ == "__main__":
    run("the arm genome redrawn on the arm's graph", [(m4d, "paired_genome", redrawn)], T.test_the_paired_genomes)
    run("the signs drawn fresh at the host's block edges", [(m4d, "sign_matrix", fresh_signs)],
        T.test_the_paired_genomes)
    run("the eligibility floor restored", [(m4d, "classify_all", with_floor)],
        T.test_every_genome_is_classified_without_a_floor)
    run("R without the degree constraint", [(m4d, "rewire", unconstrained)], T.test_the_blocks_keep_what_the_plan_says)
    run("the block checks not applied", [(m4d, "check_blocks", lambda b: None)], T.test_a_block_breaking_a_rule_is_rejected)
    run("the outside of the block not checked", [(m4d, "check_outside", lambda h, c_: None)],
        T.test_the_arm_graph_changes_only_the_block)
    run("the sham check not applied", [(m4d, "sham_check", lambda g, h, s: None)],
        T.test_the_sham_check_catches_a_redrawn_genome)
    run("the reading without the margin", [(m4d_read, "reading", no_margin)], T.test_the_readings_boundaries)
    run("genomes resampled within hosts", [(m4d_read, "boot_interval", genome_resampled)], T.test_the_host_bootstrap)
    run("the unresolved bounds ignored", [(m4d_read, "read", unbounded)], T.test_the_unresolved_genomes_bound_the_reading)
    run("records not validated", [(m4d, "validate", lambda rec, r, a, d: None)], T.test_records_are_validated)
    run("the arm's content hash not checked", [(m4d, "validate", hash_ignored)], T.test_records_are_validated)
    run("freshness not checked", [(m4d, "fresh", lambda n, d, u: True)], T.test_the_hosts_are_fresh)
    run("content hashed another way", [(m4d, "sha_content", lambda ch, gp: "x" + str(ch.sum()))],
        T.test_a_used_graph_is_recognised_by_its_content)
    run("the host list not checked", [(m4d, "check_host_list", lambda recs: None)], T.test_the_host_list_is_checked)
    run("the envelope from the two extreme assignments only", [(m4d_read, "envelope", extremes_only)],
        T.test_the_envelope_covers_one_host_assignments)
    run("the single-host guard removed", [(m4d_read, "guarded", lambda ti, tr, a, b, m=m4d_read.MARGIN,
                                           guard=m4d_read.HOST_GUARD: m4d_read.reading(ti, tr, m))],
        T.test_the_readings_boundaries)
    run("the simulation's widened interval not widened", [(m4d_read, "interval", lambda d, idx, use_t:
                                                          m4d_read.boot_interval(d, idx))],
        T.test_the_host_bootstrap)
    run("the companion copying the whole genome", [(m4d, "with_selected", lambda gf, gs: gs.clone())],
        T.test_the_companion_takes_only_the_block_and_core_parameters)
    run("the reader without verify_run", [(m4d_read, "main", main_unverified)], T.test_the_reader_checks_before_it_reads)
    run("the reader's panels not validated", [(m4d, "validate", lambda rec, r, a, d: None)],
        T.test_the_reader_validates_every_panel_against_its_arm_graph)
    run("one host read", [(m4d_read, "MIN_HOSTS", 1)], T.test_the_reader_validates_every_panel_against_its_arm_graph)
    run("the pairing ignored", [(m4d_read, "paired_counts", lambda pb, pt, pr, n, rng: (rng.binomial(n, pt),
                                                                                       rng.binomial(n, pb)))],
        T.test_the_paired_counts)
    run("the tables' digest check removed", [(m4d_tables, "check_digest", lambda s, d: None)],
        T.test_the_tables_stop_on_a_changed_blocks_file)
