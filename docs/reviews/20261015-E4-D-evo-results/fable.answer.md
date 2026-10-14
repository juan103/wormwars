**Verdict: fix then publish.** The registered reading is correct, in the registered wording, with the registered limits. I recomputed the headline numbers and every cell of the controls table by hand from the raw records, and they all match. The fixes below are traceability and wording; none touches the reading.

**What I recomputed from `formal/` (not from summary.json)**

- L: gains sum to 1688/128 over 32 runs, mean 0.41211; sum of squares 652 counts², sd 4.586/128, t(31) 1.6955, LB 0.40137, UB 0.42285. F: 200/4, mean 0.39063; t(3) 2.3534, LB 0.35791. Sign-flip 1/2³² and 1/2⁴. Min and max gains, every `minus_eg`, all match `report-l/f.json`.
- Controls, L, all 32 runs tallied: intact neither 185/4096 = 0.045; removed neither 3326/4096 = 0.812, range 0 to 128, 24 champions at 100 or more; fixed neither 188/4096 = 0.046; cut neither 46/4096 = 0.011, cut equals E-G in every run; reversal swaps counts exactly in every run. F: intact 114/128 mean, removed neither 0.934, cut 0.359 (0.258 to 0.5), E-G 0.016. All match RESULTS.
- Check: control 112/128, E-G 64/64/0, oracle 117/128, reversed 14/112, removed 64/64/0, 76.03 s/gen, 2.534 projected, 6.23 allowance, 787 s. Compute 9891 s = 2.75 h, 1650 s = 0.46 h, 6.09 + 3.21 = 9.30. Checkpoints, slot means and positives, contrasts, lineage median 88 (80 to 94), validation mean 0.939 all match.

**Findings**

1. **Medium, rule 5.** Three numbers in RESULTS are not in summary.json, which `RESULTS.md:4` says holds every number: "24 of 32 champions at 100 or more" (`RESULTS.md:51`), "validation above test in 25 of 32 runs" (`RESULTS.md:92`), "at least 0.78 in every run's every generation" (`RESULTS.md:95`). `scripts/e4d_evo_summary.py:94-109` and `:136-142` emit only spreads. Worse, the 25 is a rounding artefact: `validation_shares` are stored to 6 decimals, so run 0 (117/128 = 0.9140625, stored 0.914062) reads as below test and run 8 (123/128, stored 0.960938) as above. On the 1/128 grid the count is 24 above, 2 equal (runs 0 and 8), 6 below. Fix: compute validation from counts, add the three counts to summary.json, add per-run counts for every condition to `runs[]` (§7.3 says "reported per champion, with the counts"; today only intact is per run), and write "24 above, 2 equal, 6 below".

2. **Low, interpretation.** `RESULTS.md:45-46` presents the reversal as evidence that "the champions use A's cue". Under paired assignments, reversed(maze, a) is the same world as intact(maze, 1−a): B reads the sum, A reads the other candidate. The exact swap is an identity of the evaluation path, which is how `check` uses it (§5), not an independent control. The evidence for cue use is the intact share above 0.5 with B blind to the assignment. Say so in one clause; keep the row.

3. **Low, scope.** `RESULTS.md:9-11`, `README.md:12`, root `README.md:56`: "in all 32 runs" sits inside the confirmatory statement. §1 and §7.1 register a claim about the mean. The per-run statement is true (lowest gain 39/128) but descriptive; mark it "beside the registered mean". Also `RESULTS.md:23` says "five states"; §7.1's table has seven rows.

4. **Low, wiring.** `RESULTS.md:79-82` "evolution fed A's steering signal into B's sensory input" reads weights as function; no ablation of the comparator-to-nose slots alone was run. Add "function not tested by ablation". Separately, summary.json's per-slot `class` is by origin, so A_CL→B_NL is labelled `into_B.comparator` (`e4d_evo_summary.py:56-59`), which a reader will take as "into B's comparators". Rename to `into_B.from_comparator`.

5. **Low, hygiene of the summary.** summary.json copies check's per-maze arrays (about 7 000 of its 9 600 lines); RESULTS cites none of them. Keep the counts, drop the arrays, or leave it and say so.

6. **D279: no material weakening.** The exemption needs the key suffix, shape [n, 2] and values in {0, 1} (`tests/test_publication_hygiene.py:123-129`), with a sabotage test at `:464-476`. A binary pair list cannot name a neuron above 1, so no graph can pass through it.

7. **Deviations: none undisclosed found.** Stage commits chain correctly (check a2e9ae7, train-l 32d279b, evaluate/report-l 0864e88, train-f 4752508, evaluate/report-f 3579985 after the tests-only D279 change, which D278 placed outside provenance). The GPU use between L and F is in D280. F's compute record counts only F's stages. S's non-trigger follows §3.

8. **Labels are right.** The contrasts are marked "chosen after seeing L's data" in RESULTS, summary.json and the script docstring; the removed-cue effect is marked unpredicted and unmeasured; §7.1's limits paragraph is reproduced verbatim in sense. The removed-cue sentence "most of them need it to approach a candidate at all" is supported by 24 of 32 at 100 or more neither.