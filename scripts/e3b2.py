"""E3b-2: where E3b-1's gain comes from (exploratory; docs/E3/E3b-2-PLAN.md draft 2, D194).

    python scripts/e3b2.py project | attribution | lesions | latch | report
    add --smoke for toy sizes in runs/e3b2-smoke, with stand-in champions (never results)

Every stage runs in E2's stage frame, configured for E3b-2's own folders, once, with one rerun after a crash or
a kill. E3b-1's records and genomes are read-only inputs, hash-checked. Each chunk's per-maze arrays are saved
when it completes, with its full specification. A rerun resumes at the first chunk that did not complete, and
refuses a saved chunk whose specification differs. Nothing here is a registered test (§8).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import torch
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e04a.evolve import moved  # noqa: E402
from wormwars.e3 import attribution as AT  # noqa: E402
from wormwars.e3 import maze as MZ  # noqa: E402
from wormwars.e3 import maze_measures as MM  # noqa: E402
from wormwars.e3 import maze_organisms as MO  # noqa: E402
from wormwars.e3 import maze_world as MW  # noqa: E402
from wormwars.e3 import organism as O  # noqa: E402
from wormwars.e3 import probe as P  # noqa: E402
from wormwars.e3 import tuning as T  # noqa: E402
from wormwars.e4s import arms as A  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population  # noqa: E402


def _load(name: str, file: str):
    s = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


E = _load("e2_for_e3b2", "e2.py")  # E2's stage frame; E3b-1's runner is not imported (D194)

EXP = ROOT / "experiments" / "E3-ab-organism" / "E3b-2"
OUT = ROOT / "runs" / "e3b2"
PLAN = "docs/E3/E3b-2-PLAN.md"
E3B1 = "experiments/E3-ab-organism/E3b-1"
FIXED = {  # §2: read-only inputs, checked at load (LF line endings, as committed)
    f"{E3B1}/champions.json": None, f"{E3B1}/evaluate.json": None, f"{E3B1}/PREREGISTRATION.md": None,
    "experiments/E3-ab-organism/E3b-0/report.json": "af82e1c9573b0f2b73d228d065c277f9bb46310f2fd8d395439a557e359d7df8",
    "experiments/E4s-stereo-module/E4s-0/module.json": "9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4",
}
GENOMES_E3B1 = ROOT / "runs" / "e3b1" / "genomes"
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", PLAN, *FIXED]
SMOKE = False

STAGES = ["project", "attribution", "lesions", "latch", "report"]
REGISTERED = {
    "maze_seed": 1_180_000, "c": 5, "H": 2400, "colony": 8, "spawns": 4,
    "trail": {"mu": 0.01, "lam": 0.02, "delta": 0.05, "d0": 1.142},
    "ids": {"fresh": [7000, 7256], "benchmark": [7300, 7556], "smoke": [9800, 9900]},
    "t_champions": [f"ta:{i}" for i in range(8)] + [f"tf:{i}" for i in range(8)],
    "n_champions": [f"n:{i}" for i in range(4)],
    "chunk": 16, "cap_gpu_hours": 5.0, "reserve_factor": 1.25,
    "bootstrap": {"resamples": 10_000, "seed": 0},
    "drops": ["n champions", "side attribution", "lesions none"],
    "rerun_kill_tail_seconds": 900,
}
RECORD = {s: s for s in STAGES}
WHAT = {s: f"E3b-2's {s}" for s in STAGES}


def configure() -> None:
    E.EXP, E.OUT, E.GUARDED, E.REGISTERED, E.SMOKE = EXP, OUT, GUARDED, REGISTERED, SMOKE
    E.STAGES = STAGES
    E.OUTCOMES = {**E.OUTCOMES, "stopped": "E3b-2: not completed (the run stopped)",
                  "cap": "E3b-2: not completed (the cap was reached)"}
    E.RECORD.update(RECORD)
    E.WHAT.update(WHAT)


configure()


def output_paths() -> list:
    """Every place E3b-2 writes: its experiment folder and its run folder (tested to lie outside E3b-0 and E3b-1)."""
    return [EXP, OUT, OUT / "compute", EXP / "chunks"]


def sha_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def check_inputs() -> dict:
    got = {}
    for rel, want in FIXED.items():
        h = sha_lf(ROOT / rel)
        if want is not None and h != want:
            raise SystemExit(f"{rel} has changed (sha256 {h}): refusing to run")
        got[rel] = h
    return got


def base_config():
    cfg = E.E1.config(6.0)
    want = json.loads(E.E1_GATE.read_text(encoding="utf-8"))["resolved_config"]
    if hashlib.sha256(json.dumps(want, sort_keys=True).encode()).hexdigest() != E.config_sha256(cfg):
        raise SystemExit("Task N's resolved configuration differs from E1's gate: refusing to run")
    return cfg


def cfg_for(access: str):
    R = REGISTERED
    return MW.maze_config(base_config(), c=R["c"], horizon=R["H"], colony=R["colony"], access=access,
                          spawns=R["spawns"], **R["trail"])


E.task_config = lambda: cfg_for("shared")


def seed() -> int:
    return REGISTERED["maze_seed"]


def ids(key: str) -> np.ndarray:
    return np.arange(*REGISTERED["ids"][key])


def maze_ids() -> np.ndarray:
    """The fresh block (smoke: the first 4 smoke ids)."""
    return ids("smoke")[:4] if SMOKE else ids("fresh")


# ============================================================================== organisms

_CX: dict = {}


def context(cfg) -> dict:
    if not _CX:
        con, l1 = load_connectome(), A.load_l1()
        s = T.start_organism("seed", con, l1, cfg.brain)
        _CX.update(con=con, seed=s, spec=BrainSpec.from_connectome(s.ext))
    return _CX


def check_genome(genome: Genome, want: str, name: str) -> None:
    if genome_hash(genome, 0) != want:
        raise SystemExit(f"{name}'s genome does not match its E3b-1 record: refusing to run")


def organisms(cfg) -> dict:
    """{name: genome}: the seed, the T champions and N's champions, each checked against E3b-1's record. Smoke
    uses deterministic stand-ins (the seed with every mutable parameter perturbed)."""
    cx = context(cfg)
    if "organisms" in cx:
        return cx["organisms"]
    out = {"seed": cx["seed"].genome}
    names = REGISTERED["t_champions"] + REGISTERED["n_champions"]
    if SMOKE:
        sc = {k: v * 8 for k, v in T.scales(cx["seed"].ext).items()}
        for k, n in enumerate(names):
            out[n] = Genome.cat([cx["seed"].genome]).mutate(cfg.mutation, generator=torch.Generator().manual_seed(100 + k),
                                                            scales=sc)
    else:
        rec = json.loads((ROOT / E3B1 / "champions.json").read_text(encoding="utf-8"))["champions"]
        want = {f"{c['arm']}:{c['run']}": c["sha256"] for c in rec if c["read"] == "final"}
        for n in names:
            arm, i = n.split(":")
            g, _ = load_population(GENOMES_E3B1 / f"{arm}-run{int(i):02d}-champion-final.npz", cx["spec"], cfg.brain)
            check_genome(g, want[n], n)
            out[n] = g
    cx["organisms"] = out
    return out


# ============================================================================== the plan: chunks

def default_plan() -> dict:
    return {"t": list(REGISTERED["t_champions"]), "n": list(REGISTERED["n_champions"]), "side": True,
            "lesion_conditions": ["shared", "none"], "drops": []}


def chunks_of(items: list, size: int) -> list:
    return [items[k:k + size] for k in range(0, len(items), size)]


def attribution_chunks(plan: dict) -> list:
    """A: one chunk per champion and condition with its 16 functional hybrids, the all-seed first. B: two
    champions per chunk, 8 side hybrids each, shared trails."""
    out = []
    fcoal = AT.coalitions(AT.FUNCTIONAL)
    for cond in ("shared", "none"):
        for c in plan["t"]:
            out.append({"analysis": "A", "condition": cond, "key": f"A-{cond}-{c.replace(':', '')}",
                        "variants": [(c, ("hybrid", "functional", tuple(sorted(S, key=AT.FUNCTIONAL.index))))
                                     for S in fcoal]})
    if plan["side"]:
        scoal = AT.coalitions(AT.SIDE)
        for k, pair in enumerate(chunks_of(plan["t"], 2)):
            out.append({"analysis": "B", "condition": "shared", "key": f"B-shared-{k:02d}",
                        "variants": [(c, ("hybrid", "side", tuple(sorted(S, key=AT.SIDE.index))))
                                     for c in pair for S in scoal]})
    return out


LESIONS = [("intact",), ("clamp_a",), ("clamp_b",), ("edge", "input_cut"), ("edge", "gate_cut"), ("reflex",),
           ("edge", "outputs_a"), ("edge", "outputs_b")]


def lesion_organisms(plan: dict) -> list:
    return plan["t"] + plan["n"] + ["seed"]


def lesion_chunks(plan: dict) -> list:
    out = []
    orgs = lesion_organisms(plan)
    for cond in plan["lesion_conditions"]:
        variants = [(o, les) for o in orgs for les in LESIONS]
        for k, part in enumerate(chunks_of(variants, REGISTERED["chunk"])):
            out.append({"analysis": "C", "condition": cond, "key": f"C-{cond}-{k:02d}", "variants": part})
        for k, part in enumerate(chunks_of([(o, ("scent",)) for o in orgs], REGISTERED["chunk"])):
            out.append({"analysis": "C", "condition": cond, "key": f"C-{cond}-scent-{k:02d}", "variants": part,
                        "scent": True})
        out.append({"analysis": "C", "condition": cond, "key": f"C-{cond}-w2ref",
                    "variants": [("w2_ref", ("w2_reference",))]})
    return out


def latch_chunks(plan: dict) -> list:
    orgs = lesion_organisms(plan)
    return [{"analysis": "D", "condition": "shared", "key": f"D-shared-{k:02d}", "variants": [(o, ("intact",)) for o in part],
             "recorder": True} for k, part in enumerate(chunks_of(orgs, REGISTERED["chunk"]))]


def all_chunks(plan: dict) -> list:
    return attribution_chunks(plan) + lesion_chunks(plan) + latch_chunks(plan)


def projected_seconds(t: dict, plan: dict) -> float:
    secs = 0.0
    for c in all_chunks(plan):
        if c.get("recorder"):
            secs += t["recorder_chunk"]
        elif c.get("scent"):
            secs += t["scent_chunk"]
        elif c["analysis"] == "C" and any(v[1][0] in ("clamp_a", "clamp_b", "reflex") for v in c["variants"]):
            secs += t["clamp_chunk"]
        else:
            secs += t["chunk"]
    return secs


DROP_STEPS = {"n champions": lambda p: p.__setitem__("n", []),
              "side attribution": lambda p: p.__setitem__("side", False),
              "lesions none": lambda p: p.__setitem__("lesion_conditions", ["shared"])}


def apply_drops(t: dict, spent: float) -> dict:
    """§7: the drop order, until spent + the projection × 1.25 fits the cap."""
    plan = default_plan()
    R = REGISTERED
    for name in [None] + R["drops"]:
        if name is not None:
            DROP_STEPS[name](plan)
            plan["drops"].append(name)
        total = spent + projected_seconds(t, plan) / 3600 * R["reserve_factor"]
        if total <= R["cap_gpu_hours"]:
            break
    return {**plan, "planned_total": total, "fits": total <= R["cap_gpu_hours"]}


# ============================================================================== playing a chunk

def variant_genome(org: str, les: tuple, orgs: dict, cx) -> tuple[Genome, dict]:
    """(genome, clamps) for one variant."""
    ext = cx["seed"].ext
    if les[0] == "w2_reference":
        return AT.edge_lesion(orgs["seed"], ext, "outputs_both"), {}
    g = orgs[org]
    if les[0] == "hybrid":
        groups = AT.parameter_groups(ext, les[1])
        return AT.hybrid(orgs["seed"], g, groups, set(les[2])), {}
    if les[0] in ("intact", "scent"):
        return g, {}
    if les[0] == "edge":
        return AT.edge_lesion(g, ext, les[1]), {}
    if les[0] == "reflex":
        return g, AT.reflex_clamp(ext)
    low, _, high = AT.latch_states(g, ext)
    coding = AT.a_high(g, ext)
    a_state, b_state = (high, low) if coding in (True, None) else (low, high)
    return g, {ext.index(O.Q): a_state if les[0] == "clamp_a" else b_state}


def variant_id(org: str, les: tuple, genome: Genome, clamps: dict) -> str:
    return f"{org}|{json.dumps(les)}|{genome_hash(genome, 0)}|{json.dumps(sorted(clamps.items()))}"


def summaries(ev: dict, H: int) -> dict:
    """[organisms, mazes] per outcome (§3), from events shaped [organisms, mazes, ...]."""
    vt = ev["visit_tick"]
    S, n = vt.shape[:2]
    f = lambda x: np.asarray(x).reshape(S * n, *np.asarray(x).shape[2:])  # noqa: E731
    legs = MM.legs(f(vt))
    rate, unvisited = MM.later_leg_rate(f(vt), H)
    out = {"visits": MM.colony_mean(f(ev["visits"])), "legs": MM.colony_mean(legs), "later_leg_rate": rate,
           "unvisited_share": unvisited, "round_trip_share": (legs >= 2).mean(axis=-1),
           "later_first_b": MM.later_first_b(f(ev["first_b_tick"]), H)}
    return {k: np.asarray(v, dtype=np.float64).reshape(S, n) for k, v in out.items()}


def play_chunk(chunk: dict, orgs: dict, cx, dev, mazes: np.ndarray) -> dict:
    cond = chunk["condition"]
    cfg = cfg_for(cond)
    iface = AT.without_scent(cx["seed"].iface) if chunk.get("scent") else cx["seed"].iface
    built = [variant_genome(o, les, orgs, cx) for o, les in chunk["variants"]]
    pop = Genome.cat([g for g, _ in built])
    if str(dev) != "cpu":
        pop = moved(pop, dev)
    brain = AT.HeldBrain(pop)
    if any(c for _, c in built):
        brain.clamp([c for _, c in built])
    S, n = len(built), len(mazes)
    strain_of = torch.as_tensor(np.repeat(np.arange(S), n), device=dev).view(-1, 1)
    w = MW.MazeWorld(cfg, iface, brain, strain_of, run_seed=seed(), world_ids=np.tile(mazes, S), device=dev, access=cond)
    rec = None
    if chunk.get("recorder"):
        rec = AT.LatchRecorder(cx["seed"].ext, [g.select([0]) if g.n_strains > 1 else g for g, _ in built])
        rec.attach(w)
        w.recorder = rec
    w.run()
    ev = w.task_events()
    ev = {k: (v.reshape(S, n, *v.shape[1:]) if isinstance(v, np.ndarray) and v.shape[:1] == (S * n,) else v)
          for k, v in ev.items()}
    out = summaries(ev, int(cfg.world.max_ticks))
    if rec is not None:
        res = rec.result()
        for k in res[0]:
            if k != "strain":
                out[f"latch_{k}"] = np.asarray([r[k] for r in res], dtype=np.int64).reshape(S, n)
    return out


def chunk_spec(chunk: dict, orgs: dict, cx, mazes, cfg_sha: str) -> dict:
    built = [variant_genome(o, les, orgs, cx) for o, les in chunk["variants"]]
    return {"mazes": [int(mazes[0]), int(mazes[-1]) + 1, len(mazes)], "maze_seed": seed(), "condition": chunk["condition"],
            "config_sha256": cfg_sha, "scent_removed": bool(chunk.get("scent")), "recorder": bool(chunk.get("recorder")),
            "organisms": [variant_id(o, les, g, c) for (o, les), (g, c) in zip(chunk["variants"], built)],
            "composition": [len(built), len(mazes), REGISTERED["colony"]]}


def chunk_path(key: str) -> Path:
    return EXP / "chunks" / f"{key}.npz"


def run_chunk(path: Path, spec: dict, play) -> None:
    """Skipped if a completed attempt saved it with the same specification (its observations stand); refused if
    the saved specification differs; else played and saved atomically."""
    text = json.dumps(spec, sort_keys=True)
    if path.exists():
        with np.load(path, allow_pickle=False) as z:
            have = str(z["spec"])
        if have != text:
            raise SystemExit(f"{path.name} was saved with another specification: refusing to resume over it")
        return
    arrays = dict(play())
    arrays["spec"] = np.asarray(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **{k: np.asarray(v) for k, v in arrays.items()})
    E.replace(tmp, path)


def run_chunks(ctx, chunks: list) -> list:
    dev = ctx.args.device
    cfg = cfg_for("shared")
    cx = context(cfg)
    orgs = organisms(cfg)
    mazes = maze_ids()
    done = []
    for c in chunks:
        sha = E.config_sha256(cfg_for(c["condition"]))
        spec = chunk_spec(c, orgs, cx, mazes, sha)
        path = chunk_path(c["key"])
        ctx.cap.check()

        def play(c=c):
            with acct.category("measure"):
                return play_chunk(c, orgs, cx, dev, mazes)
        run_chunk(path, spec, play)
        done.append(path.name)
        E.write_atomic(E.partial_path(ctx.doc["stage"]), {"stage": ctx.doc["stage"], "completed_chunks": done})
    return done


def load_chunk(key: str) -> dict:
    with np.load(chunk_path(key), allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


# ============================================================================== stages

def preflight() -> dict:
    """Every maze of the run (and the benchmark's), built before the first stage; redraws listed."""
    redrawn = []
    for key in ("fresh", "benchmark", "smoke"):
        for mid in ids(key):
            _, k = MZ.walls_for(run_seed=seed(), maze_id=int(mid), c=REGISTERED["c"])
            MZ.maze_for(run_seed=seed(), maze_id=int(mid), episode=0, c=REGISTERED["c"], n_spawns=REGISTERED["spawns"])
            if k:
                redrawn.append({"block": key, "id": int(mid), "k": int(k)})
    return {"redrawn": redrawn}


def cmd_project(args):
    def body(ctx):
        inputs = check_inputs()
        dev = ctx.args.device
        cfg = cfg_for("shared")
        cx = context(cfg)
        orgs = organisms(cfg)
        mazes = ids("smoke")[:4] if SMOKE else ids("benchmark")
        plan = default_plan()
        a = attribution_chunks(plan)[0]
        les = [c for c in lesion_chunks(plan) if any(v[1][0] == "clamp_a" for v in c["variants"])][0]
        scent = [c for c in lesion_chunks(plan) if c.get("scent")][0]
        rec = latch_chunks(plan)[0]
        timing = {}
        for name, c in (("chunk", a), ("clamp_chunk", les), ("scent_chunk", scent), ("recorder_chunk", rec)):
            for _ in range(2):  # the second of two repeats
                if str(dev) != "cpu":
                    torch.cuda.synchronize()
                t0 = time.perf_counter()
                with acct.category("measure"):
                    play_chunk(c, orgs, cx, dev, mazes)
                if str(dev) != "cpu":
                    torch.cuda.synchronize()
                timing[name] = time.perf_counter() - t0
        spent = E.clock().spent_hours() + (time.perf_counter() - ctx.cap.t_start) / 3600
        p = apply_drops(timing, spent)
        if not p["fits"] and not SMOKE:
            raise SystemExit("even after every drop the plan exceeds the cap: the owner is asked")
        return {"fixed_inputs": inputs, "mazes": preflight(), "timing": timing, "plan": p,
                "note": "timings on the benchmark block 7300-7555 (outside every block); no result is read"}

    return E.run_stage(args, "project", lambda a, prov: {}, body)


def stage_plan(args, prov) -> dict:
    p = E.require_earlier(args, prov, "project")
    return {"project": p}


def make_stage(stage: str, chunks_fn):
    def cmd(args):
        def body(ctx):
            check_inputs()
            ctx.doc["stage"] = stage
            plan = ctx.earlier["project"]["plan"]
            chunks = chunks_fn(plan)
            done = run_chunks(ctx, chunks)
            return {"chunks": done, "plan": plan, "mazes": [int(maze_ids()[0]), int(maze_ids()[-1]) + 1],
                    "composition": [REGISTERED["chunk"], len(maze_ids()), REGISTERED["colony"]]}
        return E.run_stage(args, stage, stage_plan, body)
    return cmd


cmd_attribution = make_stage("attribution", attribution_chunks)
cmd_lesions = make_stage("lesions", lesion_chunks)
cmd_latch = make_stage("latch", latch_chunks)


# ============================================================================== the readings (report)

def read_table(X: np.ndarray, players, seed_shared: np.ndarray) -> dict:
    """One champion's attribution from X [coalitions, mazes] (visits; the coalitions in `AT.coalitions` order,
    the all-seed first): the gain, Shapley allocations, reversion, transplant and dividends, in units of the
    seed's shared mean."""
    den = float(np.mean(seed_shared))
    coal = AT.coalitions(players)
    table = {S: (float(X[k].mean()) - float(X[0].mean())) / den for k, S in enumerate(coal)}
    divs = AT.dividends(table, players)
    return {"gain": table[frozenset(players)], "shapley": AT.shapley(table, players),
            "reversion": AT.reversion(table, players), "transplant": AT.transplant(table, players),
            "dividends": {"+".join(sorted(S, key=list(players).index)) or "none": v for S, v in divs.items()},
            "table": {"+".join(sorted(S, key=list(players).index)) or "none": v for S, v in table.items()}}


def bootstrap_indices(n_mazes: int, resamples: int, seed: int) -> np.ndarray:
    return np.random.default_rng(seed).integers(0, n_mazes, size=(resamples, n_mazes))


def shapley_matrix(players) -> np.ndarray:
    """W [players, coalitions] with Shapley values = W @ table."""
    coal = AT.coalitions(players)
    W = np.zeros((len(players), len(coal)))
    for k, S in enumerate(coal):
        unit = {S2: float(S2 == S) for S2 in coal}
        phi = AT.shapley(unit, players)
        W[:, k] = [phi[p] for p in players]
    return W


def t_interval(x) -> dict:
    x = np.asarray(x, dtype=np.float64)
    if len(x) < 2:
        return {"n": len(x), "mean": float(x.mean()) if len(x) else None}
    se = x.std(ddof=1) / math.sqrt(len(x))
    q = float(stats.t.ppf(0.975, len(x) - 1))
    return {"n": len(x), "mean": float(x.mean()), "ci95": [float(x.mean() - q * se), float(x.mean() + q * se)]}


def attribution_report(plan: dict) -> dict:
    R = REGISTERED["bootstrap"]
    out, by = {}, {}
    seeds_shared = []
    for c in plan["t"]:
        seeds_shared.append(load_chunk(f"A-shared-{c.replace(':', '')}")["visits"][0])
    exact = all(np.array_equal(seeds_shared[0], s) for s in seeds_shared)
    seed_shared = seeds_shared[0]
    for part, players, cond_list in (("functional", AT.FUNCTIONAL, ("shared", "none")), ("side", AT.SIDE, ("shared",))):
        if part == "side" and not plan["side"]:
            continue
        for cond in cond_list:
            per = {}
            Xs = {}
            for c in plan["t"]:
                if part == "functional":
                    X = load_chunk(f"A-{cond}-{c.replace(':', '')}")["visits"]
                else:
                    k = plan["t"].index(c) // 2
                    Z = load_chunk(f"B-shared-{k:02d}")["visits"]
                    off = (plan["t"].index(c) % 2) * len(AT.coalitions(players))
                    X = Z[off:off + len(AT.coalitions(players))]
                Xs[c] = X
                per[c] = read_table(X, players, seed_shared)
            by[(part, cond)] = Xs
            # schedules: means with t intervals over runs, and the maze-paired bootstrap (joint across champions)
            idx = bootstrap_indices(len(seed_shared), R["resamples"], R["seed"])
            Wm = shapley_matrix(players)
            sched = {}
            for arm in ("ta", "tf"):
                names = [c for c in plan["t"] if c.startswith(arm)]
                if not names:
                    continue
                s = {"gain": t_interval([per[c]["gain"] for c in names])}
                for kind in ("shapley", "reversion", "transplant"):
                    s[kind] = {p: t_interval([per[c][kind][p] for c in names]) for p in players}
                den = seed_shared[idx].mean(axis=1)  # [R]
                phis = []
                for c in names:
                    M = Xs[c][:, idx].mean(axis=2)  # [coalitions, R]
                    table = (M - M[0]) / den
                    phis.append(Wm @ table)  # [players, R]
                ph = np.mean(phis, axis=0)
                s["shapley_bootstrap95"] = {p: [float(np.quantile(ph[i], 0.025)), float(np.quantile(ph[i], 0.975))]
                                            for i, p in enumerate(players)}
                gains = sum(per[c]["gain"] for c in names)
                s["share_of_summed_gain"] = {p: (sum(per[c]["shapley"][p] for c in names) / gains if gains else None)
                                             for p in players}
                sched[arm] = s
            out[f"{part}-{cond}"] = {"per_champion": per, "schedules": sched}
    w2 = load_chunk("C-shared-w2ref")["visits"][0] if chunk_path("C-shared-w2ref").exists() else None
    flags = {}
    if w2 is not None:
        for (part, cond), Xs in by.items():
            for c, X in Xs.items():
                low = [k for k in range(len(X)) if X[k].mean() < w2.mean()]
                if low:
                    flags[f"{part}-{cond}-{c}"] = low
    return {"tables": out, "seed_exact_across_chunks": bool(exact), "seed_shared_mean": float(seed_shared.mean()),
            "w2_reference_mean": None if w2 is None else float(w2.mean()), "hybrids_below_w2": flags}


def lesion_report(plan: dict, seed_shared_mean: float) -> dict:
    rows = {}
    for c in lesion_chunks(plan):
        z = load_chunk(c["key"])
        for k, (o, les) in enumerate(c["variants"]):
            rows[(c["condition"], o, json.dumps(les))] = {m: z[m][k] for m in
                                                          ("visits", "legs", "later_leg_rate", "unvisited_share",
                                                           "round_trip_share", "later_first_b")}
    out = {}
    for (cond, o, les), r in rows.items():
        if les == json.dumps(["intact"]) or o == "w2_ref":
            continue
        base = rows[(cond, o, json.dumps(["intact"]))]
        out.setdefault(cond, {}).setdefault(o, {})[les] = {
            m: float((r[m].mean() - base[m].mean()) / (seed_shared_mean if m == "visits" else 1.0)) for m in r}
    intact = {cond: {o: {m: float(r[m].mean()) for m in r} for (cc, o, les), r in rows.items()
                     if cc == cond and les == json.dumps(["intact"])} for cond in plan["lesion_conditions"]}
    sched = {}
    for cond in out:
        for arm in ("ta", "tf", "n"):
            names = [o for o in out[cond] if o.startswith(arm + ":")]
            if names:
                sched.setdefault(cond, {})[arm] = {les: t_interval([out[cond][o][les]["visits"] for o in names])
                                                   for les in out[cond][names[0]]}
    return {"cost": out, "intact": intact, "schedules": sched,
            "note": "cost = (lesioned − intact) / the seed's shared mean for visits; raw differences for the others"}


def latch_report(plan: dict) -> dict:
    out = {}
    for c in latch_chunks(plan):
        z = load_chunk(c["key"])
        for k, (o, _) in enumerate(c["variants"]):
            tot = {key[len("latch_"):]: int(z[key][k].sum()) for key in z if key.startswith("latch_")}
            per_maze_agree = []
            for g in ("A", "B"):
                d = z[f"latch_decided_{g}"][k]
                a = z[f"latch_agree_{g}"][k]
                per_maze_agree.append(np.where(d > 0, a / np.maximum(d, 1), np.nan))
            r = {"counts": tot}
            for g in ("A", "B"):
                r[f"agreement_{g}"] = tot[f"agree_{g}"] / tot[f"decided_{g}"] if tot[f"decided_{g}"] else None
            vals = [r["agreement_A"], r["agreement_B"]]
            r["agreement_equal_weight"] = None if None in vals else (vals[0] + vals[1]) / 2
            for d in ("to_a", "to_b"):
                legs = tot[f"legs_{d}"]
                r[f"switched_{d}"] = tot[f"crossed_{d}"] / legs if legs else None
                r[f"latency_{d}"] = tot[f"lat_{d}"] / tot[f"crossed_{d}"] if tot[f"crossed_{d}"] else None
            out[o] = r
    return out


def genome_report(plan: dict, cfg) -> dict:
    cx = context(cfg)
    orgs = organisms(cfg)
    ext = cx["seed"].ext
    pc = P.ProbeContext(ext, cx["seed"].iface, cfg, device="cpu")
    out = {}
    for o in lesion_organisms(plan):
        g = orgs[o]
        e = MO.named_edges(g, ext)
        low, mid, high = AT.latch_states(g, ext)
        r = {"latch": {"low": low, "unstable": mid, "high": high, "w_qq": e[(O.Q, O.Q)],
                       "ra_q": e[("E3_RA", O.Q)], "rb_q": e[("E3_RB", O.Q)], "a_high": AT.a_high(g, ext)},
             "gate": {cn: e[(O.Q, cn)] for cn in O.COMPARATORS}}
        r["effective_bias"] = {state: {cn: float(g.bias[0, ext.index(cn)]) + e[(O.Q, cn)] * math.tanh(qv)
                                       for cn in O.COMPARATORS} for state, qv in (("low", low), ("high", high))}
        r["resting_turn"] = {state: float(P.u_at(g, pc, 0.0, pc.latch_state(g, qv))[0])
                             for state, qv in (("low", low), ("high", high))}
        out[o] = r
    return out


def replication_report(plan: dict, seed_shared_mean: float) -> dict:
    ev = json.loads((ROOT / E3B1 / "evaluate.json").read_text(encoding="utf-8"))["readings"]["G"]["d"]
    pairs = []
    for arm in ("ta", "tf"):
        for i, d_test in enumerate(ev[arm]):
            name = f"{arm}:{i}"
            if name in plan["t"]:
                X = load_chunk(f"A-shared-{name.replace(':', '')}")["visits"]
                pairs.append({"champion": name, "fresh": float((X[-1].mean() - X[0].mean()) / seed_shared_mean),
                              "test": float(d_test)})
    f, t = np.array([p["fresh"] for p in pairs]), np.array([p["test"] for p in pairs])
    return {"pairs": pairs, "correlation": float(np.corrcoef(f, t)[0, 1]) if len(pairs) > 2 else None,
            "means": {arm: {"fresh": float(np.mean([p["fresh"] for p in pairs if p["champion"].startswith(arm)])),
                            "test": float(np.mean([p["test"] for p in pairs if p["champion"].startswith(arm)]))}
                      for arm in ("ta", "tf") if any(p["champion"].startswith(arm) for p in pairs)}}


def cmd_report(args):
    def requires(a, prov):
        out = stage_plan(a, prov)
        for s in ("attribution", "lesions", "latch"):
            out[s] = E.require_earlier(a, prov, s)
        return out

    def body(ctx):
        check_inputs()
        plan = ctx.earlier["project"]["plan"]
        cfg = cfg_for("shared")
        att = attribution_report(plan)
        with acct.category("probe"):
            genomes = genome_report(plan, cfg)
        summary = {"attribution": att, "lesions": lesion_report(plan, att["seed_shared_mean"]),
                   "latch": latch_report(plan), "genomes": genomes,
                   "replication": replication_report(plan, att["seed_shared_mean"])}
        E.write_atomic(EXP / "summary.json", summary)
        return {"summary": summary, "note": "descriptive throughout (§9); no gate"}

    return E.run_stage(args, "report", requires, body)


# ============================================================================== smoke and main

def use_smoke(args) -> None:
    """Toy sizes and stand-in champions in runs/e3b2-smoke. Never results."""
    global EXP, OUT, SMOKE
    EXP = OUT = ROOT / "runs" / "e3b2-smoke"
    SMOKE = True
    R = REGISTERED
    R["H"] = 120
    R["t_champions"] = ["ta:0", "ta:1", "tf:0", "tf:1"]
    R["n_champions"] = ["n:0"]
    R["bootstrap"] = {"resamples": 200, "seed": 0}
    configure()
    if args.command in STAGES:
        for s in STAGES[STAGES.index(args.command):]:
            for f in (E.record_path(s), E.marker_path(s), E.partial_path(s)):
                if EXP in f.parents:
                    f.unlink(missing_ok=True)
        if STAGES.index(args.command) <= STAGES.index("attribution"):
            for f in (EXP / "chunks").glob("*.npz") if (EXP / "chunks").exists() else []:
                f.unlink()


COMMANDS = {"project": cmd_project, "attribution": cmd_attribution, "lesions": cmd_lesions, "latch": cmd_latch,
            "report": cmd_report}


def main():
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
    smoke = "--smoke" in sys.argv
    out_dir = ROOT / "runs" / ("e3b2-smoke" if smoke else "e3b2")
    try:
        run_script(main, out_default=str(out_dir), default="measure", name="e3b2")
    finally:
        agg = out_dir / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
