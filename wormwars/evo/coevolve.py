"""Two-swarm coevolution: match scheduling, hall of fame, frozen opponent suite.

Three rules from the spec drive the design here.

**Match score** is `(own surviving energy - enemy surviving energy) / total starting energy in the
match`, so a 50-vs-200 result is on the same scale as a 100-vs-100 one.

**Paired evaluation.** Every pairing is played on the same map seed at least twice with the spawn
sides swapped, and lopsided matchups are also played with the headcounts swapped. Within a
generation every candidate faces an equivalent schedule of maps, sizes and opponents -- the schedule
is built once per generation and reused for all candidates, so nobody gets an easier draw.

**A single frozen baseline is an exploitable target**, so absolute progress is measured against a
*suite* of several diverse frozen strains, on held-out world ids, and the suite is versioned.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch

from ..brain import Brain, BrainSpec, Genome
from ..config import Config
from ..interface import Interface
from ..world import World
from .genomes import load_genome, nickname, save_population


@dataclass
class Match:
    """One scheduled fight. `a` indexes the candidate genome, `b` the opponent genome."""

    a: int
    b: int
    world_id: int
    swap_sides: bool
    size_a: int
    size_b: int


@dataclass
class MatchResult:
    score: np.ndarray  # [n_matches] from A's point of view, in [-1, 1]
    energy_a: np.ndarray
    energy_b: np.ndarray
    alive_a: np.ndarray
    alive_b: np.ndarray
    damage_to_flank: float
    damage_to_head: float
    ledger_error: float


def sample_sizes(
    rng: np.random.Generator,
    n: int,
    size_range: tuple[int, int] = (50, 200),
    lopsided_fraction: float = 0.5,
) -> list[tuple[int, int]]:
    """`n` headcount pairs drawn from `size_range`, some of them deliberately lopsided.

    Every pair is used for *all* candidates against *all* opponents, so the schedule stays balanced:
    varying size varies the test, not who gets the easy draw.
    """
    lo, hi = size_range
    out = []
    for _ in range(n):
        a = int(rng.integers(lo, hi + 1))
        b = a if rng.random() >= lopsided_fraction else int(rng.integers(lo, hi + 1))
        out.append((a, b))
    return out


def build_schedule(
    n_candidates: int,
    n_opponents: int,
    world_ids: np.ndarray,
    rng: np.random.Generator,
    sizes: tuple[int, int] | list[tuple[int, int]] = (100, 100),
    lopsided: bool = False,
) -> list[Match]:
    """Every candidate against every opponent, on every world id, from both sides.

    `sizes` is one headcount pair, or a list of pairs to play in addition to each other. With
    `lopsided`, each unequal pair also gets its headcounts swapped, so an advantage from being the
    bigger swarm cancels out.
    """
    size_list = [tuple(sizes)] if isinstance(sizes, tuple) else [tuple(s) for s in sizes]
    matches: list[Match] = []
    for wid in world_ids:
        for size_a, size_b in size_list:
            pairs = [(size_a, size_b)]
            if lopsided and size_a != size_b:
                pairs.append((size_b, size_a))
            for sa, sb in pairs:
                for swap in (False, True):
                    for a in range(n_candidates):
                        for b in range(n_opponents):
                            matches.append(Match(a, b, int(wid), swap, sa, sb))
    rng.shuffle(matches)
    return matches


def play(
    cfg: Config,
    iface: Interface,
    genome_a: Genome,
    genome_b: Genome,
    matches: list[Match],
    run_seed: int,
    device="cpu",
    combat_stage: int = 1,
    chunk_worlds: int = 256,
    recorder=None,
    ticks: int | None = None,
) -> MatchResult:
    """Run a list of matches. Swarm 0 is always genome A, swarm 1 always genome B.

    Sides are exchanged with `swap_sides`, not by exchanging swarm indices, which keeps each swarm
    column's brain batch rectangular and lets A and B be different graphs.
    """
    brains = [Brain(genome_a), Brain(genome_b)]
    out = {k: [] for k in ("score", "ea", "eb", "aa", "ab")}
    flank = head = 0.0
    worst_err = 0.0

    # Arena area scales with headcount to hold starting density constant, and a batch shares one
    # arena -- so matches are grouped by TOTAL headcount before chunking. Mixing a 50v50 with a
    # 200v200 in one batch would give the small match a four-times-emptier arena than it should
    # have. Grouping by the total keeps 50v200 and 200v50 together, which is what paired
    # evaluation of lopsided matchups needs.
    order: list[int] = []
    groups: dict[int, list[int]] = {}
    for i, m in enumerate(matches):
        groups.setdefault(m.size_a + m.size_b, []).append(i)
    batches: list[list[int]] = []
    for total in sorted(groups):
        idx = groups[total]
        for lo in range(0, len(idx), chunk_worlds):
            batches.append(idx[lo : lo + chunk_worlds])

    for batch in batches:
        order.extend(batch)
        part = [matches[i] for i in batch]
        strain_of = torch.tensor([[m.a, m.b] for m in part], dtype=torch.long)
        sizes = torch.tensor([[m.size_a, m.size_b] for m in part], dtype=torch.long)
        swap = torch.tensor([m.swap_sides for m in part], dtype=torch.bool)
        ids = np.array([m.world_id for m in part], dtype=np.int64)
        world = World(
            cfg, iface, brains, strain_of, run_seed=run_seed, world_ids=ids, device=device,
            combat_stage=combat_stage, swarm_sizes=sizes, swap_sides=swap,
        )
        if recorder is not None and lo == 0:
            recorder.attach(world)
        world.run(ticks)

        e = world.swarm_energy()
        start = (sizes.to(e.device).sum(dim=1) * cfg.world.start_energy).to(e.dtype)
        out["score"].append(((e[:, 0] - e[:, 1]) / start).cpu().numpy())
        out["ea"].append(e[:, 0].cpu().numpy())
        out["eb"].append(e[:, 1].cpu().numpy())
        alive = world.n_alive()
        out["aa"].append(alive[:, 0].cpu().numpy())
        out["ab"].append(alive[:, 1].cpu().numpy())
        flank += world.flank_damage
        head += world.head_damage
        worst_err = max(worst_err, world.energy_ledger_error().abs().max().item())

    cat = {k: np.concatenate(v) for k, v in out.items()}
    # results came back grouped by headcount; put them back in the caller's order
    inverse = np.empty(len(order), dtype=np.int64)
    inverse[np.asarray(order)] = np.arange(len(order))
    cat = {k: v[inverse] for k, v in cat.items()}
    return MatchResult(
        score=cat["score"], energy_a=cat["ea"], energy_b=cat["eb"],
        alive_a=cat["aa"], alive_b=cat["ab"],
        damage_to_flank=flank, damage_to_head=head, ledger_error=worst_err,
    )


def candidate_scores(matches: list[Match], score: np.ndarray, n_candidates: int) -> np.ndarray:
    """Mean match score per candidate. Every candidate has the same schedule, so a plain mean is
    already a paired comparison."""
    out = np.zeros(n_candidates)
    counts = np.zeros(n_candidates)
    for m, s in zip(matches, score):
        out[m.a] += s
        counts[m.a] += 1
    return out / np.maximum(counts, 1)


@dataclass
class HallOfFame:
    """Past champions of *this run only*. Runs never exchange anything."""

    capacity: int = 12
    entries: list = field(default_factory=list)  # (generation, Genome[1], nickname)

    def add(self, genome: Genome, index: int, generation: int) -> None:
        self.entries.append((generation, genome.select([index]), nickname(genome, index)))
        if len(self.entries) > self.capacity:
            # thin the middle, keep the oldest and the newest: diversity beats recency
            del self.entries[len(self.entries) // 2]

    def sample(self, k: int, rng: np.random.Generator) -> list:
        if not self.entries:
            return []
        idx = rng.choice(len(self.entries), size=min(k, len(self.entries)), replace=False)
        return [self.entries[int(i)] for i in idx]

    def as_genome(self, entries) -> Genome | None:
        if not entries:
            return None
        gs = [g for _, g, _ in entries]
        base = gs[0]
        return Genome(
            base.spec, base.cfg,
            torch.cat([g.w for g in gs]), torch.cat([g.g for g in gs]),
            torch.cat([g.tau for g in gs]), torch.cat([g.bias for g in gs]),
            None if base.dale_sign is None else torch.cat([g.dale_sign for g in gs]),
        )


SUITE_VERSION = 1


def make_frozen_suite(
    spec: BrainSpec, cfg: Config, n: int = 6, seed: int = 4242, device="cpu"
) -> tuple[Genome, dict]:
    """A versioned suite of diverse frozen opponents.

    Diversity comes from spreading the initialisation, not from evolving them: these are fixed
    reference points, and several of them, because one fixed baseline becomes something evolution
    learns to beat specifically rather than something it gets better against in general.
    """
    gen = torch.Generator(device=device).manual_seed(seed)
    parts = []
    scales = np.linspace(0.5, 2.0, n)
    for i, s in enumerate(scales):
        c = type(cfg.brain)(**{**vars(cfg.brain)})
        c.init_w_scale = cfg.brain.init_w_scale * float(s)
        c.init_bias_std = cfg.brain.init_bias_std * float(s)
        parts.append(Genome.random(spec, c, 1, generator=gen, device=device))
    base = parts[0]
    suite = Genome(
        base.spec, cfg.brain,
        torch.cat([p.w for p in parts]), torch.cat([p.g for p in parts]),
        torch.cat([p.tau for p in parts]), torch.cat([p.bias for p in parts]),
    )
    suite.clamp_()
    meta = {
        "suite_version": SUITE_VERSION,
        "graph": spec.label,
        "n": n,
        "seed": seed,
        "init_scales": [float(x) for x in scales],
        "nicknames": [nickname(suite, i) for i in range(n)],
    }
    return suite, meta


def save_suite(path, suite: Genome, meta: dict) -> Path:
    return save_population(path, suite, **meta)


@dataclass
class CoevoLog:
    generation: int
    best: float
    mean: float
    suite_best: float | None
    suite_mean: float | None
    flank_share: float
    elapsed_s: float
    matches: int
    ledger_error: float
    best_nickname: str


def coevolve(
    cfg: Config,
    iface: Interface,
    spec: BrainSpec,
    run: int,
    run_seed: int,
    device="cpu",
    combat_stage: int = 1,
    out_dir: str | Path | None = None,
    verbose: bool = True,
):
    """One coevolutionary run. Opponents are the current population plus this run's hall of fame;
    absolute progress is measured against the versioned frozen suite on held-out world ids."""
    from .evolve import breed
    from .rollout import SeedPool

    e = cfg.evo
    gen_t = torch.Generator(device=device).manual_seed(run_seed)
    rng = np.random.default_rng(run_seed)
    pop = Genome.random(spec, cfg.brain, e.population, generator=gen_t, device=device)
    pool = SeedPool(cfg, run_seed)
    hof = HallOfFame(capacity=e.hof_capacity)
    suite, suite_meta = make_frozen_suite(spec, cfg, n=e.suite_size, device=device)
    log: list[CoevoLog] = []

    import time

    for g in range(e.generations):
        t0 = time.perf_counter()
        # --- opponents: self-play sample + hall of fame sample ---
        self_idx = rng.choice(e.population, size=min(e.opponents_self, e.population), replace=False)
        opp_parts = [pop.select(list(self_idx))]
        hof_entries = hof.sample(e.opponents_hof, rng)
        hof_genome = hof.as_genome(hof_entries)
        if hof_genome is not None:
            opp_parts.append(hof_genome)
        opponents = Genome(
            spec, cfg.brain,
            torch.cat([p.w for p in opp_parts]), torch.cat([p.g for p in opp_parts]),
            torch.cat([p.tau for p in opp_parts]), torch.cat([p.bias for p in opp_parts]),
        )

        ids = pool.train_ids(g, e.coevo_worlds)
        sizes = (
            sample_sizes(rng, e.coevo_size_pairs, tuple(e.coevo_size_range),
                         e.coevo_lopsided_fraction)
            if e.coevo_vary_sizes
            else tuple(e.coevo_sizes)
        )
        matches = build_schedule(
            e.population, opponents.n_strains, ids, rng,
            sizes=sizes, lopsided=e.coevo_lopsided or e.coevo_vary_sizes,
        )
        res = play(cfg, iface, pop, opponents, matches, run_seed, device, combat_stage,
                   chunk_worlds=e.chunk_worlds)
        fit = candidate_scores(matches, res.score, e.population)
        best_i = int(np.argmax(fit))
        hof.add(pop, best_i, g)

        sb = sm = None
        if g % e.suite_every == 0 or g == e.generations - 1:
            # scored at a fixed headcount so the number means the same thing every generation
            suite_size = tuple(e.suite_sizes) if e.coevo_vary_sizes else tuple(e.coevo_sizes)
            held = build_schedule(
                1, suite.n_strains, pool.holdout[: e.suite_worlds], rng,
                sizes=suite_size, lopsided=False,
            )
            sres = play(cfg, iface, pop.select([best_i]), suite, held, run_seed, device,
                        combat_stage, chunk_worlds=e.chunk_worlds)
            sb = float(sres.score.mean())
            sm = float(np.median(sres.score))

        total_dmg = res.damage_to_flank + res.damage_to_head
        entry = CoevoLog(
            generation=g, best=float(fit.max()), mean=float(fit.mean()),
            suite_best=sb, suite_mean=sm,
            flank_share=float(res.damage_to_flank / max(total_dmg, 1e-9)),
            elapsed_s=time.perf_counter() - t0, matches=len(matches),
            ledger_error=res.ledger_error, best_nickname=nickname(pop, best_i),
        )
        log.append(entry)
        if verbose:
            suite_txt = f" suite {sb:+.3f}" if sb is not None else ""
            print(
                f"  [{spec.label} coevo run{run:02d}] g{g:04d} best {entry.best:+.3f} "
                f"mean {entry.mean:+.3f}{suite_txt} flank {entry.flank_share:.2f} "
                f"{entry.elapsed_s:5.1f}s {entry.best_nickname}"
            )
        if g < e.generations - 1:
            pop = breed(pop, fit, cfg, gen_t)

    if out_dir is not None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        save_population(out / f"{spec.label}-coevo-run{run:02d}.npz", pop, cfg=cfg, run=run,
                        run_seed=run_seed, kind="coevolution")
        save_suite(out / f"{spec.label}-frozen-suite-v{SUITE_VERSION}.npz", suite, suite_meta)
        (out / f"{spec.label}-coevo-run{run:02d}-log.json").write_text(
            json.dumps([vars(x) for x in log], indent=2), encoding="utf-8"
        )
    return pop, hof, log, suite_meta
