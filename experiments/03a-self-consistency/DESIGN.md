# 03a: the self-consistency hypothesis, a six-neuron proof of concept (design v4)

**Status:** design v4, 2026-10-16, for review by Astra 6 and Fable 5.1. Not a pre-registration. Nothing specific to
03a has been coded, drawn or run.
- **The draft it replaces:** [`DRAFT.md`](DRAFT.md) v3.2 (2026-09-25), a 24-neuron panel on experiment 02's T1. It
  stays as the record of the earlier design; this file is the design going forward.
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
  by Astra 6 and Fable 5.1 (D045-D047). This version: Claude Opus 5.5.

## 1. The question

**The hypothesis (the owner's):** if a connectome is shaped to perform tasks, the wiring of one missing neuron can
be predicted, to some extent, from the rest of the brain plus a task. Delete a neuron X, place it back with random
wiring, let only X's wiring optimise for the task, and see whether X's original partners come back.

**What the proof of concept asks:** on six neurons of evolved N2 brains, does this procedure separate the three
outcomes (anatomical recovery, functional substitution, search failure), and does reconstruction with the trained
intact network's information (MIP) recover more anatomy than reconstruction from anatomy alone (NIP), the
"imprinting effect" that D094 makes the condition for expanding the panel?

**What it is not:** a map, or a test that the real worm's wiring is optimised for any task. Every result is
conditional on the model, the task and the search. Six targets give little power for panel-level claims; the
per-target readings carry the proof of concept.

## 2. The task: Task N with one nose ("Task N-mono")

**Proposed:** Task N exactly as E1, 04a and E2 ran it (one wey, a 24-cell arena, a sensing-only scent source of
σ = 6 that jumps to the next position of a per-world sequence when the head comes within 1.5 cells, 300 ticks, energy
off, 32 substeps, the count of targets reached), with **`food_sensing = "mono"`**: both food sensors read the scent
at the head's centre point (`wormwars/world.py`, the branch experiment 02's T1 used). No left-right difference
exists, so steering up the gradient needs a comparison over time.

**Why this task:**
- **Memory is needed to do well, by a scripted gap already measured in this world.** E1's tuned controllers on the
  bilateral mean (the same information as one nose, up to the sample point): memory on the mean (M-avg) 2.16 targets
  per episode; the best memoryless controller on the level (K, level kinesis) 1.03; the best blind one 0.66
  (wall-follower); the oracle 8.85 (`experiments/E1-navigation/RESULTS.md`, tuning table). The gap M − K is about
  1.1 targets, a doubling. It is re-measured in the mono world before anything is built on it (§9, step 1).
- **It is cheap and its throughput is measured:** one wey, 300 ticks. Lockstep batches of 8 runs ran at 419-429
  episodes per second in 04a, E2 and E4s-1, and E2d's wider composition (256 strains × 32 worlds) at about 1 046
  (`experiments/04a-navigation-primitive/compute-record.json`, `experiments/E2-optimizer-screen/compute-record.json`,
  `experiments/E2d-taskn-diagnosis/projection.json`).
- **Evolution works on Task N with N2:** 04a's GA (population 32, 8 worlds per genome, 1 000 generations) gave
  navigators in 12 of 16 runs on the stereo version. Whether it gives memory users on the mono version is not known;
  the pilot measures it on shuffles (§8).
- **It ties to the memory thread:** P4 is a history dependence of the turn read-out under food ramps, and RIA and AIY
  carry the response it is normalised by (03mc). A mono gradient task is the behaviour in which such a dependence
  could be useful. Whether evolved brains use it is measured, not assumed.

**Alternatives considered (for the reviewers to weigh):**
- **Task N with stereo sensing:** proven evolvable (04a), but memoryless stereo steering scores 8.78; it is not a
  memory task, against the roadmap's text.
- **E3a's shuttle task on a whole N2 brain:** needs memory by construction (E's latch is worth +4.83 visits), but it
  has never been played by an N2 brain (there is no N2 mapping of its `at_a`/`at_b` signals), its episodes are 600
  ticks, and from-scratch search for even a 13-parameter selector found one in 1 of 8 GA runs (E3a).
- **Experiment 02's T1** (20 weys, 200 ticks): a scripted memory share of 0.40 (D034), but 02's champions showed no
  detected history use, and its cost per episode is about 20 times a one-wey episode's in brain work.

## 3. Arms and brains

As in the draft (NIP and MIP, both primary; deletion, never silencing; D044):
- **MIP (reconstruction with information from an intact trained network):** evolve an intact brain; delete X; insert
  X with random wiring; search only X. **3 intact N2 brains**, each carrying all six targets.
- **NIP (reconstruction from anatomy alone):** evolve a brain from scratch with X deleted (`deletion.without_neuron`);
  insert X with random wiring; search only X. **3 NIP N2 brains per target** (18).
- **Imprinting:** MIP's recovery minus NIP's, per target (§7).
- **Whole-brain evolution:** 04a's GA unchanged (population 32, 3 elites, top 8 as parents, Gaussian mutation,
  8 worlds per genome, 1 000 generations), unshaped fitness (the count), champion by validation worlds as in 04a.
  Motor gains are calibrated once per graph on intact brains and frozen through deletion and reinsertion (D035).

## 4. The panel: six neurons per graph, by a rule

**Eligible:** neither mapped (sensor or motor, `configs/interface.yaml`) nor pharyngeal; connected by directed paths
both to and from the interface in that graph. About 245 neurons in N2.

**Relevance:** the mean drop in Task N-mono score when the neuron is deleted from that graph's intact brains,
measured on target-selection worlds never used for anything else. For a bilateral pair (`configs/mirror_pairs.yaml`,
the curated annotation, D050), one member is chosen by a fixed seed before any measurement, so its mirror stays in
the brain; the pair is represented by that member.

**Tiers (D094: 3 high, 2 medium, 1 low), fixed by rule before any N2 measurement:**
- **High:** the 3 eligible neurons with the largest drops, each with its drop's lower 95% bound above the margin p
  (§6). Fewer than 3 qualify: take those that do and record the shortfall; the criterion is never relaxed.
- **Medium:** 2 drawn with a fixed seed from the eligible neurons whose drop is above p but not among the top 10
  (proposed band; open question 4).
- **Low:** 1 drawn with a fixed seed from the eligible neurons whose drop's 95% interval lies inside ±p.
- The same rule runs in every graph, so the procedure is matched, not the criticality; each tier's drops and degrees
  are reported per graph.
- Whether the tiers contain RIA, AIY or AIZ (03m's and 02b's leads) is reported; they are never chosen by hand.

## 5. What the search may change (the 02b risk)

02b found that 94 of the 96 most critical deletion targets in 02's champions connect directly to interface neurons.
The draft kept X's interface connections fixed and searched only interneuron partners, so for most critical
targets the recovered part would have been the part that does not make them critical.

**Proposed:** search **all** of X's connections. The candidate pool for every connection type is every
non-pharyngeal neuron other than X, interface neurons included. Recovery is scored over the whole pool and, as
pre-declared secondaries, separately over interface and non-interface candidates.
- The draft excluded interface candidates so that a direct sensor-to-motor shortcut could not make substitution
  trivial. Here X is told its true numbers of incoming, outgoing and gap partners (as in the draft), so a shortcut
  must fit X's own degree. A shortcut that scores well is a finding about substitution, reported as such, not a
  defect.
- Chemical self-connections are kept as in the original and never searched or scored.

## 6. Searches, scoring and margins (the draft's, sized down)

For every target in every brain and arm (a "target-brain"):
- **Original-partner refits, 3** (the reference): true partners; weights, τ and bias optimised.
- **Random-partner refits, 5:** partners drawn uniformly with the true counts.
- **Structural-baseline refits, 2:** paired targets, the mirror ranking's and the class model's top-k; unpaired,
  the class model's and the degree ranking's.
- **Free searches, 5:** partners, weights, τ and bias.
- **MIP check:** reinserting X's saved parameters reproduces the intact score (an implementation check).
- **Initial weights** never use per-edge anatomical magnitudes: every inserted edge starts at `init_w_scale` with a
  random sign; τ and bias from the pinned initial distributions.

**The search:** the draft's replica exchange (4 replicas, 8 offspring, 100 generations, swaps every 5 generations,
partner moves that keep the counts and keep gap junctions symmetric), with **16 search worlds per evaluated state**
(proposed, up from 8, because a 300-tick count is noisier than 02's 20-wey score; the pilot checks it). The ladder is
tuned on pilot graphs only. Refits disable partner moves.

**Implementation:** each lockstep batch shares one connectome mask. X's rows and columns hold every candidate edge,
with weights pinned at zero outside the current partner set. A test checks that this equals a network built with
exactly that partner set.

**Scoring:** the draft's ranking (the mean absolute final weight over the 5 free searches, per connection type),
ROC AUC against the target's label-permutation null, precision at k, PR-AUC and per-search AUC; functional recovery
as a fraction of the intact score, on **512 final-evaluation worlds** (proposed; the draft's 64 cannot resolve 5%
at these scores).

**Margins (the draft's):** a performance margin p of 5% of the intact brain's mean score; noise estimates δ_eval and
δ_search from the pilot, used only for reliability; every performance comparison three-state against ±p
(equivalent, above, below, undetermined).

**Per-target attributes and outcomes:** the draft's five attributes (reference reliability, headroom,
original-partner advantage, functional success, overlap) and its derived outcome summary (excluded; anatomical
recovery; functional success, anatomy undetermined; search failure; inconclusive). Functional substitution is
claimed only for a set of targets with an equivalence band on chance overlap, which six targets are unlikely to
give.

## 7. What is read, and what counts as an imprinting effect

**Proposed confirmatory family (Holm, 12 members):** for each of the 6 N2 targets, in each arm, anatomical enrichment:
the target's AUC (aggregated over its 3 target-brains, equal weight) above its label-permutation null, one-sided.

**Proposed expansion criterion (D094's "imprinting effect"), registered as a reading, not a test:** at least one
target, in a high or medium tier, has
1. MIP anatomical enrichment (passing under Holm) with functional success reached or exceeded, and
2. a MIP − NIP AUC difference whose 90% interval (bootstrap over target-brains and searches) lies above 0.

And the proof of concept "separates the outcomes" if its targets are not all excluded, and at least two different
outcome summaries occur among the non-excluded ones. Both readings are reported whatever they say; expansion still
needs the owner's word and its own pre-registration (D094).

**Descriptive:** every attribute per target-brain; the cross-table; the panel-mean MIP − NIP AUC with its interval;
the no-task control (§8); per-target stratification by whether X has interface partners; whether the high tier
includes 03m's leads.

## 8. Controls, null graphs and the pilot

**Null graphs (D094 allows the null arms to be cut first):** proposed, one of experiment 03's validated ensembles,
**SH-mirror**, with 3 graphs (fresh seeds), each with its own panel by the same rule, 1 intact brain and 1 NIP brain
per target. N2 against SH-mirror is descriptive at this size. SH-mirror is proposed because mirror symmetry is the
most generic explanation for recovered partners (the mirror ranking predicts many of them); SH-route is the
alternative (routing changes which neurons are critical). Open question 3.

**No-task control:** free searches with fitness identically zero, for every N2 target in one MIP brain. With zero
fitness the search is a random walk over partner sets, so it needs no simulation and costs nothing on the GPU. It
tests the pipeline for bias toward true partners.

**Dropped from the draft (stated):** the mismatched-task control; ordinary SH as a second null; whole-brain RD.

**Implementation tests before any GPU work** (the draft's list): deletion equals a network without X; the union mask
with zeroed edges equals the partner-set network; direction (in and out unswapped); gap symmetry after moves;
degrees constant during a search; common random numbers; a planted optimum on a small synthetic problem; the
no-task control's AUC distribution matches the permutation null.

**The pilot (GPU; graphs SH-mirror pilot seeds outside every formal draw; never N2):**
- 2 pilot graphs; per graph 1 intact brain, the panel rule's 3 high targets plus 1 low target, 1 NIP brain per
  target: 8 targets, 10 whole-brain evolutions.
- **Pass criteria, all required:**
  1. **Memory in the task, scripted (step 1, before any evolution):** in the mono world, the best tuned memory
     controller beats the best tuned memoryless one by a paired lower bound above a registered margin.
  2. **Evolved brains use the cue and beat memoryless control:** the pilot's intact champions beat K-mono's tuned
     score (paired lower bound above 0), and lose score under the constant-scent probe.
  3. **Resolution:** δ_eval and δ_search at most p/2.
  4. **Headroom and identifiability in NIP** (interneuron use): at least 3 of the 8 targets have a reliable
     reference, headroom present and original-partner advantage present.
  5. **MIP recovery:** on the targets passing (4), MIP free searches reach functional success with anatomical
     enrichment on at least half.
  6. **Timing:** the measured throughput projects the whole formal design under the remaining cap.
- If the pilot fails, the formal panel does not run, and the pilot is reported.

## 9. Order of work and budget

**Order:**
1. Mono-world scripted gate (E1's controller families, tuned on fresh tuning worlds): CPU or a few GPU-minutes.
2. Code and implementation tests (CPU), reviewed by both.
3. Pilot (GPU; the owner's word first), reported openly.
4. Pre-registration, reviewed, bound and pushed before any N2 brain is evolved.
5. Formal run (the owner's word first), results, review, publication.

**Budget (72 GPU-hours, pilot included, registered in code, never extended).** At a conservative 420 episodes per
second (8-run lockstep batches; the wider compositions the searches allow measured about 1 000):

| Workload | Count | Episodes | Hours at 420/s |
|---|---|---|---|
| One search (100 gen × 4 replicas × 9 states × 16 worlds) | | 57 600 | 0.038 |
| One target-brain (15 searches) | | 864 000 | 0.57 |
| N2 target-brains: MIP 6 × 3, NIP 6 × 3 | 36 | 31.1 M | 20.6 |
| N2 whole-brain evolutions: 3 intact + 18 NIP, 256 000 episodes each | 21 | 5.4 M | 3.6 |
| SH-mirror target-brains: 3 graphs × 6 targets × 2 arms | 36 | 31.1 M | 20.6 |
| SH-mirror evolutions: 3 × (1 + 6) | 21 | 5.4 M | 3.6 |
| Pilot: 16 target-brains + 10 evolutions | | 16.4 M | 10.8 |
| Relevance scans, final evaluations (512 worlds), scripted gate, checks | | about 3 M | 2 |
| **Total** | | **about 92 M** | **about 61** |

At the measured wide-batch rate it would be about 26 hours. **The cut order if the pilot's projection exceeds the
remaining cap:** SH-mirror to 2 graphs, then no null arm, then random-partner refits and free searches 5 → 3 (with
pilot criteria 4-5 re-checked at the reduced counts), then stop and report. The six neurons, both arms, the reference
refits and N2's three brains per arm are never cut (D094).

## 10. Open questions for the reviewers

1. **The task.** Is Task N-mono a defensible "task that requires memory" for this proof of concept, given a scripted
   gap of about one target (M-avg 2.16 against K 1.03)? Is pilot criterion 2 (beat K-mono, lose score under the
   constant probe) the right operational check that evolved solutions use history, or is a direct history probe
   needed (for example, a P4-style ramp on the evolved brain, or a scent whose recent history is scrambled)?
2. **The 02b risk.** Searching all connections with interface candidates included (§5), or the roadmap's other
   option (choose targets whose relevance does not come from interface adjacency)?
3. **The null arm.** SH-mirror or SH-route, and is 3 graphs worth its 24 hours, or should the proof of concept be N2
   only with the null arm left to the expansion?
4. **The tiers.** Are the high, medium and low bands (§4) well defined, and is "medium = drop above p, outside the
   top 10" sensible with six targets?
5. **The confirmatory family and the expansion criterion (§7).** Per-target enrichment under Holm, and a registered
   expansion reading: right for a proof of concept, or should the proof of concept register no hypothesis tests at
   all and only the readings?
6. **Anything in the draft's machinery** (attributes, three-state margins, reliability, structural baselines) that
   should be simplified at six targets, or that no longer fits the new task.
7. **The budget arithmetic** and the cut order.
