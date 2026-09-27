**Scope:** I read the code at bb25331 but could not run anything (read-only, no shell), so the tests are unrun by me and 03's byte-identical `report.json` is unverified.

## My earlier points

| Point | Status |
|---|---|
| M1 untimed "other", no "final"/"tuning" | Resolved. "other" is null and flagged; "final" is set in `exp02.py:351`, `evolve_forage.py:85`, `experiment.py:148`; "tuning" on `tune` and `tune_batched`. |
| M2 lost on failure, no per-run compute | Resolved. `attempt` writes in `finally`, and `rec["compute"]` is in place. A hard kill still loses the attempt file. |
| M3 exact-count tests | Resolved: calibration, both probes, early termination, substeps override, scripted brains. |
| S1 coevolution | Resolved in code (`coevolve.py:357, 372`), but untested. |
| S2 aggregation | Resolved for exp02 and exp03. The five legacy scripts write attempts but no aggregate. |
| S3 production-path test | Partial. Still no test for coevolution, 02b replays, the stimulus bank, viewers or benchmarks. |
| S4 "measure" | Resolved in D069 and the docstring. `T0.md:37` still lists eight categories. |
| S5 timing tests | Resolved for exclusive time. Nothing tests that boundaries sync. |
| S6 exception-safe `pop`, S7 exp03 | Resolved. |
| Minors | Resolved: toggle, `reset()`, uncounted list, totals/commit/device, unique names. The purity test is still CPU-only, as declared. |

The gaps-off change is safe: the old code at the 03r binding worktree passed `dale_sign` too, so `with_params` gives the same genome.

## New since the fixes

No script fails at start, no counts are wrong, and nothing in the report path changed. Four things to fix, none blocking:

1. **The default category absorbs all overhead time.** Breeding, I/O, bootstraps and whole commands like `report` or exp03 `build` are now billed as "measure" or "probe" seconds with zero counts.
   - This makes `accounting.py:22-23` false for the default category.
   - The `uncategorised` warning can no longer fire in any script, so a future uncategorised path is silently billed to the default.
   - Fix: record `default` in the attempt file and correct the docstring.
2. **02b writes attempts into a tracked directory.** `experiments/02b-champion-analysis/compute/` is not covered by `.gitignore`, which only ignores `runs/**/compute/`. The files carry pid, device names and error strings that can hold local paths, and the repo is public.
3. **A test name overstates its coverage.** `test_coevolution_and_geometry_work_is_categorised` only tests geometry.
4. **Legacy scripts pool attempts per script.** `runs/compute/<script>` is shared across different `--out` runs and argv is not recorded, so attempts from different experiments cannot be separated.

Two smaller notes:
- **Per-run compute in exp02:** `rec["compute"]` excludes the run's "final" and generation-0 drive work, and under `attempt` it gains a time-only "measure" entry. A snapshot around `_execute` would cover the whole run.
- **Default-category assignment:** `cmd_validate_probes` and `_history_probe_validation` land in "measure" by default, though they are arguably "probe".

item 2: accept