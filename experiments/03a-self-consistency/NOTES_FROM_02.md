# What experiment 02 found that bears on 03a

These are notes for the next review of `DRAFT.md` (v2). The draft itself is unchanged. It is
queued in the pipeline, not scheduled, and nothing here is a decision. Every point comes from
experiment 02's reviewed results ([`../02-screening/RESULTS.md`](../02-screening/RESULTS.md)) and
`DECISIONS.md` D034-D043.

## The draft's conditional inputs, resolved

- **Task.** The draft says to use experiment 02's single-nose task (T1) unless 02 "found this
  task unsolvable". The scripted gate passed (memory share 0.40 [0.38, 0.41], D034), so T1
  stands. But solvable is not solved-as-intended: 02's evolved T1 champions beat the memoryless
  scripted controller without any detected sensitivity to 1-cell history jitter. They circle, and
  they lose 0.30-0.40 when collision sensing is removed. So the neurons T1 "uses" may sit mostly
  on food-level and collision pathways. That makes the draft's "not identifiable" outcome likely
  for many targets, which its four-way classification already allows for.
- **Gap junctions.** Experiment 02 kept D030's truncation, so the pinned code's behaviour applies.
- **Parameters to copy:** `wormwars/exp02/grid.py:task_config(…, "T1")`. That is odour sigma 1,
  200 ticks, food x2, halved food sensing scale, pheromone off, 32 integrator substeps, and motor
  gains calibrated per graph in-world on 2048 genomes (D035).

## Points the next review may want to weigh

1. **Mirror symmetry is a generic explanation for SC2 and SC3.** Degree-preserving shuffles keep
   13-16% of chemical edges under the left-right relabelling; N2 keeps 64%. A recovery advantage
   for N2 over SH (SC2) could come from symmetry alone. The mirror baseline (SC3) is available
   only where symmetry exists. A mirror-symmetric shuffle condition would separate the two.
   Experiment 02's reviewers recommended building exactly that ensemble for a generation-0 study
   (D043), and 03a could reuse it.
2. **Shuffles give the food neurons direct routes to the motor read-out** (direct weight 1.5-43
   per food pair, against N2's 0-1). This changes which neurons are critical in SH brains, and so
   which targets its panel draws. A routing-matched shuffle ensemble would address it.
3. **Three graphs per control condition.** Experiment 02 found that a percentile bootstrap over 8
   units already undercovers. Resampling 3 graph instances gives only 10 distinct resamples, so
   the SC2 intervals will be coarse, whatever their nominal level. Report a t-interval beside
   them, or add graphs.
4. **Verdict mechanics that 02's reviews forced:**
   - withhold a verdict when registered units are missing or malformed, with the completeness
     rule written in the pre-registration;
   - split "contradicted" by cause;
   - make every tripwire's "not assessed" state explicit;
   - add an end-to-end smoke test of the analysis on synthetic data with the real schema.
   Each was a real defect in 02 before review (D040, D041).
5. **Evolution.** In 02, all eight 80-generation continuations were still improving (+0.05 to
   +0.27 from generation 39 to 79), so 150 generations is reasonable. There was no selection
   gradient for stereo: within a cell, stereo use did not correlate with score. So a capability
   the task could reward is not necessarily present in the evolved brain whose neuron is removed.
6. **Budget.** Experiment 02 evaluated whole populations as one batched strain set, and ran
   scripted tuning about 85 times faster batched than serially. The draft's rule, to time the
   batched pilot before projecting, looks right. The 280-hour estimate probably overstates the cost.

## Ordering in the pipeline

The generation-0 structural study that both reviewers recommended as experiment 03 (D043) would
build the mirror-symmetric and routing-matched shuffle ensembles. Points 1 and 2 above need those
ensembles. Running that study first would give 03a better controls at almost no extra cost.
