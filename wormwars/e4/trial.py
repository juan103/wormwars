"""E4-D's single-choice trial (docs/E4/E4-D-DESIGN.md v2.1 §1-§3).

- `trial_config`: E4's maze family (6 × 6 islands, k_r = 0) with one wey, no trails, the scent untruncated at σ_D,
  and the horizon H_t.
- `block_distance`, `start_cell`: §2's rule on the free grid, with distances to the goal blocks: outside both blocks,
  |d₀ − d₁| ≤ 4, the downhill sets parting within 4 common steps, the largest min(d₀, d₁), row-major ties; None if no
  cell qualifies.
- `TrialWorld`: a `MazeWorld` subclass, so every earlier path is unchanged. The two carved goal sites are the
  candidates, in canonical order; `assign` [worlds] says which is real. The wey starts at the start cell with a
  heading from the trial's own stream, the latch at v_q = −1 (mode B). A's noses read the real candidate (or, for the
  controls, the decoy, candidate 0 whatever the assignment, or nothing); B's read the sum (or, for the oracle, the
  real one). The relays read nothing, the start cue is off and the goal is pinned at B. The first entry into either
  candidate is latched per wey (its candidate and tick); later events are ignored.
- `latch_first`, `control_genome` (the two wirings of §4).

Simultaneous entries into both candidates cannot happen (disjoint blocks, one head), so `latch_first`'s tie-break is
never used. The maze world's own ledgers (visits, the goal's switch before it is re-pinned, deposits) keep running and
are not read; only the first-entry record is.

Every option that breaks the design (`keep_start_cue`, `relay_leak`, and `b_source="real"` outside the oracle) exists
for the tests' sabotages and the oracle; the feasibility runner states which it uses.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import torch

from ..brain import Genome
from ..e3 import maze_world as MW

TRIAL_HEADING_STREAM = 0x7E1A
NO_TRUNCATION = 10 ** 6
SEPARATION_STEPS = 4
DISTANCE_TOLERANCE = 4
A_SOURCES = ("real", "decoy", "fixed0", "none")
B_SOURCES = ("sum", "real")


def trial_config(*, sigma: float, horizon: int, c: int = 6, base=None):
    """One wey, no trails (access none), the scent untruncated at `sigma`; E4's trail constants (unused)."""
    return MW.maze_config(base, c=c, horizon=horizon, colony=1, mu=0.01, lam=0.02, delta=0.05, d0=1.142,
                          access="none", family="islands", k_r=0, scent_sigma=sigma, scent_reach=NO_TRUNCATION)


def _down(d: np.ndarray, y: int, x: int) -> list:
    """The free 4-neighbours of (y, x) that lower `d`, in index order."""
    out = []
    for dy, dx in ((-1, 0), (0, -1), (0, 1), (1, 0)):  # row-major order of the neighbours
        yy, xx = y + dy, x + dx
        if 0 <= yy < d.shape[0] and 0 <= xx < d.shape[1] and np.isfinite(d[yy, xx]) and d[yy, xx] < d[y, x]:
            out.append((yy, xx))
    return out


def _separates(d0: np.ndarray, d1: np.ndarray, y: int, x: int) -> bool:
    for _ in range(SEPARATION_STEPS + 1):
        a, b = _down(d0, y, x), _down(d1, y, x)
        common = [p for p in a if p in b]
        if not common:
            return bool(a) and bool(b)
        y, x = common[0]
    return False


def block_distance(mz, cell) -> np.ndarray:
    """4-neighbour BFS distance over free grid cells from every free cell of the maze cell's 3 × 3 goal block (§2: the
    distances are to the candidates' goal blocks, not their centres; Astra); inf in walls and where unreachable."""
    from collections import deque
    n = mz.wall.shape[0]
    dist = np.full(mz.wall.shape, np.inf)
    y0, x0 = 1 + 4 * cell[0], 1 + 4 * cell[1]
    q = deque()
    for y in range(y0, y0 + 3):
        for x in range(x0, x0 + 3):
            if not mz.wall[y, x]:
                dist[y, x] = 0
                q.append((y, x))
    while q:
        y, x = q.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < n and 0 <= xx < n and not mz.wall[yy, xx] and np.isinf(dist[yy, xx]):
                dist[yy, xx] = dist[y, x] + 1
                q.append((yy, xx))
    return dist


def start_cell(wall: np.ndarray, d0: np.ndarray, d1: np.ndarray):
    """§2's start: the qualifying free grid cell with the largest min(d₀, d₁), row-major ties; None if none."""
    best, best_key = None, None
    H, W = wall.shape
    for y in range(H):
        for x in range(W):
            if wall[y, x] or not (np.isfinite(d0[y, x]) and np.isfinite(d1[y, x])):
                continue
            if abs(d0[y, x] - d1[y, x]) > DISTANCE_TOLERANCE or min(d0[y, x], d1[y, x]) <= 0:
                continue  # outside both goal blocks (v2.3)
            if not _separates(d0, d1, y, x):
                continue
            key = min(d0[y, x], d1[y, x])
            if best is None or key > best_key:
                best, best_key = (y, x), key
    return best


def latch_first(cand: torch.Tensor, tick: torch.Tensor, entry: torch.Tensor, t: int) -> None:
    """In place: weys with no first entry yet and an entry now ([worlds, weys, 2]) record its candidate and `t`."""
    hit = entry.any(-1) & (cand < 0)
    which = entry.to(torch.long).argmax(-1)
    cand.copy_(torch.where(hit, which, cand))
    tick.copy_(torch.where(hit, torch.full_like(tick, t), tick))


class TrialWorld(MW.MazeWorld):
    def __init__(self, cfg, iface, brain, strain_of, run_seed, world_ids, *, assign, q_index: int, device="cpu",
                 a_source: str = "real", b_source: str = "sum", keep_start_cue: bool = False,
                 relay_leak: bool = False, **kw):
        if a_source not in A_SOURCES or b_source not in B_SOURCES:
            raise ValueError((a_source, b_source))
        self.assignment = torch.as_tensor(np.asarray(assign, dtype=np.int64), device=device)
        self.a_source, self.b_source = a_source, b_source
        self.keep_start_cue, self.relay_leak = keep_start_cue, relay_leak
        self.starts = []
        super().__init__(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=world_ids, device=device,
                         access="none", **kw)
        if self.n_weys != 1:
            raise ValueError("a trial has one wey")
        if len(self.assignment) != self.n_worlds:
            raise ValueError("one assignment per world")
        self.v[0][..., int(q_index)] = -1.0  # mode B from the first substep; the latch is free afterwards
        self.goal.fill_(1)
        self.first_candidate = torch.full((self.n_worlds, 1), -1, dtype=torch.long, device=self.device)
        self.first_tick = torch.full((self.n_worlds, 1), -1, dtype=torch.long, device=self.device)

    def _build_maps(self) -> None:
        super()._build_maps()
        pos, head = self.pos.clone(), self.heading.clone()
        for w, (mz, pl) in enumerate(zip(self.mazes, self.placements)):
            c0, c1 = sorted((tuple(pl.a), tuple(pl.b)))
            self.placements[w] = dataclasses.replace(pl, a=c0, b=c1)
            s = start_cell(mz.wall, block_distance(mz, c0), block_distance(mz, c1))
            if s is None:
                raise ValueError(f"maze {int(self.world_ids[w])} has no qualifying start cell (skip it)")
            self.starts.append(s)
            pos[w, 0, 0] = torch.tensor([s[1] + 0.5, s[0] + 0.5], dtype=self.dtype)
            rng = np.random.default_rng([self.run_seed, int(self.world_ids[w]), TRIAL_HEADING_STREAM])
            head[w, 0, 0] = float(rng.uniform(0, 2 * np.pi))
        self.pos.copy_(pos)
        self.heading.copy_(head)

    def trial_signals(self) -> dict:
        return self._extra_signals(self.sample_points())

    def _extra_signals(self, pts):
        sig = super()._extra_signals(pts)
        Wn = self.n_worlds
        c0 = torch.stack((sig["a_left"], sig["a_right"]), -1)  # candidate 0's scent at the noses [W, 1, B, (L, R)]
        c1 = torch.stack((sig["b_left"], sig["b_right"]), -1)
        one = (self.assignment == 1).view(Wn, 1, 1, 1)
        real, decoy = torch.where(one, c1, c0), torch.where(one, c0, c1)
        a = {"real": real, "decoy": decoy, "fixed0": c0, "none": torch.zeros_like(c0)}[self.a_source]
        b = c0 + c1 if self.b_source == "sum" else real
        out = dict(sig)
        out["cand"] = torch.stack((c0, c1), -2)  # [W, 1, B, 2, (L, R)], for the tests and records
        out["a_left"], out["a_right"] = a[..., 0].contiguous(), a[..., 1].contiguous()
        out["b_left"], out["b_right"] = b[..., 0].contiguous(), b[..., 1].contiguous()
        out["goal_left"], out["goal_right"] = out["b_left"], out["b_right"]
        zero = torch.zeros_like(sig["at_a"])
        out["at_a"] = zero
        out["at_b"] = sig["at_b"] if self.keep_start_cue else zero.clone()
        if self.relay_leak:
            out["at_b"] = self.assignment.view(Wn, 1, 1).to(zero.dtype).expand_as(zero).contiguous()
        return out

    def _post_move(self, moved) -> None:
        before = self._inside.clone()
        t = self.tick_count
        super()._post_move(moved)
        entry = self._inside & ~before & self.alive[:, 0].unsqueeze(-1)
        latch_first(self.first_candidate, self.first_tick, entry, t)
        self.goal.fill_(1)

    def trial_events(self) -> dict:
        real = self.assignment.view(-1, 1)
        fc = self.first_candidate
        return {"first_candidate": fc.cpu().numpy(), "first_tick": self.first_tick.cpu().numpy(),
                "real_first": ((fc >= 0) & (fc == real)).cpu().numpy(), "decoy_first": ((fc >= 0) & (fc != real)).cpu().numpy(),
                "assign": self.assignment.cpu().numpy(), "starts": [list(s) for s in self.starts]}


def control_genome(genome: Genome, cx, wiring: str, w: float) -> Genome:
    """§4's control: E-G with A's steering signal copied into B. "comparator": A_CL → B_CL, A_CR → B_CR at +w.
    "nose": B's own four signed nose → comparator edges, from A's noses. Set directly, not clamped."""
    edges = {"comparator": [("E3_A_CL", "E3_B_CL", 1.0), ("E3_A_CR", "E3_B_CR", 1.0)],
             "nose": [("E3_A_NL", "E3_B_CL", 1.0), ("E3_A_NL", "E3_B_CR", -1.0),
                      ("E3_A_NR", "E3_B_CR", 1.0), ("E3_A_NR", "E3_B_CL", -1.0)]}[wiring]
    spec, ext = genome.spec, cx["org"].ext
    out = genome.w.clone()
    for pre, post, sign in edges:
        k = ((spec.chem_i == ext.index(pre)) & (spec.chem_j == ext.index(post))).nonzero()
        if len(k) != 1:
            raise ValueError(f"no single slot {pre} → {post}")
        out[:, int(k[0, 0])] = sign * float(w)
    return genome.with_params(w=out)
