"""E3a's shuttle task: its configuration and world-id blocks
(experiments/E3-ab-organism/E3a/PREREGISTRATION.md §3, §7).

Built on E1's Task N configuration (σ 6, amplitude 1, R 1.5, wall clearance 3, 32 substeps, padding
on), with the task switched to "shuttle" and a horizon of 600 ticks.
"""

from __future__ import annotations

import numpy as np

from ..config import Config
from ..e1.task import task_n_config

# the sources' own random stream, apart from the map's and Task N's targets' (world.py uses the same)
SHUTTLE_SOURCES_STREAM = 0x5E3A

SELECTION_BASE, SELECTION_SPAN = 944_000_000, 500_000
VALIDATION_IDS = np.arange(945_000_000, 945_000_256)
TEST_IDS = np.arange(946_000_000, 946_000_256)
CENSUS_IDS = np.arange(947_000_000, 947_000_016)
ASSAY_IDS = np.arange(947_100_000, 947_100_256)
GATE_IDS = np.arange(947_200_000, 947_201_024)
CALIBRATION_IDS = np.arange(948_000_000, 948_000_256)
SMOKE_IDS = np.arange(0, 10_000)
EVALUATION_WORLD_SEED = 1_171_000


def shuttle_config(base: Config | None = None, *, horizon: int = 600) -> Config:
    c = task_n_config(base, sigma=6.0, amplitude=1.0, radius=1.5, separation=8.0, horizon=horizon)
    w = c.world
    w.task = "shuttle"
    w.shuttle_separation_min, w.shuttle_separation_max = 8.0, 14.0
    w.shuttle_spawn_min, w.shuttle_spawn_max = 6.0, 16.0
    w.shuttle_cue_ticks = 5
    return c
