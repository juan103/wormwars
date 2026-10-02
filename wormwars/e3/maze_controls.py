"""E3b-0's scripted controls on the maze (docs/E3/E3b-0-PLAN.md §3a).

- `oracle`: the path oracle, the ceiling. Its waypoints are the maze-cell centres along the tree path to
  each wey's current goal; it steers at the next one (E1's oracle gain k = 2) at full speed, within the
  world's turn limit. A waypoint is passed when the head enters that cell's open block. Privileged: it
  reads the world's positions, headings, goals and mazes directly, as E1's oracle does.
- `follower`: the scripted trail follower. It senses its goal channel's bilateral reading (trail +
  scent, as the world senses them under the access mode), the wall-only collision sensors, and its goal
  through that channel; no temporal comparison. If max(L, R) ≥ 0.005 it steers by 32 (L − R) plus W1's
  reflex; otherwise it explores as W2; forward is always 1.
- `reflex_walk`: E1's tuned persistent random walk (speed 1, rate 1, persistence 0.5, seed 0) plus W1's
  reflex. `w2_alone`: W2's turn. The carrier's circle is the carrier organism itself.

The scripted reflexes are the organisms' steady states (D176): a reflex neuron's activation is
tanh(−0.5 + c) for its collision current c; W1's term is the turn its two neurons command on a carrier
with no turn bias, turn_gain · tanh(3 (r_R − r_L)); W2's turn is the whole W2 carrier's, with its resting
turn of 0.4. Every policy reads the world's own signals (`World.last_signals`) and returns world-layout
commands, which the brain hands back through the strain assignment.
"""

from __future__ import annotations

import math
from collections import deque

import numpy as np
import torch

from ..e1 import controllers as C1
from ..exp02.scripted import ScriptedBrain
from . import maze as M
from . import maze_organisms as MO

FOLLOW_K = 32.0
FOLLOW_THRESHOLD = 0.005
ORACLE_K = 2.0


def _activation(c, cfg):
    b = cfg.brain
    return torch.tanh(MO.REFLEX_BIAS + (c * b.input_gain).clamp(-b.input_max, b.input_max))


def _turn(v, cfg):
    """The world's turn read-out for dorsal state v and ventral −v: 0.5 gain (tanh v − tanh(−v))."""
    return 0.5 * cfg.world.turn_gain * (torch.tanh(v) - torch.tanh(-v))


def w1_reflex(cl, cr, cfg):
    """W1's reflex term: its turn command on a carrier with no turn bias (unclamped)."""
    return _turn(MO.REFLEX_W * (_activation(cr, cfg) - _activation(cl, cfg)), cfg)


def w2_turn(cl, cr, cfg):
    """W2's whole turn command at steady state, the carrier's bias included (unclamped)."""
    b = math.atanh(MO.carrier_turn("W2") / 2)
    return _turn(b - MO.REFLEX_W * _activation(cl, cfg) + MO.W2_RIGHT_W * _activation(cr, cfg), cfg)


class TrailFollower:
    """`symmetric_occlusion` (a diagnostic variant, D179): where exactly one nose is occluded (reading 0),
    both sides read the other nose, so occlusion alone gives no turn."""

    def __init__(self, k: float = FOLLOW_K, threshold: float = FOLLOW_THRESHOLD, symmetric_occlusion: bool = False):
        self.k, self.threshold, self.symmetric = float(k), float(threshold), bool(symmetric_occlusion)

    def __call__(self, sig, cfg):
        left, right = sig["goal_left"], sig["goal_right"]
        if self.symmetric and "_blocked" in sig:
            bl, br = sig["_blocked"][..., 0], sig["_blocked"][..., 1]
            left, right = torch.where(bl & ~br, right, left), torch.where(br & ~bl, left, right)
        cl, cr = sig["collision_front_left"], sig["collision_front_right"]
        steer = self.k * (left - right) + w1_reflex(cl, cr, cfg)
        turn = torch.where(torch.maximum(left, right) >= self.threshold, steer, w2_turn(cl, cr, cfg))
        return torch.ones_like(left), turn.clamp(-1, 1)


class ReflexWalk:
    def __init__(self, speed=1.0, rate=1.0, persistence=0.5, seed: int = 0):
        self.walk = C1.PersistentRandomWalk(speed, rate, persistence, seed=seed)
        self.state = self.walk.init(None, None)

    def __call__(self, sig, cfg):
        cl, cr = sig["collision_front_left"], sig["collision_front_right"]
        fwd, turn, self.state = self.walk(torch.zeros_like(cl), torch.zeros_like(cl), self.state)
        return fwd, (turn + w1_reflex(cl, cr, cfg)).clamp(-1, 1)


class W2Alone:
    def __call__(self, sig, cfg):
        cl, cr = sig["collision_front_left"], sig["collision_front_right"]
        return torch.ones_like(cl), w2_turn(cl, cr, cfg).clamp(-1, 1)


class WorldScripted(ScriptedBrain):
    """A scripted controller on the world's signals, in world layout [worlds, 1, weys]."""

    def __init__(self, iface, cfg, policy, n: int = 302, device="cpu"):
        super().__init__(iface, n, None, cfg.world.forward_gain, cfg.world.turn_gain, n_strains=1, device=device)
        self.cfg, self.world_policy, self.world = cfg, policy, None

    def initial_state(self, n_weys: int) -> torch.Tensor:
        return torch.zeros(self.n_strains, n_weys, self.n, device=self.device)

    def attach_world(self, world) -> None:
        self.world = world

    def _to_brain(self, x):
        return self.world.assigns[0].to_brain(x[:, 0].unsqueeze(-1))[..., 0]

    def commands(self):
        sig = self.world.last_signals
        if getattr(self.world, "last_blocked", None) is not None:
            sig = {**sig, "_blocked": self.world.last_blocked.unsqueeze(1)}  # [worlds, 1, weys, (L, R)]
        return self.world_policy(sig, self.cfg)

    def step(self, v, current):
        fwd, turn = self.commands()
        return self.command(current, self._to_brain(fwd), self._to_brain(turn))


class MazeOracle(WorldScripted):
    def __init__(self, iface, cfg, n: int = 302, device="cpu", k: float = ORACLE_K):
        super().__init__(iface, cfg, None, n=n, device=device)
        self.k = float(k)

    def attach_world(self, world) -> None:
        super().attach_world(world)
        c = int(world.cfg.world.maze_cells)
        hop = np.zeros((world.n_worlds, 2, c, c, 2), dtype=np.int64)  # the next cell toward A or B
        for w, (mz, pl) in enumerate(zip(world.mazes, world.placements)):
            nb = mz.neighbours()
            for g, goal in enumerate((pl.a, pl.b)):
                hop[w, g][goal] = goal
                seen, q = {goal}, deque([goal])
                while q:
                    u = q.popleft()
                    for v in nb[u]:
                        if v not in seen:
                            seen.add(v)
                            hop[w, g][v] = u
                            q.append(v)
        self.hop = torch.from_numpy(hop).to(world.device)
        spawn = np.array([[pl.spawns[b % len(pl.spawns)] for b in range(world.n_weys)] for pl in world.placements])
        self.cur = torch.from_numpy(spawn.astype(np.int64)).to(world.device)  # [worlds, weys, (i, j)]

    def commands(self):
        w = self.world
        head, heading = w.pos[:, 0], w.heading[:, 0]  # [worlds, weys, 2], [worlds, weys]
        ix, iy = head[..., 0].floor().long(), head[..., 1].floor().long()
        in_block = (ix % 4 != 0) & (iy % 4 != 0)
        at_cur = in_block & ((iy - 1) // 4 == self.cur[..., 0]) & ((ix - 1) // 4 == self.cur[..., 1])
        Wn, B = self.cur.shape[:2]
        wi = torch.arange(Wn, device=head.device).view(-1, 1).expand(Wn, B)
        nxt = self.hop[wi, w.goal, self.cur[..., 0], self.cur[..., 1]]
        self.cur = torch.where(at_cur.unsqueeze(-1), nxt, self.cur)
        tx = (2.5 + 4 * self.cur[..., 1]).to(head.dtype)
        ty = (2.5 + 4 * self.cur[..., 0]).to(head.dtype)
        want = torch.atan2(ty - head[..., 1], tx - head[..., 0])
        diff = torch.remainder(want - heading + math.pi, 2 * math.pi) - math.pi
        turn = (self.k * diff).clamp(-1, 1).unsqueeze(1)
        return torch.ones_like(turn), turn


def oracle(iface, cfg, n: int = 302, device="cpu") -> MazeOracle:
    return MazeOracle(iface, cfg, n=n, device=device)


def follower(iface, cfg, n: int = 302, device="cpu") -> WorldScripted:
    return WorldScripted(iface, cfg, TrailFollower(), n=n, device=device)


def reflex_walk(iface, cfg, n: int = 302, device="cpu") -> WorldScripted:
    return WorldScripted(iface, cfg, ReflexWalk(), n=n, device=device)


def w2_alone(iface, cfg, n: int = 302, device="cpu") -> WorldScripted:
    return WorldScripted(iface, cfg, W2Alone(), n=n, device=device)
