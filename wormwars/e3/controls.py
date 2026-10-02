"""E3a's scripted controls on the shuttle (experiments/E3-ab-organism/E3a/PREREGISTRATION.md §4).

- `oracle`: E1's oracle (k 2, speed 1), steering at the current goal (`World.current_target`).
- `s_shuttle`: E1's S-const reading the current goal's bilateral scent (`goal_left`, `goal_right`):
  a perfect scripted memory, privileged as the oracle is.
- `blind`: constant motion, the persistent random walk (E1's tuned settings) and the carrier's circle
  is built from the carrier itself.

The interface must route `goal_left` and `goal_right` (L1-switch's graft does).
"""

from __future__ import annotations

from ..e1 import controllers as C1
from ..exp02.scripted import ScriptedBrain


class GoalScriptedBrain(ScriptedBrain):
    """A scripted policy whose (left, right) inputs are the goal's scent, not food."""

    def __init__(self, iface, n, policy, forward_gain, turn_gain, n_strains=1, device="cpu"):
        super().__init__(iface, n, policy, forward_gain, turn_gain, n_strains=n_strains, device=device)
        names = list(iface.signal_names)
        self.left = int(iface.sensor_neuron[names.index("goal_left")])
        self.right = int(iface.sensor_neuron[names.index("goal_right")])


def oracle(iface, cfg, n: int, device="cpu"):
    return C1.OracleBrain(iface, n, cfg.world.forward_gain, cfg.world.turn_gain, k=2.0, speed=1.0, device=device)


def s_shuttle(iface, cfg, n: int, *, k: float, speed: float, turn: float, device="cpu") -> GoalScriptedBrain:
    return GoalScriptedBrain(iface, n, C1.s_const(k, speed, turn), cfg.world.forward_gain, cfg.world.turn_gain,
                             device=device)


def constant(iface, cfg, n: int, device="cpu"):
    return C1.scripted(iface, C1.ConstantMotion(0.8, 0.1), cfg, device=device, n=n)


def random_walk(iface, cfg, n: int, device="cpu"):
    return C1.scripted(iface, C1.PersistentRandomWalk(1.0, 1.0, 0.5, seed=0), cfg, device=device, n=n)
