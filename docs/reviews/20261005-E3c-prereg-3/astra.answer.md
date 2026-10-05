**Verdict: revise, narrowly.** The permutation test is sound for the registered distributional claim, and the main calibration objection is resolved. Two corrections remain: undefined coverage measurements still produce a false component conclusion, and §8 overstates when Q1 is decisive.

I checked commit `65cd529` on `roadmap`. All **29 statistics/power tests pass**. I reproduced the entire `power.json` exactly in memory, including all **15,040 comparisons against `readings`**. Independent permutation checks covered ties and unequal sample sizes. The four pinned file hashes and all 512 P-joint genome hashes match. No files were changed.

**1. Draft 2’s required changes are mostly taken correctly.**

| Previous requirement | Assessment |
|---|---|
| Astra: resolve confirmatory status | **Taken.** All Welch margin labels are approximate; the observed-failure gate is withdrawn. [§7.1, lines 240–258](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:240). |
| Astra: repair the power audit | **Taken.** The counter includes false direction, “beyond,” “within,” and “no relevant difference”; joint coverage and analytic means are recorded. I independently checked the counter’s logic. [Power script, lines 160–207](/D:/Claude/random/wormWars/scripts/e3c_power.py:160). |
| Astra/Fable: repair undefined coverage handling | **Partly taken.** The overall classification becomes “mixed,” but the separately reported P-joint comparison remains wrong. Details below. |
| Astra: execution and secondary-statistics contract | **Substantially taken.** Cut compositions, learning references, reading-specific eligibility, whole-stage reruns, trails-off scope, bootstrap level, decomposition/no-run cases and 21 checkpoints are specified. [§5, lines 171–211](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:171), [§7.1–7.2, lines 283–332](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:283). One benchmark clarification is suggested below. |
| Astra: correct the completion claim and fallback attribution | **Taken.** The dated corrections accurately identify the previous errors. [§15, lines 638–644](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:638), [D207 correction, lines 6744–6749](/D:/Claude/random/wormWars/DECISIONS.md:6744). |
| Fable: require `g-e` to pass | **Taken.** Training requires passage; any mismatch stops E3c and requires reconsideration of reuse. [§5, lines 166–170](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:166). |
| Fable: disclose the failed-run count’s blind spots | **Taken.** Above-threshold failures, the approximately 8% missed component draws, and unsimulated partial outcomes are explicit. [§7.1, lines 283–295](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:283). |

**2. The exact permutation decision is sound, with the interpretation stated in §7.1.**

- **Null and claim:** Under joint exchangeability, exhaustive label permutation gives finite-sample valid inference. Independent runs drawn from the same distribution satisfy that null. Rejecting it supports the distributional claim; equal means alone do not satisfy the null. The Q2 example with unequal spreads is therefore legitimate. This matches the independent-sample null described in [SciPy’s permutation-test documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.permutation_test.html). See [§7.1, lines 245–251](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:245).

- **“X higher”:** Acceptable **as explicitly defined: the observed sample mean is higher**. It supplies no calibrated conclusion about population-mean ordering or stochastic dominance. The saved wrong-direction rate of 0.1082 makes that distinction consequential. [§8, lines 437–442](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:437), [power.json, line 10605](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:10605).

- **Bonferroni:** Correct. Testing each distributional null at 0.025 controls familywise error at at most 0.05; sharing S-mod does not invalidate that bound. Suppressing Q1 when its floor guard fails can only remove rejections. [§7.1, lines 244 and 260–261](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:244).

- **Implementation and ties:** `permutation_p` enumerates every allocation of observation indices, computes the difference in means, and counts absolute statistics at least as extreme as observed. Repeated values correctly retain their allocation multiplicities. Exhaustive enumeration needs no Monte Carlo “+1” adjustment. The `1e-12` tolerance includes numerical ties appropriately at the registered scale. I independently checked 48 tied integer examples, including 8-versus-6 and interrupted-run sizes, and conditional null distributions with ties. All agreed. [Statistics, lines 100–113](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:100).

- **What “exact” means:** Error control is **at most** 0.025, not necessarily a rejection probability equal to 0.025. Discreteness and ties can make it conservative. “Whatever the failure rates” remains conditional on exchangeability; it does not promise mean-null calibration when outcome distributions differ. The text already states that qualification, but the suggested wording below would make it harder to misread.

A difference-in-means statistic is not sensitive to every distributional alternative. Consequently, “no difference detected” must remain exactly that; it cannot establish identical distributions. The current label respects this.

**3. The power analysis faithfully implements the registered procedure. §8’s numerical summaries check out, but one conclusion is too broad.**

The simulation shares S-mod between contrasts, retains eight P-joint runs under the cut, applies the floor guard, and uses the registered exact decision and approximate margin rules. The complete artifact reproduced exactly.

The principal figures agree:

| Quantity | Verified value |
|---|---:|
| Q1 rejection range across 93 identical-distribution scenarios | 0.0188–0.0310 |
| Base Q2 rejection at equal means, unequal spreads | 0.0420 |
| Base Q2 power at −1 / +1 visit, Q1 = 0 | 0.7598 / 0.7576 |
| Corresponding six-S-run power | 0.6110 / 0.6184 |
| Maximum base no-failure joint false margin assertion | 0.0492 |
| Base no-failure joint interval coverage range | 0.9478–0.9592 |
| Maximum joint false margin assertion / minimum coverage | 0.4720 / 0.5232 |

These support [§8, lines 415–458](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:415); the worst mixture case is recorded at [power.json, lines 21405–21410](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:21405).

However, **“Q1 is decisive if no run fails” is wrong without the narrow-spread qualification**. In the saved no-failure scenario with S spread 0.4 and both true contrasts zero, Q1 produces:

- “unclear”: **0.8226**;
- “no relevant difference”: **0.1500**.

That directly contradicts the unqualified conclusion at [§8, line 461](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:461). The counterexample starts at [power.json, line 22496](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/power.json:22496). Absence of observed failures also must not substitute for an assumed no-failure population model.

**4. The remaining code defect concerns the separately reported coverage components.**

This input:

```python
coverage_rule({
    "s_mod": [True] * 8,
    "s_dense": [True] * 8,
    "p_joint": [None] * 8,
})
```

returns:

```python
{
    "coverers": "mixed",
    "s_arms": "mixed",
    "p_joint_lower_than_both": True,
    "shares": {"s_mod": 1.0, "s_dense": 1.0, "p_joint": 0.0},
    ...
}
```

The overall label is repaired. **The component conclusion is not:** unmeasured P-joint champions still establish a lower share. Also, fully measured S arms lose their “high” classification solely because P-joint is undefined. These outputs matter because [§7.3, line 371](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:371) expressly requires them to be reported separately.

The causes are the denominator at line 177, the global undefined check at line 179, and the unconditional comparison at line 187. [Statistics, lines 174–195](/D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:174). The new test checks only the overall label and undefined count, so it misses the remaining defect. [Test, lines 186–191](/D:/Claude/random/wormWars/tests/test_e3c_stats.py:186).

The staged implementation/review arrangement in §0 otherwise remains acceptable; absent formal-stage code is not itself a blocker.

**5. Required changes before binding:**

1. **Finish the coverage repair.** Keep the overall result “mixed” when any required champion is undefined. Compute the S-arm component from the S arms alone. Return an explicitly undefined P-joint comparison when required shares are unknown; do not report undefined champions as an observed zero share. Add tests asserting these component outputs. Also clarify §7.3’s precedence: equal low shares produce “not supported,” despite line 369’s broad statement that equal/exceeding P-joint shares are included in “mixed.”

2. **Qualify §8’s Q1 conclusion.** Limit it to the narrow-spread, no-failure base model and distinguish practical-margin resolution from exact distributional detection. The saved spread-0.4 sensitivity case should prevent the present blanket claim.

Optional suggestions:

- Make the label self-contained: **“distributions differ (exact test); observed mean higher for X.”**
- Say **“finite-sample type-I error at most 0.025 under exchangeability”**, and state the absolute-statistic tail definition explicitly.
- Clarify the benchmark projection: [§9, lines 485–486](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:485) times checkpoint/champion chunks on 256 mazes, whereas their formal compositions use 128. Specify either 128-maze benchmark subsets or the conversion from those timings to the formal projection.