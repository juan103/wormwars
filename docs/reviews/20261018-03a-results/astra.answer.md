**fix first.**

Outcome (iii) agrees with the recorded rule. D318 correctly distinguishes matching the refits from restoring the intact brain, and 62.5% is correct. The exploratory label is appropriate. However, several interpretations overreach, one correction did not reach ROADMAP, and the reproduction instructions have a substantive problem. This was a static review; I did not execute repository scripts or tests.

1. **High — The NIP conclusion is wrong.** [RESULTS.md:153](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:153), also lines 27, 233 and 247; [ROADMAP.md:11](D:/Claude/random/wormWars/ROADMAP.md:11).

   Neither reaching an optimum nor an inherent inability to benefit from X was established. Even an optimum in the network **without** X need not remain optimal when X adds degrees of freedom. Moreover, NIP/URXL’s measured headroom is **+0.0521 [0.0317, 0.0721]**: below the practical margin, but not zero.

   Replace the general conclusion with “Neither tested NIP target-brain had headroom exceeding p under these refits.” Remove “N2 would share it.” That sentence directly contradicts the stated absence of conclusions about N2. Joint optimisation and less-trained brains are possible follow-ups, not demonstrated necessities.

2. **Medium — The claimed dominance of gap-partner variance is unsupported by the recorded nulls.** [RESULTS.md:255](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:255).

   `search-check.json → variants → enrichment_per_type` records these null SDs:

   | Variant | Incoming | Outgoing | Gap |
   |---|---:|---:|---:|
   | V4 | 0.05035 | 0.04770 | 0.03852 |
   | V3 | 0.05494 | 0.04646 | 0.05143 |
   | V1 | 0.04984 | 0.04818 | 0.05184 |

   These do not substantiate “carry most of the null’s variance”; V4’s gap SD is the smallest. Fable’s earlier calculation was a design concern, not a measurement of these realised rankings. Qualify it accordingly or substantiate an actual variance decomposition. Also replace **“registered recovery statistic”** with **“planned recovery statistic”**: there was no pre-registration.

3. **Medium — Group-average equivalence becomes “every time” and equality.** [RESULTS.md:19](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:19), also lines 147 and 193; [README.md:36](D:/Claude/random/wormWars/README.md:36).

   The functional comparisons concern **mean free-search scores against mean refit scores**, within ±p. They do not establish success for every search. For example, `full`’s MIP/URXL `free-3` scores **1.71094**, versus mean refits **1.83431**—a deficit larger than p.

   Likewise, “partners at chance” is stronger than failure to detect enrichment. Use “no enrichment detected.” At line 193, V4’s original-partner advantage is positive, **0.0274 [0.0134, 0.0415]**, although practically equivalent. Say “no advantage exceeding p,” rather than “no longer beat.”

4. **Medium — The noise diagnosis and proposed remedies are too categorical.** [RESULTS.md:23](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:23), [RESULTS.md:221](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:221), [RESULTS.md:252](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:252).

   The re-evaluation supports a local diagnosis at **two selected final states**. Its reference is estimated from 1,024 worlds; median SEs of individual reference gains are about **0.016**, and selecting the reference-best offspring also introduces selection bias. “True improvements” should therefore be “improvements estimated on the reference worlds.”

   These observations support evaluation noise as a contributor. They do not establish the complete reason searches failed, or that successful restoration **needs** larger evaluations, gradients, a surrogate, or smaller steps. Present those as candidate remedies requiring investigation.

5. **Medium — D318’s review-timing correction was not propagated.** [ROADMAP.md:9](D:/Claude/random/wormWars/ROADMAP.md:9).

   “Before any GPU run … the code was reviewed in three rounds” is false. `PILOT-DEV.md:12–14` and `RESULTS.md:55–56` explicitly say early stages overlapped review rounds 2 and 3. Exploratory GPU checks also preceded design v7.1. Correct this with the actual chronology and a dated annotation.

6. **Medium — The reproduction instructions cannot regenerate everything on a fresh checkout as described.** [RESULTS.md:274](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:274).

   The committed stage records make the bare commands refuse execution. Adding the mentioned rerun flags does not fully solve this: `_finished_rows()` in [scripts/e03a.py:791](D:/Claude/random/wormWars/scripts/e03a.py:791) reuses completed rows from the archived `full` record. All four committed rows qualify, so `full --rerun` skips their searches and does not regenerate their local state files. `search-check` then requires those files at line 1185.

   Document a fresh-run procedure that keeps historical records outside the active resume lookup, or provide separate output locations. The CPU summary-rebuilding description and the limited exactness claims are otherwise accurate.

7. **Low — Three displayed numbers suffer from double rounding.**

   - [RESULTS.md:43](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:43): probe wall time **0.09 → 0.08 hours**. Raw duration is 305.939341 seconds, or 0.084983 hours.
   - [RESULTS.md:99](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:99): NIP/PLNL at L=10, **1.17 → 1.16**. Raw mean: 1.16455078125.
   - [RESULTS.md:102](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:102): KTS T=10 at L=10, **2.35 → 2.34**. Raw mean: 2.3447265625.

   Round once from raw values, or retain enough precision in `summary.json`. I found no other numerical discrepancies in the reported tables and quantities. Separately, line 156’s “gained no AUC” is literally contradicted by **0.490 → 0.497**; “no consistent improvement” would fit the observations.

8. **Medium — “Nothing ran on N2” is literally false.** [RESULTS.md:3](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:3), [03a README.md:6](D:/Claude/random/wormWars/experiments/03a-self-consistency/README.md:6), [README.md:36](D:/Claude/random/wormWars/README.md:36).

   Setup explicitly runs an N2 reference calibration in [scripts/e03a.py:314](D:/Claude/random/wormWars/scripts/e03a.py:314), recorded as `setup.json → calibration.n2_reference`. The preceding development checks also evaluated 04a champions.

   Say **“No 03a reconstruction searches or pilot brain evolutions ran on N2.”** Those calibration/development evaluations do not turn this into a test of the self-consistency hypothesis on N2.

9. **Low — The probe reading needs its remaining limitations stated locally.** [RESULTS.md:104](D:/Claude/random/wormWars/experiments/03a-self-consistency/RESULTS.md:104).

   State dependence under this intervention is a defensible reading. KTS’s small or reversed score changes do **not** fail the stipulated calibration: the design explicitly requires no sign. They also do not establish that score loss measures useful sensory memory.

   Retain the existing filtering/rhythm caveat and add the design’s omitted qualifications: history varies between L and 2L between resets; the first affected action is 2L+1; comparisons across L do not estimate memory horizons; no nonspecific-disruption control was run. Showing all three KTS rows would help—T=20 loses about 0.194 at L=10, which the selected T=10 row does not reveal.

10. **Low — Compute presentation has an ambiguity and a faulty attribution.** [03a README.md:4](D:/Claude/random/wormWars/experiments/03a-self-consistency/README.md:4); [summary.json:60](D:/Claude/random/wormWars/experiments/03a-self-consistency/summary.json:60).

    The README assigns 5.29 hours to pilot-dev **“and then”** describes the bounded check. But 5.29 already includes that check. State explicitly that it is the combined measured total.

    The summary note says **“D317 gives 0.026”**, but D317 gives rounded totals of 5.31 and 5.84, not that preflight subtotal. The number is hard-coded in `e03a_summary.py:54`. Commit or correctly identify its source, or label it approximate. This is a traceability defect, not evidence that the overall 5.84 total is wrong.

11. **Low — Historical-text preservation is incomplete in the project README.** [README.md:36](D:/Claude/random/wormWars/README.md:36), [README.md:50](D:/Claude/random/wormWars/README.md:50).

    The commit diff shows the previous table entry and “next; not started” sentence being replaced. The experiment README preserves and annotates its earlier statements, and ROADMAP retains its earlier status entries. The project README does not preserve those statements in the document. For the preservation convention requested here, add a short dated historical note. The new “Next on the roadmap” direction itself agrees with D318.