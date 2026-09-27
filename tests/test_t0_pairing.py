"""T0 (docs/foundations/T0.md v2), item 1: complete inheritance and genome-score pairing (D066)."""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path

import numpy as np
import pytest
import torch

from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import rollout
from wormwars.evo.evolve import _breed_islands, _migrate, breed, evolve
from wormwars.evo.genomes import load_genome, nickname, save_genome, save_population
from wormwars.interface import load_interface

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def distinct(spec, n, dale, seed=0) -> Genome:
    """A population whose every field differs between strains (initial gaps are identical across
    strains, so they are overwritten)."""
    cfg = Config()
    cfg.brain.dale = dale
    g = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed))
    g.g.copy_(torch.rand(g.g.shape, generator=torch.Generator().manual_seed(seed + 1)) * 0.1)
    g.clamp_()
    return g


def same_strain(a: Genome, i: int, b: Genome, j: int) -> bool:
    for k in Genome.PARAMS:
        x, y = getattr(a, k), getattr(b, k)
        if (x is None) != (y is None):
            return False
        if x is not None and not torch.equal(x[i], y[j]):
            return False
    return True


def test_every_tensor_field_is_a_declared_parameter():
    """A field added to Genome later must join Genome.PARAMS, which every operation iterates."""
    fields = {f.name for f in dataclasses.fields(Genome)} - {"spec", "cfg"}
    assert fields == set(Genome.PARAMS)


@pytest.mark.parametrize("dale", [False, True])
def test_every_parameter_survives_every_operation(parts, tmp_path, dale):
    con, iface, spec = parts
    p = distinct(spec, 6, dale)
    # select, clone
    s = p.select([4, 1])
    assert same_strain(s, 0, p, 4) and same_strain(s, 1, p, 1)
    c = p.clone()
    assert all(same_strain(c, i, p, i) for i in range(6))
    # cat and assign
    cat = Genome.cat([p.select([0]), p.select([5])])
    assert same_strain(cat, 0, p, 0) and same_strain(cat, 1, p, 5)
    a = p.assign([2, 3], p.select([5, 0]))
    assert same_strain(a, 2, p, 5) and same_strain(a, 3, p, 0) and same_strain(a, 1, p, 1)
    # breed with zero mutation: elites exact, every child an exact copy of some parent
    cfg = Config()
    cfg.brain.dale = dale
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = 6, 2, 3
    cfg.mutation.w_sigma = cfg.mutation.g_sigma = cfg.mutation.tau_sigma = cfg.mutation.bias_sigma = 0.0
    fit = np.array([0.0, 5.0, 1.0, 4.0, 2.0, 3.0])
    nxt = breed(p, fit, cfg, torch.Generator().manual_seed(1))
    assert same_strain(nxt, 0, p, 1) and same_strain(nxt, 1, p, 3)
    for i in range(6):
        assert any(same_strain(nxt, i, p, j) for j in (1, 3, 5))
    # islands and migration
    cfg.evo.islands, cfg.evo.migrants = 2, 1
    isl = np.arange(6) % 2
    bi = _breed_islands(p, fit, isl, cfg, torch.Generator().manual_seed(2))
    for i in range(6):
        assert any(same_strain(bi, i, p, j) for j in np.flatnonzero(isl == isl[i]))
    moved, _ = _migrate(p, fit, isl, cfg.evo, torch.Generator().manual_seed(3))
    # island 0 = {0, 2, 4} (fit 0, 1, 2), island 1 = {1, 3, 5} (fit 5, 4, 3): island 0's best (4)
    # replaces island 1's worst (5), and island 1's best (1) replaces island 0's worst (0)
    assert same_strain(moved, 5, p, 4) and same_strain(moved, 0, p, 1)
    # save and load, one genome and a population
    one, _ = load_genome(save_genome(tmp_path / "one.npz", p, 3, cfg=cfg), spec)
    assert same_strain(one, 0, p, 3)
    pop_, _ = load_genome(save_population(tmp_path / "pop.npz", p, cfg=cfg), spec)
    assert all(same_strain(pop_, i, p, i) for i in range(6))


def test_operations_do_not_alias_their_inputs(parts):
    con, iface, spec = parts
    p = distinct(spec, 4, True)
    before = p.clone()
    for out in (p.select([0, 1]), p.clone(), Genome.cat([p.select([0]), p.select([1])]),
                p.assign([0], p.select([1])), p.with_params(bias=p.bias + 1.0)):
        for k in Genome.PARAMS:
            getattr(out, k).add_(1.0)
    assert all(same_strain(p, i, before, i) for i in range(4))


def test_no_genome_is_built_by_hand_in_the_library():
    """Hand-built Genome(...) calls dropped fields before (coevolution lost dale_sign). Only the
    class itself and the loader build one; everything else uses select, cat, assign or
    with_params."""
    allowed = {ROOT / "wormwars" / "brain.py", ROOT / "wormwars" / "evo" / "genomes.py"}
    offenders = []
    for path in (ROOT / "wormwars").rglob("*.py"):
        if path in allowed:
            continue
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"(?<![\w.])Genome\(", line):
                offenders.append(f"{path.relative_to(ROOT)}:{n}")
    assert not offenders, offenders


def test_saved_fitness_is_per_strain_and_the_champion_is_the_logged_best(parts, tmp_path):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 60
    cfg.evo.population, cfg.evo.generations, cfg.evo.worlds_per_strain = 6, 2, 2
    cfg.evo.holdout_worlds, cfg.evo.elites, cfg.evo.truncation = 2, 2, 3
    r = evolve(cfg, iface, spec, run=0, run_seed=11, verbose=False, holdout_every=9, out_dir=tmp_path)
    pop_, meta = load_genome(tmp_path / f"{spec.label}-run00-final.npz", spec)
    assert len(meta["fitness"]) == cfg.evo.population == pop_.n_strains
    assert len(meta["best_per_generation"]) == cfg.evo.generations
    best = int(np.argmax(meta["fitness"]))
    assert nickname(r.champion) == r.log[-1].best_nickname == nickname(pop_, best)
    assert meta["fitness"][best] == pytest.approx(r.log[-1].best)


def test_scores_pair_with_their_genomes_under_permutation_and_chunking(parts):
    """CPU is the deterministic mode: full [strain, world] arrays must match exactly."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 40
    p = distinct(spec, 5, False)
    ids = np.array([7, 8, 9])
    base = rollout(cfg, iface, p, ids, run_seed=3, chunk_worlds=64).score
    perm = [3, 0, 4, 1, 2]
    permuted = rollout(cfg, iface, p.select(perm), ids, run_seed=3, chunk_worlds=64).score
    np.testing.assert_array_equal(permuted, base[perm])
    chunked = rollout(cfg, iface, p, ids, run_seed=3, chunk_worlds=3).score
    np.testing.assert_array_equal(chunked, base)


def test_jitter_noise_follows_world_identity_not_batch_position(parts):
    """Astra's reproduction (D065): two strains, worlds 101 and 102, run seed 3, radius 1, 20
    ticks. Changing chunk_worlds from 4 to 2 changed a per-world score."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.max_ticks = 20
    cfg.world.food_probe, cfg.world.food_probe_radius = "jitter", 1.0
    p = distinct(spec, 2, False)
    ids = np.array([101, 102])
    a = rollout(cfg, iface, p, ids, run_seed=3, chunk_worlds=4).score
    b = rollout(cfg, iface, p, ids, run_seed=3, chunk_worlds=2).score
    np.testing.assert_array_equal(a, b)
    # and a strain placed second gets the noise it would get first
    c = rollout(cfg, iface, p.select([1, 0]), ids, run_seed=3, chunk_worlds=4).score
    np.testing.assert_array_equal(c[[1, 0]], a)


def test_loading_checks_the_genome_hash(parts, tmp_path):
    con, iface, spec = parts
    p = distinct(spec, 2, False)
    path = save_genome(tmp_path / "g.npz", p, 0, cfg=Config())
    d = dict(np.load(path, allow_pickle=False))
    d["bias"] = d["bias"] + 1e-3
    np.savez_compressed(path, **d)
    with pytest.raises(ValueError, match="hash"):
        load_genome(path, spec)


def test_committed_n2_genomes_pass_the_hash_check(parts):
    con, iface, spec = parts
    files = [p for p in ROOT.glob("runs/**/*.npz") if "N2" in p.name]
    assert files
    for f in files:
        meta = json.loads(str(np.load(f, allow_pickle=False)["meta"]))
        if meta.get("graph") != spec.label:
            continue
        load_genome(f, spec)  # raises on a hash mismatch
