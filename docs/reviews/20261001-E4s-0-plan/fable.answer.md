**Verdict: revise.** The design is sound and needs no new round, but a few pins are missing or contradict the code, and the tests miss the likeliest bugs. I ran nothing.

## What I checked and found correct

- **Carrier arithmetic.** `forward_gain` is 4.0 and `turn_gain` is 2.0 (`config.py:97-98`), and `e1/task.py` does not override them. So forward = 2·tanh(b_f) with only the plus neurons biased, and turn = 2·tanh(b_t) with ±b_t. The biases (at most 0.549) are inside `b_max = 2`, and τ = 0.5 equals `tau_min`.
- **Sign.** `turn_plus` is the dorsal set, heading increases toward the left normal, and `P_FRONT_L` is on the left. L1's 20 edges give about 4·w_o·w_n·d with the right sign.
- **Residual timing.** `last_signals` is set before `_read_motors` in `tick`, so the same-tick L and R are available.
- **World ids.** The ranges are disjoint from each other and from every range in `scripts/` and `wormwars/` (950–980 M, 992.7–999 M). Seeds 1 150 000 and 1 151 000 are free.
- **Selection.** `evolve_batch` picks generation 0's best by `np.argmax(fitness)`, so ties go to the lowest index, as the plan says.
- **Budget.** The episode arithmetic reproduces: 312 832 + about 262 k + about 115 k + about 18 k + about 49 k ≈ 0.76 M.
- **Robustness.** `p_mutate` is 1.0, so the fallback rule is not vacuous.

## Must-fix

1. **§1, the wrapper's tests do not test "before the clamp" or the sign.** `_read_motors` returns an already clamped turn. The obvious implementation (call the original, add k·(L − R), clamp again) passes the k = 0 check and "k ≠ 0 changes the turn", but is wrong whenever the raw turn exceeds 1 in magnitude (it can reach ±2).
   - Add a test with a raw turn of 1.5 and k·(L − R) = −0.3, expecting 1.0, not 0.7.
   - Add a test that k > 0 with L > R raises the turn. A swapped L/R would otherwise produce 47 "harmed" champions and read as a finding.
   - Add a test that the patch is removed after the sweep (try/finally, as `e2d.py` does for `rollout`), so no stale k leaks into item 3.

2. **§1, the k = 0 check needs its composition pinned.** State that the unwrapped reference runs in the same batch composition and chunking as the wrapped runs, and that every k uses that composition. Otherwise an "exact" mismatch could be CUDA composition drift (rule 6), not a wrapper bug.

3. **Common settings, the bootstrap seed contradicts the code.** The plan says seed 20 261 001 and "imported from `scripts/e2d.py` unchanged". `world_ci` reads `REGISTERED["analysis"]["seed"]`, which is 0 (`e2d.py:82`). Either say seed 0, or say the script overrides it and test that.

4. **§1, the classes drop the proposal's conditions and "unclear" is unreachable.** The plan's list omits "no smaller k is harmed". Under the proposal's definitions the five named classes are exhaustive, so "unclear" can never occur. A champion that improves at k = 4–16 and is harmed at 64–256 is labelled "rises late".
   - Restate the full definitions.
   - Either define "unclear" or drop it.
   - Record "harmed at a larger k" as a flag.
   - Add a unit test of the classifier on synthetic intervals, including the k = 256 edge. None is listed, and this is the most bug-prone logic in the script.

5. **§3.2, the simulated statistic is not tested against E4s-1's selection and has less power.**
   - Add a toy-size test: the simulated G0 best equals `evolve_batch`'s generation-0 `best_sha256` when run through the `initial` hook on the same worlds. This is the only guarantee that the statistic is the one E4s-1 uses.
   - E4s-1 classifies G0 on 1 024 hold-out worlds; the plan uses 256. More genomes will land in "unclear", and the "fewer than 12 are D" rule counts those as not D. Either use 1 024 (about 37 k extra episodes) or state the bias and report D, unclear and not-D counts separately.

6. **Budget, the smoke cannot project the formal run.** Throughput here depends on composition (strains per `bmm`, rows per strain). Toy shapes (4 candidates, 2 champions) say little about 648 strains × 128 worlds, 47 × 512, or 1 padded strain × 1 024. Time one chunk of each formal composition on smoke ids, as E2d's `project` stage does. Say whether the projection and the k = 0 reference run (about 24 k episodes, not in the budget) count against the cap.

7. **§4, no test that robustness mutates only the module.** Add a test that the mutants' worm block and carrier biases are bit-identical to the parent's and that the module parameters differ. Also pin whether seeds 1 151 000 + j are per mutant or per scale, and whether the scales share draws. `e2d.children` resets the generator so every scale takes the same draws; say whether that is reused.

## Suggestions

- **Shrink order.** I would shrink tuning (128 → 64) first: it is a screen with a 512-world re-score behind it. The sweep's 512 worlds drive the only interval-based classes in item 1, so shrink them last. The full shrink only reaches about 0.43 M episodes, so a projection above roughly 3 h stops the stage regardless.
- **L4's base.** L1, L2 and L3 are compared on re-scored means from three different world sets. Score the three finalists on one common set, or note that the comparison is unpaired.
- **Response time.** At w_s = 0.95 and τ = 2 the effective time constant is roughly 40 ticks or more, so "settled = mean of the last 10 of 40 ticks" is not settled. Lengthen the window for L2 and L3, or record a "not settled" flag.
- **No step qualifies.** Say explicitly that items 3.2–3.5 are skipped, so the 12-of-16 reading is "not drawn". Say why item 4 uses L1 and not the best-scoring unqualified candidate.
- **Grid.** A comparator bias of −0.5 can only lower L1's gain (sech² ≈ 0.79). It is harmless, but it is half of L1's grid.
- **Backgrounds.** D on 64 worlds will be mostly "unclear"; label it so.
- **Stage frame.** Importing `e2d.py` runs `configure()`, which points its copy of E2's frame at E2d's folders. Test that E4s-0's records and cap clock use its own folder and compute file.

I did not read `e2d.py` past line 904, and I did not open E1's gate record.