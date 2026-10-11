"""E4 / 04c: do the two minds share? The pilot (docs/E4/E4-DESIGN.md v3 §6; exploratory, GPU, after the owner's
word). The formal stages come after the pre-registration, which takes the pilot's numbers.

    python scripts/e4.py pilot --device cuda
    add --smoke for toy sizes in runs/e4-smoke (never results)

**The pilot** (§6), in this order:
1. **The generation-1 load** under common random numbers, for X0 and for X+ at every candidate factor (0.25 to 4):
   32 copies of E-G bred once from one generator seed, played on the same mazes.
2. **Training:** X0 and X+, 4 runs each, paired by run seed (the same training mazes and the same breeding
   generator; one batch per arm, since a batch needs distinct seeds), 100 generations of E3c's GA frame
   (population 32, elites 3, truncation 8) from 32 copies of E-G, gated in every rollout, checkpoints every 10.
   **X+ trains at the largest candidate meeting the load bound** (Fable, code review: the pilot's P1 numbers must
   come from a factor the formal run may use; the rule's fallback is now that factor). Every run's lineage replay
   is checked against its final population before anything else is played.
3. **Champions:** each run's final population on the validation block, per strain and maze; the best is the
   champion; its lineage's mutation count (the scale rule's input).
4. **Each champion's conditions,** per maze, on the test block and on a second block of the same size (the
   re-evaluation band), in the same batch composition (both reviewers): under shared trails, intact, the 32 cut,
   the 32 mean-substituted, into A, into B, sensory, comparator and the 8 source bundles (X+), intact and the sham
   cut (X0); under own and no trails, intact, cut and mean-substituted (X+), intact (X0). The latch's switches
   and their timing, the visit ticks (for censored leg durations and the directional read), the source means (X+
   champions, one batch per arm), the slots' weights.
5. **References:** E-G (generation 0) as a champion; the blind family (E3d's members that need no E3c champion)
   and the navigators on the validation block, for competence.

Everything is written as it completes (the partial record, and the stage's salvage), and the bulky arrays and
genomes are saved under `runs/e4/pilot/` (local): the final populations, the champions, the selection matrices, the
parents, the validation matrices and the visit ticks.

**Its blocks** (maze run seed 1 400 000, E4's own): validation 40 000-40 063, test 40 100-40 227, re-evaluation
40 300-40 427, load 40 500-40 507; training ids from 60 000 000 (span 10 000 000). The formal blocks will be fresh.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e3 import assembly as AS  # noqa: E402
from wormwars.e3 import attribution as AT  # noqa: E402
from wormwars.e3 import islands as IS  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e4 import arms as AR  # noqa: E402
from wormwars.e4 import evaluate as EVL  # noqa: E402
from wormwars.e4 import lineage as LI  # noqa: E402
from wormwars.e4 import means as ME  # noqa: E402
from wormwars.e4 import scale_rule as SR  # noqa: E402
from wormwars.e4 import train as TR  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.evolve import breed  # noqa: E402
from wormwars.evo.genomes import genome_hash, save_population  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e4", "e2.py")  # E2's stage frame, configured for E4's own folders
X = _load("e3c_for_e4", "e3c.py")  # E3c's base configuration (Task N, checked against E1's gate)
D = _load("e3d_for_e4", "e3d.py")  # E3d's blind family and navigators (built, not run, from here)

EXP = ROOT / "experiments" / "E4-two-minds"
OUT = ROOT / "runs" / "e4"
SMOKE_DIR = ROOT / "runs" / "e4-smoke"
DESIGN = "docs/E4/E4-DESIGN.md"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", DESIGN]
SMOKE = False

STAGES = ["pilot"]
ARMS = AR.ARMS
ARM_OFFSET = {"x0": 0, "x_plus": 10}
REGISTERED = {
    "design": DESIGN, "maze_seed": 1_400_000, "c": 6, "H": 1800, "colony": 8, "spawns": 4, "family": "islands",
    "k_r": 0, "trail": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": 1.142},
    "ga": {"population": 32, "elites": 3, "truncation": 8,
           "mutation": {"w_sigma": 0.08, "tau_sigma": 0.15, "bias_sigma": 0.05, "p_mutate": 1.0}},
    "pilot": {"runs_per_arm": 4, "G": 100, "W": 8, "checkpoint_every": 10, "run_seed_base": 1_400_100,
              "train_base": 60_000_000, "train_span": 10_000_000,
              "blocks": {"validation": [40_000, 40_064], "test": [40_100, 40_228], "reeval": [40_300, 40_428],
                         "load": [40_500, 40_508]},
              "load_replicates": 4, "load_seed_base": 1_400_900, "reach_simulations": 20_000,
              "reach_seed": 20_261_012, "formal_G": [200, 300, 400]},
    "blind": {"turn_grid": [-0.8, -0.4, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 1.95],
              "walk_grid": {"persistence": [0.25, 0.5, 0.8], "rate": [0.5, 1.0, 2.0], "speed": 1.0, "seed": 0}},
    "cap_gpu_hours": 3.0,  # §6: the pilot at 2-3 h; it counts toward E4's 30
    "rerun_kill_tail_seconds": 900,  # E2's kill reconciliation needs it (Astra, code review)
}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E4: not completed (the run stopped)",
                  "cap": "E4: not completed (the cap was reached)"}
    E.RECORD.update({s: s for s in STAGES})
    E.WHAT.update({s: f"E4's {s}" for s in STAGES})
    E.task_config = lambda: cfg_for("shared")
    D.REGISTERED["walk_grid"] = REGISTERED["blind"]["walk_grid"]  # read by D.build


def cfg_for(access: str):
    R = REGISTERED
    cfg = MW.maze_config(X.base_config(), c=R["c"], horizon=R["H"], colony=R["colony"], access=access,
                         spawns=R["spawns"], family=R["family"], k_r=R["k_r"], **R["trail"])
    g = R["ga"]
    cfg.evo.population, cfg.evo.elites, cfg.evo.truncation = g["population"], g["elites"], g["truncation"]
    cfg.evo.worlds_per_strain = int(R["pilot"]["W"])
    for k, v in g["mutation"].items():
        setattr(cfg.mutation, k, v)
    return cfg


configure()


def block(name: str) -> np.ndarray:
    return np.arange(*REGISTERED["pilot"]["blocks"][name])


def seed() -> int:
    return REGISTERED["maze_seed"]


def pilot_runs() -> list:
    P_ = REGISTERED["pilot"]
    return [{"arm": arm, "run": ARM_OFFSET[arm] + k, "seed": P_["run_seed_base"] + k}
            for arm in ARMS for k in range(P_["runs_per_arm"])]


def preflight(ids) -> dict:
    R, redrawn = REGISTERED, []
    for mid in sorted(set(int(x) for x in ids)):
        _, _, im = IS.maze_for(run_seed=seed(), maze_id=mid, episode=0, c=R["c"], k_r=R["k_r"], n_spawns=R["spawns"])
        if im.k:
            redrawn.append({"id": mid, "k": int(im.k)})
    return {"checked": len(set(int(x) for x in ids)), "redrawn": redrawn}


def _r(x) -> list:
    return np.round(np.asarray(x, dtype=np.float64), 6).tolist()


def _trim(vt: np.ndarray) -> np.ndarray:
    """Visit ticks [..., LEGS], −1 padded, cut after the longest record, as int32."""
    n = int((vt >= 0).sum(-1).max()) if vt.size else 0
    return vt[..., :max(n, 1)].astype(np.int32)


def _summary(out: dict) -> dict:
    s = {"visits": _r(out["visits"]), "legs": _r(out["legs"]), "mean_visits": float(np.mean(out["visits"])),
         "mean_legs": float(np.mean(out["legs"]))}
    if "switches" in out:
        s["switches"] = {k: out["switches"][k] for k in ("match_share", "aligned_share", "latency_min", "latency_max",
                                                         "latency_q99")}
    return s


def pilot_dir() -> Path:
    return OUT / "pilot"


def generation1_load(cfg, org, cx, dev) -> dict:
    """§1's load bound: 32 copies of E-G bred once (3 elites, 29 mutated children), for X0 and for X+ at each
    candidate, from the same generator seed, on the same mazes; per replicate the mean fitness (visits per wey)."""
    P_ = REGISTERED["pilot"]
    P = cfg.evo.population
    start = Genome.cat([org.genome.select([0])] * P)
    zero, ids = np.zeros(P), block("load")
    arms = {"x0": AR.scales(cx, "x0"), **{f"x_plus_{f}": AR.scales(cx, "x_plus", cross_factor=f) for f in SR.CANDIDATES}}
    out = {k: [] for k in arms}
    fn = TR.gated_rollout(org.gate)
    for rep in range(P_["load_replicates"]):
        pops = []
        for sc in arms.values():
            gen = torch.Generator(device=dev).manual_seed(P_["load_seed_base"] + rep)
            pops.append(breed(EV.moved(start, dev), zero, cfg, gen, sc))
        res = fn(cfg, org.iface, Genome.cat(pops), ids, seed(), dev, chunk_worlds=len(pops) * P * len(ids))
        score = np.asarray(res.score).reshape(len(arms), P, len(ids)).mean(axis=(1, 2))
        for j, k in enumerate(arms):
            out[k].append(float(score[j]))
    means = {k: float(np.mean(v)) for k, v in out.items()}
    return {"per_replicate": out, "means": means, "composition": [len(arms) * P, len(ids), REGISTERED["colony"]],
            "load_ok": {f: SR.load_ok(means[f"x_plus_{f}"], means["x0"]) for f in SR.CANDIDATES}}


def champion(cfg, org, final: Genome, dev) -> dict:
    """The final population's best on the validation block (mean visits; ties to the lowest index), with the whole
    strain × maze matrix (selection noise against the block's size)."""
    names = {f"s{k}": final.select([k]) for k in range(final.n_strains)}
    out = EVL.play(cfg, org, names, block("validation"), seed(), dev, access="shared")
    mat = np.stack([out[f"s{k}"]["visits"] for k in range(final.n_strains)])
    k = int(np.argmax(mat.mean(axis=1)))
    return {"index": k, "matrix": mat, "genome": final.select([k])}


def assess(cfg, org, cx, g: Genome, arm: str, means, dev, tag: str) -> dict:
    """One champion's conditions on the test and re-evaluation blocks (the module docstring, step 4)."""
    if arm == "x_plus":
        shared = EVL.conditions(g, cx, means=means)
        other = ("intact", "cut_all", "meansub_all")
    else:
        shared = EVL.conditions(g, cx, names=("intact", "cut_all"))
        other = ("intact",)
    rec, cost, events = {"blocks": {}}, {}, {}
    for blk in ("test", "reeval"):
        rec["blocks"][blk] = {}
        for access in EVL.TRAILS:
            if blk == "reeval" and access != "shared":
                continue
            conds = shared if access == "shared" else {n: shared[n] for n in other}
            t0 = time.perf_counter()
            out = EVL.play(cfg, org, conds, block(blk), seed(), dev, access=access, q_flips=access == "shared")
            cost[f"{blk}_{access}_seconds"] = time.perf_counter() - t0
            cost[f"{blk}_{access}_composition"] = [len(conds), len(block(blk)), REGISTERED["colony"]]
            rec["blocks"][blk][access] = {n: _summary(o) for n, o in out.items()}
            for n, o in out.items():
                events[f"{blk}/{access}/{n}"] = _trim(o["visit_tick"])
    np.savez_compressed(pilot_dir() / f"visit-ticks-{tag}.npz", **events)
    rec["slot_weights"] = _r(g.w[0, AR.slot_indices(cx)].cpu())
    rec["cost"] = cost
    return rec


def blind_references(cfg, con, l1, org, dev) -> dict:
    """E3d's blind members that need no E3c champion, the navigators, the seed and E-G, on the validation block."""
    cx3 = AS.context(con, l1, cfg.brain)
    B = REGISTERED["blind"]
    specs = [{"name": "wall_left", "kind": "wall", "hand": "left"}, {"name": "wall_right", "kind": "wall", "hand": "right"},
             {"name": "w2", "kind": "w2"}]
    specs += [{"name": f"w2_turn_{r:g}", "kind": "w2_turn", "r": r} for r in B["turn_grid"]]
    specs += [{"name": f"w2_{v[3:].lower()}", "kind": "carrier", "variant": v} for v in ("W2+M40", "W2+M80")]
    specs += [{"name": f"walk_p{p:g}_r{q:g}", "kind": "walk", "persistence": p, "rate": q}
              for p in B["walk_grid"]["persistence"] for q in B["walk_grid"]["rate"]]
    specs += [{"name": "seed_noses", "kind": "seed", "noses": False}]
    specs += [{"name": "oracle", "kind": "oracle", "navigator": True},
              {"name": "follower_shared", "kind": "follower", "access": "shared", "navigator": True},
              {"name": "follower_none", "kind": "follower", "access": "none", "navigator": True},
              {"name": "seed", "kind": "seed", "noses": True, "navigator": True}]
    ids = block("validation")
    out = {}
    for sp in specs:
        access = sp.get("access", "shared")
        c = cfg_for(access)
        iface, brain, _, _ = D.build(sp, c, con, l1, cx3, {}, dev)
        out[sp["name"]] = _play_one(c, iface, brain, ids, access, dev, role="navigator" if sp.get("navigator") else "blind")
    eg_blind = dataclasses.replace(org, iface=AT.without_scent(org.iface))
    for name, o in (("eg_noses", eg_blind), ("eg", org)):
        out[name] = _play_one(cfg, o.iface, TR.gated_brain(o.genome.select([0]), o.gate, dev), ids, "shared", dev,
                              role="blind" if name == "eg_noses" else "navigator")
    blind = {k: v["mean_visits"] for k, v in out.items() if v["role"] == "blind"}
    best = max(blind, key=blind.get)
    return {"conditions": out, "b_max": {"member": best, "mean_visits": blind[best]}}


def _play_one(cfg, iface, brain, ids, access, dev, role) -> dict:
    strain_of = torch.zeros(len(ids), 1, dtype=torch.long, device=dev)
    w = MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=seed(), world_ids=np.asarray(ids), device=dev, access=access)
    w.run()
    ev = w.task_events()
    legs = MM.legs(ev["visit_tick"])
    v = MM.colony_mean(ev["visits"])
    return {"role": role, "visits": _r(v), "mean_visits": float(v.mean()),
            "median_colony_legs": float(np.median(MM.colony_mean(legs)))}


def cmd_pilot(args):
    def body(ctx):
        dev = ctx.args.device
        P_ = REGISTERED["pilot"]
        cfg = cfg_for("shared")
        con, l1 = load_connectome(), A.load_l1()
        cx = AR.context(con, l1, cfg.brain)
        org = cx["org"]
        runs = pilot_runs()
        by_run = {r["run"]: r for r in runs}
        P, G_ = cfg.evo.population, P_["G"]
        pilot_dir().mkdir(parents=True, exist_ok=True)
        state = {"stage": "pilot", "partial": True}
        ctx.salvage = lambda: state

        def save_partial():
            E.write_atomic(E.partial_path("pilot"), state)

        train = [int(x) for r in runs for g in range(G_)
                 for x in EV.train_ids(r["seed"], g, P_["W"], P_["train_base"], P_["train_span"])]
        state["mazes"] = preflight([*train, *[i for b in P_["blocks"] for i in block(b)]])
        start = Genome.cat([org.genome.select([0])] * P)
        cost = state["cost"] = {}

        # 1. the generation-1 load, then X+'s pilot factor
        ctx.cap.check()
        with acct.category("probe"):
            t0 = time.perf_counter()
            load = state["generation1_load"] = generation1_load(cfg, org, cx, dev)
            cost["load_seconds"] = time.perf_counter() - t0
        factor = SR.largest_load_passing(load["load_ok"])
        state["pilot_cross_factor"] = {"factor": factor if factor is not None else SR.CANDIDATES[0],
                                       "rule": "the largest candidate meeting the load bound" if factor is not None
                                       else "no candidate meets the load bound: the smallest is used, flagged"}
        f_x = state["pilot_cross_factor"]["factor"]
        scales = {"x0": AR.scales(cx, "x0"), "x_plus": AR.scales(cx, "x_plus", cross_factor=f_x)}
        state["mutable_counts"] = {"x0": AR.mutable_count(cx, "x0"), "x_plus": AR.mutable_count(cx, "x_plus", cross_factor=f_x)}
        save_partial()

        # 2. training, one batch per arm (paired by seed)
        recs, rep, cost["training_seconds"], comp = [], [], {}, {}

        def on_checkpoint(records, g):
            state["training_progress"] = {"generation": g, "runs": [{"run": x.spec.run, "generations": len(x.log)}
                                                                    for x in records]}
            save_partial()

        for arm in ARMS:
            specs = [EV.RunSpec(r["run"], r["seed"], 0.0) for r in runs if r["arm"] == arm]
            cap = LI.Capture(TR.gated_rollout(org.gate))
            t0 = time.perf_counter()
            got = EV.evolve_batch(cfg, org.iface, org.genome.spec, specs, generations=G_,
                                  checkpoint_every=P_["checkpoint_every"], validation_ids=block("validation"),
                                  world_seed=seed(), id_base=P_["train_base"], id_span=P_["train_span"], device=dev,
                                  rollout_fn=cap, check=ctx.cap.check, category=acct.category,
                                  initial=lambda r: start, mutation_scales=lambda r: scales[arm],
                                  on_checkpoint=on_checkpoint)
            cost["training_seconds"][arm] = time.perf_counter() - t0
            comp[f"training_{arm}"] = [len(specs) * P, P_["W"], REGISTERED["colony"]]
            comp[f"checkpoints_{arm}"] = [len(specs), len(block("validation")), REGISTERED["colony"]]
            for rec in got:
                AR.assert_frozen(start, rec.final, scales[arm])
            replayed = LI.replay(cfg, specs, cap.selections, initial=lambda r: start,
                                 mutation_scales=lambda r: scales[arm], device=dev)
            for rec, rp in zip(got, replayed):
                if not all(torch.equal(getattr(rec.final, k), getattr(rp["final"], k)) for k in ("w", "bias", "tau", "g")):
                    raise RuntimeError(f"run {rec.spec.run}: the lineage replay differs from the run")
                save_population(pilot_dir() / f"final-{arm}-run{rec.spec.run:02d}.npz", rec.final, cfg=cfg,
                                run=rec.spec.run, stage="pilot")
            np.savez_compressed(pilot_dir() / f"selections-{arm}.npz",
                                score=np.stack([s["score"] for s in cap.selections]),
                                progress=np.stack([s["progress"] for s in cap.selections]),
                                **{f"parents_source_run{rp['run']:02d}": np.array([p["source"] for p in rp["parents"]])
                                   for rp in replayed},
                                **{f"parents_child_run{rp['run']:02d}": np.array([p["child"] for p in rp["parents"]])
                                   for rp in replayed})
            recs += got
            rep += replayed
            state["composition"] = comp
            save_partial()

        # 3. champions and their lineages
        champs = {}
        state["runs"] = {arm: [] for arm in ARMS}
        for rec, rp in zip(recs, rep):
            r = by_run[rec.spec.run]
            ctx.cap.check()
            with acct.category("holdout"):
                t0 = time.perf_counter()
                ch = champion(cfg, org, rec.final, dev)
                t_ch = time.perf_counter() - t0
            champs[r["run"]] = ch["genome"]
            np.savez_compressed(pilot_dir() / f"validation-{r['arm']}-run{r['run']:02d}.npz", visits=ch["matrix"])
            save_population(pilot_dir() / f"champion-{r['arm']}-run{r['run']:02d}.npz", ch["genome"], cfg=cfg,
                            run=r["run"], stage="pilot", strain=ch["index"])
            state["runs"][r["arm"]].append({
                "run": r["run"], "seed": r["seed"], "champion_index": ch["index"],
                "champion_sha256": genome_hash(ch["genome"], 0),
                "validation_means": _r(ch["matrix"].mean(axis=1)), "champion_seconds": t_ch,
                "lineage_mutations": LI.mutations(rp["parents"], ch["index"]),
                "generation0": {"counts": rec.generation0.get("counts"), "train_ids": rec.generation0.get("train_ids")},
                "log": [{k: g.get(k) for k in ("generation", "best_fitness", "mean_fitness", "best_count", "mean_count",
                                               "max_count", "zero_share", "batch_seconds")} for g in rec.log],
                "learning_curve": [{k: c[k] for k in ("generation", "validation_mean", "validation_counts", "sha256")}
                                   for c in rec.checkpoints]})
            save_partial()

        # 4. the conditions; X+'s source means in one batch per arm
        xp = [r for r in runs if r["arm"] == "x_plus"]
        ctx.cap.check()
        with acct.category("probe"):
            t0 = time.perf_counter()
            means = ME.source_means(cfg, org.iface, Genome.cat([champs[r["run"]] for r in xp]), org.gate,
                                    block("validation"), seed(), dev)
            cost["source_means_seconds"] = time.perf_counter() - t0
        comp["source_means"] = [len(xp), len(block("validation")), REGISTERED["colony"]]
        mean_of = {r["run"]: means[k] for k, r in enumerate(xp)}
        for arm in ARMS:
            for entry in state["runs"][arm]:
                ctx.cap.check()
                with acct.category("probe"):
                    a = assess(cfg, org, cx, champs[entry["run"]], arm, mean_of.get(entry["run"]), dev,
                               tag=f"{arm}-run{entry['run']:02d}")
                if arm == "x_plus":
                    a["source_means"] = _r(mean_of[entry["run"]])
                entry["assessment"] = a
                save_partial()

        # 5. references
        ctx.cap.check()
        with acct.category("probe"):
            t0 = time.perf_counter()
            state["reference_eg"] = assess(cfg, org, cx, org.genome.select([0]), "x0", None, dev, tag="eg")
            state["blind_references"] = blind_references(cfg, con, l1, org, dev)
            cost["references_seconds"] = time.perf_counter() - t0
        save_partial()

        # the scale rule's inputs: every lineage's mutated share, scaled to candidate formal horizons
        counts = [x["lineage_mutations"] for arm in ARMS for x in state["runs"][arm]]
        rule = {"lineage_mutations": counts, "breedings": G_ - 1, "by_formal_G": {}}
        for g_formal in P_["formal_G"]:
            fc = SR.formal_counts(counts, g_pilot=G_ - 1, g_formal=g_formal - 1)
            reach = {f: SR.reach(fc, cfg.mutation.w_sigma, f, cfg.brain.w_max, n_sim=P_["reach_simulations"],
                                 seed=P_["reach_seed"]) for f in SR.CANDIDATES}
            rule["by_formal_G"][str(g_formal)] = {"counts": fc, **SR.choose(reach, load["load_ok"])}
        state["scale_rule"] = rule
        state.pop("partial", None)
        state["note"] = "exploratory (§6); the pre-registration takes its numbers, and the formal blocks are fresh"
        return state

    return E.run_stage(args, "pilot", lambda a, prov: {}, body)


def use_smoke(args) -> None:
    global EXP, OUT, SMOKE
    EXP = OUT = SMOKE_DIR
    SMOKE = True
    R = REGISTERED
    R["H"] = 60
    R["ga"].update({"population": 6, "elites": 2, "truncation": 3})
    R["pilot"].update({"runs_per_arm": 2, "G": 3, "W": 2, "checkpoint_every": 2, "load_replicates": 1,
                       "reach_simulations": 500, "formal_G": [6],
                       "blocks": {"validation": [8000, 8002], "test": [8002, 8004], "reeval": [8004, 8006],
                                  "load": [8006, 8008]}})
    R["blind"] = {"turn_grid": [0.4], "walk_grid": {"persistence": [0.5], "rate": [1.0], "speed": 1.0, "seed": 0}}
    configure()
    for s in STAGES:
        files = [E.record_path(s), E.marker_path(s), E.partial_path(s)]
        files += [E.rerun_note(E.record_path(s))] + [E.attempt1(f) for f in list(files)]
        for f in files:
            if EXP in f.parents:
                f.unlink(missing_ok=True)


COMMANDS = {"pilot": cmd_pilot}


def main():
    import argparse
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=list(COMMANDS))
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--guarded", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--reason")
    args = ap.parse_args()
    if args.smoke:
        use_smoke(args)
    COMMANDS[args.command](args)


if __name__ == "__main__":
    from wormwars.accounting import run_script
    if any(a == "--out" or a.startswith("--out=") for a in sys.argv[1:]):
        raise SystemExit("--out is not accepted: E4 writes only to its own folders")
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e4-smoke" if smoke else "e4")
    try:
        run_script(main, out_default=str(out_dir), default="measure", name="e4")
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
