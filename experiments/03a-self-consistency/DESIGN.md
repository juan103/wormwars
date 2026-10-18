# 03a: the self-consistency hypothesis, a six-neuron proof of concept (design v7.1)

**Status:** design v7.1, 2026-10-17, **agreed by both reviewers as the basis of the pre-registration** (round 4,
D307). Not a pre-registration. Nothing specific to 03a has been coded or run, apart from
the exploratory scripted checks in §2 (D303, D304).
- **v4** (`eeeeb60`, D302): both reviewers said "revise" (run 20261016-174135, `docs/reviews/20261016-03a-design-v4/`).
- **v5** (`9a11651`, D303): Fable "ready for the pre-registration, with small fixes"; Astra "revise" (run
  20261016-182131, `docs/reviews/20261016-03a-design-v5/`). v6 takes every finding of both (§12), adds a
  slow-memory check (D304), and leaves one choice to the owner (§2, "The owner's choice"), made on 2026-10-17
  (D305: history use measured, not gated).
- **v6** (`0cdd3a2`, D304-D305): Fable "ready for the pre-registration, with small fixes"; Astra "revise" (run
  20261017-151803, `docs/reviews/20261017-03a-design-v6/`). Both found that family 2's pooled test ignored the MIP
  brains shared across targets. v7 makes family 2 per-target again, under Holm, and takes every other finding (§12;
  D306).
- **v7** (`9ded377`, D306): both "ready for the pre-registration, with small fixes" (run 20261017-152826,
  `docs/reviews/20261017-03a-design-v7/`). v7.1 makes those fixes (§12; D307).
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
- **History use is measured, not required** (the owner, D305). A null anatomy or imprinting result therefore cannot
  be separated from "these brains use little history on this task"; every reading is conditional on the history use
  the bounded-history probe reports (§8).
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
| KTS, T = 50 | ~50 ticks | 1.17 | 1.17 | 1.18 |
| 04a's 16 champions, median (trained on stereo Task N) | ? | 2.26 | 2.25 | 2.25 |

(SEs 0.01-0.05 for the scripted rows. The jitter probe reads the scent at a random point within r cells, fresh every
tick, so the level survives and fast change becomes noise.)

**What they show, and what they do not:**
- **The task rewards memory within the families tried:** one tick of memory adds 1.64 targets to the memoryless family
  it is nested in (nested by construction; the grid actually searched for KTM did not include the no-memory setting,
  which does not change the winner, Astra). This is not a bound on memoryless policies: KT has one threshold, coarse grids and one-sided
  collision avoidance (Astra).
- **Evolution reaches the memory controllers' level:** 04a's champions have similar typical performance with one nose
  (median 2.26 against 2.32 with stereo; per champion, mono minus stereo is −0.16 to +0.02), consistent with E2d's
  finding that no Task N champion uses the left-right difference. Each is 0.83-1.48 targets above KT, and each
  collapses with a constant scent (0.08-0.34).
- **Their history use is not shown.** A slow comparison scores at the champions' level (T = 5 above it, T = 10 close)
  and tolerates r = 1, but every memory controller that scores near that level (T ≤ 10) loses a quarter or more at
  r = 2, and the champions show little measured loss (per champion −0.06 to +0.03, median change −0.003). The T = 20 controller loses nothing either, but scores 1.58. Jitter tolerance
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
  - *Annotation, 2026-10-17 (D309; code review round 1, both reviewers accept it):* the implementation evolves NIP
    brains **on the intact mask with X's edges pinned at zero** (zero at generation 0, mutation scale zero), not on a
    separate mask. It is deletion, tested, and it lets NIP brains of several targets share a batch with the selector and
    MIP brains. What changes, stated precisely (Astra): a NIP brain has no functional exposure to X during evolution,
    but its initial weight scale is normalised by the intact mask's mean anatomical weight, X's edges included, as
    every other arm's is. See `PILOT-DEV.md` §4.
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
a 95% interval from a paired bootstrap over worlds (one shared resample of world ids for all three brains) of the
three-brain mean; the spread between the three brains is reported beside it (Fable: a bootstrap over three brains
has ten distinct resamples, too coarse to set tiers). The margin p_sel is 5% of the selector brains' mean intact
score on those worlds. Ties are broken by a fixed seeded order.

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
- **Random-partner refits, 5:** partners drawn with the true counts per connection type and, within each type, with
  the true partners' composition over the null's strata (kind × degree bin, below), uniformly within each stratum
  (Fable: so original-partner advantage is not a kind or degree effect).
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
- **Final evaluation on 2 048 worlds** per scored state, one bank shared by all brains and arms (the bank is crossed
  with brains).
- **Ranking:** per target-brain and connection type, each candidate's score is the mean absolute final weight (or
  conductance) of its connection to X over the 5 free searches (0 if not connected). Ties get the average rank.
- **Recovery statistic:** the ROC AUC of that ranking against the true partners, averaged with equal weight over
  the connection types X has (a type with no true partner, or with every candidate a partner, is unscoreable and
  left out, counted), then over the five brains of the arm.
- **Primary null, stratified:**
  - *Kind* is the candidate's interface role in `configs/interface.yaml` (mapped sensor, mapped motor) or otherwise
    pharyngeal or other, in that order: MCL and MCR are both pharyngeal and mapped pump motors, and are "motor"
    (Fable). Sensors that receive no signal in Task N stay "sensor", and the pump motors stay "motor" though the pump
    does nothing with energy off.
  - *Degree* is its total degree (chemical in plus chemical out plus gap) in the graph with X deleted. Tertiles are
    computed within each kind, with boundaries after ranks ⌊n/3⌋ and ⌊2n/3⌋ by ascending degree; a group of tied
    degrees is never split, and goes wholly to the lower bin; a bin with fewer than 3 candidates is merged into the
    bin below it of the same kind (the lowest bin into the one above).
  - One draw of the null is one permutation of candidate identities within strata; it relabels every connection
    type's truth at once and is applied to every brain, search and arm of that target, so brains and types are not
    counted as independent anatomical evidence. B = 10 000; p = (1 + #{null ≥ observed})/(B + 1), ties counted.
  - Reported per target: stratum sizes, partner counts per stratum, the null's mean AUC (which need not be 0.5), and
    the support as the number of distinct joint truth patterns over the connection types together, since one
    permutation relabels them all at once (many identity permutations give the same labels; Astra). Restricted subsets with no scoreable truth (for example a mirror-zero subset with no true partner) are
    reported and left out.
- **Structural comparators (no GPU):** the mirror ranking (paired targets), the class-model ranking and the degree
  ranking, each with its AUC against the same truth, beside every task AUC. **Beyond structure:** the task AUC minus
  the composite structural AUC (mirror for paired targets, class model for unpaired), and for paired targets the task
  AUC on the candidates the mirror ranking leaves tied at zero (the draft's SC3-paired).
- **Also reported:** precision at k against the same null, PR-AUC, per-search AUC, the AUC over interface and over
  non-interface candidates, and the no-task control's AUC (§8).

**Margins, resolution and attributes:**
- **p** = 5% of the MIP brains' mean intact score on the final-evaluation worlds.
- **Three-state comparisons:** a paired difference on the final-evaluation worlds with its 95% interval, from a
  bootstrap over worlds (one shared resample of world ids, applied to every brain and state compared) and over brains
  (the MIP brains keep their identities across targets): *equivalent* if inside ±p,
  *above* if entirely above +p, *below* if entirely below −p, otherwise *undetermined*. Undetermined is never counted
  either way.
- **Resolution, defined for these comparisons (Astra: the draft's δ_eval was for 64 worlds):** δ_eval is the
  half-width of that 95% interval for a target-brain's comparison of two scored states, pooled as a root mean square
  over the pilot's comparisons; δ_search is the SD of the three original-partner refits' 2 048-world scores within a
  target-brain, pooled the same way. Both are required to be at most p/2. δ_search is frozen from pilot-check **as a
  fraction of that graph's p**, and the formal reliability rule applies that fraction to N2's p (Fable: shuffled-graph
  brains score lower, and count variance scales with the mean).
- **Five attributes per target and arm** (and per target-brain, descriptive): reference reliability (refit SD at
  most 2 δ_search and, in MIP, the reference *equivalent to or above* exact restoration; undetermined does not
  qualify); headroom (reference minus deleted-brain score); original-partner advantage (reference minus mean
  random-partner refit); functional success (mean free search minus reference: reached if equivalent, exceeded if
  above, failed if below); overlap (anatomical enrichment if the arm's family-1 test passes under Holm, §7). A
  target-arm's reference is reliable if at least 3 of its 5 target-brains' references are. Headroom and
  original-partner advantage are **present** when the comparison is *above* (Fable).
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

**Family 2, imprinting (Holm, 5 members: the high and medium targets, a fixed set):**
- **Statistic, per target:** the mean of its five MIP brains' recovery statistics minus the mean of its five NIP
  brains'.
- **Null and test:** within one target the ten brains are distinct, independently evolved brains (the MIP brains are
  shared across targets, never within one). Under the sharp null that a target's ten per-brain AUCs do not depend on
  the arm, the exact permutation of arm labels over the 252 splits is valid for that target. One-sided; p is the share
  of splits at least as extreme, the observed one included.
- **Across targets, Holm** at α = 0.05, which holds under any dependence between the targets, including the shared
  MIP brains. v6's pooled test permuted targets independently and so ignored that dependence: Astra's exact
  counterexample rejects 14.8% of null datasets at a nominal 5%.
- **Effect floor:** a target counts only if its observed difference is also at least **0.05 AUC**. The floor filters
  the observed effect; it does not show that the true difference exceeds 0.05.
- **Fixed set, no selection on reliability** (Astra): all five targets are tested; reliability qualifies the
  interpretation and is reported beside each test. A target with a missing registered brain is withheld and keeps
  its place in the family with p = 1, so the family never shrinks (Astra).
- **Power, stated:** Holm's strictest level is 0.01, so the first rejection needs at most 2 of the 252 splits to be at
  least as extreme; in practice, near-complete separation of the arms. A moderate true difference will often not
  pass, and a family-2 null is not evidence against imprinting (Fable).
- **Validation before the formal run:** 20 000 simulated datasets per scenario. Under the sharp null, both with
  independent targets and with a shared MIP-brain effect across targets that leaves each target's arms exchangeable
  (intraclass correlation 0.3 and 0.5; Astra: that dependence is inside the null, and Holm handles it), the
  family-wise rejection rate must be at most 0.0531 (0.05 plus two Monte Carlo standard errors). Unequal arm variances,
  outside the null, are a robustness check whose rate is reported. All rates go into the pre-registration.
- **Descriptive:** the panel-mean MIP − NIP over the five targets, each target's brain-level values, and the
  leave-one-brain-out range of each contrast. No pooled p value is given.

**The registered readings:**
- **"Imprinting effect" (D094's condition for expansion):** at least one high or medium target passes family 2 and,
  in MIP, has anatomical enrichment (family 1) and functional success reached or exceeded, with a reliable reference
  in both arms (the same target, so the contrast and the recovery belong together; Astra).
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
- **Timing:** after the action of every tick t that is a multiple of L, and before sensing at t + 1, the brain's
  neural state is rebuilt by starting from the canonical initial state (zeros, `wormwars/brain.py`) and replaying the
  inputs it received at ticks t − L + 1 to t; the episode then continues. Between resets the brain carries between L
  and 2L ticks of input history; the current input always acts; nothing about attractor choice survives from before
  the window. Neither the time before the first reset nor the first reset changes anything (at t = L the window is
  the whole history), so the first action that can differ is at 2L + 1: for L = 50, the first 100 of 300 actions are
  unperturbed, and comparisons across L change both the history kept and how often and how long the intervention
  acts; they do not estimate a memory horizon (Astra). The replayed inputs are the ones the perturbed trajectory
  actually received, with the same integration settings. The body's position and heading are untouched, so history
  kept in the body is not removed.
- **Why the rebuild is fully defined** (Fable, checked in the code): the brain's state is its voltage tensor alone,
  started at zeros, with no noise (`wormwars/brain.py:431-434`); motor commands are applied without a filter
  (`wormwars/world.py`); the inputs are the food and collision senses (`wormwars/interface.py`).
- L = 5, 10, 20, 50. **Implementation control:** replaying the whole episode so far must reproduce the unperturbed
  episode bitwise on the CPU, and on CUDA within the same batch composition (rule 6), so the control runs in the
  probe's own composition.
- **Validation of the rebuild** on prescribed input sequences, including sequences where the discarded history
  provably changes a scripted controller's action.
- **Calibration, with the expected results stated:** the same rebuild applied to the scripted families' own state.
  KT (no memory) and KTM (one tick of memory, shorter than every L) must be unaffected. KTS at T = 5, 10, 20 has its
  stored average changed when L is short against T; its closed-loop score is measured with no sign required, since a
  changed average need not cost score (Astra).
- **What it measures:** dependence on neural state older than the window, under this intervention. That includes slow
  neurons acting as filters (τ runs to 20 ticks) and any autonomous rhythm the reset disturbs, so a loss is not
  uniquely useful sensory memory, and no loss does not show a memoryless brain (Astra, Fable). Each brain's τ
  distribution is reported beside it. **No nonspecific-disruption control is run** (Astra asked for one); since the
  probe is measured, not gated, the design states the limit instead. L = 50, above the 20-tick τ ceiling, is the
  reading least confounded by filtering.
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
  bounded-history probe's full replay equals the unperturbed episode, and its rebuild passes the prescribed-sequence
  validation;
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
- A re-evolved MIP brain (criterion 1) replaces the first one for every later criterion; the two are never combined,
  and the first is reported.
- **Pass criteria, all required, evaluated on pilot-check:**
  1. **Evolved brains beat memoryless control and use the cue:** each graph's MIP brain beats the D303 KT winner by a
     paired 95% lower bound above 0.5 targets on the registered check worlds, and loses at least half its score under
     the constant scent. If a graph's MIP brain fails this, one re-evolution with a fresh seed is allowed for this
     criterion only, counted in the cap (Fable: the criterion is about the task and graph, not one seed).
  2. **Solutions use interneurons** (Astra's version of Fable's gate): in each graph, at least 2 of the 3 high targets,
     re-measured on the MIP brain on 2 048 fresh worlds, have drops whose lower bound (one-sided, Bonferroni over the
     three) exceeds p.
  3. **Resolution:** δ_eval and δ_search at most p/2 (§6), judged at the pilot graph's own p; the same quantities are
     also reported against the p of 04a's champions in the mono world (5% of 2.26), so a narrow failure caused by a
     low-scoring shuffled graph is read as such (Fable).
  4. **Headroom in NIP:** at least 3 of the 8 targets have a reliable NIP reference and NIP headroom present. NIP's
     original-partner advantage is reported as the shuffled-graph anchor, not gated: on a shuffled graph nothing
     task-shaped links X to its "true" partners, so gating on it would fail the pilot for a reason N2 does not share
     or pass it through structure (Fable).
  5. **Identifiability and recovery in MIP:** let n be the number of targets that pass (4) and whose MIP reference is
     reliable with MIP original-partner advantage present. Criterion 5 fails if n < 2; otherwise at least ⌈n/2⌉ of
     those n must reach functional success in MIP with a stratified enrichment p below 0.05. The weakest pass, one
     recovery of two, possibly on one graph, is a feasibility threshold, not a replication across graphs (Astra).
  6. **Search diagnostics:** within the thresholds frozen by pilot-dev.
  7. **Timing:** pilot-dev's measured throughputs project the formal design within the remaining cap, with the cuts
     of §10 applied first if needed.
  8. *Not applied (the owner chose to measure history use, D305).* **Only if the owner chooses Astra's reading (§2):** each graph's MIP brain loses at least 0.3 targets under the
     bounded-history probe at the L chosen by pilot-dev, more than the KT calibrator loses at that L.
- The scripted gap is re-measured on registered check worlds (the D303 and D304 winners, not re-tuned) and reported,
  descriptively; it is about the task, which the gates above already cover.
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
| N2 relevance scan (3 brains × (245 deletions + intact) × 512, an upper bound, since a pair is scanned through one member) and selection check (5 × 7 × 512) | | 0.40 M | 0.26 |
| N2 probes: 38 brains × 14 episode-equivalents × 2 048 (4 replay probes counted double, constant, 2 jitters, hold, a two-phase ramp) | | 1.09 M | 0.72 |
| Pilot-dev (cap) | | 9.07 M | 6.00 |
| Pilot-check: 2 × (6 evolutions + 8 target-brains) and 2 re-evolutions (15.71 M); evaluations 16 × 14 × 2 048 (0.46 M); scans 2 × 246 × 512 (0.25 M); interneuron re-measurement 2 × 4 × 2 048 (0.02 M); probes 2 × 6 × 14 × 2 048 (0.34 M) | | 16.78 M | 11.10 |
| Scripted re-measurement and probe calibration | | 0.20 M | 0.13 |
| **Total** (episodes exclude the 2.33 M exploratory worlds already run) | | **about 84.4 M** | **about 56.3** |

The reserve is about 15.7 hours at 420/s; at the wide-batch rate the whole would be about 24 hours. Failed attempts
count. **Cuts, decided from pilot-dev's measured timing before pilot-check runs, in this order:** random-partner
refits 5 → 3; then free searches 5 → 4 (the frozen protocol then restates the ranking and the no-task control over
four searches); then stop and report (Astra: dropping family 2 alone would save no simulator work). Brains per arm
stay at five, and the final-evaluation precision and selector brains are
kept (Astra: with four brains per arm the per-target exact test could never pass Holm, and the cut order must not
silently remove a registered test). The six neurons and both arms are never cut (D094).

## 11. Open questions

1. **For the owner:** history use measured (Fable) or gated (Astra), §2. *Decided 2026-10-17: measured (D305).*
2. **For the reviewers:** none open; round 4 agreed v7 as the basis of the pre-registration, with the fixes v7.1 makes.

## 12. Changes

**v7 → v7.1 (round 4: run 20261017-152826; both "ready for the pre-registration, with small fixes"; D307):**
- **Pilot criterion 4** gates NIP headroom only; original-partner advantage moves to criterion 5 in MIP, and NIP's is
  the reported shuffled-graph anchor (Fable 1). **Random-partner refits** are drawn within the null's strata (Fable 7).
- **δ_search frozen as a fraction of p** (Fable 2); "present" means "above" (Fable 3); the relevance interval is a world
  bootstrap of the three-brain mean, the brain spread reported (Fable 4).
- **Family 2:** shared MIP effects that keep each target's arms exchangeable are inside the null and in its
  calibration; 20 000 datasets per scenario and an acceptance bound of 0.0531; a withheld target keeps p = 1
  (Astra 2).
- **The replay probe:** the first affected action is 2L + 1; comparisons across L are not memory horizons; the
  replayed inputs are the perturbed trajectory's; why the rebuild is fully defined; no nonspecific-disruption control,
  stated; L = 50 the least confounded reading (Astra 3, Fable 6).
- **Support** counted over joint truth patterns (Astra 4); the weakest pilot pass described as feasibility (Astra 5).
- **Wording:** the champions "show little measured loss" (Astra 8); T = 5 above and T = 10 close to the champions
  (Fable 5); the scripted gap's justification (Astra 8); the scan's upper bound (Fable).

**v6 → v7 (round 3: run 20261017-151803; Fable "ready, with small fixes", Astra "revise"; D306):**
- **Family 2 per target under Holm** (both: the pooled test ignored the MIP brains shared across targets; Astra's
  counterexample gives 14.8% false rejections at 5%). The panel mean is descriptive, with no pooled p. The simulated
  validation adds shared-brain effects (Fable) and separates the sharp null from robustness checks (Astra).
- **No selection on reliability in family 2:** a fixed set of five, reliability reported beside it; the imprinting
  reading requires the passing target itself to show MIP recovery and reliable references (Astra 3).
- **The replay probe:** reset timing; bitwise scope of the full-replay control; validation on prescribed inputs;
  KTM expected unaffected; no sign required of KTS; what a loss does and does not mean; τ reported (Astra 4, Fable 2).
- **Criterion 5** cannot pass on an empty set (n ≥ 2, then ⌈n/2⌉; Astra 5); criterion 3 also reported at a reference p
  (Fable 4); a re-evolved MIP brain replaces the first for every later criterion (Astra 5).
- **Resampling:** one shared world resample across brains and states; MIP identities kept across targets; δ_search
  frozen from pilot-check; target-arm reliability defined (Astra 5).
- **The stratified null:** tertile boundaries, unsplit ties, the merge direction, unscoreable subsets, support as
  distinct label arrangements (Astra 6); MCL and MCR corrected (Fable 3).
- **§1 limit** from D305 (Fable 5); the T = 50 row; SEs 0.01-0.05; the KTM grid's nesting noted (Astra 7, Fable 6).
- **Budget:** probes at 14 equivalents with the ramp priced; pilot-check itemised; the exploratory worlds noted as
  outside the episode total; the descriptive fallback removed, since it saved nothing (Astra 8, Fable 6).

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
