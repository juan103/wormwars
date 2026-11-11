"""E5-1's settings as worlds (docs/E5/E5-1-DESIGN.md §3, §9): a per-world prey and pin for a list of named settings,
one per column, and Task H played on them.

The prey are built on the interface they are given (E5-0 used the worm's, whose collision, food and motor indices a
grafted interface keeps, `graft_interface` appending the noses after them) with as many neurons as the hunter, since
the world's input current has the hunter's width.
"""

from __future__ import annotations

import numpy as np

from . import settings as ST
from .play import HuntResult, play
from .prey import MixedPrey


def prey(iface, cfg, names, params, n: int = 302, device="cpu") -> MixedPrey:
    """The prey for a list of setting names, one per world, in world order."""
    st = [ST.BY_NAME[nm] for nm in names]
    p = params
    return MixedPrey(iface, n, cfg.world.forward_gain, cfg.world.turn_gain, [s["prey"] for s in st],
                     [s["speed"] for s in st], gain=p["route"]["gain"], spacing=p["route"]["spacing"],
                     reach=p["route"]["reach"], rate=p["walk"]["rate"], persistence=p["walk"]["persistence"],
                     wall=p["wall"], device=device)


def rule_of(names) -> str:
    rules = sorted({ST.BY_NAME[nm]["rule"] for nm in names})
    if len(rules) != 1:
        raise ValueError(f"one capture rule per world: the settings mix {rules}")
    return rules[0]


def play_settings(cfg, iface, hunter, names, world_ids, run_seed, params, *, prey_iface=None, device="cpu",
                  hunter_attack: float = 1.0, prey_body: bool | None = None) -> HuntResult:
    """Every strain of `hunter` on the world ids, column k under setting `names[k]` (the same for every strain).
    `world_ids` is [columns] or [strains, columns]."""
    names = list(names)
    world_ids = np.asarray(world_ids, dtype=np.int64)
    if world_ids.shape[-1] != len(names):
        raise ValueError(f"{len(names)} settings for {world_ids.shape[-1]} columns")
    rule = rule_of(names)
    S = hunter.n_strains
    pr = prey(prey_iface or iface, cfg, names * S, params, n=hunter.n, device=device)
    return play(cfg, iface, hunter, pr, world_ids, run_seed, rule=rule, prey_energy=params["e_prey"],
                pinned=[ST.BY_NAME[nm]["pinned"] for nm in names], hunter_attack=hunter_attack, prey_body=prey_body,
                device=device)
