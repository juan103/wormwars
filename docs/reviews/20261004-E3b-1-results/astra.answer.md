The confirmatory conclusions are supported, but **RESULTS.md needs corrections before publication**. The main problems are an incorrect T-A summary, an ambiguous denominator, missing registered descriptive results, and an unsupported mechanistic claim.

I independently recomputed the statistics from the committed `eval-*.npz` arrays. All 130 organism–condition records contain 256 finite observations, and their means match `evaluate.json`. I also checked calibration arrays, probe values, champion selection, training records and compute. I did not rerun evolution or the probes.

The registered statistical results check out:

| Reading | Recomputed estimate | Raw p | Holm p | Registered bound |
|---|---:|---:|---:|---:|
| G | +0.225319 | 0.0000720505 | — | Lower: +0.165696 |
| S-gen | +0.315238 | 0.000998887 | 0.001997774 | Lower: +0.190455 |
| S-trail | +0.126902 | 0.004965084 | 0.004965084 | Lower: +0.054372 |
| S-peer | −0.060252 | 0.0000281585 | 0.0000844754 | Upper: −0.042391 |

Thus **“better,” “and at least 10%,” and all three secondary conclusions survive**. G is correctly outside the “concentrated” category: all 16 final T champions meet the criterion, with median legs ranging from 4.25 to 5.50; only eight were required.

The schedule intervals, all 16 reported d values, sensitivity p-values, four S-trail means and decomposition, and G’s absolute and comparator-scaled gains are correct. Specifically, the gain is 1.315826 visits per wey; its two multiples are 0.319291 and 0.118137. The pooled p is 0.000232914 and the exact sign-flip p is 1/65,536. These checks support the draft’s central outcome.

The required fixes are:

1. **Correct T-A’s S-trail numbers and clarify the N denominator.**

   [RESULTS.md:51](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:51) says T-A’s e averages −0.05 and is negative in six runs. The correct values are **−0.0589047, negative in seven of eight runs**. Report −0.059, or −0.06 at two decimals. T-F’s +0.312709 and eight positive runs are correct.

   At [line 133](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:133), the reported N +0.36 and T-A +0.13 subtract the seed’s **none** mean but divide by its **shared** mean. Make that formula explicit:
   \[
   (\text{champion none}-\text{seed none})/\text{seed shared}.
   \]
   The values are +0.356898 and +0.128344. If you instead intend percentages relative to the seed’s none mean, they are **+0.463464 and +0.166667**, with N’s range +0.421390 to +0.524430. Keeping the recorded numbers and correcting the explanation is sufficient.

2. **Remove “the probes suggest [the improvement] largely does not” run through the selector.**

   That conclusion at [line 58](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:58) exceeds what these probes establish. They measure local motor sensitivity under imposed states and inputs, using E3b-0’s levels and thresholds. They do not partition the maze-performance gain by mechanism.

   There is a concrete counterexample to the accompanying phrase **“respond to neither goal.”** For `tf:2:final`, the active \(K_D\) values are zero, but at level 0.2290867653 its one-nose results for **both** goal channels are:
   - no input: turn +1;
   - left-only input: +1;
   - right-only input: −1.

   The same pattern occurs in `tf:3:final` and `tf:7:final`. These champions demonstrably respond to asymmetric inputs despite having zero local \(K_D\) around the tested equal-input conditions. Their strict one-nose checks fail because the left response does not exceed an already saturated baseline. See the [saved probe record](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/evaluate.json:2453).

   Replace the mechanistic claim with something like:

   > None of the champions meets the registered active-comparator criteria under this probe protocol. This establishes departure from the seed’s measured component performance; it does not establish whether, or how much, the maze gain depends on the engineered selector.

   Describe the three champions as having **zero measured active \(K_D\) at all tested levels through 1.0**, rather than no response. Keep the upper-state-as-A caveat, and explicitly mention the fixed levels and imposed-state assumptions. Static bistability also does not establish functional switching during maze behaviour; the memory assays were deliberately omitted.

3. **Report the missing registered descriptive results.**

   The records contain them, but the narrative omits several requested readings from [§7](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md:291).

   **S-trail’s later-leg-rate contrast:** in legs per 1,000 ticks, the shared-minus-none differences are seed **0.610893**, T-A **0.464177**, and T-F **1.546338**. Relative to the seed’s contrast, these are **−0.146716**, **+0.935445**, and **+0.394365** for the equal-weight schedule average. Report this descriptively, without another significance test.

   **Peer-condition exposure:** the replay coefficient is not a substitute for achieved exposure on the test block. Mean exposure values, seed / final-T average, are:
   - shared: **0.113438 / 0.115659**;
   - replay: **0.089245 / 0.100541**;
   - scramble: **0.018674 / 0.018760**;
   - peers-only: **0.102736 / 0.102368**.

   These matter: replay calibration does not produce exact exposure matching on the test block, and scramble exposure is much lower. The route-overlap values and coefficients currently printed are correct. Specify that overlap is **geometric A–B route overlap**, not overlap of travelled trajectories.

   **Nose recorder:** the printed 2.9%–9.9% range covers final T champions. T-F’s index-124 champions are missing; their range is **2.2616%–3.5798%**. Label the final range and add the snapshot range, with a direct link to the per-champion shares. The remaining printed nose percentages check out.

   **Other component results:** include a compact summary of the saved flags: inactive criterion **29/30**, switching **30/30**, startup **0/30**, offset **2/30**. Qualify switching: its implementation compares against 90% of the settled response, so a zero settled response can make a pass uninformative. Do not present 30/30 as proof of functioning goal switching.

   The training and learning curves are present and internally consistent. Their inclusion by reference is defensible, but provide direct links or a compact supplemental figure/table for best fitness, mean fitness, zero shares and learning curves. No additional tests are needed.

4. **Keep the schedule emphasis, but avoid equivalence and mechanistic interpretations.**

   The draft already conveys the G heterogeneity strongly enough. Preserve the prominent schedule table. Their gain ratio is approximately **5.49**, so “about 5.5-fold” is more precise than “a factor of five.”

   “S-trail comes from T-F” is fair as a descriptive decomposition once T-A’s numbers are corrected. It is not a separately registered schedule-specific significance claim. Also avoid implying T-A does not benefit from trails: its shared-minus-none advantage is **0.998779 visits per wey**, compared with the seed’s 1.342773. Its *increase in dependence* is absent; its trail benefit is not.

   For S-worlds, change **“16 mazes per generation did no better than 8”** to **“the observed means were similar: +0.0694 and +0.0660.”** This descriptive comparison establishes neither equivalence nor absence of an effect.

   S-peer’s “about half the seed’s size” is numerically fair as a descriptive comparison using the common denominator. It is not a tested reduction in peer benefit.

5. **Correct the peer-condition interpretation.**

   [Line 142](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:142) says “peer fields not laid by the colony itself hurt.” Scramble uses the colony’s own peers’ field, spatially permuted. That sentence misdescribes the manipulation and generalises beyond the tested conditions.

   Use: **“Replay and scrambled peer fields reduced later-leg rate relative to own-only trails under these conditions.”** The reported numerical differences are correct. Include the exposure qualifications above.

6. **Replace retrospective power language with observed precision.**

   The spread **0.127046**, planning assumption **0.282**, and prospective MDE **0.19** are correct. But [“the test had more power than planned”](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:100) is not established by one realised sample and its observed effect.

   State instead that observed within-schedule variation was smaller than assumed, with **SE 0.031761 and lower bound 0.165696**, exceeding the 10% reference. Preserve §8’s distinction between the prospective large-effect detection target and the 10% descriptor. Most within-schedule variation is indeed in T-F: the schedule SDs are **0.032004 and 0.176797**.

7. **Make the disclosure language consistent throughout.**

   **“256 untouched mazes” is literally false** given the disclosed trace on maze 6000 and the geometry audit. Replace it in both the summary and conclusions with “256 prespecified test mazes,” immediately qualifying the early audit exposure. State that this breached §4’s evaluation-only opening rule, while also stating the limitation of what was inspected: hashes, not scores or behavioural results.

   Change “before the amendment” to **“during the amendment audit, before the formal rerun and evaluation”** unless a more precise chronology is documented. The reference and comparison straddled the generator change.

   Replace “every feasible maze is bitwise unchanged” with **“every previously feasible maze in the audited corpus was bitwise unchanged,”** matching §14’s explicit finite-corpus qualification. The 37 training ids refer to the original registered schedules; the executed stages list **36 after cut 1**.

   Compute otherwise checks out: **67,426.044756 seconds = 18.729457 hours**, nine attempts, one failed project attempt, all training completed first attempt, and every frozen-parameter assertion passed. Every stage time and projection in the table rounds correctly. Cut 1 was the only cut. Clarify that the accounting unit is synchronised wall-clock time, including CPU work, rather than GPU kernel time.

   The failed project attempt’s approximately one-second duration agrees with its underlying accounting record, **1.1284 seconds**; the stage-body `seconds` field is shorter. No kill occurred. D189 nevertheless explicitly promised disclosure of the possible roughly 40-minute undercharge bound; one parenthetical can state it and that it was not exercised.

8. **Finish the publication package.**

   The experiment [README](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/README.md:3) still says training is underway. Update its status and link the reviewed results.

   Mark the \(K_D>10\) grouping and level bins as an **exploratory presentation of the registered probes** unless their selection was fixed elsewhere before inspection. Their counts check out, but that additional response threshold is not registered. For precision, N’s reported high-level B responses span approximately **11.89–16.45**, rather than 12–17.

The R summaries, probe bistability count, active-threshold failures, four one-nose passes and their identities all check out. I found no numerical reason to alter the registered gate or Holm conclusions. The fixes concern reporting completeness, factual wording and the limits of mechanistic inference.

**Verdict: fix then publish.** Correct the T-A numbers and denominator explanation; add the omitted descriptive readings; remove the selector-bypass and no-response claims; qualify the power, schedule and peer interpretations; reconcile the disclosures; and update the README.