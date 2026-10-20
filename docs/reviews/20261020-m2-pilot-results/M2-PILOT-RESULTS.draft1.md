# M2 pilot: validating a dynamical census — results

*Draft 1, 2026-10-20, before review. Exploratory: the plan ([`M2-PILOT-PLAN.md`](M2-PILOT-PLAN.md), draft 9, agreed by
Astra 6 and Fable 5.1 after nine rounds) fixed the sample, the classifier, its thresholds and the checks R1 to R6
before anything ran; nothing here is a pre-registration. Numbers come from `runs/memory-m2/`: `summary.json`, the
stage records (`sample.json`, `classes__`, `r3__`, `r4__`, `r5__<graph>.json`, `r4p.json`, `r6.json`) and
`describe.json`, written after the data by [`scripts/memory_m2/describe.py`](../../scripts/memory_m2/describe.py)
from those records (per-genome details; it changes no class and no check). Anything not fixed in the plan is marked
**descriptive** or **after the data**.*

## The run

- Run on 2026-10-20, 16:40 to 17:58 UTC, on the CPU of the tested machine, at commit 6809c25 (D353), all stages in
  order (`runs/memory-m2/pilot_run.txt`, a copy of the local `pilot.log`; exit 0). Compute:
  `runs/memory-m2/pilot-compute-record.json`, a copy of the local `compute.json`: 6.73 × 10⁸ neural updates and
  4714 s (79 minutes), category probe. The plan expected under 4 hours; the projection after the first graph was
  about 1.5 hours, so the 8-hour stop did not apply.
- **The sample:** 467 genomes on five graphs (100 on N2, 104 on SH-recip-2050039, 68 on SH-class-2030099, 96 on
  SH-2010013, 99 on SH-mirror-2040045; `sample.json`), 934 histories.
  - The carriers hold 51%, 50% and 51% of the eligible tick-30 numerator on N2 and the two selected graphs (38, 39
    and 20 genomes, uncapped). On the two reference graphs the cap of 64 binds (118 and 116 genomes would be needed),
    and the 64 hold 37%.
  - M1's cohort: 14 genomes on N2, 64 on SH-recip, 34 on SH-class, none on the two reference graphs.
  - The growers: the pool of eligible genomes that grow over 10 ticks with radius below 1 is 61 on N2, and 0, 2, 1 and
    3 on the four null graphs. So M1's grower diagnostic replicates on this new draw: such genomes are much more common
    on N2 than on these null graphs.

## The checks

| Check | Threshold (the plan's) | Result | Reading |
|---|---|---|---|
| **R1**, 03mc's criterion against the classifier | ≥ 95% of genomes settled at tick 300 reach stable roots in both histories | 420 of 421 (99.8%) | **passes** |
| **R2**, resolution at tick 2000 | ≤ 5% unresolved overall and per graph, ≤ 10% of each graph's tick-30 numerator | 2 of 467 (0.4%); per graph at most 2% (N2), holding 5.7% of the N2 pilot genomes' tick-30 numerator | **passes** |
| **R3**, integration and batch | class agreement ≥ 95% under each variant; every "separate states" history reaches the same root under all four | agreement 99.5% (64 substeps), 99.5% (float64), 100% (batches of 16); no basin change | **passes** |
| **R4**, perturbations at stable roots | every conclusive test that is not a small basin returns | 9990 of 9990 return; none inconclusive, no small basin | **passes** |
| **R4′**, P³² against the tick's automatic derivative | within 10⁻⁸ | largest gap 1.3 × 10⁻¹⁴ over 20 roots; at every located root of the pilot genomes, P and the continuous sign agree | **passes** |
| **R5**, the family of histories | (descriptive) | 216 genomes: none reaches more than two stable roots | **two states** |
| **R6**, the planted genomes | all six named exactly | six of six, the damped spiral rejected by the veto alone | **passes** |

So no check fails, and the classifier goes to the census unrevised by any failure.

**Whose numerator.** The shares in `summary.json` are of the pilot genomes' summed |δy(30)| or |δy(300)| (per graph,
per group, or over R3's graphs), not of a graph's whole eligible numerator over 1024 genomes. The plan's R2 says "each
graph's tick-30 numerator"; the code took the pilot's. The pilot genomes hold 59% of N2's eligible tick-30 numerator
(62%, 72%, 39% and 40% on the others; `describe.json`, after the data), so against the whole numerator every share
of a flagged set is smaller: N2's two unresolved genomes hold 3.4% of it rather than 5.7%. The readings are the same
either way.

Details:

- **R1.** The one settled genome that does not reach stable roots in both histories is N2 genome 349 (see R2). The
  settled genomes it does not cover hold 2.3% of N2's tick-30 numerator and 6.0% of its tick-300 numerator; on the
  other four graphs every settled genome reaches.
- **R2: the two unresolved genomes,** both N2 carriers (`describe.json`):
  - **Genome 26**, an oscillation that no rule could name. Both histories keep a range of about 3.94 over the
    20,000-tick float64 continuation (essentially all of it), but no period between 2 substeps and 50 ticks repeats
    the last three periods. One history's Newton run fails (σ_min 6.5 × 10⁻⁷); the other locates an unstable root
    1.9 away. A cycle longer than 50 ticks or a quasi-periodic orbit would look like this; the plan leaves both
    unresolved, and the pilot does not tell them apart. It holds 3.4% of the N2 pilot genomes' tick-30 numerator.
  - **Genome 349**, in M1's cohort. One history reaches its stable root; the other ends 1.38 × 10⁻³ from a stable,
    accurate root (error bound 6.7 × 10⁻¹¹, σ_min 0.008), just outside the plan's 10⁻³ locating radius, so the
    continuation is not run and the verdict is "located root not reached". At 64 substeps and in float64 (R3) the same
    history reaches that root and the genome is **separate states**; in batches of 16 it stays unresolved. *After the
    data:* this looks like the float32 trajectory stopping short of a poorly conditioned root, but the pilot does not
    test that. It holds 2.3%.
- **R3.** Of 218 representatives, genome 349 is the only one whose class changes, and only under the 64-substep and
  float64 variants (unresolved to separate states, its roots unchanged). Genome 26 stays unresolved under all three,
  with varying reasons. Genome 349 holds 1.4% of the five graphs' pilot genomes' summed tick-30 numerator and 2.6%
  of their tick-300 numerator. No "separate states" genome changes basin. Since the
  pilot finds no persistent oscillation, R3's aliasing check had nothing to test.
- **R4.** 333 roots (distinct, stable, reached by a representative; 49, 156, 88, 20 and 20 by graph), each with ten
  directions (eight random, P's two slowest modes) at three sizes (10⁻⁸, 10⁻⁶, 10⁻⁴): 9990 tests, all returned.
- **R5.** Every "separate states" genome (116) reaches exactly two stable roots from the nine ramp starts, and every
  sampled fading genome (100) one. No start is unresolved. Along the starts (0.25 to 1.75 of the final level), every
  "separate states" genome switches root exactly once (`describe.json`, `r5_switches`): the ramp start chooses
  between two states at a single threshold. Nine starts give a lower bound and cannot show a continuum; R5 reads
  "two states" against "more than two", and the answer is two.
- **R6.** All six planted genomes are confirmed by the float64 simulation and classed exactly (`r6.json`). The
  oscillating ring has a period of 459 substeps and keeps its range (3.041 against 3.041); the integrator cycle has
  473 substeps, its root unstable for the integrator (radius 1.00009 per substep) and stable for the continuous
  system (largest real part −1.25 × 10⁻⁶ per tick). The damped spiral repeats with a period of 473 substeps and keeps 0.939 and 0.943
  of its range, so the period and range rules pass it, and it is rejected by the veto alone: its root, 5 × 10⁻⁵ from
  the orbit's mean, is marginal.

## The classes

| Graph | Genomes | Separate states | Fading | Unresolved |
|---|---|---|---|---|
| N2 | 100 | 14 | 84 | 2 |
| SH-recip-2050039 | 104 | 68 | 36 | 0 |
| SH-class-2030099 | 68 | 34 | 34 | 0 |
| SH-2010013 | 96 | 0 | 96 | 0 |
| SH-mirror-2040045 | 99 | 0 | 99 | 0 |

No genome is "separate states, read-out silent" and none a persistent oscillation. The counts do not change with
the distinct-root threshold at 10⁻⁴ or 10⁻⁸. These are not rates: the groups are chosen, and the census estimates
rates.

**By group (descriptive),** with each class's part of the group's tick-30 and tick-300 numerators (`summary.json`,
`by_group`):
- **M1's cohort is the separate-states genomes.** Of its 112 genomes (14, 64 and 34), 111 are separate states; the
  112th is genome 349, separate states under float64 and 64 substeps. No fading genome is in the cohort, so the
  float32 stall contaminates none of it here. Five separate-states genomes are outside the cohort (N2 genome 666 and
  four on SH-recip), all unsettled at tick 300 by 03mc's range criterion.
- **N2's carriers are mostly fading at tick 30.** Its 38 carriers: 12 separate states holding 37% of the carriers'
  tick-30 numerator and 88% of their tick-300 numerator; 24 fading, holding 57% and 5%; 2 unresolved, 7% and 7%. On
  the selected graphs the separate states hold most of it at tick 30 as well (SH-recip: 35 of 39, 89%; SH-class: all
  20). On the reference graphs every carrier fades.
- **The growers all fade:** the 32 on N2, and the 2, 1 and 3 on the null graphs that have any. Transient growth under
  the ramp-end Jacobian is not separate states in this sample.
- **The controls** all fade (160 genomes).

## Descriptions for the census

- **The 300-tick classification.** The full rules at tick 300 leave 29 genomes unresolved (15 of 100 on N2; 5, 1, 3
  and 5 on the others): 26 with "located root not reached", two with a Newton failure, and one (genome 26) with a
  Newton failure and an unstable root. 27 of them resolve by tick 2000: 23 as fading, 4 (on SH-recip) as
  separate states. **No genome resolved at tick 300 changes class by tick 2000** (`R1.transitions_300_to_2000`). So a
  300-tick follow-up classifies correctly what it classifies, but on N2 it leaves 15% unresolved, which a census at
  R2's thresholds could not accept.
- **The cheaper "reaches" rule** (a located, accurate root within 10⁻³ of the tick-2000 state) agrees with the full
  verdict on all 934 histories: 931 both yes, 3 both no (genome 26's two histories and genome 349's second).
- **Forecasts.** M1's tanh-consistent midpoint forecast of r(30) ranks the observed r(30) well among fading genomes
  (Spearman 0.94, 349 genomes) and barely among separate states (0.15, 116 genomes).
- **Fading slopes.** For all 349 fading genomes, P³²'s predicted late slope of log |δy| matches the slope observed in
  the float64 continuation (medians −0.04207 and −0.04207 per tick, median absolute difference 4 × 10⁻⁷). 307 of them
  are flagged as cancellations (the predicted δy(300) below a tenth of the summed size of its modal terms), so for
  most fading genomes the read-out difference near the root is a small remainder of larger modal parts.
- **The float32 stall.** 345 of the 349 fading genomes end in a stationary stall, with a median |δy(2000)| of
  7.2 × 10⁻⁶; none is above 0.1 a at tick 2000. Three have |δy(300)| above 0.1 a (two N2 carriers and an N2
  grower), none of them in M1's cohort, since none had settled by tick 300. So the contamination that the plan
  guarded against does not occur in this sample.
- **Cost.** The main run of 2000 ticks took 181 s for all 467 genomes; the classification 1198 s (2.6 s a genome on
  average, 3.6 s on N2, which held the long candidate); the whole pilot, its checks included, 79 minutes.

## What the pilot hands the census

The plan's list, answered:
- **The classifier:** no check failed, so none forces a revision. One choice is open for the census plan, *after the
  data*: genome 349 suggests that the 10⁻³ locating radius can turn a float32 stop near a poorly conditioned root into
  "not reached". Running the float64 continuation whenever a stable, accurate root is located, at any distance, would
  let the continuation decide. The census plan should decide this before it runs, not the census.
- **The follow-up length:** 2000 ticks. At 300 ticks N2 leaves 15% unresolved; a census could also classify at 300
  and continue only the unresolved, since no class resolved at 300 changed.
- **The cheaper "reaches" rule:** it agreed on all 934 histories here.
- **Float64, finer integration or fixed batches (R3):** not needed for the class. One genome in 218 depends on
  them, and it is the locating-radius case above.
- **Two states or more (R5):** two. The census can count separate states without counting how many.
- **The cost:** about 3 s a genome to classify after a 0.4 s main run, on the CPU, without the checks.

**What it does not show.** The groups are chosen, so the class counts are not rates. The pilot finds no confirmed
oscillation, so the oscillation rule is tested only on the planted genomes, and genome 26 shows a kind of orbit
(long or irregular) that the rule leaves unresolved by design. The pilot covers five graphs and one probe.

For the roadmap's split, the pilot suggests, without estimating it, that the settling cohort M1 measured is the
separate-states genomes, while N2's tick-30 lead among its largest carriers is more than half fading. The census
estimates both.
