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
import os
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
               "factorial_permutations": 2, "null_deletion_graphs_per_ensemble": 1, "cap_hours": 1.0,
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

BUILD_RECORDS = ["build.json", "ensembles.json", "graphs_manifest.json", "graphs_content_manifest.json"]
CHECK_RECORDS = ["prerun-check.json", "prerun-repeat.json"]
RECORD_DIR = "experiments/03mc-p4-confirm"
MEASUREMENT_INPUTS = ["experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"]  # (Astra)
ENV_COMPARE = ("python", "numpy", "torch", "cuda", "gpu", "connectome_cache_sha256")


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


def check_prereg_chain(versions: list[bytes], now: bytes) -> None:
    """Every committed version since binding grows from the one before, and the working file from the last: an
    amendment, once committed, can be neither edited nor removed (Astra, prereg review)."""
    for a, b in zip(versions, versions[1:] + [now]):
        prereg_append_only(a, b)


def prereg_versions(since: str) -> list[bytes]:
    later = subprocess.check_output(["git", "log", "--reverse", "--format=%H", f"{since}..HEAD", "--", PREREG],
                                    cwd=ROOT, text=True).split()
    return [prereg_at(c) for c in [since, *later]]


def check_code_commit_named(now: bytes, bd: dict) -> None:
    """A moved code commit must be named in an appended amendment (Astra, prereg review)."""
    if bd["code_commit"] != bd["commit"] and bd["code_commit"][:7].encode() not in _lf(now):
        raise SystemExit("bound.json's code_commit is named by no amendment in the pre-registration: refusing")


def guarded(stage: str) -> list[str]:
    """What must be committed (and, for every stage, pushed) before a stage starts."""
    g = [*CODE, PREREG, f"{RECORD_DIR}/bound.json", *MEASUREMENT_INPUTS]
    if stage in ("check", "run", "report"):
        g += [f"{RECORD_DIR}/{f}" for f in BUILD_RECORDS]
    if stage in ("run", "report"):
        g += [f"{RECORD_DIR}/{f}" for f in CHECK_RECORDS]
    if stage == "report":
        g += [f"{RECORD_DIR}/measurements.json"]
    return g


def provenance(stage: str) -> dict:
    return reg.provenance(guarded(stage))


def guards(args, prov: dict, stage: str) -> str | None:
    """Every formal stage (PREREGISTRATION §9): the bound commit and any code commit are ancestors of HEAD; every
    committed version of the pre-registration since binding grows from the last; a moved code commit is named by an
    amendment; the code is unchanged since the code commit; the stage's records are committed and HEAD is pushed;
    the pinned environment. `check` and `run` also need CUDA on the registered GPU. Returns the bound commit (None
    in smoke runs)."""
    if SMOKE:
        return None
    bd = bound()
    for c in {bd["commit"], bd["code_commit"]}:
        if subprocess.run(["git", "merge-base", "--is-ancestor", c, "HEAD"], cwd=ROOT).returncode != 0:
            raise SystemExit(f"{c[:7]} (bound.json) is not an ancestor of HEAD: refusing")
    now = (ROOT / PREREG).read_bytes()
    check_prereg_chain(prereg_versions(bd["commit"]), now)
    check_code_commit_named(now, bd)
    reg.require_same_code(bd["code_commit"], [*CODE, *MEASUREMENT_INPUTS])  # the inputs are bound too (Astra)
    if stage in ("check", "run"):
        reg.require_formal(args.device, prov)
    else:  # the build (CPU) and the report: the pinned environment, committed and pushed
        reg.require_pins(prov)
        reg.require_pushed(prov)
    return bd["commit"]


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


def records_sha(files) -> dict:
    return {f: reg.file_sha256(exp_dir() / f) for f in files if (exp_dir() / f).exists()}


def cmd_build(args):
    """The build is one cap unit, checked before it starts: 03's builder queues every graph in one pool, so its
    overrun can be the whole build (PREREGISTRATION §4). The wrapper's own steps run in two small attempts of the
    same accounting; the builder records its own attempt."""
    prov = provenance("build")
    b = guards(args, prov, "build")
    exp = exp_dir()
    if (exp / "build.json").exists():
        raise SystemExit("build.json exists: the build has run and is not rerun")
    with acct.attempt(out_dir() / "compute", default="measure", script="p4mc", argv=["build", "pre"]):
        before = audit()
        if not before["ok"]:
            reg.write_json(exp / "build.json", {"outcome": "refused: the planned seeds are not fresh", "audit": before})
            raise SystemExit(f"the freshness audit failed before the build: {before}")
        cap_clock().check()
    cmd = [sys.executable, str(ROOT / "scripts" / "exp03.py"), "build", "--instance",
           "03mc-smoke" if SMOKE else "03mc", "--workers", str(args.workers)]
    env = {**os.environ, "P4MC_BUILD_TOKEN": b or "smoke"}  # exp03.py refuses a formal 03mc build without it
    t0 = time.perf_counter()
    subprocess.run(cmd, cwd=ROOT, check=True, env=env)  # exp03's own build records its compute in runs/p4mc*/compute
    with acct.attempt(out_dir() / "compute", default="measure", script="p4mc", argv=["build", "post"]):
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
            "graphs": {e: len(v) for e, v in names.items()},
            "substituted": {e: validation[e]["substituted"] for e in mc.ENSEMBLES},
            "records_sha256": records_sha(BUILD_RECORDS[1:]), "seconds": time.perf_counter() - t0})
    if not ok:
        raise SystemExit("the build's checks failed: nothing is measured (DESIGN §3); see build.json")
    print({e: len(v) for e, v in names.items()}, "audit ok, content ok, validation ok")


def require_build(b: str | None) -> dict:
    """The build completed, under this binding, and its records are as it wrote them (Astra, prereg review)."""
    p = exp_dir() / "build.json"
    if not p.exists():
        raise SystemExit("no build.json: run the build first")
    rec = json.loads(p.read_text(encoding="utf-8"))
    if rec.get("outcome") != "completed":
        raise SystemExit(f"the build did not complete: {rec.get('outcome')}")
    if not SMOKE and rec.get("bound_commit") != b:
        raise SystemExit("build.json was written under another binding: refusing")
    if rec.get("records_sha256") != records_sha(BUILD_RECORDS[1:]):
        raise SystemExit("the build's records changed since build.json was written: refusing")
    return rec


# ----------------------------------------------------------------------------- the pre-run check

@acct.counted("probe")
def repeat_check(device) -> dict:
    """Fable (prereg review): the empty-deletion stop needs two runs of the same genomes to agree bitwise. On old
    inputs (03's N2 genomes, never a fresh draw), at the registered composition: intact twice, then the empty
    deletion, compared bit for bit."""
    con, bank, iface = setup(device)
    g, cfg = EQ.P.probe_genomes(con, "N2", device, n=8 if SMOKE else None)
    runs = {"intact": twin.history(g, cfg, iface, bank, follow=5),
            "intact again": twin.history(g, cfg, iface, bank, follow=5),
            "empty deletion": twin.history(delete_neurons(g, [[]] * g.n_strains), cfg, iface, bank, follow=5)}
    ref = runs["intact"]["raw_turn"]
    same = {k: all(np.array_equal(v["raw_turn"][q], ref[q]) for q in ("final", "steady_contrast")) for k, v in runs.items()}
    return {"what": "bitwise repeat of the probe at the registered composition, old inputs", "device": device,
            "genomes": int(g.n_strains), "identical": same, "passed": all(same.values())}


def cmd_check(args):
    prov = provenance("check")
    b = guards(args, prov, "check")
    word = owner_word(args)
    require_build(b)
    exp = exp_dir() if not SMOKE else SMOKE_DIR / "record"
    for f in CHECK_RECORDS:
        if not SMOKE and (EXP_FORMAL / f).exists():
            raise SystemExit(f"{f} exists: the pre-run check has run and is not rerun")
    EQ.check_references()  # before the one-shot marker: a stale reference must not use up the check (Fable)
    names = {e: v[:R("graphs_per_ensemble")] for e, v in ensemble_names().items()}
    if not SMOKE:
        reg.start_marker(out_dir() / "markers", "check", {**prov, "owner_word": word, "bound_commit": b})
    cap_clock().check()
    device = "cpu" if SMOKE else args.device
    rep = repeat_check(device)
    reg.write_json(exp / "prerun-repeat.json", {**rep, "provenance": prov, "bound_commit": b,
                                                "inputs": inputs_digest(names)})
    if not rep["passed"] and not SMOKE:  # before the equivalence set: nothing formal can follow anyway (Fable)
        raise SystemExit("the probe does not repeat bitwise at the registered composition: nothing formal runs")
    argv = ["--set", "check", "--device", device, "--record", "prerun-check.json"]
    EQ.main(argv + (["--smoke"] if SMOKE else []))


def require_check(code_commit: str | None, prov: dict | None = None, digest: dict | None = None) -> None:
    """The registered pre-run check passed on the current code, at the registered set and device, with the pinned
    references, and the repeat check passed (Astra, Fable, prereg review); both ran on clean code, in the current
    environment, on the current measurement inputs (Astra, review of draft 2)."""
    if SMOKE:
        return
    pc, pr = EXP_FORMAL / "prerun-check.json", EXP_FORMAL / "prerun-repeat.json"
    if not pc.exists() or not pr.exists():
        raise SystemExit("the pre-run check has not run: nothing formal runs (PREREGISTRATION §5)")
    c, r = json.loads(pc.read_text(encoding="utf-8")), json.loads(pr.read_text(encoding="utf-8"))
    problems = []
    if not c.get("passed"):
        problems.append("the check did not pass")
    if c.get("set") != "check" or not str(c.get("device", "")).startswith("cuda") or c.get("genomes") != 2048:
        problems.append("not the registered check set, device or genome count")
    if c.get("reference_sha256", {}).get("decay") != EQ.REFERENCE_SHA256["decay"] or any(
            c.get("reference_sha256", {}).get(k) != v for k, v in EQ.REFERENCE_SHA256.items()):
        problems.append("not the pinned references")
    stamp = c.get("stamp", {})
    if stamp.get("dirty"):
        problems.append("the check ran on uncommitted code")
    if not r.get("passed") or not str(r.get("device", "")).startswith("cuda") or r.get("genomes") != 2048:
        problems.append("the repeat check did not pass at the registered composition")
    if r.get("provenance", {}).get("dirty", True):
        problems.append("the repeat check ran on uncommitted code")
    if prov is not None:
        for k in ENV_COMPARE:
            if stamp.get(k) != prov.get(k) or r.get("provenance", {}).get(k) != prov.get(k):
                problems.append(f"the environment differs from the check's ({k})")
                break
    if digest is not None and r.get("inputs") != digest:
        problems.append("the measurement inputs differ from the check's")
    if problems:
        raise SystemExit("the pre-run check does not admit the run: " + "; ".join(problems))
    for commit in {stamp.get("git_commit"), r.get("provenance", {}).get("git_commit")}:
        reg.require_same_code(commit, CODE)  # the check ran on the code that runs now
    if code_commit:
        reg.require_same_code(code_commit, CODE)
    if not (out_dir() / "markers" / "check-started.json").exists():
        raise SystemExit("no start marker for the check: refusing")


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
    if SMOKE:  # the smoke screen is the eight controls, so the report's controls path runs (Fable)
        pairs = [k for ks in REGISTERED["controls"].values() for k in ks]
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


def array_path(uid: str) -> Path:
    return out_dir() / "arrays" / f"{safe(uid)}.npz"


def save_arrays(path: Path, arrays: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + ".tmp.npz")
    np.savez_compressed(tmp, **arrays)
    EQ.P.replace(tmp, path)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_loader(units: dict):
    """Loads a unit's arrays only if they hash as its record says (Fable, Astra, prereg review)."""
    def load(uid: str) -> dict:
        p = array_path(uid)
        if hashlib.sha256(p.read_bytes()).hexdigest() != units[uid]["arrays_sha256"]:
            raise SystemExit(f"{p.name} does not hash as its record says: refusing")
        with np.load(p, allow_pickle=False) as z:
            return {k: z[k] for k in z.files}
    return load


def inputs_digest(names: dict) -> dict:
    """What a resume must find unchanged: the graph manifests, the stimulus bank, the remaps and the interface."""
    files = [exp_dir() / "ensembles.json", exp_dir() / "graphs_manifest.json", exp_dir() / "graphs_content_manifest.json",
             X.PILOT, X.INPUT_FILES["remaps.json"], ROOT / "configs" / "interface.yaml"]
    return {str(p.relative_to(ROOT)): reg.file_sha256(p) for p in files if p.exists()}


def empty_reproduces(rec: dict, intact: dict) -> bool:
    """The empty deletion, in the same composition, must reproduce batch 0's intact terms exactly (DESIGN §4)."""
    return (rec["numerator"], rec["denominator"]) == (intact["numerator"], intact["denominator"])


TERMINAL = "stopped: the empty deletion does not reproduce batch 0's intact terms"


def check_resume(doc: dict, prov: dict, digest: dict, units: list, verify_arrays=True) -> None:
    """A resume continues the first attempt only (Fable, Astra, prereg review): never after the terminal stop; the
    same code and environment (formal), inputs, registered settings, smoke or formal identity and the whole plan;
    and every completed unit's arrays as recorded."""
    if any(str(a.get("outcome", "")).startswith(TERMINAL) for a in doc["attempts"]):
        raise SystemExit("an earlier attempt stopped at the empty deletion: the run does not resume (an amendment decides)")
    u = doc["units"]
    if "qb/0/empty" in u and "qb/0/intact" in u and not empty_reproduces(u["qb/0/empty"], u["qb/0/intact"]):
        raise SystemExit("the recorded empty deletion does not reproduce batch 0's intact terms: refusing to resume")
    first = doc["attempts"][0]["provenance"]
    if not SMOKE:
        reg.require_same_code(first["git_commit"], CODE)
        reg.require_same_env(first, prov)
    if doc.get("smoke") != SMOKE or doc.get("registered") != REGISTERED:
        raise SystemExit("the registered settings or the smoke identity differ from the first attempt's: refusing")
    if doc["inputs"] != digest:
        raise SystemExit("an input changed since the first attempt: refusing to resume")
    if doc["plan"] != units:
        raise SystemExit("the plan differs from the first attempt's: refusing to resume")
    if verify_arrays:
        load = array_loader(u)
        for uid in u:
            if not array_path(uid).exists():
                raise SystemExit(f"{uid}'s arrays are missing: refusing to resume")
            load(uid)


class RunLock:
    """One run at a time (Astra, prereg review). A lock left by a crash is removed by hand after checking that no
    run is alive; the run never removes another's lock."""

    def __init__(self, path: Path):
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.path, "x", encoding="utf-8") as f:
                f.write(f"{os.getpid()} {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n")
        except FileExistsError:
            raise SystemExit(f"{self.path} exists: another run is alive, or a crashed one left it (check, then remove "
                             "it by hand)") from None
        return self

    def __exit__(self, *exc):
        self.path.unlink(missing_ok=True)
        return False


def cmd_run(args):
    prov = provenance("run")
    b = guards(args, prov, "run")
    word = owner_word(args)
    require_build(b)
    device = "cpu" if SMOKE else args.device
    n = R("genomes")
    names = ensemble_names()
    names = {e: v[:R("graphs_per_ensemble")] for e, v in names.items()}
    digest = inputs_digest(names)
    require_check(None if SMOKE else bound()["code_commit"], prov, digest)
    con, bank, iface = setup(device)
    units = plan(con, names)
    path = exp_dir() / "measurements.json"
    with RunLock(out_dir() / "run.lock"):
        if path.exists():
            doc = json.loads(path.read_text(encoding="utf-8"))
            check_resume(doc, prov, digest, units)
        else:
            doc = {"what": "03mc's measurements, one record per unit, in the registered order", "registered": REGISTERED,
                   "smoke": SMOKE, "bound_commit": b, "inputs": digest, "plan": units, "attempts": [], "units": {}}
        doc["attempts"].append({"provenance": prov, "owner_word": word, "replaced_orphan_arrays": [],
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
                    ap = array_path(unit["id"])
                    if ap.exists():  # left by an interruption between the arrays and the record: replaced, and said
                        doc["attempts"][-1]["replaced_orphan_arrays"].append(unit["id"])
                    rec["arrays_sha256"] = save_arrays(ap, arrays)
                    rec["seconds"] = time.perf_counter() - t0
                    doc["units"][unit["id"]] = rec
                    if unit["id"] == "qb/0/empty" and not empty_reproduces(rec, doc["units"]["qb/0/intact"]):
                        outcome = TERMINAL
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
    if outcome == TERMINAL:
        raise SystemExit(outcome)


# ----------------------------------------------------------------------------- report

def reserve_report_path(directory: Path) -> Path:
    """`report.json`, or the first free `report-<time>-<k>.json`, created exclusively, so no report is ever replaced
    (Astra, review of draft 2: a seconds-resolution name alone could collide)."""
    directory.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    for k in range(10_000):
        p = directory / ("report.json" if k == 0 else f"report-{stamp}-{k}.json")
        try:
            with open(p, "x", encoding="utf-8"):
                return p
        except FileExistsError:
            continue
    raise SystemExit("no free report name")


def validate_measurements(doc: dict, b: str | None, units: list, digest: dict) -> None:
    """Before the report (Astra, review of draft 2): the measurements belong to this binding, settings, plan and
    inputs, every attempt ran the current code, and every completed unit's arrays hash as recorded. A run stopped at
    the empty deletion stays reportable."""
    if not SMOKE:
        if doc.get("bound_commit") != b:
            raise SystemExit("measurements.json was written under another binding: refusing")
        for a in doc["attempts"]:
            reg.require_same_code(a["provenance"]["git_commit"], CODE)
            if a["provenance"].get("dirty"):
                raise SystemExit("an attempt ran on uncommitted code: refusing")
    if doc.get("smoke") != SMOKE or doc.get("registered") != REGISTERED:
        raise SystemExit("the measurements' registered settings or smoke identity differ: refusing")
    if doc["plan"] != units:
        raise SystemExit("the measurements' plan differs from the registered plan: refusing")
    extra = set(doc["units"]) - {u["id"] for u in units}
    if extra:
        raise SystemExit(f"units not in the plan: {sorted(extra)[:5]}: refusing (Fable, review of draft 3)")
    if doc["inputs"] != digest:
        raise SystemExit("the measurement inputs differ from those the run recorded: refusing")
    load = array_loader(doc["units"])
    for uid in doc["units"]:
        load(uid)


def cmd_report(args):
    """Guarded like every formal stage, without the GPU (Fable, Astra, prereg review); each unit's arrays are
    checked against their recorded hash before use; a report is never overwritten (a later one gets a time stamp)."""
    from wormwars.exp03 import mc_report
    prov = provenance("report")
    b = guards(args, prov, "report")
    path = exp_dir() / "measurements.json"
    if not path.exists():
        raise SystemExit("no measurements.json")
    doc = json.loads(path.read_text(encoding="utf-8"))
    names = {e: v[:R("graphs_per_ensemble")] for e, v in ensemble_names().items()}
    validate_measurements(doc, b, plan(load_connectome(), names), inputs_digest(names))
    rep = mc_report.build(doc, names, array_loader(doc["units"]), REGISTERED,
                          minimum={"graphs": R("min_graphs"), "permutations": R("min_permutations")},
                          effect_boot=100 if SMOKE else 1000)
    rep["provenance"], rep["bound_commit"] = prov, b
    rep["written_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out = reserve_report_path(exp_dir())
    reg.write_json(out, rep, atomic=True)
    print(out.name)
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
