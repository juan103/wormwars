**Verdict: fix then publish.** The fixed decision readings are correct. The exploratory phase calculation has a real bug, and several sentences overstate or misreport the results.

I independently recomputed all **1,440 hunter–setting classifications**, **543 qualification probes**, **480 fixed-probe contrasts**, and **90 ghost–reach contrasts** from the committed counts, using the specified paired bootstrap. No discrepancies. The three summary tests pass. H1-ghost is correctly excluded from the decision rules; baseline selection is correctly repeated within each resample; failure, uncertainty and fall-off are correctly distinguished in `reading.json`.

The fixes I require are:

1. **Fix the missing-contact sentinel in the phase script.**  
   [e5_0_phases.py:27](D:/Claude/random/wormWars/scripts/e5_0_phases.py:27) selects every captured life, including those with `first_contact_tick == -1`. That produces negative approach durations and fictitious kill durations.

   Across the six hunters and six settings in `phases.json`, **46 captured lives have no recorded contact**. At H2-1, L1 has **23 such lives out of 2,111 captures**. Restricting phase durations to captured lives with valid first-contact timestamps changes its kill median from **22 to 21 ticks**, affecting [RESULTS.md:228](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:228). The other displayed approach/kill medians remain unchanged.

   Report captures without contact separately, calculate phase medians only where the timestamps are valid, and add a regression test for this case. This concerns the exploratory analysis, not the capture counts or qualification readings.

2. **Rewrite the phase interpretation around what was actually measured.**  
   [RESULTS.md:230](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:230) needs three qualifications:

   - “Contact was not measured directly” is wrong: `contact_ticks` is logged and its median already appears in `phases.json`. However, it measures the hunter’s head coming within 1.5 cells of a prey body point—not damaging bite contact. The captures without recorded contact demonstrate that distinction.
   - These are medians **conditional on capture**, excluding unfinished lives and weighting worlds by their number of captures. They do not establish why total performance changes.
   - S-const is retuned at each setting. This comparison changes both prey speed and hunter parameters. Its phases also do not shorten monotonically: approach is 28, 29, 18 ticks at speeds 0.1, 0.5, 1.0; kill is 26, 14, 15.

   Describe shorter phases at the endpoints and longer post-contact intervals in the **two inspected E4s-1 champions**. Keep “losing contact” and body-sweep explanations as hypotheses. The headline currently generalizes the two champions to the whole family.

3. **Preserve the plan’s distinction between nonqualification and demonstrated failure.**  
   The records do; the prose sometimes does not.

   | Location | Required correction |
   |---|---|
   | [RESULTS:24](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:24), [README:35](D:/Claude/random/wormWars/experiments/E5-hunter/README.md:35) | Random-walk fall-off includes **0.75**: `e2 extension run04`. The distribution is 24 at 0.25, 22 at 0.5, one at 0.75. |
   | RESULTS:24, “18 first fail at 0.4” | Say **18 first do not qualify**. Twelve have demonstrated failure; six are uncertain. |
   | [RESULTS:179](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:179), “then fails again” | 04a run04 qualifies at 0.2, is **uncertain at 0.3**, and demonstrably fails at 0.4. |
   | [RESULTS:241](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:241), “generation 0 catches nothing” | False. It never qualifies. Its best H1-reach genome averages **0.6015625 captures**, and its route family means reach approximately 0.24. |

   The proposed E5-1 speed ranges should likewise be identified as selected candidate ranges, rather than presented as the complete observed fall-off ranges.

4. **Narrow the stereo conclusion.**  
   [RESULTS.md:210](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:210) and the README’s “dividing line” wording are too categorical.

   The results support **substantial dependence on the bilateral difference in E4s-1 and L1, with much smaller, mixed effects in E2d**. They do not establish that stereo use explains the entire between-family performance difference. After the mean probe, E4s-1 still averages approximately **1.624 captures at H1-bite**, versus E2d’s **1.016 intact**, and **1.637 at H2-0.5**, versus **0.689 intact**.

   E2d also has 11 positive and three negative intervals for the H1-bite mean contrast. Its small family average is not evidence of universal absence of stereo sensitivity. The historical E2d criterion can be cited as an operational result on Task N, not transferred into a categorical mechanism claim here.

   The mirrored probe supports dependence on spatially informative scent. It does not identify the alternative computation as temporal, or otherwise explain “by other means.”

5. **Remove two unsupported causal attributions.**  
   At [RESULTS.md:142](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:142), replace “the tuned constant turn matters there” with “the tuned parameters improve performance there.” Gain, forward speed and turn changed together; this analysis does not isolate turn.

   At [RESULTS.md:243](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:243), starting from “E4s-1’s graft” does not establish that a null-graph arm inherits a strong hunter. The demonstrated competence belongs to the tested **whole N2-plus-graft brains**. Transfer to null graphs remains untested. Similarly, poor zero-shot transfer of Task-N-trained N2 champions does not establish poor evolvability on Task H.

   The E5-1 discussion should also retain L1 as a demanding frozen comparator: at route speed 1.0 it beats every tested E4s-1 champion, not merely their mean.

6. **Correct the equivalence coverage claim.**  
   [RESULTS.md:12](D:/Claude/random/wormWars/experiments/E5-hunter/E5-0/RESULTS.md:12) implies that per-tick traces were checked under all three probes. In [e5_0.py:449](D:/Claude/random/wormWars/scripts/e5_0.py:449), the trace loop runs **under real scent only**. Counts, capture ticks and path lengths cover all three probes.

   State that coverage explicitly, including the limitation relative to the wording of plan §4.2. The README should say equivalence held **in the specified CPU checks**, rather than making an unrestricted engine-equivalence claim.

7. **Fix the smaller numerical and reporting errors.**

   | Entry | From unrounded records | Display |
   |---|---:|---:|
   | H2-0.4 baseline ratio | 0.0484937546 | **0.048**, not 0.049 |
   | H2b-wall-0.5 ratio upper bound | 0.1225075942 | **0.123**, not 0.122 |
   | H1-ghost E2d family mean | 2.0947473404 | **2.09**, not 2.10 |

   Round from full precision when producing the final display; `summary.json`’s intermediate rounding contributes to the problem.

   “Each champion … decline[s] after” its peak is also too strong: E4s-1 runs **04, 10 and 14** have subsequent increases. Say they finish below their peaks or decline overall.

   “The prey’s body … costs most genomes nothing” should be “usually has small effects.” For E4s-1’s ghost–reach comparison, 15 of 16 point estimates are nonzero and 11 intervals exclude zero.

8. **Make the traceability and reproduction instructions accurate.**  
   “Every number is in `summary.json`” is not literally true: the quoted CPU episode rate comes from `bench.json`; the README also omits the phases exception. Name the actual sources or expand the summary.

   The formal reproduction command cannot simply run in a checkout containing the committed start markers: `start_marker()` explicitly refuses to overwrite them. Document a separate replication procedure and distinguish it from regenerating summaries from existing records.

The run itself does not show a cap violation or an omitted qualification probe. The recorded total is **28,572.204 seconds**, leaving **227.796 seconds—about 3.80 minutes**. The thin margin, random-walk wall limitation and pursuit reference’s shortcomings are already disclosed adequately. Clarify that the wall-limited percentages pool all hunter evaluations, whereas realised-speed medians use the stationary hunter.

One additional accounting correction belongs beside the plan: §8 says **379 tuning combinations**, but the registered grids contain **487**, giving **592,192 tuning episodes**. The benchmark used the actual grids, so this is an estimate-text error, not evidence of an unregistered tuning expansion.

These findings warrant correcting the derived phase analysis and publication text. They do **not** invalidate the fixed solvability, qualification or fall-off readings.