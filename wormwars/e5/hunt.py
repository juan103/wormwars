"""Task H: Task N with a living target (docs/E5/E5-0-PLAN.md §2).

One hunter (swarm 0) and one prey (swarm 1) per world, built on E1's Task N configuration with `task = hunt`:

- the hunter spawns exactly as Task N's wey (the map's spawn step places one swarm), and the prey's lives sit at the
  centres of Task N's own target sequence: life k at the first centre after life k - 1's that is at least D - R from
  the hunter's head (for a static prey reached within R that is always the next centre, so a ghost keeps Task N's
  sequence);
- the hunter's food channels carry only the prey's scent, A exp(-d^2 / 2 sigma^2) around the prey's position (its head
  point), truncated as Task N's; the prey's carry the map's food and pellets. The food probes act on both as in Task N;
- capture rules: `ghost` (the prey adds nothing to the body field, so it gives no collision input; capture when the
  hunter's head is within R of the prey's position, checked after the move, as Task N), `reach` (the same, with the
  prey's body), `bite` (combat stage 1, the prey's attack deposit zero; capture when its energy reaches 0). Ghost and
  reach run without combat (stage 0). `prey_body=False` with `bite` is the body probe: bites land (combat samples
  body points, not the body field) but the hunter's collision inputs never see the prey;
- with one hunter and one prey, crowding never acts: two bodies reach a body density of 2/3, below the threshold of
  0.8, and bodies never block movement (`_resolve_move` checks walls only). The pin is a guard; its log reads zero;
- the prey never drains, eats, heals or bites; a pinned prey's moves are refused;
- a capture leaves no pellet: the prey's body mass and remaining energy are booked as removed, and the new life's
  energy and body mass as respawned (`HuntLedger`), in the same tick, so the episode always runs to the horizon.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
from torch import Tensor

from ..world import BODY_POINTS, Ledger, World, sample_bilinear, splat, blur, gaussian_blur, world_seed
from ..world import N_POINTS, P_FRONT_C, P_FRONT_L, P_FRONT_R

RULES = ("ghost", "reach", "bite")
HUNTER, PREY = 0, 1
_HEADING_STREAM = 0x5E7A  # the prey's headings at each life's start, apart from the map's and the targets' streams
CONTACT_RADIUS = 1.5  # contact: the hunter's head within this of any prey body point (logged, never scored)


@dataclass
class HuntLedger(Ledger):
    """Task N's terms plus a capture's two bookings: the removed prey (body mass and remaining energy, a sink) and
    the new life (its energy and body mass, a source)."""

    respawned: Tensor = None
    removed: Tensor = None

    @staticmethod
    def zeros(n_worlds: int, device) -> "HuntLedger":
        z = lambda: torch.zeros(n_worlds, dtype=torch.float64, device=device)  # noqa: E731
        return HuntLedger(z(), z(), z(), z(), z(), z(), z())

    def net(self) -> Tensor:
        return super().net() + self.respawned - self.removed

    def totals(self) -> dict[str, float]:
        return {**super().totals(), "respawned": float(self.respawned.sum()), "removed": float(self.removed.sum())}


E1_TASK = {"sigma": 6.0, "amplitude": 1.0, "radius": 1.5, "separation": 8.0, "max_separation": 0.0, "horizon": 300,
           "wall_clearance": 3.0, "sense_scale_food": 0.35}  # E1's registered task, at its chosen sigma (freeze.json)


def e1_task_n():
    """Task N exactly as E1's gate ran it (scripts/e1.py `config(6.0)`)."""
    from ..e1.task import task_n_config
    t = E1_TASK
    c = task_n_config(sigma=t["sigma"], amplitude=t["amplitude"], radius=t["radius"], separation=t["separation"],
                      max_separation=t["max_separation"], horizon=t["horizon"])
    c.world.target_wall_clearance = t["wall_clearance"]
    c.world.sense_scale_food = t["sense_scale_food"]
    return c


def hunt_config(base=None):
    """Task H from a Task N configuration (E1's, by default): the hunt task, one hunter and one prey."""
    base = e1_task_n() if base is None else base
    if base.world.task != "navigate":
        raise ValueError("Task H is built from a Task N configuration")
    c = base.copy()
    c.world.task = "hunt"
    c.world.n_swarms, c.world.weys_per_swarm = 2, 1
    return c


class HuntWorld(World):
    _hunt_task = True

    def __init__(self, cfg, iface, brain, strain_of, run_seed, world_ids=None, device="cpu", dtype=torch.float32, *,
                 rule: str, prey_energy: float = 12.0, pinned=True, hunter_attack: float = 1.0,
                 prey_body: bool | None = None):
        """`pinned` is one flag for every world, or one per world (E5-1's mixed world)."""
        if cfg.world.task != "hunt":
            raise ValueError("HuntWorld plays the hunt task (wormwars.e5.hunt.hunt_config)")
        if rule not in RULES:
            raise ValueError(f"rule must be one of {RULES}")
        if int(strain_of.shape[1]) != 2:
            raise ValueError("Task H has two swarms: the hunter and the prey")
        self.rule, self.prey_energy = rule, float(prey_energy)
        if np.ndim(pinned) == 0:
            self.pinned, self._pin_worlds = bool(pinned), None
        else:
            flags = np.asarray(pinned, dtype=bool).reshape(-1)
            if flags.size != int(strain_of.shape[0]):
                raise ValueError(f"{flags.size} pin flags for {int(strain_of.shape[0])} worlds")
            self.pinned = bool(flags.all()) if flags.all() or not flags.any() else None  # None: some worlds pinned
            self._pin_worlds = torch.as_tensor(flags, device=device) if self.pinned is None else None
        self.prey_body = (rule != "ghost") if prey_body is None else bool(prey_body)
        if rule == "ghost" and self.prey_body:
            raise ValueError("a ghost has no body (use reach)")
        self._started = False
        super().__init__(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=world_ids, device=device,
                         dtype=dtype, combat_stage=1 if rule == "bite" else 0)
        if self.n_weys != 1:
            raise ValueError("E5-0's Task H has one wey per swarm")
        self.attack_scale = torch.tensor([float(hunter_attack), 0.0], device=self.device, dtype=self.dtype)
        # the ledger: Task N's terms, plus the captures' bookings (all zero so far)
        self.ledger = HuntLedger.zeros(self.n_worlds, self.device)
        # the "constant" probe's value, as Task N's: the mean food level at tick 0 plus the mean scent
        self._food_constant = self.fields[:, self.ch.FOOD].mean(dim=(1, 2)) + self.prey_scent().mean(dim=(1, 2))
        self._started = True

    # -------------------------------------------------------------- setup

    def _spawn_swarms(self) -> int:
        return 1  # the hunter spawns as Task N's wey; the prey is placed below

    def _build_maps(self) -> None:
        super()._build_maps()
        self._build_targets()  # Task N's sequence, from the hunter's spawn, on its own stream
        Wn, K, dev = self.n_worlds, self.target_centres.shape[1], self.device
        self.life = torch.zeros(Wn, dtype=torch.long, device=dev)  # the sequence index of the current life
        self.captures = torch.zeros(Wn, dtype=torch.long, device=dev)
        self._overflow = torch.zeros((), dtype=torch.bool, device=dev)
        heads = np.zeros((Wn, K), dtype=np.float32)
        for w in range(Wn):
            rng = np.random.default_rng([world_seed(self.run_seed, int(self.world_ids[w])), _HEADING_STREAM])
            heads[w] = rng.uniform(0, 2 * np.pi, K)
        self._life_heading = torch.from_numpy(heads).to(dev, self.dtype)
        ar = torch.arange(Wn, device=dev)
        self.pos[:, PREY, 0] = self.target_centres[ar, self.life]
        self.heading[:, PREY, 0] = self._life_heading[ar, self.life]
        self.energy[:, PREY, 0] = self.prey_energy
        self._points = None
        # events, per world and sequence index: the tick a life began and was captured (-1: never), the hunter's and
        # the prey's path lengths during it, the hunter's contact ticks, and the damage the prey took
        self.ev_activation = torch.full((Wn, K), -1, dtype=torch.long, device=dev)
        self.ev_activation[:, 0] = 0
        self.ev_capture = torch.full((Wn, K), -1, dtype=torch.long, device=dev)
        self.ev_hunter_path = torch.zeros(Wn, K, dtype=torch.float64, device=dev)
        self.ev_prey_path = torch.zeros(Wn, K, dtype=torch.float64, device=dev)
        self.ev_contact = torch.zeros(Wn, K, dtype=torch.long, device=dev)
        self.ev_damage = torch.zeros(Wn, K, dtype=torch.float64, device=dev)
        self.pin_push = torch.zeros(Wn, dtype=torch.float64, device=dev)  # the displacement a pinned prey refused
        # the prey's moves the arena limited: clamped at the wall ring or refused by a wall cell (the route check's
        # stall count; with the boundary ring alone, a refusal cannot happen, so this is the clamp)
        self.prey_wall_limited = torch.zeros(Wn, dtype=torch.long, device=dev)
        # the first contact of each life: its tick (-1: none) and the hunter's bearing from the prey's mid point,
        # relative to the prey's heading (0: in front of its head, +-pi: behind its tail; logged, never scored)
        self.ev_first_contact = torch.full((Wn, K), -1, dtype=torch.long, device=dev)
        self.ev_bearing = torch.full((Wn, K), float("nan"), dtype=torch.float64, device=dev)

    # ------------------------------------------------------------- the prey's scent

    def prey_scent(self) -> Tensor:
        """[worlds, H, W]: the live prey's scent around its position, Task N's form and truncation."""
        wcfg = self.cfg.world
        c = self.pos[:, PREY, 0]
        dx = self._grid_x.unsqueeze(0) - c[:, 0].view(-1, 1, 1)
        dy = self._grid_y.unsqueeze(0) - c[:, 1].view(-1, 1, 1)
        reach = math.ceil(3 * wcfg.target_sigma)
        inside = (dx.abs() <= reach) & (dy.abs() <= reach) & self.alive[:, PREY, 0].view(-1, 1, 1)
        g = wcfg.target_amplitude * torch.exp(-(dx * dx + dy * dy) / (2 * wcfg.target_sigma ** 2))
        return torch.where(inside, g, torch.zeros_like(g))

    def _sensor_signals(self, sampled: Tensor) -> dict[str, Tensor]:
        """The `constant` probe replaces the hunter's food channels only: the prey keeps its own food reading."""
        sig = super()._sensor_signals(sampled)
        wcfg = self.cfg.world
        if wcfg.food_probe == "constant":
            if wcfg.food_odour_sigma > 0:
                raise ValueError("the hunt's constant probe assumes no food odour blur")
            food = (sampled[:, self.ch.FOOD] + sampled[:, self.ch.PELLET])[:, PREY]
            pts = {"food_left": P_FRONT_C, "food_right": P_FRONT_C} if wcfg.food_sensing == "mono" else \
                {"food_left": P_FRONT_L, "food_right": P_FRONT_R}
            for k, p in pts.items():
                v = sig[k].clone()
                v[:, PREY] = food[..., p] * wcfg.sense_scale_food
                sig[k] = v
        return sig

    def _wants_food_field(self) -> bool:
        return self.cfg.world.food_probe != "constant"  # the hunter's scent is never in the sampled channels

    def _sensed_food(self, pts: Tensor) -> Tensor:
        """The hunter senses the prey's scent alone; the prey senses food and pellets (blurred as configured). Every
        probe that moves the sample points moves both."""
        wcfg, ch = self.cfg.world, self.ch
        food = self.fields[:, ch.FOOD] + self.fields[:, ch.PELLET]
        if wcfg.food_odour_sigma > 0:
            food = gaussian_blur(food, wcfg.food_odour_sigma)
        if wcfg.food_probe == "mirrored":
            x, y = pts[..., 0], pts[..., 1]
            pts = torch.stack((self.W - 1 - x, self.H - 1 - y), dim=-1)
        elif wcfg.food_probe == "jitter":
            pts = self._jittered(pts)
        both = torch.stack((self.prey_scent(), food), dim=1).contiguous()  # [Wd, 2, H, W]
        s = sample_bilinear(both, pts).reshape(self.n_worlds, 2, self.n_swarms, self.n_weys, N_POINTS)
        return torch.stack((s[:, 0, HUNTER], s[:, 1, PREY]), dim=1)

    # ------------------------------------------------------------- bodies and movement

    def _update_body_field(self) -> None:
        if self.prey_body:
            return super()._update_body_field()
        wcfg = self.cfg.world
        dens = torch.zeros(self.n_worlds, self.H, self.W, device=self.device, dtype=self.dtype)
        present = self.alive.clone()
        present[:, PREY] = False  # no body in the field: no collision input from the prey
        p3 = present.unsqueeze(-1).expand(-1, -1, -1, len(BODY_POINTS)).reshape(self.n_worlds, -1)
        splat(dens, self.body_points(), torch.full_like(p3, wcfg.body_splat, dtype=self.dtype) * p3.to(self.dtype))
        self.fields[:, self.ch.BODY] = blur(dens, wcfg.crowd_blur)

    def _resolve_move(self, proposed: Tensor) -> Tensor:
        new = super()._resolve_move(proposed)
        self.prey_wall_limited += (new[:, PREY, 0] != proposed[:, PREY, 0]).any(-1).long()
        if self.pinned:
            self.pin_push += (new[:, PREY, 0] - self.pos[:, PREY, 0]).norm(dim=-1).double()
            new = new.clone()
            new[:, PREY] = self.pos[:, PREY]
        elif self.pinned is None:  # some worlds pinned: the same arithmetic in those, nothing in the others
            pin = self._pin_worlds
            push = (new[:, PREY, 0] - self.pos[:, PREY, 0]).norm(dim=-1).double()
            self.pin_push += torch.where(pin, push, torch.zeros_like(push))
            new = new.clone()
            new[:, PREY] = torch.where(pin.view(-1, 1, 1), self.pos[:, PREY], new[:, PREY])
        return new

    # ------------------------------------------------------------- captures

    def _post_move(self, moved: Tensor) -> None:
        ar = torch.arange(self.n_worlds, device=self.device)
        self.ev_hunter_path[ar, self.life] += moved[:, HUNTER, 0].double()
        self.ev_prey_path[ar, self.life] += moved[:, PREY, 0].double()
        head = self.pos[:, HUNTER, 0]
        body = self.body_points().reshape(self.n_worlds, self.n_swarms, self.n_weys, len(BODY_POINTS), 2)[:, PREY, 0]
        contact = (body - head.unsqueeze(1)).norm(dim=-1).min(dim=-1).values <= CONTACT_RADIUS
        self.ev_contact[ar, self.life] += contact.long()
        first = contact & (self.ev_first_contact[ar, self.life] < 0)
        if bool(first.any()):
            rel = head - body[:, 1]
            bearing = torch.atan2(rel[:, 1], rel[:, 0]) - self.heading[:, PREY, 0]
            bearing = torch.remainder(bearing + math.pi, 2 * math.pi) - math.pi
            self.ev_first_contact[ar, self.life] = torch.where(first, torch.full_like(self.life, self.tick_count),
                                                               self.ev_first_contact[ar, self.life])
            self.ev_bearing[ar, self.life] = torch.where(first, bearing.double(), self.ev_bearing[ar, self.life])
        if self.rule in ("ghost", "reach"):
            reached = (head - self.pos[:, PREY, 0]).norm(dim=-1) <= self.cfg.world.target_radius
            self._capture(reached)

    def _combat(self) -> None:
        super()._combat()
        ar = torch.arange(self.n_worlds, device=self.device)
        # combat's own capped damage, not an energy difference: near a large measuring energy, float32 would round it
        self.ev_damage[ar, self.life] += self.last_damage_taken[:, PREY, 0].double()

    def _reap(self) -> None:
        if self.rule == "bite":
            self._capture(self.alive[:, PREY, 0] & (self.energy[:, PREY, 0] <= 0))
        super()._reap()  # the hunter cannot die under Task N's energy settings; kept for safety

    def _capture(self, caught: Tensor) -> None:
        """Book and replace every caught prey, in this tick: no pellet; the next life at the first later centre at
        least D - R from the hunter's head."""
        if not bool(caught.any()):
            return
        wcfg, K = self.cfg.world, self.target_centres.shape[1]
        ar = torch.arange(self.n_worlds, device=self.device)
        mass = float(wcfg.body_mass)
        self.ledger.removed += torch.where(caught, self.energy[:, PREY, 0].double() + mass, 0.0)
        self.ev_capture[ar, self.life] = torch.where(caught, torch.full_like(self.life, self.tick_count),
                                                     self.ev_capture[ar, self.life])
        self.captures += caught.long()
        head = self.pos[:, HUNTER, 0]
        nxt = self.life + caught.long()
        min_d = wcfg.target_separation - wcfg.target_radius
        for _ in range(K):
            c = self.target_centres[ar, nxt.clamp_max(K - 1)]
            near = caught & ((c - head).norm(dim=-1) < min_d) & (nxt < K)
            if not bool(near.any()):
                break
            nxt = nxt + near.long()
        self._overflow |= (nxt >= K).any()
        nxt = nxt.clamp_max(K - 1)
        self.life = nxt
        new_pos = self.target_centres[ar, nxt]
        self.pos[:, PREY, 0] = torch.where(caught.unsqueeze(-1), new_pos, self.pos[:, PREY, 0])
        self.heading[:, PREY, 0] = torch.where(caught, self._life_heading[ar, nxt], self.heading[:, PREY, 0])
        self.energy[:, PREY, 0] = torch.where(caught, torch.full_like(self.energy[:, PREY, 0], self.prey_energy),
                                              self.energy[:, PREY, 0])
        self.ledger.respawned += torch.where(caught, torch.full_like(self.ledger.respawned, self.prey_energy + mass),
                                             torch.zeros_like(self.ledger.respawned))
        self.ev_activation[ar, nxt] = torch.where(caught, torch.full_like(nxt, self.tick_count + 1),
                                                  self.ev_activation[ar, nxt])
        self._points = None
        brain = self.brains[PREY]
        if hasattr(brain, "reset_worlds"):  # a fresh policy or brain state for the new life
            self.v[PREY] = brain.reset_worlds(self.v[PREY], caught, self)

    def done(self) -> bool:
        return self.tick_count >= self.cfg.world.max_ticks

    def hunt_events(self) -> dict[str, np.ndarray]:
        """The event table, [worlds, sequence index] each, and the episode's counts, [worlds]."""
        if bool(self._overflow):
            raise RuntimeError("a world used every centre of its sequence: raise target_sequence_length")
        c = self.target_centres.cpu().numpy()
        return {"activation_tick": self.ev_activation.cpu().numpy(), "capture_tick": self.ev_capture.cpu().numpy(),
                "hunter_path": self.ev_hunter_path.cpu().numpy(), "prey_path": self.ev_prey_path.cpu().numpy(),
                "contact_ticks": self.ev_contact.cpu().numpy(), "damage": self.ev_damage.cpu().numpy(),
                "first_contact_tick": self.ev_first_contact.cpu().numpy(), "bearing": self.ev_bearing.cpu().numpy(),
                "centre_x": c[..., 0], "centre_y": c[..., 1]}
