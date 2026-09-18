# WormWars 01 — measured results

*C. elegans wiring vs. shuffled and random graphs. A foraging null result.*

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

Graph distances, measured over the ten control graphs actually used in M9, shortest path from the
mapped sensors across chemical and gap edges. **Locomotor read-out and pump read-out are reported
separately**, because pooling them was misleading (Corrections C4):

| graph | sensors → locomotor read-out (mean) | max | sensors → pump (MC) |
|---|---|---|---|
| N2 | **1.17** | 2 | **3, 3** |
| SH1–SH5 | 1.00, 1.06, 1.00, 1.00, 1.17 | 1–2 | 1–2 |
| RD1–RD5 | 1.39, 1.06, 1.17, 1.17, 1.28 | 2 | 1–2 |

Two separate facts, and only one of them is large:

- For **locomotion**, N2 is not meaningfully deeper than its controls. Its 1.17 sits inside the
  shuffle range (1.00–1.17) and below RD1 (1.39). Whatever disadvantages N2 on foraging, a longer
  sensor-to-motor path is not obviously it.
- For the **pump**, N2 is clearly deeper: 3 hops against 1–2 in every one of the ten controls,
  because all somatic-pharyngeal traffic crosses the two-neuron `RIP↔I1` bridge. Predicted in
  `DECISIONS.md` D008 before the experiment was run — **and never tested**, because the N2/SH/RD
  comparison was only ever run on foraging with automatic eating.

---

## M9 — full N2 / SH / RD experiment, motor gains calibrated

K=5, R=3: five independent SH graphs and five RD graphs with three runs each, and fifteen runs of
N2, so every condition has **15 runs**. 25 generations, population 32, 8 worlds per strain, 400
ticks. Motor gains calibrated per graph so every condition's random population starts with the same
mean |forward| and |turn|. 45 runs, 0.897 GPU-hours.

### Final held-out score — **no separation**

| condition | score | graphs x runs |
|---|---|---|
| N2 | 1.4115 [1.3661, 1.4526] | 1g x 15r |
| SH | 1.4581 [1.3851, 1.5515] | 5g x 15r |
| RD | 1.4521 [1.3982, 1.5103] | 5g x 15r |

| contrast | difference | P(first > second) | verdict |
|---|---|---|---|
| N2 - SH | -0.047 [-0.148, +0.039] | 0.167 | no separation |
| N2 - RD | -0.041 [-0.113, +0.029] | 0.130 | no separation |
| SH - RD | +0.006 [-0.090, +0.114] | 0.524 | no separation |

N2's mean sits inside the spread of the individual control graphs (SH graph means 1.384-1.607,
RD graph means 1.406-1.530) rather than at either end of it.

### Speed of improvement (area under the fitness curve) — **N2 is slower**

**Speed of improvement** is the mean of the best-of-generation fitness over all 25 generations of
a run — same units as the foraging score (surviving swarm energy divided by starting swarm energy,
dimensionless). A run that climbs earlier has a higher mean, so **lower means slower**. All P
values here are bootstrap tail
probabilities over **20 000 resamples**, so the smallest value distinguishable from zero is
1/20 000; "P < 1/20 000" means no resample favoured the first condition.

| condition | AUC |
|---|---|
| N2 | 1.3586 [1.3441, 1.3732] |
| SH | 1.4586 [1.4329, 1.4836] |
| RD | 1.4705 [1.4385, 1.5056] |

| contrast | difference | P(first > second) | verdict |
|---|---|---|---|
| N2 - SH | **-0.100 [-0.129, -0.070]** | **< 1/20 000** | **N2 < SH** |
| N2 - RD | **-0.112 [-0.150, -0.077]** | **< 1/20 000** | **N2 < RD** |
| SH - RD | -0.012 [-0.055, +0.029] | 0.288 | no separation |

Per GPU-hour, neither contrast separates (P = 0.052 and 0.027 against SH and RD).

### The same experiment without calibration

Identical seeds, one fixed motor gain for every graph. N2's configuration is unchanged by
calibration, so only the controls moved. N2 was nevertheless **re-run from scratch in both arms**
(15 runs each, 1 089 s and 1 070 s of wall clock) and all 15 of its held-out scores and AUC values
came out identical, giving the same 1.4115 in both. That is what was observed on this machine for
this pair of arms; it is **not** a guarantee. `docs/REPRODUCIBILITY.md` states that CUDA
`index_add_` leaves GPU rollouts not bit-exact in general, and that exact reproduction is claimed
only under `replay_mode()`.

| condition | uncalibrated | calibrated |
|---|---|---|
| N2 | 1.4115 [1.3661, 1.4526] | 1.4115 [1.3661, 1.4526] |
| SH | 1.5214 [1.4470, 1.5804] | 1.4581 [1.3851, 1.5515] |
| RD | 1.4825 [1.4343, 1.5379] | 1.4521 [1.3982, 1.5103] |

| contrast | uncalibrated | calibrated |
|---|---|---|
| N2 - SH (final) | **-0.110 [-0.185, -0.026]**, P=0.005 | -0.047 [-0.148, +0.039], P=0.167 |
| N2 - RD (final) | **-0.071 [-0.141, -0.007]**, P=0.014 | -0.041 [-0.113, +0.029], P=0.130 |
| N2 - SH (AUC) | **-0.118 [-0.160, -0.080]**, P < 1/20 000 | **-0.100 [-0.129, -0.070]**, P < 1/20 000 |
| N2 - RD (AUC) | **-0.144 [-0.178, -0.106]**, P < 1/20 000 | **-0.112 [-0.150, -0.077]**, P < 1/20 000 |

So the apparent *final-score* deficit was mostly the motor-scale confound: matching the read-out
magnitude removes it. The *speed* deficit survives calibration essentially intact, and is the more
robust of the two findings.

### What this says

With the nuisance variable removed, on this task, with this interface:

- **no difference in final score at generation 25 is detectable** between the real wiring, its
  degree-preserving shuffles and random sparse graphs of the same size -- a null result on "ends up
  better". This is a failure to detect a difference, not a demonstration of equality: the N2 - SH
  interval [-0.148, +0.039] still admits a deficit of about 10%, and nothing had converged by
  generation 25 (see the README's Limitations), so no claim about a ceiling is made;
- **it improves more slowly**, consistently and with a tight interval -- a *negative* result on
  "evolves faster";
- **shuffles and random graphs showed no detectable benefit over each other** on anything measured,
  so preserving the real degree sequence did not help either.

This is one task, one interface, one search algorithm and one set of bounds. It is not a statement
about biological wiring in general, and the project's README says so in the same words.

---

## M7 — coevolution

2 runs, 20 generations, population 16, stage 1. Absolute progress is the score against the versioned
frozen opponent suite on held-out world ids; the within-generation score is relative and drifts on
its own as the opponents improve, so it is not the measure of anything.

**Fixed 40 v 40**, 0.071 GPU-hours:

| run | frozen suite, first → last |
|---|---|
| 0 | +0.071 → **+0.377** |
| 1 | +0.185 → **+0.310** |

Improved in **2 of 2 runs**. With n = 2 no interval over runs is given, for the same reason as in
the tactics section below.

**Headcounts varying 50–200 per generation, including lopsided pairs** (each played from both spawn
sides *and* with the headcounts swapped), suite scored at the standard 100 v 100, 0.288 GPU-hours:

| run | frozen suite, first → last |
|---|---|
| 0 | +0.168 → +0.165 |
| 1 | +0.096 → **+0.211** |

Improved in **1 of 2 runs**.

Varying the headcount makes the objective non-stationary and progress correspondingly slower, which
is the expected ordering rather than a surprise.

Coevolution improves the score against the frozen suite. It does **not** produce any measurable
combat tactic: see *Tactics* below and the *Corrections* section. An earlier version of this
document claimed that coevolved swarms "learned to flank"; that claim was an artifact and is
retracted (`DECISIONS.md` D026).

Paired evaluation is exact: a match played as (A=swarm0, B=swarm1, sides unswapped) and as
(B=swarm0, A=swarm1, sides swapped) gives **exactly negated scores**, asserted as a test. That holds
because spawn jitter is drawn per *side* in a fixed order, so a side swap is a pure relabelling.

*These numbers are from a re-run after the food economy was fixed to scale with headcount
(`DECISIONS.md` D023); the original 40 v 40 run, on the unscaled economy, went +0.059 → +0.156.
The single-swarm results (M4, M5, M8, M9) are at 20 weys, where the scaling factors are exactly 1,
and are unaffected.*

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

---

## M11 — scaling

`scripts/bench_scaling.py`, RTX 5080. "Thousands of worlds" was a target to measure, not assume:

| worlds | swarms | weys/swarm | total weys | arena | ms/tick | wey-ticks/s | peak VRAM |
|---|---|---|---|---|---|---|---|
| 8 | 1 | 20 | 160 | 24 | 4.77 | 33 511 | 40 MB |
| 128 | 1 | 20 | 2 560 | 24 | 4.92 | 520 258 | 68 MB |
| 512 | 1 | 20 | 10 240 | 24 | 6.29 | 1 627 663 | 158 MB |
| **2048** | 1 | 20 | **40 960** | 24 | 19.53 | **2 097 281** | **520 MB** |
| 64 | 2 | 100 | 12 800 | 72 | 9.38 | 1 365 192 | 146 MB |
| 64 | 2 | 200 | 25 600 | 100 | 13.37 | 1 914 105 | 251 MB |
| 1 (showcase) | 2 | 2000 | 4 000 | 312 | 7.68 | 520 659 | 67 MB |

- **2 048 worlds fit in 520 MB** of a 16 GB card, so the limit here is not memory.
- Below about 512 worlds the tick time is flat at 5-8 ms: the simulation is **kernel-launch bound**,
  not compute bound. Small batches waste the GPU; a rollout should be as wide as it can be.
- A **2 000 v 2 000 showcase** match runs in a 312x312 arena at 520 k wey-ticks/s in 67 MB.
- Chunked rollout agreement on CUDA: max |score difference| **5.96e-08** on scores of order 1.4.
  Bit-identical on the CPU. See `docs/REPRODUCIBILITY.md`.

---

## M10 — ablation, convergence, tactics

45 champions (15 per condition, from the calibrated M9 arm), 93 ablations each, 32 held-out worlds,
paired: every ablation of a champion plays exactly the same worlds. Sensitivity is the fractional
loss against that champion's own unablated baseline (N2 1.404, SH 1.472, RD 1.455 -- matching M9).

Each champion is replayed **at the motor gains it was evolved under**. Getting this wrong the first
time produced baselines of 0.40 for SH champions whose real score is 1.5, and made every number
computed from them meaningless (`DECISIONS.md` D024).

### Implementation checks — true by construction, and not evidence about biology

These silence neurons the sensor/motor map names. They verify the interface is wired as configured.

| ablation | N2 | SH | RD |
|---|---|---|---|
| turn read-out SMDD | +0.459 | +0.464 | +0.259 |
| AVB (forward read-out) | +0.217 | +0.203 | +0.259 |
| AVA (forward read-out) | +0.109 | +0.256 | +0.085 |
| anterior touch ALM/AVM | +0.109 | +0.062 | +0.257 |
| food sensors AWC | +0.059 | +0.159 | +0.075 |
| pump read-out MC | +0.001 | +0.062 | +0.048 |

Silencing the turn read-out costs about 46% of performance, which is what a read-out term should
cost. Silencing MC costs nothing at stage 0, which is also right: nothing reads the pump when eating
is automatic.

### Emergent tests — against matched random ablations

These silence interneurons the map does **not** name, each compared with 16 random ablations matched
on size, neuron class and degree. Mean over 15 champions, +- standard error, with the z-score
against that condition's own matched controls.

| target | N2 | SH | RD |
|---|---|---|---|
| RIA | **+0.396 ± 0.077** (z +1.5) | +0.171 ± 0.054 (z +0.2) | +0.019 ± 0.012 (z -0.5) |
| RIM | +0.234 ± 0.070 (z +0.8) | +0.084 ± 0.027 (z -0.2) | +0.136 ± 0.046 (z +0.3) |
| AIZ | +0.165 ± 0.049 (z +0.7) | +0.151 ± 0.050 (z +0.5) | +0.053 ± 0.024 (z -0.3) |
| AIB | +0.147 ± 0.060 (z +0.3) | +0.173 ± 0.056 (z +0.3) | +0.044 ± 0.017 (z -0.3) |
| AIY | +0.026 ± 0.008 (z -0.3) | +0.208 ± 0.061 (z +0.9) | +0.007 ± 0.009 (z -0.5) |
| RIP-I1 bridge | +0.005 ± 0.004 | +0.000 | +0.000 |

**The honest reading: no emergent target is clearly above its matched random controls.** The largest
effect anywhere is RIA in N2 champions -- silencing two neurons the interface never mentions costs
40% of performance, and it is the only target whose z-score reaches 1.5 -- but a *matched random*
pair of interneurons of the same class and degree costs nearly as much on average. This is precisely
what matched controls are for, and it is why "ablating AIY hurts" would have been the wrong
conclusion to draw from the raw number.

Cutting the **RIP-I1 bridge** costs nothing, in any condition. That is the expected result and a
useful negative control: foraging never uses the pump, so severing the only route to the pharynx
should not matter. It will matter at stage 2, and N2 is the condition with something to lose there.

### Convergence — do independent runs rely on the same neurons?

Correlation between ablation-sensitivity profiles, over all 990 champion pairs:

| comparison | r | pairs |
|---|---|---|
| same graph, different runs (N2) | **+0.205** | 105 |
| same graph, different runs (SH) | +0.181 | 15 |
| same graph, different runs (RD) | +0.101 | 15 |
| different conditions | +0.102 | 675 |

Independent runs on the *same* graph do agree more than pairs drawn across different graphs
(+0.205 vs +0.102 for N2), so there is some convergence -- but it is weak, and the ordering
N2 > SH > RD is well inside the noise at these sample sizes. Evolution is finding many different
solutions on the same wiring, not one.

### Tactics — no evidence of learned flanking

Measured by `scripts/tactics.py`: 2 runs x 16 strains against the same 6 frozen opponents, on the
same 8 held-out world ids, at 40 v 40, 400 ticks. Each figure is a pooled ratio — summed numerators
over summed denominators — so a match in which almost nothing happened does not weigh as much as a
real fight.

**There are two runs.** Every number is given per run, side by side. **No interval over runs is
computed, because an interval over n = 2 says nothing.** The spread quoted across strains is
*within-run* spread and is not a run-level interval.

**What the frozen suite is.** Six **random-weight** strains, never evolved for anything — not for
foraging, not for combat. Their diversity comes from spreading the initialisation scale from 0.5x to
2.0x, not from training (`make_frozen_suite`). It is **regenerated from its seed, not shipped**:
because it is unevolved, its weights are proportional to the connectome's anatomical weights, which
this project does not redistribute (`DECISIONS.md` D028). `make_frozen_suite` is deterministic, so
regenerating it reproduces exactly the opponents the runs faced.

**Why the suite deals heavy damage against coevolved swarms and almost none against random ones.**
Contact is created by whichever side approaches, and biting is automatic once bodies are close. The
same six suite strains, on the same worlds, dealt:

| suite's opponents | damage the suite dealt, run 0 | run 1 |
|---|---|---|
| random strains | **94** | **2** |
| generation 0 | 51 | 7 361 |
| final coevolved populations | **38 063** | **13 244** |

The suite did not become more aggressive; the coevolved swarms came to it.

| metric | group | run 0 | run 1 | within-run spread across strains |
|---|---|---|---|---|
| **placement share** | random | 0.7102 | 1.0000 | n = 2 and n = 1 strains with any damage |
| (armour removed) | generation 0 | 0.8915 | 0.6296 | 0.770–1.000 / 0.622–0.787 |
| | final coevolved | **0.6571** | **0.6613** | 0.629–0.840 / 0.574–0.786 |
| | frozen suite, same matches | 0.6500 | 0.6983 | |
| | *reference line* | *0.6667* | *0.6667* | *not a null* |
| **unanswered damage** | random | 0.5463 | 1.0000 | |
| | generation 0 | 0.8836 | 0.2738 | 0.782–1.000 / 0.243–0.898 |
| | final coevolved | **0.3141** | **0.3559** | 0.142–0.975 / 0.203–0.890 |
| | frozen suite, same matches | 0.5645 | 0.7260 | |
| **turns toward the bite** | random | 0.2609 | 0.0000 | |
| | generation 0 | 0.5590 | 0.5347 | 0.000–0.698 / 0.190–0.943 |
| | final coevolved | **0.4540** | **0.5839** | 0.153–0.552 / 0.475–0.885 |
| | frozen suite, same matches | 0.4908 | 0.4502 | |
| **flank share** (retracted) | final coevolved | 0.8846 | 0.8865 | 0.871–0.955 / 0.843–0.936 |
| | frozen suite, same matches | 0.8813 | 0.9025 | |
| | *reference line* | *0.8889* | *0.8889* | *not a null* |

**The suite is a matched comparison, not a null.** Both sides' numbers come out of the same
engagements and are mechanically coupled — a tick in which A bites B and B bites A is a single event
counted from both sides — and the side that approaches and the side that is approached have
different roles in it. It shows whether the coevolved side's damage is shaped differently from its
opponent's. It does not say what would happen by chance.

Coevolved side minus the suite it was fighting, per run:

| metric | run 0 | run 1 | reading |
|---|---|---|---|
| placement share | **+0.0072** | **-0.0370** | signs disagree — no effect |
| turns toward the bite | **-0.0368** | **+0.1338** | signs disagree — no effect |
| flank share (retracted) | **+0.0033** | **-0.0160** | signs disagree, both tiny |
| unanswered damage | -0.2504 | -0.3701 | same sign both runs — **suggestive at most** |

**There is no evidence that coevolution produced flanking.** Three of the four metrics change sign
between the two runs, which is what no effect looks like. Bites land no further back on enemies than
the opponent's do, and turning toward the bite sits near chance (0.5) with the runs disagreeing.

The unanswered-damage gap is the one metric with a consistent sign across both runs. It is reported
as **suggestive at most and is not interpreted here**: n = 2, the two sides' figures are
mechanically coupled, and their roles in the engagement differ, so the direction of the gap cannot
be read as a tactic either way.

The combat geometry itself is real and was measured directly (M6): a flank costs the victim 0.120
damage per tick and the attacker nothing, against 0.084 each way head-on. The rules reward flanking.
**Evolution did not visibly find it** in 20 generations of a population of 16.

### Where the energy actually came from — coevolved swarms win by eating

From the energy accounting, per swarm, in the same matches:

| group | run | energy eaten | energy from biting | biting's share |
|---|---|---|---|---|
| final coevolved | 0 | **789 393** | 2 651 | **0.3%** |
| frozen suite, same matches | 0 | 181 141 | 3 793 | 2.1% |
| final coevolved | 1 | **683 955** | 468 | **0.1%** |
| frozen suite, same matches | 1 | 184 828 | 1 133 | 0.6% |
| generation 0 | 0 / 1 | 161 431 / 207 062 | 1 / 459 | 0.0% / 0.2% |
| random | 0 / 1 | 133 792 / 120 686 | 4 / 0 | 0.0% |

The coevolved populations take in **4.4x and 3.7x** more energy by eating than the frozen opponents
they beat, while biting supplies **0.1–0.3%** of their energy. This is measured from the energy
ledger, not inferred: coevolution under these settings produced better foragers, and combat barely
contributes to the result.

---

## Showcase — 2000 v 2000, and what it shows

Two strains coevolved at 40 v 40, played at 2 000 a side in a 312x312 arena. Never used for
selection; this is spectacle and a generalisation test, and it is informative precisely because they
fail it.

| match length | result | wey-ticks/s | peak VRAM |
|---|---|---|---|
| 600 ticks (the standard length) | 227 / 2 000 and 352 / 2 000 alive | 453 k | 68 MB |
| 4 070 ticks (scaled with the arena) | 5 / 2 000 and 0 / 2 000 alive, ended early at 3 901 | 469 k | 68 MB |

Looking at the replay explains it. **The swarms barely leave their spawn blocks.** The arena side
grows as sqrt(headcount) while wey speed does not, so crossing a 2 000 v 2 000 map takes about ten
times as long as crossing a 40 v 40 one, and the standard 600-tick match is simply not long enough
for strains that learned to reach food about ten cells away. Most of the deaths are starvation in
place, not combat.

Scaling the match length with the arena (`--scale-ticks`) fixes the travel problem and immediately
creates another: food does not regenerate, and a wey's metabolic cost over 4 070 ticks is about 142
energy against a food supply of 23.5 per wey, so a long match is unsurvivable by construction.

Both are reported rather than tuned away. The honest summary is that **this design does not
generalise across a 50x change in headcount**, for a reason that is structural rather than
accidental: travel time scales with sqrt(headcount) while speed, match length and food per wey do
not. Making the showcase comfortable would mean redesigning the economy around it, which is not what
a generalisation test is for.

---

## Corrections

Things this document previously got wrong, what replaced them, and where the reasoning is recorded.
Nothing is deleted; the retracted claims are stated here so the correction can be checked.

### C1 — "Coevolved swarms learned to flank" (retracted)

**Claimed:** that coevolved swarms learned to flank, because 88.8% of the damage they dealt landed
on an enemy's mid or tail rather than its head. Appeared in the M7 section, the M10 tactics section,
and the README.

**Why it was wrong:** the damage rule weights the head by `head_armor = 0.25` and mid and tail by
1.0, so a uniform attack across the body already gives `2 / 2.25 = 0.8889`. The reported 88.8% is
that reference line. The refutation was already in the recorded data: generation-0 populations
scored 0.881 and 0.879 on the same metric, against final values of 0.884 and 0.897 — it never moved.

**Caught by:** external review before publication, as arithmetic on the damage rule.

**And the reference line is not the null.** Unevolved weys in a dense heap measure 0.793 flank share
and 0.489 placement share, both below the analytic lines, because they meet each other head-first.
The null has to be measured, not derived.

**Replaced by:** three metrics that can move — placement share (armour divided out), unanswered
damage share, and turns-toward-the-bite — compared against the frozen opponent suite inside the same
matches, reported per run because there are only two runs. Result: **no evidence of learned
flanking**; three of the four metrics change sign between the runs. Numbers in *M10 → Tactics*;
reasoning in `DECISIONS.md` D026.

**Not affected:** the M6 combat-geometry measurements (the flank rule itself), the M9 N2/SH/RD
comparison, and the M7 frozen-suite scores. Those are separate measurements and none of them
depended on the flank-share number.

### C2 — M7 coevolution figures superseded by a re-run

The first M7 numbers (+0.059 → +0.156) were measured before food was made to scale with headcount
(`DECISIONS.md` D023). They are superseded by the re-run reported above (+0.128 → +0.343). Both are
kept here; the difference is the corrected food economy at 40 v 40, not a change in method. Results
measured at the development size of 20 weys — M4, M5, M8, M9 — are unaffected, because both scaling
factors are exactly 1 there.

### C3 — tactics figures restated per run, and pooled differently

The first version of the tactics table pooled both runs together and quoted a hierarchical bootstrap
interval over runs and strains, with each strain's ratio weighted equally regardless of how much it
had actually fought. Two things changed:

- **Per run, no run-level interval.** With n = 2 runs an interval over runs is not meaningful. The
  two runs are now shown side by side; spread across strains is reported separately and labelled as
  within-run.
- **Pooled ratios.** Each figure is now summed numerators over summed denominators, so a strain that
  barely fought no longer counts as much as one that fought hard.

The figures therefore differ from the first version (for example the coevolved placement share reads
0.6571 / 0.6613 per run rather than a pooled 0.6725, and unanswered damage 0.3141 / 0.3559 rather
than 0.4991). Both are kept here. The difference is the weighting and the grouping, not a different
measurement, and **the conclusion is unchanged**: no evidence of learned flanking.

### C4 — sensor-to-motor distance was reported with the pump folded in

An earlier version of the M5 section gave N2's mean sensor-to-motor graph distance as 1.35 with a
maximum of 3, against 1.00–1.05 for the shuffles, and used it to suggest that N2 routes through
interneuron layers where the controls go almost straight from sensor to motor.

That figure pooled the locomotor read-out with the **pump** read-out. Separated, and measured across
all ten control graphs rather than three: the locomotor distance is **1.17 for N2** against
**1.00–1.17 for the five shuffles** and **1.06–1.39 for the five random graphs** — N2 is inside the
shuffle range, not outside it. The entire gap was the pump: **3 hops in N2, 1–2 in every control**.

Both are kept. The correction matters because the foraging experiment never used the pump, so the
one place N2 is measurably deeper is the one place the experiment did not look.
