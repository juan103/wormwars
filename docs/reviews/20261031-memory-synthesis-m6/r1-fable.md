**Verdict: fix then publish.** Every M6 number in draft 5 traces to its results file or `summary.json`, and the draft avoids the "must not say" list except for one sentence in the lessons. Five wording fixes, none needing a rerun. I could not run `git diff` (no shell in this session), so I checked draft 5's M6 text against the four results files, D374-D383 and the summary directly, not against draft 4.

**1. Faithfulness.** All checked, all match: 4.80 and 117.23 hours (0.96 + 0.20 + 3.64 on 112.43); 1 of 102 against 5 of 408 and the interval −0.015 (−0.044 to +0.013); τ_stay 39 to 46.5; "six times" (0.161 against 0.026); 44 sources and 30 full texts; 55 of 169 held, 54 returned, 112 faded, 111 at the rising-start state, 163 agreements; −24.5% (−26.4 to −22.5), −7.5%, −12.7%, −35.1%; −2.8 points (−6.1 to +0.4); 6.0%; 1.77, 0.93, 2.73; 39 neurons; median ratio 0.23; 113.59 at the D381 annotation; the 200-tick episode (the plan's and the compute record's figure). The fixed wordings are quoted as the readers write them. Step 1's census switches and step 2's evolved champions are kept apart, as Astra asked.

**2. What it must not say.** Avoided in "In short", section 7, "What holds" and the annotations: the history effect's benefit is left open, "tuned optimum" is refused, T0 equivalence is "not established", the interior arm does not place the cost, warm-up stands beside the slow-side loss, the a-association is not mentioned at all, step 1 says nothing about behaviour, and the literature check is "not biological validation". The two "exceeded" sentences sit beside the floor caveat (`docs/memory/SYNTHESIS.md:355`, and the table row at line 130). M6 is labelled exploratory at line 308. One slip:

- **Fix 1, `SYNTHESIS.md:476`:** "the T0 champions were what showed it was not specific to the single-nose task" is the "nothing singles out T1" claim both reviewers cut from the results (D383). The matched interval allows T1 to drop up to 6 points more. Say instead that the T0 champions were what stopped a drop in T1 from being read as specific to the single-nose task, since no matched difference was detected.

**3. Credit.** Right against D376-D383, with two adjustments:

- **Fix 2, `SYNTHESIS.md:510`:** the owner line credits "the order of the last steps (the quick check, the champions' test, then stop)". D379 says the owner named the champions' test first; Claude proposed swapping, and the owner said "go ahead". Claude's line at 544 already claims the order. Credit the owner with the steps and the stop, and the order to Claude, accepted by the owner.
- Optional, line 536: the exact rescaling's construction (substeps times 1/k) is Fable's, as the plan says. Astra's design review independently showed that scaling tau alone is not a time rescaling of the semi-implicit update, which D382 lists under Astra; a few words for that would be fair.

**4. The stop paragraph** is mostly fair, with two problems:

- **Fix 3, `SYNTHESIS.md:500-501`:** "resetting each brain towards its steady state was costed at about 100 times step 2" presents a design-note guess as a costing. In the design review Astra said that figure "needs evidence or qualification" and that the reset does not preserve latency, since it bypasses the temporal responses and can jump motor output. The plan never revisited it. So the paragraph cites, as the selective intervention that was merely too dear, one that the review said is not selective. Drop the parenthetical, or state it as the design note's rough and unverified figure and add Astra's objection.
- **Fix 4, `SYNTHESIS.md:502`:** "the worm's best-described turn memory" ranks the literature. M6-3 says only "the most directly relevant study checked" places it in oscillation phase. Use that wording.
- Optional: "Open questions from the table above" names two, but the table also leaves open the split of N2's lead between switches and fading (M2) and M4e's degree and exact-block steps. "Among them" would be enough.

**5. One stale definition.**

- **Fix 5, `SYNTHESIS.md:83`:** "A genome is one random set of weights ... (generation 0, never evolved)" is now false for section 7, which classifies and rescales evolved champions. Add the exception.

Optional and small: line 420's "every result is for the 10-tick ramp" no longer covers step 2's foraging scores or step 1's 2000-tick removal; line 428's list of steps chosen after earlier results could add M6's branch; line 314 could say the 03mc bank was the secondary.