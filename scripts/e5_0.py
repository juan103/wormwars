"""E5-0, Task H's feasibility check (docs/E5/E5-0-PLAN.md). CPU only, no evolution.

Stages, in order (each writes its record to experiments/E5-hunter/E5-0/, or runs/e5-0-smoke/ with --smoke):
  calibrate    E_prey from a held contact and the driven approaches; the route follower's check; the tuning per setting
  equivalence  old engine against new (scripts/e5_0_reference.py in a worktree at ab749bb); H1-ghost against Task N;
               the CUDA gap against E1's gate record (reported)
  bench        throughput, the projected hours, and the plan's cuts if they are needed
  evaluate     every hunter at every setting on the 512 evaluation worlds (resumable with --resume)
  probe        the fixed probes, then the qualification probes (staged under the cap)
  read         the decision rules (§6) -> reading.json

    python scripts/e5_0.py <stage> [--smoke] [--resume]
"""

from __future__ import annotations

import os

if __name__ == "__main__":  # CPU only; not on import (tests)
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

import argparse  # noqa: E402
import itertools  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import subprocess  # noqa: E402
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
GUARDED = ["wormwars", "scripts", "configs", "docs/E5/E5-0-PLAN.md"]
SMOKE = False

REGISTERED = {
    "run_seed": 1_500_001,
    "ids": {"calibration": [991_000_000, 64], "equivalence": [991_200_000, 512], "evaluation": [991_100_000, 512],
            "trace_worlds": 8},
    "e1_gate": {"first": 996_201_000, "count": 1024, "run_seed": 1_100_001},
    "e_prey": {"ticks": 20, "factor": 10.0, "measure_energy": 1e6, "bite_offset": 0.9, "approach_start": 3.0,
               "approach_ticks": 300},
    "route": {"gain": 2.0, "spacing": 6.0, "reach": 1.0, "check_ticks": 3000, "share": 0.95, "speed_fraction": 0.8,
              "max_refused_fraction": 0.01, "fallbacks": [{"gain": 4.0}, {"gain": 4.0, "spacing": 8.0}]},
    "speeds_h2": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    "speeds_h2b": [0.25, 0.5, 0.75],
    "walk": {"rate": 0.4, "persistence": 0.9},
    "generation0": {"genomes": 16, "seed": 1_500_011},
    "tuning": {
        "combos_per_chunk": 64, "random_walk_seed": 0, "tie": "the first maximum in grid order",
        "grids": {  # E1's (scripts/e1.py REGISTERED["tuning"]["grids"])
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
    "bootstrap": {"resamples": 10_000, "seed": 0, "lower": 5, "upper": 95},
    "rules": {"reliability": 0.80, "margin": 0.5, "too_easy": 0.5, "flag": 0.25},
    "cap_hours": 8.0,
    "cuts": ["generation 0 down to 8 genomes", "mean and mirrored probes at H1-bite only",
             "H2's speeds thinned to 0.1, 0.3, 0.5, 0.7, 1.0", "evaluation worlds down to 256"],
}
CONTROLS = ("S-const", "constant", "random-walk", "wall-follower")
BASELINES = ("stationary", "constant", "random-walk", "wall-follower")


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
    return reg.CapClock(REGISTERED["cap_hours"], OUT / "compute.json")


def guard(stage: str) -> dict:
    prov = reg.provenance(GUARDED)
    if not SMOKE:
        if prov.get("dirty"):
            raise SystemExit("the tree is dirty: commit (and push) the code and the plan before a formal stage")
        reg.require_pushed(prov)
    return prov


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


class Env:
    """The connectome, interfaces and configuration, built once."""

    def __init__(self):
        self.con = load_connectome()
        self.iface = load_interface(self.con)
        self.l1, self.ext, self.ext_spec = HN.grafted(self.con)
        self.gface = G.graft_interface(self.ext, self.l1, probe="real")
        self.cfg = hunt_config()
        fz = freeze()
        want = json.loads(json.dumps(e1_task_n().to_dict()))
        if want != fz["resolved_config"]:
            raise SystemExit("e1_task_n() is not E1's frozen configuration")
        self.freeze = fz
        self.own_body = float(fz["own_body"]["own_body_max_current"])


def cfg_for(env: Env, probe: str = "real", ticks: int | None = None):
    c = env.cfg.copy()
    c.world.food_probe = probe
    if ticks is not None:
        c.world.max_ticks = int(ticks)
    return c


def prey_for(env: Env, st: dict, n: int, route: dict, cfg=None) -> PreyBrain:
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


def hunt(env, st, hunter, iface, n, world_ids, e_prey, route, probe="real", prey_body=None, hunter_attack=1.0,
         ticks=None, setup=None):
    cfg = cfg_for(env, probe, ticks)
    prey = prey_for(env, st, n, route, cfg)
    r = play(cfg, iface, hunter, prey, world_ids, REGISTERED["run_seed"], rule=st["rule"], prey_energy=e_prey,
             pinned=st["pinned"], hunter_attack=hunter_attack, prey_body=prey_body, setup=setup)
    return r, prey


# ------------------------------------------------------------------------------------------------------ calibration
def _place(w, where: str, start: float):
    """Put the hunter `start` cells from a point of each prey's body, facing it: `held` (its bite point on the mid point
    from the prey's left), `head` (ahead of the prey's head), `side` (left of its mid point), `rear` (behind its tail)."""
    L = w.cfg.world.body_length
    p, h = w.pos[:, PREY, 0], w.heading[:, PREY, 0]
    fwd = torch.stack((torch.cos(h), torch.sin(h)), dim=-1)
    left = torch.stack((-torch.sin(h), torch.cos(h)), dim=-1)
    mid, tail = p - fwd * (L / 2), p - fwd * L
    at, out = {"held": (mid, left), "head": (p, fwd), "side": (mid, left), "rear": (tail, -fwd)}[where]
    hp = at + out * start
    w.pos[:, HUNTER, 0] = hp
    w.heading[:, HUNTER, 0] = torch.atan2(-out[:, 1], -out[:, 0])
    w._points = None
    w._update_body_field()


def _run_tracking(w):
    """Run to the horizon, returning each world's largest single-tick damage to the prey."""
    worst = torch.zeros(w.n_worlds, dtype=torch.float64)
    last = w.ev_damage.sum(dim=1)
    while not w.done():
        w.tick()
        now = w.ev_damage.sum(dim=1)
        worst = torch.maximum(worst, now - last)
        last = now
    return worst


def e_prey_calibration(env: Env, route: dict) -> dict:
    E = REGISTERED["e_prey"]
    cid = ids("calibration")
    st = {"name": "H1-bite", "rule": "bite", "prey": "stationary", "speed": 0.0, "pinned": True}
    cfg = cfg_for(env, ticks=E["ticks"])
    hunter = scripted(env, "stationary", {}, cfg)
    w = HuntWorld(cfg, env.iface, [hunter, prey_for(env, st, 302, route, cfg)], torch.zeros(len(cid), 2, dtype=torch.long),
                  run_seed=REGISTERED["run_seed"], world_ids=cid, rule="bite", prey_energy=E["measure_energy"])
    _place(w, "held", E["bite_offset"])
    worst_held = _run_tracking(w)
    per_world = w.ev_damage.sum(dim=1).numpy() / E["ticks"]
    median = float(np.median(per_world))
    e_prey = E["factor"] * median
    approaches, worst = {}, float(worst_held.max())
    for where, aim in (("head", "position"), ("side", "mid"), ("rear", "tail")):
        cfg = cfg_for(env, ticks=E["approach_ticks"])
        w = HuntWorld(cfg, env.iface, [pursuit(env, cfg, aim), prey_for(env, st, 302, route, cfg)],
                      torch.zeros(len(cid), 2, dtype=torch.long), run_seed=REGISTERED["run_seed"], world_ids=cid,
                      rule="bite", prey_energy=max(e_prey, 1e-9))
        _place(w, where, E["approach_start"])
        worst = max(worst, float(_run_tracking(w).max()))
        ev = w.hunt_events()
        cap0, fc0 = ev["capture_tick"][:, 0], ev["first_contact_tick"][:, 0]
        ok = (cap0 >= 0) & (fc0 >= 0)
        kill = (cap0 - fc0)[ok]
        approaches[where] = {"aim": aim, "worlds": int(len(cid)), "captured_first_life": int(ok.sum()),
                             "kill_ticks_median": float(np.median(kill)) if kill.size else None,
                             "kill_ticks_min": int(kill.min()) if kill.size else None,
                             "kill_ticks_max": int(kill.max()) if kill.size else None}
    stop = None
    if median <= 0:
        stop = "the held contact's median damage is zero"
    elif e_prey <= worst:
        stop = f"E_prey {e_prey:.4f} is not larger than the largest single-tick damage seen ({worst:.4f})"
    return {"held": {"worlds": int(len(cid)), "ticks": E["ticks"], "per_world_damage_per_tick": per_world.tolist(),
                     "median": median, "min": float(per_world.min()), "max": float(per_world.max())},
            "e_prey": e_prey, "largest_single_tick_damage": worst, "approaches": approaches, "stop": stop}


def route_check(env: Env, route: dict) -> dict:
    R = REGISTERED["route"]
    cid = ids("calibration")
    T = R["check_ticks"]
    rows = []
    for s in REGISTERED["speeds_h2"]:
        st = {"name": f"check-{s:g}", "rule": "bite", "prey": "route", "speed": s, "pinned": False}
        cfg = cfg_for(env, ticks=T)
        r, prey = hunt(env, st, scripted(env, "stationary", {}, cfg), env.iface, 302, cid, 1.0, route,
                       hunter_attack=0.0, ticks=T)
        path = r.events["prey_path"][0].sum(axis=1) / T
        laps = prey.laps_done.numpy()
        refused = r.prey_wall_refused[0] / T
        ok_speed = path >= R["speed_fraction"] * s * env.cfg.world.max_speed
        ok_lap, ok_ref = laps >= 1, refused <= R["max_refused_fraction"]
        rows.append({"speed": s, "share_speed": float(ok_speed.mean()), "share_lap": float(ok_lap.mean()),
                     "share_refused": float(ok_ref.mean()), "path_per_tick_median": float(np.median(path)),
                     "laps_median": float(np.median(laps)), "captures": int(r.captures.sum()),
                     "passed": bool(min(ok_speed.mean(), ok_lap.mean(), ok_ref.mean()) >= R["share"])})
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
    reg.start_marker(EXP, "calibrate", prov)
    env = Env()
    t0 = time.perf_counter()
    R = REGISTERED["route"]
    route = {"gain": R["gain"], "spacing": R["spacing"]}
    with acct.category("calibration"):
        checks = [route_check(env, route)]
        for fb in R["fallbacks"]:
            if checks[-1]["passed"]:
                break
            route = {**route, **fb}
            checks.append(route_check(env, route))
        doc = {"provenance_at_start": prov, "registered": REGISTERED, "route_checks": checks, "route": route}
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
        for st in settings():
            tuned[st["name"]] = {name: tune(env, st, name, ep["e_prey"], route) for name in CONTROLS}
            print(st["name"], {k: round(v["tuned_mean"], 3) for k, v in tuned[st["name"]].items()}, flush=True)
            write("calibration.json", {**doc, "tuned": tuned, "complete": False})
    doc.update(tuned=tuned, complete=True, seconds=time.perf_counter() - t0)
    write("calibration.json", doc)
    print("E_prey", round(ep["e_prey"], 4), "route", route)


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


def equivalence_hunters(env: Env, cfg_n, cfg_h):
    """(label, Task N brain or genome, Task H brain, interface, n) for §4.2."""
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
                         ("e2 ga run00", e2, env.iface), ("generation0 #0", g0, env.iface)):
        out.append((label, g, g, fc, g.spec.n))
    return out


def stage_equivalence(args):
    prov = guard("equivalence")
    reg.start_marker(EXP, "equivalence", prov)
    env = Env()
    t0 = time.perf_counter()
    doc = {"provenance_at_start": prov, "reference_commit": REF_COMMIT}
    # 1. old engine against new
    with acct.category("measure"):  # the equivalence checks
        wt = ROOT.parent / "wormWars-e5ref"
        if not wt.exists():
            subprocess.run(["git", "worktree", "add", "--detach", str(wt), REF_COMMIT], cwd=ROOT, check=True)
        files = {}
        for side, root in (("old", wt), ("new", ROOT)):
            f = OUT / f"reference-{side}.npz"
            subprocess.run([sys.executable, str(ROOT / "scripts" / "e5_0_reference.py"), "--root", str(root),
                            "--out", str(f)], cwd=str(root), check=True)
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
                rh = play(c2, fc, hb, prey_for(env, settings()[0], n, {"gain": 2.0, "spacing": 6.0}, c2), eid,
                          REGISTERED["run_seed"], rule="ghost")
                same = {"count": np.array_equal(rn.score[0].astype(np.int64), rh.captures[0]),
                        "capture_tick": np.array_equal(rn.events["reach_tick"][0], rh.events["capture_tick"][0]),
                        "path": np.array_equal(rn.events["path_length"][0], rh.events["hunter_path"][0])}
                rows[f"{probe}|{label}"] = {**same, "mean": float(rh.captures.mean())}
                if not all(same.values()):
                    bad2.append(f"{probe}|{label}")
        # traces on the first worlds
        tw = eid[:REGISTERED["ids"]["trace_worlds"]]
        for label, tn, th, fc, n in [h for h in hunters if h[0] in ("S-const", "e4s1 M run00", "e2 ga run00")]:
            taps = []
            for kind in ("navigate", "hunt"):
                b = Brain(tn) if isinstance(tn, Genome) else tn
                tap = Tap(b)
                if kind == "navigate":
                    w = World(cn, fc, tap, torch.zeros(len(tw), 1, dtype=torch.long), run_seed=REGISTERED["run_seed"],
                              world_ids=tw)
                else:
                    so = torch.zeros(len(tw), 2, dtype=torch.long)
                    w = HuntWorld(ch, fc, [tap, prey_for(env, settings()[0], n, {"gain": 2.0, "spacing": 6.0})], so,
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


# ---------------------------------------------------------------------------------------------------- the hunters
def neural_sets(env: Env) -> dict:
    """{family: [(label, genome)]}: the 80 frozen neural hunters, or fewer under the plan's first cut."""
    b = env.cfg.brain
    g0n = REGISTERED["generation0"]["genomes"]
    g0 = HN.generation0(env.con, b, g0n, REGISTERED["generation0"]["seed"])
    return {"e4s1": [(k, g) for k, (g, _) in HN.e4s1_champions(env.con, b).items()],
            "L1": [("L1 carrier", HN.l1_carrier(env.con, b))],
            "e2d": [(k, g) for k, (g, _) in HN.e2d_champions(env.con, b).items()],
            "generation0": [(f"generation0 #{i:02d}", g0.select([i])) for i in range(g0n)]}


def neural_iface(env: Env, family: str):
    return (env.gface, 306) if family in ("e4s1", "L1") else (env.iface, 302)


def run_neural(env, st, family, members, e_prey, route, world_ids, chunk, probe="real", prey_body=None):
    """{label: HuntResult rows} for a family, in chunks of `chunk` strains."""
    fc, n = neural_iface(env, family)
    out = {}
    for lo in range(0, len(members), chunk):
        cap().check()
        part = members[lo:lo + chunk]
        g = Genome.cat([m[1] for m in part])
        r, _ = hunt(env, st, Brain(g), fc, n, world_ids, e_prey, route, probe=probe, prey_body=prey_body)
        for i, (label, _) in enumerate(part):
            out[label] = {"captures": r.captures[i], "capture_tick": r.events["capture_tick"][i],
                          "contact": r.events["contact_ticks"][i], "bearing": r.events["bearing"][i],
                          "ledger": r.ledger_rel_error, "pin_push": float(r.pin_push[i].sum())}
    return out


def run_scripted(env, st, e_prey, route, tuned, world_ids):
    fz = env.freeze["tuned"]
    out = {}
    jobs = [(f"{n} tuned", scripted(env, n, tuned[n]["params"], env.cfg)) for n in CONTROLS]
    jobs += [(f"{n} E1-frozen", scripted(env, n, fz[n]["params"], env.cfg)) for n in CONTROLS]
    jobs += [("pursuit", pursuit(env, env.cfg)), ("stationary", scripted(env, "stationary", {}, env.cfg))]
    for label, brain in jobs:
        cap().check()
        r, prey = hunt(env, st, brain, env.iface, 302, world_ids, e_prey, route)
        out[label] = {"captures": r.captures[0], "capture_tick": r.events["capture_tick"][0],
                      "contact": r.events["contact_ticks"][0], "bearing": r.events["bearing"][0],
                      "ledger": r.ledger_rel_error, "pin_push": float(r.pin_push[0].sum()),
                      "prey_path_per_tick": (r.events["prey_path"][0].sum(axis=1) / r.ticks).tolist(),
                      "prey_wall_refused": int(r.prey_wall_refused.sum())}
    if st["name"] == "H1-bite":
        r, _ = hunt(env, st, pursuit(env, env.cfg), env.iface, 302, world_ids, e_prey, route, hunter_attack=0.0)
        out["pursuit attack-disabled"] = {"captures": r.captures[0], "damage": float(r.events["damage"].sum()),
                                          "ledger": r.ledger_rel_error}
    return out


# ---------------------------------------------------------------------------------------------------------- bench
def stage_bench(args):
    env = Env()
    cal = read("calibration.json")
    route, e_prey = cal["route"], cal["e_prey"]["e_prey"]
    st = next(s for s in settings() if s["name"] == "H2-0.5")
    bid = ids("equivalence")  # the intended batch (512 worlds; no claim rests on these worlds)
    rows = {}
    with acct.category("measure"):  # the benchmark
        for label, run in (("scripted", lambda: hunt(env, st, pursuit(env, env.cfg), env.iface, 302, bid, e_prey, route)),):
            t = time.perf_counter()
            run()
            rows[label] = (time.perf_counter() - t) / len(bid)
        sets = neural_sets(env)
        for fam, chunk in (("e4s1", 16), ("e2d", 16)):
            t = time.perf_counter()
            run_neural(env, st, fam, sets[fam][:chunk], e_prey, route, bid, chunk)
            rows[f"neural {fam} x{chunk}"] = (time.perf_counter() - t) / (len(bid) * chunk)
    per_neural = max(v for k, v in rows.items() if k.startswith("neural"))
    per_scripted = rows["scripted"]
    S, W = len(settings()), REGISTERED["ids"]["evaluation"][1]
    n_neural = sum(len(v) for v in sets.values())
    main_h = (n_neural * per_neural + 11 * per_scripted) * S * W / 3600
    fixed_h = n_neural * 3 * len(REGISTERED["probe_settings"]) * W * per_neural / 3600
    spent = cap().spent_hours()
    doc = {"seconds_per_episode": rows, "settings": S, "worlds": W, "neural_hunters": n_neural,
           "projected_hours": {"main_pass": main_h, "fixed_probes": fixed_h, "spent_before": spent,
                               "total_before_qualification_probes": main_h + fixed_h + spent},
           "cap_hours": REGISTERED["cap_hours"], "cuts": []}
    total = main_h + fixed_h + spent
    # the plan's cuts, in order, until it fits
    g0 = REGISTERED["generation0"]["genomes"]
    cuts = []
    est = {"g0": g0, "probes_at": 2, "speeds": 10, "worlds": W}

    def project(e):
        n_n = n_neural - g0 + e["g0"]
        s = S - 10 + e["speeds"]
        m = (n_n * per_neural + 11 * per_scripted) * s * e["worlds"] / 3600
        f = n_n * (1 * len(REGISTERED["probe_settings"]) + 2 * e["probes_at"]) * e["worlds"] * per_neural / 3600
        return m + f + spent
    steps = [("generation 0 down to 8 genomes", {"g0": 8}), ("mean and mirrored probes at H1-bite only", {"probes_at": 1}),
             ("H2's speeds thinned to 0.1, 0.3, 0.5, 0.7, 1.0", {"speeds": 5}), ("evaluation worlds down to 256", {"worlds": 256})]
    total = project(est)
    for label, change in steps:
        if total <= REGISTERED["cap_hours"]:
            break
        est.update(change)
        cuts.append(label)
        total = project(est)
    doc.update(cuts=cuts, projected_after_cuts=total, fits=total <= REGISTERED["cap_hours"], sizes=est)
    write("bench.json", doc)
    print(json.dumps({k: doc[k] for k in ("seconds_per_episode", "projected_hours", "cuts", "projected_after_cuts",
                                          "fits")}, indent=1))
    if not doc["fits"]:
        raise SystemExit("even with every cut E5-0 does not fit its cap: it stops before evaluating")


def sized_settings(bench: dict) -> list[dict]:
    S = settings()
    if bench["sizes"]["speeds"] == 5:
        keep = {"H2-0.1", "H2-0.3", "H2-0.5", "H2-0.7", "H2-1"}
        S = [s for s in S if not s["name"].startswith("H2-") or s["name"] in keep]
    return S


# ------------------------------------------------------------------------------------------------------- evaluate
def _save_setting(name: str, rows: dict) -> None:
    d = OUT / "evaluation"
    d.mkdir(parents=True, exist_ok=True)
    arrays = {}
    for label, r in rows.items():
        for k, v in r.items():
            if isinstance(v, np.ndarray):
                arrays[f"{label}|{k}"] = v
    np.savez_compressed(d / f"{name}.npz", **arrays)
    meta = {label: {k: v for k, v in r.items() if not isinstance(v, np.ndarray)} for label, r in rows.items()}
    reg.write_json(d / f"{name}.json", meta)


def stage_evaluate(args):
    prov = reg.provenance(GUARDED)
    if not args.resume:
        guard("evaluate")
        reg.start_marker(EXP, "evaluate", prov)
    env = Env()
    eq = read("equivalence.json")
    if not eq["passed"]:
        raise SystemExit("the equivalence checks did not pass")
    cal, bench = read("calibration.json"), read("bench.json")
    if not bench["fits"]:
        raise SystemExit("bench says E5-0 does not fit its cap")
    route, e_prey = cal["route"], cal["e_prey"]["e_prey"]
    W = bench["sizes"]["worlds"]
    eid = ids("evaluation")[:W]
    sets = neural_sets(env)
    if bench["sizes"]["g0"] < len(sets["generation0"]):
        sets["generation0"] = sets["generation0"][:bench["sizes"]["g0"]]
    done = set()
    d = OUT / "evaluation"
    if d.exists():
        done = {p.stem for p in d.glob("*.json")}
    attempts = (read("evaluation-progress.json")["attempts"] if (EXP / "evaluation-progress.json").exists() else [])
    attempts.append({"provenance": prov, "resume": bool(args.resume), "skipped_done": sorted(done)})
    t0 = time.perf_counter()
    with acct.category("final"):
        for st in sized_settings(bench):
            if st["name"] in done:
                continue
            rows = run_scripted(env, st, e_prey, route, cal["tuned"][st["name"]], eid)
            for fam, members in sets.items():
                rows.update(run_neural(env, st, fam, members, e_prey, route, eid, chunk=16))
            _save_setting(st["name"], rows)
            write("evaluation-progress.json", {"attempts": attempts, "completed": sorted(done | {st["name"]})})
            done.add(st["name"])
            print(st["name"], "done", round(time.perf_counter() - t0), "s", flush=True)
    write("evaluation-progress.json", {"attempts": attempts, "completed": sorted(done), "complete": True})


# ---------------------------------------------------------------------------------------------------------- reading
class Boot:
    """Paired percentile bootstrap over the evaluation worlds, one resample set for everything (§6)."""

    def __init__(self, n_worlds: int):
        B = REGISTERED["bootstrap"]
        self.idx = np.random.default_rng(B["seed"]).integers(0, n_worlds, size=(B["resamples"], n_worlds))
        self.lo, self.hi = B["lower"], B["upper"]

    def means(self, x: np.ndarray) -> np.ndarray:
        return np.asarray(x, dtype=np.float64)[self.idx].mean(axis=1)

    def bounds(self, r: np.ndarray) -> tuple[float, float]:
        r = r[np.isfinite(r)]
        if r.size == 0:
            return float("nan"), float("nan")
        return float(np.percentile(r, self.lo)), float(np.percentile(r, self.hi))


def criteria(boot: Boot, counts: np.ndarray, best_r: np.ndarray) -> dict:
    R = REGISTERED["rules"]
    rel_lo, rel_hi = boot.bounds(boot.means(counts >= 1))
    adv_lo, adv_hi = boot.bounds(boot.means(counts) - best_r)
    return {"mean": float(np.mean(counts)), "share_at_least_1": float(np.mean(counts >= 1)),
            "reliability": [rel_lo, rel_hi], "advantage_over_best_baseline": [adv_lo, adv_hi],
            "capture_criteria": bool(rel_lo >= R["reliability"] and adv_lo > R["margin"]),
            "fails_reliability": bool(rel_hi < R["reliability"]), "fails_advantage": bool(adv_hi < R["margin"])}


def load_setting(name: str):
    d = OUT / "evaluation"
    z = np.load(d / f"{name}.npz", allow_pickle=False)
    counts = {k.split("|")[0]: z[k] for k in z.files if k.endswith("|captures")}
    meta = json.loads((d / f"{name}.json").read_text(encoding="utf-8"))
    return counts, meta


def baselines_r(boot: Boot, counts: dict) -> tuple[np.ndarray, dict]:
    names = {"stationary": "stationary", "constant": "constant tuned", "random-walk": "random-walk tuned",
             "wall-follower": "wall-follower tuned"}
    rs = {k: boot.means(counts[v]) for k, v in names.items()}
    return np.max(np.stack(list(rs.values())), axis=0), {k: float(np.mean(counts[v])) for k, v in names.items()}


# ------------------------------------------------------------------------------------------------------------ probes
def stage_probe(args):
    prov = reg.provenance(GUARDED)
    if not args.resume:
        guard("probe")
        reg.start_marker(EXP, "probe", prov)
    env = Env()
    cal, bench = read("calibration.json"), read("bench.json")
    route, e_prey = cal["route"], cal["e_prey"]["e_prey"]
    W = bench["sizes"]["worlds"]
    eid = ids("evaluation")[:W]
    sets = neural_sets(env)
    if bench["sizes"]["g0"] < len(sets["generation0"]):
        sets["generation0"] = sets["generation0"][:bench["sizes"]["g0"]]
    d = OUT / "probes"
    d.mkdir(parents=True, exist_ok=True)
    by_name = {s["name"]: s for s in sized_settings(bench)}
    with acct.category("probe"):
        # the fixed probes
        for sname in REGISTERED["probe_settings"]:
            kinds = [("body", "real", False)]
            if bench["sizes"]["probes_at"] == 2 or sname == "H1-bite":
                kinds += [("mean", "mean", None), ("mirrored", "mirrored", None)]
            for kind, probe, body in kinds:
                f = d / f"{sname}__{kind}.npz"
                if f.exists():
                    continue
                rows = {}
                for fam, members in sets.items():
                    rows.update(run_neural(env, by_name[sname], fam, members, e_prey, route, eid, 16, probe=probe,
                                           prey_body=body))
                np.savez_compressed(f, **{k: v["captures"] for k, v in rows.items()})
        # the qualification probes, staged
        boot = Boot(W)
        order = ["e4s1", "L1", "e2d", "generation0"]
        todo = []
        for st in sized_settings(bench):
            if st["name"] == "H1-ghost":  # the bridge to Task N: no rule is read there
                continue
            counts, _ = load_setting(st["name"])
            best_r, _ = baselines_r(boot, counts)
            for fam in order:
                for label, g in sets[fam]:
                    if criteria(boot, counts[label], best_r)["capture_criteria"]:
                        todo.append((fam, st["name"], label, g))
        todo.sort(key=lambda t: order.index(t[0]))
        untested = []
        groups = {}  # in the staged order: (family, setting) -> its hunters still to probe, run 16 at a time
        for fam, sname, label, g in todo:
            if not (d / f"{sname}__constant__{label}.npz").exists():
                groups.setdefault((fam, sname), []).append((label, g))
        for (fam, sname), members in groups.items():
            for lo in range(0, len(members), 16):
                part = members[lo:lo + 16]
                try:
                    r = run_neural(env, by_name[sname], fam, part, e_prey, route, eid, 16, probe="constant")
                except reg.CapReached:
                    untested += [f"{sname}|{label}" for label, _ in part]
                    continue
                for label, _ in part:
                    np.savez_compressed(d / f"{sname}__constant__{label}.npz", captures=r[label]["captures"])
    reg.write_json(d / "probes-progress.json", {"provenance": prov, "qualification_probes": len(todo),
                                               "untested_under_the_cap": untested})


def stage_read(args):
    bench = read("bench.json")
    W = bench["sizes"]["worlds"]
    boot = Boot(W)
    R = REGISTERED["rules"]
    out = {"rules": R, "bootstrap": REGISTERED["bootstrap"], "settings": {}}
    pdir = OUT / "probes"
    for st in sized_settings(bench):
        name = st["name"]
        counts, meta = load_setting(name)
        best_r, base_means = baselines_r(boot, counts)
        pc = counts["S-const tuned"]
        pc_c = criteria(boot, pc, best_r)
        row = {"setting": st, "baseline_means": base_means, "positive_control": pc_c,
               "solvable": pc_c["capture_criteria"],
               "pursuit_mean": float(np.mean(counts["pursuit"])),
               "e1_frozen_means": {n: float(np.mean(counts[f"{n} E1-frozen"])) for n in CONTROLS},
               "pin_push_total": sum(v.get("pin_push", 0.0) for v in meta.values()),
               "ledger_rel_error_max": max(v.get("ledger", 0.0) for v in meta.values())}
        if row["solvable"]:
            pr = boot.means(pc)
            ratio = np.where(pr > 0, best_r / np.where(pr > 0, pr, 1.0), np.nan)
            lo, hi = boot.bounds(ratio)
            point = float(max(base_means.values()) / pc.mean()) if pc.mean() > 0 else float("nan")
            row["too_easy"] = {"ratio": point, "bounds": [lo, hi], "flag": bool(point >= R["flag"]),
                               "reading": ("too easy" if lo >= R["too_easy"] else "not too easy" if hi < R["too_easy"]
                                           else "inconclusive")}
        if name == "H1-bite":
            ad = meta.get("pursuit attack-disabled", {})
            row["attack_disabled"] = {"captures": int(np.sum(counts.get("pursuit attack-disabled", 0))),
                                      "damage": ad.get("damage")}
        hunters = {}
        for label, c in counts.items():
            if label in ("pursuit attack-disabled",) or any(label.startswith(n) for n in (*CONTROLS, "pursuit",
                                                                                         "stationary")):
                continue
            h = criteria(boot, c, best_r)
            f = pdir / f"{name}__constant__{label}.npz"
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
    # falls off, per speed series
    series = {"H2": [s["name"] for s in sized_settings(bench) if s["name"].startswith("H2-")],
              "H2b walk": [s["name"] for s in sized_settings(bench) if s["name"].startswith("H2b-walk")],
              "H2b wall": [s["name"] for s in sized_settings(bench) if s["name"].startswith("H2b-wall")]}
    falls = {}
    labels = list(out["settings"]["H1-bite"]["hunters"])
    for label in labels:
        falls[label] = {}
        for sname, names in series.items():
            hs = [out["settings"][n]["hunters"][label] for n in names]
            q = [h["reading"] for h in hs]
            first = next((n for n, x in zip(names, q) if x != "qualifies"), None)
            first_cc = next((n for n, h in zip(names, hs) if not h["capture_criteria"]), None)
            falls[label][sname] = {"first_not_qualifying": first, "first_capture_criteria_not_met": first_cc,
                                   "readings": dict(zip(names, q))}
    out["falls_off"] = falls
    # readings without a threshold
    g, r = load_setting("H1-ghost")[0], load_setting("H1-reach")[0]
    out["ghost_minus_reach"] = {k: float(np.mean(g[k]) - np.mean(r[k])) for k in g if k in r}
    probes = {}
    for sname in REGISTERED["probe_settings"]:
        counts, _ = load_setting(sname)
        for kind in ("body", "mean", "mirrored"):
            f = pdir / f"{sname}__{kind}.npz"
            if f.exists():
                z = np.load(f, allow_pickle=False)
                probes[f"{sname}|{kind}"] = {k: float(np.mean(counts[k]) - np.mean(z[k])) for k in z.files}
    out["intact_minus_probe"] = probes
    write("reading.json", out)
    print("solvable:", {n: v["solvable"] for n, v in out["settings"].items()})


def main():
    global EXP, OUT, SMOKE
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("stage", choices=["calibrate", "equivalence", "bench", "evaluate", "probe", "read"])
    ap.add_argument("--smoke", action="store_true", help="tiny sizes, scratch folder, no git checks")
    ap.add_argument("--resume", action="store_true", help="continue a started evaluate or probe stage")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
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
        for f in EXP.glob("*-started.json"):
            if args.stage not in ("evaluate", "probe") or not args.resume:
                if f.name.startswith(args.stage):
                    f.unlink()
    torch.set_num_threads(max(1, os.cpu_count() or 1))
    {"calibrate": stage_calibrate, "equivalence": stage_equivalence, "bench": stage_bench,
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
