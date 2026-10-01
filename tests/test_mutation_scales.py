"""Per-parameter mutation scales (`Genome.mutate(..., scales=...)`, E4s design v2): no scales and
scale vectors of ones are bit-identical to the plain mutation; a scale multiplies each parameter's
perturbation; a scale of 0 pins a parameter through any number of mutations."""

from __future__ import annotations

import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config, MutationConfig
from wormwars.connectome import load_connectome


@pytest.fixture(scope="module")
def genome():
    cfg = Config()
    return Genome.random(BrainSpec.from_connectome(load_connectome()), cfg.brain, 4,
                         generator=torch.Generator().manual_seed(11))


def ones(g: Genome) -> dict:
    return {"w": torch.ones(g.spec.n_chem), "g": torch.ones(g.spec.n_gap), "tau": torch.ones(g.spec.n),
            "bias": torch.ones(g.spec.n)}


def mutated(g, scales=None, mcfg=None, seed=3):
    return g.clone().mutate(mcfg or MutationConfig(), torch.Generator().manual_seed(seed), scales=scales)


@pytest.mark.parametrize("p_mutate", [1.0, 0.3])
def test_no_scales_and_ones_are_bit_identical(genome, p_mutate):
    mcfg = MutationConfig(p_mutate=p_mutate)
    plain = genome.clone().mutate(mcfg, torch.Generator().manual_seed(3))
    for other in (mutated(genome, None, mcfg), mutated(genome, ones(genome), mcfg)):
        for k in ("w", "g", "tau", "bias"):
            assert torch.equal(getattr(plain, k), getattr(other, k)), k


def test_a_scale_multiplies_the_perturbation(genome):
    s = ones(genome)
    s = {k: v * 0.25 for k, v in s.items()}
    big = MutationConfig(w_sigma=1e-3, g_sigma=1e-3, tau_sigma=1e-3, bias_sigma=1e-3)  # far from the bounds
    full, quarter = mutated(genome, None, big), mutated(genome, s, big)
    for k in ("w", "bias"):
        d_full = getattr(full, k) - getattr(genome, k)
        d_q = getattr(quarter, k) - getattr(genome, k)
        inside = (getattr(genome, k).abs() < 1.5)  # not clamped
        torch.testing.assert_close(d_q[inside], 0.25 * d_full[inside], atol=1e-6, rtol=1e-4)
    free = (genome.tau > 0.51) & (genome.tau < 19.5)  # not clamped at the bounds
    torch.testing.assert_close(torch.log(quarter.tau / genome.tau)[free],
                               0.25 * torch.log(full.tau / genome.tau)[free], atol=1e-6, rtol=1e-3)


def test_a_zero_scale_pins_its_parameters(genome):
    s = ones(genome)
    pin_w = torch.zeros(genome.spec.n_chem, dtype=torch.bool)
    pin_w[::7] = True
    pin_n = torch.zeros(genome.spec.n, dtype=torch.bool)
    pin_n[:20] = True
    s["w"][pin_w] = 0.0
    s["tau"][pin_n] = 0.0
    s["bias"][pin_n] = 0.0
    g = genome.clone()
    gen = torch.Generator().manual_seed(9)
    for _ in range(50):
        g.mutate(MutationConfig(), gen, scales=s)
    assert torch.equal(g.w[:, pin_w], genome.w[:, pin_w])
    assert torch.equal(g.tau[:, pin_n], genome.tau[:, pin_n])
    assert torch.equal(g.bias[:, pin_n], genome.bias[:, pin_n])
    assert not torch.equal(g.w[:, ~pin_w], genome.w[:, ~pin_w])  # the rest did mutate


def test_scales_of_the_wrong_shape_or_key_are_refused(genome):
    with pytest.raises(ValueError):
        mutated(genome, {"w": torch.ones(3)})
    with pytest.raises(ValueError):
        mutated(genome, {**ones(genome), "tau_sigma": torch.ones(genome.spec.n)})
