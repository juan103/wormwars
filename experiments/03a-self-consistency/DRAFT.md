# WormWars 03a: the self-consistency hypothesis. A 24-neuron panel study

**Status: DRAFT v3** (2026-09-25). v2 was reviewed by Astra 6 and Fable 5.1 as part of the roadmap
review (`docs/reviews/20260925-163118-roadmap/`). v3 folds in their points and experiment 02's
lessons (`NOTES_FROM_02.md`). The changes are listed at the end.

Next steps: review v3 again. Then write the code and run the feasibility pilot, both disclosed
and on pilot shuffles only, never N2. Freeze code, analysis and the pilot-derived margins, and
tag `exp03a-prereg` before any confirmatory run. Any change after the tag is a deviation and goes
in DECISIONS.md.

- **Hypothesis:** Juan H. González Estefan.
- **Design:** Claude Fable 5.1 (Anthropic), in conversation.
- **Reviews:** Astra 6 (OpenAI) on v1 and v2; Fable 5.1 on v2.
- **v3 revision:** Claude Opus 5.5 (Claude Code), with the owner's delegation.

## The hypothesis

**Self-consistency hypothesis:** if a connectome is shaped to perform tasks, the wiring of one
missing neuron can be predicted, to some extent, from the rest of the brain plus a task. Place the
neuron back with random wiring, and let only that neuron optimise for the task.

It borrows from two ideas:

- **Self-consistent field methods.** In Hartree-Fock, each orbital is optimal in the field of all
  the others. Here, each neuron's wiring would be optimal given the rest of the brain. The
  single-neuron test is the analogue of an SCF stability check.
- **Molecularly imprinted polymers.** A polymer formed around a template keeps a cavity that
  rebinds it, and every imprinting study compares against a non-imprinted polymer (NIP) made
  without the template.

If the hypothesis holds, task optimisation becomes one more tool for filling gaps in incomplete
connectome reconstructions, alongside structural methods.

**What this is not.** Useful wiring need not be uniquely recoverable. A negative result can mean
that many wirings serve the task equally well, which says something about the task and the
procedure, not necessarily about the connectome. The four-way classification below exists to
tell these cases apart.

**What 03a is for.** Before paying for a map of the whole brain (03b), 03a tests on a fixed panel
whether the method can tell apart three outcomes:
- the neuron's original wiring is recovered (anatomical recovery);
- a different wiring does the job equally well (functional substitution);
- the search fails (search failure).

## Inputs fixed now

- **Task:** single-nose foraging (T1) exactly as in experiment 02:
  `wormwars/exp02/grid.py:task_config(…, "T1")`. That is 20 weys, odour sigma 1, 200 ticks, food
  x2, halved food sensing scale, pheromone off, 32 substeps and automatic eating. Its parameters
  are copied into `configs/exp03a.yaml` before the tag. Experiment 02's evolved T1 champions solve
  it without detected history use, so many targets may prove not identifiable (NOTES_FROM_02).
  The feasibility pilot measures this before the panel is bought.
- **Brain model:** as in the pinned code, with no plasticity, and D030's gap truncation (kept in
  experiment 02).
- **Motor calibration:** each graph's gains are calibrated once, in-world, on the intact graph
  (D035), and frozen through deletion and reinsertion.
- **Code:** pinned at the tag, including the chemical-direction fix and a true deletion operator
  (built and tested in 02b; see "Deletion" below).
- **Evolution of whole brains:** the pinned genetic algorithm, 150 generations, population 32.
  Experiment 02's continuations were still improving at 80 generations.
- **Seed partitions,** fixed in the config, disjoint from each other:
  - evolution training worlds;
  - target-selection worlds, used for criticality;
  - search worlds, per generation;
  - final evaluation worlds.

## Arms

Both arms are primary, each for its own claim. They differ only in the evolved weights; the
remaining anatomy is the real one in both.

- **NIP arm: reconstruction from anatomy alone.** Evolve a brain from scratch with target neuron X
  deleted. Then insert X with random wiring and evolve only X, with the rest frozen.
  - Named assumption: the rest of the brain has already settled on one weight solution that
    compensates for X's absence. An anatomy-only method could instead infer weights and the
    missing wiring jointly. That is exploratory here.
- **MIP arm: reconstruction with functional information from an intact *simulated trained*
  network.** Evolve a brain with X present, delete X, insert X with random wiring, and evolve only
  X with the rest frozen.
  - This is information from a trained model, not measured activity from an animal. MIP is not
    assumed to be an upper bound.
- **Imprinting:** the difference in recovery between the MIP and NIP arms (not a ratio).
- **Compensation deficit:** the intact brain's score minus the NIP brain's score before X is
  reinserted. It shows how much work reinsertion had left to do.

**Deletion** means removing all of X's incoming, outgoing and gap connections, its time constant
and its bias, so that no term involving X remains in any other neuron's update. **Silencing**,
meaning clamping X's activity, is a different intervention. With gap junctions, a clamped neuron
still pulls its neighbours toward the clamp value. The pinned code's `Brain.silence` does exactly
that (D044), so it is not used anywhere in 03a.

## Reference searches

For every target in every brain:

1. **Original-partner refits (the reference), 3 independent.** X keeps its true partners; only
   its weights, time constant and bias are optimised. The reference score is their mean. Their
   spread is also reported.
2. **Random-partner refits, 5 independent partner sets.** Partners are drawn at random with the
   same numbers of incoming, outgoing and gap connections. Only weights, time constant and bias
   are optimised.
3. **Structural-baseline refits, 1 each.** The partner sets are the top-k of the mirror ranking
   and of the class-model ranking. Only weights, time constant and bias are optimised.
4. **Free searches, 5 independent.** Partners, weights, time constant and bias are all optimised.

**Known attainable reference (MIP only):** reinserting X's saved original parameters exactly
must reproduce the intact score within numerical tolerance. This is an implementation check.

**Deleted-brain score:** the brain's score with X deleted and not reinserted, in both arms.

**Initialisation independent of hidden partners:**
- Every inserted connection starts at the same magnitude, `init_w_scale`, with a random sign.
  The per-edge anatomical magnitude is never used, since it would leak which partners are true.
- Time constant and bias come from the pinned initial distributions.
- All refits start from the same rule.

## Margins (measured in the feasibility pilot, frozen at the tag)

- **δ_eval:** evaluation noise, the spread of an intact brain's score across independent sets of
  evaluation worlds.
- **δ_search:** search noise, the spread of final held-out scores across repeated free searches
  of the same target.
- **Equivalence margin m = max(δ_eval, δ_search).** Every "reaches" or "within" statement is a
  paired comparison on the final evaluation worlds. It holds when the paired difference's 95%
  interval lies inside ±m.
- **AUC chance band:** [0.45, 0.55], fixed now.

## Outcome classification

Applied per target and brain, in this order:

1. **Reference failure:** the original-partner refits disagree by more than m, or the MIP
   exact-restoration check fails. The target is excluded from recovery statistics and counted.
2. **No headroom:** the reference is within m of the deleted-brain score. X does not matter
   here. Criticality measured in intact brains does not guarantee headroom in NIP brains, which
   compensated during evolution.
3. **Not identifiable:** the mean of the 5 random-partner refits reaches the reference within m.
   The task cannot tell the sampled wirings apart for this neuron. This is a statement about the
   sampled alternatives, not about all wirings.
4. **Search failure:** the mean of the 5 free searches stays more than m below the reference.
5. Otherwise the free searches reach the reference, and:
   - **anatomical recovery:** the target's AUC interval (over searches) lies above 0.55;
   - **functional substitution:** the AUC interval lies inside the chance band [0.45, 0.55];
   - **inconclusive overlap:** anything else.

**Exceeding the reference:** if the free-search mean is *above* the reference by more than m,
this is recorded, and step 5 applies to the target unchanged. A better-than-original wiring with
chance-level overlap is functional substitution.

The distribution of these outcomes, per panel cell and graph condition, is the **central
descriptive result** of 03a.

## Graph conditions

Every target is scored against the true partners in its own graph.

- **N2:** the real wiring. 3 intact brains, and 3 NIP brains per target, all with different
  seeds.
- **SH-matched:** 6 routing- and mirror-matched shuffles from experiment 03's ensemble. 1 intact
  brain and 1 NIP brain per target per graph. This is the main control. N2's mirror symmetry and
  its lack of food-to-motor shortcuts are generic properties, and this ensemble matches them.
- **SH:** 3 ordinary degree-preserving shuffles, as in experiments 01b and 02. Same numbers as
  SH-matched.
- **RD:** dropped. SH and RD have never separated in this series, and the budget goes to matched
  graphs instead.

## The panel

Each graph gets its own panel of 24 targets, chosen by the same rule, so conditions are compared
at matched criticality. Choosing targets only for being critical in N2 would favour N2.

**Eligible neurons:**
- not among the roughly 40 mapped sensor and motor neurons;
- not pharyngeal, since this task does not use pumping;
- connected by directed paths both to and from the interface in that graph.
Chemical self-connections are left exactly as in the original, never searched, and excluded from
scoring.

**Candidate partners for the searches:** all eligible neurons plus the non-interface,
non-pharyngeal neurons, but **never the mapped sensor and motor neurons**. Otherwise the
score-maximising wiring is a direct sensor-to-motor shortcut, which experiment 02 showed scores
well and which would make functional substitution trivial. X's true partners among interface
neurons are kept fixed in every search and excluded from scoring. The count of such kept
connections is reported per target.

**Paired or unpaired:** from a curated left/right annotation file, fixed before the tag and
built from the dataset's or WormAtlas's annotation, never from name patterns. The helper
`structure.mirror_index` uses name suffixes and is not used here. For each bilateral pair, one
member is chosen with a fixed seed, so the target's mirror stays in the brain.

**Criticality:** the mean drop in score when the neuron is *deleted* from that graph's intact
brains, measured on the target-selection worlds, which are never used for final evaluation.

**Cells, 6 targets each:**

| | high criticality | low criticality |
|---|---|---|
| **paired** | the 6 paired neurons with the largest drops above m | 6 drawn at random, with a fixed seed, from paired neurons whose drop is within m |
| **unpaired** | the 6 unpaired neurons with the largest drops above m | 6 drawn at random, with a fixed seed, from unpaired neurons whose drop is within m |

- If a high cell has fewer than 6 neurons with a drop above m, take all that qualify and record
  the shortfall. The criterion is never relaxed.
- An empty cell is reported as empty, never back-filled.
- Each cell's distributions of criticality and degree are reported per condition. Conditions
  whose panels differ in criticality are compared with that difference shown.

**The low-criticality cells are a comparison stratum, not a negative control** (Astra). A neuron
can matter little yet still be predictable from the remaining structure.

## Search algorithm

**What the reinserted neuron is given:** its true numbers of incoming, outgoing and gap partners
among the candidate pool. A connection type with zero true partners stays at zero, and is
excluded from that target's scoring.

**Initial state:** partners uniformly at random among the candidates. Weights, time constant and
bias as in "Initialisation independent of hidden partners".

**Mutations:** each offspring gets one of the following, with probabilities fixed in the config
before the pilot and never tuned on N2:
- move one connection (incoming, outgoing or gap, chosen in proportion to their counts) to a
  random candidate it is not already connected to, keeping the weight. A gap move updates both
  sides, since gap junctions are symmetric;
- a Gaussian perturbation of the weights;
- a Gaussian perturbation of the time constant and bias.

**Replica exchange (parallel tempering):**
- M = 4 replicas at geometrically spaced temperatures T₁ < T₂ < T₃ < T₄.
- Each replica holds one current state and produces λ = 8 offspring per generation. The offspring
  and the current state are all scored on the same search worlds for that generation (common
  random numbers).
- The best offspring o replaces the current state c if its score s_o ≥ s_c. Otherwise it
  replaces it with probability exp((s_o − s_c) / T).
- Every 5 generations, alternating between even and odd neighbour pairs, replicas m and m+1
  swap states with probability min(1, exp((1/T_m − 1/T_{m+1}) × (s_{m+1} − s_m))).
- 100 generations per search. The result is the coldest replica's final state, scored on the
  final evaluation worlds.
- The temperature ladder is tuned on pilot shuffles only, then discarded. It aims for a 20-40%
  swap acceptance rate between neighbours.
- Refits use the same algorithm, with partner moves disabled.

## Scoring

**Candidate ranking:** for each target and connection type, each candidate gets a continuous
score. It is the mean, over the 5 free searches, of the absolute weight or conductance on its
connection to X in the final state (zero if not connected). Ties get the average rank.

**Metrics, per target and connection type:**
- **ROC AUC**, with chance at 0.5. The decision rules below use it. Its interval over searches is
  a bootstrap over the 5 free searches' rankings.
- **Precision at k** (k = the true number of partners among the candidates). Its null is computed
  by permuting the candidate labels under the same aggregation, not assumed hypergeometric.
- **Area under the precision-recall curve,** against its chance level.
- **Per-search AUC,** so that an aggregate ranking that matches no single working reconstruction
  is visible.
- **Functional recovery:** the brain's held-out score with the reinserted X, as a fraction of the
  intact score.

**A target's summary** is the equal-weight mean over its defined connection types. The null for
this summary comes from the same permutation. Per-type results are also reported.

**Structural baselines,** computed only from the graph with X deleted:
- **Mirror:** for paired targets, rank candidates by the weight of the mirror-image connection of
  X's bilateral partner, using the curated annotation. Where that would require a connection to
  or from X itself, which was deleted, use the class-model score.
- **Class model:** the connection probability between X's neuron class and each candidate's
  class, estimated with X removed. Class annotation comes from the dataset or WormAtlas; if none
  is available, stop and ask.
- **Degree,** and **chance.**
- **The composite baseline** is fixed by rule: mirror for paired targets, class model for
  unpaired targets. It is never selected by how well it scores on a target.

## Hypotheses and decision rules

**Intervals** are 95% hierarchical bootstrap intervals, B = 20 000. The resampling preserves the
design's dependence:
- graph instances within a condition;
- then brains, where a MIP intact brain is resampled together with all targets that share it;
- then targets;
- then searches.
Student t-intervals over graph instances are reported beside them, because 3-6 graph instances
undercover. A P-value of zero is reported as P < 1/B.

**Verdicts:**
- **supported:** the interval lies entirely on the predicted side;
- **contradicted,** labelled by cause: *reversed* (the interval lies entirely on the other side),
  or *tightly null* (the interval lies inside the equivalence band registered for that
  hypothesis);
- **null:** anything else;
- **withheld:** data are incomplete under the completeness rule, fixed at the tag.

**Confirmatory family,** high-criticality cells unless stated, Holm-corrected across SC1-SC4:
- **SC1, self-consistency exists.** N2, NIP arm: mean AUC is above 0.5.
- **SC2, it belongs to the real wiring.** NIP arm: N2's AUC minus SH-matched's AUC is above 0.
  N2 minus ordinary SH is reported beside it, as a secondary.
- **SC3, it adds to structure.**
  - Unpaired high-criticality N2 targets: NIP AUC minus composite-baseline AUC is above 0.
  - Paired high-criticality N2 targets: the task ranking's AUC, restricted to the candidates the
    mirror ranking leaves undecided (tied at zero), is above 0.5 (Fable).
- **SC4, imprinting.** N2: MIP AUC minus NIP AUC is above 0.

**Exploratory:**
- **SC5, compensation:** the Spearman correlation between NIP AUC and compensation deficit
  across all 24 N2 targets. With 3 seeds it is dominated by evolutionary noise for low-criticality
  targets (Fable).

**Power, stated honestly:** the high-criticality cells hold at most 12 targets per graph, and
SC3 for unpaired targets rests on at most 6. 03a is a panel study. Null results here are weak
evidence and should be read as such.

## Controls and tests

**Before the pilot:**
- **Deletion test:** a brain with X deleted produces the same dynamics, within numerical
  tolerance, as a separately built network in which X never existed (301 neurons, re-indexed).
- **Direction test:** an asymmetric test neuron with known incoming and outgoing partners is
  recovered with the two sets unswapped.
- **Gap symmetry test:** after any gap move, the gap matrix is still symmetric.
- **Degree test:** the reinserted neuron's numbers of partners never change during a search.
- **Common random numbers test:** re-scoring the same state on the same seeds gives the same
  score.
- **Planted-optimum test, synthetic:** on a small synthetic problem with a known best wiring, the
  search finds it. Synthetic data only.
- **No-task control:** rebinding with a reward that is identically zero, for the 12 N2
  high-criticality targets in one intact brain. It is calibrated against the permutation null of
  the whole pipeline, not against an interval that merely contains 0.5. This tests
  implementation bias.
- **Mismatched-task control:** rebinding under a different task's reward, the roadmap's
  non-worm-like control task, for the same 12 targets. This tests whether the chosen task
  contributes specific information.

**Feasibility pilot** (on pilot shuffles SH101 and up, never N2 or panel graphs). It passes only
if all three hold:
1. **Refit screen:** on at least 4 of 8 high-criticality pilot targets, the original-partner
   reference beats the mean random-partner refit by more than m.
2. **Real-model planted test:** in a MIP brain, on the targets passing (1), the free searches'
   AUC interval lies above 0.55 on at least half of them.
3. **Timing:** the batched throughput projects the full panel under the budget rule.

If the pilot fails, the panel is not run and the pilot is reported. The pilot also supplies
δ_eval, δ_search, the temperature ladder and the throughput.

## Budget

- **Workload as written:** 576 target-arm-brain combinations: N2 24 × (3 + 3), SH-matched
  6 × 24 × 2, SH 3 × 24 × 2. Each gets 3 + 5 + 2 + 5 = 15 searches, of 100 generations ×
  4 replicas × 9 evaluated states. That is about 31 million genome evaluations before whole-brain
  evolution.
- **At experiment 01's unbatched speed** (about 11 evaluations per second), that is about 785
  GPU-hours. So the one-week cap binds unless batching gives more than about 5 times the speed.
  Experiment 02's batched scripted tuning was about 85 times faster than serial evaluation. The
  pilot measures it.

**Rule:** if the pilot's projection exceeds 168 hours (one week):
1. reduce to 16 targets per graph, 4 per cell;
2. if still over, reduce random-partner refits from 5 to 3 and free searches from 5 to 3;
3. if still over, stop and report before proceeding.

Never drop the NIP arm, the MIP arm, the refits, the no-task or mismatched-task control, or graph
replication. Record the final numbers in DECISIONS.md before the confirmatory runs.

## Exploratory (labelled as such)

- **Crosslink dial:** for a few targets, the rest of the brain keeps mutating at low and medium
  rates while X rebinds.
- **Joint inference:** X rebinds while the rest of the brain's weights also adapt, starting from
  the NIP brain.
- **Selectivity:** transplant the wiring of X's mirror partner, a same-class neuron and a random
  neuron into X's slot, and compare how well each fits.
- **Funnel analysis:** along search trajectories, the score against Q, the fraction of true
  partners currently connected.
- **Shortcut exposure:** rerun a few targets with interface neurons allowed as candidates, to
  measure how often the search takes them.
- **Transfer:** rebind, on stereo foraging, a brain evolved on single-nose foraging.
- **Reversed wiring:** N2 with the chemical direction reversed, as a fourth condition. The
  roadmap's experiment 03 also includes it at generation 0.
- **Free degree:** the reinserted neuron chooses how many partners to have, with a wiring cost in
  the score.

## Honesty notes

- The task is small, so recovery can only be expected for the neurons it uses. Every result is
  conditional on this task.
- A positive result shows self-consistency under this model and task. It does not show that the
  real worm's connectome is optimised for this task.
- The reinserted neuron is told its true number of partners, which a real reconstruction may not
  know.
- There is no plasticity in this brain model, so compensation happens only through evolution,
  not within a lifetime.
- Every behaviour claim needs the same metric on untrained or random baselines, as established
  after the flanking correction in experiment 01.

## Changes since draft v2 (review by Astra 6 and Fable 5.1, and experiment 02)

- **Candidate partners exclude the mapped sensor and motor neurons,** which prevents trivial
  shortcut substitution. A shortcut-exposure run is exploratory (Fable).
- **Outcome classes:** added reference failure, no headroom and inconclusive overlap. There is an
  explicit rule for exceeding the reference. "Not identifiable" is worded for sampled
  alternatives only (both).
- **Refits:** 3 original-partner refits instead of 1, and 5 random-partner sets. Structural-baseline
  refits, a MIP exact-restoration check and the deleted-brain score are added (both).
- **Margins:** m = max(δ_eval, δ_search) with paired interval comparisons, replacing 2 × SD of the
  evaluation noise. The AUC chance band is fixed at [0.45, 0.55] (both).
- **Controls:** the low-criticality cells become a comparison stratum. The no-task control is
  calibrated against a permutation null, and a mismatched-task control is added (Astra).
- **SC3 (paired)** is tested on the candidates the mirror leaves undecided. SC5 is exploratory.
  SC1-SC4 are Holm-corrected. "Contradicted" is split by cause, and "withheld" is added (both).
- **Graphs:** the main control is 6 routing- and mirror-matched shuffles from experiment 03. The
  ordinary shuffles stay; RD is dropped. The bootstrap keeps shared MIP brains together, and
  t-intervals are reported beside it (both; experiment 02).
- **Other fixes:**
  - initialisation independent of the hidden partners;
  - frozen motor calibration;
  - separate seed partitions;
  - a curated left/right annotation, not name suffixes;
  - permutation nulls for aggregated metrics;
  - per-search AUC;
  - an empty-cell rule;
  - criticality and degree distributions reported (Astra).
- **Feasibility pilot** with a registered pass criterion. The panel runs only if it passes (both).
- **Order of work:** code and pilot are disclosed and happen before the tag. Code, analysis and
  margins are frozen before the confirmatory runs (Astra: the draft's "tag before any code"
  conflicted with its own batched pilot).
- **Budget recounted:** about 31 million genome evaluations as now written, 785 GPU-hours
  unbatched. v2's allocation gave about 14 million, 353 GPU-hours, not 280 (Astra).
- **Silencing is not deletion:** confirmed in the pinned code (D044).

## What comes after: 03b and beyond

- **03b, the full map:** all eligible neurons, if 03a shows the method can separate the outcomes,
  with at least a pre-registered minimum count of informative targets.
- **More tasks:** if the connectome is shaped by many behaviours, the fraction of recoverable
  neurons should grow as tasks are added.
- **Leave-k-out:** remove 5%, 10% and 25% of neurons at once.
- **Missing synapses:** remove individual connections rather than whole neurons.
- **Full self-consistent field:** scramble the whole connectome, then cycle through the neurons,
  re-optimising each in the field of the others with damping. See whether it converges back to
  the real wiring.
