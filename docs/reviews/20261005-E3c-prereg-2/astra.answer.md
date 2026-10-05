**Verdict: revise.** The main blocker remains calibration: draft 2 documents the failure of confirmatory inference, but still emits confirmatory labels under the conditions that cause it.

I checked commit `0e27083` on `roadmap`. All 22 statistics/power tests pass. I reproduced the entire `power.json` exactly in memory, including the 15,040 comparisons against `readings`. The four pinned file hashes and all 512 P-joint genome hashes match. The raw accounting records sum to **3.9457356 hours**, matching the aggregate. No files were changed.

**1. Were draft 1’s required changes taken?**

Not all. Against Astra’s seven required changes:

| Prior requirement | Draft 2 assessment |
|---|---|
| Correct and regenerate power | Centering, P-joint’s eight runs, sensitivity scenarios and Monte Carlo SEs are corrected. Joint claim-error accounting remains incomplete; simultaneous interval coverage is absent. |
| Replace intervals and resolve calibration | Fixed 97.5% intervals are implemented correctly. Calibration is **not resolved** by the observed-failure rule. |
| Repair coverage classification | Proportions, separate components and direct nose comparisons are present. Undefined P-joint measurements still produce an invalid comparison. |
| Specify secondary statistics | Mostly addressed. Bootstrap confidence levels and insufficient-data cases remain unspecified. |
| Complete execution contract | Substantially improved; several composition and measurement details remain open. Accounting is corrected. |
| Restore ledger and change inventory | Addressed in [§11 and §13](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:479). |
| Narrow mechanistic and Q2 wording | Addressed in [§1](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:30) and [§7.3](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:302). |

Fable’s requested binding sequence, hash pins/refusal, P-fixed intervention, coverage wording, loss interval and inventory changes are present. Its earlier assessment of mixture calibration does not survive the corrected simulation.

Consequently, [§15’s “Every required change is taken”](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:570) and [D207’s attribution of the fallback](/D:/Claude/random/wormWars/DECISIONS.md:6738) overstate compliance.

**2. Are the statistics, tests and fallback right?**

The Welch calculation, fixed interval levels, Holm adjustment, strict margin comparisons and censored median for nonempty valid inputs are correct. The Welch test and confidence-interval comparison use the appropriate [SciPy interface](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html). See [statistics lines 42–94](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:42).

**The failed-run rule is useful as a diagnostic, but unsound as the gate between approximate and confirmatory inference.** It makes that distinction using the same small sample whose missing failures cause the problem. The committed simulation demonstrates:

- Unequal failure rates, eight S runs, true global null: joint false rejection **0.3348 or 0.3520**.
- The corresponding six-run cases: **0.4414 or 0.4576**.
- Q2 alone reaches **0.1402**.

These are already *after* applying the fallback. See [eight-run example](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:7642), [six-run example](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:20678), and [Q2 example](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:25531).

The disclosure in [§7.1, lines 259–261](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:259) is candid. It does not restore error control. Nor can an inference about all-run means automatically become a valid inference about successful-run means: that changes the estimand, and the conditional procedure has not been calibrated.

My fallback recommendation was to downgrade Welch’s primary conclusions when useful calibration could not be achieved. **It was not to retain confirmatory status whenever observed failures happen to be zero.**

The numerical limit is mostly correctly quantified. Two qualifications matter:

- \((7/8)^8=0.3436\) correctly describes no failure-component draws.
- The pilot bound \(1-0.05^{1/6}=0.3930\) describes a pooled/common-rate calculation. It does **not** bound either arm’s failure probability by 0.39. With three observations per arm, the separate one-sided bounds are **0.6316 each**, and concern the pilot endpoint. Clarify [§8, line 425](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:425).

There is also a concrete coverage defect. This input returns `"supported"`:

```python
coverage_rule({
    "s_mod": [True] * 8,
    "s_dense": [True] * 8,
    "p_joint": [None] * 8,
})
```

Undefined P-joint measurements become a zero coverer share, establishing “lower than both” without measurements. See [statistics lines 140–155](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:140). The tests cover undefined S-arm measurements, but miss this case.

**3. Is the power analysis faithful, and does §8 match it?**

**The generated samples and label simulation are faithful to the current registered algorithm.** The corrected centering is algebraically right; both contrasts share S-mod; P-joint remains eight under the planned cuts; and the entire saved output reproduces.

Most quoted rates match, including the failure-mixture rates and Q2 sensitivity table. However, **“Any false confirmatory claim” is the wrong description of the counter.**

[Script lines 127–140](/D:/Claude/random/wormWars/scripts/e3c_power.py:127) count only null/wrong-direction rejections in that joint quantity. They exclude:

- false “beyond the margin” assertions;
- false “within the margin” assertions;
- false “no relevant difference” assertions.

The latter two make claims of practical negligibility regardless of whether zero is excluded.

Using the exact saved simulation draws, I obtained:

| True Q1, Q2, visits | Existing joint counter | Any false label assertion |
|---|---:|---:|
| 0.5, 0 | 0.0274 | **0.0544** |
| 1.0, 0.5 | 0.0002 | **0.0144** |

The second row is independently visible in the saved output: false “beyond” is 0.0110, false equivalence is 0.0032, and wrong direction is 0.0002. These disjoint outcomes total 0.0144. See [power.json lines 1980–2015](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:1980), against [§8’s table](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:382).

These checks establish a counter-definition problem. The 0.0544 estimate alone does not establish significant miscalibration beyond Monte Carlo uncertainty.

Also:

- The requested **simultaneous interval coverage** is still not recorded.
- Analytic population means are not stored per scenario, although the centering code is now correct.
- [§8, line 371](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:371) incorrectly says both S arms’ successes are at 6.7. S-mod’s are; S-dense’s successful-component mean is adjusted to preserve the requested contrast.

**4. Are §0 and §5 complete enough?**

**§0’s binding sequence is acceptable.** It explicitly separates registration from later implementation and requires review plus an amendment identifying the implementation commit. The absent formal runner is therefore no longer itself a blocker. See [§0, lines 19–28](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:19).

The execution contract still needs these decisions:

- **Reduced compositions:** §5 fixes training at `[256,8,8]` and `[128,8,8]`, while §10 reduces run counts. Specify whether reduced batches become `[192,8,8]` and `[64,8,8]`, or preserve full compositions through padding; likewise specify reduced checkpoint compositions. Run IDs alone do not settle this. See [§5, lines 166–183](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:166).
- **Benchmark construction:** the benchmark block has 32 IDs, but checkpoint/champion/evaluation chunks require 128 or 256 worlds per strain. Specify repetition or another explicit construction, and timing/projection for cut compositions. See [§4, line 138](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:138) and [§9](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:439).
- **Learning-curve references:** §7.2 requires W2 and P-fixed on the learning-curve block, but §5 schedules these references only on the test block. Assign their learning-block evaluations a stage and composition. See [§7.2, lines 282–285](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:282).
- **Interruption semantics:** distinguish complete intact-test eligibility from eligibility for paired intervention/path readings; resolve whole-stage versus missing-chunk reruns and preservation of batch membership. Define the scope of “trails off” so its cost and first cut are calculable. See [§5, lines 181–197](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:181).

The retained IDs, admission refusal, minimum primary sample sizes and accounting charge are otherwise sufficiently explicit.

**5. Anything else wrong or overstated?**

Three additional corrections:

- [§7.3, line 335](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:335) says every arm being “mostly coverers” implies P-joint is not lower. That is false: shares \(1,1,0.75\) produce `"supported"`. Say **equal shares**, or **all champions are coverers**, if that is intended.
- The checkpoint schedule contains **21 checkpoints**, not 20: eleven from 0–50, nine from 75–275, plus 299. Correct [§10, line 459](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:459).
- The contrast bootstrap specifies resampling and seed, but no confidence level/percentile endpoints. The successful-run decomposition also lacks a rule when fewer than two successes remain. P-sel may have zero eligible runs; `censored_median([])` currently returns `NaN`, not a registered no-data outcome. See [§7.1, lines 262–270](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:262) and [statistics lines 164–172](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:164).

**6. Required changes before binding**

1. **Resolve confirmatory status.** Either classify all current Welch primary conclusions as approximate, retaining failure counts and decomposition, or register and validate a fixed procedure supporting the all-run mean claims. Zero observed failures cannot confer confirmatory status.
2. **Repair the power audit and §8.** Count every false label assertion jointly, including “within”; record simultaneous coverage; test the counters independently; regenerate the affected summaries. Correct the component-mean description and qualify the pilot failure-rate bound.
3. **Repair undefined coverage handling.** Undefined P-joint measurements must not establish lower coverer prevalence. Register the rule and add a failing-first test. Correct the “mostly coverers” sentence.
4. **Finish the execution and secondary-statistics contract.** Resolve the compositions, benchmark construction, learning references, interruption/condition eligibility and bootstrap/no-data cases identified above; correct the checkpoint count.
5. **Correct §15 and D207’s completion claim** to reflect these outstanding issues and the actual scope of the calibration fallback.

Optional suggestions: store analytic arm means explicitly in each power scenario; normalize or reject NumPy boolean inputs in `coverage_rule` (`np.bool_(True)` currently fails its `is True` count); replace the stale Holm-level wording at the top of `test_e3c_stats.py`.