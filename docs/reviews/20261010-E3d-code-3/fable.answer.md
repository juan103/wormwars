**Verdict: run.**

All five D228 fixes are in place and behave as described. I checked them against the diff `c86f281..17b06c1`, the files at HEAD, and by executing the guard and the runner's tests with the project's Python 3.13.

What I verified:

- **Scripts guard.** `git diff 202666e HEAD -- scripts` is the single `binding_commit` line. At HEAD, with formal arguments, `engine_changes()` and `script_changes()` are both empty, the design's LF-normalised sha256 equals the registered constant, and `require_bound` passes. The hidden-entry case (`"binding_commit": "x", "H": 60` moved onto a binding line) is refused, and `tests/test_e3d_runner.py` passes (14 tests, rc 0).
- **Reserve.** `reserved_hours` is earlier attempts (from `compute.json`, which the accounting writes only at process exit, so no double count) plus elapsed time since the cap clock was made (before preflight and the timing plays) plus the 0.25 h allowance. The smoke record confirms the arithmetic: total 0.3689 h = 0.1185 h spent + 0.25 h + about 1.5 s elapsed. `runs/e3d/` holds no compute folder, so the formal clock starts at zero.
- **Timing saves.** The three timing plays pass `save_as`, the per-world records cost is the summarise-plus-save remainder scaled by H/H_t, and the files are unlinked. The smoke's calibrate stage shows the sum of condition seconds roughly equal to the stage's wall time, so the remaining untimed per-condition setup is negligible at formal scale.
- **Record files on rerun.** `stage_records()` is evaluated before `run_stage`, so it lists attempt 1's files; `apply_rerun` renames them to `-attempt1.npz` before the body runs, and `reconcile_kill` now includes their mtimes.
- **Erratum.** Dated, appended beneath the correction, hash updated at 202666e and matching.

Non-blocking, for the record:

1. **A control byte in `_normalise`.** `scripts/e3d.py:136` contains a literal chr(1) (`^A`) inside the raw replacement string, committed at HEAD. The intent was evidently `\1` (keep the key, blank the value). As committed, the whole `"key": "value"` match becomes `\x01"<bound>"`. The same substitution applies to both texts, so the comparison is sound and the guard's power is intact; swapping the two keys is the only masked edit, and it is a no-op or a refusal. Fixing it means re-binding, so I would leave it and note it.
2. **No test for the `local_files` wiring.** D228 says each fix was seen failing first; `stage_records` and the two `local_files=` arguments have no test. A process gap, not a result risk.
3. The runner's first docstring line still says "bound at 65b77fb". Cosmetic.

Conditions from my earlier reviews stand: the owner is told first, then the GPU reference from the 40bd50f worktree with the device string the compare will use, then `g-e` on CUDA, then a `--smoke --device cuda` pass of all five stages before the formal `project`.