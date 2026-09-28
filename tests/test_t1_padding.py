"""T1.2: single-strain padding (docs/foundations/T1.md v2, D086).

On CUDA a batch of one strain can take a different `bmm` path from the same strain inside a larger
batch (D082). With `BrainConfig.pad_single_strain` on, `Brain.step` runs a single strain as two
identical copies and keeps the first. These tests run on the CPU, where padding cannot change a
result, so they check the mechanism directly: the batch that reaches `bmm`, the loading defaults
that keep published results on the old path, the cache, and the accounting. The CUDA equivalence
test is `scripts/t1_equivalence.py`.
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest
import torch

from wormwars import accounting as A
from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import BrainConfig, Config
from wormwars.connectome import load_connectome
from wormwars.evo.genomes import brain_config_for, load_genome, save_genome
from wormwars.exp02 import grid


@pytest.fixture(scope="module")
def spec() -> BrainSpec:
    return BrainSpec.from_connectome(load_connectome())


def _genome(spec, n, pad, seed=0):
    cfg = dataclasses.replace(BrainConfig(), pad_single_strain=pad)
    return Genome.random(spec, cfg, n, generator=torch.Generator().manual_seed(seed))


def _inputs(spec, s, rows, seed=1):
    g = torch.Generator().manual_seed(seed)
    return [torch.randn(s, rows, spec.n, generator=g) * 0.5 for _ in range(3)]


def _run(brain, currents, substeps=None):
    v = brain.initial_state(currents[0].shape[1])
    for c in currents:
        v = brain.step(v, c, substeps=substeps)
    return v


class _BmmSpy:
    def __init__(self, monkeypatch):
        self.batches = []
        real = torch.bmm

        def spy(a, b):
            self.batches.append((a.shape[0], b.shape[0]))
            return real(a, b)
        monkeypatch.setattr(torch, "bmm", spy)


def test_new_configs_pad_by_default():
    assert BrainConfig().pad_single_strain is True
    assert Config.from_dict({}).brain.pad_single_strain is True


def test_a_single_strain_reaches_bmm_as_two_copies_when_on(spec, monkeypatch):
    spy = _BmmSpy(monkeypatch)
    _run(Brain(_genome(spec, 1, True)), _inputs(spec, 1, 4))
    assert spy.batches and set(spy.batches) == {(2, 2)}


def test_a_single_strain_reaches_bmm_alone_when_off(spec, monkeypatch):
    spy = _BmmSpy(monkeypatch)
    _run(Brain(_genome(spec, 1, False)), _inputs(spec, 1, 4))
    assert spy.batches and set(spy.batches) == {(1, 1)}


def test_several_strains_are_never_padded(spec, monkeypatch):
    spy = _BmmSpy(monkeypatch)
    _run(Brain(_genome(spec, 3, True)), _inputs(spec, 3, 4))
    assert set(spy.batches) == {(3, 3)}


def _prepare(brain, variant, spec):
    if variant == "silenced":
        brain.silence([[0, 5, 10]] * brain.n_strains)
    if variant == "gap_cut":
        brain.cut_gap([[(int(spec.gap_i[0]), int(spec.gap_j[0]))]] * brain.n_strains)
    return brain


@pytest.mark.parametrize("variant", ["plain", "silenced", "gap_cut", "substeps8"])
def test_a_padded_single_strain_equals_its_batch_member(spec, variant):
    """The contract, on the CPU. Before T1 a batch of one could differ here too (1.2e-7 after three
    steps at 5 rows on the development machine; D087): the CPU's own single-strain path."""
    currents = _inputs(spec, 3, 5)
    sub = 8 if variant == "substeps8" else None
    g = _genome(spec, 3, True)
    batch = _run(_prepare(Brain(g), variant, spec), currents, substeps=sub)
    alone = _run(_prepare(Brain(g.select([0])), variant, spec), [c[:1] for c in currents], substeps=sub)
    assert alone.shape == (1, 5, spec.n)
    assert torch.equal(alone, batch[:1])


def test_switch_off_is_the_pre_t1_single_strain_path(spec, monkeypatch):
    """Off, a single strain is computed alone, exactly as before T1 (the published path)."""
    spy = _BmmSpy(monkeypatch)
    currents = _inputs(spec, 1, 5)
    off = _run(Brain(_genome(spec, 1, False)), currents)
    assert set(spy.batches) == {(1, 1)}
    br = Brain(_genome(spec, 1, False))
    v = br.initial_state(5)
    for c in currents:  # the pre-T1 update, written out
        for _ in range(br.cfg.substeps):
            v = (v + br.c.unsqueeze(1) * (br.bias.unsqueeze(1) + c + torch.bmm(torch.tanh(v), br.W_drive)
                                         + torch.bmm(v, br.G))) / br.den.unsqueeze(1)
    assert torch.equal(off, v)


def test_silencing_still_applies_when_padded(spec):
    br = Brain(_genome(spec, 1, True)).silence([[0, 5, 10]])
    v = _run(br, _inputs(spec, 1, 5))
    assert torch.all(v[..., [0, 5, 10]] == 0)


def test_cut_gap_after_a_padded_step_uses_the_cut_matrix(spec):
    """The padded copy of G is cached; cutting a junction afterwards must not leave it stale."""
    i, j = int(spec.gap_i[0]), int(spec.gap_j[0])
    currents = _inputs(spec, 3, 5)
    g = _genome(spec, 3, True)
    br = Brain(g.select([0]))
    _run(br, [c[:1] for c in currents])  # builds the padded cache
    br.cut_gap([[(i, j)]])
    after = _run(br, [c[:1] for c in currents])
    batch = _run(Brain(g).cut_gap([[(i, j)]] * 3), currents)
    assert torch.equal(after, batch[:1])


def test_accounting_counts_the_padded_work_and_its_share(spec):
    rows, k = 5, BrainConfig().substeps
    A.LEDGER.reset()
    try:
        with A.category("probe"):
            _run(Brain(_genome(spec, 1, True)), _inputs(spec, 1, rows))
        c = A.LEDGER.counts["probe"]
        assert c.neural_updates == 3 * 2 * rows * k  # computed work, the copy included (T0.md)
        assert c.neural_padding == 3 * 1 * rows * k
        A.LEDGER.reset()
        with A.category("probe"):
            _run(Brain(_genome(spec, 1, False)), _inputs(spec, 1, rows))
        c = A.LEDGER.counts["probe"]
        assert (c.neural_updates, c.neural_padding) == (3 * rows * k, 0)
    finally:
        A.LEDGER.reset()


def _strip_switch(path):
    """Rewrite a saved genome as a file written before T1 (no `pad_single_strain`)."""
    with np.load(path, allow_pickle=False) as d:
        arrays = {k: d[k] for k in d.files}
    meta = json.loads(str(arrays["meta"]))
    del meta["brain_config"]["pad_single_strain"]
    arrays["meta"] = np.array(json.dumps(meta))
    np.savez(path, **arrays)


def test_new_genome_files_store_the_switch(spec, tmp_path):
    p = save_genome(tmp_path / "g.npz", _genome(spec, 1, True))
    with np.load(p, allow_pickle=False) as d:
        assert json.loads(str(d["meta"]))["brain_config"]["pad_single_strain"] is True


def test_a_genome_file_without_the_switch_loads_with_it_off(spec, tmp_path):
    p = save_genome(tmp_path / "g.npz", _genome(spec, 1, True))
    _strip_switch(p)
    g, _ = load_genome(p, spec)
    assert g.cfg.pad_single_strain is False
    assert brain_config_for(p, BrainConfig()).pad_single_strain is False


def test_brain_config_for_follows_the_file(spec, tmp_path):
    p = save_genome(tmp_path / "g.npz", _genome(spec, 1, True))
    assert brain_config_for(p, dataclasses.replace(BrainConfig(), pad_single_strain=False)).pad_single_strain is True


def test_a_bundle_without_the_switch_reads_it_off():
    raw = Config().to_dict()
    del raw["brain"]["pad_single_strain"]
    assert Config.from_bundle(raw).brain.pad_single_strain is False
    assert Config.from_dict(raw).brain.pad_single_strain is True


@pytest.mark.parametrize("task", ["T0", "T1", "A"])
def test_02s_config_builder_pins_it_off(task):
    """02's and 03's scripts build their configs here, so their published evaluations reproduce."""
    assert grid.task_config(Config(), task).brain.pad_single_strain is False
