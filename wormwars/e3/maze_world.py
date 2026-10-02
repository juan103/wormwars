"""E3b's maze shuttle (docs/E3/E3b-0-PLAN.md §1a-§1e): `MazeWorld`, a World subclass, and its parts.

- **The maze:** walls from `maze.maze_for` keyed by (run seed, maze id = world id), placements by (run
  seed, maze id, episode). The colony's weys start round-robin at the spawn cells' centres, with headings
  from their own stream keyed by (run seed, maze id, episode).
- **Visits, per wey:** every wey's goal starts at A. An entry into the current goal's dead-end block (the
  head's grid cell inside its 3 × 3 open block) is a confirmed visit and switches that wey's goal; an entry
  into the other source is a raw entry only. The visit levels `at_a`/`at_b` report the position after the
  previous tick's movement, with `at_b` held at 1 for the start cue (E3a's).
- **Movement:** a step whose segment crosses a wall cell (an exact supercover test against closed cells)
  is refused; with sliding, the x-component alone and then the y-component alone are tried.
- **Trails:** per world [weys, (A, B), H, W], linear, no clamp. After the move: events, timers (0 at a
  visit, else + 1), a deposit d0 exp(−λ t) at the head's cell onto the trail of the source last visited (by
  weys with a visit behind them), flux diffusion, evaporation × (1 − μ).
- **Sensing:** each nose reads (trail as accessed + the path-distance scent) × `sense_scale_food`,
  occluded: 0 if the head → nose segment crosses a wall cell, and a bilinear support cell counts only if
  the nose → cell-centre segment crosses none (weights not renormalised). Collision reads walls only;
  crowding is off in `maze_config`.
- **Access modes,** per world: shared (every wey's trail), own, peers (shared − own), none, replay (own + a
  lockstep donor world's total × a frozen coefficient) and scramble (own + the peers' field with its open
  cells permuted by a fixed permutation per episode).
"""

from __future__ import annotations

import math

import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor

from ..config import Config
from ..fields import sample_bilinear
from ..world import N_POINTS, P_FRONT_C, P_FRONT_L, P_FRONT_R, P_REAR_L, P_REAR_R, World
from . import maze as M
from .task import shuttle_config

ACCESS = ("shared", "own", "peers", "none", "replay", "scramble")
HEADING_STREAM = 0x4EAD
SCRAMBLE_STREAM = 0x5C4A
LEGS = 256  # visits tracked per wey; running out is an error


def maze_config(base: Config | None = None, *, c: int, horizon: int, colony: int = 8, mu: float, lam: float,
                delta: float, d0: float, access: str = "shared", sliding: bool = True, spawns: int = 4,
                scent_sigma: float = 3.0, scent_reach: int = 9) -> Config:
    """E3a's shuttle configuration (Task N's brain and energy settings, the 5-tick cue, the nose scale 0.35)
    turned into the maze shuttle: a colony of `colony` weys, the arena 4c + 1 wide, crowding off."""
    cfg = shuttle_config(base, horizon=horizon)
    w = cfg.world
    w.task = "maze_shuttle"
    w.shuttle_separation_min = w.shuttle_separation_max = w.shuttle_spawn_min = w.shuttle_spawn_max = None
    w.weys_per_swarm = int(colony)
    w.cells_per_wey, w.min_side = 0, 4 * int(c) + 1
    w.crowd_resist, w.crowd_push = 0.0, 0.0
    w.maze_cells, w.maze_spawns, w.maze_sliding = int(c), int(spawns), bool(sliding)
    w.maze_trail_mu, w.maze_trail_lambda, w.maze_trail_delta, w.maze_trail_d0 = (float(mu), float(lam), float(delta),
                                                                               float(d0))
    w.maze_scent_sigma, w.maze_scent_reach, w.maze_trail_access = float(scent_sigma), int(scent_reach), str(access)
    return cfg


# ------------------------------------------------------------------ geometry

_WINDOW = [(ox, oy) for oy in range(3) for ox in range(3)]


def segment_hits(wall: Tensor, p0: Tensor, p1: Tensor) -> Tensor:
    """[N, P]: whether each segment p0 → p1 ([N, P, 2], (x, y) in cell units) touches a wall cell of
    `wall` [N, H, W], each cell taken as the closed square [x, x + 1] × [y, y + 1]; outside the grid
    counts as wall. Exact for segments shorter than 2 cells along each axis (a 3 × 3 window of cells
    from the segment's lower corner), which covers every use here: a step of at most 0.35, a nose at
    0.78 from the head and a support cell's centre within 1.5 of the nose."""
    n, h, w = wall.shape
    p0, p1 = p0.double(), p1.double()
    d = (p1 - p0).unsqueeze(-2)  # [N, P, 1, 2]
    a = p0.unsqueeze(-2)
    off = torch.tensor(_WINDOW, dtype=torch.float64, device=wall.device)
    cell = torch.minimum(p0, p1).floor().unsqueeze(-2) + off  # [N, P, 9, 2]
    cx, cy = cell[..., 0].long(), cell[..., 1].long()
    in_grid = (cx >= 0) & (cx < w) & (cy >= 0) & (cy < h)
    idx = (cy.clamp(0, h - 1) * w + cx.clamp(0, w - 1)).reshape(n, -1)
    is_wall = wall.reshape(n, h * w).gather(1, idx).reshape(cx.shape) | ~in_grid
    flat_axis = d == 0
    safe = torch.where(flat_axis, torch.ones_like(d), d)
    t1, t2 = (cell - a) / safe, (cell + 1 - a) / safe
    inside = (a >= cell) & (a <= cell + 1)
    lo_k = torch.where(flat_axis, torch.where(inside, -math.inf, math.inf), torch.minimum(t1, t2))
    hi_k = torch.where(flat_axis, torch.where(inside, math.inf, -math.inf), torch.maximum(t1, t2))
    t_lo = lo_k.amax(-1).clamp_min(0.0)
    t_hi = hi_k.amin(-1).clamp_max(1.0)
    return (is_wall & (t_lo <= t_hi)).any(-1)


def occlusion(wall: Tensor, head: Tensor, nose: Tensor) -> dict:
    """The geometry of an occluded bilinear read at `nose` [N, P, 2] from `head`, against `wall` [N, H, W]:
    whether the head → nose segment is blocked, the four support cells' flat indices and their weights
    with every hidden or out-of-grid cell's weight at 0, and whether all four are in view. One supercover
    call for all five segments per nose."""
    n, h, w = wall.shape
    x, y = nose[..., 0] - 0.5, nose[..., 1] - 0.5
    x0, y0 = x.floor(), y.floor()
    fx, fy = x - x0, y - y0
    x0, y0 = x0.long(), y0.long()
    dx = torch.tensor([0, 1, 0, 1], device=nose.device)
    dy = torch.tensor([0, 0, 1, 1], device=nose.device)
    cx, cy = x0.unsqueeze(-1) + dx, y0.unsqueeze(-1) + dy  # [N, P, 4]
    wt = torch.stack(((1 - fx) * (1 - fy), fx * (1 - fy), (1 - fx) * fy, fx * fy), dim=-1)
    centre = torch.stack(((cx + 0.5).to(nose.dtype), (cy + 0.5).to(nose.dtype)), dim=-1)  # [N, P, 4, 2]
    P = nose.shape[1]
    starts = torch.cat((head, nose.unsqueeze(2).expand(-1, -1, 4, -1).reshape(n, 4 * P, 2)), dim=1)
    ends = torch.cat((nose, centre.reshape(n, 4 * P, 2)), dim=1)
    hits = segment_hits(wall, starts, ends)
    blocked, hidden = hits[:, :P], hits[:, P:].reshape(n, P, 4)
    in_grid = (cx >= 0) & (cx < w) & (cy >= 0) & (cy < h)
    return {"blocked": blocked, "all_seen": ~hidden.any(-1),
            "idx": cy.clamp(0, h - 1) * w + cx.clamp(0, w - 1), "wt": wt * (~hidden & in_grid)}


def read_occluded(field: Tensor, nose: Tensor, occ: dict) -> Tensor:
    """[N, C, P]: `field` [N, C, H, W] read at `nose` through the geometry `occ` (`occlusion`): exactly
    `sample_bilinear` where every support cell is in view and the nose is not blocked; the visible cells'
    weighted sum, not renormalised, where some are hidden; 0 where the nose is blocked."""
    n, c, h, w = field.shape
    plain = sample_bilinear(field, nose)
    P = nose.shape[1]
    vals = field.reshape(n, c, h * w).gather(2, occ["idx"].reshape(n, 1, 4 * P).expand(n, c, -1)).reshape(n, c, P, 4)
    acc = (vals * occ["wt"].unsqueeze(1)).sum(-1)
    out = torch.where(occ["all_seen"].unsqueeze(1), plain, acc)
    return torch.where(occ["blocked"].unsqueeze(1), torch.zeros_like(out), out)


def occluded_bilinear(field: Tensor, wall: Tensor, head: Tensor, nose: Tensor,
                      return_blocked: bool = False):
    """[N, C, P]: `field` [N, C, H, W] read bilinearly at `nose` [N, P, 2], occluded by `wall` [N, H, W]:
    0 where the head → nose segment crosses a wall cell; otherwise each of the four support cells counts
    only if the nose → its centre segment crosses no wall cell, with the weights not renormalised. A nose
    with every support cell in view reads exactly `sample_bilinear` (bitwise)."""
    occ = occlusion(wall, head, nose)
    out = read_occluded(field, nose, occ)
    return (out, occ["blocked"]) if return_blocked else out


def diffuse(x: Tensor, open_: Tensor, delta: float) -> Tensor:
    """One step of flux diffusion on the open cells, x_i + (δ/4) Σ_open neighbours (x_j − x_i), for `x`
    [..., H, W] zero in walls and `open_` [H, W] or broadcastable (1 open, 0 wall): symmetric, mass
    conserving, and flat at equilibrium. The outer ring must be wall."""
    if delta == 0:
        return x.clone()
    pad = F.pad(x, (1, 1, 1, 1))
    nb = pad[..., :-2, 1:-1] + pad[..., 2:, 1:-1] + pad[..., 1:-1, :-2] + pad[..., 1:-1, 2:]
    op = F.pad(open_, (1, 1, 1, 1))
    n_open = op[..., :-2, 1:-1] + op[..., 2:, 1:-1] + op[..., 1:-1, :-2] + op[..., 1:-1, 2:]
    return (x + (delta / 4) * (nb - n_open * x)) * open_


# ------------------------------------------------------------------ the world

class MazeWorld(World):
    _maze_task = True

    def __init__(self, cfg: Config, iface, brain, strain_of: Tensor, run_seed: int, world_ids=None,
                 device="cpu", dtype=torch.float32, swarm_sizes=None, *, episodes=None, access=None, donors=None,
                 replay_coef=None):
        """`episodes` [worlds] keys each world's placement (default 0). `access` is one mode for every
        world or one per world (default `maze_trail_access`). A replay world names its donor, a world of the
        same batch on the same walls, in `donors` [worlds] (−1 for none), and its coefficient in
        `replay_coef` [worlds]."""
        wcfg = cfg.world
        if wcfg.task != "maze_shuttle":
            raise ValueError("MazeWorld plays the maze_shuttle task (wormwars.e3.maze_world.maze_config)")
        n = int(strain_of.shape[0])
        self.episodes = np.zeros(n, dtype=np.int64) if episodes is None else np.asarray(episodes, dtype=np.int64)
        acc = wcfg.maze_trail_access if access is None else access
        self.access = [acc] * n if isinstance(acc, str) else [str(a) for a in acc]
        self.donors = np.full(n, -1, dtype=np.int64) if donors is None else np.asarray(donors, dtype=np.int64)
        self.replay_coef = np.zeros(n) if replay_coef is None else np.asarray(replay_coef, dtype=np.float64)
        if not (len(self.episodes) == len(self.access) == len(self.donors) == len(self.replay_coef) == n):
            raise ValueError("episodes, access, donors and replay_coef need one entry per world")
        bad = sorted(set(self.access) - set(ACCESS))
        if bad:
            raise ValueError(f"unknown access mode(s) {bad}; known: {ACCESS}")
        ids = np.arange(n, dtype=np.int64) if world_ids is None else np.asarray(world_ids)
        for w in range(n):
            if self.access[w] == "replay":
                dn = int(self.donors[w])
                if not (0 <= dn < n) or dn == w or ids[dn] != ids[w]:
                    raise ValueError(f"world {w}: a replay donor must be another world on the same walls")
        super().__init__(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=world_ids, device=device,
                         dtype=dtype, swarm_sizes=swarm_sizes)
        if self.n_swarms != 1:
            raise ValueError("the maze shuttle has one swarm (a colony)")
        self._build_maze_state()

    # -------------------------------------------------------------- setup

    def _build_maps(self) -> None:
        wcfg = self.cfg.world
        c = int(wcfg.maze_cells)
        if self.side != 4 * c + 1:
            raise ValueError(f"the arena side {self.side} is not 4c + 1 = {4 * c + 1} (maze_config sets it)")
        Wn, B = self.n_worlds, self.n_weys
        wall = np.zeros((Wn, self.H, self.W), dtype=np.float32)
        pos = np.zeros((Wn, 1, B, 2), dtype=np.float32)
        head = np.zeros((Wn, 1, B), dtype=np.float32)
        self.mazes, self.placements = [], []
        for w in range(Wn):
            mid, ep = int(self.world_ids[w]), int(self.episodes[w])
            mz, pl = M.maze_for(run_seed=self.run_seed, maze_id=mid, episode=ep, c=c, n_spawns=int(wcfg.maze_spawns))
            self.mazes.append(mz)
            self.placements.append(pl)
            wall[w] = mz.wall
            for b in range(B):
                pos[w, 0, b] = M.cell_centre(pl.spawns[b % len(pl.spawns)])
            rng = np.random.default_rng([self.run_seed, mid, ep, HEADING_STREAM])
            head[w, 0] = rng.uniform(0, 2 * np.pi, B)
        self.food_patch_centres = [np.zeros((0, 2), dtype=np.float32) for _ in range(Wn)]
        f = self.fields
        f[:, self.ch.FOOD] = 0
        f[:, self.ch.HAZARD] = 0
        f[:, self.ch.WALL] = torch.from_numpy(wall).to(self.device, self.dtype)
        self.pos.copy_(torch.from_numpy(pos).to(self.device, self.dtype))
        self.heading.copy_(torch.from_numpy(head).to(self.device, self.dtype))

    def _build_maze_state(self) -> None:
        wcfg, dev, dt = self.cfg.world, self.device, self.dtype
        Wn, B, H, W = self.n_worlds, self.n_weys, self.H, self.W
        self._wall = self.fields[:, self.ch.WALL] > 0
        self._open = (~self._wall).to(dt)
        self._wall_per_wey = self._wall.unsqueeze(1).expand(-1, B, -1, -1).reshape(Wn * B, H, W).contiguous()
        lo = np.zeros((Wn, 2, 2), dtype=np.int64)  # [worlds, (A, B), (x, y)] of each source block's low corner
        scent = np.zeros((Wn, 2, H, W), dtype=np.float32)
        sig, reach = float(wcfg.maze_scent_sigma), float(wcfg.maze_scent_reach)
        for w, (mz, pl) in enumerate(zip(self.mazes, self.placements)):
            for k, cell in enumerate((pl.a, pl.b)):
                lo[w, k] = (1 + 4 * cell[1], 1 + 4 * cell[0])
                d = mz.free_distance(cell)
                ok = np.isfinite(d) & (d <= reach)
                scent[w, k] = np.where(ok, np.exp(-np.where(ok, d, 0.0) ** 2 / (2 * sig ** 2)), 0.0)
        self._src_lo = torch.from_numpy(lo).to(dev)
        self.scent = torch.from_numpy(scent).to(dev, dt)
        self.goal = torch.zeros(Wn, B, dtype=torch.long, device=dev)  # 0: A, 1: B
        self.visits = torch.zeros(Wn, B, dtype=torch.long, device=dev)
        self.timer = torch.zeros(Wn, B, dtype=torch.long, device=dev)
        self.has_visited = torch.zeros(Wn, B, dtype=torch.bool, device=dev)
        self._inside = torch.zeros(Wn, B, 2, dtype=torch.bool, device=dev)
        self.trails = torch.zeros(Wn, B, 2, H, W, dtype=dt, device=dev)
        self._visit_tick = torch.full((Wn, B, LEGS), -1, dtype=torch.long, device=dev)
        self._entries = torch.zeros(Wn, B, 2, dtype=torch.long, device=dev)
        self._first_b = torch.full((Wn, B), -1, dtype=torch.long, device=dev)
        self._occluded_ticks = torch.zeros(Wn, B, dtype=torch.long, device=dev)
        self._exposure = torch.zeros(Wn, B, dtype=torch.float64, device=dev)
        self._exposure_zero = torch.zeros(Wn, B, dtype=torch.long, device=dev)
        self._overflow = torch.zeros((), dtype=torch.bool, device=dev)
        self.last_occluded = torch.zeros(Wn, B, dtype=torch.long, device=dev)
        self.last_exposure = torch.zeros(Wn, B, dtype=dt, device=dev)
        modes = np.asarray(self.access)
        self._mode = {m: torch.as_tensor(modes == m, device=dev).view(Wn, 1, 1, 1, 1) for m in set(self.access)}
        self._donor = torch.as_tensor(np.maximum(self.donors, 0), device=dev)
        self._coef = torch.as_tensor(self.replay_coef, dtype=dt, device=dev).view(Wn, 1, 1, 1, 1)
        if "scramble" in self._mode:
            open_flat = (~self._wall).reshape(Wn, -1).cpu().numpy()
            counts = open_flat.sum(1)
            if (counts != counts[0]).any():
                raise ValueError("every maze of one size has the same number of open cells")
            idx = np.stack([np.flatnonzero(r) for r in open_flat])
            src = np.stack([idx[w][np.random.default_rng([self.run_seed, int(self.world_ids[w]), int(self.episodes[w]),
                                                           SCRAMBLE_STREAM]).permutation(idx.shape[1])]
                            for w in range(Wn)])
            self._open_idx = torch.from_numpy(idx).to(dev)
            self._scramble_src = torch.from_numpy(src).to(dev)

    # -------------------------------------------------------------- trails as sensed

    def _components(self) -> tuple[Tensor, Tensor, Tensor]:
        """(base, other, exposed), each [worlds, weys, 2, H, W]. What each wey senses of the trails under its
        world's access mode is base + other (shared: the total, exactly; peers: total − own; none: nothing).
        `exposed` is the part that is not the wey's own, which the exposure reads: `other`, except under
        shared, where it is the live peers' field total − own (D178: it was 0, which zeroed the replay
        coefficient)."""
        own = self.trails
        total = own.sum(dim=1, keepdim=True)
        zero = torch.zeros_like(own)
        base = zero
        other = zero
        m = self._mode
        if "own" in m or "replay" in m or "scramble" in m:
            keep = m.get("own", False) | m.get("replay", False) | m.get("scramble", False)
            base = torch.where(keep, own, zero)
        exposed_shared = None
        if "shared" in m:
            base = torch.where(m["shared"], total.expand_as(own), base)
            exposed_shared = total - own
        if "peers" in m:
            other = torch.where(m["peers"], total - own, other)
        if "replay" in m:
            donor_total = total[self._donor] * self._coef
            other = torch.where(m["replay"], donor_total.expand_as(own), other)
        if "scramble" in m:
            peers = (total - own).reshape(self.n_worlds, self.n_weys, 2, -1)
            n_open = self._open_idx.shape[1]
            vals = peers.gather(-1, self._scramble_src.view(self.n_worlds, 1, 1, n_open).expand(-1, self.n_weys, 2, -1))
            perm = torch.zeros_like(peers).scatter_(
                -1, self._open_idx.view(self.n_worlds, 1, 1, n_open).expand(-1, self.n_weys, 2, -1), vals)
            other = torch.where(m["scramble"], perm.reshape(own.shape), other)
        exposed = other if exposed_shared is None else torch.where(m["shared"], exposed_shared, other)
        return base, other, exposed

    def sensed_trails(self) -> Tensor:
        """[worlds, weys, 2, H, W]: the trails each wey senses under its world's access mode."""
        base, other, _ = self._components()
        return base + other

    # -------------------------------------------------------------- hooks

    def _resolve_move(self, proposed: Tensor) -> Tensor:
        Wn, B = self.n_worlds, self.n_weys
        p0, p1 = self.pos.double().reshape(Wn, -1, 2), proposed.double().reshape(Wn, -1, 2)

        if self.cfg.world.maze_sliding:
            qx = torch.stack((p1[..., 0], p0[..., 1]), dim=-1)
            qy = torch.stack((p0[..., 0], p1[..., 1]), dim=-1)
            n = p0.shape[1]
            ok = ~segment_hits(self._wall, p0.repeat(1, 3, 1), torch.cat((p1, qx, qy), dim=1))
            full, okx, oky = ok[:, :n], ok[:, n:2 * n], ok[:, 2 * n:]
            new = torch.where(full.unsqueeze(-1), p1,
                              torch.where(okx.unsqueeze(-1), qx, torch.where(oky.unsqueeze(-1), qy, p0)))
        else:
            new = torch.where((~segment_hits(self._wall, p0, p1)).unsqueeze(-1), p1, p0)
        return new.reshape(Wn, 1, B, 2).to(self.dtype)

    def _extra_signals(self, pts: Tensor) -> dict:
        wcfg = self.cfg.world
        Wn, B, H, W = self.n_worlds, self.n_weys, self.H, self.W
        P = pts.reshape(Wn, B, N_POINTS, 2)
        head = P[:, :, 0:1].expand(-1, -1, 2, -1).reshape(Wn * B, 2, 2)
        noses = P[:, :, [P_FRONT_L, P_FRONT_R]].reshape(Wn * B, 2, 2)
        occ = occlusion(self._wall_per_wey, head, noses)
        base, other, exposed = self._components()
        field = (base + other + self.scent.unsqueeze(1)).reshape(Wn * B, 2, H, W)
        read, blocked = read_occluded(field, noses, occ), occ["blocked"]  # [W*B, (A, B), (L, R)]
        sf = wcfg.sense_scale_food
        read = (read * sf).reshape(Wn, 1, B, 2, 2)
        a_l, a_r, b_l, b_r = read[..., 0, 0], read[..., 0, 1], read[..., 1, 0], read[..., 1, 1]
        self.last_blocked = blocked.reshape(Wn, B, 2)  # per nose, (left, right)
        self.last_occluded = self.last_blocked.sum(-1)
        self._occluded_ticks += (self.last_occluded > 0).long()
        if set(self._mode) <= {"own", "none"}:  # nothing but the wey's own trail is sensed
            self.last_exposure = torch.zeros(Wn, B, dtype=self.dtype, device=self.device)
        else:
            ex = read_occluded(exposed.reshape(Wn * B, 2, H, W), noses, occ) * sf
            self.last_exposure = ex.reshape(Wn, B, 4).mean(-1)
        self._exposure += self.last_exposure.double()
        self._exposure_zero += (self.last_exposure == 0).long()
        to_b = (self.goal == 1).view(Wn, 1, B)
        level = self._inside.to(self.dtype)
        at_a, at_b = level[..., 0].view(Wn, 1, B), level[..., 1].view(Wn, 1, B)
        if self.tick_count < wcfg.shuttle_cue_ticks:
            at_b = torch.ones_like(at_b)
        wall_read = sample_bilinear(self.fields[:, self.ch.WALL:self.ch.WALL + 1], pts)[:, 0].reshape(Wn, 1, B, N_POINTS)
        sc = wcfg.sense_scale_collision
        return {"a_left": a_l, "a_right": a_r, "b_left": b_l, "b_right": b_r,
                "goal_left": torch.where(to_b, b_l, a_l), "goal_right": torch.where(to_b, b_r, a_r),
                "at_a": at_a.contiguous(), "at_b": at_b.contiguous(),
                "collision_front": wall_read[..., P_FRONT_C] * sc,
                "collision_front_left": wall_read[..., P_FRONT_L] * sc,
                "collision_front_right": wall_read[..., P_FRONT_R] * sc,
                "collision_rear_left": wall_read[..., P_REAR_L] * sc,
                "collision_rear_right": wall_read[..., P_REAR_R] * sc}

    def _post_move(self, moved: Tensor) -> None:
        wcfg, t = self.cfg.world, self.tick_count
        Wn, B = self.n_worlds, self.n_weys
        head = self.pos[:, 0]  # [worlds, weys, 2]
        ix, iy = head[..., 0].floor().long(), head[..., 1].floor().long()
        lo = self._src_lo.unsqueeze(1)  # [worlds, 1, (A, B), (x, y)]
        inside = ((ix.unsqueeze(-1) >= lo[..., 0]) & (ix.unsqueeze(-1) < lo[..., 0] + 3)
                  & (iy.unsqueeze(-1) >= lo[..., 1]) & (iy.unsqueeze(-1) < lo[..., 1] + 3))  # [worlds, weys, 2]
        alive = self.alive[:, 0]
        entry = inside & ~self._inside & alive.unsqueeze(-1)
        self._entries += entry.long()
        confirmed = entry.gather(2, self.goal.unsqueeze(-1)).squeeze(-1)
        k = self.visits.clamp_max(LEGS - 1).unsqueeze(-1)
        self._visit_tick.scatter_(2, k, torch.where(confirmed.unsqueeze(-1), torch.full_like(k, t),
                                                    self._visit_tick.gather(2, k)))
        self._first_b = torch.where(confirmed & (self.goal == 1) & (self._first_b < 0),
                                    torch.full_like(self._first_b, t), self._first_b)
        self.visits += confirmed.long()
        self._overflow |= (self.visits >= LEGS).any()
        self.goal = torch.where(confirmed, 1 - self.goal, self.goal)
        self.has_visited |= confirmed
        self.timer = torch.where(confirmed, torch.zeros_like(self.timer), self.timer + 1)
        # deposit at the head's cell onto the trail of the source last visited (the one not now sought)
        amt = (wcfg.maze_trail_d0 * torch.exp(-wcfg.maze_trail_lambda * self.timer.to(torch.float64))).to(self.dtype)
        amt = amt * (self.has_visited & alive).to(self.dtype)
        wi = torch.arange(Wn, device=self.device).view(-1, 1).expand(Wn, B)
        bi = torch.arange(B, device=self.device).view(1, -1).expand(Wn, B)
        src = 1 - self.goal
        cy, cx = iy.clamp(0, self.H - 1), ix.clamp(0, self.W - 1)
        self.trails[wi, bi, src, cy, cx] = self.trails[wi, bi, src, cy, cx] + amt
        self.trails = diffuse(self.trails, self._open.view(Wn, 1, 1, self.H, self.W), wcfg.maze_trail_delta) \
            * (1.0 - wcfg.maze_trail_mu)
        self._inside = inside

    # -------------------------------------------------------------- outcomes

    def task_score(self) -> Tensor:
        """[worlds]: confirmed visits per wey, the colony's mean."""
        return self.visits.sum(dim=1).to(torch.float32) / self.swarm_sizes[:, 0].to(torch.float32)

    def task_events(self) -> dict[str, np.ndarray]:
        """The colony's ledger, per world and wey: the confirmed-visit ticks ([worlds, weys, LEGS], −1
        padded; visits alternate A, B, A, ...), raw entries into (A, B), the first-B tick (−1: none), the
        ticks with at least one occluded nose, the summed exposure to the other part of the sensed trails
        and its zero ticks, and the sources' cells."""
        if bool(self._overflow):
            raise RuntimeError("a wey completed every tracked visit: raise LEGS")
        pl = self.placements
        return {"visit_tick": self._visit_tick.cpu().numpy(), "visits": self.visits.cpu().numpy(),
                "entries": self._entries.cpu().numpy(), "first_b_tick": self._first_b.cpu().numpy(),
                "occluded_ticks": self._occluded_ticks.cpu().numpy(), "exposure_sum": self._exposure.cpu().numpy(),
                "exposure_zero_ticks": self._exposure_zero.cpu().numpy(),
                "ticks": np.full(self.n_worlds, self.tick_count, dtype=np.int64),
                "episode": self.episodes.copy(),
                "a_cell": np.array([p.a for p in pl], dtype=np.int64), "b_cell": np.array([p.b for p in pl], dtype=np.int64)}
