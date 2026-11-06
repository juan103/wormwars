"""E5-0, Task H's feasibility check (docs/E5/E5-0-PLAN.md). CPU only, no evolution.

Stages, in order (each writes its record to experiments/E5-hunter/E5-0/, or runs/e5-0-smoke/ with --smoke):
  bench        throughput at the intended batches, the projected hours of every later stage, and the plan's cuts
  equivalence  old engine against new (scripts/e5_0_reference.py in a worktree at ab749bb); H1-ghost against Task N;
               the CUDA gap against E1's gate record (reported)
  calibrate    the route follower's check; E_prey from a held contact and the driven approaches; the tuning per setting
  evaluate     every hunter at every setting on the evaluation worlds (resumable with --resume)
  probe        the fixed probes, then the qualification probes (staged under the cap; resumable)
  read         the decision rules (§6) -> reading.json

    python scripts/e5_0.py <stage> [--smoke] [--resume]

Every stage after bench refuses to run unless the code (wormwars, scripts, configs) is unchanged since the stages it
builds on; a resumed stage checks it against its own start marker. Every Task H run checks the ledger at every tick
(1e-5 of each world's starting total) and stops on a larger or non-finite residual.
"""

from __future__ import annotations

import os

if __name__ == "__main__":  # CPU only; not on import (tests)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
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
from wormwars.e1 import controllers as C  # noqa: E402
from wormwars.e5 import hunters as HN  # noqa: E402
from wormwars.e5.hunt import HUNTER, PREY, HuntWorld, e1_task_n, hunt_config  # noqa: E402
from wormwars.e5.play import play  # noqa: E402
from wormwars.e5.prey import PreyBrain, PursuitBrain  # noqa: E402
from wormwars.evo.rollout import rollout, rollout_brain  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402
from wormwars.world import World  # noqa: E402

torch.set_grad_enabled(False)
EXP = ROOT / "experiments" / "E5-hunter" / "E5-0"
OUT = ROOT / "runs" / "e5-0"
E1_FREEZE = ROOT / "experiments" / "E1-navigation" / "freeze.json"
E1_GATE = ROOT / "experiments" / "E1-navigation" / "gate.json"
REF_COMMIT = "ab749bb5b1f4870899d047bec07cb2ddb1c20ea1"  # the engine before E5's hooks (D385)
REF_WORKTREE = ROOT.parent / "wormWars-e5ref"
GUARDED = ["wormwars", "scripts", "configs", "docs/E5/E5-0-PLAN.md"]
CODE = ["wormwars", "scripts", "configs"]  # what a later stage requires unchanged since an earlier one
SMOKE = False
CLOCK: reg.CapClock | None = None
LEDGER_TOL = 1e-5  # T0's relative tolerance

REGISTERED = {
    "run_seed": 1_500_001,
    "ids": {"calibration": [991_000_000, 64], "equivalence": [991_200_000, 512], "evaluation": [991_100_000, 512],
            "trace_worlds": 8},
    "e1_gate": {"first": 996_201_000, "count": 1024, "run_seed": 1_100_001},
    "e_prey": {"ticks": 20, "factor": 10.0, "measure_energy": 1e6, "bite_offset": 0.9, "approach_start": 3.0,
               "approach_ticks": 300},
    "route": {"gain": 2.0, "spacing": 6.0, "reach": 1.0, "check_ticks": 3000, "share": 0.95, "speed_fraction": 0.8,
              "max_limited_fraction": 0.01, "fallbacks": [{"gain": 4.0}, {"gain": 4.0, "spacing": 8.0}]},
    "speeds_h2": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    "speeds_h2b": [0.25, 0.5, 0.75],
    "walk": {"rate": 0.4, "persistence": 0.9},
    "generation0": {"genomes": 16, "seed": 1_500_011},
    "tuning": {
        "combos_per_chunk": 64, "random_walk_seed": 0, "tie": "the first maximum in grid order",
        "grids": {  # E1's (scripts/e1.py REGISTERED["tuning"]["grids"]; checked against freeze.json)
            "S-const": {"k": [1, 2, 4, 8, 16, 32, 64, 256, 1024, 8192], "speed": [0.4, 0.6, 0.8, 1.0],
                        "turn": [-0.2, -0.1, 0.0, 0.1, 0.2]},
            "constant": {"speed": [0.2, 0.4, 0.6, 0.8, 1.0], "turn": [round(-0.6 + 0.1 * i, 1) for i in range(13)]},
            "random-walk": {"speed": [0.4, 0.7, 1.0], "rate": [0.2, 0.4, 0.8, 1.0],
                            "persistence": [0.5, 0.8, 0.9, 0.95, 0.99]},
            "wall-follower": {"speed": [0.4, 0.7, 1.0], "seek_turn": [-0.1, -0.2, -0.4], "avoid_turn": [0.4, 0.8, 1.0],
                              "threshold_above_own_body": [0.05, 0.1, 0.2, 0.4, 0.8, 1.6]},
        },
    },
    "pursuit": {"k": 2.0, "speed": 1.0},
    "probe_settings": ["H1-bite", "H2-0.5"],
    "bench": {"provisional_e_prey": 1.0, "neural_chunk": 16},
    "bootstrap": {"resamples": 10_000, "seed": 0, "lower": 5, "upper": 95},
    "rules": {"reliability": 0.80, "margin": 0.5, "too_easy": 0.5, "flag": 0.25},
    "cap_hours": 8.0,
    "cuts": ["generation 0 down to 8 genomes", "mean and mirrored probes at H1-bite only",
             "H2's speeds thinned to 0.1, 0.3, 0.5, 0.7, 1.0", "evaluation worlds down to 256"],
}
CONTROLS = ("S-const", "constant", "random-walk", "wall-follower")
E1_GRIDS = json.loads(json.dumps(REGISTERED["tuning"]["grids"]))  # as registered, before a smoke run shrinks them
BASELINES = {"stationary": "stationary", "constant": "constant tuned", "random-walk": "random-walk tuned",
             "wall-follower": "wall-follower tuned"}
SCRIPTED_LABELS = (*(f"{n} tuned" for n in CONTROLS), *(f"{n} E1-frozen" for n in CONTROLS), "pursuit", "stationary",
                   "pursuit attack-disabled")


# ----------------------------------------------------------------------------------------------------------- basics
def ids(name: str) -> np.ndarray:
    first, n = REGISTERED["ids"][name]
    return np.arange(first, first + n, dtype=np.int64)


def write(name: str, doc) -> None:
    reg.write_json(EXP / name, doc, atomic=True)


def read(name: str):
    return json.loads((EXP / name).read_text(encoding="utf-8"))


def freeze() -> dict:
    return json.loads(E1_FREEZE.read_text(encoding="utf-8"))


def cap() -> reg.CapClock:
    """One clock per process, made at its start, so the running stage's own time counts (Astra, Fable)."""
    global CLOCK
    if CLOCK is None:
        CLOCK = reg.CapClock(REGISTERED["cap_hours"], OUT / "compute.json")
    return CLOCK


def guard(stage: str, resume: bool = False) -> dict:
    """A clean, pushed tree; a resumed stage also needs the code its start marker recorded."""
    prov = reg.provenance(GUARDED)
    if not SMOKE:
        if prov.get("dirty"):
            raise SystemExit("the tree is dirty: commit and push the code and the plan before a formal stage")
        reg.require_pushed(prov)
    if resume:
        marker = EXP / f"{stage}-started.json"
        if not marker.exists():
            raise SystemExit(f"--resume: {stage} has not started")
        if not SMOKE:
            reg.require_same_code(json.loads(marker.read_text(encoding="utf-8"))["provenance"]["git_commit"], CODE)
    else:
        reg.start_marker(EXP, stage, prov)
    return prov


def built_on(*names: str) -> dict:
    """The earlier stages' records, each complete and run on the code that is here now."""
    docs = {}
    for name in names:
        if not (EXP / name).exists():
            raise SystemExit(f"{name} is missing: run its stage first")
        d = read(name)
        if d.get("complete") is False or d.get("passed") is False or d.get("fits") is False:
            raise SystemExit(f"{name} did not complete or did not pass")
        if not SMOKE:
            reg.require_same_code(d["provenance_at_start"]["git_commit"], CODE)
        docs[name] = d
    return docs


def settings() -> list[dict]:
    S = [{"name": "H1-ghost", "rule": "ghost", "prey": "stationary", "speed": 0.0, "pinned": True},
         {"name": "H1-reach", "rule": "reach", "prey": "stationary", "speed": 0.0, "pinned": True},
         {"name": "H1-bite", "rule": "bite", "prey": "stationary", "speed": 0.0, "pinned": True}]
    for s in REGISTERED["speeds_h2"]:
        S.append({"name": f"H2-{s:g}", "rule": "bite", "prey": "route", "speed": s, "pinned": False})
    for kind, label in (("random_walk", "walk"), ("wall_follower", "wall")):
        for s in REGISTERED["speeds_h2b"]:
            S.append({"name": f"H2b-{label}-{s:g}", "rule": "bite", "prey": kind, "speed": s, "pinned": False})
    return S


def sized_settings(sizes: dict) -> list[dict]:
    S = settings()
    if sizes["speeds"] == 5:
        keep = {"H2-0.1", "H2-0.3", "H2-0.5", "H2-0.7", "H2-1"}
        S = [s for s in S if not s["name"].startswith("H2-") or s["name"] in keep]
    return S


class Env:
    """The connectome, interfaces and configuration, built once, with E1's configuration and grids checked."""

    def __init__(self):
        self.con = load_connectome()
        self.iface = load_interface(self.con)
        self.l1, self.ext, self.ext_spec = HN.grafted(self.con)
        self.gface = G.graft_interface(self.ext, self.l1, probe="real")
        self.cfg = hunt_config()
        fz = freeze()
        if json.loads(json.dumps(e1_task_n().to_dict())) != fz["resolved_config"]:
            raise SystemExit("e1_task_n() is not E1's frozen configuration")
        self.freeze = fz
        self.own_body = float(fz["own_body"]["own_body_max_current"])
        for name in CONTROLS:  # the copied grids are E1's
            mine, theirs = dict(E1_GRIDS[name]), fz["tuned"][name]["grid"]
            if name == "wall-follower":
                mine["threshold"] = [self.own_body + d for d in mine.pop("threshold_above_own_body")]
            if json.loads(json.dumps(mine)) != theirs:
                raise SystemExit(f"the {name} grid is not E1's")


def cfg_for(env: Env, probe: str = "real", ticks: int | None = None):
    c = env.cfg.copy()
    c.world.food_probe = probe
    c.world.check_ledger_every_tick = True  # measurement only: the per-tick maximum of the ledger's residual
    if ticks is not None:
        c.world.max_ticks = int(ticks)
    return c


def prey_for(env: Env, st: dict, n: int, route: dict, cfg=None) -> PreyBrain:
    """The setting's scripted prey. It is built on the worm's interface even beside a grafted hunter: `graft_interface`
    appends the noses after the worm's entries, so every collision and motor index it reads is the same (Fable)."""
    c = cfg or env.cfg
    wf = env.freeze["tuned"]["wall-follower"]["params"]
    return PreyBrain(env.iface, n, c.world.forward_gain, c.world.turn_gain, st["prey"], speed=st["speed"],
                     gain=route["gain"], spacing=route["spacing"], reach=REGISTERED["route"]["reach"],
                     rate=REGISTERED["walk"]["rate"], persistence=REGISTERED["walk"]["persistence"],
                     wall={k: wf[k] for k in ("seek_turn", "avoid_turn", "threshold")})


def scripted(env: Env, name: str, params: dict, cfg, n_strains: int = 1):
    """A blind control or the positive control, with parameters as floats or [strains, 1] tensors."""
    if name == "S-const":
        pol = C.s_const(params["k"], params["speed"], params["turn"])
    elif name == "constant":
        pol = C.ConstantMotion(params["speed"], params["turn"])
    elif name == "random-walk":
        pol = C.PersistentRandomWalk(params["speed"], params["rate"], params["persistence"],
                                     seed=REGISTERED["tuning"]["random_walk_seed"])
    elif name == "wall-follower":
        pol = C.WallFollower(params["speed"], params["seek_turn"], params["avoid_turn"], params["threshold"])
    elif name == "stationary":
        pol = C.ConstantMotion(0.0, 0.0)
    else:
        raise ValueError(name)
    return C.scripted(env.iface, pol, cfg, n_strains=n_strains)


def pursuit(env: Env, cfg, aim="position"):
    return PursuitBrain(env.iface, 302, cfg.world.forward_gain, cfg.world.turn_gain, aim=aim, **REGISTERED["pursuit"])


def check_ledger(rel: float, where: str) -> None:
    if not math.isfinite(rel) or rel > LEDGER_TOL:
        raise SystemExit(f"the ledger's residual is {rel} at {where} (tolerance {LEDGER_TOL}): E5-0 stops")


def hunt(env, st, hunter, iface, n, world_ids, e_prey, route, probe="real", prey_body=None, hunter_attack=1.0,
         ticks=None, setup=None):
    cfg = cfg_for(env, probe, ticks)
    prey = prey_for(env, st, n, route, cfg)
    r = play(cfg, iface, hunter, prey, world_ids, REGISTERED["run_seed"], rule=st["rule"], prey_energy=e_prey,
             pinned=st["pinned"], hunter_attack=hunter_attack, prey_body=prey_body, setup=setup)
    check_ledger(r.ledger_rel_error, f"{st['name']} ({probe})")
    return r, prey


def rows_of(r, i: int) -> dict:
    """Everything one strain's run produced: the counts, the full event table, the bite energy, the prey's movement."""
    out = {"captures": r.captures[i], "bite_energy": r.bite_energy[i], "pin_push": r.pin_push[i],
           "prey_wall_limited": r.prey_wall_limited[i], "ledger": r.ledger_rel_error, "ticks": r.ticks}
    for k, v in r.events.items():
        out[f"ev {k}"] = v[i]
    return out


# ---------------------------------------------------------------------------------------------------------- bench
def n_combos(name: str) -> int:
    g = REGISTERED["tuning"]["grids"][name]
    return int(np.prod([len(v) for v in g.values()]))


def stage_bench(args):
    prov = guard("bench")
    env = Env()
    B = REGISTERED["bench"]
    route = {"gain": REGISTERED["route"]["gain"], "spacing": REGISTERED["route"]["spacing"]}
    e_prey = B["provisional_e_prey"]  # E_prey is not known before calibration; a provisional value of its order
    st = next(s for s in settings() if s["name"] == "H2-0.5")
    bid = ids("equivalence")  # the intended batch (512 worlds; no claim rests on these worlds here)
    cid = ids("calibration")
    sec = {}
    with acct.category("measure"):
        t = time.perf_counter()
        hunt(env, st, pursuit(env, env.cfg), env.iface, 302, bid, e_prey, route)
        sec["scripted episode"] = (time.perf_counter() - t) / len(bid)
        n = REGISTERED["tuning"]["combos_per_chunk"]
        params = {k: torch.tensor([v[0]] * n, dtype=torch.float32).view(n, 1)
                  for k, v in REGISTERED["tuning"]["grids"]["S-const"].items()}
        t = time.perf_counter()
        hunt(env, st, scripted(env, "S-const", params, env.cfg, n_strains=n), env.iface, 302, cid, e_prey, route)
        sec["tuning chunk"] = time.perf_counter() - t
        sets = neural_sets(env, REGISTERED["generation0"]["genomes"])
        k = B["neural_chunk"]
        for fam in ("e4s1", "e2d"):
            t = time.perf_counter()
            run_neural(env, st, fam, sets[fam][:k], e_prey, route, bid, k)
            sec[f"neural episode {fam}"] = (time.perf_counter() - t) / (len(bid) * k)
    per_n = max(sec["neural episode e4s1"], sec["neural episode e2d"])
    per_s = sec["scripted episode"]
    spent = cap().spent_hours() + (time.perf_counter() - cap().t_start) / 3600
    W0, n_all = REGISTERED["ids"]["evaluation"][1], sum(len(v) for v in sets.values())
    g0 = REGISTERED["generation0"]["genomes"]
    chunks = sum(math.ceil(n_combos(nm) / REGISTERED["tuning"]["combos_per_chunk"]) for nm in CONTROLS)

    def project(e):
        n_n = n_all - g0 + e["g0"]
        S = len(sized_settings(e))
        h2 = len([s for s in sized_settings(e) if s["name"].startswith("H2-")])
        W = e["worlds"]
        p = {"equivalence": (2 * 2 + 4 * 3 * 2) * 512 * per_n / 3600 + (5 * 3 * 2 + 1024 / 512) * 512 * per_s / 3600,
             "calibration: route check": 3 * h2 * 64 * 10 * per_s / 3600,  # 3 000 ticks = 10 episodes; fallbacks
             "calibration: E_prey": 4 * 64 * per_s / 3600,
             "calibration: tuning": S * chunks * sec["tuning chunk"] / 3600,
             "evaluation": (n_n * per_n + 11 * per_s) * S * W / 3600,
             "fixed probes": n_n * (1 * 2 + 2 * e["probes_at"]) * W * per_n / 3600}
        p["total"] = sum(p.values()) + spent
        return p

    sizes = {"g0": g0, "probes_at": 2, "speeds": 10, "worlds": W0}
    steps = [(REGISTERED["cuts"][0], {"g0": 8}), (REGISTERED["cuts"][1], {"probes_at": 1}),
             (REGISTERED["cuts"][2], {"speeds": 5}), (REGISTERED["cuts"][3], {"worlds": 256})]
    before = project(sizes)
    cuts = []
    for label, change in steps:
        if project(sizes)["total"] <= REGISTERED["cap_hours"]:
            break
        sizes.update(change)
        cuts.append(label)
    after = project(sizes)
    doc = {"provenance_at_start": prov, "seconds": sec, "provisional_e_prey": e_prey, "neural_hunters": n_all,
           "spent_hours_at_projection": spent, "projected_hours_before_cuts": before, "cuts": cuts,
           "projected_hours": after, "sizes": sizes, "cap_hours": REGISTERED["cap_hours"],
           "fits": after["total"] <= REGISTERED["cap_hours"],
           "note": "the qualification probes are staged after evaluation, under what is left of the cap"}
    write("bench.json", doc)
    print(json.dumps({k: doc[k] for k in ("seconds", "projected_hours", "cuts", "fits")}, indent=1))
    if not doc["fits"]:
        raise SystemExit("even with every cut E5-0 does not fit its cap: it stops before evaluating")


# ------------------------------------------------------------------------------------------------------ equivalence
class Tap:
    def __init__(self, brain):
        self._b, self.currents, self.states = brain, [], []

    def __getattr__(self, name):
        return getattr(self._b, name)

    def step(self, v, current):
        out = self._b.step(v, current)
        self.currents.append(current.detach().clone().numpy())
        self.states.append(out.detach().clone().numpy())
        return out


def _same(a: dict, b: dict) -> list[str]:
    bad = [k for k in sorted(set(a) | set(b)) if k not in a or k not in b]
    for k in sorted(set(a) & set(b)):
        x, y = np.asarray(a[k]), np.asarray(b[k])
        if x.shape != y.shape or not np.array_equal(x, y, equal_nan=x.dtype.kind == "f"):
            bad.append(k)
    return bad


def reference_worktree() -> dict:
    """The old engine's worktree, created if absent, and checked: its HEAD is the reference commit and it is clean."""
    if not REF_WORKTREE.exists():
        reg.git("worktree", "add", "--detach", str(REF_WORKTREE), REF_COMMIT)
    head = reg.git("rev-parse", "HEAD", root=REF_WORKTREE)
    dirty = reg.git("status", "--porcelain", root=REF_WORKTREE)
    if head != REF_COMMIT or dirty:
        raise SystemExit(f"the reference worktree is at {head[:7]} (dirty: {bool(dirty)}), not a clean {REF_COMMIT[:7]}")
    return {"path": str(REF_WORKTREE), "head": head, "clean": True}


def equivalence_hunters(env: Env, cfg_n, cfg_h):
    """(label, Task N brain or genome, Task H brain or genome, interface, n) for §4.2."""
    fz = env.freeze["tuned"]
    e4s = HN.e4s1_champions(env.con, cfg_n.brain)["e4s1 M run00"][0]
    e2 = HN.e2d_champions(env.con, cfg_n.brain)["e2 ga run00"][0]
    l1 = HN.l1_carrier(env.con, cfg_n.brain)
    g0 = HN.generation0(env.con, cfg_n.brain, 1, REGISTERED["generation0"]["seed"])
    out = [("S-const", scripted(env, "S-const", fz["S-const"]["params"], cfg_n),
            scripted(env, "S-const", fz["S-const"]["params"], cfg_h), env.iface, 302),
           ("oracle", C.OracleBrain(env.iface, 302, cfg_n.world.forward_gain, cfg_n.world.turn_gain,
                                    **REGISTERED["pursuit"]), pursuit(env, cfg_h), env.iface, 302)]
    for name in ("constant", "random-walk", "wall-follower"):
        out.append((name, scripted(env, name, fz[name]["params"], cfg_n), scripted(env, name, fz[name]["params"], cfg_h),
                    env.iface, 302))
    for label, g, fc in (("e4s1 M run00", e4s, env.gface), ("L1 carrier", l1, env.gface),
                         ("e2 ga run00", e2, env.iface), ("generation0 #00", g0, env.iface)):
        out.append((label, g, g, fc, g.spec.n))
    return out


def stage_equivalence(args):
    prov = guard("equivalence")
    built_on("bench.json")
    env = Env()
    t0 = time.perf_counter()
    doc = {"provenance_at_start": prov, "reference_commit": REF_COMMIT}
    stationary = settings()[0]
    with acct.category("measure"):
        # 1. old engine against new
        doc["reference_worktree"] = reference_worktree()
        files = {}
        for side, root in (("old", REF_WORKTREE), ("new", ROOT)):
            f = OUT / f"reference-{side}.npz"
            acct.run_counted_child([sys.executable, str(ROOT / "scripts" / "e5_0_reference.py"), "--root", str(root),
                                    "--out", str(f)], OUT / f"reference-{side}-ledger.json", cwd=str(root))
            files[side] = dict(np.load(f, allow_pickle=False))
        bad1 = _same(files["old"], files["new"])
        doc["old_against_new"] = {"arrays": len(files["new"]), "differ": bad1, "identical": not bad1}
        # 2. H1-ghost against Task N
        eid = ids("equivalence")
        cn, ch = e1_task_n(), env.cfg
        bad2, rows = [], {}
        hunters = equivalence_hunters(env, cn, ch)
        for probe in ("real", "constant", "mirrored"):
            for label, tn, th, fc, n in hunters:
                c1, c2 = cn.copy(), cfg_for(env, probe)
                c1.world.food_probe = probe
                rn = rollout(c1, fc, tn, eid, REGISTERED["run_seed"]) if isinstance(tn, Genome) \
                    else rollout_brain(c1, fc, tn, eid, REGISTERED["run_seed"])
                hb = Brain(th) if isinstance(th, Genome) else th
                rh = play(c2, fc, hb, prey_for(env, stationary, n, {"gain": 2.0, "spacing": 6.0}, c2), eid,
                          REGISTERED["run_seed"], rule="ghost")
                check_ledger(rh.ledger_rel_error, f"ghost {probe} {label}")
                same = {"count": np.array_equal(rn.score[0].astype(np.int64), rh.captures[0]),
                        "capture_tick": np.array_equal(rn.events["reach_tick"][0], rh.events["capture_tick"][0]),
                        "path": np.array_equal(rn.events["path_length"][0], rh.events["hunter_path"][0])}
                rows[f"{probe}|{label}"] = {**same, "mean": float(rh.captures.mean())}
                if not all(same.values()):
                    bad2.append(f"{probe}|{label}")
        # traces on the first worlds, every hunter, under the real scent
        tw = eid[:REGISTERED["ids"]["trace_worlds"]]
        for label, tn, th, fc, n in hunters:
            taps = []
            for kind, b in (("navigate", tn), ("hunt", th)):
                tap = Tap(Brain(b) if isinstance(b, Genome) else b)
                if kind == "navigate":
                    w = World(cn, fc, tap, torch.zeros(len(tw), 1, dtype=torch.long), run_seed=REGISTERED["run_seed"],
                              world_ids=tw)
                else:
                    so = torch.zeros(len(tw), 2, dtype=torch.long)
                    w = HuntWorld(ch, fc, [tap, prey_for(env, stationary, n, {"gain": 2.0, "spacing": 6.0})], so,
                                  run_seed=REGISTERED["run_seed"], world_ids=tw, rule="ghost")
                pos, head = [], []
                while not w.done():
                    w.tick()
                    pos.append(w.pos[:, 0].clone().numpy())
                    head.append(w.heading[:, 0].clone().numpy())
                taps.append({"pos": np.stack(pos), "heading": np.stack(head), "current": np.stack(tap.currents),
                             "state": np.stack(tap.states)})
            d = _same(*taps)
            rows[f"trace|{label}"] = {"identical": not d, "differ": d}
            if d:
                bad2.append(f"trace|{label}")
        doc["ghost_against_task_n"] = {"worlds": len(eid), "rows": rows, "differ": bad2, "identical": not bad2}
        # 3. the CUDA gap, reported
        gate = json.loads(E1_GATE.read_text(encoding="utf-8"))
        g = REGISTERED["e1_gate"]
        gids = np.arange(g["first"], g["first"] + g["count"])
        nav = rollout_brain(cn, env.iface, scripted(env, "S-const", env.freeze["tuned"]["S-const"]["params"], cn), gids,
                            g["run_seed"]).score[0].astype(np.int64)
        ref = np.asarray(gate["per_world_counts"]["navigator"], dtype=np.int64)[:len(gids)]
        doc["cuda_gap"] = {"worlds": int(len(gids)), "cpu_mean": float(nav.mean()), "cuda_mean": float(ref.mean()),
                           "mean_difference": float(nav.mean() - ref.mean()),
                           "share_identical": float((nav == ref).mean()),
                           "note": "a second use of E1's gate worlds, for an engine comparison only"}
    doc["seconds"] = time.perf_counter() - t0
    doc["passed"] = bool(doc["old_against_new"]["identical"] and doc["ghost_against_task_n"]["identical"])
    write("equivalence.json", doc)
    print("old against new:", doc["old_against_new"]["identical"], "| ghost against Task N:",
          doc["ghost_against_task_n"]["identical"], "| CUDA gap:", doc["cuda_gap"]["mean_difference"],
          doc["cuda_gap"]["share_identical"])
    if not doc["passed"]:
        raise SystemExit("an equivalence check failed: E5-0 stops until it is explained")


# ------------------------------------------------------------------------------------------------------ calibration
def _place(w, where: str, start: float) -> int:
    """Put the hunter `start` cells from a point of each prey's body, facing it: `held` (its bite point on the mid point
    from the prey's left), `head` (ahead of the prey's head), `side` (left of its mid point), `rear` (behind its tail).
    A head kept inside the arena is clamped there (Fable), so the start distance is not uniform; the clamped count is
    returned. Kill times are measured from first contact, so a clamp does not bias them."""
    L = w.cfg.world.body_length
    p, h = w.pos[:, PREY, 0], w.heading[:, PREY, 0]
    fwd = torch.stack((torch.cos(h), torch.sin(h)), dim=-1)
    left = torch.stack((-torch.sin(h), torch.cos(h)), dim=-1)
    mid, tail = p - fwd * (L / 2), p - fwd * L
    at, out = {"held": (mid, left), "head": (p, fwd), "side": (mid, left), "rear": (tail, -fwd)}[where]
    hp = at + out * start
    clamped = hp.clamp(1.05, w.side - 1.05)
    n = int((clamped != hp).any(-1).sum())
    w.pos[:, HUNTER, 0] = clamped
    w.heading[:, HUNTER, 0] = torch.atan2(at[:, 1] - clamped[:, 1], at[:, 0] - clamped[:, 0])
    w._points = None
    w._update_body_field()
    return n


def _run_tracking(w):
    """Run to the horizon, returning each world's largest single-tick damage to the prey (combat's capped damage)."""
    worst = torch.zeros(w.n_worlds, dtype=torch.float64)
    while not w.done():
        w.tick()
        worst = torch.maximum(worst, w.last_damage_taken[:, PREY, 0].double())
    return worst


def e_prey_calibration(env: Env, route: dict) -> dict:
    E = REGISTERED["e_prey"]
    cid = ids("calibration")
    st = {"name": "H1-bite", "rule": "bite", "prey": "stationary", "speed": 0.0, "pinned": True}
    cfg = cfg_for(env, ticks=E["ticks"])
    w = HuntWorld(cfg, env.iface, [scripted(env, "stationary", {}, cfg), prey_for(env, st, 302, route, cfg)],
                  torch.zeros(len(cid), 2, dtype=torch.long), run_seed=REGISTERED["run_seed"], world_ids=cid,
                  rule="bite", prey_energy=E["measure_energy"])
    clamped_held = _place(w, "held", E["bite_offset"])
    worst_held = _run_tracking(w)
    check_ledger(float(w.ledger_rel_max.max()), "E_prey's held contact")
    per_world = w.ev_damage.sum(dim=1).numpy() / E["ticks"]
    median = float(np.median(per_world))
    e_prey = E["factor"] * median
    approaches, worst = {}, float(worst_held.max())
    for where, aim in (("head", "position"), ("side", "mid"), ("rear", "tail")):
        cfg = cfg_for(env, ticks=E["approach_ticks"])
        w = HuntWorld(cfg, env.iface, [pursuit(env, cfg, aim), prey_for(env, st, 302, route, cfg)],
                      torch.zeros(len(cid), 2, dtype=torch.long), run_seed=REGISTERED["run_seed"], world_ids=cid,
                      rule="bite", prey_energy=max(e_prey, 1e-9))
        nc = _place(w, where, E["approach_start"])
        # capped at E_prey, a driven tick's damage can equal E_prey only on a one-tick kill: the stop rule then fires
        worst = max(worst, float(_run_tracking(w).max()))
        check_ledger(float(w.ledger_rel_max.max()), f"E_prey's {where} approach")
        ev = w.hunt_events()
        cap0, fc0 = ev["capture_tick"][:, 0], ev["first_contact_tick"][:, 0]
        ok = (cap0 >= 0) & (fc0 >= 0)
        kill = (cap0 - fc0)[ok]
        approaches[where] = {"aim": aim, "worlds": int(len(cid)), "start_clamped": nc,
                             "captured_first_life": int(ok.sum()),
                             "kill_ticks_median": float(np.median(kill)) if kill.size else None,
                             "kill_ticks_min": int(kill.min()) if kill.size else None,
                             "kill_ticks_max": int(kill.max()) if kill.size else None}
    stop = None
    if median <= 0:
        stop = "the held contact's median damage is zero"
    elif e_prey <= worst:
        stop = f"E_prey {e_prey:.4f} is not larger than the largest single-tick damage seen ({worst:.4f})"
    return {"held": {"worlds": int(len(cid)), "ticks": E["ticks"], "start_clamped": clamped_held,
                     "per_world_damage_per_tick": per_world.tolist(), "median": median,
                     "min": float(per_world.min()), "max": float(per_world.max())},
            "e_prey": e_prey, "largest_single_tick_damage": worst, "approaches": approaches, "stop": stop}


def route_check(env: Env, route: dict, speeds) -> dict:
    """The plan's three conditions, required jointly in at least 95% of worlds (Astra); each also reported alone."""
    R = REGISTERED["route"]
    cid = ids("calibration")
    T = R["check_ticks"]
    rows = []
    for s in speeds:
        st = {"name": f"check-{s:g}", "rule": "bite", "prey": "route", "speed": s, "pinned": False}
        cfg = cfg_for(env, ticks=T)
        r, prey = hunt(env, st, scripted(env, "stationary", {}, cfg), env.iface, 302, cid, 1.0, route,
                       hunter_attack=0.0, ticks=T)
        path = r.events["prey_path"][0].sum(axis=1) / T
        laps = prey.laps_done.numpy()
        limited = r.prey_wall_limited[0] / T
        ok_speed = path >= R["speed_fraction"] * s * env.cfg.world.max_speed
        ok_lap, ok_lim = laps >= 1, limited <= R["max_limited_fraction"]
        joint = ok_speed & ok_lap & ok_lim
        rows.append({"speed": s, "share_joint": float(joint.mean()), "share_speed": float(ok_speed.mean()),
                     "share_lap": float(ok_lap.mean()), "share_limited": float(ok_lim.mean()),
                     "path_per_tick_median": float(np.median(path)), "laps_median": float(np.median(laps)),
                     "captures": int(r.captures.sum()), "passed": bool(joint.mean() >= R["share"])})
    return {"route": route, "rows": rows, "passed": all(x["passed"] for x in rows)}


def tune(env: Env, st: dict, name: str, e_prey: float, route: dict) -> dict:
    T = REGISTERED["tuning"]
    grid = dict(T["grids"][name])
    if name == "wall-follower":
        offs = grid.pop("threshold_above_own_body")
        grid["threshold"] = [env.own_body + d for d in offs]
    keys = list(grid)
    combos = [list(c) for c in itertools.product(*(grid[k] for k in keys))]
    cid = ids("calibration")
    means = []
    for lo in range(0, len(combos), T["combos_per_chunk"]):
        cap().check()
        chunk = combos[lo:lo + T["combos_per_chunk"]]
        n = len(chunk)
        params = {k: torch.tensor([c[i] for c in chunk], dtype=torch.float32).view(n, 1) for i, k in enumerate(keys)}
        with acct.category("tuning"):
            r, _ = hunt(env, st, scripted(env, name, params, env.cfg, n_strains=n), env.iface, 302, cid, e_prey, route)
        means.extend(r.captures.mean(axis=1).tolist())
    i = int(np.argmax(means))
    return {"keys": keys, "grid": grid, "means": means, "winner_index": i,
            "params": dict(zip(keys, [float(x) for x in combos[i]])), "tuned_mean": float(means[i])}


def stage_calibrate(args):
    prov = guard("calibrate")
    bench = built_on("bench.json", "equivalence.json")["bench.json"]
    env = Env()
    t0 = time.perf_counter()
    R = REGISTERED["route"]
    route = {"gain": R["gain"], "spacing": R["spacing"]}
    S = sized_settings(bench["sizes"])
    speeds = [s["speed"] for s in S if s["name"].startswith("H2-")]
    with acct.category("calibration"):
        checks = [route_check(env, route, speeds)]
        for fb in R["fallbacks"]:
            if checks[-1]["passed"]:
                break
            route = {**route, **fb}
            checks.append(route_check(env, route, speeds))
        doc = {"provenance_at_start": prov, "registered": REGISTERED, "sizes": bench["sizes"], "route_checks": checks,
               "route": route, "complete": False}
        if not checks[-1]["passed"]:
            doc["stop"] = "the route follower failed its check at gain 4 and spacing 8: E5-0 stops for a revision"
            write("calibration.json", doc)
            raise SystemExit(doc["stop"])
        ep = e_prey_calibration(env, route)
        doc["e_prey"] = ep
        if ep["stop"]:
            doc["stop"] = ep["stop"]
            write("calibration.json", doc)
            raise SystemExit(ep["stop"])
        tuned = {}
        for st in S:
            tuned[st["name"]] = {name: tune(env, st, name, ep["e_prey"], route) for name in CONTROLS}
            print(st["name"], {k: round(v["tuned_mean"], 3) for k, v in tuned[st["name"]].items()}, flush=True)
            write("calibration.json", {**doc, "tuned": tuned})
    doc.update(tuned=tuned, complete=True, seconds=time.perf_counter() - t0)
    write("calibration.json", doc)
    print("E_prey", round(ep["e_prey"], 4), "route", route)


# ---------------------------------------------------------------------------------------------------- the hunters
def neural_sets(env: Env, g0n: int) -> dict:
    """{family: [(label, genome)]}: the frozen neural hunters (80, or 72 under the plan's first cut)."""
    b = env.cfg.brain
    g0 = HN.generation0(env.con, b, REGISTERED["generation0"]["genomes"], REGISTERED["generation0"]["seed"])
    e2d = HN.e2d_champions(env.con, b)
    if not SMOKE and len(e2d) != 47:
        raise SystemExit(f"{len(e2d)} E2d champions, not 47")
    return {"e4s1": [(k, g) for k, (g, _) in HN.e4s1_champions(env.con, b).items()],
            "L1": [("L1 carrier", HN.l1_carrier(env.con, b))],
            "e2d": [(k, g) for k, (g, _) in e2d.items()],
            "generation0": [(f"generation0 #{i:02d}", g0.select([i])) for i in range(g0n)]}


def neural_iface(env: Env, family: str):
    return (env.gface, 306) if family in ("e4s1", "L1") else (env.iface, 302)


def run_neural(env, st, family, members, e_prey, route, world_ids, chunk, probe="real", prey_body=None):
    """{label: rows} for a family, in chunks of `chunk` strains."""
    fc, n = neural_iface(env, family)
    out = {}
    for lo in range(0, len(members), chunk):
        cap().check()
        part = members[lo:lo + chunk]
        g = Genome.cat([m[1] for m in part])
        r, _ = hunt(env, st, Brain(g), fc, n, world_ids, e_prey, route, probe=probe, prey_body=prey_body)
        for i, (label, _) in enumerate(part):
            out[label] = rows_of(r, i)
    return out


def run_scripted(env, st, e_prey, route, tuned, world_ids):
    fz = env.freeze["tuned"]
    out = {}
    jobs = [(f"{n} tuned", scripted(env, n, tuned[n]["params"], env.cfg)) for n in CONTROLS]
    jobs += [(f"{n} E1-frozen", scripted(env, n, fz[n]["params"], env.cfg)) for n in CONTROLS]
    jobs += [("pursuit", pursuit(env, env.cfg)), ("stationary", scripted(env, "stationary", {}, env.cfg))]
    for label, brain in jobs:
        cap().check()
        r, _ = hunt(env, st, brain, env.iface, 302, world_ids, e_prey, route)
        out[label] = rows_of(r, 0)
    if st["name"] == "H1-bite":
        r, _ = hunt(env, st, pursuit(env, env.cfg), env.iface, 302, world_ids, e_prey, route, hunter_attack=0.0)
        out["pursuit attack-disabled"] = rows_of(r, 0)
        caught, damage = int(r.captures.sum()), float(r.events["damage"].sum())
        if caught or damage:
            raise SystemExit(f"the attack-disabled check captured {caught} and dealt {damage}: a bug; E5-0 stops")
    return out


# ------------------------------------------------------------------------------------------------------- evaluate
def _save_setting(name: str, rows: dict) -> None:
    d = OUT / "evaluation"
    d.mkdir(parents=True, exist_ok=True)
    arrays = {f"{label}|{k}": v for label, r in rows.items() for k, v in r.items() if isinstance(v, np.ndarray)}
    np.savez_compressed(d / f"{name}.npz", **arrays)
    meta = {label: {k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for label, r in rows.items()}
    reg.write_json(d / f"{name}.json", meta)


def load_setting(name: str):
    d = OUT / "evaluation"
    z = np.load(d / f"{name}.npz", allow_pickle=False)
    counts = {k.split("|")[0]: z[k] for k in z.files if k.endswith("|captures")}
    meta = json.loads((d / f"{name}.json").read_text(encoding="utf-8"))
    return counts, meta, z


def committed_evaluation(sizes: dict) -> dict:
    """The committed record (rule 5): per-world counts of every hunter at every setting, and per setting the prey's
    realised speed (with the stationary hunter), the pin's log and the ledger's largest residual."""
    out = {"worlds": ids("evaluation")[:sizes["worlds"]].tolist(), "settings": {}}
    for st in sized_settings(sizes):
        counts, meta, z = load_setting(st["name"])
        sp = z["stationary|ev prey_path"].sum(axis=1) / meta["stationary"]["ticks"]
        out["settings"][st["name"]] = {
            "setting": st, "per_world_counts": {k: v.astype(int).tolist() for k, v in counts.items()},
            "prey_speed_with_stationary_hunter": {"median": float(np.median(sp)), "min": float(sp.min())},
            "pin_push_total": float(sum(float(z[f"{k}|pin_push"].sum()) for k in counts)),
            "prey_wall_limited_total": int(sum(int(z[f"{k}|prey_wall_limited"].sum()) for k in counts)),
            "ledger_rel_error_max": max(float(v["ledger"]) for v in meta.values())}
    return out


def stage_evaluate(args):
    prov = guard("evaluate", resume=args.resume)
    docs = built_on("bench.json", "equivalence.json", "calibration.json")
    bench, cal = docs["bench.json"], docs["calibration.json"]
    env = Env()
    route, e_prey = cal["route"], cal["e_prey"]["e_prey"]
    sizes = bench["sizes"]
    eid = ids("evaluation")[:sizes["worlds"]]
    sets = neural_sets(env, sizes["g0"])
    d = OUT / "evaluation"
    done = {p.stem for p in d.glob("*.json")} if d.exists() else set()
    progress = read("evaluation-progress.json") if (EXP / "evaluation-progress.json").exists() else {"attempts": []}
    progress["attempts"].append({"provenance": prov, "resume": bool(args.resume), "skipped_done": sorted(done)})
    t0 = time.perf_counter()
    with acct.category("final"):
        for st in sized_settings(sizes):
            if st["name"] in done:
                continue
            rows = run_scripted(env, st, e_prey, route, cal["tuned"][st["name"]], eid)
            for fam, members in sets.items():
                rows.update(run_neural(env, st, fam, members, e_prey, route, eid, REGISTERED["bench"]["neural_chunk"]))
            _save_setting(st["name"], rows)
            done.add(st["name"])
            write("evaluation-progress.json", {**progress, "completed": sorted(done)})
            print(st["name"], "done", round(time.perf_counter() - t0), "s", flush=True)
    write("evaluation.json", {"provenance_at_start": prov, **committed_evaluation(sizes), "complete": True})
    write("evaluation-progress.json", {**progress, "completed": sorted(done), "complete": True})


# ---------------------------------------------------------------------------------------------------------- reading
class Boot:
    """Paired percentile bootstrap over the evaluation worlds, one resample set for everything (§6)."""

    def __init__(self, n_worlds: int):
        B = REGISTERED["bootstrap"]
        self.idx = np.random.default_rng(B["seed"]).integers(0, n_worlds, size=(B["resamples"], n_worlds))
        self.lo, self.hi = B["lower"], B["upper"]

    def means(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(x, dtype=np.float64)[self.idx].mean(axis=1)

    def bounds(self, r: np.ndarray) -> list[float]:
        r = r[np.isfinite(r)]
        if r.size == 0:
            return [float("nan"), float("nan")]
        return [float(np.percentile(r, self.lo)), float(np.percentile(r, self.hi))]

    def diff(self, a, b) -> dict:
        return {"mean": float(np.mean(a) - np.mean(b)), "bounds": self.bounds(self.means(a) - self.means(b))}


def criteria(boot: Boot, counts: np.ndarray, best_r: np.ndarray) -> dict:
    R = REGISTERED["rules"]
    rel_lo, rel_hi = boot.bounds(boot.means(counts >= 1))
    adv_lo, adv_hi = boot.bounds(boot.means(counts) - best_r)
    return {"mean": float(np.mean(counts)), "share_at_least_1": float(np.mean(counts >= 1)),
            "reliability": [rel_lo, rel_hi], "advantage_over_best_baseline": [adv_lo, adv_hi],
            "capture_criteria": bool(rel_lo >= R["reliability"] and adv_lo > R["margin"]),
            "fails_reliability": bool(rel_hi < R["reliability"]), "fails_advantage": bool(adv_hi < R["margin"])}


def baselines_r(boot: Boot, counts: dict) -> tuple[np.ndarray, dict]:
    rs = {k: boot.means(counts[v]) for k, v in BASELINES.items()}
    return np.max(np.stack(list(rs.values())), axis=0), {k: float(np.mean(counts[v])) for k, v in BASELINES.items()}


def neural_labels(counts: dict) -> list[str]:
    return [k for k in counts if k not in SCRIPTED_LABELS]


# ------------------------------------------------------------------------------------------------------------ probes
def probe_file(sname: str, kind: str, label: str | None = None) -> Path:
    return OUT / "probes" / (f"{sname}__{kind}.npz" if label is None else f"{sname}__{kind}__{label}.npz")


def stage_probe(args):
    prov = guard("probe", resume=args.resume)
    docs = built_on("bench.json", "equivalence.json", "calibration.json", "evaluation.json")
    bench, cal = docs["bench.json"], docs["calibration.json"]
    env = Env()
    route, e_prey = cal["route"], cal["e_prey"]["e_prey"]
    sizes = bench["sizes"]
    W = sizes["worlds"]
    eid = ids("evaluation")[:W]
    sets = neural_sets(env, sizes["g0"])
    (OUT / "probes").mkdir(parents=True, exist_ok=True)
    by_name = {s["name"]: s for s in sized_settings(sizes)}
    k = REGISTERED["bench"]["neural_chunk"]
    with acct.category("probe"):
        # the fixed probes
        for sname in REGISTERED["probe_settings"]:
            kinds = [("body", "real", False)]
            if sizes["probes_at"] == 2 or sname == "H1-bite":
                kinds += [("mean", "mean", None), ("mirrored", "mirrored", None)]
            for kind, probe, body in kinds:
                f = probe_file(sname, kind)
                if f.exists():
                    continue
                rows = {}
                for fam, members in sets.items():
                    rows.update(run_neural(env, by_name[sname], fam, members, e_prey, route, eid, k, probe=probe,
                                           prey_body=body))
                np.savez_compressed(f, **{lab: v["captures"] for lab, v in rows.items()})
        # the qualification probes, staged: every (setting, hunter) meeting the capture criteria; H1-ghost excluded
        boot = Boot(W)
        order = ["e4s1", "L1", "e2d", "generation0"]
        groups = {}
        for fam in order:
            for st in sized_settings(sizes):
                if st["name"] == "H1-ghost":
                    continue
                counts, _, _ = load_setting(st["name"])
                best_r, _ = baselines_r(boot, counts)
                for label, g in sets[fam]:
                    if criteria(boot, counts[label], best_r)["capture_criteria"] and \
                            not probe_file(st["name"], "constant", label).exists():
                        groups.setdefault((fam, st["name"]), []).append((label, g))
        untested = []
        for (fam, sname), members in groups.items():
            for lo in range(0, len(members), k):
                part = members[lo:lo + k]
                try:
                    r = run_neural(env, by_name[sname], fam, part, e_prey, route, eid, k, probe="constant")
                except reg.CapReached:
                    untested += [f"{sname}|{label}" for label, _ in part]
                    continue
                for label, _ in part:
                    np.savez_compressed(probe_file(sname, "constant", label), captures=r[label]["captures"])
    committed = {"provenance_at_start": prov, "untested_under_the_cap": untested, "fixed": {}, "constant": {}}
    for f in sorted((OUT / "probes").glob("*.npz")):
        parts = f.stem.split("__")
        z = np.load(f, allow_pickle=False)
        if len(parts) == 2:
            committed["fixed"][f.stem] = {lab: z[lab].astype(int).tolist() for lab in z.files}
        else:
            committed["constant"][f.stem] = z["captures"].astype(int).tolist()
    write("probes.json", {**committed, "complete": True})


def stage_read(args):
    docs = built_on("bench.json", "equivalence.json", "calibration.json", "evaluation.json", "probes.json")
    sizes = docs["bench.json"]["sizes"]
    W = sizes["worlds"]
    boot = Boot(W)
    R = REGISTERED["rules"]
    out = {"rules": R, "bootstrap": REGISTERED["bootstrap"], "settings": {}}
    for st in sized_settings(sizes):
        name = st["name"]
        counts, meta, _ = load_setting(name)
        if name == "H1-ghost":  # the bridge to Task N: no rule is read there (§6)
            out["settings"][name] = {"setting": st, "bridge": True,
                                     "means": {k: float(np.mean(v)) for k, v in counts.items()}}
            continue
        best_r, base_means = baselines_r(boot, counts)
        pc = counts["S-const tuned"]
        pc_c = criteria(boot, pc, best_r)
        row = {"setting": st, "baseline_means": base_means, "positive_control": pc_c,
               "solvable": pc_c["capture_criteria"], "pursuit_mean": float(np.mean(counts["pursuit"])),
               "e1_frozen_means": {n: float(np.mean(counts[f"{n} E1-frozen"])) for n in CONTROLS}}
        if row["solvable"]:
            pr = boot.means(pc)
            ratio = np.where(pr > 0, best_r / np.where(pr > 0, pr, 1.0), np.nan)
            lo, hi = boot.bounds(ratio)
            point = float(max(base_means.values()) / pc.mean()) if pc.mean() > 0 else float("nan")
            row["too_easy"] = {"ratio": point, "bounds": [lo, hi], "flag": bool(point >= R["flag"]),
                               "reading": ("too easy" if lo >= R["too_easy"] else "not too easy" if hi < R["too_easy"]
                                           else "inconclusive")}
        if name == "H1-bite":
            row["attack_disabled"] = {"captures": int(np.sum(counts["pursuit attack-disabled"]))}
        hunters = {}
        for label in neural_labels(counts):
            c = counts[label]
            h = criteria(boot, c, best_r)
            f = probe_file(name, "constant", label)
            if h["capture_criteria"]:
                if f.exists():
                    k = np.load(f, allow_pickle=False)["captures"]
                    lo, hi = boot.bounds(boot.means(c) - boot.means(k))
                    h["cue"] = [lo, hi]
                    h["fails_cue"] = bool(hi <= 0)
                    h["qualifies"] = bool(lo > 0)
                    h["reading"] = "qualifies" if h["qualifies"] else ("fails cue dependence" if h["fails_cue"]
                                                                      else "uncertain")
                else:
                    h["qualifies"] = None
                    h["reading"] = "capture criteria met; cue dependence untested"
            else:
                h["qualifies"] = False
                fails = [x for x in ("reliability", "advantage") if h[f"fails_{x}"]]
                h["reading"] = ("demonstrated failure: " + ", ".join(fails)) if fails else "uncertain"
            hunters[label] = h
        row["hunters"] = hunters
        out["settings"][name] = row
    S = sized_settings(sizes)
    series = {"H2": [s["name"] for s in S if s["name"].startswith("H2-")],
              "H2b walk": [s["name"] for s in S if s["name"].startswith("H2b-walk")],
              "H2b wall": [s["name"] for s in S if s["name"].startswith("H2b-wall")]}
    falls = {}
    for label in out["settings"]["H1-bite"]["hunters"]:
        falls[label] = {}
        for sname, names in series.items():
            hs = [out["settings"][n]["hunters"][label] for n in names]
            q = [h["reading"] for h in hs]
            falls[label][sname] = {"first_not_qualifying": next((n for n, x in zip(names, q) if x != "qualifies"), None),
                                   "first_capture_criteria_not_met": next(
                                       (n for n, h in zip(names, hs) if not h["capture_criteria"]), None),
                                   "readings": dict(zip(names, q))}
    out["falls_off"] = falls
    # readings without a threshold, with paired intervals
    g, r = load_setting("H1-ghost")[0], load_setting("H1-reach")[0]
    out["ghost_minus_reach"] = {k: boot.diff(g[k], r[k]) for k in g if k in r and k != "pursuit attack-disabled"}
    probes = {}
    for sname in REGISTERED["probe_settings"]:
        counts = load_setting(sname)[0]
        for kind in ("body", "mean", "mirrored"):
            f = probe_file(sname, kind)
            if f.exists():
                z = np.load(f, allow_pickle=False)
                probes[f"{sname}|{kind}"] = {lab: boot.diff(counts[lab], z[lab]) for lab in z.files}
    out["intact_minus_probe"] = probes
    write("reading.json", out)
    print("solvable:", {n: v.get("solvable") for n, v in out["settings"].items()})


def main():
    global EXP, OUT, SMOKE
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("stage", choices=["bench", "equivalence", "calibrate", "evaluate", "probe", "read"])
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, scratch folder, no git checks")
    ap.add_argument("--resume", action="store_true", help="continue a started evaluate or probe stage")
    args = ap.parse_args()
    if args.resume and args.stage not in ("evaluate", "probe"):
        raise SystemExit("--resume is for evaluate and probe")
    if args.smoke:
        SMOKE = True
        EXP = OUT = ROOT / "runs" / "e5-0-smoke"
        R = REGISTERED
        for k in ("calibration", "equivalence", "evaluation"):
            R["ids"][k][1] = 8
        R["ids"]["trace_worlds"] = 2
        R["e1_gate"]["count"] = 16
        R["route"]["check_ticks"] = 300
        R["route"]["share"] = 0.0
        R["generation0"]["genomes"] = 2
        R["speeds_h2"] = [0.1, 0.5, 1.0]
        R["speeds_h2b"] = [0.5]
        R["bootstrap"]["resamples"] = 200
        R["tuning"]["grids"] = {k: {kk: vv[:2] for kk, vv in g.items()} for k, g in R["tuning"]["grids"].items()}
        if not args.resume:
            (EXP / f"{args.stage}-started.json").unlink(missing_ok=True)
    cap()  # the clock starts with the process
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    {"bench": stage_bench, "equivalence": stage_equivalence, "calibrate": stage_calibrate,
     "evaluate": stage_evaluate, "probe": stage_probe, "read": stage_read}[args.stage](args)


if __name__ == "__main__":
    smoke = "--smoke" in sys.argv
    out = ROOT / "runs" / ("e5-0-smoke" if smoke else "e5-0")
    try:
        acct.run_script(main, out_default=str(out), default="measure", name="e5_0")
    finally:
        agg = out / "compute.json"
        if agg.exists() and not smoke:
            EXP.mkdir(parents=True, exist_ok=True)
            (EXP / "compute-record.json").write_text(agg.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
