"""Experiment 02b: what experiment 02's champions compute (roadmap item 1). Exploratory and
descriptive; no evolution. Uses the saved genomes in runs/exp02-screening/ (not in git).

Stages (python analyse.py <stage> ...; each writes <stage>.json next to this file):
  magnitudes  Spearman correlation of |w| with the anatomical magnitude, per champion.
  response    the input-response probe on evolved champions (generation 0 and 39), next to each
              champion's stereo use from 02's probes.
  behaviour   per-tick replays: how turning and speed depend on the food level, its change, the
              left-right difference and collision (standardised regression per champion).
  history     matched current input after different food histories (rising, falling, constant):
              does the motor output depend on the history?
  criticality deletion of every eligible neuron of each T1-M0 champion, one at a time.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.deletion import delete_neurons  # noqa: E402
from wormwars.evo import load_genome, rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp02 import probes as P  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import World  # noqa: E402

HERE = Path(__file__).resolve().parent
RUNS = ROOT / "runs" / "exp02-screening"
DEV = "cuda" if torch.cuda.is_available() else "cpu"
CON = load_connectome()
REMAPS = json.loads((grid.EXP02_DIR / "remaps.json").read_text(encoding="utf-8"))["sets"]
CAL = json.loads((grid.EXP02_DIR / "calibration.json").read_text(encoding="utf-8"))
RECORDS = [json.loads(line) for line in (RUNS / "records.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
BY_KEY = {r["key"]: r for r in RECORDS}


def family(graph: str) -> str:
    return "N2perm" if graph.startswith("N2perm") else "SH" if graph.startswith("SH") else graph


def champions(task: str, mapping: str = "M0", families=("N2", "SH")):
    return [r for r in RECORDS if r["task"] == task and r["mapping"] == mapping and family(r["graph"]) in families]


def setup(r):
    cfg = grid.brain_config_for_graph(grid.task_config(Config(), r["task"]), r["graph"])
    cfg.world.forward_gain, cfg.world.turn_gain = CAL[r["graph"]]["forward_gain"], CAL[r["graph"]]["turn_gain"]
    iface = grid.interface_for(CON, r["mapping"], REMAPS)
    graph = grid.graph_for(CON, r["graph"])
    spec = BrainSpec.from_connectome(graph, device=DEV)
    return cfg, iface, graph, spec


def load(r, tag, spec):
    g, _ = load_genome(RUNS / f"{r['key']}-{tag}.npz", spec, None, device=DEV)
    return g


def save(stage, obj):
    (HERE / f"{stage}.json").write_text(json.dumps(obj, indent=1), encoding="utf-8")


def spearman(a, b):
    ra, rb = np.argsort(np.argsort(a)), np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


# ------------------------------------------------------------------------------ stages

def stage_magnitudes():
    out = {}
    for task in ("T0", "T1"):
        for r in champions(task):
            cfg, iface, graph, spec = setup(r)
            anat = spec.chem_anat.cpu().numpy()
            out[r["key"]] = {tag: spearman(np.abs(load(r, tag, spec).w[0].cpu().numpy()), anat)
                             for tag in ("g00", "g39")}
    save("magnitudes", out)
    for fam in ("N2", "SH"):
        v = [x for k, x in out.items() if family(BY_KEY[k]["graph"]) == fam]
        print(fam, "g00", round(np.mean([x["g00"] for x in v]), 3), "g39", round(np.mean([x["g39"] for x in v]), 3))


def stage_response():
    use = json.loads((RUNS / "probes.json").read_text(encoding="utf-8"))["champions"]
    out = {}
    for r in champions("T0"):
        cfg, iface, graph, spec = setup(r)
        row = {}
        for tag in ("g00", "g39"):
            res = P.input_response(spec, cfg, iface, None, DEV, genome=load(r, tag, spec))
            sc = use[r["key"]][tag]["channels"]["scores"]
            row[tag] = {**{k: float(np.mean(v)) for k, v in res.items()},
                        "use_mean": float(np.mean(np.array(sc["real"]) - np.array(sc["food_mean"]))),
                        "use_swap": float(np.mean(np.array(sc["real"]) - np.array(sc["food_swapped"])))}
        out[r["key"]] = row
    save("response", out)
    for tag in ("g00", "g39"):
        x = [v[tag]["directional_turn_signed_motor"] for v in out.values()]
        y = [v[tag]["use_swap"] for v in out.values()]
        print(tag, "corr(signed directional turn, swap use) over T0-M0 champions:", round(spearman(x, y), 3))


BEHAVIOUR_WORLDS = grid.PROBE_IDS[:8]


def replay(cfg, iface, champ, seed):
    """Per-tick logs of alive weys: food level, its change, the left-right difference, the
    collision left-right difference and total, and the motor commands."""
    n = len(BEHAVIOUR_WORLDS)
    world = World(cfg, iface, Brain(champ), torch.zeros(n, 1, dtype=torch.long, device=DEV),
                  run_seed=seed, world_ids=np.asarray(BEHAVIOUR_WORLDS), device=DEV)
    rows, prev = [], None
    while not world.done():
        alive = world.alive.clone()
        world.tick()
        s = world.last_signals
        level = (s["food_left"] + s["food_right"]) / 2
        coll_l = s["collision_front_left"]
        coll_r = s["collision_front_right"]
        if prev is not None:
            m = alive & world.alive
            rows.append(torch.stack([level[m], level[m] - prev[m], (s["food_left"] - s["food_right"])[m],
                                     (coll_l - coll_r)[m], (coll_l + coll_r + s["collision_front"])[m],
                                     world.last_forward[m], world.last_turn[m]], -1).cpu())
        prev = level.clone()
    return torch.cat(rows).numpy()


PREDICTORS = ("food_level", "food_change", "food_left_minus_right", "collision_left_minus_right", "collision_total")


def std_regression(x, y):
    xs = (x - x.mean(0)) / np.where(x.std(0) > 0, x.std(0), 1)
    ys = (y - y.mean()) / (y.std() if y.std() > 0 else 1)
    beta, *_ = np.linalg.lstsq(np.c_[np.ones(len(xs)), xs], ys, rcond=None)
    r2 = 1 - np.mean((ys - np.c_[np.ones(len(xs)), xs] @ beta) ** 2)
    return {"beta": dict(zip(PREDICTORS, map(float, beta[1:]))), "r2": float(r2)}


def stage_behaviour():
    out = {}
    for task in ("T0", "T1"):
        for r in champions(task):
            cfg, iface, graph, spec = setup(r)
            d = replay(cfg, iface, load(r, "g39", spec), r["run_seed"])
            x = d[:, :5]
            out[r["key"]] = {"n": int(len(d)), "forward": std_regression(x, d[:, 5]),
                             "turn": std_regression(x, d[:, 6]),
                             "turn_sign_persistence": float(np.mean(np.sign(d[1:, 6]) == np.sign(d[:-1, 6])))}
    save("behaviour", out)
    for task in ("T0", "T1"):
        for fam in ("N2", "SH"):
            v = [x for k, x in out.items() if k.startswith(task) and family(BY_KEY[k]["graph"]) == fam]
            f = {p: round(np.mean([x["forward"]["beta"][p] for x in v]), 3) for p in PREDICTORS}
            t = {p: round(np.mean([x["turn"]["beta"][p] for x in v]), 3) for p in PREDICTORS}
            print(task, fam, "forward", f, "R2", round(np.mean([x["forward"]["r2"] for x in v]), 3))
            print(task, fam, "turn   ", t, "R2", round(np.mean([x["turn"]["r2"] for x in v]), 3))


def build_current(iface, cfg, values: dict, n):
    """The injected current for given signal values, as World._build_current does."""
    cur = torch.zeros(1, 1, n, device=DEV)
    for name, j, gain in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        cur[..., int(j)] += float(values.get(name, 0.0)) * float(gain) * cfg.brain.input_gain
    return cur.clamp(-cfg.brain.input_max, cfg.brain.input_max)


def motors(iface, cfg, v):
    a = torch.tanh(v)
    fwd = a[..., list(iface.forward_plus)].mean(-1) - a[..., list(iface.forward_minus)].mean(-1)
    turn = a[..., list(iface.turn_plus)].mean(-1) - a[..., list(iface.turn_minus)].mean(-1)
    return (float((fwd * 0.5 * cfg.world.forward_gain).clamp(-1, 1)), float((turn * 0.5 * cfg.world.turn_gain).clamp(-1, 1)))


def history_one(r, tag, warm=30, span=10):
    """Same final input, three food histories over the last `span` ticks. The other signals stay
    at their typical level (the mean over a short replay of this champion). Returns the motor
    commands on the final tick and on the next 5 ticks of identical input."""
    cfg, iface, graph, spec = setup(r)
    champ = load(r, tag, spec)
    brain = Brain(champ)
    n = len(BEHAVIOUR_WORLDS)
    world = World(cfg, iface, Brain(champ), torch.zeros(n, 1, dtype=torch.long, device=DEV),
                  run_seed=r["run_seed"], world_ids=np.asarray(BEHAVIOUR_WORLDS), device=DEV)
    sums, count = {}, 0
    for _ in range(40):
        world.tick()
        if bool(world.alive.any()):
            for k, v in world.last_signals.items():
                sums[k] = sums.get(k, 0.0) + float(v[world.alive].mean())
            count += 1
    typical = {k: v / max(count, 1) for k, v in sums.items()}
    food = (typical["food_left"] + typical["food_right"]) / 2
    res = {}
    for name, start in (("rising", 0.25 * food), ("constant", food), ("falling", 1.75 * food)):
        v = brain.initial_state(1)
        for _ in range(warm):
            v = brain.step(v, build_current(iface, cfg, dict(typical, food_left=start, food_right=start), spec.n))
        for t in range(span):
            lvl = start + (food - start) * (t + 1) / span
            v = brain.step(v, build_current(iface, cfg, dict(typical, food_left=lvl, food_right=lvl), spec.n))
        trace = [motors(iface, cfg, v)]
        for _ in range(5):
            v = brain.step(v, build_current(iface, cfg, dict(typical, food_left=food, food_right=food), spec.n))
            trace.append(motors(iface, cfg, v))
        res[name] = trace
    f = {k: tr[0][0] for k, tr in res.items()}
    t = {k: tr[0][1] for k, tr in res.items()}
    return {"typical_food": food, "traces": res,
            "forward_rising_minus_falling": float(f["rising"] - f["falling"]),
            "turn_rising_minus_falling": float(t["rising"] - t["falling"])}


def stage_history():
    """Generation-39 champions against generation-0 champions (the best of 32 random genomes):
    any recurrent network carries some history, so the random baseline is the comparison."""
    out = {}
    for task in ("T0", "T1"):
        for r in champions(task):
            out[r["key"]] = {tag: history_one(r, tag) for tag in ("g00", "g39")}
    save("history", out)
    for task in ("T0", "T1"):
        for fam in ("N2", "SH"):
            v = [x for k, x in out.items() if k.startswith(task) and family(BY_KEY[k]["graph"]) == fam]
            for tag in ("g00", "g39"):
                print(task, fam, tag,
                      "forward rising-falling", round(np.mean([x[tag]["forward_rising_minus_falling"] for x in v]), 4),
                      "turn |rising-falling|", round(np.mean([abs(x[tag]["turn_rising_minus_falling"]) for x in v]), 4))


CRIT_WORLDS = grid.PROBE_IDS[:32]


def eligible(iface, graph):
    mapped = set(int(i) for i in iface.mapped_neurons)
    return [i for i in range(graph.n) if i not in mapped and graph.classes[i] != "pharyngeal"]


def stage_criticality(limit=None, chunk=48, mapping="M0", families=("N2", "SH")):
    """Deletion criticality of every eligible neuron. The R1 run (N2 only) is the control for
    reading M0's critical neurons: are they the food route, or hubs whatever the mapping?"""
    name = "criticality" if mapping == "M0" else f"criticality_{mapping}"
    out = {}
    recs = champions("T1", mapping, families)
    recs = recs[:limit] if limit else recs
    for r in recs:
        t0 = time.perf_counter()
        cfg, iface, graph, spec = setup(r)
        champ = load(r, "g39", spec)
        base = rollout(cfg, iface, champ, CRIT_WORLDS, r["run_seed"], DEV).score[0]
        drops = {}
        cand = eligible(iface, graph)
        for i in range(0, len(cand), chunk):
            ks = cand[i:i + chunk]
            many = Genome(spec, champ.cfg, champ.w.repeat(len(ks), 1), champ.g.repeat(len(ks), 1),
                          champ.tau.repeat(len(ks), 1), champ.bias.repeat(len(ks), 1),
                          None if champ.dale_sign is None else champ.dale_sign.repeat(len(ks), 1))
            sc = rollout(cfg, iface, delete_neurons(many, [[k] for k in ks]), CRIT_WORLDS, r["run_seed"], DEV).score
            for j, k in enumerate(ks):
                drops[graph.names[k]] = float(np.mean(base - sc[j]))
        out[r["key"]] = {"intact": float(base.mean()), "drops": drops, "seconds": time.perf_counter() - t0}
        print(r["key"], f"{out[r['key']]['seconds']:.0f}s", "top:",
              sorted(drops.items(), key=lambda kv: -kv[1])[:5], flush=True)
        save(name, out)


if __name__ == "__main__":
    stage = sys.argv[1]
    arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    {"magnitudes": stage_magnitudes, "response": stage_response, "behaviour": stage_behaviour,
     "history": stage_history, "criticality": lambda: stage_criticality(arg),
     "criticality_R1": lambda: stage_criticality(arg, mapping="R1", families=("N2",))}[stage]()
