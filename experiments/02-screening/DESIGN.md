# WormWars 02: a 12-hour screening experiment

**Status: design draft, before review.** No code for it exists yet, and no experiment-02 data.
After review, a pre-registration fixes the design, the predictions and the tripwires before any run
that involves N2.

## Why a screening experiment first

The question for the series is whether the real wiring's advantage (seen in 01b) generalises across
tasks and interfaces, and whether it is concentrated where conditions are worm-like
(`experiments/01b-direction-corrected/`, `DECISIONS.md` D031-D033). The full grid (tasks x
interface mappings x plasticity, properly replicated) was costed by two reviewers at 40-150+
GPU-hours. The project's two most expensive mistakes so far were found late: synapses running
backwards for a week, and an overclaim that only review caught. So the first experiment is a
**fraction of the full design, capped at 12 GPU-hours**, with three jobs:

1. **Find failure modes** that no one has thought of yet, while they are still cheap.
2. **Measure the numbers that size the full experiment**: graph-to-graph and run-to-run variance,
   convergence, and cost per cell.
3. **Take a first look at the specialisation interaction**, labelled throughout as a screening
   estimate. It is not a confirmatory result, and it will not be reported as one.

Plasticity is **not** in experiment 02. Both reviewers recommended establishing the fixed-weight
interface effect first. Plasticity becomes a later experiment with its own controls.

## What the screening can and cannot conclude

- **Can:** show that a task or a mapping is unusable; show that an effect is plausibly large or
  plausibly absent; estimate the variance components that set the full experiment's size; and
  catch implementation, calibration and numerical problems.
- **Cannot:** establish that N2 is specialised, or equivalent. With a few graphs and runs per cell,
  the interaction interval will be wide. Any result is reported as "screening".

## Factors in the fraction

**Brains.** N2 (6 runs per cell) and SH (the same 4 shuffled graphs in every cell, 2 runs each).
RD is dropped: SH and RD have never separated, and SH is the control that matters. Separating SH
graph-to-graph variance from run-to-run variance is one of the screening's jobs, hence 4 x 2
rather than 8 x 1.

**Tasks.**
- **T0, stereo foraging:** 01b's task, kept as the anchor. It is not a worm behaviour.
- **T1, temporal (mono) chemotaxis:** one food-concentration sample at the head, copied to both
  sides, so direction can only come from change over time. This mirrors klinotaxis. Before T1 counts,
  a memoryless controller must fail and a one-step-memory controller must succeed (see Diagnostics).

A reversed-valence hazard task (proposed by a reviewer) is **not** in the fraction. In this model,
synapse signs are not fixed: every weight starts with a random sign and can flip under mutation. So
the worm's "nociceptor -> reversal command" wiring provides a route, not an innate urge to avoid,
and approaching versus avoiding a signal is nearly symmetric. It is exactly symmetric except for gap
junctions, which couple raw voltages. The screening tests that argument cheaply (valence probe
below) instead of spending a task on it.

**Interface mappings** (only the food channel is remapped; every other channel and the motor
read-out stay fixed):
- **M0, biologically motivated:** food scent into AWA, AWC and ASE, as now.
- **M1-M3, matched remaps:** three disjoint sets of three bilateral sensory pairs from outside the
  interface, matched to AWA/AWC/ASE on chemical out-degree, in-degree and gap degree (declared
  tolerances) and on N2 hop distance to the motor read-out, measured in the direction signal flows.
  Candidates that meet the tolerances: ASI, ASJ, ASG, IL2D, IL2V, IL2, AWB, PLN. They are chosen by a
  fixed rule before any fitness measurement, and the same sets are used for every graph.
- **MS, shortcut remap (T1 only, exploratory):** three sensory pairs with direct connections to the
  read-out command interneurons (for example FLP, URYD, OLL). This tests one reviewer's worry
  directly: unmatched wrong mappings give N2 a shortcut, and could produce an "anti-specialisation"
  result for reasons that have nothing to do with specialisation.

**Known weakness of M1-M3.** Matching on degree and distance pulls the remaps toward other amphid
chemosensory neurons (ASI, ASJ, ASG, AWB). These are real smell neurons, just not the food ones. A
"wrong" mapping may then be only mildly wrong, and the contrast diluted. The screening reports each
remap's sensory modality and the interaction per remap, so the full experiment can decide how to
build its ensemble.

**Cells.** T0 x {M0, M1, M2, M3} + T1 x {M0, M1, M2, M3, MS} = 9 cells x 14 runs = 126 runs.

## Held fixed, and changed from 01b

- **Integrator: 32 substeps.** Measured on the RTX 5080, one generation (32 strains x 8 worlds x
  400 ticks) costs 3.9 s at 8 substeps, 4.2 s at 16 and 4.9 s at 32: only 24% more, because the
  world dominates the cost. D032 found 8 substeps under-resolved for strongly evolved genomes.
- **Calibration to a fixed target, not to N2.** Every graph's motor gains are fitted to an absolute
  |forward| and |turn| target, on a sensor-silent probe, so the mapping cannot change a graph's
  gains. Gains are then frozen per graph across tasks and mappings. The drive achieved at the fitted
  gains is measured and reported, because 01b's residual (84-97% of target) favoured N2.
- **Initial weights:** anatomical magnitudes with random signs, as in 01b. The claim is therefore
  about the wiring *plus* its anatomical synapse strengths. A generation-0 probe with a common,
  anatomy-independent magnitude asks whether any head start comes from the strengths.
- **Budget:** 40 generations, population 32, 8 training worlds; held-out score on 64 worlds never
  used for selection.
- **N2 never touches tuning.** Task difficulty, remap tolerances and anything else tuned are set on
  SH or RD pilots or scripted controllers only, and those pilot runs are discarded.

## Probes: cheap side measurements, all pre-registered

1. **Diagnostics** (no evolution): for each task, an untrained population and scripted controllers
   (memoryless proportional, one-step memory, straight-running, stationary), which set each task's
   floor and ceiling. Scores are reported on the floor-to-ceiling scale.
2. **Valence symmetry** (T1-M0, N2 and SH, 4 runs each): food signal negated. If N2's result differs
   from the unnegated arm beyond run-to-run noise, the no-fixed-sign argument is wrong and valence
   belongs in the full design.
3. **Uniform-magnitude generation 0:** for every graph and mapping, the generation-0 score with
   anatomy-independent initial magnitudes, against the anatomical ones.
4. **Input drive per mapping:** at generation 0, how strongly the food signal moves the motor
   read-out under each mapping and graph. This measures whether the remaps change "input gain" as
   well as routing.
5. **Integrator refinement** on the evolved champions of every cell: read-out and fitness at 32
   against 128 substeps.
6. **Behaviour audit:** speed, turning, time near walls, time on food, and a short replay of the best
   and worst champion per cell, to catch degenerate or exploitative strategies that a score hides.

## Tripwires, and what each changes before the full experiment

| tripwire | consequence for the full design |
|---|---|
| T1's memoryless controller reaches within 20% of its memory controller | T1 does not demand memory; redesign it before anything else |
| a cell's runs all sit at the floor, or all at the ceiling | the task or mapping is unusable at this budget; replace or re-tune on non-N2 pilots |
| fewer than 80% of runs are still improving between generations 30 and 40 | raise the generation count |
| integrator: any champion's fitness moves more than 5% of the floor-to-ceiling range between 32 and 128 substeps | raise substeps or make the chemical term semi-implicit |
| achieved drive differs between graphs by more than 10% after calibration | fix calibration before any comparison |
| the valence probe differs beyond noise | valence becomes a factor in the full design |
| MS (shortcut) moves N2's advantage far more than M1-M3 do | wrong mappings must stay routing-matched in the full design |
| the remaps' interactions disagree in sign | the ensemble needs more remaps than planned |
| graph-to-graph variance dominates run-to-run variance | spend the full budget on more SH graphs, not more runs |

Every tripwire is reported whether it fires or not.

## Budget

Measured cost is 4.9 s per generation, so a 40-generation run takes 3.3 minutes, 4.2 with a 30%
margin for slowdowns. 126 runs come to about 8.9 hours, the probes to about 1.5 hours (valence
probe 16 runs, the rest mostly generation-0 evaluation), and calibration, diagnostics and held-out
scoring to about 0.5 hours. **Total: about 11 hours, under the 12-hour cap.** If a pilot shows it
will not fit, the cut order is: MS, then M3, then the valence probe's SH arm.

## Work before any run

1. Integrator default to 32 substeps, with the refinement check extended to fitness.
2. Calibration to an absolute target on a sensor-silent probe, with the achieved drive reported.
3. Mono sensing mode for T1, and the food channel's negation for the valence probe.
4. Interface variants built from a declared remap rule, with tests that they preserve pairing,
   gains and the fixed read-out.
5. A scripted-controller harness that drives the motors directly, for the diagnostics.
6. An experiment runner for the grid, which reuses graph identities and seed blocks across cells.
7. Analysis: the interaction per task and remap, variance components, tripwires, and the
   generation-0 versus gain decomposition.
8. Tests for each of these, including the direction tests that already exist.

## The screening estimate of the interaction

For task t and mapping m, let A(t, m) be N2's mean held-out score minus SH's, on the
floor-to-ceiling scale. The screening estimate is I(t) = A(t, M0) - mean over matched remaps of
A(t, m), with a bootstrap interval that keeps graph and run blocks, and remaps crossed with graphs.
It is reported with its interval and labelled as a screening estimate. Its main use is to size the
full experiment.
