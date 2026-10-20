"""Sabotage runs for the census's rule tests (rule 9): each breaks one thing the tests guard, and the matching test must
then fail. Prints one line per sabotage. Usage: python scripts/memory_m2/sabotage_census.py"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import census  # noqa: E402
import split  # noqa: E402


def fails(fn):
    try:
        fn()
    except AssertionError:
        return True
    except BaseException as err:  # pytest's "DID NOT RAISE" is an outcome exception, not an AssertionError
        if type(err).__name__ == "Failed":
            return True
        raise
    return False


def run(label, patch, test):
    saved = {k: getattr(mod, k) for mod, k, _ in patch}
    for mod, k, v in patch:
        setattr(mod, k, v)
    try:
        print(f"{label}: {'fails, as it must' if fails(test) else 'PASSES (the test does not guard it)'}")
    finally:
        for (mod, k, _), v in zip(patch, saved.values()):
            setattr(mod, k, v)


orig_split = split.split_from
orig_boot = split.bootstrap
orig_combine = split.combine


def band_without_ref_u(n2, refs):  # the band's lower end forgets the reference's unresolved
    out = orig_split(n2, refs)
    mean = {k: np.mean([r[k] for r in refs], 0) for k in n2}
    with np.errstate(invalid="ignore", divide="ignore"):
        out["phi_S_lo"] = np.where(out["Lambda"] > 0, (n2["S"] - mean["S"]) / out["Lambda"], np.nan)
    return out


def resampled(V, ref_names, n2_names, rng, t, b, own_w=False, across=False):
    """bootstrap() with one thing broken: own_w gives N2's seed-7600 panel its own genome indices instead of the
    nulls'; across resamples the reference graphs from the whole reference instead of within ensembles."""
    n = len(V[ref_names[0]]["a"])
    W1 = split.multiplicities(rng.integers(0, n, (b, n)), n)
    W2 = split.multiplicities(rng.integers(0, n, (b, n)), n)
    W3 = split.multiplicities(rng.integers(0, n, (b, n)), n)
    C = {g: split.contributions(V[g], W1, t) for g in ref_names}
    groups = [ref_names] if across else [[g for g in ref_names if split.ensemble_of(g.split("__")[0]) == e]
                                         for e in split.ENSEMBLES]
    refs = []
    for grp in (x for x in groups if x):
        pk = rng.integers(0, len(grp), (b, len(grp)))
        refs += [{k: np.choose(pk[:, col], [C[g][k] for g in grp]) for k in C[ref_names[0]]} for col in range(len(grp))]
    W = {"__7600": W3 if own_w else W1}
    return {name: split.split_from(split.contributions(V[name], W.get(name[-6:], W2), t), refs) for name in n2_names}


def unshared(V, ref_names, n2_names, rng, t, b=split.B):
    return resampled(V, ref_names, n2_names, rng, t, b, own_w=True)


def across_ensembles(V, ref_names, n2_names, rng, t, b=split.B):
    return resampled(V, ref_names, n2_names, rng, t, b, across=True)


def combine_with_branch(r1, r2):  # draft 3's code: "little" panels that differ only in the branch are "not replicated"
    return "not replicated" if (r1, r2) == ("little", "little") else orig_combine(r1, r2)


run("band without the reference's unresolved", [(split, "split_from", band_without_ref_u)], split.test_rules)
run("genome indices not shared", [(split, "bootstrap", unshared)], split.test_rules)
run("graphs resampled across ensembles", [(split, "bootstrap", across_ensembles)], split.test_rules)
run("two 'little' panels not replicated", [(split, "combine", combine_with_branch)], split.test_rules)

orig_joint = census.joint_radius


def last_history_only(rec, vh):  # draft 3's code: one history changed at a time, the last kept
    h = max(vh)
    return orig_joint(rec, {h: vh[h]})


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
import test_memory_m2 as T  # noqa: E402

run("radius sensitivity one history at a time", [(census, "joint_radius", last_history_only)],
    T.test_the_radius_sensitivity_changes_both_histories_together)

orig_c5 = census.c5_compare


def c5_ignores_lost(pilot, proots, cen, croots):  # draft 3's code: a lost genome is a disagreement, not a basin change
    rows, same, n, sw = orig_c5(pilot, proots, cen, croots)
    return rows, same, n, [x for x in sw if x.get("census") != "not eligible"]


run("C5 ignores a lost separate-states genome", [(census, "c5_compare", c5_ignores_lost)],
    T.test_c5_fails_when_a_separate_states_genome_is_lost)

# round 4's gates
orig_guard = census.guard


def guard_first_only(todo):  # draft 4's code: the limit checked only when the projection is first computed
    f = census.OUT / "guard.json"
    if f.exists():
        return
    orig_guard(todo)


import tempfile  # noqa: E402

for label, patch, test in (
        ("cost guard enforced only once", [(census, "guard", guard_first_only)], T.test_the_cost_guard_holds_on_a_restart),
        ("C3 without the completeness gate", [(census, "missing_panels", lambda: [])],
         T.test_c3_refuses_an_incomplete_census_and_an_empty_cached_pass)):
    with tempfile.TemporaryDirectory() as d:
        run(label, patch, lambda test=test, d=d: test(Path(d)))
