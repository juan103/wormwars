"""M4d: tables behind the results write-up, after the data, from the panel records, readings.json, companion.json and
the hosts' and blocks' records (no simulation): every class by arm, every host's counts, the contrasts with each end of
the unresolved box, the blocks, the write and read measures, the unresolved genomes' reasons and the companion.
blocks.json holds N2's C3 weights, so it stays local (rule 1); this script writes blocks-summary.json from it (counts
and the file's sha256, no entries and no per-neuron degrees), and reads the summary when the local file is missing. A
local blocks.json whose sha256 differs from a saved summary's stops the script instead of overwriting the summary.
MEMORY_M4D_OUT, as for m4d.py, points it at another run's output folder.
    py scripts/memory_m4/m4d_tables.py > runs/memory-m4d/tables.txt"""
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m4d_read as R  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("MEMORY_M4D_OUT", ROOT / "runs" / "memory-m4d"))
ARMS = ("I", "D", "R", "Rr", "P", "T", "T+G")
CODES = ["separate states", "separate states, read-out silent", "fading", "persistent oscillation", "unresolved"]


def panel(name, arm):
    return json.load(open(OUT / "arms" / f"{name}__{arm.replace('+', 'p')}.json"))


def check_digest(s, digest):
    """A saved summary must name the local blocks.json's sha256: a differing file stops the script."""
    if s.exists() and json.load(open(s))["sha256"] != digest:
        raise SystemExit(f"blocks.json's sha256 {digest} differs from blocks-summary.json's: stop")


def blocks_summary():
    f, s = OUT / "blocks.json", OUT / "blocks-summary.json"
    if f.exists():
        raw = f.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        check_digest(s, digest)
        b = json.loads(raw)
        out = {"source": "blocks.json (local: it holds N2's C3 weights)", "sha256": digest,
               "blocks": [{"host": r["host"], "chains": r["chains"],
                           "arms": {a: {"edges": x["edges"], "weight": x["weight"], "autapses": x["autapses"],
                                        "reciprocal": x["reciprocal"],
                                        "in_degree_range": [min(x["in_degree"]), max(x["in_degree"])],
                                        "out_degree_range": [min(x["out_degree"]), max(x["out_degree"])]}
                                    for a, x in r["blocks"].items()}} for r in b["blocks"]]}
        json.dump(out, open(s, "w"), indent=1)
    return json.load(open(s))


def overlap(hosts, a, b):
    """Genomes (host and genome id) classified separate states in both arms, in a only, in b only."""
    both = only_a = only_b = 0
    for h in hosts:
        x = [k in (0, 1) for k in panel(h, a)["class"]]
        y = [k in (0, 1) for k in panel(h, b)["class"]]
        both += sum(p and q for p, q in zip(x, y))
        only_a += sum(p and not q for p, q in zip(x, y))
        only_b += sum(q and not p for p, q in zip(x, y))
    return both, only_a, only_b


def main():
    r = json.load(open(OUT / "readings.json"))
    hosts = r["counts"]["hosts"]
    n = r["counts"]["n"]
    print(f"{len(hosts)} hosts x {n} genomes; reading: {r['reading']}\n(before the unresolved bounds: "
          f"{r['reading_before_bounds']})")

    print("\n== every class by arm, pooled over the ten hosts (10 240 genomes per arm)")
    print("  arm   " + " / ".join(CODES) + "; panels valid; eligible (a >= START_FLOOR); not settled (oscillation +"
          " unresolved)")
    secs = {}
    for a in ARMS:
        c, valid, elig, s = Counter(), 0, 0, 0.0
        for h in hosts:
            p = panel(h, a)
            c.update(p["class"])
            valid += p["valid"]
            elig += p["eligible"]
            s += p["seconds"]
        secs[a] = s
        print(f"  {a:5s} " + " / ".join(str(c.get(k, 0)) for k in range(5)) + f"; {valid}/10; {elig}; "
              f"{c.get(3, 0) + c.get(4, 0)}")

    print("\n== separate states (and unresolved) per host and arm, of 1024")
    print("  host                 " + "".join(f"{a:>9s}" for a in ARMS))
    sep, unr = r["counts"]["separate"], r["counts"]["unresolved"]
    for i, h in enumerate(hosts):
        print(f"  {h:20s} " + "".join(f"{sep[a][i]:>5d} ({unr[a][i]:d})".rjust(9) for a in ARMS))
    print("  total                " + "".join(f"{sum(sep[a]):>5d} ({sum(unr[a]):d})".rjust(9) for a in ARMS))
    print("  rate (%)             " + "".join(f"{100 * sum(sep[a]) / (n * len(hosts)):9.2f}" for a in ARMS))
    print("  with unresolved (%)  " + "".join(f"{100 * (sum(sep[a]) + sum(unr[a])) / (n * len(hosts)):9.2f}"
                                             for a in ARMS))

    print("\n== the two read contrasts: counted, unresolved all against T (low), all for T (high); hull intervals")
    idx = np.random.default_rng(R.SEED_BOOT).integers(0, len(hosts), (R.B, len(hosts)))
    for b in ("I", "R"):
        for where in ("main", "low", "high"):
            d = R.diffs(sep, unr, n, "T", b, where)
            lo, hi = R.interval(d, idx, r["t_widened"])
            blo, bhi = R.boot_interval(d, idx)
            tlo, thi = R.t_interval(d)
            print(f"  T-{b:2s} {where:4s}: mean {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}] (bootstrap [{blo:+.4f}, "
                  f"{bhi:+.4f}], t [{tlo:+.4f}, {thi:+.4f}]); host max {d.max():+.4f}, min {d.min():+.4f}; hosts above"
                  f" m {int((d > R.MARGIN).sum())}, at or above the guard {int((d >= R.HOST_GUARD).sum())}")
        print(f"  T-{b} envelope over every assignment: [{r['envelope']['D_T' + b][0]:+.4f}, "
              f"{r['envelope']['D_T' + b][1]:+.4f}]")
    # can any assignment make T-R's lower bound pass m? The bootstrap's lower bound rises with every host's difference,
    # so every assignment but the all-for-T end is at or below that end with one host one genome lower
    hi, lo = R.diffs(sep, unr, n, "T", "R", "high"), R.diffs(sep, unr, n, "T", "R", "low")
    one_down = []
    for h in range(len(hosts)):
        if hi[h] > lo[h]:
            d = hi.copy()
            d[h] -= 1 / n
            one_down.append(R.boot_interval(d, idx)[0])
    print(f"  T-R's highest lower bound: at the all-for-T end bootstrap {R.boot_interval(hi, idx)[0]:+.8f}, Student-t "
          f"{R.t_interval(hi)[0]:+.8f}; any other assignment's bootstrap lower bound <= {max(one_down):+.8f} "
          f"(margin {R.MARGIN})")

    print("\n== the descriptive contrasts (not read)")
    for k, v in r["descriptive"].items():
        print(f"  {k:7s} {v['D']:+.4f} [{v['interval'][0]:+.4f}, {v['interval'][1]:+.4f}]; host max {v['host_max']:+.4f}")
    print(f"  hosts with p_T > p_R: {r['hosts_T_over_R']}; with p_T > p_I: {r['hosts_T_over_I']}")
    d = R.diffs(sep, unr, n, "Rr", "R")
    lo, hi = R.interval(d, idx, r["t_widened"])
    print(f"  D_RrR   {d.mean():+.4f} [{lo:+.4f}, {hi:+.4f}]; hosts with Rr > R {int((d > 0).sum())}")
    for a, b in (("R", "D"), ("R", "I"), ("D", "I"), ("T", "Rr"), ("T", "P"), ("T+G", "T")):
        env = R.envelope(R.diffs(sep, unr, n, a, b, "low"), R.diffs(sep, unr, n, a, b, "high"), idx, r["t_widened"])
        print(f"  {a}-{b} envelope over the unresolved: [{env[0]:+.4f}, {env[1]:+.4f}]")
    for a in ("T", "R", "P"):
        print(f"  {a} per host: {min(sep[a])} to {max(sep[a])}")
    d = R.diffs(sep, unr, n, "T", "P")
    print(f"  T-P per host: {d.min():+.4f} to {d.max():+.4f}")
    print("  the same genome (host and genome id) separate states in both arms:")
    for a, b in (("T", "P"), ("T", "R"), ("T", "T+G"), ("R", "Rr")):
        both, only_a, only_b = overlap(hosts, a, b)
        print(f"    {a} and {b}: both {both}, {a} only {only_a}, {b} only {only_b}")

    print("\n== by ensemble (separate states summed over its two hosts, of 2048)")
    for e, v in r["by_ensemble"].items():
        print(f"  {e:10s} " + "  ".join(f"{a} {v[a]}" for a in ARMS))

    print("\n== the blocks (from blocks-summary.json): off-diagonal edges, their weight, autapses, reciprocal pairs; and"
          " the host's own")
    bs = blocks_summary()
    hrec = json.load(open(OUT / "hosts.json"))["hosts"]
    for hb, hr in zip(bs["blocks"], hrec):
        arms = hb["arms"]
        print(f"  {hr['name']:20s} I {hr['edges']:3d} edges, weight {hr['weight']:5.0f}, autapses {hr['autapses']}, "
              f"reciprocal {hr['reciprocal']:2d} | " + "; ".join(
                  f"{a} {x['edges']}/{x['weight']:.0f}/{x['autapses']}/{x['reciprocal']}" for a, x in arms.items()))
    print(f"  blocks.json sha256 {bs['sha256']}")

    print("\n== write and read by arm (pooled medians over all genomes; read-out difference over separate-states genomes;"
          " silent share over separate-states genomes at or above the floor)")
    for a, m in r["measures"].items():
        print(f"  {a:5s} write {m['write_sq_median']:.3f}, on C3 {m['write_core_median']:.3f}, zero {m['write_zero']}; "
              f"read-out difference {m['readout_difference_separate_median']:.3f}; silent share above the floor "
              f"{m['silent_share_above_floor']:.3f}; invalid panels {m['invalid_panels']}; unresolved > 5% "
              f"{m['unresolved_over_5pct']}")

    print("\n== the unresolved genomes' reasons, by arm: genomes whose reason names each failure (a reason can name"
          " several), of the arm's unresolved")
    for a in ARMS:
        c, tot = Counter(), 0
        for h in hosts:
            p = panel(h, a)
            for x, k in zip(p["reason"], p["class"]):
                if k == 4:
                    tot += 1
                    c.update({y.strip() for y in x.split(";")})
        print(f"  {a:5s} ({tot}) " + "; ".join(f"{k} {v}" for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))))

    print("\n== the companion: M4c's 141 N2 switch genomes' C3 parameters on fresh exteriors (selected) against the same"
          " fresh genomes unchanged (control); separate states of 141")
    comp = json.load(open(OUT / "companion.json"))
    tot = Counter()
    for p in comp["parts"]:
        k = sum(x in (0, 1) for x in p["class"])
        u = sum(x == 4 for x in p["class"])
        tot[(p["where"] == "N2", p["which"])] += k
        print(f"  {p['where']:20s} {p['seed']} {p['which']:8s} {k:3d} (unresolved {u}); valid {p['valid']}")
    print(f"  N2 total: selected {tot[(True, 'selected')]} of 282, control {tot[(True, 'control')]} of 282; hosts total: "
          f"selected {tot[(False, 'selected')]} of 1410, control {tot[(False, 'control')]} of 1410")
    for which in ("selected", "control"):
        n2 = [x for p in comp["parts"] if p["where"] == "N2" and p["which"] == which for x in p["class"]]
        hs = [x for p in comp["parts"] if p["where"] != "N2" and p["which"] == which for x in p["class"]]
        print(f"  {which}: N2 classes {dict(sorted(Counter(n2).items()))}; hosts unresolved {hs.count(4)}")
    sw = [[x in (0, 1) for x in p["class"]] for p in comp["parts"] if p["where"] == "N2" and p["which"] == "selected"]
    print(f"  distinct donor genomes separate in at least one N2 redraw: {sum(a or b for a, b in zip(*sw))}; in both: "
          f"{sum(a and b for a, b in zip(*sw))}")

    print("\n== seconds per arm, summed over hosts")
    print("  " + "; ".join(f"{a} {secs[a] / 3600:.2f} h" for a in ARMS) + f"; all {sum(secs.values()):.0f} s, "
          f"{sum(secs.values()) / 3600:.2f} h")


if __name__ == "__main__":
    main()
