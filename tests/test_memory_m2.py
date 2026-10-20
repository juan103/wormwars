"""M2 pilot's equilibrium tools (scripts/memory_m2, docs/memory/M2-PILOT-PLAN.md): Newton with strains converging at
different iterations, and P against the integrator's own derivative (a sabotage check: the transposed convention must
fail it)."""
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
