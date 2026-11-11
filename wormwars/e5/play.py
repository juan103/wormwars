"""Batched episodes of Task H: every hunter strain on every world id, against one scripted prey per world.

Hunters are strains (a neural `Brain`, or a scripted brain with [strains, 1] parameters); the worlds are tiled once per
strain, as `wormwars.evo.rollout` does, so every strain meets the same worlds and, with scripted prey, the same prey
until its own contact changes them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from ..accounting import LEDGER  # noqa: F401  (the world counts its own ticks and updates)
from .hunt import HuntWorld


@dataclass
class HuntResult:
    captures: np.ndarray  # [strains, worlds]
    events: dict  # each [strains, worlds, sequence index]
    bite_energy: np.ndarray  # the hunter's energy gained from bites, [strains, worlds] (logged, never scored)
    pin_push: np.ndarray  # [strains, worlds]
    prey_wall_limited: np.ndarray  # [strains, worlds]
    ledger_rel_error: float
    ticks: int
    max_index: int = -1  # E5-1: the highest sequence index any world reached (its live prey's)


def play(cfg, iface, hunter, prey, world_ids, run_seed, *, rule: str, prey_energy: float = 12.0, pinned=True,
         hunter_attack: float = 1.0, prey_body: bool | None = None, device="cpu", setup=None) -> HuntResult:
    """`setup(world)`, if given, runs after the world is built and before the first tick (calibration's placements).

    E5-1: `world_ids` is [worlds], shared by every strain, or [strains, worlds], each strain its own (as
    `wormwars.evo.rollout`); `pinned` is one flag or one per column, the same for every strain. The prey brain's rows
    are the worlds in strain-major order, so a per-world prey is built for the tiled columns."""
    world_ids = np.asarray(world_ids, dtype=np.int64)
    S, n_ids = hunter.n_strains, world_ids.shape[-1]
    if world_ids.ndim == 2:
        if world_ids.shape[0] != S:
            raise ValueError(f"{world_ids.shape[0]} rows of world ids for {S} strains")
        ids = world_ids.reshape(-1)
    else:
        ids = np.tile(world_ids, S)
    if np.ndim(pinned):
        if len(pinned) != n_ids:
            raise ValueError(f"{len(pinned)} pin flags for {n_ids} columns")
        pinned = np.tile(np.asarray(pinned, dtype=bool), S)
    strain_of = torch.zeros(S * n_ids, 2, dtype=torch.long, device=device)
    strain_of[:, 0] = torch.arange(S, device=device).repeat_interleave(n_ids)
    w = HuntWorld(cfg, iface, [hunter, prey], strain_of, run_seed=run_seed, world_ids=ids,
                  device=device, rule=rule, prey_energy=prey_energy, pinned=pinned, hunter_attack=hunter_attack,
                  prey_body=prey_body)
    if setup is not None:
        setup(w)
    w.run()
    # E5-1, §6: a non-finite state stops the caller. Captures are integers, so nothing downstream would show it
    states = [w.pos, w.heading, w.energy, *[v for v in w.v if torch.is_tensor(v)]]
    if not all(bool(torch.isfinite(t).all()) for t in states):
        raise FloatingPointError("a non-finite state (positions, headings, energies or brain states) in Task H")
    shape = (S, n_ids)
    ev = {k: v.reshape(S, n_ids, *v.shape[1:]) for k, v in w.hunt_events().items()}
    rel = (w.ledger_rel_max if w.ledger_rel_max is not None else w.energy_ledger_rel_error()).max().item()
    return HuntResult(captures=w.captures.reshape(shape).cpu().numpy(), events=ev,
                      bite_energy=w.energy_from_biting[:, 0].reshape(shape).cpu().numpy(),
                      pin_push=w.pin_push.reshape(shape).cpu().numpy(),
                      prey_wall_limited=w.prey_wall_limited.reshape(shape).cpu().numpy(), ledger_rel_error=float(rel),
                      ticks=w.tick_count, max_index=int(w.life.max()))
