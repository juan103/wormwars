"""03h's scripted gate (experiments/03h-history-use/PILOT.md §2; DESIGN.md v3.3 §4): nested families tuned on tuning
worlds under their own condition, each scored once on check worlds, with paired bootstrap intervals over the check
worlds (02's `_paired`)."""

from __future__ import annotations

import numpy as np

from ..exp02 import scripted
from .scripted import BitKinesis, SlowMemoryKinesis

# 02's grids and physical-edge set (scripts/exp02.py K_GRID, FALL_GRID, PHYSICAL; tests/test_e03h_gate.py checks they
# are still equal)
K_GRID = {"slow": [0.0, 0.25, 0.5, 0.75, 1.0], "fast": [0.5, 0.75, 1.0],
          "threshold": [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 0.6, 1.0, 1.5, 2.0, 3.0, 5.0],
          "turn": [0.0, 0.1, 0.2, 0.4, 0.7]}
FALL_GRID = {"fall_turn": [0.4, 0.7, 1.0], "fall_threshold": [0.0, 0.001, 0.003]}
PHYSICAL = {"fast": {1.0}, "slow": {0.0, 1.0}, "turn": {0.0}, "fall_turn": {1.0}, "fall_threshold": {0.0},
            "threshold": {5.0}, "k": {8192.0}}
G_GRID = {"slow": [0.0, 0.25, 0.5, 0.75, 1.0], "fast": [0.5, 0.75, 1.0], "scale": [0.03, 0.1, 0.3, 1.0, 3.0],
          "turn": [0.0, 0.1, 0.2, 0.4, 0.7]}
T_GRID = [1.0, 2.0, 5.0, 10.0, 20.0]
GRIDS = {"K": K_GRID, "G": G_GRID, "FALL": FALL_GRID, "T": T_GRID}

MAKERS = {
    "K": lambda **p: scripted.LevelKinesis(**p),
    "Graded": lambda **p: scripted.GradedKinesis(**p),
    "M": lambda **p: scripted.MemoryKinesis(**p),
    "Bit": lambda **p: BitKinesis(**p),
    "Slow": lambda **p: SlowMemoryKinesis(**p),
}
_SPEED_TURN = ("slow", "fast", "threshold", "turn")


def near(params: dict, grid: dict) -> dict:
    """Each parameter at its grid neighbours (02's `_near`), for the keys of `grid`."""
    out = {}
    for k, vals in grid.items():
        vals = list(vals)
        i = vals.index(params[k])
        out[k] = vals[max(0, i - 1): i + 2]
    return out


def edges(params: dict, grid: dict) -> list:
    """02's `_edges`: the parameters chosen at a grid edge that is not a physical bound."""
    out = []
    for k, v in params.items():
        if k not in grid:
            continue
        vals = sorted(grid[k])
        if len(vals) > 1 and v in (vals[0], vals[-1]) and v not in PHYSICAL.get(k, set()):
            out.append(f"{k}={v}")
    return out


def tune_families(cfgs: dict, iface, ids, seed, device, tune=scripted.tune_batched, parts: str = "all",
                  grids: dict | None = None, check=None, base: dict | None = None) -> dict:
    """`cfgs` maps a condition ("level", and "relief" or "sham") to its configuration. Returns, per family, its kind,
    parameters, tuning score, condition and grid-edge flags; the "+ bit" families are tuned under the condition that
    is not "level". `parts` = "memoryless" stops after the memoryless + bit family (G2). `base`, if given, supplies
    the K, Graded and memoryless families already tuned (G2 reuses G1's, Fable). `check()` runs before each tuning
    unit (the cap; Astra). `grids` defaults to the registered ones.

    Nesting (02's rule, PILOT.md §2): K and Graded on their grids; memoryless = the better. Bit around K's optimum,
    falling back to memoryless. M around K's optimum with FALL_GRID; Slow at M's speed and turn parameters over T x
    FALL_GRID (so T = 1 contains M itself; Fable); memory = the best of memoryless, M and Slow. Memory + bit: Slow at the
    memory optimum's speed, turn and fall parameters (M's when memory fell back to memoryless) over T, with use_memory
    and use_bit each in {0, 1}, or the memoryless + bit optimum, whichever is better."""
    gr = dict(GRIDS, **(grids or {}))
    lv = cfgs["level"]
    bit_name = next(k for k in cfgs if k != "level")
    bitc = cfgs[bit_name]
    edge_grid, preset = {}, {}

    def t(kind, grid, cfg):
        if check is not None:
            check()
        edge_grid[kind] = grid
        return tune(MAKERS[kind], grid, cfg, iface, ids, seed, device)

    if base is None:
        kp, ks = t("K", gr["K"], lv)
        gp, gs = t("Graded", gr["G"], lv)
        fam = {"K": ("K", kp, ks, "level"), "Graded": ("Graded", gp, gs, "level")}
        fam["memoryless"] = fam["K"] if ks >= gs else fam["Graded"]
    else:
        fam = {k: (base[k]["kind"], base[k]["params"], base[k]["tuning_score"], base[k]["condition"])
               for k in ("K", "Graded", "memoryless")}
        preset = {k: base[k]["edges"] for k in ("K", "Graded", "memoryless")}
        kp = fam["K"][1]
    loc = near(kp, gr["K"])
    bp, bs = t("Bit", dict(loc, fall_turn=gr["FALL"]["fall_turn"]), bitc)
    if check is not None:
        check()
    ml_on_bit = _score_on(fam["memoryless"], bitc, iface, ids, seed, device)
    fam["memoryless+bit"] = ("Bit", bp, bs, bit_name) if bs > ml_on_bit else (
        fam["memoryless"][0], fam["memoryless"][1], ml_on_bit, bit_name)
    if parts == "memoryless":
        return _out(fam, edge_grid, preset)
    mp, ms = t("M", dict(loc, **gr["FALL"]), lv)
    one = lambda d: {k: [v] for k, v in d.items()}  # noqa: E731
    st = {k: mp[k] for k in _SPEED_TURN}
    sp, ss = t("Slow", dict(one(st), **gr["FALL"], T=gr["T"], use_memory=[1.0], use_bit=[0.0]), lv)
    fam["M"], fam["Slow"] = ("M", mp, ms, "level"), ("Slow", sp, ss, "level")
    fam["memory"] = max([fam["memoryless"], fam["M"], fam["Slow"]], key=lambda c: c[2])  # first maximum on ties
    src = sp if fam["memory"][0] == "Slow" else mp  # M's optimum also when memory fell back to memoryless
    bx = {k: v for k, v in src.items() if k not in ("T", "use_memory", "use_bit")}
    xp, xs = t("Slow", dict(one(bx), T=gr["T"], use_memory=[0.0, 1.0], use_bit=[0.0, 1.0]), bitc)
    fam["memory+bit"] = max([fam["memoryless+bit"], ("Slow", xp, xs, bit_name)], key=lambda c: c[2])
    return _out(fam, edge_grid, preset)


def _out(fam: dict, edge_grid: dict, preset: dict) -> dict:
    out = {}
    for k, v in fam.items():
        kind, params = v[0], _plain(v[1])
        if k in preset:
            e = preset[k]
        elif k == "memoryless+bit" and kind != "Bit":  # the fallback: the memoryless family's own flags
            e = out["memoryless"]["edges"] if "memoryless" in out else edges(params, edge_grid.get(kind, {}))
        else:
            e = edges(params, edge_grid.get(kind, {}))
        out[k] = {"kind": kind, "params": params, "tuning_score": float(v[2]), "condition": v[3], "edges": e}
    return out


def _plain(p: dict) -> dict:
    return {k: float(v) for k, v in p.items()}


def _score_on(member, cfg, iface, ids, seed, device) -> float:
    kind, params = member[0], member[1]
    return float(scripted.score_policy(cfg, iface, MAKERS[kind](**params), ids, seed, device).mean())


def check_scores(fams: dict, cfgs: dict, iface, ids, seed, device, check=None) -> dict:
    """Each family's chosen policy scored once on the check worlds, under its condition: per-world arrays."""
    out = {}
    for k, v in fams.items():
        if check is not None:
            check()
        out[k] = np.asarray(scripted.score_policy(cfgs[v["condition"]], iface, MAKERS[v["kind"]](**v["params"]), ids,
                                                  seed, device), dtype=np.float64)
    return out


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
