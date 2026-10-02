**Verdict: proceed to pre-registration**, on condition that the budget is corrected in the design first (dated, rule 4), because the owner is being asked for a cap on numbers that do not add up. Everything else can be pinned in the pre-registration, which gets its own review. I ran nothing; the numbers below are hand estimates.

## 1. v1 must-fixes

All are resolved in substance. Four sub-items are not:

- **Maximum spawn distance (Fable 8):** not added. The spawn can be more than 18 cells from A along an axis, where `target_field` returns exactly zero, so leg 1 can start blind. The feasibility check is cited but I found no committed file for it (rule 5).
- **Dtypes:** the change map says "every per-world array's dtype declared", but the body of v2 does not declare any.
- **Movement-to-sensing latency (Astra 2):** the tick at which the brain first sees `at_x`, relative to the entry tick, is still unstated.
- **Replicates, disjoint selection and test worlds, stopping rules (Astra 7):** absent. This is acceptable only if the pre-registration carries them.

## 2. What checks out

- **Latch:** q* = ±1.915 and tanh q* = 0.9575 are right. With w_s = 3 the zero crossing takes about 0.73 τ. After a one-tick pass q is about +0.85 and climbs on its own, so a one-tick pass does switch it.
- **Start cue:** five ticks drive q to about 4.9, and it relaxes to 1.915 within a few ticks. A level of 3 is inside `input_max` = 5.
- **Gate:** L1's own comparator bias is 0 (`module.json`), so the active pair sits at offset 0 and matches L1 alone. The inactive pair sits at −3.83 with slope 0.0019, so its K_D is about 0.07, or 0.2% of the active one. The inactive CL and CR cancel push-pull, so the offset is near 0.
- **Component thresholds:** all four should pass with margin. The bias −1.915 against `b_max` = 2 leaves only 0.085 of headroom, which matters in Stage 2.

## 3. New problems in v2

1. **The budget is wrong by about a factor of two.** E4s-1's 0.2 h per run was at 8 worlds per strain (population 32, 1 000 generations, 300 ticks). Stage 2 uses 16 worlds and 600 ticks, which is 4× the rollout-ticks: about 0.8 h per run, not 0.4.
   - Stage 2 and random sampling come to about 6.4 h each, not 3.2 h.
   - B-task is "the same budget as Stage 2 plus Stage 3", but the table gives it 3.2 h, which is one stage at the wrong rate.
   - My total is about 26-35 h against a proposed 20 h cap.
   - Population and generations are never stated, so the table cannot be checked as written.
2. **w_s is not a genome parameter.** The equation feeds the levels straight into q, and the 9-neuron count confirms there is no relay neuron. That makes w_s an interface gain, which `Genome` (w, g, tau, bias) does not hold and `mutate` cannot touch. It has no bound, so "uniform over its bound's full range" is undefined. Either add a relay neuron (then the drive is at most 3·tanh, with a lag, and the switching numbers change) or declare new evolvable-gain machinery under rule 7.
3. **The "7 parameters" count is ambiguous.** It is 7 only if all four comparators share one bias and `at_a`/`at_b` share one antisymmetric gain. The tying needs stating.
4. **The hold test does not separate a latch from a leaky trace.** A decaying trace keeps its sign. With τ = 20 and a self-weight just under 1, the effective time constant exceeds 600 ticks. Stage 2's classification needs an analytic bistability criterion on (self-weight, bias), a hysteresis test, and a magnitude criterion such as the gate still passing its component thresholds after the hold.
5. **Stage 2 may be answered at generation 0.** With 7 parameters drawn over their full range, I would guess around 1% of random selectors work, so the census of 1 024 probably contains some. The design has the random comparator, but no outcome wording for "random sampling does as well".
6. **The carrier's circle is not a negligible baseline in every world.** Its radius is about 5.8 cells (0.35 / (0.2 × 0.30)), so its diameter of 11.7 sits inside the 8-14 separation. A circle through both discs alternates at roughly 105 ticks per loop, which could reach about 10 visits. Gate on the per-world distribution as well as the mean.
7. **Stage 3's "share of evaluations"** is unclear: is it part of fitness or measurement only?
8. **B-task's mutation scale** is unstated.
9. **Clamping q to a value** is new engine code (`silence` only clamps to 0). It should be listed in the engine change.

## 4. What the pre-registration must pin

- **Stage gates:** every "registered fraction" and "registered level", fixed before Stage 0 runs, or Stage 0 declared a pilot.
- **Evolution settings:** population, generations, elites, world-id blocks (selection, validation, test, disjoint), seeds, and the champion-selection rule.
- **Stage 2 outcomes:** the definition of "working selector", the latch / leaky / transient classification thresholds, the test statistic over the 8 runs, and wording for each outcome, including evolution ≤ random sampling.
- **The selector:** w_s's implementation, bound and tying; τ's initial distribution (uniform or log-uniform); which biases are shared.
- **The start cue:** whether it is excluded from the ledger, and that B-task, B-shared and L1-switch receive it identically.
- **Timing:** the signal latency; substeps (32 here, where the config default is 8); how K_D is measured (step size, carrier turn command 0 or 0.2, which ticks).
- **Geometry:** the maximum spawn distance, and the feasibility check committed.
- **B-task:** its mask, input routing, initial distribution, mutation scale and budget.
- **B-shared:** engineered or evolved.
- **Budget:** the corrected table, the pre-stated shrink order, and the cap as set by the owner.
- **Engine check:** the declared worlds and compositions; dtypes for every per-world array.