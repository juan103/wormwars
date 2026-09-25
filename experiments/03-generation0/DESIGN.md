# WormWars 03: generation-0 structure and task specificity

**Status: design v2** (2026-09-25). v1 was reviewed by Astra 6 (maximum effort) and Fable 5.1
(`docs/reviews/20260925-210723-03-design/`). v2 answers every point; the changes are listed at the
end (D050). No N2 data of any kind is produced before the pre-registration. Structure-only work
may happen before it: building and validating the ensembles, and a shuffle-only pilot that sets
the margins. No N2 brain is run.

## The question

Every N2-specific signal in the series so far appears at generation 0, before selection:
- 01b's head start;
- 02's generation-0 mapping interaction, which turned out to be the shuffles starting worse under
  the biological mapping (D042);
- 02's larger input sensitivity;
- 02b's larger history dependence in random N2 brains.

The shuffles used so far differ from N2 in generic ways: mirror symmetry, food-to-motor routing,
the class structure of the wiring, and the placement of anatomical weights on edges.

**03 asks, without evolution:** at generation 0, is N2 *distinctive relative to null ensembles
that preserve those generic properties*, and is what distinguishes it tied to food information?

**What 03 can and cannot conclude.** Compatibility with an ensemble means consistency with that
null, not that its constraint caused the result. Standing out from every ensemble means
distinctive relative to these nulls, not N2-specific in any unrestricted sense. No ensemble
preserves routing, symmetry and class structure jointly (Astra, point 6).

## A correction first: mirror symmetry and this read-out (D050)

The turn read-out is **dorsal minus ventral** (SMDD/RMDD against SMDV/RMDV), and each group
contains left and right neurons. Under the left-right relabelling both groups map to themselves.
So for a perfectly mirror-equivariant network, food on the left and food on the right give the
*same* turn response. **Symmetry does not give a left-right comparison for free here; it forbids
one.** Steering needs the network to break the symmetry between the left-right sensors and the
dorsal-ventral read-out.

This reverses the rationale of D041 and of 02's registered reading. It also reverses the
docstring of `structure.py` (Astra, point 5). SH-mirror stays as a control for a generic property
N2 has. Its registered prediction is now that matching N2's symmetry *lowers* the directional
response relative to ordinary shuffles.

## Graphs

- **N2**, the real wiring.
- **N2perm1-3:** N2's mask, with anatomical weights permuted across its own edges (as in 02's
  strength control). Every shuffle permutes weights, so without these a difference could come
  from topology or from weight placement (Fable 17, Astra 6).
- **N2-rev:** the chemical mask transposed. Descriptive only: transposing swaps every neuron's in-
  and out-degree and changes routing, so it is neither a matched control nor an independent
  anatomy (Astra 16).
- **Four control ensembles, 64 graphs each:**
  1. **SH, ordinary:** the double-edge-swap sampler of 01b and 02. It preserves each neuron's
     chemical in- and out-degree and gap degree, and permutes anatomical weights onto the new
     edges. The shuffles 01b and 02 used were checked: every one reached its full swap target
     (74 180 chemical and 21 820 gap swaps), so the sampler's silent attempt cap never fired
     there.
  2. **SH-route, routing-matched:**
     - For every input pair used for fitness (M0, R1 and R2's six pairs), the final *weighted*
       graph keeps each neuron's direct weight onto the 18 motor read-out neurons, chemical plus
       gap, at or below its N2 value.
     - Its hop distances to the forward and turn read-outs are at or above N2's minus 0.5.
     - Enforced during swaps, which forbid creating a new direct edge from a constrained neuron
       to a read-out neuron, and again after weight permutation. Weights for the constrained
       direct edges are drawn only from pool values at or below the cap.
     - Checked on the final weighted graph, separately for chemical and gap (both reviewers).
  3. **SH-mirror, routing- and mirror-matched:** N2's edges are partitioned into mirror orbits
     under the curated left-right map (Fable 1):
     - **Paired edges** (e and its image both present, e ≠ image) are swapped only in mirror
       pairs. Each proposal is atomic: the four old edges are replaced by four new ones in one
       step, rejected if any new edge duplicates an existing one or falls outside the paired
       class.
     - **Self-mirrored edges** (e equal to its image, such as edges between midline neurons) are
       swapped only with other self-mirrored edges.
     - **Unpaired edges** get ordinary swaps, rejecting any new edge whose image is present.
     - The share of edges kept under the relabelling then equals N2's exactly, for chemical and
       gap separately, with no acceptance band.
     - The routing constraint of SH-route also applies.
  4. **SH-class, class-preserving:** a swap (a→b, c→d) → (a→d, c→b) is allowed only when b and d
     share a class *and* a and c share a class. This preserves each neuron's in- and out-degree
     *per partner class*, a stronger null than class-to-class counts (Astra 4, named
     accurately). "Class" is the dataset's five types: sensory, inter, motor, pharyngeal and
     other. The ~118 anatomical classes are too small to mix (Fable 4). Gaps use the undirected
     analogue.
- **The left-right map** is a curated file, built from the dataset's names, with every pair
  checked by hand against WormAtlas and every non-pair listed. It is committed with its hash
  before any ensemble is built. N2's chemical and gap symmetry shares are recomputed with it.
  The v1 figure of 0.64 came from name suffixes.

**Sampler contract (all four ensembles):**
- **Failing loudly.** Every sampler returns accepted and attempted counts. If a graph fails to
  reach its accepted-swap target within its attempt cap, it is reported and rebuilt with the
  next seed. The substitution is disclosed, and an ensemble short of 64 is reported as short.
- **The null is the chain run to its plateau,** not a uniform distribution over feasible graphs
  (Astra 3). The plateau rule: at 1× and 2× the pass count, Jaccard to N2 and the constrained
  statistics must agree within a registered tolerance, checked on 4 independent chains per
  ensemble.
- **Validation, per ensemble,** with thresholds relative to SH's own plateau (Fable 6):
  - Jaccard to N2, chemical and gap;
  - median pairwise Jaccard within the ensemble;
  - edge turnover in the interface neighbourhood, so the interface is not frozen;
  - acceptance rate;
  - duplicates and autapses;
  - reciprocity.
  All are reported against N2's values.

## Interfaces

- **M0, R1 and R2** for fitness, **MS** for input response only (`remaps.json`). No further
  matched remaps can be added: under D036's hard tolerances exactly six pairs qualify, so R1 and
  R2 are a forced partition (Fable 13 asked for R3 and R4). 03 therefore cannot resolve 02's R1/R2
  disagreement, and says so.
- **Motor remap: dropped from 03.** It needs its own matching specification: paths from the food
  neurons to candidate motors, dorsal/ventral eligibility, tolerances and a no-feasible-match
  outcome. Only SMB, SIA and SIB qualify as paired dorsal/ventral non-interface motor neurons,
  so the match would be weak (Astra 13, Fable 22). It is deferred to its own design.

## Motor calibration

Every graph's motor gains are calibrated in-world on the T0 configuration, as in 02 (D035), on
1 024 random genomes. That is about 2% standard error on drive, and about 15 seconds per graph.
A validation on 2 048 independent genomes is run for N2 and for 8 graphs per ensemble.

N2's calibration is an N2 run, so it happens after the pre-registration. Drive per graph is
reported as a covariate for every fitness signal (Fable 9, Astra 15).

## Tasks

- **T0** (stereo foraging) and **T1** (single-nose foraging), exactly as in 02.
- **T1-const, the primary control (Fable 11):** T1 with the food signal replaced by each world's
  tick-0 mean (02's `food_probe="constant"`). It has the same world, score, drain and drive; only
  food *information* is removed. N2's food-information dependence is T1 minus T1-const.
- **C, locomotion coverage, descriptive only:**
  - C is a locomotor baseline, not a matched sensory control (Astra 7);
  - food, pellets and metabolic drain are zeroed, with the food channel explicitly silenced;
  - hazards are off;
  - the map is generated before food is removed, so later random draws are unchanged;
  - score: the union of grid cells the swarm visits, relative to a scripted straight-running
    reference;
  - the arena ceiling is reported.
- **"Avoid food" is not used.** The v1 sign-flip argument was loose: the flip maps approach to
  approach of negative food, not to avoidance. It is exact only without gaps (Fable 8, Astra 8).
  The honest reason is simpler: with unselected genomes no graph has a mean valence, and
  avoidance is solved by not moving.
- **A nonmonotone sensory task** (occupying an intermediate concentration band, Astra 7) is a
  good candidate for a matched sensory control. It needs scripted validation first, so it is a
  pilot for a later experiment, not part of 03.

## Genomes, worlds and pairing

- **Per graph:** 128 random genomes × 16 worlds, a fixed world set shared by every graph and
  task, disjoint from 02's pools (Fable 16, Astra 12).
- **Pairing:** genome seeds are identical across tasks and mappings within a graph, so every
  contrast is paired by genome and world.
- **Saved:** genome × world outcomes.
- **Unit of analysis:** the graph. Genomes and worlds are crossed replicates within it, and N2's
  own uncertainty comes from a crossed bootstrap over its genomes and worlds.

## Signals

**Primary set,** with the direction 02 and 02b predict. A result in the other direction is
reported as a reversal (Fable 15):

| | signal | definition (per graph, over genomes and worlds) | expected |
|---|---|---|---|
| P1 | directional selectivity | mean signed directional turn response ÷ mean common-mode turn response (ratio of means), under M0, raw read-out, the corrected probe with its registered stimulus | N2 above |
| P2 | own mapping preference | c = F(M0) − mean(F(R1), F(R2)) on T1 | N2 above |
| P3 | food-information dependence | F(T1) − F(T1-const) under M0 | N2 above |
| P4 | history dependence | \|rising − falling\| turn read-out ÷ the steady-state contrast, with one stimulus bank shared by all graphs, random genomes | N2 above |

**Secondary, reported, no verdicts:**
- the absolute directional response;
- common-mode sensitivity;
- the top-decile mean of T0 fitness under M0, which connects to 01b's head start (Fable 19);
- each ensemble's mean mapping preference μ_E(c) against zero, and across ensembles. This is the
  "shuffles start worse under M0" finding of 02, an ensemble property. v1's signals (b) and (c)
  were the same comparison (both reviewers);
- the same signals on T0;
- C coverage;
- gaps-off and magnitude-mode variants of P1;
- N2-rev and N2perm on every signal.

## The verdict

For each primary signal and each ensemble E:
- **Test:** a one-sided prediction-interval test in the expected direction. It asks whether N2
  is an outlier among E's graph values, using N2's value, E's mean and SD, the t-distribution with
  n − 1 degrees of freedom, a √(1 + 1/n) factor, and N2's own bootstrap variance added.
  The rank statistic p = (r + 1)/65 is reported beside it (Fable 18). The prediction-interval
  test is used because with 64 graphs the rank test cannot go below 1/65.
- **Stands out from E:** the test's p is at most its Holm-adjusted level across the four primary
  signals, *and* N2 differs from E's mean by more than the effect margin.
- **Compatible with E:** the 90% interval of N2 − E's mean lies inside the equivalence margin,
  and N2 lies inside E's central 80%.
- **Inconclusive:** otherwise. A reversal is reported as such.
- **Distinctive relative to these nulls:** a signal stands out from all four ensembles. This is
  an intersection-union test, so no further correction across ensembles is needed.
- **N2perm:** if N2perm stands out too, the property belongs to the topology; if not, to weight
  placement.
- **N2-rev** is reported, not folded in.

**Margins** are set by a shuffle-only pilot of the unselected statistics, not by 02's best-of-32
numbers (Astra 9, Fable 19). The pilot uses 16 pilot shuffles (SH101-SH116) through the full
pipeline:
- effect margin: 0.5 of SH's between-graph SD per signal;
- equivalence margin: 0.25 of it.
The pilot also checks that per-graph precision is adequate: N2's bootstrap SE must be under a
quarter of the equivalence margin.

## Budget, from the measured throughput

The v1 benchmark ran at the default of 512 worlds per chunk (both reviewers). Rerun at 512 to
16 384 worlds per chunk, throughput stays at about **168 genome-world evaluations per second**
(`timing.json`). It is compute-bound on dense 302 × 302 products, so wider batching does not
help; sparse kernels or fewer integrator substeps might.

| item | cost |
|---|---|
| fitness: 261 graphs × 7 task-mapping cells (T0 and T1 at M0/R1/R2, T1-const at M0) × 128 × 16 | about 6.2 GPU-hours |
| C: 261 cells | about 0.9 |
| input response, 512 brains: M0, R1, R2, MS, plus gaps-off and two magnitude modes at M0 | about 1.2 |
| history dependence | about 0.3 |
| calibration: 261 × about 15 s, plus validations | about 1.3 |
| shuffle-only pilot (16 graphs, everything) | about 0.6 |
| **total** | **about 10.5 GPU-hours,** under a cap of 12 |

**For 03a,** carried to its next review: with about 2 times 02's throughput, not 5, 03a v3.2's
panel does not fit its one-week cap even after both reduction steps (about 227 GPU-hours, Astra
15). It needs a cheaper evaluation (sparse kernels, fewer substeps or worlds, shorter searches)
or a smaller panel. Its feasibility pilot must decide.

## Order

1. **Implementation, test-first:**
   - the four samplers, the contract, and validation;
   - the curated left-right map;
   - N2perm and N2-rev;
   - T1-const reuse and task C;
   - per-genome saving;
   - the history probe on random genomes with the shared stimulus bank;
   - the prediction-interval verdict;
   - an end-to-end smoke test on pilot shuffles.
2. Build and validate the ensembles (structure only), then the shuffle-only pilot, which fixes
   the margins.
3. The pre-registration fixes:
   - hashes, seeds, thresholds, margins and the completeness rule;
   - the stimulus bank;
   - the failure rules for samplers and the budget.
   It is reviewed (Astra at maximum effort, Fable).
4. The run. N2's calibration and every N2 measurement happen here, for the first time.

## Changes from v1 (D050)

**Corrected:**
- mirror symmetry forbids, rather than gives, a left-right comparison at this read-out;
- the throughput plateau is real (compute-bound), rechecked at wider chunks;
- the published shuffles were checked: none hit the silent cap.

**Ensembles:**
- routing is constrained on final weighted graphs for all fitness mappings;
- SH-mirror has an orbit-based sampler with exact symmetry;
- SH-class is defined, with partner-class profiles;
- a sampler contract that fails loudly, with a plateau rule and 4 chains;
- N2perm is added, and N2-rev is descriptive.

**Tasks:**
- T1-const is the primary control;
- C is descriptive, with its traps fixed;
- the avoidance argument is replaced;
- a nonmonotone task is deferred to a pilot.

**Signals:**
- the redundant (b)/(c) pair is merged into P2 plus the ensemble property;
- (a) and (e) are ratios to their own scale;
- there is a primary set with expected signs and Holm across four signals;
- the gate uses intervals;
- prediction-interval tests are used, with rank statistics reported beside them;
- margins come from a shuffle-only pilot of the unselected statistics.

**Design:**
- 16 shared worlds, paired genomes, graph as the unit;
- calibration added;
- the motor remap is dropped;
- no further remaps are possible under D036.
