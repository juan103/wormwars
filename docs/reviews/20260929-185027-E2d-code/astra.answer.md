**fix.** The main statistical rules are implemented correctly, but failure handling can block the hold-out pass or produce readings from incomplete arms.

Must-fix items:

1. **A training cap stop blocks every later stage.** [scripts/e2d.py:399](D:/Claude/random/wormWars/scripts/e2d.py:399) accepts skipped or final stopped records, but not `OUTCOMES["cap"]`. E2’s `require_earlier` rejects that outcome, and `rerun_plan` forbids rerunning it. Consequently, reaching 6.5 hours makes the protected evaluation inaccessible. Treat capped arms as final, incomplete prerequisites accepted by `final_ok`. Test continuation through subsequent skips into evaluation.

2. **Incomplete arms receive normal readings.** [scripts/e2d.py:811](D:/Claude/random/wormWars/scripts/e2d.py:811) loads champions from salvaged records regardless of outcome; [line 846](D:/Claude/random/wormWars/scripts/e2d.py:846) checks only whether all runs have counts. A crash after a checkpoint leaves candidates for all eight runs. I reproduced a final stopped C2 receiving **“supports”**, with an interaction claimed. Require completed arms for readings and dependent contrasts; require the complete matched checkpoint set for C2′. Test failure after a checkpoint, not only before training.

3. **Failed Part B checks do not propagate correctly.** [scripts/e2d.py:597](D:/Claude/random/wormWars/scripts/e2d.py:597) still draws per-set readings, and [line 856](D:/Claude/random/wormWars/scripts/e2d.py:856) ignores `b["checks"]["passed"]`. I reproduced “leaves plateau” with failed checks and every champion scoring below 2.5. Suppress Part B’s set readings and make Part C use scores alone when checks fail.

4. **Arm records describe the wrong configuration.** [scripts/e2d.py:752](D:/Claude/random/wormWars/scripts/e2d.py:752) replaces `ctx.cfg` after [scripts/e2.py:605](D:/Claude/random/wormWars/scripts/e2.py:605) records and hashes the baseline configuration. C1 therefore records eight worlds; C2 records unhalved mutation. Resolve the arm configuration before recording it, or refresh both configuration fields before any partial record. Also set its `evo.generations` to the arm’s actual generation count.

5. **Pairing failures do not invalidate paired readings.** [scripts/e2d.py:759](D:/Claude/random/wormWars/scripts/e2d.py:759) records a failed check but still completes the arm, and evaluation ignores it. Furthermore, [line 779](D:/Claude/random/wormWars/scripts/e2d.py:779) compares two regenerated schedules, rather than checking the IDs actually used at generation 249. Capture those actual IDs, check the complete expected run roster, and prevent paired readings when pairing fails.

6. **C0’s reference uncertainty is not the specified bootstrap.** [scripts/e2d.py:672](D:/Claude/random/wormWars/scripts/e2d.py:672) and [line 686](D:/Claude/random/wormWars/scripts/e2d.py:686) use the full-world sample SD divided by √248. Implement the planned bootstrap SE of the reference means and record its resampling settings, or explicitly amend the plan. The current tests do not distinguish these estimators.

7. **The projection omits its own cost.** [scripts/e2d.py:466](D:/Claude/random/wormWars/scripts/e2d.py:466) compares only future stages with the 6.2-hour **total** limit. Include already charged attempts and the current projection’s elapsed time. Otherwise a projected future cost just below 6.2 hours passes despite exceeding the planned total.

8. **Several promised analysis outputs are absent.** [scripts/e2d.py:851](D:/Claude/random/wormWars/scripts/e2d.py:851) discards arm contrast estimates and intervals after extracting classes; GA′ and C2′ are never classified. Preserve full per-genome contrasts for arms and matched references. Also add the bootstrap/sign-flip disagreement statement required by the plan, and the budget comparison’s selection costs and validation curves against cumulative episodes ([line 605](D:/Claude/random/wormWars/scripts/e2d.py:605)). These need no additional GPU work.

Suggestions:

- **Strengthen interval tests.** [tests/test_e2d_analysis.py:31](D:/Claude/random/wormWars/tests/test_e2d_analysis.py:31) accepts incorrect confidence levels: I substituted 95% run intervals labelled “90%”, and all four relevant existing test cases still passed. `world_ci` has no direct test. Pin paired resampling and exact percentile levels.
- The sibling test at [line 108](D:/Claude/random/wormWars/tests/test_e2d_analysis.py:108) never reverses the complement’s ordering. Add reversal, the 30-distinct-pair boundary, and ES exclusion cases. The noise test checks only GA weights; extend it to gap weights, log-τ, bias and both ES σ values.
- The command tests miss the consequential continuations: cap → evaluation, checkpointed failure → evaluation, and failed Part B checks → Part C. Their current passing assertions do not establish those rules.
- [scripts/e2d.py:893](D:/Claude/random/wormWars/scripts/e2d.py:893) reduces C0’s smoke sizes but retains its formal noise seeds. Give smoke C0 separate seeds as planned.
- Fail explicitly on missing 04a source records instead of silently shrinking the read sets, and report the pooled distinct-genome count.

What I checked and found correct:

- All **48 champion references** match their local parameter hashes, representing **47 distinct genomes**: E2’s 31 and 04a’s 16. The shaped/unshaped split is 12/4. Deduplication by genome hash and probe is correct.
- `world_ci` uses paired 95% intervals; `run_summary` uses 90% intervals. Classification boundaries, set rules, plateau band, budget threshold, exact sign-flip enumeration, run-2 support/harm rules and the interaction formula match the plan.
- C0 correctly fixes bins by full-world differences, scores each draw against its complement, excludes zero complements, respects reversed complements, counts distinct pairs and breaks truncation ties by index. Noise generators reset across scales/σ; parents and means join the 65-strain evaluations.
- Replay uses E2’s verified seeds, IDs, settings and composition, generations 0–25, twice, comparing both checkpoints in default mode.
- Arm settings, reference assignments, first-best matched selection, and admission accounting—including reruns—are otherwise correct.
- The reachable reused E2 functions resolve output paths through the reassigned globals. I found no accidental writes to E2’s folders or reachable E2 outcome wording. The configuration snapshot and terminal-state assumptions above are the reuse problems.

Read-only review. I exercised 18 pure statistical test cases in memory using the unchanged function bodies. Full pytest was blocked by temporary-file requirements; command tests were inspected, not run. No GPU work or file changes.