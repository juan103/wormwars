"""E3c's arms (docs/E3/E3c-DESIGN.md v2.1 §3-§4).

Every trained arm has E's 11 grafted neurons in the same interface positions, plus W2's two frozen neurons and the
carrier at W2's resting turn (`maze_organisms.maze_organism`).

- **S-dense:** B-task's full mask (all 121 edges among the 11, plus the 32 output edges), drawn by
  `samplers.b_task_draw` and put on the carrier with W2. It has 171 mutable scalars.
- **S-mod:** the same full draw, projected onto E's mask: E's edges take the draw's values by name, and every other
  drawn edge is dropped. The 11 neurons' τ and biases come from the draw. It has E's 65 mutable scalars.
- **P-sel:** the seed E + W2 with its 13 selector parameters drawn by `samplers.ga_draw` (E3a Stage 2's start),
  the modules frozen. It has 13 mutable scalars.

Each arm's mutation factor is 1.0. The relays' τ and bias, W2, the worm block and the gap junctions stay frozen.
"""

from __future__ import annotations

import numpy as np

from .. import graft as G
from ..brain import Genome
from . import maze_organisms as MO
from . import samplers as SA
from . import tuning as T

TRAINED = ("s_mod", "s_dense", "p_sel")
FACTOR = 1.0


def context(con, l1, bcfg) -> dict:
    """The seed E + W2, and B-task's module grafted alone (the draw's own layout) and with W2 (S-dense's)."""
    seed = T.start_organism("seed", con, l1, bcfg)
    module = SA.b_task_module(l1)
    bt_ext = G.graft_connectome(con, module)
    one = SA.b_task_draw(np.random.default_rng(0), bt_ext, module, bcfg, 1)
    dense = MO.maze_organism(con, MO.Seed("e3c-dense", module, bt_ext, one), "W2", bcfg)
    return {"con": con, "bcfg": bcfg, "seed": seed, "bt_module": module, "bt_ext": bt_ext, "dense": dense}


def arm_ext(arm: str, cx):
    return cx["dense"].ext if arm == "s_dense" else cx["seed"].ext


def arm_scales(arm: str, cx) -> dict:
    if arm == "p_sel":
        return SA.stage2_scales(cx["seed"].ext)
    if arm in ("s_mod", "s_dense"):
        return T.scales(arm_ext(arm, cx), factor=FACTOR)
    raise ValueError(f"no mutation mask for {arm}")


def _neurons(genome: Genome, ext, strain: int) -> dict:
    return {n: (float(genome.tau[strain, ext.index(n)]), float(genome.bias[strain, ext.index(n)])) for n in SA.NEURONS}


def draw(arm: str, cx, rng: np.random.Generator, n: int) -> Genome:
    """n independent starting genomes of an arm (§4), reproducible from `rng`."""
    if arm == "p_sel":
        return SA.with_selector(cx["seed"].genome, cx["seed"].ext, SA.ga_draw(rng, n))
    raw = SA.b_task_draw(rng, cx["bt_ext"], cx["bt_module"], cx["bcfg"], n)
    parts = []
    for s in range(n):
        edges = MO.named_edges(raw, cx["bt_ext"], strain=s)
        if arm == "s_dense":
            target, ext = cx["dense"].genome, cx["dense"].ext
        elif arm == "s_mod":
            target, ext = cx["seed"].genome, cx["seed"].ext
            mask = MO.named_edges(target, ext)
            edges = {k: v for k, v in edges.items() if k in mask}  # E's mask: the draw's values; the rest dropped
        else:
            raise ValueError(f"no draw for {arm}")
        parts.append(MO._set_grafted(target.select([0]), ext, edges, _neurons(raw, cx["bt_ext"], s)))
    return Genome.cat(parts)
