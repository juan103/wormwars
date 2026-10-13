"""Champion lineages for E4's scale rule (docs/E4/E4-DESIGN.md v3 §1): "a simulated champion lineage with the pilot's
recorded mutation count, not G, since `breed` copies elites unmutated".

`evolve_batch` keeps no parents. `Capture` wraps its `rollout_fn` and keeps every selection call's results (the
calls with one row of world ids per strain); `replay` then runs `breed` again with each run's own generator, which
draws the parents first, and so recovers each generation's parents exactly. A test checks that the replayed final
populations equal `evolve_batch`'s, bitwise. The replay runs on the device the run used.
"""

from __future__ import annotations

import copy

import numpy as np
import torch

from ..e04a import evolve as EV
from ..evo.evolve import breed, ranking


class Capture:
    """A `rollout_fn` that passes every call through and keeps the selection calls' score and progress."""

    def __init__(self, inner):
        self.inner = inner
        self.selections = []

    def __call__(self, cfg, iface, genome, world_ids, run_seed, device="cpu", **kw):
        res = self.inner(cfg, iface, genome, world_ids, run_seed, device, **kw)
        if np.asarray(world_ids).ndim == 2:
            sel = {"score": np.array(res.score, copy=True), "progress": np.array(res.progress, copy=True)}
            for k in ("real_first", "decoy_first", "neither"):  # the evolutionary E4-D's trial counts, when present
                if hasattr(res, k):
                    sel[k] = np.array(getattr(res, k), copy=True)
            self.selections.append(sel)
        return res


def replay(cfg, runs, selections, *, initial, mutation_scales=None, device="cpu", random_ties: bool = False) -> list:
    """Per run: `parents` (one entry per breeding, `source` and `child` per strain of the next generation) and the
    replayed `final` population."""
    P, e = cfg.evo.population, cfg.evo
    out = []
    for i, r in enumerate(runs):
        pop = EV.moved(initial(r), device)
        sc = None if mutation_scales is None else mutation_scales(r)
        gen = torch.Generator(device=device).manual_seed(EV.breed_seed(r.run_seed))
        ties = EV.tie_rng(r.run_seed) if random_ties else None
        parents = []
        for g, sel in enumerate(selections):
            fit = EV.fitness(sel["score"][i * P:(i + 1) * P], sel["progress"][i * P:(i + 1) * P], r.shaping)
            if g == len(selections) - 1:
                break
            order = ranking(fit, copy.deepcopy(ties))  # the same draws `breed` takes next
            elites, pool = order[:e.elites], order[:min(e.truncation, len(order))]
            peek = torch.Generator(device=device)
            peek.set_state(gen.get_state())
            pick = pool[torch.randint(len(pool), (P - len(elites),), generator=peek, device=device).cpu().numpy()]
            pop = breed(pop, fit, cfg, gen, sc, ties)
            parents.append({"source": [int(x) for x in np.concatenate([elites, pick])],
                            "child": [False] * len(elites) + [True] * len(pick)})
        out.append({"run": r.run, "parents": parents, "final": EV.moved(pop, "cpu")})
    return out


def mutations(parents: list, strain: int) -> int:
    """The mutations along `strain`'s lineage, from the last generation back to the first."""
    n, k = 0, int(strain)
    for p in reversed(parents):
        n += bool(p["child"][k])
        k = p["source"][k]
    return n
