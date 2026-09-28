"""Task N's configuration and world-id ranges (docs/E1/DESIGN.md v2.1).

E1 has its own config builder: 02's `grid.task_config` pins single-strain padding off, so building
E1 on it would silently disable padding (T1, D092).
"""

from __future__ import annotations

import numpy as np

from ..config import Config

# Separate ranges for the task pilot, tuning, the positive-control gate and 04a's hold-out, disjoint
# from every earlier experiment's (02: train and hold-out bases; 03: 993-994 million; 02's
# checkpoints and probes: 950 and 980 million). How many ids each stage uses is fixed later (the
# freeze), inside these ranges.
PILOT_IDS = np.arange(996_000_000, 996_100_000)
TUNING_IDS = np.arange(996_100_000, 996_200_000)
GATE_IDS = np.arange(996_200_000, 996_300_000)
HOLDOUT_04A_IDS = np.arange(996_300_000, 996_400_000)


def task_n_config(base: Config | None = None, *, sigma: float, amplitude: float, radius: float,
                  separation: float, max_separation: float = 0.0, horizon: int = 300) -> Config:
    """Task N: one swarm of one wey, the boundary wall only, no food, hazards, pheromones or
    combat, and energy off (no drain, no movement cost, no eating), so the wey lives the whole
    horizon. A sensing-only scent source moves when reached; the score counts targets reached.
    The brain keeps 02's 32 substeps and single-strain padding on (D092)."""
    c = (base or Config()).copy()
    w, m = c.world, c.map
    w.task = "navigate"
    w.n_swarms, w.weys_per_swarm, w.max_ticks = 1, 1, horizon
    w.metabolic_drain, w.move_cost, w.eat_rate, w.hazard_damage = 0.0, 0.0, 0.0, 0.0
    w.pheromone_deposit, w.sense_scale_pheromone = 0.0, 0.0
    w.food_odour_sigma, w.food_sensing, w.food_probe = 0.0, "stereo", "real"
    w.target_sigma, w.target_amplitude, w.target_radius = float(sigma), float(amplitude), float(radius)
    w.target_separation, w.target_max_separation = float(separation), float(max_separation)
    m.food_patches, m.hazard_patches, m.food_regen = (0, 0), (0, 0), 0.0
    c.brain.substeps = 32
    c.brain.pad_single_strain = True
    return c
