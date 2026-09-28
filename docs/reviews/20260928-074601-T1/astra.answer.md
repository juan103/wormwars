I agree with the main direction: retain dense FP32, avoid a port, prefer brain-level padding, and defer multi-run infrastructure. I would change the reproducibility handling, equivalence tests, profiling requirements, and closure gate before approving v1.

I reviewed the committed plan at `98dc4f7` and the relevant code. I have not independently reproduced the exploratory timings.

1. **The profile supports a likely bottleneck, but overstates the diagnosis.**

   The brain-time fractions are arithmetically consistent: 5.2/9.3 ≈ 56%, and 20/27 ≈ 74%. The implementation also confirms two `bmm` calls per substep. However, isolated brain timing is an estimate of its rollout contribution, not an attribution measured inside the rollout. ([T1.md:42](D:/Claude/random/wormWars/docs/foundations/T1.md:42), [brain.py:387](D:/Claude/random/wormWars/wormwars/brain.py:387))

   **873 ms CPU versus 538 ms GPU does not establish that the CPU is the limit.** CPU time can include dispatch and waiting, and CPU/GPU execution can overlap. Require a timeline showing launch gaps, synchronization, and device occupancy before making that causal claim. Synchronized wall-clock measurements should remain the throughput authority. [PyTorch’s CUDA timing documentation](https://docs.pytorch.org/docs/2.12/notes/cuda.html#asynchronous-execution) explains the asynchronous execution issue.

   There are concrete omissions worth measuring:

   - `World._reap()` evaluates a CUDA tensor as a Python Boolean every tick; `World.done()` does likewise during the run loop. These are host-device synchronization points. Measure their waiting time before concluding that launch overhead alone explains the gap. ([world.py:873](D:/Claude/random/wormWars/wormwars/world.py:873), [world.py:988](D:/Claude/random/wormWars/wormwars/world.py:988))
   - Attribute the world’s remaining time: sensing/odour convolution, assignment packing, movement, splatting/field updates, and world construction. Include CPU map generation and result transfers. `_play` performs several CPU transfers and scalar extractions. ([world.py:631](D:/Claude/random/wormWars/wormwars/world.py:631), [rollout.py:55](D:/Claude/random/wormWars/wormwars/evo/rollout.py:55))
   - Measure a complete short evolutionary run, including breeding, checkpoints, final evaluations, and hashing/logging. Single-strain evaluations occur repeatedly during evolution; they are not just final 64-world hold-outs. Experiment 02 uses **16-world checkpoints**, plus separate final evaluations. “A negligible share” is currently unsupported. ([evolve.py:149](D:/Claude/random/wormWars/wormwars/evo/evolve.py:149), [exp02.py:341](D:/Claude/random/wormWars/scripts/exp02.py:341), [grid.py:29](D:/Claude/random/wormWars/wormwars/exp02/grid.py:29))
   - Profile Task N when available. Its one-wey, 300-tick workload differs substantially from the current 20-wey, 200-tick benchmark. ([E1/DESIGN.md:36](D:/Claude/random/wormWars/docs/E1/DESIGN.md:36), [E1/DESIGN.md:85](D:/Claude/random/wormWars/docs/E1/DESIGN.md:85))

   T1.1 should specify warm-up, repeated unprofiled timings with spread, timing boundaries, actual ticks executed, relevant numerical settings, and peak allocated/reserved memory. “Memory is not a constraint” should be scoped to the measured configurations.

2. **Most §2 decisions are sound; several explanations need narrowing.**

   Keep 512 as the default: the measured 6% gain at 1,024 is limited to larger evaluations and does not accelerate the stated evolution workload. Retain 1,024 as an experiment-specific option if its measured budget warrants it.

   Deferring CUDA graphs is reasonable given only 4–11% improvement **on the brain**, which implies a smaller rollout improvement. Rejecting fused GEMM and neuron-dimension padding is also reasonable given their measured costs. Excluding TF32 from this exactness-focused milestone is sound.

   Reject the tested CSR implementation because its repeated outputs differ. But scope the finding to that implementation, inputs, and environment; it does not establish that every sparse implementation is nondeterministic. Also rerun the diagnostic with `replay_mode(warn=False)`: the existing helper defaults to warning-only enforcement, so “raises no error inside `replay_mode()`” is weak evidence by itself. ([T1.md:65](D:/Claude/random/wormWars/docs/foundations/T1.md:65), [bundle.py:126](D:/Claude/random/wormWars/wormwars/evo/bundle.py:126))

   Reject concurrent processes for this workload because they showed no useful measured benefit. The throughput table alone does not establish Windows scheduling as the cause.

   Finally, replace “the framework is not the bottleneck” with **“these measurements do not justify a framework port.”** Dispatch and launch overhead are precisely areas where execution strategy can matter. Likewise, multi-run batching is the largest measured exact candidate, not demonstrably the only remaining exact lever. ([T1.md:78](D:/Claude/random/wormWars/docs/foundations/T1.md:78))

3. **Keep class E at zero tolerance; remove the binding class N thresholds for now.**

   Class E is appropriate, provided the comparison means **old versus new on each device separately**, within a pinned environment—not CPU versus CUDA. The observation that tested batches with at least two strains agree is not a guarantee for all shapes. PyTorch explicitly does not promise bitwise equivalence between batched and sliced computations. ([T1.md:83](D:/Claude/random/wormWars/docs/foundations/T1.md:83), [PyTorch numerical accuracy](https://docs.pytorch.org/docs/2.12/notes/numerical_accuracy.html#batched-computations-or-slice-computations))

   Require an independent pre-change reference. Comparing two executions of the modified engine can establish internal consistency while missing a shared regression. Also require matching shapes, finite outputs, and direct brain-state comparisons for paths without world scores. T0’s current composition helper returns **only scores**, so merely rerunning it does not implement T1’s promised energy/alive/eaten contract. ([t0_gpu_checks.py:80](D:/Claude/random/wormWars/scripts/t0_gpu_checks.py:80))

   The proposed class N numbers are premature:

   - Relative `1e-5` lacks a defined norm, absolute allowance near zero, and justification.
   - A ±0.01 energy-score margin does not transfer to Task N’s arrival counts.
   - `32 genomes × 512 worlds` does not by itself define valid uncertainty: shared worlds and repeated observations within genomes require an explicit analysis.
   - Spearman ≥0.99 can still permit changes among the best candidates.
   - “Champion’s rank unchanged” after an independently evolving 40-generation run is ambiguous once the candidate populations diverge, and one run cannot establish optimizer equivalence.

   Keep the requirement for a separate, preregistered numerical-change plan and explicit engine provenance. Declare its margins when the actual change and scientific endpoint exist. ([T1.md:93](D:/Claude/random/wormWars/docs/foundations/T1.md:93))

4. **Brain-level padding is my preferred D082 decision, with important conditions.**

   It covers direct brain probes as well as worlds and avoids duplicating world simulation. Rollout-level duplication is a reasonable fallback to investigate, but it misses direct `Brain.step` callers. A warning or guard documents the inconsistency without resolving it. Default-off leaves new experiments exposed to it. I therefore favor **default-on for new work, effective on CUDA**, conditional on equivalence passing.

   **Historical loading must default missing metadata to off.** Currently, `load_genome` reconstructs `BrainConfig(**stored)`. Adding a default-true field would silently change old files. `Config.from_bundle` and `brain_config_for` also need explicit legacy handling, following the existing chemical-direction precedent. Changing only T0’s historical replay invocation is insufficient. Persist explicit values in new artifacts and make deliberate re-evaluation under the new policy distinguishable from historical replay. ([genomes.py:158](D:/Claude/random/wormWars/wormwars/evo/genomes.py:158), [genomes.py:201](D:/Claude/random/wormWars/wormwars/evo/genomes.py:201), [config.py:257](D:/Claude/random/wormWars/wormwars/config.py:257))

   Padding is **exact against the old multi-strain reference**, while deliberately changing affected old singleton evaluations. State that explicitly; it is not a globally behavior-preserving engine change.

   The proposed test can fail, but needs strengthening. Require all three comparisons: padding off versus old singleton behavior; padding on versus old multi-strain behavior; and unaffected multi-strain behavior versus the old engine. Add direct brain tests at actual row counts, including probes, evolution, checkpoints, hold-outs, and Task N shapes. Cover silencing, cut gaps, and substep overrides because these are supported brain operations. ([brain.py:326](D:/Claude/random/wormWars/wormwars/brain.py:326), [brain.py:347](D:/Claude/random/wormWars/wormwars/brain.py:347), [probes.py:107](D:/Claude/random/wormWars/wormwars/exp02/probes.py:107))

   The “switch off must differ” negative control should require **a known failing CUDA fixture**, not divergence in every configuration: T0 already records zero difference at 16 rows. This fixture is environment-specific. ([T0_gpu.json:499](D:/Claude/random/wormWars/docs/foundations/T0_gpu.json:499))

   **Count the padding.** T0 explicitly says computed padding counts as neural work. The current hook uses the incoming state shape, so duplicating afterward would undercount unless changed. This matters for E2’s equal-work comparisons. ([T0.md:23](D:/Claude/random/wormWars/docs/foundations/T0.md:23), [brain.py:375](D:/Claude/random/wormWars/wormwars/brain.py:375))

   Finally, failure of brain padding should trigger diagnosis, not automatic approval of rollout padding. A two-world-composition fallback still needs its own equivalence evidence.

5. **Deferring multi-run batching is right and consistent with the tripwire.**

   T1 is explicitly exempted by the roadmap, but that exemption should not justify speculative infrastructure. Build only after a measured, scientifically adequate experiment cannot fit its declared cap and batching is expected to resolve the shortfall. Fix the minimum experimental scope and cap first; otherwise “fit the budget” can become circular. ([ROADMAP.md:62](D:/Claude/random/wormWars/ROADMAP.md:62), [T1.md:142](D:/Claude/random/wormWars/docs/foundations/T1.md:142))

   Remove or redefine the “over twice as long” trigger: the best reported batching speedup is 1.36×, so that branch cannot fire under the current evidence.

   If triggered, restrict the first implementation to compatible configurations and preserve each run’s world IDs as well as its seeds and RNG streams. Two contract details need correction now:

   - “Every run’s log bit-identical” must exclude timing/provenance fields: `GenerationLog.elapsed_s` necessarily changes.
   - Combined batches can delay batch-wide early termination. Test runs that finish at different times and account for any extra simulation; equal final scores alone do not establish equal work.

   ([evolve.py:27](D:/Claude/random/wormWars/wormwars/evo/evolve.py:27), [world.py:988](D:/Claude/random/wormWars/wormwars/world.py:988))

6. **T1.4 is not a real budget gate as written, and T1 should not close on those conditions alone.**

   “Scripted, therefore fits any budget” is false. World simulation and tuning still cost time. Moreover, E1’s mandatory pilot includes generation-0 neural genomes, not just scripted controllers. ([T1.md:157](D:/Claude/random/wormWars/docs/foundations/T1.md:157), [E1/DESIGN.md:136](D:/Claude/random/wormWars/docs/E1/DESIGN.md:136))

   Make this a staged gate: T1.1/T1.2 completion authorizes a **bounded E1 pilot**; that pilot measures scripted and neural Task N throughput; then a committed calculation lists planned tuning, training, checkpoints, final evaluations and diagnostics against an explicit cap, with headroom. Resolve the current ordering language so this pilot can occur before final T1 closure. ([E1/DESIGN.md:6](D:/Claude/random/wormWars/docs/E1/DESIGN.md:6), [ROADMAP.md:78](D:/Claude/random/wormWars/ROADMAP.md:78))

   Alternatively, explicitly amend the roadmap to close T1’s engineering work while transferring the budget gate to E1/04a. Either is honest. Calling the current conditions satisfaction of the existing measured-budget gate is not.

T1 plan: approve with changes (measure world/synchronization and full-run costs; defer class N thresholds; preserve legacy loading; strengthen independent equivalence tests and padding accounting; tighten T1.3’s trigger; replace T1.4 with an explicit measured-budget gate).