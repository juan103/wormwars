"""Hierarchical bootstrap over graphs and runs.

The unit of analysis is the **run**. Thousands of worlds evaluating one lineage are not independent
samples of anything, and islands that exchange champions are not independent either -- so worlds
never enter the bootstrap, only per-run summary scores do.

Two levels of resampling:

1. resample *graphs* with replacement (SH1..SHK, RD1..RDK; N2 has only one graph)
2. within each sampled graph, resample its *runs* with replacement

For N2 level 1 is degenerate: there is exactly one real connectome, so N2's interval reflects
run-to-run variation only, while SH and RD intervals also carry graph-to-graph variation. That
asymmetry is real and is stated in every report rather than hidden: the question "is N2 unusual"
is asked against the SH/RD *distribution over graphs*, which is what the extra level buys.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BootstrapResult:
    mean: float
    lo: float
    hi: float
    n_graphs: int
    n_runs: int
    samples: np.ndarray

    def __str__(self) -> str:
        return f"{self.mean:.4f} [{self.lo:.4f}, {self.hi:.4f}] ({self.n_graphs}g x {self.n_runs}r)"


def hierarchical_bootstrap(
    groups: dict[str, list[float]],
    n_boot: int = 10_000,
    ci: float = 0.95,
    rng: np.random.Generator | None = None,
) -> BootstrapResult:
    """`groups` maps a graph label to that graph's per-run scores."""
    rng = rng or np.random.default_rng(0)
    labels = list(groups)
    arrays = [np.asarray(groups[k], dtype=float) for k in labels]
    if not labels or all(a.size == 0 for a in arrays):
        raise ValueError("no runs to bootstrap")
    n_g = len(labels)
    samples = np.empty(n_boot)
    for b in range(n_boot):
        gi = rng.integers(0, n_g, size=n_g)
        vals = []
        for g in gi:
            a = arrays[g]
            vals.append(a[rng.integers(0, a.size, size=a.size)].mean())
        samples[b] = float(np.mean(vals))
    alpha = (1 - ci) / 2
    return BootstrapResult(
        mean=float(np.mean([a.mean() for a in arrays])),
        lo=float(np.quantile(samples, alpha)),
        hi=float(np.quantile(samples, 1 - alpha)),
        n_graphs=n_g,
        n_runs=int(sum(a.size for a in arrays)),
        samples=samples,
    )


@dataclass
class Comparison:
    a: str
    b: str
    diff: float
    lo: float
    hi: float
    p_a_greater: float

    def verdict(self, name_a: str | None = None, name_b: str | None = None) -> str:
        a, b = name_a or self.a, name_b or self.b
        if self.lo > 0:
            return f"{a} > {b}"
        if self.hi < 0:
            return f"{a} < {b}"
        return f"no separation between {a} and {b}"

    def __str__(self) -> str:
        return (
            f"{self.a} - {self.b} = {self.diff:+.4f} [{self.lo:+.4f}, {self.hi:+.4f}], "
            f"P({self.a} > {self.b}) = {self.p_a_greater:.3f}"
        )


def compare(
    a: dict[str, list[float]],
    b: dict[str, list[float]],
    name_a: str = "A",
    name_b: str = "B",
    n_boot: int = 10_000,
    ci: float = 0.95,
    seed: int = 0,
) -> Comparison:
    """Bootstrap the difference of two conditions, resampling each independently."""
    rng = np.random.default_rng(seed)
    ra = hierarchical_bootstrap(a, n_boot, ci, np.random.default_rng(rng.integers(1 << 62)))
    rb = hierarchical_bootstrap(b, n_boot, ci, np.random.default_rng(rng.integers(1 << 62)))
    d = ra.samples - rb.samples
    alpha = (1 - ci) / 2
    return Comparison(
        a=name_a,
        b=name_b,
        diff=float(ra.mean - rb.mean),
        lo=float(np.quantile(d, alpha)),
        hi=float(np.quantile(d, 1 - alpha)),
        p_a_greater=float((d > 0).mean()),
    )


def per_graph_table(groups: dict[str, list[float]]) -> str:
    lines = [f"{'graph':<8} {'runs':>5} {'mean':>9} {'sd':>8} {'min':>8} {'max':>8}"]
    for label, vals in groups.items():
        v = np.asarray(vals, dtype=float)
        lines.append(
            f"{label:<8} {v.size:>5} {v.mean():>9.4f} {v.std(ddof=1) if v.size > 1 else 0:>8.4f} "
            f"{v.min():>8.4f} {v.max():>8.4f}"
        )
    return "\n".join(lines)


def area_under_curve(history: np.ndarray) -> float:
    """Mean of a fitness-vs-generation curve: 'how fast did it get there', not just 'how far'."""
    h = np.asarray(history, dtype=float)
    h = h[~np.isnan(h)]
    return float(h.mean()) if h.size else float("nan")
