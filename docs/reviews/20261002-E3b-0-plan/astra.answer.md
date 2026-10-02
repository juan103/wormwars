**Verdict: fix then run.** I checked `roadmap` at `f6d3532`, the archived reviews, D173 and the engine. The problems are fixable within E3b-0’s plan; they do not require abandoning the design.

**Not every pin is carried through.** The update order, rate conventions, polarity assumptions, body-channel removal, equivalence tolerances and wall-follower-as-ceiling decision are present. Missing or incomplete are replay/scramble construction and validation, exact exploration policies, executable search rules, gate power and complete failure handling. The seed’s **own-only and single-wey evaluations**, and Fable’s pre-first-B own-only/none sabotage test, are also missing. That exact-trajectory test applies to the scripted goal-channel follower; the seed’s inactive module is not perfectly silenced.

Required fixes:

1. **Close the remaining geometry loopholes.** The proposed occlusion fixes the demonstrated straight-wall leak. But a free nose can still interpolate a hidden cell around a corner: checking only the head-to-nose segment does not check the bilinear sampling footprint. Likewise, forbidding passage between **two** diagonally touching walls does not prevent clipping a **single** wall corner. Test and specify both cases, including sliding attempts. [Geometry rules](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:33)

2. **Specify implementable maze-ready controllers.** W1’s gain, W2’s bias and wall-detection threshold, motor combination/clamping, and M’s amplitude, initialization and parameterization are unspecified. More fundamentally, the current brain has **no adaptation state**: two mutually inhibiting neurons do not implement the stated adaptation oscillator without additional circuitry or an engine change. The claim that this particular W2 “explores every dead end” is unsupported; a generic wall-following theorem does not establish that this controller follows walls reliably. “Trails can only add shortcuts” is also wrong—they can misdirect or trap it. Require measured coverage and dead-end escape. With both periods, there are **seven concrete candidates**, not five; specify period selection and ties. [Brain update](D:/Claude/random/wormWars/wormwars/brain.py:402)

3. **Make the search executable before running it.**
   - Maze selection depends on follower performance **before its trail constants are selected**. Either declare pilot constants or explicitly nest the searches: eight geometries × 24 trail settings = **192 combinations**.
   - The 24-setting arithmetic is correct. But scent amplitude **A**, the precise normalization of d₀, remaining tie-breaks, endpoint/spawn sampling and rejection rules, episode seeds and repetitions are not pinned.
   - Define aggregation: “eight visits per wey” means a mean, median or minimum? Keep inference on colony summaries.
   - Ensure rejecting unsuitable placements cannot make maze generation depend on the episode stream. [Search](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:148)

4. **Keep the deposit rule, but strengthen its qualification.** The event → timer → deposit → diffusion/evaporation order is consistent, and **λ > −ln(1−μ)** is correct under the stated simplified assumptions. However:
   - Define “on-trail” independently of measured intensity, and specify deposition trajectories, ages and per-condition thresholds.
   - Persistence is restrictive: even without diffusion, an isolated input of 0.2 falls to **0.00164 after 2,400 ticks at μ = 0.002**. Pooling ages could conceal unusable old trails.
   - The wrong-way test needs flat-gradient/no-trail controls. On a straight symmetric trail, a directly backward-facing stereo follower has **L = R** and therefore no polarity steering. Eventual return through wall exploration is not evidence that it read polarity.

5. **Repair the journey and signal gates.** An A→B journey is one leg, **not a round trip**. Specify A→B→A, or rename the measure and adjust thresholds. With confirmed visits starting at A, two completed returns require at least five visits.

   Criterion 3 can currently pass with **shared = own > none**, despite the agreed shared > own > none requirement. Require a declared detectable peer benefit on an appropriate endpoint, or explicitly classify peer feasibility as failed. A hand-picked example where a control loses information is insufficient.

   Pin donor selection, endpoint differences, lockstep timing, route overlap and usefulness across the evaluation distribution. Scrambling must preserve the recipient’s live own trail; specify its permutation/timing and measure exposure at noses. Compare replay against own-only to distinguish **misleading replay** from **helpful live peers**. [Measures and gates](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:135)

6. **Replace the power placeholder with an actual calculation.** A 90% bootstrap confidence interval is not a power specification. Declare significance level, target power, gate margin, variance scaling and the simulated run-level decision rule.

   The committed Stage 3 test means have sample SD **3.4098**, versus E’s mean **12.7891**. If their relative SD transfers, an optimistic normal approximation gives minimum detectable effects of approximately **23.4% of the seed mean at 80% power**, versus **27.6% at 90% power**, using a two-sided 90% interval and zero margin. Thus the unspecified power target changes whether the 25% criterion passes. Eight-run bootstrap performance needs simulation and variance sensitivity analysis. [Committed values](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/summary.json:1009)

7. **Repair failure handling.** Report-set failures trigger further selection on those same mazes. Use fresh report blocks after retries, or label the resulting intervals as adaptively selected exploratory results. Also:
   - Resolve the conflicting fallback triggers in §§4 and 6; controller failure does not automatically justify changing trail chemistry.
   - Component qualification can fail; criterion 4 cannot simply be “not a failure.”
   - Add explicit branches for failed headroom and exhausted GPU budget.
   - Restore the agreed budget-cut order, including horizon. Reducing weys changes the peer task and requires requalification.
   - Longer tuning is not, by itself, a remedy for insufficient statistical power.

**Feasibility:** implementable, but not already supported by the engine. Besides adaptation, the current shuttle ledger and oracle assume one wey, and existing diffusion is unmasked eight-neighbour diffusion.

**Three GPU-hours for E3b-0 is plausible, not demonstrated**, with scripted searches on CPU. The largest trail tensor is **285 MB (272 MiB)** before buffers and donors. Pin the full composition—e.g. `(256 strains, 16 worlds/strain, 8 weys)`—and budget every search, retry, equivalence check and report evaluation.

E3b-1 remains the larger constraint: linear scaling of committed E3a timing gives about **47 hours for two training arms at 1,200 ticks**, or **94 hours at 2,400**, before additional maze costs. Measured throughput and substantial scope reductions must establish the 24-hour projection; the plan’s assertion does not establish it.