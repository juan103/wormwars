# WormWars 03: generation-0 structure and task specificity

**Status: design v3** (2026-09-25). v1 was reviewed by Astra 6 (maximum effort) and Fable 5.1
(`docs/reviews/20260925-210723-03-design/`), and v2 answered them (D050). Astra's confirmation pass
on v2 (`docs/reviews/20260925-212556-03-design-v2/`) found flaws in the samplers and the verdict,
and v3 fixes them (D051). The changes are listed at the end. No N2 data of any kind is produced before the pre-registration. Structure-only work
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
N2 has, **with no predicted direction**. Symmetric wiring does not make a brain with independently
drawn random weights equivariant (Astra, v2 pass).

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
     - **Topology state space:** every degree-preserving graph in which each constrained neuron
       has at most as many direct read-out edges, chemical and gap separately, as it has in N2.
       Ordinary swaps are proposed and accepted if the result stays inside this space. Direct
       edges can therefore be removed *and* recreated, so the moves are reversible (Astra, v2
       pass: v2's rule only removed them).
     - **Weights, jointly and after topology:** the anatomical weight multiset is permuted onto
       the edges. The weights on each constrained neuron's direct read-out edges are then
       redrawn together, without replacement, until their *sum* is at most N2's direct weight
       for that neuron. v2 capped each weight separately, which does not cap the sum.
     - **Final check on the weighted graph:** aggregate direct weight and hop distances, for every
       constrained neuron, chemical and gap separately. A graph that fails is rebuilt with the
       next seed, and the substitution is disclosed.
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
     - **A stronger null than symmetry alone, stated as such** (Astra, v2 pass). The moves also
       keep each neuron's degree within each orbit category. The self-mirrored gap junctions (46
       in N2, left-right homolog junctions such as AWAL-AWAR) can only be swapped among
       themselves, and in practice stay nearly frozen.
     - **Orbit membership is recomputed on the complete graph after every accepted move,**
       including images that the move itself creates. A proposal is accepted only if every
       edge's category is unchanged. Proposal probabilities are symmetric, so each move's
       reverse is proposed with equal probability.
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
  (Astra 3). A plateau does not prove mixing, so it is a necessary check, not a sufficient one.
- **Structural acceptance rules, fixed now, before any ensemble is built** (Astra, v2 pass):
  - 20 passes of accepted swaps per graph, as in 01b and 02;
  - **plateau:** on 4 independent chains per ensemble, the mean Jaccard to N2 at 20 and at 40
    passes differs by less than 0.01, for chemical and gap separately;
  - **acceptance rate** at least 5%;
  - **per graph,** Jaccard to N2 no more than the ensemble's own plateau mean plus 0.02;
  - **constraints met exactly** on the final graph.
  A graph that fails is rebuilt with the next seed and disclosed. Thresholds are relative to
  each ensemble's own attainable plateau, not SH's.
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
  - hazards are off, and the movement cost is kept. With no drain and no hazards, no wey dies;
  - the map is generated before food is removed, so later random draws are unchanged;
  - score: the union of grid cells the swarm visits, relative to a scripted straight-running
    reference;
  - the arena ceiling is reported.
- **"Avoid food" is not used.** The v1 sign-flip argument was loose: the flip maps approach to
  approach of negative food, not to avoidance, and it is exact only without gaps (Fable 8, Astra
  8). The reason kept is simpler: avoidance can be solved by not moving, so it does not test food
  handling.
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

**Numerical definitions (Astra, v2 pass):**
- **P1:** the stimulus is 02's: b = 0.1, d = 0.05, 40 ticks from rest, raw read-out. The value is
  the mean over genomes and ticks of the signed directional turn, divided by the same mean of
  the absolute common-mode turn.
- **P4:** the stimulus bank is fixed before any graph is measured. Every graph gets the same
  final food level and background, 0.3 of the sensing scale, from the median of 02's
  generation-0 replays on pilot shuffles only. The value is 02b's \|rising − falling\| over the
  steady-state contrast, as a ratio of means over genomes. The decay after 5 ticks is reported.
- **Denominators:** if a graph's denominator mean is below 10⁻⁴, the graph is excluded from that
  signal and counted. Non-finite values are excluded and counted too. The completeness rule
  requires at least 120 of 128 graphs per ensemble, and a valid N2.

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

**Graphs per ensemble: 128, not 64** (Astra, v2 pass). An exact rank test then reaches the needed
significance levels. A parametric prediction test would need a distributional model that ratio
signals do not justify.

For each primary signal j and each ensemble E:
- **Rank test:** p_jE = (r + 1)/(n + 1), one-sided in the expected direction, where r is the
  number of ensemble graphs at least as extreme as N2, and n = 128. It is exact under
  exchangeability of N2 with the ensemble's graphs. That is the null being tested.
- **Across ensembles, then signals** (intersection-union, then Holm; Astra, v2 pass):
  1. p_j = max over E of p_jE.
  2. Holm across the four primary signals.
  v2 did these in the wrong order.
- **Effect size with its uncertainty:** the 90% interval of N2 minus E's mean must lie beyond
  the effect margin. The interval comes from a joint bootstrap. Its **world** indices are
  resampled once and shared by N2 and every graph, because the worlds are shared. Genomes are
  resampled within each graph, and ensemble graphs are resampled.

**Verdicts per signal:**
- **distinctive relative to these nulls:** the Holm-adjusted p_j is at most 0.05, and the
  effect interval lies beyond the margin in every ensemble;
- **compatible with E:** the 90% effect interval lies inside E's equivalence margin. This is
  reported per ensemble;
- **reversed:** the same as distinctive, in the other direction;
- **inconclusive:** otherwise.

**Margins,** set by the shuffle-only pilot:
- effect margin: 0.5 of SH's between-graph SD;
- equivalence margin: also 0.5 SD. v2's 0.25 SD gave only about 26% power to show compatibility
  even at exact equality (Astra, v2 pass).

The pilot's precision check uses a pilot shuffle standing in for N2, never N2 itself. v2 asked
for N2's standard error in the pilot, which is an N2 measurement.

**Not attributed:** "N2perm stands out, so it is topology" is not a registered inference. Three
N2perm graphs are reported descriptively. Their failing to stand out cannot show that weight
placement is the cause (Astra, v2 pass). T1-const holds the motor gains fixed, not the realised
drive. It changes input statistics and dynamics as well as information, and drive under it is
reported.

## Budget, from the measured throughput

The v1 benchmark ran at the default of 512 worlds per chunk (both reviewers). Rerun at 512 to
16 384 worlds per chunk, throughput stays at about **168 genome-world evaluations per second**
(`timing.json`). It is compute-bound on dense 302 × 302 products, so wider batching does not
help; sparse kernels or fewer integrator substeps might.

| item | cost |
|---|---|
| fitness: 517 graphs (N2, N2-rev, 3 N2perm, 4 × 128) × 7 task-mapping cells × 64 genomes × 16 worlds | about 6.1 GPU-hours |
| C: 517 cells, 64 × 16 | about 0.9 |
| input response, 512 brains: M0, R1, R2, MS, plus gaps-off and two magnitude modes at M0 | about 2.4 |
| history dependence | about 0.6 |
| calibration: 517 × about 15 s, plus validations | about 2.4 |
| shuffle-only pilot (16 graphs, everything) | about 0.4 |
| **total** | **about 12.8 GPU-hours,** under a cap of 15; C, the revised probes and calibration of constrained graphs are estimated, not benchmarked, and the pilot measures them |

**For 03a,** carried to its next review: with about 2 times 02's throughput, not 5, 03a v3.2's
panel does not fit its one-week cap even after both reduction steps (about 204 GPU-hours at
exactly 2 times; Astra). It needs a cheaper evaluation (sparse kernels, fewer substeps or worlds, shorter searches)
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

## Changes in v3 (Astra's confirmation pass on v2, D051)

- **Routing:** the topology state space is reversible, so direct edges can be recreated. Weights
  are allocated jointly under an aggregate cap, and the final weighted graph is checked.
- **Mirror:** the stronger null is stated, including the nearly frozen self-mirrored gap
  junctions. Orbit membership is checked on the complete post-move graph, and proposals are
  symmetric.
- **SH-mirror** has no predicted direction.
- **Structural acceptance rules** are fixed before construction, relative to each ensemble's
  own plateau.
- **P1 and P4** are defined numerically, with a pilot-derived stimulus bank and denominator,
  non-finite and completeness rules.
- **Verdict:** 128 graphs per ensemble and exact rank tests, with no parametric tails. The
  maximum p over ensembles comes first, then Holm across signals. The effect interval must lie
  beyond the margin. Equivalence is 0.5 SD. A joint bootstrap resamples the shared worlds.
- **The pilot's precision check** uses a stand-in shuffle, never N2.
- **Attribution** from N2perm is dropped; T1-const is described accurately.
- **Budget** rises to about 12.8 GPU-hours, with a cap of 15. 03a's arithmetic is corrected to
  about 204 GPU-hours.
