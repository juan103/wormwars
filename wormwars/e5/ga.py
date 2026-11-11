"""E5-1's rollout for the GA on Task H (docs/E5/E5-1-DESIGN.md §3, §6, §9), `evolve_batch`'s `rollout_fn`.

Each strain is the hunter (swarm 0) and a scripted prey is swarm 1 in every world. Column k of the world ids is played
under a setting fixed by the column count: 8 columns are the training slots in order; the validation's columns are
`validation_per_slot` per slot, slot-major (32 in the formal run, 256 columns). The whole call is one world (evolve_batch
passes its whole batch as one chunk), so the composition is the batch's.

On every rollout:
- **the target sequence's overflow** (`HuntWorld._capture` clamps silently; `hunt_events` raises) stops the batch as
  `SequenceOverflow`, a design error (§6), and the highest sequence index reached is kept (`max_index`);
- **the ledger:** its residual, relative to each world's starting energy, must be finite and at most `ledger_tol`
  (T0's 1e-5), or `LedgerError` stops the batch.

Returns `RolloutResult` with the raw captures as `score` and zero `progress` (Task H has no shaping).
"""

from __future__ import annotations

import math

import numpy as np

from ..brain import Brain
from ..evo.rollout import RolloutResult
from . import mixed as MX
from . import settings as ST
from .prey import PursuitBrain

LEDGER_TOL = 1e-5


class SequenceOverflow(RuntimeError):
    """A world used every centre of its target sequence: a design error (§6), not a unit's failure."""


class LedgerError(FloatingPointError):
    """The energy ledger's residual is non-finite or above its tolerance."""


def pursuit_hunter(iface, cfg, n_strains: int = 1, k: float = 2.0, speed: float = 1.0):
    """E5-0's privileged pursuit hunter (one strain only), for checks that need captures."""
    if n_strains != 1:
        raise ValueError("the pursuit hunter is one strain")
    return PursuitBrain(iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, k=k, speed=speed)


def validation_layout(per_slot: int) -> tuple[str, ...]:
    return tuple(ST.TRAINING[k] for k in np.repeat(np.arange(len(ST.TRAINING)), per_slot))


class TaskHRollout:
    def __init__(self, params: dict, *, prey_iface, validation_per_slot: int = 32, ledger_tol: float = LEDGER_TOL,
                 make_hunter=None):
        self.params, self.prey_iface, self.ledger_tol = params, prey_iface, float(ledger_tol)
        self.layouts = {len(ST.TRAINING): tuple(ST.TRAINING)}
        val = validation_layout(int(validation_per_slot))
        if len(val) in self.layouts:
            raise ValueError("the validation and training shapes must differ in their column counts")
        self.layouts[len(val)] = val
        self.make_hunter = make_hunter or Brain
        self.max_index = -1
        self.rollouts = 0

    def weights(self) -> tuple[np.ndarray, np.ndarray]:
        """`evolve_batch`'s weights: the training slots', and the validation columns' (per slot, the slot's)."""
        n_val = max(self.layouts)
        val_slots = np.array([ST.TRAINING.index(nm) for nm in self.layouts[n_val]])
        return np.asarray(ST.TRAINING_WEIGHTS, dtype=np.int64), ST.column_weights(val_slots)

    def __call__(self, cfg, iface, genome, world_ids, world_seed, device, chunk_worlds=None, **_):
        ids = np.asarray(world_ids, dtype=np.int64)
        cols = ids.shape[-1]
        if cols not in self.layouts:
            raise ValueError(f"{cols} columns: Task H's rollout plays {sorted(self.layouts)} (training, validation)")
        S = genome.n_strains
        if chunk_worlds is not None and chunk_worlds < S * cols:
            raise ValueError("Task H's GA rollout plays the whole batch in one world")
        try:
            r = MX.play_settings(cfg, iface, self.make_hunter(genome), list(self.layouts[cols]), ids, world_seed,
                                 self.params, prey_iface=self.prey_iface, device=device)
        except RuntimeError as e:
            if "every centre of its sequence" in str(e):
                raise SequenceOverflow(str(e)) from e
            raise
        self.rollouts += 1
        self.max_index = max(self.max_index, r.max_index)
        rel = float(r.ledger_rel_error)
        if not math.isfinite(rel) or rel > self.ledger_tol:
            raise LedgerError(f"the ledger's residual is {rel} (tolerance {self.ledger_tol})")
        score = r.captures.astype(np.float64)
        z = np.zeros_like(score)
        return RolloutResult(score=score, energy=z, alive=z, eaten=z, ticks=r.ticks, ledger_error=rel,
                             ledger_rel_error=rel, progress=z)
