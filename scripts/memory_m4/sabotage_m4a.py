"""Sabotage runs for M4a's tests (rule 9): each breaks one thing a test guards, and that test must then fail. Prints one
line per sabotage. Usage: python scripts/memory_m4/sabotage_m4a.py"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "tests"))
import m4a  # noqa: E402
import m4a_read  # noqa: E402
import test_memory_m4a as T  # noqa: E402


def fails(fn):
    try:
        fn()
    except AssertionError:
        return True
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


def cut_in_place(g, mask):  # zeroes the original genome's weights: the intact brain is never restored
    import torch
    g.w[torch.as_tensor(mask)] = 0
    return g


orig_follow = m4a.follow_arm


def never_restored(brain, brain_cut, cfg, v0, food, window, ticks, core_idx):
    return orig_follow(brain, brain_cut, cfg, v0, food, (window[0], ticks) if window else None, ticks, core_idx)


run("no bisection", [(m4a, "BISECT", 0)], T.test_the_matching_search)
run("controls matched at tick 10", [(m4a, "MATCH_TICK", 10)], T.test_the_match_uses_the_windows_third_tick_only)
run("the cut made in place", [(m4a, "cut", cut_in_place)], T.test_masks_and_the_cut)
run("the cut never restored", [(m4a, "follow_arm", never_restored)], T.test_the_window_switches_brains_and_back)
run("no margin", [(m4a_read, "MARGIN", 0.0)], T.test_the_readings_boundaries)
run("no collapse condition", [(m4a_read, "COLLAPSE", 10.0)], T.test_the_readings_boundaries)
run("any root counts as the same", [(m4a, "SAME_ROOT", 1.0)], T.test_part_2_outcomes)


def uniform_instead(spec, internal, external, n, seed):  # draft 2's idea: draws not stratified by endpoint degree
    return m4a.uniform_draws(internal, external, n, seed)


run("random cuts not degree-stratified", [(m4a, "stratified_draws", uniform_instead)],
    T.test_the_random_cuts_follow_c3s_endpoint_degrees)


# round 3
def boot_mean(x_int, x_c3, X_draws, rng, b=m4a_read.B):  # D against the draws' mean, not their maximum
    import numpy as np
    n = len(x_int)
    idx = rng.integers(0, n, (b, n))
    si = x_int[idx].sum(1)
    Lc = 1 - x_c3[idx].sum(1) / si
    Ld = 1 - np.stack([x[idx].sum(1) for x in X_draws]) / si
    q = lambda a: [float(np.percentile(a, 5)), float(np.percentile(a, 95))]  # noqa: E731
    return q(Lc), q(Lc - Ld.mean(0))


orig_strat = m4a.stratified_draws


def key_ignored(spec, internal, external, n, seed, key=None):  # the weight family stratified on degree after all
    return orig_strat(spec, internal, external, n, seed)


def gate_skipped(out):
    return None


run("D against the draws' mean", [(m4a_read, "boot_max", boot_mean)], T.test_the_readings_boundaries)
run("weight key ignored", [(m4a, "stratified_draws", key_ignored)], T.test_weight_stratified_draws_follow_c3s_weights)
import tempfile  # noqa: E402
from pathlib import Path as _P  # noqa: E402


class _MP:
    def __init__(self):
        self.undo = []

    def setattr(self, obj, name, value):
        self.undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)


def _gate_test():
    mp = _MP()
    try:
        with tempfile.TemporaryDirectory() as d:
            try:
                T.test_part_2s_gate_holds_on_a_restart(_P(d), mp)
            except BaseException as err:  # pytest's "DID NOT RAISE" is an outcome exception
                if type(err).__name__ == "Failed":
                    raise AssertionError("did not raise")
                raise
    finally:
        for obj, name, value in reversed(mp.undo):
            setattr(obj, name, value)


run("Part 2's gate skipped on restart", [(m4a, "part2_gate", gate_skipped)], _gate_test)

# M4b
import m4b  # noqa: E402
import m4b_read  # noqa: E402


def smallest_difference(roots_one, k=m4b.TOP):  # the k neurons where the roots differ least
    import numpy as np
    d = np.abs(roots_one[0] - roots_one[1])
    return np.argsort(d)[:k]


run("M4b: no margin", [(m4b_read, "MARGIN", 0.0)], T.test_m4b_reading_and_contrast)
run("M4b: the own set is where the roots differ least", [(m4b, "top_difference", smallest_difference)],
    T.test_m4b_own_location_sets)


def validate_nothing(p, ids, name=None, role=None):
    return None


def _validate_test():
    try:
        T.test_m4b_rejects_invalid_records()
    except BaseException as err:
        if type(err).__name__ == "Failed":
            raise AssertionError("did not raise")
        raise


run("M4b: records not validated", [(m4b, "validate", validate_nothing)], _validate_test)


def incoming_instead(spec, nodes):  # edges into the 30 neurons instead of out of them
    import numpy as np
    i, j = spec.chem_i.numpy(), spec.chem_j.numpy()
    inn = np.zeros(spec.n, bool)
    inn[list(nodes)] = True
    return np.where(~inn[i] & inn[j] & (i != j))[0]


run("M4b: incoming edges as the outgoing control", [(m4b, "out_edges", incoming_instead)], T.test_m4b_own_location_sets)


def trust_the_flag(p, ids, name=None, role=None):  # draft 2's code: a saved N2 flag is trusted, not compared
    p = dict(p)
    if p.get("role") == "N2":
        p["role"] = "N2-trusted"
    if p.get("role") == "N2-trusted" and p.get("matches_m4a_part2") is not False:
        return None
    return orig_validate(p, ids, name, role)


orig_validate = m4b.validate


def _n2_test():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        try:
            T.test_m4b_n2_records_are_checked_against_m4a(Path(d))
        except BaseException as err:
            if type(err).__name__ == "Failed":
                raise AssertionError("did not raise")
            raise


run("M4b: N2's saved flag trusted", [(m4b, "validate", trust_the_flag)], _n2_test)
