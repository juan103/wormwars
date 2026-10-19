"""03h: the exploratory amplitude check after the pilot (D338; the owner's choice of 2026-10-19, after D337's review).

**Exploratory and disclosed.** PILOT.md's amplitude rule fixed 0.25, because the decile shift moved there. This check
is outside that rule: it asks whether a stronger bit reaches random brains, so that the owner can choose between
stopping 03h and a redesign round (Fable, D337). Nothing here is a test of 03h's questions, and no number from it
becomes a registered value without a new design round.

**What runs:** the pilot's 3 graphs, gains, genomes and banks (S1's record, every hash checked), at amplitudes 0.5 and
1.0, under relief and sham at S1's rates:
- the selection bank (256 genomes x 16 worlds) under each condition, the decile selected per condition;
- the selected decile on the test bank (26 x 64 worlds);
- the bit's turn response (PILOT.md §4).
Level is not rerun: with the bit at 0 the interface injects nothing, whatever the amplitude (rule 7, D327). The pilot's
0.25 readings are quoted from `pilot/pilot.json`.

**Readings, per amplitude, and at 0.25 from the pilot's hash-checked arrays:**
- **The decile shift** (relief − sham on the test bank):
  - per graph;
  - its mean, with a 95% interval from 2 000 shared resamples of the test worlds;
  - its between-graph SD;
  - the ratio of the mean to that SD, with the ratio's range from the SD's 90% chi-square bounds (2 degrees of
    freedom), as in `b_power.py` (Fable).
- **On the selection bank, over all 256 genomes:** relief − sham, relief − level and sham − level, per graph and as
  ensemble means with 95% intervals from shared resamples of the 16 selection worlds. Relief − level and sham − level
  tell a relief benefit from sham damage (Astra).
- **Relief − sham over the pilot's level-selected decile,** per graph.
- **The realised counts** of the relief bit and of the injected bit, per condition (Fable, Astra).
- **The turn response's** mean absolute value, per graph.

**The guide, fixed before the run** (Fable, D337, revised by the review of this script). It is a heuristic for
whether to pursue B's rank design with the ASK bit, not a registered rule. The owner decides.
- **Both ratios finite and under 1:** the rank route is not supported at these amplitudes.
  - This does not show that random brains cannot use the bit, or that the ASK relief is exhausted (Astra).
  - Astra's ensemble-mean route rests on the mean shift's interval, reported beside the ratio (Fable).
- **Either ratio at 2 or above:** a redesign round at that amplitude is supported (Fable).
- **Otherwise, or with a ratio undefined** (a zero between-graph SD): the readings go to the owner as they are.
- **Flags.** Any flag means the evidence is discordant. It replaces the branch, and the readings go to the owner with
  the flags printed (Astra):
  - sham − level below 0 by its interval: the difference may be sham damage;
  - an all-genome relief − sham interval above 0 while the ratio is under 1;
  - a ratio of 2 or above whose mean shift's interval includes the 0.25 mean, or whose between-graph SD shrank from
    0.25: the larger ratio is not corroborated (Fable, round 2).
- **The error rates at three graphs** (a non-central t with 2 degrees of freedom; Fable's estimate, checked):
  - with a true ratio of 0.8, one amplitude reads 2 or above about 19% of the time. The larger of two reads so about
    35% of the time if the two are independent, and at most 38% under any dependence (the union bound; Astra);
  - with a true ratio of 2, one amplitude reads under 1 about 7% of the time.
  - So this is a coarse screen.

**Guards, all before any GPU work:**
- a clean, pushed tree, the pilot's records included;
- the pilot's bound implementation unchanged since its bound commit: the library, the driver, the configurations,
  the requirements and the committed inputs (`scripts/e03h.py` `CODE`; Fable, Astra). This script is new since then,
  so it is excluded from that comparison and kept in the clean, pushed check (Fable, Astra, round 2);
- a completed pilot at 0.25 whose chain (G1, S1, G2) is current. The pilot's and the binding's hashes are recorded;
- the environment as the pilot's: Python, numpy, torch, CUDA, the GPU and the connectome (`require_same_env`; Astra);
- step 0's and the pilot's compute ledgers present.

**The cap:** 1.0 GPU-hour for everything before the pre-registration, shared with step 0 and the pilot (0.209 spent).
This check's own budget is 0.3 h within it.
- Both are checked before every unit of work.
- The record notes any overrun at the end.

    python scripts/e03h_amplitude.py             # on CUDA, records to experiments/03h-history-use/development-records/
    python scripts/e03h_amplitude.py --smoke     # tiny, on the CPU, after the pilot driver's smoke stages
    python scripts/e03h_amplitude.py --smoke --device cuda   # the same on CUDA: the preflight
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wormwars import accounting as acct  # noqa: E402
from wormwars import registration as reg  # noqa: E402
from wormwars.connectome import load_connectome  # noqa: E402
from wormwars.e03h import interface_03h, pilot as PL  # noqa: E402
from wormwars.e03h.probes import bit_turn_response  # noqa: E402
from wormwars.exp03 import samplers as SM  # noqa: E402
from scipy import stats  # noqa: E402


def _driver():
    spec = importlib.util.spec_from_file_location("e03h_pilot_driver", ROOT / "scripts" / "e03h.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


P = _driver()
AMPLITUDES = (0.5, 1.0)
BOOT_SEED = 3_671_001  # fresh, outside every earlier seed
OWN_CAP_HOURS = 0.3
GUARDED = P.GUARDED + ["scripts/e03h_amplitude.py", "experiments/03h-history-use/pilot"]
# the pilot's bound implementation; this script is new since the bound commit (Fable, Astra, round 2)
CODE = P.CODE + [":(exclude)scripts/e03h_amplitude.py"]


def out_dir() -> Path:
    return P.out_dir().parent / "amplitude"


def rec_path() -> Path:
    return (out_dir() / "records" if P.SMOKE else P.EXP / "development-records") / "amplitude-check.json"


class Clock(P.Clock):
    """The pre-registration cap: step 0's and the pilot's recorded seconds plus this check's own (P.Clock), with this
    check's own budget inside it."""

    def __init__(self, cap_hours, compute_json, pilot_json):
        super().__init__(cap_hours, compute_json)
        self.pilot_json = Path(pilot_json)

    def own_hours(self) -> float:
        return reg.CapClock.spent_hours(self) + (time.perf_counter() - self.t_start) / 3600

    def spent_hours(self) -> float:
        pilot = json.loads(self.pilot_json.read_text(encoding="utf-8"))["totals"]["seconds_timed"] / 3600
        return super().spent_hours() + pilot

    def check(self) -> None:
        super().check()
        if self.own_hours() >= OWN_CAP_HOURS:
            raise SystemExit(f"the amplitude check's own budget of {OWN_CAP_HOURS} h is reached")


def clock() -> Clock:
    ledgers = [P.out_dir() / "compute.json"] + ([] if P.SMOKE else [ROOT / "runs" / "e03h" / "step0" / "compute.json"])
    if (P.out_dir() / "compute").exists():
        acct.write_aggregate(P.out_dir() / "compute", P.out_dir() / "compute.json")
    missing = [str(p) for p in ledgers if not p.exists()]
    if missing:
        raise SystemExit(f"a compute ledger the cap needs is missing: {missing} (Astra)")
    if (out_dir() / "compute").exists():
        acct.write_aggregate(out_dir() / "compute", out_dir() / "compute.json")
    return Clock(P.cfg()["cap_hours"], out_dir() / "compute.json", P.out_dir() / "compute.json")


def _boot_ci(per_graph_world: list, n_boot: int, seed: int) -> dict:
    """The mean over graphs of per-graph [worlds] values, with a 95% interval from shared resamples of the worlds."""
    x = np.stack(per_graph_world)  # [graphs, worlds]
    rng = np.random.default_rng(seed)
    W = x.shape[1]
    b = np.array([x[:, rng.integers(0, W, W)].mean() for _ in range(n_boot)])
    lo, hi = np.quantile(b, [0.025, 0.975])
    return {"per_graph": x.mean(1).tolist(), "mean": float(x.mean()), "lo": float(lo), "hi": float(hi)}


def selection_bank(sel: dict, level_decile: list, names: list) -> dict:
    """All-genome differences on the selection bank, per graph and as an ensemble mean with its interval, and relief −
    sham over the level-selected decile. `sel[c]` lists [genomes, worlds] per graph."""
    n = P.cfg()["shared_boots"]
    out = {"graphs": names}
    for a, b in (("relief", "sham"), ("relief", "level"), ("sham", "level")):
        out[f"{a}_minus_{b}_all_genomes"] = _boot_ci([(x - y).mean(0) for x, y in zip(sel[a], sel[b])], n, BOOT_SEED)
    out["relief_minus_sham_level_decile"] = [float((x - y).mean(1)[d].mean())
                                             for x, y, d in zip(sel["relief"], sel["sham"], level_decile)]
    return out


def ratio_range(mean: float, sd: float | None, n: int) -> dict:
    """The ratio mean / SD, and its range from the SD's 90% chi-square bounds (as b_power.py; Fable)."""
    if not sd or n < 2:
        return {"ratio": None, "lo": None, "hi": None}
    df = n - 1
    lo_sd, hi_sd = sd * np.sqrt(df / stats.chi2.ppf(0.95, df)), sd * np.sqrt(df / stats.chi2.ppf(0.05, df))
    lo, hi = sorted((float(mean / hi_sd), float(mean / lo_sd)))  # sorted for a negative mean (Astra, round 2)
    return {"ratio": float(mean / sd), "lo": lo, "hi": hi}


def b_part(test_relief: list, test_sham: list) -> dict:
    """The decile shift, its between-graph SD and the ratio, from the selected deciles' test-bank scores."""
    b = PL.b_readings({"relief": test_relief, "sham": test_sham}, P.cfg()["shared_boots"], BOOT_SEED)
    sh, sd = b["decile_shift"], b["U_between_graph_sd"]
    return {"decile_shift": sh, "between_graph_sd": sd, "ratio_mean_to_sd": ratio_range(sh["mean"], sd, len(test_relief))}


def guide(r: dict, base: dict | None = None) -> dict:
    """The docstring's guide: a branch and its flags. `r[amp]` holds `ratio_mean_to_sd`, `decile_shift`,
    `between_graph_sd` and optionally `selection_bank`; `base` is the same at 0.25."""
    ratios = {a: v["ratio_mean_to_sd"]["ratio"] for a, v in r.items()}
    finite = [x for x in ratios.values() if x is not None and np.isfinite(x)]
    flags = []
    for a, v in r.items():
        sb, x = v.get("selection_bank"), ratios[a]
        if sb and sb["sham_minus_level_all_genomes"]["hi"] < 0:
            flags.append(f"{a}: sham − level is below 0 by its interval (the difference may be sham damage)")
        if sb and x is not None and x < 1 and sb["relief_minus_sham_all_genomes"]["lo"] > 0:
            flags.append(f"{a}: the all-genome relief − sham is above 0 by its interval while the ratio is under 1")
        if x is not None and x >= 2 and base is not None and (
                v["decile_shift"]["lo"] <= base["decile_shift"]["mean"]
                or v["between_graph_sd"] < base["between_graph_sd"]):
            flags.append(f"{a}: the ratio is 2 or above, but its mean shift's interval includes the 0.25 mean or its "
                         "between-graph SD shrank from 0.25 (not corroborated)")
    if flags:  # discordance replaces the branch (Astra, round 2)
        branch = "discordant evidence: the readings go to the owner as they are, with the flags"
    elif not ratios or len(finite) < len(ratios):
        branch = "a ratio is undefined: the readings go to the owner as they are"
    elif max(finite) >= 2:
        branch = "a redesign round is supported at the amplitude reaching 2 (the owner decides)"
    elif max(finite) < 1:
        branch = ("the rank route is not supported at these amplitudes; this does not show that random brains cannot "
                  "use the bit (the owner decides)")
    else:
        branch = "in between: the readings go to the owner as they are"
    return {"branch": branch, "flags": flags, "discordant": bool(flags)}


def _pilot_arrays(pilot: dict) -> dict:
    path = P.out_dir() / "states" / pilot["arrays_npz"]
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != pilot["arrays_npz_sha256"]:
        raise SystemExit("the pilot's per-genome arrays are missing or do not match their recorded hash")
    with np.load(path, allow_pickle=False) as z:
        return {k: z[k] for k in z.files}


def run(dv, ck, pilot: dict) -> dict:
    s1 = P.read("sham-rates")
    con = load_connectome()
    sel, test = P.ids("selection"), P.ids("test")
    s_sel, s_test = P.cfg()["run_seeds"]
    bank = json.loads((ROOT / "experiments" / "03-generation0" / "pilot.json").read_text(encoding="utf-8"))["bank"]
    pa = _pilot_arrays(pilot)
    names = [row["name"] for row in s1["graphs"]]
    level_sel = [pa[f"{n}::selection_level"].astype(np.float64) for n in names]
    level_decile = [pa[f"{n}::decile_level"] for n in names]  # the pilot's own, from float64 means (Fable)
    per_amp = {a: {"selection": {"relief": [], "sham": []}, "test_relief": [], "test_sham": [], "counts": [],
                   "turn": []} for a in AMPLITUDES}
    timing, arrays = [], {}
    for row, lv in zip(s1["graphs"], level_sel):
        name = row["name"]
        graph, _ = SM.build(con, P.cfg()["graphs"]["kind"], row["seed"], passes=P.cfg()["graphs"]["passes"])
        if P.graph_sha(graph) != row["graph_sha256"]:
            raise SystemExit(f"{name}: the rebuilt graph does not match S1's hash")
        gains = tuple(row["gains"])
        cfgs = {"level": P.t1("level", gains), "relief": P.t1("relief", gains),
                "sham": P.t1("sham", gains, s1["rates"])}
        g = P.genomes_for(graph, name, cfgs["level"], dv)
        if P.genome_sha(g) != row["genome_sha256"]:
            raise SystemExit(f"{name}: the regenerated genomes do not match S1's")
        for amp in AMPLITUDES:
            iface = interface_03h(con, amp)
            t, ts, counts = {}, {}, {}
            for c in ("relief", "sham"):
                ck.check()
                t0 = time.perf_counter()
                sc, counts[c] = P._scores(cfgs[c], iface, g, sel, s_sel, dv)
                t[f"selection_{c}"] = time.perf_counter() - t0
                top = PL.select_decile(sc.mean(1))
                ck.check()
                t0 = time.perf_counter()
                ts[c], _ = P._scores(cfgs[c], iface, g.select(top.tolist()), test, s_test, dv)
                t[f"test_{c}"] = time.perf_counter() - t0
                per_amp[amp]["selection"][c].append(sc)
                arrays.update({f"{name}::{amp}::selection_{c}": sc, f"{name}::{amp}::test_{c}": ts[c],
                               f"{name}::{amp}::decile_{c}": top})
            ck.check()
            t0 = time.perf_counter()
            with P.mode():
                turn = bit_turn_response(g, cfgs["level"], iface, bank)
            t["turn_response"] = time.perf_counter() - t0
            timing.append({"name": name, "amplitude": amp, **t})
            per_amp[amp]["test_relief"].append(ts["relief"])
            per_amp[amp]["test_sham"].append(ts["sham"])
            per_amp[amp]["counts"].append(counts)  # the relief bit's and the injected bit's, per condition
            per_amp[amp]["turn"].append(float(np.abs(turn).mean()))
            arrays[f"{name}::{amp}::turn"] = turn
    apath = out_dir() / "states" / "amplitude-arrays.npz"
    apath.parent.mkdir(parents=True, exist_ok=True)
    np.savez(apath, **arrays)
    r = {}
    for amp, v in per_amp.items():
        r[str(amp)] = {**b_part(v["test_relief"], v["test_sham"]), "graphs": names,
                       "selection_bank": selection_bank({"level": level_sel, **v["selection"]}, level_decile, names),
                       "realised_food_fell_counts": v["counts"], "turn_response_mean_abs": v["turn"]}
    at_025 = {**b_part([pa[f"{n}::test_relief"] for n in names], [pa[f"{n}::test_sham"] for n in names]),
              "graphs": names,
              "selection_bank": selection_bank({"level": level_sel,
                                                "relief": [pa[f"{n}::selection_relief"] for n in names],
                                                "sham": [pa[f"{n}::selection_sham"] for n in names]},
                                               level_decile, names),
              "turn_response_mean_abs": pilot["readings"]["manipulation"]["turn_response_mean_abs"],
              "pilot_recorded_decile_shift": pilot["readings"]["manipulation"]["decile_shift"],
              "note": "recomputed from the pilot's hash-checked arrays with this check's bootstrap seed; the pilot's "
                      "own interval (seed 3 653 001) is quoted beside it"}
    return {"amplitudes": list(AMPLITUDES), "readings": r, "at_0.25": at_025, "guide": guide(r, at_025),
            "timing": timing, "arrays_npz": apath.name,
            "arrays_npz_sha256": hashlib.sha256(apath.read_bytes()).hexdigest(),
            "note": "exploratory and disclosed (D338); outside PILOT.md's amplitude rule; not a test of 03h's "
                    "questions"}


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--device", default="cpu", choices=["cpu", "cuda"], help="with --smoke only")
    args = ap.parse_args(argv)
    if args.device != "cpu" and not args.smoke:
        raise SystemExit("--device is for smoke runs; the check itself runs on CUDA")
    P.SMOKE, P.SMOKE_DEVICE = args.smoke, args.device
    prov = reg.provenance(GUARDED)
    bound = P.read("bind")
    if not P.SMOKE:
        reg.require_pushed(prov)  # the plan and the pilot's records are public before the run
        reg.require_pins(prov)
        reg.require_same_code(bound["bound_commit"], CODE)  # the pilot's implementation and inputs
    pilot = P.read("pilot")  # completed, and its chain (G1, S1, G2) current, before any GPU work (Fable, Astra)
    if pilot["amplitude"] != P.AMPLITUDE:
        raise SystemExit("the check extends the pilot at 0.25")
    if not P.SMOKE:
        reg.require_same_env(pilot["provenance"], prov)  # the pilot's GPU, CUDA, packages and connectome (Astra)
    upstream = {s: P.sha(P.rec_path(s)) for s in ("bind", "gate", "sham-rates", "gate-sham", "pilot")}
    dv = P.device()
    ck = clock()
    ck.check()
    path = rec_path()
    if path.exists():  # a completed check runs once; a failed attempt is kept beside the retry
        old = json.loads(path.read_text(encoding="utf-8"))
        if old.get("status") == "completed" and not P.SMOKE:
            raise SystemExit(f"{path} has completed: the check runs once")
        k = 1
        while path.with_name(f"{path.stem}.attempt{k}.json").exists():
            k += 1
        path.replace(path.with_name(f"{path.stem}.attempt{k}.json"))
    t0 = time.time()
    doc = {"check": "amplitude", "smoke": P.SMOKE, "device": dv, "provenance": prov, "upstream": upstream,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    try:
        with acct.recorded(out_dir() / "compute", out_dir() / "compute.json", default="measure", experiment="03h",
                           stage="amplitude-check", script="scripts/e03h_amplitude.py"):
            doc.update(run(dv, ck, pilot))
        doc["status"] = "completed"
    except BaseException as e:  # noqa: BLE001  (recorded, then re-raised)
        doc["status"], doc["error"] = "failed", f"{type(e).__name__}: {e}"
        raise
    finally:
        doc["seconds"] = time.time() - t0
        try:  # the aggregate already holds this attempt, so its time is counted once (as the pilot driver)
            doc["over_cap_at_end"] = bool(ck.over_at_end())
            doc["over_own_budget_at_end"] = bool(reg.CapClock.spent_hours(ck) > OWN_CAP_HOURS)
        except Exception as e:  # noqa: BLE001
            doc["over_cap_at_end"] = f"unreadable: {e}"
        reg.write_json(rec_path(), doc, atomic=True)
    g = doc.get("guide", {})
    print(f"amplitude check: {doc['status']} in {doc['seconds']:.0f} s -> {rec_path()}; {g.get('branch', '')}")
    for f in g.get("flags", []):
        print(f"  flag: {f}")
    return doc


if __name__ == "__main__":
    main()
