Everything I needed is in hand: all numbers are checked against summary.json and the raw records, and I've confirmed the review-round timing, the record paths and the calibrator values. Writing up the verdict now.

**Verdict: publish, after small fixes.** Every number in RESULTS.md traces to summary.json or to the named record and is correctly rounded. I found no numeric error. The fixes below are wording and consistency. Three of them should be made before the push, because each repeats a claim the write-up elsewhere retracts.

**What checks out**

- All stage hours, commits, champion scores, p, deficits, degrees, the probe table, the tuning figures, the full table, the projection, the three variants, the lesion and the re-evaluation match summary.json. The V1 interval's lower bound rounds correctly from the raw value in search-check.json.
- Numbers not in summary.json are in full.json under `paired_diff_sd_mean`, `pair_rates` and `turnover_per_10_from_0`, or in setup.json (the graph's sha256) and evolve-intact.json (1 000 generations). The 10 largest lesion drops are indeed all outgoing (the top 16 are).
- D318's three fixes are right. "Regained" is gone from the free-search claims. The review timing matches PILOT-DEV's status and D310, D311. 62.5% is kept.
- All six review directories in Record exist. The summary test's sabotage case can fail.
- "Exploratory" is applied correctly. The check's rule was fixed in advance but was never a registration, and the page says so.

**Findings**

1. **ROADMAP.md:9-10, medium.** "Before any GPU run: design v7.1 was agreed by both reviewers, and the code was reviewed in three rounds." Rounds 2 and 3 were under review while `setup` through `probe` ran (PILOT-DEV.md:12-14, D310, D311). This is the exact overclaim D318 says it fixed in the draft. It survives in the ROADMAP status and contradicts RESULTS.md:55-56. Reword to "round 1 before any GPU run; rounds 2 and 3 while the first stages ran".

2. **RESULTS.md:255, medium.** "the registered recovery statistic". Nothing in 03a was registered, as line 3 says. Write "the design's recovery statistic (DESIGN §6)".

3. **RESULTS.md:154, medium.** "That is a property of the arm, and N2 would share it." This is a prediction about N2, and the next section says nothing about N2 is shown. The logical point holds only if an N2 NIP brain also reaches the task's ceiling without X, which is not shown. Make it conditional: "the same would hold on any graph whose NIP brain reaches the ceiling without X".

4. **RESULTS.md:94-109, medium.** The probe's reading. The KTS calibrators did not "move little": T = 10 gained 0.19 at L = 5 and 0.16 at L = 10, and T = 20 lost 0.19 at L = 10 (summary.json `probe.scripted`). Those are about 2p. The table shows only T = 10, which moves in one direction, so "both directions" cannot be seen from it. Two consequences for the reading. First, the rebuild demonstrably changes a stored average when L ≤ T, with T = 10 moving toward T = 5's higher score, which is the calibration the design asked for. Second, a known slow memory shifts the score by at most 0.19, while the evolved brains lose up to 1.95 at short L, so the calibrators give no scale on which those losses read as sensory memory. Add the T = 5 and T = 20 rows, give the ±0.19, and say the second point under "What a loss does and does not mean". "The evolved brains depend on neural state older than the window" stays true as worded.

5. **RESULTS.md:240-241, low-medium.** "The original-partner advantage of 0.12 under pilot-dev's setting shows the true partners do help a refit." Under the two single-chain variants the advantage was equivalent (0.03 and −0.00, line 186), as the page says at line 193. Add "and under V1, but not under the single-chain variants".

6. **RESULTS.md:259-269 and 285, low.** Corrections lists D313's and D316's corrections but not D318's correction to D317, which is the one that bears on this page. Record cites "D302-D317"; it should be D302-D318. Also D313's correction of the offspring-minus-current figures (the −0.14 and 0.32 came from a refit) is missing from the list.

7. **RESULTS.md:273-275, low.** "Reproduce it" should say that a clone already holds the committed records, so every stage refuses unless run with `--rerun --reason`, and the rerun renames the committed record to `<stage>.attemptN.json` (scripts/e03a.py:1435-1445). As written, a reader will run the first command and be refused.

8. **summary.json:60, low.** The note says "D317 gives 0.026". D317 gives 5.31 hours with the preflight included and no preflight figure. The 0.026 is report.json's 0.019 (through `report`) plus D316's "about 0.007". Say that, since the preflight directory is local and this is the only trace.

9. **RESULTS.md:147-148, low.** "Each free search's Q stayed near its chance level." D313 already corrected "inside the chance range" for the same series. The ranges are in summary.json (`free_q_range`: 0.04-0.16 and 0-0.18 against 0.070; 0-0.10 against 0.011, where one hit of ten is 0.10). Quote the ranges and keep D313's wording: no sustained enrichment trajectory, and the final tests did not reject.

10. **RESULTS.md:23-24, low.** The one-paragraph "Why:" presents D317's post hoc reading as a finding. The page is labelled exploratory, so this is defensible, but "A reading:" or "Why, as far as two states show:" would match D317's own label.

11. **RESULTS.md:28, low.** "this was one target-brain on one shuffled graph". Pilot-dev's `full` ran four target-brains; the check ran one. "One informative target-brain" or "one target-brain with headroom" is exact.

12. **README.md:36, low.** The one-line result leads with "No anatomical signal", which against the Question column reads as an answer to the hypothesis. The qualifier follows, but leading with "The search could not test the hypothesis on one shuffled graph" would prevent the misreading.

13. **README.md:400, low.** "03a's redesign, which does not fit our compute" is stale: the redesign was made, ran, and stopped. Annotate with the date rather than rewrite.

14. **experiments/03a-self-consistency/README.md:191, 194-203, low.** "After 03a: a full map runs only if 03a separates the three outcomes" is not annotated with the outcome, and the Record section still ends at D094 and the September reviews. Both are kept-as-was text, which rule 4 allows, but a dated line pointing to D302-D318 would help a reader who starts there. Line 33's "runs on `a5760c4` to `4d6e887`, 5.84 GPU-hours" mixes the pilot-dev commits with the 03a total that includes the earlier 0.53.

15. **ROADMAP.md:585, trivial.** "The full map runs only if 03a separates the three outcomes" could carry a one-line dated annotation that it did not.

On the question of whether any sentence reads as evidence about N2 or the hypothesis: only item 3 does in RESULTS.md, and item 12 invites it in the project README. The dated README and ROADMAP updates otherwise say the same as RESULTS.md, and the earlier statements are kept with "Earlier:" or dated annotations rather than overwritten.