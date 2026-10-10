**Scope note:** I could not run pytest, but I did run `git diff`, `git show` and a sha256 through a one-shot command stream, so the binding facts below are verified, not inferred.

## 1. Every required change was taken correctly

- **g-e's rollout leg** (`scripts/e3d.py:532-546`): the record is unlinked first, and `identical` is true only if the subprocess exits 0 and the fresh record says so. The test at `tests/test_e3d_runner.py:150-169` covers the stale, missing and failing cases. Correct.
- **Records per condition** (`:364-380`, `:396-398`): head cells per tick, the visit ledger, first-entry ticks, the first label and class per wey, and per-visit rows (world, wey, visit, tick, remembered, outside) with `world_ids` and `strain_of_world`. Every §6 observer uses `floor` of the position, so cells suffice to recompute them. Saved and hashed per condition; the smoke's `confirm.json` carries the hashes.
- **Per-goal scent split** (`:629-649`): arrival share at each goal against that goal's flag, A and B separately and pooled, the whole-maze split kept beside. This is the reading at `docs/E3/E3d-DESIGN.md:114-119`. Correct.
- **Bootstrap** covers `seed_median_legs` and `oracle_visited_share` inside each resample (`wormwars/e3/e3d_gate.py:109-117`).
- **Predictions** decide on the inequalities; the ratio is `None` on a zero tree mean (`:98-99`).
- **Tree spawn candidates** (`scripts/e3d.py:297-298`) is exactly `place`'s candidate rule at `wormwars/e3/maze.py:152`.
- **Scripts guard** (`:130-159`): any script other than the runner, or any non-binding line of the runner, refuses. I confirmed `git diff 4886ba9 c86f281` is one line (the binding commit), the engine diff from 4886ba9 is empty, the guarded tree is clean, and the design's normalised sha256 equals the registered constant. So `require_bound` passes at c86f281 and would refuse anything else.
- **Projection reserve**: spent hours plus 0.25 h. E3c's formal g-e took 244 s and the smoke's full-rollout CPU leg ran inside 82 s, so the allowance has about 2× margin. `runs/e3d/` holds no compute folder, so the formal clock starts at zero.
- **Readable contact** counts a tick once per class (`e3d_records.py:138`), matching `contact_batch`; the tie test is a real equal-count tie.
- **Tree config on an island base** clears both fields (`maze_world.py:69`); `to_dict` omits them when unset, so the equivalence config hashes are unchanged.
- **Tests**: the orbit now needs ten full turns; x = 13.7 genuinely separates `_probe` from `_point` (0.5 and 1.0 samples hit column 14, the endpoint 15.2 misses); the guard's negative branches, both `failed_check` branches, the goal stream and the strain mapping are covered.
- **E3c test** (`tests/test_e3c_stages.py:307-314`): it recomputes the freeze with the same pathspec and the same "added files are allowed" rule as `e3c_formal.engine_freeze` (`:91-98`). At HEAD the diff from 69d7cd5 is M config.py, M maze_world.py, five A files, so the test expects `passes` false with exactly those two paths. Consistent.
- **The correction to Amendment 1** is dated and appended. The 12:47 UTC smoke compute record shows 32 single-strain worlds at H = 60, which is 16 timing mazes, so "40 100-40 115" is right.

## 2. No fix introduces a result-changing error

I looked specifically at the five areas named and found nothing that would make a result wrong or uninterpretable.

## 3. Verdict: run

After the owner is told, with the conditions from my first review unchanged: the GPU reference made from the 40bd50f worktree with the same device string the compare will use, then `g-e` on CUDA, then a `--smoke --device cuda` pass of all five stages.

Non-blocking, for the record or a later commit:

- **Reruns overwrite the record files.** `play_block` writes to fixed paths and E3d passes no `local_files` to `run_stage`, so a rerun replaces attempt 1's `.npz` files while the archived attempt-1 JSON still names their hashes. Pass the stage's record paths as `local_files`.
- **"Uncounted" is half right.** The compare's wall time lands in the g-e stage's "calibration" seconds and so in the cap clock; only its worlds, ticks and neural updates are uncounted. Say that in the compute record.
- **Saving the records is not timed** by the projection, since the timing plays pass no `save_as`. A few GB of int8 cells compress in a minute or two; small, but the admission is slightly optimistic.
- **Wording in the correction:** the equivalence leg plays trees with ids 30 000-30 007 at H = 2 400. "No formal block's maze" is accurate; "no calibration id at the formal horizon" is not quite.
- **The design-hash line is exempt from the scripts guard,** so the design is frozen between stages only by the same-code check in `require_earlier`, and before `project` only by convention and the commit log. That is acceptable; it should be stated.