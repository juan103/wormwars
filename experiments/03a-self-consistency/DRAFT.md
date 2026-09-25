# WormWars 03a: the self-consistency hypothesis. A 24-neuron panel study

**Status: DRAFT v3.2** (2026-09-25). v2 was reviewed by Astra 6 and Fable 5.1 as part of the
roadmap review (`docs/reviews/20260925-163118-roadmap/`). v3 folded in their points and
experiment 02's lessons (`NOTES_FROM_02.md`). v3.1 folds in Fable's review of v3
(`docs/reviews/20260925-172550-v3/`). v3.2 folds in Astra 6's review of v3.1, run at maximum
effort (`docs/reviews/20260925-174815-v31/`). Where the two disagreed, the choice is recorded in
D047. The changes are listed at the end.

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

**What "recovery" means here.** The search places only X's connections to non-interface neurons.
X's true connections to mapped sensor and motor neurons are kept fixed (see "The panel"). So
recovery means recovery of the non-interface partners.

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
  - evolution training worlds (8 per genome per generation, as in 02);
  - target-selection worlds, used for criticality (64);
  - search worlds, per generation (8, shared by all states of that generation);
  - final evaluation worlds (64, as 02's held-out set).

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
3. **Structural-baseline refits, 2 per target.** Paired targets: the top-k of the mirror
   ranking and of the class-model ranking. Unpaired targets, which have no mirror: the top-k of
   the class-model ranking and of the degree ranking. Ties at the k-th place are broken by a
   fixed seeded order. Only weights, time constant and bias are optimised.
4. **Free searches, 5 independent.** Partners, weights, time constant and bias are all optimised.

**Known attainable reference (MIP only):** reinserting X's saved original parameters exactly
must reproduce the intact score within numerical tolerance. This is an implementation check.

**Deleted-brain score:** the brain's score with X deleted and not reinserted, in both arms.

**Initialisation independent of hidden partners:**
- Every inserted connection starts at the same magnitude, `init_w_scale`, with a random sign.
  The per-edge anatomical magnitude is never used, since it would leak which partners are true.
- Time constant and bias come from the pinned initial distributions.
- All refits start from the same rule.

## Margins

Two kinds of number, kept apart (Astra):

- **Performance margin p, a scientific tolerance fixed now:** 5% of the intact brain's mean score
  in that graph and task. "Equivalent", "above" and "below" are judged against p.
- **Noise estimates, measured in the feasibility pilot:**
  - δ_eval: the standard deviation of an intact brain's mean score across independent sets of 64
    evaluation worlds;
  - δ_search: the standard deviation of final scores across repeated original-partner refits of
    the same target.
  Each is pooled across pilot targets and arms as a root mean square. They are used only for
  reliability checks. If either exceeds p/2, the pilot fails: the method could not resolve the
  registered tolerance.
- **Three-state comparison.** Each comparison below is a paired difference on the final
  evaluation worlds, with its 95% interval. The difference is:
  - **equivalent** if the interval lies inside ±p;
  - **above** if it lies entirely above +p;
  - **below** if it lies entirely below −p;
  - **undetermined** otherwise. An undetermined comparison is never counted as either.

## Per-target attributes, and the outcome summary

Each target in each brain gets five attributes, reported separately and cross-tabulated (Astra:
an exclusive classification order would hide targets with little headroom but recoverable
anatomy).

1. **Reference reliability:**
   - *reliable:* the SD of the 3 original-partner refits is at most 2 δ_search, and, in MIP, the
     reference is equivalent to or above the exact restoration of the saved neuron;
   - *underperforming:* in MIP, the reference is below the saved-neuron restoration (consistently
     poor refits);
   - *unstable:* otherwise.
2. **Headroom** (reference minus deleted-brain score):
   - *present:* above;
   - *absent:* equivalent;
   - *reinsertion harmful:* below;
   - *undetermined.*
3. **Original-partner advantage** (reference minus mean random-partner refit):
   - *present:* above;
   - *absent:* equivalent. The task does not tell those sampled wirings apart; this is a
     statement about the sampled alternatives only;
   - *random partners better:* below. This is a difference, not non-identifiability;
   - *undetermined.*
4. **Functional success** (mean free search minus reference):
   - *reached:* equivalent;
   - *exceeded:* above;
   - *failed:* below;
   - *undetermined.*
5. **Overlap**, the aggregated-ranking AUC against the target's own label-permutation null:
   - *anatomical enrichment:* above the null's 95th percentile. This is enrichment for true
     partners, not a claim of full reconstruction;
   - *not detected:* inside the central 90%. This means only that no enrichment was detected;
     anatomy is undetermined;
   - *depleted:* below the 5th percentile.

**Outcome summary** (derived from the attributes, for the central table):
- **Excluded:** reference not reliable.
- **Anatomical recovery:** functional success reached or exceeded, and anatomical enrichment.
- **Functional success, anatomy undetermined:** functional success reached or exceeded, and
  overlap not detected.
- **Search failure:** functional success failed.
- **Inconclusive:** anything else.

Headroom and original-partner advantage are shown beside each summary, never folded into it. The
full attribute cross-table is reported for every cell and condition.

**Functional substitution** needs positive evidence of chance-level overlap, which a single
target cannot give. It is therefore claimed only at cell level: the targets in the cell reach
functional success, and the cell's mean AUC interval lies inside 0.5 ± 0.03.

The distribution of outcome summaries, with the attribute cross-table, per panel cell and graph
condition, is the **central descriptive result** of 03a.

## Graph conditions

Every target is scored against the true partners in its own graph.

- **N2:** the real wiring. 3 intact brains, and 3 NIP brains per target, all with different
  seeds.
- **SH-matched:** 6 routing- and mirror-matched shuffles from experiment 03's ensemble, the first
  6 by generation seed. The rule is fixed now, before 03 exists. 1 intact brain and 1 NIP brain
  per target per graph. This is the main control. N2's mirror symmetry and
  its lack of food-to-motor shortcuts are generic properties, and this ensemble matches them.
- **SH:** 3 ordinary degree-preserving shuffles, as in experiments 01b and 02. Same numbers as
  SH-matched.
- **RD:** dropped. SH and RD have never separated in this series, and the budget goes to matched
  graphs instead.

## The panel

Each graph gets its own panel of 24 targets, chosen by the same rule. That keeps the procedure
matched, not the resulting criticality (Astra), so each cell's criticality and degree
distributions are reported per condition. Choosing targets only for being critical in N2 would
favour N2.

**Eligible neurons:**
- not among the roughly 40 mapped sensor and motor neurons;
- not pharyngeal, since this task does not use pumping;
- connected by directed paths both to and from the interface in that graph.
Chemical self-connections are left exactly as in the original, never searched, and excluded from
scoring.

**Candidate partners for the searches:** all eligible neurons plus the non-interface,
non-pharyngeal neurons, but **never the mapped sensor and motor neurons**. Otherwise the
score-maximising wiring is a direct sensor-to-motor shortcut, which experiment 02 showed scores
well and which would make functional substitution trivial.

**Kept connections.** X's true connections to interface neurons, and its chemical
self-connection if it has one, are kept as fixed *partners* in every search, refit and arm.
Their *weights* are initialised by the partner-independent rule and optimised together with the
rest of X's weights. They are excluded from scoring. The count of kept connections is reported
per target.

**Paired or unpaired:** from a curated left/right annotation file, fixed before the tag and
built from the dataset's or WormAtlas's annotation, never from name patterns. The helper
`structure.mirror_index` uses name suffixes and is not used here. For each bilateral pair, one
member is chosen with a fixed seed *first*, so the target's mirror stays in the brain. Pairs are
then ranked by that member's own drop.

**Criticality:** the mean drop in score when the neuron is *deleted* from that graph's intact
brains, measured on the target-selection worlds, which are never used for final evaluation.

**Cells, 6 targets each:**

| | high criticality | low criticality |
|---|---|---|
| **paired** | the 6 paired neurons with the largest drops above p | 6 drawn at random, with a fixed seed, from paired neurons whose drop is within p |
| **unpaired** | the 6 unpaired neurons with the largest drops above p | 6 drawn at random, with a fixed seed, from unpaired neurons whose drop is within p |

- If a high cell has fewer than 6 neurons with a drop above p, take all that qualify and record
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

**Intervals** are 95% hierarchical bootstrap intervals, B = 20 000. They follow the design,
which is crossed in one arm and nested in the other (Astra):
- graph instances are resampled within a condition;
- **targets** are resampled once per graph. That same resample is used across MIP brains, across
  arms and across baselines, so every paired contrast stays paired;
- **MIP brains** are crossed with targets, since each intact brain carries all 24 targets. They
  are resampled independently of targets;
- **NIP brains** are nested within their target, and are resampled within it;
- searches are resampled within each target-brain.
Student t-intervals over graph instances are reported beside them, because 3-6 graph instances
undercover. A P-value of zero is reported as P < 1/B.

**Analysis set.**
- **Primary:** targets whose reference is reliable.
- **Contrasts across arms or baselines** (SC3, SC4) use the *common* set: targets reliable in
  every arm involved. The two sides always compare the same targets.
- **Secondary:** only targets with functional success reached or exceeded.
- **Stratification:** SC1-SC4 are also reported by whether X has kept interface connections (0,
  or more than 0).

**Verdicts,** mutually exclusive (Astra). Each hypothesis has a null value and an equivalence band
around it:
- **supported:** the interval lies entirely on the predicted side of the null value, and not
  entirely inside the band;
- **negligible:** the interval lies entirely inside the band, whichever side it is on;
- **reversed:** the interval lies entirely on the other side, and not entirely inside the band;
- **null:** anything else;
- **withheld:** data are incomplete under the completeness rule, fixed at the tag.

**Confirmatory family,** high-criticality cells unless stated. It has five members: SC1, SC2,
SC3-unpaired, SC3-paired and SC4. They are Holm-corrected, and each member's interval is reported
at its Holm-adjusted level. **Bands,** in AUC units, fixed now: 0.5 ± 0.02 for SC1 and
SC3-paired, and 0 ± 0.03 for the differences in SC2, SC3-unpaired and SC4.
- **SC1, self-consistency exists.** N2, NIP arm: mean AUC is above 0.5.
- **SC2, it belongs to the real wiring.** NIP arm: N2's AUC minus SH-matched's AUC is above 0.
  N2 minus ordinary SH is reported beside it, as a secondary.
- **SC3, it adds to structure.**
  - Unpaired high-criticality N2 targets: NIP AUC minus composite-baseline AUC is above 0.
  - Paired high-criticality N2 targets: the task ranking's AUC, restricted to the candidates the
    mirror ranking leaves undecided (tied at zero), is above 0.5 (Fable). Targets with no true
    partner among those candidates have no AUC. They are excluded and counted.
- **SC4, imprinting.** N2: MIP AUC minus NIP AUC is above 0.

**Exploratory:**
- **SC5, compensation:** the Spearman correlation between NIP AUC and compensation deficit
  across all 24 N2 targets. With 3 seeds it is dominated by evolutionary noise for low-criticality
  targets (Fable).

**Power, stated honestly:** the high-criticality cells hold at most 12 targets per graph, and
SC3 for unpaired targets rests on at most 6. 03a is a panel study. Null results here are weak
evidence and should be read as such.

## Controls and tests

**Implementation tests, before the pilot** (synthetic data or pilot shuffles only):
- **Deletion test:** a brain with X deleted produces the same dynamics, within numerical
  tolerance, as a separately built network in which X never existed (301 neurons, re-indexed).
- **Direction test:** an asymmetric test neuron with known incoming and outgoing partners is
  recovered with the two sets unswapped.
- **Gap symmetry test:** after any gap move, the gap matrix is still symmetric.
- **Degree test:** the reinserted neuron's numbers of partners never change during a search.
- **Common random numbers test:** re-scoring the same state on the same seeds gives the same
  score.
- **Planted-optimum test, synthetic:** on a small synthetic problem with a known best wiring, the
  search finds it.
- **Development versions of the two task controls** below, run on the pilot shuffles, to debug
  them and calibrate the permutation null.

**Task controls on N2, after the confirmatory freeze** (Astra: they touch N2, so they cannot run
before the tag):
- **No-task control:** rebinding with a reward that is identically zero, for the 12 N2
  high-criticality targets in one intact brain. It is calibrated against the permutation null of
  the whole pipeline. It tests implementation bias.
- **Mismatched-task control:** rebinding under the roadmap's non-worm-like control task, for the
  same 12 targets. It tests whether the chosen task carries specific information.

**Feasibility pilot** (pilot shuffles SH101 and SH102, never N2 or panel graphs). Per pilot graph:
one intact brain, one NIP brain per target, and 4 high-criticality targets chosen by the panel
rule, 2 paired and 2 unpaired. That is 8 targets in all. It passes only if all four hold:
1. **Resolution:** δ_eval and δ_search are both at most p/2.
2. **NIP headroom and identifiability** (Astra: the reference must beat *both* the deleted brain
   and random partners): in the NIP arm, at least 4 of the 8 targets have a reliable reference,
   headroom present, and original-partner advantage present.
3. **MIP recovery:** on the targets that passed (2), the MIP free searches reach functional
   success with anatomical enrichment on at least half. This checks the method where the answer
   is attainable by construction. It does not show NIP headroom, which (2) does.
4. **Timing:** at the planned batch width, the measured throughput projects the full panel under
   the budget rule. The projection includes every workload:
   - searches and whole-brain evolutions;
   - both task controls;
   - criticality selection, calibration and final scoring.
   If the budget cut applies, feasibility (2) and (3) must be re-checked at the reduced search
   counts.

**Pilot cost:** about 432 000 genome evaluations per arm, about 11 GPU-hours per arm at 02's
batch-32 throughput. It also needs 10 whole-brain evolutions: 2 intact and 8 NIP. It drops
sharply if wider batching works, and the pilot measures exactly that.

If the pilot fails, the panel is not run and the pilot is reported. The pilot also supplies
δ_eval, δ_search, the temperature ladder and the throughput.

## Budget

- **Workload as written:** 576 target-arm-brain combinations: N2 24 × (3 + 3), SH-matched
  6 × 24 × 2, SH 3 × 24 × 2. Each gets 3 + 5 + 2 + 5 = 15 searches, of 100 generations ×
  4 replicas × 9 evaluated states. That is about 31 million genome evaluations before whole-brain
  evolution.
- **Whole-brain evolutions** add 12 intact and 288 NIP brains, each 150 generations × 32
  genomes = 4 800 evaluations. That is about 37 GPU-hours at 02's rate, and about 25 after
  reduction step 1.
- **At 02's batch-32 throughput** (about 11 genome evaluations per second), the searches alone
  come to about 785 GPU-hours. Staying under the one-week cap needs about 4.9 times 02's speed if
  both workloads speed up, or about 6 times if only the searches do.
  Experiment 02's batched scripted tuning was about 85 times faster than serial evaluation. The
  pilot measures it.

**Rule:** if the pilot's projection exceeds 168 hours (one week):
1. reduce to 16 targets per graph, 4 per cell: the high cells keep their 4 largest drops, and
   the low cells the first 4 of their seeded draw;
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

## Changes in v3.1 (Fable's review of v3)

- **Every comparison is three-state** (equivalent, above, below, undetermined), and each
  classification step is written two-sided. v3 let an undetermined free search through as
  "reached", and missed a reference below the deleted score and random partners above the
  reference.
- **Per-target overlap** is judged against each target's permutation null, which a fixed band
  cannot be (the null SD is about 0.10-0.15). The fixed band stays for cell-level aggregates.
- **δ_search** is measured on original-partner refits, not free searches.
- **Analysis set** defined: all targets except reference failures (primary), step-5 targets
  (secondary), and a stratification by kept interface connections.
- **Equivalence bands** are fixed for every hypothesis, and the Holm family is named (5 members,
  intervals at the adjusted level).
- **Pilot:** its design and arms are specified. The refit screen runs in the NIP arm, and its
  criterion is an interval statement.
- **Budget:** adds the whole-brain evolutions (about 37 GPU-hours) and the pilot's own cost,
  and notes that 11 per second is a batch-32 rate.
- **Fixed rules:** the numbers of worlds; how SH-matched graphs are picked; pair-member choice
  before ranking; SC3-paired targets without a scoreable partner; which targets survive a cut.

## Changes in v3.2 (Astra's review of v3.1, maximum effort)

- **Uncertainty is never negative evidence.** Every comparison keeps an undetermined state, and
  random partners beating the original are reported as a difference, not as non-identifiability.
  This disagrees with Fable on its point 5; D047 records why.
- **Attributes instead of an exclusive order.** Headroom, original-partner advantage, functional
  success and overlap are reported separately and cross-tabulated. The outcome summary is derived
  from them, so a low-headroom target with recoverable anatomy stays visible.
- **Margins separated:**
  - a scientific performance margin p (5% of the intact score), fixed now;
  - noise estimates used only for reliability, pooled as a root mean square across pilot
    targets and arms;
  - the pilot fails if noise exceeds p/2;
  - references that consistently underperform the saved-neuron restoration in MIP are flagged.
- **Overlap labels corrected:**
  - above the permutation null is "anatomical enrichment";
  - inside it is "no enrichment detected, anatomy undetermined", not substitution;
  - functional substitution is claimed only at cell level, with an equivalence band.
  This partly reverses v3.1's adoption of Fable's point 6. The permutation null stays; the
  reading changes.
- **Pilot:** criterion (2) requires NIP targets with a reliable reference and headroom present,
  not just an advantage over random partners. The targets split 2 paired and 2 unpaired per
  graph. The pilot needs 10 whole-brain evolutions, not 18. Timing covers every workload, and
  feasibility is re-checked if the budget cut applies.
- **N2 task controls move after the freeze.** Their development versions run on pilot shuffles.
- **Verdicts are mutually exclusive:** supported, negligible, reversed, null or withheld. The
  unused fixed chance band is removed.
- **Bootstrap:** targets are crossed with MIP brains and nested for NIP brains, and one target
  resample is shared across arms and baselines. SC3 and SC4 use the common analysis set.
- **Specified:**
  - tie-breaking for the structural top-k;
  - the unpaired structural refits (class model and degree);
  - that kept connections have fixed partners and optimised weights;
  - panel matching is of the procedure, not of criticality.

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
