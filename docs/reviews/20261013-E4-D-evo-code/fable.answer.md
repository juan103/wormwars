Verified what I needed. Writing the verdict now.

**Verdict: fix first.** The core pieces (ranking, flag-off path, replay peek, trial layout, fitness, champion rule, factor and keep rules, cap, saves) match design v2.1. Two things would make the pilot's numbers wrong or lost, and one sizing mismatch could sink it against the cap.

**Checked and correct**

- `ranking`: `lexsort((draws, -fit))` sorts by fitness first, draw second. Fitness values are sums of at most 64 halves over 2W, exact in float64, so ties are exact ties. Flag-off path is `np.argsort(-fitness)` as before (by reading, no shell here to diff).
- `replay`: the deep-copied stream peeks the same P draws `breed` takes next; the torch generator peek matches; the loop breaks before the last generation as `evolve_batch` does.
- `trial_rollout`: strain-major, maze, assignment ordering matches `trial_events` reshape; `score.mean` over W is real-first count / 2W; progress zero; shaping 0; `qualifying` deterministic and assignment-independent.
- `champion`: lexsort order is validation, final fitness, norm, index. `_assess` takes the final fitness from the last captured selection, which is index-aligned with `rec.final` since no breeding follows the last evaluation.
- Visibility draws: 8 × 64 = 512 fills the pool exactly; draws are disjoint within each W (nested across W, which is fine). Tie-as-half is the script's reading, recomputable from the saved fitness lists.
- Rule 7: `breed`'s new argument defaults to None; `_breed_islands` and `evolve` never pass it.

**Findings**

1. **High. The entry-rate safeguard compares across different mazes.** `scripts/e4d_evo.py:250-253` takes E-G's rate from generation 0 (its mazes) and the children's from generation 1 (other mazes). Each E-G figure rests on 2W trials per run; at W = 16 the maze-draw noise on the difference is about 0.045, the size of the 5% threshold. The factor choice and F's keep rule (`:294`, `:324`) are then near coin flips for a factor with no real effect. Fix: at generation 1 the elites (indices below `elites`) are E-G exactly, on the same mazes as the children. Use `n[:E]` versus `n[E:]` of `selections[1]`, and keep the generation-0 figure as descriptive.

2. **High. The pilot's played data is not saved.** `cap.selections` (per strain, per maze, per generation: score and the three counts), `rec.log`, `rec.checkpoints` (the validation learning curves §4 asks for), `rec.generation0` and `rp["parents"]` are never written (`scripts/e4d_evo.py:191-227`, `:256-263`). Only snapshots and a few derived numbers survive. Parent-pool turnover, tipped maze pairs and the neutral-walk comparison cannot be computed afterwards. On a cap or stop, `state` carries only a generation number and `after_fail` is unset. Fix: in `on_checkpoint` write the selections so far per run to an npz under `pilot/`; at the end write logs, checkpoints, train ids and parents; set `ctx.after_fail` to the same save.

3. **Medium. The timing is measured at half the screen's batch.** The precheck times 8 runs × 32 strains (`:174`), but `cmd_screen` evolves all 16 runs in one `evolve_batch` (`:282`, composition recorded at `:298`). Peak memory at W = 64 is untested at 512 × 128 worlds, and the per-generation seconds are off by about 2×. The timing also omits `qualifying`'s cold cost (training ids are fresh each generation; the timing's validation ids warm the cache across W). Fix: time at `len(factors) × runs_per_factor` runs with fresh ids, or batch the screen as two batches of 8 runs and record both compositions.

4. **Medium. Per-world Python maze construction will dominate at this scale.** `maze_world.py:217-232` and `trial.py:141-150` build the maze, four BFS maps and the start cell for every world; `qualifies` builds the maze once more per id. A generation has 2W × 512 worlds but only 16W distinct mazes, so this is 64× redundant. E4's pilot ran 1 024 worlds per generation at 56 s; here W = 16 gives 16 384. Fix: memoize per (run seed, id, episode) inside `_build_maps` and `start_cell`, with an equivalence test. Let the corrected timing from finding 3 decide whether it is needed before the screen, but it likely is at W ≥ 16 within a 6 h cap.

5. **Medium. The `parents` record under random ties is untested.** `test_the_replay_follows_random_ties` checks only `final`; a wrong peek that still let `breed` draw correctly would pass, and `lineage_mutations` (`:260`) would be wrong. Fix: port `test_the_recovered_parents_are_the_real_ones` from `tests/test_e4_lineage.py:71` with `random_ties=True`.

6. **Low. The stage record's resolved config is for W = 8.** `E.task_config = lambda: cfg_for(8)` (`:96`) feeds `resolved_config` and its hash for every stage. Record `cfg_for(W).to_dict()` and its hash in the screen and f outputs.

7. **Low. "Asserted" is not asserted.** Shaping 0 and zero progress are hard-coded, not checked (design §3 says asserted). Add `assert (res.progress == 0).all()` in `_train`'s capture and `AR.assert_frozen(start, rec.final, scales)` on arm L's finals so "cut links give E-G exactly" is verified rather than assumed.

8. **Low. Tests that pass with a broken implementation.** `test_without_a_stream_the_ranking_is_unchanged` compares the function to its own body. Pin the contract instead: tied fitness without a stream ranks in index order, and `breed` with ties and no stream keeps elites `[0, 1, 2]`. The integrity check compares total counts; per-maze equality (`rf.sum(2) == df.sum(2)`) is stronger and free, and `test_scores_progress_and_shapes` already relies on it.

9. **Low. E-G on the validation block is not recorded** (design §4: "E-G on both"). One extra rollout in `cmd_screen`.

Findings 1 and 2 are required before the precheck; 3 and 4 before the screen; the rest can land in the same commit.