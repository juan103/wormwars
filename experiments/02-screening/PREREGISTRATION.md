# WormWars 02: pre-registration of the screening

**Fixed on 2026-09-25, before any N2 run.** No N2 brain has been evolved or scored in the experiment-02
task world. The one N2 measurement seen, a generation-0 structural probe, is disclosed in §2. The binding version of this file and of the code is the commit the run's `bundle.json` records
(the last commit before the first N2 run). The design argument is in `DESIGN.md` (v3) and
`DECISIONS.md` D034-D040. Where they differ, this file is binding.

## 1. What this experiment is

A **screening** experiment, capped at 12 GPU-hours. It asks whether the real *C. elegans* wiring
(N2) has an advantage over degree-preserving shuffles (SH), and whether that advantage depends on
the task and on whether food enters through the biologically motivated sensory neurons. It is
also a search for failure modes before a full design. Nothing in it is reported as confirmatory
except the single primary outcome in §4. That outcome is a screening-level test, labelled as
motivated by preliminary evidence.

## 2. Disclosures

1. **The design changed after a failed gate.** The pilot's feasibility gate (`pilot.json`) failed
   as pre-set. A 40-generation champion on a pilot-only shuffle beat the tuned memoryless
   controller, but it was not hurt by the validated history ablation. The capability-use outcomes
   below were added because of that failure. They were not the original plan (D038).
2. **One N2 measurement was seen.** It gave two numbers, both under the M0 mapping: N2's
   generation-0 turn response to a left-right food difference, 0.12 (against 0.009-0.030 for
   eight pilot shuffles), and to common-mode food, 0.16. The probe confounded the difference with
   the total food level, so it does not establish a routing difference. It motivated the primary prediction below. N2 under the
   remapped interfaces was deliberately not looked at. No N2 fitness was seen, evolved or scripted.
3. **Exploration on pilot shuffles** (SH101-SH108, never used in the main runs) is archived in
   `exploration/` with its scripts. It includes 120-generation runs and search-size pilots.
4. **Reviews.** Astra 6 reviewed the go/no-go decision (a conditional go, 11 points, all adopted;
   D038), and then this file (no-go as written, 9 points, all adopted; §11, D040). Every review
   is archived verbatim in `reviews/`.

## 3. Design

**Brains.** N2: 8 runs per cell, seeds 20000-20007. SH: 8 degree-preserving shuffles, SH1-SH8,
2 runs each, seeds 21000 + 10k + run. N2perm1-3 (N2 with anatomical magnitudes permuted within
its mask, the strength control): T1-M0 only, 2 runs each. Every unit's seed is shared across
its cells.

**Tasks** (`grid.task_config`; single swarm of 20; D034):
- **T0, stereo foraging:** odour sigma 1, 200 ticks, food x2, food sensing scale halved,
  pheromone off.
- **T1, single-nose foraging:** T0 with one food sample at the head, copied to both sides.
- **A, 01b anchor:** 01b's world exactly (400 ticks, pheromone 0.35, no odour), M0 only; N2 all
  runs, SH run 0.

**Mappings** of the food channel (`remaps.json`, D036): M0 = AWA, AWC, ASE; R1 = ASJ, ASI, ASG;
R2 = PLN, IL2D, IL2V; MS = FLP, PHB, PVD (T1 only, exploratory shortcut).

**Cells:** T0 x {M0, R1, R2}, T1 x {M0, R1, R2, MS}, A-M0, and the strength control. That is
190 runs: N2 64, SH 120, N2perm 6. Eight runs continue to 80 generations: T1-M0 and T0-M0, each
with N2 runs 0-1 and SH1 and SH2 run 0.

**Held fixed:** 40 generations, population 32, 8 training worlds per strain, 64 held-out worlds
per run, 32 integrator substeps, anatomical-magnitude initialisation with random signs, and each
graph's motor gains calibrated in-world on 2048 genomes (`calibration.json`; every variant
validates within 4% on an independent 2048).

**Frozen inputs,** sha256 of the committed files (first 16 hex digits):

| file | sha256 |
|---|---|
| `remaps.json` | `7082f0ef76ab5b11` |
| `calibration.json` | `1524f8488bfce0ae` |
| `diagnostics.json` | `069873f3609258ad` |
| `probe_validation.json` | `a0450e2cd31c2720` |
| `pilot.json` | `d5c0c8b0168be4bc` |

## 4. The primary outcome

**Estimand.** For a champion c and probe p, U_p(c) is the mean over the 64 probe worlds
(`grid.PROBE_IDS`) of the real score minus the score under p. It is signed: negative means the
probe helped. N2's use is the mean over its runs. SH's use is the mean of the 8 graph means,
each graph's runs averaged first. **Delta_p = N2 - SH.**

**Primary:** Delta for the **bilateral-mean probe** (both sides fed (L+R)/2, D039) in cell
**T0-M0**, generation-39 champions.

**Prediction** (motivated by the disclosed generation-0 number, so labelled): *under this
40-generation procedure, N2 champions show greater, meaningful dependence on bilateral food
information than champions from the sampled shuffle distribution.*

**Interval.** A hierarchical bootstrap with 20 000 resamples and seed 0. N2 runs are resampled
with replacement; SH graphs are resampled with replacement, then runs within each drawn graph.
Each unit's whole vector of cells travels together. 95% percentile intervals.

**Verdict,** with USE = 0.10 score units (about a tenth of the scripted stereo gain of 1.11), a
screening convention for a meaningful absolute use:
- **supported:** Delta's interval lies above 0 and N2's use interval lies above USE;
- **challenged:** N2's use interval lies below USE, or Delta's interval lies below 0;
- **inconclusive:** anything else. A wide interval, or a Delta straddling 0, is inconclusive, not
  a failure. No margin is registered for Delta itself, so a small positive Delta with meaningful
  N2 use counts as support. Its size is reported next to the verdict.
- **withheld:** the primary data are incomplete. The verdict needs, in T0-M0, all 8 N2 runs and
  run 0 of all 8 SH graphs, each with its registered seed (`report.primary_registered_units`).
  Every N2 and SH champion present in the cell also needs real and bilateral-mean scores of 64
  finite values on exactly `grid.PROBE_IDS`, with the run's seed as the probe seed
  (`report.primary_completeness`). A malformed probe entry anywhere is listed in the report and
  left out of every estimate. It is never averaged. These units are in the first 16 batches of the schedule, so
  any budget cut that §8 allows leaves them in. SH second runs in T0-M0 enter the estimate when
  present.

Also reported, with no verdict attached: the same Delta at generation 0 (a starting advantage);
Delta(g39) - Delta(g0) per unit (acquisition); and the mapping interaction
Delta(M0) - mean(Delta(R1), Delta(R2)). The prediction's M0-specific reading is weakened if N2
shows a similar advantage under the remaps. Its acquisition reading is weakened if the difference
is already present at generation 0.

**Not claimed under any result:** that shuffles *cannot* use stereo. The number of SH graphs with
*detected* meaningful use is reported. Each graph's interval comes from a bootstrap over probe
worlds of its run-averaged difference, so it is conditional on the runs made. A capable graph can
stay inconclusive. This is a detection count under this procedure, not a prevalence estimate, and
no bound on prevalence is drawn from it.

## 5. Secondary outcomes (exploratory; intervals reported, no claims drawn)

- **Capability use** (U_p, N2, SH and Delta per cell, generations 0 and 39):
  - swap (T0), single-nose substitution (T0);
  - jitter 1 and jitter 3 (T0, T1): history *sensitivity*, not history use (D039);
  - constant food (T0, T1).
- **Each champion's own use,** with its class (meaningful / below threshold / inconclusive), per
  graph and run.
- **The screening fitness estimates,** on scores normalised per world to the best scripted
  controller on that world, at generations 0 and 39:
  - A(t, m) = N2 - SH;
  - I(t) = A(t, M0) - mean(A(t, R1), A(t, R2));
  - I(T1) - I(T0);
  - variance components of the SH mapping contrast (one-way random effects; unbalanced
    replication handled with the usual n0);
  - leave-one-graph-out.

  No directional prediction is registered. I(t) > 0 would be read as the advantage being
  specific to the biological mapping.
- **Strength control:** N2perm - N2 and N2perm - SH on T1-M0.
- **Generation-0 structure:**
  - input response per graph and mapping (common mode; difference at a fixed common mode,
    signed and absolute, raw and motor; b = 0.1, d = 0.05; 256 strains);
  - anatomical, uniform and permuted magnitudes per graph and mapping (T1, 32 strains, 8 worlds);
  - valence symmetry, with and without gap junctions, for N2 and SH1 under M0 only (128 strains).
- **Integrator:** the interactions at 32 and at 128 substeps, on **raw** scores over the 16
  checkpoint worlds, against the chaos floor.
- **Convergence:** checkpoint curves, fitted per graph family; the generation at which 90% of
  the fitted improvement since generation 0 is complete; the continuation runs.
- **Behaviour,** on 4 checkpoint worlds: speed, turning, wall time, time on food; plant food
  against pellet intake (held-out worlds).

With this many intervals, some will exclude zero by chance. Only §4 carries a verdict.

## 6. Tripwires

Each is reported, fired or not (`analysis.tripwires`). A fired tripwire changes the full design
and the reading of the affected estimates. It never changes the §4 verdict rule. A tripwire whose
input was dropped under §8 is reported as **not assessed**, never as passed.

| tripwire | fires when |
|---|---|
| champions do not use food | the pooled real minus constant-food interval (g39, all champions) is not entirely above 0.10 |
| memory is not worth anything on T1 | the scripted M - K interval on the runs' held-out worlds is not above 0 |
| the anchor disagrees with 01b | the sign of the anchor's N2 - SH estimate differs from 01b's |
| drive is off target | any graph's validation drive is off by more than 4% |
| the integrator matters | the largest shift of I(T0), I(T1) or I(T1) - I(T0), on raw scores, between 32 and 128 substeps exceeds the chaos floor and 0.02 |
| convergence is late | more than a third of fitted cells (graph family x task x mapping) complete 90% of their fitted improvement after generation 40 |
| shortcuts differ | MS's advantage minus the matched remaps' advantage excludes 0 |
| the remaps disagree | R1's advantage minus R2's excludes 0 |
| SH cares about mapping | SH's T1 M0-minus-remap contrast excludes 0 |
| valence is broken | the generation-0 sign flip without gap junctions differs by more than 1e-5 |

If a cell sits at the floor or ceiling of its scripted references, that is recorded as an
observation.

## 7. Probes

The capability suite is validated on scripted controllers in `probe_validation.json`. A probe is
valid when a controller that cannot use the capability moves by less than ±0.02, interval included,
and the capable controller's gain falls. It runs per world on the 64 probe worlds with the run's
seed, for the generation-0 and generation-39 champion of every run. The integrator rescoring uses
the 16 checkpoint worlds and the behaviour measures 4 of them, both on the generation-39 champion
only. Probe
scores are saved per world with their world ids and seed.

## 8. Budget, stop rule and cut order

Measured cost, from the pilot and `exploration/structure_and_timing.json`:
- evolution: about 7.0 h (about 2 min per T0/T1 run, about 3.7 min per anchor run);
- champion probes: about 3.0 h;
- generation-0 probes: about 0.2 h.

The total is about 10.2 h. The approximately 2 GPU-hours of exploration before this file are not
counted against the cap.

- `exp02.py run --max-hours 8.0` stops only between whole batches. The schedule order is the cut
  order. N2 runs are interleaved with each SH graph's first run; then come the SH second runs;
  then the strength control. A cut loses the strength control first, then SH second runs.
- `exp02.py probes --max-hours 12.0` then runs on every completed run, and `exp02.py report`
  follows. The 12 h count includes the evolution wall time recorded in the runs. Stages run in a
  fixed order:
  1. the capability suite on every champion (never dropped);
  2. the generation-0 structure;
  3. integrator rescoring, champion by champion;
  4. behaviour, champion by champion.

  Before each step of stages 3 and 4, the step runs only if time used plus the slowest such step
  so far stays inside 12 h. The first step of a stage has no measured cost yet, so it can overrun
  by that one step. Otherwise the step is recorded in `probes.json` as dropped, so behaviour is
  dropped first. Measured costs and dropped steps persist, so a resumed run never retries a
  dropped step. If any integrator step is dropped, the integrator tripwire is reported as not
  assessed.

## 9. Deviations

Any deviation from this file is recorded in `DECISIONS.md` and in the results, and labelled
there. A crash or bug found mid-run is fixed and recorded. Affected runs are rerun from their
seeds; completed ones are kept only if the bug provably did not touch them.

## 10. What the results decide for the full design

- **§4 supported:** the full design keeps stereo foraging and tests the mechanism (routing
  ablations, remaps) with more graphs.
- **§4 challenged or inconclusive:** the capability question needs longer evolution or a
  different search before a full design.
- **Fitness interactions:** planning ranges for the full design's sample sizes, not conclusions.

Plasticity and a hazard task remain deferred.

## 11. Changes from the team's review of this file

Astra 6 reviewed the first version of this file (`reviews/20260925-053628-preregistration/`):
no-go as written, 9 points. Each was reproduced or checked against the code and fixed with a test
that failed first (D040):

1. The report crashed on a NumPy boolean in the anchor tripwire, and the smoke test hid it.
   Tripwires now return native booleans, and the smoke test writes the report with plain JSON.
2. A branch of the verdict challenged small positive contrasts that the support rule never
   required to be large. It is removed (§4).
3. Incomplete primary data could yield "supported". The verdict is now withheld unless the
   completeness rule of §4 holds.
4. The budget fallback was promised but not implemented. It is now implemented in staged,
   resumable probes; dropped steps are recorded, and their tripwire reads "not assessed" (§8).
5. The prevalence bound for SH was unjustified, and the per-graph interval averaged endpoints.
   The bound is removed, and each graph gets a world-bootstrap interval with a detection count (§4).
6. The convergence criterion measured 90% of the fitted improvement, not of the asymptote. It is
   now named for what it measures (§5, §6).
7. The variance components broke under unequal runs per graph. They are now handled (§5).
8. Stated scopes did not match execution: behaviour worlds, valence scope, and raw scores for the
   integrator. They are corrected (§5, §6).
9. The review record was not in the repository, and "one N2 number" was really two. All reviews
   are archived in `reviews/`, and §2 now gives both numbers.

A confirmation pass by Astra (`reviews/20260925-055819-preregistration-recheck/`) found points 3,
4 and 8 only partly fixed:

- completeness checked graph names, not the registered runs and seeds, and a short probe
  vector crashed the report;
- a resumed probes run forgot measured costs and retried dropped steps, and the CLI printed
  "not assessed" as "ok";
- one sentence still said 16 behaviour worlds.

All three were reproduced and fixed with tests that failed first, or, for the resume, a smoke
run on the pilot champions.

Fable 5.1 was unavailable until after this version was fixed (usage limit). Its review, if it
arrives while the evolution runs, is recorded here. Any change it causes is also recorded in
DECISIONS and, if it touches evolution, triggers the §9 rerun rule.
