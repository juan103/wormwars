"""03h's scripted gate (experiments/03h-history-use/PILOT.md §2; DESIGN.md v3.2 §4): nested families tuned on tuning
worlds under their own condition, each scored once on check worlds, with paired bootstrap intervals over the check
worlds (02's `_paired`)."""

from __future__ import annotations

import numpy as np

from ..exp02 import scripted
from .scripted import BitKinesis, SlowMemoryKinesis

# 02's grids (scripts/exp02.py K_GRID and FALL_GRID; tests/test_e03h_gate.py checks they are still equal)
K_GRID = {"slow": [0.0, 0.25, 0.5, 0.75, 1.0], "fast": [0.5, 0.75, 1.0],
          "threshold": [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 0.6, 1.0, 1.5, 2.0, 3.0, 5.0],
          "turn": [0.0, 0.1, 0.2, 0.4, 0.7]}
FALL_GRID = {"fall_turn": [0.4, 0.7, 1.0], "fall_threshold": [0.0, 0.001, 0.003]}
G_GRID = {"slow": [0.0, 0.25, 0.5, 0.75, 1.0], "fast": [0.5, 0.75, 1.0], "scale": [0.03, 0.1, 0.3, 1.0, 3.0],
          "turn": [0.0, 0.1, 0.2, 0.4, 0.7]}
T_GRID = [1.0, 2.0, 5.0, 10.0, 20.0]

MAKERS = {
    "K": lambda **p: scripted.LevelKinesis(**p),
    "Graded": lambda **p: scripted.GradedKinesis(**p),
    "M": lambda **p: scripted.MemoryKinesis(**p),
    "Bit": lambda **p: BitKinesis(**p),
    "Slow": lambda **p: SlowMemoryKinesis(**p),
}


def near(params: dict, grid: dict) -> dict:
    """Each parameter at its grid neighbours (02's `_near`), for the keys of `grid`."""
    out = {}
    for k, vals in grid.items():
        vals = list(vals)
        i = vals.index(params[k])
        out[k] = vals[max(0, i - 1): i + 2]
    return out


def tune_families(cfgs: dict, iface, ids, seed, device, tune=scripted.tune_batched, parts: str = "all") -> dict:
    """`cfgs` maps a condition ("level", and "relief" or "sham") to its configuration. Returns, per family, its kind,
    parameters, tuning score and condition; the "+ bit" families are tuned under the condition that is not "level".
    `parts` = "memoryless" stops after the memoryless and memoryless + bit families (G2).

    Nesting (02's rule, PILOT.md §2): K and Graded on their grids; memoryless = the better. Bit around K's optimum,
    falling back to memoryless. M around K's optimum with FALL_GRID; Slow at M's optimum over T (so T = 1 is M itself);
    memory = the best of memoryless, M and Slow. Memory + bit: Slow at the memory optimum's parameters over T, with
    use_memory and use_bit each in {0, 1}, or the memoryless + bit optimum, whichever is better."""
    lv = cfgs["level"]
    bit_name = next(k for k in cfgs if k != "level")
    bitc = cfgs[bit_name]
    t = lambda kind, grid, cfg: tune(MAKERS[kind], grid, cfg, iface, ids, seed, device)  # noqa: E731
    kp, ks = t("K", K_GRID, lv)
    gp, gs = t("Graded", G_GRID, lv)
    loc = near(kp, K_GRID)
    fam = {"K": ("K", kp, ks, "level"), "Graded": ("Graded", gp, gs, "level")}
    fam["memoryless"] = fam["K"] if ks >= gs else fam["Graded"]
    bp, bs = t("Bit", dict(loc, fall_turn=FALL_GRID["fall_turn"]), bitc)
    ml_on_bit = _score_on(fam["memoryless"], bitc, iface, ids, seed, device)
    fam["memoryless+bit"] = ("Bit", bp, bs, bit_name) if bs > ml_on_bit else (
        fam["memoryless"][0], fam["memoryless"][1], ml_on_bit, bit_name)
    if parts == "memoryless":
        return _out(fam)
    mp, ms = t("M", dict(loc, **FALL_GRID), lv)
    one = lambda d: {k: [v] for k, v in d.items()}  # noqa: E731
    sp, ss = t("Slow", dict(one(mp), T=T_GRID, use_memory=[1.0], use_bit=[0.0]), lv)
    fam["M"], fam["Slow"] = ("M", mp, ms, "level"), ("Slow", sp, ss, "level")
    fam["memory"] = max([fam["memoryless"], fam["M"], fam["Slow"]], key=lambda c: c[2])  # first maximum on ties
    base = sp if fam["memory"][0] == "Slow" else mp  # the memory optimum's speed, turn and fall parameters
    base = {k: v for k, v in base.items() if k not in ("T", "use_memory", "use_bit")}
    xp, xs = t("Slow", dict(one(base), T=T_GRID, use_memory=[0.0, 1.0], use_bit=[0.0, 1.0]), bitc)
    fam["memory+bit"] = max([fam["memoryless+bit"], ("Slow", xp, xs, bit_name)], key=lambda c: c[2])
    return _out(fam)


def _out(fam: dict) -> dict:
    return {k: {"kind": v[0], "params": _plain(v[1]), "tuning_score": float(v[2]), "condition": v[3]}
            for k, v in fam.items()}


def _plain(p: dict) -> dict:
    return {k: float(v) for k, v in p.items()}


def _score_on(member, cfg, iface, ids, seed, device) -> float:
    kind, params = member[0], member[1]
    return float(scripted.score_policy(cfg, iface, MAKERS[kind](**params), ids, seed, device).mean())


def check_scores(fams: dict, cfgs: dict, iface, ids, seed, device) -> dict:
    """Each family's chosen policy scored once on the check worlds, under its condition: per-world arrays."""
    return {k: np.asarray(scripted.score_policy(cfgs[v["condition"]], iface, MAKERS[v["kind"]](**v["params"]), ids,
                                                seed, device), dtype=np.float64) for k, v in fams.items()}


def paired(a, b, level: float, n: int = 20_000, seed: int = 0) -> dict:
    """a − b paired over check worlds: the mean and its `level` percentile interval from a world bootstrap (02's
    `_paired`, at a chosen level)."""
    d = np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)
    rng = np.random.default_rng(seed)
    m = d[rng.integers(0, len(d), (n, len(d)))].mean(1)
    q = (1 - level) / 2
    return {"estimate": float(d.mean()), "lo": float(np.quantile(m, q)), "hi": float(np.quantile(m, 1 - q)),
            "level": level}


def recovered_share(ml_bit, ml, mem, n: int = 20_000, seed: int = 0) -> dict:
    """(memoryless + bit − memoryless) / (memory − memoryless), with a 95% world-bootstrap interval of the ratio of
    means (02's `_share`)."""
    a, b, c = (np.asarray(x, dtype=np.float64) for x in (ml_bit, ml, mem))
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(a), (n, len(a)))
    s = (a - b)[idx].mean(1) / (c - b)[idx].mean(1)
    return {"estimate": float((a - b).mean() / (c - b).mean()), "lo": float(np.quantile(s, 0.025)),
            "hi": float(np.quantile(s, 0.975))}


def g1_verdicts(scores: dict) -> dict:
    """PILOT.md §2's G1 criteria on the check-world scores."""
    lvl = paired(scores["memory"], scores["memoryless"], 0.95)
    rel = paired(scores["memory+bit"], scores["memoryless+bit"], 0.90)
    return {"level": {**lvl, "pass": bool(lvl["lo"] >= 0.5)},
            "relief": {**rel, "pass": bool(rel["lo"] >= -0.3 and rel["hi"] <= 0.3)},
            "recovered_share": recovered_share(scores["memoryless+bit"], scores["memoryless"], scores["memory"])}


def g2_verdict(scores: dict) -> dict:
    """PILOT.md §2's G2 criterion: under sham, memoryless reading the sham against memoryless."""
    d = paired(scores["memoryless+bit"], scores["memoryless"], 0.90)
    return {**d, "pass": bool(d["lo"] >= -0.3 and d["hi"] <= 0.3)}
