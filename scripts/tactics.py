"""Does coevolution actually produce flanking? Measure it, per run.

    python scripts/tactics.py --runs runs/m7 --out runs/tactics

The original claim -- "88.8% of damage lands on mid/tail, so they learned to flank" -- was an
artifact. Damage is `k * (head_armor * a_head + a_mid + a_tail)`, so an attack field that is uniform
over the victim's body already reads `2 / (2 + head_armor)` = 0.889 with no tactics at all. See
DECISIONS.md D026.

Four numbers per group:

  placement share   where bites land, with the armor multipliers divided back out
  unanswered share  damage dealt by weys that took nothing back in the same tick
  turn-toward rate  how often a bitten wey turned toward the side the bite came from
  flank share       the retracted metric, kept so the retraction can be checked

**There are only two runs.** Everything is reported per run, side by side. No interval over runs is
computed, because an interval over n = 2 says nothing. Spread across strains *within* a run is
reported separately and labelled as such -- it is not a run-level interval and must not be read as
one.

The analytic values (0.889 armor-weighted, 2/3 with armor removed) are reference lines, not nulls:
weys meet each other head-first, so head contacts are more likely than a uniform share before any
tactic exists.
"""

from __future__ import annotations

import argparse
import json
import sys as _sys
from pathlib import Path as _Path

import numpy as np
import torch

_sys.path.insert(0, str(_Path(__file__).resolve().parents[1]))

from wormwars.analysis import chance_flank_share, chance_placement_share
from wormwars.brain import BrainSpec, Genome
from wormwars.config import Config
from wormwars.connectome import load_connectome
from wormwars.evo import SeedPool, load_genome
from wormwars.evo.coevolve import build_schedule, make_frozen_suite, play
from wormwars.interface import load_interface

METRICS = ("placement", "unanswered", "turn_toward", "flank")
LABELS = {
    "placement": "placement share (armour removed)",
    "unanswered": "unanswered damage share",
    "turn_toward": "turns toward the bite",
    "flank": "flank share (RETRACTED metric)",
}
GROUPS = ("random", "generation 0", "final population")


def _ratios(res, matches, n_strains: int, side: str):
    """Pooled ratios for one side, plus the same per candidate strain.

    Pooled means ratio of summed numerators to summed denominators: a match in which almost nothing
    happened must not weigh as much as a real fight.
    """
    dp = res.damage_points if side == "a" else res.damage_points_b
    ap = res.attack_points if side == "a" else res.attack_points_b
    un = res.unanswered if side == "a" else res.unanswered_b
    tt = res.turn_toward if side == "a" else res.turn_toward_b
    col = 0 if side == "a" else 1

    num = {k: np.zeros(n_strains) for k in METRICS}
    den = {k: np.zeros(n_strains) for k in METRICS}
    eaten = np.zeros(n_strains)
    bitten = np.zeros(n_strains)
    for i, m in enumerate(matches):
        a = m.a
        num["flank"][a] += dp[i][1:].sum()
        den["flank"][a] += dp[i].sum()
        num["placement"][a] += ap[i][1:].sum()
        den["placement"][a] += ap[i].sum()
        num["unanswered"][a] += un[i, 0]
        den["unanswered"][a] += un[i, 1]
        num["turn_toward"][a] += tt[i, 0]
        den["turn_toward"][a] += tt[i, 1]
        eaten[a] += res.energy_eaten[i, col]
        bitten[a] += res.energy_from_biting[i, col]

    pooled = {
        k: (float(num[k].sum() / den[k].sum()) if den[k].sum() > 0 else float("nan"))
        for k in METRICS
    }
    per_strain = {}
    for k in METRICS:
        with np.errstate(invalid="ignore", divide="ignore"):
            per_strain[k] = np.where(den[k] > 0, num[k] / np.maximum(den[k], 1e-12), np.nan)
    return {
        "pooled": pooled,
        "per_strain": per_strain,
        "damage": float(den["flank"].sum()),
        "energy_eaten": float(eaten.sum()),
        "energy_from_biting": float(bitten.sum()),
        "strains_with_damage": int((den["flank"] > 0).sum()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/m7")
    ap.add_argument("--worlds", type=int, default=8)
    ap.add_argument("--out", default="runs/tactics")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    args = ap.parse_args()

    run_dir = _Path(args.runs)
    bundle = json.loads((run_dir / "bundle.json").read_text(encoding="utf-8"))
    bargs = bundle["extra"]["args"]
    cfg = Config.from_dict(bundle["config"])

    con = load_connectome()
    iface = load_interface(con)
    spec = BrainSpec.from_connectome(con, device=args.device)
    pop_size = int(bargs["population"])
    seeds = [int(bargs["base_seed"]) + i for i in range(int(bargs["runs"]))]

    # The frozen suite is REGENERATED from its seed rather than read from a file. It is an
    # unevolved population, so its weights are proportional to the connectome's anatomical
    # weights, and this project does not redistribute those (see NOTICE and DECISIONS.md D028).
    # make_frozen_suite is deterministic, so this reproduces the suite the runs actually used.
    suite, suite_meta = make_frozen_suite(
        spec, cfg, n=cfg.evo.suite_size, device=args.device
    )

    ref = {"flank": chance_flank_share(cfg.combat), "placement": chance_placement_share(cfg.combat)}
    print(
        f"frozen opponent suite (regenerated from seed): {suite.n_strains} RANDOM-WEIGHT strains, never evolved for "
        f"anything -- not for foraging, not for combat. Diversity comes from spreading the "
        f"initialisation scale ({suite_meta.get('init_scales')})."
    )
    print(f"reference lines (NOT nulls): flank {ref['flank']:.4f}, placement {ref['placement']:.4f}")
    print(
        f"{len(seeds)} runs x {pop_size} strains vs the suite on {args.worlds} held-out worlds "
        f"at {tuple(cfg.evo.coevo_sizes)}, {cfg.world.max_ticks} ticks, {args.device}\n"
    )

    data: dict[str, dict] = {}
    for run_i, run_seed in enumerate(seeds):
        pool = SeedPool(cfg, run_seed)
        ids = pool.holdout[: args.worlds]
        groups = {
            "random": Genome.random(
                spec, cfg.brain, pop_size,
                generator=torch.Generator(device=args.device).manual_seed(run_seed + 900_000),
                device=args.device,
            ),
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
            rng = np.random.default_rng(run_seed)  # identical schedule for every group
            matches = build_schedule(
                genome.n_strains, suite.n_strains, ids, rng,
                sizes=tuple(cfg.evo.coevo_sizes), lopsided=False,
            )
            res = play(
                cfg, iface, genome, suite, matches, run_seed, args.device,
                combat_stage=1, chunk_worlds=cfg.evo.chunk_worlds,
            )
            data[f"{name}|run{run_i}"] = {
                "group": name, "run": run_i, "run_seed": run_seed,
                "side_a": _ratios(res, matches, genome.n_strains, "a"),
                "side_b": _ratios(res, matches, genome.n_strains, "b"),
            }
            a = data[f"{name}|run{run_i}"]["side_a"]
            print(
                f"  run{run_i} {name:<17} "
                + "  ".join(f"{k} {a['pooled'][k]:.4f}" for k in METRICS)
                + f"   damage {a['damage']:>8.0f}  strains-with-damage {a['strains_with_damage']:>2}"
            )

    def cell(key, group, run, side="side_a"):
        d = data[f"{group}|run{run}"][side]
        return d["pooled"][key] if key in METRICS else d[key]

    print("\n" + "=" * 78)
    print("PER-RUN VALUES. n = 2 runs: no interval over runs is computed, because an interval")
    print("over two numbers says nothing. The two runs are shown side by side instead.")
    print("=" * 78)

    for k in METRICS:
        print(f"\n== {LABELS[k]} ==")
        print(f"{'group':<34} {'run 0':>9} {'run 1':>9}    within-run spread across strains")
        for g in GROUPS:
            sp = []
            for r in (0, 1):
                v = data[f"{g}|run{r}"]["side_a"]["per_strain"][k]
                v = v[np.isfinite(v)]
                sp.append(f"{np.nanmin(v):.3f}-{np.nanmax(v):.3f} (n={v.size})" if v.size else "-")
            print(
                f"{g:<34} {cell(k, g, 0):>9.4f} {cell(k, g, 1):>9.4f}    "
                f"run0 {sp[0]}, run1 {sp[1]}"
            )
        print(
            f"{'frozen suite, same matches':<34} "
            f"{cell(k, 'final population', 0, 'side_b'):>9.4f} "
            f"{cell(k, 'final population', 1, 'side_b'):>9.4f}    (matched comparison, not a null)"
        )
        if k in ref:
            print(f"{'reference line':<34} {ref[k]:>9.4f} {ref[k]:>9.4f}    (not a null)")
        d0 = cell(k, "final population", 0) - cell(k, "final population", 0, "side_b")
        d1 = cell(k, "final population", 1) - cell(k, "final population", 1, "side_b")
        print(f"{'coevolved minus suite':<34} {d0:>+9.4f} {d1:>+9.4f}")

    print("\n== damage dealt, and how much of it either side could deal at all ==")
    print(f"{'group':<34} {'run 0':>12} {'run 1':>12}")
    for g in GROUPS:
        print(f"{g + ' (side A)':<34} {cell('damage', g, 0):>12,.0f} {cell('damage', g, 1):>12,.0f}")
        print(
            f"{'  suite facing it (side B)':<34} "
            f"{cell('damage', g, 0, 'side_b'):>12,.0f} {cell('damage', g, 1, 'side_b'):>12,.0f}"
        )

    print("\n== where each side's energy came from ==")
    print(f"{'group':<34} {'run':>4} {'eaten':>12} {'from biting':>12} {'biting share':>13}")
    for g in GROUPS:
        for r in (0, 1):
            for side, tag in (("side_a", ""), ("side_b", "  suite facing it")):
                e = cell("energy_eaten", g, r, side)
                b = cell("energy_from_biting", g, r, side)
                label = (g if not tag else tag) + (" (side A)" if not tag else "")
                print(f"{label:<34} {r:>4} {e:>12,.0f} {b:>12,.0f} {b / max(e + b, 1e-9):>12.1%}")

    out = _Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    serialisable = {
        key: {
            "group": v["group"], "run": v["run"], "run_seed": v["run_seed"],
            "side_a": {kk: vv for kk, vv in v["side_a"].items() if kk != "per_strain"},
            "side_b": {kk: vv for kk, vv in v["side_b"].items() if kk != "per_strain"},
        }
        for key, v in data.items()
    }
    (out / "tactics.json").write_text(
        json.dumps(
            {
                "source_runs": str(run_dir),
                "n_runs": len(seeds),
                "note": (
                    "n = 2 runs. No interval over runs is computed. The frozen suite is a matched "
                    "comparison, not a null: both sides' numbers come from the same engagements "
                    "and are mechanically coupled."
                ),
                "frozen_suite": {
                    "n": suite.n_strains,
                    "kind": "random weights, never evolved for anything",
                    "init_scales": suite_meta.get("init_scales"),
                },
                "held_out_worlds": args.worlds,
                "sizes": list(cfg.evo.coevo_sizes),
                "ticks": cfg.world.max_ticks,
                "reference_lines": ref,
                "per_run": serialisable,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {out / 'tactics.json'}")


if __name__ == "__main__":
    main()
