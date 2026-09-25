# WormWars 03a: the self-consistency hypothesis. A 24-neuron panel study

**Status: DRAFT v2.** Revised after external review of v1 by Astra 6. Next steps: review again, commit, and tag `exp03a-prereg` before any code for 03a is written. Any change after the tag is a deviation and goes in DECISIONS.md.

Hypothesis: Juan H. González Estefan. Design: Claude Fable 5.1 (Anthropic), in conversation. Review: Astra 6 (OpenAI).

## The hypothesis

**Self-consistency hypothesis:** if a connectome is shaped to perform tasks, the wiring of one missing neuron can be predicted, to some extent, from the rest of the brain plus a task: place the neuron back with random wiring and let only that neuron optimise for the task.

It borrows from two ideas:

- **Self-consistent field methods.** In Hartree-Fock, each orbital is optimal in the field of all the others. Here, each neuron's wiring would be optimal given the rest of the brain. The single-neuron test is the analogue of an SCF stability check.
- **Molecularly imprinted polymers.** A polymer formed around a template keeps a cavity that rebinds it, and every imprinting study compares against a non-imprinted polymer (NIP) made without the template.

If the hypothesis holds, task optimisation becomes one more tool for filling gaps in incomplete connectome reconstructions, alongside structural methods.

**What 03a is for.** Before paying for a map of the whole brain (03b), 03a tests on a fixed panel whether the method can tell apart three outcomes: the neuron's original wiring is recovered (anatomical recovery), a different wiring does the job equally well (functional substitution), or the search simply fails (search failure).

## Inputs fixed now, independent of experiment 02's results

- **Task:** the single-nose foraging task exactly as specified in the committed experiment 02 pre-registration, 20 weys, automatic eating, no combat. Its parameters are copied into `configs/exp03a.yaml` before the tag. If experiment 02's solvability gate found this task unsolvable, use the stereo foraging task from experiment 01b instead.
- **Brain model:** as in the pinned code, with no plasticity. Gap-junction initialisation follows whatever experiment 02 decided about D030; if nothing was decided, the pinned code's behaviour.
- **Code:** a commit pinned at the tag, including the chemical-synapse direction fix from experiment 01b.
- **Evolution of whole brains:** the pinned code's genetic algorithm, 150 generations, population 32.

## Arms

Both arms are primary, each for its own claim. They differ only in the evolved weights; the remaining anatomy is the real one in both.

- **NIP arm: reconstruction from anatomy alone.** Evolve a brain from scratch with target neuron X deleted. Then insert X with random wiring and evolve only X, with the rest frozen. A reconstruction that has only the incomplete anatomy would have to evolve weights without X, as here.
- **MIP arm: reconstruction with functional information from the intact animal.** Evolve a brain with X present, delete X, insert X with random wiring, and evolve only X with the rest frozen. The rest of the brain was tuned with X present, so this arm assumes information that an anatomy-only reconstruction lacks. It is not assumed to be an upper bound.
- **Imprinting** is reported as the difference in recovery between the MIP and NIP arms, not a ratio.
- **Compensation deficit:** the intact brain's score minus the NIP brain's score before X is reinserted. This shows how much work reinsertion had left to do.

**Deletion** means removing all of X's incoming, outgoing and gap connections, its time constant and its bias, so that no term involving X remains in any other neuron's update. Silencing, meaning clamping X's activity, is a different intervention: with gap junctions, a clamped neuron still pulls its neighbours toward the clamp value. Silencing is not used anywhere in 03a.

## Reference searches: the controls that make the result readable

For every target in every brain, run three kinds of search:

1. **Original-partner refit (ceiling):** X keeps its true partners; only its weights, time constant and bias are optimised.
2. **Random-partner refit (floor):** X gets partners drawn at random with the same number of incoming, outgoing and gap connections; only weights, time constant and bias are optimised. Three independent random partner sets.
3. **Free search:** partners, weights, time constant and bias are all optimised.

**Score equivalence margin δ:** twice the standard deviation of the intact brain's score across independent held-out seed sets, measured in the pilot and fixed before real runs.

**Outcome classification**, applied per target and brain, in this order:

- **Not identifiable:** the mean random-partner refit reaches the ceiling within δ. The task cannot tell wirings apart for this neuron.
- **Search failure:** the free search stays more than δ below the ceiling.
- **Anatomical recovery:** the free search reaches the ceiling within δ, and the overlap with the true partners (precision at k, below) exceeds the 95th percentile of its chance distribution.
- **Functional substitution:** the free search reaches the ceiling within δ, but the overlap is within chance. A different wiring does the job.

The distribution of these four outcomes, per panel cell and per graph condition, is the **central descriptive result** of 03a.

## Graph conditions

- **N2:** the real wiring. 3 intact brains, and 3 NIP brains per target, all with different seeds.
- **SH:** 3 independently generated degree-preserving shuffles. 1 intact brain and 1 NIP brain per target per graph.
- **RD:** 3 independently generated random graphs with the same neuron and edge counts. Same numbers as SH.

Each condition therefore has 3 intact brains and 3 NIP brains per target. Every target is scored against the true partners in its own graph. Targets from the same control graph stay grouped in the uncertainty analysis.

## The panel

Each graph gets its own panel of 24 targets, chosen by the same rule, so that conditions are compared at matched criticality. Choosing targets only for being critical in N2 would favour N2.

**Eligible neurons:** not among the roughly 40 mapped sensor and motor neurons; not pharyngeal, since this task does not use pumping; and connected by directed paths both to and from the interface in that graph. Chemical self-connections are left exactly as in the original, never searched, and excluded from scoring.

**Paired or unpaired:** from the dataset's or WormAtlas's left/right annotation, never from name patterns. For each bilateral pair, one member is chosen with a fixed seed, so the target's mirror stays in the brain.

**Criticality:** the mean drop in score when the neuron is deleted from that graph's intact brains, measured on held-out seeds.

**Cells, 6 targets each:**

| | high criticality | low criticality |
|---|---|---|
| **paired** | the 6 paired neurons with the largest drops above δ | 6 drawn at random, with a fixed seed, from paired neurons whose drop is within δ |
| **unpaired** | the 6 unpaired neurons with the largest drops above δ | 6 drawn at random, with a fixed seed, from unpaired neurons whose drop is within δ |

If a high cell has fewer than 6 neurons with a drop above δ, take all that qualify and record the shortfall. The criterion is never relaxed.

The low-criticality cells are **negative controls**: their neurons should not be recoverable.

## Search algorithm

**What the reinserted neuron is given:** its true numbers of incoming, outgoing and gap partners. A connection type with zero true partners stays at zero and is excluded from that target's scoring.

**Initial state:** partners uniformly at random among all other neurons; weights, time constant and bias from the pinned initialisation distributions.

**Mutations:** each offspring gets one of the following, with probabilities fixed in the config before any pilot and never tuned on N2:

- move one connection (incoming, outgoing or gap, chosen in proportion to their counts) to a random partner it is not already connected to, keeping the weight; a gap move updates both sides, since gap junctions are symmetric;
- a Gaussian perturbation of the weights;
- a Gaussian perturbation of the time constant and bias.

**Replica exchange (parallel tempering):**

- M = 4 replicas at temperatures T₁ < T₂ < T₃ < T₄, geometrically spaced.
- Each replica holds one current state. Each generation it produces λ = 8 offspring. The offspring and the current state are all scored on the same world seeds for that generation (common random numbers).
- The best offspring o replaces the current state c if its score s_o ≥ s_c; otherwise it replaces it with probability exp((s_o − s_c) / T).
- Every 5 generations, alternating between even and odd neighbour pairs, replicas m and m+1 swap states with probability min(1, exp((1/T_m − 1/T_{m+1}) × (s_{m+1} − s_m))), using scores on that generation's seeds.
- 100 generations per search.
- The search's result is the coldest replica's final state, scored on held-out seeds.
- The temperature ladder is tuned on RD pilot runs only, which are then discarded, aiming for a 20 to 40% swap acceptance rate between neighbours.
- Refit searches use the same algorithm, with partner moves disabled.

**Searches per brain:** 5 free searches and 4 refits (1 original-partner, 3 random-partner) per target per brain.

## Scoring

**Candidate ranking:** for each target and connection type, give each candidate partner a continuous score equal to the mean, over the 5 free searches, of the absolute weight or conductance on its connection to X in the final state (zero if not connected). Ties get the average rank.

**Metrics, per target and per connection type:**

- **ROC AUC** (area under the ROC curve), with chance at 0.5. This is the statistic used in the decision rules below.
- **Precision at k**, where k is the true number of partners; its chance distribution is hypergeometric.
- **Area under the precision-recall curve**, compared with its chance level, the fraction of candidates that are true partners.
- **Functional recovery:** the brain's held-out score with the reinserted X, as a fraction of the intact score.

A target's summary is the equal-weight mean over its defined connection types. Per-type results are also reported.

**Structural baselines**, computed only from the graph with X deleted:

- **Mirror:** for paired targets, rank each candidate by the weight of the mirror-image connection of X's bilateral partner. Where that would require a connection to or from X itself, which was deleted, use the class-model score.
- **Class model:** the connection probability between X's neuron class and each candidate's class, estimated with X removed. Class annotation comes from the dataset or WormAtlas; if none is available, stop and ask.
- **Degree:** rank candidates by their number of connections.
- **Chance.**
- **The composite baseline** is fixed by rule: mirror for paired targets, class model for unpaired targets. It is never selected by how well it scores on a target.

## Hypotheses and decision rules

Intervals are 95% hierarchical bootstrap intervals with B = 20,000 resamples, resampling graph instances within each condition, then targets, then brains, then searches. A P-value of zero is reported as P < 1/B. For each hypothesis the outcome is **supported** if the interval lies entirely on the predicted side, **contradicted** if it lies entirely on the other side, and **null** otherwise. Unless stated otherwise, the confirmatory analyses use the high-criticality cells.

- **NC, validity check.** The no-task control (below) and the low-criticality cells must be at chance: their AUC intervals must include 0.5. If the no-task control's interval excludes 0.5, the mutation operator is biased; stop and diagnose before interpreting anything else.
- **SC1, self-consistency exists.** N2, NIP arm: mean AUC is above 0.5.
- **SC2, it belongs to the real wiring.** NIP arm: N2's AUC minus SH's AUC is above 0; separately, N2's minus RD's is above 0.
- **SC3, it adds to structure.** For unpaired high-criticality N2 targets: NIP AUC minus composite-baseline AUC is above 0. For paired high-criticality N2 targets: an equal-weight combination of the task ranking and the mirror ranking beats the mirror ranking alone.
- **SC4, imprinting.** N2: MIP AUC minus NIP AUC is above 0.
- **SC5, compensation.** Across all 24 N2 targets: the Spearman correlation between NIP AUC and compensation deficit is above 0.

**Power, stated honestly:** the high-criticality cells hold at most 12 targets per graph, and SC3 for unpaired targets rests on at most 6. 03a is a panel study. Null results here are weak evidence and should be read as such.

## Controls and tests (must pass before real runs)

- **Deletion test:** a brain with X deleted produces the same dynamics, within numerical tolerance, as a separately built network in which X never existed (301 neurons, re-indexed). Silencing is not tested as equivalent, because it is not.
- **Direction test:** an asymmetric test neuron with known incoming and outgoing partners must be recovered with the two sets unswapped.
- **Gap symmetry test:** after any gap move, the gap matrix is still symmetric.
- **Degree test:** the reinserted neuron's numbers of partners never change during a search.
- **Common random numbers test:** re-scoring the same state on the same seeds gives the same score.
- **Planted-optimum test:** on a small synthetic problem with a known best wiring, the search finds it. Synthetic data only, never anything derived from the connectome.
- **No-task control:** rebinding with a reward that is identically zero, for the 12 N2 high-criticality targets in one intact brain. Expected AUC 0.5.

## Budget

Estimated at experiment 01's measured speed (about 11 genome evaluations per second on the RTX 5080, measured one run at a time), the full panel is roughly 280 GPU-hours: about 70% free searches, 20% refits and 10% whole-brain evolutions. Running many searches at once on the GPU should cut this substantially.

**Rule:** the timing pilot first measures genome evaluations per second with searches batched together, then projects the total. If the projection exceeds 168 hours (one week):

1. reduce to 16 targets per graph, 4 per cell;
2. if still over, reduce free searches from 5 to 3 per brain;
3. if still over, stop and report before proceeding.

Never drop the NIP arm, the MIP arm, the refit controls, the no-task control or graph replication. Record the final numbers in DECISIONS.md before the real runs.

## Exploratory (labelled as such)

- **Crosslink dial:** for a few targets, let the rest of the brain keep mutating at low and medium rates while X rebinds.
- **Selectivity:** transplant the wiring of X's mirror partner, a same-class neuron and a random neuron into X's slot, and compare how well each fits.
- **Funnel analysis:** along search trajectories, score against Q, the fraction of true partners currently connected.
- **Transfer:** rebind on stereo foraging a brain evolved on single-nose foraging.
- **Reversed wiring:** N2 with chemical-synapse direction reversed, as a fourth condition.
- **Free degree:** the reinserted neuron chooses how many partners to have, with a wiring cost in the score.

## Honesty notes

- The task is small, so recovery can only be expected for the neurons it uses. Every result is conditional on this task.
- A positive result shows self-consistency under this model and task. It does not show that the real worm's connectome is optimised for this task.
- The reinserted neuron is told its true number of partners, which a real reconstruction may not know.
- There is no plasticity in this brain model, so compensation happens only through evolution, not within a lifetime.
- Every behaviour claim needs the same metric on untrained or random baselines, as established after the flanking correction in experiment 01.

## Changes since draft v1 (from Astra 6's review)

- Arms relabelled by the information they assume; both primary; MIP is no longer called an upper bound.
- Added original-partner and random-partner refits and the four-way outcome classification as the central analysis.
- Corrected the deletion test: silencing and deletion differ when gap junctions are present.
- Removed the dependencies on experiment 02's results; the task and model are fixed now.
- Fixed the scoring details: self-connections, connection types with zero partners, continuous rankings with tie handling, per-graph ground truth, difference instead of ratio for imprinting, precision-recall alongside ROC AUC, graph-grouped bootstrap, and baselines fixed by rule rather than selected on the target.
- Wrote replica exchange out as an explicit algorithm.
- Replaced the full map with a 24-neuron panel in a 2 × 2 design (paired or unpaired × high or low criticality), with panels chosen separately in each graph.

## What comes after: 03b and beyond

- **03b, the full map:** all eligible neurons, if 03a shows the method can separate the four outcomes.
- **More tasks:** if the connectome is shaped by many behaviours, the fraction of recoverable neurons should grow as tasks are added.
- **Leave-k-out:** remove 5%, 10% and 25% of neurons at once.
- **Missing synapses:** remove individual connections rather than whole neurons.
- **Full self-consistent field:** scramble the whole connectome, then cycle through the neurons, re-optimising each in the field of the others with damping, and see whether it converges back to the real wiring.
