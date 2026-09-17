"""The batched world: fields, bodies, movement, eating, and the energy ledger.

Shapes. Every simulation tensor has a leading world axis and there is no Python loop over worlds or
weys anywhere in `tick()`.

    fields   [worlds, channels, H, W]
    pos      [worlds, swarms, weys, 2]      (x, y) in cell units
    heading  [worlds, swarms, weys]         radians
    energy   [worlds, swarms, weys]
    alive    [worlds, swarms, weys]         bool

Energy bookkeeping. The total energy of a world is

    sum(energy of living weys) + body_mass * (living weys) + sum(food) + sum(pellets)

and it may change only through the sources and sinks listed in `Ledger`. Everything else -- eating,
dying, biting -- only moves energy between those four pots. `energy_ledger_error()` checks it.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from .brain import Brain
from .config import Config
from .fields import (
    blur,
    diffuse_decay,
    gradient,
    sample_bilinear,
    sample_nearest,
    scale_to_cap,
    splat,
    splat_into,
)
from .interface import Interface

# --- sample points carried per wey, in this order ---
P_HEAD, P_MID, P_TAIL = 0, 1, 2
P_FRONT_L, P_FRONT_R, P_FRONT_C = 3, 4, 5
P_REAR_L, P_REAR_R = 6, 7
P_BODY_L, P_BODY_R = 8, 9
N_POINTS = 10
BODY_POINTS = (P_HEAD, P_MID, P_TAIL)


class Channels:
    """Channel layout of the field tensor. Pheromone and attack are per swarm."""

    def __init__(self, n_swarms: int):
        self.FOOD = 0
        self.PELLET = 1
        self.HAZARD = 2
        self.WALL = 3
        self.BODY = 4
        self.PHEROMONE = 5
        self.ATTACK = 5 + n_swarms
        self.n = 5 + 2 * n_swarms
        self.n_swarms = n_swarms

    def pheromone(self, swarm: int) -> int:
        return self.PHEROMONE + swarm

    def attack(self, swarm: int) -> int:
        return self.ATTACK + swarm


@dataclass
class Ledger:
    """Cumulative energy sources and sinks per world, in float64.

    These are the *only* ways a world's total energy may change. Anything else is a bug and
    `energy_ledger_error` will find it.
    """

    spawned: Tensor  # source: food added to the map after tick 0
    drained: Tensor  # sink: metabolism and movement
    pumped: Tensor  # sink: cost of pumping (stage 2)
    hazard: Tensor  # sink: hazard damage
    inefficiency: Tensor  # sink: the part of bite damage not transferred to the attacker

    @staticmethod
    def zeros(n_worlds: int, device) -> "Ledger":
        z = lambda: torch.zeros(n_worlds, dtype=torch.float64, device=device)  # noqa: E731
        return Ledger(z(), z(), z(), z(), z())

    def net(self) -> Tensor:
        return self.spawned - (self.drained + self.pumped + self.hazard + self.inefficiency)

    def totals(self) -> dict[str, float]:
        return {
            "spawned": float(self.spawned.sum()),
            "drained": float(self.drained.sum()),
            "pumped": float(self.pumped.sum()),
            "hazard": float(self.hazard.sum()),
            "inefficiency": float(self.inefficiency.sum()),
        }


class StrainAssignment:
    """Maps one swarm column's (world -> strain) choice onto a strain-major brain batch.

    The brain wants `[strains, weys, neurons]`; the world is `[worlds, weys, ...]` for this column.
    Strains that appear fewer times than the busiest one are padded with unused slots, so a schedule
    does not have to be perfectly balanced. Padding costs compute, never correctness: padded slots
    are never read back.
    """

    def __init__(self, strain_of: Tensor, n_strains: int):
        flat = strain_of.reshape(-1)
        counts = torch.bincount(flat, minlength=n_strains)
        self.n_strains = n_strains
        self.n_slots = int(counts.max())
        self.counts = counts
        order = torch.argsort(flat, stable=True)
        starts = torch.cumsum(counts, 0) - counts
        rank = torch.arange(flat.numel(), device=flat.device) - starts[flat[order]]
        slot = flat[order] * self.n_slots + rank
        self.slot_of = torch.empty_like(flat)
        self.slot_of[order] = slot
        self.padding_fraction = 1.0 - flat.numel() / max(n_strains * self.n_slots, 1)

    def to_brain(self, x: Tensor) -> Tensor:
        """[worlds, weys, C] -> [strains, slots*weys, C]"""
        n, weys, c = x.shape
        buf = torch.zeros(
            self.n_strains * self.n_slots, weys, c, device=x.device, dtype=x.dtype
        )
        buf[self.slot_of] = x
        return buf.reshape(self.n_strains, self.n_slots * weys, c)

    def from_brain(self, y: Tensor, worlds: int, weys: int) -> Tensor:
        """[strains, slots*weys, C] -> [worlds, weys, C]"""
        buf = y.reshape(self.n_strains * self.n_slots, weys, y.shape[-1])
        return buf[self.slot_of]


def world_seed(run_seed: int, world_index: int) -> int:
    """Documented derivation of a world's RNG seed from the run seed.

    splitmix64 of (run_seed * 2^32 + world_index). Deterministic, independent of batch composition
    and of how worlds are chunked, so world 37 of a run always gets the same map.
    """
    z = (run_seed * (1 << 32) + world_index + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return (z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF


def arena_side(cfg, total_weys: int) -> int:
    """Square arena whose interior area keeps `cells_per_wey` constant as headcount changes."""
    interior = float(cfg.world.cells_per_wey) * total_weys
    side = int(np.ceil(np.sqrt(interior))) + 2  # + the one-cell wall ring on each side
    return max(side, cfg.world.min_side)


class World:
    def __init__(
        self,
        cfg: Config,
        iface: Interface,
        brain: Brain | list[Brain],
        strain_of: Tensor,
        run_seed: int,
        world_ids: np.ndarray | None = None,
        device: str | torch.device = "cpu",
        dtype: torch.dtype = torch.float32,
        combat_stage: int = 0,
        swarm_sizes: Tensor | np.ndarray | None = None,
        swap_sides: Tensor | np.ndarray | None = None,
    ):
        """
        `brain` may be one Brain shared by every swarm, or one per swarm. Per-swarm brains are what
        make a match between two *different* graphs possible at all: N2 and SH have different masks,
        so they cannot share a weight tensor.

        `swarm_sizes [worlds, swarms]` gives each swarm's real headcount; the wey axis is padded to
        the largest and the surplus weys start dead. `swap_sides [worlds]` exchanges the two spawn
        boxes, which is how paired evaluation gets the same map played from both sides without
        touching which swarm index is which strain.
        """
        self.cfg, self.iface = cfg, iface
        self.device = torch.device(device)
        self.dtype = dtype
        self.combat_stage = combat_stage
        wcfg = cfg.world

        strain_of = strain_of.to(self.device)
        self.n_worlds, self.n_swarms = int(strain_of.shape[0]), int(strain_of.shape[1])
        self.brains = list(brain) if isinstance(brain, (list, tuple)) else [brain] * self.n_swarms
        if len(self.brains) != self.n_swarms:
            raise ValueError(f"{len(self.brains)} brains for {self.n_swarms} swarms")
        self.brain = self.brains[0]
        if swarm_sizes is None:
            swarm_sizes = torch.full(
                (self.n_worlds, self.n_swarms), wcfg.weys_per_swarm, dtype=torch.long
            )
        self.swarm_sizes = torch.as_tensor(swarm_sizes, dtype=torch.long, device=self.device)
        self.n_weys = int(self.swarm_sizes.max())
        self.swap_sides = (
            torch.zeros(self.n_worlds, dtype=torch.bool, device=self.device)
            if swap_sides is None
            else torch.as_tensor(swap_sides, dtype=torch.bool, device=self.device)
        )
        self.assigns = [
            StrainAssignment(strain_of[:, s], self.brains[s].n_strains)
            for s in range(self.n_swarms)
        ]
        self.assign = self.assigns[0]
        self.ch = Channels(self.n_swarms)

        total = int(self.swarm_sizes.sum(dim=1).max())
        self.side = arena_side(cfg, total)
        self.H = self.W = self.side
        self.run_seed = int(run_seed)
        self.world_ids = (
            np.arange(self.n_worlds, dtype=np.int64) if world_ids is None else np.asarray(world_ids)
        )

        self.fields = torch.zeros(
            self.n_worlds, self.ch.n, self.H, self.W, device=self.device, dtype=dtype
        )
        self.pos = torch.zeros(
            self.n_worlds, self.n_swarms, self.n_weys, 2, device=self.device, dtype=dtype
        )
        self.heading = torch.zeros(
            self.n_worlds, self.n_swarms, self.n_weys, device=self.device, dtype=dtype
        )
        # weys beyond a swarm's real headcount are padding: dead from tick 0, no energy, no body
        # mass, and they never leave a corpse
        index = torch.arange(self.n_weys, device=self.device).view(1, 1, -1)
        self.alive = index < self.swarm_sizes.unsqueeze(-1)
        self.energy = torch.where(
            self.alive, torch.full_like(self.heading, wcfg.start_energy), torch.zeros_like(self.heading)
        )
        self.pump = torch.zeros_like(self.heading)
        self.last_damage_taken = torch.zeros_like(self.heading)
        self.last_damage_dealt = torch.zeros_like(self.heading)
        # tactics accounting: damage received at head / mid / tail, and how often a wey turned
        # toward the side it was bitten from
        self.damage_by_point = torch.zeros(3, dtype=torch.float64, device=self.device)
        self.turn_toward_damage = torch.zeros(2, dtype=torch.float64, device=self.device)
        self.v = [
            self.brains[s].initial_state(self.assigns[s].n_slots * self.n_weys)
            for s in range(self.n_swarms)
        ]
        self.ledger = Ledger.zeros(self.n_worlds, self.device)
        self.tick_count = 0
        self.recorder = None

        to = lambda a: torch.as_tensor(a, device=self.device)  # noqa: E731
        self._m_fwd_p, self._m_fwd_m = to(iface.forward_plus), to(iface.forward_minus)
        self._m_turn_p, self._m_turn_m = to(iface.turn_plus), to(iface.turn_minus)
        self._m_pump = to(iface.pump_neurons)
        self._sensor_idx = to(iface.sensor_neuron)
        self._sensor_gain = torch.as_tensor(iface.sensor_gain, device=self.device, dtype=dtype)
        self._points = None  # recomputed whenever pos/heading change

        self._build_maps()
        self._update_body_field()
        self.start_energy_total = self.total_energy().clone()

    # ---------------------------------------------------------------- setup

    def _build_maps(self) -> None:
        """Per-world random map. One numpy RNG per world, seeded by `world_seed`, so a world's map
        depends only on (run_seed, world_id) and never on how worlds were batched."""
        mcfg, wcfg = self.cfg.map, self.cfg.world
        H, W = self.H, self.W
        food = np.zeros((self.n_worlds, H, W), dtype=np.float32)
        hazard = np.zeros((self.n_worlds, H, W), dtype=np.float32)
        wall = np.zeros((self.n_worlds, H, W), dtype=np.float32)
        wall[:, 0, :] = wall[:, -1, :] = wall[:, :, 0] = wall[:, :, -1] = 1.0
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        yy, xx = yy + 0.5, xx + 0.5
        cy = cx = (H - 1) / 2.0

        pos = np.zeros((self.n_worlds, self.n_swarms, self.n_weys, 2), dtype=np.float32)
        head = np.zeros((self.n_worlds, self.n_swarms, self.n_weys), dtype=np.float32)
        self.food_patch_centres: list[np.ndarray] = []

        def bump(px, py, r):
            """Finite-support blob: zero outside radius r, so patches stay patches.

            A Gaussian's tail put a little food in every cell of the arena, which let weys eat
            wherever they happened to spawn. This profile has hard support.
            """
            d2 = ((xx - px) ** 2 + (yy - py) ** 2) / (r * r)
            return np.clip(1.0 - d2, 0.0, None) ** 2

        for w in range(self.n_worlds):
            rng = np.random.default_rng(world_seed(self.run_seed, int(self.world_ids[w])))

            # Spawn boxes first, so hazards can be kept clear of them.
            #
            # Every random draw here is indexed by *side*, not by swarm, and the draws happen in a
            # fixed side order. Swapping sides is then an exact relabelling of who stands where: the
            # same map, the same two spawn clouds, the two swarms exchanged. If the jitter were
            # drawn per swarm index instead, swapping would also reshuffle the starting positions
            # and "the same seed from both sides" would not be the same fight.
            half = mcfg.spawn_spread * W / 2
            radius = (W / 2 - mcfg.spawn_margin) * 0.82
            sides = []
            for side in range(self.n_swarms):
                if self.n_swarms == 1:
                    ang = rng.uniform(0, 2 * np.pi)
                else:
                    ang = np.pi * side + rng.uniform(-0.35, 0.35)
                sides.append(
                    (
                        cx + np.cos(ang) * radius,
                        cy + np.sin(ang) * radius,
                        rng.uniform(-half, half, self.n_weys),
                        rng.uniform(-half, half, self.n_weys),
                        rng.uniform(0, 2 * np.pi, self.n_weys),
                    )
                )
            spawn_centres = [(bx, by) for bx, by, *_ in sides]
            swap = bool(self.swap_sides[w])
            for s in range(self.n_swarms):
                bx, by, jx, jy, jh = sides[(s + 1) % self.n_swarms if swap else s]
                pos[w, s, :, 0] = np.clip(bx + jx, 1.2, W - 1.2)
                pos[w, s, :, 1] = np.clip(by + jy, 1.2, H - 1.2)
                head[w, s] = jh

            centres = []
            for _ in range(rng.integers(*mcfg.food_patches, endpoint=True)):
                r = rng.uniform(*mcfg.food_patch_radius)
                amount = rng.uniform(*mcfg.food_per_patch)
                # patches sit toward the middle: hiding in a corner means starving
                px = cx + rng.uniform(-1, 1) * mcfg.food_centre_bias * (W / 2 - r - 2)
                py = cy + rng.uniform(-1, 1) * mcfg.food_centre_bias * (H / 2 - r - 2)
                blob = bump(px, py, r)
                food[w] += (amount * blob / max(blob.sum(), 1e-6)).astype(np.float32)
                centres.append((px, py))
            self.food_patch_centres.append(np.array(centres, dtype=np.float32))

            for _ in range(rng.integers(*mcfg.hazard_patches, endpoint=True)):
                r = rng.uniform(*mcfg.hazard_radius)
                strength = rng.uniform(*mcfg.hazard_strength)
                for _try in range(20):
                    px, py = rng.uniform(2, W - 2), rng.uniform(2, H - 2)
                    if all(
                        np.hypot(px - bx, py - by) > mcfg.hazard_spawn_clearance
                        for bx, by in spawn_centres
                    ):
                        break
                hazard[w] = np.maximum(hazard[w], (strength * bump(px, py, r)).astype(np.float32))

        f = self.fields
        f[:, self.ch.FOOD] = torch.from_numpy(food).to(self.device, self.dtype)
        f[:, self.ch.HAZARD] = torch.from_numpy(hazard).to(self.device, self.dtype)
        f[:, self.ch.WALL] = torch.from_numpy(wall).to(self.device, self.dtype)
        self.pos.copy_(torch.from_numpy(pos).to(self.device, self.dtype))
        self.heading.copy_(torch.from_numpy(head).to(self.device, self.dtype))
        # nothing may start inside a wall
        self.pos.clamp_(1.05, self.side - 1.05)

    # ------------------------------------------------------------- geometry

    def sample_points(self) -> Tensor:
        """[worlds, swarms*weys*N_POINTS, 2] -- every point every wey needs, in one tensor.

        Cached within a tick: `pos` and `heading` only change once per tick, and three separate
        consumers (sensing, body density, combat) need the same points.
        """
        if self._points is not None:
            return self._points
        wcfg, iface = self.cfg.world, self.iface
        c, s = torch.cos(self.heading), torch.sin(self.heading)
        fwd = torch.stack((c, s), dim=-1)  # [Wd, S, B, 2]
        left = torch.stack((-s, c), dim=-1)
        head = self.pos
        mid = head - fwd * (wcfg.body_length * 0.5)
        tail = head - fwd * wcfg.body_length
        fo, lo = iface.forward_offset, iface.lateral_offset
        pts = torch.stack(
            [
                head,
                mid,
                tail,
                head + fwd * fo + left * lo,
                head + fwd * fo - left * lo,
                head + fwd * fo,
                tail - fwd * fo + left * lo,
                tail - fwd * fo - left * lo,
                mid + left * lo,
                mid - left * lo,
            ],
            dim=3,
        )  # [Wd, S, B, N_POINTS, 2]
        self._points = pts.reshape(self.n_worlds, -1, 2)
        return self._points

    def body_points(self) -> Tensor:
        """[worlds, swarms*weys*3, 2] -- the head, mid and tail of every wey."""
        pts = self.sample_points().reshape(
            self.n_worlds, self.n_swarms, self.n_weys, N_POINTS, 2
        )
        return pts[:, :, :, BODY_POINTS].reshape(self.n_worlds, -1, 2)

    # -------------------------------------------------------------- sensing

    def _sensor_signals(self, sampled: Tensor) -> dict[str, Tensor]:
        """`sampled` is [worlds, channels, swarms, weys, N_POINTS]; returns named signals
        shaped [worlds, swarms, weys], already scaled to injected-current units."""
        ch, wcfg = self.ch, self.cfg.world
        n_sw = self.n_swarms
        swarm_ix = torch.arange(n_sw, device=self.device)

        def at(channel, point):
            return sampled[:, channel, :, :, point]

        food = sampled[:, ch.FOOD] + sampled[:, ch.PELLET]
        own_ph = sampled[:, ch.PHEROMONE + swarm_ix, swarm_ix]  # [Wd, S, B, P]
        if n_sw > 1:
            all_ph = sampled[:, ch.PHEROMONE : ch.PHEROMONE + n_sw]  # [Wd, S_ch, S, B, P]
            enemy_ph = all_ph.sum(dim=1) - own_ph
            all_at = sampled[:, ch.ATTACK : ch.ATTACK + n_sw]
            enemy_at = all_at.sum(dim=1) - all_at[:, swarm_ix, swarm_ix]
        else:
            enemy_ph = torch.zeros_like(own_ph)
            enemy_at = torch.zeros_like(own_ph)

        obstacle = sampled[:, ch.WALL] + sampled[:, ch.BODY]
        sf, sp = wcfg.sense_scale_food, wcfg.sense_scale_pheromone
        sh, sd, sc = wcfg.sense_scale_hazard, wcfg.sense_scale_damage, wcfg.sense_scale_collision
        return {
            "food_left": food[..., P_FRONT_L] * sf,
            "food_right": food[..., P_FRONT_R] * sf,
            "ally_pheromone_left": own_ph[..., P_FRONT_L] * sp,
            "ally_pheromone_right": own_ph[..., P_FRONT_R] * sp,
            "enemy_pheromone_left": enemy_ph[..., P_FRONT_L] * sp,
            "enemy_pheromone_right": enemy_ph[..., P_FRONT_R] * sp,
            "hazard_left": at(ch.HAZARD, P_FRONT_L) * sh,
            "hazard_right": at(ch.HAZARD, P_FRONT_R) * sh,
            "damage_left": enemy_at[..., P_BODY_L] * sd,
            "damage_right": enemy_at[..., P_BODY_R] * sd,
            "collision_front": obstacle[..., P_FRONT_C] * sc,
            "collision_front_left": obstacle[..., P_FRONT_L] * sc,
            "collision_front_right": obstacle[..., P_FRONT_R] * sc,
            "collision_rear_left": obstacle[..., P_REAR_L] * sc,
            "collision_rear_right": obstacle[..., P_REAR_R] * sc,
        }

    def _build_current(self, signals: dict[str, Tensor]) -> Tensor:
        iface, bcfg = self.iface, self.cfg.brain
        shape = (self.n_worlds, self.n_swarms, self.n_weys, self.brains[0].n)
        current = torch.zeros(shape, device=self.device, dtype=self.dtype)
        values = torch.stack([signals[name] for name in iface.signal_names], dim=-1)
        flat = current.reshape(-1, self.brains[0].n)
        flat.index_add_(
            1,
            self._sensor_idx,
            (values * self._sensor_gain * bcfg.input_gain).reshape(-1, len(self._sensor_idx)),
        )
        current = flat.reshape(shape).clamp_(-bcfg.input_max, bcfg.input_max)
        return current * self.alive.unsqueeze(-1)

    def _read_motors(self, v_world: Tensor) -> tuple[Tensor, Tensor, Tensor]:
        act = torch.tanh(v_world)
        fwd = act[..., self._m_fwd_p].mean(-1) - act[..., self._m_fwd_m].mean(-1)
        turn = act[..., self._m_turn_p].mean(-1) - act[..., self._m_turn_m].mean(-1)
        pump = torch.sigmoid(self.iface.pump_gain * act[..., self._m_pump].mean(-1))
        wcfg = self.cfg.world
        return (
            (fwd * 0.5 * wcfg.forward_gain).clamp(-1, 1),
            (turn * 0.5 * wcfg.turn_gain).clamp(-1, 1),
            pump,
        )

    # ------------------------------------------------------------ the tick

    def tick(self) -> None:
        wcfg = self.cfg.world
        alive_f = self.alive.to(self.dtype)

        # 1. sense
        pts = self.sample_points()
        sampled = sample_bilinear(self.fields, pts).reshape(
            self.n_worlds, self.ch.n, self.n_swarms, self.n_weys, N_POINTS
        )
        signals = self._sensor_signals(sampled)
        current = self._build_current(signals)

        # 2. think -- one brain per swarm, so two graphs can meet in the same world
        cols = []
        for s in range(self.n_swarms):
            a = self.assigns[s]
            self.v[s] = self.brains[s].step(self.v[s], a.to_brain(current[:, s]))
            cols.append(a.from_brain(self.v[s], self.n_worlds, self.n_weys))
        v_world = torch.stack(cols, dim=1)
        forward, turn, pump = self._read_motors(v_world)
        self.pump = pump * alive_f

        # tactics: did a wey that is being bitten turn toward the side the bite came from?
        # Heading increases toward the left-hand normal, so turn > 0 means turning left.
        dl, dr = signals["damage_left"], signals["damage_right"]
        eps = 1e-6
        asked = (dl + dr > eps) & ((dl - dr).abs() > eps) & (turn.abs() > eps) & self.alive
        toward = asked & (torch.sign(dl - dr) == torch.sign(turn))
        self.turn_toward_damage += torch.stack(
            (toward.sum().double(), asked.sum().double())
        )

        # 3. act: turn, then move, resisted and deflected by crowding, blocked by walls
        self.heading = (self.heading + wcfg.max_turn * turn * alive_f) % (2 * torch.pi)
        self._points = None
        speed = torch.where(forward >= 0, forward, forward * wcfg.reverse_fraction)
        speed = speed * wcfg.max_speed * alive_f

        body = self.fields[:, self.ch.BODY]
        crowd = sample_nearest(body.unsqueeze(1), self.pos.reshape(self.n_worlds, -1, 2))[:, 0]
        crowd = crowd.reshape(self.n_worlds, self.n_swarms, self.n_weys)
        over = (crowd - wcfg.crowd_threshold).clamp_min(0.0)
        resist = 1.0 - wcfg.crowd_resist * torch.tanh(over)
        speed = speed * resist

        c, s = torch.cos(self.heading), torch.sin(self.heading)
        step = torch.stack((c, s), dim=-1) * speed.unsqueeze(-1)

        grad = gradient(body)  # [Wd, 2, H, W]
        gsamp = sample_nearest(grad, self.pos.reshape(self.n_worlds, -1, 2))
        gsamp = gsamp.reshape(self.n_worlds, 2, self.n_swarms, self.n_weys).permute(0, 2, 3, 1)
        gnorm = gsamp / gsamp.norm(dim=-1, keepdim=True).clamp_min(1e-6)
        push = -gnorm * (wcfg.crowd_push * torch.tanh(over)).unsqueeze(-1) * alive_f.unsqueeze(-1)

        proposed = self.pos + step + push
        proposed = proposed.clamp(1.02, self.side - 1.02)
        blocked = (
            sample_nearest(
                self.fields[:, self.ch.WALL].unsqueeze(1), proposed.reshape(self.n_worlds, -1, 2)
            )[:, 0].reshape(self.n_worlds, self.n_swarms, self.n_weys)
            > 0
        )
        new_pos = torch.where(blocked.unsqueeze(-1), self.pos, proposed)
        moved = (new_pos - self.pos).norm(dim=-1)
        self.pos = new_pos
        self._points = None

        # 4. pay for living and moving (capped at remaining energy, so energy never goes negative)
        cost = (wcfg.metabolic_drain + wcfg.move_cost * moved) * alive_f
        if self.combat_stage >= 2:
            pump_cost = self.cfg.combat.pump_cost * self.pump * alive_f
            paid_pump = torch.minimum(pump_cost, self.energy)
            self.energy -= paid_pump
            self.ledger.pumped += paid_pump.sum(dim=(1, 2)).double()
        paid = torch.minimum(cost, self.energy)
        self.energy -= paid
        self.ledger.drained += paid.sum(dim=(1, 2)).double()

        # 5. eat
        self._eat()

        # 6. hazard
        hz = sample_nearest(
            self.fields[:, self.ch.HAZARD].unsqueeze(1), self.pos.reshape(self.n_worlds, -1, 2)
        )[:, 0].reshape(self.n_worlds, self.n_swarms, self.n_weys)
        burn = torch.minimum(hz * wcfg.hazard_damage * self.alive.to(self.dtype), self.energy)
        self.energy -= burn
        self.ledger.hazard += burn.sum(dim=(1, 2)).double()

        # 7. combat (no-op until milestone 6)
        if self.combat_stage >= 1:
            self._combat()

        # 8. death, then fields
        self._reap()
        self._update_fields()
        self.tick_count += 1
        if self.recorder is not None:
            self.recorder.record(self)

    def _eat(self) -> None:
        wcfg = self.cfg.world
        ch = self.ch
        alive_f = self.alive.to(self.dtype)
        headroom = (wcfg.max_energy - self.energy).clamp_min(0.0)
        rate = wcfg.eat_rate * (self.pump if self.combat_stage >= 2 else 1.0)
        demand = torch.minimum(rate * alive_f, headroom)
        head = self.pos.reshape(self.n_worlds, -1, 2)
        dflat = demand.reshape(self.n_worlds, -1)

        demand_grid = splat(
            torch.zeros(self.n_worlds, self.H, self.W, device=self.device, dtype=self.dtype),
            head,
            dflat,
        )
        food, pellet = self.fields[:, ch.FOOD], self.fields[:, ch.PELLET]
        avail = food + pellet
        scale = scale_to_cap(avail, demand_grid)  # [Wd, H, W], <= 1

        per_wey = sample_nearest(scale.unsqueeze(1), head)[:, 0].reshape(
            self.n_worlds, self.n_swarms, self.n_weys
        )
        intake = demand * per_wey
        self.energy += intake

        taken = torch.minimum(demand_grid, avail)
        share = torch.where(avail > 0, food / avail.clamp_min(1e-12), torch.zeros_like(avail))
        self.fields[:, ch.FOOD] = food - taken * share
        self.fields[:, ch.PELLET] = pellet - taken * (1.0 - share)

    def bite_points(self) -> Tensor:
        """[worlds, swarms, weys, 2] -- the cell just ahead of each head, where the bite lands."""
        off = self.cfg.combat.attack_offset
        c, s = torch.cos(self.heading), torch.sin(self.heading)
        return self.pos + torch.stack((c, s), dim=-1) * off

    def _combat(self) -> None:
        """Stage 1: automatic biting. Stage 2: the deposit is scaled by pump intensity.

        Energy accounting. A victim loses exactly `capped` energy, capped at what it has left. The
        attacking swarm collects that damage back through the adjoint of the attack blur, and
        `transfer_fraction` of what it collects becomes energy. Everything a victim lost that did
        not end up in an attacker is booked as `ledger.inefficiency`, so the books balance whatever
        the geometry does.
        """
        ccfg, wcfg, ch = self.cfg.combat, self.cfg.world, self.ch
        n_sw, Wd, B = self.n_swarms, self.n_worlds, self.n_weys
        alive_f = self.alive.to(self.dtype)

        # 1. deposit, one cell ahead of each head, on the attacker's own attack channel
        deposit = torch.zeros(Wd, n_sw, self.H, self.W, device=self.device, dtype=self.dtype)
        strength = ccfg.attack_strength * alive_f
        if self.combat_stage >= 2:
            strength = strength * self.pump
        bite = self.bite_points()
        for s in range(n_sw):
            splat_into(deposit, s, bite[:, s], strength[:, s])

        # 2. a very light blur, symmetric and normalised so it is its own adjoint
        blurred = blur(deposit, ccfg.attack_blur)
        self.fields[:, ch.ATTACK : ch.ATTACK + n_sw] = blurred

        # 3. every wey samples every attack field at head, mid and tail
        body = self.body_points()  # [Wd, S*B*3, 2]
        sampled = sample_nearest(blurred, body).reshape(Wd, n_sw, n_sw, B, len(BODY_POINTS))
        # sampled[w, src, victim_swarm, wey, point]
        armor = torch.tensor(
            [ccfg.head_armor, 1.0, 1.0], device=self.device, dtype=self.dtype
        ).view(1, 1, 1, 1, 3)
        # damage a victim would take from each attacking swarm, before capping
        raw_per_src = ccfg.damage_k * (sampled * armor)  # [Wd, src, victim, wey, point]
        own = torch.arange(n_sw, device=self.device)
        raw_per_src[:, own, own] = 0.0  # no friendly fire
        raw_point = raw_per_src.sum(dim=1)  # [Wd, victim, wey, point]
        raw_total = raw_point.sum(dim=-1) * alive_f  # [Wd, victim, wey]

        # 4. cap at the victim's remaining energy, then take it
        capped = torch.minimum(raw_total, self.energy)
        scale = torch.where(raw_total > 0, capped / raw_total.clamp_min(1e-12), torch.zeros_like(capped))
        self.energy -= capped
        self.last_damage_taken = capped

        # 5. bite credit. Splat each victim's capped per-point damage, attributed to the attacking
        #    swarm that caused it, onto that swarm's damage-received grid.
        received = torch.zeros_like(deposit)
        share = scale.unsqueeze(-1).unsqueeze(1)  # [Wd, 1, victim, wey, 1]
        capped_per_src = raw_per_src * share * alive_f.unsqueeze(1).unsqueeze(-1)
        self.damage_by_point += capped_per_src.sum(dim=(0, 1, 2, 3)).double()
        for s in range(n_sw):
            splat_into(received, s, body, capped_per_src[:, s].reshape(Wd, -1))
        # 6. the adjoint of step 2 is the same blur, because the kernel is symmetric
        credit = blur(received, ccfg.attack_blur)

        # 7. each attacker collects from its own bite cell, in proportion to its share of the
        #    deposit there
        credit_at = sample_nearest(credit, bite.reshape(Wd, -1, 2)).reshape(Wd, n_sw, n_sw, B)
        deposit_at = sample_nearest(deposit, bite.reshape(Wd, -1, 2)).reshape(Wd, n_sw, n_sw, B)
        mine = torch.arange(n_sw, device=self.device)
        credit_mine = credit_at[:, mine, mine]  # [Wd, swarm, wey]
        deposit_mine = deposit_at[:, mine, mine]
        collected = torch.where(
            deposit_mine > 0,
            credit_mine * strength / deposit_mine.clamp_min(1e-12),
            torch.zeros_like(credit_mine),
        )
        gain = ccfg.transfer_fraction * collected
        headroom = (wcfg.max_energy - self.energy).clamp_min(0.0)
        gain = torch.minimum(gain, headroom) * alive_f
        self.energy += gain
        self.last_damage_dealt = collected
        # everything the victims lost that did not arrive anywhere is the stated inefficiency
        self.ledger.inefficiency += (capped.sum(dim=(1, 2)) - gain.sum(dim=(1, 2))).double()

    def _reap(self) -> None:
        """A wey with no energy dies and leaves a pellet worth its body mass."""
        dying = self.alive & (self.energy <= 0)
        if not bool(dying.any()):
            return
        mass = torch.full_like(self.energy, self.cfg.world.body_mass) * dying.to(self.dtype)
        splat_into(
            self.fields,
            self.ch.PELLET,
            self.pos.reshape(self.n_worlds, -1, 2),
            mass.reshape(self.n_worlds, -1),
        )
        self.alive &= ~dying
        self.energy = self.energy * self.alive.to(self.dtype)

    def _update_fields(self) -> None:
        wcfg, ch = self.cfg.world, self.ch
        # pheromone: deposit, diffuse, decay
        for s in range(self.n_swarms):
            splat_into(
                self.fields,
                ch.pheromone(s),
                self.pos[:, s],
                torch.full_like(self.energy[:, s], wcfg.pheromone_deposit)
                * self.alive[:, s].to(self.dtype),
            )
        lo, hi = ch.PHEROMONE, ch.PHEROMONE + self.n_swarms
        self.fields[:, lo:hi] = diffuse_decay(
            self.fields[:, lo:hi], wcfg.pheromone_diffusion, wcfg.pheromone_decay
        )
        if self.cfg.map.food_regen > 0:
            self._regen_food()
        self._update_body_field()

    def _regen_food(self) -> None:
        """Food re-grows where it already is, which keeps patches where the map put them."""
        food = self.fields[:, self.ch.FOOD]
        norm = food.sum(dim=(1, 2), keepdim=True).clamp_min(1e-6)
        add = food / norm * self.cfg.map.food_regen
        self.fields[:, self.ch.FOOD] = food + add
        self.ledger.spawned += add.sum(dim=(1, 2)).double()

    def _update_body_field(self) -> None:
        wcfg = self.cfg.world
        dens = torch.zeros(self.n_worlds, self.H, self.W, device=self.device, dtype=self.dtype)
        alive3 = (
            self.alive.unsqueeze(-1)
            .expand(-1, -1, -1, len(BODY_POINTS))
            .reshape(self.n_worlds, -1)
        )
        splat(
            dens,
            self.body_points(),
            torch.full_like(alive3, wcfg.body_splat, dtype=self.dtype) * alive3.to(self.dtype),
        )
        self.fields[:, self.ch.BODY] = blur(dens, wcfg.crowd_blur)

    # ---------------------------------------------------------- accounting

    def total_energy(self) -> Tensor:
        """[worlds] -- weys + their body mass + food + pellets, in float64."""
        wcfg, ch = self.cfg.world, self.ch
        alive_f = self.alive.double()
        return (
            self.energy.double().sum(dim=(1, 2))
            + alive_f.sum(dim=(1, 2)) * wcfg.body_mass
            + self.fields[:, ch.FOOD].double().sum(dim=(1, 2))
            + self.fields[:, ch.PELLET].double().sum(dim=(1, 2))
        )

    def energy_ledger_error(self) -> Tensor:
        """[worlds] -- how far the books are from balancing. Must stay at rounding level."""
        return self.total_energy() - (self.start_energy_total + self.ledger.net())

    @property
    def head_damage(self) -> float:
        return float(self.damage_by_point[0])

    @property
    def flank_damage(self) -> float:
        """Damage landed on mid and tail -- the share a flanking tactic produces."""
        return float(self.damage_by_point[1:].sum())

    def neuron_state(self) -> Tensor:
        """[worlds, swarms, weys, neurons] -- the brain state laid back out over the world."""
        return torch.stack(
            [
                self.assigns[s].from_brain(self.v[s], self.n_worlds, self.n_weys)
                for s in range(self.n_swarms)
            ],
            dim=1,
        )

    def swarm_energy(self) -> Tensor:
        """[worlds, swarms] -- surviving energy, the raw material of the match score."""
        return (self.energy * self.alive.to(self.dtype)).sum(dim=2)

    def n_alive(self) -> Tensor:
        return self.alive.sum(dim=2)

    def done(self) -> bool:
        if self.tick_count >= self.cfg.world.max_ticks:
            return True
        if self.n_swarms > 1:
            return bool((self.n_alive() == 0).any(dim=1).all())
        return bool((self.n_alive().sum(dim=1) == 0).all())

    def run(self, ticks: int | None = None) -> "World":
        limit = self.cfg.world.max_ticks if ticks is None else self.tick_count + ticks
        while self.tick_count < limit and not self.done():
            self.tick()
        return self
