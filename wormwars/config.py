"""All tunable numbers live here or in `configs/*.yaml`. No magic numbers in the simulation code.

Every dataclass is plain data: no behaviour, no defaults that depend on other sections. YAML files
override fields by name; an unknown field is an error, not a silently ignored typo.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "configs" / "default.yaml"

CHEM_DIRECTIONS = ("pre_to_post", "post_to_pre")
# What anything saved without an explicit direction actually ran with (DECISIONS.md D031).
LEGACY_CHEM_DIRECTION = "post_to_pre"


@dataclass
class BrainConfig:
    """The leaky rate model and the bounds evolution must respect.

    Time is measured in world ticks: `tau = 1.0` means a neuron relaxes with a one-tick time
    constant. `substeps` brain updates are taken per tick, each of size `dt = 1 / substeps`.
    """

    substeps: int = 8
    # hard bounds, enforced by clamping after every mutation
    tau_min: float = 0.5
    tau_max: float = 20.0
    w_max: float = 3.0
    g_max: float = 2.0
    b_max: float = 2.0
    # initialisation
    init_w_scale: float = 0.2  # |W| = init_w_scale * anat / mean(anat), random sign
    init_g_scale: float = 0.05  # G = init_g_scale * anat / mean(anat), >= 0
    init_bias_std: float = 0.5
    init_tau_log_uniform: bool = True
    dale: bool = False  # one sign per presynaptic neuron
    # input
    input_gain: float = 1.0
    input_max: float = 5.0  # |I| bound, so the analytic activity bound is finite
    # "pre_to_post": signal flows from presynaptic to postsynaptic neuron, as in the animal.
    # "post_to_pre": the reversed update experiment 01 actually ran (DECISIONS.md D031). It exists
    # only so that experiment 01 reproduces exactly; never choose it for anything new.
    chem_direction: str = "pre_to_post"

    @property
    def dt(self) -> float:
        return 1.0 / self.substeps


@dataclass
class WorldConfig:
    """The arena, the bodies and the energy economy.

    Lengths are in cells, angles in radians, time in ticks. Arena size is not here: it is derived
    from headcount at construction so that starting density stays constant across swarm sizes.
    """

    n_swarms: int = 1
    weys_per_swarm: int = 20
    max_ticks: int = 600
    cells_per_wey: float = 24.0  # arena area / total weys, held constant across headcounts
    min_side: int = 24

    # --- body and movement ---
    body_length: float = 2.4  # head to tail; mid point sits halfway (tuned by the flank tests)
    max_speed: float = 0.35  # cells per tick at full forward drive
    reverse_fraction: float = 0.4  # backward drive is this much of forward
    max_turn: float = 0.30  # radians per tick at full turn drive
    # The read-out is a difference of means of tanh, which is small near rest: a random genome
    # produces |forward| ~ 0.10 and |turn| ~ 0.16 (measured). These gains map that onto a usable
    # fraction of full speed before the [-1, 1] clamp, so an unevolved population actually moves
    # and selection has behaviour to act on. See DECISIONS.md D014.
    forward_gain: float = 4.0
    turn_gain: float = 2.0

    # --- energy ---
    start_energy: float = 12.0
    max_energy: float = 40.0
    body_mass: float = 6.0  # becomes a corpse pellet on death; exists from tick 0
    metabolic_drain: float = 0.035  # per tick; over max_ticks this exceeds start_energy
    move_cost: float = 0.020  # per cell travelled
    hazard_damage: float = 0.25  # per tick at full hazard intensity
    eat_rate: float = 0.60  # maximum intake per tick per wey

    # --- fields ---
    pheromone_deposit: float = 1.0
    pheromone_decay: float = 0.93
    pheromone_diffusion: float = 0.35
    sense_scale_food: float = 0.35  # field value -> injected current
    sense_scale_pheromone: float = 0.35
    sense_scale_hazard: float = 2.0
    sense_scale_damage: float = 2.0
    sense_scale_collision: float = 2.0

    # --- crowding ---
    body_splat: float = 1.0  # deposited per body point
    crowd_threshold: float = 0.8  # density above which movement is resisted
    crowd_resist: float = 0.6  # fraction of speed removed at full crowding
    crowd_push: float = 0.10  # cells per tick pushed down the density gradient
    crowd_blur: int = 1


@dataclass
class MapConfig:
    """Per-world randomisation. Every field is a range, sampled independently per world."""

    food_patches: tuple[int, int] = (3, 6)
    food_patch_radius: tuple[float, float] = (2.5, 5.0)
    food_per_patch: tuple[float, float] = (70.0, 160.0)
    food_centre_bias: float = 0.62  # patches land within this fraction of the arena half-extent
    hazard_patches: tuple[int, int] = (1, 4)
    hazard_radius: tuple[float, float] = (2.0, 4.0)
    hazard_strength: tuple[float, float] = (0.5, 1.0)
    hazard_spawn_clearance: float = 6.0  # hazards are kept this far from a spawn box centre
    spawn_margin: float = 3.0  # weys start this far inside the wall
    spawn_spread: float = 0.28  # spawn box half-width, as a fraction of the arena
    food_regen: float = 0.0  # energy added per patch per tick (a ledger source when nonzero)
    # Arena area scales with headcount to hold starting *density* constant, so food has to scale
    # with it in two ways or a big match is not a scaled-up small one:
    #   amount per patch x (total_weys / reference)        -> same food per wey
    #   patch radius     x sqrt(total_weys / reference)    -> same fraction of the arena covered
    # Hazard radii scale the same way. At the development size (one swarm of 20) both factors are
    # exactly 1, so nothing measured at 20 weys changes.
    food_scales_with_headcount: bool = True
    food_reference_weys: int = 20


@dataclass
class CombatConfig:
    """Stage 1 is automatic biting; stage 2 gates the bite and the bite-sized mouthful on pump.

    The geometry numbers here are the ones the scripted flank tests tune: they decide whether being
    T-boned is actually punishing.
    """

    attack_strength: float = 1.0  # deposited into the cell ahead of the head
    attack_offset: float = 0.9  # how far ahead of the head the deposit lands, in cells
    attack_blur: int = 1  # "a very light blur"
    damage_k: float = 0.55  # damage per unit of sampled enemy attack
    head_armor: float = 0.25  # the head samples count this much
    transfer_fraction: float = 0.5  # of capped damage, this much reaches the attacker
    # The flank targets the scripted-geometry tests enforce (DECISIONS.md D019).
    max_flank_payback: float = 0.10  # a T-boned or rear-bitten wey may deal back at most this
    max_head_on_asymmetry: float = 1.5  # head-on must be within this factor of an even trade
    pump_cost: float = 0.10  # energy per tick at full pump (stage 2)


@dataclass
class MutationConfig:
    w_sigma: float = 0.08
    g_sigma: float = 0.04
    tau_sigma: float = 0.15  # multiplicative, in log space
    bias_sigma: float = 0.05
    p_mutate: float = 1.0  # fraction of parameters perturbed per offspring


@dataclass
class EvoConfig:
    """One evolutionary run.

    Seed pools are disjoint by construction: `train` world ids drive selection, `holdout` ids are
    never used for selection and are where absolute progress is measured.
    """

    population: int = 32
    generations: int = 40
    elites: int = 3
    truncation: int = 8  # the top this many strains are the parents
    worlds_per_strain: int = 6  # evaluation worlds per strain per generation
    holdout_worlds: int = 24
    islands: int = 1
    migrate_every: int = 10  # generations between migrations (islands only)
    migrants: int = 1
    chunk_worlds: int = 512  # rollouts are split into chunks of at most this many worlds
    train_seed_base: int = 0  # world ids 0 .. train_seed_span-1
    train_seed_span: int = 1_000_000
    holdout_seed_base: int = 900_000_000  # disjoint from the training span
    eval_ticks: int = 0  # 0 means use world.max_ticks

    # --- coevolution (milestone 7) ---
    opponents_self: int = 3  # opponents drawn from the current population
    opponents_hof: int = 2  # opponents drawn from this run's hall of fame
    coevo_worlds: int = 2  # map seeds per generation (each played from both sides)
    coevo_sizes: tuple[int, int] = (40, 40)  # used when coevo_vary_sizes is false
    coevo_lopsided: bool = False  # also play headcount-swapped copies
    # Standard fights are 100v100; across worlds sizes vary in this range, including lopsided
    # matchups. Arena area scales with headcount so starting density is unchanged.
    coevo_vary_sizes: bool = False
    coevo_size_range: tuple[int, int] = (50, 200)
    coevo_size_pairs: int = 2  # distinct headcount pairs per generation
    coevo_lopsided_fraction: float = 0.5
    hof_capacity: int = 12
    suite_every: int = 5  # generations between frozen-suite evaluations
    # Headcount the frozen suite is played at. When sizes vary during training, the suite must be
    # scored somewhere INSIDE the training distribution, or "progress" is really a measurement of
    # generalisation to a size never trained on. 100v100 is the spec's standard fight.
    suite_sizes: tuple[int, int] = (100, 100)
    suite_size: int = 6
    suite_worlds: int = 8


@dataclass
class Config:
    brain: BrainConfig = field(default_factory=BrainConfig)
    world: WorldConfig = field(default_factory=WorldConfig)
    map: MapConfig = field(default_factory=MapConfig)
    combat: CombatConfig = field(default_factory=CombatConfig)
    mutation: MutationConfig = field(default_factory=MutationConfig)
    evo: EvoConfig = field(default_factory=EvoConfig)

    @classmethod
    def from_yaml(cls, path: str | Path | None = None) -> "Config":
        path = Path(path) if path is not None else DEFAULT_CONFIG
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls.from_dict(raw)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Config":
        kwargs: dict[str, Any] = {}
        sections = {f.name: f for f in dataclasses.fields(cls)}
        unknown = set(raw) - set(sections)
        if unknown:
            raise ValueError(f"unknown config section(s): {sorted(unknown)}")
        for name, f in sections.items():
            sub = raw.get(name) or {}
            section_cls = f.type if isinstance(f.type, type) else _resolve(f)
            known = {g.name for g in dataclasses.fields(section_cls)}
            bad = set(sub) - known
            if bad:
                raise ValueError(f"unknown field(s) in config section {name!r}: {sorted(bad)}")
            # YAML has no tuples, so a range written as [2.5, 5.0] arrives as a list. Coerce it,
            # or a config loaded from YAML would not be interchangeable with the defaults.
            sub = dict(sub)
            if name == "brain" and "chem_direction" not in sub:
                # Every config written before the direction fix lacks this field, and every one of
                # them ran with chemical synapses reversed. Read them as what they were, so that
                # experiment 01's bundles reproduce (DECISIONS.md D031). New configs state it.
                sub["chem_direction"] = LEGACY_CHEM_DIRECTION
            for g in dataclasses.fields(section_cls):
                if g.name in sub and str(g.type).startswith("tuple") and isinstance(sub[g.name], list):
                    sub[g.name] = tuple(sub[g.name])
            kwargs[name] = section_cls(**sub)
        return cls(**kwargs)

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    def copy(self) -> "Config":
        """A deep copy. `Config(**cfg.to_dict())` does NOT work: asdict flattens the sections to
        plain dicts, so the sections have to be rebuilt."""
        return Config.from_dict(dataclasses.asdict(self))


def _resolve(f: dataclasses.Field) -> type:
    # dataclass field types are strings under `from __future__ import annotations`
    return globals()[f.type]
