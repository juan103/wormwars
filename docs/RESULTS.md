# Measured results

Every number here was measured on this machine by a script in `scripts/`. Nothing is an expectation.

Hardware: NVIDIA GeForce RTX 5080, 16 GB, sm_120, driver 591.86, CUDA 13.1.
Software: Python 3.13.3, torch 2.12.0+cu130 (sm_120 present in `get_arch_list()`), Windows 11.

---

## M0 — environment

`scripts/check_env.py` runs real kernels rather than trusting `torch.cuda.is_available()`:

| check | result |
|---|---|
| 512x512 matmul + tanh + reduce, GPU vs CPU | relative error **0.00e+00** |
| `index_add_` scatter of 10 000 elements | total 10 000, exact |
| verdict | the installed build has sm_120 kernels; no reinstall needed |

---

## M1 — connectome

Cook et al. 2019 hermaphrodite, corrected July 2020, sha256 verified against the published file.

| | |
|---|---|
| neurons | **302** (pharyngeal 20, sensory 83, inter 81, motor 116, other 2) |
| chemical edges | 3 709 directed, including 38 autapses |
| gap junctions | 1 091 undirected |
| `max abs(G - G^T)` as published | **0** — no symmetrisation needed |
| interface neurons resolved by individual name | **39 / 39** |
| weight quantity | `em_sections` (total EM serial sections; **not** a synapse count) |

Somatic-pharyngeal connectivity, measured: gap `I1L-RIPL` = 2, `I1R-RIPR` = 2, chemical
`M1 -> RIPL` = 1, and nothing else. All pump control in N2 must pass through that two-neuron bridge.

---

## M2 — brain

Genome: **5 404** parameters (3 709 W + 1 091 G + 302 tau + 302 bias).

**Timestep refinement** — relative deviation from a 512-substep reference over 40 ticks:

| genome | substeps 2 | 4 | 8 | 16 |
|---|---|---|---|---|
| random | 0.0423 | 0.0176 | **0.0083** | 0.0040 |
| every bound saturated | 0.0127 | 0.00021 | **0.00001** | 0.00001 |
| all tau at `tau_min`, all G at `g_max` | 0.00054 | 0.00002 | **0.00001** | 0.00002 |

First-order convergence confirmed (error halves per halving of dt). **substeps = 8** chosen, worst
case 0.83%. The *extreme* corner is not the hard case; a random genome with tau spread across the
allowed range is.

**Dense vs sparse** — one strain, 4 096 weys, 6.46% mask density:
dense `bmm` **0.467 ms/tick** vs sparse CSR **2.513 ms/tick**. Dense wins by **5.4x**.

Brain-only throughput: 5-6 M wey-ticks/s (64 strains x 2 048 weys = 131 072 weys at 26.3 ms/tick,
1.29 GB peak).

---

## M3 — foraging world

- **Energy ledger** balances to < 1e-5 relative, every tick, over 300-tick rollouts, including runs
  where most of the swarm starves.
- **Wall behaviour**: 17.9% of wey-ticks within 2 cells of a wall, against ~30% for a uniform
  distribution in a 24-cell arena — weys are not attracted to walls.
- **Crowding**: a swarm forced into a 0.06-cell cloud disperses to 2.45 cells std within 120 ticks;
  weys in the single densest cell go 20 -> 2; max body density 3.89 -> 1.44.
- **Movement**: mean step 0.085 cells/tick against a 0.35 maximum (24%) for random genomes.
- **Selection signal**: final swarm energy across 32 random strains spans 0 to 447, std 91.
- World throughput: ~1.0 M wey-ticks/s at 256 worlds x 20 weys on the 5080.

Viewer output was inspected before any score was trusted; it is what caught Gaussian food patches
leaking food into every cell and a metabolic rate low enough that doing nothing was survivable.

---

## M4 — reproducible improvement

3 independent runs, 30 generations, population 32, 8 worlds/strain, 400 ticks, at the final
shipped configuration. Scores are held-out world ids **never used for selection**.

| run | champion | random mean | best of 32 random | ratio |
|---|---|---|---|---|
| 0 | 1.414 | 0.390 | 0.980 | 3.62x |
| 1 | 1.398 | 0.459 | 1.179 | 3.04x |
| 2 | 1.382 | 0.446 | 1.027 | 3.10x |

**champion 1.398 ± 0.013 vs random 0.432 ± 0.030.** Every run beat not just the average random
strain but the **best of 32** random strains. Total cost: **0.071 GPU-hours**.

Not an exploit: champions keep 16.0-18.5 of 20 weys alive (random: 6.2-6.9) and remove 443-479
units of food from the map (random: 112-126). They forage; they do not farm corpses.

---

## M6 — combat geometry

Measured over an 8x8 grid of sub-cell placements, because exact lattice placement measures the grid
rather than the geometry. Damage per tick at the final settings (`body_length` 2.4,
`attack_offset` 0.9, `attack_blur` 1, `head_armor` 0.25, `damage_k` 0.55):

| gap | head-on A / B | T-bone A / B | rear A / B |
|---|---|---|---|
| 0.40 | 0.0764 / 0.0840 | **0.0000** / 0.1203 | **0.0000** / 0.1241 |
| 0.90 | 0.0611 / 0.0687 | **0.0000** / 0.1203 | **0.0000** / 0.1146 |
| 1.40 | 0.0306 / 0.0382 | **0.0000** / 0.1203 | **0.0000** / 0.0840 |
| 1.90 | 0.0153 / 0.0153 | **0.0000** / 0.1203 | **0.0000** / 0.0611 |

- **T-boned payback 0.000**, **rear-bitten payback 0.000** (configured limit 0.10)
- **head-on asymmetry 1.17** (limit 1.50), peaking at 0.084 damage against 0.120 for a flank

So head-on is even *and* weak, and flanking is a 1.43x better trade before counting that it costs
nothing. A continuously flanked wey dies in ~100 ticks; a head-on grind takes ~170.

The first attempt failed both targets (T-bone payback 0.556, head-on asymmetry 5.0) because the body
was shorter than the attack blur. See `DECISIONS.md` D019.

---

## M5 — N2 / SH / RD foraging comparison (pipeline check, K=3, R=2)

Held-out foraging score, hierarchical bootstrap over graphs and runs, 18 runs, 0.345 GPU-hours:

| condition | score | graphs x runs |
|---|---|---|
| N2 | **1.369** [1.266, 1.470] | 1g x 6r |
| SH | **1.550** [1.427, 1.657] | 3g x 6r |
| RD | **1.501** [1.433, 1.577] | 3g x 6r |

| contrast | difference | P(first > second) | verdict |
|---|---|---|---|
| N2 - SH | -0.181 [-0.329, -0.030] | 0.009 | **N2 < SH** |
| N2 - RD | -0.132 [-0.260, -0.006] | 0.020 | **N2 < RD** |
| SH - RD | +0.049 [-0.084, +0.176] | 0.767 | no separation |

The same ordering holds for speed of improvement (area under the fitness curve: N2 1.376,
SH 1.434, RD 1.515) and for score per GPU-hour. N2's mean sits below **all six** SH and RD graph
means individually.

**The real wiring did worse than both controls on this task.** Two things were then checked:

- *Not a bounds artifact.* Champions are nowhere near the parameter bounds, and all three conditions
  use the parameter space identically: |W| at bound 0.004% (N2) / 0.009% (SH) / 0.013% (RD),
  G at zero 12.6% / 13.3% / 14.3%, tau median 3.10 / 3.11 / 3.01.
- *There is a confound.* The raw magnitude of the motor read-out is a property of the graph, and N2
  is the weakest of all seven graphs tested: mean |forward| before gain 0.0815 for N2 against
  0.102-0.159 for the controls. `forward_gain` was tuned on N2, so under a single fixed gain the
  controls simply move more before evolution starts, and foraging rewards moving.
  `wormwars/calibration.py` equalises this; M9 reports the experiment **both ways**.

Graph distances, measured, sensors to motors (chemical + gap, shortest path):

| graph | mean | max | sensors to pump (MC) |
|---|---|---|---|
| N2 | 1.35 | 3 | **3, 3** |
| SH1-3 | 1.00-1.05 | 1-2 | 1-2 |
| RD1-3 | 1.05-1.40 | 2 | 1-2 |

N2's pump neurons are three hops from any sensor because everything must pass the two-neuron
RIP-I1 bridge; in every control they are one or two. Predicted in `DECISIONS.md` D008 before the
experiment was run.

---

## M7 — coevolution

2 runs, 20 generations, population 16, 40 v 40, stage 1, 0.069 GPU-hours.

| | run 0 + run 1 |
|---|---|
| score vs the frozen suite, first measured generation | **+0.059 ± 0.026** |
| score vs the frozen suite, final generation | **+0.156 ± 0.005** |
| improved | **2 / 2 runs** |
| share of damage landed on mid/tail rather than head, final generation | **0.884** |

Coevolved swarms learned to flank: 88% of the damage they deal lands on an enemy's flank or tail
rather than its head, which is exactly what the measured combat geometry rewards.

Paired evaluation is exact: a match played as (A=swarm0, B=swarm1, sides unswapped) and as
(B=swarm0, A=swarm1, sides swapped) gives **exactly negated scores**, asserted as a test. That holds
because spawn jitter is drawn per *side* in a fixed order, so a side swap is a pure relabelling.

---

## M8 — foraging still evolves when eating requires pumping

Stage 2: eating demand is scaled by pump intensity and pumping costs energy every tick, so a wey
must learn to open its mouth as well as find food. 3 runs, 30 generations, held-out seeds.

| run | champion | random mean | best of 32 random | ratio |
|---|---|---|---|---|
| 0 | 0.874 | 0.119 | 0.325 | 7.33x |
| 1 | 0.781 | 0.095 | 0.281 | 8.26x |
| 2 | 0.775 | 0.080 | 0.273 | 9.74x |

**champion 0.810 ± 0.045 vs random 0.098 ± 0.016**, every run above the best of 32 random strains.
The *ratio* is much larger than at stage 0 (8.3x vs 3.2x) because random weys are far worse when
eating is gated: 0.098 against 0.432. Absolute scores are lower in both arms, as they should be --
pumping costs energy and pumping at nothing wastes it.
