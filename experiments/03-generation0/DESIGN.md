# WormWars 03: generation-0 structure and task specificity

**Status: design v1, for review** (2026-09-25). Roadmap item 2 (`ROADMAP.md` v2.2). No N2 data
of any kind is produced before the pre-registration. Structure-only work is allowed before it:
building and validating the control ensembles uses N2's wiring, which is published data, but no
N2 brain is run. The only other measurement so far is the throughput benchmark on the pilot
shuffle SH101 (`timing.json`).

## The question

Every N2-specific signal in the series so far appears at generation 0, before selection:
- 01b's head start;
- 02's generation-0 mapping interaction;
- 02's larger input response;
- 02b's larger history dependence in random N2 brains.

The controls so far, degree-preserving shuffles, differ from N2 in two generic ways (02,
D041-D043). They destroy mirror symmetry (0.13-0.16 of chemical edges kept, against N2's 0.64).
They also give the food neurons direct routes to the motor read-out, which N2's food neurons
nearly lack.

**03 asks, without evolution:** is anything about N2 at generation 0 specific to N2, beyond
those generic properties, and is it specific to food-driven tasks?

## Graphs

- **N2**, the real wiring.
- **N2-rev**, N2 with the chemical direction reversed: same graph, wrong direction. Experiment 01
  ran this by accident.
- **Four control ensembles, 64 graphs each,** all degree-preserving (every neuron's chemical in-
  and out-degree and gap degree kept), with anatomical weights permuted onto the new edges:
  1. **SH:** ordinary shuffles, the sampler of 01b and 02.
  2. **SH-route:** routing-matched. Swaps are rejected if any food neuron (AWA, AWC, ASE, both
     sides) gets more direct chemical or gap edges onto the 18 motor read-out neurons than it has
     in N2.
  3. **SH-mirror:** routing-matched *and* mirror-matched. Swaps are made in mirror pairs: an edge
     swap is applied together with its mirror image under the left-right relabelling, where that
     image exists. The ensemble is then accepted only if its share of chemical edges kept under
     the relabelling lies within ±0.03 of N2's (0.64), so it matches N2's *partial* symmetry, not
     perfect symmetry. Gap junctions are handled the same way.
  4. **SH-class:** class-preserving. A swap (a→b, c→d) → (a→d, c→b) is allowed only when b and d
     share a neuron class, and likewise for sources. This keeps the class-to-class edge counts
     exactly. It is a separate branch, not nested with 2-3 (D047).
- The left-right relabelling uses a curated annotation file, not name suffixes (Astra, D047).

**Ensemble validation, before any fitness measurement, with thresholds fixed in the
pre-registration:**
- **Mixing:** the Jaccard overlap of each graph's chemical edges with N2's is at most 0.5. Swap
  passes continue until this plateaus.
- **Diversity:** the median pairwise Jaccard within an ensemble is below 0.3.
- **Constraint check:** SH-route and SH-mirror meet their constraints exactly. SH-mirror's
  symmetry lies within ±0.03 of 0.64.
- **Interface-local similarity:** for each ensemble, the distribution over graphs of the food
  pairs' routing features (D036's six) is reported next to N2's value. It is descriptive, not a
  gate.

## Interfaces (mappings)

- **M0** (AWA, AWC, ASE), **R1**, **R2** and **MS**, as in 02 (`remaps.json`).
- **MR, a motor remap (new):** the turn read-out (SMDD/RMDD against SMDV/RMDV) is moved to 4
  dorsal and 4 ventral non-interface motor neurons. They are matched pair by pair to the
  originals on chemical in-degree, out-degree and gap degree, and on hop distance from the food
  neurons, by the D036 procedure with hard routing tolerances. The set is frozen in
  `remaps.json` before any measurement. The forward read-out is unchanged.

## Tasks

- **T0** (stereo foraging) and **T1** (single-nose foraging), exactly as in 02.
- **C, a food-free locomotion task,** the matched control:
  - same world, interface, swarm and episode length, but no food and no metabolic drain;
  - score: the number of distinct grid cells the swarm's weys visit, relative to the best scripted
    controller on that world;
  - the food channel is silent, so the food mapping cannot matter.

**Why not "avoid food".** With random synapse signs, a random network's avoidance of food is
the sign-flip image of its approach. The valence check in 02 showed this symmetry is exact
without gap junctions. So at generation 0 an avoidance task cannot separate N2's food handling
from its approach behaviour. It would not be a control.

## Conditions and measures

All measures use unselected random genomes, never best-of-32 champions (Astra, D049), with
per-genome values saved.

| measure | graphs | mappings | tasks | conditions | genomes × worlds per cell |
|---|---|---|---|---|---|
| generation-0 fitness | all 258 | M0, R1, R2 | T0, T1 | gaps on, anatomical | 256 × 4 |
| generation-0 fitness | all 258 | (not used) | C | gaps on, anatomical | 256 × 4 |
| input response (directional signed and absolute; common mode) | all 258 | M0, R1, R2, MS, MR | none | gaps on, anatomical | 512 |
| input response | all 258 | M0 | none | gaps off; uniform and permuted magnitudes | 512 |
| history dependence (02b's matched-input test) | all 258 | M0 | none | gaps on, anatomical | 512 |

## Registered signals (margins set in the pre-registration, from 02's effect sizes)

| signal | definition | unit |
|---|---|---|
| (a) directional selectivity | the signed directional turn response relative to the common-mode response, under M0 | per graph, mean over genomes |
| (b) mapping interaction | A(M0) − mean(A(R1), A(R2)), where A is the graph's generation-0 fitness relative to the ensemble, per task | normalised score |
| (c) mapping-specific level | the graph's M0 fitness minus its mean R1/R2 fitness (the graph's own mapping preference). It distinguishes "N2 prefers M0" from "the shuffles are worse under M0" (02's catch-up finding, D042) | normalised score |
| (d) food-task specificity | N2's standing on T0 and T1 at M0 minus its standing on C, both as z-scores within each ensemble | z |
| (e) history dependence | \|rising − falling\| turn read-out after matched input, random genomes | raw read-out |

**Gate, per signal and per ensemble.** N2's value is compared with the ensemble's distribution of
graph values. Two claims are reported, and never merged:
- **the percentile claim:** where N2 falls among the 64 graphs;
- **the mean claim:** N2 minus the ensemble mean, with its interval.

The verdict, against a registered effect margin and equivalence margin per signal:
- **stands out from E:** N2 lies beyond E's central 95% *and* differs from E's mean by more than
  the effect margin;
- **compatible with E:** N2 lies inside E's central 80% *and* its difference from E's mean lies
  inside the equivalence margin;
- **inconclusive:** otherwise.

N2's compatibility is reported for each ensemble separately. No unique "narrowest explanation"
is claimed (D047). N2-rev is reported the same way, as a second real-anatomy graph. A signal that
stands out from every ensemble is N2-specific at generation 0. A signal compatible with an
ensemble is explained by that ensemble's constraint, and the claim narrows. It does not stop the
series (D045).

## Budget, from the measured throughput

The benchmark on SH101 (`timing.json`) saturates at about **155 genome-world evaluations per
second** from a batch of 256 genomes upward. That is about 1.8 times experiment 02's batch-32
rate, not the 5 or more that 03a's budget assumed (see below).

| item | combinations | cost |
|---|---|---|
| fitness, T0 and T1 | 258 graphs × 3 mappings × 2 tasks = 1 548 | 1 548 × 1 024 / 155 s ≈ 2.8 GPU-hours |
| fitness, C | 258 | about 0.5 GPU-hours |
| input response, 512 brains (about 2.5 s each) | 258 × (5 + 3) | about 1.4 GPU-hours |
| history dependence | 258 | about 0.3 GPU-hours |
| scripted references for normalisation (C, and T0 and T1 on the fitness worlds) | | about 0.5 GPU-hours |
| **total** | | **about 5.5 GPU-hours,** under a cap of 10 |

**Consequence for 03a (recorded here, to be carried into its next review).** 03a v3.2 needs
about 4.9 times experiment 02's throughput to fit its one-week cap. The measured gain from wide
batching is about 1.8 times. As written, 03a's panel will not fit even after its reduction steps,
unless its searches are made much cheaper, for example with fewer worlds per evaluation or
shorter searches. Its feasibility pilot will have to decide that.

## Pre-registration order

1. This design is reviewed (Astra 6 at maximum effort, and Fable 5.1).
2. Implementation, test-first:
   - the four samplers and their validation;
   - the MR remap selection;
   - task C and its scripted references;
   - the history probe on random genomes;
   - an end-to-end smoke test on pilot shuffles.
3. The ensembles are built and validated. This is structure only.
4. The pre-registration fixes the margins, thresholds, completeness rule and verdicts, and is
   reviewed.
5. The run. The first N2 measurement of 03 happens here.
