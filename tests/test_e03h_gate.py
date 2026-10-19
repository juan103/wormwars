"""03h's scripted gate (wormwars/e03h/gate.py; PILOT.md §2): 02's grids unchanged; the families nest (each richer family
scores at least its fallback on the tuning worlds); the intervals and the verdicts follow their registered rules."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

from wormwars.e03h import gate

ROOT = Path(__file__).resolve().parents[1]


def test_the_grids_are_02s():
    spec = importlib.util.spec_from_file_location("exp02_for_e03h_gate", ROOT / "scripts" / "exp02.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert gate.K_GRID == m.K_GRID and gate.FALL_GRID == m.FALL_GRID and gate.PHYSICAL == m.PHYSICAL


class FakeTune:
    """Scores a grid point by a fixed formula, as `tune_batched` would on worlds: the first maximum wins."""

    def __init__(self):
        self.calls = []

    def __call__(self, make, grid, cfg, iface, ids, seed, device):
        import itertools
        keys = sorted(grid)
        best, bs = None, -np.inf
        for vals in itertools.product(*(grid[k] for k in keys)):
            p = dict(zip(keys, vals))
            s = (p.get("slow", 0) * 0.1 + p.get("fast", 0) + 0.05 * p.get("turn", 0) + 0.2 * p.get("fall_turn", 0)
                 + 0.01 * p.get("T", 0) + 0.3 * p.get("use_bit", 0) * (cfg == "relief") + 0.1 * p.get("use_memory", 0))
            if cfg == "level":
                # memory loses under level here, so the fallback must decide
                s -= 0.5 * p.get("fall_turn", 0) + 0.01 * p.get("T", 0) + 0.1 * p.get("use_memory", 0)
            if s > bs:
                best, bs = p, s
        self.calls.append((sorted(grid), cfg))
        return best, bs


def test_the_families_nest(monkeypatch):
    monkeypatch.setattr(gate, "_score_on", lambda member, cfg, *a: member[2] - 0.01)
    fam = gate.tune_families({"level": "level", "relief": "relief"}, None, None, None, "cpu", tune=FakeTune())
    assert fam["memory"]["tuning_score"] >= fam["memoryless"]["tuning_score"]
    assert fam["memory"]["kind"] == fam["memoryless"]["kind"]  # the fallback: memory did not beat memoryless
    assert fam["memory+bit"]["tuning_score"] >= fam["memoryless+bit"]["tuning_score"]
    assert fam["memoryless"]["tuning_score"] == max(fam["K"]["tuning_score"], fam["Graded"]["tuning_score"])
    assert fam["memoryless+bit"]["condition"] == "relief" and fam["memory"]["condition"] == "level"
    assert fam["Slow"]["params"]["T"] in gate.T_GRID
    # Slow is tuned at M's speed and turn parameters, over T and the fall grid (Fable)
    m, sl = fam["M"]["params"], fam["Slow"]["params"]
    assert all(sl[k] == m[k] for k in ("slow", "fast", "threshold", "turn"))
    assert all("edges" in v for v in fam.values())


def test_g2_tunes_only_the_memoryless_families(monkeypatch):
    monkeypatch.setattr(gate, "_score_on", lambda member, cfg, *a: member[2])
    fam = gate.tune_families({"level": "level", "sham": "sham"}, None, None, None, "cpu", tune=FakeTune(),
                             parts="memoryless")
    assert set(fam) == {"K", "Graded", "memoryless", "memoryless+bit"}
    assert fam["memoryless+bit"]["condition"] == "sham"


def test_the_paired_interval_and_the_verdicts():
    rng = np.random.default_rng(0)
    base = rng.normal(1.0, 0.3, 256)
    scores = {"memoryless": base, "memory": base + 0.9 + rng.normal(0, 0.05, 256),
              "memoryless+bit": base + 0.8, "memory+bit": base + 0.85 + rng.normal(0, 0.05, 256)}
    v = gate.g1_verdicts(scores)
    assert v["level"]["pass"] and v["relief"]["pass"]
    assert v["level"]["level"] == 0.95 and v["relief"]["level"] == 0.90
    assert abs(v["recovered_share"]["estimate"] - 0.8 / 0.9) < 0.02
    bad = dict(scores, **{"memory+bit": base + 1.3})
    assert not gate.g1_verdicts(bad)["relief"]["pass"]  # memory beyond the bit by 0.5: outside +-0.3
    weak = dict(scores, memory=base + 0.4)
    assert not gate.g1_verdicts(weak)["level"]["pass"]
    assert gate.g2_verdict({"memoryless": base, "memoryless+bit": base + 0.05})["pass"]
    assert not gate.g2_verdict({"memoryless": base, "memoryless+bit": base + 0.4})["pass"]


class NoBitTune(FakeTune):
    """Under relief the bit does not help, and reading it costs: the memory + bit family must fall back."""

    def __call__(self, make, grid, cfg, iface, ids, seed, device):
        import itertools
        keys = sorted(grid)
        best, bs = None, -np.inf
        for vals in itertools.product(*(grid[k] for k in keys)):
            p = dict(zip(keys, vals))
            s = p.get("fast", 0) + 0.1 * p.get("slow", 0) - 0.5 * p.get("use_bit", 0) - 0.4 * p.get("use_memory", 0)                 + 0.2 * p.get("fall_turn", 0) * (cfg == "relief")
            if s > bs:
                best, bs = p, s
        return best, bs


def test_the_memory_plus_bit_family_falls_back(monkeypatch):
    monkeypatch.setattr(gate, "_score_on", lambda member, cfg, *a: member[2] - 0.01)
    fam = gate.tune_families({"level": "level", "relief": "relief"}, None, None, None, "cpu", tune=NoBitTune())
    assert fam["memory+bit"]["kind"] == fam["memoryless+bit"]["kind"]
    assert fam["memory+bit"]["tuning_score"] == fam["memoryless+bit"]["tuning_score"]


def test_g2_reuses_g1s_families_and_checks_the_cap(monkeypatch):
    monkeypatch.setattr(gate, "_score_on", lambda member, cfg, *a: member[2])
    tune = FakeTune()
    g1 = gate.tune_families({"level": "level", "relief": "relief"}, None, None, None, "cpu", tune=tune)
    tune2, checks = FakeTune(), []
    g2 = gate.tune_families({"level": "level", "sham": "sham"}, None, None, None, "cpu", tune=tune2,
                            parts="memoryless", base=g1, check=lambda: checks.append(1))
    assert [c[1] for c in tune2.calls] == ["sham"]  # only the bit family is tuned again
    assert g2["memoryless"] == g1["memoryless"] and g2["K"]["params"] == g1["K"]["params"]
    assert len(checks) >= 2  # before the tuning unit and before the fallback's scoring
