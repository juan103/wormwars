**Revise.** Several v1 fixes are implemented, but “every must-fix adopted” is not accurate. The main remaining problems are the settling diagnostic, incomplete result retention, and stale compute-record export. Q1b also contains a definite ensemble-filtering bug.

This was a static review of `0916f41`, including both v1 reviews, the runner, tests, outputs, and relevant initialization/accounting code. I ran no simulations, tests, or statistical recomputations. The original local per-genome measures are absent from this worktree.

My v1 must-fixes stand as follows:

| V1 requirement | V2 assessment |
|---|---|
| Preserve deletion batch composition | **Implemented:** formal batches contain one 2,048-genome deletion. An empty deletion is included and compared exactly, although only after the entire deletion sweep. |
| Exclude invalid P4 from percentiles, leads and permutation summaries | **Implemented for those calculations:** explicit validity flag, missing P4/positions, and valid-only selection. Non-finite serialization still needs attention below. |
| CPU smoke, fixed formal population, cumulative cap and retained results | **Partly implemented:** CPU smoke, population restriction and cumulative `CapClock` exist. Retention and committed accounting remain incomplete. |
| Narrow Q4 interpretation and add eligibility/convergence checks | **Partly implemented:** wording and absolute eligibility floor are corrected. The convergence check does not measure what the plan says. |
| Separate deletion outcome classes | **Implemented:** P4-only, response-only and joint classes, with the threshold caveat. A new no-effect interpretation is incorrect. |
| Correct factual and causal wording | **Implemented:** rank, response ranges, residual-SD caveat and partial input-path wording are corrected; Q5 now distinguishes independent and paired designs. |

Fable’s eight-seed requirement is also implemented. I checked that magnitude permutations use a private generator, so Q3 and paired Q5 preserve the intended signs, biases and time constants. Its per-genome retention requirement is only partially implemented.

**Must-fixes**

1. **Replace the endpoint-only settling check.**  
   In [history_full](/D:/Claude/random/wormWars-p4/scripts/p4m.py:433), `hold_change` and `end_change` compare two states. They do **not** take the largest change over the intervening window. A trajectory can move substantially and return near its initial state, passing this check despite oscillating—the alternative Q4 specifically needs to distinguish.

   There is also an indexing error: with `after=300, window=10`, `v_end` is captured before step 290, so the comparison is between states 289 and 300, spanning **11** ticks.

   Define and implement a statistic that examines every tick in the declared window, separately for both trajectories and starting holds. Add a regression case where the endpoint returns to its earlier value after substantial intervening movement. The current test checks measurement timing, not settling.

2. **Actually retain completed measurements and the promised per-genome arrays.**  
   The omissions are visible in the command implementations:

   - [Synapses](/D:/Claude/random/wormWars-p4/scripts/p4m.py:394) and [weights](/D:/Claude/random/wormWars-p4/scripts/p4m.py:551) keep results in memory until completion. Neither writes partial results or per-genome arrays.
   - [Lesions](/D:/Claude/random/wormWars-p4/scripts/p4m.py:349) checkpoints summary rows, but writes its main per-genome arrays only after all follow-ups. Follow-up arrays are discarded.
   - [Decay](/D:/Claude/random/wormWars-p4/scripts/p4m.py:517) checkpoints summaries, but saves curves only after the entire panel. It discards per-genome steady contrasts, settling diagnostics and saturation diagnostics.

   Thus a cap stop can lose completed work, and even successful runs discard measurements needed for the promised diagnostic reanalysis. Save each completed condition/graph’s summaries and raw terms incrementally, including follow-ups. This remains an unresolved v1 requirement.

3. **Export accounting after the current attempt has been finalized.**  
   [finish](/D:/Claude/random/wormWars-p4/scripts/p4m.py:172) aggregates and copies the compute record while still inside `run_script`. The current attempt file is written only when the enclosing [accounting context exits](/D:/Claude/random/wormWars-p4/wormwars/accounting.py:273).

   Consequently, `compute-record.json` omits the current command; on a first attempt it can be absent altogether. On failure or cap exhaustion, `finish` is never reached. The local aggregate is subsequently updated correctly by `run_script`, but the experiment-folder copy remains stale.

   Copy the aggregate after accounting finalization, including failure paths. Test both a first successful command and a cap-stopped command.

4. **Fix Q1b’s SH filtering and regenerate its output.**  
   [cmd_tails](/D:/Claude/random/wormWars-p4/scripts/p4m.py:244) uses `startswith("SH-")`, which includes SH-route, SH-class, SH-mirror and SH-recip. The consequence is already visible: [tails.json](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/tails.json:21) reports **640 graphs for SH**, instead of 128.

   Use the exact ensemble-membership logic already implemented in `ensemble_rows`. The reported SH reliability and concentration statistics are pooled-ensemble statistics, not SH statistics. Add a regression case containing names from all five ensembles, and record the correction openly.

5. **Narrow Q1’s new interpretations to what was calculated.**  
   The corrected numerical ranges match `tradeoff.json`: response/median **4.699–7.087**, response/maximum **1.553–2.690**, log-log slopes **0.834–0.956**, and common-response correlations **−0.3798 to −0.6903**. The residual-SD caveat is appropriate. The following deductions in [Q1](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/PLAN.md:52) are stronger than those calculations support:

   **The common-response correlation does not establish “not only the ratio’s arithmetic.”** A separate response measure can correlate with P4’s denominator and inherit a negative association with the ratio. This check removes literal reuse of the denominator as the horizontal variable; it does not rule out denominator-mediated association.

   **High split-half P4 reliability does not directly measure estimation-error contributions to the P4–response association.** It supports reproducible between-graph differences in P4. Say that a noise-only explanation is less plausible, rather than declaring estimation noise excluded.

   **The tail statistics concern numerator and denominator contributions, not a distribution of P4.** The code sorts their contributions separately. The 40% and 38% therefore need not come from the same genomes. Furthermore, the ensemble “about 19%” statistic is calculated for the **numerator only**. These results establish concentrated contributions, not that a particular minority drives N2’s high ratio. To make that claim, examine a common selected subset and the ratio with that subset removed. Q4’s current numerator-only concentration statistic does not directly supply this check.

6. **Remove the new claim that an empty deletion screen establishes no neuronal dependence.**  
   [PLAN.md:93](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/PLAN.md:93) says that if no deletion enters a class, “P4 in N2 would then not depend on any single neuron or pair.”

   That does not follow. Deletions can change P4 substantially without crossing these thresholds; some neurons are excluded; invalid measurements cannot establish absence of dependence. Say: **“No tested valid single or bilateral-pair deletion removed the unusual elevation under these thresholds.”**

**Suggestions**

- Move the empty-deletion equality check immediately after that measurement. Currently an unsuccessful check can consume the entire sweep, and cap-stopped partial results never reach it. Consider enforcing the declared reproduction tolerance on Q4’s per-graph comparison; currently discrepancies are merely recorded.
- Tighten missing-value handling. `p4_of` retains non-finite numerator/denominator values, and `json.dumps(r)` in the test permits `NaN` by default. Test non-finite inputs with `allow_nan=False`. Conditional proportions with no eligible or remaining genomes should be missing, with their counts reported, rather than manufactured as zero.
- Update the compute projection for the added matched gaps-off panel: 81 extra histories at 12.7 seconds add approximately **0.29 hours**. Q3 now has 20 histories before its reproduction gate. The stated 2.9-hour total appears to omit this added work.
- Correct “the weakest associations are in the two routing-constrained ensembles”: in 03r, SH-class’s association, −0.365, is weaker than SH-mirror’s, −0.447.
- Record actual device and genome count in every output, plus the identity/hash of Q1b’s local inputs. Its current stamp identifies a dirty v1 checkout, not the measurement files consumed.

**03m plan: revise**