"""M6 option 0 (docs/memory/M6-0-PLAN.md): the probe's input context (a food mapping's interface and a bank), and the
driver's pieces: drift, persistence, the copied second pass, the genome list and the stored-configuration check."""

from __future__ import annotations

import dataclasses
import json
import os
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m6"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m4"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))

import common as c  # noqa: E402
import pilot as P  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp03 import measures  # noqa: E402

REMAPS = json.loads((grid.EXP02_DIR / "remaps.json").read_text(encoding="utf-8"))["sets"]
GENOMES = ROOT / "runs" / "exp02-screening"
local_genomes = pytest.mark.skipif(not (GENOMES / "T1-M0-N2-run00-g39.npz").exists(),
                                   reason="02's genomes are local, not in git")


@pytest.fixture(scope="module")
def panel():
    return c.S.genomes(c.S.CON, 4, 4242)


@pytest.fixture(scope="module")
def M(tmp_path_factory):
    os.environ["MEMORY_M6_OUT"] = str(tmp_path_factory.mktemp("m6"))
    import m6_0
    yield m6_0
    os.environ.pop("MEMORY_M6_OUT", None)


def iface(mapping):
    return grid.interface_for(c.S.CON, mapping, REMAPS)


def bank_with_food(x):
    return dict(c.S.BANK, food_left=x, food_right=x)


# --------------------------------------------------------------------------------------------------- the input context
def test_the_default_input_is_the_m0_interface_and_03mcs_bank(panel):
    g, cfg = panel
    n, s = g.spec.n, g.n_strains
    want = torch.cat([c.S._current(c.S.IFACE, cfg, dict(c.S.BANK, food_left=lv, food_right=lv), n, s, "cpu")
                      for lv in (0.1, 0.7)], 1)
    assert torch.equal(c.at(cfg, n, s, [0.1, 0.7]), want)
    assert c.final_food() == (c.S.BANK["food_left"] + c.S.BANK["food_right"]) / 2


@pytest.mark.parametrize("mapping, food", [("M0", None), ("R1", 0.9), ("MS", 0.3)])
def test_the_probe_equals_the_library_history_measure(panel, mapping, food):
    """measures.history is 02b's test in library form, with the interface and bank passed explicitly: the probe's
    tick-0 and tick-5 read-out differences are its "final" and "after" (Fable). M0 with 03mc's bank is the old path,
    by an independent route (Astra)."""
    g, cfg = panel
    i, b = iface(mapping), (c.S.BANK if food is None else bank_with_food(food))
    h = measures.history(g, cfg, i, b, after=5)["raw_turn"]
    if food is None:
        run = P.probe_states(g, cfg, ticks=5, record=False)
    else:
        with c.probe_input(i, b):
            run = P.probe_states(g, cfg, ticks=5, record=False)
    y = run["y"]
    assert np.allclose(y[:, 0, 0] - y[:, 0, 1], np.asarray(h["final"]), atol=1e-6)
    assert np.allclose(y[:, 5, 0] - y[:, 5, 1], np.asarray(h["after"]), atol=1e-6)
    if food is not None:  # and the context matters
        plain = P.probe_states(g, cfg, ticks=5, record=False)["y"]
        assert not np.allclose(plain[:, 0, 0] - plain[:, 0, 1], y[:, 0, 0] - y[:, 0, 1], atol=1e-6)


def test_inside_the_context_the_food_current_sits_on_the_remapped_sensors(panel):
    g, cfg = panel
    n, s = g.spec.n, g.n_strains
    for m in ("MS", "R1", "R2"):
        i = iface(m)
        with c.probe_input(i, c.S.BANK):
            d = (c.at(cfg, n, s, [0.5]) - c.at(cfg, n, s, [0.0]))[0, 0]
            big = (c.at(cfg, n, s, [1e6]) - c.at(cfg, n, s, [0.0]))[0, 0]
        food = {int(j): float(gain) for name, j, gain in zip(i.signal_names, i.sensor_neuron, i.sensor_gain)
                if name in ("food_left", "food_right")}
        assert set(np.nonzero(d.numpy())[0].tolist()) == set(food), m
        assert not set(food) & set(c.FOOD_SENSORS), m  # none of M0's food sensors
        for j, gain in food.items():
            assert abs(float(d[j]) - 0.5 * gain * cfg.brain.input_gain) < 1e-5 or abs(gain) == 0, m
        assert float(big.abs().max()) <= 2 * cfg.brain.input_max + 1e-6  # the clamp holds


def test_the_oscillation_checks_rerun_runs_inside_the_context(monkeypatch):
    """The rerun runs only on candidates, so a panel test is vacuous (Fable): its recording, read from the period
    search's argument, equals the first pass's tail tick for tick inside the context, and not outside it."""
    g, cfg = c.S.genomes(c.S.CON, 1, 4243)
    i, b = iface("R1"), bank_with_food(0.9)
    seen = []
    monkeypatch.setattr(P.K, "returns", lambda x, *a, **k: seen.append(np.array(x)) or None)
    with c.probe_input(i, b):
        run = P.probe_states(g, cfg)
        P.oscillation_check(g, cfg, run["end"][0, 0], run["tail"][0, :, 0], run["cur"][:1, :1], (0.25, 1.75), 0,
                            cap=3)
    P.oscillation_check(g, cfg, run["end"][0, 0], run["tail"][0, :, 0], run["cur"][:1, :1], (0.25, 1.75), 0, cap=3)
    per_tick = [x[P.SUBSTEPS - 1::P.SUBSTEPS] for x in seen]
    assert np.array_equal(per_tick[0], run["tail"][0, :, 0])
    assert not np.allclose(per_tick[1], run["tail"][0, :, 0], atol=1e-6)


def test_the_second_pass_hold_continues_the_first_pass_inside_the_context(panel, M):
    g, cfg = panel
    with c.probe_input(iface("R2"), bank_with_food(0.9)):
        short = P.probe_states(g, cfg, ticks=40, record=False)
        long_ = P.probe_states(g, cfg, ticks=60, record=False)
        hold = M.continue_hold(g, cfg, short["end"], 20, tail=5)
    assert torch.equal(hold["end"], long_["end"])
    assert torch.equal(hold["cur"], long_["cur"])


def test_the_copied_second_pass_equals_m4es(panel, M):
    import m4e
    g, cfg = panel
    with c.probe_input(iface("R1"), bank_with_food(0.9)):
        run = P.probe_states(g, cfg, ticks=30, record=False)
        mine = M.continue_hold(g, cfg, run["end"], 25, tail=10)
        theirs = m4e.continue_hold(g, cfg, run["end"], 25, tail=10)
    for k in ("end", "cur", "pre_tail"):
        assert torch.equal(mine[k], theirs[k]), k
    assert np.array_equal(mine["tail"], theirs["tail"])
    import ast
    import inspect
    import textwrap

    def body(f):  # the code without its docstring and comments
        fn = ast.parse(textwrap.dedent(inspect.getsource(f))).body[0]
        return [ast.dump(x) for x in fn.body[1:]]
    assert body(M.second_pass) == body(m4e.second_pass)


def test_the_context_restores_the_defaults_and_refuses_nesting(panel):
    g, cfg = panel
    with pytest.raises(RuntimeError, match="inside"):
        with c.probe_input(iface("R2"), bank_with_food(0.9)):
            raise RuntimeError("inside")
    test_the_default_input_is_the_m0_interface_and_03mcs_bank(panel)
    with c.probe_input(iface("R1"), bank_with_food(0.9)):
        with pytest.raises(RuntimeError, match="nest"):
            with c.probe_input(iface("R2"), c.S.BANK):
                pass
        assert c.final_food() == 0.9  # the refused inner context changed nothing
    with c.probe_input(iface("MS"), bank_with_food(0.3)):  # successive contexts
        assert c.final_food() == 0.3
    test_the_default_input_is_the_m0_interface_and_03mcs_bank(panel)


def test_the_context_refuses_an_interface_with_another_read_out():
    other = dataclasses.replace(c.S.IFACE, turn_plus=c.S.IFACE.turn_minus, turn_minus=c.S.IFACE.turn_plus)
    with pytest.raises(ValueError):
        with c.probe_input(other, c.S.BANK):
            pass


# ------------------------------------------------------------------------------------------------------------- driver
def test_drift_is_39_mutations_on_its_own_generator(panel, M):
    g, cfg = panel
    task = grid.task_config(c.S.genomes(c.S.CON, 1, 1)[1], "T1")
    seed = M.drift_seed("T1-M0-N2-run00", 2)
    gen = torch.Generator(device="cpu").manual_seed(seed)
    want = g.clone()
    for _ in range(39):
        want.mutate(task.mutation, generator=gen)
    got = M.drifted(g, task, seed)
    for k in ("w", "g", "tau", "bias"):
        assert torch.equal(getattr(got, k), getattr(want, k)), k
    assert not torch.equal(got.w, g.w)
    seeds = {M.drift_seed(k, r) for k in ("T1-M0-N2-run00", "T1-R1-N2-run00") for r in range(4)}
    assert len(seeds) == 8 and all(0 <= s < 2 ** 63 for s in seeds)
    assert M.drift_seed("T1-M0-N2-run00", 2) == seed  # from the key, not an order


def test_persistence_measures_on_constructed_differences(M):
    T = 2000
    t = np.arange(T + 1)
    rows = {"decay": 0.2 * 0.9 ** t, "flat": np.full(T + 1, 0.2), "tiny": 1e-4 * 0.5 ** t,
            "rebound": np.where((t < 10) | ((t >= 50) & (t < 60)), 0.2, 0.0)}
    y = np.zeros((len(rows), T + 1, 2))
    for k, d in enumerate(rows.values()):
        y[k, :, 0] = d
    p = dict(zip(rows, M.persistence(y)))
    tau = int(np.ceil(np.log(0.1) / np.log(0.9)))  # the first tick with 0.9^t < 0.1
    assert p["decay"]["tau_stay"] == tau and p["decay"]["tau_first"] == tau and not p["decay"]["returns"]
    assert abs(p["decay"]["r5"] - 0.9 ** 5) < 1e-12
    assert p["flat"]["tau_stay"] is None and p["flat"]["tau_first"] is None  # censored: beyond 2000
    assert not p["tiny"]["eligible"] and "tau_stay" not in p["tiny"]  # below the start floor
    assert p["rebound"]["tau_first"] == 10 and p["rebound"]["tau_stay"] == 60 and p["rebound"]["returns"]


@local_genomes
def test_a_changed_stored_configuration_stops_the_run(M):
    r = next(x for x in M.t1_records() if x["key"] == "T1-M0-N2-run00")
    cfg, _, spec = M.setup(r)
    M.load_one(r, "g39", spec, cfg)
    bad = cfg.copy()
    bad.brain.input_gain = cfg.brain.input_gain * 2
    with pytest.raises(M.Stop, match="stored brain configuration"):
        M.load_one(r, "g39", spec, bad)


@local_genomes
def test_the_genome_list_is_the_t1_files_and_a_missing_one_stops_it(M, tmp_path, monkeypatch):
    M.stage_genomes()
    saved = json.loads((M.OUT / "genomes.json").read_text(encoding="utf-8"))
    assert saved["counts"] == M.EXPECT and saved["blocks"] == 30
    files = sorted(GENOMES.glob("T1-*.npz"))
    for f in files:
        if f.name != "T1-R2-SH5-run01-g39.npz":
            shutil.copy(f, tmp_path / f.name)
    monkeypatch.setattr(M, "GENOMES", tmp_path)
    with pytest.raises(M.Stop, match="genome counts"):
        M.stage_genomes()


def test_the_driver_hides_the_gpu_when_run(M):
    src = Path(M.__file__).read_text(encoding="utf-8")
    assert src.index('os.environ["CUDA_VISIBLE_DEVICES"] = ""') < src.index("import torch")
    assert 'CUDA was initialised' in src


@local_genomes
def test_02bs_module_runs_on_the_cpu(M):
    assert M.analyse().DEV == "cpu"
    r = M.t1_records()[0]
    assert M.setup(r)[2].device.type == "cpu"


# ------------------------------------------------------------------------------------------------------------- reader
def _world(tmp, g39_class="fading", drift_class="fading", n_blocks=6, runs_per_block=2, g39_tau=50, drift_tau=50,
           drift_a=0.1, unresolved_g39=0, history_off=False, audit_fail=False, secondary=None, drop=None):
    """A synthetic run folder: n_blocks x runs_per_block runs, each with g00, g39 and four drift genomes; two runs
    with 02b history values that match (unless history_off)."""
    genomes, rows = [], []
    banks = {"own": {}, "03mc": dict(food_left=0.5, food_right=0.5)}
    history = {}
    k = 0
    for b in range(n_blocks):
        for r in range(runs_per_block):
            key = f"T1-M{r}-SH{b}-run00"
            banks["own"][key] = dict(food_left=0.4, food_right=0.4)
            for label in ("g00", "g39", "drift0", "drift1", "drift2", "drift3"):
                tag = "drift" if label.startswith("drift") else label
                cls = g39_class if tag == "g39" else drift_class if tag == "drift" else "fading"
                if tag == "g39" and k < unresolved_g39:
                    cls = "unresolved"
                a = drift_a if tag == "drift" else 0.1
                tau = g39_tau if tag == "g39" else drift_tau
                genomes.append({"key": key, "label": label, "tag": tag, "block": f"SH{b}-run00",
                                "mapping": f"M{r}", "family": "SH", "graph": f"SH{b}"})
                rows.append({"key": key, "label": label, "tag": tag, "class": cls, "reason": None, "a": a,
                             "d5": 0.09, "eligible": a >= 1e-3,
                             **({"tau_stay": tau, "r5": 0.9, "r30": 0.2, "r100": 0.01, "returns": False}
                                if a >= 1e-3 else {})})
            if k < 2:
                off = 2.0 if history_off else 1.0
                history[key] = {"typical_food": 0.4,
                                **{t: {"raw_turn": {"final": 0.1 * off, "after": -0.09}} for t in ("g00", "g39")},
                                "drift": [{"raw_turn": {"final": 0.05, "after": 0.04}}] * 4}
            k += 1
    (tmp / "genomes.json").write_text(json.dumps({"genomes": genomes, "counts": {}, "blocks": n_blocks,
                                                  "distinct_g00": 1}))
    (tmp / "banks.json").write_text(json.dumps(banks))
    for bank in ("own", "03mc"):
        rs = [dict(x) for x in rows]
        if bank == "03mc" and secondary:
            for x in rs:
                if x["tag"] == "g39":
                    x["class"] = secondary
        audit = [0]
        rec = {"0": {"class": "separate states" if audit_fail else "fading", "reason": None, "root_distance": 0,
                     "readout_difference": 0}}
        rs[0]["class"] = "fading"
        (tmp / f"first-{bank}.json").write_text(json.dumps({"bank": bank, "rows": rs}))
        if drop != f"second-{bank}":
            (tmp / f"second-{bank}.json").write_text(json.dumps({"bank": bank, "audit": audit, "ids": [0],
                                                                 "records": rec}))
    hist = tmp / "history.json"
    hist.write_text(json.dumps(history))
    return hist


@pytest.fixture
def RD(monkeypatch):
    import m6_0_read
    return m6_0_read


def _read(RD, tmp_path, monkeypatch, **kw):
    monkeypatch.setattr(RD, "HISTORY", _world(tmp_path, **kw))
    return RD.read(tmp_path)


def test_reader_enrichment(RD, tmp_path, monkeypatch):
    res = _read(RD, tmp_path, monkeypatch, g39_class="separate states")
    assert res["words"]["switches"].startswith("enrichment") and res["consistency"]["passes"]


def test_reader_negative_wording(RD, tmp_path, monkeypatch):
    res = _read(RD, tmp_path, monkeypatch)
    assert res["words"]["switches"].startswith("We did not detect enrichment") and "0 were found" in \
        res["words"]["switches"]
    assert res["words"]["persistence"].startswith("the history effect's persistence is not distinguishable")


def test_reader_too_few_switches_is_negative(RD, tmp_path, monkeypatch):
    res = _read(RD, tmp_path, monkeypatch, n_blocks=2, g39_class="separate states")  # 4 switches, none in drift
    assert res["words"]["switches"].startswith("We did not detect") and "4 were found" in res["words"]["switches"]


@pytest.mark.parametrize("kw, why", [({"drop": "second-03mc"}, "incomplete"), ({"history_off": True}, "consistency"),
                                     ({"audit_fail": True}, "audited"),
                                     ({"g39_class": "separate states", "unresolved_g39": 9}, "straddle")])
def test_reader_inconclusive_causes(RD, tmp_path, monkeypatch, kw, why):
    res = _read(RD, tmp_path, monkeypatch, **kw)
    assert res["words"]["switches"].startswith("inconclusive") and why in res["words"]["switches"]
    assert "persistence" not in res["words"]


def test_reader_censoring_ranks_highest(RD, tmp_path, monkeypatch):
    res = _read(RD, tmp_path, monkeypatch, g39_tau=None, drift_tau=1999)
    assert res["primary"]["persistence"] == "lengthened" and res["primary"]["persistence_vs_drift"]["mean"] == 0.5
    res = _read(RD, tmp_path, monkeypatch, g39_tau=10, drift_tau=None)
    assert res["primary"]["persistence"] == "shortened"


def test_reader_skips_a_run_without_an_eligible_drift_replicate(RD, tmp_path, monkeypatch):
    res = _read(RD, tmp_path, monkeypatch, drift_a=1e-4)
    p = res["primary"]["persistence_vs_drift"]
    assert p["runs_skipped"] == 12 and p["blocks"] == 0 and res["primary"]["persistence"] == "not computable"


def test_reader_secondary_only_positive_is_a_dependence_on_input(RD, tmp_path, monkeypatch):
    res = _read(RD, tmp_path, monkeypatch, secondary="separate states")
    assert res["words"]["switches"].startswith("We did not detect") and "dependence on input" in res["words"]["input"]


def _row(key, label, a=0.1, r=0.5, eligible=True, returns=False, cls="fading", tau=50, block=0):
    return {"key": key, "label": label, "tag": label.rstrip("0123456789") if label.startswith("drift") else label,
            "a": a, "r5": r, "r30": r, "r100": r, "eligible": eligible, "returns": returns, "class": cls,
            "tau_stay": tau, "block": block}


def test_the_fading_profile_is_over_eligible_genomes_with_absolute_differences(RD):
    rows = [_row("k", "g39", a=0.2, r=0.5, returns=True), _row("k", "g39", a=0.4, r=0.25),
            _row("k", "g39", a=9.0, r=9.0, eligible=False, returns=True)]
    p = RD.fading_profile(rows)["g39"]
    assert p["eligible"] == 2 and p["a"] == pytest.approx(0.3) and p["r30"] == pytest.approx(0.375)
    assert p["d30"] == pytest.approx(0.1) and p["returns"] == 1  # medians of a * r, not median a times median r
    assert RD.fading_profile(rows)["g00"]["eligible"] == 0


def test_fading_only_drops_a_censored_switch_replicate(RD):
    rows = []
    for b in range(4):
        k = f"run{b}"
        rows += [_row(k, "g39", tau=40, block=b), _row(k, "g00", tau=40, block=b),
                 _row(k, "drift0", tau=None, cls="separate states", block=b), _row(k, "drift1", tau=40, block=b)]
    assert RD.compare_persistence(rows, "drift")["mean"] == pytest.approx(-0.25)
    fo = RD.fading_only(rows)
    assert fo["drift"]["mean"] == pytest.approx(0.0) and fo["drift"]["runs_skipped"] == 0
    rows[0]["class"] = "separate states"  # a non-fading g39 skips its run
    assert RD.fading_only(rows)["drift"]["runs_skipped"] == 1
