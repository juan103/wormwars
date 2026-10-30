"""M6, step 2 (docs/memory/M6-STEP2-PLAN.md): the time-scale intervention (an exact rescaling of the discrete update,
no clamping, the interior arm's unscaled boundary), the batch composition, the genomes against M6-0's, and the
reader's readings, wordings and guards."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "memory_m6"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m2"))
sys.path.insert(0, str(ROOT / "scripts" / "memory_m1"))

import common as c  # noqa: E402
from wormwars.brain import Brain  # noqa: E402

local_genomes = pytest.mark.skipif(not (ROOT / "runs" / "exp02-screening" / "T1-M0-N2-run00-g39.npz").exists(),
                                   reason="02's genomes are local, not in git")


@pytest.fixture(scope="module")
def S(tmp_path_factory):
    os.environ["MEMORY_M6_STEP2_OUT"] = str(tmp_path_factory.mktemp("step2"))
    import step2
    yield step2
    os.environ.pop("MEMORY_M6_STEP2_OUT", None)


@pytest.fixture
def R(tmp_path, monkeypatch):
    import step2_read
    monkeypatch.setattr(step2_read, "OUT", tmp_path)
    return step2_read


@pytest.fixture(scope="module")
def panel():
    import dataclasses
    g, cfg = c.S.genomes(c.S.CON, 2, 4545)
    g.cfg = dataclasses.replace(g.cfg, substeps=32)
    return g, cfg


def test_scaling_is_an_exact_time_rescaling(S, panel):
    g, cfg = panel
    v = torch.randn(2, 2, g.spec.n) * 0.3
    cur = c.at(cfg, g.spec.n, g.n_strains, [0.2, 0.2])
    intact = Brain(g)
    two = intact.step(intact.step(v, cur), cur)
    half = Brain(S.scaled(g, 0.5)).step(v, cur)       # tau x 0.5, 64 substeps: one tick = two intact ticks
    assert torch.equal(half, two)
    four = Brain(S.scaled(g, 2)).step(Brain(S.scaled(g, 2)).step(v, cur), cur)   # two ticks at k = 2 = one intact
    assert torch.equal(four, intact.step(v, cur))


def test_scaling_never_clamps_and_keeps_the_boundary(S, panel):
    g, cfg = panel
    q = S.scaled(g, 0.25)
    assert q.cfg.substeps == 128 and torch.equal(q.tau, g.tau * 0.25) and float(q.tau.min()) < cfg.brain.tau_min
    keep = [0, 5, 7]
    p = S.scaled(g, 0.25, keep=keep)
    assert torch.equal(p.tau[:, keep], g.tau[:, keep]) and torch.equal(p.tau[:, 1], g.tau[:, 1] * 0.25)
    assert torch.equal(g.tau, panel[0].tau) and g.cfg.substeps == 32   # the original is untouched
    with pytest.raises(SystemExit):
        S.scaled(g, 0.3)


def test_the_boundary_is_the_sensory_and_motor_neurons(S):
    iface = c.S.IFACE
    b = set(S.boundary(iface))
    want = set(map(int, iface.sensor_neuron)) | set(map(int, iface.turn_plus)) | set(map(int, iface.turn_minus)) \
        | set(map(int, iface.forward_plus)) | set(map(int, iface.forward_minus)) | set(map(int, iface.pump_neurons))
    assert b == want and len(b) > 20


def test_the_batch_composition(S):
    t1 = S.batches({"task": "T1"})
    assert [a for a, _ in t1] == [0.25, 0.5, 1, 2, 4, S.INTERIOR, S.ALONE]
    assert dict(t1)[0.25] == ["g39", "g00", "drift0"] and dict(t1)[0.5] == ["g39"] and dict(t1)[S.INTERIOR] == ["g39"]
    assert dict(t1)[S.ALONE] == ["g39"]
    assert S.batches({"task": "T0"}) == [(k, ["g39"]) for k in S.KS]


@local_genomes
def test_the_genomes_match_m6_0(S):
    r = [x for x in S.M.t1_records() if x["key"] == "T1-M0-N2-run00"][0]
    cfg, iface, spec = S.M.setup(r)
    gs = S.run_genomes(r, cfg, spec)
    m60 = {(x["key"], x["label"]): x["param_sha256"]
           for x in json.loads((S.M6_0 / "genomes.json").read_text(encoding="utf-8"))["genomes"]}
    assert all(S.M.param_hash(g) == m60[(r["key"], lb)] for lb, g in gs.items())


# ------------------------------------------------------------------------------------------------------------- reader
def _arm(v):
    return {"mean": float(v), "worlds": [float(v)] * 32}


def _write(path, R, n_blocks=8, g39=(1.0, 0.7), g00=(1.0, 1.0), drift=(1.0, 1.0), cont=(10.0, 3.0, 20.0),
           crit_off=False, drop_probe=False, t0=(1.0, 0.9), wobble=0.0, drop_arm=None, ms_drop=None):
    genomes, scores, probe, crit = [], {}, {}, {}
    for b in range(n_blocks):
        for m in ("M0", "R1", "MS"):
            key = f"T1-{m}-SH{b}-run00"
            genomes += [{"key": key, "task": "T1", "block": f"SH{b}-run00", "mapping": m, "label": lb,
                         "tau": {"median": 3.0 + b, "at_min": 0.0, "at_max": 0.0}} for lb in ("g39", "g00", "drift0")]
            low = (ms_drop if (m == "MS" and ms_drop is not None) else g39[1]) * (1 + wobble * (-1) ** b)
            arms = {"0.25": low, "0.5": 0.9 * g39[0], "1": g39[0], "2": 1.0, "4": 0.95, "interior 0.25": 0.8,
                    "1 alone": 0.9 * g39[0]}
            scores[key] = {"g39": {a: _arm(v * (1 + 0.01 * b)) for a, v in arms.items()},
                           "g00": {a: _arm(v) for a, v in (("0.25", g00[1]), ("1", g00[0]), ("4", 1.0))},
                           "drift0": {a: _arm(v) for a, v in (("0.25", drift[1]), ("1", drift[0]), ("4", 1.0))}}
            p = {a: {"a_written_at_1": 0.1, "continued_integral": v, "a_full": 0.1, "full_integral": v}
                 for a, v in (("1", cont[0]), ("0.25", cont[1]), ("4", cont[2]), ("0.5", 6.0), ("2", 14.0),
                              ("interior 0.25", 4.0))}
            probe[key] = {"g39": p}
            if m == "M0":
                crit[key] = {"intact": g39[0] * (1 + 0.01 * b) * (1.5 if crit_off else 1.0)}
            if m != "MS":
                k0 = f"T0-{m}-SH{b}-run00"
                genomes.append({"key": k0, "task": "T0", "block": f"SH{b}-run00", "mapping": m, "label": "g39",
                                "tau": {"median": 3.0, "at_min": 0.0, "at_max": 0.0}})
                scores[k0] = {"g39": {a: _arm(v) for a, v in (("0.25", t0[1]), ("0.5", 1.0), ("1", t0[0]),
                                                              ("2", 1.0), ("4", 1.0))}}
    if drop_probe:
        probe.pop(next(iter(probe)))
    if drop_arm:
        key, lb, arm = drop_arm
        scores[key][lb].pop(arm)
    for name, obj in (("genomes.json", {"genomes": genomes}), ("scores.json", {"scores": scores}),
                      ("probe.json", {"probe": probe})):
        (path / name).write_text(json.dumps(obj))
    m60 = path / "m60"
    m60.mkdir(exist_ok=True)
    (m60 / "first-own.json").write_text(json.dumps({"rows": [{"key": k, "label": "g39", "a": 0.1 + 0.01 * i}
                                                             for i, k in enumerate(scores) if k.startswith("T1")]}))
    (path / "crit.json").write_text(json.dumps(crit))
    return m60, path / "crit.json"


def _read(R, tmp_path, monkeypatch, **kw):
    m60, crit = _write(tmp_path, R, **kw)
    monkeypatch.setattr(R, "M6_0", m60)
    monkeypatch.setattr(R, "CRIT", crit)
    monkeypatch.setattr(R, "RESAMPLES", 400)
    return R.read(tmp_path)


def test_reader_primary_reduced_with_control_excess(R, tmp_path, monkeypatch):
    res = _read(R, tmp_path, monkeypatch)
    assert res["primary"]["direction"] == "reduced"
    assert res["words"]["primary"].startswith("Making every neuron four times faster reduced")
    assert "mean within-champion change" in res["words"]["primary"]
    assert res["words"]["g00"] == "The reduction exceeded that of the generation-0 champions."
    assert res["words"]["caveat"] == R.CAVEAT


def test_reader_reduction_without_excess_and_smaller(R, tmp_path, monkeypatch):
    res = _read(R, tmp_path, monkeypatch, g00=(1.0, 0.7), drift=(1.0, 0.7), wobble=0.2)
    assert res["primary"]["direction"] == "reduced"
    assert res["words"]["drift0"] == "A champion reduction with no detected excess over the drift genomes."
    res = _read(R, tmp_path, monkeypatch, g00=(1.0, 0.3))
    assert res["words"]["g00"] == "The reduction was smaller than that of the generation-0 champions."


def test_reader_null_and_increase(R, tmp_path, monkeypatch):
    res = _read(R, tmp_path, monkeypatch, g39=(1.0, 1.0), wobble=0.1)
    assert res["words"]["primary"].startswith("No reliable mean reduction")
    res = _read(R, tmp_path, monkeypatch, g39=(1.0, 1.3))
    assert res["primary"]["direction"] == "increased"


def test_reader_inconclusive_guards_gate_every_sentence(R, tmp_path, monkeypatch):
    res = _read(R, tmp_path, monkeypatch, crit_off=True)
    assert set(res["words"]) == {"reading"} and "consistency" in res["words"]["reading"]
    res = _read(R, tmp_path, monkeypatch, cont=(10.0, 8.0, 20.0))
    assert set(res["words"]) == {"reading"} and "validation" in res["words"]["reading"]
    res = _read(R, tmp_path, monkeypatch, cont=(10.0, 3.0, 9.0))
    assert "validation" in res["words"]["reading"]
    res = _read(R, tmp_path, monkeypatch, drop_probe=True)
    assert res["inconclusive"].startswith("the run is incomplete")


def test_reader_missing_arm_is_incomplete(R, tmp_path, monkeypatch):
    res = _read(R, tmp_path, monkeypatch, drop_arm=("T1-R1-SH3-run00", "g39", "0.25"))
    assert res["inconclusive"].startswith("the run is incomplete") and res["n_missing"] == 1
    res = _read(R, tmp_path, monkeypatch, drop_arm=("T0-M0-SH2-run00", "g39", "4"))
    assert res["inconclusive"].startswith("the run is incomplete")


def test_reader_floor_and_t0_matched_by_mapping(R, tmp_path, monkeypatch):
    res = _read(R, tmp_path, monkeypatch, drift=(0.01, 0.01))
    assert any(x[1] == "drift0" for x in res["below_floor"]) and res["controls"]["drift0"]["own_relative_0.25"]["blocks"] == 0
    res = _read(R, tmp_path, monkeypatch, t0=(1.0, 0.8), ms_drop=0.2)   # a big MS-only drop must not enter T1 - T0
    assert res["T0"]["matched_runs"] == 16 and abs(res["T0"]["T1_minus_T0_0.25_matched"]["mean"] - (-0.1)) < 1e-9


def test_spearman_handles_ties_and_constants(R):
    assert abs(R.spearman([1, 1, 2], [1, 2, 3]) - 0.8660254) < 1e-6
    assert R.spearman([1, 1, 1], [1, 2, 3]) is None and R.spearman([1, 2], [2, 1]) is None


def test_the_forecast_weights_by_load(S):
    t1, t0 = {"task": "T1"}, {"task": "T0"}
    assert S.load_of(t1) == 744 and S.load_of(t0) == 248
    recs = [t1] * 102 + [t0] * 72
    f = S.forecast([t1] * 3, 300.0, recs)
    assert abs(f - 300.0 / (3 * 744) * (102 * 744 + 72 * 248)) < 1e-6


@local_genomes
def test_score_run_and_probe_one_paths(S):
    """The real paths on one run and one world: every label and arm, the composition check, and the probe's fields
    with the ramp-end difference written once at k = 1."""
    r = [x for x in S.M.t1_records() if x["key"] == "T1-M0-N2-run00"][0]
    res = S.score_run(r, worlds=S.M.analyse().CRIT_WORLDS[:1])
    assert set(res) == {"g39", "g00", "drift0"}
    assert set(res["g39"]) == {"0.25", "0.5", "1", "2", "4", S.INTERIOR, S.ALONE}
    assert set(res["g00"]) == set(res["drift0"]) == {"0.25", "1", "4"}
    assert all(len(v["worlds"]) == 1 for d in res.values() for v in d.values())
    assert abs(res["g39"][S.ALONE]["mean"] - res["g39"]["1"]["mean"]) < 1e-4
    cfg, iface, spec = S.M.setup(r)
    g = S.run_genomes(r, cfg, spec)["g39"]
    pr = S.probe_one(g, cfg, iface, S.own_bank(r["key"]), [0.25, 1, S.INTERIOR])
    assert len({v["a_written_at_1"] for v in pr.values()}) == 1
    assert pr["1"]["continued_integral"] == pr["1"]["full_integral"] and pr["0.25"]["continued_integral"] < pr["1"]["continued_integral"]


def test_composition_baseline(R, tmp_path, monkeypatch):
    """The one-strain arms are read against k = 1 in a one-strain batch (Astra): 0.5 equals its own baseline here."""
    res = _read(R, tmp_path, monkeypatch)
    assert abs(res["k"]["0.5"]["relative"]["mean"]) < 1e-12 and abs(res["composition_check"]["mean"] + 0.1 * 1.035) < 0.01
