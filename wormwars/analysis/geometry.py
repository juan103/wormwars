"""Scripted two-wey duels, for measuring the combat geometry.

The flank rule is a hypothesis about the geometry, not something the code gets for free. These
helpers place two weys in an exact relative pose, run one combat step with the brains bypassed, and
report the damage each one dealt and took. Blur radius, body length, attack offset and cell size are
then tuned against the measurement.

Poses (A is always the one with the advantage, except head-on where there is none):

    head_on     A -->   <-- B        both bite each other's front
    t_bone      A -->     B|         A bites B's flank; B's bite points across
    rear        A -->   B -->        A bites B's tail; B's bite points away
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import torch

from ..brain import Brain, BrainSpec, Genome
from ..config import Config
from ..connectome.loader import Connectome
from ..interface import load_interface
from ..world import World

POSES = ("head_on", "t_bone", "rear")


@dataclass
class DuelResult:
    pose: str
    gap: float
    damage_to_a: float
    damage_to_b: float

    @property
    def payback_ratio(self) -> float:
        """What the disadvantaged wey (B... except head-on) deals back per unit it takes.

        For `t_bone` and `rear`, A is the attacker and B is the victim, so this is
        damage_to_a / damage_to_b: how much the flanked wey gives back.
        """
        if self.damage_to_b <= 0:
            return float("inf") if self.damage_to_a > 0 else 0.0
        return self.damage_to_a / self.damage_to_b

    def __str__(self) -> str:
        return (
            f"{self.pose:<8} gap {self.gap:4.2f}  A takes {self.damage_to_a:7.4f}  "
            f"B takes {self.damage_to_b:7.4f}  payback {self.payback_ratio:6.3f}"
        )


def place(pose: str, gap: float, centre: float, body_length: float):
    """Positions and headings of A and B for one pose. Returns ((xa, ya, ta), (xb, yb, tb))."""
    if pose == "head_on":
        a = (centre, centre, 0.0)
        b = (centre + gap, centre, math.pi)
    elif pose == "t_bone":
        # B's middle sits `gap` ahead of A's head, B lying across A's line of attack
        b_mid_x, b_mid_y = centre + gap, centre
        half = body_length * 0.5
        b = (b_mid_x, b_mid_y + half, math.pi / 2)
        a = (centre, centre, 0.0)
    elif pose == "rear":
        # B directly ahead of A, facing the same way, so A meets B's tail
        a = (centre, centre, 0.0)
        b = (centre + gap + body_length, centre, 0.0)
    else:
        raise ValueError(f"unknown pose {pose!r}; expected one of {POSES}")
    return a, b


def duel(
    con: Connectome,
    cfg: Config | None = None,
    pose: str = "head_on",
    gap: float = 1.0,
    combat_stage: int = 1,
    pump: float = 1.0,
    device: str = "cpu",
    phase: tuple[float, float] = (0.0, 0.0),
) -> DuelResult:
    """One combat step between two weys in a scripted pose, brains bypassed."""
    cfg = cfg or Config()
    cfg = Config(**cfg.to_dict()) if not isinstance(cfg, Config) else cfg
    wcfg = cfg.world
    saved_swarms, saved_weys = wcfg.n_swarms, wcfg.weys_per_swarm
    wcfg.n_swarms, wcfg.weys_per_swarm = 2, 1
    try:
        iface = load_interface(con)
        spec = BrainSpec.from_connectome(con, device=device)
        genome = Genome.random(
            spec, cfg.brain, 1, generator=torch.Generator().manual_seed(0), device=device
        )
        world = World(
            cfg, iface, Brain(genome), torch.zeros(1, 2, dtype=torch.long),
            run_seed=0, device=device, combat_stage=combat_stage,
        )
        world.fields.zero_()
        a, b = place(pose, gap, world.side / 2, wcfg.body_length)
        # `phase` shifts BOTH weys by the same sub-cell amount. The relative geometry is untouched;
        # only where the pair sits inside the cell lattice changes. Averaging over phase is the
        # honest measurement, because weys move continuously and never sit on lattice points.
        px, py = phase
        world.pos[0, 0, 0] = torch.tensor([a[0] + px, a[1] + py])
        world.pos[0, 1, 0] = torch.tensor([b[0] + px, b[1] + py])
        world.heading[0, 0, 0] = a[2]
        world.heading[0, 1, 0] = b[2]
        world.energy.fill_(1e6)  # so nothing is capped by a near-empty victim
        world.pump.fill_(pump)
        world._points = None
        world._update_body_field()
        world._combat()
        return DuelResult(
            pose=pose,
            gap=gap,
            damage_to_a=float(world.last_damage_taken[0, 0, 0]),
            damage_to_b=float(world.last_damage_taken[0, 1, 0]),
        )
    finally:
        wcfg.n_swarms, wcfg.weys_per_swarm = saved_swarms, saved_weys


def phases(n: int = 4):
    """A grid of sub-cell offsets covering one cell."""
    step = 1.0 / n
    return [(i * step, j * step) for i in range(n) for j in range(n)]


def duel_mean(con, cfg=None, pose="head_on", gap=1.0, n_phase=4, **kw) -> DuelResult:
    """A duel averaged over sub-cell lattice phase -- what the pose costs on average in play."""
    rs = [duel(con, cfg, pose=pose, gap=gap, phase=p, **kw) for p in phases(n_phase)]
    return DuelResult(
        pose=pose,
        gap=gap,
        damage_to_a=sum(r.damage_to_a for r in rs) / len(rs),
        damage_to_b=sum(r.damage_to_b for r in rs) / len(rs),
    )


def sweep(con: Connectome, cfg: Config | None = None, gaps=(0.5, 0.8, 1.1, 1.4, 1.7), n_phase=4):
    """Every pose at every gap, averaged over sub-cell phase. The flank-rule tuning table."""
    return {
        pose: [duel_mean(con, cfg, pose=pose, gap=g, n_phase=n_phase) for g in gaps]
        for pose in POSES
    }


def engaged(results: dict[str, list[DuelResult]], pose: str, frac: float = 0.5):
    """Only the gaps where a fight is actually happening.

    At long gaps nobody reaches anybody, and a ratio computed there measures lattice noise rather
    than geometry. "Engaged" means the victim is taking at least `frac` of the most damage seen at
    any gap for that pose.
    """
    rows = results[pose]
    peak = max((max(r.damage_to_a, r.damage_to_b) for r in rows), default=0.0)
    return [r for r in rows if max(r.damage_to_a, r.damage_to_b) >= frac * peak and peak > 0]


def worst_payback(results: dict[str, list[DuelResult]], pose: str, frac: float = 0.5) -> float:
    """The most the flanked wey ever gives back, per unit taken, at engagement range."""
    vals = [r.payback_ratio for r in engaged(results, pose, frac) if r.damage_to_b > 1e-9]
    return max(vals) if vals else float("nan")


def head_on_asymmetry(results: dict[str, list[DuelResult]], frac: float = 0.5) -> float:
    """How lopsided head-on fights are at engagement range. 1.0 is a perfectly even trade."""
    worst = 0.0
    for r in engaged(results, "head_on", frac):
        lo, hi = sorted((r.damage_to_a, r.damage_to_b))
        worst = max(worst, hi / max(lo, 1e-12))
    return worst
