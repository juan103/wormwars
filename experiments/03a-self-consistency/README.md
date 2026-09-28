# 03a: The self-consistency hypothesis (draft, not run)

> **This is a draft design. It has not been run, and it is deliberately not scheduled.** Nothing in
> this folder is a result. The owner decided on 2026-09-27 (D062) that 03a's task and budget are
> revisited after 03r, using measured throughput (about 2 times experiment 02's), not the
> hoped-for 5 times. Until then, no code specific to 03a, no feasibility pilot and no
> pre-registration tag exist.

**Status:** draft v3.2 (2026-09-25), not run, not scheduled (D062) · **Run:** none · **Commit:**
none · **Compute:** none spent. The draft as written is estimated at about 31 million genome
evaluations for its searches, about 785 GPU-hours at 02's batch-32 throughput, plus about 37
GPU-hours of whole-brain evolution

**The hypothesis (the owner's):** if a connectome is shaped to perform tasks, the wiring of one
missing neuron can be predicted, to some extent, from the rest of the brain plus a task. Delete a
neuron, place it back with random wiring, let only that neuron optimise for the task, and see
whether its original partners come back. The idea borrows from self-consistent field methods
(each orbital optimal in the field of the others) and from molecularly imprinted polymers (always
compared against a non-imprinted polymer made without the template). If it holds, task
optimisation becomes one more tool for filling gaps in incomplete connectome reconstructions.
Before paying for a map of the whole brain, 03a tests on a fixed panel of neurons whether the
method can tell apart three outcomes: the original wiring is recovered (anatomical recovery), a
different wiring does the job equally well (functional substitution), or the search fails.
([`DRAFT.md`](DRAFT.md), "The hypothesis".)

## Where it stands

- **Not run.** Draft v3.2 is the latest design. Its own "Next steps" (review, code, a disclosed
  feasibility pilot on shuffles only, then the tag `exp03a-prereg`) are on hold under D062.
- **The budget does not fit.** At 02's batch-32 throughput (about 11 genome evaluations per
  second) the searches alone come to about 785 GPU-hours. Staying under the draft's one-week cap
  (168 hours) needs about 4.9 times 02's speed if both workloads speed up, or about 6 times if only
  the searches do. Measured throughput is about 2 times 02's (D050, from experiment 03's
  benchmark, [`../03-generation0/timing.json`](../03-generation0/timing.json), which found
  evaluation compute-bound, so wider batching did not help). At exactly 2 times, the panel does not fit even after both of the draft's reduction steps (about
  204 GPU-hours; Astra, in [03's design](../03-generation0/DESIGN.md)). It needs a cheaper
  evaluation or a smaller panel.
- **03r replicated** (D080). Roadmap v3 says that if it does, 03a switches to a memory task.
  That redesign has not been written; the roadmap lists what it keeps and changes (see
  "Extend it").
- **What already exists that 03a needs:** a true deletion operator, built and tested in 02b
  (`wormwars/deletion.py`, `tests/test_deletion.py`), and experiment 03's validated null
  ensembles.

## Design (draft v3.2, summarised)

Everything below is the draft's text, not a registered design.

- **Task:** single-nose foraging (T1) exactly as in experiment 02
  (`wormwars/exp02/grid.py:task_config(…, "T1")`). Brain model as in the pinned code, with no
  plasticity; motor gains calibrated once per graph on the intact brain and frozen.
- **Two arms, both primary:**
  - **NIP, reconstruction from anatomy alone:** evolve a brain from scratch with target neuron X
    deleted, then insert X with random wiring and evolve only X.
  - **MIP, reconstruction with functional information from an intact simulated trained
    network:** evolve a brain with X present, delete X, reinsert it with random wiring and evolve
    only X. MIP is not assumed to be an upper bound.
  - **Imprinting** is the MIP minus NIP difference in recovery.
- **Deletion, not silencing:** deletion removes every term involving X; the pinned code's
  `Brain.silence` clamps X, which still pulls gap-junction neighbours, so it is not used (D044).
- **Searches per target:** 3 original-partner refits (the reference), 5 random-partner refits, 2
  structural-baseline refits and 5 free searches. Initial weights never use per-edge anatomical
  magnitudes, which would leak the true partners.
- **Search algorithm:** replica exchange with 4 replicas, 8 offspring each, 100 generations, with
  the temperature ladder tuned on pilot shuffles only.
- **Candidate partners** never include the mapped sensor and motor neurons, so a direct
  sensor-to-motor shortcut cannot make substitution trivial. X's true connections to interface
  neurons are kept as fixed partners.
- **Graph conditions:** N2 (3 intact brains, 3 NIP brains per target), 6 routing- and
  mirror-matched shuffles from experiment 03's ensemble ("SH-matched", the main control), and 3
  ordinary shuffles (SH). RD is dropped.
- **The panel:** 24 targets per graph, chosen by the same rule in every graph: paired or unpaired
  (from a curated left-right annotation) × high or low criticality, 6 per cell. The low cells are
  a comparison stratum, not a negative control.
- **Per-target attributes,** reported separately and cross-tabulated: reference reliability,
  headroom, original-partner advantage, functional success and overlap (ROC AUC against the
  target's own label-permutation null). Every comparison is three-state against a performance
  margin p of 5% of the intact score, with "undetermined" never counted either way.
- **Confirmatory family (Holm, five members), high-criticality cells:**
  - **SC1:** self-consistency exists (N2, NIP arm, AUC above 0.5);
  - **SC2:** it belongs to the real wiring (N2 minus SH-matched);
  - **SC3:** it adds to structure (against the composite structural baseline for unpaired
    targets; on the candidates the mirror ranking leaves undecided for paired targets);
  - **SC4:** imprinting (MIP minus NIP).
  - SC5 (compensation) is exploratory. Verdicts are supported, negligible, reversed, null or
    withheld.
- **Feasibility pilot** on pilot shuffles SH101 and SH102 only, never N2, with four pass criteria:
  resolution, NIP headroom and identifiability, MIP recovery, and timing. If it fails, the panel
  is not run and the pilot is reported.
- **Power, as the draft states it:** the high-criticality cells hold at most 12 targets per graph,
  so null results would be weak evidence.

**Notes from experiment 02** ([`NOTES_FROM_02.md`](NOTES_FROM_02.md), written for the review of
draft v2 and folded into v3):
- T1 is solvable, but 02's evolved T1 champions solved it without detected history use, so many
  targets may prove not identifiable.
- Mirror symmetry is a generic explanation for SC2 and SC3, and shuffles give the food neurons
  direct routes to the motor read-out. Mirror-symmetric and routing-matched shuffle ensembles
  would separate these; experiment 03 built them.
- Three graphs per control condition give coarse intervals (only 10 distinct resamples); report a
  t-interval beside them, or add graphs.
- 02's reviews forced verdict mechanics that 03a adopts: withheld verdicts, "contradicted" split by
  cause, explicit "not assessed" states, and an end-to-end smoke test on synthetic data.
- In 02, all eight 80-generation continuations were still improving, so 150 generations is
  reasonable.

## Caveats and open problems

- **The throughput gap** above is why 03a is not scheduled (D062).
- **The 02b risk** (roadmap v3): the connections that make neurons critical, to sensor and motor
  neurons, are ones v3.2 keeps fixed. The redesign must either search the targets' interface
  connections or pick targets whose criticality does not come only from interface adjacency.
- **The draft predates experiment 03.** It fixed its SH-matched rule "before 03 exists"; roadmap
  v3 asks the redesign to use 03's validated ensembles, with several graphs each, instead of
  unconstrained SH.
- **Its own honesty notes:** every result is conditional on the task; a positive result shows
  self-consistency under this model and task, not that the real connectome is optimised for it;
  the reinserted neuron is told its true number of partners; there is no plasticity.
- **Review history:** where Astra 6 and Fable 5.1 disagreed on v3.1, the choices are recorded in
  D047. D047 also corrects D046, which had overstated Fable's endorsement of v3.1.

## Files

| File | What it is |
|---|---|
| [`DRAFT.md`](DRAFT.md) | Draft v3.2 of the design, with the changes from each review round and the "not scheduled" header |
| [`NOTES_FROM_02.md`](NOTES_FROM_02.md) | What experiment 02 found that bears on 03a, written for the review of draft v2 |

There is no pre-registration, code specific to 03a, configuration or run data.

## Reproduce it

**Not run.** There is nothing to reproduce.

## Extend it

Roadmap v3's redesign list ([`ROADMAP.md`](../../ROADMAP.md#03a-redesign-after-03r-before-any-confirmatory-run)):
- **Keep:** the question; the feasibility pilot on shuffled graphs only, never N2; the
  three-outcome classification.
- **Change:**
  - **Task:** if P4 replicates (it did, D080), use a task that requires memory. In any case, the
    pilot must show that solutions to the task use interneurons.
  - **The 02b risk:** search interface connections, or choose targets accordingly.
  - **Nulls:** experiment 03's validated ensembles, with several graphs each.
  - **Budget:** fit the design to measured throughput; shrink the panel (24, then 16, then 12) or
    the searches before extending the cap, and say which was cut.
  - **Wording:** animal-to-animal variability is not a ceiling on recovery from one fixed graph.
- **After 03a:** a full map runs only if 03a separates the three outcomes. Later ideas from the
  draft: more tasks, leave-k-out, missing synapses, and a full self-consistent-field loop.

## Record

- Design: [`DRAFT.md`](DRAFT.md); notes: [`NOTES_FROM_02.md`](NOTES_FROM_02.md).
- Decisions ([`DECISIONS.md`](../../DECISIONS.md)): D044 (silencing is not deletion), D045 (draft
  v3), D046 (Fable's review of v3), D047 (Astra's review of v3.1; disagreements), D062 (not
  scheduled). Related: D043 (the generation-0 study as experiment 03), D050 (the "about 2 times,
  not 5" throughput).
- Reviews (`docs/reviews/`): `20260925-163118-roadmap` (v2), `20260925-172550-v3` (v3),
  `20260925-174815-v31` (v3.1).
- Roadmap: [`ROADMAP.md`](../../ROADMAP.md), "Where the project stands" and "Track B".
