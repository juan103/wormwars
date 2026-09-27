"""T0 items 3-5 after Astra's and Fable's review (D074): the island coverage section 6 promises,
numerical checks at every tick across graphs and tasks, and adversarial tests for the per-tick
ledger contract."""

from __future__ import annotations

import importlib
import math

import numpy as np
import pytest
import torch

from wormwars.brain import Brain, BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.connectome.graphs import random_graph, shuffled
from wormwars.evo import rollout
from wormwars.evo.genomes import genome_hash
from wormwars.exp02 import grid
from wormwars.interface import load_interface
from wormwars.world import World

E = importlib.import_module("wormwars.evo.evolve")
R = importlib.import_module("wormwars.evo.rollout")


@pytest.fixture(scope="module")
def parts():
    con = load_connectome()
    return con, load_interface(con), BrainSpec.from_connectome(con)


def _cfg(pop, islands, migrants=1, migrate_every=1, gens=3):
    cfg = Config()
    cfg.world.max_ticks = 10
    cfg.evo.population, cfg.evo.islands, cfg.evo.migrants = pop, islands, migrants
    cfg.evo.migrate_every, cfg.evo.generations, cfg.evo.worlds_per_strain = migrate_every, gens, 1
    cfg.evo.holdout_worlds, cfg.evo.elites, cfg.evo.truncation = 1, 2, 4
    return cfg


# ------------------------------------------------------------------ islands (section 6)

def test_every_ring_edge_including_the_wrap_and_untouched_slots(parts):
    con, iface, spec = parts
    cfg = _cfg(9, 3)
    p = Genome.random(spec, cfg.brain, 9, generator=torch.Generator().manual_seed(1))
    isl = np.arange(9) % 3  # island k = {k, k+3, k+6}
    fit = np.array([5.0, 1.0, 9.0, 0.0, 2.0, 3.0, 7.0, 4.0, 6.0])
    moved, new_fit = E._migrate(p, fit, isl, cfg.evo, torch.Generator().manual_seed(2))
    best = {k: int(np.flatnonzero(isl == k)[np.argmax(fit[isl == k])]) for k in range(3)}
    worst = {k: int(np.flatnonzero(isl == k)[np.argmin(fit[isl == k])]) for k in range(3)}
    for k in range(3):  # island k's best replaces island k+1's worst, including 2 -> 0
        dst = worst[(k + 1) % 3]
        assert genome_hash(moved, dst) == genome_hash(p, best[k]) and new_fit[dst] == fit[best[k]]
    for s in set(range(9)) - set(worst.values()):
        assert genome_hash(moved, s) == genome_hash(p, s) and new_fit[s] == fit[s]


def test_an_uneven_population_runs_through_migration(parts):
    con, iface, spec = parts
    r = E.evolve(_cfg(5, 2, migrants=1, migrate_every=1), iface, spec, run=0, run_seed=3, verbose=False,
                 holdout_every=99)
    assert len(r.log) == 3


def test_log_and_snapshots_pair_with_islands_and_migration(parts, monkeypatch):
    con, iface, spec = parts
    real, seen = E.evaluate_on, {}

    def capture(cfg, iface_, genome, ids, run_seed, device, combat_stage=0):
        r = real(cfg, iface_, genome, ids, run_seed, device, combat_stage)
        if genome.n_strains > 1:
            seen.setdefault("pops", []).append((genome.clone(), r.per_strain().copy()))
        return r

    monkeypatch.setattr(E, "evaluate_on", capture)
    r = E.evolve(_cfg(6, 2, migrants=1, migrate_every=1), iface, spec, run=0, run_seed=4, verbose=False,
                 holdout_every=1, snapshots=(1, 2))
    for gen, (pop, fit) in enumerate(seen["pops"]):
        assert r.log[gen].best_sha256 == genome_hash(pop, int(np.argmax(fit)))
    assert set(r.snapshots) == {1, 2}  # not vacuous (Fable)
    for gen, snap in r.snapshots.items():
        assert genome_hash(snap, 0) == r.log[gen].best_sha256


@pytest.mark.parametrize("kw, msg", [
    ({"pop": 6, "islands": 0}, "islands"),
    ({"pop": 6, "islands": 2, "migrants": -1}, "migrants"),
    ({"pop": 3, "islands": 3, "migrants": 0}, "at least 2"),
])
def test_further_unsupported_island_settings_are_refused(parts, kw, msg):
    con, iface, spec = parts
    with pytest.raises(ValueError, match=msg):
        E.evolve(_cfg(**kw), iface, spec, run=0, run_seed=1, verbose=False)


def test_a_non_finite_fitness_stops_evolution(parts, monkeypatch):
    """np.argmax would pick a NaN strain as the best (Fable)."""
    con, iface, spec = parts
    real = E.evaluate_on

    def poisoned(cfg, iface_, genome, ids, run_seed, device, combat_stage=0):
        r = real(cfg, iface_, genome, ids, run_seed, device, combat_stage)
        if genome.n_strains > 1:
            r.score = r.score.copy()
            r.score[1, 0] = np.nan
        return r

    monkeypatch.setattr(E, "evaluate_on", poisoned)
    with pytest.raises(FloatingPointError):
        E.evolve(_cfg(4, 1, gens=1), iface, spec, run=0, run_seed=5, verbose=False)


# ------------------------------------------------------------------ numbers at every tick

def _bounded_random(spec, cfg, n, seed):
    """Random genomes pushed hard into the mutation bounds, and the mixed-sign corner."""
    g = Genome.random(spec, cfg, n, generator=torch.Generator().manual_seed(seed))
    for k, scale in (("w", 10 * cfg.w_max), ("g", 10 * cfg.g_max), ("bias", 10 * cfg.b_max)):
        getattr(g, k).add_(torch.randn(getattr(g, k).shape, generator=torch.Generator().manual_seed(seed + 1)) * scale)
    g.tau.mul_(torch.exp(torch.randn(g.tau.shape, generator=torch.Generator().manual_seed(seed + 2)) * 5))
    g.clamp_()
    gen = torch.Generator().manual_seed(seed + 3)
    w_sign = torch.where(torch.rand(1, spec.n_chem, generator=gen) < 0.5, -1.0, 1.0)
    b_sign = torch.where(torch.rand(1, spec.n, generator=gen) < 0.5, -1.0, 1.0)  # mixed bias too (Fable)

    def corner(ws, bs):
        return g.select([0]).with_params(w=ws * cfg.w_max, g=torch.full((1, spec.n_gap), cfg.g_max),
                                         tau=torch.full((1, spec.n), cfg.tau_min), bias=bs * cfg.b_max)

    one_w, one_b = torch.ones(1, spec.n_chem), torch.ones(1, spec.n)
    return Genome.cat([g, corner(w_sign, b_sign), corner(one_w, one_b), corner(-one_w, -one_b)])


@pytest.mark.parametrize("task", ["T0", "T1"])
@pytest.mark.parametrize("which", ["N2", "SH", "RD"])
def test_everything_stays_finite_at_every_tick(parts, task, which):
    con, iface, spec = parts
    graph = {"N2": con, "SH": shuffled(con, seed=11), "RD": random_graph(con, seed=12)}[which]
    gspec = BrainSpec.from_connectome(graph)
    cfg = grid.task_config(Config(), task)
    g = _bounded_random(gspec, cfg.brain, 1, seed=21)  # 1 bounded random + 3 corners
    n_worlds = 8  # distinct world ids per genome, as T0.md section 5 declares (Astra)
    strain_of = torch.arange(g.n_strains).repeat_interleave(n_worlds).reshape(-1, 1)
    w = World(cfg, load_interface(graph), Brain(g), strain_of, run_seed=6,
              world_ids=np.tile(np.arange(n_worlds), g.n_strains))
    while not w.done():
        w.tick()
        assert all(torch.isfinite(v).all() for v in w.v), f"brain state, tick {w.tick_count}"
        assert torch.isfinite(w.energy).all(), f"energy, tick {w.tick_count}"
    from wormwars.evo.rollout import foraging_score
    assert torch.isfinite(foraging_score(w)).all()


# ------------------------------------------------------------------ the ledger contract

def _fake_errors(monkeypatch, seq):
    """World.energy_ledger_error returns the values of `seq` in turn (one per call, per world)."""
    it = iter(seq)

    def fake(self):
        v = next(it, seq[-1])
        return torch.full((self.n_worlds,), float(v), dtype=torch.float64)

    monkeypatch.setattr(World, "energy_ledger_error", fake)


def _run(parts, cfg, ids=(1,), chunk=None):
    con, iface, spec = parts
    g = Genome.random(spec, cfg.brain, 2, generator=torch.Generator().manual_seed(7))
    return rollout(cfg, iface, g, np.array(ids), run_seed=1, chunk_worlds=chunk)


def test_an_early_ledger_peak_survives_a_zero_final_residual(parts, monkeypatch):
    cfg = Config()
    cfg.world.max_ticks, cfg.world.check_ledger_every_tick = 4, True
    _fake_errors(monkeypatch, [0.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    r = _run(parts, cfg)
    assert r.ledger_rel_error > 0 and r.ledger_error == 0.0


def test_an_early_nan_survives_later_finite_ticks(parts, monkeypatch):
    cfg = Config()
    cfg.world.max_ticks, cfg.world.check_ledger_every_tick = 4, True
    _fake_errors(monkeypatch, [0.0, float("nan"), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    assert math.isnan(_run(parts, cfg).ledger_rel_error)


def test_an_infinite_residual_is_reported(parts, monkeypatch):
    cfg = Config()
    cfg.world.max_ticks, cfg.world.check_ledger_every_tick = 3, True
    _fake_errors(monkeypatch, [float("inf")])
    assert math.isinf(_run(parts, cfg).ledger_rel_error)


@pytest.mark.parametrize("order", [(1.0, float("nan")), (float("nan"), 1.0)])
def test_nan_propagates_across_chunks_in_either_order(order):
    a, b = order
    assert math.isnan(R._nanmax(R._nanmax(0.0, a), b))


def test_the_relative_error_uses_each_worlds_own_start(parts):
    con, iface, spec = parts
    cfg = Config()
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(8))
    w = World(cfg, iface, Brain(g), torch.zeros(2, 1, dtype=torch.long), run_seed=1, world_ids=np.array([1, 2]))
    w.start_energy_total = torch.tensor([10.0, 1000.0], dtype=torch.float64)
    err = torch.tensor([1.0, 1.0], dtype=torch.float64)
    w.energy_ledger_error = lambda: err
    torch.testing.assert_close(w.energy_ledger_rel_error(), torch.tensor([0.1, 0.001], dtype=torch.float64))


def test_the_ledger_gate_covers_deaths(parts):
    """At 02's settings nothing starves in 200 ticks (Fable), so this case forces deaths."""
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T0")
    cfg.world.check_ledger_every_tick = True
    cfg.world.metabolic_drain = 0.2
    g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(9))
    w = World(cfg, iface, Brain(g), torch.zeros(4, 1, dtype=torch.long), run_seed=2, world_ids=np.arange(4))
    alive0 = int(w.alive.sum())
    w.run()
    assert int(w.alive.sum()) < alive0, "nobody died: the case does not exercise deaths"
    assert float(w.ledger_rel_max.max()) < 1e-5


def test_tracking_the_ledger_changes_no_result(parts):
    con, iface, spec = parts
    cfg = grid.task_config(Config(), "T1")
    cfg.world.max_ticks = 60
    off = _run(parts, cfg, ids=(1, 2)).score
    cfg.world.check_ledger_every_tick = True
    np.testing.assert_array_equal(_run(parts, cfg, ids=(1, 2)).score, off)


def test_nan_is_not_swallowed_in_coevolution_and_exp02_reporting():
    """The same max(0.0, nan) pattern in coevolution's play and exp02's run record and report."""
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    import re
    bare_max = re.compile(r'(?<![\w.])max\((worst_err|x\.ledger_error|r\["ledger_error"\])')
    for rel in ("wormwars/evo/coevolve.py", "scripts/exp02.py", "wormwars/exp02/report.py"):
        assert not bare_max.search((root / rel).read_text(encoding="utf-8")), rel
    from wormwars.exp02.report import _max_keeping_nan
    assert math.isnan(_max_keeping_nan([0.0, float("nan"), 1.0])) and _max_keeping_nan([1.0, 3.0]) == 3.0


@pytest.mark.parametrize("family", ["N2", "SH1", "RD1"])
def test_a_published_champion_of_each_family_stays_finite_at_every_tick(parts, family):
    """One 01b champion per graph family, 8 worlds, checked at every tick (Astra, Fable)."""
    from pathlib import Path
    from wormwars.evo.genomes import apply_world_meta, load_genome
    con, iface, spec = parts
    graph = {"N2": con, "SH1": shuffled(con, seed=1, label="SH1"), "RD1": random_graph(con, seed=1, label="RD1")}[family]
    f = Path(__file__).resolve().parents[1] / "runs" / "exp01b-direction-corrected" / f"champion-{family}-run00.npz"
    champ, meta = load_genome(f, BrainSpec.from_connectome(graph))  # the edge hash checks the rebuilt graph
    cfg, _ = apply_world_meta(Config(), meta)
    cfg.brain = champ.cfg
    w = World(cfg, load_interface(graph), Brain(champ), torch.zeros(8, 1, dtype=torch.long), run_seed=8,
              world_ids=np.arange(8))
    while not w.done():
        w.tick()
        assert all(torch.isfinite(v).all() for v in w.v), f"brain state, tick {w.tick_count}"
        assert torch.isfinite(w.energy).all(), f"energy, tick {w.tick_count}"
    from wormwars.evo.rollout import foraging_score
    assert torch.isfinite(foraging_score(w)).all()


def test_coevolution_keeps_a_nan_ledger_error(parts, monkeypatch):
    """Behaviour, not a source search (Fable): coevolution's play reports NaN, not 0."""
    from wormwars.evo.coevolve import build_schedule, play
    con, iface, spec = parts
    cfg = Config()
    cfg.world.n_swarms, cfg.world.max_ticks = 2, 3
    a = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(1))
    b = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(2))
    matches = build_schedule(1, 1, np.array([1]), np.random.default_rng(0), sizes=(2, 2))
    monkeypatch.setattr(World, "energy_ledger_error",
                        lambda self: torch.full((self.n_worlds,), float("nan"), dtype=torch.float64))
    res = play(cfg, iface, a, b, matches, 1, "cpu", 1)
    assert math.isnan(res.ledger_error)
