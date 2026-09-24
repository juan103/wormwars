"""Experiment 02's grid: tasks, cells, crossed seeds, balanced resumable batches.

Every replicate unit (a graph and a run index) uses one seed in every cell it appears in, so
cells are paired within a unit: identical generation-0 populations, identical training and
checkpoint worlds. A batch is one unit's runs across all its cells. Batches are ordered so that a
budget cut removes second shuffle replicates and then the strength control before it removes any
N2 replicate or any first shuffle replicate.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ..config import Config
from ..connectome.graphs import shuffled
from ..interface import interface_from_spec, load_interface_spec, remapped_spec

ROOT = Path(__file__).resolve().parents[2]
EXP02_DIR = ROOT / "experiments" / "02-screening"
TARGET_DRIVE = (0.5, 0.4)
CHECKPOINT_IDS = np.arange(950_000_000, 950_000_016)
TUNING_IDS = np.arange(960_000_000, 960_000_032)
TUNING_SEED = 99_999
N2_RUNS, SH_GRAPHS, SH_RUNS, PERMS, PERM_RUNS = 4, 6, 2, 3, 2
MAIN = [("T0", m) for m in ("M0", "R1", "R2")] + [("T1", m) for m in ("M0", "R1", "R2", "MS")]
GRAPH_VARIANTS = (["N2"] + [f"N2perm{k}" for k in range(1, PERMS + 1)]
                  + [f"SH{k}" for k in range(1, SH_GRAPHS + 1)])
# Pre-registered continuation runs: 80 generations; their generation-39 snapshot is the
# 40-generation result, so they replace their 40-generation counterparts rather than adding runs.
CONTINUATION = {("T1", "M0", "N2", 0), ("T1", "M0", "N2", 1), ("T1", "M0", "SH1", 0),
                ("T1", "M0", "SH2", 0), ("T0", "M0", "N2", 0), ("T0", "M0", "N2", 1),
                ("T0", "M0", "SH1", 0), ("T0", "M0", "SH2", 0)}


def task_config(base: Config, task: str) -> Config:
    if task not in ("T0", "T1", "A"):
        raise ValueError(f"unknown task {task!r}")
    c = base.copy()
    c.brain.substeps = 32
    c.world.max_ticks = 400
    c.evo.generations, c.evo.population = 40, 32
    c.evo.worlds_per_strain, c.evo.holdout_worlds = 8, 64
    c.world.food_sensing = "mono" if task == "T1" else "stereo"
    c.world.sense_scale_pheromone = 0.35 if task == "A" else 0.0
    return c


@dataclass(frozen=True)
class Cell:
    task: str
    mapping: str


@dataclass(frozen=True)
class RunSpec:
    cell: Cell
    graph: str  # "N2", "N2perm1".."N2perm3", "SH1".."SH6"
    run: int
    run_seed: int
    generations: int
    snapshots: tuple

    @property
    def key(self) -> str:
        return f"{self.cell.task}-{self.cell.mapping}-{self.graph}-run{self.run:02d}"


def _seed(graph: str, run: int) -> int:
    if graph == "N2":
        return 20_000 + run
    if graph.startswith("N2perm"):
        return 22_000 + 10 * int(graph[6:]) + run
    return 21_000 + 10 * int(graph[2:]) + run


def _spec(task, mapping, graph, run) -> RunSpec:
    cont = (task, mapping, graph, run) in CONTINUATION
    return RunSpec(Cell(task, mapping), graph, run, _seed(graph, run), 80 if cont else 40, (0, 39))


def _unit_order() -> list[tuple[str, int]]:
    """N2 replicates interleaved with first shuffle replicates, then second shuffle replicates,
    then the strength control."""
    first = [f"SH{k}" for k in range(1, SH_GRAPHS + 1)]
    units, sh = [], iter(first)
    for r in range(N2_RUNS):
        units.append(("N2", r))
        for _ in range(-(-SH_GRAPHS // N2_RUNS)):  # ceil(6 / 4) = 2 shuffles per N2 replicate
            nxt = next(sh, None)
            if nxt is not None:
                units.append((nxt, 0))
    units += [(g, 0) for g in sh]  # any shuffles left over
    units += [(g, r) for r in range(1, SH_RUNS) for g in first]
    units += [(f"N2perm{k}", r) for r in range(PERM_RUNS) for k in range(1, PERMS + 1)]
    return units


def run_schedule() -> list[list[RunSpec]]:
    batches = []
    for graph, r in _unit_order():
        if graph.startswith("N2perm"):
            batches.append([_spec("T1", "M0", graph, r)])
            continue
        b = [_spec(t, m, graph, r) for t, m in MAIN]
        if graph == "N2" or r == 0:
            b.append(_spec("A", "M0", graph, r))
        batches.append(b)
    return batches


def pending(schedule, done_keys: set[str]) -> list[list[RunSpec]]:
    out = []
    for b in schedule:
        left = [r for r in b if r.key not in done_keys]
        if left:
            out.append(left)
    return out


def select_batches(n_batches: int, elapsed_s: float, per_batch_s: float, budget_s: float) -> int:
    """How many whole batches still fit in the budget."""
    if per_batch_s <= 0:
        return n_batches
    return max(0, min(n_batches, int((budget_s - elapsed_s) // per_batch_s)))


def read_records(path: Path) -> list[dict]:
    """Every complete record; a partial trailing line from an interrupted write is ignored."""
    if not Path(path).exists():
        return []
    out = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def graph_for(con, name: str):
    if name == "N2" or name.startswith("N2perm"):
        return con
    return shuffled(con, int(name[2:]), name)


def brain_config_for_graph(cfg: Config, name: str) -> Config:
    c = cfg.copy()
    if name.startswith("N2perm"):
        c.brain.init_chem_magnitude = c.brain.init_gap_magnitude = "permuted"
        c.brain.init_permutation_seed = int(name[6:])
    return c


def interface_for(con, mapping: str, remap_sets: dict):
    spec = load_interface_spec()
    if mapping == "M0":
        return interface_from_spec(con, spec)
    pairs = [tuple(p) for p in remap_sets[mapping]]
    return interface_from_spec(con, remapped_spec(spec, "food", pairs))
