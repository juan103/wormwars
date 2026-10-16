"""03mc: the confirmatory test of 03m's leads on P4, as the bound pre-registration fixes it
(`experiments/03mc-p4-confirm/PREREGISTRATION.md`; design v2.2, `DESIGN.md`).

    python scripts/p4mc.py build                                   # CPU: the freshness audit, then the 640 graphs
    python scripts/p4mc.py check --device cuda --owner-word "..."  # the pre-run check on old inputs
    python scripts/p4mc.py run --device cuda --owner-word "..."    # every unit, in the registered order; resumable
    python scripts/p4mc.py report                                  # the registered statistics, from the records
    add --smoke for toy sizes on the CPU in runs/p4mc-smoke (its own salt, seeds and graphs; never results)

**Before any formal stage:** the pre-registration's bound text survives as a prefix of the current file (amendments
are appended); the code (`wormwars`, `scripts`, `configs`, `requirements.txt`) is unchanged since the bound commit;
the registered GPU and environment; a clean tree, pushed. The bound commit is read from `bound.json`, committed after
binding (a commit cannot name itself).

**The run** measures units in the registered order (DESIGN §5): N2's batch 0, Q-C's permutations, Q-B's batches, the
ensembles interleaved, then the secondaries. Each unit is written as it completes: its summary into
`measurements.json` (committed), its per-genome arrays into `runs/p4mc/arrays/` (local; their sha256 recorded). The
cap is checked before every unit. A resume skips completed units and refuses changed code, environment or inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.brain import BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.deletion import delete_neurons  # noqa: E402
from wormwars.exp03 import mc  # noqa: E402
from wormwars.exp03 import twin  # noqa: E402
from wormwars.exp03.measures import genome_seed  # noqa: E402


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


X = _load("exp03_for_p4mc", "exp03.py")
EQ = _load("p4mc_equivalence_for_p4mc", "p4mc_equivalence.py")

EXP_FORMAL = ROOT / "experiments" / "03mc-p4-confirm"
OUT_FORMAL = ROOT / "runs" / "p4mc"
SMOKE_DIR = ROOT / "runs" / "p4mc-smoke"
PREREG = "experiments/03mc-p4-confirm/PREREGISTRATION.md"
CODE = ["wormwars", "scripts", "configs", "requirements.txt"]
TURN_PAIRS = ("RMDD", "RMDV", "SMDD", "SMDV")
ORDER = ("SH-route", "SH-class", "SH-mirror", "SH-recip", "SH")  # the ensembles' interleaving (DESIGN §5)
CONDITIONS = ("RIA", "AIY", "both")
REGISTERED = {
    "genomes": 2048, "rows": 2, "follow": 300, "every": 10, "extra": [5], "settle_window": 10,
    "salt": "03mc:", "graphs_per_ensemble": 128, "qb_batches": 32, "permutation_seeds": [1000, 1255],
    "factorial_permutations": 32, "null_deletion_graphs_per_ensemble": 32, "cap_hours": 10.0,
    "tick": 30, "secondary_ticks": [10, 50, 100, 300], "denominator_floor": 1e-4, "start_floor": 1e-3,
    "remaining_fraction": 0.10, "settle_tolerance": 1e-4, "min_graphs": 120, "min_permutations": 240,
    "margins": {"cut": mc.MARGIN_CUT, "P4": mc.MARGIN_P4}, "bootstrap": {"resamples": 10_000, "genomes_seed": 20261016,
                                                                         "permutations_seed": 20261017,
                                                                         "graphs_seed": 20261018},
    "controls": {"RIA": ["AIB", "AVJ", "RIM", "AVH"], "AIY": ["AWB", "RIF", "RIP", "RIV"]},
}
SMOKE_SIZES = {"genomes": 8, "graphs_per_ensemble": 2, "qb_batches": 2, "permutation_seeds": [9000, 9002],
               "factorial_permutations": 2, "null_deletion_graphs_per_ensemble": 1, "pairs": 3, "cap_hours": 1.0,
               "min_graphs": 2, "min_permutations": 2}
SMOKE = False


def R(key):
    """A registered size, or its smoke size."""
    return SMOKE_SIZES[key] if SMOKE and key in SMOKE_SIZES else REGISTERED[key]


def exp_dir() -> Path:
    return SMOKE_DIR / "record" if SMOKE else EXP_FORMAL


def out_dir() -> Path:
    return SMOKE_DIR if SMOKE else OUT_FORMAL


def use_smoke(on: bool) -> None:
    global SMOKE
    SMOKE = on
    X.use_instance("03mc-smoke" if on else "03mc")


use_smoke(False)


# ----------------------------------------------------------------------------- provenance and guards

def bound() -> dict:
    """`bound.json`: the binding commit, and the formal code's commit if an amendment moved it (as E4-D's
    Amendment 1 did); the code is checked against the latter."""
    path = EXP_FORMAL / "bound.json"
    if not path.exists():
        raise SystemExit("bound.json is missing: the pre-registration is not bound yet")
    b = json.loads(path.read_text(encoding="utf-8"))
    return {"commit": b["commit"], "code_commit": b.get("code_commit") or b["commit"]}


def bound_commit() -> str:
    return bound()["commit"]


def prereg_at(commit: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{PREREG}"], cwd=ROOT)


def _lf(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def prereg_append_only(bound: bytes, now: bytes) -> None:
    """The bound text, then only new lines: an addition must start on a line of its own, so extending the bound
    text's last line is refused too (a weakness of the prefix check E4-D's runner used; D289)."""
    b, n = _lf(bound).rstrip(b"\n"), _lf(now)
    if not (n.rstrip(b"\n") == b or n.startswith(b + b"\n")):
        raise SystemExit("the pre-registration's bound text was changed, not only appended to: refusing")


def guards(args, prov: dict) -> str | None:
    """Every formal stage: the bound text kept, the code unchanged since binding, the registered GPU and
    environment, a clean tree, pushed. Returns the bound commit (None in smoke runs)."""
    if SMOKE:
        return None
    bd = bound()
    b = bd["commit"]
    now = (ROOT / PREREG).read_bytes()
    for c in {b, bd["code_commit"]}:
        subprocess.run(["git", "merge-base", "--is-ancestor", c, "HEAD"], cwd=ROOT, check=True)
        prereg_append_only(prereg_at(c), now)  # the bound text, and any amendment in force, survive
    reg.require_same_code(bd["code_commit"], CODE)
    if args.command != "build":
        reg.require_formal(args.device, prov)
    elif prov["dirty"]:
        raise SystemExit("uncommitted changes in the guarded files: commit first")
    return b


def provenance() -> dict:
    return reg.provenance([*CODE, PREREG, "experiments/03mc-p4-confirm/bound.json"])


def owner_word(args) -> str | None:
    if SMOKE:
        return None
    if not args.owner_word or not args.owner_word.strip():
        raise SystemExit("formal GPU stages need --owner-word: the owner's words and their date")
    return args.owner_word.strip()


def cap_clock() -> reg.CapClock:
    comp = out_dir() / "compute"
    if comp.exists():
        acct.write_aggregate(comp, out_dir() / "compute.json")
    return reg.CapClock(R("cap_hours"), out_dir() / "compute.json")


# ----------------------------------------------------------------------------- the build (CPU)

def old_names() -> dict:
    """Every graph name of 03, 03r and 03m, by salt, for the freshness audit (DESIGN §3)."""
    out = {}
    for salt, inst in (("", "03"), ("03r:", "03r")):
        c = X.INSTANCES[inst]
        rec = json.loads((ROOT / "experiments" / c["exp"] / "ensembles.json").read_text(encoding="utf-8"))["graphs"]
        out[salt] = [r["name"] for r in rec] + list(c["real"])
    out[""] += [f"pilotSH{s}" for s in X.PILOT_SEEDS] + [f"N2perm{s}" for s in range(100, 164)]
    return out


def old_permutation_seeds() -> list[int]:
    """03 (0, the default, and 1-3), 03r (4-6, and every graph's secondary `_gseed(name) + 2`), 03m (100-163)."""
    seeds = [0, 1, 2, 3, 4, 5, 6, *range(100, 164)]
    for n in old_names()["03r:"]:
        seeds.append(genome_seed(n, "03r:") + 2)
    return seeds


def planned_names(ens_names: dict | None = None) -> dict:
    c = X.INSTANCES["03mc-smoke" if SMOKE else "03mc"]
    if ens_names is None:
        ens_names = {e: [f"{e}-{c['seed_base'][e] + i}" for i in range(c["n"][e])] for e in mc.ENSEMBLES}
    names = ["N2", *[f"N2#{b}" for b in range(1, R("qb_batches"))], *[n for e in mc.ENSEMBLES for n in ens_names[e]]]
    return {c["genome_salt"]: names}


def permutation_seeds() -> list[int]:
    lo, hi = R("permutation_seeds")
    return list(range(lo, hi + 1))


def smoke_names_as_old() -> dict:
    """The formal audit also keeps clear of the smoke streams."""
    c = X.INSTANCES["03mc-smoke"]
    names = ["N2", *[f"N2#{b}" for b in range(1, SMOKE_SIZES["qb_batches"])],
             *[f"{e}-{c['seed_base'][e] + i}" for e in mc.ENSEMBLES for i in range(c["n"][e])]]
    return {c["genome_salt"]: names}


def audit(ens_names: dict | None = None) -> dict:
    old = old_names()
    old_perm = old_permutation_seeds()
    if not SMOKE:
        old.update(smoke_names_as_old())
        old_perm += list(range(SMOKE_SIZES["permutation_seeds"][0], SMOKE_SIZES["permutation_seeds"][1] + 1))
    return mc.freshness_audit(planned_names(ens_names), old, permutation_seeds(), old_perm)


def content_hashes(names) -> dict:
    return {n: X._sha_content(X.GRAPHS / f"{n}.npz") for n in names}


def old_content_hashes() -> set:
    out = set()
    for inst in ("03", "03r"):
        p = ROOT / "experiments" / X.INSTANCES[inst]["exp"] / "graphs_content_manifest.json"
        out |= set(json.loads(p.read_text(encoding="utf-8"))["graphs"].values())
    return out


def ensemble_names() -> dict:
    rec = json.loads((exp_dir() / "ensembles.json").read_text(encoding="utf-8"))["graphs"]
    by = {e: [] for e in mc.ENSEMBLES}
    for r in rec:
        by[r["kind"]].append(r["name"])
    return by


def cmd_build(args):
    prov = provenance()
    b = guards(args, prov)
    exp = exp_dir()
    if (exp / "build.json").exists():
        raise SystemExit("build.json exists: the build has run and is not rerun")
    before = audit()
    if not before["ok"]:
        reg.write_json(exp / "build.json", {"outcome": "refused: the planned seeds are not fresh", "audit": before})
        raise SystemExit(f"the freshness audit failed before the build: {before}")
    cap = cap_clock()
    cap.check()  # the build is one unit (DESIGN §7)
    cmd = [sys.executable, str(ROOT / "scripts" / "exp03.py"), "build", "--instance",
           "03mc-smoke" if SMOKE else "03mc", "--workers", str(args.workers)]
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=ROOT, check=True)  # exp03's own build records its compute in runs/p4mc*/compute
    names = ensemble_names()
    rec = json.loads((exp / "ensembles.json").read_text(encoding="utf-8"))
    flat = [n for e in mc.ENSEMBLES for n in names[e]]
    hashes = content_hashes(flat)
    reg.write_json(exp / "graphs_content_manifest.json", {"what": "each graph's array content (exp03._sha_content)",
                                                          "graphs": hashes})
    content = mc.content_check(hashes, old_content_hashes())
    after = audit(names)
    validation = rec["validation"]
    valid = all(rec["plateau"][e]["passes"] for e in mc.ENSEMBLES) and all(
        validation[e]["acceptance_min"] >= 0.05 and not validation[e]["over_ceiling"] for e in mc.ENSEMBLES)
    ok = content["ok"] and after["ok"] and valid
    reg.write_json(exp / "build.json", {
        "outcome": "completed" if ok else "refused: see the failed checks", "bound_commit": b, "provenance": prov,
        "audit_before": before, "audit_after": after, "content": content, "validation_rules_pass": valid,
        "graphs": {e: len(v) for e, v in names.items()}, "substituted": {e: validation[e]["substituted"] for e in mc.ENSEMBLES},
        "seconds": time.perf_counter() - t0})
    if not ok:
        raise SystemExit("the build's checks failed: nothing is measured (DESIGN §3); see build.json")
    print({e: len(v) for e, v in names.items()}, "audit ok, content ok, validation ok")


def require_build() -> dict:
    p = exp_dir() / "build.json"
    if not p.exists():
        raise SystemExit("no build.json: run the build first")
    b = json.loads(p.read_text(encoding="utf-8"))
    if b.get("outcome") != "completed":
        raise SystemExit(f"the build did not complete: {b.get('outcome')}")
    return b


# ----------------------------------------------------------------------------- the pre-run check

def cmd_check(args):
    prov = provenance()
    b = guards(args, prov)
    word = owner_word(args)
    require_build()
    if not SMOKE:
        reg.start_marker(out_dir() / "markers", "check", {**prov, "owner_word": word, "bound_commit": b})
    cap = cap_clock()
    cap.check()
    argv = ["--set", "check", "--device", "cpu" if SMOKE else args.device, "--record", "prerun-check.json"]
    EQ.main(argv + (["--smoke"] if SMOKE else []))


def require_check() -> None:
    if SMOKE:
        return
    p = EXP_FORMAL / "prerun-check.json"
    if not p.exists() or not json.loads(p.read_text(encoding="utf-8")).get("passed"):
        raise SystemExit("the pre-run check has not passed: nothing formal runs (DESIGN §5)")


# ----------------------------------------------------------------------------- units

def setup(device):
    con = load_connectome()
    bank = json.loads(X.PILOT.read_text(encoding="utf-8"))["bank"]
    remap_sets = json.loads(X.INPUT_FILES["remaps.json"].read_text(encoding="utf-8"))["sets"]
    return con, bank, X.grid.interface_for(con, "M0", remap_sets)


def pair_index(con) -> dict:
    names = list(con.names)
    idx = {n: i for i, n in enumerate(names)}
    return {n[:-1]: [i, idx[n[:-1] + "R"]] for n, i in idx.items() if n.endswith("L") and n[:-1] + "R" in idx}


def screen_pairs(con) -> list[str]:
    """Every bilateral pair that touches no turn read-out neuron, in name order (03m's 95)."""
    return sorted(k for k in pair_index(con) if k not in TURN_PAIRS)


def plan(con, names: dict) -> list[dict]:
    """The registered order (DESIGN §5). Every unit: id, kind, the graph and genome stream, the change."""
    u = [{"id": "N2/long", "kind": "long", "graph": "N2", "seed_name": "N2", "cfg": "N2", "primary": True},
         {"id": "N2/gaps", "kind": "gaps", "graph": "N2", "seed_name": "N2", "cfg": "N2", "primary": True}]
    for s in permutation_seeds():
        u.append({"id": f"perm/{s}", "kind": "std", "graph": "N2", "seed_name": "N2", "cfg": f"N2perm{s}",
                  "primary": True})
    for b in range(R("qb_batches")):
        sn = "N2" if b == 0 else f"N2#{b}"
        for cond in ("intact", *CONDITIONS):
            u.append({"id": f"qb/{b}/{cond}", "kind": "std", "graph": "N2", "seed_name": sn, "cfg": "N2",
                      "delete": None if cond == "intact" else cond, "primary": True})
            if b == 0 and cond == "intact":
                u.append({"id": "qb/0/empty", "kind": "std", "graph": "N2", "seed_name": sn, "cfg": "N2",
                          "delete": "empty", "primary": True})
    n_per = max(len(v) for v in names.values())
    for i in range(n_per):
        for e in ORDER:
            if i < len(names[e]):
                g = names[e][i]
                u += [{"id": f"graph/{g}/long", "kind": "long", "graph": g, "seed_name": g, "cfg": g, "primary": True},
                      {"id": f"graph/{g}/gaps", "kind": "gaps", "graph": g, "seed_name": g, "cfg": g, "primary": True}]
    pairs = [k for k in screen_pairs(con) if k not in ("RIA", "AIY")]
    if SMOKE:
        pairs = pairs[:SMOKE_SIZES["pairs"]]
    for k in pairs:
        u.append({"id": f"pair/{k}", "kind": "std", "graph": "N2", "seed_name": "N2", "cfg": "N2", "delete": k,
                  "primary": False})
    for s in permutation_seeds()[:R("factorial_permutations")]:
        for cond in CONDITIONS:
            u.append({"id": f"fact/{s}/{cond}", "kind": "std", "graph": "N2", "seed_name": "N2", "cfg": f"N2perm{s}",
                      "delete": cond, "primary": False})
    k_null = R("null_deletion_graphs_per_ensemble")
    for i in range(k_null):
        for e in ORDER:
            if i < len(names[e]):
                g = names[e][i]
                for cond in CONDITIONS:
                    u.append({"id": f"null/{g}/{cond}", "kind": "std", "graph": g, "seed_name": g, "cfg": g,
                              "delete": cond, "primary": False})
    return u


def deletion_lists(con, which) -> list[int]:
    if which in (None, "empty"):
        return []
    pi = pair_index(con)
    if which == "both":
        return pi["RIA"] + pi["AIY"]
    return list(pi[which])


def genomes_for(con, unit: dict, device, n: int, graphs: dict):
    if unit["graph"] not in graphs:
        graphs[unit["graph"]] = X._load_graph(con, unit["graph"])
    graph = graphs[unit["graph"]]
    spec = BrainSpec.from_connectome(graph, device=device)
    cfg = X.grid.brain_config_for_graph(X.grid.task_config(Config(), "T1"), unit["cfg"])
    gen = torch.Generator(device=device).manual_seed(X._gseed(unit["seed_name"]) + 1)
    g = Genome.random(spec, cfg.brain, n, generator=gen, device=device)
    if unit["kind"] == "gaps":
        g = g.with_params(g=torch.zeros_like(g.g))
    if unit.get("delete") is not None:
        g = delete_neurons(g, [deletion_lists(con, unit["delete"])] * g.n_strains)
    return g, cfg


def f64abs(x) -> np.ndarray:
    return np.abs(np.asarray(x, dtype=np.float64))


def terms(final, steady, floor) -> dict:
    num, den = float(f64abs(final).mean()), float(f64abs(steady).mean())
    valid = bool(math.isfinite(num) and math.isfinite(den) and den >= floor)
    return {"numerator": num, "denominator": den, "P4": num / den if valid else None, "valid": valid}


def summarise(unit: dict, h: dict) -> tuple[dict, dict]:
    """A unit's summary (committed) and its per-genome arrays (local)."""
    floor = REGISTERED["denominator_floor"]
    rec = {"id": unit["id"], **terms(h["raw_turn"]["final"], h["raw_turn"]["steady_contrast"], floor)}
    arrays = {"final": np.asarray(h["raw_turn"]["final"], np.float32),
              "steady": np.asarray(h["raw_turn"]["steady_contrast"], np.float32)}
    if unit["kind"] == "long":
        pre = terms(h["pre_turn"]["final"], h["pre_turn"]["steady_contrast"], floor)
        rec.update({f"pre_{k}": v for k, v in pre.items()})
        d = f64abs(h["diff"])
        mad = d.mean(axis=1)
        rec["ticks"] = list(h["ticks"])
        rec["mean_abs_difference"] = mad.tolist()
        share_ok = rec["valid"] and mad[0] >= floor
        rec["share"] = {str(t): (float(mad[h["ticks"].index(t)] / mad[0]) if share_ok else None)
                        for t in [REGISTERED["tick"], *REGISTERED["secondary_ticks"]]}
        start, end = d[0], d[-1]
        eligible = start >= REGISTERED["start_floor"]
        remaining = eligible & (end > REGISTERED["remaining_fraction"] * start)
        settled = np.asarray(h["end_state_range"]) < REGISTERED["settle_tolerance"]
        rec.update({"eligible": int(eligible.sum()), "remaining": int(remaining.sum()), "settled": int(settled.sum()),
                    "settled_and_remaining": int((settled & remaining).sum()),
                    "slope_hold": float(np.mean(h["slope_hold"])), "slope_ramp": float(np.mean(h["slope_ramp"]))})
        arrays.update({"pre_final": np.asarray(h["pre_turn"]["final"], np.float32),
                       "pre_steady": np.asarray(h["pre_turn"]["steady_contrast"], np.float32),
                       "diff": np.asarray(h["diff"], np.float32),
                       "end_state_range": np.asarray(h["end_state_range"], np.float32)})
    return rec, arrays


def measure(con, bank, iface, unit: dict, device, n: int, graphs: dict) -> tuple[dict, dict]:
    g, cfg = genomes_for(con, unit, device, n, graphs)
    if unit["kind"] == "long":
        h = twin.history(g, cfg, iface, bank, follow=REGISTERED["follow"], every=REGISTERED["every"],
                         extra=tuple(REGISTERED["extra"]), window=REGISTERED["settle_window"])
    else:
        h = twin.history(g, cfg, iface, bank, follow=5)
    return summarise(unit, h)


def safe(uid: str) -> str:
    return uid.replace("/", "__").replace("#", "_")


def save_arrays(path: Path, arrays: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    EQ.P.replace(tmp, path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_arrays(uid: str) -> dict:
    with np.load(out_dir() / "arrays" / f"{safe(uid)}.npz", allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def inputs_digest(names: dict) -> dict:
    """What a resume must find unchanged: the graph manifests, the stimulus bank, the remaps and the plan."""
    files = [exp_dir() / "ensembles.json", exp_dir() / "graphs_manifest.json", exp_dir() / "graphs_content_manifest.json",
             X.PILOT, X.INPUT_FILES["remaps.json"], ROOT / "configs" / "interface.yaml"]
    return {str(p.relative_to(ROOT)): reg.file_sha256(p) for p in files if p.exists()}


def check_resume(doc: dict, prov: dict, digest: dict, units: list) -> None:
    """A resume continues the first attempt only: the same code and environment (formal), the same inputs, the
    same plan."""
    first = doc["attempts"][0]["provenance"]
    if not SMOKE:
        reg.require_same_code(first["git_commit"], CODE)
        reg.require_same_env(first, prov)
    if doc["inputs"] != digest:
        raise SystemExit("an input changed since the first attempt: refusing to resume")
    if [u["id"] for u in doc["plan"]] != [u["id"] for u in units]:
        raise SystemExit("the plan differs from the first attempt's: refusing to resume")


def empty_reproduces(rec: dict, intact: dict) -> bool:
    """The empty deletion, in the same composition, must reproduce batch 0's intact terms exactly (DESIGN §4)."""
    return (rec["numerator"], rec["denominator"]) == (intact["numerator"], intact["denominator"])


def cmd_run(args):
    prov = provenance()
    b = guards(args, prov)
    word = owner_word(args)
    require_build()
    require_check()
    device = "cpu" if SMOKE else args.device
    n = R("genomes")
    names = ensemble_names()
    names = {e: v[:R("graphs_per_ensemble")] for e, v in names.items()}
    con, bank, iface = setup(device)
    units = plan(con, names)
    path = exp_dir() / "measurements.json"
    digest = inputs_digest(names)
    if path.exists():
        doc = json.loads(path.read_text(encoding="utf-8"))
        check_resume(doc, prov, digest, units)
    else:
        doc = {"what": "03mc's measurements, one record per unit, in the registered order", "registered": REGISTERED,
               "smoke": SMOKE, "bound_commit": b, "inputs": digest, "plan": units, "attempts": [], "units": {}}
    doc["attempts"].append({"provenance": prov, "owner_word": word,
                            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "outcome": "running"})
    reg.write_json(path, doc, atomic=True)
    cap = cap_clock()
    graphs: dict = {}
    outcome = "completed"
    try:
        with acct.category("probe"):
            for unit in units:
                if unit["id"] in doc["units"]:
                    continue
                cap.check()
                t0 = time.perf_counter()
                rec, arrays = measure(con, bank, iface, unit, device, n, graphs)
                rec["arrays_sha256"] = save_arrays(out_dir() / "arrays" / f"{safe(unit['id'])}.npz", arrays)
                rec["seconds"] = time.perf_counter() - t0
                doc["units"][unit["id"]] = rec
                if unit["id"] == "qb/0/empty":
                    if not empty_reproduces(rec, doc["units"]["qb/0/intact"]):
                        outcome = "stopped: the empty deletion does not reproduce batch 0's intact terms"
                        break
                reg.write_json(path, doc, atomic=True)
                if len(graphs) > 4:  # graph objects are reused only within a graph's units
                    graphs.clear()
    except reg.CapReached as e:
        outcome = f"stopped: {e}"
    doc["attempts"][-1]["outcome"] = outcome
    doc["attempts"][-1]["ended_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    reg.write_json(path, doc, atomic=True)
    print(outcome, f"{len(doc['units'])} of {len(units)} units")
    if outcome.startswith("stopped: the empty"):
        raise SystemExit(outcome)


# ----------------------------------------------------------------------------- report

def cmd_report(args):
    from wormwars.exp03 import mc_report
    path = exp_dir() / "measurements.json"
    if not path.exists():
        raise SystemExit("no measurements.json")
    doc = json.loads(path.read_text(encoding="utf-8"))
    names = {e: v[:R("graphs_per_ensemble")] for e, v in ensemble_names().items()}
    rep = mc_report.build(doc, names, load_arrays, REGISTERED, minimum={"graphs": R("min_graphs"),
                                                                     "permutations": R("min_permutations")},
                          effect_boot=100 if SMOKE else 1000)
    reg.write_json(exp_dir() / "report.json", rep)
    print(json.dumps(rep["headline"], indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("command", choices=["build", "check", "run", "report", "audit"])
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--owner-word", default=None)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args(argv)
    use_smoke(args.smoke)
    if args.command == "audit":  # the planned seeds' audit alone: no file written, nothing drawn
        print(json.dumps(audit(), indent=1))
        return
    {"build": cmd_build, "check": cmd_check, "run": cmd_run, "report": cmd_report}[args.command](args)


if __name__ == "__main__":
    smoke = "--smoke" in sys.argv
    command = next((a for a in sys.argv[1:] if not a.startswith("-")), "")
    if command in ("build", "audit", "report"):  # the build's child records its own compute (exp03's accounting)
        main()
    else:
        acct.run_script(main, out_default=str(SMOKE_DIR if smoke else OUT_FORMAL), default="probe", name="p4mc")
