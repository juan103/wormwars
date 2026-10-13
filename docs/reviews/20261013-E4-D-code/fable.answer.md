**Verdict: fix first.** The trial, the channel mapping and §3's exactness hold in the code (checked: `g_A` is exactly 0 or 1 at `brain.py:480`; the slots at 0 give exact zero products; `Genome.dense` builds W from `w` with no sign or clamp, so the nose-origin's negative edges survive; the maze shuttle has zero drain so no wey dies; `tick_count` increments after `_post_move`, so `first_tick` is 0-based and an entry on the last tick records `H_t − 1`). What needs fixing is around the trial: one cross-composition comparison, one registered check that is not run, one misleading reading, and two tests that cannot fail.

## Findings

1. **Important. The reversal mapping check compares across batch compositions.** `scripts/e4d.py:210-218`: the normal control is played in a 3-strain batch, the reversed one in a 1-strain (padded) batch. Rule 6 claims exactness only within one composition; the criterion is an exact count equality, so a last-bit difference that flips one near-boundary trial fails the verdict spuriously, and would be read as "the mapping failed". Fix: one genome per batch in `trials()` (every condition then has composition (1, 2n, 1); the X0-vs-cut comparison becomes a same-composition CPU repeat, which the repo does claim), or per-world `a_source`/`b_source` so every condition sits in one batch. State which in the record.

2. **Important. The registered per-trial latch check is not run.** Design §1: "q is negative at every substep until the trial ends, read directly." `trials()` (`scripts/e4d.py:87-111`) sets no `substep_hook`; only the unit test checks it, for 120 ticks on 3 mazes. Fix: a hook that ORs `(v[..., q] >= 0).any()` per world over the run, recorded per stage and included in the verdict.

3. **Important. A failed exactness or mapping check is read as a slots result.** `scripts/e4d.py:224-227`: `passed` is false if any check fails, and the reading then says "the slots did not carry the signal" or "the task is infeasible". A false `x0_invariant` or `reversal_ok` is a bug or a composition artefact, not either of those. Fix: branch on the checks first ("a check failed: the result is void"), then on the share with the oracle beside it.

4. **Important. Two tests pass with a broken implementation (rule 9).** `tests/test_e4d_trial.py:137-144` asserts a tautology (`first_tick < 0 or < max_ticks`) and never produces an entry on the last tick; a latch that never fires passes. Fix: find `first_tick` on a maze, rerun with horizon `first_tick + 1` and assert the entry is recorded, and with horizon `first_tick` assert −1. `tests/test_e4d_trial.py:61-69` passes vacuously if every maze gives `None`; assert at least one qualifies.

5. **Minor. `paired_identical` is weaker than §3's test.** `scripts/e4d.py:114-119` compares first candidate, first tick and final position only. Add the final non-A brain state and heading (both already in hand) so the evaluation's invariance checks match what the unit test checks, and so a divergence that happens to re-converge in position is caught.

6. **Minor. The sabotage that matters most is absent.** `tests/test_e4d_trial.py:179-192` has no nonzero-slot sabotage; add `control_genome(eg, cx, "nose", 0.05)` → not invariant. Also the invariance trace (`:168-176`) runs 150 ticks on 2 mazes without asserting an entry occurred, so the post-entry path (goal flip and reset, deposit) may be untraced; run to the horizon and assert an entry in at least one traced world.

7. **Minor. An undeclared rule.** `wormwars/e4/trial.py:71` rejects `min(d₀, d₁) ≤ 2`; §2 has no such clause. It changes skip outcomes, so declare it (an amendment, with the reason: it keeps the start out of both 3 × 3 blocks).

8. **Minor. Tests the design lists are missing.** §1's enumeration test (the assignment reaches only E3_A_NL/NR: diff `_build_current` under both assignments). The decoy, fixed0, none and oracle mappings are untested (`tests/test_e4d_trial.py:86-95`). Crowding and pheromones off are not asserted (`:80-83`).

9. **Minor. The oracle is not played on the calibration block** (§4: "on every block"), `scripts/e4d.py:182-198`. Cheap to add.

10. **Minor, bookkeeping.** Raw start readings are reduced to medians (`:160-166`); record the per-trial array (rule 5). The partial write (`:167`) creates `scout.json`, so a crash mid-scout blocks the rerun through `guard` (`:130-137`); write partials under another name. No stage checks that the previous stage's commit matches its own (provenance is recorded, so auditable, but a changed start rule between stages would not be refused). `np.quantile`'s interpolation is unstated. Calibration/evaluation manifest disjointness is not asserted.

## Rulings on the deviations

All four accepted. The subclass satisfies rule 7 by construction; say so with the commit's file list, since §6 promised a tolerance-zero comparison. The smoke's forced σ is labelled. Raising inside `TrialWorld` is fine with the runner filtering first by the same function. Reporting the starts is right.

## On §3's test

Comparing positions and non-A states at every tick boundary within one batch is sufficient: inputs and the update are deterministic given those, so motor commands and injected currents follow. The three sabotages are real and each would be detected; "ungated" is a leak through all of A's motor edges rather than one direct A → motor edge, which is acceptable. Simultaneous entries are unreachable (disjoint blocks, one head), so `latch_first`'s `argmax` tie never arises; say so rather than claim it is handled.