"""E4's calibration, stage A (exploratory; D255, after both reviewers read the diagnostics, D254).

    python scripts/e4_calibrate.py --device cuda      # writes experiments/E4-two-minds/calibration.json
    add --smoke for toy sizes (runs/e4-smoke/calibration.json)

Generation 1, children only (32 copies of E-G bred once: 3 elites, 29 children; 4 generator seeds, the same for every
condition), every condition paired on block A (16 fresh mazes, 40 800-40 815, maze seed 1 400 000):
1. **The bias split** at 0.25: nose biases only, comparator biases only (Fable predicted the noses cost about three
   times the comparators: the open-loop gain is 18 from a nose bias, 6 from a comparator bias).
2. **The bias ladder:** weights and τ at 0.25, the module biases at 0.05, 0.02, 0.01, 0.005 and 0 (frozen); the factor
   by `calibration.bias_factor`; its confirmation on block B (16 fresh mazes, 40 900-40 915).
3. **The cross-link ladder** at the chosen bias factor: X+ with the slots at 0.25, 0.5, 1, 2 and 4, against X0's
   children; each by `calibration.cross_load_ok`.
4. **Reading 2's test** (both): children with only the 32 slots mutated (everything inherited frozen) at 0.25 and 1.0,
   played intact, mean-substituted (the links' constant part kept, their fluctuation cut) and centred (the constant part
   removed, the fluctuation kept); cut is E-G itself. Each child's source means come from block C (8 fresh mazes,
   40 950-40 957). Nose-origin and comparator-origin links are reported apart, by cutting each subset.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4 import calibration as CB  # noqa: E402
from wormwars.e4 import evaluate as EVL  # noqa: E402
from wormwars.e4 import means as ME  # noqa: E402
from wormwars.e4 import train as TR  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.evolve import breed  # noqa: E402


def _load(name, file):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


P4 = _load("e4_for_calibration", "e4.py")

OUT = ROOT / "experiments" / "E4-two-minds" / "calibration.json"
SEED = 1_400_000
BLOCK_A, BLOCK_B, BLOCK_C = np.arange(40_800, 40_816), np.arange(40_900, 40_916), np.arange(40_950, 40_958)
REPLICATES, REP_SEED = 4, 1_400_960
P, ELITES = 32, 3
CROSS = (0.25, 0.5, 1.0, 2.0, 4.0)
SMOKE = False


def bred(base: Genome, cfg, sc, dev) -> Genome:
    """4 replicates × 32 strains, bred once from copies of `base` with scales `sc`, same seeds for every condition."""
    start = EV.moved(Genome.cat([base.select([0])] * P), dev)
    return Genome.cat([breed(start, np.zeros(P), cfg, torch.Generator(device=dev).manual_seed(REP_SEED + r), sc)
                       for r in range(REPLICATES)])


def children(g: Genome) -> Genome:
    return g.select([r * P + k for r in range(REPLICATES) for k in range(ELITES, P)])


def play(cfg, org, g: Genome, ids, dev) -> np.ndarray:
    """[strains]: mean visits per wey on `ids`, gated."""
    res = TR.gated_rollout(org.gate)(cfg, org.iface, g, np.asarray(ids), SEED, dev, chunk_worlds=g.n_strains * len(ids))
    return np.asarray(res.score).mean(axis=1)


def summary(v: np.ndarray) -> dict:
    per_rep = v.reshape(REPLICATES, -1).mean(axis=1)
    return {"mean": float(v.mean()), "se": float(per_rep.std(ddof=1) / np.sqrt(REPLICATES)) if REPLICATES > 1 else None,
            "per_replicate": np.round(per_rep, 4).tolist(), "share_at_least_5": float((v >= 5).mean())}


def main_body(dev: str) -> dict:
    t0 = time.perf_counter()
    cfg = P4.cfg_for("shared")
    cx = AR.context(load_connectome(), A.load_l1(), cfg.brain)
    org = cx["org"]
    eg = EV.moved(org.genome.select([0]), dev)
    out = {"inputs": {"block_A": BLOCK_A.tolist(), "block_B": BLOCK_B.tolist(), "block_C": BLOCK_C.tolist(),
                      "replicates": REPLICATES, "replicate_seed": REP_SEED}}

    def kids(sc):
        return play(cfg, org, children(bred(eg, cfg, sc, dev)), BLOCK_A, dev)

    with acct.category("probe"):
        out["eg_block_A"] = float(play(cfg, org, eg, BLOCK_A, dev)[0])
        out["bias_split_0.25"] = {c: summary(kids(AR.class_scales(cx, c))) for c in ("nose_bias", "comparator_bias")}
        P4.E.write_atomic(OUT.with_name(OUT.stem + "-partial.json"), out)
        ladder = {b: summary(kids(AR.combined_scales(cx, bias_factor=b))) for b in (*CB.BIAS_CANDIDATES, 0.0)}
        out["bias_ladder"] = {str(b): v for b, v in ladder.items()}
        choice = CB.bias_factor({b: v["mean"] for b, v in ladder.items()}, eg=out["eg_block_A"])
        out["bias_choice"] = {**choice, "children": {str(k): v for k, v in choice["children"].items()}}
        b = choice["factor"]
        eg_b = float(play(cfg, org, eg, BLOCK_B, dev)[0])
        kb = play(cfg, org, children(bred(eg, cfg, AR.combined_scales(cx, bias_factor=b), dev)), BLOCK_B, dev)
        out["confirmation_block_B"] = {"eg": eg_b, "children": summary(kb),
                                       "confirmed": CB.confirmed(children=float(kb.mean()), eg=eg_b)}
        P4.E.write_atomic(OUT.with_name(OUT.stem + "-partial.json"), out)
        x0 = ladder[b]["mean"]
        cross = {}
        for f in CROSS:
            s = summary(kids(AR.combined_scales(cx, bias_factor=b, cross_factor=f)))
            cross[str(f)] = {**s, "loss_vs_x0": x0 - s["mean"], "load_ok": CB.cross_load_ok(s["mean"], x0=x0)}
        out["cross_ladder"] = {"x0_children": x0, "by_factor": cross}
        P4.E.write_atomic(OUT.with_name(OUT.stem + "-partial.json"), out)
        sets = EVL.link_sets(cx)
        reading2 = {}
        for f in (0.25, 1.0):
            g = children(bred(eg, cfg, AR.combined_scales(cx, bias_factor=0.0, cross_factor=f, inherited=False), dev))
            m = ME.source_means(cfg, org.iface, g, org.gate, BLOCK_C, SEED, dev)
            conds = {"intact": g, "mean_substituted": AR.mean_substitute(g, sets["all"], m),
                     "centred": AR.center(g, sets["all"], m), "sensory_cut": AR.cut(g, sets["sensory"]),
                     "comparator_cut": AR.cut(g, sets["comparator"])}
            reading2[str(f)] = {k: summary(play(cfg, org, v, BLOCK_A, dev)) for k, v in conds.items()}
        out["reading2"] = {"eg_is_cut": out["eg_block_A"], "by_factor": reading2}
    out["seconds"] = time.perf_counter() - t0
    return out


def main():
    global BLOCK_A, BLOCK_B, BLOCK_C, REPLICATES, OUT
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        OUT = ROOT / "runs" / "e4-smoke" / "calibration.json"
        BLOCK_A, BLOCK_B, BLOCK_C, REPLICATES = BLOCK_A[:1], BLOCK_B[:1], BLOCK_C[:1], 2
        P4.REGISTERED["H"] = 40
        P4.configure()
    prov = reg.provenance(P4.GUARDED + ["scripts/e4_calibrate.py"])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {"provenance": prov, "device": args.device, **main_body(args.device)}
    reg.write_json(OUT, doc, atomic=True)
    print("bias split", {k: round(v["mean"], 3) for k, v in doc["bias_split_0.25"].items()}, "eg", round(doc["eg_block_A"], 3))
    print("ladder", {k: round(v["mean"], 3) for k, v in doc["bias_ladder"].items()}, "choice", doc["bias_choice"]["factor"],
          "confirmed", doc["confirmation_block_B"]["confirmed"])
    print("cross", {k: (round(v["mean"], 3), v["load_ok"]) for k, v in doc["cross_ladder"]["by_factor"].items()})
    print("reading2", {f: {k: round(v["mean"], 3) for k, v in d.items()} for f, d in doc["reading2"]["by_factor"].items()})


if __name__ == "__main__":
    from wormwars.accounting import run_script
    smoke = "--smoke" in sys.argv
    run_script(main, out_default=str(ROOT / "runs" / ("e4-smoke" if smoke else "e4-diag")), default="measure",
               name="e4-calibrate")
