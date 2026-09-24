# WormWars 02: a 12-hour screening experiment

**Status: design v2, revised after review by Astra 6 and Fable 5.1** (both 2026-09-25; what changed
and why is at the end). No code for it exists yet, and there is no experiment-02 data. A
pre-registration will fix the design, predictions and tripwires before any run that involves N2.

## Why a screening experiment first

The series asks whether the real wiring's edge in 01b generalises across tasks and interfaces, and
whether it is concentrated where conditions are worm-like (`experiments/01b-direction-corrected/`,
`DECISIONS.md` D031-D033). The full grid would cost 40-150+ GPU-hours. So experiment 02 is a
**fraction of it, capped at 12 GPU-hours**, with three jobs:

1. **Find failure modes** no one has named yet, while they are cheap to find.
2. **Measure what sizes the full experiment:** the variance of the planned contrasts, convergence,
   and end-to-end cost per cell.
3. **Take a first look at the specialisation interaction**, labelled throughout as a screening
   estimate. It will not be reported as a confirmatory result.

Plasticity, and a hazard-based task, are **deferred** to later experiments. The hazard task is
deferred, not dismissed: it would enter N2 through AFD, a different route, which is itself a
generalisation question.

## What the screening can and cannot conclude

- **Can:** show that a task, mapping or measurement is unusable; show whether an effect is plausibly
  large or plausibly absent; give planning ranges for the variance components; catch
  implementation, calibration and numerical problems.
- **Cannot:** establish specialisation or equivalence. Everything is reported as "screening".

## Failure modes found while designing, measured before building

A sensory audit of real rollouts (16 worlds x 400 ticks, a random population and 01b's N2
champion) confirmed the reviewers' two leading concerns:

| channel | mean level | mean left-right difference | share of ticks active |
|---|---|---|---|
| food scent | 0.14-0.39 | 0.12-0.28 | 21-42% |
| own pheromone | 0.78-0.83 | 0.19-0.21 | 100% |
| front collision | 1.03-1.28 | 0.32-0.43 | 100% |

- **The swarm's own pheromone is an always-on stereo signal,** 2-6 times the level of food scent.
  It enters through ASK, an amphid neuron wired into the same interneuron hub as the food neurons,
  under every mapping. It would let a "single-nose" task be solved without temporal sensing, and it
  would dilute the mapping contrast. **Pheromone sensing is off in the main grid.**
- **The collision channels are never silent** (own body and teammates), so a sensor-silent
  calibration probe measures the wrong operating point. **Calibration happens in-world.**
- **Corpse pellets** are 14% of what a random population eats but 2% of what the 01b champion eats.
  Minor for evolved brains, but plant-food and pellet intake are accounted for separately.
- **Matched remaps are close to the food neurons in other ways too.** Matching on degree and distance
  pulls them toward other amphid chemosensory neurons (ASI, ASJ, ASG, AWB). Some also have direct gap
  or chemical edges to the read-out, as the food neurons do (AWCL -> AVAL and SMDVL). The exact sets
  and a full matching table are published before any run (below).
- **Sign-free synapses.** Weights start with random signs and mutate symmetrically, so negating an
  input is equivalent to flipping the input neurons' signs and biases. Gap junctions break that
  exactly, and nothing else does. This is tested with a paired generation-0 check instead of evolved
  runs.

## The fraction

**Brains.** N2, 4 runs per cell. SH: the same **6 shuffled graphs in every cell, 2 runs each**, with
graph identities SH1-SH6 reserved for the main runs. Pilots use different shuffles (SH101 onwards)
and are discarded. RD is dropped, since SH and RD have never separated.

**Tasks** (single swarm of 20, pheromone sensing off unless stated):
- **T0, stereo foraging:** food scent sampled left and right.
- **T1, single-nose chemotaxis:** one food sample at the head, copied to both sides.
- **A, 01b anchor:** T0 with 01b's settings (pheromone on) under M0 only, to check that the sign of
  01b's N2 - SH contrast replicates under the new calibration and integrator.

**Mappings** (the food channel only; every other channel and the motor read-out stay fixed):
- **M0, biologically motivated:** food into AWA, AWC and ASE.
- **R1, R2, matched remaps:** two disjoint triples of bilateral sensory pairs from outside the
  interface. They are chosen by a fixed rule from all candidate triples: minimise the distance to
  M0 in chemical in- and out-degree, gap degree, hop distance to the forward read-out and to the
  turn read-out (separately), and summed weight of direct edges to the read-out. Chosen before any
  fitness measurement, and published in the pre-registration with the full table.
- **MS, shortcut remap (T1 only, exploratory):** three sensory pairs with strong direct edges to
  the command interneurons, to test whether unmatched wrong mappings hand N2 a shortcut.

**Strength control (T1-M0 only):** N2 with its anatomical magnitudes permuted within its own mask
(signs, biases and time constants initialised as usual), 6 runs. This asks whether N2's edge comes
from its topology or its synapse strengths.

**Cells and runs.**

| block | cells | runs per cell | runs |
|---|---|---|---|
| main grid: T0 x {M0, R1, R2} + T1 x {M0, R1, R2, MS} | 7 | 4 N2 + 12 SH | 112 |
| anchor A | 1 | 4 N2 + 6 SH (one run per graph) | 10 |
| strength control | 1 | 6 N2-permuted | 6 |
| continuation: 8 main-grid runs extended from 40 to 80 generations | | | 8 equivalents |

**Held fixed:** 40 generations, population 32, 8 training worlds, 32 integrator substeps (measured
at only 24% more cost than 8), anatomical-magnitude initialisation with random signs, and D030's gap
truncation. D030 is kept deliberately: it affects all graphs equally, because shuffles preserve the
weight multiset.

**Calibration:** each graph's motor gains are fitted **in-world** under M0, to a fixed absolute
|forward| and |turn| target (not N2's), **iterated** until the achieved drive is within 2% of target,
and then frozen per graph across tasks and mappings. It is validated on independent random genomes,
reporting signed command distributions, clipping frequency and actual displacement.

## Probes: evaluation only, no extra evolution

1. **Diagnostic controllers** set each task's reference levels: untrained, straight-running,
   stationary, a *tuned* memoryless controller (same observations and motor limits as the memory
   controller), and a one-step-memory controller. Scores are reported raw and normalised per world
   to the best scripted controller on that world. They are not clipped: evolved brains may exceed
   the scripted ones.
2. **Channel dependence:** every champion is re-scored with, in turn, food replaced by a constant,
   food replaced by an unrelated signal with the same distribution, collision silenced, and (anchor
   only) pheromone silenced. **T1 counts as a temporal task only if champions lose substantially
   when food history is removed and survive when the unrelated signal is removed.**
3. **Valence, generation 0:** the paired sign-flip transformation on hundreds of random strains,
   with gap junctions removed (it should be exact) and restored (it measures the exception).
4. **Strength, generation 0:** anatomical against uniform magnitudes, and against within-mask
   permutations, for every graph and mapping.
5. **Input response per mapping, generation 0:** the time course of the motor read-out's response
   to common-mode and to left-right food input.
6. **Integrator:** the main contrasts and the interaction at 32 against 128 substeps on paired
   worlds, against a chaos floor (32 substeps with a 1e-6 perturbation of the initial state), plus
   rank stability of checkpoint populations.
7. **Convergence:** held-out scores of checkpoint champions at generations 0, 10, 20, 30 and 40 on a
   fixed diagnostic world suite separate from the final test suite. A saturating fit gives the
   generation at which 90% of the asymptote is reached, and the continuation runs check it.
8. **Energy sources and behaviour:** plant-food against pellet intake, speed, turning persistence,
   wall time, and a replay of the best and worst champion per cell.

## Tripwires, and what each changes

Each is reported whether it fires or not. Thresholds on contrasts are stated relative to their
intervals, not as bare numbers.

| tripwire | consequence for the full design |
|---|---|
| T1 champions do not depend on food history (probe 2), or the tuned memoryless controller matches the memory controller within its interval | T1 is not a temporal task; redesign it first |
| the anchor's N2 - SH sign differs from 01b's | find out why (calibration, integrator, pheromone) before comparing anything to 01b |
| achieved in-world drive at generation 0 differs between graphs by more than the 2% calibration tolerance | fix calibration before any comparison |
| the integrator changes the interaction by more than the chaos floor | raise substeps or make the chemical term semi-implicit |
| the 90%-of-asymptote generation exceeds 40 in more than a third of cells | the full design uses the measured asymptote, not a guess |
| a cell sits at the floor or ceiling of its scripted references | recorded as an observation (it may be the architecture's limit), and the task or mapping is revisited for the full design |
| MS changes N2's advantage by more than R1 and R2 do, beyond their intervals | routing must stay matched in the full design |
| R1 and R2 interactions are heterogeneous beyond their intervals | the full design needs more remaps |
| SH's own M0 vs remap contrast is non-zero beyond its interval | the matching failed for the controls too; rebuild the remaps |
| the generation-0 sign-flip check with gaps removed is not exact | there is a bug in input handling |

## Estimates reported

For task t and mapping m, A(t, m) is N2's mean held-out score minus SH's. The screening
interaction is I(t) = A(t, M0) - mean(A(t, R1), A(t, R2)), and the task contrast is I(T1) - I(T0).
All three are reported at generation 0 and at generation 40, with a bootstrap that keeps each run's
whole vector of cells together, with remaps crossed with graphs and seeds crossed as they were
assigned. Variance components are estimated for these contrasts, not for raw scores, with
leave-one-graph-out sensitivity.

## Integrity measures

- Every saved genome records its graph's edge-order hash, the resolved interface mapping, the
  sensing mode and the gains. `load_genome` refuses a mismatch, and a test proves that loading under
  the wrong mapping or a same-labelled different shuffle fails.
- A neuron-relabelling invariance test: permuting graph, genome and interface consistently must
  leave motor output and rollout scores unchanged. This is a cheap defence against another indexing
  or direction error.
- In-memory against saved-and-reloaded rollouts must match for every condition type.
- Cells run interleaved in balanced batches, with wall time recorded per run. If the 12-hour cap is
  reached, whole batches stop together, so no cell is lost selectively.

## Budget

Measured cost is 4.9 s per generation (32 strains x 8 worlds x 400 ticks, 32 substeps), plus evolution's internal held-out
checkpoints. End-to-end is about 3.7 minutes per 40-generation run, confirmed by a timed pilot
before the pre-registration. 136 run-equivalents come to about 8.4 hours, and the probes to about
0.5 hours (evaluation only). With a 30% slowdown margin the total is about 11.5 hours. Cut order, if
the pilot says it will not fit: MS, then the continuation runs, then the anchor's SH arm, then R2.

## Also fixed along the way

Two documentation errors found by review: `configs/interface.yaml` says injection uses tanh(v)
(injection adds a clipped current; tanh is used for transmission and read-out), and
`wormwars/connectome/graphs.py` says anatomical weights travel with the edges (they are permuted
onto the shuffled edges; only the overall distribution is preserved).

## What the review changed

Astra 6 and Fable 5.1 reviewed v1 independently. Checked against the code and data before adopting:

- **Both:** the swarm's own pheromone as a stereo cue (confirmed by the sensory audit); the remap
  arithmetic (v1 asked for nine pairs from a pool of eight); integrator and convergence tripwires
  that measured the wrong thing (a max over 126 champions fires on chaos; training-curve slopes are
  selection noise); and the valence arm, which was underpowered and now uses an exact generation-0
  check.
- **Fable:** calibration at the wrong operating point (confirmed: collision is never silent), the
  01b sign-replication anchor, and per-world normalisation.
- **Astra:** genome files that could be replayed under the wrong mapping or shuffle; pilot graph
  identities leaking into the main runs; the strength-versus-topology question; a tuned memoryless
  controller; the neuron-relabelling test; variance of contrasts rather than raw scores; and corpse
  pellets (confirmed, but minor for evolved brains: 2%).
- **Where they differed,** on graph sampling (Fable: 8 graphs x 1 run; Astra: 6 x 2 with fewer N2
  runs), I chose 6 x 2. The variance that matters is that of within-graph mapping contrasts (Astra),
  and single runs per graph would confound it with run noise.
