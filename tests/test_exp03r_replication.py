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
    return {"n2": 0.93, "p": p, "p_opposite": 1.0, "effect_interval": [lo, lo + 0.05], "margin": margin,
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


# ---- changes from the pre-registration review (D060) ----

def _one_r(p, lo, n2=0.93, margin=0.01, above=0):
    vals = [0.5] * (20 - above) + [0.95] * above
    return {"n2": n2, "p": p, "p_opposite": 1.0, "effect_interval": [lo, lo + 0.05], "margin": margin,
            "n2_interval": [0.9, 0.95], "values": vals}


def test_the_primary_reports_every_ensembles_gates_so_a_split_is_visible():
    """Astra: four ensembles passing and one failing gives five 'inconclusive' labels under the
    maximum-p rule; the gates must show which one failed."""
    sig = {"A": _one_r(0.01, 0.1), "B": _one_r(0.06, 0.1, above=2)}
    r = R.single_signal(sig, "P4")
    assert r["overall"] == "not distinctive"
    assert r["gates"]["A"] == {"graphs": 20, "at_or_above": 0, "p": 0.01, "rank_gate": True, "margin_gate": True}
    assert r["gates"]["B"]["rank_gate"] is False and r["gates"]["B"]["at_or_above"] == 2


def test_a_withheld_primary_is_written_not_omitted():
    out = {"signals": {"P4": {}, "P4_complete": False}, "counts": {"P4": {"A": 10}}}
    r = R.replication_primary(out)
    assert r["overall"] == "withheld" and "reason" in r


def test_completeness_floor_can_differ_by_ensemble():
    pilot = json.loads(PILOT.read_text(encoding="utf-8"))
    measures = {m["name"]: m for m in pilot["graphs"]}
    names = sorted(measures)
    ens = {"A": names[1:9], "B": names[9:]}
    out = R.build(measures, names[0], ens, n_boot=20, min_graphs={"A": 9, "B": 1})
    assert not any(out["signals"][s + "_complete"] for s in R.PRIMARY)
    out = R.build(measures, names[0], ens, n_boot=20, min_graphs={"A": 8, "B": 1})
    assert all(out["signals"][s + "_complete"] for s in R.PRIMARY)


def test_the_cap_is_registered_per_instance_and_cannot_be_changed_on_the_command_line(exp):
    exp.use_instance("03r")
    assert exp.MAX_HOURS == 28 and exp.cap_hours(None) == 28
    with pytest.raises(exp.ProvenanceError):
        exp.cap_hours(30.0)
    assert exp.MIN_GRAPHS == {"SH": 120, "SH-route": 240, "SH-class": 120, "SH-mirror": 120, "SH-recip": 120}
    exp.use_instance("03")
    assert exp.MAX_HOURS == 24 and exp.MIN_GRAPHS == 120


def test_the_secondary_permutation_is_fresh_in_03r_and_unchanged_in_03(exp):
    exp.use_instance("03")
    assert exp.secondary_permutation_seed("N2", 0) == 0 and exp.secondary_permutation_seed("N2perm2", 2) == 2
    exp.use_instance("03r")
    s = exp.secondary_permutation_seed("N2", 0)
    assert s != 0 and s != exp.secondary_permutation_seed("N2-rev", 0)


def test_03r_pins_the_connectome_cache(exp):
    exp.use_instance("03r")
    assert "cook2019_herm.npz" in exp.INPUT_FILES
    exp.use_instance("03")
    assert "cook2019_herm.npz" not in exp.INPUT_FILES


def _record(name, scale=1.0, prov="p", final=0.1):
    h = {"final": [final * scale, -final * scale], "steady_contrast": [0.12 * scale, 0.12 * scale],
         "after": [0.09 * scale, 0.08 * scale]}
    return {"name": name, "gains": [4.0, 3.0], "provenance": prov,
            "calibration": {"target": [0.5, 0.4], "achieved": {"forward": 0.5, "turn": 0.4}},
            "calibration_validation": {"forward": 0.51, "turn": 0.39},
            "history": {"raw_turn": h, "raw_forward": h}, "response": {"M0": {"common_turn_raw": [0.01, 0.02]}}}


@pytest.fixture()
def supplement():
    spec = importlib.util.spec_from_file_location("supp", ROOT / "experiments" / "03-generation0" / "supplement.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_supplement_counts_missing_and_failed_graphs_instead_of_crashing(supplement, tmp_path):
    exp_dir, meas = tmp_path / "exp", tmp_path / "meas"
    exp_dir.mkdir(), meas.mkdir()
    (exp_dir / "ensembles.json").write_text(json.dumps({"graphs": [{"kind": "A", "name": f"g{i}"} for i in range(4)]}))
    for name, rec in {"N2": _record("N2", 5, final=0.11), "g0": _record("g0"), "g1": _record("g1", 2),
                      "g2": {"name": "g2", "calibration_failed": "x", "provenance": "p"}}.items():
        (meas / f"{name}.json").write_text(json.dumps(rec))
    out = supplement.build_supplement(exp_dir, meas, ("N2", "N2-rev"))
    assert out["missing"] == ["N2-rev", "g3"] and out["calibration_failed"] == ["g2"]
    a = out["summary"]["A"]
    assert a["P4_turn_numerator"]["n"] == 2 and "forward_gain" in a and "validation_max_rel_deviation" in a
    assert a["graphs_at_or_above_on_P4_forward"]["N2"] == 0
    (meas / "g1.json").write_text(json.dumps(_record("g1", 2, prov="other")))
    with pytest.raises(ValueError):
        supplement.build_supplement(exp_dir, meas, ("N2",))


def test_the_supplement_masks_a_forward_ratio_below_the_floor(supplement):
    rec = _record("x", 1e-4)
    assert supplement.per_graph(rec)["P4_forward"] is None


def test_the_report_accounts_for_every_planned_graph(exp):
    planned = {"A": ["a0", "a1", "a2", "a3"]}
    measures = {"a0": {}, "a1": {"calibration_failed": "x"}, "a2": {}}
    counts = {"P1": {"A": 2}, "P3": {"A": 1}, "P4": {"A": 2}}
    acc = exp.accounting(planned, measures, counts)
    assert acc["A"] == {"planned": 4, "measured": 3, "calibration_failed": 1,
                        "valid": {"P1": 2, "P3": 1, "P4": 2}, "signal_invalid": {"P1": 0, "P3": 1, "P4": 0}}


def test_03s_p4_is_set_beside_03rs(exp):
    ours = {"P4": {"A": {"n2": 0.9, "effect_interval": [0.05, 0.1], "graphs": 5, "values": [0.1, 0.95, 0.2, 0.3, 0.4]}}}
    theirs = {"signals": {"P4": {"A": {"n2": 0.93, "effect_interval": [0.08, 0.1], "graphs": 4, "values": [0.1, 0.2, 0.3, 0.94]}}}}
    side = exp.side_by_side(ours, theirs)
    assert side["A"]["03"] == {"n2": 0.93, "effect_interval": [0.08, 0.1], "graphs": 4, "at_or_above": 1}
    assert side["A"]["03r"]["at_or_above"] == 1
