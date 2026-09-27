"""Experiment 02b: what experiment 02's champions compute (roadmap item 1). Exploratory and
descriptive; no evolution. Uses the saved genomes in runs/exp02-screening/ (not in git).

v2 of this script follows the review of v1 by Astra 6 and Fable 5.1 (D049). Stages (python
analyse.py <stage>; each writes <stage>.json next to this file; `summarise` computes every
number RESULTS.md reports and writes summary.json):

  magnitudes      Spearman (average ranks) of |w| with the anatomical magnitude, per champion.
  response        the input-response probe on evolved champions, per champion, next to 02's
                  stereo-use scores.
  behaviour       per-tick replays with wey identity kept: turn persistence per wey across
                  ticks, and standardised regressions pooled and within wey.
  history         matched current input after different food histories, on one stimulus bank
                  per run shared by generation 0, generation 39 and a mutation-only drift
                  control; raw read-out and motor command; steady-state contrast and decay.
  criticality     deletion of every eligible neuron of each T1-M0 champion (one null strain per
                  batch, whose drop must be ~0).
  criticality_R1  the same for N2's T1-R1 champions; criticality_R2 for T1-R2 (non-amphid food).
  kept_edges      for each N2 T1-M0 champion's 12 most critical neurons: deleting only the edges
                  to mapped (interface) neurons, against full deletion (03a keeps those edges).
  summarise       every reported number, from the JSON files above plus the connectome.
"""

from __future__ import annotations

import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.deletion import delete_neurons  # noqa: E402
from wormwars.evo import load_genome, rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp02 import probes as P  # noqa: E402
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


def read(stage):
    return json.loads((HERE / f"{stage}.json").read_text(encoding="utf-8"))


def spearman(a, b) -> float:
    return float(stats.spearmanr(a, b).statistic)  # average ranks for ties


# ------------------------------------------------------------------------------ magnitudes

def stage_magnitudes():
    out = {}
    for task in ("T0", "T1"):
        for r in champions(task):
            cfg, iface, graph, spec = setup(r)
            anat = spec.chem_anat.cpu().numpy()
            out[r["key"]] = {tag: spearman(np.abs(load(r, tag, spec).w[0].cpu().numpy()), anat)
                             for tag in ("g00", "g39")}
    save("magnitudes", out)


# ------------------------------------------------------------------------------ response

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


# ------------------------------------------------------------------------------ behaviour

BEHAVIOUR_WORLDS = grid.PROBE_IDS[:8]
PREDICTORS = ("food_level", "food_change", "food_left_minus_right", "collision_left_minus_right", "collision_total")


def replay(cfg, iface, champ, seed):
    """Per tick, with wey identity: an array [ticks, weys, 7] of the five predictors, forward and
    turn, and an alive mask [ticks, weys]. Weys are flattened over worlds."""
    n = len(BEHAVIOUR_WORLDS)
    world = World(cfg, iface, Brain(champ), torch.zeros(n, 1, dtype=torch.long, device=DEV),
                  run_seed=seed, world_ids=np.asarray(BEHAVIOUR_WORLDS), device=DEV)
    frames, masks, prev = [], [], None
    while not world.done():
        alive_before = world.alive.clone()
        world.tick()
        s = world.last_signals
        level = (s["food_left"] + s["food_right"]) / 2
        if prev is not None:
            frames.append(torch.stack([level, level - prev, s["food_left"] - s["food_right"],
                                       s["collision_front_left"] - s["collision_front_right"],
                                       s["collision_front_left"] + s["collision_front_right"] + s["collision_front"],
                                       world.last_forward, world.last_turn], -1).reshape(-1, 7).cpu())
            masks.append((alive_before & world.alive).reshape(-1).cpu())
        prev = level.clone()
    return torch.stack(frames).numpy(), torch.stack(masks).numpy()


def std_regression(x, y):
    xs = (x - x.mean(0)) / np.where(x.std(0) > 0, x.std(0), 1)
    ys = (y - y.mean()) / (y.std() if y.std() > 0 else 1)
    a = np.c_[np.ones(len(xs)), xs]
    beta, *_ = np.linalg.lstsq(a, ys, rcond=None)
    return {"beta": dict(zip(PREDICTORS, map(float, beta[1:]))), "r2": float(1 - np.mean((ys - a @ beta) ** 2))}


def stage_behaviour():
    out = {}
    for task in ("T0", "T1"):
        for r in champions(task):
            cfg, iface, graph, spec = setup(r)
            d, m = replay(cfg, iface, load(r, "g39", spec), r["run_seed"])
            # persistence per wey across consecutive ticks, where alive on both
            both = m[1:] & m[:-1]
            same = np.sign(d[1:, :, 6]) == np.sign(d[:-1, :, 6])
            pooled = d[m]
            # within wey: subtract each wey's own mean over its alive ticks, which removes
            # circling and other stable per-wey differences
            dm = d.copy()
            for w in range(d.shape[1]):
                if m[:, w].any():
                    dm[m[:, w], w] -= d[m[:, w], w].mean(0)
            within = dm[m]
            out[r["key"]] = {"n": int(m.sum()),
                             "turn_sign_persistence": float(same[both].mean()),
                             "pooled": {"forward": std_regression(pooled[:, :5], pooled[:, 5]),
                                        "turn": std_regression(pooled[:, :5], pooled[:, 6])},
                             "within_wey": {"forward": std_regression(within[:, :5], within[:, 5]),
                                            "turn": std_regression(within[:, :5], within[:, 6])}}
    save("behaviour", out)


# ------------------------------------------------------------------------------ history

def build_current(iface, cfg, values: dict, n):
    cur = torch.zeros(1, 1, n, device=DEV)
    for name, j, gain in zip(iface.signal_names, iface.sensor_neuron, iface.sensor_gain):
        cur[..., int(j)] += float(values.get(name, 0.0)) * float(gain) * cfg.brain.input_gain
    return cur.clamp(-cfg.brain.input_max, cfg.brain.input_max)


def readout(iface, cfg, v):
    """(raw forward, raw turn, motor forward, motor turn): raw is before gain and clip."""
    a = torch.tanh(v)
    fwd = float(a[..., list(iface.forward_plus)].mean(-1) - a[..., list(iface.forward_minus)].mean(-1))
    turn = float(a[..., list(iface.turn_plus)].mean(-1) - a[..., list(iface.turn_minus)].mean(-1))
    clip = lambda x: max(-1.0, min(1.0, x))  # noqa: E731
    return fwd, turn, clip(fwd * 0.5 * cfg.world.forward_gain), clip(turn * 0.5 * cfg.world.turn_gain)


def typical_input(r, cfg, iface, spec):
    """One stimulus bank per run: the mean sensed signals over ticks 20-60 of the generation-39
    champion's replay (mid-episode, not spawn). Shared by every genome tested for this run."""
    champ = load(r, "g39", spec)
    n = len(BEHAVIOUR_WORLDS)
    world = World(cfg, iface, Brain(champ), torch.zeros(n, 1, dtype=torch.long, device=DEV),
                  run_seed=r["run_seed"], world_ids=np.asarray(BEHAVIOUR_WORLDS), device=DEV)
    sums, count = {}, 0
    for t in range(60):
        world.tick()
        if t >= 20 and bool(world.alive.any()):
            for k, v in world.last_signals.items():
                sums[k] = sums.get(k, 0.0) + float(v[world.alive].mean())
            count += 1
    return {k: v / max(count, 1) for k, v in sums.items()}


def history_one(genome, cfg, iface, spec, typical, warm=100, span=10, after=5):
    """Two food histories reaching the same final input, rising from a quarter of it and falling
    from 1.75 times it. Returns, for each read-out (raw forward and turn, motor forward and
    turn): the rising-minus-falling difference on the final tick; the same after `after` more
    ticks of identical input (decay); and the steady-state contrast between holding the two
    start levels, which normalises for gain."""
    brain = Brain(genome)
    food = (typical["food_left"] + typical["food_right"]) / 2
    at = lambda lvl: build_current(iface, cfg, dict(typical, food_left=lvl, food_right=lvl), spec.n)  # noqa: E731
    final, later, steady = {}, {}, {}
    for name, start in (("rising", 0.25 * food), ("falling", 1.75 * food)):
        v = brain.initial_state(1)
        for _ in range(warm):
            v = brain.step(v, at(start))
        steady[name] = readout(iface, cfg, v)
        for t in range(span):
            v = brain.step(v, at(start + (food - start) * (t + 1) / span))
        final[name] = readout(iface, cfg, v)
        for _ in range(after):
            v = brain.step(v, at(food))
        later[name] = readout(iface, cfg, v)
    keys = ("raw_forward", "raw_turn", "motor_forward", "motor_turn")
    return {k: {"final": final["rising"][i] - final["falling"][i],
                "after": later["rising"][i] - later["falling"][i],
                "steady_contrast": steady["falling"][i] - steady["rising"][i]} for i, k in enumerate(keys)}


def drifted(g00: Genome, cfg, generations=39, seed=0) -> Genome:
    """The generation-0 champion mutated `generations` times with the run's mutation settings
    and no selection: what parameter drift alone does to the measure."""
    gen = torch.Generator(device=DEV).manual_seed(seed)
    g = g00.clone()
    for _ in range(generations):
        g.mutate(cfg.mutation, generator=gen)
    return g


def stage_history(drift_reps=4):
    out = {}
    for task in ("T0", "T1"):
        for r in champions(task):
            cfg, iface, graph, spec = setup(r)
            typ = typical_input(r, cfg, iface, spec)
            g00 = load(r, "g00", spec)
            out[r["key"]] = {"typical_food": (typ["food_left"] + typ["food_right"]) / 2,
                             "g00": history_one(g00, cfg, iface, spec, typ),
                             "g39": history_one(load(r, "g39", spec), cfg, iface, spec, typ),
                             "drift": [history_one(drifted(g00, cfg, seed=k), cfg, iface, spec, typ)
                                       for k in range(drift_reps)]}
    save("history", out)


# ------------------------------------------------------------------------------ criticality

CRIT_WORLDS = grid.PROBE_IDS[:32]


def eligible(iface, graph):
    mapped = set(int(i) for i in iface.mapped_neurons)
    return [i for i in range(graph.n) if i not in mapped and graph.classes[i] != "pharyngeal"]


def repeat(champ: Genome, k: int) -> Genome:
    return Genome(champ.spec, champ.cfg, champ.w.repeat(k, 1), champ.g.repeat(k, 1), champ.tau.repeat(k, 1),
                  champ.bias.repeat(k, 1), None if champ.dale_sign is None else champ.dale_sign.repeat(k, 1))


def stage_criticality(mapping="M0", families=("N2", "SH"), chunk=48):
    """Deletion of every eligible neuron, one at a time. Each batch carries one null strain (no
    deletion) whose drop must be ~0: chunking must be invisible."""
    name = "criticality" if mapping == "M0" else f"criticality_{mapping}"
    out = {}
    for r in champions("T1", mapping, families):
        t0 = time.perf_counter()
        cfg, iface, graph, spec = setup(r)
        champ = load(r, "g39", spec)
        base = rollout(cfg, iface, champ, CRIT_WORLDS, r["run_seed"], DEV).score[0]
        drops, nulls = {}, []
        cand = eligible(iface, graph)
        for i in range(0, len(cand), chunk):
            ks = cand[i:i + chunk]
            sc = rollout(cfg, iface, delete_neurons(repeat(champ, len(ks) + 1), [[]] + [[k] for k in ks]),
                         CRIT_WORLDS, r["run_seed"], DEV).score
            nulls.append(float(np.mean(base - sc[0])))
            for j, k in enumerate(ks):
                drops[graph.names[k]] = float(np.mean(base - sc[j + 1]))
        out[r["key"]] = {"intact": float(base.mean()), "drops": drops, "null_drops": nulls,
                         "seconds": time.perf_counter() - t0}
        print(r["key"], f"{out[r['key']]['seconds']:.0f}s, max |null drop| {max(map(abs, nulls)):.2e}", flush=True)
        save(name, out)


def interface_edges_only(genome: Genome, per_strain):
    """Delete only the edges between each listed neuron and the mapped (interface) neurons."""
    spec = genome.spec
    w, g = genome.w.clone(), genome.g.clone()
    for s, (k, mapped) in enumerate(per_strain):
        mp = torch.as_tensor(sorted(mapped), device=genome.device)
        w[s, ((spec.chem_i == k) & torch.isin(spec.chem_j, mp)) | ((spec.chem_j == k) & torch.isin(spec.chem_i, mp))] = 0.0
        g[s, ((spec.gap_i == k) & torch.isin(spec.gap_j, mp)) | ((spec.gap_j == k) & torch.isin(spec.gap_i, mp))] = 0.0
    return Genome(spec, genome.cfg, w, g, genome.tau.clone(), genome.bias.clone(),
                  None if genome.dale_sign is None else genome.dale_sign.clone())


def stage_kept_edges(top=12):
    """03a keeps a target's edges to interface neurons fixed. If a critical neuron's criticality
    is carried by those edges, reinsertion recovers the score whatever the hidden partners."""
    crit = read("criticality")
    out = {}
    for r in champions("T1", "M0", ("N2",)):
        cfg, iface, graph, spec = setup(r)
        champ = load(r, "g39", spec)
        mapped = set(int(i) for i in iface.mapped_neurons)
        names = sorted(crit[r["key"]]["drops"], key=lambda n: -crit[r["key"]]["drops"][n])[:top]
        ks = [graph.index(n) for n in names]
        base = rollout(cfg, iface, champ, CRIT_WORLDS, r["run_seed"], DEV).score[0]
        sc = rollout(cfg, iface, interface_edges_only(repeat(champ, len(ks)), [(k, mapped) for k in ks]),
                     CRIT_WORLDS, r["run_seed"], DEV).score
        out[r["key"]] = {n: {"full_deletion_drop": crit[r["key"]]["drops"][n],
                             "interface_edges_only_drop": float(np.mean(base - sc[j])),
                             "interface_edges": int(sum(1 for m in mapped if CON.chem[k, m] > 0 or CON.chem[m, k] > 0
                                                        or CON.gap[k, m] > 0))}
                         for j, (n, k) in enumerate(zip(names, ks))}
    save("kept_edges", out)


# ------------------------------------------------------------------------------ summarise

def _t(x):
    x = np.asarray(x, dtype=float)
    se = x.std(ddof=1) / np.sqrt(len(x))
    q = stats.t.ppf(0.975, len(x) - 1)
    return [float(x.mean()), float(x.mean() - q * se), float(x.mean() + q * se)]


def _n2(key):
    return BY_KEY[key]["graph"] == "N2"


def stage_summarise():
    s = {}
    mag = read("magnitudes")
    s["magnitudes"] = {fam: {tag: float(np.mean([v[tag] for k, v in mag.items() if _n2(k) == (fam == "N2")]))
                             for tag in ("g00", "g39")} for fam in ("N2", "SH")}
    crit = read("criticality")
    s["criticality"] = {}
    for fam in ("N2", "SH"):
        ks = [k for k in crit if _n2(k) == (fam == "N2")]
        n_crit = [int(sum(v > 0.05 * crit[k]["intact"] for v in crit[k]["drops"].values())) for k in ks]
        s["criticality"][fam] = {"champions": len(ks), "eligible": len(crit[ks[0]]["drops"]),
                                 "critical_count_mean": float(np.mean(n_crit)),
                                 "critical_count_range": [min(n_crit), max(n_crit)],
                                 "critical_count_t": _t(n_crit),
                                 "max_drop": float(max(max(crit[k]["drops"].values()) for k in ks)),
                                 "mean_of_max_drops": float(np.mean([max(crit[k]["drops"].values()) for k in ks])),
                                 "max_abs_null_drop": float(max(max(map(abs, crit[k]["null_drops"])) for k in ks))}

    def counts(c):
        cnt, mean = Counter(), Counter()
        ks = [k for k in c if _n2(k)]
        for k in ks:
            cnt.update([n for n, v in c[k]["drops"].items() if v > 0.05 * c[k]["intact"]])
            mean.update({n: v / len(ks) for n, v in c[k]["drops"].items()})
        return cnt, mean, set(c[ks[0]]["drops"])

    m0c, m0m, m0e = counts(crit)
    s["n2_core_M0"] = [(n, m) for n, m in m0c.most_common() if m >= 6]
    for other in ("R1", "R2"):
        if not (HERE / f"criticality_{other}.json").exists():
            continue
        oc, om, oe = counts(read(f"criticality_{other}"))
        common = sorted(m0e & oe)
        top = lambda mm: {n for n, _ in sorted(((n, mm[n]) for n in common), key=lambda kv: -kv[1])[:20]}  # noqa: E731
        s[f"n2_vs_{other}"] = {"common_eligible": len(common),
                               "spearman_mean_drop": spearman([m0m[n] for n in common], [om[n] for n in common]),
                               "top20_overlap": len(top(m0m) & top(om)),
                               "core_counts_M0_then_other": {n: [m0c[n], oc[n]] for n in
                                                             ("AIYL", "AIYR", "AIZL", "AIZR", "RIAL", "RIAR", "RIBL", "RIBR", "RIS")},
                               "critical_ge6": [(n, m) for n, m in oc.most_common() if m >= 6]}
    iface = grid.interface_for(CON, "M0", REMAPS)
    read_idx = sorted({int(i) for i in np.concatenate([iface.forward_plus, iface.forward_minus,
                                                       iface.turn_plus, iface.turn_minus])})
    names = sorted(m0e)
    idx = [CON.index(n) for n in names]
    degree = [int((CON.chem[i] > 0).sum() + (CON.chem[:, i] > 0).sum() + (CON.gap[i] > 0).sum()) for i in idx]
    readw = [float(CON.chem[i, read_idx].sum() + CON.gap[i, read_idx].sum()) for i in idx]
    drop = [m0m[n] for n in names]
    s["n2_M0_structure"] = {"spearman_drop_degree": spearman(drop, degree),
                            "spearman_drop_readout_weight": spearman(drop, readw),
                            "degree_percentile": {n: float(stats.percentileofscore(degree, degree[names.index(n)]))
                                                  for n in ("AIYL", "AIYR", "AIZL", "AIZR", "RIAL", "RIAR")}}
    if (HERE / "kept_edges.json").exists():
        ke = read("kept_edges")
        rows = [v for champ in ke.values() for v in champ.values()]
        s["kept_edges"] = {"targets": len(rows),
                           "median_share_of_drop_from_interface_edges": float(np.median(
                               [v["interface_edges_only_drop"] / v["full_deletion_drop"] for v in rows if v["full_deletion_drop"] > 0])),
                           "with_any_interface_edge": int(sum(v["interface_edges"] > 0 for v in rows))}
    hist = read("history")
    s["history"] = {}
    for task in ("T0", "T1"):
        for fam in ("N2", "SH"):
            ks = [k for k in hist if k.startswith(task) and _n2(k) == (fam == "N2")]
            row = {"runs": len(ks)}
            for measure in ("raw_turn", "raw_forward"):
                for tag in ("g00", "g39", "drift"):
                    vals = ([np.mean([abs(d[measure]["final"]) for d in hist[k]["drift"]]) for k in ks] if tag == "drift"
                            else [abs(hist[k][tag][measure]["final"]) for k in ks])
                    row[f"{measure}_abs_{tag}_t"] = _t(vals)
                row[f"{measure}_g39_fraction_surviving_5_ticks"] = float(np.median(
                    [abs(hist[k]["g39"][measure]["after"]) / max(abs(hist[k]["g39"][measure]["final"]), 1e-9) for k in ks]))
                row[f"{measure}_g39_relative_to_steady_contrast"] = float(np.median(
                    [abs(hist[k]["g39"][measure]["final"]) / max(abs(hist[k]["g39"][measure]["steady_contrast"]), 1e-9) for k in ks]))
            row["raw_forward_g39_positive"] = int(sum(hist[k]["g39"]["raw_forward"]["final"] > 0 for k in ks))
            s["history"][f"{task}-{fam}"] = row
    beh = read("behaviour")
    s["behaviour"] = {}
    for task in ("T0", "T1"):
        for fam in ("N2", "SH"):
            v = [x for k, x in beh.items() if k.startswith(task) and _n2(k) == (fam == "N2")]
            s["behaviour"][f"{task}-{fam}"] = {
                "persistence": float(np.mean([x["turn_sign_persistence"] for x in v])),
                **{f"{kind}_{target}": {p: float(np.mean([x[kind][target]["beta"][p] for x in v])) for p in PREDICTORS}
                   for kind in ("pooled", "within_wey") for target in ("forward", "turn")}}
    resp = read("response")
    s["response"] = {}
    for fam in ("N2", "SH"):
        ks = [k for k in resp if _n2(k) == (fam == "N2")]
        for tag in ("g00", "g39"):
            vals = [resp[k][tag]["directional_turn_signed_motor"] for k in ks]
            s["response"][f"{fam}-{tag}"] = {"signed_motor_t": _t(vals), "positive": int(sum(x > 0 for x in vals)),
                                             "n": len(vals), "per_champion": dict(zip(ks, vals))}
    s["response"]["spearman_signed_vs_swap_g39"] = spearman(
        [resp[k]["g39"]["directional_turn_signed_motor"] for k in resp], [resp[k]["g39"]["use_swap"] for k in resp])
    save("summary", s)


if __name__ == "__main__":
    stage = sys.argv[1]
    from wormwars.accounting import attempt  # compute accounting (T0, D069)
    with attempt(Path(__file__).parent / "compute", default="probe", experiment="02b", stage=stage):
        {"magnitudes": stage_magnitudes, "response": stage_response, "behaviour": stage_behaviour,
         "history": stage_history, "criticality": stage_criticality,
         "criticality_R1": lambda: stage_criticality("R1", ("N2",)),
         "criticality_R2": lambda: stage_criticality("R2", ("N2",)),
         "kept_edges": stage_kept_edges, "summarise": stage_summarise}[stage]()
    from wormwars.accounting import write_aggregate  # every stage's attempts summed (D071)
    write_aggregate(Path(__file__).parent / "compute", Path(__file__).parent / "compute.json")
