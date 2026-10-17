# 03a: the self-consistency hypothesis, a six-neuron proof of concept (design v6)

**Status:** design v6, 2026-10-16; the owner's choice in §2 made 2026-10-17 (D305). Not a pre-registration. Nothing specific to 03a has been coded or run, apart from
the exploratory scripted checks in §2 (D303, D304).
- **v4** (`eeeeb60`, D302): both reviewers said "revise" (run 20261016-174135, `docs/reviews/20261016-03a-design-v4/`).
- **v5** (`9a11651`, D303): Fable "ready for the pre-registration, with small fixes"; Astra "revise" (run
  20261016-182131, `docs/reviews/20261016-03a-design-v5/`). v6 takes every finding of both (§12), adds a
  slow-memory check (D304), and leaves one choice to the owner (§2, "The owner's choice").
- **The draft it replaces:** [`DRAFT.md`](DRAFT.md) v3.2 (2026-09-25), a 24-neuron panel on experiment 02's T1. It
  stays as the record of the earlier design.
- **The owner's decisions it follows:**
  - D094 (2026-09-28): "Let's keep the proof of concept with 6 neurons (3 with high foreseeable relevance, 2 with
    medium 1 with low)"; "If there is an imprinting effect we try other neurons if we find a reason for that";
    "Proof of concept limited to 72 gpu hours".
  - The biology track first (2026-10-15, D285); after 03mc, 03a (2026-10-16: "Sure", to starting this design round).
- **What the roadmap asks of the redesign** (ROADMAP.md, "03a: redesign after 03r"): keep the question, the pilot
  on shuffled graphs only (never N2) and the three outcomes; use a task that requires memory, and show in the pilot
  that solutions use interneurons; meet the 02b risk; use experiment 03's validated null ensembles; fit the measured
  throughput; animal-to-animal variability is not a ceiling on recovery from one fixed graph.
- **Who:** the hypothesis is Juan H. González Estefan's. Draft v1-v3.2: Claude Fable 5.1 and Claude Opus 5.5, reviewed
  by Astra 6 and Fable 5.1 (D045-D047). v4-v6: Claude Opus 5.5, reviewed by Astra 6 and Fable 5.1.

## 1. The question, and what it can and cannot show

**The hypothesis (the owner's):** if a connectome is shaped to perform tasks, the wiring of one missing neuron can
be predicted, to some extent, from the rest of the brain plus a task. Delete a neuron X, place it back with random
wiring, let only X's wiring optimise for the task, and see whether X's original partners come back.

**What the proof of concept asks:** on six neurons of evolved N2 brains,
1. does the search recover X's original partners beyond what a null that keeps the candidates' kind (sensor, motor,
   pharyngeal, other) and degree bin explains, in each arm;
2. does reconstruction with the trained intact network's information (MIP) recover more than reconstruction without
   prior exposure to X (NIP), the "imprinting effect" that D094 makes the condition for expanding the panel; and
3. does the procedure separate the three outcomes (anatomical recovery, functional success with anatomy
   undetermined, search failure)?

**Limits, stated now:**
- **NIP is conditional.** It is reconstruction into one frozen solution that evolved without X. It is not a test
  of what anatomy plus the task can identify in general: joint optimisation of the remaining weights and X's wiring
  is excluded (the draft's named assumption, DRAFT.md "Arms").
- **MIP − NIP mixes three things:** information the trained network keeps about X, how much each arm's brain
  compensated for X's absence, and the headroom left for X. A fully compensated NIP brain may have no use for X.
  So every contrast is reported beside the intact score, each arm's deleted-brain score, the original-partner
  refits, the compensation deficit and the headroom.
- **"Information from the trained network" includes what it started with.** Whole-brain initial weights scale with
  the anatomical weights (`init_w_scale`), so MIP's remaining brain carries anatomy before any training. Attributing
  a contrast to *learning* would need another control; 03a does not claim it.
- **The search is told X's true numbers of partners of each connection type** (incoming chemical, outgoing chemical,
  gap). It is never told how many of them are sensors, motors or of any other kind. Every conclusion is conditional
  on the counts it is told.
- **Enrichment is beyond a specified null,** not beyond everything degree or structure could explain: ranking the
  highest-degree candidates within each degree bin can still pass. The structural comparators (§6) are reported
  beside it, and a pass with a task ranking worse than a structural one is reported as such, never as improvement
  over structural prediction.
- **Six targets** support per-target readings, not panel-level generalisation.
- A positive result shows self-consistency under this model, task and search, not that the real worm's wiring is
  optimised for the task.

## 2. The task: Task N with one nose ("Task N-mono")

**Proposed:** Task N exactly as E1, 04a and E2 ran it (one wey, a 24-cell arena, a sensing-only scent source of
σ = 6 that jumps to the next position of a per-world sequence when the head comes within 1.5 cells, 300 ticks, energy
off, 32 substeps, the count of targets reached), with **`food_sensing = "mono"`**: both food sensors read the scent
at one sample point, `P_FRONT_C`, 0.6 cells ahead of the head (`wormwars/world.py:839`, the branch experiment 02's T1
used). Collision sensing stays bilateral. No left-right food difference exists.

**The exploratory checks** (D303, D304; 2026-10-16; 0.46 GPU-hours recorded in
[`development-records/compute.json`](development-records/compute.json) plus about 0.07 estimated for two smoke attempts
whose records were deleted, so 0.53 charged to 03a's cap; world ids 1 481 000 000-511 and 1 481 100 000-255, outside
every registered range; records and scripts in [`development-records/`](development-records/)). Every family below is
tuned on the 256 tuning worlds and scored on the 512 check worlds:

| Controller (mono) | Memory | Real scent | Jitter r = 1 | Jitter r = 2 |
|---|---|---|---|---|
| KT: speed and turn by level, collision avoidance (1 920 points) | none | 1.20 | 0.95 | 0.82 |
| KTM: KT plus one tick of memory | 1 tick | 2.84 | 0.51 | 0.04 |
| KTS, T = 2 (KT plus a comparison with an exponential average over T ticks; 162 points per T) | ~2 ticks | 2.62 | 1.76 | 0.63 |
| KTS, T = 5 | ~5 ticks | 2.69 | 2.46 | 1.56 |
| KTS, T = 10 | ~10 ticks | 2.18 | 2.13 | 1.63 |
| KTS, T = 20 | ~20 ticks | 1.58 | 1.69 | 1.59 |
| 04a's 16 champions, median (trained on stereo Task N) | ? | 2.26 | 2.25 | 2.25 |

(SEs 0.02-0.05 for the scripted rows. The jitter probe reads the scent at a random point within r cells, fresh every
tick, so the level survives and fast change becomes noise.)

**What they show, and what they do not:**
- **The task rewards memory within the families tried:** one tick of memory adds 1.64 targets to the memoryless family
  it is nested in. This is not a bound on memoryless policies: KT has one threshold, coarse grids and one-sided
  collision avoidance (Astra).
- **Evolution reaches the memory controllers' level:** 04a's champions have similar typical performance with one nose
  (median 2.26 against 2.32 with stereo; per champion, mono minus stereo is −0.16 to +0.02), consistent with E2d's
  finding that no Task N champion uses the left-right difference. Each is 0.83-1.48 targets above KT, and each
  collapses with a constant scent (0.08-0.34).
- **Their history use is not shown.** A slow comparison (T ≈ 5-10) scores at or above the champions' level and
  tolerates r = 1, but every memory controller that scores at that level (T ≤ 10) loses a quarter or more at r = 2,
  and the champions lose nothing. The T = 20 controller loses nothing either, but scores 1.58. Jitter tolerance
  shows robustness to these spatial perturbations, not the absence of temporal computation (Astra). The champions may
  integrate over a longer window, use the body's own dynamics, or use a memoryless strategy outside the families
  tried. Which, is open.

**The owner's choice (D304; decided 2026-10-17, D305: "Measure, don't gate").** The reviewers disagreed on what this
means for the roadmap's requirement:
- **Fable:** keep Task N-mono and measure history use, not gate on it. The hypothesis needs reconstructable
  interneuron use, which the pilot gates directly (criterion 3), and a history gate would fail a task on which
  evolution plainly finds something above the memoryless family.
- **Astra:** the roadmap asks for a task that requires memory; useful neural history should then be a feasibility
  requirement, applied to the formal N2 brains too, and pilot failure is an acceptable result. Otherwise, narrow the
  requirement explicitly and describe 03a as task-conditioned reconstruction without demonstrated memory use.
- **The owner chose the first.** History use is measured on every evolved brain and reported, not required; the
  roadmap's requirement is annotated, dated (ROADMAP.md, "03a: redesign after 03r"), and 03a is described as
  task-conditioned reconstruction on a task that rewards memory, without assuming the brains use it. Pilot
  criterion 8 (§8), written for the second option, does not apply.

**Alternatives considered:** stereo Task N (memoryless stereo steering scores 8.78, so not a memory task); E3a's
shuttle on an N2 brain (never played by one; no N2 mapping of its signals; 600 ticks; from-scratch search hard);
experiment 02's T1 (20 weys, about 20 times the brain work per episode, and its champions' history use was neither
shown nor excluded, 02 RESULTS, though 02b later found a history-dependent read-out of unknown value).

## 3. Arms and brains

Deletion, never silencing (D044). For each graph:
- **Selector brains: 3 intact**, evolved only to choose the targets (§4). They are never used for reconstruction,
  so target selection does not favour the MIP brains.
- **MIP: 5 intact brains**, each carrying all six targets: delete X, insert X with random wiring, search only X.
- **NIP: 5 brains per target**, each evolved from scratch with X deleted: insert X with random wiring, search only X.
- **Seeds:** every brain has its own evolution seed and world schedule from a registered range; no seed is shared
  between arms, and the final-evaluation world bank is shared by every brain and arm (so arm contrasts are paired by
  world).
- **Whole-brain evolution:** 04a's GA unchanged (population 32, 3 elites, top 8 as parents, Gaussian mutation,
  8 worlds per genome, 1 000 generations, validation of 256 worlds every 25 generations), unshaped fitness (the
  count), champion chosen on validation worlds as in 04a. Motor gains are calibrated once per graph on random genomes
  of the intact graph, as D035 does, and frozen through deletion and reinsertion.
- **Batching:** the five NIP brains of one target share one mask (X's edges removed) and run in one lockstep batch;
  MIP and selector brains share the intact mask. Throughput for these batch sizes is measured in pilot-dev.
- **Unit of analysis:** the brain. A target's reading in an arm combines its five brains with equal weight; each
  brain's own values are reported beside it.

## 4. The panel: six neurons per graph, by a rule

**Eligible:** neither mapped (sensor or motor, `configs/interface.yaml`) nor pharyngeal; connected by directed paths
both to and from the interface in that graph. About 245 neurons in N2. "Interneuron" in this design means this set
(unmapped computational intermediates), not the dataset's `inter` class; the class is reported per target.

**Bilateral pairs:** for each pair in `configs/mirror_pairs.yaml` (the curated annotation, D050), one member is
chosen by a fixed seed before any measurement, so its mirror stays in the brain; the pair is represented by that
member. A pair with only one eligible member is represented by it.

**Relevance:** the drop in Task N-mono score when the neuron is deleted, on each selector brain, measured on 512
target-selection worlds used for nothing else; a neuron's relevance is the mean over the three selector brains, with
a 95% interval from a paired bootstrap over worlds within brains. The margin p_sel is 5% of the selector brains' mean
intact score on those worlds. Ties are broken by a fixed seeded order.

**Tiers (D094: 3 high, 2 medium, 1 low), chosen in this order, without replacement, so the panel is always six
distinct neurons; absolute relevance is reported:**
1. **High:** the 3 eligible neurons with the largest mean drops. A member whose lower bound does not exceed p_sel is
   flagged "relatively high only".
2. **Medium:** 2 drawn with a fixed seed from the remaining neurons whose interval contains p_sel. If fewer than 2
   exist, the rest are drawn from the remaining neurons ranked 4-20, flagged. "Medium" is an operational tier, a
   boundary case at the margin, not a claim about biological relevance (Astra).
3. **Low:** 1 drawn with a fixed seed from the remaining neurons whose interval lies inside ±p_sel. If none exists, the
   remaining neuron with the smallest absolute drop, flagged.
- The same rule runs in every graph, so the procedure is matched, not the criticality.
- **Reported per graph:** each tier's drops, intervals, degrees and classes; drops by paired versus unpaired (with
  identical left and right input, one member of a pair may drop little, so the high tier may be all unpaired, Fable);
  whether the tiers contain RIA, AIY or AIZ (03m's and 02b's leads). Nothing is chosen by hand.
- **The selection check:** the six targets' drops are re-measured on each MIP brain on 512 fresh worlds and reported,
  so selection on the selector brains is not mistaken for relevance in the MIP brains.

## 5. What the search may change (the 02b risk)

02b found that 94 of the 96 most critical target-champion observations in experiment 02 had edges to interface
neurons, and that deleting only those edges cost a median 35% of the full deletion's damage
(`experiments/02b-champion-analysis/RESULTS.md` §4). The draft kept those edges fixed, so its reinsertions would have
started partly recovered.

**Proposed:** search **all** of X's connections. The candidate pool for every connection type is every neuron other
than X, interface and pharyngeal neurons included, so exact restoration is always possible.
- X is told its true numbers of partners per connection type. A sensor-to-X-to-motor shortcut can still fit within
  them; it is a legitimate substitution, and recovering a few obvious interface partners is weaker evidence than
  recovering the rest. So the primary null is stratified (§6), and recovery is reported separately over interface and
  non-interface candidates.
- **Chemical self-connection:** if X has one, its presence is kept; its weight is re-initialised by the
  partner-independent rule and searched with X's other weights (keeping the evolved weight would leak it in MIP). It
  is never scored.

## 6. Searches, scoring and the recovery statistic

For every target in every brain and arm (a "target-brain"):
- **Original-partner refits, 3** (the reference): true partners; X's weights, τ and bias optimised.
- **Random-partner refits, 5:** partners drawn uniformly with the true counts.
- **Free searches, 5:** partners, weights, τ and bias.
- **MIP exact restoration:** reinserting X's saved parameters reproduces the intact score (an implementation check).
- **Deleted-brain score:** each brain's score with X deleted and not reinserted.
- The structural *rankings* (mirror, class model, degree) are anatomical comparators at no GPU cost; the draft's
  structural refits are dropped.

**Initialisation, independent of the hidden partners:** inserted chemical weights start at magnitude
`init_w_scale` with a random sign; inserted gap conductances start at the pinned initial gap scale, non-negative
(`Genome.clamp_` keeps g ≥ 0); τ and bias from the pinned initial distributions. No per-edge anatomical magnitude is
used.

**The search:** the draft's replica exchange (4 replicas at fixed temperatures, 8 offspring per replica per
generation, the best offspring replacing the current state by the Metropolis-like rule, neighbour swaps every 5
generations, 100 generations), on **16 search worlds per evaluated state**, shared by all states of a generation. It
is a tempered optimiser, not an equilibrium sampler, and nothing here relies on sampling guarantees. Partner moves
keep the counts and keep gap junctions symmetric; refits disable them. **Settled in pilot-dev, then frozen (§8):** the
ladder; the mutation-type probabilities; whether one offspring may make several partner moves; whether the *search*
signal adds 04a's bounded progress bonus to the count (every reported score stays the raw count); and the search
worlds, 16, or 32 only if pilot-dev's projection with 32 still leaves at least 8 hours of reserve with no cut (at the
420 per second assumed in §10 it does not; Astra).

**Scoring:**
- **Final evaluation on 2 048 worlds** per scored state, one bank shared by all brains and arms.
- **Ranking:** per target-brain and connection type, each candidate's score is the mean absolute final weight (or
  conductance) of its connection to X over the 5 free searches (0 if not connected). Ties get the average rank.
- **Recovery statistic:** the ROC AUC of that ranking against the true partners, averaged with equal weight over
  the connection types X has (a type with no true partner, or with every candidate a partner, is unscoreable and
  left out, counted), then over the five brains of the arm.
- **Primary null, stratified:**
  - *Kind* is the candidate's interface role in `configs/interface.yaml` (mapped sensor, mapped motor) or otherwise
    pharyngeal or other; sensors that receive no signal in Task N stay "sensor". No neuron is both.
  - *Degree* is its total degree (chemical in plus chemical out plus gap) in the graph with X deleted. Tertiles are
    computed within each kind; ties go to the lower bin in a fixed seeded order; a bin with fewer than 3 candidates is
    merged into its neighbour of the same kind.
  - One draw of the null is one permutation of candidate identities within strata; it relabels every connection
    type's truth at once and is applied to every brain, search and arm of that target, so brains and types are not
    counted as independent anatomical evidence. B = 10 000; p = (1 + #{null ≥ observed})/(B + 1), ties counted.
  - Reported per target: stratum sizes, partner counts per stratum, the null's mean AUC (which need not be 0.5), and
    the number of distinct permutations available.
- **Structural comparators (no GPU):** the mirror ranking (paired targets), the class-model ranking and the degree
  ranking, each with its AUC against the same truth, beside every task AUC. **Beyond structure:** the task AUC minus
  the composite structural AUC (mirror for paired targets, class model for unpaired), and for paired targets the task
  AUC on the candidates the mirror ranking leaves tied at zero (the draft's SC3-paired).
- **Also reported:** precision at k against the same null, PR-AUC, per-search AUC, the AUC over interface and over
  non-interface candidates, and the no-task control's AUC (§8).

**Margins, resolution and attributes:**
- **p** = 5% of the MIP brains' mean intact score on the final-evaluation worlds.
- **Three-state comparisons:** a paired difference on the final-evaluation worlds with its 95% interval, from a
  bootstrap over worlds (paired across the two states) within brains and over brains: *equivalent* if inside ±p,
  *above* if entirely above +p, *below* if entirely below −p, otherwise *undetermined*. Undetermined is never counted
  either way.
- **Resolution, defined for these comparisons (Astra: the draft's δ_eval was for 64 worlds):** δ_eval is the
  half-width of that 95% interval for a target-brain's comparison of two scored states, pooled as a root mean square
  over the pilot's comparisons; δ_search is the SD of the three original-partner refits' 2 048-world scores within a
  target-brain, pooled the same way. Both are required to be at most p/2.
- **Five attributes per target and arm** (and per target-brain, descriptive): reference reliability (refit SD at
  most 2 δ_search and, in MIP, the reference *equivalent to or above* exact restoration; undetermined does not
  qualify); headroom (reference minus deleted-brain score); original-partner advantage (reference minus mean
  random-partner refit); functional success (mean free search minus reference: reached if equivalent, exceeded if
  above, failed if below); overlap (anatomical enrichment if the arm's family-1 test passes under Holm, §7).
- **Functional recovery** is the free searches' score as a fraction of the MIP brains' mean intact score in both
  arms; the NIP brains' own deleted and reinserted scores are reported beside it.

**Outcome summary per target and arm** (the unit is the target-arm, combining its brains; enrichment and functional
success come from the same brains and searches):
- **Excluded:** reference not reliable.
- **Anatomical recovery:** functional success reached or exceeded, and anatomical enrichment.
- **Functional success, anatomy undetermined:** functional success reached or exceeded, no enrichment.
- **Search failure:** functional success failed.
- **Inconclusive:** anything else.
A per-search table shows which searches are functionally successful and their AUCs, so a target-level "recovery"
assembled from different searches is visible. Functional substitution (positive evidence of chance overlap) is not
claimed at six targets.

## 7. Registered tests and readings

**Family 1, anatomical enrichment (Holm, 12 members):** for each of the 6 N2 targets in each arm, the arm's recovery
statistic against the stratified null, one-sided.

**Family 2, imprinting (one test; Fable's pooled option, specified as Astra asked):**
- **Statistic:** over the high and medium targets reliable in both arms (the common set), the mean of each target's
  MIP − NIP difference in the per-brain recovery statistic (the mean of five MIP brains' AUCs minus the mean of five
  NIP brains').
- **Null:** the sharp null that, within each target, the ten brains' AUCs do not depend on the arm. Arm labels are
  permuted within each target (252 splits per target), independently across targets; B = 10 000 Monte Carlo draws,
  one-sided, p as in §6, α = 0.05.
- **Effect floor:** it counts only if the observed statistic is also at least **0.05 AUC**. The floor is a filter on
  the observed effect; it does not show that the true difference exceeds 0.05.
- **Withheld** if fewer than 3 targets are in the common set; the exclusions are reported.
- **Validation before the formal run:** the whole procedure is run on simulated per-brain AUCs under the null, with
  unequal variances between arms, and its rejection rate is reported in the pre-registration.
- **Per-target contrasts are descriptive:** each with its exact 252-split p, the brain-level values, and the
  leave-one-brain-out range. A single target separates at p ≤ 0.05 only if at most 12 of the 252 splits (the observed one
  included) are at least as extreme; with five brains per arm, a moderate true difference will often not separate, and a null result is not
  evidence against imprinting (Fable).

**The registered readings:**
- **"Imprinting effect" (D094's condition for expansion):** family 2 passes, and at least one high or medium target
  has anatomical enrichment in MIP (family 1) with functional success reached or exceeded in MIP.
- **"The proof of concept separates the outcomes":** at least two of the three substantive outcomes (anatomical
  recovery; functional success, anatomy undetermined; search failure) occur among the 12 target-arms.
- Both readings are reported whatever they say. Neither is evidence of a mechanism. Expansion still needs the
  owner's word, a stated reason, and its own pre-registration with independent brains (D094).

**Descriptive:** every attribute per target-brain and target-arm, with the cross-table; the beyond-structure
contrasts; the selection check; the probes on every evolved brain (§8); stratification by whether X has interface
partners.

## 8. Controls, the pilot and the probes

**Null graphs:** the formal null arm is cut: three SH-mirror graphs with one brain per arm would support only a
descriptive comparison at about a third of the cap. The pilot's SH-mirror graphs give a descriptive shuffled-graph
anchor. A null comparison belongs to the expansion. (SH-mirror is also routing-matched as SH-route,
`wormwars/exp03/samplers.py`.)

**No-task control:** the same search code path, with fitness identically zero, for every N2 target in all five MIP
brains. With constant fitness the replacement and swap rules act on ties by the optimiser's own tie rule, so no
episode needs simulating. It tests the pipeline for bias toward true partners, against the stratified null. It cannot
rule out generic routing preferences that appear only under task selection.

**The bounded-history probe (replacing v5's "history erase"; Astra's replay design, with Fable's calibration):**
- Every L ticks, the brain's neural state is rebuilt by starting from the canonical initial state and replaying the
  last L ticks of the inputs it actually received; the episode then continues. So between resets the brain carries
  between L and 2L ticks of input history, the current input always acts, and nothing about attractor choice survives
  from before the window. The body's position and heading are untouched, so history kept in the body is not removed.
- L = 5, 10, 20, 50. **Implementation control:** replaying the whole episode so far must reproduce the unperturbed
  episode exactly.
- **Calibration:** the same rebuild applied to the scripted families' own state: KT (no memory; must be unaffected),
  KTM (one tick), and KTS at T = 5, 10, 20 (must lose when L is short against T).
- **Cost:** L replayed ticks every L ticks, about twice an ordinary episode's neural work; itemised in §10.
- **Other probes:** constant scent, jitter (r = 1, 2), hold (h = 20), and a P4-style ramp (rising against falling to
  the same level; the turn and speed read-outs). All on every evolved brain, 2 048 worlds each, descriptive.

**Implementation tests before any GPU work:**
- deletion equals a network built without X; the union mask with zeroed edges equals the network built with exactly
  that partner set, including gap contributions to neighbours' denominators, at a tolerance declared in the test;
- the frozen background is bitwise unchanged by reinsertion (weights copied by edge identity, never re-initialised);
- in NIP evolution, X's edges stay at zero through initialisation and every mutation;
- direction (in and out unswapped); gap symmetry after moves; degrees constant during a search; common random
  numbers;
- **an information boundary:** changing the hidden truth while keeping the allowed inputs leaves initialisation and
  free-search proposals unchanged, with sabotage checks that pinning and truth isolation fail when broken;
- a planted optimum on a small synthetic problem; the no-task control's AUCs match the stratified null; the
  bounded-history probe's full replay equals the unperturbed episode;
- family 2's procedure on simulated nulls (§7).

**The pilot, in two stages, on SH-mirror graphs with seeds outside every formal draw, never N2:**
- **Pilot-dev** (one graph; at most 6 GPU-hours): evolves selector, MIP and NIP brains for 2 targets; tunes what §6
  leaves open; measures the batch throughputs; records the search diagnostics (Q, the fraction of true partners
  connected, along each trajectory; partner turnover; accepted topology moves; ranking agreement on independent
  worlds; a 2× longer search on a subset); validates the bounded-history probe on the scripted calibrators. **Its
  output is the frozen pilot protocol**, written into the pre-registration before pilot-check runs: every tuned
  setting, and acceptance thresholds for the diagnostics (turnover, ranking agreement, the longer search's gain),
  which become pilot-check criteria; nothing is turned into a pass/fail rule after pilot-check is seen.
- **Pilot-check** (two fresh graphs, the frozen protocol): per graph 1 selector brain, 1 MIP brain and 1 NIP brain
  per target, for the panel rule's 3 high targets and 1 low target: 8 targets in all. **Its limits:** one brain per
  arm cannot test the five-brain aggregation or family 2, which the simulated-null validation covers instead; it
  omits medium targets; it decides feasibility, it estimates nothing.
- **Pass criteria, all required, evaluated on pilot-check:**
  1. **Evolved brains beat memoryless control and use the cue:** each graph's MIP brain beats the D303 KT winner by a
     paired 95% lower bound above 0.5 targets on the registered check worlds, and loses at least half its score under
     the constant scent. If a graph's MIP brain fails this, one re-evolution with a fresh seed is allowed for this
     criterion only, counted in the cap (Fable: the criterion is about the task and graph, not one seed).
  2. **Solutions use interneurons** (Astra's version of Fable's gate): in each graph, at least 2 of the 3 high targets,
     re-measured on the MIP brain on 2 048 fresh worlds, have drops whose lower bound (one-sided, Bonferroni over the
     three) exceeds p.
  3. **Resolution:** δ_eval and δ_search at most p/2 (§6).
  4. **Headroom and identifiability in NIP:** at least 3 of the 8 targets have a reliable reference, headroom
     present and original-partner advantage present.
  5. **MIP recovery:** of the targets passing (4) whose MIP reference is reliable, at least half (rounded up) reach
     functional success in MIP with a stratified enrichment p below 0.05. If none passes (4), criterion 5 fails.
  6. **Search diagnostics:** within the thresholds frozen by pilot-dev.
  7. **Timing:** pilot-dev's measured throughputs project the formal design within the remaining cap, with the cuts
     of §10 applied first if needed.
  8. *Not applied (the owner chose to measure history use, D305).* **Only if the owner chooses Astra's reading (§2):** each graph's MIP brain loses at least 0.3 targets under the
     bounded-history probe at the L chosen by pilot-dev, more than the KT calibrator loses at that L.
- The scripted gap is re-measured on registered check worlds (the D303 and D304 winners, not re-tuned) and reported;
  it is not a gate, since at 2.84 against 1.20 it cannot fail (Fable).
- If the pilot fails, the formal run does not happen, and the pilot is reported. One pilot-check attempt; a second
  needs the owner's word.

## 9. Order of work

1. The owner's choice in §2 (made, D305).
2. Code and implementation tests (CPU), reviewed by both.
3. Pilot-dev (GPU; the owner's word first), reported openly.
4. Pre-registration with the frozen pilot protocol and family 2's simulated-null validation, reviewed by both, bound
   and pushed.
5. Pilot-check under the registration; if it passes, the formal N2 run (the owner's word before each GPU stage).
6. Results, review by both, publication.

## 10. Budget (72 GPU-hours, everything included, registered in code, never extended)

At a conservative 420 episodes per second (the measured 8-run lockstep rate; the search batches can be wider, where
about 1 000 was measured, E2d). An evolution is 256 000 selection episodes plus 41 validations of 256 worlds
(10 496), so 266 496 (Astra).

| Workload | Count | Episodes | Hours at 420/s |
|---|---|---|---|
| Exploratory checks so far (D303, D304; 2.33 M worlds recorded, two smoke attempts estimated) | | | 0.53 |
| One search (100 gen × 4 replicas × 9 states × 16 worlds) | | 57 600 | 0.038 |
| One target-brain (13 searches) | | 748 800 | 0.50 |
| N2 target-brains: 6 targets × (5 MIP + 5 NIP) | 60 | 44.93 M | 29.71 |
| N2 whole-brain evolutions: 3 selector + 5 MIP + 30 NIP | 38 | 10.13 M | 6.70 |
| N2 final evaluations: 60 target-brains × 14 states × 2 048, plus restoration and intact | | 1.80 M | 1.19 |
| N2 relevance scan (3 × 246 × 512) and selection check (5 × 7 × 512) | | 0.40 M | 0.26 |
| N2 probes: 38 brains × about 12 episode-equivalents × 2 048 (the bounded-history probe counted double) | | 0.93 M | 0.62 |
| Pilot-dev (cap) | | 9.07 M | 6.00 |
| Pilot-check: 2 × (6 evolutions + 8 target-brains), 2 re-evolutions, evaluations, scans, probes | | 16.73 M | 11.06 |
| Scripted re-measurement and probe calibration | | 0.20 M | 0.13 |
| **Total** | | **about 84.2 M** | **about 56.2** |

The reserve is about 16 hours at 420/s; at the wide-batch rate the whole would be about 24 hours. Failed attempts
count. **Cuts, decided from pilot-dev's measured timing before pilot-check runs, in this order:** random-partner
refits 5 → 3; then free searches 5 → 4; then stop and report, or, only with the owner's word, a descriptive proof of
concept without family 2. Brains per arm stay at five, and the final-evaluation precision and selector brains are
kept (Astra: with four brains per arm the per-target exact test could never pass Holm, and the cut order must not
silently remove a registered test). The six neurons and both arms are never cut (D094).

## 11. Open questions

1. **For the owner:** history use measured (Fable) or gated (Astra), §2. *Decided 2026-10-17: measured (D305).*
2. **For the reviewers, if a round 3 is needed:** the bounded-history probe's definition; family 2 as one pooled test;
   pilot criteria 1-8.

## 12. Changes

**v5 → v6 (round 2: run 20261016-182131; Fable "ready, with small fixes", Astra "revise"):**
- **Memory wording narrowed** (both): "rewards memory within the families tried", not "requires"; jitter tolerance
  read as robustness to that perturbation only (Astra); "similar typical performance", with the per-champion range
  (Astra). A slow-memory scripted family added and run (Fable; D304): its T ≈ 5-10 members score like the champions
  but lose at r = 2, where the champions do not.
- **History gate:** the reviewers disagree; it goes to the owner (§2). Pilot criterion 8 is written for Astra's
  option.
- **The history-erase probe** replaced by a bounded-history replay probe with a full-replay implementation control
  and calibration on no-memory, one-tick and slow-memory controllers (Astra 3; Fable 1-2).
- **Family 2** is one pooled test (Fable 3's option) with its sharp null, permutation scheme, effect-floor meaning,
  common set, withholding rule and simulated-null validation stated (Astra 4); the per-target contrasts are
  descriptive with their power limit stated (Fable 3).
- **The four-brain cut removed** (Astra 4: it would have made the per-target test unpassable); the 32-world search
  option allowed only if it fits with reserve (Astra 10).
- **The stratified null specified:** kind, degree, bins, ties, small strata, one permutation of identities applied to
  every type, the finite-sample p, and the null's own mean AUC reported (Astra 5, Fable 7); the conclusion narrowed
  to that null (Astra 5).
- **"Of each connection type"**, never "kind", for what the search is told (Fable 4).
- **Tiers chosen in order without replacement**, with every fallback excluding chosen neurons (Astra 6).
- **Interneuron gate** on the MIP brain's fresh re-measurement of the high targets, Bonferroni over three (Astra 6).
- **Resolution** defined for the actual 2 048-world paired comparisons; reference reliability needs "equivalent or
  above" (Astra 7).
- **Pilot:** frozen acceptance thresholds from pilot-dev, criterion 5 spelled out, one re-evolution for criterion 1
  (Fable 5), the scripted gap no longer a gate (Fable 8), the pilot's limits stated (Astra 6, 8).
- **No-task control** on the same code path, all five MIP brains (Astra 8, Fable 9).
- **Budget:** checkpoint validation, probe cost and an itemised ledger added; the exploratory hours made traceable
  (Astra 9-10, Fable 9).

**v4 → v5 (round 1: run 20261016-174135; both "revise"):**
- Task kept, with D303's checks; a richer memoryless family; a history probe; interneuron use as a pilot gate,
  "interneuron" defined.
- Target selection on separate selector brains; relative tiers; pair rules; a selection check on the MIP brains.
- The 02b wording corrected (about a third of the damage).
- Recovery null stratified by kind and degree, one shared permutation per target; structural rankings as
  comparators; structural refits dropped.
- An imprinting family with Holm and a 0.05 AUC floor, 5 brains per arm; the separation reading needs two
  substantive outcomes.
- Unit of analysis and outcome unit defined; a per-search coincidence table.
- 2 048 final-evaluation worlds; 512 selection worlds.
- The search's tunable choices listed, frozen after pilot-dev, with diagnostics.
- Implementation contracts: gap initialisation, pharyngeal candidates, self-connection, background, NIP pinning,
  information boundary.
- Calibration wording; functional recovery's denominator; `P_FRONT_C` named.
- The formal null arm cut; SH-mirror for the pilot; the pilot split into development and check; limits in §1.
