**Fix first.** At `30167b3`, several fixes are correct, but path validation now rejects every valid saved path file.

I ran **56 selected read-only tests successfully**, inspected the smoke artifacts, and reproduced interruption failures with in-memory dependencies. I did not rerun the writing stages or full suite. No files were modified.

| Previous requirement | Recheck |
|---|---|
| Reporting after interrupted or never-started stages | Partly fixed; available cost readings are still omitted when evaluation never starts. |
| Checkpoint consistency across reuse | Fixed: original checkpoints are persisted and checked again. |
| Durability per completed chunk | Partly fixed; several completed plays remain outside salvage. |
| Registered-block and path completeness | Formal test-count check fixed; path validation is broken. |
| No fictitious observations; independent bootstrap calculation | Holm fixed; bootstrap availability decoupled, but its registered seed changed. |
| Regression coverage | Improved, incomplete; the passing tests miss the defects below. |

The annotation is **sound as policy**, including withdrawal of the reuse exemption. Its implementation remains incomplete for points 3, 5 and 8. The registered text still matches its pinned hash. Smoke cleanup and interior checkpoints are implemented.

Required changes:

1. **Fix the path-dimension mismatch.**  
   [`save_paths`](D:/Claude/random/wormWars/scripts/e3c.py:1204) records the full offsets shape: `[worlds, weys, 2]`. [`paths_ok`](D:/Claude/random/wormWars/scripts/e3c.py:1296) compares that against `[worlds, weys]`.

   All **13 existing smoke path files** have matching hashes and matching recorded/actual dimensions; `paths_ok` accepts **zero**. Consequently, a successful formal evaluation would still make every champion’s §7.3 readings undefined and force the coverage classification to “mixed”.

   Align the writer and validator’s shape contract, and test the real validator with valid, missing, altered and wrongly shaped files. The synthetic report tests currently replace it with a constant-returning function.

2. **Finish durability beyond the champion-selection loop.**  
   In [`champions`](D:/Claude/random/wormWars/scripts/e3c.py:1147), `pj_curve` and `refs` enter salvage only after their respective loops finish. I reproduced:
   
   - stopping during the generation-299 play loses the completed generation-124 point;
   - stopping during the second learning-reference play loses the completed first reference.

   Attach those dictionaries before their loops and persist each completed result immediately. Persist W2-turn’s completed validation result immediately too.

   [`g-e`](D:/Claude/random/wormWars/scripts/e3c.py:888) similarly publishes its CPU/hook/maze results together only after all finish. Its delegated GPU rollout callbacks receive `ctx.cap`, so they check the cap without updating partial records. Save completed legs individually and connect rollout-boundary callbacks to progress writing.

   Also make successive champion-file saves atomic: the new per-chunk saving repeatedly overwrites the same `.npz` directly. An interruption during a later write can destroy previously saved champions.

3. **Preserve available readings when `evaluate` never starts.**  
   The new [`report_from` early return](D:/Claude/random/wormWars/scripts/e3c.py:1553) returns primary “not read” labels and raw learning curves only. It discards cost thresholds, successes, medians, Fisher/Holm results and P-joint’s points even when completed training and `champions` records supply everything needed.

   I reproduced this: the fallback omitted cost results that `report_readings` computed from the same available records. Use the normal reporting path with an empty evaluation, or equivalent per-reading handling. Unavailable outputs should receive explicit statuses rather than disappear.

4. **Complete the failed-verification fallback.**  
   The [`reuse exception handler`](D:/Claude/random/wormWars/scripts/e3c.py:982) handles missing files and ordinary hash mismatches, but not corrupt NPZ archives. A truncated population raises `zipfile.BadZipFile`, which is outside its exception tuple. I reproduced that using an existing population’s bytes in memory.

   Handle expected archive/read failures as failed verification, record the reason, and retrain as point 3 promises. Add a corrupt-file regression.

5. **Restore the registered bootstrap seed.**  
   [§7.1](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/PREREGISTRATION.md:311) specifies seed `20261007`. The new [implementation](D:/Claude/random/wormWars/scripts/e3c.py:1403) uses `[20261007, 1]` and `[20261007, 2]`, producing different resamples. The new oracle repeats that change rather than checking the registered calculation.

   Initialize a fresh generator with the registered scalar seed for each available contrast. This preserves independent availability without changing the registered resamples.

**The fixes did introduce defects:** the universal path rejection and changed bootstrap streams are clear regressions. The missing-evaluation fallback also introduces an incomplete reporting branch.

Add regressions for these cases. The previously requested pre-start cap exhaustion and final frame cap-check cases also remain untested in `test_e3c_stages.py`; the new once-only test does not cover them.