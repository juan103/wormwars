**Verdict: fix then publish.** The registered verdict is correct. The draft has one substantive factual error, missing reporting, and several claims that need narrowing.

I checked HEAD `d29fb3a`, independently recomputed the gates from the per-maze records, reproduced `summary.json` in memory, and verified all 90 local record files against their committed hashes. Their visit ledgers agree with `calibrate.json`. No files changed; I did not rerun simulations.

The recalculated gate quantities are:

| k_r | B_max | B_max / follower | follower / oracle | seed − B_max | Seed median legs | Failed |
|---|---:|---:|---:|---:|---:|---|
| 0 | 2.336914 | 0.141363 | 0.389418 | 6.677734 | 6.8125 | G1b |
| 2 | 2.349609 | 0.148390 | 0.371438 | 7.134766 | 7.8750 | G1b |
| 4 | 2.534180 | 0.153650 | 0.383362 | 8.032227 | 8.6875 | G1b |

The shared follower exceeds four visits at every k_r; the oracle precondition passes; first-draw feasibility is 0.796875, 0.796875 and 0.7890625. Therefore no k_r qualifies. **“E3d: failed at calibration” and stopping before confirmation, the tree reference and the tangent diagnostic follow the bound procedure.** Those unplayed blocks are not missing work.

Required fixes:

1. **Correct “no visit at all” for the S champions.**  
   [RESULTS.md:102](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/RESULTS.md:102) confuses rounded means with exact zeros. S-mod made **5 total visits at k_r = 0, 2 at k_r = 2, and 0 at k_r = 4**. At k_r = 0, four champions contributed those visits. S-dense made exactly zero throughout. Every scoring S wey made only one visit: none completed a leg.

   Suggested wording: “All 16 noses-removed S champions scored below 0.002 visits per wey at every k_r; none completed a leg.” Distinguish rounded zeros in the table.

   The historical **6.59–6.79** range is correct in E3c’s committed `evaluate.json`. Retain the existing qualifications: this does not test the intact-champion prediction or separate maze size from maze family. Also state explicitly that it does **not** establish nose dependence on islands, since intact counterparts were not played.

2. **Add the missing bootstrap intervals and remove “passed by wide margins.”**  
   [Design §5](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:236) requires intervals for each gate quantity. They are absent from both the draft and `report.json`: [the reporting function](D:/Claude/random/wormWars/scripts/e3d.py:612) returns immediately on calibration failure, before computing them.

   Using the committed bootstrap implementation with the bound 2,000 resamples and seed 20261011 gives:

   | k_r | B_max: 95% interval | follower/oracle: 95% interval |
   |---|---|---|
   | 0 | [2.2139, 2.4737] | [0.3266, 0.4516] |
   | 2 | [2.2158, 2.4961] | [0.3073, 0.4374] |
   | 4 | [2.3906, 2.6914] | [0.3191, 0.4464] |

   Every G2a interval crosses ⅓. That **does not change its registered point-estimate pass**, but it makes the owner section’s blanket “wide margins” claim misleading. Report all prescribed intervals, preferably in an additive analysis artifact, and say “every other criterion passed on this calibration block’s point estimates.”

3. **Complete the scent-reach reporting and identify where the remaining required measures live.**  
   [Design §2](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:117) requires the follower/seed performance split by scent reach. Reporting only the flag prevalence does not satisfy that requirement. There are **1, 4 and 11 unflagged goals**, respectively; small groups warrant cautious interpretation, not omission. Provide the per-goal arrival/nonarrival splits, A/B separately and pooled, and the whole-maze visits/zero-visit splits implemented by `scent_split`.

   Most §6 measures are already present in `calibrate.json`: discovery, later-leg rates, occupancy, contact classes, acquisition classes, switches and round trips for every member. I would **not call those data missing**. Add an explicit reporting index or compact appendix pointing to their fields. The draft currently presents selected summaries without explaining where readers can find the complete prescribed reporting.

4. **Narrow the mechanistic interpretation of the contact records.**  
   [RESULTS.md:83](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/RESULTS.md:83), “from the perimeter side and from fragments, not by following a ring,” goes beyond the evidence cited. The counts—2,230/2,393, 942 + 585, and 241 + 313—are correct. But a remembered component can persist through free space, and these summaries do not exclude local ring-following before a visit.

   Say instead: “Visits commonly follow remembered contact with another component, consistent with component switching.” Use the precise term **last remembered component outside the visited goal’s ring**, rather than “last component it touched.”

   Likewise, scope “defeats perimeter-following” to the tested controllers and starts: both qualified scripted followers scarcely score and complete no round trips. The geometric guarantee is separate. The draft’s qualified “open or small maze is one possible explanation” is appropriate.

5. **Fix the remaining numerical and source statements.**  
   At [RESULTS.md:45](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/RESULTS.md:45), the k_r = 0 seed mean is **9.0146484375**, which rounds to **9.01**, not 9.02. W2’s round-trip range is **27.539–31.152%**, so nearest-whole-percent reporting is **28–31%**, not 27–31%.

   The refused attempt’s **“3 s”** is unsupported by the committed summary. Its local accounting record reports **1.2051 timed seconds**, with UTC timestamps two seconds apart. Remove the duration or supply a committed source for the intended timing measure.

   The opening claim that *every number* comes through `e3d_summary.py` is false: projection figures come from `project.json`, equivalence evidence from `g-e.json`, and the historical S range from E3c’s `evaluate.json`. Correct the source statement. Apart from the issues above, the draft’s numerical summaries check out at their stated precision.

6. **Clarify compute scope and the owner’s alternatives.**  
   The **2,905.358 timed seconds, 79,747 worlds and 67,308,420 world ticks** match `compute-record.json`. However, [g-e.json](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/g-e.json:712) explicitly says the full-rollout subprocess contributes wall time but **not worlds, ticks or neural updates**. Carry that qualification into the report and identify 0.81 hours as the formal-attempt accounting total.

   The owner’s alternatives are acceptable as untested proposals after removing “wide margins.” Clarify that fewer roundabout openings require a redesigned construction that preserves island safety; those openings currently create the separation. Revisiting G1b changes the acceptance claim, and cannot rehabilitate this run. The draft correctly requires fresh blocks and an advance commitment.

D230 documents a publication-test gating slip, not a change to the experimental measurements. It does not invalidate this verdict. Preserve that disclosure, and record these corrections openly under the repository’s correction rule. None of these fixes requires playing the stopped blocks.