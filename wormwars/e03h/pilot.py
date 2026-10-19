"""03h's pilot readings (experiments/03h-history-use/PILOT.md §5; DESIGN.md v3.3): reliability, A's statistics, the
detectability report, B's U and the manipulation's decile shift. Pure numpy: the driver supplies the scores."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm

from .stats import partial_spearman

DECILE = 26  # the top 26 of 256 (DESIGN §6)


def crossed_reliability(f: np.ndarray, w: int | None = None) -> float:
    """The ranking reliability of a genome's mean over w shared worlds, var_genome / (var_genome + var_residual / w),
    from the two-way decomposition of f [genomes, worlds] (DESIGN §2; development-records/t1_generation0.py)."""
    f = np.asarray(f, dtype=np.float64)
    G, W = f.shape
    w = W if w is None else w
    gm, wm, mu = f.mean(1), f.mean(0), f.mean()
    ms_g = W * ((gm - mu) ** 2).sum() / (G - 1)
    ms_e = ((f - gm[:, None] - wm[None, :] + mu) ** 2).sum() / ((G - 1) * (W - 1))
    var_a = max((ms_g - ms_e) / W, 0.0)
    return float(var_a / (var_a + ms_e / w)) if var_a > 0 else 0.0


def select_decile(sel_means: np.ndarray, k: int = DECILE) -> np.ndarray:
    """The top k genomes by selection-bank mean, ties broken by genome index (lower first), in rank order."""
    m = np.asarray(sel_means, dtype=np.float64)
    order = np.lexsort((np.arange(len(m)), -m))
    return order[:k]


def rho(H, S, fit_means) -> tuple[float, bool]:
    return partial_spearman(H, fit_means, S)


def shared_world_sd_of_mean_D(sel: dict, H: list, S: list, n_boot: int, seed: int) -> float:
    """s_shared (PILOT.md §5.3): the SD over shared resamples of the selection worlds (one resample applied to every
    graph and condition) of the mean over graphs of D = rho_sham − rho_relief. `sel[c]` is a list over graphs of
    [genomes, worlds] scores."""
    rng = np.random.default_rng(seed)
    W = sel["sham"][0].shape[1]
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, W, W)
        ds = [rho(H[g], S[g], sel["sham"][g][:, idx].mean(1))[0] - rho(H[g], S[g], sel["relief"][g][:, idx].mean(1))[0]
              for g in range(len(H))]
        out[b] = np.mean(ds)
    return float(out.std(ddof=1))


def power(s_graph: float, s_shared: float, delta: float = 0.05, n_graphs: int = 64) -> dict:
    """PILOT.md §5.3: SE = sqrt(s_graph^2 / n + s_shared^2); the one-sided power at alpha 0.025 for a mean D of 2 delta."""
    se = float(np.sqrt(s_graph ** 2 / n_graphs + s_shared ** 2))
    return {"se": se, "power": float(1 - norm.cdf(1.96 - 2 * delta / se)) if se > 0 else 1.0,
            "s_graph": float(s_graph), "s_shared": float(s_shared), "delta": delta, "graphs": n_graphs}


def b_readings(test: dict, n_boot: int, seed: int) -> dict:
    """B's pilot readings (PILOT.md §5.2-§5.4). `test[c]` is a list over graphs of the selected decile's test-bank
    scores [decile, test worlds], for c in level, relief, sham. U_g = T_sham − T_relief; the decile shift is
    T_relief − T_sham; intervals from shared resamples of the test worlds."""
    T = {c: np.array([x.mean() for x in v]) for c, v in test.items()}
    U = T["sham"] - T["relief"]
    W = test["sham"][0].shape[1]
    rng = np.random.default_rng(seed)
    shift_b, u_b = np.empty(n_boot), np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, W, W)
        r = np.array([x[:, idx].mean() for x in test["relief"]])
        s = np.array([x[:, idx].mean() for x in test["sham"]])
        shift_b[b], u_b[b] = (r - s).mean(), (s - r).mean()
    lo, hi = np.quantile(shift_b, [0.025, 0.975])
    return {"T": {c: v.tolist() for c, v in T.items()}, "U": U.tolist(),
            "U_between_graph_sd": float(U.std(ddof=1)) if len(U) > 1 else None,
            "U_mean_shared_world_se": float(u_b.std(ddof=1)),
            "decile_shift": {"per_graph": (-U).tolist(), "mean": float((-U).mean()), "lo": float(lo), "hi": float(hi),
                             "moves": bool(lo > 0)}}


def quartile_difference(H, fit_means) -> float:
    """PILOT.md §5.2: the fitness difference between the top and the bottom quartile of H (stable order; it describes
    the effect, it is not a conversion of rho into fitness units, Astra)."""
    q = np.argsort(np.asarray(H, dtype=np.float64), kind="stable")
    k = max(1, len(q) // 4)
    f = np.asarray(fit_means, dtype=np.float64)
    return float(f[q[-k:]].mean() - f[q[:k]].mean())


def projection_table(per_graph_seconds: dict, cap_hours: float, n_primary: int = 65, n_sh: int = 64) -> dict:
    """DESIGN §8's cut order as a decision table (Astra): `per_graph_seconds[W_t]` for W_t in (64, 32). The primary run
    (SH-mirror-ASK and N2) at W_t = 64 if it fits, with SH added only if that also fits; otherwise the primary at
    W_t = 32; otherwise nothing fits, and 03h stops for redesign (this takes precedence over the amplitude rule)."""
    h = {wt: {"primary": n_primary * s / 3600, "with_SH": (n_primary + n_sh) * s / 3600}
         for wt, s in per_graph_seconds.items()}
    if h[64]["primary"] <= cap_hours:
        plan = {"W_t": 64, "SH": bool(h[64]["with_SH"] <= cap_hours)}
    elif h[32]["primary"] <= cap_hours:
        plan = {"W_t": 32, "SH": bool(h[32]["with_SH"] <= cap_hours)}
    else:
        plan = None
    return {"hours": {str(k): v for k, v in h.items()}, "cap_hours": cap_hours, "plan": plan, "fits": plan is not None}
