I read the design, the full plan, and all eight source files plus the interface YAML, loader, graphs, fields, bundle and the hygiene test. Findings below, most severe first. Tasks 3, 5, 6, 12, 13 and 14 have no substantive problems.

**MAJOR**

1. **MAJOR, Task 9, `wormwars/exp02/grid.py` `_spec`.** Ordinary 40-generation runs get snapshots `(0,)`, so `_execute` never records `holdout_g39` and never writes a `-g39.npz` file for 120 of the 128 runs. The plan's prose says every run has `holdout_g39`, but the code contradicts it. Downstream, the probes command opens the missing g39 file and the report reads a missing key. No test in the plan exercises `_execute`. Fix: snapshots `(0, 39)` for every run, `(0, 39)` plus the g79 champion for continuation runs.

2. **MAJOR, Task 11, `cmd_report` integrator tripwire.** The design asks whether the integrator changes the *interaction* by more than the chaos floor, and v2 explicitly rejected per-champion maxima. The plan computes the mean over champions of the absolute per-champion score shift at 128 versus 32 substeps, and the same for the perturbed run. Both numbers are chaotic rescorings of single champions on 16 worlds, so they will be roughly equal by construction and the tripwire is uninformative in both directions. Fix: have `integrator_rescore` return per-world scores, build unit vectors under each integrator, recompute I(T0), I(T1) and the task contrast, and compare the shift in those to the same shift under the perturbation.

3. **MAJOR, Task 11, `max_drive_error`.** It reads `c["achieved"]` from calibration.json, which is the fitting seed's in-sample result and is within 2% by construction. The tripwire can never fire. The plan stores `validation_seed1` but never uses it, and Task 12 step 3 quietly relaxes it to 5%. Fix: use the validation report, and better, measure the achieved drive of each run's actual generation-0 population, since those use seeds 20000 onward, not seed 0 or 1.

4. **MAJOR, Task 11, `t1_memory_vs_memoryless`.** Estimate, lo and hi are all the same number: the difference of in-sample tuning scores. There is no interval, so "matches within its interval" reduces to a sign test. The tuning scores are also optimistically biased and unequally so, since the memoryless grid has 36 points and the memory grid 18. Fix: use `per_seed_holdout`, which already holds both controllers on the same 22 × 64 worlds, and bootstrap the paired per-world difference.

5. **MAJOR, Task 11, `paired_bootstrap` on the anchor.** SH graphs have the A cell in run 0 only. The bootstrap resamples runs within a graph with replacement, so whenever run 1 is drawn twice the SH mean for the A cell is `np.mean([])`, which is NaN. That happens in about 82% of resamples across 6 graphs, and `np.quantile` returns NaN for the interval. The tripwire itself uses only the point estimate, so it will not crash, but the reported interval is garbage. Also, "01b's sign" is hard-coded as positive; read it from 01b's results file instead.

6. **MAJOR, Tasks 2 and 9, `brain_config_for_graph`.** All six N2perm runs use `init_permutation_seed = 1`, so the strength control is one specific permutation replicated six times. That is the single-shuffle confound the design avoided for SH by using six graphs: a lucky or unlucky permutation is indistinguishable from "strengths matter". Use one permutation per run, or 3 × 2 to mirror SH, and calibrate each permutation (or state that N2perm shares one calibration and why). Cheap now, expensive later.

**MINOR**

7. **MINOR, Task 8, `evolve` checkpoints for continuation runs.** With `holdout_every=10` an 80-generation run evaluates at 0, 10, ..., 70, 79 and never at 39. `late_cells` takes the intersection of generations across a cell's runs, so T0-M0 and T1-M0, the two cells that matter most, lose the generation-39 point and fit five-parameter curves to four points. The continuation checkpoints at 40 to 79 are stored but never used to "check the asymptote" as the design says. Fix: also evaluate when `g in snapshots`, and add a continuation check to the report.

8. **MINOR, Task 9, batch order versus the design's cut order.** The design cuts MS, then continuation, then the anchor's SH arm, then R2. The plan's batches drop whole replicate units instead, which is a better structure, but the order means N2 runs 2 and 3 are lost before SH's second replicate. Either reorder so N2 replicates are spread through the schedule, or say in the pre-registration that the cut order changed and why.

9. **MINOR, Task 11, `units`.** N2perm records are silently dropped, so the strength control is never analysed. Add N2perm minus N2 and N2perm minus SH on T1-M0 with the same bootstrap.

10. **MINOR, Task 11, `tripwires`.** The convergence threshold is `7 / 3`, but `late_cells` counts eight cells including A.

11. **MINOR, Tasks 10 and 11, T1 temporal tripwire.** Only the first half is computed. The design also requires champions to survive when the unrelated signal is removed. `collision_off` and `food_mirrored` are collected but unused. Define the second half now and compute it.

12. **MINOR, Task 10, `integrator_rescore`.** The chaos floor perturbs the bias by 1e-6, a persistent parameter change, not the initial state as the design says. It is a reasonable proxy, but say so.

13. **MINOR, Task 1, `_food_constant` and `_probe_food`.** The constant is the grid mean at tick 0, roughly 0.5 to 1.6, while the audit's sensed level is 0.14 to 0.39, so the "no information" probe drives champions at 2 to 5 times their usual input. Consider the audit's mean sensed level instead. Also `W - 1 - x` reflects about `(W-1)/2`, one cell off the arena centre; `W - x` is the true point reflection. Cosmetic.

14. **MINOR, Task 4, `_ranked_triples`.** Distance is computed on the triple *mean*, so a hub pair and two isolated pairs can match M0 exactly. Either sum per-pair distances or state the rule in the pre-registration. Separately, `test_shortcut_pairs_have_more_direct_read_out_weight` asserts a property of the data, not the code, and can fail if R1 or R2 absorbs a top-3 direct-weight pair.

15. **MINOR, Task 7, `DriveReport`.** The design asks for signed command distributions; the report has only |mean|, clip share and displacement. Add signed mean and the share of reversing weys.

16. **MINOR, Task 9, checkpoint suite.** `CHECKPOINT_IDS` are fixed ids, but maps depend on (run_seed, id), so the "fixed diagnostic suite" differs between units. Either pass a fixed seed to the checkpoint evaluation or say the suite is fixed per unit only.

17. **MINOR, Task 9, resume.** A partial trailing line in `records.jsonl` after a kill makes `json.loads` raise on restart. On resume, `per_batch` is measured from the first, possibly partial, batch, so a later full batch can overrun the cap by one batch. Both are small; guard the parse and seed `per_batch` from the records' wall times.

18. **MINOR, design integrity measures not in the plan.** No test that in-memory and saved-and-reloaded rollouts match per condition type. No rank stability of checkpoint populations, and no populations are saved to compute it. No replay of best and worst champion per cell. Generation-0 strength runs on N2 and three of six SH graphs, not "every graph". Note each as deferred or add it.

19. **MINOR, budget.** By rough scaling from the 4.9 s per generation figure, gen-0 strength (48 rollouts of 2048 world-runs), valence (8 of 4096), 128 champion probe sets and the 22-seed diagnostics look closer to 1.5 hours than the design's 0.5. The pilot should time diagnostics and probes, not only two evolution runs.

20. **MINOR, Task 6, `ScriptedBrain.initial_state`.** Returns a CPU tensor regardless of device. Harmless because `step` ignores `v`, but `neuron_state` would fail if anyone called it before the first tick on CUDA.

21. **MINOR, Task 9, anchor settings.** "T0 with 01b's settings" is implemented as exp02 settings plus pheromone on: 400 ticks, 32 substeps, 64 held-out worlds. That is what the design table implies, but the pre-registration should say the anchor is not 01b's tick count or held-out count.

**Fine as written**

- Task 1: default path is bit-identical; intake split is exact by construction since `taken` equals the sum of per-wey intake. Only point 13 applies.
- Task 3: `remapped_spec`, clash checks, `interface_hash` and both doc fixes are correct against the current YAML and `_build_current`.
- Task 5: `edge_hash`, the manifest check and the relabelling test are correct; the 01b champion path exists; the sign-flip algebra in `flip_food_signs` is exact without gap junctions and broken exactly by cross-group gap edges, as the design states.
- Task 6: `_play` reproduces `rollout` bit-for-bit; the atanh trick makes scripted commands exact through `_read_motors`.
- Task 8: the 80-generation run's generation-39 snapshot equals a 40-generation run's champion, since RNG use and train ids are identical up to that point and the final re-evaluation returns the same argmax.
- Task 9: seeds are crossed as claimed, with one seed per (graph, run) in every cell, and generation-0 populations are therefore identical across mappings within a unit, which is a strong pairing.
- Task 11: the paired bootstrap keeps unit vectors together and unit offsets cancel exactly; the variance-component estimator is the standard one-way ANOVA form.