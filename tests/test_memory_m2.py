"""M2's equilibrium tools (scripts/memory_m2, docs/memory/M2-PILOT-PLAN.md, M2-CENSUS-PLAN.md): Newton with strains
converging at different iterations, P against the integrator's own derivative (a sabotage check: the transposed
convention must fail it), the compacted continuation against the pilot's, and the census's split."""
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))


def test_the_classifiers_rules():
    """classify.test_rules(): reaching against the forecast at matching ticks, the period search, the oscillation veto
    and the classes' precedence (Fable, Astra, round 8: it ran nowhere in the suite)."""
    import classify
    classify.test_rules()


def _roots(n=4, ticks=300):
    import common as c
    import equilibria as E
    torch.set_grad_enabled(False)
    g, cfg = c.S.genomes(c.S.CON, n, 7600)
    brain, v, food = c.ramp(g, cfg)
    cur = c.at(cfg, c.S.CON.n, n, [food])
    x = v[:, :1].clone()
    for _ in range(ticks):
        x = brain.step(x, cur)
    b = E.brain64(g)
    return E, b, E.System(b, cur.double()), x[:, 0].double(), v[:, 0].double(), cur


def test_newton_handles_strains_that_converge_at_different_iterations():
    """Astra, round 3: once some strains are done, the active strains' H and A must use their own matrices. One strain
    starts at its root (done before the first iteration), one near it, two at the ramp's end, far from it."""
    E, b, sysm, near, far, cur = _roots()
    ref = sysm.newton(near)
    assert ref["located"].all()
    start = torch.stack([ref["v"][0], near[1], far[2], far[3]])
    out = sysm.newton(start)
    assert out["located"].all() and out["iterations"][0] == 0
    for s in range(4):  # each strain alone must give the same root
        alone = E.System(E.brain64(b.genome.select([s])), cur[s:s + 1].double())
        one = alone.newton(start[s:s + 1])
        assert one["located"].all()
        assert float((one["v"][0] - out["v"][s]).abs().max()) < 1e-10
    assert (sysm.error_bound(out) < 1e-9).all()


def test_p_to_the_substeps_equals_the_integrators_tick_derivative():
    """R4': at a root every substep has the same linearisation P = I + D A^T (column form), so one float64 tick's
    automatic derivative is P^32; the transposed convention I + D A must fail (the sabotage)."""
    E, b, sysm, near, far, cur = _roots(n=2)
    r = sysm.newton(near)["v"]
    k = b.cfg.substeps
    D = E.tick_autograd(b, r, cur)
    P = sysm.P(r, k)
    assert float((torch.linalg.matrix_power(P, k) - D).abs().max()) < 1e-10
    h = 1.0 / k
    wrong = torch.eye(r.shape[1], dtype=r.dtype) + (h / (sysm.tau + h * (1 + sysm.g))).unsqueeze(2) * sysm.J(r)
    assert float((torch.linalg.matrix_power(wrong, k) - D).abs().max()) > 1e-6


def test_newton_gives_up_on_a_strain_after_exactly_three_failed_line_searches():
    """Fable, Astra, round 4: the give-up must be sticky while another strain is still converging. A toy H on one
    neuron: strain 0 is v^2 + 1 started at 0 (A singular, the least-squares step is zero, every line search fails);
    strain 1 is v^3 - 8 started at 100 (converges slowly to 2)."""
    import equilibria as E

    class Toy(E.System):
        def __init__(self):
            pass

        def H(self, v, idx=None):
            idx = torch.arange(2) if idx is None else idx
            return torch.where((idx == 0).unsqueeze(1), v ** 2 + 1, v ** 3 - 8)

        def J(self, v, idx=None):
            idx = torch.arange(2) if idx is None else idx
            return torch.where((idx == 0).unsqueeze(1), 2 * v, 3 * v ** 2).unsqueeze(2)

    out = Toy().newton(torch.tensor([[0.0], [100.0]], dtype=torch.float64))
    assert out["failed_line_searches"][0] == 3 and out["iterations"][0] == 3 and not out["located"][0]
    assert out["located"][1] and abs(float(out["v"][1, 0]) - 2.0) < 1e-12 and out["iterations"][1] > 3
    assert out["singular_solves"][0] == 3


def test_the_continuation_uses_the_requested_substep_count():
    """Astra, round 5: R3 classifies at 64 substeps with a brain configured for 32, so the continuation must step with
    the count it is given, as its forecast does."""
    import pilot
    E, b, sysm, near, far, cur = _roots(n=2, ticks=50)
    r = sysm.newton(near)["v"]
    P64 = torch.linalg.matrix_power(sysm.P(r, 64), 64)
    start = near.unsqueeze(1)
    *_, v_end = pilot.continuation(b, start, r.unsqueeze(1), P64, cur.double(), cap=5, substeps=64)
    manual = start.clone()
    for _ in range(5):
        manual = b.step(manual, cur.double(), 64)
    assert float((v_end - manual).abs().max()) == 0.0
    other = start.clone()
    for _ in range(5):
        other = b.step(other, cur.double())
    assert float((v_end - other).abs().max()) > 0.0


@pytest.mark.slow
def test_the_oscillation_check_evaluates_the_integrator_it_is_given():
    """Fable, Astra, round 6: in R3's 64-substep variant the oscillation check's continuation and root veto must use 64
    substeps, not the brain's configured 32. On the planted integrator cycle, the orbit root's radius per substep must be
    P's at the count evaluated, and the two counts must give different radii."""
    import equilibria as E
    import pilot
    cases, cfg, _ = pilot.planted_genomes()
    g, init, _ = cases["integrator cycle"]
    run = pilot.follow_from(g, cfg, init)
    cur = run["cur"][:, :1]
    rhos = {}
    for k in (32, 64):
        rec, _ = pilot.oscillation_check(g, cfg, run["end"][0, 0], run["tail"][0, :, 0], cur, None, 0, cap=300,
                                         initial=init, eval_substeps=k)
        assert rec["orbit_root_rho_substep"], rec
        root = torch.zeros(1, g.spec.n, dtype=torch.float64)
        expect = float(E.System(E.brain64(g), cur).stability(root, k)[1][0])
        assert abs(rec["orbit_root_rho_substep"][0] - expect) < 1e-9, (k, rec["orbit_root_rho_substep"], expect)
        rhos[k] = rec["orbit_root_rho_substep"][0]
    assert abs(rhos[32] - rhos[64]) > 1e-6
    # Astra, round 8: R3's float64 variant must search for the period in float64 too
    rec, _ = pilot.oscillation_check(g, cfg, run["end"][0, 0], run["tail"][0, :, 0], cur, None, 0, cap=300,
                                     initial=init, dtype=torch.float64)
    assert rec["recording_dtype"] == "float64"
    rec, _ = pilot.oscillation_check(g, cfg, run["end"][0, 0], run["tail"][0, :, 0], cur, None, 0, cap=300, initial=init)
    assert rec["recording_dtype"] == "float32"


def test_the_compacted_continuation_matches_the_pilots():
    """The census plan (Astra, round 1): dropping finished strains from the batch must change nothing. Eight strains
    started at different distances from their roots, so that they finish at different ticks, leave survivors at
    non-contiguous indices and a last strain running alone, with a cap that some rows reach. Stopping times and capped
    flags must be equal, the distance and forecast windows and the returned states within 1e-12. The sabotage: a
    window read one tick late must fail the same comparison."""
    import numpy as np
    import pilot
    E, b, sysm, near, far, cur = _roots(n=8, ticks=300)
    r = sysm.newton(near)["v"]
    scale = torch.tensor([0.0, 1.0, 1e-2, 1.0, 1e-4, 1.0, 1e-1, 1.0], dtype=torch.float64).unsqueeze(1)
    start = (r + scale * (near - r)).clone()
    start[7] = far[7]  # far from its root: the slowest, alone at the end
    P32 = torch.linalg.matrix_power(sysm.P(r, 32), 32)
    args = (b, start.unsqueeze(1), r.unsqueeze(1), P32, cur.double())
    ref = pilot.continuation(*args, cap=700, substeps=32)
    new = pilot.continuation_compact(*args, cap=700, substeps=32)
    d0, T, capped, wd, wf, v = ref
    assert len(set(T[:, 0].tolist())) >= 3, T  # staggered completions
    gaps = [np.diff(np.where(T[:, 0] > t)[0]) for t in sorted(set(T[:, 0].tolist()))]
    assert any((g > 1).any() for g in gaps), T  # survivors at non-contiguous indices (Fable, round 4)
    assert (T[:, 0] == T[:, 0].max()).sum() == 1 or capped.any(), T  # one strain alone at the end, or the cap
    assert np.array_equal(T, new[1]) and np.array_equal(capped, new[2]) and np.array_equal(d0, new[0])
    assert np.abs(wd - new[3]).max() <= 1e-12 and np.abs(wf - new[4]).max() <= 1e-12
    assert float((v - new[5]).abs().max()) <= 1e-12
    late = np.roll(new[3], -1, axis=-1)  # the sabotage
    assert np.abs(wd - late).max() > 1e-12
    ref, new = (f(*args, cap=300, substeps=32) for f in (pilot.continuation, pilot.continuation_compact))  # the cap
    assert ref[2].any() and not ref[2].all()
    assert np.array_equal(ref[1], new[1]) and np.array_equal(ref[2], new[2])
    assert np.abs(ref[3] - new[3]).max() <= 1e-12 and float((ref[5] - new[5]).abs().max()) <= 1e-12


def test_the_census_split_and_its_readings():
    """split.test_rules(): the parts add up to the lead, the band brackets phi_S, composition, retention and presence add
    up with an empty class on either side, and the readings and their combination over the two N2 panels."""
    import split
    split.test_rules()


def test_batch_7s_shuffles_regenerate():
    """The census regenerates batch 7's core-frozen and hub-frozen shuffles and checks each against batch7.json."""
    import census
    for arm in ("core-frozen-shuffle", "hub-frozen-shuffle"):
        for k in range(3):
            census.batch7_graph(arm, k)


def test_c5_fails_when_a_separate_states_genome_is_lost():
    """Astra, round 3: a pilot genome with separate states that the census no longer classifies (lost to eligibility)
    must count as a basin change, so C5 fails even with 99% agreement."""
    import numpy as np
    import census
    roots = np.zeros((2, 3))
    hist = {"reach": ["reached", "reached"], "stability": ["stable", "stable"], "error": [1e-14, 1e-14], "reason": None}
    pilot = {0: {"class": "separate states"}, **{i: {"class": "fading"} for i in range(1, 100)}}
    cen = {i: dict(hist, **{"class": "fading"}) for i in range(1, 100)}
    rows, same, n, switched = census.c5_compare(pilot, {i: roots for i in pilot}, cen, {i: roots for i in cen})
    assert same / n == 0.99 and switched == [{"genome": 0, "census": "not eligible"}]
    cen[0] = dict(hist, **{"class": "separate states"})  # kept, same roots: no change
    assert census.c5_compare(pilot, {i: roots for i in pilot}, cen, {i: roots for i in cen})[3] == []
    moved = {i: roots for i in cen}
    moved[0] = roots + np.array([[0.0, 0.0, 0.0], [1e-3, 0.0, 0.0]])  # one history in another basin
    assert census.c5_compare(pilot, {i: roots for i in pilot}, cen, moved)[3] == [{"genome": 0}]


def test_the_radius_sensitivity_changes_both_histories_together():
    """Fable, Astra, round 3: a genome whose two histories both qualify is classified once, with both new verdicts:
    two stable, distinct roots, each reached only under the sensitivity, give separate states."""
    import census
    h = {"located": True, "error": 1e-14, "stability": "stable", "reach": "not approaching", "rho_substep": 0.99,
         "cont_max_re": -0.1, "residual": 1e-15, "sigma_min": 0.1, "failed_line_searches": 0, "singular_solves": 0,
         "T": 0, "dist_end_root": 2e-3, "residual_in_continuation_brain": None}
    rec = {"histories": [dict(h), dict(h)], "root_distance": 0.5, "readout_difference": 0.4, "a": 1.0,
           "oscillation": [None, None]}
    one = census.joint_radius(rec, {0: ("reached", 300)})
    both = census.joint_radius(rec, {0: ("reached", 300), 1: ("reached", 310)})
    assert one["class"] == "unresolved" and both["class"] == "separate states", (one, both)


def _census_in(tmp_path):
    import census
    old = census.OUT
    census.OUT = tmp_path
    return census, old


def test_c3_refuses_an_incomplete_census_and_an_empty_cached_pass(tmp_path):
    """Astra, round 4: C3 called before the panels exist must neither run nor save a pass, and an empty cached pass
    must not count."""
    import json
    census, old = _census_in(tmp_path)
    try:
        with pytest.raises(SystemExit):
            census.stage_c3()
        assert not (tmp_path / "c3.json").exists()
        json.dump({"checks": [], "passes": True}, open(tmp_path / "c3.json", "w"))  # draft 4's empty pass
        assert not census.c3_valid(json.load(open(tmp_path / "c3.json")))
        with pytest.raises(SystemExit):
            census.stage_c3()
    finally:
        census.OUT = old


def test_the_cost_guard_holds_on_a_restart(tmp_path):
    """Fable, Astra, round 4: a projection over the limit stops every later call, and the two measured panels are read
    from their saved records when the run was interrupted before guard.json was written."""
    import json
    census, old = _census_in(tmp_path)
    try:
        todo = census.panels()
        for name in (todo[0][0], todo[1][0]):  # both saved, guard.json never written
            json.dump({"seconds": 1500.0}, open(tmp_path / f"{name}.json", "w"))
        with pytest.raises(SystemExit):
            census.guard(todo)
        assert json.load(open(tmp_path / "guard.json"))["projected_hours"] > census.STOP_HOURS
        with pytest.raises(SystemExit):  # the restart: the cached projection still stops it
            census.guard(todo)
        json.dump({"passes": True}, open(tmp_path / "c2.json", "w"))
        with pytest.raises(SystemExit):
            census.stage_panels()
    finally:
        census.OUT = old
