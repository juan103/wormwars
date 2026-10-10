"""E3d's scripted wall-follower (docs/E3/E3d-DESIGN.md v2.2 §3). E3b-0's controls stay in `maze_controls`.

Privileged wall sensing, as the oracle's positions are: the world's wall raster along three probe rays from
the head, each a Boolean lookup of the grid cells holding its points at every half cell out to its range
(outside the grid counts as wall):
- ahead, 1.5 cells along the heading θ;
- the hugged side, 1.0 cell at θ + 90° (left-handed) or θ − 90° (right-handed);
- ahead on the hugged side, 1.4 cells at θ ± 45°.

Wall ahead → full turn away from the hugged side; side and ahead-side both clear → full turn toward it, for
at most `LOST_TICKS` ticks since either last sensed a wall, then straight (a search); otherwise straight.
Before it first senses a wall it searches straight. Forward drive 1. A positive turn increases θ (`world.py`),
so "toward" is +1 for the left hand and −1 for the right. It never reads scent or trail.

Amendment 1 to the bound design (2026-10-10, before any play), found by the qualification tests:
- **the search state:** the policy as bound circled forever in open space and in a corridor's centre, where its
  side probe always points at the circle's centre;
- **probes read along their rays:** a single point 1.5 cells ahead jumps over a 1-cell wall and lands in free
  space beyond, so the follower drove into a wall it never sensed and stalled.
"""

from __future__ import annotations

import math

import torch

from .maze_controls import WorldScripted

AHEAD, SIDE, DIAGONAL = 1.5, 1.0, 1.4
LOST_TICKS = 12  # 3.6 rad at the full turn of 0.30 rad per tick: more than enough to round a convex corner
NEVER = 1 << 30


def _point(wall: torch.Tensor, head: torch.Tensor, angle: torch.Tensor, r: float) -> torch.Tensor:
    """[worlds, weys]: whether the cell holding head + r (cos, sin)(angle) is wall (or outside the grid)."""
    Wn, H, W = wall.shape
    x = head[..., 0] + r * torch.cos(angle)
    y = head[..., 1] + r * torch.sin(angle)
    ix, iy = x.floor().long(), y.floor().long()
    inside = (ix >= 0) & (ix < W) & (iy >= 0) & (iy < H)
    wi = torch.arange(Wn, device=wall.device).view(-1, 1).expand_as(ix)
    return wall[wi, iy.clamp(0, H - 1), ix.clamp(0, W - 1)] | ~inside


def _probe(wall: torch.Tensor, head: torch.Tensor, angle: torch.Tensor, r: float) -> torch.Tensor:
    """[worlds, weys]: whether any point of the ray at 0.5, 1.0, … cells, and at r, is in a wall."""
    steps = [0.5 * k for k in range(1, int(r / 0.5) + 1)]
    if steps[-1] != r:
        steps.append(r)
    hit = _point(wall, head, angle, steps[0])
    for d in steps[1:]:
        hit = hit | _point(wall, head, angle, d)
    return hit


def wall_follow_turn(wall: torch.Tensor, head: torch.Tensor, heading: torch.Tensor, hand: str,
                     since: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    """The turn command [worlds, weys] and the updated ticks since a side probe last sensed a wall, for `wall`
    [worlds, H, W] (bool), `head` [worlds, weys, 2], `heading` [worlds, weys] and `since` [worlds, weys]."""
    if hand not in ("left", "right"):
        raise ValueError(f"hand is 'left' or 'right', not {hand!r}")
    s = 1.0 if hand == "left" else -1.0
    ahead = _probe(wall, head, heading, AHEAD)
    side = _probe(wall, head, heading + s * math.pi / 2, SIDE)
    diag = _probe(wall, head, heading + s * math.pi / 4, DIAGONAL)
    toward = torch.full_like(heading, s)
    clear = ~side & ~diag
    turn = torch.where(clear & (since < LOST_TICKS), toward, torch.zeros_like(heading))
    since = torch.where(clear, (since + 1).clamp_max(NEVER), torch.zeros_like(since))
    return torch.where(ahead, -toward, turn), since


class WallFollower(WorldScripted):
    def __init__(self, iface, cfg, hand: str, n: int = 302, device="cpu"):
        super().__init__(iface, cfg, None, n=n, device=device)
        if hand not in ("left", "right"):
            raise ValueError(f"hand is 'left' or 'right', not {hand!r}")
        self.hand, self.since = hand, None

    def attach_world(self, world) -> None:
        super().attach_world(world)
        self.since = torch.full((world.n_worlds, world.n_weys), NEVER, dtype=torch.long, device=world.device)

    def commands(self):
        w = self.world
        turn, self.since = wall_follow_turn(w._wall, w.pos[:, 0], w.heading[:, 0], self.hand, self.since)
        turn = turn.unsqueeze(1)
        return torch.ones_like(turn), turn


def wall_follower(iface, cfg, hand: str, n: int = 302, device="cpu") -> WallFollower:
    return WallFollower(iface, cfg, hand, n=n, device=device)


def tangent_start(world) -> "np.ndarray":
    """§3's diagnostic start, for every blind control alike: each wey moved from its spawn cell's centre 1 cell
    toward a closed side of that cell, heading along the wall, the wall on its left for even weys and on its
    right for odd ones. Sides are tried in the order north, east, south, west, rotated by the wey's index.
    Returns [worlds, weys]: whether the wey was moved (a spawn cell with no closed side keeps its start)."""
    import numpy as np
    sides = [((0, -1), -math.pi / 2), ((1, 0), 0.0), ((0, 1), math.pi / 2), ((-1, 0), math.pi)]  # (dx, dy), angle
    wall = world._wall.cpu().numpy()
    Wn, B = world.n_worlds, world.n_weys
    moved = np.zeros((Wn, B), dtype=bool)
    pos, head = world.pos.clone(), world.heading.clone()
    for w in range(Wn):
        spawns = world.placements[w].spawns
        for b in range(B):
            i, j = spawns[b % len(spawns)]
            cx, cy = 2.5 + 4 * j, 2.5 + 4 * i
            for k in range(4):
                (dx, dy), phi = sides[(b + k) % 4]
                if wall[w, int(cy + 2 * dy - 0.5), int(cx + 2 * dx - 0.5)]:  # the side's middle wall cell
                    pos[w, 0, b, 0], pos[w, 0, b, 1] = cx + dx, cy + dy
                    head[w, 0, b] = (phi - math.pi / 2 if b % 2 == 0 else phi + math.pi / 2) % (2 * math.pi)
                    moved[w, b] = True
                    break
    world.pos.copy_(pos)
    world.heading.copy_(head)
    world._points = None  # the body points derive from position and heading
    return moved
