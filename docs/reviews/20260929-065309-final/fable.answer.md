**Verdict: fix.** Every number in the new corrections recomputes and the test change tests the right claim, but there are small text errors to correct first. None needs another review round.

I could not run anything or read git history, so I did not see the old test's text or whether CI passes at `35c9f70`.

## 1. 03m corrections

| Correction | Check against the committed JSON | Right? |
|---|---|---|
| AIY 2.65 times | 0.060645 / 0.022893 = 2.649 | Yes |
| Lowest P4 0.733 and 0.729 | `weights.json` minima 0.73304 and 0.72946 | Yes |
| Median drop 0.046 / 0.047 | 0.93086 − 0.88514 = 0.0457; − 0.88357 = 0.0473 | Yes |
| Pooled null median P4 0.8174 | 320 of 640 null graphs in `supplement.json` are at or above 0.8174; the middle values are 0.81722 and 0.81759, so the median is 0.81740 | Yes |
| 60% and 58% | 0.0677 / 0.1135 = 0.597; 0.0662 / 0.1135 = 0.583 | Yes |
| Permutation responses 0.013-0.052; three chemical-only seeds 0.045-0.048 | Range 0.01271-0.05198 over both designs; seeds 0.0448, 0.0457, 0.0480 | Yes |
| Single deletions from 0.089 | RIAR 0.08851 | Yes |
| 23 of 49 not settled; 3.6 × 10⁻⁵ | 49 − 26; 3.588e-05 | Yes |
| Relaxation counts per tick | Checked for all 80 graphs at every recorded tick | Yes |

**Relaxation detail.** No graph is above N2 at ticks 5-50; only SH-10007 at ticks 60-140; SH-10007 and SH-mirror-40014 at ticks 150-300. SH-mirror-40014 crosses between tick 140 (0.1138 against N2's 0.1169) and tick 150 (0.1132 against 0.1103). The nearest miss is SH-recip-50014 at tick 160 (0.1041 against 0.1054).

**To fix in `RESULTS.md`:**
- **"These counts are exact at every recorded tick (Fable)"** misattributes. My confirmation answer said the counts beyond tick 50 were upper bounds. The sentence is true, and I have now verified it, so cite this round or say who recomputed.
- **0.8174 is not a stored field.** Say it is computed from the per-graph `P4_turn` values.

**Root `README.md` and `ROADMAP.md`.** Nothing stale remains in the 03m lines. Two qualifiers from the corrected summary were dropped:
- **"no single or paired deletion removes"** (`README.md:36`, `ROADMAP.md:54`) should say "tested", as `RESULTS.md` and the experiment README do. The eight read-out neurons were excluded and only 95 bilateral pairs were tried.
- **"fades more slowly than the shuffles'"** (`README.md:36`, `README.md:133`, `ROADMAP.md:51`) holds for 78 to 80 of the 80 graphs tested. SH-10007 keeps 15.5% at 300 ticks against N2's 9.4%. Write "than nearly all shuffles tested".

Two lesser points:
- **The README row's only P4 statement is the one that survived.** It omits that most weight permutations lower P4 below the threshold and that gap junctions narrow the lead. It is not false, but I would add them.
- **`ROADMAP.md:244-250` does not mention 03m.** `README.md:173` links to that section, which still describes the mechanism follow-up as future.

## 2. The test change

**It is the right claim.** D082, D091 and `docs/REPRODUCIBILITY.md` claim exactness only within one composition, and the old test compared two. The new one holds the shape and the world's index fixed, so exact equality is safe. It has the same design as `test_a_strain_is_unaffected_by_its_batch_mates` in `tests/test_e1_task.py`.

**What is lost:**
- **The only dynamics check that varied worlds per strain.** The remaining cross-composition tests vary strains per chunk. A bug that depends on the number of worlds but not on the batch-mates' content would no longer be caught in the foraging world.
- **A cheap replacement:** compare alone against a batch of 4 over about 5 ticks at 1e-4, labelled approximate. The CI failure implies growth of roughly 1.2 times per tick, so that leaves a wide margin; this is my estimate, not a measurement.

**Still exposed.** Three CPU tests assert exact equality across compositions: `tests/test_t0_pairing.py:151` (chunk 64 against 3), `tests/test_t0_pairing.py:164` (4 against 2) and `tests/test_e1_task.py:218` (15 against 5). If D112's diagnosis is right, they can fail on some runner in the same way.

**To fix in the test:**
- **The docstring's "one wey per swarm" is wrong.** `weys_per_swarm` is 20 (`wormwars/config.py:83`), so the composition is 1 strain, 4 worlds, 20 weys: one swarm of 20 weys per world.
- **"because a CPU batch of one can differ"** states as fact what D112 calls likely. The cause was not reproduced, and T1's CPU finding was about one strain against several, not 20 rows against 80.
- **`import numpy as np` inside the function** is redundant; the module imports it at line 10.

**To record:**
- **No `DECISIONS.md` entry covers the replacement** (the latest is D114). D112 asked that it not be done silently. The entry should say what is no longer tested.
- **`docs/REPRODUCIBILITY.md` has no dated note for the CI observation.** Its CPU statements are development-machine measurements, and the CI failure is the first evidence from another CPU.
- **Rule 9.** I cannot tell whether a sabotage check was done. The assert on line 259 shows the batch-mates differ, not that coupling would be caught.

**"fix"**: correct the test docstring (20 weys, "likely"), add "tested" and "nearly all" to the README and ROADMAP lines, reword the "(Fable)" exactness attribution, and add the decision entry and the `REPRODUCIBILITY.md` note for the test change.