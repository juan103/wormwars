"""E3b-0's simulation drivers (docs/E3/E3b-0-PLAN.md §3b, §3c): a colony on a block of mazes, the replay
donors, the polarity test, the trails' gradient share and the nose range.

- `play`: one controller or organism on every maze id (episode 0 unless given), returning
  `MazeWorld.task_events` and, on request, the nose range: on route-cell ticks (the head's cell at the
  tick's sensing), the share of goal-channel nose inputs in [0.005, 0.35] and above 0.35.
- `replay_donors`: each maze's donor episode, from 1000 up, advanced until A or B differs from the
  recipient's (exceptions reported). `play_replay`: recipients and donors in one lockstep batch; the
  recipients sense their own trail plus the donor colony's total times `coef`; the donors play with shared
  trails. The route overlap is the share of the recipient's route cells on the donor's route.
- `polarity`: per maze, one oracle wey's single pass A → B builds the A trail, which is then aged by that
  leg's duration (after its last deposit). The scripted follower starts at the middle maze cell of the
  route, facing away from A (toward B, with a jitter uniform in ±0.3 rad), its goal A, and passes if it
  enters A within twice the oracle's time from the same start. Three conditions: the real trail, none, and
  the route-permuted trail.
- `gradient`: oracle colonies shuttle for the horizon; each trail (summed over weys) is then aged by 1, 2
  and 4 of that maze's median oracle legs, and the gradient share is read toward its own source, A's and
  B's averaged.
"""

from __future__ import annotations

import math

import numpy as np
import torch

from . import maze as M
from . import maze_measures as MM
from . import maze_world as MW

POLARITY_STREAM, PERMUTE_STREAM = 0x901A, 0x9E2B
JITTER = 0.3
NOSE_LOW, NOSE_HIGH = 0.005, 0.35
QUANTILES = (1, 5, 25, 50, 75, 95, 99)
_EDGES = np.geomspace(1e-6, 1e2, 801)  # the histogram of positive inputs: bins 2.3% wide


class NoseRange:
    """Counts goal-channel nose inputs on route-cell ticks (the head's cell when the tick sensed)."""

    def __init__(self):
        self.on = self.inr = self.above = self.zero = self.occluded = self.q_n = self.q_high = 0

    def attach(self, world) -> None:
        routes = np.stack([MM.route_cells(mz, pl.a, pl.b) for mz, pl in zip(world.mazes, world.placements)])
        self.routes = torch.from_numpy(routes).to(world.device)
        self.prev = world.pos[:, 0].clone()
        self.edges = torch.as_tensor(_EDGES, dtype=world.dtype, device=world.device)
        self.hist = torch.zeros(len(_EDGES) + 1, dtype=torch.long, device=world.device)
        self.exists = self._exists(world)

    @staticmethod
    def _exists(world):
        """[worlds, weys, 1]: whether any trail of the wey's current goal exists anywhere in its maze."""
        mass = world.trails.sum(dim=(1, 3, 4))  # [worlds, (A, B)]
        return (mass.gather(1, world.goal) > 0).unsqueeze(-1)

    def record(self, world) -> None:
        s = world.last_signals
        g = torch.stack((s["goal_left"][:, 0], s["goal_right"][:, 0]), dim=-1)  # [worlds, weys, 2]
        ix, iy = self.prev[..., 0].floor().long(), self.prev[..., 1].floor().long()
        wi = torch.arange(world.n_worlds, device=world.device).view(-1, 1)
        on = self.routes[wi, iy, ix].unsqueeze(-1).expand_as(g)
        self.on += int(on.sum())
        self.inr += int((on & (g >= NOSE_LOW) & (g <= NOSE_HIGH)).sum())
        self.above += int((on & (g > NOSE_HIGH)).sum())
        self.zero += int((on & (g == 0)).sum())
        self.occluded += int((on & world.last_blocked).sum())
        keep = on & ~world.last_blocked & self.exists & (g > 0)
        self.q_n += int(keep.sum())
        self.q_high += int((keep & (g > NOSE_HIGH)).sum())
        self.hist += torch.bincount(torch.bucketize(g[keep], self.edges), minlength=len(_EDGES) + 1)
        self.prev = world.pos[:, 0].clone()
        self.exists = self._exists(world)

    def result(self) -> dict:
        n, m = max(self.on, 1), max(self.on - self.occluded, 1)
        h = self.hist.cpu().numpy()
        cum = np.cumsum(h) / max(h.sum(), 1)
        upper = np.concatenate([_EDGES, [np.inf]])
        q = {str(p): float(upper[min(int(np.searchsorted(cum, p / 100)), len(upper) - 1)]) for p in QUANTILES}
        return {"on_route_noses": self.on, "in_range": self.inr, "above": self.above, "zero": self.zero,
                "occluded": self.occluded, "in_range_share": self.inr / n, "above_share": self.above / n,
                "in_range_share_unoccluded": self.inr / m, "above_share_unoccluded": self.above / m,
                "positive_unoccluded_after_trail": int(h.sum()), "quantiles_unoccluded_positive": q,
                "qualified_inputs": self.q_n, "qualified_above_high": self.q_high,
                "above_high_share_qualified": self.q_high / max(self.q_n, 1)}


def world(cfg, iface, brain, ids, run_seed, device="cpu", **kw) -> MW.MazeWorld:
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long, device=device)
    return MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=run_seed, world_ids=np.asarray(ids), device=device, **kw)


def play(cfg, iface, make_brain, ids, run_seed, device="cpu", *, nose_range=False, setup=None, ticks=None, **kw) -> dict:
    w = world(cfg, iface, make_brain(), ids, run_seed, device, **kw)
    if setup is not None:
        setup(w)
    rec = None
    if nose_range:
        rec = NoseRange()
        rec.attach(w)
        w.recorder = rec
    w.run(ticks)
    out = w.task_events()
    if rec is not None:
        out["nose_range"] = rec.result()
    return out


def replay_donors(ids, run_seed: int, c: int, first: int = 1000, tries: int = 64) -> tuple[np.ndarray, list]:
    eps, exceptions = [], []
    for mid in np.asarray(ids):
        _, p0 = M.maze_for(run_seed=run_seed, maze_id=int(mid), episode=0, c=c)
        ep = first
        for _ in range(tries):
            _, p1 = M.maze_for(run_seed=run_seed, maze_id=int(mid), episode=ep, c=c)
            if p1.a != p0.a or p1.b != p0.b:
                break
            ep += 1
        else:
            exceptions.append(int(mid))
        eps.append(ep)
    return np.asarray(eps, dtype=np.int64), exceptions


def play_replay(cfg, iface, make_brain, ids, run_seed, *, donor_episodes, coef: float, device="cpu", ticks=None) -> dict:
    ids = np.asarray(ids)
    n = len(ids)
    w = world(cfg, iface, make_brain(), np.concatenate([ids, ids]), run_seed, device,
              episodes=np.concatenate([np.zeros(n, dtype=np.int64), np.asarray(donor_episodes)]),
              access=["replay"] * n + ["shared"] * n, donors=np.concatenate([np.arange(n, 2 * n), np.full(n, -1)]),
              replay_coef=np.concatenate([np.full(n, float(coef)), np.zeros(n)]))
    w.run(ticks)
    ev = w.task_events()
    out = {k: v[:n] for k, v in ev.items()}
    out["donor"] = {k: v[n:] for k, v in ev.items()}
    overlap = []
    for i in range(n):
        r = MM.route_cells(w.mazes[i], w.placements[i].a, w.placements[i].b)
        d = MM.route_cells(w.mazes[n + i], w.placements[n + i].a, w.placements[n + i].b)
        overlap.append(float((r & d).sum() / r.sum()))
    out["route_overlap"] = np.asarray(overlap)
    return out


def age(x: torch.Tensor, open_: torch.Tensor, *, delta: float, mu: float, steps: torch.Tensor) -> torch.Tensor:
    """Each row of `x` [N, ..., H, W] diffused and evaporated for its own number of `steps` [N]."""
    out = x.clone()
    cur = x.clone()
    steps = torch.as_tensor(steps).to(x.device).long()
    for k in range(1, int(steps.max()) + 1 if len(steps) else 1):
        cur = MW.diffuse(cur, open_, delta) * (1.0 - mu)
        hit = steps == k
        if bool(hit.any()):
            out[hit] = cur[hit]
    return out


def _start(mz, pl, run_seed: int, maze_id: int, facing: str = "away"):
    """The middle maze cell of the A-B route, and a heading with its jitter: toward B ("away" from the
    source A, the registered start), toward A ("toward"), or uniform ("random", a further draw)."""
    path = MM.tree_path(mz, pl.a, pl.b)
    k = len(path) // 2
    mid, nxt, prv = path[k], path[k + 1], path[k - 1]
    x0, y0 = M.cell_centre(mid)
    x1, y1 = M.cell_centre(nxt)
    rng = np.random.default_rng([run_seed, maze_id, POLARITY_STREAM])
    j = rng.uniform(-JITTER, JITTER)
    h = math.atan2(y1 - y0, x1 - x0) + j
    if facing == "toward":  # the route's previous cell, toward A (D178: not away + π, which can face a wall)
        xp, yp = M.cell_centre(prv)
        h = math.atan2(yp - y0, xp - x0) + j
    elif facing == "random":
        h = rng.uniform(0, 2 * math.pi)
    elif facing != "away":
        raise ValueError("facing is away, toward or random")
    return mid, (x0, y0), h


def polarity(cfg, iface, ids, run_seed, device="cpu", facing: str = "away", limit_factor: float = 2.0,
             age_legs: float = 1.0, synthetic=None) -> dict:
    """See the module's docstring. Diagnostic options (D178): `facing`, the deadline as `limit_factor` × the
    oracle's time, the trail's age in legs, and `synthetic(maze, placement, route)`, a field that replaces
    the oracle's trail as the real condition."""
    from . import maze_controls as MC
    wcfg = cfg.world
    ids = np.asarray(ids)
    n, H = len(ids), int(wcfg.max_ticks)
    # 1. one oracle wey's single pass: the A trail at its B visit
    w = world(cfg, iface, MC.oracle(iface, cfg, device=device), ids, run_seed, device, access="none")
    snap = torch.zeros(n, w.H, w.W, dtype=w.dtype, device=w.device)
    leg = torch.zeros(n, dtype=torch.long, device=w.device)
    done = torch.zeros(n, dtype=torch.bool, device=w.device)
    while w.tick_count < H and not bool(done.all()):
        w.tick()
        new = (w.visits[:, 0] >= 2) & ~done
        if bool(new.any()):
            snap[new] = w.trails[new, 0, 0]
            vt = w._visit_tick[:, 0]
            leg[new] = (vt[:, 1] - vt[:, 0])[new]
            done |= new
    aged = age(snap, w._open, delta=wcfg.maze_trail_delta, mu=wcfg.maze_trail_mu,
               steps=torch.round(leg.double() * float(age_legs)).long())
    if synthetic is not None:
        aged = torch.from_numpy(np.stack([
            np.asarray(synthetic(w.mazes[i], w.placements[i], MM.route_cells(w.mazes[i], w.placements[i].a,
                                                                             w.placements[i].b)), dtype=np.float32)
            for i in range(n)])).to(w.device, w.dtype)
    starts = [_start(w.mazes[i], w.placements[i], run_seed, int(ids[i]), facing) for i in range(n)]
    mids = torch.tensor([s[0] for s in starts], dtype=torch.long, device=w.device)
    pos = torch.tensor([s[1] for s in starts], dtype=w.dtype, device=w.device)
    head = torch.tensor([s[2] % (2 * math.pi) for s in starts], dtype=w.dtype, device=w.device)

    def place(world_):
        world_.pos[:, 0, 0] = pos
        world_.heading[:, 0, 0] = head
        world_._points = None
        if hasattr(world_.brains[0], "cur"):
            world_.brains[0].cur[:, 0] = mids

    # 2. the oracle's time from the start to A
    o = play(cfg, iface, lambda: MC.oracle(iface, cfg, device=device), ids, run_seed, device, access="none", setup=place)
    t_or = np.where(o["visit_tick"][:, 0, 0] >= 0, o["visit_tick"][:, 0, 0] + 1, H)
    limit = np.ceil(float(limit_factor) * t_or).astype(np.int64)
    # 3. the follower on the real, empty and route-permuted trails
    fields = {"real": aged.cpu().numpy(), "none": np.zeros_like(aged.cpu().numpy())}
    fields["permuted"] = np.stack([
        MM.route_permuted(fields["real"][i], MM.route_cells(w.mazes[i], w.placements[i].a, w.placements[i].b),
                          np.random.default_rng([run_seed, int(ids[i]), PERMUTE_STREAM])) for i in range(n)])
    out = {"oracle_ticks": t_or.astype(np.int64), "leg_ticks": leg.cpu().numpy(), "single_pass": done.cpu().numpy(),
           "facing": facing, "limit_factor": float(limit_factor), "age_legs": float(age_legs),
           "synthetic": synthetic is not None}
    for name, f in fields.items():
        trail = torch.from_numpy(f).to(device, w.dtype)

        def setup(world_, trail=trail):
            place(world_)
            world_.trails[:, 0, 0] = trail

        ev = play(cfg, iface, lambda: MC.follower(iface, cfg, device=device), ids, run_seed, device, access="own",
                  setup=setup, ticks=int(limit.max()))
        first = ev["visit_tick"][:, 0, 0]
        out[f"pass_{name}"] = ((first >= 0) & (first + 1 <= limit)).astype(np.float64)
        out[f"first_tick_{name}"] = first
    return out


def gradient(cfg, iface, ids, run_seed, device="cpu", ages=(1, 2, 4)) -> dict:
    from . import maze_controls as MC
    wcfg = cfg.world
    ids = np.asarray(ids)
    w = world(cfg, iface, MC.oracle(iface, cfg, device=device), ids, run_seed, device, access="none")
    w.run()
    ev = w.task_events()
    n, H = len(ids), int(wcfg.max_ticks)
    legs = []
    for i in range(n):
        d = [np.diff(r[r >= 0]) for r in ev["visit_tick"][i]]
        d = np.concatenate([x for x in d if len(x)]) if any(len(x) for x in d) else np.array([H])
        legs.append(int(np.median(d)))
    legs = np.asarray(legs)
    total = w.trails.sum(dim=1)  # [worlds, (A, B), H, W]
    out = {"leg_ticks": legs}
    for k in ages:
        aged = age(total, w._open.unsqueeze(1), delta=wcfg.maze_trail_delta, mu=wcfg.maze_trail_mu,
                   steps=torch.as_tensor(k * legs)).cpu().numpy()
        shares = []
        for i in range(n):
            mz, pl = w.mazes[i], w.placements[i]
            route = MM.route_cells(mz, pl.a, pl.b)
            sa = MM.gradient_share(aged[i, 0], mz, pl.a, route)
            sb = MM.gradient_share(aged[i, 1], mz, pl.b, route)
            shares.append((sa + sb) / 2)
        out[f"share_age{k}"] = np.asarray(shares)
    return out


def synthetic_slope(mz, pl, route) -> np.ndarray:
    """A reference trail with a known slope: exp(−d / 8) on the route cells, d the free distance from A."""
    d = mz.free_distance(pl.a)
    return np.where(route, np.exp(-np.where(np.isfinite(d), d, 0.0) / 8.0), 0.0)


def polarity_readings(p: dict) -> dict:
    """A polarity run's passes within 2× and 4× the oracle's time (from its arrival ticks), the readings
    real − max(none, permuted), and the arrival time over the oracle's, on the single-pass mazes."""
    ok = p["single_pass"].astype(bool)
    t = p["oracle_ticks"].astype(np.float64)
    out = {"single_pass_mazes": int(ok.sum()), "facing": p["facing"], "age_legs": p["age_legs"],
           "synthetic": p["synthetic"]}
    for name in ("real", "none", "permuted"):
        first = p[f"first_tick_{name}"]
        arrived = first >= 0
        for f in (2, 4):
            out[f"{name}_within_{f}x"] = float(((arrived & (first + 1 <= np.ceil(f * t)))[ok]).mean())
        ratio = np.where(arrived, (first + 1) / t, np.inf)[ok]
        out[f"{name}_censored_share"] = float(np.mean(~np.isfinite(ratio))) if len(ratio) else float("nan")
        qs = np.quantile(ratio, [0.25, 0.5, 0.75], method="inverted_cdf") if len(ratio) else [np.inf] * 3
        out[f"{name}_time_over_oracle_quartiles"] = [float(x) if np.isfinite(x) else None for x in qs]  # None: censored
    for f in (2, 4):
        out[f"reading_{f}x"] = out[f"real_within_{f}x"] - max(out[f"none_within_{f}x"], out[f"permuted_within_{f}x"])
    return out
