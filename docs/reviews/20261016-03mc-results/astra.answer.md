**Fix then publish.** The headline outcome is correct. Before publication, correct the interval label, complete the registered reporting, fix two rounding errors, and narrow the opening source claim. None of these findings changes a registered verdict.

1. **Medium — N2’s interval is mislabelled as 95%.**  
   [RESULTS.md:51](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:51) reports “95% interval 0.915–0.937.” Those endpoints are constructed as N2 ± 1.645 × SE in [mc_report.py:60](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:60). This is approximately a **90% normal-approximation interval using a bootstrap SE**, not a 95% percentile interval.

   Change the label and identify the method. The separate 90% effect intervals in the preceding table are percentile bootstrap intervals; these two constructions should not be conflated.

2. **Medium — RESULTS does not expose all the reporting required by §6.**  
   [PREREGISTRATION.md:240](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/PREREGISTRATION.md:240) requires every component and planned/measured/valid counts; line 247 explicitly requires each ensemble’s median ΔP4 beside Q-A.

   [RESULTS.md:64](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:64) gives only the range of ensemble medians. In ensemble order SH, SH-route, SH-class, SH-mirror, SH-recip, the individual medians are **0.094712, 0.072334, 0.072472, 0.073438, 0.087803**.

   Add a compact component/count table: Q-A’s five component p values are all 1/129; Q-D’s are **1/129, 1/129, 3/129, 2/129, 3/129**. Explicitly distinguish planned, measured and valid counts: 128 per ensemble for A/D, 256 permutations for C, and 32 batches per condition for B. Q-B’s bootstraps dropped zero resamples. The global completion statement is correct, but does not provide the separately specified reporting.

3. **Medium — Several registered descriptives are absent or only selectively presented.**  
   Against [PREREGISTRATION.md:274](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/PREREGISTRATION.md:274), the draft omits:
   
   - The null-graph deletion results entirely: per-graph cuts, ensemble medians and intervals, and N2’s ranks.
   - The full retention curves.
   - The full 95-pair screen, including numerator cuts and paired intervals; [RESULTS.md:100](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:100) presents selected entries.
   - Several descriptive intervals, including the double deletion’s response and numerator cuts.

   **These records exist in report.json.** This is a presentation omission, not evidence that analyses were skipped. An explicitly indexed supplement is sufficient; 95 rows need not interrupt the narrative. Name the JSON sections and summarize the entirely omitted null-deletion result. For example, all 15 target-by-ensemble comparisons have zero of 32 null graphs reaching N2’s response cut.

   [DECISIONS.md:9104](D:/Claude/random/wormWars/DECISIONS.md:9104)’s assertion that the draft reports “every secondary test and the descriptives” consequently needs qualification or a dated correction.

4. **Low — Two numerical rounding errors.**  
   At [RESULTS.md:49](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:49), SH-mirror’s upper effect endpoint is **0.0884685616**, which rounds to **0.088**, not 0.089.

   At [RESULTS.md:36](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:36), the local accounting records give **7.221573635 run hours**, rounding to **7.22**, not 7.23. I could read those files in this workspace. Build and check are 0.261625484 and 0.244861293 hours; the total is **7.728060412**, correctly reported as **7.73**. Neither correction changes an outcome.

5. **Low — “Every number comes from report.json” is false as written.**  
   [RESULTS.md:4](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:4) includes an overly broad provenance claim. The power estimate comes from power.json, historical P4 values from earlier experiments, and accounting from local compute records. These values check out, but they are different sources. Say that the **current study’s statistical results** come from report.json, and identify the other sources separately. Publishing the small accounting aggregate would make the compute claim independently checkable from the repository.

6. **No defect found — Registered sentences, conditional wording and decisions are correct.**  
   The quoted primary pass sentences match the registration after substituting counts and normalizing line wrapping. Q-A’s second sentence is warranted: replication is distinctive against every ensemble, and every median-based lead narrows. The replication and Q-E verdict wording is correct; the gaps-off verdict names the correct failing gates.

   The Holm table at [RESULTS.md:8](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:8) is correct. Exact raw p values in its order are **0.00389105, 0.00775194, 0.01131240, 0.02325581**; adjusted values are **0.01556420, 0.02325581, 0.02325581, 0.02325581**. All pass. Other displayed statistical values and interval endpoints agree with report.json, apart from finding 4. No other rounding changes a decision.

7. **No material computational mismatch found in the reviewed statistics.**  
   In [mc.py:19](D:/Claude/random/wormWars/wormwars/exp03/mc.py:19), the rank directions, add-one p values, intersection-union maximum and Holm adjustment implement the registered rules. Q-B uses pooled ratios of means, paired-bootstrap SEs and the specified normal-theory tests.

   Specific checks:
   
   - [mc_report.py:172](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:172) computes Q-A’s second sentence from **differences between median-based leads**, not from median ΔP4.
   - [mc_report.py:362](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:362) computes Q-D’s other ticks separately, taking the maximum p across ensembles. All four pass at the registered unadjusted 0.05.
   - [mc_report.py:431](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:431) computes the kept share as `(permutation median − pooled null median)/(N2 − pooled null median)` and transforms each permutation bootstrap draw. Its interval conditions on the observed N2 and null reference values.
   - [p4mc.py:549](D:/Claude/random/wormWars/scripts/p4mc.py:549) distinguishes graph-level retention validity from genome-level eligibility and applies the stated retention and settling cutoffs.

8. **No material overclaim found; verification has limits.**  
   [RESULTS.md:93](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:93)’s AIY observation is accurate: its 90% interval excludes zero while remaining inside ±0.02. The double-deletion estimate and 95% interval are beyond that margin. Calling these descriptive avoids adding confirmatory tests.

   [RESULTS.md:158](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:158)’s **0.875 versus ensemble means** comparison is numerically correct and explicitly descriptive. It does not establish retained distinctiveness; the draft appropriately leaves that question open. The limitations and “What follows” do not claim a mechanism, stable states, behaviour or mediation through RIA/AIY.

   I checked HEAD is `3e65ef6` on `roadmap`, and found no changes to the registered code or pre-registration since binding. I compared the displayed numbers with report.json and independently passed **104 arithmetic checks** against measurements.json, covering counts, ranks, ensemble means, lead changes, pooled deletion estimates and kept share. I inspected the build/pre-run records and local accounting. I did **not** regenerate bootstrap intervals or verify per-genome arrays/hashes, independently establish historical push timing, or verify machine exclusivity during the run. No GPU work or file modifications were performed.