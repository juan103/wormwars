"""The schedule is balanced, crossed, resumable, and stops only between whole batches."""

from __future__ import annotations

import json
from collections import Counter

import numpy as np
import pytest
import torch

from wormwars.config import Config
from wormwars.exp02 import grid


def test_task_configs():
    base = Config()
    t0, t1, a = (grid.task_config(base, t) for t in ("T0", "T1", "A"))
    assert (t0.world.food_sensing, t0.world.sense_scale_pheromone) == ("stereo", 0.0)
    assert (t1.world.food_sensing, t1.world.sense_scale_pheromone) == ("mono", 0.0)
    assert (a.world.food_sensing, a.world.sense_scale_pheromone) == ("stereo", 0.35)
    for c in (t0, t1, a):
        assert c.brain.substeps == 32 and c.evo.generations == 40 and c.evo.holdout_worlds == 64
    assert base.brain.substeps == 8, "the base config must not be mutated"
    with pytest.raises(ValueError):
        grid.task_config(base, "T9")


def test_schedule_counts_match_the_design():
    runs = [r for b in grid.run_schedule() for r in b]
    by = Counter((r.cell.task, r.cell.mapping, r.graph[:2]) for r in runs)
    for task, mapping in grid.MAIN:
        assert by[(task, mapping, "N2")] == 4 + (6 if (task, mapping) == ("T1", "M0") else 0)
        assert by[(task, mapping, "SH")] == 12
    assert by[("A", "M0", "N2")] == 4 and by[("A", "M0", "SH")] == 6
    assert sum(r.generations == 80 for r in runs) == 8
    assert len(runs) == 128
    assert len({r.key for r in runs}) == len(runs)


def test_every_run_records_generation_0_and_39():
    """Plan review F1: 40-generation runs must keep their generation-39 champion too."""
    for b in grid.run_schedule():
        for r in b:
            assert 0 in r.snapshots and 39 in r.snapshots, r.key


def test_the_strength_control_uses_three_permutations():
    """Plan review F6: one permutation six times would confound one draw with 'strengths matter'."""
    perms = {r.graph for b in grid.run_schedule() for r in b if r.graph.startswith("N2perm")}
    assert perms == {"N2perm1", "N2perm2", "N2perm3"}
    seeds = {grid.brain_config_for_graph(Config(), g).brain.init_permutation_seed for g in perms}
    assert len(seeds) == 3


def test_seeds_are_crossed_across_cells():
    runs = [r for b in grid.run_schedule() for r in b]
    seeds = {}
    for r in runs:
        seeds.setdefault((r.graph, r.run), set()).add(r.run_seed)
    assert all(len(s) == 1 for s in seeds.values()), "one seed per (graph, run) in every cell"
    assert len({next(iter(s)) for s in seeds.values()}) == len(seeds), "units never share a seed"


def test_every_batch_is_one_replicate_across_all_its_cells():
    for batch in grid.run_schedule():
        assert len({(r.graph, r.run) for r in batch}) == 1


def test_a_budget_cut_loses_second_replicates_before_any_n2_replicate():
    """Plan review F8: the tail of the schedule is what a budget cut removes."""
    units = [(b[0].graph, b[0].run) for b in grid.run_schedule()]
    last_n2 = max(i for i, (g, _) in enumerate(units) if g == "N2")
    first_second_sh = min(i for i, (g, r) in enumerate(units) if g.startswith("SH") and r == 1)
    first_perm = min(i for i, (g, _) in enumerate(units) if g.startswith("N2perm"))
    assert last_n2 < first_second_sh < first_perm


def test_resume_skips_done_runs_without_shifting_seeds():
    sched = grid.run_schedule()
    done = {r.key for r in sched[0]} | {sched[1][0].key}
    rest = grid.pending(sched, done)
    left = [r for b in rest for r in b]
    assert all(r.key not in done for r in left)
    original = {r.key: r.run_seed for b in sched for r in b}
    assert all(original[r.key] == r.run_seed for r in left)


def test_records_survive_a_partial_trailing_line(tmp_path):
    """Plan review F17: a kill mid-write must not make the runner unrestartable."""
    p = tmp_path / "records.jsonl"
    p.write_text(json.dumps({"key": "a", "wall_seconds": 5.0}) + "\n" + '{"key": "b", "wall', encoding="utf-8")
    recs = grid.read_records(p)
    assert [r["key"] for r in recs] == ["a"]


def test_budget_stops_between_batches():
    assert grid.select_batches(10, elapsed_s=0, per_batch_s=100, budget_s=350) == 3
    assert grid.select_batches(10, elapsed_s=300, per_batch_s=100, budget_s=350) == 0
    assert grid.select_batches(2, elapsed_s=0, per_batch_s=100, budget_s=1e9) == 2


def test_a_saved_champion_replays_exactly_under_its_manifest(tmp_path):
    """Plan review F18: in-memory and saved-and-reloaded rollouts must match per condition type."""
    from wormwars.brain import BrainSpec, Genome
    from wormwars.connectome import load_connectome
    from wormwars.evo import load_genome, rollout, save_genome
    from wormwars.exp02.manifest import check_manifest, run_manifest

    con = load_connectome()
    remap = {"R1": [["ASJL", "ASJR"], ["ASIL", "ASIR"], ["ASGL", "ASGR"]]}
    for task, mapping, graph in (("T1", "R1", "SH1"), ("T0", "M0", "N2perm2")):
        cfg = grid.brain_config_for_graph(grid.task_config(Config(), task), graph)
        cfg.world.max_ticks = 40
        iface = grid.interface_for(con, mapping, remap)
        spec = BrainSpec.from_connectome(grid.graph_for(con, graph))
        g = Genome.random(spec, cfg.brain, 1, generator=torch.Generator().manual_seed(3))
        path = save_genome(tmp_path / f"{graph}.npz", g, cfg=cfg, **run_manifest(cfg, iface, spec))
        back, meta = load_genome(path, spec, None)
        check_manifest(meta, cfg, iface, spec)
        ids = np.arange(2)
        np.testing.assert_array_equal(rollout(cfg, iface, g, ids, 5).score,
                                      rollout(cfg, iface, back, ids, 5).score)
