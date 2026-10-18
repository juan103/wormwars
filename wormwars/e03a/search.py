"""The search over X's wiring (experiments/03a-self-consistency/DESIGN.md v7.1 §6; DRAFT.md "Search algorithm").

**What a search is given** (the information boundary, §8): the number of candidates, X's true numbers of partners per
connection type, whether X has a chemical self-connection, and the brain configuration. Never which candidates are
partners: `Problem` holds no truth, and every free search is built from a `Problem` alone. Original- and
random-partner refits are handed their partner sets and never move them.

**Initialisation, independent of the hidden partners:** partners uniformly at random with the true counts (free
searches); every chemical weight at magnitude `init_w_scale` with a random sign, every gap conductance at
`init_g_scale`, τ and bias from the pinned initial distributions (`Genome.random`'s). Random numbers are drawn for
every candidate whatever the partners, so the draws do not depend on them.

**Mutations,** one kind per offspring, by the configured probabilities:
- *move*: 1 to `max_moves` partner moves, each in a type chosen in proportion to the movable counts (a type with no
  partner or every candidate a partner cannot move); one connected candidate gives its edge, weight kept, to one
  unconnected candidate, so the counts never change and a gap move changes both sides at once;
- *weights*: Gaussian perturbation of X's present weights and conductances (and the self-connection), clamped;
- *tau_bias*: τ multiplicatively and the bias additively, clamped.
Refits disable moves; their probability mass goes to the other two in proportion.

**Replica exchange** (the draft's, unchanged): R replicas at fixed temperatures, ascending; each produces λ offspring
per generation, and the current states and every offspring are scored on the same worlds (common random numbers).
The best offspring (the first, on ties) replaces the current state if it scores at least as well, else with
probability exp((s_o − s_c) / T). Every `swap_every` generations, alternating even and odd neighbour pairs, replicas m
and m + 1 swap with probability min(1, exp((1/T_m − 1/T_{m+1}) (s_{m+1} − s_m))). The result is the coldest replica's
final state. It is a tempered optimiser, not an equilibrium sampler. With constant fitness (the no-task control) every
best offspring is accepted and every swap made, by these same rules, so no episode is simulated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import torch

from ..brain import Genome
from ..e04a.evolve import moved
from .reinsert import TYPES, Reinsertion, XState

SEARCH_STREAM = 0x03A5EA  # the search worlds' stream key, with the search seed and generation
ACCEPT_STREAM = 0x03AACC
CONFIRM_STREAM = 0x03AC0F  # a confirmed search's confirmation worlds (D314)


@dataclass(frozen=True)
class Problem:
    """Everything a free search may know about X."""

    K: int
    counts: dict  # type -> true number of partners
    self_loop: bool

    def __post_init__(self):
        if set(self.counts) != set(TYPES):
            raise ValueError(f"counts must name {TYPES}")
        if any(not 0 <= int(v) <= self.K for v in self.counts.values()):
            raise ValueError("a count outside [0, K]")

    def movable(self) -> list:
        return [t for t in TYPES if 0 < int(self.counts[t]) < self.K]


def problem_of(reins: Reinsertion, counts: dict) -> Problem:
    return Problem(reins.K, {k: int(counts[k]) for k in TYPES}, reins.self_loop)


@dataclass(frozen=True)
class SearchConfig:
    replicas: int = 4
    offspring: int = 8
    generations: int = 100
    swap_every: int = 5
    temperatures: tuple = (0.05, 0.1, 0.2, 0.4)  # tuned in pilot-dev, then frozen (§6)
    p_move: float = 1 / 3
    p_weights: float = 1 / 3
    p_tau_bias: float = 1 / 3
    max_moves: int = 1  # partner moves per move offspring: uniform in 1..max_moves
    worlds: int = 16
    shaping: float = 0.0  # the search signal's progress bonus c; every reported score stays the raw count

    def __post_init__(self):
        if len(self.temperatures) != self.replicas or list(self.temperatures) != sorted(self.temperatures):
            raise ValueError("one temperature per replica, ascending")
        if min(self.temperatures) <= 0:
            raise ValueError("temperatures must be positive")
        p = (self.p_move, self.p_weights, self.p_tau_bias)
        if min(p) < 0 or abs(sum(p) - 1) > 1e-9:
            raise ValueError("mutation probabilities must be non-negative and sum to 1")
        if not 0.0 <= self.shaping < 1.0:
            raise ValueError("shaping must be in [0, 1)")
        if self.max_moves < 1:
            raise ValueError("max_moves must be at least 1")

    def as_dict(self) -> dict:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


def _signs(gen, *shape):
    return torch.where(torch.rand(*shape, generator=gen) < 0.5, -1.0, 1.0)


def initial_states(problem: Problem, n: int, bcfg, gen: torch.Generator, partners: dict | None = None) -> XState:
    """n initial states on the CPU. `partners` (boolean arrays over the candidates, per type) fixes the partner sets
    (the refits); otherwise each state's partners are drawn uniformly with the true counts."""
    K = problem.K
    masks = {}
    for t in TYPES:
        if partners is None:
            m = torch.zeros(n, K, dtype=torch.bool)
            for s in range(n):
                m[s, torch.randperm(K, generator=gen)[:int(problem.counts[t])]] = True
        else:
            p = torch.as_tensor(np.asarray(partners[t], dtype=bool))
            if p.shape != (K,) or int(p.sum()) != int(problem.counts[t]):
                raise ValueError(f"partners for {t!r} do not have the true count")
            m = p.unsqueeze(0).repeat(n, 1)
        masks[t] = m
    w_in = bcfg.init_w_scale * _signs(gen, n, K)
    w_out = bcfg.init_w_scale * _signs(gen, n, K)
    g = torch.full((n, K), float(bcfg.init_g_scale))
    if bcfg.init_tau_log_uniform:
        lo, hi = np.log(bcfg.tau_min), np.log(bcfg.tau_max)
        tau = torch.exp(torch.rand(n, generator=gen) * (hi - lo) + lo)
    else:
        tau = torch.rand(n, generator=gen) * (bcfg.tau_max - bcfg.tau_min) + bcfg.tau_min
    bias = torch.randn(n, generator=gen) * bcfg.init_bias_std
    w_self = bcfg.init_w_scale * _signs(gen, n)
    st = XState(masks["in"], masks["out"], masks["gap"], w_in, w_out, g, tau, bias, w_self)
    return clamp_(st, bcfg)


def clamp_(st: XState, bcfg) -> XState:
    st.w_in.clamp_(-bcfg.w_max, bcfg.w_max)
    st.w_out.clamp_(-bcfg.w_max, bcfg.w_max)
    st.w_self.clamp_(-bcfg.w_max, bcfg.w_max)
    st.g.clamp_(0.0, bcfg.g_max)
    st.tau.clamp_(bcfg.tau_min, bcfg.tau_max)
    st.bias.clamp_(-bcfg.b_max, bcfg.b_max)
    return st


OPS = ("move", "weights", "tau_bias")


def propose(current: XState, problem: Problem, scfg: SearchConfig, bcfg, mcfg, gen: torch.Generator,
            moves: bool = True) -> tuple[XState, list]:
    """λ offspring of each current state, in replica order, on the CPU; and each offspring's mutation kind."""
    R, lam, K = current.n, scfg.offspring, problem.K
    p = np.array([scfg.p_move if moves else 0.0, scfg.p_weights, scfg.p_tau_bias])
    movable = problem.movable() if moves else []
    if not movable:
        p[0] = 0.0
    if p.sum() <= 0:
        raise ValueError("no mutation is possible")
    cum = np.cumsum(p / p.sum())
    off = current.select(np.repeat(np.arange(R), lam)).to("cpu")
    kinds = []
    for s in range(off.n):
        u = float(torch.rand((), generator=gen))
        op = OPS[int(np.searchsorted(cum, u, side="right").clip(0, 2))]
        kinds.append(op)
        if op == "move":
            weights = np.array([problem.counts[t] for t in movable], dtype=float)
            n_moves = 1 + int(torch.randint(scfg.max_moves, (), generator=gen))
            for _ in range(n_moves):
                t = movable[int(np.searchsorted(np.cumsum(weights / weights.sum()),
                                                float(torch.rand((), generator=gen)), side="right").clip(0, len(movable) - 1))]
                m, w = off.masks()[t], off.weights()[t]
                on = torch.nonzero(m[s]).flatten()
                offc = torch.nonzero(~m[s]).flatten()
                a = on[int(torch.randint(len(on), (), generator=gen))]
                b = offc[int(torch.randint(len(offc), (), generator=gen))]
                m[s, a], m[s, b] = False, True
                w[s, b] = w[s, a]
                w[s, a] = 0.0
        elif op == "weights":
            e_in = torch.randn(K, generator=gen) * mcfg.w_sigma
            e_out = torch.randn(K, generator=gen) * mcfg.w_sigma
            e_g = torch.randn(K, generator=gen) * mcfg.g_sigma
            e_self = torch.randn((), generator=gen) * mcfg.w_sigma
            off.w_in[s] += e_in * off.m_in[s]
            off.w_out[s] += e_out * off.m_out[s]
            off.g[s] += e_g * off.m_gap[s]
            if problem.self_loop:
                off.w_self[s] += e_self
        else:
            off.tau[s] *= torch.exp(torch.randn((), generator=gen) * mcfg.tau_sigma)
            off.bias[s] += torch.randn((), generator=gen) * mcfg.bias_sigma
    return clamp_(off, bcfg), kinds


def search_worlds(seed: int, generation: int, n: int, base: int, span: int) -> np.ndarray:
    """One search's worlds for one generation, shared by every state it scores then: a function of (search seed,
    generation) only."""
    rng = np.random.default_rng([int(seed), int(generation), SEARCH_STREAM])
    return base + rng.integers(0, span, size=n)


@dataclass
class Trace:
    """Per generation: the current scores after replacement, which replicas accepted, the accepted offspring's kind,
    swap attempts and acceptances, and the coldest replica's partner masks (for Q and turnover, computed by callers who
    hold the truth)."""

    scores: list = field(default_factory=list)
    accepted: list = field(default_factory=list)
    accepted_kind: list = field(default_factory=list)
    swaps: list = field(default_factory=list)  # (pair index m, accepted)
    cold_masks: list = field(default_factory=list)  # after generation g + 1, at index g
    initial_cold: dict | None = None  # before the first generation
    # the paired noise the acceptance rule sees: per generation, the mean and SD over every offspring of (offspring
    # score - its replica's current score), both on that generation's worlds (Fable, round 2)
    paired: list = field(default_factory=list)
    # a confirmed search only (D314): per generation and replica, [selection worlds, confirmation worlds] score of the
    # best offspring minus the current state's
    confirmed: list = field(default_factory=list)


class ReplicaExchange:
    """One search. `partners` set: a refit (moves disabled). `ask()` gives the states to score and their worlds;
    `tell(scores)` advances one generation."""

    def __init__(self, problem: Problem, scfg: SearchConfig, bcfg, mcfg, seed: int, *, partners: dict | None = None,
                 world_base: int = 0, world_span: int = 1, label: str = "", snapshot_at: tuple = ()):
        self.problem, self.scfg, self.bcfg, self.mcfg = problem, scfg, bcfg, mcfg
        self.seed, self.label = int(seed), label
        self.refit = partners is not None
        self.gen = torch.Generator().manual_seed(self.seed)
        self.rng = np.random.default_rng([self.seed, ACCEPT_STREAM])
        self.current = initial_states(problem, scfg.replicas, bcfg, self.gen, partners)
        self.world_base, self.world_span = int(world_base), int(world_span)
        self.generation = 0
        self.trace = Trace()
        self.trace.initial_cold = {t: self.current.masks()[t][0].clone() for t in TYPES}
        self.snapshot_at = tuple(int(g) for g in snapshot_at)
        self.snapshots: dict = {}  # generation -> the coldest replica's state after it
        self._pending = None

    @property
    def done(self) -> bool:
        return self.generation >= self.scfg.generations

    def worlds(self) -> np.ndarray:
        return search_worlds(self.seed, self.generation, self.scfg.worlds, self.world_base, self.world_span)

    def ask(self) -> tuple[XState, np.ndarray]:
        if self.done:
            raise RuntimeError("the search has finished")
        off, kinds = propose(self.current, self.problem, self.scfg, self.bcfg, self.mcfg, self.gen,
                             moves=not self.refit)
        self._pending = (off, kinds)
        return XState.cat([self.current, off]), self.worlds()

    def tell(self, scores) -> None:
        off, kinds, s_cur, s_off = self._scored(scores)
        R, lam, T = self.scfg.replicas, self.scfg.offspring, self.scfg.temperatures
        take, acc, acc_kind = [], [], []
        for r in range(R):
            o = int(np.argmax(s_off[r]))  # the first best, on ties
            u = self.rng.random()
            d = s_off[r, o] - s_cur[r]
            ok = bool(d >= 0 or u < np.exp(d / T[r]))
            acc.append(ok)
            acc_kind.append(kinds[r * lam + o] if ok else None)
            take.append(R + r * lam + o if ok else r)
            if ok:
                s_cur[r] = s_off[r, o]
        self._advance(XState.cat([self.current, off]), take, s_cur, acc, acc_kind)

    def _scored(self, scores):
        """The pending offspring, their kinds, and the generation's scores split into current [R] and offspring
        [R, λ]; the paired spread goes into the trace."""
        if self._pending is None:
            raise RuntimeError("tell() without ask()")
        off, kinds = self._pending
        self._pending = None
        R, lam = self.scfg.replicas, self.scfg.offspring
        scores = np.asarray(scores, dtype=np.float64).reshape(-1)
        if scores.shape != (R + R * lam,) or not np.isfinite(scores).all():
            raise ValueError(f"expected {R + R * lam} finite scores")
        s_cur = scores[:R].copy()
        s_off = scores[R:].reshape(R, lam)
        diff = s_off - s_cur[:, None]
        self.trace.paired.append([float(diff.mean()), float(diff.std())])
        return off, kinds, s_cur, s_off

    def _advance(self, everything: XState, take: list, s_cur, acc: list, acc_kind: list) -> None:
        """The replacements (`take` indexes `everything`), the swaps on `s_cur`, the trace, the next generation."""
        R, T = self.scfg.replicas, self.scfg.temperatures
        self.current = everything.select(take)
        swaps = []
        if (self.generation + 1) % self.scfg.swap_every == 0:
            parity = ((self.generation + 1) // self.scfg.swap_every) % 2
            order = list(range(R))
            for m in range(parity, R - 1, 2):
                u = self.rng.random()
                a = (1.0 / T[m] - 1.0 / T[m + 1]) * (s_cur[m + 1] - s_cur[m])
                ok = bool(a >= 0 or u < np.exp(a))
                swaps.append((m, ok))
                if ok:
                    order[m], order[m + 1] = order[m + 1], order[m]
                    s_cur[m], s_cur[m + 1] = s_cur[m + 1], s_cur[m]
            self.current = self.current.select(order)
        self.trace.scores.append(s_cur.tolist())
        self.trace.accepted.append(acc)
        self.trace.accepted_kind.append(acc_kind)
        self.trace.swaps.append(swaps)
        self.trace.cold_masks.append({t: self.current.masks()[t][0].clone() for t in TYPES})
        self.generation += 1
        if self.generation in self.snapshot_at:
            self.snapshots[self.generation] = self.result()

    def result(self) -> XState:
        """The coldest replica's current state."""
        return self.current.select([0])


class ConfirmedExchange(ReplicaExchange):
    """D314's variant (Fable, Astra, after pilot-dev): each generation takes two evaluations. First the current states
    and their offspring on the generation's worlds, as in `ReplicaExchange`; each replica's best offspring (the first,
    on ties) is its candidate. Then each current state and its candidate on `confirm_worlds` fresh worlds (a function
    of the search seed and the generation, on their own stream), where the acceptance rule and the swaps are applied to
    the confirmation scores. A candidate with no true gain is then rejected about half the time at a cold temperature,
not always: the confirmation is a fresh Metropolis comparison, not a statistical guarantee of improvement (Fable,
Astra)."""

    def __init__(self, *args, confirm_worlds: int, **kw):
        super().__init__(*args, **kw)
        if int(confirm_worlds) < 1:
            raise ValueError("confirm_worlds must be at least 1")
        self.confirm_n = int(confirm_worlds)
        self._confirm = None  # between the two evaluations: the candidates and their selection differences

    def confirmation_worlds(self) -> np.ndarray:
        rng = np.random.default_rng([self.seed, self.generation, CONFIRM_STREAM])
        return self.world_base + rng.integers(0, self.world_span, size=self.confirm_n)

    def ask(self) -> tuple[XState, np.ndarray]:
        if self._confirm is None:
            return super().ask()
        if self._confirm["asked"]:
            raise RuntimeError("ask() twice without tell()")
        self._confirm["asked"] = True
        return XState.cat([self.current, self._confirm["candidates"]]), self.confirmation_worlds()

    def tell(self, scores) -> None:
        R, lam, T = self.scfg.replicas, self.scfg.offspring, self.scfg.temperatures
        if self._confirm is None:
            off, kinds, s_cur, s_off = self._scored(scores)
            best = [int(np.argmax(s_off[r])) for r in range(R)]
            self._confirm = {"candidates": off.select([r * lam + o for r, o in enumerate(best)]),
                             "kinds": [kinds[r * lam + o] for r, o in enumerate(best)],
                             "selection": [float(s_off[r, o] - s_cur[r]) for r, o in enumerate(best)],
                             "asked": False}
            return
        if not self._confirm["asked"]:
            raise RuntimeError("tell() without ask()")
        c = self._confirm
        self._confirm = None
        scores = np.asarray(scores, dtype=np.float64).reshape(-1)
        if scores.shape != (2 * R,) or not np.isfinite(scores).all():
            raise ValueError(f"expected {2 * R} finite confirmation scores")
        s_cur, s_cand = scores[:R].copy(), scores[R:]
        take, acc, acc_kind, conf = [], [], [], []
        for r in range(R):
            u = self.rng.random()
            d = s_cand[r] - s_cur[r]
            ok = bool(d >= 0 or u < np.exp(d / T[r]))
            acc.append(ok)
            acc_kind.append(c["kinds"][r] if ok else None)
            take.append(R + r if ok else r)
            conf.append([c["selection"][r], float(d)])
            if ok:
                s_cur[r] = s_cand[r]
        self.trace.confirmed.append(conf)
        self._advance(XState.cat([self.current, c["candidates"]]), take, s_cur, acc, acc_kind)


def run_lockstep(searches: list, evaluate, check=None, after=None) -> None:
    """Advance every search to its end together: each generation, every search's states are scored in one call,
    `evaluate([(search, states, worlds), ...]) -> [scores per search]`. `check()` runs before each call (the cap);
    `after(searches)` runs after each call, so a caller can keep what has finished. A `ConfirmedExchange` takes two
    calls per generation (Astra)."""
    while not all(s.done for s in searches):
        live = [s for s in searches if not s.done]
        asks = [(s, *s.ask()) for s in live]
        if check is not None:
            check()
        scores = evaluate(asks)
        for s, sc in zip(live, scores):
            s.tell(sc)
        if after is not None:
            after(searches)


def no_task(asks) -> list:
    """The no-task control's fitness: identically zero, so nothing is simulated (§8)."""
    return [np.zeros(st.n) for _, st, _ in asks]


def simulator(cfg, iface, reinsertion_of, world_seed: int, device="cpu", shaping: float = 0.0, chunk_worlds=None,
              rollout_fn=None):
    """The search signal from the simulator: each state's mean count (plus `shaping` x progress) over its worlds.
    `reinsertion_of(search)` names the search's reinsertion; searches sharing one are batched in one rollout."""
    from ..evo.rollout import rollout

    rollout_fn = rollout_fn or rollout

    def evaluate(asks):
        out = [None] * len(asks)
        groups = {}
        for i, (s, st, ids) in enumerate(asks):
            groups.setdefault(id(reinsertion_of(s)), []).append(i)
        for idx in groups.values():
            reins = reinsertion_of(asks[idx[0]][0])
            genome = moved(Genome.cat([reins.genome(asks[i][1]) for i in idx]), device)  # rollout does not move it
            ids = np.concatenate([np.tile(asks[i][2], (asks[i][1].n, 1)) for i in idx])
            r = rollout_fn(cfg, iface, genome, ids, world_seed, device,
                           chunk_worlds=chunk_worlds or genome.n_strains * ids.shape[1])
            count = np.asarray(r.score, dtype=np.float64)
            prog = np.asarray(r.progress, dtype=np.float64) if shaping else 0.0
            fit = (count + shaping * prog).mean(axis=1)
            if not np.isfinite(fit).all():
                raise FloatingPointError("a non-finite search score")
            lo = 0
            for i in idx:
                n = asks[i][1].n
                out[i] = fit[lo:lo + n]
                lo += n
        return out

    return evaluate


PLAN = {"refit": 3, "random": 5, "free": 5}  # §6; the registered cuts lower "random" to 3, then "free" to 4 (§10)


def search_seed(seed: int, kind: str, index: int) -> int:
    """A search's own seed, from the target-brain's seed, the search kind and its index."""
    return int(np.random.SeedSequence([int(seed), ("refit", "random", "free").index(kind), int(index)])
               .generate_state(1)[0])


def random_partners(truth: dict, strat: np.ndarray, rng: np.random.Generator) -> dict:
    """Partners with the true counts per type and, within each type, the true partners' composition over the null's
    strata, uniformly within each stratum (§6, Fable)."""
    strat = np.asarray(strat)
    out = {}
    for t in TYPES:
        tr = np.asarray(truth[t], dtype=bool)
        m = np.zeros(len(tr), dtype=bool)
        for s in np.unique(strat):
            pool = np.nonzero(strat == s)[0]
            k = int(tr[pool].sum())
            if k:
                m[rng.choice(pool, size=k, replace=False)] = True
        out[t] = m
    return out


def target_brain_searches(reins: Reinsertion, truth: dict, strat: np.ndarray, scfg: SearchConfig, bcfg, mcfg,
                          seed: int, plan: dict | None = None, world_base: int = 0, world_span: int = 1) -> list:
    """The searches of one target-brain, labelled "refit-i", "random-i" and "free-i". Refits are handed their partner
    sets; every free search is built from the `Problem` alone (X's counts and self-connection), so nothing a free search
    does can depend on which candidates are partners."""
    plan = dict(PLAN if plan is None else plan)
    counts = {t: int(np.asarray(truth[t]).sum()) for t in TYPES}
    problem = problem_of(reins, counts)
    kw = dict(world_base=world_base, world_span=world_span)
    out = []
    for i in range(plan["refit"]):
        out.append(ReplicaExchange(problem, scfg, bcfg, mcfg, search_seed(seed, "refit", i),
                                   partners={t: np.asarray(truth[t], dtype=bool) for t in TYPES},
                                   label=f"refit-{i}", **kw))
    for i in range(plan["random"]):
        s = search_seed(seed, "random", i)
        out.append(ReplicaExchange(problem, scfg, bcfg, mcfg, s,
                                   partners=random_partners(truth, strat, np.random.default_rng([s, 0x03A7])),
                                   label=f"random-{i}", **kw))
    for i in range(plan["free"]):
        out.append(free_search(problem, scfg, bcfg, mcfg, search_seed(seed, "free", i), label=f"free-{i}", **kw))
    return out


def free_search(problem: Problem, scfg: SearchConfig, bcfg, mcfg, seed: int, **kw) -> ReplicaExchange:
    """A free search: given the `Problem` and nothing else."""
    return ReplicaExchange(problem, scfg, bcfg, mcfg, seed, partners=None, **kw)


def ranking(results: list) -> dict:
    """Each candidate's score per type: the mean absolute final weight (conductance) of its connection to X over the
    free searches' results (one-state `XState`s), 0 where not connected."""
    out = {}
    for t in TYPES:
        vals = [(r.weights()[t][0].abs() * r.masks()[t][0]).cpu().numpy().astype(np.float64) for r in results]
        out[t] = np.mean(vals, axis=0)
    return out
