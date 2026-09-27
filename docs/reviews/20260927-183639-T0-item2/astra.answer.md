**Section 1 is not complete at HEAD `4303a2a`.** The counters are sound for successful calls; category coverage, timing and experiment output remain incomplete.

I ran the eight non-writing accounting tests: **8 passed**. I skipped the JSON-writing test to respect read-only operation. Additional CPU checks verified substep overrides, padding, dead slots, early termination, and exact calibration/probe counts. CUDA boundaries were checked with mocks; I did not add work to the busy GPU.

1. **Must fix — Experiment accounting is neither complete nor aggregated.**  
   [scripts/exp02.py:625](D:/Claude/random/wormWars/scripts/exp02.py:625) writes only the current process’s ledger into an invocation file. Nothing sums those files into the promised experiment-level `compute.json`; the comment “summed over processes” is incorrect. [scripts/exp03.py:684](D:/Claude/random/wormWars/scripts/exp03.py:684) writes no compute ledger, nor do the 02b analysis entry point, `experiment.py`, `coevolve.py`, `ablate.py` or `tactics.py`. Their hooked work is counted in memory, then lost. [DECISIONS.md:1839](D:/Claude/random/wormWars/DECISIONS.md:1839) explicitly defers exp03. That may explain the omission, but it does not satisfy the agreed plan.

2. **Must fix — Failed attempts disappear from persisted accounting.**  
   The write at [scripts/exp02.py:629](D:/Claude/random/wormWars/scripts/exp02.py:629) occurs only after command success. A calibration failure from [wormwars/calibration.py:256](D:/Claude/random/wormWars/wormwars/calibration.py:256) therefore discards the invocation’s accumulated work when the process exits. Retrying cannot recover it. Resumable commands can likewise retain result files while losing their accounting. Additionally, second-resolution filenames can collide, and [scripts/evolve_forage.py:120](D:/Claude/random/wormWars/scripts/evolve_forage.py:120) overwrites the previous invocation’s ledger. Persist uniquely identified attempts, including exceptions, and aggregate them without duplication.

3. **Must fix — Several known activities are misclassified as `other`.**  
   No production code selects `tuning` or `final`. Examples:
   
   - [wormwars/exp02/scripted.py:196](D:/Claude/random/wormWars/wormwars/exp02/scripted.py:196): scripted parameter tuning.
   - [scripts/exp02.py:350](D:/Claude/random/wormWars/scripts/exp02.py:350): snapshot/final champion evaluations.
   - [scripts/evolve_forage.py:84](D:/Claude/random/wormWars/scripts/evolve_forage.py:84): final champion and baseline evaluations.
   - [wormwars/evo/coevolve.py:356](D:/Claude/random/wormWars/wormwars/evo/coevolve.py:356) and line 370: selection and held-out suite evaluations.
   - [scripts/exp03.py:334](D:/Claude/random/wormWars/scripts/exp03.py:334) and line 392: fitness measurements and stimulus-bank simulations.
   
   02b’s direct replays/history also lack categories. I reproduced a two-policy tuning run: four worlds and twelve world-ticks, all assigned to `other`.

4. **Must fix — Implicit `other` work has no measured time.**  
   [wormwars/accounting.py:54](D:/Claude/random/wormWars/wormwars/accounting.py:54) assigns uncategorized counts to `other`, but [line 74](D:/Claude/random/wormWars/wormwars/accounting.py:74) records elapsed time only when the stack contains an explicit context. Consequently, the tuning reproduction and a coevolution match both reported `seconds: 0.0`.

   Geometry exposes this particularly clearly: [wormwars/analysis/geometry.py:98](D:/Claude/random/wormWars/wormwars/analysis/geometry.py:98) builds a world, then line 116 directly invokes `_combat()`. Its **one world, zero world-ticks, zero neural updates are correct** for the defined units; its combat execution time is entirely absent. Add explicit measurement scopes that capture this work without inventing full world-ticks.

5. **Must fix — The tests omit explicit acceptance requirements.**  
   [tests/test_t0_accounting.py:129](D:/Claude/random/wormWars/tests/test_t0_accounting.py:129) checks only positive calibration/probe counts, not the promised hand-computed totals. The suite lacks accounting assertions for early termination, substep overrides, padded/dead slots, scripted zero updates, coevolution, geometry, 02b, stimulus-bank generation, viewers and benchmarks. Nesting tests check counts but not exclusive timing; the JSON test checks serialization but not script integration, failures or aggregation. These omissions allowed the preceding defects through.

6. **Should fix — Synchronization exceptions prevent category restoration.**  
   [wormwars/accounting.py:95](D:/Claude/random/wormWars/wormwars/accounting.py:95) calls `_sync()` before popping the frame. Mocking successful entry synchronization followed by failing exit synchronization leaves `LEDGER.current() == "probe"` after the exception. Ordinary body exceptions restore correctly when synchronization succeeds. Put stack restoration in unconditional cleanup and preserve the original exception where appropriate.

7. **Should fix — Snapshots are not accurate timing boundaries.**  
   [wormwars/accounting.py:102](D:/Claude/random/wormWars/wormwars/accounting.py:102) excludes elapsed time in open segments. With a category opened at time 0, a snapshot at 5, and exit at 10, `since(snapshot)` reports **10 seconds instead of 5**. [Line 111](D:/Claude/random/wormWars/wormwars/accounting.py:111) also drops categories whose only change is elapsed time. Current standalone `evolve()` avoids the open-segment problem because its evaluation contexts close before reporting, but the ledger API is incorrect for nested callers.

8. **Minor — CUDA synchronization assumes the current device is the work device.**  
   [wormwars/accounting.py:42](D:/Claude/random/wormWars/wormwars/accounting.py:42) calls `synchronize()` without a device. This is adequate for the current single-GPU setup, but does not establish correct timing for work explicitly allocated on another GPU.

9. **Minor — The category schema differs from the agreed plan.**  
   [wormwars/accounting.py:27](D:/Claude/random/wormWars/wormwars/accounting.py:27) adds `measure`, used by coverage, while section 1 specifies eight categories without it. Reconcile the documented schema and intended classification.

The core arithmetic checks out: [Brain.step:374](D:/Claude/random/wormWars/wormwars/brain.py:374) uses the effective override and actual `S × B`; both swarms and computed padding count. [World.tick:630](D:/Claude/random/wormWars/wormwars/world.py:630) counts every simulated batch member, and `World.run()` stops adding counts when it terminates. Snapshot-triggered holdout work is counted once; `evaluations` retains its selection-only meaning. Normal nested timing is exclusive and CPU-safe.

The hooks introduce no simulation-tensor mutations or random draws, and the CPU on/off score-identity test passes. That supports pure measurement of simulation outputs; CUDA bit identity remains unverified.

not yet