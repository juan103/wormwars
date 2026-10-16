**Revise.** I checked `6e948d7ba5fd22592a5b55a39d3a41611620d65e` on `roadmap`, the cited documents and code, the committed summaries, and the local RIA/AIY per-genome arrays. The main blocker is Q-B’s underestimated uncertainty. Several decision rules and outcome statements also need correction.

1. **Q-B is materially less powered than claimed.** [DESIGN.md:128](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:128), [DESIGN.md:270](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:270).

   I independently ran 10,000 paired percentile-bootstrap resamples of intact, RIA and AIY from `runs/p4m/lesions-per-genome.npz`, recomputing ratios of means. Their original means exactly match the committed JSON.

   | Deletion | Response-cut SE | ΔP4 SE | 90% percentile interval for ΔP4 |
   |---|---:|---:|---:|
   | RIA | 0.0189 | 0.00746 | −0.0075 to +0.0170 |
   | AIY | 0.0300 | 0.01166 | **−0.0236 to +0.0151** |

   AIY does not establish equivalence within ±0.02 even at unadjusted 5% using this procedure. Its limiting bootstrap tail is approximately 0.093. RIA’s limiting tail is approximately 0.020, also above the first two Holm thresholds. These are diagnostic calculations on old data, not prospective power estimates, but they directly contradict “Q-B … many bootstrap SEs from the thresholds” and the expectation that Q-B takes a strict Holm position.

   **Fix:** calculate prospective power using the *paired deletion-change uncertainty*. Increase Q-B’s genome sample or explicitly accept low power. Additional independently seeded batches of 2,048 could preserve the proposed execution composition; register their pooling and pairing. Do not widen the margin merely to obtain a pass.

2. **The Q-B conjunction is appropriate, but its test is underspecified and the fixed “5%” wording conflicts with Holm.** [DESIGN.md:129](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:129).

   The correct structure is
   `p_equivalence = max(p_lower, p_upper)`, followed by the maximum across both equivalence tests and both response-cut tests. That is four component p-values after combining each TOST, or six elementary one-sided tests. No additional correction within this intersection-union claim is needed.

   However, “tested … on the bootstrap” does not specify how a p-value is constructed. Percentile inversion, basic intervals and studentized tests are different procedures. Flooring a value at `1/10001` does not establish its calibration.

   **Fix:** register the bootstrap algorithm, actual seed, paired resampling indices, ratio-of-means estimators, invalid-resample handling and p-value formula. Apply Holm to the resulting question p-value; do not separately pass equivalence at fixed 5%. At component level α, percentile TOST corresponds to a central `1−2α` interval, so 90% intervals alone cannot establish a stricter Holm result.

   For §9.3: **40% is a defensible substantive cut; ±0.02 is a defensible proposed tolerance, but needs a scientific interpretation.** “Three times intact P4’s SE” is neither that interpretation nor the uncertainty relevant to deletion differences. Say “approximately proportional”; exact proportionality is not tested.

3. **Keep Holm over the four primaries, but complete the missing-data rules and correct Q-C’s denominator.** [DESIGN.md:169](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:169), [DESIGN.md:257](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:257).

   For §9.1: **one four-question family is appropriate.** Splitting it into four families would abandon the advertised familywise protection. Maximum-p intersection-union tests over ensembles are also appropriate under the stated exchangeability nulls; dependence between questions does not invalidate Holm.

   The quoted 128-graph cutoffs are correct. The omitted `0.05/3` cutoff permits `r ≤ 1`.

   Q-C nevertheless uses `(r+1)/257` while allowing only 240 valid permutations. That denominator is wrong when `n < 256`; use **`(r+1)/(n+1)`**.

   **Fix:** retain unavailable primary questions in the four-member family with p=1, as the existing report already does for incomplete signals ([report.py:8](/D:/Claude/random/wormWars/wormwars/exp03/report.py:8)). Define validity separately for paired gaps-off changes, retention ratios and pre-tanh ratios, including valid N2 measurements for each. Report planned, attempted, completed, invalid and valid counts separately.

4. **The pass-probability sketch is not the probability of passing this procedure.** [DESIGN.md:262](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:262).

   Its arithmetic is plausible *conditional on* a 1.5% exceedance probability: for 128 draws, `Pr(r≤5)=0.9869`; for 64, `Pr(r≤2)=0.9283`. But Q-D gets the 5% Holm threshold only in the appropriate ordering after the earlier tests pass. With Q-B’s observed uncertainty, Q-D may instead face 2.5%, requiring `r≤2`; at that same 1.5% tail probability, its SH-recip gate passes only **0.6985** of the time.

   I also could not reproduce the asserted 1.5% tail from a conventional fit to the 16 SH-recip log-retention values: using their sample log SD gives approximately **0.67%** at tick 30. This does not prove the author’s calculation wrong—the fitting method is unspecified—but it makes the sketch unauditable.

   **Fix:** commit the calculation, specify fitting conventions, and simulate the actual Holm ordering with shared N2 uncertainty, Q-B’s joint uncertainty and sensitivity to graph-tail assumptions. Label rank-gate probabilities separately from whole-procedure power.

5. **Q-A is a fair primary comparison, but its wording overstates what passing or failing establishes.** [DESIGN.md:98](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:98).

   For §9.4: **keep the change comparison primary.** It directly tests differential sensitivity to removing gap junctions. Gaps-off levels answer the separate question of residual distinctiveness and can remain secondary.

   A rank pass can tolerate several null graphs beyond N2; it does not establish “lower than every … graph.” Nor does the test require either change to be positive, despite “raises” in the pass wording. A failed test does not establish that N2’s change “is not lower.” Finally, calling this dependence of an existing “lead” needs qualification if intact P4 fails to replicate.

   **Fix:** use “N2 showed an unusually small ΔP4 relative to each ensemble,” give counts and changes in ensemble gaps, and condition the “lead narrows” interpretation on the observed intact lead. Failure should say the registered criterion was not met. Retain the ceiling caveat; P4’s definition does not itself impose a ceiling of one.

6. **Tick 30 is legitimate, but Q-D tests retained separation at one time, not a decay rate.** [DESIGN.md:182](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:182).

   For §9.2: **keep tick 30 if that is the scientific target.** Choosing it from exploratory data is acceptable with the disclosed fresh confirmatory sample. An average over 0–50 is another defensible estimand, but is not intrinsically less selected after viewing the curves.

   Greater retention can reflect a plateau, transient shape or slower relaxation. The single endpoint cannot separate these. It also does not show that every sampled null graph, or every N2 genome, retains less.

   **Fix:** make the pass statement “N2 retained an unusually large fraction of its initial history difference at tick 30 relative to each ensemble.” Keep the curve and tick-300 result. Explicitly define the retention denominator’s validity rule and the secondary settling calculation as the maximum neuron range over the final ten sampled ticks, requiring both histories to settle.

7. **Q-E’s causal verdicts are unsupported in both directions.** [DESIGN.md:209](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:209).

   The proposed measure changes the final observation map. It does not remove tanh from recurrent dynamics: [brain.py:476](/D:/Claude/random/wormWars/wormwars/brain.py:476) still applies tanh before chemical transmission.

   A pre-tanh pass shows robustness to that observation-map change; it does not show that saturation makes no contribution. A failure can arise from uncertainty, an effect-margin failure or an invalid denominator; it does not establish dependence on nonlinearity.

   **Fix:** use “P4 distinctiveness persists on the pre-tanh read-out” versus “pre-tanh distinctiveness was not established,” with the actual failing gates. Preserve inconclusive and withheld outcomes.

8. **The proposed equivalence check does not cover all new measurements.** [DESIGN.md:234](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:234).

   The two-row approach is structurally sound: `Brain.step` operates on `[S,B,N]`, broadcasts strain parameters and has no interaction across B rows ([brain.py:434](/D:/Claude/random/wormWars/wormwars/brain.py:434)). But the existing read-out explicitly selects `v[:,0]` ([measures.py:84](/D:/Claude/random/wormWars/wormwars/exp03/measures.py:84)); adapting the probe requires care.

   Agreement of two aggregate intact ramp-end means cannot validate paired per-genome bootstrap inputs, tick-30/tick-300 trajectories, pre-tanh values, settling or intervention conditions.

   **Fix:** retain the declared relative `1e−5` aggregate check and add declared checks for those outputs against the sequential implementation on old inputs, including representative gaps-off, deletion and permutation conditions. Include row-swap/isolation and empty-deletion checks. Register near-zero tolerances and stop-on-failure behavior before testing. Either use and test `replay_mode()` for exact-repeat claims or qualify [DESIGN.md:243](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:243).

9. **The quoted exploratory numbers mostly check; the permutation count is wrong.** [DESIGN.md:14](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:14), [DESIGN.md:165](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:165).

   Recomputed from the committed JSON:

   - Gap ΔP4: N2 **0.01440515**; null range **0.05079739–0.14317276**; five gaps-off null graphs exceed N2.
   - RIA: response cut **61.719%**, numerator cut **61.517%**, ΔP4 **+0.00491985**.
   - AIY: response cut **52.837%**, numerator cut **53.057%**, ΔP4 **−0.00434289**.
   - RIA and AIY are first and second among 95 pairs; ASE is third at **31.063%**.
   - **94/95** pair deletions have `|ΔP4|<0.02`; AIZ is the exception.
   - **59/64** permutations have P4 below N2 in each genome design. All permutation responses are below the pooled null maximum.
   - N2 exceeds all 80 null graphs at every recorded tick from 5 through 50. At 300, the exceptions are **SH-10007 and SH-mirror-40014**.
   - The approximately 60% retained excess is **58% for the paired design**, versus 60% for the independent design.

   **Fix:** replace “all 128 permutations” with **“64 permutations evaluated under two genome designs.”** This was explicitly corrected in 03m. For Q-C’s confirmatory claim, use “response unusually high relative to magnitude permutations”; the rank test does not require beating every permutation or establish a complete account of response size.

10. **Matched controls are promised but not specified.** [DESIGN.md:35](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:35), [DESIGN.md:145](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:145).

    Ranking RIA and AIY among all bilateral pairs is not a degree-matched comparison. Thus “takes up all … suggestions” is inaccurate. The null-graph deletions and permutation factorial are useful descriptive additions, but do not supply that missing match.

    **Fix:** register a structural matching rule, eligible controls, tie-breaking and comparison summary before fresh measurements—or explicitly decline matched controls and narrow the specificity claim. Specify the factorial interaction contrast if it will support a statement about weight placement acting through these neurons.

11. **Freshness is plausible; the audit and cap policy need operational detail.** [DESIGN.md:76](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:76), [DESIGN.md:245](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:245), [DESIGN.md:294](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:294).

    The proposed base seed ranges differ from the old ones. I found no collision between the 641 planned N2/ensemble hashed genome seeds and the checked historical ensemble/N2/03m streams. However, a new salt alone does not guarantee distinct seeds: `genome_seed` truncates to 31 bits ([measures.py:22](/D:/Claude/random/wormWars/wormwars/exp03/measures.py:22)).

    **Fix:** audit actual derived seeds, substitutions, smoke streams and prior secondary permutations; check content duplicates within the new panel as well as against old panels. Register deterministic collision handling.

    The timing arithmetic supports roughly **7.1–7.2 hours of probes**, plus approximately **0.4 hours of CPU build** if included. D285 records the short-probe timing, not validation of the full workload. `CapClock` counts accumulated wall time, not GPU kernel time ([registration.py:123](/D:/Claude/random/wormWars/wormwars/registration.py:123)).

    Keep the 10-hour cap, but define included work, restarts, failed attempts and batch-boundary overrun. Move the 93 descriptive deletions and permutation factorial behind the primary ensemble measurements. Distinguish administrative stopping from invalid observations, preserve the four-question Holm family, and prohibit outcome-dependent continuation.

12. **For §9.5, readers need a complete decision and audit trail for either outcome.** [DESIGN.md:252](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:252), [DESIGN.md:274](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:274).

    **Fix:** specify publication of raw and adjusted question p-values, every component gate, effect estimates and intervals, exclusions, partial-run counts, and pass/fail/withheld wording. Preserve per-genome arrays with hashes, and pin configuration, stimulus/interface inputs and measurement code across resumes. Secondary nominal tests should be explicitly outside any study-wide error guarantee.

    I did **not** run GPU simulations, verify the timing experimentally, execute a new two-row implementation, or validate future collision/cap enforcement. Those remain pre-registration implementation checks; the design currently supplies intentions rather than an executable procedure.