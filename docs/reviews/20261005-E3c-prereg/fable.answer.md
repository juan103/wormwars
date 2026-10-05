I have everything I need now: the draft, the design, the pilot and reviews, the stats code and tests, the power script and all 9 483 lines of `power.json`, the runner, and the block and seed records from E3b-0/1/2. Writing the review.

# E3c pre-registration draft 1: review

**Verdict: revise.** The statistics code is correct and the draft is faithful to the design and to D205/D206, but three things must change before it binds: the code it claims to bind does not exist yet, §8's false-positive summary does not match `power.json`, and §7.3's coverage rule has an ambiguity and an undefined interval. The required list is at the end, separate from suggestions.

## Answers to the seven questions

**1. Faithfulness.** The draft registers what design v2.1 and D205/D206 require: the task unchanged, the noses-removed reading for every champion including P-joint and P-sel, the coverage hypothesis, the narrowed wording, the W2-turn reference, genomes saved and published by name, factor 1.0, the T-F cohort reused with hash checks and reselection. Three things are missing or wrong:

- **§2 line 66 says E3c's code is bound at this commit.** At 54f6f5f `scripts/e3c.py` has two stages, `pilot` and `replay` (`STAGES`, line 68). None of §5's seven formal stages exists, and most of §12's tests are not written. The registration cannot bind code that is not there. It must state the sequence: the text binds now; the stages are written test-first, reviewed by both, and the formal commit is recorded in an amendment and the start marker, with the engine paths unchanged since binding. This is the same gap D205's note caught for the replay.
- **§13 is incomplete.** Not listed: the per-champion Spearman correlations and the resting turn and K_D descriptives (§7.4; Fable's change 4), the change to the cut list (design §8 cut 1 was "the evaluation's secondary conditions", §10 now cuts trails-off only and keeps the noses-removed reading), and Astra's paired loss and "no material loss" bound (§7.3).
- **Readings asked for and not present:** Fable's analytic coverage ceiling beside the W2-turn reference is neither registered nor declined. PILOT.md says it is unchecked, so declining it with a sentence is fine.

**2. The statistics.** `e3c_stats.py` is right. I checked `contrasts` by hand: ordering by p, level 1 − α/(m − i), rejection iff p ≤ α/(m − i), later contrasts keep the failed step's level; for Welch with one df the (1 − α) interval excludes 0 exactly when p ≤ α, so the "rejected iff the interval excludes 0" claim holds. The `label` function matches the table in §7.1 lines 201-207, including the dual-margin direction ("beyond" against the larger, "within" and "no relevant difference" against the smaller). The dual margin itself is stated unambiguously at lines 189-197.

Two wording defects:
- **§7.1 lines 209-210:** "Q1 is 'not read' unless at least one S arm's mean exceeds W2 + 1. If so, it enters Holm with p = 1." The "if so" points the wrong way. It should read "if not read, it enters Holm with p = 1, so Q2 is tested at 0.025". The code does the right thing.
- **§7.1 line 184:** "1 − 0.05 / (2 − rank)" needs "rank 0 for the smaller p", or the formula gives the wrong level.

On Q2's false-positive rate: disclosure is enough, and the rule should not change. The inflation is 0.06 against 0.05 with a Monte Carlo standard error of about 0.005, it appears only in scenarios the pilot gave no evidence for, and the scenario's own null (a matched mean over a two-point mixture) is half the story. A permutation primary would be exact but departs from the agreed design for a small gain. But the disclosure must be correct, and it is not (next point). A non-tuning addition that helps: register "a failed run is a champion below W2 alone + 1 on the test block", report the count per arm, and append it to the labels when nonzero.

**3. The power analysis.** The simulation is faithful: both contrasts through `readings`, one S-mod sample in both, the floor guard, the dual margin at seed 5.0, Holm ordering. The scenarios are adequate for the S arms. P-joint's distribution is sensible, but the "empirical" shape resamples 8 values from 8 atoms, so nearly every sample has ties and the t-statistic is anti-conservative; that is an artifact of the shape, not a property of P-joint. §8 should say so.

§8's summary has errors against `power.json`:

| §8 claim | `power.json` |
|---|---|
| Q2 any "better" at 0, S-mod failing 1/4: 0.054-0.062 | 0.0415 to 0.066 across δ₁ and shape (n = 8); 0.026 at n = 6 |
| "otherwise it is at most 0.03" | 0.058, 0.061, 0.0625 at p_fail = 0, empirical shape, δ₁ = 0.25, 0.5, 1.0; 0.037 at the full null, empirical |
| Q1 false positives "at or below 0.03 in every scenario" | 0.0335 and 0.0345 in two scenarios (p_fail 1/4, δ₂ = 1.0, sd 0.06 empirical and sd 0.2) |
| Base case Q2 "unclear 0.97; any better 0.02" | true for the normal shape only; empirical gives 0.961 and 0.037 |

The rest checks out: Q1's table, Q2's 0.65-0.67 and 0.61 and 0.69 and 0.51 and 0.45 and 0.19, "beyond" at most about 0.3, P-sel's 0.59 and 0.20, the 6-run cut. Astra's two power asks not taken, separate S-mod and S-dense SDs and endpoint uncertainty, are minor and could be named as such.

**4. The coverage hypothesis (§7.3).** The classes, the coverer criterion and its thresholds are D205's, fixed before any result, and sound. Problems:
- **"P-joint has fewer coverers than either S arm" is ambiguous** (fewer than each, or than at least one).
- **The rule conflates two claims.** If both S arms are 8/8 coverers and P-joint is too, the first claim is fully supported and the second refuted, yet the label is "mixed", the same as heterogeneity. Register the two parts separately, or state in the rule that "mixed" includes this case.
- **The run-level interval for L is undefined** (t over the arm's runs, or a bootstrap with which seed). Numbers must be traceable (rule 5). P-fixed has no runs, so say it gets the maze-paired bootstrap instead.
- **The qualifier** appended to Q1's and Q2's labels is fair as a qualifier, since the text says it never changes a label. But line 262 says "class counts" and the example shows "coverers"; pick one. Astra's caveat belongs here in one sentence: "scent-independent" means the intervention costs little, not that the intact controller ignores its noses.

**5. Blocks, ids, seeds, stages, champions, cap, cuts.** Blocks 10 000-10 655 are disjoint from everything I could find: E3b-0's 0-255, 1000-1255, 2000-2255 and smoke 9000-9999, E3b-1's 4000-4127, 4500-4627, 5000-5255, 6000-6255, E3b-2's 7000-7255 and 7300-7555, the pilot's 7600-7727, E3c's smoke 8000-8099, the audit 9900-9902. Run seeds 1 300 000+ are clear of E3b-1's 1 190 000+ and the pilot's 1 200 000+. Training ids 40-50 M are clear of 10-20 M and 30-40 M. The pinned hashes for `module.json` and `pilot.json` match the runner's. The champion rule and the W2-turn choice are unambiguous. The T-F read at 124 exists locally per E3b-1 §6. Gaps:
- **§3 line 103:** the consequence of a failed T-F hash check is not stated (refuse the stage, or Q2 "not read"). State it.
- **§2 lines 62-63:** `train-tf.json` and `maze-reference.json` are relied on but not pinned by sha256, unlike the other two.
- **§5 step 6:** P-fixed is played with the noses removed per §7.3 but is not listed there.
- **§10's checkpoint line** budgets 0.2 h for the extra checkpoints, but T-F's 6.44 h had no periodic checkpoints at all, so all 20 per run are new cost, roughly 0.6-0.9 h. The `project` stage will measure it, so this is a note, not a blocker.

**6. Wording.** Mostly careful. §1 line 19 "keep 100% of their visits" should be "99.9-100.6%". Line 20's 5.6-5.8 is on the pilot block; say so. §8 "Welch's test is fragile to such mixtures" names the wrong cause; the issue is a two-point mixture at n = 8 and, for the empirical shape, the 8-atom resampling. Nothing in the draft claims more about mechanism than the readings support.

**7. Verdict: revise.**

Required:
1. §2, §5, §12: remove "bound at this registration's commit" and state the binding sequence for the formal stages (written after binding, test-first, reviewed by both, commit recorded in an amendment and the start marker, engine paths unchanged since binding).
2. §8: correct the false-positive statements to the ranges above, give the Monte Carlo SE, say the base case is the normal shape, and name the 8-atom resampling artifact.
3. §7.1: fix the "if so" at line 210 and define rank at line 184.
4. §7.3: define L's interval (and P-fixed's), fix "fewer than either", and split the coverage hypothesis or make "mixed" explicit for the "all coverers" case.
5. §13: add the three missing post-pilot items.
6. §3 and §2: the consequence of a failed T-F hash check; pin the two unpinned files; add P-fixed to §5 step 6's noses-removed condition.

Suggested, not required: the failed-run count qualifier; a test that the second Holm level is 0.95 after a rejection and 0.975 after a non-rejection (`test_holm_levels_and_intervals_agree` checks only the first); Astra's one-sentence caveat on "scent-independent"; decline or register Fable's ceiling; "99.9-100.6%"; the checkpoint budget line; W2-turn's coverage and tour match as descriptives; a sentence naming the two Astra power asks not taken.