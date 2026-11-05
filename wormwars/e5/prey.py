"""Task H's scripted prey and the privileged pursuit hunter (docs/E5/E5-0-PLAN.md §3, §5).

The prey are privileged scripted brains: like E1's oracle they read the world directly (`attach_world`), and they
command the read-out neurons through `ScriptedBrain.command`, so the world's own read-out moves them. One strain;
their rows are the worlds, in world order. A prey's state for a new life is reset by `reset_worlds`, which the world
calls at each capture.

- `stationary`: forward and turn 0;
- `route`: a closed loop through 4 waypoints (the life's start, then 3 drawn per world id and life from the route's
  own stream, inside the wall clearance, each at least `spacing` from the previous and the last at least `spacing`
  from the start, closing the loop), visited in order from waypoint 1 and steered at with turn = clamp(gain x heading
  error, +-1) at forward command `speed`; a waypoint is reached within `reach`; a lap ends on returning to the start;
- `random_walk`: forward `speed`, turn = rate x u, u_t = p u_(t-1) + sqrt(1 - p^2) e_t, with e_t a normal draw keyed
  to (run seed, world id, tick), so every hunter meets the same path until contact changes it; u restarts at 0;
- `wall_follower`: E1's wall-follower on the prey's own collision inputs, which include the hunter's body (so it is
  weakly reactive).
"""

from __future__ import annotations

import math

import numpy as np
import torch

from ..e1.controllers import OracleBrain, WallFollower
from ..exp02.scripted import ScriptedBrain
from ..world import world_seed

KINDS = ("stationary", "route", "random_walk", "wall_follower")
_ROUTE_STREAM = 0x5E7B
_WALK_STREAMS = (0x5E7C, 0x5E7D)  # the walk's two keyed uniforms (Box-Muller)
PREY, HUNTER = 1, 0


class PreyBrain(ScriptedBrain):
    def __init__(self, iface, n, forward_gain, turn_gain, kind: str, *, speed: float = 0.0, gain: float = 2.0,
                 spacing: float = 6.0, reach: float = 1.0, rate: float = 0.4, persistence: float = 0.9,
                 wall: dict | None = None, device="cpu"):
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        super().__init__(iface, n, None, forward_gain, turn_gain, n_strains=1, device=device)
        self.kind, self.speed, self.gain, self.spacing, self.reach = kind, float(speed), float(gain), float(spacing), float(reach)
        self.rate, self.persistence = float(rate), float(persistence)
        self.wall = WallFollower(speed=float(speed), **(wall or {})) if kind == "wall_follower" else None
        self.world = None

    def attach_world(self, world) -> None:
        self.world = world
        Wn = world.n_worlds
        self.u = torch.zeros(Wn, device=world.device, dtype=world.dtype)
        if self.kind == "route":
            self.waypoints = torch.zeros(Wn, 4, 2, device=world.device, dtype=world.dtype)
            self.wp = torch.zeros(Wn, dtype=torch.long, device=world.device)
            self.laps_done = torch.zeros(Wn, dtype=torch.long, device=world.device)
            self.visits = torch.zeros(Wn, dtype=torch.long, device=world.device)  # waypoints reached this life
            self.seen = torch.zeros(Wn, 4, dtype=torch.bool, device=world.device)  # which waypoints were reached
            self._route_for(torch.ones(Wn, dtype=torch.bool, device=world.device))

    def initial_state(self, n_weys: int) -> torch.Tensor:
        return torch.zeros(1, n_weys, self.n, device=self.device)

    def _route_for(self, worlds: torch.Tensor) -> None:
        """Draw the current life's route for the given worlds, from the route's own stream."""
        w = self.world
        wcfg = w.cfg.world
        lo, hi = 1.0 + wcfg.target_wall_clearance, w.side - 1.0 - wcfg.target_wall_clearance
        start = w.target_centres[torch.arange(w.n_worlds, device=w.device), w.life].cpu().numpy().astype(np.float64)
        life = w.life.cpu().numpy()
        for i in np.flatnonzero(worlds.cpu().numpy()):
            rng = np.random.default_rng([world_seed(w.run_seed, int(w.world_ids[i])), _ROUTE_STREAM, int(life[i])])
            pts, prev = [start[i]], start[i]
            for k in range(3):
                for _try in range(10_000):
                    c = rng.uniform(lo, hi, 2)
                    if float(np.hypot(*(c - prev))) >= self.spacing and (
                            k < 2 or float(np.hypot(*(c - start[i]))) >= self.spacing):
                        break
                else:
                    raise ValueError(f"no waypoint satisfies the spacing (world {w.world_ids[i]})")
                pts.append(c)
                prev = c
            self.waypoints[i] = torch.as_tensor(np.array(pts), dtype=w.dtype, device=w.device)
            self.wp[i] = 1
            self.laps_done[i] = 0
            self.visits[i] = 0
            self.seen[i] = False

    def reset_worlds(self, v, caught, world):
        self.u = torch.where(caught, torch.zeros_like(self.u), self.u)
        if self.kind == "route":
            self._route_for(caught)
        return v

    def _normal(self) -> torch.Tensor:
        w = self.world
        u1 = w._keyed_uniform(_WALK_STREAMS[0])[:, PREY, 0, 0].double()
        u2 = w._keyed_uniform(_WALK_STREAMS[1])[:, PREY, 0, 0].double()
        return (torch.sqrt(-2.0 * torch.log1p(-u1)) * torch.cos(2 * math.pi * u2)).to(w.dtype)

    def step(self, v, current):
        w = self.world
        Wn = w.n_worlds
        zero = torch.zeros(Wn, device=w.device, dtype=w.dtype)
        if self.kind == "stationary":
            fwd, turn = zero, zero
        elif self.kind == "route":
            ar = torch.arange(Wn, device=w.device)
            pos, heading = w.pos[:, PREY, 0], w.heading[:, PREY, 0]
            at = (pos - self.waypoints[ar, self.wp]).norm(dim=-1) <= self.reach
            self.laps_done += (at & (self.wp == 0)).long()
            self.visits += at.long()
            self.seen[ar[at], self.wp[at]] = True
            self.wp = torch.where(at, (self.wp + 1) % 4, self.wp)
            c = self.waypoints[ar, self.wp]
            want = torch.atan2(c[:, 1] - pos[:, 1], c[:, 0] - pos[:, 0])
            err = torch.remainder(want - heading + math.pi, 2 * math.pi) - math.pi
            turn = (self.gain * err).clamp(-1, 1)
            fwd = zero + self.speed
        elif self.kind == "random_walk":
            p = self.persistence
            self.u = p * self.u + math.sqrt(1 - p * p) * self._normal()
            turn = (self.rate * self.u).clamp(-1, 1)
            fwd = zero + self.speed
        else:
            col = {k: current[..., i].view(-1) for k, i in self.collision.items()}
            one = torch.ones(Wn, device=w.device, dtype=w.dtype)
            fwd, turn, _ = self.wall(one, one, None, collision=col)
        return self.command(current, fwd.view(1, -1), turn.view(1, -1))


class PursuitBrain(OracleBrain):
    """The privileged pursuit hunter: E1's oracle (k, speed) steering at the live prey's position, or, for E_prey's
    calibration, at a point of its body (`aim`: position, mid or tail)."""

    AIMS = ("position", "mid", "tail")

    def __init__(self, iface, n, forward_gain, turn_gain, k: float = 2.0, speed: float = 1.0, aim: str = "position",
                 device="cpu"):
        super().__init__(iface, n, forward_gain, turn_gain, k=k, speed=speed, device=device)
        if aim not in self.AIMS:
            raise ValueError(f"aim must be one of {self.AIMS}")
        self.aim = aim

    def target(self) -> torch.Tensor:
        w = self.world
        p, h = w.pos[:, PREY, 0], w.heading[:, PREY, 0]
        back = torch.stack((torch.cos(h), torch.sin(h)), dim=-1)
        L = w.cfg.world.body_length
        return {"position": p, "mid": p - back * (L / 2), "tail": p - back * L}[self.aim]

    def step(self, v, current):
        w = self.world
        head, heading = w.pos[:, HUNTER, 0], w.heading[:, HUNTER, 0]
        c = self.target()
        want = torch.atan2(c[:, 1] - head[:, 1], c[:, 0] - head[:, 0])
        diff = torch.remainder(want - heading + math.pi, 2 * math.pi) - math.pi
        turn = (self.k * diff).clamp(-1, 1).view(1, -1)
        fwd = torch.full_like(turn, self.speed)
        return self.command(current, fwd, turn)
