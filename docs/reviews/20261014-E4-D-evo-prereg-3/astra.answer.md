**Verdict: bind as is.** All substantive draft-2 findings are resolved correctly. Draft 3 can bind at the next pushed commit once both reviewers agree. Only wording notes remain.

1. **Resolved — draft-2 #1, §5:** The dependency table correctly makes S depend on L’s triggering report, independently of F. No fix needed.

2. **Resolved — draft-2 #2, §§7.2/10; `evo_stats.improvement`:** Correct paired-difference range, grid, count validation, one-sided t lower bound and strict `LB > 0`. Chance comparisons remain separate. No fix needed.

3. **Resolved — draft-2 #3, §8; `e4d_evo_power.py`:** Worst/best selection correctly considers only tied validation winners and chooses their lowest/highest latent probability. The reported numbers match `power.json`. **Wording note:** qualify “by at most 0.004” as “in these σ = 0 simulations”; this is an estimated sensitivity result, not a universal bound.

4. **Resolved — draft-2 #4, §§5/10:** Cross-stage and rerun environment equality, validation composition and checkpoint compositions are explicit, with refusal tests required. No fix needed.

5. **Resolved — draft-2 #5–7, §8:** Near-E-G failures are correctly described as a modelling assumption. Earlier resolved findings remain resolved. **R = 32 remains acceptable** under the conditional power wording; my preference for 40 remains nonblocking.

6. **Resolved — Fable’s implementation findings, §§0.3/5/10:** The additive `TrialResult` authorization is sufficient, with an explicit zero-tolerance equivalence check. `check` exercises the formal evaluation assertions before training. Replay seeds, factors, initialization, maze IDs and index-10 snapshot agree with the pilot code. These checks still require implementation and review after binding, as specified.

7. **Low, wording only — §9:** The caps sum correctly to 15.5 hours, and the revised L cap supports the stated pilot-rate rerun. However, “At most 15.5” overstates enforcement: `CapClock` checks before rollouts, allowing an in-flight rollout to overrun. Say **“nominal caps total 15.5 hours.”** No cap or stopping-rule change needed.

8. **Low, cosmetic — §10:** Add the missing `cx` argument in `control_genome(E-G, cx, "comparator", 0.5)`, matching §3.

**Verification:** All 31 statistics tests passed; independent paired-boundary/refusal and tie-selection checks passed. All six pinned hashes and the population digest matched, including hashes recomputed from population arrays. Timing projections matched. I did not rerun the full power grid or GPU stages.