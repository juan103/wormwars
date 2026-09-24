"""Initial magnitude modes: anatomical (default, unchanged), uniform, and permuted in-mask."""

from __future__ import annotations

import dataclasses

import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome import load_connectome


@pytest.fixture(scope="module")
def spec():
    return BrainSpec.from_connectome(load_connectome())


def gen(spec, **kw):
    cfg = dataclasses.replace(BrainConfig(), **kw)
    return Genome.random(spec, cfg, 2, generator=torch.Generator().manual_seed(11))


def test_anatomical_default_is_the_original_formula(spec):
    g = gen(spec)
    cfg = BrainConfig()
    expect = cfg.init_w_scale * spec.chem_anat / spec.chem_anat.mean()
    torch.testing.assert_close(g.w.abs()[0], expect.clamp(max=cfg.w_max), rtol=0, atol=0)


def test_uniform_sets_every_magnitude_to_the_scale(spec):
    g = gen(spec, init_chem_magnitude="uniform", init_gap_magnitude="uniform")
    cfg = BrainConfig()
    assert torch.allclose(g.w.abs(), torch.full_like(g.w, cfg.init_w_scale))
    assert torch.allclose(g.g, torch.full_like(g.g, cfg.init_g_scale))


def test_permuted_keeps_the_multiset_and_the_signs(spec):
    a = gen(spec)
    p = gen(spec, init_chem_magnitude="permuted", init_gap_magnitude="permuted")
    assert torch.equal(torch.sort(a.w.abs()[0]).values, torch.sort(p.w.abs()[0]).values)
    assert torch.equal(torch.sort(a.g[0]).values, torch.sort(p.g[0]).values)
    assert torch.equal(torch.sign(a.w), torch.sign(p.w)), "signs must stay paired"
    assert not torch.equal(a.w.abs(), p.w.abs()), "positions must actually move"


def test_permutation_seed_changes_the_permutation(spec):
    p0 = gen(spec, init_chem_magnitude="permuted", init_permutation_seed=0)
    p1 = gen(spec, init_chem_magnitude="permuted", init_permutation_seed=1)
    assert not torch.equal(p0.w, p1.w)


def test_chem_and_gap_modes_are_independent(spec):
    a = gen(spec)
    c = gen(spec, init_chem_magnitude="uniform")
    assert torch.equal(a.g, c.g) and not torch.equal(a.w.abs(), c.w.abs())


def test_unknown_mode_is_an_error(spec):
    with pytest.raises(ValueError, match="magnitude"):
        gen(spec, init_chem_magnitude="vibes")
