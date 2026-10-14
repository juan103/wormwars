"""The evolutionary E4-D's formal run: its registered constants and pure helpers, as the bound pre-registration fixes
them (`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`, D274). The stages are in `scripts/e4d_evo_formal.py`.

- **Runs and seeds** (§3): L 0-31, F 100-103, S 200-231; seed 1 440 000 + the run's number.
- **Blocks** (§4): per run, a 64-maze validation block and the 64 maze ids after it as its test block; the check and
  checkpoint blocks; the training and timing ranges; `preflight` resolves every block as it will be played and
  refuses collisions, with each other or with the pilot.
- **The registered assertions** (§5) raise `IntegrityError`: per-maze balance, ids in range. `is_integrity` tells an
  integrity failure from an infrastructure stop by the frame's recorded error.
- **Dependencies, groups and caps** (§5, §9); S's trigger (§3).
- **Reports** (§7): the gains and the readings, only through `evo_stats.reading` and `evo_stats.improvement`, with the
  registered counts.
"""

from __future__ import annotations

import numpy as np

from . import evo_stats as ES

MAZE_SEED = 1_420_000
SEED_BASE = 1_440_000
POP = 32
MAZES = 64
TRIALS = 2 * MAZES
FIRST_RUN = {"L": 0, "F": 100, "S": 200}
N_RUNS = {"L": 32, "F": 4, "S": 32}
BASES = {"L": 55_000, "F": 60_000, "S": 61_000}
CHECK_IDS = np.arange(54_000, 54_064)
CHECKPOINT_IDS = np.arange(54_100, 54_108)
TRAIN = (100_000_000, 110_000_000)
TIMING = (110_000_000, 120_000_000)
PILOT_RANGES = ((53_000, 53_064), (53_100, 53_612), (53_700, 53_764), (53_800, 53_864), (70_000_000, 80_000_000),
                (90_000_000, 100_000_000))

CONDITIONS = {"intact": "real", "reversed": "decoy", "removed": "none", "fixed": "fixed0"}
BALANCED = ("removed", "fixed", "cut", "eg")  # assignment-blind by construction: per maze, real-first = decoy-first

DEPENDS = {"check": (), "train-l": ("check",), "evaluate-l": ("train-l",), "report-l": ("evaluate-l",),
           "train-f": ("report-l",), "evaluate-f": ("train-f",), "report-f": ("evaluate-f",),
           "train-s": ("report-l",), "evaluate-s": ("train-s",), "report-s": ("evaluate-s",)}
GROUP = {s: ("l" if s == "check" else s.rsplit("-", 1)[1]) for s in DEPENDS}
CAPS = {"l": 8.0, "f": 1.5, "s": 6.0}  # GPU-hours, each counting every attempt of its group's stages
TRIGGER = (ES.STATES[3], ES.STATES[4])  # "practical gain excluded; transfer not detected", "inconclusive"


class IntegrityError(RuntimeError):
    """A registered assertion failed (§5): the arm is "not evaluable", and the stage is never rerun."""


def runs(arm: str) -> list[dict]:
    return [{"arm": arm, "run": FIRST_RUN[arm] + k, "seed": SEED_BASE + FIRST_RUN[arm] + k} for k in range(N_RUNS[arm])]


def blocks(arm: str, run: int) -> tuple[np.ndarray, np.ndarray]:
    """The run's validation and test ids."""
    k = int(run) - FIRST_RUN[arm]
    if not 0 <= k < N_RUNS[arm]:
        raise ValueError(f"{arm} has no run {run}")
    v0 = BASES[arm] + 128 * k
    return np.arange(v0, v0 + MAZES), np.arange(v0 + MAZES, v0 + 2 * MAZES)


def all_blocks() -> dict:
    out = {"check": CHECK_IDS, "checkpoints": CHECKPOINT_IDS}
    for arm in FIRST_RUN:
        for r in runs(arm):
            v, t = blocks(arm, r["run"])
            out[f"{arm}{r['run']}:validation"], out[f"{arm}{r['run']}:test"] = v, t
    return out


def _in_pilot(ids: np.ndarray) -> np.ndarray:
    return np.any([(ids >= lo) & (ids < hi) for lo, hi in PILOT_RANGES], axis=0)


def preflight(named: dict, resolve) -> dict:
    """Every block resolved as it will be played (`resolve`: `evo_trial.qualifying` at the maze seed); every
    replacement recorded; the resolved blocks pairwise disjoint and disjoint from the pilot's, else `IntegrityError`."""
    resolved, replacements, owner = {}, {}, {}
    for name, ids in named.items():
        ids = np.asarray(ids)
        got = np.asarray(resolve(ids)).reshape(ids.shape)
        resolved[name] = got
        moved = [[int(a), int(b)] for a, b in zip(ids, got) if a != b]
        if moved:
            replacements[name] = moved
        if np.any(_in_pilot(got)):
            raise IntegrityError(f"block {name} resolves into the pilot's ids")
        for i in got.tolist():
            if i in owner and owner[i] != name:
                raise IntegrityError(f"maze {i} is in blocks {owner[i]} and {name}")
            owner[i] = name
    return {"replacements": replacements, "blocks": {k: [int(v[0]), int(v[-1]), len(v)] for k, v in resolved.items()}}


def check_ids(ids: np.ndarray) -> None:
    """Resolved ids played in training: the training range, or the checkpoint block (§4)."""
    ids = np.asarray(ids)
    ok = ((ids >= TRAIN[0]) & (ids < TRAIN[1])) | np.isin(ids, CHECKPOINT_IDS)
    if not np.all(ok):
        raise IntegrityError(f"resolved training ids outside their range: {np.unique(ids[~ok])[:5].tolist()}")


def assert_balanced(real_first_maze, decoy_first_maze, label: str) -> None:
    """[strains, mazes, 2]: per strain and maze, as many real-first as decoy-first entries (§5)."""
    rf = np.asarray(real_first_maze).sum(axis=2)
    df = np.asarray(decoy_first_maze).sum(axis=2)
    bad = np.argwhere(rf != df)
    if len(bad):
        raise IntegrityError(f"{label}: unbalanced at (strain, maze) {bad[:5].tolist()}")


def is_integrity(error: str) -> bool:
    """The frame records an error as "<type>: <message>"; these are registered integrity failures (§5)."""
    e = str(error)
    return (e.startswith("IntegrityError:") or e.startswith("FloatingPointError:")
            or e.startswith("RuntimeError: integrity:"))


def check_rerun_reason(reason) -> None:
    """A rerun needs a recorded reason naming the infrastructure cause (§5)."""
    if not reason or not str(reason).strip().lower().startswith("infrastructure:"):
        raise SystemExit('a rerun needs --reason "infrastructure: <the cause>" (a crash, a driver failure, the machine)')


def s_triggered(report_l: dict) -> bool:
    return report_l.get("state") in TRIGGER


def _share(c: dict) -> float:
    n = int(c["real_first"]) + int(c["decoy_first"]) + int(c["neither"])
    if n != TRIALS:
        raise ValueError(f"a test block has {n} trials, not {TRIALS}")
    return int(c["real_first"]) / TRIALS


def report(arm: str, per_run: list[dict]) -> dict:
    """§7.1-§7.2 against chance: each run's champion share on its test block minus 0.5, read by `evo_stats.reading`
    with the registered count; the champion minus E-G beside."""
    gains = [_share(r["test"]["intact"]) - 0.5 for r in per_run]
    minus_eg = [_share(r["test"]["intact"]) - _share(r["test"]["eg"]) for r in per_run]
    return {"arm": arm, "gains": gains, "minus_eg": minus_eg,
            "reading": ES.reading(gains, n_expected=N_RUNS[arm], trials=TRIALS)}


def improvement_report(per_run: list[dict]) -> dict:
    """§7.2, S against its start: the champion's share minus S₀'s on the same test block."""
    d = [_share(r["test"]["intact"]) - _share(r["start"]) for r in per_run]
    return {"differences": d, "reading": ES.improvement(d, n_expected=N_RUNS["S"], trials=TRIALS)}
