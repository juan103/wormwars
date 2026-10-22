# M4a: do the head core's connections help maintain the history difference? — the plan

*Draft 4, 2026-10-22, after three rounds of review (Astra 6 and Fable 5.1, both "revise" each time; round 3 on
implementation and wording only) and a smoke run of draft 2's code that changed the design (below); drafts 1 and 2 and the reviews are archived in [`docs/reviews/20261022-m4a-plan/`](../reviews/20261022-m4a-plan/)). Exploratory: nothing here is a
pre-registration, but the arms, the controls and their matching, the measures and the readings are fixed here before
anything runs. The first slice of step M4 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md), as agreed in one round on
direction ([`docs/reviews/20261022-m3-m4-direction/`](../reviews/20261022-m3-m4-direction/)); M3 is closed in
[`M3-NOTE.md`](M3-NOTE.md). CPU only.*

## The question, and what it can and cannot answer

M2 found that N2's tick-30 lead over its null graphs is carried by a few separate-states genomes and by fading
genomes that keep more of their difference. Both are kept in batch 7's core-frozen shuffles. M4a asks: **does
removing the whole set of N2's anatomy core C3's internal chemical edges for a window cost more of the history
difference later than removing sampled sets of as many external edges, matched on endpoint degree or on weight?**

- **What a positive result says** (Astra, round 2): removing C3's whole internal edge set causes a greater lasting
  loss than every sampled external set of equal size, conditional on the sampled sets. It is not a claim about
  individual edges, and it does not separate maintenance from the consequences of a stronger initial disruption:
  C3's cut is far stronger at once (below), and reporting that does not control it.
- A null result is reported as **"not demonstrated"**, never as "access": it could reflect a short cut, redundant
  maintenance or the sampled controls (Astra). The roadmap's "store dropped for access" branch is annotated
  accordingly when the results are written.
- C3 is M1's anatomy core (top 30 of N2's read-out neighbourhood by internal degree; [`M3-NOTE.md`](M3-NOTE.md)). It
  holds the eight read-out neurons, so its internal edges include the read-out's afferents inside it (Fable). For that
  reason **the primary measure is the full-state separation, not the read-out** (Fable).

**Why draft 3 changed the design: the smoke run** (64 N2 genomes per seed, other draws than the census, nothing from
the real panels; `runs/memory-m4a-smoke/`, scripts `smoke_isolation.py` and `smoke_count_matched.py` in
`scripts/memory_m4/`). Draft 2's controls were matched per genome on the three-tick attenuation. In the smoke, only 15
and 24 of about 60 genomes matched: for most genomes, cutting C3's 260 internal edges attenuates the separation more
in three ticks than cutting all 2696 external edges can. And the matched subset **selected the genomes on which the
C3 cut has the least effect** (on it, no loss and no collapse; on all genomes, a large loss). So draft 3 reads over
all eligible genomes and controls with sampled external cuts of equal size. The smoke also showed these brains to be
fragile to any 30-tick cut (random external sets of 260 edges lose −0.01 to 0.37 of the separation at tick 60, and
losses often grow after the cut is lifted) and C3's edges to carry about twice the |w| of degree-matched external
ones (|w| is proportional to the anatomical weight), hence the weight-matched family. The smoke's eligibility and
classes were taken by index from the census, which is invalid for other draws (Astra); only its all-genome numbers
are used here, and the reader now computes a smoke's eligibility from its own start.

**What the smoke predicts** (Fable, round 2), written down so the result is not a surprise: at seed 7600, C3's
early-30 cut lost 0.65 of the separation at tick 60 with the core collapsed to 0.22; at seed 7700 it lost 0.32 with
the core at 0.55, above the collapse threshold. With the weight-matched draws the largest draw lost 0.52 and 0.47. So
**"unresolved" is the likely combined reading**, and the run's value is the description on all genomes.

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
| the controls for each C3 arm | 30 sampled external sets, the whole exterior, (early-30) 5 uniform sets, and the flagged effect-matched controls; below | the same window | the same | |

Recorded every tick to 100: the norms ‖δv‖ (full state and on C3) and |δy| per genome, not the vectors (Fable).

**Part 2: the switch, from its roots** (Astra: separate maintenance of an existing state from settling, and basin
identity from transient convergence). For every separate-states genome of N2 (28), the reference (38) and the
selected graphs (387), each history starts exactly at its own stable root (M2's located, accurate roots, local; the
smallest max-norm distance between a genome's two roots is 0.478, Astra), the two histories under the final input,
on **M2's float64 system** (the brain its roots were validated on; Astra). The arms: **intact** (no cut, the drift
baseline; Fable, Astra), **the C3 cut** for ticks 1 to 30, and **the first 5 degree-stratified external sets of Part
1** (Fable: one comparator for both parts), then the intact network to tick 330. Each history's end is assigned by **M2's own reaching rule** (the located root within 10⁻³ in max-norm,
confirmed by M2's float64 continuation verdict "reached"; Fable, Astra), and the reached root is compared with the two
stored roots (within 10⁻⁶). The outcomes, enumerated per genome: **both kept** (each history at its own root),
**erased** (both at the same root), **swapped**, **other root** (a history reached a root that is neither; Fable,
round 3) and **not reached**. Every intact-arm genome must be "both kept", or Part 2 stops for investigation; the
record is saved either way, and a saved failure stops the run again on every restart (Astra, round 3).
- **The location contrast** (Fable), checked first: the fraction of ‖v₁* − v₂*‖² on C3's 30 neurons, computed from
  the saved roots for every Part 2 genome (Astra: M2's location fractions were on batch 7's `top30_start`, not on C3).
  Reported per group, and used only as a description.

## The controls (fixed here)

**Primary: sampled external cuts of equal size** (Fable, Astra, round 2). External edges have both endpoints outside
C3 (boundary edges excluded). Each sampled set has |internal| edges (260 on N2), drawn without replacement, the same
sets for every genome of a panel:
- **20 stratified on summed endpoint degree** (Fable: C3's edges join hubs): C3's edges are binned at the quintiles of
  their summed endpoint degree in the graph's own wiring, and each set takes as many external edges from each bin as
  C3 has there; a bin short of external edges is filled with the unused external edges nearest its range
  (`default_rng(20261103)`);
- **10 stratified the same way on anatomical weight**, since |w| is proportional to it in `Genome.random` and C3's
  edges carry about twice the |w| of degree-matched ones (`default_rng(20261105)`).

**Each family is matched on one property, not both** (Fable, round 3): in the smoke the degree sets carry Σ|w| of 41 to
61 against C3's 83, and the weight sets a mean endpoint degree of 62 to 70 against C3's 86. A positive reading says
that C3's cut beats every set matched on degree and every set matched on weight. Each set's mean summed endpoint
degree and Σ|w| (mean over genomes) are recorded beside C3's.

**Descriptive:** 5 uniform random sets of 260 external edges (early-30 only), and **the whole exterior** (2696 edges),
a benchmark, not a bound (Astra: a random subset already lost more than the whole exterior in the smoke).

**Secondary, flagged and not read: draft 2's effect-matched controls** (per genome, nested random external cuts
matched on the three-tick attenuation, with grid and bisection), reported with their coverage on all genomes and
explicitly marked as biased toward the genomes the C3 cut barely affects. **The balance rule is dropped** from the
reading: with sampled sets of equal size it would fire by construction (Fable).

## The measures

- **Primary, the separation at the reading:** v(t) = Σ_E ‖δv_i(t)‖ / Σ_E ‖δv_i(0)‖, the full state, aggregated as M1's
  share is, per arm, with E from the intact census (Fable).
- **Secondary, the read-out share at the reading:** s(t) = Σ_E |δy_i(t)| / Σ_E a_i.
- **The core's collapse,** c = Σ ‖δv_i‖_C3 under the cut / Σ ‖δv_i‖_C3 intact, **at the same tick** (the window's
  end), on all eligible genomes, per panel (Astra: against the concurrent intact state, so natural fading cannot satisfy
  it).
- **Per class** (separate states, fading), the same, from the census's classes: **descriptive only**, not subject to
  the readings (15 and 13 separate-states genomes per panel; Fable).

## The readings (fixed here)

For each maintenance arm X (C3-early-30, C3-early-10, C3-late-30) and each N2 panel, over **all eligible genomes**:
C3's loss L_X = 1 − Σ_E ‖δv(t)‖_X / Σ_E ‖δv(t)‖_intact at X's reading tick, each sampled set's loss L_d the same way,
and **D_X = L_X − max over the 30 sets of L_d**. The bootstrap (2000 genome resamples, `default_rng(20261102)`;
**90% intervals, the 5th and 95th percentiles**; Fable, Astra, round 3)
resamples genomes once for every cut, recomputes C3's loss and all 30 sets' losses in each resample, and takes D from
them (Fable, Astra: coherently, against the maximum, not a percentile of 20). **The reading is conditional on these
30 sampled sets** (Astra); it does not estimate a population percentile of external sets. **0.10, the margin, is the
smallest effect of interest:** ten percentage points of the intact separation at the reading.
- **Positive** for X on a panel if lower(D_X) > 0.10, lower(L_X) > 0 (an actual loss; Astra) and the core collapsed,
  c ≤ 0.5 (the declared threshold, evaluated on all eligible genomes; Fable, Astra: kept as declared, and "unresolved"
  accepted when it fails).
- **Null** if upper(D_X) < 0.10 and c ≤ 0.5.
- **Unresolved** otherwise.
- **Combined over both panels:** "cutting C3's internal edges for the window costs more separation at the reading
  than any of the sampled degree- or weight-matched external cuts of equal size" if both are positive; "not
  demonstrated" if both are null; otherwise "unresolved".
- The primary arm is **C3-early-30**; the others are read the same way and reported, with no correction, as secondary.
- **Reported beside each reading, not read:** C3's and the sets' losses at the window's third tick (C3's immediate
  strength); the same contrasts on the read-out share; the uniform sets and the whole exterior; the effect-matched
  controls with their coverage; per class (separate states, fading), C3's loss against the sets' median.
- **Part 2,** descriptive: per group (N2, reference, selected), the fraction of genomes with each outcome under the
  C3 cut, under the first 5 degree-stratified sets (each set over every genome, pooled; the same sets as Part 1,
  Fable), and intact; and the location fractions on C3.

## The reference, as a comparison (descriptive)

On the 30 reference graphs, the intact arm, C3-early-30, 5 degree-stratified and 3 weight-stratified external sets
and the whole exterior only. C3 is N2's neuron set: in a
reference graph it encloses that graph's own edges among those neurons, fewer than N2's (M3: graphs keep 11 to 22%
of N2's edges inside C3); their count is reported per graph. Reported: N2's lead over the reference mean at tick 60,
intact and under the C3 cut, and the cut's loss in each graph. Not like-for-like, and not read (Fable).

## Checks and tests

- **Before:** the intact arm reproduces the census within 10⁻⁴; a cut of zero edges equals the intact run bitwise;
  cutting every chemical edge for a window equals a genome with w = 0 for that window; every Part 2 genome's intact
  arm is "both kept".
- **Tests (rule 9, each first seen failing, with sabotages; `tests/test_memory_m4a.py`,
  `scripts/memory_m4/sabotage_m4a.py`, `runs/m4a-sabotage.txt`):** the cut is restored after its window and leaves the
  genome untouched; the window switches brains and back; the sampled sets follow C3's per-bin counts of endpoint degree
  and of weight; the effect-matched search (smallest match, every grid value, bisection, "unmatched"); the match uses
  the window's third tick only; the readings' boundaries (margin, actual loss, collapse) and the bootstrap against the
  maximum; Part 2's outcome assignment and its gate on a restart; cutting every edge equals w = 0, bitwise.
- **Cost guard** (in the code; Fable, Astra, round 3): after the first N2 panel the script projects the rest (the
  second N2 panel at the first's time, each reference graph at 11/113 of it by its number of 100-tick runs, an hour
  for Part 2) and keeps it in `guard.json`. If the projection exceeds 8 CPU hours, the reference comparison is reduced
  to one graph per ensemble, and the change is recorded. The stages run in the order N2, Part 2, reference.

## Outputs and cost

`scripts/memory_m4/` (`m4a.py` for the arms and matching, `m4a_read.py` for the readings), inside
`wormwars.accounting`. Outputs in `runs/memory-m4a/`: per panel and arm, a JSON record (committed) and arrays
(local). **Cost:** the smoke of draft 3's code took 132 s per 64-genome N2 panel, so about 35 minutes per 1024-genome
N2 panel if linear; the reference comparison about 3 minutes per graph, 1.5 hours; Part 2 under an hour. About 3 CPU
hours, benchmarked on the first N2 panel. No GPU.

## Deferred to later M4 slices

Core dissection (internal rewiring at fixed degrees, permuted weights, broken reciprocal pairs, sensory or motor half,
boundary rewiring), paired genomes across rewired graphs, a pulse-written history and another input direction, and
the transplant screen.
