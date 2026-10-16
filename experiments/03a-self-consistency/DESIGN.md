# 03a: the self-consistency hypothesis, a six-neuron proof of concept (design v5)

**Status:** design v5, 2026-10-16, for review by Astra 6 and Fable 5.1. Not a pre-registration. Nothing specific to
03a has been coded or run, apart from the exploratory scripted checks in §2 (D303).
- **v4** (`eeeeb60`, D302): both reviewers said "revise" (run 20261016-174135, `docs/reviews/20261016-03a-design-v4/`).
  v5 takes their findings (§12 lists each and what changed) and adds the exploratory checks of D303.
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
  by Astra 6 and Fable 5.1 (D045-D047). v4-v5: Claude Opus 5.5, reviewed by Astra 6 and Fable 5.1.

## 1. The question, and what it can and cannot show

**The hypothesis (the owner's):** if a connectome is shaped to perform tasks, the wiring of one missing neuron can
be predicted, to some extent, from the rest of the brain plus a task. Delete a neuron X, place it back with random
wiring, let only X's wiring optimise for the task, and see whether X's original partners come back.

**What the proof of concept asks:** on six neurons of evolved N2 brains,
1. does the search recover X's original partners beyond what the partners' kind (sensor, motor, other) and degree
   explain, in each arm;
2. does reconstruction with the trained intact network's information (MIP) recover more than reconstruction without
   prior exposure to X (NIP), the "imprinting effect" that D094 makes the condition for expanding the panel; and
3. does the procedure separate the three outcomes (anatomical recovery, functional success with anatomy
   undetermined, search failure)?

**Limits, stated now (Astra):**
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
- **The search is told X's true numbers of partners** of each kind. Every conclusion is conditional on that.
- **Six targets** support per-target readings, not panel-level generalisation.
- A positive result shows self-consistency under this model, task and search, not that the real worm's wiring is
  optimised for the task.

## 2. The task: Task N with one nose ("Task N-mono")

**Proposed:** Task N exactly as E1, 04a and E2 ran it (one wey, a 24-cell arena, a sensing-only scent source of
σ = 6 that jumps to the next position of a per-world sequence when the head comes within 1.5 cells, 300 ticks, energy
off, 32 substeps, the count of targets reached), with **`food_sensing = "mono"`**: both food sensors read the scent
at one sample point, `P_FRONT_C`, 0.6 cells ahead of the head (`wormwars/world.py:839`, the branch experiment 02's T1
used). Collision sensing stays bilateral. No left-right food difference exists, so steering up the gradient needs a
comparison over time, or some other use of the brain's own dynamics.

**What the exploratory checks of D303 found** (2026-10-16; 0.40 GPU-hours, charged to 03a's cap; records and scripts
in [`development-records/`](development-records/); world ids 1 481 000 000-511 and 1 481 100 000-255, outside every
registered range):
- **The task rewards memory, by a wide scripted gap.** A memoryless family richer than E1's K (one level threshold;
  speed *and* turn rate set by the level; optional collision avoidance; 1 920 grid points, tuned on 256 tuning
  worlds) reaches **1.20** targets per episode on 512 check worlds (SE 0.05). The same family with one tick of memory
  (a separate turn when the level has fallen; nested, so it differs only by the memory) reaches **2.84** (SE 0.04).
  E1's K and M-avg score 0.95 and 2.22 in the mono world.
- **Evolution reaches it already.** 04a's 16 champions, trained on stereo Task N, score the same with one nose
  (median 2.26 against 2.32 with stereo; range 2.03-2.68), as E2d's finding that no Task N champion uses the
  left-right difference predicts (`experiments/E2d-taskn-diagnosis/RESULTS.md`). Every one beats the tuned
  memoryless family by about 0.8-1.5 targets, and every one collapses with a constant scent (0.08-0.34).
- **But their history use is not shown, and is not fast.** Under the jitter probe (the scent read at a random point
  within r cells, fresh every tick: the level survives, tick-to-tick change becomes noise), the memory controller
  falls from 2.84 to 1.53, 0.51 and 0.04 at r = 0.5, 1, 2; the memoryless one from 1.20 to 0.82; the champions do
  not move (median 2.26, 2.26, 2.25, 2.25). Holding the reading for h ticks barely affects them at h ≤ 5 and lowers
  most at h = 20 (median 1.73), but it also lowers the memoryless controllers, so hold is not specific to memory.
  So the champions beat every memoryless controller tried without depending on tick-to-tick change. They may use a
  slow comparison, the body's own dynamics, or a memoryless strategy outside the families tried.

**What this means for the design:**
- "A task that requires memory" holds at the task level (the scripted gap), and the evolved level sits above the
  best memoryless controller found. Whether evolved solutions use history, and at what timescale, is **measured as an
  attribute of the brains, not assumed**, with a history-erase probe that keeps the current input (§8).
- The roadmap's other requirement, that solutions use interneurons, becomes a pilot gate measured directly by
  deletion (§8, criterion 3).
- **Alternatives considered:** stereo Task N (memoryless stereo steering scores 8.78, so not a memory task); E3a's
  shuttle on an N2 brain (never played by one; no N2 mapping of its signals; 600 ticks; from-scratch search hard);
  experiment 02's T1 (20 weys, about 20 times the brain work per episode, and its champions' history use was
  neither shown nor excluded, 02 RESULTS, though 02b later found a history-dependent read-out of unknown value).

## 3. Arms and brains

Deletion, never silencing (D044). For each graph:
- **Selector brains: 3 intact**, evolved only to choose the targets (§4). They are never used for reconstruction,
  so target selection does not favour the MIP brains (Astra).
- **MIP: 5 intact brains**, each carrying all six targets: delete X, insert X with random wiring, search only X.
- **NIP: 5 brains per target**, each evolved from scratch with X deleted: insert X with random wiring, search only X.
- **Whole-brain evolution:** 04a's GA unchanged (population 32, 3 elites, top 8 as parents, Gaussian mutation,
  8 worlds per genome, 1 000 generations), unshaped fitness (the count), champion chosen on validation worlds as in
  04a. Motor gains are calibrated once per graph on random genomes of the intact graph, as D035 does, and frozen
  through deletion and reinsertion.
- **Batching:** the five NIP brains of one target share one mask (X's edges removed) and run in one lockstep batch;
  MIP and selector brains share the intact mask. Throughput for these batch sizes is measured in the pilot.
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
a 95% interval from a paired bootstrap over worlds within brains. The margin p is 5% of the selector brains' mean
intact score on those worlds. Ties are broken by a fixed seeded order.

**Tiers (D094: 3 high, 2 medium, 1 low), relative, so the panel always has six; absolute relevance is reported:**
- **High:** the 3 eligible neurons with the largest mean drops. A member whose lower bound does not exceed p is
  flagged "relatively high only".
- **Medium:** 2 drawn with a fixed seed from the remaining neurons whose interval contains p (Fable). If fewer than 2
  exist, the rest are drawn from ranks 4-20, flagged.
- **Low:** 1 drawn with a fixed seed from the neurons whose interval lies inside ±p. If none exists, the neuron with
  the smallest absolute drop, flagged.
- The same rule runs in every graph, so the procedure is matched, not the criticality.
- **Reported per graph:** each tier's drops, intervals, degrees and classes; drops by paired versus unpaired (with
  identical left and right input, one member of a pair may drop little, so the high tier may be all unpaired, Fable);
  whether the tiers contain RIA, AIY or AIZ (03m's and 02b's leads). Nothing is chosen by hand.
- **A selection check:** the six targets' drops are re-measured on the MIP brains on fresh worlds and reported, so
  selection on the selector brains is not mistaken for relevance in the MIP brains.

## 5. What the search may change (the 02b risk)

02b found that 94 of the 96 most critical target-champion observations in experiment 02 had edges to interface
neurons, and that deleting only those edges cost a median 35% of the full deletion's damage
(`experiments/02b-champion-analysis/RESULTS.md` §4). The draft kept those edges fixed, so its reinsertions would have
started partly recovered.

**Proposed:** search **all** of X's connections. The candidate pool for every connection type is every neuron other
than X, interface and pharyngeal neurons included, so exact restoration is always possible.
- X is told its true numbers of incoming chemical, outgoing chemical and gap partners. A sensor-to-X-to-motor
  shortcut can still fit within them (Astra); it is a legitimate substitution, and recovering a few obvious
  interface partners is weaker evidence than recovering the rest. So the primary null is stratified (§6), and
  recovery is reported separately over interface and non-interface candidates.
- **Chemical self-connection:** if X has one, its presence is kept; its weight is re-initialised by the
  partner-independent rule and searched with X's other weights (Fable: keeping the evolved weight would leak it in
  MIP). It is never scored.

## 6. Searches, scoring and the recovery statistic

For every target in every brain and arm (a "target-brain"):
- **Original-partner refits, 3** (the reference): true partners; X's weights, τ and bias optimised.
- **Random-partner refits, 5:** partners drawn uniformly with the true counts.
- **Free searches, 5:** partners, weights, τ and bias.
- **MIP exact restoration:** reinserting X's saved parameters reproduces the intact score (an implementation check).
- **Deleted-brain score:** each brain's score with X deleted and not reinserted.
- The draft's structural-baseline *refits* are dropped (Fable: they fed no reading); the structural *rankings* stay,
  as anatomical comparators at no GPU cost.

**Initialisation, independent of the hidden partners:** inserted chemical weights start at magnitude
`init_w_scale` with a random sign; inserted gap conductances start at the pinned initial gap scale, non-negative
(`Genome.clamp_` keeps g ≥ 0, Astra); τ and bias from the pinned initial distributions. No per-edge anatomical
magnitude is used.

**The search:** the draft's replica exchange (4 replicas at fixed temperatures, 8 offspring per replica per
generation, the best offspring replacing the current state by the Metropolis-like rule, neighbour swaps every 5
generations, 100 generations), on **16 search worlds per evaluated state**, shared by all states of a generation. It
is a tempered optimiser, not an equilibrium sampler, and nothing here relies on sampling guarantees (Astra).
Partner moves keep the counts and keep gap junctions symmetric; refits disable them. Settled in the pilot's
development stage and then frozen (§8): the ladder, the mutation-type probabilities, whether one offspring may make
several partner moves, the search worlds (16 or 32), and whether the *search* signal adds 04a's bounded progress
bonus to the count (Fable; every reported score stays the raw count).

**Scoring:**
- **Final evaluation on 2 048 worlds** per scored state (Fable: at p ≈ 0.11 targets and a per-world SD near 1, 512
  worlds leave most three-state comparisons undetermined).
- **Ranking:** per target-brain and connection type, each candidate's score is the mean absolute final weight (or
  conductance) of its connection to X over the 5 free searches (0 if not connected). Ties get the average rank.
- **Recovery statistic:** the ROC AUC of that ranking against the true partners, averaged with equal weight over
  the defined connection types, then over the five brains of the arm.
- **Primary null, stratified (Fable, Astra):** the true-partner labels are permuted within strata defined by the
  candidate's kind (sensor, motor, pharyngeal, other) crossed with tertiles of its total degree in the graph with X
  deleted. One permutation is drawn per target and applied to every brain, search and connection type of that
  target, so brains are not counted as independent anatomical evidence (Astra). B = 10 000.
- **Structural comparators (no GPU):** the mirror ranking (paired targets), the class-model ranking and the degree
  ranking, each with its AUC against the same truth, reported beside every task AUC. **Beyond structure** (Astra):
  the task AUC minus the composite structural AUC (mirror for paired targets, class model for unpaired), and for
  paired targets the task AUC on the candidates the mirror ranking leaves tied at zero (the draft's SC3-paired).
- **Also reported:** precision at k against the same null, PR-AUC, per-search AUC, the AUC over interface and over
  non-interface candidates, and the no-task control's AUC (§8).

**Margins and attributes (the draft's, restated):**
- **p** = 5% of the MIP brains' mean intact score on the final-evaluation worlds. δ_eval and δ_search from the
  pilot are used only for reliability.
- **Three-state comparisons:** a paired difference on the final-evaluation worlds with its 95% interval, from a
  bootstrap over worlds within brains and over brains: *equivalent* if inside ±p, *above* if entirely above +p,
  *below* if entirely below −p, otherwise *undetermined*. Undetermined is never counted either way.
- **Five attributes per target and arm** (and per target-brain, descriptive): reference reliability (refit SD at
  most 2 δ_search and, in MIP, the reference not below exact restoration); headroom (reference minus deleted-brain
  score); original-partner advantage (reference minus mean random-partner refit); functional success (mean free
  search minus reference: reached if equivalent, exceeded if above, failed if below); overlap (anatomical enrichment
  if the arm's enrichment test passes under Holm, §7).
- **Functional recovery** is the free searches' score as a fraction of the MIP brains' mean intact score in both
  arms; the NIP brains' own deleted and intact-equivalent scores are reported beside it.

**Outcome summary per target and arm** (Astra: the unit is the target-arm, combining its brains; enrichment and
functional success come from the same brains and searches):
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

**Family 2, imprinting (Holm, 5 members: the high and medium targets):** for each, the difference MIP − NIP in the
recovery statistic, by an exact permutation of arm labels over the ten brains (252 splits, one-sided), counted only
if the difference is also at least **0.05 AUC**. The low target's contrast is reported, not tested. With 5 brains per
arm the smallest attainable p is 1/252 ≈ 0.004, below the strictest Holm level 0.01, so a contrast that separates
the arms completely can pass.

**The registered readings:**
- **"Imprinting effect" (D094's condition for expansion):** at least one high or medium target passes family 2,
  has anatomical enrichment in MIP (family 1) and functional success reached or exceeded in MIP.
- **"The proof of concept separates the outcomes":** at least two of the three substantive outcomes (anatomical
  recovery; functional success, anatomy undetermined; search failure) occur among the 12 target-arms (Fable).
- Both readings are reported whatever they say. Neither is evidence of a mechanism. Expansion still needs the
  owner's word, a stated reason, and its own pre-registration with independent brains (D094; Astra).

**Descriptive:** every attribute per target-brain and target-arm, with the cross-table; all brain-level contrasts
and the leave-one-brain-out range of each imprinting contrast; the panel-mean MIP − NIP with its interval; the
beyond-structure contrasts; the selection check; the history-erase probe and the other probes on every evolved brain
(§8); stratification by whether X has interface partners.

## 8. Controls, the pilot and the probes

**Null graphs:** the formal null arm is cut (both reviewers): three SH-mirror graphs with one brain per arm would
support only a descriptive comparison at about a third of the cap. The pilot's SH-mirror graphs give a descriptive
shuffled-graph anchor. A null comparison belongs to the expansion. (SH-mirror is also routing-matched as SH-route,
`wormwars/exp03/samplers.py`.)

**No-task control:** free searches with fitness identically zero, for every N2 target in one MIP brain. Every
offspring is accepted, so the search is a random walk over partner sets and needs no simulation. It tests the
pipeline for bias toward true partners, against the stratified null. It cannot rule out generic routing preferences
that appear only under task selection (Astra).

**Probes on every evolved brain (descriptive; Task N-mono, 2 048 worlds each):**
- **History erase (new; Astra's matched-current-input probe):** every k ticks (k = 10, 20, 50), each neuron's state
  is replaced by the brain's steady state under the current input held fixed, so the current input acts but history
  older than k ticks is erased. The same probe on the memoryless and memory scripted controllers is its calibration.
- The constant scent, jitter (r = 1) and hold (h = 20) probes, as in D303.
- A P4-style ramp on the evolved brain (rising against falling to the same level, the turn and speed read-outs).

**Implementation tests before any GPU work:**
- deletion equals a network built without X; the union mask with zeroed edges equals the network built with exactly
  that partner set, including gap contributions to neighbours' denominators, at a tolerance declared in the test;
- the frozen background is bitwise unchanged by reinsertion (weights copied by edge identity, never re-initialised;
  Astra);
- in NIP evolution, X's edges stay at zero through initialisation and every mutation;
- direction (in and out unswapped); gap symmetry after moves; degrees constant during a search; common random
  numbers;
- **an information boundary:** changing the hidden truth while keeping the allowed inputs leaves initialisation and
  free-search proposals unchanged, with sabotage checks that pinning and truth isolation fail when broken (Astra);
- a planted optimum on a small synthetic problem; the no-task control's AUCs match the stratified null.

**The pilot, in two stages (Astra: development separate from the feasibility check), on SH-mirror graphs with seeds
outside every formal draw, never N2:**
- **Pilot-dev** (one graph; at most 6 GPU-hours): evolves selector, MIP and NIP brains for 2 targets; tunes what §6
  leaves open; records the search diagnostics (Q, the fraction of true partners connected, along each trajectory;
  partner turnover; accepted topology moves; ranking agreement on independent worlds; a 2× longer search on a
  subset). Its outputs are frozen in the pre-registration's pilot protocol before pilot-check runs.
- **Pilot-check** (two fresh graphs, the frozen protocol): per graph 1 selector brain, 1 MIP brain and 1 NIP brain
  per target, for the panel rule's 3 high targets and 1 low target: 8 targets in all.
- **Pass criteria, all required, evaluated on pilot-check:**
  1. **Scripted memory gap** in the mono world, re-measured on registered tuning and check worlds: the memory family
     beats the memoryless family by a paired 95% lower bound of at least 0.5 targets.
  2. **Evolved brains beat memoryless control and use the cue:** each pilot graph's MIP brain beats the tuned
     memoryless family by a paired lower bound above 0.5 targets, and loses at least half its score under the
     constant scent.
  3. **Solutions use interneurons** (Fable): each pilot graph has at least 3 eligible neurons whose drop's lower
     bound exceeds p.
  4. **Resolution:** δ_eval and δ_search at most p/2.
  5. **Headroom and identifiability in NIP:** at least 3 of the 8 targets have a reliable reference, headroom
     present and original-partner advantage present.
  6. **MIP recovery:** on the targets passing (5), MIP free searches reach functional success, with the stratified
     enrichment p below 0.05, on at least half.
  7. **Timing:** the measured throughput projects the formal design within the remaining cap.
- If the pilot fails, the formal run does not happen, and the pilot is reported. One pilot-check attempt; a
  second needs the owner's word.

## 9. Order of work

1. Code and implementation tests (CPU), reviewed by both.
2. Pilot-dev (GPU; the owner's word first), reported openly.
3. Pre-registration with the frozen pilot protocol, reviewed by both, bound and pushed.
4. Pilot-check under the registration; if it passes, the formal N2 run (the owner's word before each GPU stage).
5. Results, review by both, publication.

## 10. Budget (72 GPU-hours, everything included, registered in code, never extended)

At a conservative 420 episodes per second (the measured 8-run lockstep rate; the search batches can be wider, where
about 1 000 was measured, E2d):

| Workload | Count | Episodes | Hours at 420/s |
|---|---|---|---|
| Exploratory checks so far (D303) | | | 0.40 |
| One search (100 gen × 4 replicas × 9 states × 16 worlds) | | 57 600 | 0.038 |
| One target-brain (13 searches) | | 748 800 | 0.50 |
| N2 target-brains: 6 targets × (5 MIP + 5 NIP) | 60 | 44.9 M | 29.7 |
| N2 whole-brain evolutions: 3 selector + 5 MIP + 30 NIP, 256 000 episodes each | 38 | 9.7 M | 6.4 |
| N2 final evaluations (2 048 worlds), relevance scan, probes | | 2.5 M | 1.6 |
| Pilot-dev (cap) | | 9.1 M | 6.0 |
| Pilot-check: 2 graphs × (6 evolutions + 8 target-brains) + evaluations | | 15.9 M | 10.5 |
| Scripted gate (registered re-measurement) | | 2.0 M | 1.3 |
| **Total** | | **about 84 M** | **about 56** |

The reserve is about 16 hours at 420/s; at the wide-batch rate the whole would be about 24 hours. Failed attempts
count. **Cuts, decided from pilot-dev's timing before pilot-check runs:** random-partner refits 5 → 3; then free
searches 5 → 4; then brains per arm 5 → 4; then stop and report. Final-evaluation precision and the selector brains
are kept before search count (Astra). The six neurons and both arms are never cut (D094).

## 11. Open questions for the reviewers

1. **The task, given D303:** evolved brains beat every memoryless controller tried by about one target, yet ignore
   fast history. Is Task N-mono still the right task, with history use measured (history erase) rather than gated?
   Or should history use be a gate, at the risk that the pilot fails on a task otherwise suited to the question?
2. **The history-erase probe** (§8): is resetting to the steady state under the current input a sound
   matched-current-input history ablation, and what should calibrate it?
3. **Family 2:** 5 brains per arm and an exact arm-label permutation with a 0.05 AUC floor. Is this an honest
   imprinting test, or should the proof of concept keep the contrast descriptive (Astra's preference in round 1)?
4. **The stratified null** (§6): are kind × degree tertiles the right strata, and is one shared permutation per
   target right?
5. **Pilot-check's size** (1 selector, 1 MIP, 1 NIP per target per graph) and criteria 1-7: enough to decide, and
   are the thresholds right?
6. **The budget** and the cut order.

## 12. Changes from v4 (round 1: run 20261016-174135; both "revise")

- **Task:** kept, with D303's checks (Fable: test the 04a champions under mono first). The memory gate is now
  against a richer memoryless family (Astra: K is a narrow baseline) and the champions' history use is reported as
  not shown; a history-erase probe with the current input matched is added (Astra); constant-probe and
  beat-K criteria alone no longer stand as evidence of history (both).
- **Interneuron use is a pilot gate,** by deletion (Fable 4); "interneuron" is defined (Astra 8).
- **Target selection on separate selector brains** (Astra 2); relative tiers that always give six, with absolute
  relevance flagged (Astra) and the medium and low bands by interval against p (Fable 7); pair rules,
  paired-versus-unpaired report (Fable 8); a selection check on the MIP brains.
- **The 02b wording corrected:** about a third of the damage, not "the part that does not make them critical"
  (Astra 11).
- **Recovery null stratified by kind and degree,** one shared permutation per target (Fable 1-2, Astra 4-5);
  structural rankings as AUC comparators and a beyond-structure reading (Astra 4); structural refits dropped (Fable).
- **The imprinting test** is now a Holm family with a 0.05 AUC floor, 5 brains per arm and exact permutations
  (Astra 5, Fable 9: the old expansion reading's chance rate was about 20%); the separation reading needs two
  substantive outcomes (both).
- **Unit of analysis and outcome unit** defined (Astra 9); a per-search coincidence table (Astra 5).
- **2 048 final-evaluation worlds; 512 selection worlds** (Fable 6).
- **The search:** tunable choices listed and frozen after pilot-dev; diagnostics added (Astra 8, Fable 10); not
  described as an equilibrium sampler (Astra).
- **Implementation contracts:** gap initialisation non-negative; pharyngeal candidates included; self-connection
  weight re-initialised; background bitwise; NIP pinning; information-boundary and sabotage tests (Astra 7, Fable 12).
- **Calibration wording** corrected to D035's random genomes (Fable); functional recovery's denominator defined
  (Fable); `P_FRONT_C` named (both).
- **The formal null arm cut** (both); SH-mirror for the pilot (both).
- **Pilot split** into development and a frozen check (Astra 12); budget recomputed with the reserve both asked for.
- **Limits stated** in §1 (Astra 3).
