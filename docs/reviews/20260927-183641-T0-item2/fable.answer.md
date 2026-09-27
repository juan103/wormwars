# Review: T0 item 2, compute accounting (D068, HEAD 4303a2a)

I read every file listed, plus `evo/rollout.py`, `evo/coevolve.py`, `exp02/scripted.py`, `analysis/geometry.py`, `analysis/ablation.py` and `scripts/exp03.py`, `experiment.py`, `bench_brain.py`. I could not run the tests (read-only, no shell), so everything below is from reading.

## What is correct

- **Neural count.** `brain.py:374-375` uses the effective `k` and `v.shape[0] * v.shape[1]`. In a world that is strains × (slots × weys), so padding and dead slots count and the `substeps` override is respected.
- **Scripted brains count zero.** `ScriptedBrain.step` never touches the ledger.
- **World-ticks and early termination.** `world.py:630` counts per call, and `run` (`world.py:987`) only calls `tick` while not done. The hand-written loops in calibration, `behaviour` and `coverage` also count only what ran.
- **Hand counts in the evolve test.** The arithmetic is right: 16 selection worlds, 240 ticks, holdout 3 (g0), snapshot 3 (g1).
- **Nesting and time.** Push closes the parent's segment and pop restarts it (`accounting.py:79-100`), so nothing is double-timed. This also holds for same-name nesting (`calibrate_in_world` → `achieved_drive`).
- **CUDA.** Sync runs before the clock is read on both push and pop, so pending work from before a category is not billed to it. `is_initialized()` keeps CPU runs from touching CUDA.
- **Pure measurement.** The hooks do integer arithmetic on shapes, touch no tensor and draw no random numbers.
- **03r is not affected.** It runs from its own worktree.

## Must fix

**M1. Uncategorised work gets zero seconds, and the scripts leave real experiment compute uncategorised.**
- `_close_segment` only runs when the stack is non-empty (`accounting.py:74-77`), so "other" accumulates counts but `seconds` stays 0.0.
- `"final"` and `"tuning"` are never set anywhere; a grep finds only selection, holdout, snapshot, calibration, probe and measure.
- What lands in "other" at 0 s:
  - `scripts/exp02.py:350`: the final held-out evaluation of every champion (this is what "final" is for).
  - `scripts/exp02.py:117, 141, 218, 307`: all scripted tuning, gate and reference scoring, so `diagnostics-*.json` will be 100% "other" with 0.0 s.
  - `scripts/exp02.py:375-381`: the feasibility gate.
  - `scripts/evolve_forage.py:84-87` and `scripts/experiment.py:147`.
- **Fix:** set the categories in the scripts, and either time "other" or write its seconds as null. I would also have the experiment scripts refuse or warn when "other" is non-empty at write time.

**M2. The experiment-level file is lost on any exception or kill, and per-run compute is not persisted.**
- `scripts/exp02.py:623-629` writes only after the command returns; `evolve_forage.py:119-120` is the same.
- `calibrate_in_world` raises on non-convergence (`calibration.py:256`). That is the "calibration attempts and retries" case the plan names, and it writes nothing.
- `cmd_run` appends each run to `records.jsonl`, but `rec` (`exp02.py:340-356`) has no `compute`. A crash at run 37 keeps 36 results and loses all their accounting.
- **Fix:** wrap the dispatch in try/finally, and add `rec["compute"] = res.compute`.

**M3. Plan-specified tests are missing.**
- The plan requires hand-computed counts for "a small evolve run, a calibration and a probe". Calibration, `input_response` and `history` are only checked `> 0` (`test_t0_accounting.py:137-144`), though all three are trivially hand-computable.
- There is no test for early termination (a world set that dies before `max_ticks`), the `substeps` override, or scripted brains counting zero neural updates with non-zero ticks. The code is right on all three, but nothing stops a regression.

## Should fix

- **S1. Coevolution is counted but uncategorised and unreported.** `coevolve.py:356` (selection) and `:370` (suite) run in "other" at 0 s. `coevolve()` returns no compute and `scripts/coevolve.py` writes no file.
- **S2. Nothing sums the processes.** The plan says one `compute.json` "summing every process". exp02 writes one file per invocation under `runs/exp02-screening/compute/` and no code merges them. Add a merge function with a test, called from `report`.
- **S3. The production-path test covers 5 of the listed paths.** Missing are exp03's stimulus bank (`exp03.py:392`), the 02b replays, coevolution, geometry, viewers and benchmarks. They do record, because the hooks are in `World` and `Brain`, but the plan promised a test.
- **S4. "measure" is a ninth category that the agreed plan does not have.** Amend T0.md or D068 to say it was added and why.
- **S5. Timing is barely tested.** The only assertion is `seconds >= 0` (line 76). A fake `perf_counter` would test the parent-excludes-child rule exactly, and a monkeypatched `_sync` would test that the boundaries sync.
- **S6. `pop` is not exception-safe.** If `_sync()` raises at `accounting.py:95` (a CUDA device-side error surfaces there), the stack is not popped and later counts go to a stale category. Pop in a `finally`.
- **S7. exp03 is deferred.** That is declared, and reasonable given 03r. When it is done, `exp03.py:334` (fitness rollouts) and `:392` need categories or they fall under M1.

## Minor

- **`enabled` toggle:** a push while disabled stores start 0.0 (`accounting.py:83`). Re-enabling before the pop adds the absolute `perf_counter` value to seconds.
- **`reset()` inside a category:** the next pop raises IndexError.
- **Purity test scope:** it is CPU-only and checks only torch's global CPU generator. Adding numpy's state and a `replay_mode` CUDA variant is cheap.
- **Uncounted list:** the plan says `SparseBrain` is "listed as uncounted", but it is listed nowhere outside the plan. Geometry's `duel` also builds worlds and calls `_combat` without `tick`, so it has worlds and zero ticks. Put both in the `accounting.py` docstring.
- **JSON contents:** no totals, commit or device. The neural unit ignores network size N, which matters for deleted-neuron brains.
- **Category seconds:** they exclude breeding and logging, so they will not sum to `gpu_seconds`. Say so.
- **Empty files:** `remaps` and `report` write empty compute files.
- **Filename collisions:** stamps have one-second resolution and overwrite silently.
- **Naming:** `world.py` now has `Ledger` (energy), `self.ledger` and `LEDGER` (compute) in one module.

The core of the item (hooks, counts, nesting) is sound. The output layer is not: it reports zero seconds for real work and loses data on failure.

**item 2: not yet**