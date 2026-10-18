"""D314 (Fable): splitting `ReplicaExchange.tell` into `_scored` and `_advance` is meant as code motion only. This runs
the search module as it was at f27d4c4 (before the split) and as it is now, side by side, on the same problems and
the same deterministic fitness, and compares every trace field and the final states exactly.

    python experiments/03a-self-consistency/development-records/tell_split_check.py > .../tell-split-check.txt
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from wormwars.config import Config  # noqa: E402
from wormwars.e03a import reinsert as R  # noqa: E402
from wormwars.e03a import search as NEW  # noqa: E402

BEFORE = "f27d4c4"


def old_module():
    src = subprocess.run(["git", "show", f"{BEFORE}:wormwars/e03a/search.py"], cwd=ROOT, check=True,
                         capture_output=True, text=True).stdout
    spec = importlib.util.spec_from_loader("wormwars.e03a.search_before_split", loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "wormwars.e03a"
    sys.modules[spec.name] = mod  # dataclasses look their module up there
    exec(compile(src, f"{BEFORE}:wormwars/e03a/search.py", "exec"), mod.__dict__)
    return mod


def fitness(asks):
    """Deterministic in the states and the generation's worlds: a fixed linear score of the masks and weights, plus
    noise keyed by the worlds, so ties and both acceptance branches occur."""
    out = []
    for _, st, w in asks:
        v = np.random.default_rng(7).normal(size=st.m_in.shape[1])
        base = (st.m_in.double().numpy() @ v + 0.3 * (st.w_out.double().numpy() * st.m_out.numpy()).sum(1)
                + 0.1 * st.tau.double().numpy())
        noise = np.random.default_rng([int(w.sum()) % 2**32, st.n]).normal(scale=0.5, size=st.n)
        out.append(np.round(base + noise, 2))
    return out


def run(mod, kind, scfg_kw, seed):
    cfg = Config()
    pr = mod.Problem(40, {"in": 5, "out": 4, "gap": 2}, True)
    scfg = mod.SearchConfig(**scfg_kw)
    partners = None
    if kind == "refit":
        g = np.random.default_rng(seed)
        partners = {t: np.zeros(40, bool) for t in R.TYPES}
        for t, k in pr.counts.items():
            partners[t][g.choice(40, k, replace=False)] = True
    s = mod.ReplicaExchange(pr, scfg, cfg.brain, cfg.mutation, seed, partners=partners, world_base=0,
                            world_span=10**6, snapshot_at=(5,))
    mod.run_lockstep([s], fitness)
    return s


def same(a, b) -> list:
    bad = []
    for f in ("scores", "accepted", "accepted_kind", "swaps", "paired"):
        if getattr(a.trace, f) != getattr(b.trace, f):
            bad.append(f)
    if not all(all(torch.equal(x[t], y[t]) for t in R.TYPES) for x, y in zip(a.trace.cold_masks, b.trace.cold_masks)):
        bad.append("cold_masks")
    if not a.current.equal(b.current):
        bad.append("final states")
    if not a.snapshots[5].equal(b.snapshots[5]):
        bad.append("snapshot")
    return bad


def main():
    OLD = old_module()
    cases = [("free", {"generations": 30}), ("free", {"generations": 30, "swap_every": 1,
                                                       "temperatures": (0.5, 1.0, 2.0, 4.0)}),
             ("refit", {"generations": 30}), ("free", {"generations": 30, "replicas": 1, "temperatures": (0.01,)}),
             ("free", {"generations": 30, "offspring": 3, "p_move": 0.6, "p_weights": 0.2, "p_tau_bias": 0.2,
                       "max_moves": 3})]
    fails = 0
    for kind, kw in cases:
        for seed in (0, 1, 2):
            a, b = run(OLD, kind, kw, seed), run(NEW, kind, kw, seed)
            bad = same(a, b)
            acc = float(np.mean(a.trace.accepted))
            swaps = sum(len(x) for x in a.trace.swaps)
            print(f"{kind:5s} {kw} seed {seed}: accepted share {acc:.2f}, swap attempts {swaps}: "
                  f"{'identical' if not bad else 'DIFFERENT in ' + ', '.join(bad)}")
            fails += bool(bad)
    print(f"{fails} of {len(cases) * 3} runs differ (before: {BEFORE}; after: the working tree)")
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
