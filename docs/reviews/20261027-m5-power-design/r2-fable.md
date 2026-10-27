**Verdict: revise, narrowly.** I accept the design in substance (the control, the estimand, the target, the criterion, the power plan). The pilot should not run as specified, because its seed families collide with M4e's audit family, and two rules it will inform are not yet written down. Those are small fixes to the pilot's note, and I do not need another round on them. The audit branch (Q3) should be redesigned before the power script, not before the pilot.

## Answers

**Q1. K\* = Rr, T and Rr as the only arms: accept, with three corrections.**

- **The wording "a swap accepted only if the 75 reciprocal pairs stay" is wrong.** `rewire` with `keep_recip` accepts a swap when `recip_delta` is zero, so a swap that breaks one pair and makes another passes (`scripts/memory_m4/m4d.py:219`). The estimand sentence already says "its count of reciprocal pairs", which is right. Fix the construction sentence to match.
- **Astra did not accept Rr.** Astra's point 3 accepted "T − K\*" with the global weight shuffle as primary and called T − Rr "a narrower question". Choosing Rr is your choice and a reasonable one. Do not cite Astra as endorsing it. Ask Astra directly this round.
- **Report the pilot's edge overlap split into reciprocal and non-reciprocal edges.** The reciprocity rule rejects most proposals (M4d's `blocks-summary.json`: about 52,000 attempts per 5200 accepted for Rr, against about 14,500 for R), so reciprocal edges move less. "Exact wiring" may in practice mean the placement of the non-reciprocal edges. The reader should see that number.
- The chain-length check should say whether the 10,400-swap block is the same chain continued (same seed) or an independent chain. I recommend the continuation. Overlap with T at 5200 and at 10,400 along one chain is the direct mixing check.

**Q2. The primary over all genomes, the secondaries, the qualifier: accept, with the qualifier's margin fixed by a rule now.**

- The primary is M4e's counted rate, a lower bound on each arm's true rate. The asymmetry should be stated: unresolved switches in T attenuate the contrast, unresolved switches in Rr create a false "raises". Only the second needs a guard.
- "To be set from the pilot" is a free parameter chosen after seeing twenty T − Rr host-draws. Write the derivation rule before (a) runs.
- A better qualifier is calibrated rather than a margin on the unresolved shares. Pilot (b) measures r, the share of unresolved genomes that settle as separate states at 100,000 ticks. M4e's second pass saw 2 of 56 settle that way. Then the sensitivity adds r × unresolved to each arm's confirmed count, at r's point estimate and its upper bound, and the reading is "raises, qualified" only if the direction fails at the adjusted counts. This is one assignment per host, so it scales, and it uses the project's existing `diffs` construction. The r = 1 envelope stays as a reported sensitivity. It cannot be the qualifier: at unresolved shares near 0.0035 per arm it would qualify every result near the target, however many hosts run.

**Q3. The audit: neither "not validated" nor M4e's revert. Treat the audit as a measurement with a pre-specified adjustment.**

The kill switch contradicts the budget. A rate inside the budget still produces transitions in a large audit:

| Audited per arm | Transition rate | P(at least one in that arm) | Upper bound after 0 / 1 / 2 transitions |
|---|---|---|---|
| 3000 | 0.0002 | 0.45 | 0.0010 / 0.0016 / 0.0021 |
| 3000 | 0.0005 | 0.78 | |
| 6000 | 0.0002 | 0.70 | 0.0005 / 0.0008 / 0.0011 |

With 3000 per arm and a 0.001 budget, one transition anywhere already breaks the budget, so "any transition voids" is the budget rule in disguise, and it voids a correct experiment nearly half the time at a rate five times below the budget. Proposed instead:

- **Pre-specify the adjustment.** Each arm's confirmed count is raised by its audit's point-estimate rate times its fading count. Zero transitions means no change. The reading is "raises" if it holds at the adjusted counts, with the upper bound stated beside it, as M4e did. It is "raises, qualified by the audit" if it holds only at the unadjusted counts. Only Rr's transitions can flip a "raises".
- **Size the audit to tolerate one transition inside the budget,** which is about 6000 per arm at 0.001. Fable's round-1 cost (a few seconds each) puts that under ten hours.
- **Pre-draw a second tranche** of audit ids per arm, run only if the first tranche finds a transition in that arm. That is the affordable "further classification". Reclassifying every fading genome of an arm is not: at 60 hosts and 1024 genomes it is about 60,000 genomes at M4e's second-pass cost, roughly 80 hours.
- **Use M4e's pooled audit as prior evidence.** Its eight arms audited 6354 fading genomes with zero transitions (`readings.json`, `audited_fading_per_arm`), a pooled one-sided bound near 0.00047. Pilot (c) adds 4500. Say in the plan what rate the design already excludes.
- The simulation then reports, per scenario and transition rate, how often the reading is qualified, not only how often it says "raises".

**Q4. The pilot: three fixes before it runs, two additions, nothing to drop.**

- **The seeds collide with M4e's audit family.** Confirmed in `scripts/memory_m4/m4e.py:355`: audit ids use 20261601 + 100(2h + d) + arm index, which spans 20261601 to 20263508. The proposed pilot seeds fall inside it:

  | Proposed | Collides with |
  |---|---|
  | Rr block, host 0 draw 0: 20261701 | M4e audit, host 0 draw 1, arm I |
  | Rr block, host 5 draw 0: 20261801 | M4e audit, host 1 draw 0, arm I |
  | large audit 20261801 to 20261803 | M4e audit, host 1 draw 0, arms I, U_LL, U_LH |

  Same seed means the same bit stream. The practical effect is negligible, but the repository's rule is that seed families do not overlap. Move both families above 20263508.
- **The tick-2000 and tick-22,000 states are not stored.** `classify_panel` keeps `end` in memory and the records hold classes and reasons only (`m4e.py:420`, `:435`). Pilots (b) and (c) must regenerate the first pass, and (b) the second, before continuing. The float32 hold is deterministic, so this is exact, but say it and count its time. It also gives a free check: the regenerated first-pass class must equal the record's for every genome continued. Register that check.
- **Write now what (b)'s outcome does to M5.** If most unresolved genomes settle by 100,000 ticks, M5's second pass on unresolved genomes should run longer. Fix the threshold and the consequence before (b) runs, otherwise the horizon is chosen after seeing which way those genomes lean.
- Commit the pilot note with the target 0.002 and its rationale before (a) runs. The pilot's T − Rr must not become the expected effect.
- (c) should exclude ids M4e already audited, or say that overlap is accepted.
- Run the pilot inside `wormwars.accounting` (rule 8).

**Q5. The power calculation: five things missing.**

- **The rule that turns the table into one pre-registered H.** "Fewest hosts under each scenario" is a table. State now which scenario and which host-variance source decide H, for example the constant-effect scenario under the larger of the pilot's T − Rr and M4e's T − K host components, with the sparse and one-ensemble powers reported as limits.
- **The Monte Carlo budget.** "Lower 95% bound at least 0.80" needs about 1500 to 2000 replicates per cell near the boundary, each with a 2000-resample bootstrap. On a grid of 59 H values, two D, two G, five effects and eight spreads that is tens of millions of replicates. Use a coarse grid, then refine around the boundary, and say so.
- **False "raises" under the control-side scenarios.** Report the rate at effect zero with switch-enriched unresolved genomes in Rr and with a positive transition rate in Rr. Those are the only scenarios where the nominal 2.5% can be exceeded, so they are the ones the pre-registration must show.
- **M4d's variance sources are first-pass only.** T − R and T − Rr there had no second pass and no audit, so their host components are not on M5's protocol. Keep them in the range, but label them.
- **Which Student-t under fixed strata.** The stratified bootstrap removes between-ensemble variance; the plain t over all hosts keeps it. The hull is conservative either way, but the pre-registration should name the t it uses, and the one-sided conservative t bound for the envelope should be validated against enumeration as you propose.

One smaller point: the cost model should take per-panel time distributions, not means, with Rr's from the pilot, since the second pass's time scales with each panel's unresolved count. The cap-exceedance probability depends on that tail.