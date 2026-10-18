**Revise.** Before pilot-dev, fix partial reporting, preserve completed search states, and account for full-history replay controls in the projection. These are bounded driver fixes; I would keep the current search budget and round-B settings for pilot-dev.

I verified HEAD is `a5760c43c373d7b6d88751d27db3262424de941a` on `roadmap`. This was a static review: I read code, tests and records; I did not execute tests or experiments or modify files.

1. **High — partial reporting still fails in the cap-stop case it is meant to handle.**

   [`stage_full`, line 676](D:/Claude/random/wormWars/scripts/e03a.py:676) puts only `target_brains` into `progress`. Its `p`, `setting` and `plan` appear only in the successful return at line 727.

   Consequently, if one target-brain finishes and the next hits the cap, the failed record contains completed rows but no `p`. [`stage_report`, line 866](D:/Claude/random/wormWars/scripts/e03a.py:866) then evaluates `resolution(rows, full["p"])` and raises `KeyError`.

   There is a second obstruction: line 825 requires a completed `probe`. With the documented stage order, a cap reached during `full` prevents that later GPU stage from completing, so the report cannot expose even the measurements already available.

   **Required:** put the metadata into `progress` before starting searches. Separate partial scientific reporting from budget authorization: emit completed measurements and explicit missing-work information without inventing rates; withhold the projection and 32-world permission when their inputs are missing. Add a cap-stop regression covering a completed target followed by an interrupted target.

2. **High — completed searches and anatomical results are still disposable.**

   [`stage_full`, line 687](D:/Claude/random/wormWars/scripts/e03a.py:687) waits for every search for a target, including the 200-generation searches, before extracting anything.

   A concrete failure case: stop at generation 150. All thirteen ordinary searches finished at generation 100, and both long searches have generation-100 snapshots, but none of those states enters the failure record or a local file. The entire current target’s search output is lost.

   Even successful execution saves `states` as **labels**, not states, at line 716. The weight vectors, partner masks and aggregate rankings are not retained. Thus a subsequent correction to an anatomical diagnostic cannot be applied to saved search output without rerunning simulation.

   The new library snapshots are correctly copied after the specified generation, including swaps; they simply remain in memory.

   **Required:** retain completed search states and long-search snapshots locally as they become available, plus periodic progress for ongoing searches. Save final rankings or enough state to regenerate them. Record whether final-world evaluation has completed separately. This does not require implementing full resumability.

3. **High for budget decisions — the projection omits expensive replay controls and still mixes compositions.**

   [`stage_probe`, line 794](D:/Claude/random/wormWars/scripts/e03a.py:794) runs a full-history replay control for every evolved brain, but passes `kind=None`, discarding its individual timing. [`stage_report`, line 831](D:/Claude/random/wormWars/scripts/e03a.py:831) prices only six plain-like conditions and four bounded replay conditions.

   A full-history control is materially different from a bounded replay. With 300 ticks and `L=10`, it replays

   `10 + 20 + … + 290 = 4,350`

   additional neural ticks: **4,650 neural ticks including the ordinary episode**, versus 300 ordinarily. This is not a claim of 15.5× wall time, but it demonstrates why silently omitting the control is unsafe.

   **Required:** retain its measured time and specify the number of these controls in the projected protocol. If formal validation will use fewer controls than the pilot driver, state and justify that scope explicitly.

   The workload-unit corrections otherwise look right: selection and validation are separated, scans use `measure`, bounded probes use measured condition times, and pilot-check has fourteen evolutions.

   Composition remains an extrapolation. The `search` category combines 540-strain MIP batches, their 72-strain extension tails, and 468-strain NIP batches. Cuts and 32 worlds change composition again. Lines 870–871’s claim that formal target-brains have “the same shape” is therefore inaccurate. Preserve composition-specific timings and label unmeasured scaling assumptions; wider evolution batches are not *demonstrated* conservative merely because they are wider.

4. **Medium — two anatomical diagnostics need correction or an explicit definition.**

   **Turnover remains shifted.** [`_diagnostics`, line 606](D:/Claude/random/wormWars/scripts/e03a.py:606) passes only post-generation masks to `_turnover`. Consequently, a 100-generation search compares generations 1→11, …, 81→91, omitting 0→10 and 90→100. Q’s timestamps are now correct; turnover’s are not. Include `initial_cold` and compare 0→10→…→100, retaining the intervals if they will inform plateau thresholds.

   **The mirror-zero subset is an intersection across types.** [`_descriptive`, line 657](D:/Claude/random/wormWars/scripts/e03a.py:657) keeps candidates only when **all three** mirror scores are zero. That excludes, for example, an incoming-edge candidate whose incoming mirror score is zero but outgoing mirror score is positive.

   I read the design’s type-specific rankings as requiring the zero subset separately for each type, followed by averaging scoreable type AUCs. The prose does not explicitly settle this cross-type intersection, so this is an interpretation issue as well as a likely implementation mismatch. Either implement per-type subsets or explicitly name and justify the intersection. Report subset sizes, positive counts and excluded types.

   `null.subset_recovery` itself correctly computes recovery for the common mask it receives and returns `None` when nothing is scoreable.

5. **Medium — the planted-check summary misstates chance, and “upper bound” is unjustified. Keep the current pilot-dev search settings.**

   The recorded mean perfect-signal ranges support the reported approximately 33–52% at generation 100 and 46–66% at generation 200. However, the recorded chance levels are:

   | Target | Chance Q |
   |---|---:|
   | AIYL | 3.61% |
   | RIAL | 10.12% |
   | AIZL | 6.47% |

   These are explicit in [`planted-scale-check.json`](D:/Claude/random/wormWars/experiments/03a-self-consistency/development-records/planted-scale-check.json:9). “Against about 3%” in PILOT-DEV §4.7 and D309 is wrong for two of the three targets and overstates enrichment.

   The noiseless planted oracle is also **not a mathematical upper bound** on task-driven recovery. It has its own landscape and reward scale; weights and τ/bias are irrelevant to its fitness. The noisy version adds independent candidate noise rather than modelling the simulator’s common-world correlations. It is a useful favorable-oracle diagnostic.

   **What I would do:** retain 100 generations, the four existing round-B settings, and the paired 100→200 extensions for pilot-dev. Do not add higher move rates or double the main budget now. Higher move rates necessarily reduce weight and τ/bias exploration, which costs nothing useful in this oracle but can matter substantially on the real task.

   Use pilot-dev to distinguish:
   
   - continuing functional and anatomical improvement;
   - functional plateau with continuing anatomical improvement;
   - negligible improvement despite additional generations.

   Those imply different next steps. The present evidence says 100 generations is not established as sufficient; it does not identify the best replacement. Keep any conclusions from the MIP-only extensions scoped accordingly.

6. **Low to medium — remaining library and control observations.**

   - [`search.simulator`](D:/Claude/random/wormWars/wormwars/e03a/search.py:332) now moves both genome parameters and the spec to the requested device. The added device-contract and CUDA integration tests address the original blocker.
   - [`panel.relevance`](D:/Claude/random/wormWars/wormwars/e03a/panel.py:74) preserves the shared-world bootstrap using multiplicity weights. The new heterogeneous-data comparison meaningfully checks the calculation.
   - [`stats.family2`](D:/Claude/random/wormWars/wormwars/e03a/stats.py:67) now withholds non-finite brain values with `p=1`, fixing the artificial-zero/Holm problem.
   - [`expected_jaccard`](D:/Claude/random/wormWars/wormwars/e03a/null.py:246) correctly uses the hypergeometric expectation for `0 < m < K`. Its `m == K` result should be **1**, not NaN: both sets necessarily equal the universe. This is unlikely to affect the selected targets.
   - [`same_episodes`](D:/Claude/random/wormWars/wormwars/e03a/arms.py:70) correctly handles unfinished-event NaNs and compares counts, final positions and event fields. This is stronger state/event evidence, not a comparison of every action or position along the trajectory; D309’s “whole episodes” wording overstates it.
   - Baseline/probe failures block dependent stages, but both accumulate failures before raising. A failed early KT control still allows all evolved-brain probes to run. Failing immediately after saving the offending result would avoid unnecessary spending.
   - `_ladder_pick` matches the revised per-neighbour rule. I found no error in its qualification or fallback ordering.

7. **Disposition of every round-1 finding.**

   | Round-1 finding | Status | Code-based assessment |
   |---|---|---|
   | **1. CUDA device mismatch — blocking** | **Resolved** | Device transfer is explicit in `search.py:332`; both spec and parameters move. |
   | **2. Non-enforcing/weak controls — high** | **Resolved for pilot-dev** | Baseline and probe compare state/event evidence under `replay_mode()` and fail their stages; downstream reads require completion. Fail-fast and wording qualifications are above. |
   | **3. Timing projection — high** | **Partly resolved** | Workload units, missing-rate refusal and fourteen evolutions are corrected. Replay-control cost and composition claims remain problematic. |
   | **4. Longer-search diagnostic — high** | **Partly resolved** | Same-search snapshots, paired final evaluations, AUCs, Q and acceptance diagnostics are implemented. Durable state retention remains absent; turnover remains shifted. |
   | **5. Cap recovery — high** | **Partly resolved** | Evolution candidates are checkpointed; completed tuning rounds and target rows survive caught exceptions. Current-target search results are lost, and partial reporting fails. |
   | **6. Shared permutations across arms — medium** | **Resolved** | Both enrichment and descriptive nulls use `null_seed + x`, with the same target’s strata and draw count. |
   | **7. Non-finite family-2 values — medium** | **Resolved** | They now retain their family position with `p=1`; a targeted test was added. |
   | **8. NIP initialization disclosure — medium** | **Resolved** | The dated DESIGN annotation explicitly accepts intact-mask normalization and distinguishes it from functional exposure to X. |
   | **9. Tuning uncertainty and neighbour rates — medium** | **Resolved for pilot-dev** | Per-pair rates drive ladder selection; MIP deletion deficits are recorded; noisy B/C choices and low-target limitations are disclosed. |
   | **10. Incomplete analysis outputs** | **Partly resolved** | Structural contrasts, interface subsets, precision and AP are now exported. Mirror-zero semantics need clarification; the promised no-task AUC and explicit five-attribute summaries are still not emitted by `full`. Deferring the formal five-brain pipeline is acceptable. |
   | **11. Test claims exceeding coverage** | **Partly resolved** | New tests meaningfully address acceptance probabilities, swap parities, snapshots, bootstrap heterogeneity, class probabilities, intact-run equivalence and exact probe onset. Driver tests still do not cover interruption recovery, projection arithmetic or diagnostic extraction—the remaining bugs illustrate those gaps. |
   | **12. Mutation evidence — low** | **Resolved as selected evidence** | The runner requires exit 1 and the named failed test and retains an error line. The record supports nineteen caught mutations and one survivor; the surviving `>=`→`>` mutation remains equivalent under the probabilistic tie branch. It is appropriately no longer presented as comprehensive validation. |