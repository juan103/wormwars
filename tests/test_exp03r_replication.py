"""Experiment 03r, the full replication of 03 (D059): the same runner and report under a second
instance with fresh graph seeds, fresh genomes (N2's included), fresh worlds and seeds, 256
routing-matched graphs, and fresh weight permutations. Instance 03 must stay exactly as it ran."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from wormwars.exp03 import measures as M
from wormwars.exp03 import report as R

ROOT = Path(__file__).parents[1]
PILOT = ROOT / "experiments" / "03-generation0" / "pilot.json"


@pytest.fixture()
def exp():
    spec = importlib.util.spec_from_file_location("exp03_script_r", ROOT / "scripts" / "exp03.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_genome_seed_is_unchanged_without_a_salt_and_independent_with_one():
    assert M.genome_seed("N2") == int.from_bytes(hashlib.sha256(b"N2").digest()[:4], "little") % (2 ** 31)
    assert M.genome_seed("N2", salt="03r:") != M.genome_seed("N2")


def test_instance_03_is_unchanged(exp):
    exp.use_instance("03")
    order = exp.run_order()
    assert len(order) == 645 and order[-5:] == ["N2", "N2-rev", "N2perm1", "N2perm2", "N2perm3"]
    assert order[:5] == ["SH-10000", "SH-route-20000", "SH-class-30000", "SH-mirror-40000", "SH-recip-50000"]
    assert exp.RUN_SEED == 3 and exp.GENOME_SALT == "" and exp.CALIBRATION_SEED == 0 and exp.VALIDATION_SEED == 1
    assert exp.WORLDS[0] == 993_000_000 and len(exp.WORLDS) == 16


def test_instance_03r_draws_everything_fresh(exp):
    exp.use_instance("03")
    old = dict(seed_base=dict(exp.SEED_BASE), worlds=set(exp.WORLDS.tolist()), run_seed=exp.RUN_SEED,
               cal=(exp.CALIBRATION_SEED, exp.VALIDATION_SEED), real=list(exp.REAL))
    exp.use_instance("03r")
    assert exp.EXP.name == "03r-replication" and exp.OUT.as_posix().endswith("runs/exp03r")
    assert exp.N_PER == {"SH": 128, "SH-route": 256, "SH-class": 128, "SH-mirror": 128, "SH-recip": 128}
    # graph seeds, including any +100 000 substitutions, never reach 03's
    for k, base in exp.SEED_BASE.items():
        assert base >= 1_000_000 and base != old["seed_base"][k]
    assert not set(exp.WORLDS.tolist()) & old["worlds"]
    assert exp.RUN_SEED != old["run_seed"] and (exp.CALIBRATION_SEED, exp.VALIDATION_SEED) != old["cal"]
    assert exp.GENOME_SALT and M.genome_seed("N2", exp.GENOME_SALT) != M.genome_seed("N2")
    assert exp.REAL == ["N2", "N2-rev", "N2perm4", "N2perm5", "N2perm6"]
    assert exp.PILOT.parent.name == "03-generation0"  # the same stimulus bank: the same probe
    assert exp.INPUT_FILES["pilot.json"] == exp.PILOT
    assert exp.INPUT_FILES["ensembles.json"].parent.name == "03r-replication"


def test_interleaving_is_proportional_so_a_budget_stop_removes_graphs_evenly(exp):
    by = {"A": [f"A{i}" for i in range(4)], "B": [f"B{i}" for i in range(8)], "C": [f"C{i}" for i in range(4)]}
    order = exp.interleave(by, ["A", "B", "C"])
    assert sorted(order) == sorted(sum(by.values(), []))
    assert order[:4] == ["A0", "B0", "C0", "B1"]
    for cut in range(1, len(order) + 1):
        pre = order[:cut]
        a, b = sum(x.startswith("A") for x in pre), sum(x.startswith("B") for x in pre)
        assert abs(b - 2 * a) <= 2


def test_building_never_overwrites_an_existing_ensemble_record(exp, tmp_path, monkeypatch):
    exp.use_instance("03")
    monkeypatch.setattr(exp, "EXP", tmp_path)
    (tmp_path / "ensembles.json").write_text("{}", encoding="utf-8")
    with pytest.raises(exp.ProvenanceError):
        exp.cmd_build(type("A", (), {"workers": 1})())


def test_provenance_names_the_instance(exp, monkeypatch):
    exp.use_instance("03r")
    # 03r's own inputs exist only after its build; hash the shared ones here
    monkeypatch.setattr(exp, "INPUT_FILES", {k: v for k, v in exp.INPUT_FILES.items() if v.exists()})
    assert exp.provenance("cpu")["instance"] == "03r"


def test_report_ranks_the_variants_it_is_given():
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    measures = {m["name"]: m for m in pilot["graphs"]}
    names = sorted(measures)
    out = R.build(measures, names[0], {"A": names[2:]}, n_boot=50, min_graphs=1, descriptive=(names[1],))
    assert list(out["ranks_descriptive"]) == [names[1]]


def _one(p, lo, margin=0.01):
    return {"p": p, "p_opposite": 1.0, "effect_interval": [lo, lo + 0.05], "margin": margin,
            "n2_interval": [0.9, 0.95], "values": list(np.linspace(0.5, 0.8, 20))}


def test_the_replication_verdict_tests_p4_alone_with_the_maximum_over_ensembles():
    """03r's primary test is P4 alone: the maximum p over the ensembles at alpha 0.05, with the
    same effect-margin gate, and no Holm over three signals (registered in 03r)."""
    sig = {"A": _one(0.04, 0.1), "B": _one(0.02, 0.1)}
    r = R.single_signal(sig, "P4")
    assert r["p_max"] == 0.04 and r["overall"] == "distinctive relative to every ensemble"
    assert r["verdicts"] == {"A": "distinctive", "B": "distinctive"}
    sig["B"] = _one(0.06, 0.1)
    assert R.single_signal(sig, "P4")["overall"] == "not distinctive"
    sig["B"] = _one(0.02, 0.005)  # significant, but the effect interval is inside the margin
    assert R.single_signal(sig, "P4")["verdicts"]["B"] != "distinctive"
