"""T1.2's class E equivalence test for single-strain padding (docs/foundations/T1.md v2, section 3).

    python scripts/t1_equivalence.py --save-reference   # at the pre-change commit
    python scripts/t1_equivalence.py --compare          # after the change
    python scripts/t1_equivalence.py --published        # 02's single-strain hold-outs, off and on

The script runs at both commits: before the change `BrainConfig` has no `pad_single_strain`, and
the script leaves the config alone.

**Cases** (every one run in default mode and, in a fresh process, in `replay_mode(warn=False)`):
- 02-T1 at 200 ticks, 256 random N2 genomes x 8 worlds (160 rows per strain), with 2, 3, 4, 16, 32,
  64, 128 and 256 strains per chunk, and the first 32 strains one per chunk;
- the first 32 random genomes on 1, 16 and 64 worlds (20, 320 and 1 280 rows), one per chunk and 32
  per chunk; the 16-world set also with 31 per chunk (a remainder of one) and at 600 ticks;
- 02's 8 N2 champions for T1 on 16 and 64 worlds, alone and 8 per chunk;
- the Task N proxy (one wey, 300 ticks): the first 32 random genomes on 8, 16, 20 and 64 worlds (as
  many rows), one, two and 32 per chunk;
- the brain alone: 4 random genomes stepped 10 ticks at 1, 8, 16, 20, 64, 160, 320 and 1 280 rows,
  as a batch of 4 and each strain alone, plain, silenced, with a gap junction cut, and with the
  substeps overridden. The final states are compared.
- Fields compared: score, energy, alive, eaten, pellets eaten and starting food.
- With `--quick` (used for the CPU leg), rollouts run 20 ticks (30 for the stress test and the
  proxy) on fewer genomes.

**Legs** (tolerance zero; unequal values and the maximum difference recorded):
- **off:** every output equals the pre-change reference;
- **on:** multi-strain outputs equal the reference; each single-strain output equals the same strain
  in the reference's multi-strain batch;
- **sensitivity** (reference only; environment-dependent, not a pass condition): which single-strain
  cases differed from the batch before the change.

The reference is saved locally (`runs/t1-equivalence/`, not committed; it holds brain states) and
its sha256 is recorded in the committed summary.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
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
from wormwars.brain import Brain, BrainSpec, Genome  # noqa: E402
from wormwars.config import Config  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.evo import SeedPool, rollout  # noqa: E402
from wormwars.evo.bundle import replay_mode  # noqa: E402
from wormwars.evo.genomes import apply_world_meta, load_genome  # noqa: E402
from wormwars.exp02 import grid  # noqa: E402
from wormwars.interface import load_interface  # noqa: E402

OUT = ROOT / "runs" / "t1-equivalence"
PROXY_WORLDS = (8, 16, 20, 64)  # one wey: rows per strain = worlds (E1's shapes, D091)
FIELDS = ("score", "energy", "alive", "eaten", "pellet_eaten", "food_start")
CHUNKINGS = (2, 3, 4, 16, 32, 64, 128, 256)
BRAIN_ROWS = (1, 8, 16, 20, 64, 160, 320, 1280)


def provenance() -> dict:
    def git(*a):
        return subprocess.check_output(["git", *a], cwd=ROOT, text=True).strip()
    return {"git_commit": git("rev-parse", "HEAD"),
            "dirty": bool(git("status", "--porcelain", "--", "wormwars", "scripts", "configs"))}


def has_switch() -> bool:
    from wormwars.config import BrainConfig
    return "pad_single_strain" in {f.name for f in dataclasses.fields(BrainConfig)}


def with_pad(g: Genome, pad: bool | None) -> Genome:
    """`g` with the switch set, or unchanged when `pad` is None (the pre-change engine)."""
    if pad is None:
        return g
    return g.with_params(cfg=dataclasses.replace(g.cfg, pad_single_strain=pad))


def _to(g: Genome, device) -> Genome:
    return Genome(g.spec.to(device), g.cfg, **{k: None if v is None else v.to(device) for k, v in g.params().items()})


def _roll(cfg, iface, g, ids, device, per_chunk, ticks=None) -> dict:
    r = rollout(cfg, iface, g, ids, run_seed=3, device=device, chunk_worlds=per_chunk * len(ids), ticks=ticks)
    return {f: np.asarray(getattr(r, f)) for f in FIELDS}


def _champions(spec, runs02: Path):
    cfg = grid.task_config(Config(), "T1")
    files = sorted(runs02.glob("T1-M0-N2-run*-g39.npz"))[:8]
    if len(files) < 8:
        raise SystemExit(f"need 8 of 02's T1 N2 champions in {runs02}, found {len(files)}")
    gs, metas = zip(*[load_genome(f, spec) for f in files])
    cfg, _ = apply_world_meta(cfg, metas[0])
    cfg.brain = gs[0].cfg
    return Genome.cat(list(gs)), cfg, [f.name for f in files]


def _states(g, currents, variant, spec) -> np.ndarray:
    """The brain state after stepping `g` through `currents`, one tensor per tick."""
    br = Brain(g)
    if variant == "silenced":
        br.silence([[0, 5, 10]] * g.n_strains)
    if variant == "gap_cut":
        i, j = int(spec.gap_i[0]), int(spec.gap_j[0])
        br.cut_gap([[(i, j)]] * g.n_strains)
    v = br.initial_state(currents[0].shape[1])
    for c in currents:
        v = br.step(v, c, substeps=8 if variant == "substeps8" else None)
    return v.cpu().numpy()


def run_cases(con, device, pad, runs02: Path, quick: bool) -> tuple[dict, dict]:
    """Every case's outputs, as {name: array}, and a description of each case."""
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con)
    out, desc = {}, {}

    def put(case, res, **d):
        for f, a in res.items():
            out[f"{case}/{f}"] = a
        desc[case] = d

    t1 = grid.task_config(Config(), "T1")
    n_random = 32 if quick else 256
    rnd = with_pad(_to(Genome.random(spec, t1.brain, n_random, generator=torch.Generator().manual_seed(1)), device), pad)
    first = rnd.select(list(range(min(32, n_random) if not quick else 4)))
    ticks = 20 if quick else None

    # 1. strains per chunk, B = 160
    for k in CHUNKINGS:
        if k <= n_random:
            # a chunking whose last chunk holds one strain is a single-strain case (256 = 85 x 3 + 1);
            # the first full comparison counted chunk 3 as multi-strain (D090)
            put(f"T1/random{n_random}x8/chunk{k}", _roll(t1, iface, rnd, np.arange(8), device, k, ticks),
                strains=n_random, worlds=8, per_chunk=k)
    put(f"T1/first{first.n_strains}x8/chunk1", _roll(t1, iface, first, np.arange(8), device, 1, ticks),
        strains=first.n_strains, worlds=8, per_chunk=1, batch_ref=f"T1/random{n_random}x8/chunk{n_random}")

    # 2. rows per strain, the remainder case and the stress test
    for w in (1, 16, 64):
        ids = np.arange(w)
        for k in (1, first.n_strains):
            put(f"T1/first{first.n_strains}x{w}/chunk{k}", _roll(t1, iface, first, ids, device, k, ticks),
                strains=first.n_strains, worlds=w, per_chunk=k)
    put(f"T1/first{first.n_strains}x16/chunk{first.n_strains - 1}",
        _roll(t1, iface, first, np.arange(16), device, first.n_strains - 1, ticks),
        strains=first.n_strains, worlds=16, per_chunk=first.n_strains - 1)
    stress = t1.copy()
    stress.world.max_ticks = 30 if quick else 600
    for k in (1, first.n_strains):
        put(f"T1-600/first{first.n_strains}x16/chunk{k}", _roll(stress, iface, first, np.arange(16), device, k),
            strains=first.n_strains, worlds=16, per_chunk=k, ticks=stress.world.max_ticks)

    # 3. 02's champions: checkpoint and hold-out shapes
    if runs02 is not None:
        champs, ccfg, names = _champions(spec, runs02)
        champs = with_pad(_to(champs, device), pad)
        for w in (16, 64):
            for k in (1, 8):
                put(f"T1-champions/8x{w}/chunk{k}", _roll(ccfg, iface, champs, np.arange(w), device, k, ticks),
                    strains=8, worlds=w, per_chunk=k, files=names)

    # 4. the Task N proxy: one wey, 300 ticks
    proxy = t1.copy()
    proxy.world.weys_per_swarm = 1
    proxy.world.max_ticks = 30 if quick else 300
    for w in PROXY_WORLDS:
        for k in (1, 2, first.n_strains):
            put(f"proxy/first{first.n_strains}x{w}/chunk{k}", _roll(proxy, iface, first, np.arange(w), device, k),
                strains=first.n_strains, worlds=w, per_chunk=k, weys=1, ticks=proxy.world.max_ticks)

    # 5. the brain alone
    four = with_pad(_to(Genome.random(spec, t1.brain, 4, generator=torch.Generator().manual_seed(5)), device), pad)
    gen = torch.Generator().manual_seed(6)
    for rows in BRAIN_ROWS:
        cur = [(torch.randn(4, rows, spec.n, generator=gen) * 0.5).to(device) for _ in range(10)]
        for variant in ("plain", "silenced", "gap_cut", "substeps8"):
            out[f"brain/B{rows}/{variant}/batch4"] = _states(four, cur, variant, spec)
            out[f"brain/B{rows}/{variant}/alone"] = np.concatenate(
                [_states(four.select([i]), [c[i:i + 1] for c in cur], variant, spec) for i in range(4)])
    return out, desc


def _eq(a, b) -> dict:
    """Bit equality, strictly: the same shape and dtype, every value finite, and the same bits (so
    -0.0 and +0.0 differ, and matching NaNs do not pass). The numeric difference is reported beside
    it (Astra, D091)."""
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape or a.dtype != b.dtype:
        return {"equal": False, "shape": [list(a.shape), list(b.shape)], "dtype": [str(a.dtype), str(b.dtype)]}
    floating = a.dtype.kind == "f"
    finite = bool(np.isfinite(a).all() and np.isfinite(b).all()) if floating else True
    same = (a.view(f"u{a.itemsize}") == b.view(f"u{b.itemsize}")) if floating else (a == b)
    diff = np.abs(a.astype(np.float64) - b.astype(np.float64))
    return {"equal": bool(same.all()) and finite, "finite": finite, "unequal": int((~same).sum()),
            "values": int(a.size), "max_abs_diff": float(np.nanmax(diff)) if diff.size else 0.0}


def _batch_rows(ref: dict, key: str, n: int) -> np.ndarray:
    """The first n strains' rows of the multi-strain reference output matching `key`."""
    return np.asarray(ref[key])[:n]


def _single_strain(d: dict) -> bool:
    """Whether any chunk of this case holds exactly one strain: one per chunk, or a last chunk of one
    (256 strains in chunks of 3). Inferred from the counts, not from a stored flag, so an old
    reference's descriptions classify correctly (Fable, Astra, D091)."""
    k, n = d.get("per_chunk"), d.get("strains")
    return k == 1 or (k is not None and n is not None and k > 1 and n % k == 1)


def single_strain_pairs(keys, desc) -> list[tuple[str, str, int]]:
    """(single-strain key, multi-strain reference key, strains) for every output of a case with a
    single-strain chunk."""
    keys = list(keys)
    present = set(keys)
    pairs = []
    for k in keys:
        if k.startswith("brain/"):  # brain keys carry no field: brain/B{rows}/{variant}/{alone|batch4}
            if k.endswith("/alone"):
                pairs.append((k, k[: -len("alone")] + "batch4", 4))
            continue
        case, field = k.rsplit("/", 1)
        if case not in desc or "per_chunk" not in desc[case] or "strains" not in desc[case]:
            raise AssertionError(f"{k}: no case description, so it cannot be classified")
        d = desc[case]
        if _single_strain(d):
            batch = d.get("batch_ref") or case.rsplit("/chunk", 1)[0] + f"/chunk{d['strains']}"
            pairs.append((k, f"{batch}/{field}", d["strains"]))
    # every pair needs its batch output, or a leg would silently compare against nothing (D092)
    missing = sorted(p[0] for p in pairs if p[1] not in present)
    if missing:
        raise AssertionError(f"single-strain outputs whose batch output is missing: {missing[:5]}")
    return pairs


def cross_composition(outputs: dict, desc: dict) -> dict:
    """Every multi-strain chunking against the largest chunking of the same case, as a table of
    tested pairs (the contract's amendment lists what was tested, D091)."""
    groups = {}
    for case, d in desc.items():
        if "/chunk" in case and not _single_strain(d):
            groups.setdefault(case.rsplit("/chunk", 1)[0], []).append((d["per_chunk"], case))
    out = {}
    for members in groups.values():
        members.sort()
        full_k, full = members[-1]
        for k, case in members[:-1]:
            for f in FIELDS:
                key, full_key = f"{case}/{f}", f"{full}/{f}"
                if key in outputs and full_key in outputs:
                    n = outputs[key].shape[0]
                    out[f"{case} vs chunk{full_k}/{f}"] = _eq(outputs[full_key][:n], outputs[key])
    return out


def compare(ref: dict, desc: dict, off: dict, on: dict) -> dict:
    """The three legs. The reference and both new runs must hold the same, non-empty set of outputs,
    so nothing added or dropped passes silently (Astra, D092)."""
    if not ref:
        raise AssertionError("empty reference")
    if not (set(ref) == set(off) == set(on)):
        raise AssertionError(f"output inventories differ: only in the reference {sorted(set(ref) - set(off))[:5]}, "
                             f"only in the new run {sorted(set(off) - set(ref))[:5]}")
    pairs = {p[0]: p for p in single_strain_pairs(ref.keys(), desc)}
    res = {"off_equals_reference": {}, "on_multi_equals_reference": {}, "on_single_equals_batch": {}}
    for k in ref:
        res["off_equals_reference"][k] = _eq(ref[k], off[k])
        if k in pairs:
            _, batch_key, n = pairs[k]
            res["on_single_equals_batch"][k] = _eq(_batch_rows(ref, batch_key, n), on[k])
        else:
            res["on_multi_equals_reference"][k] = _eq(ref[k], on[k])
    res["passed"] = {leg: all(v["equal"] for v in rows.values()) for leg, rows in res.items()}
    return res


def sensitivity(ref: dict, desc: dict) -> dict:
    """Before the change: which single-strain outputs differed from the same strains in a batch."""
    out = {}
    for k, batch_key, n in single_strain_pairs(ref.keys(), desc):
        out[k] = _eq(_batch_rows(ref, batch_key, n), ref[k])
    return out


def _save(path: Path, arrays: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(path, **{k.replace("/", "|"): v for k, v in arrays.items()})
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as d:
        return {k.replace("|", "/"): d[k] for k in d.files}


def one_mode(args, mode: str) -> dict:
    """Run in this process (default mode) or re-invoke in a fresh one (replay mode)."""
    if mode == "replay_mode":
        cmd = [sys.executable, str(Path(__file__)), "--in-replay", "--device", args.device, "--tag", args.tag,
               "--runs02", str(args.runs02)] + (["--quick"] if args.quick else [])
        cmd += ["--save-reference"] if args.save_reference else ["--compare"]
        # the child's counts join this attempt's record, even if it fails (D091, D092)
        acct.run_counted_child(cmd, OUT / f"{args.tag}-{args.device}-replay_mode-ledger.json")
        return json.loads((OUT / f"{args.tag}-{args.device}-replay_mode.json").read_text(encoding="utf-8"))
    return run_mode(args, mode)


def run_mode(args, mode: str) -> dict:
    con = load_connectome()
    runs02 = Path(args.runs02) if args.runs02 else None
    t = time.perf_counter()
    if args.save_reference:
        a, desc = run_cases(con, args.device, None, runs02, args.quick)
        b, _ = run_cases(con, args.device, None, runs02, args.quick)
        sha = _save(OUT / f"reference-{args.device}-{mode}.npz", a)
        res = {"mode": mode, "device": args.device, "reference_sha256": sha, "cases": desc,
               "reference_repeats": {k: _eq(a[k], b[k]) for k in a},
               "sensitivity": sensitivity(a, desc), "cross_composition": cross_composition(a, desc)}
        res["reference_repeats_all_equal"] = all(v["equal"] for v in res["reference_repeats"].values())
    else:
        if not has_switch():
            raise SystemExit("--compare needs the changed engine (BrainConfig.pad_single_strain)")
        path = OUT / f"reference-{args.device}-{mode}.npz"
        ref = _load(path)
        # the case descriptions come from this run, not the saved reference, so a classification
        # fix reaches the comparison (Fable, D091)
        off, desc = run_cases(con, args.device, False, runs02, args.quick)
        on, _ = run_cases(con, args.device, True, runs02, args.quick)
        res = {"mode": mode, "device": args.device,
               "reference_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
               **compare(ref, desc, off, on), "cross_composition_on": cross_composition(on, desc)}
    res["seconds"] = time.perf_counter() - t
    if args.in_replay:
        (OUT / f"{args.tag}-{args.device}-replay_mode.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


PROBE_VARIANTS = {"food_constant": {"food_probe": "constant"}, "food_mean": {"food_probe": "mean"}}


def _replay(cfg, iface, champ, ids, seed, device, stored) -> dict:
    """One stored per-world score list replayed with the switch off and on. Stored scores were
    float32 written as JSON floats, so float32 recovers their exact bits."""
    stored = np.asarray(stored, dtype=np.float32)
    row = {}
    for label, pad in (("off", False), ("on", True)):
        score = rollout(cfg, iface, with_pad(champ, pad), ids, seed, device).score[0]
        row[label] = _eq(stored, score)
        # in a common dtype, so bit-identical arrays report exactly zero (Fable, Astra, D091)
        row[label]["mean_change"] = float(score.astype(np.float64).mean() - stored.astype(np.float64).mean())
    return row


def published(args) -> dict:
    """02's single-strain evaluations replayed with the switch off and on, against what 02 stored:
    - every final hold-out (one champion on 64 worlds; `records.jsonl`);
    - the capability probes of every generation-39 champion (one champion on 64 probe worlds;
      `probes.json`): the real signal, the constant-food probe, and the bilateral mean (the primary
      probe; stereo tasks only). The jitter probes are left out: current code cannot regenerate
      02's jitter draws (D066, D067).
    Off must reproduce them; on shows the change."""
    from wormwars.exp02.probes import _variant
    con = load_connectome()
    exp02 = ROOT / "runs" / "exp02-screening"
    runs02 = Path(args.runs02)
    remaps = json.loads((grid.EXP02_DIR / "remaps.json").read_text(encoding="utf-8"))["sets"]
    calib = json.loads((grid.EXP02_DIR / "calibration.json").read_text(encoding="utf-8"))
    probes = json.loads((exp02 / "probes.json").read_text(encoding="utf-8"))["champions"]
    recs = grid.read_records(exp02 / "records.jsonl")
    if args.quick:
        recs = recs[:3]
    holdouts, probe_rows, t = {}, {}, time.perf_counter()
    for r in recs:
        cfg = grid.brain_config_for_graph(grid.task_config(Config(), r["task"]), r["graph"])
        cfg.world.forward_gain, cfg.world.turn_gain = calib[r["graph"]]["forward_gain"], calib[r["graph"]]["turn_gain"]
        iface = grid.interface_for(con, r["mapping"], remaps)
        spec = BrainSpec.from_connectome(grid.graph_for(con, r["graph"]))
        pool = SeedPool(cfg, r["run_seed"])
        for tag in sorted(k[len("holdout_"):] for k in r if k.startswith("holdout_")):
            champ, _ = load_genome(runs02 / f"{r['key']}-{tag}.npz", spec)
            champ = _to(champ, args.device)
            row = _replay(cfg, iface, champ, pool.holdout, r["run_seed"], args.device, r[f"holdout_{tag}"])
            row["loaded_switch"] = getattr(champ.cfg, "pad_single_strain", None)
            holdouts[f"{r['key']}-{tag}"] = row
            stored = probes.get(r["key"], {}).get(tag, {}).get("channels")
            if tag != "g39" or stored is None:
                continue
            ids = np.asarray(stored["world_ids"])
            variants = {"real": cfg, "food_constant": _variant(cfg, **PROBE_VARIANTS["food_constant"])}
            if cfg.world.food_sensing == "stereo":
                variants["food_mean"] = _variant(cfg, **PROBE_VARIANTS["food_mean"])
            for name, vcfg in variants.items():
                probe_rows[f"{r['key']}-{tag}/{name}"] = _replay(vcfg, iface, champ, ids, stored["probe_seed"],
                                                                 args.device, stored["scores"][name])

    def summary(rows):
        return {"evaluations": len(rows),
                "off_reproduces_all": all(v["off"]["equal"] for v in rows.values()),
                "off_unequal": sorted(k for k, v in rows.items() if not v["off"]["equal"]),
                "on_changed": sum(not v["on"]["equal"] for v in rows.values()),
                "on_max_abs_diff": max(v["on"]["max_abs_diff"] for v in rows.values()),
                "on_max_abs_mean_change": max(abs(v["on"]["mean_change"]) for v in rows.values())}
    return {"seconds": time.perf_counter() - t, "holdouts": summary(holdouts), "probes": summary(probe_rows),
            "loaded_switch_values": sorted({str(v["loaded_switch"]) for v in holdouts.values()}),
            "per_holdout": holdouts, "per_probe": probe_rows}


def main():
    ap = argparse.ArgumentParser(allow_abbrev=False)
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--save-reference", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--published", action="store_true")
    ap.add_argument("--in-replay", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--tag", default="run")
    ap.add_argument("--runs02", default=str(ROOT / "runs" / "exp02-screening"),
                    help="where 02's champion .npz files are (local; not committed)")
    ap.add_argument("--result", default=None)
    args = ap.parse_args()
    if sum((args.save_reference, args.compare, args.published)) != 1:
        raise SystemExit("choose one of --save-reference, --compare, --published")
    if args.in_replay:
        # the child's counts under "measure", written even if it fails (D092)
        with acct.child_ledger(), replay_mode(warn=False), acct.category("measure"):
            run_mode(args, "replay_mode")
        return
    prov = provenance()
    if prov["dirty"] and not args.quick:
        raise SystemExit("uncommitted changes in wormwars/, scripts/ or configs/: commit first")
    res = {"provenance_at_start": prov, "device": args.device, "torch": torch.__version__,
           "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
           "switch_present": has_switch(), "quick": args.quick, "modes": {}}
    if args.published:
        if not has_switch():
            raise SystemExit("--published needs the changed engine")
        with acct.category("measure"):
            res["published"] = published(args)
        path = Path(args.result) if args.result else OUT / "published.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(json.dumps({k: v for k, v in res["published"].items() if not k.startswith("per_")}, indent=1))
        return
    with acct.category("measure"):
        for mode in ("default", "replay_mode"):
            res["modes"][mode] = one_mode(args, mode)
    name = f"reference-{args.device}.json" if args.save_reference else f"compare-{args.device}.json"
    path = Path(args.result) if args.result else OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(res, indent=1), encoding="utf-8")
    summary = {m: {k: v for k, v in r.items() if k in ("passed", "reference_repeats_all_equal", "seconds")}
               for m, r in res["modes"].items()}
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    if "--in-replay" in sys.argv:
        main()
    else:
        from wormwars.accounting import run_script
        run_script(main, out_default=str(OUT), default="measure", name="t1_equivalence")
