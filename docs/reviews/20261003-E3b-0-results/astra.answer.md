**Verdict: fix then publish.** The main findings survive checking, but several interpretations need correction.

I recomputed the report’s paired contrasts and confidence intervals from `report.npz`, checked 1,492 summary statistics against the stage arrays, and verified that the requested records are committed. I did not rerun simulations or the test suite.

1. **The principal numbers are correct.** The trail benefits, first-B contrasts, stage outcomes, headroom, 2.62-hour accounting and 70.66-hour projection agree with the records. One numerical correction: **K_D × level at q95 is 15.1913, so 15.2, not 15.1**. The seed’s shared−own rate interval starts at **0.000892**; printing `0.00` obscures its narrowly positive lower bound. [Results](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/RESULTS.md:115)

2. **Fix “Exposure was matched,” especially in “In brief.”** Replay’s *mean* exposure was approximately matched: residuals are −4.1% for the follower and −6.5% for the seed. Scramble was not exposure-matched: its exposure was only **7.1% and 17.6%**, respectively, of shared-condition peer exposure. Scrambling preserves field mass, not experienced exposure. The report must distinguish these controls. [Exposure records](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/report.json)

3. **Keep the operational replay finding; weaken its mechanistic explanation.** “Another episode’s trails on the same walls impair performance relative to own-only” is supported. **“Since they mark the wrong route” and “the peers’ benefit depends on … the colony’s own sources” are not established.** Replay also changes spatial and temporal structure and the relationship between trails and recipient behaviour; scramble changes exposure substantially. The independent evidence for beneficial live peers is the shared−own first-B contrast. Directional trail use remains unshown. [Interpretation](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/RESULTS.md:131)

4. **Correct statements that revive previously rejected claims:**

   - “Could not be passed” must become **“did not pass under the tested conditions.”** The confirmed amendment explicitly withdrew the impossibility claim.
   - “Weak ones gave no effect” should become **“neither cap-passing setting established a positive effect.”** Their estimates were +0.225 [−0.126, 0.608] and −0.164 [−0.522, 0.213].
   - “Before it affected a recorded result” is false: Stage B’s committed exposure arrays contain zeros. Say the bugs were fixed before the final report comparisons, while identifying affected earlier records.
   - The amendments changed **qualification rules**, not the linear trail dynamics.
   - Scope −0.76 to **S3r3+W2’s four-maze, 600-tick CPU diagnostic**. It is not a measured turn bias for every variant.
   - Label the 4.0% exceedance and component-test input quantiles as **selection-maze measurements**. Qualify H=1200’s failure as occurring **at Stage A’s pilot constants**.

   These corrections follow the [confirmed amendments](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:545), [B2 record](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/stage-b2.json) and [decision log](D:/Claude/random/wormWars/DECISIONS.md:5537).

**The exit criteria are otherwise read correctly.** Criterion 1’s missing GPU leg is adequately disclosed in the detailed section, but its overall status is **incomplete**, not passed. Complete it before E3b-1 runs. Criteria 2–4 pass under the amended rules; criterion 4 does not certify the entire input distribution. Criterion 5 fails as sized. Criterion 6 passes **conditionally on the assumed run-level variability**: at CV 0.282, twelve runs give simulated minimum detectable effects of roughly 20–22%. The distinction from the 0.744 between-maze CV is correct; that quantity cannot validate the run-level assumption. [Power record](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/power.json)

**E3b-1 should inherit the qualified task:** c=5, H=2400, eight weys, E+W2, the selected linear trail constants and scents, and common wall mechanics across comparisons. Retain the defined peer endpoint, fresh evaluation mazes, and twelve independent runs for each confirmatory gate arm. D=141 is the measured assay-delay reference. Evolution settings, validation schedule, detailed hypotheses and affordable secondary scope remain open. Task changes require the stipulated requalification; E3b-0 establishes neither evolutionary improvement nor directional trail use.

**Bring the budget down by generations first.** Using the committed projection:

| Generations | Two-arm training, including 25% reserve |
|---:|---:|
| 100 | 14.1 h |
| 125 | 17.7 h |
| 150 | 21.2 h |
| 170 | 24.0 h |

These exclude validation, evaluation and assays. **125 generations is a reasonable budgeting candidate, not yet a demonstrated feasible design.** Benchmark the complete proposed workflow, including initialization, evolution overhead, replay donors and the outstanding equivalence check. Aim for ≤24 hours all-in for E3b-1; the owner’s total ceiling leaves approximately **27.38 hours after E3b-0**. [Timing](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/timing.json)

If necessary, reduce worlds per genome next and remeasure throughput; horizon comes last and requires requalification. Preserve twelve gate runs. Making the no-trails arm descriptive is the documented scope fallback, with correspondingly weaker training-arm claims. Dropping that arm alone cannot rescue 500 generations: one arm with reserve still projects to **35.3 hours**. Any null must remain a conclusion about the preregistered, affordable tuning effort.