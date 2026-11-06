**Verdict: fix then publish.** The readings are applied as the plan fixed them, every number I re-derived from the committed records matches, and nothing needs a rerun. Seven sentences are wrong or overclaim, and one calibration figure needs a reconciling sentence. All fixes are to text, plus one guard in the exploratory phases script.

## 1. Readings against the plan

The read stage implements §6 as written: one-sided 90% paired percentile bounds over the 512 worlds, the best baseline recomputed inside each resample for both the advantage and the ratio, "too easy" read only where "solvable" holds, criterion (c) run wherever (a) and (b) hold, "uncertain" wherever neither qualification nor demonstrated failure applies, and "falls off" as the first speed whose reading is anything other than "qualifies". H1-ghost is excluded from every rule. The attack-disabled check and the per-tick ledger are enforced by stops, so the run's completion is the evidence for them.

Two sentences read more than any rule licenses. "What separates E2d from E4s-1 is the use of the stereo difference" and the README's "the dividing line is stereo use" are causal headlines built on a reading the plan lists as "without a threshold". See §3 below for why the records do not support the causal form.

## 2. Numbers and sentences that do not match the records

All four tables in RESULTS §3, §4, §5 and §6 trace to summary.json and phases.json, cell by cell. The compute table, the bench projection, the calibration figures, the equivalence counts and the time span all check. These do not:

- **"On the random walk and the wall follower at 0.25 or 0.5"** in "What came out" item 3, repeated in the README and loosened in "What this means for E5-1". One E2d champion, E2 extension run 4, qualifies at random-walk 0.5 and falls off at 0.75. Your own falls-off table says "0.75: 1". Fix the three sentences.
- **"The tuned constant turn matters there"** in §3. E1's frozen S-const is k 8192, speed 1.0, turn 0.0. The tuned winners at route speeds 0.4 to 0.7 are k 64, speed 0.6 to 0.8, turn 0.0 or minus 0.1. What the tuning changed is the gain and the speed, not the turn. This is a more interesting finding than the one written: a low-gain, slower scent follower beats both the pursuit reference and the saturating steerer on mid-speed prey.
- **"Contact was not measured directly"** in §6. The event table logs contact ticks, and phases.json already holds a median per hunter. For E4s-1 run 0 the kill phase lengthens from 33 to 59 ticks between H1-bite and route speed 1.0 while contact ticks within it fall from 15 to 12. That supports the losing-contact reading and should be in the table.
- **"A capture takes at least 10 ticks of bites"** in §2 and §3 sits next to a side-approach kill time of 7 ticks and a rear one of 8. Both are true, and the reader needs the bridge: the largest single-tick damage of 0.1375 was measured over the held fixture and the three approaches, so a kill needs at least 10 damaging ticks, but damage lands before the contact criterion is met, since the bite point is 0.9 ahead of the head and contact needs the head within 1.5 of a body point. Kill time from first contact is therefore not a count of biting ticks. Say so, or report kill time from first damage as well.
- **"04a run 4 fails the route at 0.1 and qualifies at 0.2, then fails again."** At 0.3 it reads "uncertain"; the demonstrated failures start at 0.4.
- **"While L1's rise to 4.5"** in §4. L1 peaks at 4.51 at speed 0.8 and is 4.12 at 1.0.
- **"Did no damage"** for the attack-disabled check is enforced by the stop in the evaluate stage, but the damage total is not in any committed record; reading.json holds only the capture count. Add the damage figure to the reading, or say the stop is the evidence. Rule 5.

Smaller: "from s = 0.4 to 0.8 the tuned S-const beats" the pursuit reference also holds at H1-bite, H2-0.1 and wall-0.25 by smaller margins, and these are point comparisons without intervals; and the best-baseline share's minimum is 2.8%, which "3%" rounds up.

## 3. The interpretations

**The stereo reading overclaims in three ways.**

- Under the `mean` probe the E4s-1 family still averages about 1.6 captures at H1-bite and about 1.6 at route speed 0.5, against E2d intact at 1.02 and 0.69. Stereo use accounts for part of the gap between the families, not all of it. E4s-1 also has the better non-stereo residue, and it was already far ahead at H1-ghost, which is Task N.
- The family spread is wide and has an exception. E4s-1 run 12 loses 0.10 under `mean` at H1-bite, with bounds 0.02 to 0.17, yet qualifies everywhere; run 13 loses 2.97 of its 3.05. Name run 12, since "costs every E4s-1 champion" is technically true and materially misleading for it.
- "E2d still follows the scent (the `mirrored` probe costs 46 of 47)" draws the wrong inference from the right number. A hunter that ignores the left-right difference should be indifferent to a swap of the noses, as it is to their mean. A cost under `mirrored` with none under `mean` points to lateralised use of the two noses, one nose or unequal weights, rather than to "following the scent by other means". Scent dependence in E2d is shown by the `constant` probe, which every qualifying genome passed. Cite that instead, and note that 11 of 47 E2d genomes have a small but bounded-above-zero `mean` cost, at most 0.10, so "nothing" should read "nothing material".

**The phases reading** needs three caveats. The tuned positive control is a different controller at each speed, so its medians compare controllers as well as prey; the cleaner evidence that faster route prey are easier is the two fixed-parameter references, the pursuit rising from 4.48 to 8.11 and E1's frozen S-const from 4.52 to 7.72, which the text should cite. The tuned control's approach median is not monotone, 29 ticks at speed 0.5 as at H1-bite, so "both shorten with the prey's speed" is loose. And the script takes approach as first contact minus activation for every captured life without guarding against a life captured with no logged contact, which the calibration code does guard; add the guard and report the count, since damage before contact makes such lives possible.

**For E5-1**, one reading that matters is missing: E4s-1's weakness on fast prey is specifically a longer kill phase, while L1 on its constant-turn carrier kills fast prey faster than slow ones. That bears on the choice of start and on whether the carrier's gait, not only the comparator, is what to inherit.

## 4. The run itself

The cap margin, the random-walk prey's wall contact and the pursuit reference falling below the tuned control are all disclosed. The reference worktree's time is counted through the accounting's child runner, the read stage ended at 09:04 UTC as stated, and the local CI record for the formal commit reads success. I did not verify that the per-setting JSON summaries under runs/e5-0/evaluation are tracked in f2199d9, which "committed beside them" asserts.

One thing to add: the tuned S-const at H1-ghost scores 8.65 against E1's frozen 8.67 on the same worlds, so per-setting tuning on 64 worlds is slightly noisy. It does not change any reading, and it belongs in Limits.

## 5. Fixes before publishing

1. Correct the mover fall-off sentence in RESULTS item 3, the README, and the E5-1 proposal.
2. Replace "the tuned constant turn matters" with the gain and speed.
3. Reword item 4 and the README's "dividing line" to the associational form, with the residual under `mean`, run 12, and the `constant` probe as the scent-dependence evidence.
4. Add the contact-tick column to §6, cite the fixed-parameter references, soften "both shorten", and guard the phases script.
5. Reconcile the 7-tick kill time with the 10-tick minimum.
6. Fix "then fails again" and "L1's rise to 4.5".
7. Record the attack-disabled damage total, or state that the stop enforces it.