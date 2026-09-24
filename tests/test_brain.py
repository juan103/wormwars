"""Milestone 2 acceptance checks for the brain.

"No NaNs" is not sufficient and is not what is checked here. The three things that matter are:
batching changes nothing, activity stays inside its analytic bound at the corners of the parameter
bounds, and the integrator is accurate enough at the configured dt that halving it twice barely
moves the answer.
"""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig, MutationConfig
from wormwars.connectome import load_connectome

torch.manual_seed(0)


@pytest.fixture(scope="module")
def spec() -> BrainSpec:
    return BrainSpec.from_connectome(load_connectome())


@pytest.fixture(scope="module")
def cfg() -> BrainConfig:
    return BrainConfig()


def _gen(spec, cfg, s=3, seed=0):
    g = torch.Generator().manual_seed(seed)
    return Genome.random(spec, cfg, s, generator=g)


def test_spec_matches_connectome(spec):
    con = load_connectome()
    assert spec.n == 302
    assert spec.n_chem == int((con.chem > 0).sum())
    assert spec.n_gap == int((con.gap > 0).sum()) // 2
    assert spec.n_params == spec.n_chem + spec.n_gap + 604


def test_dense_respects_the_mask(spec, cfg):
    con = load_connectome()
    genome = _gen(spec, cfg, 2)
    W, G = genome.dense()
    chem_mask = torch.from_numpy(con.chem > 0)
    gap_mask = torch.from_numpy(con.gap > 0)
    for s in range(2):
        assert (W[s][~chem_mask] == 0).all(), "W must be zero off the chemical mask"
        assert (W[s][chem_mask] != 0).all(), "W must be nonzero on the chemical mask"
        assert (G[s][~gap_mask] == 0).all(), "G must be zero off the gap mask"
        assert torch.equal(G[s], G[s].T), "G must be symmetric"
        assert (G[s] >= 0).all(), "G must be nonnegative"
        assert (torch.diagonal(G[s]) == 0).all()


def test_bounds_are_enforced_after_mutation(spec, cfg):
    genome = _gen(spec, cfg, 4)
    mcfg = MutationConfig(w_sigma=5.0, g_sigma=5.0, tau_sigma=3.0, bias_sigma=5.0)
    for _ in range(5):
        genome.mutate(mcfg, torch.Generator().manual_seed(1))
    assert genome.w.abs().max() <= cfg.w_max + 1e-6
    assert genome.g.min() >= 0.0 and genome.g.max() <= cfg.g_max + 1e-6
    assert genome.tau.min() >= cfg.tau_min - 1e-6 and genome.tau.max() <= cfg.tau_max + 1e-6
    assert genome.bias.abs().max() <= cfg.b_max + 1e-6


def test_dale_keeps_one_sign_per_presynaptic_neuron(spec):
    cfg = BrainConfig(dale=True)
    genome = _gen(spec, cfg, 2)
    genome.mutate(MutationConfig(w_sigma=2.0), torch.Generator().manual_seed(2))
    for s in range(2):
        for j in range(spec.n):
            out = genome.w[s][spec.chem_i == j]
            if out.numel() > 1:
                assert (out >= 0).all() or (out <= 0).all(), f"neuron {j} has mixed synapse signs"


def test_batched_equals_unbatched(spec, cfg):
    """One strain stepped alone must give exactly what it gives inside a batch."""
    genome = _gen(spec, cfg, 5, seed=3)
    b_all = Brain(genome)
    v = torch.randn(5, 7, spec.n) * 0.5
    cur = torch.randn(5, 7, spec.n) * 0.3
    out_all = b_all.step(v.clone(), cur)

    for s in (0, 2, 4):
        one = Brain(genome.select([s]))
        out_one = one.step(v[s : s + 1].clone(), cur[s : s + 1])
        torch.testing.assert_close(out_one[0], out_all[s], rtol=1e-5, atol=1e-6)

    # and splitting the wey axis must not matter either
    out_split = torch.cat(
        [b_all.step(v[:, :3].clone(), cur[:, :3]), b_all.step(v[:, 3:].clone(), cur[:, 3:])], dim=1
    )
    torch.testing.assert_close(out_split, out_all, rtol=1e-5, atol=1e-6)


def _extreme_genome(spec, cfg, sign=1.0):
    """The corner of the parameter box: every bound saturated at once."""
    S = 1
    w = torch.full((S, spec.n_chem), sign * cfg.w_max)
    g = torch.full((S, spec.n_gap), cfg.g_max)
    tau = torch.full((S, spec.n), cfg.tau_min)
    bias = torch.full((S, spec.n), sign * cfg.b_max)
    return Genome(spec, cfg, w, g, tau, bias)


@pytest.mark.parametrize("sign", [1.0, -1.0])
def test_activity_bounded_at_the_corners_of_the_parameter_box(spec, cfg, sign):
    brain = Brain(_extreme_genome(spec, cfg, sign))
    bound = brain.activity_bound()
    v = torch.zeros(1, 4, spec.n)
    cur = torch.full((1, 4, spec.n), sign * cfg.input_max)
    for _ in range(300):
        v = brain.step(v, cur)
        assert torch.isfinite(v).all(), "state left the reals"
        assert v.abs().max() <= bound, f"|v| = {v.abs().max():.1f} exceeded the bound {bound:.1f}"
    # and it must actually settle, not drift forever
    v2 = brain.step(v.clone(), cur)
    assert (v2 - v).abs().max() < 1e-3, "state had not converged after 300 ticks"


def test_activity_bounded_with_extreme_mixed_signs(spec, cfg):
    """All bounds saturated but signs random: the hardest case for the gap coupling."""
    gen = torch.Generator().manual_seed(7)
    S = 2
    sign = torch.where(torch.rand(S, spec.n_chem, generator=gen) < 0.5, -1.0, 1.0)
    genome = Genome(
        spec,
        cfg,
        w=sign * cfg.w_max,
        g=torch.full((S, spec.n_gap), cfg.g_max),
        tau=torch.full((S, spec.n), cfg.tau_min),
        bias=torch.where(torch.rand(S, spec.n, generator=gen) < 0.5, -cfg.b_max, cfg.b_max),
    )
    brain = Brain(genome)
    v = torch.randn(S, 3, spec.n, generator=gen) * 10.0
    cur = torch.randn(S, 3, spec.n, generator=gen) * cfg.input_max
    for _ in range(300):
        v = brain.step(v, cur)
    assert torch.isfinite(v).all()
    assert v.abs().max() <= brain.activity_bound()


def _refine(brain, v0, cur, ticks, substeps):
    v = v0.clone()
    for _ in range(ticks):
        v = brain.step(v, cur, substeps=substeps)
    return v


@pytest.mark.parametrize("kind", ["random", "extreme", "fast_tau"])
def test_timestep_refinement(spec, cfg, kind):
    """dt and dt/4 must agree: this is what justifies the configured substep count."""
    if kind == "random":
        genome = _gen(spec, cfg, 2, seed=11)
    elif kind == "extreme":
        genome = _extreme_genome(spec, cfg, 1.0)
    else:  # every neuron at tau_min, where the integrator is under most strain
        genome = _gen(spec, cfg, 2, seed=12)
        genome.tau.fill_(cfg.tau_min)
        genome.g.fill_(cfg.g_max)
    brain = Brain(genome)
    S = genome.n_strains
    gen = torch.Generator().manual_seed(13)
    v0 = torch.randn(S, 4, spec.n, generator=gen) * 0.5
    cur = torch.randn(S, 4, spec.n, generator=gen) * 1.0

    coarse = _refine(brain, v0, cur, ticks=40, substeps=cfg.substeps)
    fine = _refine(brain, v0, cur, ticks=40, substeps=cfg.substeps * 4)
    if kind == "extreme":
        # Every weight at +w_max makes the network bistable, and a wey that starts near the
        # boundary between the two attractors can be tipped either way by ANY finite dt: that is
        # basin selection, not integration accuracy. Measured over 200 weys it happens to 1.5% of
        # them, at the same rate in both synapse directions (DECISIONS.md D031). Compare only weys
        # that reached the same attractor, and require that nearly all of them did.
        same = ~((torch.sign(coarse) != torch.sign(fine)) & (fine.abs() > 5)).any(dim=2)
        assert same.float().mean() >= 0.75, f"attractor flips in {int((~same).sum())} weys"
        coarse, fine = coarse[same], fine[same]
    err = (coarse - fine).abs().max().item()
    scale = max(fine.abs().max().item(), 1.0)
    assert err / scale < 0.01, f"{kind}: dt vs dt/4 differ by {err:.4f} (rel {err / scale:.4f})"


@pytest.mark.parametrize("rounds", [0, 25])
def test_motor_readout_is_resolved_in_the_evolved_range(spec, cfg, rounds):
    """What the body reads, for genomes like the ones experiment 01 actually evolved.

    The single-seed refinement test above passed for years' worth of edits while telling us little
    about evolved genomes. This one checks 8 x 16 weys at the configured dt against dt/4, on the
    bounded output the motors read. It holds at initialisation and after 25 rounds of mutation
    (experiment 01's champions measure a worst readout error of 0.023). It does NOT hold after
    ~150 rounds: 8 substeps is under-resolved there, in both directions (DECISIONS.md D032).
    """
    from wormwars.config import MutationConfig as _MC

    g = Genome.random(spec, cfg, 8, generator=torch.Generator().manual_seed(3))
    mg = torch.Generator().manual_seed(4)
    for _ in range(rounds):
        g.mutate(_MC(), mg)
    brain = Brain(g)
    gen = torch.Generator().manual_seed(200)
    v0 = torch.randn(8, 16, spec.n, generator=gen) * 0.5
    cur = torch.randn(8, 16, spec.n, generator=gen) * 1.0
    coarse = torch.tanh(_refine(brain, v0, cur, ticks=40, substeps=cfg.substeps))
    fine = torch.tanh(_refine(brain, v0, cur, ticks=40, substeps=cfg.substeps * 4))
    per_wey = (coarse - fine).abs().amax(dim=2).flatten()
    assert (per_wey > 0.05).float().mean() <= 0.03, (
        f"{int((per_wey > 0.05).sum())}/{per_wey.numel()} weys off by more than 0.05"
    )


def test_refinement_converges_at_first_order(spec, cfg):
    """Halving dt must roughly halve the error: evidence the scheme is consistent, not just stable."""
    genome = _gen(spec, cfg, 1, seed=17)
    brain = Brain(genome)
    gen = torch.Generator().manual_seed(19)
    v0 = torch.randn(1, 2, spec.n, generator=gen) * 0.5
    cur = torch.randn(1, 2, spec.n, generator=gen)
    ref = _refine(brain, v0, cur, 30, substeps=cfg.substeps * 32)
    errs = []
    for mult in (1, 2, 4):
        out = _refine(brain, v0, cur, 30, substeps=cfg.substeps * mult)
        errs.append((out - ref).abs().max().item())
    assert errs[0] > errs[1] > errs[2], f"error did not shrink with dt: {errs}"
    ratio = errs[0] / max(errs[1], 1e-12)
    assert 1.5 < ratio < 3.0, f"expected ~2x error reduction per halving, got {ratio:.2f}"


def test_step_is_deterministic(spec, cfg):
    genome = _gen(spec, cfg, 2, seed=23)
    brain = Brain(genome)
    v = torch.randn(2, 3, spec.n)
    cur = torch.randn(2, 3, spec.n)
    a = brain.step(v.clone(), cur)
    b = brain.step(v.clone(), cur)
    assert torch.equal(a, b)


def test_zero_input_zero_bias_stays_at_rest(spec, cfg):
    genome = _gen(spec, cfg, 1, seed=29)
    genome.bias.zero_()
    brain = Brain(genome)
    v = torch.zeros(1, 2, spec.n)
    for _ in range(50):
        v = brain.step(v, torch.zeros_like(v))
    assert v.abs().max() == 0.0, "v = 0 must be a fixed point when bias and input are zero"
