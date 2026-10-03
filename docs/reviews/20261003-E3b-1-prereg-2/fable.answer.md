**Verdict: bind**, with the last fixes below applied as written. No further round.

**1. My draft 1 points.** All seven resolved, and I checked them against the files rather than §15:
- §8 carries pin 1: every number matches `power.json` (false positives, MDEs, the opposite-effects rejection, pooled-t and sign-flip at 5.0 to 5.5%, the 0.34 SD scope caveat).
- §9 and §10 use one admission formula, reserve on training only, matching design pin 11 (`docs/E3/E3b-1-DESIGN.md:268`).
- §6 pins validation access per arm, N under none.
- S-gen, S-peer and the descriptors have their denominators and conditions.
- G_F − 1 is carried everywhere, including cut 3.
- 200 learning-curve points, 0.24 h. The budget sums to 17.52 plus the probes, so "about 17.6" and 21.4 hold.
- Two-sided 95% intervals.

The code the rules lean on exists: `latch.structure` returns bistable or monostable with the two states, `organism.no_latch`, `maze_runs.replay_donors`, `train_ids`. E3b-0's thresholds (K_D ≥ 30 up to 0.35; relative minimum 10.5) match `report.json`. The 32 read points for validation are right.

**2. Computable and free of post-hoc choices.** Yes, with four small gaps:
- **SE = 0 is handled only for G.** S-gen's paired t and the stratified tests on e give NaN with zero variance. Say the SE = 0 rule applies to every registered test.
- **§10's "their projection"** for `champions` and `evaluate` is ambiguous. Say that `champions` is admitted on hours spent + both stages' projections ≤ 24, so no champion is validated that cannot then be evaluated.
- **§5's crash rule for `evaluate`.** Blocks are saved as they complete; a rerun "unchanged" could restart or resume. Say which. Also cap total attempts of a training stage at three, so a crash followed by a non-finite score has a defined path.
- **The record must name the non-finite runs.** `evolve_batch` currently raises with only the generation (`wormwars/e04a/evolve.py:148`). §5's second rerun depends on names the record does not yet write. Add that to §12 test 4, and add a sabotage test that `g-e` fails on a hash mismatch, since the GPU script only records mismatches.

**3. Must change before binding** (text only):
- **Stale cross-references:** the status lines say §14 maps the changes, §12 lists departures and §13 holds amendments; the actual sections are §15, §13 and §14. §3's "(§11)" for none-equals-deposit-off points at §12 item 2. Registered text cannot be fixed later.
- **§8's shifted null:** `power.json` gives 0.29 at CV 0.282 and 0.31 unequal, not 0.28. The 0.28 is the CV 0.267 scenario, which the table omits. That figure came from my draft 1 review, so the error is mine.
- **§13:** the stage-level failure rule is an elaboration of design pin 10 forced by the batch abort. List it as a departure.

**Not verified:** I had no shell this session, so I could not recompute the nine hashes at 6d251fd. Both reviewers confirmed them at 95800aa, and the two later commits are documentation by their messages.