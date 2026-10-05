**Fix first.** The successful-run wiring is mostly correct, but interruption handling can discard completed work, and the report does not implement the registered eligibility rules.

I compared the working tree with `69d7cd5`: the pre-registration and registered statistics are unchanged. I ran 46 read-only tests successfully, verified all 512 reused P-joint genomes against their recorded hashes, and checked all four pinned inputs. I inspected the existing smoke outputs; I did not rerun the writing stages or independently complete the full suite.

1. **Does every stage implement §5 exactly? No.**

   The following parts are correct:

   | Stage | Checked behavior |
   |---|---|
   | `project` | Uses benchmark IDs for scored rollouts; benchmarks the four training compositions, checkpoint chunks, validation and recorded evaluation. Remaining budget includes prior compute and elapsed project time. [e3c.py:725](D:/Claude/random/wormWars/scripts/e3c.py:725) |
   | `g-e` | Reuses E3b-1’s CPU, GPU and maze comparisons plus its snapshot-hook check. Training requires both completion and `passed`. [e3c.py:711](D:/Claude/random/wormWars/scripts/e3c.py:711), [e3c.py:787](D:/Claude/random/wormWars/scripts/e3c.py:787) |
   | Training | Correct run IDs, seeds, draw RNG, masks, factors, training range and full/cut compositions. Frozen parameters are checked against the draws. [e3c_formal.py:11](D:/Claude/random/wormWars/wormwars/e3/e3c_formal.py:11), [e3c.py:813](D:/Claude/random/wormWars/scripts/e3c.py:813) |
   | `champions` | Checks both P-joint population sets before validation; validates each final population separately; uses the lower-index champion tie rule. W2-turn uses validation and the registered ties. P-joint’s two candidates use the correct generation’s logged hash. [e3c.py:952](D:/Claude/random/wormWars/scripts/e3c.py:952) |
   | `evaluate` | Correct champion/reference chunks, test IDs, intact/noses-removed conditions and optional trails-off membership. Champion hashes are checked again. [e3c.py:1057](D:/Claude/random/wormWars/scripts/e3c.py:1057) |

   The departures are substantial:

   - **Durable progress and salvage are incomplete.** Training saves final populations only after all post-hoc checkpoint plays. Its salvage contains generation counts and hashes, not the current arm’s recoverable genomes or completed checkpoint measurements. `champions` and `evaluate` install no salvage callback or partial-record writer. [e3c.py:830](D:/Claude/random/wormWars/scripts/e3c.py:830), [e3c.py:863](D:/Claude/random/wormWars/scripts/e3c.py:863), [e2.py:609](D:/Claude/random/wormWars/scripts/e2.py:609)
   - **Interrupted-stage eligibility is not implemented.** Every prerequisite must be `completed`; there is no route from a finally stopped stage into the registered partial analysis. The frame also refuses to start `report` after the cap is exhausted. [e3c.py:714](D:/Claude/random/wormWars/scripts/e3c.py:714), [e2.py:426](D:/Claude/random/wormWars/scripts/e2.py:426), [e2.py:594](D:/Claude/random/wormWars/scripts/e2.py:594)
   - **Full paths are discarded.** `play_recorded` retains only two weys on the first four mazes: eight paths per champion/condition, instead of all 2,048. It computes the aggregate measures using all trajectories, but does not preserve those trajectories. [e3c.py:446](D:/Claude/random/wormWars/scripts/e3c.py:446)
   - **Stage order is incomplete.** `train-psel` requires `project` and `g-e`, but not `train-s`. [e3c.py:913](D:/Claude/random/wormWars/scripts/e3c.py:913)
   - **Benchmark training IDs are not pre-flighted.** The project preflight covers the four fixed blocks; `gen_seconds` then draws a separate set of training IDs without preflighting or recording their redraws. Formal training does preflight its actual schedules correctly. [e3c.py:735](D:/Claude/random/wormWars/scripts/e3c.py:735), [e3c.py:744](D:/Claude/random/wormWars/scripts/e3c.py:744), [e3c.py:825](D:/Claude/random/wormWars/scripts/e3c.py:825)

   The cut order and admission comparison are correct. One accounting omission remains: the projection budgets **21 checkpoint plays per trained batch**, while execution performs **23**—the 21 post-hoc plays plus the two in-loop plays. Other projection terms use conservative proxies, so this does not establish that the total is underestimated, but those extra rollouts should be explicitly included. [e3c_formal.py:68](D:/Claude/random/wormWars/wormwars/e3/e3c_formal.py:68)

2. **The checkpoint approach is substantively equivalent on a completed run; the consistency check is insufficient.**

   The snapshot hook saves the evaluated population **before breeding**. The post-hoc code selects the genome identified by that generation’s `best_sha256`, preserves run ordering and uses the registered learning block and composition. Learning-block evaluation does not feed back into breeding. I see no algorithmic objection to evaluating these snapshots after training. [evolve.py:173](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:173), [evolve.py:182](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:182), [e3c.py:870](D:/Claude/random/wormWars/scripts/e3c.py:870)

   However, `checkpoint_consistency` compares **only the mean**, and a false result merely becomes a field in an otherwise completed training record. Different per-maze results can have the same mean. There is no refusal on mismatch. [e3c.py:886](D:/Claude/random/wormWars/scripts/e3c.py:886)

   Compare candidate hashes and the complete per-maze vectors, enforce failure, and sabotage that enforcement. The existing CPU smoke tests only generations 0 and 5, because smoke uses six generations; it exercises no checkpoint between the two in-loop endpoints. It also provides no CUDA equivalence evidence. [e3c.py:1248](D:/Claude/random/wormWars/scripts/e3c.py:1248), [test_e3c_stages.py:166](D:/Claude/random/wormWars/tests/test_e3c_stages.py:166)

3. **`report_readings` does not compute every §7 reading as registered.**

   For complete, aligned records with sufficient runs and a finite positive P-fixed mean, these parts are correct:

   - The unit \(d\), contrast directions, exact tests, approximate margin labels, fixed Welch intervals, Holm values, successful-run decomposition and Mann–Whitney supplement use the bound statistics correctly. [e3c.py:1116](D:/Claude/random/wormWars/scripts/e3c.py:1116), [e3c_stats.py:131](D:/Claude/random/wormWars/wormwars/e3/e3c_stats.py:131)
   - The maze bootstrap shares each resample across arms and P-fixed, recomputes the denominator and every run’s \(d\), and uses the registered seed and percentiles. [e3c.py:1137](D:/Claude/random/wormWars/scripts/e3c.py:1137)
   - Complete cost curves use strict threshold exceedance, count a hit at 299 as success, use censored medians, and calculate Fisher tests with Holm adjustment. [e3c.py:1148](D:/Claude/random/wormWars/scripts/e3c.py:1148)

   **Eligibility and missing-data handling are wrong.** I reproduced these cases in memory:

   | Input change | Actual result |
   |---|---|
   | Reduce S-mod to five evaluated runs | Both Q1 and Q2 remain readable |
   | Mark an evaluated run’s training incomplete | It remains in the primary contrasts |
   | Remove one run’s entire checkpoint curve | It becomes censored, rather than undefined |
   | Remove one S-mod noses-removed row | `zip` silently drops the champion; coverage can still read “supported” with zero undefined champions |
   | Remove the noses-removed key | The whole report crashes |
   | Leave one eligible P-sel run with zero loss | Reports CI `[0, 0]` and `no_material_loss=True`; one observation cannot supply the registered t-interval |
   | Give P-fixed an infinite mean | The report eventually raises instead of returning the registered unavailable reading |

   These follow directly from unfiltered evaluation arrays, unchecked checkpoint completeness, positional `zip`, the one-run interval fallback and the incomplete denominator guard. [e3c.py:1120](D:/Claude/random/wormWars/scripts/e3c.py:1120), [e3c.py:1152](D:/Claude/random/wormWars/scripts/e3c.py:1152), [e3c.py:1183](D:/Claude/random/wormWars/scripts/e3c.py:1183), [e3c.py:1195](D:/Claude/random/wormWars/scripts/e3c.py:1195)

   **Several required outputs are also absent:**

   - P-fixed’s nose class, coverer classification and “no material loss” reading; its report entry contains only retained fraction and loss statistics.
   - Explicit maze-level intact-minus-removed differences.
   - The learning curves, including P-joint’s two points.
   - Each P-sel run’s comparison with P-fixed and P-joint.
   - W2-turn’s coverage and tour match.
   - Each champion’s resting-turn offset and \(K_D\), although evaluation records these.
   - Nose/coverer qualifiers attached to both primary labels; they currently appear only in a separate top-level object.

   See [e3c.py:1203](D:/Claude/random/wormWars/scripts/e3c.py:1203) and [e3c.py:1216](D:/Claude/random/wormWars/scripts/e3c.py:1216). Several omissions can be repaired from existing records without additional simulation. Full missing paths cannot.

4. **Yes, a late stop can waste the intended formal run.**

   The clearest example is a cap stop during the post-hoc learning plays: all 300 generations may have finished, but that arm’s final populations have not yet been saved. The salvage callback retains hashes and counts, not the genomes. Fix this before spending the training budget. [e3c.py:848](D:/Claude/random/wormWars/scripts/e3c.py:848), [e3c.py:889](D:/Claude/random/wormWars/scripts/e3c.py:889)

   A late failure in `evaluate` loses completed condition results because they live only in local variables. Even a cap failure **after the body returns** discards its returned output unless salvage contains it. [e3c.py:1067](D:/Claude/random/wormWars/scripts/e3c.py:1067), [e2.py:613](D:/Claude/random/wormWars/scripts/e2.py:613)

   Missing periodic files also weaken killed-attempt accounting: reconciliation uses the last write among the registered stage files plus 900 seconds. `champions` does not register its genome files in `local_files`, so those writes do not repair that gap. [e2.py:521](D:/Claude/random/wormWars/scripts/e2.py:521), [e3c.py:1036](D:/Claude/random/wormWars/scripts/e3c.py:1036)

   I found **no wrong-organism or wrong-mask defect**, and the actual P-joint populations and logged candidate hashes passed verification. The main risk is losing or excluding valid completed work.

5. **§12 is only partly covered.**

   | Registered test | Coverage and missing part |
   |---|---|
   | Blocks and every-ID preflight | Block disjointness covered; no test that every actual training/benchmark ID is pre-flighted and redraws retained. [test_e3c_formal.py:42](D:/Claude/random/wormWars/tests/test_e3c_formal.py:42) |
   | Order, once-only, rerun | One `champions` prerequisite refusal; no complete E3c order test, once-only test, or rerun/archive/batch-membership test. [test_e3c_stages.py:139](D:/Claude/random/wormWars/tests/test_e3c_stages.py:139) |
   | Salvage and eligibility | Missing for formal stages: injected failures, cap stops, completed-run recovery, minimum counts, incomplete maze blocks, missing checkpoints and missing nose/path records. |
   | CPU smoke of every stage | Present. [test_e3c_stages.py:154](D:/Claude/random/wormWars/tests/test_e3c_stages.py:154) |
   | P-joint hash sabotage | Final-population expected-hash sabotage present; snapshot-population sabotage not covered. [test_e3c_stages.py:36](D:/Claude/random/wormWars/tests/test_e3c_stages.py:36) |
   | Champion ties | Covered. [test_e3c_formal.py:55](D:/Claude/random/wormWars/tests/test_e3c_formal.py:55) |
   | W2-turn validation-only choice and ties | Ties covered; no integration assertion that selection uses only validation. [test_e3c_formal.py:60](D:/Claude/random/wormWars/tests/test_e3c_formal.py:60) |
   | P-joint learning candidates | Generic hash lookup covered; no assertion that both real stage points use their respective logged generation-best genomes. [test_e3c_formal.py:72](D:/Claude/random/wormWars/tests/test_e3c_formal.py:72) |
   | Nose intervention and paths | Existing tests cover the four-channel intervention and path-measure primitives; no formal-stage test verifies complete path retention in both conditions. [test_e3b2_attribution.py:151](D:/Claude/random/wormWars/tests/test_e3b2_attribution.py:151), [test_e3c_runner.py:144](D:/Claude/random/wormWars/tests/test_e3c_runner.py:144) |
   | Report, every label | Incomplete. Missing explicit integration coverage for within-margin, margin-unresolved, unclear, all unavailable outcomes and missing-data classifications; no numerical bootstrap oracle. [test_e3c_stages.py:92](D:/Claude/random/wormWars/tests/test_e3c_stages.py:92) |
   | Cut IDs and compositions | Pure helpers covered; actual stage calls under each cut are not checked. [test_e3c_formal.py:16](D:/Claude/random/wormWars/tests/test_e3c_formal.py:16) |
   | Engine freeze | Predicate covered; no guarded-stage refusal sabotage or verification of every stage marker. The smoke checks only `project`, and accepts either boolean value. [test_e3c_formal.py:94](D:/Claude/random/wormWars/tests/test_e3c_formal.py:94), [test_e3c_stages.py:159](D:/Claude/random/wormWars/tests/test_e3c_stages.py:159) |

   I cannot verify failing-first history from this working tree. The report tests explicitly say they were written after the report. [test_e3c_stages.py:130](D:/Claude/random/wormWars/tests/test_e3c_stages.py:130)

6. **Verdict: “fix first.” The concrete defects to fix are:**

   1. Save final populations and checkpoint candidates before post-hoc evaluation; durably retain completed chunks and useful salvage throughout long stages.
   2. Implement the registered interrupted-stage continuation and reporting route, including reporting after the compute cap.
   3. Enforce primary eligibility, minimum run counts, checkpoint completeness and explicit undefined nose/path records. Never silently drop missing champions.
   4. Preserve every required wey/maze path in both conditions.
   5. Complete the missing §7 outputs and fix the one-run loss interval and nonfinite-denominator handling.
   6. Make checkpoint consistency compare hashes and per-maze results and refuse mismatches.
   7. Enforce `train-s` before `train-psel`, preflight benchmark training IDs, and include the additional endpoint checkpoint plays in the projection.
   8. Add the missing §12 tests above.

   One additional guard omission should be fixed: E3c’s pre-registration is absent from `GUARDED` and the pinned-input list. Although it is unchanged now, the formal dirty-tree guard would not catch a local edit to the bound text. [e3c.py:67](D:/Claude/random/wormWars/scripts/e3c.py:67), [e3c.py:86](D:/Claude/random/wormWars/scripts/e3c.py:86)