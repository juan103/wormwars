# M4a: do the head core's connections help maintain the history difference? — the plan

*Draft 2, 2026-10-22, after one round of review (Astra 6 and Fable 5.1, both "revise"; draft 1 and the review are
archived in [`docs/reviews/20261022-m4a-plan/`](../reviews/20261022-m4a-plan/)). Exploratory: nothing here is a
pre-registration, but the arms, the controls and their matching, the measures and the readings are fixed here before
anything runs. The first slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), as agreed in one round on
direction ([`docs/reviews/20261022-m3-m4-direction/`](../reviews/20261022-m3-m4-direction/)); M3 is closed in
[`M3-NOTE.md`](M3-NOTE.md). CPU only.*

## The question, and what it can and cannot answer

M2 found that N2's tick-30 lead over its null graphs is carried by a few separate-states genomes and by fading
genomes that keep more of their difference. Both are kept in batch 7's core-frozen shuffles. M4a asks: **do the
connections inside N2's anatomy core C3 contribute to maintaining the history difference after it is written, beyond
connections elsewhere cut with the same three-tick attenuation of the difference?**

- A positive result says that C3's internal connections contribute to maintenance. It does not locate the store
  exclusively inside C3 (Astra), and it holds for the matched genomes only.
- A null result is reported as **"maintenance specificity not demonstrated"**, never as "access": it could reflect a
  short cut, redundant maintenance or imperfect controls (Astra). The roadmap's "store dropped for access" branch is
  annotated accordingly when the results are written.
- **What the control matches, and what it does not** (Astra): the control removes as much of the full-state
  separation over three ticks as the C3 cut. It is not matched on the direction of the perturbation, the read-out or
  the mean state; those are balance-checked below, and the claim is limited to "beyond external cuts matched on
  three-tick attenuation".
- C3 is M1's anatomy core (top 30 of N2's read-out neighbourhood by internal degree; [`M3-NOTE.md`](M3-NOTE.md)). It
  holds the eight read-out neurons, so its internal edges include the read-out's afferents inside it (Fable). For that
  reason **the primary measure is the full-state separation, not the read-out** (Fable): an external cut reaches the
  read-out only through uncut boundary edges, so a read-out measure would favour the C3 cut by proximity.

## The brains

M2's census draws, so every genome already has its class: **N2 at seeds 7600 and 7700, M1's 30 random reference
graphs (seed 7600) and M1's 10 selected graphs (seed 7600)**, 1024 genomes each, M1's probe (100 ticks of warm-up at
0.25× or 1.75× the final food level, a 10-tick ramp, then the final level), float32, 32 substeps. **Eligibility,
classes and denominators are the intact census's,** fixed across every arm (Astra). The ramp-end state is computed
once per genome and reused by every post-ramp arm, so all of them start bitwise from the same tick-0 state (Fable);
the intact arm from that state must reproduce the census's a and |δy(30)| within 10⁻⁴ (M1's chunked gaps were below
10⁻⁶), or the run stops. The write arm runs its own ramp.

## The interventions

A **cut** sets a set of chemical edges' weights to zero for a window of ticks and restores them after; nothing else
changes (`Genome.with_params`, w zeroed on the set's edge indices; the chemical term has no normalisation, so nothing
else moves; Fable). Autapses are never cut (C3 was defined without them). Ticks count from the ramp's end (tick 0).
**C3's cut** is its internal off-diagonal chemical edges, both endpoints in C3.

**Part 1: the hold windows** (N2's two panels, all eligible genomes).

| Arm | Cut | Window | Reading tick | Role |
|---|---|---|---|---|
| intact | none | | 60, 100 | |
| **C3-early-30** | C3's internal edges | ticks 1 to 30 | 60 | **primary** |
| C3-early-10 | the same | ticks 1 to 10 | 60 | secondary |
| C3-late-30 | the same | ticks 31 to 60 | 100, after restoration (Fable: at 60 it is still cut, a direct effect, not maintenance) | secondary |
| C3-write | the same | the 10 ramp ticks only | 60 | **description only**: its window ends at tick 0, during writing, so it says nothing about maintenance (Fable); its contrast with the hold arms has different durations and recovery times, so it is reported, not read (Astra) |
| gaps-off-30 | every gap junction (g = 0) | ticks 1 to 30 | 60 | **description only** (M1: gaps off lengthens memory; Fable) |
| a matched control for each C3 arm | external edges, below | the same window | the same | |

Recorded: δv and δy every tick to 100.

**Part 2: the switch, from its roots** (Astra: separate maintenance of an existing state from settling, and basin
identity from transient convergence). For every separate-states genome of N2 (28), the reference (38) and the
selected graphs (387), each history starts exactly at its own stable root (M2's located, accurate roots, local; the
smallest max-norm distance between a genome's two roots is 0.478, Astra), the two histories under the final input,
on **M2's float64 system** (the brain its roots were validated on; Astra). Three arms: **intact** (no cut, the drift
baseline; Fable, Astra), **the C3 cut** for ticks 1 to 30, and **its matched control**, then the intact network to
tick 330. Each history's end is assigned by **M2's own reaching rule** (the located root within 10⁻³ in max-norm,
confirmed by M2's float64 continuation verdict "reached"; Fable, Astra). The outcomes, enumerated per genome: **both
kept** (each history at its own root), **erased** (both at the same root), **swapped**, and **unresolved** (either
history not reached). Every intact-arm genome must be "both kept", or Part 2 stops for investigation.
- **The location contrast** (Fable), checked first: the fraction of ‖v₁* − v₂*‖² on C3's 30 neurons, computed from
  the saved roots for every Part 2 genome (Astra: M2's location fractions were on batch 7's `top30_start`, not on C3).
  Reported per group, and used only as a description.

## The matched controls (fixed here; Fable, Astra)

C3 is by construction a dense set, so no coherent matched set exists. The control is **external**: edges with both
endpoints outside C3 (boundary edges excluded), cut in the same window, **matched per genome on the three-tick
attenuation of the separation**.
1. **The matching quantity,** m(k) = 1 − Σ‖δv(t₀ + 3)‖_cut / ‖δv(t₀ + 3)‖_intact, at the third tick of the window
   (t₀ its start; window-relative; Astra), on the full state (for Part 2, ‖v₁ − v₂‖). If the intact ‖δv(t₀ + 3)‖ is
   below 10⁻⁹, the genome is "unmatched" (zero denominator). The C3 cut's own value is m*.
2. **Candidates:** three independent random orders of the external edges per genome (`default_rng(20261101)`); for
   each order, cuts of its first k edges, k on a **geometric integer grid** of 16 values from 1 to every external edge
   (duplicates removed), then **bisection** on k between every pair of adjacent grid values whose m brackets m*, to at
   most 8 steps (Fable). Every candidate is evaluated; **monotonicity is not assumed** (Astra).
3. **A match** is a candidate with |m(k) − m*| ≤ 0.2 |m*|, or ≤ 0.01 when |m*| < 0.05 (signed m; Astra). Among an
   order's matches, the smallest k. "Unmatched" means no sampled candidate matched in any order. The number of orders
   matched per genome is recorded (Fable).
4. **Balance, checked, not matched** (Astra): for the cut and its control, at the window's third tick, the read-out
   difference's attenuation (as m, on |δy|) and the displacement of the two histories' mean state, each aggregated
   over matched genomes. **If either aggregate differs by more than a factor of 2 between the cut and its control,
   that arm's reading is "unresolved (imbalanced)".**
5. **Nothing after the window's third tick is ever used to choose a control** (Astra). The control's effect is the
   mean over its matched orders.

**Coverage** (Astra): an arm's reading uses its matched genomes, and every arm of a panel is compared on the
**common matched subset** of its C3 arms. If the unmatched genomes hold more than 20% of N2's eligible numerator at
tick 30 or at the arm's reading tick (intact, full state), the reading is "unresolved". Coverage is reported per
class.

## The measures

- **Primary, the separation at the reading:** v(t) = Σ_E ‖δv_i(t)‖ / Σ_E ‖δv_i(0)‖, the full state, aggregated as M1's
  share is, per arm, with E from the intact census (Fable).
- **Secondary, the read-out share at the reading:** s(t) = Σ_E |δy_i(t)| / Σ_E a_i.
- **The core's collapse,** c = Σ ‖δv_i‖_C3 under the cut / Σ ‖δv_i‖_C3 intact, **at the same tick** (the window's
  end), on the matched genomes, per panel (Astra: against the concurrent intact state, so natural fading cannot satisfy
  it).
- **Per class** (separate states, fading), the same, from the census's classes: **descriptive only**, not subject to
  the readings (15 and 13 separate-states genomes per panel; Fable).

## The readings (fixed here)

For each maintenance arm X (C3-early-30, C3-early-10, C3-late-30) and each N2 panel, over the common matched subset:
the loss L_X = (v_intact − v_X) / v_intact at X's reading tick, its control's loss L_ctrl, and the contrast
D_X = L_X − L_ctrl, with 90% intervals from 2000 genome resamples (`default_rng(20261102)`; the cut and its control
resampled together). **0.10, the margin, is the smallest effect of interest:** ten percentage points of the intact
separation at the reading (Fable, Astra).
- **"C3's connections contribute to maintenance beyond external cuts matched on three-tick attenuation"** for X if,
  on both N2 panels: lower(D_X) > 0.10, lower(L_X) > 0 (an actual loss against intact, not only against the control;
  Astra), and the core collapsed under the cut, c ≤ 0.5.
- **"Not demonstrated"** if upper(D_X) < 0.10 on both panels and the core collapsed (c ≤ 0.5) on both.
- **"Unresolved"** otherwise: an interval across the margin, no collapse (a cut that collapses nothing tests nothing;
  Fable, Astra), the coverage rule or the balance rule.
- The primary arm is **C3-early-30**; the others are read the same way and reported, with no correction, as secondary.
- The same contrasts on the read-out share s are reported beside each reading, not read.
- **Part 2,** descriptive: per group (N2, reference, selected), the counts of each outcome under the C3 cut, its
  control and intact, and the location fractions on C3.

## The reference, as a comparison (descriptive)

On the 30 reference graphs, the intact arm and C3-early-30 with its control only. C3 is N2's neuron set: in a
reference graph it encloses that graph's own edges among those neurons, fewer than N2's (M3: graphs keep 11 to 22%
of N2's edges inside C3); their count is reported per graph. Reported: N2's lead over the reference mean at tick 60,
intact and under the C3 cut, and the cut's loss in each graph. Not like-for-like, and not read (Fable).

## Checks and tests

- **Before:** the intact arm reproduces the census within 10⁻⁴; a cut of zero edges equals the intact run bitwise;
  cutting every chemical edge for a window equals a genome with w = 0 for that window; every Part 2 genome's intact
  arm is "both kept".
- **Tests (rule 9, each first seen failing, with sabotages):** the cut is restored after its window (the weights
  after equal the weights before); the matching picks the smallest matching k, evaluates every candidate, bisects
  between bracketing grid values, and reports "unmatched" when none matches or the denominator is zero; no quantity
  after the window's third tick enters the matching (a sabotage that matches at a later tick must fail); the readings'
  boundaries, including the actual-loss and collapse conditions and the balance rule; Part 2's outcome assignment.
- **Cost guard:** the plan benchmarks one N2 panel first. If the projection exceeds 8 CPU hours, the reference
  comparison is reduced to one graph per ensemble before anything else runs, and the change is recorded.

## Outputs and cost

`scripts/memory_m4/` (`m4a.py` for the arms and matching, `m4a_read.py` for the readings), inside
`wormwars.accounting`. Outputs in `runs/memory-m4a/`: per panel and arm, a JSON record (committed) and arrays
(local). **Cost, extrapolated:** a 100-tick follow-up of 1024 genomes takes about 2 minutes (M1). Part 1 is 5 arms
and 3 controls per N2 panel, each control with its matching search (3 orders × up to 24 three-tick candidates), so
roughly 30 to 40 minutes per N2 panel; Part 2 is 453 genomes in float64 for 330 ticks plus continuations, under an
hour; the reference comparison about 6 minutes per graph, 3 hours in all. About 4 to 5 CPU hours, benchmarked before
the run. No GPU.

## Deferred to later M4 slices

Core dissection (internal rewiring at fixed degrees, permuted weights, broken reciprocal pairs, sensory or motor half,
boundary rewiring), paired genomes across rewired graphs, a pulse-written history and another input direction, and
the transplant screen.
