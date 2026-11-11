"""E5-1's fixed numbers (docs/E5/E5-1-DESIGN.md §3, §4, §6, §7): the world-generation seed, the world-id blocks, the
run seeds, the GA, the graphs by name, and the admission order. Nothing here is read from data.
"""

from __future__ import annotations

import numpy as np

from . import settings as ST

WORLD_SEED = 1_520_001  # one world-generation seed for every E5-1 world, formal and pilot (§3)
GENERATIONS = 500  # generations 0 .. 499
CHECKPOINT_EVERY = 25
RUNS_PER_BATCH = 4  # one composition for every arm: 128 strains x 8 worlds
VALIDATION_PER_SLOT = 32  # 256 validation worlds
SUITE_WORLDS = 512  # per suite setting
GA = {"population": 32, "elites": 3, "truncation": 8, "worlds_per_strain": 8, "islands": 1,
      "mutation": {"w_sigma": 0.08, "g_sigma": 0.04, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}}
MODULE_FACTOR = 0.25  # the module's mutation at 0.25x 02's scales, the host's at 1x (E4s-1's M arm)
GAINS = {"forward": 4.0, "turn": 2.0}  # Task N's and Task H's, for every graph (§4)
DELTA = 0.25  # captures per episode on the suite score (§5)

# ------------------------------------------------------------------------------------------------- world ids (§3)
BLOCKS = {  # (first id, count); a training block's count is its span
    "formal_training": (985_000_000, 500_000),
    "formal_validation": (985_600_000, len(ST.TRAINING) * VALIDATION_PER_SLOT),
    "suite": (985_700_000, len(ST.SUITE) * SUITE_WORLDS),  # probes and lesions reuse the suite's ids of their settings
    "bridges": (985_720_000, 2 * SUITE_WORLDS),  # H1-ghost 512, then H1-reach 512
    "o0": (985_730_000, 64),  # 8 per training setting
    "mutational": (985_740_000, 256),  # 32 per training setting
    "selection_signal": (985_760_000, 256),  # 32 per training setting
    "cuda_sd": (985_790_000, 1024),
    "cuda_checks": (985_800_000, 40_960),
    "pilot_training": (986_000_000, 100_000),
    "pilot_validation": (986_200_000, len(ST.TRAINING) * VALIDATION_PER_SLOT),
}


def ids(block: str) -> np.ndarray:
    first, n = BLOCKS[block]
    if block.endswith("_training"):
        raise ValueError(f"{block} is a span drawn from by each run's schedule (evolve_batch's train_ids)")
    return np.arange(first, first + n, dtype=np.int64)


def suite_ids(setting: str) -> np.ndarray:
    """985 700 000 + 512 k + i, setting k in §3's order."""
    k = ST.SUITE.index(setting)
    first = BLOCKS["suite"][0] + SUITE_WORLDS * k
    return np.arange(first, first + SUITE_WORLDS, dtype=np.int64)


def bridge_ids(setting: str) -> np.ndarray:
    k = ST.BRIDGES.index(setting)
    first = BLOCKS["bridges"][0] + SUITE_WORLDS * k
    return np.arange(first, first + SUITE_WORLDS, dtype=np.int64)


def per_slot_layout(n_per_slot: int) -> tuple[str, ...]:
    """A block played per training setting, slot-major: the first `n_per_slot` ids under slot 0's setting, and so on."""
    return tuple(ST.TRAINING[k] for k in np.repeat(np.arange(len(ST.TRAINING)), n_per_slot))


# ------------------------------------------------------------------------------------------------- graphs (§4)
SH_ROUTE = tuple(f"SH-route-{1_020_000 + j}" for j in range(20))  # S0 .. S19
SH_ROUTE_CUT = SH_ROUTE[:16]  # §7's cut (4)
SH_ROUTE_PILOT = tuple(f"SH-route-{1_020_020 + j}" for j in range(4))
SH_ROUTE_PILOT_EVOLVED = SH_ROUTE_PILOT[:2]
P_PERMUTATION_SEEDS = (4, 5, 6)  # 02's N2perm4 to N2perm6

# ------------------------------------------------------------------------------------------------- seeds (§4)
SEED_BASE = {"G-N2": 1_510_000, "G-SHr": 1_511_000, "A0": 1_512_000, "P": 1_513_000,
             "pilot_null": 1_518_000, "pilot_n2": 1_519_000,
             "check": 1_517_000,  # E5-1a's checks and bench: generation-0 genomes that are never a reading
             "sensitivity": 1_517_500}  # E5-1a's mutational-sensitivity mutation streams
N2_RUNS, SHR_RUNS_PER_GRAPH, A0_RUNS, P_RUNS_PER_DRAW, B_RUNS = 32, 4, 8, 4, 16


def run_seed(arm: str, run: int, graph: int | None = None) -> int:
    """G-N2 run i: 1 510 000 + i; B and A0r run i: G-N2 run i's; G-SHr graph j run r: 1 511 000 + 4j + r; A0 run i:
    1 512 000 + i; P draw k run r: 1 513 000 + 4k + r; the pilot's null graph j run r: 1 518 000 + 4j + r; the pilot's
    N2 populations: 1 519 000 + i."""
    run = int(run)
    if arm in ("G-N2", "B", "A0r"):
        return SEED_BASE["G-N2"] + run
    if arm == "A0":
        return SEED_BASE["A0"] + run
    if arm == "pilot_n2":
        return SEED_BASE["pilot_n2"] + run
    if arm in ("G-SHr", "P", "pilot_null"):
        if graph is None or not 0 <= run < 4:
            raise ValueError(f"{arm} needs a graph (or draw) index and a run in 0..3")
        return SEED_BASE[arm] + 4 * int(graph) + run
    raise ValueError(f"unknown arm {arm!r}")


# ------------------------------------------------------------------------------------------------- admission (§6)
ADMISSION = ("N1", "S0", "S1", "S2", "N2", "S3", "S4", "N3", "S5", "S6", "S7", "N4", "S8", "S9", "N5", "S10", "S11",
             "S12", "N6", "S13", "S14", "N7", "S15", "S16", "S17", "N8", "S18", "S19")


def batch_units(unit: str) -> dict:
    """A test batch: N_k holds G-N2 runs 4k - 4 .. 4k - 1; S_j is SH-route graph j's 4 runs."""
    if unit.startswith("N"):
        k = int(unit[1:])
        return {"arm": "G-N2", "graph": "N2", "runs": list(range(4 * k - 4, 4 * k)),
                "seeds": [run_seed("G-N2", r) for r in range(4 * k - 4, 4 * k)]}
    j = int(unit[1:])
    return {"arm": "G-SHr", "graph": SH_ROUTE[j], "runs": [4 * j + r for r in range(4)],
            "seeds": [run_seed("G-SHr", r, j) for r in range(4)]}
