**Verdict: proceed to the pre-registration, with the fixes below; no further design round.**

V2 resolves the substantive design objections: the schedule-average estimand, within-schedule uncertainty, sensitivity-only sign-flips, champion selection, fresh maze blocks, non-adaptive reads, mutation exclusions, and narrower interpretation.

The power table matches [power.json](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/power.json), subject to rounding. The implemented gate formula is correct. **However, the empirical simulation has a scaling error**, so agreement with the file does not validate all the power claims.

The compute arithmetic reproduces from [timing.json](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-0/timing.json): T-A **4.711 h**, T-F **5.653 h**, N **3.533 h**, R **1.178 h**; training **15.074 h**, with reserve **18.843 h**. Validation is **1.206 h** and learning curves **0.207 h**. Approximately **21.2 h** is a reasonable provisional total; evaluation and assay allowances still need the promised benchmark.

Fix these before binding the pre-registration:

1. **Correct empirical power scaling.** [Line 35](D:/Claude/random/wormWars/scripts/e3b1_power.py:35) standardizes eight values with `ddof=1`, then samples them uniformly with replacement. That sampling distribution has variance **7/8**, not 1. Consequently, nominal SD 0.282 actually generates **0.26379**. Use `ddof=0` for this empirical distribution and regenerate the power results and claims. The same issue exists in `e3b0_power.py`; record the historical correction openly.

2. **Scope the shifted-null claim.** “MDE 0.28–0.31” does not cover every displayed scenario: the current JSON gives **0.36 for both shapes at CV 0.40**. State which scenarios the range describes, then update after fixing scaling.

3. **Specify secondary tests completely.** Holm correction alone does not define them. Pin S-gen’s paired test and S-trail/S-peer’s schedule-stratified estimators and variance formulas. For S-peer’s inherited **first-B time**, improvement means **shared − own < 0**; explicitly register that direction.

4. **Pin indexing and aggregation.** `evolve_batch(generations=125)` currently evaluates indices **0–124**. Define exactly which population supplies each read and snapshot. Also define whether “median legs per wey” means the median across individual weys or across colony means: E3b-0 used **the median of colony means**, which is different.

5. **Replace the automatic CV interpretation.** Define spread consistently with the simulation—within schedules, normalized by the seed mean. An observed CV above 0.282 does not by itself establish “underpowered”; report uncertainty relative to the prespecified practical effect.

The §7 implementation checks remain prerequisites. I checked source, committed outputs, and arithmetic; I did not rerun the simulations.