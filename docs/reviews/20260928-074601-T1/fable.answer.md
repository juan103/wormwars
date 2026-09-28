# Review of T1 plan v1

The direction is right (brain-level padding on by default, batching deferred, no class N adopted), but the profile misattributes the bottleneck and T1.2 needs a legacy-default mechanism. I ran nothing: §1-§2 numbers are taken as given, and I read `scripts/t1_profile.py`, already in the tree, as the T1.1 draft.

## 1. The profile's reading

**The attribution is partly wrong.** The plan's own numbers say the brain step is GPU-bound and the CPU-bound part is the world:

| Part | Evolution batch | 4× larger batch | Cost ratio |
|---|---|---|---|
| Brain step (T1.md:42-44) | 5.2 ms at 5 120 rows | about 20 ms at 20 480 rows | 3.85 |
| Rest of the tick | 4.1 ms at 256 worlds | about 7 ms at 1 024 worlds | 1.7 |

- The brain runs at about 11.5 TFLOPS at the evolution batch, already the kernel's rate.
- The CUDA graph's ×1.04-1.11 (T1.md:65) fits a brain step that is not launch-bound.
- So the batch-size gain comes from amortising the world's fixed per-tick cost, about 44% of a tick. The plan profiles none of it, and every engine lever in §2 is a brain lever.

**Unmeasured, most important first:**
- **Task N's shape.** E1 uses one wey per world (E1 DESIGN.md:37) and the arena stays 24 × 24 (`min_side`). Brain work per world falls 20-fold, so the world will dominate 04a. A proxy is measurable now: 02-T1 with `weys_per_swarm = 1`.
- **The world's breakdown.** A world-only tick with a `ScriptedBrain` measures it directly. Candidates:
  - two host syncs per tick (world.py:876, and `done()` at 988-999);
  - pheromone splat and diffusion every tick, though 02-T0/T1 sense it at scale 0 (world.py:888-902, grid.py:58);
  - the per-world Python loop in `_build_maps` (world.py:390).
- **Single-strain shapes.** These are 1 × 16 for 02's in-run checkpoints (exp02.py:341-342) and 1 × 64 for final hold-outs (exp02.py:356). "Negligible share" is asserted, not measured.
- **`replay_mode`'s cost.**
- **Variance.** `_rate` times one rollout, warmed up at a different shape (t1_profile.py:69-79). A ×1.06 gain and the non-monotonic R series need repeats, with median and range.
- **Script and table disagree.** The script has no 384 padding, no transposed storage (t1_profile.py:253) and no single-strain row.

## 2. The §2 decisions

I agree with every adopt, defer and reject. Four caveats:
- **"Windows time-slices processes"** is a hypothesis. Write "consistent with".
- **"Expected bit-identical" for batching is an extrapolation.** T0 tested at most 32 strains and 512 worlds, at B = 320; R = 4 is 128 strains. Add 64, 128 and 256 strains to the sweep now, which needs no `evolve_many`.
- **The dense-brain pin should test behaviour, not the call:** bit-equality with an independent reference, as tests/test_direction.py:87-108 does for legacy mode, plus repeat-identical on CUDA.
- **Record that T1 found no exact lever for 03a's gap.** It needs about ×2.5 more (ROADMAP.md:23); the best exact lever is ×1.36.

## 3. The equivalence contract

**Class E at zero tolerance is right.** Changes:
- **Shapes.** Exactness is empirical and shape-dependent: no difference at 16 rows, one at 64. The sweep has only B = 320 (t0_gpu_checks.py:106). Add B = 160 and 1 280, and Task-N-like row counts.
- **Scope.** State that it covers strains per chunk only. Worlds per strain is a separate composition, untested; test_brain.py:94-98 asserts only a tolerance for splitting the wey axis.
- **Compare brain states too,** since probes read them.
- **Record bit-equality.** `_diffs` counts worlds over 1e-4, and T0_gpu.json:133-137 holds a 2.4e-7 difference counted as zero worlds.
- **Default mode.** On a mismatch, check that the unchanged engine repeats on that case before failing the change.
- **Three legs for padding:**
  - switch on equals in-batch;
  - switch off equals the previous engine;
  - multi-strain paths are unchanged.
- **Replay leg (unsure).** `replay_mode` sets `CUBLAS_WORKSPACE_CONFIG` after cuBLAS may already be initialised (bundle.py:133-137). A fresh process would make that leg independent.

**Class N: keep the category and its rules, drop the numbers.**
- The 1e-5 per-step bound sits between the measured 1e-6 and 1e-3. It is in effect a decision to exclude TF32, the only class N lever with a gain. Say so or leave it open.
- "Champion's rank unchanged in a 40-generation run" cannot be evaluated: trajectories diverge, and near-clone elites flip rank.
- The equivalence test names no unit of analysis, and ±0.01 is five times 02's chaos floor.

## 4. T1.2

**Brain-level padding, on by default, is right.**
- Padding in `rollout` misses direct-step probes and `coevolve.play` (coevolve.py:141).
- A guard would fire on every hold-out (evolve.py:153-156).
- Default-off protects no one.

**Required changes:**
- **Legacy default.** `load_genome` builds `BrainConfig(**stored)` (genomes.py:201-204), so published champions would silently load with padding on. Follow the `chem_direction` precedent: a missing field means off, in `load_genome` and `Config.from_bundle` (config.py:257-270).
- **Config builders.** Some paths take the brain config from the script, not the genome (probes.py:148-151). 02's `task_config` must pin the switch off.
- **Published effect, measured.** 02's final hold-outs and capability probes are single-strain (exp02.py:356, 538). Replay them with the switch off against the stored per-world scores, then report the difference with it on.
- **Implementation.** Pad only the two `bmm` operands, cache the padded matrices, and invalidate them in `cut_gap` (brain.py:347-355).
- **Accounting.** T0.md:25 says computed padding counts; brain.py:375 would not count it. Decide, and keep the historical counter comparable.
- **A test that can fail without a GPU.** "CPU unchanged" passes even if the switch is ignored. Assert the batch dimension reaching `bmm` is 2 with the switch on.
- **The negative control** depends on the environment. Record it as a sensitivity check in the GPU script, not a suite assertion.

From memory, unverified: PyTorch sends a batch of one to plain `gemm` and larger batches to the batched routine, which fits the finding.

## 5. T1.3

**Deferring is right under the tripwire.** Three corrections:
- **The scope is understated.** `_play` crosses every strain with every world id (rollout.py:55-63), but each run has its own training ids. The global ledger also needs per-run accounting (evolve.py:131, 197).
- **The second trigger is vacuous.** "Over twice as long as with batching" cannot fire when the best gain is ×1.36. Evaluate it on Task N's numbers.
- **Order it against ROADMAP.md:253,** "shrink the experiment first".

## 6. T1.4

**The gate is trivially satisfied as written:** all three conditions are process conditions. In substance Track E probably fits: a 02-style run is about 10 240 strain-worlds, roughly 75 s at 139 per second. Add that arithmetic as a provisional 04a and E2 budget from the Task N proxy, and state that E1's pilot re-measures and can reopen T1.3. With that, T1 should close on these conditions.

T1 plan: approve with changes — (1) profile the world, the Task N proxy and single-strain shapes, with repeats; (2) legacy-off default in the loader, `from_bundle` and 02's config builder, plus a 02 replay check; (3) widen class E's shapes, compare states, record bit-equality; (4) drop class N's numeric thresholds; (5) specify padding's implementation, accounting and a CPU-runnable test; (6) replace T1.4's gate with a provisional budget fit and fix T1.3's trigger.