"""T0 item 1, confirmation pass (D067): Astra's and Fable's findings on f6af625, each as a test
that failed before its fix."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo.genomes import genome_hash, load_genome, save_population
from wormwars.interface import load_interface
from wormwars.world import World, _hash32, _mix32

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def distinct(spec, n, dale, seed=0) -> Genome:
    cfg = Config()
    cfg.brain.dale = dale
    g = Genome.random(spec, cfg.brain, n, generator=torch.Generator().manual_seed(seed))
    g.g.copy_(torch.rand(g.g.shape, generator=torch.Generator().manual_seed(seed + 1)) * 0.1)
    g.clamp_()
    return g


def same_strain(a: Genome, i: int, b: Genome, j: int) -> bool:
    for k in Genome.PARAMS:
        x, y = getattr(a, k), getattr(b, k)
        if (x is None) != (y is None) or (x is not None and not torch.equal(x[i], y[j])):
            return False
    return True


def test_with_params_never_aliases_even_supplied_tensors(parts):
    """Astra reproduced: q = p.with_params(w=p.w); q.w += 1 changed p."""
    con, iface, spec = parts
    p = distinct(spec, 2, True)
    before = p.clone()
    q = p.with_params(w=p.w, bias=p.bias[:, :])  # the original tensor, and a view of it
    for k in Genome.PARAMS:
        getattr(q, k).add_(1.0)
    assert all(same_strain(p, i, before, i) for i in range(2))


def test_assign_checks_strain_count_and_dale_parity(parts):
    con, iface, spec = parts
    p, d = distinct(spec, 4, False), distinct(spec, 4, True)
    with pytest.raises(ValueError):
        p.assign([0, 1], p.select([2]))  # one strain into two slots would broadcast silently
    with pytest.raises(ValueError):
        p.assign([0], d.select([1]))  # a Dale source into a genome without signs
    with pytest.raises(ValueError):
        d.assign([0], p.select([1]))


def test_population_files_are_checked_by_full_per_strain_hashes(parts, tmp_path):
    """Nicknames have 63 x 63 = 3 969 values; Astra built a tampered population with the same
    nicknames that the loader accepted. New files store the full sha256 of every strain."""
    con, iface, spec = parts
    p = distinct(spec, 3, False)
    path = save_population(tmp_path / "pop.npz", p, cfg=Config())
    meta = json.loads(str(np.load(path, allow_pickle=False)["meta"]))
    assert meta["genome_sha256s"] == [genome_hash(p, i) for i in range(3)]
    d = {k: v.copy() for k, v in np.load(path, allow_pickle=False).items()}
    d["bias"][1, 0] += 1e-3
    np.savez_compressed(path, **d)
    with pytest.raises(ValueError, match="hash"):
        load_genome(path, spec)


def test_the_champion_is_the_logged_best_even_if_a_further_evaluation_would_rank_differently(parts, monkeypatch):
    """The old code re-evaluated the final population to pick the champion. Here every population
    evaluation after the first ranks the strains in reverse, so a re-evaluation would pick the
    logged worst: the champion must still be the logged best, by full hash."""
    import importlib
    E = importlib.import_module("wormwars.evo.evolve")
    con, iface, spec = parts
    real, calls = E.evaluate_on, {"n": 0}

    def rigged(cfg, iface_, genome, ids, run_seed, device, combat_stage=0):
        r = real(cfg, iface_, genome, ids, run_seed, device, combat_stage)
        if genome.n_strains > 1:
            calls["n"] += 1
            if calls["n"] > 1:
                r.score = -r.score
        return r

    monkeypatch.setattr(E, "evaluate_on", rigged)
    cfg = Config()
    cfg.world.max_ticks = 40
    cfg.evo.population, cfg.evo.generations, cfg.evo.worlds_per_strain = 5, 1, 2
    cfg.evo.holdout_worlds = 2
    r = E.evolve(cfg, iface, spec, run=0, run_seed=13, verbose=False, holdout_every=9)
    assert r.log[-1].best_sha256 == genome_hash(r.champion, 0)


def test_saved_fitness_is_the_full_final_vector_and_holdouts_and_snapshots_pair(parts, tmp_path, monkeypatch):
    import importlib
    E = importlib.import_module("wormwars.evo.evolve")
    con, iface, spec = parts
    seen = {"holdout": {}}
    real = E.evaluate_on

    def capture(cfg, iface_, genome, ids, run_seed, device, combat_stage=0):
        r = real(cfg, iface_, genome, ids, run_seed, device, combat_stage)
        if genome.n_strains > 1:
            seen["fit"], seen["pop"] = r.per_strain().copy(), genome.clone()
        else:
            seen["holdout"][genome_hash(genome, 0)] = float(r.per_strain()[0])
        return r

    monkeypatch.setattr(E, "evaluate_on", capture)
    cfg = Config()
    cfg.world.max_ticks = 40
    cfg.evo.population, cfg.evo.generations, cfg.evo.worlds_per_strain = 5, 3, 2
    cfg.evo.holdout_worlds, cfg.evo.elites, cfg.evo.truncation = 2, 2, 3
    r = E.evolve(cfg, iface, spec, run=0, run_seed=17, verbose=False, holdout_every=1,
                 out_dir=tmp_path, snapshots=(0, 2))
    pop_, meta = load_genome(tmp_path / f"{spec.label}-run00-final.npz", spec)
    np.testing.assert_array_equal(np.asarray(meta["fitness"]), seen["fit"])
    # anchor the logged hash independently of evolve's own argmax (Fable, D067)
    assert genome_hash(seen["pop"], int(np.argmax(seen["fit"]))) == r.log[-1].best_sha256
    assert all(same_strain(pop_, i, seen["pop"], i) for i in range(5))
    for g in r.log:
        if g.holdout_best is not None:
            assert seen["holdout"][g.best_sha256] == pytest.approx(g.holdout_best)
    for gen, snap in r.snapshots.items():
        assert genome_hash(snap, 0) == r.log[gen].best_sha256


def test_mutation_changes_parameters_but_never_the_dale_signs(parts):
    con, iface, spec = parts
    p = distinct(spec, 3, True)
    q = p.clone().mutate(Config().mutation, generator=torch.Generator().manual_seed(5))
    torch.testing.assert_close(q.dale_sign, p.dale_sign, rtol=0, atol=0)
    for k in ("w", "tau", "bias"):
        assert not torch.equal(getattr(q, k), getattr(p, k))
    nz = q.w != 0
    assert torch.equal(torch.sign(q.w[nz]), q.dale_sign[:, spec.chem_i][nz])


def _hash_from_arrays(d) -> str:
    h = hashlib.sha256(np.concatenate([np.atleast_2d(d[k])[0].astype(np.float32).ravel()
                                       for k in ("w", "g", "tau", "bias")]).tobytes())
    if d["dale"].size:
        h.update(np.atleast_2d(d["dale"])[0].astype(np.float32).tobytes())
    return h.hexdigest()


def test_every_committed_single_genome_matches_its_stored_hash():
    """Every graph, not only N2 (Fable): the hash needs no spec, only the stored arrays."""
    n = 0
    for f in ROOT.glob("runs/**/*.npz"):
        d = np.load(f, allow_pickle=False)
        if "meta" not in d.files:
            continue
        meta = json.loads(str(d["meta"]))
        if "genome_sha256" in meta:
            assert _hash_from_arrays(d) == meta["genome_sha256"], f.name
            n += 1
    assert n > 0


def test_the_jitter_hash_is_pinned():
    """lowbias32 (skeeto/hash-prospector), against an independent reference in Python ints."""
    edge = [0, 1, 0xFFFF, 0x10000, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 123456789]

    def ref(x):
        x ^= x >> 16
        x = (x * 0x7FEB352D) & 0xFFFFFFFF
        x ^= x >> 15
        x = (x * 0x846CA68B) & 0xFFFFFFFF
        return x ^ (x >> 16)

    assert [_mix32(x) for x in edge] == [ref(x) for x in edge]
    assert _hash32(torch.tensor(edge, dtype=torch.int64)).tolist() == [ref(x) for x in edge]


def test_jitter_uniforms_are_uniform_and_the_radius_is_bounded(parts):
    con, iface, spec = parts
    cfg = Config()
    cfg.world.food_probe, cfg.world.food_probe_radius = "jitter", 3.0
    p = distinct(spec, 1, False)
    w = World(cfg, iface, Brain(p), torch.zeros(64, 1, dtype=torch.long), run_seed=3,
              world_ids=np.arange(64))
    u = torch.cat([w._keyed_uniform(s).ravel() for s in (0, 1)])
    assert abs(u.mean().item() - 0.5) < 0.005 and abs(u.var().item() - 1 / 12) < 0.003
    assert (u >= 0).all() and (u < 1).all()
    pts = w.sample_points()
    moved = w._jittered(pts)
    assert ((moved - pts).norm(dim=-1) <= 3.0 + 1e-5).all()


def test_jitter_keys_are_explicit_coordinates_not_a_padded_flat_index(parts):
    """Astra: keys used a flattened point index that includes the padded wey count, so a batch
    neighbour with more weys changed another match's noise. Keys are now explicit
    (swarm, wey, sample point) coordinates."""
    con, iface, spec = parts
    cfg = Config()
    cfg.world.food_probe = "jitter"
    p = distinct(spec, 1, False)
    w = World(cfg, iface, Brain(p), torch.zeros(1, 1, dtype=torch.long), run_seed=3,
              world_ids=np.array([5]))
    a = w._keyed_uniform(0, n_swarms=2, n_weys=2)  # [worlds, swarms, weys, points]
    b = w._keyed_uniform(0, n_swarms=2, n_weys=3)
    torch.testing.assert_close(a, b[:, :, :2], rtol=0, atol=0)


def test_published_champions_match_their_logs_final_best_by_nickname():
    """Fable's one-time check, made reproducible. Old logs carry only the nickname (about 12
    bits), so this detects mismatches at nickname resolution only; it is not proof of identity."""
    import re
    n = 0
    import subprocess
    tracked = subprocess.check_output(["git", "ls-files", "runs/**/champion-*.npz"], cwd=ROOT, text=True).split()
    for f in sorted(ROOT / t for t in tracked):  # committed files only, so a fresh clone agrees (D084)
        m = re.match(r"champion-(.+)-run(\d+)\.npz", f.name)
        log = f.parent / f"{m.group(1)}-run{m.group(2)}-log.json" if m else None
        if log is None or not log.exists():
            continue
        meta = json.loads(str(np.load(f, allow_pickle=False)["meta"]))
        assert meta["nickname"] == json.loads(log.read_text())[-1]["best_nickname"], f.name
        n += 1
    assert n == 135  # the committed champions with a log; 18 more exist only locally (D084)
