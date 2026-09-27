**Scope:** I read the code at 572f764 but could not run anything (read-only, no shell), so the five new tests are unrun by me.

## My remaining points

| Point | Status |
|---|---|
| 1. Default category absorbs overhead | Resolved. `default_category` is in every attempt file (`accounting.py:216`), the docstring is corrected (`accounting.py:17-21`), and a test asserts the field. |
| 2. 02b attempts in a tracked folder | Resolved. `.gitignore:73-74` covers it, and no attempt files exist under `experiments/` on a clean tree, so none were committed. |
| 3. Test name overstated | Resolved. Renamed to `test_geometry_work_is_categorised`, and a real coevolution test was added. |
| 4. Legacy scripts pooled per script | Resolved. All five use `run_script`, which routes to `<--out>/compute/`, records `argv`, and aggregates after the attempt file is written. |
| Per-run compute in exp02 | Resolved. The snapshot is taken at the top of `_execute` (`exp02.py:329`), before the drive, and read after the "final" loop. |
| Probe validation category | Resolved. Both functions are `@acct.counted("probe")`. |
| S1/S3 coevolution and stimulus bank untested | Resolved. The stimulus-bank count of 16 × 4 worlds matches `exp03.py:390-393`. |
| S4 `T0.md` listed eight categories | Resolved (`T0.md:37-38`). |
| S5 boundary syncs untested | Resolved. The test checks that `_sync` is called at entry and exit, not that CUDA synchronises, which is all a CPU test can do. |

Astra's `--help` point is also fixed: `--help` bypasses `attempt`, and `SystemExit` with code 0 or None is recorded as completed.

## New or still open

None of these block.

1. **`T0.md:34` still overstates the tests.** It says a test checks every production path listed, but 02b's replays, the viewers and the benchmarks have none. D070 records this; the plan text should say the same.
2. **02b writes no aggregate.** Astra raised this, and D070 neither fixes nor lists it. `T0.md:52` says each experiment script writes a `compute.json`, which 02b does not.
3. **The aggregate does not identify legacy or 02b attempts.** `aggregate` copies only `command` (`accounting.py:238`), but `run_script` records `script` and `argv`, and 02b records `stage`. Those attempts appear with `command: null`.
4. **`run_script` parses `--out` itself and misses argparse abbreviations.** `--ou runs/x` is accepted by argparse, but the attempt would go to the default directory. Setting `allow_abbrev=False` in the five parsers closes it.
5. **A usage error leaves a failed attempt.** A mistyped flag exits with code 2 inside `attempt`, so it creates `<out>/compute/` and inflates `failed_attempts` with zero work.
6. **exp02 and exp03 aggregate inside the `report` attempt.** `compute.json` therefore excludes the report's own attempt and goes stale if anything runs afterwards. This is time-only overhead and unchanged from D069.
7. **No test covers a non-zero `SystemExit` being recorded as failed.** The code is correct by reading.

item 2: accept