"""E5-1a, the checks before E5-1's formal run (docs/E5/E5-1-DESIGN.md §7, §14). Exploratory, with stop rules fixed in
the design and, where it left a number open, in §14 before the stage runs.

Stages, in order (each writes its record to experiments/E5-hunter/E5-1/E5-1a/, or runs/e5-1a-smoke/ with --smoke):
  equivalence  (CPU) Task H against itself after E5-1's changes: E5-0's engine (a worktree at 7d25460) against the
               working tree, every setting, bit for bit; the mixed world against each slot alone at the training and
               validation shapes; the GA rollout against that serial reference (the weighted fitness and validation);
               E5-0's 68 arrays and H1-ghost against Task N re-run
  graphs       (CPU) the 24 SH-route graphs rebuilt and checked against 03r's manifests; the graft's checks; P's
               configurations, host-magnitude hashes and checks
  cuda         (GPU) Task H on CUDA with fixed genomes: score level (worlds sized by a measured SD), prey paths,
               pursuit traces, H1-ghost against Task N, attack disabled, respawns, state level, the ledger
  bench        (GPU) every shape timed, generation 0 and a scoring (B-construction) batch; the projection, the
               evaluation and rerun reserves, the cut levels. E5-1a stops here: the owner sets the cap
               (`cap --hours H --note "..."`), before anything below runs
  signal       (GPU) the selection signal on N2's construction (pilot seeds 1 519 000 to 003)
  pilot        (GPU) the same on the 4 pilot SH-route graphs; 2 of them evolved 100 generations, 4 runs each
  composition  (GPU) the batch shapes against one strain x 512, on scoring genomes
  sensitivity  (GPU) 64 mutants around B's 16 starts and 8 generation-0 winners

    python scripts/e5_1a.py <stage> [--smoke] [--device cuda]

A formal stage needs a clean, pushed tree; a later stage needs the earlier stages' records, explicitly complete or
passed, made on the code that is here now; the stages after the bench need the owner's cap, bound to the bench's
record. Every play checks E5-1a's cap first, and the ledger, the sequence overflow and finiteness after.
"""

from __future__ import annotations

import os

if __name__ == "__main__" and "--device" not in os.sys.argv:  # CPU stages see no GPU
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import torch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import graft as G  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import Brain, Genome  # noqa: E402
from wormwars.connectome.loader import load_connectome  # noqa: E402
from wormwars.e04a import evolve as EV  # noqa: E402
from wormwars.e1 import controllers as C  # noqa: E402
from wormwars.e4s import arms as EA  # noqa: E402
from wormwars.e5 import arms as AR  # noqa: E402
from wormwars.e5 import ga as GA  # noqa: E402
from wormwars.e5 import graphs as GR  # noqa: E402
from wormwars.e5 import hunters as HN  # noqa: E402
from wormwars.e5 import mixed as MX  # noqa: E402
from wormwars.e5 import plan as PL  # noqa: E402
from wormwars.e5 import settings as ST  # noqa: E402
from wormwars.e5.hunt import HUNTER, PREY, HuntWorld, hunt_config  # noqa: E402
from wormwars.evo.genomes import genome_hash, load_population, save_population  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

torch.set_grad_enabled(False)
EXP = ROOT / "experiments" / "E5-hunter" / "E5-1" / "E5-1a"
OUT = ROOT / "runs" / "e5-1a"
SMOKE = False
GUARDED = ["wormwars", "scripts", "configs", "docs/E5/E5-1-DESIGN.md"]
CODE = ["wormwars", "scripts", "configs"]
CLOCK: reg.CapClock | None = None
REF_COMMIT = "7d254607ea09c22a466b3eb3ef75433ae1eb3dec"  # E5-0's formal code (its stages ran on it)
REF_WORKTREE = ROOT.parent / "wormWars-e5-1ref"
E5_0_OLD = ROOT / "runs" / "e5-0" / "reference-old.npz"  # E5-0's old engine's 68 arrays (ab749bb), local
E1_FREEZE = ROOT / "experiments" / "E1-navigation" / "freeze.json"
STAGES = ("equivalence", "graphs", "cuda", "bench", "signal", "pilot", "composition", "sensitivity")
BEFORE = {"equivalence": (), "graphs": ("equivalence",), "cuda": ("equivalence", "graphs"),
          "bench": ("equivalence", "graphs", "cuda"), "signal": ("bench",), "pilot": ("signal",),
          "composition": ("pilot",), "sensitivity": ("composition",)}
AFTER_CAP = ("signal", "pilot", "composition", "sensitivity")
SMOKE_TICKS = 40

REGISTERED = {
    "cap_hours": 6.0,  # E5-1a's own cap: every stage, CPU and GPU time together
    "ledger_tol": 1e-5,  # T0's
    "check_seed": PL.SEED_BASE["check"],  # generation-0 genomes for the checks and the bench, never a reading
    "equivalence": {"shape_runs": 4, "formula_tol": 1e-12},
    "cuda": {"sd_worlds": 512,  # of the 1 024 in the SD block: each check's per-world SD of the difference
             "z": 54.8, "unit": 512, "max_worlds": 8192, "margin": 0.10, "precision": 0.03,
             # §14: a trajectory agrees if its largest absolute difference over the ticks is at most 1e-3 cells; a
             # check passes if 99% of its worlds agree (256 worlds, so at most 2 may differ)
             "path_tol": 1e-3, "path_share": 0.99, "path_worlds": 256, "trace_ticks": 30, "trace_worlds": 256,
             "respawn_worlds": 64, "attack_worlds": 256,
             "state_tol": 1e-4, "state_factor": 1.5, "state_ticks": 300, "ghost_ids": [991_200_000, 512],
             "settings": ["H1-bite", "H2-0.5", "H2-1", "H2b-walk-0.5", "H2b-wall-0.5"]},
    "bench": {"generations": 6, "checkpoint_every": 5, "suite_settings": ["H1-bite", "H2-0.5", "H2b-walk-0.5"],
              "rerun_reserve": 0.15},
    "signal": {"level": 0.90, "min_populations": 3},
    "pilot": {"generations": 100},
    "composition": {"suite_settings": list(ST.PROBE_SETTINGS)},
    "sensitivity": {"mutants": 64, "share_floor": 0.7, "seed": PL.SEED_BASE["sensitivity"], "chunk_strains": 16},
}
# §8's evaluation, by count, per item (episodes); the cut levels are recomputed from what each cut removes
EVAL_PER_RUN = {"suite C and G0": 2 * 17 * 512, "probes": 5 * 4 * 2 * 512, "lesion": 4 * 512,
                "bridges": 2 * 2 * 512}
EVAL_FIXED = {"references": 60_928, "B's Task N readings": 16_384}
O0_PER_TEST_RUN = 2 * 32 * 64  # the 32 strains of generation 0 on 64 mixture worlds, at the fixed and calibrated gains
RUNS = {"G-N2": 32, "G-SHr": 80, "A0r": 8, "A0": 8, "P": 12, "B": 16}


# ================================================================================================= frame
def write(name: str, doc) -> None:
    reg.write_json(EXP / name, doc, atomic=True)


def read(name: str) -> dict:
    return json.loads((EXP / name).read_text(encoding="utf-8"))


def cap() -> reg.CapClock:
    global CLOCK
    if CLOCK is None:
        CLOCK = reg.CapClock(REGISTERED["cap_hours"], OUT / "compute.json")
    return CLOCK


def guard(stage: str) -> dict:
    prov = reg.provenance(GUARDED)
    if not SMOKE:
        if prov.get("dirty"):
            raise SystemExit("the tree is dirty: commit and push the code first")
        reg.require_pushed(prov)
    for name in BEFORE[stage]:
        if not (EXP / f"{name}.json").exists():
            raise SystemExit(f"{name}.json is missing: run its stage first")
        d = read(f"{name}.json")
        if not (d.get("passed") is True or (d.get("complete") is True and "passed" not in d)):
            raise SystemExit(f"{name} did not complete and pass: E5-1a stops")
        if not SMOKE:
            reg.require_same_code(d["provenance_at_start"]["git_commit"], CODE)
    if stage in AFTER_CAP:
        if not (EXP / "cap.json").exists():
            raise SystemExit("the owner sets the cap at the bench (stage `cap`) before the selection signal")
        c = read("cap.json")
        if c.get("bench_sha256") != reg.file_sha256(EXP / "bench.json"):
            raise SystemExit("cap.json was set on another bench record")
        if not c.get("fits"):
            raise SystemExit("the projection does not fit the owner's cap even with every cut: E5-1 goes back to them")
    reg.start_marker(EXP, stage, prov)
    return prov


def ids_of(block: str, n: int | None = None) -> np.ndarray:
    """A block's ids (the first n); with --smoke, ids from 987 100 000 on, outside every E5-1 block."""
    first, count = PL.BLOCKS[block]
    n = count if n is None else int(n)
    if n > count:
        raise ValueError(f"{block} holds {count} ids, not {n}")
    if SMOKE:
        first = 987_100_000 + 50_000 * list(PL.BLOCKS).index(block)
    return np.arange(first, first + n, dtype=np.int64)


def span_of(block: str) -> tuple[int, int]:
    first, count = PL.BLOCKS[block]
    return (987_100_000 + 50_000 * list(PL.BLOCKS).index(block), 40_000) if SMOKE else (first, count)


class Env:
    def __init__(self):
        self.con = load_connectome()
        self.iface = load_interface(self.con)
        self.l1 = EA.load_l1()
        self.cfg = task_config()
        self.ext, self.spec, self.gface = GR.grafted(self.con, self.l1)
        self.gface_mean = G.graft_interface(self.ext, self.l1, probe="mean")
        self.params = ST.prey_params()
        self.freeze = json.loads(E1_FREEZE.read_text(encoding="utf-8"))


def task_config(ticks: int | None = None, ledger_every_tick: bool = True):
    cfg = hunt_config()
    if (cfg.world.forward_gain, cfg.world.turn_gain) != (PL.GAINS["forward"], PL.GAINS["turn"]):
        raise SystemExit("Task H's gains are not E5-1's 4.0 and 2.0")
    e, m = cfg.evo, PL.GA
    e.population, e.elites, e.truncation = m["population"], m["elites"], m["truncation"]
    e.worlds_per_strain, e.islands = m["worlds_per_strain"], m["islands"]
    for k, v in m["mutation"].items():
        setattr(cfg.mutation, k, v)
    if SMOKE:
        cfg.world.max_ticks = SMOKE_TICKS
        e.population, e.elites, e.truncation = 4, 1, 2
    if ticks is not None:
        cfg.world.max_ticks = int(ticks)
    cfg.world.check_ledger_every_tick = bool(ledger_every_tick)
    return cfg


def check_ledger(rel: float, where: str) -> None:
    if not math.isfinite(rel) or rel > REGISTERED["ledger_tol"]:
        raise SystemExit(f"the ledger's residual is {rel} at {where}: E5-1a stops")


def moved(g: Genome, device) -> Genome:
    return EV.moved(g, device)


def c_champions(env) -> list[tuple[str, Genome]]:
    out = [(k, g) for k, (g, _) in HN.e4s1_champions(env.con, env.cfg.brain).items()]
    return out[:3] if SMOKE else out


def gen0(env, graph, ext, seed: int, n: int) -> Genome:
    return AR.initial("G-N2" if graph.label == "N2" else "G-SHr", seed, graph, ext, env.l1, env.cfg.brain, n)


def play(env, cfg, hunter, names, world_ids, device="cpu", iface=None, **kw):
    """`play_settings` with E5-1a's cap checked first and the ledger after (the sequence overflow and finiteness are
    checked inside `play`)."""
    cap().check()
    r = MX.play_settings(cfg, iface or env.gface, hunter, list(names), world_ids, PL.WORLD_SEED, env.params,
                         prey_iface=env.iface, device=device, **kw)
    check_ledger(r.ledger_rel_error, f"{names[0]}..{names[-1]} on {device}")
    return r


def finish_world(w, where: str) -> None:
    """For a world stepped by hand: the ledger, the sequence overflow (`hunt_events`) and finiteness."""
    rel = (w.ledger_rel_max if w.ledger_rel_max is not None else w.energy_ledger_rel_error()).max().item()
    check_ledger(rel, where)
    w.hunt_events()
    if not all(bool(torch.isfinite(t).all()) for t in (w.pos, w.heading, w.energy)):
        raise SystemExit(f"a non-finite state at {where}: E5-1a stops")


def weighted_by_slot(counts: np.ndarray, names) -> np.ndarray:
    """[strains]: the score's weighted mean over columns played under training settings."""
    slots = np.array([ST.TRAINING.index(n) for n in names])
    return ST.weighted_fitness(counts, ST.column_weights(slots))


def formula(counts_by_slot: np.ndarray) -> np.ndarray:
    """(1/3)[c1 + mean(c2..c6) + mean(c7, c8)] from [strains, 8] per-slot means, the design's own words."""
    c = np.asarray(counts_by_slot, dtype=np.float64)
    return (c[:, 0] + c[:, 1:6].mean(1) + c[:, 6:8].mean(1)) / 3


def _same(a: dict, b: dict) -> list[str]:
    bad = [k for k in sorted(set(a) | set(b)) if k not in a or k not in b]
    for k in sorted(set(a) & set(b)):
        x, y = np.asarray(a[k]), np.asarray(b[k])
        if x.shape != y.shape or not np.array_equal(x, y, equal_nan=x.dtype.kind == "f"):
            bad.append(k)
    return bad


def _result_arrays(r, cols=None) -> dict:
    sel = (lambda x: x) if cols is None else (lambda x: x[:, cols])
    out = {k: sel(getattr(r, k)) for k in ("captures", "bite_energy", "pin_push", "prey_wall_limited")}
    out.update({f"ev {k}": sel(v) for k, v in r.events.items()})
    return out


# ================================================================================================= statistics
def interval(d: np.ndarray) -> list[float]:
    """The 90% t interval of a mean of paired differences (0 width if they are all equal)."""
    from scipy.stats import t as T
    d = np.asarray(d, dtype=np.float64)
    if d.size < 2:
        return [float(d.mean()), float(d.mean())]
    h = float(T.ppf(0.95, d.size - 1)) * d.std(ddof=1) / math.sqrt(d.size)
    return [float(d.mean() - h), float(d.mean() + h)]


def stratified(d: np.ndarray, names) -> tuple[float, list[float]]:
    """The score-weighted mean of paired differences over worlds played under training settings, and its 90% interval:
    t with Welch-Satterthwaite degrees of freedom from the per-slot variances (§14; conservative where one static slot
    carries a third of the weight)."""
    from scipy.stats import t as T
    names = list(names)
    w = np.asarray(ST.TRAINING_WEIGHTS, dtype=np.float64) / float(sum(ST.TRAINING_WEIGHTS))
    est, var, dfden = 0.0, 0.0, 0.0
    for k, s in enumerate(ST.TRAINING):
        x = np.asarray(d, dtype=np.float64)[[i for i, n in enumerate(names) if n == s]]
        if x.size < 2:
            raise ValueError(f"the slot {s} has {x.size} worlds: a stratified interval needs 2 per slot")
        v = w[k] ** 2 * x.var(ddof=1) / x.size
        est, var, dfden = est + w[k] * x.mean(), var + v, dfden + v ** 2 / (x.size - 1)
    if var == 0.0:
        return float(est), [float(est), float(est)]
    h = float(T.ppf(0.95, var ** 2 / dfden)) * math.sqrt(var)
    return float(est), [float(est - h), float(est + h)]


def required_worlds(d: np.ndarray, names) -> tuple[float, int, int]:
    """(the SD that sizes the check, its worlds, the worlds before the cap): n = (54.8 sd)^2, rounded up to 512, at most 8 192. For worlds under
    training settings, the weighted mean's SD, sqrt(8 sum_k w_k^2 s_k^2), so its interval has the same width."""
    c = REGISTERED["cuda"]
    names = list(names)
    if all(n in ST.TRAINING for n in names) and len(set(names)) == len(ST.TRAINING):
        w = np.asarray(ST.TRAINING_WEIGHTS, dtype=np.float64) / float(sum(ST.TRAINING_WEIGHTS))
        s2 = [np.asarray(d)[[i for i, n in enumerate(names) if n == s]].var(ddof=1) for s in ST.TRAINING]
        sd = float(math.sqrt(len(ST.TRAINING) * float(w ** 2 @ np.array(s2))))
    else:
        sd = float(np.std(d, ddof=1)) if np.asarray(d).size > 1 else 0.0
    n = max(c["unit"], int(math.ceil(math.ceil((c["z"] * sd) ** 2) / c["unit"]) * c["unit"]))
    return sd, (min(n, c["max_worlds"]) if not SMOKE else 16), n  # the last: before the design's cap at 8 192


def judged(d: np.ndarray, names, sd: float, n_required: int, n_uncapped: int) -> dict:
    """The check passes if its interval lies within the margin. The 0.03 half-width is reached only if the design's
    cap (8 192 worlds) did not bind; whether it did is recorded, not a stop (§14.1)."""
    c = REGISTERED["cuda"]
    names = list(names)
    mixed = len(set(names)) > 1
    est, (lo, hi) = stratified(d, names) if mixed else (float(np.mean(d)), interval(d))
    half = (hi - lo) / 2
    return {"worlds": int(np.asarray(d).size), "sd": sd, "worlds_required": n_required,
            "worlds_required_uncapped": n_uncapped,
            "estimate": est, "interval": [lo, hi], "half_width": half,
            "precision_reached": bool(half <= c["precision"]), "weighted": mixed,
            "share_identical": float((np.asarray(d) == 0).mean()),
            "passed": bool(-c["margin"] <= lo and hi <= c["margin"])}


# ================================================================================================= batched plays
class Hunters:
    """Hunters to compare: `labels`, and `make(indices, device)` giving a brain whose strains are those hunters (a
    scripted hunter is one strain, index 0)."""

    def __init__(self, labels, make, iface, scripted=False):
        self.labels, self.make, self.iface, self.scripted = list(labels), make, iface, scripted

    @staticmethod
    def of(genomes: list[tuple[str, Genome]], iface) -> "Hunters":
        gen = Genome.cat([g for _, g in genomes])
        return Hunters([lab for lab, _ in genomes], lambda idx, d: Brain(moved(gen.select(idx), d)), iface)


def counts_by_task(env, cfg, hunters: Hunters, S: int, chunk: list, ids: np.ndarray, device) -> dict:
    """Every hunter on every id: (hunter, chunk of W ids) tasks, S strains per play (each strain on its own W ids, the
    columns' settings `chunk`, the same for every strain), the last play padded with repeats that are not kept.
    Returns {label: counts [n]} in id order."""
    W, n = len(chunk), ids.size
    if n % W:
        raise SystemExit(f"{n} worlds do not split into chunks of {W}")
    if hunters.scripted and S != 1:
        raise SystemExit("a scripted hunter is one strain")
    tasks = [(i, j) for i in range(len(hunters.labels)) for j in range(n // W)]
    out = {i: np.zeros(n) for i in range(len(hunters.labels))}
    for lo in range(0, len(tasks), S):
        real = tasks[lo:lo + S]
        batch = real + [real[0]] * (S - len(real))
        rows = np.stack([ids[j * W:(j + 1) * W] for _, j in batch])
        b = play(env, cfg, hunters.make([i for i, _ in batch], device), chunk, rows, device,
                 iface=hunters.iface).captures
        for k, (i, j) in enumerate(real):
            out[i][j * W:(j + 1) * W] = b[k]
    return {lab: out[i] for i, lab in enumerate(hunters.labels)}


def compare(env, cfg, hunters: Hunters, chunk: list, side_a, side_b) -> dict:
    """Two ways of playing the same worlds, `side_x(ids) -> {label: counts}`: the SD on the SD block's worlds, the
    largest required count over the hunters (§7.3), then each hunter's paired interval on that many check worlds."""
    W = len(chunk)
    nsd = REGISTERED["cuda"]["sd_worlds"] if not SMOKE else 16
    nsd = int(math.ceil(nsd / W) * W)
    names_sd = chunk * (nsd // W)
    sd_ids = ids_of("cuda_sd", nsd)
    a, b = side_a(sd_ids), side_b(sd_ids)
    need = {lab: required_worlds(b[lab] - a[lab], names_sd) for lab in hunters.labels}
    n = max(v[1] for v in need.values())
    n = int(math.ceil(n / W) * W)
    names = chunk * (n // W)
    ids = ids_of("cuda_checks", n)
    a, b = side_a(ids), side_b(ids)
    return {lab: judged(b[lab] - a[lab], names, *need[lab]) for lab in hunters.labels}


def chunk_for(setting: str, W: int) -> list:
    """The columns' settings in a chunk of W: one setting, or the training mixture (8 columns, or slot-major blocks)."""
    if setting != "mixed":
        return [setting] * W
    return list(ST.TRAINING) * (W // 8) if W <= 8 * 8 else list(PL.per_slot_layout(W // 8))


# ================================================================================================= 1. equivalence
def reference_worktree() -> dict:
    if not REF_WORKTREE.exists():
        reg.git("worktree", "add", "--detach", str(REF_WORKTREE), REF_COMMIT)
    head = reg.git("rev-parse", "HEAD", root=REF_WORKTREE)
    dirty = reg.git("status", "--porcelain", root=REF_WORKTREE)
    if head != REF_COMMIT or dirty:
        raise SystemExit(f"the reference worktree is at {head[:7]} (dirty: {bool(dirty)}), not a clean {REF_COMMIT[:7]}")
    return {"path": str(REF_WORKTREE), "head": head, "clean": True}


def mixed_against_alone(env, cfg, hunter_factory, ids, names):
    """The mixed world against each column's setting alone, at the same composition: per slot, the differing arrays."""
    mixed = play(env, cfg, hunter_factory(), names, ids)
    out, bad = {"captures_mean": float(mixed.captures.mean()), "max_index": mixed.max_index}, []
    alone_counts = np.zeros_like(mixed.captures)
    for name in dict.fromkeys(names):
        cols = [i for i, n in enumerate(names) if n == name]
        alone = play(env, cfg, hunter_factory(), [name] * len(names), ids)
        d = _same(_result_arrays(mixed, cols), _result_arrays(alone, cols))
        alone_counts[:, cols] = alone.captures[:, cols]
        if d:
            bad.append({"setting": name, "differ": d})
    out["differ"] = bad
    return out, alone_counts


def stage_equivalence(args):
    worktree = reference_worktree()  # before the start marker: a dirty or missing worktree is not a started stage
    prov = guard("equivalence")
    env = Env()
    t0 = time.perf_counter()
    doc = {"provenance_at_start": prov, "reference_commit": REF_COMMIT}
    cfg = task_config()
    tol = REGISTERED["equivalence"]["formula_tol"]
    with acct.category("measure"):
        # (a) E5-0's engine against the working tree, every setting (a smoke too: on smoke ids, a short horizon)
        doc["reference_worktree"] = worktree
        first = ids_of("cuda_checks", 64)[0]
        files = {}
        for side, root in (("old", REF_WORKTREE), ("new", ROOT)):
            cap().check()
            left = (REGISTERED["cap_hours"] - cap().spent_hours()) * 3600 - (time.perf_counter() - cap().t_start)
            extra = ["--first", str(first), "--count", "64", "--budget-seconds", str(max(left, 0.0))]
            extra += ["--ticks", str(SMOKE_TICKS)] if SMOKE else []
            f = OUT / f"reference-{side}.npz"
            acct.run_counted_child([sys.executable, str(ROOT / "scripts" / "e5_1_reference.py"), "--root", str(root),
                                    "--out", str(f), *extra], OUT / f"reference-{side}-ledger.json", cwd=str(root))
            files[side] = dict(np.load(f, allow_pickle=False))
        bad = _same(files["old"], files["new"])
        caps = {k: int(v.sum()) for k, v in files["new"].items() if k.endswith("|captures")}
        doc["old_against_new"] = {"engines": {"old": REF_COMMIT, "new": prov["git_commit"]},
                                  "worlds": {"first": int(first), "count": 64}, "arrays": len(files["new"]),
                                  "differ": bad, "identical": not bad, "captures_by_setting_and_hunter": caps,
                                  "max_life_in_traces": {k: int(v.max()) for k, v in files["new"].items()
                                                         if k.endswith("|life")}}
        print("old against new:", not bad, len(files["new"]), "arrays")

        # (b) + (c) the mixed world against each slot alone, and the GA rollout against that serial reference
        R, P = (REGISTERED["equivalence"]["shape_runs"], PL.GA["population"]) if not SMOKE else (1, 4)
        vps = PL.VALIDATION_PER_SLOT if not SMOKE else 2
        seeds = [REGISTERED["check_seed"] + i for i in range(R)]
        pops = Genome.cat([gen0(env, env.con, env.ext, s, P) for s in seeds])
        champs = Genome.cat([g for _, g in c_champions(env)])
        tiled = champs.select([i % champs.n_strains for i in range(R * P)])
        base, span = span_of("cuda_checks")
        train = np.concatenate([np.tile(EV.train_ids(s, 0, 8, base, span), (P, 1)) for s in seeds])
        train_c = np.stack([EV.train_ids(REGISTERED["check_seed"] + 100 + i, 0, 8, base, span) for i in range(R * P)])
        rows = {}
        roll = GA.TaskHRollout(env.params, prey_iface=env.iface, validation_per_slot=vps)
        tw, vw = roll.weights()
        val_ids = ids_of("cuda_checks", len(ST.TRAINING) * vps)
        for label, genome, ids, names in (
                ("training shape, generation 0 of 4 G-N2-construction runs", pops, train, list(ST.TRAINING)),
                ("training shape, the E4s-1 C champions tiled (scoring)", tiled, train_c, list(ST.TRAINING)),
                ("validation shape, 4 E4s-1 C champions", champs.select([0, 1, 2, 3][:min(4, champs.n_strains)]),
                 val_ids, list(GA.validation_layout(vps)))):
            res, alone = mixed_against_alone(env, cfg, lambda g=genome: Brain(g), ids, names)
            r = roll(cfg, env.gface, genome, ids, PL.WORLD_SEED, "cpu", chunk_worlds=genome.n_strains * ids.shape[-1])
            w = tw if len(names) == len(ST.TRAINING) else vw
            num = r.score.astype(np.int64) @ w  # exact integer numerators
            fit = (r.score @ w.astype(np.float64)) / float(w.sum())
            per_slot = np.stack([alone[:, [i for i, n in enumerate(names) if n == s]].mean(1) for s in ST.TRAINING], 1)
            ref = formula(per_slot)
            ties_exact = all(fit[a] == fit[b] for a in range(num.size) for b in range(a) if num[a] == num[b])
            res.update({"rollout_equals_serial_counts": bool(np.array_equal(r.score, alone.astype(np.float64))),
                        "weighted_against_formula_max_abs": float(np.abs(fit - ref).max()),
                        "equal_numerators_equal_fitness": bool(ties_exact),
                        "captures_mean": float(r.score.mean())})
            rows[label] = res
        doc["mixed_against_alone"] = rows
        # a short weighted evolution: every logged best fitness and checkpoint score against the formula, on the counts
        # the rollout returned
        seen = []

        def recording(*a, **k):
            out = roll(*a, **k)
            seen.append(out.score.copy())
            return out

        runs = [EV.RunSpec(i, s, 0.0) for i, s in enumerate(seeds)]
        recs = EV.evolve_batch(cfg, env.gface, env.spec, runs, generations=3, checkpoint_every=2,
                               validation_ids=val_ids, world_seed=PL.WORLD_SEED, id_base=base, id_span=span,
                               rollout_fn=recording, initial=lambda r: gen0(env, env.con, env.ext, r.run_seed, P),
                               mutation_scales=lambda r: AR.scales(env.ext, env.l1, "G-N2"), weights=(tw, vw),
                               check=cap().check)
        worst, k = 0.0, 0
        for g in range(3):
            tr = seen[k]
            k += 1
            for i, rec in enumerate(recs):
                worst = max(worst, abs(rec.log[g]["best_fitness"] - float(formula(tr[i * P:(i + 1) * P]).max())))
            if g in (0, 2):
                v = seen[k]
                k += 1
                lay = np.array(GA.validation_layout(vps))
                for i, rec in enumerate(recs):
                    ck = [c for c in rec.checkpoints if c["generation"] == g][0]
                    per_slot = np.array([v[i][lay == s].mean() for s in ST.TRAINING])
                    worst = max(worst, abs(ck["validation_mean"] - float(formula(per_slot[None])[0])))
        doc["weighted_evolution"] = {"generations": 3, "max_abs_against_formula": worst,
                                     "max_index": roll.max_index, "rollouts": roll.rollouts}

        # (d) E5-0's 68 arrays, and H1-ghost against Task N, re-run
        cap().check()
        f = OUT / "e5_0-reference-new.npz"
        acct.run_counted_child([sys.executable, str(ROOT / "scripts" / "e5_0_reference.py"), "--root", str(ROOT),
                                "--out", str(f)], OUT / "e5_0-reference-new-ledger.json", cwd=str(ROOT))
        new = dict(np.load(f, allow_pickle=False))
        old = dict(np.load(E5_0_OLD, allow_pickle=False)) if E5_0_OLD.exists() else {}
        d = _same(old, new)
        doc["e5_0_arrays"] = {"arrays": len(new), "old_file": str(E5_0_OLD.relative_to(ROOT)), "differ": d,
                              "identical": bool(old) and not d}
        doc["ghost_against_task_n"] = ghost_against_task_n_cpu(env)
    doc["seconds"] = time.perf_counter() - t0
    scoring = [r for k, r in rows.items() if "C champions" in k]
    doc["scoring_rows_captured"] = all(r["captures_mean"] > 0 for r in scoring) or SMOKE
    doc["passed"] = bool(doc["old_against_new"]["identical"] and doc["scoring_rows_captured"]
                         and all(not r["differ"] and r["rollout_equals_serial_counts"]
                                 and r["equal_numerators_equal_fitness"]
                                 and r["weighted_against_formula_max_abs"] <= tol for r in rows.values())
                         and doc["weighted_evolution"]["max_abs_against_formula"] <= tol
                         and doc["e5_0_arrays"]["identical"] and doc["ghost_against_task_n"]["identical"])
    write("equivalence.json", doc)
    print(json.dumps({k: (v if not isinstance(v, dict) else {kk: vv for kk, vv in v.items()
                                                                if kk in ("identical", "differ", "max_abs_against_formula")})
                      for k, v in doc.items() if k not in ("provenance_at_start", "mixed_against_alone")}, indent=1))
    if not doc["passed"]:
        raise SystemExit("an equivalence check failed: E5-1a stops")


def ghost_hunters(env, cn, ch, device):
    """(label, Task N brain or genome, Task H brain or genome, interface, neurons): E1's frozen S-const, the oracle and
    the pursuit, E4s-1 run 0's C, L1 on its carrier."""
    fz = env.freeze["tuned"]["S-const"]["params"]
    e4s = c_champions(env)[0][1]
    l1c = HN.l1_carrier(env.con, cn.brain)
    return [("S-const", C.scripted(env.iface, C.s_const(**fz), cn, device=device),
             C.scripted(env.iface, C.s_const(**fz), ch, device=device), env.iface, 302),
            ("oracle", C.OracleBrain(env.iface, 302, cn.world.forward_gain, cn.world.turn_gain, device=device),
             GA.PursuitBrain(env.iface, 302, ch.world.forward_gain, ch.world.turn_gain, device=device), env.iface, 302),
            ("e4s1 C run00", e4s, e4s, env.gface, 306), ("L1 carrier", l1c, l1c, env.gface, 306)]


def ghost_pair(env, cn, ch, hunter, ids, run_seed, device):
    """(Task N counts, H1-ghost result) for one hunter on the same worlds."""
    from wormwars.e5.play import play as hplay
    from wormwars.e5.prey import PreyBrain
    from wormwars.evo.rollout import rollout, rollout_brain
    label, tn, th, fc, nn = hunter
    cap().check()
    if isinstance(tn, Genome):
        rn = rollout(cn, fc, moved(tn, device), ids, run_seed, device)
    else:
        rn = rollout_brain(cn, fc, tn, ids, run_seed, device)
    hb = Brain(moved(th, device)) if isinstance(th, Genome) else th
    prey = PreyBrain(env.iface, nn, ch.world.forward_gain, ch.world.turn_gain, "stationary", device=device)
    rh = hplay(ch, fc, hb, prey, ids, run_seed, rule="ghost", device=device)
    check_ledger(rh.ledger_rel_error, f"ghost {label} on {device}")
    return rn, rh


def ghost_configs():
    from wormwars.e5.hunt import e1_task_n
    cn, ch = e1_task_n(), hunt_config()
    ch.world.check_ledger_every_tick = True
    if SMOKE:
        cn.world.max_ticks = ch.world.max_ticks = SMOKE_TICKS
    return cn, ch


def ghost_against_task_n_cpu(env) -> dict:
    """E5-0's check (scripts/e5_0.py, equivalence §2) on its 512 equivalence worlds, under the real scent, bit for bit:
    the same counts, capture ticks and paths."""
    first, n = REGISTERED["cuda"]["ghost_ids"]
    eid = np.arange(first, first + (n if not SMOKE else 16))
    cn, ch = ghost_configs()
    rows, bad = {}, []
    for h in ghost_hunters(env, cn, ch, "cpu"):
        rn, rh = ghost_pair(env, cn, ch, h, eid, 1_500_001, "cpu")
        same = {"count": bool(np.array_equal(rn.score[0].astype(np.int64), rh.captures[0])),
                "capture_tick": bool(np.array_equal(rn.events["reach_tick"][0], rh.events["capture_tick"][0])),
                "path": bool(np.array_equal(rn.events["path_length"][0], rh.events["hunter_path"][0]))}
        rows[h[0]] = {**same, "mean_task_n": float(rn.score.mean()), "mean_ghost": float(rh.captures.mean())}
        if not all(same.values()):
            bad.append(h[0])
    return {"worlds": int(len(eid)), "run_seed": 1_500_001, "rows": rows, "differ": bad, "identical": not bad}


# ================================================================================================= 2. graphs
def stage_graphs(args):
    prov = guard("graphs")
    env = Env()
    t0 = time.perf_counter()
    raw = json.loads((GR.R03 / "graphs_manifest.json").read_text(encoding="utf-8"))
    local = ROOT / "runs" / "exp03r" / "graphs"
    names = list(PL.SH_ROUTE + PL.SH_ROUTE_PILOT) if not SMOKE else [PL.SH_ROUTE[0], PL.SH_ROUTE_PILOT[0]]
    rows, bad = {}, []
    sup = json.loads((GR.R03 / "supplement.json").read_text(encoding="utf-8"))["per_graph"]
    with acct.category("measure"):
        for name in names:
            cap().check()
            g, info = GR.sh_route(env.con, name)  # stops on a content mismatch
            with tempfile.TemporaryDirectory() as tmp:
                p = Path(tmp) / f"{name}.npz"
                np.savez_compressed(p, chem=g.chem, gap=g.gap)
                info["raw_sha256_rebuilt"] = hashlib.sha256(p.read_bytes()).hexdigest()
            info["raw_matches_manifest"] = info["raw_sha256_rebuilt"] == raw.get(name)
            lp = local / f"{name}.npz"
            if lp.exists():
                z = np.load(lp, allow_pickle=False)
                info["local_file_arrays_equal"] = bool(np.array_equal(z["chem"], g.chem)
                                                       and np.array_equal(z["gap"], g.gap))
                info["local_file_raw_matches_manifest"] = hashlib.sha256(lp.read_bytes()).hexdigest() == raw.get(name)
            ext, spec, _ = GR.grafted(g, env.l1)  # stops if L1's edges or noses are missing
            info["grafted"] = AR.identity("G-SHr", 0, 0, name, ext)
            row = sup.get(name, {})
            info["03r"] = {k: row.get(k) for k in ("P4_turn", "P4_forward", "forward_gain", "turn_gain")}
            rows[name] = info
            if info.get("local_file_arrays_equal") is False:
                bad.append(name)
        n2 = AR.identity("G-N2", 0, 0, "N2", env.ext)
        hw, hg = AR.host_masks(env.ext)
        _, _, me, _, mn = EA._masks(env.ext)
        designed = G.seeded_genome(env.ext, env.l1, env.cfg.brain, n_strains=1)
        p_rows = {}
        for k, perm in enumerate(PL.P_PERMUTATION_SEEDS):
            seed = PL.run_seed("P", 0, k)
            p = AR.initial("P", seed, env.con, env.ext, env.l1, env.cfg.brain, 4, perm_seed=perm)
            n = AR.initial("G-N2", seed, env.con, env.ext, env.l1, env.cfg.brain, 4)
            checks = {
                "same_edges_as_g_n2": bool(p.spec.same_as(n.spec)),
                "module_equals_l1": bool(torch.equal(p.w[:, me], designed.w[:, me].expand_as(p.w[:, me]))
                                         and torch.equal(p.tau[:, mn], designed.tau[:, mn].expand_as(p.tau[:, mn]))
                                         and torch.equal(p.bias[:, mn], designed.bias[:, mn].expand_as(p.bias[:, mn]))),
                "host_w_magnitudes_differ": not bool(torch.equal(p.w[:, hw].abs(), n.w[:, hw].abs())),
                "host_w_magnitudes_permuted": bool(torch.equal(p.w[:, hw].abs().sort(1).values,
                                                               n.w[:, hw].abs().sort(1).values)),
                "host_g_differ": not bool(torch.equal(p.g[:, hg], n.g[:, hg])),
                "host_g_permuted": bool(torch.equal(p.g[:, hg].sort(1).values, n.g[:, hg].sort(1).values)),
                "standard_configuration": p.cfg == env.cfg.brain}
            p_rows[f"N2perm{perm}"] = {"permutation_seed": perm, "configuration": {
                "init_chem_magnitude": "permuted", "init_gap_magnitude": "permuted", "init_permutation_seed": perm},
                "run0_seed": seed, "host_magnitude_sha256_run0_strain0": AR.host_magnitude_sha256(p, env.ext),
                "g_n2_same_seed_sha256": AR.host_magnitude_sha256(n, env.ext), "checks": checks,
                "03r": {kk: sup.get(f"N2perm{perm}", {}).get(kk) for kk in ("forward_gain", "turn_gain")}}
            if not all(checks.values()):
                bad.append(f"N2perm{perm}")
    doc = {"provenance_at_start": prov, "graphs": rows, "n2": n2, "p": p_rows, "failed": bad,
           "raw_matches": sum(bool(r["raw_matches_manifest"]) for r in rows.values()),
           "note": "content (arrays) must match 03r's content manifest (a stop); raw bytes are reported, D106",
           "seconds": time.perf_counter() - t0}
    doc["passed"] = not bad
    write("graphs.json", doc)
    print(f"{len(rows)} graphs rebuilt and checked; raw bytes equal for {doc['raw_matches']}; P checks:",
          {k: all(v["checks"].values()) for k, v in p_rows.items()})
    if bad:
        raise SystemExit(f"graph or P checks failed: {bad}")


# ================================================================================================= 3. cuda
def score_hunters(env) -> list[tuple[Hunters, dict]]:
    """(hunters, {setting: (strains per play, worlds per strain)}): E1's frozen S-const and the pursuit (one strain on
    the worm's interface, as E5-0 played them), L1 on its carrier, and E4s-1 runs 0 to 3's C (the mixed world at the
    training shape, 128 x 8, each genome tiled)."""
    cfg = env.cfg
    fz = env.freeze["tuned"]["S-const"]["params"]
    single = {s: (1, 512) for s in REGISTERED["cuda"]["settings"] + ["mixed"]}
    if SMOKE:
        single = {s: (1, 16) for s in single}
    s_const = Hunters(["S-const"], lambda idx, d: C.scripted(env.iface, C.s_const(**fz), cfg, device=d), env.iface,
                      scripted=True)
    pursuit = Hunters(["pursuit"], lambda idx, d: GA.PursuitBrain(env.iface, 302, cfg.world.forward_gain,
                                                                  cfg.world.turn_gain, device=d), env.iface,
                      scripted=True)
    l1c = Hunters.of([("L1 carrier", HN.l1_carrier(env.con, cfg.brain))], env.gface)
    four = Hunters.of(c_champions(env)[:4], env.gface)
    genome_shapes = {**{s: (4, 512) for s in REGISTERED["cuda"]["settings"]}, "mixed": (128, 8)}
    if SMOKE:
        genome_shapes = {s: (2, 16) if s != "mixed" else (4, 8) for s in genome_shapes}
    return [(s_const, single), (pursuit, single), (l1c, single), (four, genome_shapes)]


def trajectories(env, cfg, hunter, prey_name, ids, device, ticks, hunter_attack=1.0) -> np.ndarray:
    """Per-tick positions of both bodies, [ticks, worlds, 2, 2], then the world's checks."""
    prey = MX.prey(env.iface, cfg, [prey_name] * len(ids), env.params, n=hunter.n, device=device)
    so = torch.zeros(len(ids), 2, dtype=torch.long, device=device)
    cap().check()
    w = HuntWorld(cfg, env.iface, [hunter, prey], so, run_seed=PL.WORLD_SEED, world_ids=ids, device=device,
                  rule=ST.BY_NAME[prey_name]["rule"], prey_energy=env.params["e_prey"],
                  pinned=ST.BY_NAME[prey_name]["pinned"], hunter_attack=hunter_attack)
    pos = []
    for _ in range(ticks):
        w.tick()
        pos.append(w.pos[:, :, 0].clone().cpu().numpy())
    finish_world(w, f"trajectories {prey_name} on {device}")
    return np.stack(pos)


def respawn_distances(env, cfg, device, names) -> dict:
    """Every new life's distance from the hunter's head at its respawn, on the device, under the pursuit; a check
    without a respawn fails (it would show nothing)."""
    D = cfg.world.target_separation - cfg.world.target_radius
    out = {}
    for name in names:
        n = REGISTERED["cuda"]["respawn_worlds"] if not SMOKE else 8
        ids = ids_of("cuda_checks", n)
        hunter = GA.PursuitBrain(env.iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, device=device)
        prey = MX.prey(env.iface, cfg, [name] * n, env.params, device=device)
        so = torch.zeros(n, 2, dtype=torch.long, device=device)
        cap().check()
        w = HuntWorld(cfg, env.iface, [hunter, prey], so, run_seed=PL.WORLD_SEED, world_ids=ids, device=device,
                      rule="bite", prey_energy=env.params["e_prey"], pinned=ST.BY_NAME[name]["pinned"])
        life = w.life.clone()
        dmin, k = float("inf"), 0
        while not w.done():
            w.tick()
            new = w.life != life
            if bool(new.any()):
                dist = (w.pos[new, PREY, 0] - w.pos[new, HUNTER, 0]).norm(dim=-1)
                dmin, k = min(dmin, float(dist.min())), k + int(new.sum())
                life = w.life.clone()
        finish_world(w, f"respawns {name} on {device}")
        out[name] = {"respawns": k, "min_distance": dmin if k else None, "required": D,
                     "passed": bool(k > 0 and dmin >= D - 1e-5) or (SMOKE and k == 0)}
    return out


def _as64(g: Genome) -> Genome:
    return g.with_params(**{k: v.double() for k, v in g.params().items() if v is not None})


def state_level(env, device, perturb=None, shapes=None, families=None) -> dict:
    """Open loop under one imposed input history, at the training (128 x 8), validation (4 x 256) and suite (8 x 512)
    shapes, every genome at every shape (in groups of the shape's strains). Inputs: uniform on [0, 1] times each
    sensor's gain at every sensor neuron, drawn on the CPU. A non-finite state fails.

    Amendment 1 (§14.3), judged per strain (each genome's largest difference over ticks, rows and neurons):
    - one step, resynchronised: every tick CUDA steps from the CPU's float32 state, and its result must lie within
      1e-4 of the CPU's step (the registered tolerance; local error is not amplified);
    - free running: CUDA float32 may be at most 1.5 times as far from a higher-precision reference (the same genome on
      the CPU in float64) as CPU float32 is, plus 1e-4;
    - generation-0 genomes keep the original rule: CPU against CUDA, free running, within 1e-4.
    `perturb(genome) -> genome`, if given, alters the CUDA copy only; `shapes` and `families` restrict the run (both for
    the sabotage, `scripts/e5_1a_state_sabotage.py`)."""
    c = REGISTERED["cuda"]
    ticks = c["state_ticks"] if not SMOKE else 10
    gens = {"E4s-1 C": (Genome.cat([g for _, g in c_champions(env)]), [lab for lab, _ in c_champions(env)])}
    for j, name in enumerate(PL.SH_ROUTE_PILOT if not SMOKE else PL.SH_ROUTE_PILOT[:1]):
        g, _ = GR.sh_route(env.con, name)
        ext = GR.grafted(g, env.l1)[0]
        gens[f"generation 0 on {name}"] = (gen0(env, g, ext, PL.run_seed("pilot_null", 0, j), 4),
                                           [f"{name} #{i}" for i in range(4)])
    if shapes is None:
        shapes = {"training": (128, 8), "validation": (4, 256), "suite": (8, 512)} if not SMOKE else {"small": (2, 4)}
    if families is not None:
        gens = {k: v for k, v in gens.items() if k in families}
    idx = torch.as_tensor(np.asarray(env.gface.sensor_neuron), dtype=torch.long)
    gain = torch.as_tensor(np.asarray(env.gface.sensor_gain), dtype=torch.float32)
    rows, finite, failed = {}, True, []
    per = lambda t: t.abs().nan_to_num(nan=float("inf")).amax(dim=(1, 2)).double().cpu()  # noqa: E731  [S]
    for family, (gen, labels) in gens.items():
        champion = family == "E4s-1 C"
        for shape, (S, B) in shapes.items():
            for lo in range(0, gen.n_strains, S):  # every genome, S at a time (the last group padded)
                cap().check()
                pick = [(lo + i) % gen.n_strains for i in range(S)]
                g = gen.select(pick)
                gd = moved(g, device) if perturb is None else perturb(moved(g, device))
                rng = torch.Generator().manual_seed(7)
                b32, b64, bg = Brain(g), Brain(_as64(g)), Brain(gd)
                v32, v64, vg = b32.initial_state(B), b64.initial_state(B).double(), bg.initial_state(B)
                m = {k: torch.zeros(S, dtype=torch.float64) for k in ("one step", "cpu32 - cuda32", "cpu32 - cpu64",
                                                                        "cuda32 - cpu64")}
                for _ in range(ticks):
                    cur = torch.zeros(S, B, g.spec.n)
                    cur[:, :, idx] = torch.rand(S, B, len(idx), generator=rng) * gain
                    cd = cur.to(device)
                    one = bg.step(v32.to(device), cd)  # CUDA from the CPU's state
                    v32n, v64, vg = b32.step(v32, cur), b64.step(v64, cur.double()), bg.step(vg, cd)
                    if not all(bool(torch.isfinite(t).all()) for t in (v32n, v64, vg, one)):
                        finite = False
                    gc = vg.cpu().double()
                    m["one step"] = torch.maximum(m["one step"], per(one.cpu() - v32n))
                    m["cpu32 - cuda32"] = torch.maximum(m["cpu32 - cuda32"], per(v32n.double() - gc))
                    m["cpu32 - cpu64"] = torch.maximum(m["cpu32 - cpu64"], per(v32n.double() - v64))
                    m["cuda32 - cpu64"] = torch.maximum(m["cuda32 - cpu64"], per(gc - v64))
                    v32 = v32n
                seen = set()
                for k, gi in enumerate(pick):
                    if gi in seen:  # the padding repeats a genome: its first strain is the record
                        continue
                    seen.add(gi)
                    r = {key: float(v[k]) for key, v in m.items()}
                    r["bound"] = c["state_factor"] * r["cpu32 - cpu64"] + c["state_tol"]
                    checks = {"one step": r["one step"] <= c["state_tol"]}
                    if champion:
                        checks["free running, against float64"] = r["cuda32 - cpu64"] <= r["bound"]
                    else:
                        checks["free running, CPU against CUDA"] = r["cpu32 - cuda32"] <= c["state_tol"]
                    r["checks"], r["passed"] = checks, all(checks.values())
                    key = f"{labels[gi]} | {shape}"
                    rows[key] = r
                    if not r["passed"]:
                        failed.append(key)
    return {"strains": rows, "finite": finite, "failed": failed, "factor": c["state_factor"],
            "floor": c["state_tol"], "worst_cpu_cuda": max(v["cpu32 - cuda32"] for v in rows.values()),
            "worst_one_step": max(v["one step"] for v in rows.values()), "passed": bool(finite and not failed)}


def stage_cuda(args):
    prov = guard("cuda")
    dev = args.device
    if not (dev.startswith("cuda") and torch.cuda.is_available()):
        raise SystemExit("the CUDA stage needs --device cuda")
    if not SMOKE:
        reg.require_formal(dev, prov)
    env = Env()
    t0 = time.perf_counter()
    cfg = task_config()
    c = REGISTERED["cuda"]
    doc = {"provenance_at_start": prov, "registered": c}
    with acct.category("measure"):
        score = {}
        for hunters, shapes in score_hunters(env):
            for setting, (S, W) in shapes.items():
                chunk = chunk_for(setting, W)
                rows = compare(env, cfg, hunters, chunk,
                               lambda ids, h=hunters, S=S, ch=chunk: counts_by_task(env, cfg, h, S, ch, ids, "cpu"),
                               lambda ids, h=hunters, S=S, ch=chunk: counts_by_task(env, cfg, h, S, ch, ids, dev))
                for lab, r in rows.items():
                    score[f"{lab} | {setting} | {S} x {W}"] = r
                    print(lab, setting, round(r["estimate"], 3), [round(x, 3) for x in r["interval"]], r["passed"])
        doc["score_level"] = score
        # prey paths with a motionless hunter, its attack disabled (the engine has no ghost mode for a hunter; its body
        # stays, so a prey that meets it is steered by it, alike on both devices); the pursuit's first ticks
        paths = {}
        still = lambda d: C.scripted(env.iface, C.ConstantMotion(0.0, 0.0), cfg, device=d)  # noqa: E731
        for name in ("H2-0.5", "H2b-walk-0.5", "H2b-wall-0.5"):
            n = c["path_worlds"] if not SMOKE else 8
            ids = ids_of("cuda_checks", n)
            ta = trajectories(env, cfg, still("cpu"), name, ids, "cpu", cfg.world.max_ticks, hunter_attack=0.0)
            tb = trajectories(env, cfg, still(dev), name, ids, dev, cfg.world.max_ticks, hunter_attack=0.0)
            dev_max = np.abs(ta[:, :, PREY] - tb[:, :, PREY]).max(axis=(0, 2))
            share = float((dev_max <= c["path_tol"]).mean())
            paths[f"prey {name}"] = {"worlds": n, "share_agreeing": share, "max_abs": float(dev_max.max()),
                                     "passed": share >= c["path_share"]}
        purs = lambda d: GA.PursuitBrain(env.iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, device=d)  # noqa: E731
        for name in ("H1-bite", "H2-0.5"):
            n = c["trace_worlds"] if not SMOKE else 8
            ids = ids_of("cuda_checks", n)
            ta = trajectories(env, cfg, purs("cpu"), name, ids, "cpu", c["trace_ticks"])
            tb = trajectories(env, cfg, purs(dev), name, ids, dev, c["trace_ticks"])
            dev_max = np.abs(ta - tb).max(axis=(0, 2, 3))
            share = float((dev_max <= c["path_tol"]).mean())
            paths[f"pursuit trace {name}"] = {"worlds": n, "ticks": c["trace_ticks"], "share_agreeing": share,
                                              "max_abs": float(dev_max.max()), "passed": share >= c["path_share"]}
        doc["paths"] = paths
        # H1-ghost against Task N on CUDA: sized and judged like the score checks (the bitwise share is reported)
        cn, ch = ghost_configs()
        ghost = {}
        for h in ghost_hunters(env, cn, ch, dev):
            def side(ids, which, h=h):  # in chunks of 512 worlds
                parts = []
                for a in range(0, ids.size, 512):
                    rn, rh = ghost_pair(env, cn, ch, h, ids[a:a + 512], PL.WORLD_SEED, dev)
                    parts.append((rn.score[0] if which == "n" else rh.captures[0]).astype(np.float64))
                return {h[0]: np.concatenate(parts)}
            ghost.update(compare(env, cfg, Hunters([h[0]], None, None), ["H1-ghost"],
                                 lambda ids, s=side: s(ids, "n"), lambda ids, s=side: s(ids, "h")))
        doc["ghost_against_task_n"] = ghost
        # attack disabled
        n = c["attack_worlds"] if not SMOKE else 8
        att = {}
        for name in ("H1-bite", "H2-0.5"):
            r = play(env, cfg, purs(dev), [name] * n, ids_of("cuda_checks", n), dev, iface=env.iface,
                     hunter_attack=0.0)
            att[name] = {"captures": int(r.captures.sum()), "damage": float(r.events["damage"].sum()),
                         "passed": bool(r.captures.sum() == 0 and r.events["damage"].sum() == 0)}
        doc["attack_disabled"] = att
        doc["respawns"] = respawn_distances(env, cfg, dev, ["H1-bite", "H2-0.5", "H2b-walk-0.5"])
        doc["state_level"] = state_level(env, dev)
    doc["seconds"] = time.perf_counter() - t0
    fails = [k for k, v in doc["score_level"].items() if not v["passed"]]
    fails += [k for k, v in doc["paths"].items() if not v["passed"]]
    fails += [f"ghost {k}" for k, v in doc["ghost_against_task_n"].items() if not v["passed"]]
    fails += [f"attack {k}" for k, v in doc["attack_disabled"].items() if not v["passed"]]
    fails += [f"respawn {k}" for k, v in doc["respawns"].items() if not v["passed"]]
    fails += [] if doc["state_level"]["passed"] else ["state level"]
    doc["failed"], doc["passed"] = fails, not fails
    doc["imprecise"] = [k for k, v in {**doc["score_level"], **doc["ghost_against_task_n"]}.items()
                        if not v["precision_reached"]]
    doc["ledger"] = f"every play checked every tick at {REGISTERED['ledger_tol']} (a failure stops the stage)"
    write("cuda.json", doc)
    print("CUDA checks:", "passed" if not fails else f"FAILED {fails}", "| imprecise:", doc["imprecise"])
    if fails:
        raise SystemExit("a CUDA check failed: E5-1a stops; diagnosis is a dated, reviewed amendment")


# ================================================================================================= 4. bench
def timed(fn):
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    t = time.perf_counter()
    out = fn()
    if torch.cuda.is_available():
        torch.cuda.synchronize()
    return out, time.perf_counter() - t


def bench_batch(env, cfg, graph, ext, spec, iface, dev, seeds, initial) -> dict:
    """evolve_batch at the formal shape for a few generations; seconds per generation and per checkpoint."""
    b = REGISTERED["bench"]
    G_, every = (b["generations"], b["checkpoint_every"]) if not SMOKE else (3, 2)
    base, span = span_of("cuda_checks")
    roll = GA.TaskHRollout(env.params, prey_iface=env.iface,
                           validation_per_slot=PL.VALIDATION_PER_SLOT if not SMOKE else 2)
    val = ids_of("cuda_sd", len(ST.TRAINING) * (PL.VALIDATION_PER_SLOT if not SMOKE else 2))
    runs = [EV.RunSpec(i, s, 0.0) for i, s in enumerate(seeds)]
    recs, total = timed(lambda: EV.evolve_batch(
        cfg, iface, spec, runs, generations=G_, checkpoint_every=every, validation_ids=val, world_seed=PL.WORLD_SEED,
        id_base=base, id_span=span, device=dev, rollout_fn=roll, weights=roll.weights(), check=cap().check,
        initial=initial, mutation_scales=lambda r: AR.scales(ext, env.l1, "G-N2")))
    secs = [x["batch_seconds"] for x in recs[0].log]
    ck = [g for g in range(G_) if g % every == 0 or g == G_ - 1]
    plain = [s for g, s in enumerate(secs) if g not in ck]
    with_ck = [s for g, s in enumerate(secs) if g in ck and g > 0]
    per_gen = float(np.mean(plain)) if plain else float(np.mean(secs))
    per_ck = max(0.0, float(np.mean(with_ck)) - per_gen) if with_ck else 0.0
    n_ck = len([g for g in range(PL.GENERATIONS) if g % PL.CHECKPOINT_EVERY == 0 or g == PL.GENERATIONS - 1])
    return {"graph": graph.label, "seconds_per_generation": per_gen, "seconds_per_checkpoint": per_ck,
            "generation_seconds": secs, "max_index": roll.max_index, "total_seconds": total,
            "mean_fitness_by_generation": [float(np.mean([r.log[g]["mean_fitness"] for r in recs])) for g in range(G_)],
            "hours_per_batch": (PL.GENERATIONS * per_gen + n_ck * per_ck) / 3600, "checkpoints": n_ck}


def projection(h: dict, rate: float, reserve: float) -> dict:
    """GPU-hours by part, and after each cut in §7.4's order, recomputed from what each cut removes."""
    ev = lambda runs: runs * sum(EVAL_PER_RUN.values())  # noqa: E731
    probes_half = EVAL_PER_RUN["probes"] / 2

    def total(b=True, p=True, probes_full=True, graphs=20):
        runs = {**RUNS, "G-SHr": 4 * graphs, "B": RUNS["B"] if b else 0, "P": RUNS["P"] if p else 0}
        train = {"G-N2": 8 * h["n2"], "G-SHr": graphs * h["null"], "A0r + A0": 4 * h["n2"],
                 "P": 3 * h["n2"] if p else 0.0, "B": 4 * h["b"] if b else 0.0}
        episodes = sum(ev(r) for r in runs.values()) + sum(EVAL_FIXED.values())
        episodes += O0_PER_TEST_RUN * (runs["G-N2"] + runs["G-SHr"])
        if not b:
            episodes -= EVAL_FIXED["B's Task N readings"]
        if not probes_full:
            episodes -= sum(runs.values()) * probes_half
        evaluation = episodes / rate / 3600
        sub = sum(train.values()) + evaluation
        return {"training": train, "evaluation_episodes": int(episodes), "evaluation": evaluation,
                "rerun_reserve": reserve * sub, "total": sub * (1 + reserve)}

    cuts = {"none": total(), "(1) B moves to a later stage": total(b=False),
            "(2) P is dropped": total(b=False, p=False),
            "(3) the probes shrink to H1-bite and route 0.5": total(b=False, p=False, probes_full=False),
            "(4) 16 SH-route graphs": total(b=False, p=False, probes_full=False, graphs=16)}
    return cuts


def stage_bench(args):
    prov = guard("bench")
    dev = args.device
    if not SMOKE:
        reg.require_formal(dev, prov)
    env = Env()
    t0 = time.perf_counter()
    cfg = task_config(ledger_every_tick=False)  # the formal runs' setting: the ledger checked on its final residual
    b = REGISTERED["bench"]
    R = PL.RUNS_PER_BATCH if not SMOKE else 1
    P = cfg.evo.population
    seeds = [REGISTERED["check_seed"] + 10 + i for i in range(R)]
    champs = c_champions(env)
    doc = {"provenance_at_start": prov, "registered": b}
    with acct.category("measure"):
        doc["n2_batch"] = bench_batch(env, cfg, env.con, env.ext, env.spec, env.gface, dev, seeds,
                                      lambda r: gen0(env, env.con, env.ext, r.run_seed, P))
        # a scoring batch: B's construction (32 copies of a C champion per run), whose captures exercise respawns
        doc["b_batch"] = bench_batch(env, cfg, env.con, env.ext, env.spec, env.gface, dev, seeds,
                                     lambda r: AR.initial("B", r.run_seed, env.con, env.ext, env.l1, cfg.brain, P,
                                                          champion=champs[r.run % len(champs)][1]))
        g, _ = GR.sh_route(env.con, PL.SH_ROUTE_PILOT[2])  # a pilot graph that the pilot does not evolve
        ext, spec, gi = GR.grafted(g, env.l1)
        doc["null_batch"] = bench_batch(env, cfg, g, ext, spec, gi, dev, seeds,
                                        lambda r: gen0(env, g, ext, r.run_seed, P))
        # evaluation: the suite chunk, 8 strains x 512 worlds of one setting, on scoring genomes
        eight = Genome.cat([gg for _, gg in champs][:8])
        n = PL.SUITE_WORLDS if not SMOKE else 16
        ev = {}
        for name in b["suite_settings"]:
            ids = ids_of("cuda_checks", n)
            _, s = timed(lambda: play(env, cfg, Brain(moved(eight, dev)), [name] * n, ids, dev))
            ev[name] = {"episodes": eight.n_strains * n, "seconds": s, "per_second": eight.n_strains * n / s}
        rate = float(np.mean([v["per_second"] for v in ev.values()]))
        # one strain x 512 (the composition check's reference) and 16 strains x 256 (sensitivity's chunks)
        _, s1 = timed(lambda: play(env, cfg, Brain(moved(eight.select([0]), dev)), ["H2-0.5"] * n,
                                   ids_of("cuda_checks", n), dev))
        doc["suite_chunk"] = {"settings": ev, "episodes_per_second": rate, "one_strain_per_second": n / s1}
        # Task H against Task N at the training shape (Task H's overhead, f)
        pops = Genome.cat([gen0(env, env.con, env.ext, s, P) for s in seeds])
        base, span = span_of("cuda_checks")
        rows = np.concatenate([np.tile(EV.train_ids(s, 0, 8, base, span), (P, 1)) for s in seeds])
        _, th = timed(lambda: play(env, cfg, Brain(moved(pops, dev)), ST.TRAINING, rows, dev))
        from wormwars.e5.hunt import e1_task_n
        from wormwars.evo.rollout import rollout
        cn = e1_task_n()
        cn.world.max_ticks = cfg.world.max_ticks
        _, tn = timed(lambda: rollout(cn, env.gface, moved(pops, dev), rows, 1_500_001, dev, chunk_worlds=rows.size))
        doc["task_h_overhead"] = {"task_h_seconds": th, "task_n_seconds": tn, "f": th / tn}
    # the projection (§8), GPU-hours: the test arms between generation-0 and scoring batches
    lo = {"n2": doc["n2_batch"]["hours_per_batch"], "null": doc["null_batch"]["hours_per_batch"],
          "b": doc["b_batch"]["hours_per_batch"]}
    hi = {"n2": max(lo["n2"], lo["b"]), "null": max(lo["null"], lo["b"] * lo["null"] / max(lo["n2"], 1e-9)),
          "b": lo["b"]}
    r = b["rerun_reserve"]
    proj = {"low (generation-0 rates)": projection(lo, rate, r), "high (scoring rates)": projection(hi, rate, r)}
    cmax = REGISTERED["cuda"]["max_worlds"]
    one = doc["suite_chunk"]["one_strain_per_second"]
    remainder = {  # E5-1a after the cap, at its largest sizes
        "signal": 5 * (32 * 8 + 2 * 256) / rate / 3600,
        "null pilot (2 batches x 100 generations)": 2 * hi["null"] * 100 / PL.GENERATIONS,
        "composition (24 genomes, 6 shapes, 512 + 8 192 worlds, batch and one-strain reference)":
            24 * 6 * (512 + cmax) * (1 / rate + 1 / one) / 3600,
        "sensitivity (24 parents x 65 x 256)": 24 * 65 * 256 / rate / 3600,
        "composition's CPU sides (8 null champions x 6 checks x (512 + 8 192), at E5-0's 0.0165 s per episode)":
            8 * 6 * (512 + cmax) * 0.0165 / 3600}
    spent = cap().spent_hours() + (time.perf_counter() - cap().t_start) / 3600
    doc["projection_gpu_hours"] = {"formal": proj, "e5_1a_remainder_upper": remainder,
                                   "e5_1a_spent_so_far": spent,
                                   "e5_1a_fits_its_cap": bool(spent + sum(remainder.values())
                                                              <= REGISTERED["cap_hours"]),
                                   "note": "the owner's cap covers the formal run (training, evaluation, the 15% "
                                           "rerun reserve); E5-1a runs under its own 6-hour cap"}
    doc["capture_rates"] = {"note": "mean weighted fitness per generation of each benched batch; E5-0's pursuit "
                                    "reference is in experiments/E5-hunter/E5-0/evaluation.json",
                            **{k: doc[k]["mean_fitness_by_generation"] for k in ("n2_batch", "b_batch", "null_batch")}}
    doc["seconds"] = time.perf_counter() - t0
    doc["complete"] = True
    doc["next"] = "the owner sets the cap (python scripts/e5_1a.py cap --hours H --note ...) before any later stage"
    write("bench.json", doc)
    print(json.dumps({"h/batch (N2 gen-0, B scoring, null gen-0)": [round(lo[k], 3) for k in ("n2", "b", "null")],
                      "eval eps/s": round(rate, 1), "f": round(doc["task_h_overhead"]["f"], 2),
                      "total with reserve, by cut (low, high)": {k: [round(proj[x][k]["total"], 1) for x in proj]
                                                                for k in proj["low (generation-0 rates)"]},
                      "E5-1a remainder (upper)": round(sum(remainder.values()), 2)}, indent=1))


def stage_cap(args):
    hours = args.hours
    if hours is None or not math.isfinite(hours) or hours <= 0 or not args.note:
        raise SystemExit("cap needs a finite positive --hours and --note (the owner's words)")
    if (EXP / "cap.json").exists():
        raise SystemExit("cap.json exists: the cap is set once")
    bench = read("bench.json")
    if bench.get("complete") is not True:
        raise SystemExit("the bench is not complete")
    high = bench["projection_gpu_hours"]["formal"]["high (scoring rates)"]
    level = next((k for k, v in high.items() if v["total"] <= hours), None)
    write("cap.json", {"cap_gpu_hours": float(hours), "owner": args.note, "cut_level": level, "fits": level is not None,
                       "judged_on": "the high projection (scoring rates)",
                       "bench_sha256": reg.file_sha256(EXP / "bench.json"),
                       "set_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                       "provenance": reg.provenance(GUARDED)})
    print("cap", hours, "->", level or "does not fit even with every cut: E5-1 comes back to the owner")


# ================================================================================================= 5. signal
def signal_for(env, cfg, graph, ext, gi, gi_mean, seeds, dev, block="pilot_training") -> dict:
    """Each population's training winner on its generation-0 batch (preselected), then its module-only `mean`
    contrast on the selection-signal worlds."""
    P = cfg.evo.population
    pops = [gen0(env, graph, ext, s, P) for s in seeds]
    base, span = span_of(block)
    rows = np.concatenate([np.tile(EV.train_ids(s, 0, 8, base, span), (P, 1)) for s in seeds])
    allp = Genome.cat(pops)
    r = play(env, cfg, Brain(moved(allp, dev)), ST.TRAINING, rows, dev, iface=gi)
    fit = ST.weighted_fitness(r.captures)
    out, winners = {}, []
    names = list(PL.per_slot_layout((PL.BLOCKS["selection_signal"][1] // 8) if not SMOKE else 2))
    sig_ids = ids_of("selection_signal", len(names))
    for i, s in enumerate(seeds):
        f = fit[i * P:(i + 1) * P]
        w = int(np.argmax(f))
        winners.append(pops[i].select([w]))
        out[str(s)] = {"winner": w, "winner_fitness": float(f[w]), "all_equal": bool(np.all(f == f[0])),
                       "fitness_mean": float(f.mean()), "winner_sha256": genome_hash(pops[i], w)}
    wg = Genome.cat(winners)
    real = play(env, cfg, Brain(moved(wg, dev)), names, sig_ids, dev, iface=gi).captures.astype(np.float64)
    mean = play(env, cfg, Brain(moved(wg, dev)), names, sig_ids, dev, iface=gi_mean).captures.astype(np.float64)
    for i, s in enumerate(seeds):
        est, (lo, hi) = stratified(real[i] - mean[i], names)
        out[str(s)].update({"real": float(weighted_by_slot(real[i:i + 1], names)[0]),
                            "mean_probe": float(weighted_by_slot(mean[i:i + 1], names)[0]),
                            "contrast": est, "interval": [lo, hi], "above_zero": bool(lo > 0)})
    return {"populations": out, "winners": wg}


def stage_signal(args):
    prov = guard("signal")
    dev = args.device
    if not SMOKE:
        reg.require_formal(dev, prov)
    env = Env()
    cfg = task_config()
    t0 = time.perf_counter()
    seeds = [PL.run_seed("pilot_n2", i) for i in range(4 if not SMOKE else 2)]
    with acct.category("measure"):
        res = signal_for(env, cfg, env.con, env.ext, env.gface, env.gface_mean, seeds, dev)
    pops = res["populations"]
    above = sum(v["above_zero"] for v in pops.values())
    flat = [k for k, v in pops.items() if v["all_equal"]]
    stop = above < REGISTERED["signal"]["min_populations"] or bool(flat)
    save_population(OUT / "genomes" / "signal-winners.npz", res["winners"], cfg=cfg, stage="signal")
    doc = {"provenance_at_start": prov, "populations": pops, "above_zero": above, "no_variation": flat,
           "rule": "stop if fewer than 3 of the 4 intervals lie above 0, or any population has no selectable variation",
           "stop": bool(stop), "passed": bool(not stop or SMOKE),  # a smoke exercises the later stages, never reads
           "seconds": time.perf_counter() - t0}
    if stop:
        doc["finding"] = "no scent-dependent signal was detected"
    write("signal.json", doc)
    print({k: (round(v["contrast"], 3), [round(x, 3) for x in v["interval"]]) for k, v in pops.items()},
          "STOP" if stop else "passed")
    if stop and not SMOKE:
        raise SystemExit("the selection-signal stop applies: E5-1 stops for redesign")


# ================================================================================================= 6. pilot
def stage_pilot(args):
    prov = guard("pilot")
    dev = args.device
    if not SMOKE:
        reg.require_formal(dev, prov)
    env = Env()
    cfg = task_config(ledger_every_tick=False)
    t0 = time.perf_counter()
    doc = {"provenance_at_start": prov, "signal": {}, "evolution": {}}
    graphs = PL.SH_ROUTE_PILOT if not SMOKE else PL.SH_ROUTE_PILOT[:2]
    with acct.category("measure"):
        for j, name in enumerate(graphs):
            g, _ = GR.sh_route(env.con, name)
            ext, spec, gi = GR.grafted(g, env.l1)
            gm = G.graft_interface(ext, env.l1, probe="mean")
            res = signal_for(env, cfg, g, ext, gi, gm, [PL.run_seed("pilot_null", 0, j)], dev)
            doc["signal"][name] = res["populations"]
    with acct.category("selection"):
        for j, name in enumerate(PL.SH_ROUTE_PILOT_EVOLVED if not SMOKE else PL.SH_ROUTE_PILOT_EVOLVED[:1]):
            g, _ = GR.sh_route(env.con, name)
            ext, spec, gi = GR.grafted(g, env.l1)
            R = PL.RUNS_PER_BATCH if not SMOKE else 1
            runs = [EV.RunSpec(4 * j + r, PL.run_seed("pilot_null", r, j), 0.0) for r in range(R)]
            roll = GA.TaskHRollout(env.params, prey_iface=env.iface,
                                   validation_per_slot=PL.VALIDATION_PER_SLOT if not SMOKE else 2)
            base, span = span_of("pilot_training")
            G_ = REGISTERED["pilot"]["generations"] if not SMOKE else 3
            P = cfg.evo.population
            recs = EV.evolve_batch(cfg, gi, spec, runs, generations=G_, checkpoint_every=PL.CHECKPOINT_EVERY,
                                   validation_ids=ids_of("pilot_validation", len(roll.layouts[max(roll.layouts)])),
                                   world_seed=PL.WORLD_SEED, id_base=base, id_span=span, device=dev, rollout_fn=roll,
                                   weights=roll.weights(), check=cap().check, category=acct.category,
                                   initial=lambda r: gen0(env, g, ext, r.run_seed, P),
                                   mutation_scales=lambda r: AR.scales(ext, env.l1, "G-SHr"))
            rows = {}
            for rec in recs:
                ci = rec.champion_index()
                champ = rec.candidates[ci]
                save_population(OUT / "genomes" / f"pilot-{name}-run{rec.spec.run:02d}-candidates.npz",
                                Genome.cat(rec.candidates), cfg=cfg, run=rec.spec.run, run_seed=rec.spec.run_seed,
                                stage="pilot")
                v = [c["validation_mean"] for c in rec.checkpoints]
                rows[str(rec.spec.run)] = {"validation": v, "climb": v[-1] - v[0], "champion_checkpoint": ci,
                                           "champion_sha256": genome_hash(champ, 0),
                                           "seconds_per_generation": float(np.mean([x["batch_seconds"]
                                                                                    for x in rec.log])),
                                           **AR.identity("pilot_null", rec.spec.run, rec.spec.run_seed, name, ext)}
            doc["evolution"][name] = {"runs": rows, "max_index": roll.max_index,
                                      "climbs": bool(any(r["climb"] > 0 for r in rows.values()))}
    doc["max_index"] = max(v["max_index"] for v in doc["evolution"].values())
    doc["headroom"] = {"max_index": doc["max_index"], "limit": 32, "sequence_length": cfg.world.target_sequence_length,
                       "within": doc["max_index"] <= 32}
    doc["seconds"] = time.perf_counter() - t0
    doc["complete"] = True
    doc["note"] = ("never a stop (a failure on null graphs is a finding); not read beside N2. The null signal plays "
                   "one population (32 x 8, then 1 x 256), where N2's plays four (128 x 8, then 4 x 256)")
    write("pilot.json", doc)
    print({k: {r: round(x["climb"], 3) for r, x in v["runs"].items()} for k, v in doc["evolution"].items()},
          "max index", doc["max_index"])


# ================================================================================================= 7. composition
def composition_rows(env, cfg, genomes: list[tuple[str, Genome]], iface, dev) -> dict:
    """Each genome's per-world counts in the training (128 x 8, mixed), validation (4 x 256, mixed) and suite-chunk
    (8 x 512, one setting) shapes against the same genome alone, one strain x 512, on the same worlds and settings, on
    CUDA: every genome on every world, sized and judged as in the CUDA stage (the largest required count over the
    genomes; the score-weighted, stratified interval for the mixed shapes)."""
    hunters = Hunters.of(genomes, iface)
    shapes = {"training": (128, 8), "validation": (4, 256)}
    for name in REGISTERED["composition"]["suite_settings"]:
        shapes[f"suite {name}"] = (8, 512)
    if SMOKE:
        shapes = {"training": (4, 8), f"suite {ST.PROBE_SETTINGS[0]}": (2, 8)}
    out = {}
    for shape, (S, W) in shapes.items():
        chunk = (list(ST.TRAINING) if shape == "training" else list(PL.per_slot_layout(W // 8))
                 if shape == "validation" else [shape.split(" ", 1)[1]] * W)
        one = chunk * (512 // W) if not SMOKE else chunk
        rows = compare(env, cfg, hunters, chunk,
                       lambda ids, S=S, ch=chunk: counts_by_task(env, cfg, hunters, S, ch, ids, dev),
                       lambda ids, ch=one: counts_by_task(env, cfg, hunters, 1, ch, ids, dev))
        out.update({f"{lab} | {shape}": r for lab, r in rows.items()})
    return out


def stage_composition(args):
    prov = guard("composition")
    dev = args.device
    if not SMOKE:
        reg.require_formal(dev, prov)
    env = Env()
    cfg = task_config()
    t0 = time.perf_counter()
    doc = {"provenance_at_start": prov, "note": "the single-strain reference uses padding (pad_single_strain)"}
    with acct.category("measure"):
        rows = composition_rows(env, cfg, c_champions(env), env.gface, dev)
        pilot = read("pilot.json")
        for name, ev in pilot["evolution"].items():
            g, _ = GR.sh_route(env.con, name)
            ext, spec, gi = GR.grafted(g, env.l1)
            champs = []
            for run, r in ev["runs"].items():
                pop, _ = load_population(OUT / "genomes" / f"pilot-{name}-run{int(run):02d}-candidates.npz", spec,
                                         cfg.brain)
                ch = pop.select([r["champion_checkpoint"]])
                if genome_hash(ch, 0) != r["champion_sha256"]:
                    raise SystemExit(f"{name} run {run}: the champion file does not match its record")
                champs.append((f"{name} run {run} C", ch))
            rows.update(composition_rows(env, cfg, champs, gi, dev))
            # CPU against CUDA score checks of the null champions, as in the CUDA stage
            hunters = Hunters.of(champs, gi)
            for st in REGISTERED["cuda"]["settings"] + ["mixed"]:
                S, W = ((len(champs), 512) if st != "mixed" else (128, 8)) if not SMOKE else ((1, 16) if st != "mixed"
                                                                                           else (2, 8))
                chunk = chunk_for(st, W)
                res = compare(env, cfg, hunters, chunk,
                              lambda ids, ch=chunk, S=S: counts_by_task(env, cfg, hunters, S, ch, ids, "cpu"),
                              lambda ids, ch=chunk, S=S: counts_by_task(env, cfg, hunters, S, ch, ids, dev))
                rows.update({f"{lab} | CPU against CUDA {st}": r for lab, r in res.items()})
    doc["rows"] = rows
    doc["failed"] = [k for k, v in rows.items() if not v["passed"]]
    doc["imprecise"] = [k for k, v in rows.items() if not v["precision_reached"]]
    doc["passed"] = not doc["failed"]
    doc["seconds"] = time.perf_counter() - t0
    write("composition.json", doc)
    print("composition:", "passed" if doc["passed"] else f"FAILED {doc['failed']}", "| imprecise:", doc["imprecise"])
    if not doc["passed"]:
        raise SystemExit("a composition check failed: E5-1a stops")


# ================================================================================================= 8. sensitivity
def stage_sensitivity(args):
    prov = guard("sensitivity")
    dev = args.device
    if not SMOKE:
        reg.require_formal(dev, prov)
    env = Env()
    cfg = task_config()
    t0 = time.perf_counter()
    s = REGISTERED["sensitivity"]
    parents = [(lab, g, env.ext, env.gface) for lab, g in c_champions(env)]
    sig, _ = load_population(OUT / "genomes" / "signal-winners.npz", env.spec, cfg.brain)
    parents += [(f"N2 generation-0 winner {i}", sig.select([i]), env.ext, env.gface) for i in range(sig.n_strains)]
    pilot = read("pilot.json")
    for j, name in enumerate(PL.SH_ROUTE_PILOT if not SMOKE else PL.SH_ROUTE_PILOT[:2]):
        g, _ = GR.sh_route(env.con, name)
        ext, spec, gi = GR.grafted(g, env.l1)
        seed = PL.run_seed("pilot_null", 0, j)
        rec = pilot["signal"][name][str(seed)]
        win = gen0(env, g, ext, seed, cfg.evo.population).select([rec["winner"]])
        if genome_hash(win, 0) != rec["winner_sha256"]:
            raise SystemExit(f"{name}: the generation-0 winner does not match the pilot's record")
        parents.append((f"{name} generation-0 winner", win, ext, gi))
    names = list(PL.per_slot_layout((PL.BLOCKS["mutational"][1] // 8) if not SMOKE else 2))
    ids = ids_of("mutational", len(names))
    M = s["mutants"] if not SMOKE else 4
    rows = {}
    with acct.category("measure"):
        for k, (lab, g, ext, gi) in enumerate(parents):
            gen = torch.Generator().manual_seed(s["seed"] + k)
            mut = g.select([0] * M)
            mut.mutate(cfg.mutation, generator=gen, scales=AR.scales(ext, env.l1, "G-N2"))
            both = Genome.cat([g, mut])
            counts = []
            for lo in range(0, both.n_strains, s["chunk_strains"]):  # at most 16 strains x 256 worlds per play
                part = both.select(list(range(lo, min(lo + s["chunk_strains"], both.n_strains))))
                counts.append(play(env, cfg, Brain(moved(part, dev)), names, ids, dev, iface=gi).captures)
            sc = weighted_by_slot(np.concatenate(counts), names)
            par, kids = float(sc[0]), sc[1:]
            share = kids / par if par > 0 else None
            rows[lab] = {"parent": par, "mutant_median": float(np.median(kids)),
                         "median_share": float(np.median(share)) if share is not None else None,
                         "share_below_0.7": float(np.mean(share < s["share_floor"])) if share is not None else None}
    doc = {"provenance_at_start": prov, "rows": rows, "mutants": M, "worlds": len(ids), "complete": True,
           "note": "measured, not a stop (SCOPE.md §7); a parent scoring 0 has no share",
           "seconds": time.perf_counter() - t0}
    write("sensitivity.json", doc)
    print({k: (round(v["parent"], 2), v["median_share"] and round(v["median_share"], 2)) for k, v in rows.items()})


# ================================================================================================= main
def main():
    global EXP, OUT, SMOKE
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("stage", choices=[*STAGES, "cap"])
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, smoke ids, scratch folder, no git checks")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--note", default="")
    args = ap.parse_args()
    if args.smoke:
        SMOKE = True
        EXP = OUT = ROOT / "runs" / "e5-1a-smoke"
        if args.stage != "cap":
            (EXP / f"{args.stage}-started.json").unlink(missing_ok=True)
    cap()
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    {"equivalence": stage_equivalence, "graphs": stage_graphs, "cuda": stage_cuda, "bench": stage_bench,
     "cap": stage_cap, "signal": stage_signal, "pilot": stage_pilot, "composition": stage_composition,
     "sensitivity": stage_sensitivity}[args.stage](args)


if __name__ == "__main__":
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e5-1a-smoke" if smoke else "e5-1a")
    try:
        acct.run_script(main, out_default=str(out), default="measure", name="e5_1a")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
