"""The report end to end on synthetic records, with the committed diagnostics, calibration and
schedule (Astra's decision review, point 9): a schema drift must fail here, before the grid runs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from wormwars.exp02 import grid, report

EXP = Path(__file__).parents[1] / "experiments" / "02-screening"


@pytest.fixture(scope="module")
def frozen():
    load = lambda n: json.loads((EXP / n).read_text(encoding="utf-8"))  # noqa: E731
    return load("diagnostics.json"), load("calibration.json")


def test_every_scheduled_run_has_reference_scores_and_calibration(frozen):
    diag, cal = frozen
    for batch in grid.run_schedule():
        for r in batch:
            assert str(r.run_seed) in diag[r.cell.task]["per_seed_holdout"], r.key
            assert r.graph in cal, r.key


def synthetic(diag, n2_use=0.3, sh_use=0.02, seed=0):
    rng = np.random.default_rng(seed)
    recs, champs = [], {}
    for batch in grid.run_schedule():
        for r in batch:
            n_worlds = len(diag[r.cell.task]["per_seed_holdout"][str(r.run_seed)]["K"])
            held = list(rng.uniform(1.5, 3.0, n_worlds))
            recs.append({"key": r.key, "task": r.cell.task, "mapping": r.cell.mapping, "graph": r.graph,
                         "run": r.run, "run_seed": r.run_seed, "generations": r.generations,
                         "gen0_drive": {"forward": 0.5, "turn": 0.4},
                         "checkpoints": [(g, 1 - np.exp(-g / 5)) for g in range(0, 40, 10)],
                         "ledger_error": 0.0, "holdout_g00": held, "holdout_g39": held,
                         "pellet_share_g39": 0.1})
            use = n2_use if (r.graph == "N2" and (r.cell.task, r.cell.mapping) == ("T0", "M0")) else sh_use
            champs[r.key] = {}
            for snap, u in (("g00", 0.0), ("g39", use)):
                real = rng.uniform(2.0, 3.0, 64)
                scores = {"real": list(real)}
                for p in ("food_constant", "food_mirrored", "collision_off", "jitter1", "jitter3"):
                    scores[p] = list(real - 0.5 - rng.normal(0, 0.05, 64))
                if r.cell.task != "T1":
                    for p in ("mono", "food_mean", "food_swapped"):
                        scores[p] = list(real - u - rng.normal(0, 0.05, 64))
                champs[r.key][snap] = {"channels": {"world_ids": list(range(64)), "probe_seed": r.run_seed,
                                                    "scores": scores}}
            champs[r.key]["g39"]["integrator"] = {k: list(real) for k in ("s32", "s128", "s32_bias_perturbed")}
    probes = {"valence": [{"gaps": False, "max_abs_score_diff": 0.0}], "champions": champs}
    return recs, probes


def test_report_runs_end_to_end_and_finds_a_planted_stereo_advantage(frozen):
    diag, cal = frozen
    recs, probes = synthetic(diag)
    out = report.build(recs, diag, probes, cal, sign_01b=1.0, n_boot=200)
    p = out["primary"]
    assert p["verdict"] == "supported" and p["n2_use_class"] == "meaningful"
    assert abs(p["delta"]["estimate"] - 0.28) < 0.03
    assert out["capability"]["food_mean"]["acquisition"]["T0-M0"]["lo"] > 0
    assert out["sh_graphs_with_stereo_use"]["meaningful"] == 0
    assert {t["name"] for t in out["tripwires"]}
    json.dumps(out, default=float)  # the report must serialise


def test_report_challenges_when_n2_does_not_use_the_capability(frozen):
    diag, cal = frozen
    recs, probes = synthetic(diag, n2_use=0.02)
    assert report.build(recs, diag, probes, cal, sign_01b=1.0, n_boot=200)["primary"]["verdict"] == "challenged"
