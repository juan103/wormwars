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
# 03h's own switches: both values are the switch's bounds, never a grid edge (Fable, round 2); and T = 1, the slow
# trace's own bound (it is then M itself)
SWITCHES = ("use_memory", "use_bit")
BOUNDS = {**PHYSICAL, "T": {1.0}}
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


def edges(params: dict, grid: dict, full: dict | None = None) -> list:
    """02's `_edges`: the parameters chosen at a grid edge that is not a physical bound. Only keys searched over more
    than one value are flagged, the switches never are, and a key that `full` holds is judged against `full`'s values:
    a local neighbourhood's edge inside the registered grid is not a grid edge (Fable, round 2)."""
    out = []
    for k, v in params.items():
        if k not in grid or k in SWITCHES or len(grid[k]) < 2:
            continue
        vals = sorted((full or {}).get(k, grid[k]))
        if len(vals) > 1 and v in (vals[0], vals[-1]) and v not in BOUNDS.get(k, set()):
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
    full = dict(gr["K"], **gr["FALL"], T=gr["T"])  # the registered grids, against which edges are judged
    lv = cfgs["level"]
    bit_name = next(k for k in cfgs if k != "level")
    bitc = cfgs[bit_name]

    def t(kind, grid, cfg, cond):
        """One tuning unit: (kind, params, score, condition, edges). Each unit carries its own search grid's flags, so
        the second Slow search no longer overwrites the first's (Astra, round 2)."""
        if check is not None:
            check()
        p, s = tune(MAKERS[kind], grid, cfg, iface, ids, seed, device)
        return (kind, p, s, cond, edges(_plain(p), grid, full))

    if base is None:
        fam = {"K": t("K", gr["K"], lv, "level"), "Graded": t("Graded", gr["G"], lv, "level")}
        fam["memoryless"] = fam["K"] if fam["K"][2] >= fam["Graded"][2] else fam["Graded"]
    else:
        fam = {k: (base[k]["kind"], base[k]["params"], base[k]["tuning_score"], base[k]["condition"],
                   base[k]["edges"]) for k in ("K", "Graded", "memoryless")}
    kp = fam["K"][1]
    loc = near(kp, gr["K"])
    bit = t("Bit", dict(loc, fall_turn=gr["FALL"]["fall_turn"]), bitc, bit_name)
    if check is not None:
        check()
    ml_on_bit = _score_on(fam["memoryless"], bitc, iface, ids, seed, device)
    ml = fam["memoryless"]
    # the fallback keeps the memoryless family's own flags
    fam["memoryless+bit"] = bit if bit[2] > ml_on_bit else (ml[0], ml[1], ml_on_bit, bit_name, ml[4])
    if parts == "memoryless":
        return _out(fam)
    fam["M"] = t("M", dict(loc, **gr["FALL"]), lv, "level")
    mp = fam["M"][1]
    one = lambda d: {k: [v] for k, v in d.items()}  # noqa: E731
    st = {k: mp[k] for k in _SPEED_TURN}
    fam["Slow"] = t("Slow", dict(one(st), **gr["FALL"], T=gr["T"], use_memory=[1.0], use_bit=[0.0]), lv, "level")
    fam["memory"] = max([fam["memoryless"], fam["M"], fam["Slow"]], key=lambda c: c[2])  # first maximum on ties
    src = fam["Slow"][1] if fam["memory"][0] == "Slow" else mp  # M's optimum also when memory fell back to memoryless
    bx = {k: v for k, v in src.items() if k not in ("T", "use_memory", "use_bit")}
    x = t("Slow", dict(one(bx), T=gr["T"], use_memory=[0.0, 1.0], use_bit=[0.0, 1.0]), bitc, bit_name)
    fam["memory+bit"] = max([fam["memoryless+bit"], x], key=lambda c: c[2])
    return _out(fam)


def _out(fam: dict) -> dict:
    return {k: {"kind": v[0], "params": _plain(v[1]), "tuning_score": float(v[2]), "condition": v[3],
                "edges": list(v[4])} for k, v in fam.items()}


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
