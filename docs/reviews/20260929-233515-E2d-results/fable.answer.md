## Verdict: **fix**

The registered readings and every number I recomputed are right. The corrections needed are text only: three interpretive overclaims (one contradicts the plan), some plan-promised reporting that is missing, and narrow margins that are not flagged. No rerun or re-analysis is needed.

## Must-fix

1. **`RESULTS.md:197`, "knowing that module is near its ceiling on this task".** This sits under "as the plan frames it", but the plan says the opposite (`PLAN.md:148` "it does not establish a ceiling"; `PLAN.md:70` "not a ceiling"). The records also disagree: the budget reading is "budget-limited", and non-stereo champions score 2.64, 2.84 and 2.92. Delete the clause.

2. **`RESULTS.md:183-185`, "every method lands in the same non-stereo basin, whose level is about 2.2".**
   - "Basin" claims a shared region or attractor. Nothing measured similarity in genome space or behaviour, and line 181 says how the champions navigate is not measured.
   - Random sampling's champions score 1.31-1.90 (median 1.64), which the plan treats as below the plateau and does not read.
   - "Came close" depends on GA run 2. On this hold-out the GA averages 1.98 against random's 1.62; without run 2 it is 2.16, a gap of 0.54.
   - Supportable wording: random sampling's champions are also non-stereo (0 of 8 use the difference); all methods differ within one class, and none approaches 8.7.

3. **`RESULTS.md:179-180`, "there is at least one stereo strategy at the plateau's level; evolution did not find even that".** The k = 4 reference is a scripted controller. It shows the probe is sensitive at that score, not that an N2 genome can express the strategy through this interface. At equal score, selection also has no reason to prefer it, so its absence says little about reachability.

4. **`RESULTS.md:126-131` and `146-151`, sign-flip tests are missing.** The plan requires the p-value beside each interval and any disagreement stated (`PLAN.md:242-243`). The records have them:
   - C1 0.125, C2 0.008, C4 0.023, C3 0.78.
   - Two disagreements are unstated: C1's 8-run interval excludes 0 with p = 0.125, and the interaction's does with p = 0.148.

5. **`RESULTS.md:149-151`, the interaction.** Add the 7-run figure: −0.140 (−0.314, +0.007). Say that run 2 supplies −1.589 of the −2.570 total (62%). Each single change rescued run 2, so the difference of differences is mechanically negative there.

6. **`RESULTS.md:147-148`, "inconclusive" for C4 − C1 and C4 − C2′.** The plan fixes no reading for these two contrasts; the label is the runner applying the arm rule. Say so. Also report that C4 − C1 excludes 0 both ways (7 runs: +0.076, +0.029 to +0.120). It is small but the cleanest mutation contrast.

7. **`RESULTS.md:136-137`, "supplies most of each arm's mean".** Run 2's shares are C1 81%, C4 64% and C2 50% (1.725 of 3.456). Give the shares.

8. **Narrow margins flagged for C0 only.**
   - C4 (`RESULTS.md:130`): mean 0.3044 against 0.3. Beside E2's registered champion it is 0.279, which would read "inconclusive".
   - 04a unshaped (`RESULTS.md:68`): 3 of 4 is exactly three-quarters. One more "unclear" makes the set "mixed" and removes the plateau reading.

9. **`RESULTS.md:115-119`, C0's per-champion rates are missing** (`PLAN.md:185-186` promises them).
   - Middle bin at × 1: 0.87, 0.86, **0.75** (run 2), 0.83, 0.84, 0.85, 0.82, 0.84.
   - Run 2's parent supplies 601 of 2 343 pairs; without it the pooled rate is about 0.84 (my computation).
   - At × 0.5 and × 0.25 the pooled rate is 0.794 and 0.772, under the line at the scale C2 and C4 use. Line 189 should say so.

## Suggestions

- **Run 2's role is understated.** All three GA arms rescued it, including C1 (02's mutation) and C2 (8 worlds). The rescue cannot be attributed to either change, and there is no control with fresh mutation draws at unchanged settings.
- **"Clearest operator lead" is acceptable with caveats:**
  - two of the eight gains (+0.009, +0.051) are near the hold-out's error;
  - the arm-reference correlation is −0.17, so pairing removed little;
  - C2's mean (2.41) equals 04a's unshaped runs at 02's unchanged mutation (2.39, n = 4), by my computation from `part-b.json`;
  - C0's children come from end-of-run champions, and even × 0.25 leaves 40% under half.
- **C3's run 2:**
  - its final hash equals E2's ES generation-25 hash (`9534c0d1…`), so the mean never moved;
  - its champion is the start genome, so its "no material benefit" class is vacuous. Footnote the "31".
- **Disclosures:**
  - C3's attempt has `git_commit_at_end` 937e8b9 ≠ 6ec1761, because two documentation commits landed mid-run;
  - the ledger's 14 037 s is the sum of rounded rows, and the record says 14 036.1.
- **Leaving the plateau:** add per-arm counts at or above 2.5 (C2 2, C3 1, C1 and C4 0).
- **C2′ run 5** is "unclear" (+0.19, +0.49) at a matched checkpoint, while C2's final run 5 shows no benefit. Partial left-right dependence appears and is not retained.
- **Top-8 overlap:** state that chance is 0.125; run 2's parent sits at 0.09-0.26.
- **Status text:** the README's "four rounds" were four versions and three reviews. `ROADMAP.md:64-71,196` and the root `README.md:39` still say "running".

## Checked and found correct

- **Part B:** all 47 classes from the intervals; set counts and medians; the contrast ranges; the references; the named genomes; the checks.
- **Budget:** per-run gains, mean, median, 7 of 8, and p = 4/256. The validation curve rises from 2.02 to 2.31.
- **Part C:** per-run differences, means, medians and improved counts with and without run 2; each reading under the rule; the 31 + 1 classes; no arm with 4 champions.
- **C0:** the mutation table at all three scales, the pooled bins, the ES pair rates, the reference error.
- **Run 2 and C3:** 0.69 from the same genome in both references; E2's ES leaving zero at generation 52; C3's 622 flat generations.
- **Replay and pairing:** the replay passed; every arm's pairing check passed.
- **Ledger and order:** every row, the 8 919 552 total, the projection's 3.86 h, and the push log showing the plan and runner pushed before 17:37:08 UTC.
- **E2's 22-30%** (`E2 RESULTS.md:208`).

**Not checked:** I could not run code. The bootstrap intervals, and the sign-flip p-values other than the budget's, are taken from the records. I could not diff the runner after a337d48 and relied on the commit messages.

## For E3 (advice)

1. **Settle expressibility first.** E1's gain curve rises at every step (0.88 to 8.78), so the scripted family has a selectable path. Build or imitate a low-gain stereo N2 genome, confirm it with Part B's probes, then evolve from it. This seeded start is the most informative of the four options.
2. **Test the non-stereo module on E3's real cue** (trails, branches) before building on it.
3. **Make the probes a standing measure,** along training and not only on champions.
4. **Do not adopt halved mutation or 32 worlds as defaults on this evidence.** If tested again, add a fresh-seed control at unchanged settings and consider sparser mutation.
5. **Pre-declare the handling of all-zero starts;** they decided four readings here.