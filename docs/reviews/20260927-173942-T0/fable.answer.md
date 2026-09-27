I've finished the review. I had no shell or git access, so I could not diff 54ad0a9 or run the tests; everything below comes from reading the current tree on `roadmap`.

## Part 1: island fixes (54ad0a9, D064)

**Are the three bugs real?** Yes, as far as the current code, tests and D064 show.
- **Mixing:** `island_of` is interleaved (`evolve.py:122`), so writing children back in blocks would mix islands from the second generation.
- **Culled migrants:** a migrant copied over the worst slot with stale `fit` is removed by truncation.
- **Dale sign:** `dale_sign` is per strain (`brain.py:138`) and `clamp_` re-imposes it (`brain.py:207-208`), so a migrant keeping the destination's signs has its weights re-signed at the next mutation.

**Are the fixes correct?** Yes by reading.
- `_breed_islands` (`evolve.py:201-215`) writes each island back to its own slots, and the islands partition the population.
- `_migrate` (`evolve.py:222-242`) reads from the original `genome` and `fit`, so the ring is synchronous. It copies all five fields and returns a new `fit` without modifying the caller's.

**Did the single-island path change?** Not by reading: with `islands == 1` the migration branch is skipped (`evolve.py:167`) and `_breed_islands` returns `breed(...)` at once (`evolve.py:196-197`), with no extra draws from the generator. The cited test does not show this, though; see S1.

**Do the three match what a careful reader would find?** Plausibly yes; they are the three most visible defects. Other candidates a reader might have meant are in S3, and D064 should say they were examined.

### Must fix
None.

### Should fix

**S1. The one-island test is a tautology.** `tests/test_evo_islands.py:74-83` compares `_breed_islands` with `breed`, but with one island the former just calls the latter. It cannot detect a change to `evolve`, and it compares only `w`.
- D064's claim "the one-island path is unchanged (tested)" (`DECISIONS.md:1644-1645`) rests on it.
- Better: re-run the first 2-3 generations of a published run from its bundle config and seed, on the same device, and compare `best` and `mean` with the stored log (`runs/m5/N2-run00-log.json` and others exist).

**S2. The tests check less than their names say.**
- `test_migrants_carry_their_own_fitness_into_breeding` (`test_evo_islands.py:48-59`) checks `new_fit[1] == 7.0` and never breeds. Add `_breed_islands(moved, new_fit, ...)` and assert that `p.w[6]` survives in island 1's slots.
- The end-to-end test (`test_evo_islands.py:86-96`) asserts only lengths and finiteness. Add a multi-generation run through `evolve` with all sigmas 0 and `migrate_every` above `generations`, checking every final slot descends from its own island's generation-0 members.

**S3. Unvalidated island settings.**
- `islands > population` gives an empty island and `torch.randint(0, ...)` fails in `breed`.
- `migrants` at or above half an island's size lets `worst` overlap that island's own best (`evolve.py:231-232`).
- Per-island `max(1, elites // islands)` and `max(2, truncation // islands)` (`evolve.py:208-209`) change total selection pressure. With `elites=3`, two islands give 2 elites in total and four give 4; `elites=0` becomes 1 per island.
- Validate at the top of `evolve` and document the rule. This matters if an island arm is ever compared with a single-island arm.

### Minor
- `_migrate` indexes torch tensors with numpy arrays (`evolve.py:233-241`) while `_breed_islands` converts first (`evolve.py:211`). I believe this works on CUDA but no test runs it there.
- `gen_t` is unused in `_migrate` (`evolve.py:218`).

## Part 2: T0 plan (`docs/foundations/T0.md`)

### Must fix

**M1. Section 4 calls CPU the deterministic mode and expects old champions to replay exactly (`T0.md:50-54`).**
- Published runs were scored on CUDA: `tests/test_direction.py:161` says "01 was scored on CUDA; bit-exactness needs it".
- The repo already defines its exact mode as `replay_mode()` on the same GPU and pinned environment (`wormwars/evo/bundle.py:126-145`, `docs/REPRODUCIBILITY.md:40-51`).
- A CUDA champion replayed on CPU will not match its log exactly, so the test as written fails for a reason that is not a bug.
- Revise to: CPU exact for fresh save/load/replay; CUDA under `replay_mode()` exact; old champions replayed on the device recorded in their bundle.

**M2. The 1e-4 tolerance is under-specified and the repo's own evidence conflicts on it (`T0.md:55-57`).**
- It does not say which comparison (run-to-run on one GPU, chunking, or CPU vs CUDA), which statistic (per world or per-strain mean over how many worlds), or what episode length.
- `docs/REPRODUCIBILITY.md:25-28` measured 5.96e-08 across chunkings on CUDA for 8 strains x 8 worlds.
- `docs/REPRODUCIBILITY.md:33-36` says default CUDA runs "can differ visibly" after a few hundred ticks.
- `experiments/02-screening/RESULTS.md:260` reports a chaos floor of 0.0018 on an aggregate statistic from a 1e-6 bias perturbation.
- I am unsure whether 1e-4 holds at 600 ticks; I expect it to fail for some worlds. Declaring a number is right, but declare it per comparison with the statistic, world count and tick count, and say in advance what an exceedance means.

**M3. Fix the energy-ledger bound now (`T0.md:61-62`).** A gate with an undeclared bound is not a gate.
- The documented tolerance is relative: `err / start_energy_total < 1e-5` (`tests/test_world.py:51,63`, `tests/test_combat.py:101`); the coevolution test uses 1e-4 (`tests/test_coevolve.py:139`).
- The rollout's `ledger_error` is absolute (`rollout.py:74`), so the units do not match.
- Declare relative 1e-5 and have `_play` return the normalised error or the scale.

**M4. `_play` is the wrong choke point for world simulation (`T0.md:16-19`).** "Every rollout and scripted controller goes through it" is false. Worlds are also built at:

| Site | How it steps |
|---|---|
| `wormwars/evo/coevolve.py:168` | `world.run` |
| `wormwars/calibration.py:103,198` | `world.tick()` directly |
| `wormwars/exp02/probes.py:155` | `world.tick()` directly |
| `wormwars/exp03/measures.py:49` | `world.tick()` directly |
| `wormwars/analysis/geometry.py:98` | not checked |
| `scripts/exp03.py:392`, `experiments/02b-champion-analysis/analyse.py:132,207` | not checked |

- `calib.achieved_drive` runs inside every exp02 run (`scripts/exp02.py:335`), so it is per-run compute that `_play` never sees.
- Count in `World.__init__` and `World.tick` (`world.py:579`) instead: every path goes through `tick`, and no list of exceptions is needed.
- Count actual ticks, since `run` stops early when all worlds are done (`world.py:936`).

**M5. The neural-update unit leaves out the batch axis (`T0.md:20`).** `Brain.step` takes `v [S, B, N]` (`brain.py:336-360`), and B (worlds x weys) dominates. Count S x B x substeps, or a probe with B=1 weighs the same as a rollout. State that scripted brains count zero.

### Should fix

**S4. The champion is chosen by a second, uncounted evaluation (`evolve.py:172-174`).** It re-evaluates the same population on the same ids as the last generation. On default CUDA the argmax can differ, so the champion may not be the strain named in the last log entry.
- The only test is on CPU (`tests/test_exp02_evolve.py:60-66`).
- Either reuse the last `fit`, recorded as an equivalence-checked change, or count it as "final" and add a champion-to-log pairing test.

**S5. The saved population's `fitness` is not per strain (`evolve.py:171,187`).** It holds the best score per generation (length `generations`) beside `population` genomes. I found no reader of it, so it is latent. Rename it and save the real per-strain fitness, then add a test that it is index-aligned.

**S6. The inheritance test will only cover the operations it names (`T0.md:43-46`).** Every operation hand-lists the fields:
- `evolve.py:86,215,242`;
- `coevolve.py:250`;
- `coevolve.py:279` and `:354`, which drop `dale_sign`;
- `exp02/probes.py:22,30,145`;
- `deletion.py:37`.

Add `Genome.cat` and `Genome.assign` that iterate over the fields, and scan for `Genome(` outside `brain.py`.

**S7. `genome_sha256` is written but never checked on load (`genomes.py:94`, `160-217`).** Verifying it is a cheap integrity check. The hash excludes `dale_sign` (`brain.py:253-255`).

**S8. No experiment-level roll-up.** The plan puts `compute` on `RunResult` only. Calibration, tuning and probes run outside `evolve`, often in other processes, so say where their counts are stored and summed. Also test that nothing in `evolve` lands in "other".

### Minor
- `holdout_mean` is a copy of `holdout_best` (`evolve.py:141`).
- `rollout` does not return `food_start`, though `rollout_brain` does (`rollout.py:83-84`, `131-139`).
- `coevolve.play` tests `lo == 0` with a stale loop variable (`coevolve.py:172`).
- The NaN/Inf check should include evolved champions and the extreme genomes already in `tests/test_brain.py:113`.

**Completeness against the roadmap:** every T0 bullet has a section. The gaps are in specification (M1-M5), not coverage.

island fixes: accept (the code is correct; S1-S3 should follow, and D064's "tested" claim for the one-island path needs S1).
T0 plan: revise (M1-M5).