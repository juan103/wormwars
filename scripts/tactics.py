"""Does coevolution actually produce flanking? Measure it properly.

    python scripts/tactics.py --runs runs/m7 --out runs/tactics

The original claim -- "88.8% of damage lands on mid/tail, so they learned to flank" -- was an
artifact. Damage is `k * (head_armor * a_head + a_mid + a_tail)`, so an attack field that is uniform
over the victim's body already reads `2 / (2 + head_armor)` = 0.889 with no tactics at all. See
DECISIONS.md D026.

This script compares three groups under identical conditions -- the same frozen opponent suite, the
same held-out world ids, the same headcounts -- and reports four numbers for each:

  placement share   where bites land, with the armor multipliers divided back out
  unanswered share  damage dealt by weys that took nothing back in the same tick
  turn-toward rate  how often a bitten wey turned toward the side the bite came from
  flank share       the retracted metric, kept so the retraction can be checked

The analytic values (0.889 armor-weighted, 2/3 with armor removed) are printed as **reference
lines, not nulls**. Weys approach shared food head-first, so head contacts need not be as likely as
mid or tail contacts even with no tactic at all. The null is what random and generation-0 strains
actually measure here.
"""

from __future__ import annotations

import argparse
import json
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import torch

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.analysis import chance_flank_share, chance_placement_share, hierarchical_bootstrap
from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import load_genome
from wormwars.evo.coevolve import build_schedule, play
from wormwars.interface import load_interface

METRICS = ("placement", "unanswered", "turn_toward", "flank")
FROZEN = "frozen suite (same matches)"
LABELS = {
    "placement": "placement share (armor removed)",
    "unanswered": "unanswered damage share",
    "turn_toward": "turns toward the bite",
    "flank": "flank share (RETRACTED metric)",
}


def per_strain(res, matches, n_strains: int, side: str = "a") -> dict[str, np.ndarray]:
    """Aggregate per-match tactics into one value per candidate strain.

    Ratios are formed from summed numerators and denominators, not by averaging per-match ratios:
    a match in which almost nothing happened must not count as much as a real fight.

    `side="b"` reads the opponent's numbers out of the same matches, still indexed by the candidate
    it was facing, so the two sides can be compared match for match.
    """
    dp_all = res.damage_points if side == "a" else res.damage_points_b
    ap_all = res.attack_points if side == "a" else res.attack_points_b
    un_all = res.unanswered if side == "a" else res.unanswered_b
    tt_all = res.turn_toward if side == "a" else res.turn_toward_b
    num = {k: np.zeros(n_strains) for k in METRICS}
    den = {k: np.zeros(n_strains) for k in METRICS}
    for i, m in enumerate(matches):
        a = m.a
        dp, ap = dp_all[i], ap_all[i]
        num["flank"][a] += dp[1:].sum()
        den["flank"][a] += dp.sum()
        num["placement"][a] += ap[1:].sum()
        den["placement"][a] += ap.sum()
        num["unanswered"][a] += un_all[i, 0]
        den["unanswered"][a] += un_all[i, 1]
        num["turn_toward"][a] += tt_all[i, 0]
        den["turn_toward"][a] += tt_all[i, 1]
    out = {}
    for k in METRICS:
        with np.errstate(invalid="ignore", divide="ignore"):
            v = np.where(den[k] > 0, num[k] / np.maximum(den[k], 1e-12), np.nan)
        out[k] = v
    out["_damage"] = den["flank"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/m7", help="a coevolution output directory")
    ap.add_argument("--worlds", type=int, default=8, help="held-out world ids per group")
    ap.add_argument("--out", default="runs/tactics")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    run_dir = _Path(args.runs)
    bundle = json.loads((run_dir / "bundle.json").read_text(encoding="utf-8"))
    bargs = bundle["extra"]["args"]
    cfg = Config.from_dict(bundle["config"])
    cfg.evo.suite_worlds = args.worlds

    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=args.device)
    pop_size = int(bargs["population"])
    seeds = [int(bargs["base_seed"]) + i for i in range(int(bargs["runs"]))]

    suite_path = next(run_dir.glob("*frozen-suite*.npz"))
    suite, _ = load_genome(suite_path, spec, cfg.brain, device=args.device)

    ref_flank = chance_flank_share(cfg.combat)
    ref_place = chance_placement_share(cfg.combat)
    print(f"reference lines (NOT nulls): flank share {ref_flank:.4f}, placement share {ref_place:.4f}")
    print(
        f"{len(seeds)} runs x {pop_size} strains vs {suite.n_strains} frozen opponents "
        f"on {args.worlds} held-out worlds at {tuple(cfg.evo.coevo_sizes)}, "
        f"{cfg.world.max_ticks} ticks, device {args.device}\n"
    )

    # group name -> run_seed -> per-strain values for each metric
    GROUPS = ("random", "generation 0", "final population", FROZEN)
    collected: dict[str, dict[str, dict[int, list[float]]]] = {
        g: {k: {} for k in METRICS} for g in GROUPS
    }
    damage_totals: dict[str, float] = {g: 0.0 for g in GROUPS}
    paired: dict[str, dict[int, list[float]]] = {k: {} for k in METRICS}

    for run_i, run_seed in enumerate(seeds):
        from wormwars.evo import SeedPool

        pool = SeedPool(cfg, run_seed)
        ids = pool.holdout[: args.worlds]

        groups = {
            # a population that never saw this game at all
            "random": Genome.random(
                spec, cfg.brain, pop_size,
                generator=torch.Generator(device=args.device).manual_seed(run_seed + 900_000),
                device=args.device,
            ),
            # exactly the population coevolution started from: same construction, same seed
            "generation 0": Genome.random(
                spec, cfg.brain, pop_size,
                generator=torch.Generator(device=args.device).manual_seed(run_seed),
                device=args.device,
            ),
            "final population": load_genome(
                run_dir / f"N2-coevo-run{run_i:02d}.npz", spec, cfg.brain, device=args.device
            )[0],
        }

        for name, genome in groups.items():
            rng = np.random.default_rng(run_seed)  # same schedule for every group
            matches = build_schedule(
                genome.n_strains, suite.n_strains, ids, rng,
                sizes=tuple(cfg.evo.coevo_sizes), lopsided=False,
            )
            res = play(
                cfg, iface, genome, suite, matches, run_seed, args.device,
                combat_stage=1, chunk_worlds=cfg.evo.chunk_worlds,
            )
            vals = per_strain(res, matches, genome.n_strains, side="a")
            damage_totals[name] += float(vals["_damage"].sum())
            for k in METRICS:
                collected[name][k][run_seed] = [float(x) for x in vals[k] if np.isfinite(x)]
            print(
                f"  run{run_i} {name:<28} "
                + "  ".join(f"{k} {np.nanmean(vals[k]):.4f}" for k in METRICS)
                + f"   (damage dealt {vals['_damage'].sum():.0f})"
            )
            if name == "final population":
                # The frozen suite fought exactly these engagements, so it is the one null here
                # guaranteed to have been in as many real fights as the coevolved side.
                opp = per_strain(res, matches, genome.n_strains, side="b")
                damage_totals[FROZEN] += float(opp["_damage"].sum())
                for k in METRICS:
                    collected[FROZEN][k][run_seed] = [
                        float(x) for x in opp[k] if np.isfinite(x)
                    ]
                    both = np.isfinite(vals[k]) & np.isfinite(opp[k])
                    paired[k][run_seed] = [float(x) for x in (vals[k] - opp[k])[both]]
                print(
                    f"  run{run_i} {FROZEN:<28} "
                    + "  ".join(f"{k} {np.nanmean(opp[k]):.4f}" for k in METRICS)
                    + f"   (damage dealt {opp['_damage'].sum():.0f})"
                )

    print()
    rows = {}
    for k in METRICS:
        print(f"== {LABELS[k]} ==")
        boots = {}
        for g in collected:
            groups_for_boot = {str(s): v for s, v in collected[g][k].items() if v}
            b = hierarchical_bootstrap(groups_for_boot, n_boot=20_000)
            boots[g] = b
            print(f"  {g:<18} {b.mean:.4f}  [{b.lo:.4f}, {b.hi:.4f}]   ({b.n_runs} strains)")
        ref = ref_flank if k == "flank" else (ref_place if k == "placement" else None)
        if ref is not None:
            print(f"  {'reference line':<18} {ref:.4f}   (not a null)")
        d = boots["final population"].samples - boots["generation 0"].samples
        lo, hi = float(np.quantile(d, 0.025)), float(np.quantile(d, 0.975))
        verdict = "no separation" if lo <= 0 <= hi else ("higher" if lo > 0 else "lower")
        print(
            f"  final vs generation 0: {float(np.mean(d)):+.4f} [{lo:+.4f}, {hi:+.4f}] "
            f"-> coevolved population is {verdict}"
        )
        d2 = boots["final population"].samples - boots["random"].samples
        lo2, hi2 = float(np.quantile(d2, 0.025)), float(np.quantile(d2, 0.975))
        verdict2 = "no separation" if lo2 <= 0 <= hi2 else ("higher" if lo2 > 0 else "lower")
        print(
            f"  final vs random      : {float(np.mean(d2)):+.4f} [{lo2:+.4f}, {hi2:+.4f}] "
            f"-> coevolved population is {verdict2}\n"
        )
        rows[k] = {
            g: {"mean": b.mean, "lo": b.lo, "hi": b.hi, "n": b.n_runs} for g, b in boots.items()
        }
        rows[k]["final_minus_gen0"] = [float(np.mean(d)), lo, hi]
        rows[k]["final_minus_random"] = [float(np.mean(d2)), lo2, hi2]
        rows[k]["reference_line"] = ref
        # The sound comparison: paired, within the same matches, against opponents that fought
        # exactly as much.
        pb = hierarchical_bootstrap(
            {str(sd): v for sd, v in paired[k].items() if v}, n_boot=20_000
        )
        v3 = "no separation" if pb.lo <= 0 <= pb.hi else ("higher" if pb.lo > 0 else "lower")
        print(
            "  PAIRED coevolved minus frozen suite, same matches: "
            f"{pb.mean:+.4f} [{pb.lo:+.4f}, {pb.hi:+.4f}] -> coevolved side is {v3}"
        )
        print()
        rows[k]["paired_vs_frozen_same_matches"] = [pb.mean, pb.lo, pb.hi]

    out = _Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "tactics.json").write_text(
        json.dumps(
            {
                "source_runs": str(run_dir),
                "held_out_worlds": args.worlds,
                "sizes": list(cfg.evo.coevo_sizes),
                "ticks": cfg.world.max_ticks,
                "reference_flank_share": ref_flank,
                "reference_placement_share": ref_place,
                "total_damage_by_group": damage_totals,
                "metrics": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out / 'tactics.json'}")


if __name__ == "__main__":
    main()
