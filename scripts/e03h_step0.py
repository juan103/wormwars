"""03h's step 0 (experiments/03h-history-use/DESIGN.md §7.2, annotated 2026-10-19): exploratory and disclosed, on 03's
committed T1 fitness.

    python scripts/e03h_step0.py            # on CUDA; writes experiments/03h-history-use/development-records/step0.json
    python scripts/e03h_step0.py --smoke    # two graphs, few genomes, on the CPU, to runs/e03h-smoke/ (checks the code)

03's pilot (experiments/03-generation0/pilot.json) holds T1-M0 fitness for 256 random genomes x 16 worlds on each of 16
SH graphs, but measured history on a separate genome draw. Step 0 rebuilds those graphs and genomes by 03's recipe
(`scripts/exp03.py`: graphs `pilotSH101`-`pilotSH116`, SH with that seed and 20 passes; fitness genomes from one CUDA
`Genome.random(..., 256, ...)` call seeded by `genome_seed(name, "")`; the probe population from one call of 2 048
seeded one higher).

**Verification first, on `pilotSH101`, in two checks:**
- **(a) the fitness replay:** T1-M0 for the 256 fitness genomes, against the committed fitness;
- **(b) world-free:** `history()` on the 2 048 probe genomes, against the committed per-genome history.

Each check runs in 03's default mode and inside `replay_mode()`, each mode in its own process, because cuBLAS reads its
workspace setting once per process (Fable). Every comparison is bit-equality (T1's class-E contract, tolerance zero).

**The rule, fixed before step 0 runs:**
- If any check is bit-equal in either mode, the recipe is verified, and step 0 measures H and S on the fitness genomes
  of every pilot graph (in `replay_mode()`) and relates them to the committed fitness, under level only.
- Otherwise step 0 is dropped and the record says so. DESIGN §7.7's s_graph then uses the pilot's estimate alone.
- Step 0 sets nothing by itself.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import json
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
from wormwars.e03h.stats import partial_spearman  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.evo.rollout import rollout  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.exp03.measures import history  # noqa: E402

_spec = importlib.util.spec_from_file_location("exp03_for_e03h", ROOT / "scripts" / "exp03.py")
X3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(X3)  # 03's driver, instance "03" (its import-time default): seeds, worlds, graphs

EXP = ROOT / "experiments" / "03h-history-use"
# the code, and every input step 0 reads: 03's pilot record (bank, gains, fitness, history) and the remaps (Astra)
GUARDED = ["wormwars", "scripts", "configs", "requirements.txt", "experiments/03h-history-use/DESIGN.md",
           "experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"]
INPUTS = ["experiments/03-generation0/pilot.json", "experiments/02-screening/remaps.json"]
VERIFY = "pilotSH101"
MODES = ("default", "replay")
SMOKE_GENOMES, SMOKE_PROBE = 16, 32


def cfg_t1(name, gains):
    c = grid.brain_config_for_graph(grid.task_config(Config(), "T1"), name)
    c.world.forward_gain, c.world.turn_gain = gains
    return c


def genomes_of(con, name, cfg, n, device, offset=0):
    """03's draws: the fitness population (offset 0, 256) or the probe population (offset 1, 2 048)."""
    graph = X3._load_graph(con, name)
    spec = BrainSpec.from_connectome(graph, device=device)
    gen = torch.Generator(device=device).manual_seed(X3._gseed(name) + offset)
    return Genome.random(spec, cfg.brain, n, generator=gen, device=device)


def _context():
    X3.use_instance("03")
    pilot = json.loads(X3.PILOT.read_text(encoding="utf-8"))
    remap = json.loads(X3.INPUT_FILES["remaps.json"].read_text(encoding="utf-8"))["sets"]
    con = load_connectome()
    return pilot, con, grid.interface_for(con, "M0", remap), {g["name"]: g for g in pilot["graphs"]}


def _equal(got, committed) -> dict:
    got, committed = np.asarray(got, dtype=np.float32), np.asarray(committed, dtype=np.float32)
    if got.shape != committed.shape:
        return {"bit_equal": False, "shape": list(got.shape), "reference_shape": list(committed.shape)}
    bad = ~(np.isfinite(got) & np.isfinite(committed)) | (got != committed)
    d = np.abs(got.astype(np.float64) - committed.astype(np.float64))
    return {"bit_equal": bool(not bad.any()), "unequal_values": int(bad.sum()),
            "max_difference": float(np.nanmax(d)) if d.size else 0.0}


def verify(mode: str, smoke: bool) -> dict:
    """Checks (a) and (b) on `pilotSH101` in one mode ("default", "replay", or "cpu" in smoke)."""
    pilot, con, iface, records = _context()
    device = "cpu" if smoke else "cuda"
    rec = records[VERIFY]
    cfg = cfg_t1(VERIFY, tuple(rec["gains"]))
    ctx = replay_mode if mode == "replay" else contextlib.nullcontext
    with acct.category("measure"), ctx():
        fit_g = genomes_of(con, VERIFY, cfg, 256, device)
        probe_g = genomes_of(con, VERIFY, cfg, 2048, device, offset=1)
        if smoke:
            fit_g, probe_g = fit_g.select(list(range(SMOKE_GENOMES))), probe_g.select(list(range(SMOKE_PROBE)))
        score = rollout(cfg, iface, fit_g, X3.WORLDS, X3.RUN_SEED, device, chunk_worlds=4096).score
        h = history(probe_g, cfg, iface, pilot["bank"])
    n_f, n_p = fit_g.n_strains, probe_g.n_strains
    hist = {f"{k}.{part}": _equal(h[k][part], np.asarray(rec["history"][k][part])[:n_p])
            for k in ("raw_turn", "raw_forward") for part in ("final", "after", "steady_contrast")}
    return {"mode": mode, "graph": VERIFY,
            "fitness": {"genomes": int(n_f), **_equal(score, np.asarray(rec["fitness"]["T1-M0"])[:n_f])},
            "history": {"genomes": int(n_p), "parts": hist, "bit_equal": all(v["bit_equal"] for v in hist.values())}}


def measure(smoke: bool) -> dict:
    """H and S on every pilot graph's fitness genomes, against the committed fitness, under level."""
    pilot, con, iface, records = _context()
    device = "cpu" if smoke else "cuda"
    names = sorted(records)[:2] if smoke else sorted(records)
    ctx = contextlib.nullcontext if smoke else replay_mode
    out = {}
    for name in names:
        rec = records[name]
        cfg = cfg_t1(name, tuple(rec["gains"]))
        with acct.category("measure"), ctx():
            g = genomes_of(con, name, cfg, 256, device)
            if smoke:
                g = g.select(list(range(SMOKE_GENOMES)))
            hist = history(g, cfg, iface, pilot["bank"])
        fit = np.asarray(rec["fitness"]["T1-M0"], dtype=np.float64)[: g.n_strains].mean(axis=1)
        H = np.abs(hist["raw_turn"]["final"])
        S = np.abs(hist["raw_turn"]["steady_contrast"])
        rho, flag = partial_spearman(H, fit, S)
        q = np.argsort(H, kind="stable")
        k = max(1, len(q) // 4)
        out[name] = {"rho_level": rho, "degenerate": flag,
                     "top_minus_bottom_quartile_fitness": float(fit[q[-k:]].mean() - fit[q[:k]].mean()),
                     "H_mean": float(H.mean()), "S_mean": float(S.mean()), "fitness_mean": float(fit.mean())}
    return out


def run(smoke: bool, enforce: bool | None = None, verifications: dict | None = None) -> dict:
    """`verifications` maps a mode to `verify`'s output (computed here, in-process, if not given). `enforce` (default:
    not smoke) applies the registered rule: no bit-equal check stops step 0."""
    enforce = (not smoke) if enforce is None else enforce
    if verifications is None:
        verifications = {"cpu" if smoke else "replay": verify("cpu" if smoke else "replay", smoke)}
    out = {"exploratory": True, "device": "cpu" if smoke else "cuda", "smoke": smoke, "graphs": {},
           "verification": verifications,
           "inputs": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in INPUTS}}
    passed = [m for m, v in verifications.items() if v["fitness"]["bit_equal"] or v["history"]["bit_equal"]]
    out["verified_by"] = passed
    if not passed and enforce:
        out["dropped"] = ("no verification check was bit-equal in any mode, so step 0 is dropped (DESIGN.md §7.2, "
                          "annotated 2026-10-19); §7.7's s_graph uses the pilot's estimate alone")
        return out
    out["graphs"] = measure(smoke)
    rhos = np.array([r["rho_level"] for r in out["graphs"].values()])
    out["summary"] = {"graphs": len(rhos), "mean_rho_level": float(rhos.mean()),
                      "between_graph_sd_rho_level": float(rhos.std(ddof=1)) if len(rhos) > 1 else None,
                      "positive": int((rhos > 0).sum())}
    return out


def _verify_in_subprocesses(out_dir: Path) -> dict:
    res = {}
    for mode in MODES:
        path = out_dir / f"verify-{mode}.json"
        r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--verify", mode, "--out", str(path)],
                           cwd=ROOT)
        if r.returncode != 0:
            raise SystemExit(f"the {mode}-mode verification failed to run (exit {r.returncode})")
        res[mode] = json.loads(path.read_text(encoding="utf-8"))
    return res


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--verify", choices=MODES, help="internal: one mode's verification, in its own process")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    out_dir = ROOT / "runs" / ("e03h-smoke" if args.smoke else "e03h") / "step0"
    if args.verify:
        with acct.recorded(out_dir / "compute", out_dir / "compute.json", default="measure", experiment="03h",
                           stage=f"step0-verify-{args.verify}", script="scripts/e03h_step0.py"):
            v = verify(args.verify, smoke=False)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(v, indent=1) + "\n", encoding="utf-8")
        return v
    prov = reg.provenance(GUARDED)
    if not args.smoke:
        if prov["dirty"]:
            raise SystemExit("uncommitted changes in the guarded files: commit first")
        reg.require_pins(prov)
        if not torch.cuda.is_available():
            raise SystemExit("step 0 runs on CUDA (03's genomes were drawn by a CUDA generator)")
    rec = (out_dir / "step0.json") if args.smoke else (EXP / "development-records" / "step0.json")
    t0 = time.time()
    verifications = None if args.smoke else _verify_in_subprocesses(out_dir)
    with acct.recorded(out_dir / "compute", out_dir / "compute.json", default="measure", experiment="03h",
                       stage="step0", script="scripts/e03h_step0.py"):
        doc = run(args.smoke, verifications=verifications)
    doc.update({"provenance": prov, "seconds": time.time() - t0})
    reg.write_json(rec, doc, atomic=True)
    print(f"step 0: verified by {doc['verified_by']}; {json.dumps(doc.get('summary', doc.get('dropped')))} -> {rec}")
    return doc


if __name__ == "__main__":
    main()
