# M4a: does the head core maintain the history difference? — the plan

*Draft 1, 2026-10-22, for review by Astra 6 and Fable 5.1. Exploratory: nothing here is a pre-registration, but the
arms, the controls and their matching, the measures and the readings are fixed here before anything runs. The first
slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), as agreed in one round on direction
([`docs/reviews/20261022-m3-m4-direction/`](../reviews/20261022-m3-m4-direction/)); M3 is closed in
[`M3-NOTE.md`](M3-NOTE.md). CPU only.*

## The question, and what it can and cannot answer

M2 found that N2's tick-30 lead over its null graphs is carried by a few separate-states genomes and by fading
genomes that keep more of their difference. Both are kept in batch 7's core-frozen shuffles. M4a asks: **do the
connections inside N2's anatomy core C3 contribute to maintaining the history difference after it is written, beyond
connections elsewhere cut with the same immediate effect?**

- A positive result says that C3's internal connections contribute to maintenance. It does not locate the store
  exclusively inside C3 (Astra).
- A null result is reported as **"maintenance specificity not demonstrated"**, never as "access": it could reflect a
  short cut, redundant maintenance or imperfect controls (Astra). The roadmap's "store dropped for access" branch is
  annotated accordingly when the results are written.
- C3 is M1's anatomy core (top 30 of N2's read-out neighbourhood by internal degree; [`M3-NOTE.md`](M3-NOTE.md)). It
  holds the eight read-out neurons, so its internal edges include the read-out's afferents inside it (Fable).

## The brains

M2's census draws, so every genome already has its class: **N2 at seeds 7600 and 7700, M1's 30 random reference
graphs (seed 7600) and M1's 10 selected graphs (seed 7600)**, 1024 genomes each, M1's probe (100 ticks of warm-up at
0.25× or 1.75× the final food level, a 10-tick ramp, then the final level), float32, 32 substeps. **Eligibility,
classes and denominators are the intact census's,** fixed across every arm (Astra). Each arm reruns the intact probe
in the same batch first, and the intact arm must reproduce the census's a and |δy(30)| within 10⁻⁴ (M1's chunked
gaps were below 10⁻⁶), or the run stops.

## The interventions

A **cut** sets a set of chemical edges' weights to zero for a window of ticks and restores them after; nothing else
changes (`Genome.with_params`, w zeroed on the set's edge indices). Autapses are never cut (C3 was defined without
them). Ticks count from the ramp's end (tick 0).

**Part 1: the hold windows** (N2's two panels, all eligible genomes).

| Arm | Cut | Window |
|---|---|---|
| intact | none | |
| C3-early-10 | C3's internal off-diagonal chemical edges | ticks 1 to 10 |
| C3-early-30 | the same | ticks 1 to 30 |
| C3-late-30 | the same | ticks 31 to 60, ending at the reading (Fable: an equal-duration window ending at the read, not a one-tick read cut) |
| C3-write | the same | the 10 ramp ticks only |
| gaps-off-30 | every gap junction (g = 0) | ticks 1 to 30; **descriptive, outside the readings** (M1: gaps off lengthens memory; Fable) |
| a matched control for each C3 arm | external edges, below | the same window |

The reading tick is **60** for every arm (30 ticks after the longest early window ends), with tick 100 as a second
reading. Recorded: δy and δv every tick to 100.

**Part 2: the switch, from its roots** (Astra: separate maintenance of an existing state from settling, and basin
identity from transient convergence). For every separate-states genome of N2 (28), the reference (38) and the
selected graphs (387), each history starts exactly at its own stable root (M2's located, accurate roots, local), the
two histories under the final input. Then the C3 cut for ticks 1 to 30, then the intact network for 300 ticks. At
the end each history is assigned to a root: the one it lies within 10⁻³ of, or "neither". **Basin identity is erased**
if both histories end at the same root. The selected graphs' states lie mostly off the core (M2: core fraction 0.05
to 0.77), a location contrast for free (Fable). The same with its matched control.

## The matched controls (fixed here; Fable, Astra)

C3 is by construction a dense set, so no coherent matched set exists. The control is **external**: edges with both
endpoints outside C3 (boundary edges excluded), cut in the same window, **matched per genome on the immediate effect**:
1. Three independent random orders of the external edges per genome (`default_rng(20261101)`).
2. For each order, nested cuts of its first k edges, k on a grid of 16 values from 1 to every external edge.
3. The **matching quantity**, measured over the window's first 3 ticks only: the drop in the full-state separation,
   1 − ‖δv(3)‖_cut / ‖δv(3)‖_intact (for Part 2, ‖v₁ − v₂‖ between the two histories). The C3 cut's own value is m.
4. The control for that genome and order is the smallest k whose value lies within ±20% of m (relative), or ±0.01
   absolute when |m| < 0.05. **If no k matches in any order, the genome's comparison is "unmatched"** and it is
   counted, not dropped silently. The arm's reading uses matched genomes; if more than 20% of N2's eligible tick-30
   numerator is unmatched, the reading is "unresolved".
5. Reported beside the match, never used to choose it: the immediate change of the read-out difference and the
   displacement of the two histories' mean state, for the cut and its control. **Nothing after tick 3 is ever used
   to choose a control** (Astra).

The control's effect is the mean over the matched orders.

## The measures

- **The share at the reading,** s(60) = Σ_E |δy_i(60)| / Σ_E a_i, per arm, with E and a from the intact census.
- **The separation inside and outside C3,** ‖δv‖ restricted to C3's 30 neurons and to the rest, every tick: the
  primary trace (Fable). If the cut does not reduce ‖δv‖ inside C3 by the window's end, the arm's reading cannot
  speak to maintenance and says so (Fable: a cut that collapses nothing tests nothing).
- **Per class** (separate states, fading), the same, from the census's classes.

## The readings (fixed here)

For each C3 arm X of Part 1 and each N2 panel: the loss L_X = (s_intact(60) − s_X(60)) / s_intact(60), and its
matched control's loss L_ctrl, over matched genomes. The contrast D_X = L_X − L_ctrl, with a 90% interval from 2000
genome resamples (`default_rng(20261102)`; the cut and its control resampled together).
- **"C3's connections contribute to maintenance beyond the matched control"** for X if lower(D_X) > 0.10 on both N2
  panels, and the window collapses ‖δv‖ inside C3 (a drop of at least 50% at the window's end, aggregated as for s).
- **"Not demonstrated"** if upper(D_X) < 0.10 on both panels.
- **"Unresolved"** otherwise, or under the unmatched rule above.
- The primary arm is **C3-early-30**. The others are read the same way and reported, with no correction, as secondary.
- **Write against hold:** if C3-write's D is larger than C3-early-30's, the core matters more for writing than for
  holding; reported as a description.
- **Part 2,** descriptive: the counts of separate-states genomes whose basin identity is erased by the C3 cut and by
  its control, per graph group, and the count landing at "neither".

## The reference, as a comparison (descriptive)

On the 30 reference graphs, the intact arm and C3-early-30 with its control only. C3 is N2's neuron set: in a
reference graph it encloses that graph's own edges among those neurons, fewer than N2's (M3: graphs keep 11 to 22%
of N2's edges inside C3); their count is reported per graph. Reported: N2's lead over the reference mean, at tick 60,
intact and under the C3 cut, and the cut's loss in each graph. Not like-for-like, and not read (Fable).

## Checks and tests

- **Before:** the intact arm reproduces the census within 10⁻⁴ (above); a planted check: a cut of zero edges equals
  the intact run bitwise, and cutting every chemical edge for the window equals a brain with w = 0 for that window.
- **Tests (rule 9, each first seen failing):** the cut is restored after its window (the weights after equal the
  weights before); the matching picks the smallest k within tolerance and reports "unmatched" when none is; no
  quantity after tick 3 enters the matching (a sabotage that matches on tick 10 must fail); the readings' boundaries;
  Part 2's root assignment.
- **Cost guard:** the plan benchmarks one N2 panel first. If the projection exceeds 8 CPU hours, the reference
  comparison is reduced to one graph per ensemble before anything else runs, and the change is recorded.

## Outputs and cost

`scripts/memory_m4/` (`m4a.py` for the arms and matching, `m4a_read.py` for the readings), inside
`wormwars.accounting`. Outputs in `runs/memory-m4a/`: per panel and arm, a JSON record (committed) and arrays
(local). **Cost, extrapolated:** a 100-tick follow-up of 1024 genomes takes about 2 minutes (M1). Part 1 is 6 arms and
4 controls per N2 panel, each control with its matching search (3 orders × 16 values × 3 ticks), so roughly 30 to 40
minutes per N2 panel; Part 2 is 453 genomes for 330 ticks, a few minutes; the reference comparison about 6 minutes per
graph, 3 hours in all. About 4 CPU hours, benchmarked before the run. No GPU.

## Deferred to later M4 slices

Core dissection (internal rewiring at fixed degrees, permuted weights, broken reciprocal pairs, sensory or motor half,
boundary rewiring), paired genomes across rewired graphs, a pulse-written history and another input direction, and
the transplant screen.
