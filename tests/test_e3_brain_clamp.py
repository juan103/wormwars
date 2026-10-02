"""E3a's clamp of a named neuron to a value (E3a PREREGISTRATION §5 G-E, §6 the clamp assays; test 6).

`Brain.clamp` holds chosen neurons at chosen values after every substep, per strain. `silence` is the
special case of value 0 and stays as it was.
"""

from __future__ import annotations

import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig
from wormwars.connectome import load_connectome


def _brain(strains=2):
    con = load_connectome()
    spec = BrainSpec.from_connectome(con)
    cfg = BrainConfig()
    g = Genome.random(spec, cfg, strains, generator=torch.Generator().manual_seed(3))
    return Brain(g), spec


def test_a_clamped_neuron_holds_its_value_and_drives_its_targets():
    brain, spec = _brain()
    v = torch.zeros(2, 1, spec.n)
    cur = torch.zeros_like(v)
    brain.clamp([{5: 1.25}, {}])
    for _ in range(3):
        v = brain.step(v, cur)
    assert torch.all(v[0, :, 5] == 1.25)
    assert not torch.all(v[1, :, 5] == 1.25)
    free, _ = _brain()
    vf = torch.zeros(2, 1, spec.n)
    for _ in range(3):
        vf = free.step(vf, cur)
    # the clamp changes the rest of the clamped strain, and nothing in the other strain
    assert not torch.equal(v[0], vf[0])
    assert torch.equal(v[1], vf[1])


def test_no_clamp_is_bit_identical_to_the_unclamped_engine():
    a, spec = _brain()
    b, _ = _brain()
    b.clamp([{5: 0.7}, {}])
    b.clamp(None)
    v = torch.randn(2, 3, spec.n, generator=torch.Generator().manual_seed(1))
    cur = torch.randn(2, 3, spec.n, generator=torch.Generator().manual_seed(2))
    assert torch.equal(a.step(v, cur), b.step(v, cur))


def test_clamp_and_silence_compose():
    brain, spec = _brain()
    brain.silence([[7], []])
    brain.clamp([{5: -0.5}, {}])
    v = brain.step(torch.ones(2, 1, spec.n), torch.zeros(2, 1, spec.n))
    assert v[0, 0, 7] == 0 and v[0, 0, 5] == -0.5


def test_clamp_refuses_the_wrong_strain_count():
    brain, _ = _brain()
    try:
        brain.clamp([{5: 1.0}])
    except ValueError:
        return
    raise AssertionError("a clamp for 1 of 2 strains must be refused")
