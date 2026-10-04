**Verdict: fix first.** The arms, masks, units and access mode are right. The things to fix are the compute stop and what the run leaves behind if it fails or when it ends.

## 1. Draws and masks against §3-§4: correct

- **S-mod** `wormwars/e3/assembly.py:66-69` takes the full B-task draw and keeps only keys in the seed's named edges. All 47 of E's edges lie inside B-task's 153, so the projection is exact. The 11 neurons' τ and bias come from the draw (`:72`). W2's 16 outputs are not in the draw and stay at the seed's values. Count 65 is tested.
- **S-dense** `assembly.py:64-65` writes all 153 drawn edges and 11 neurons onto the W2 carrier organism. Nothing from the `rng(0)` layout draw in `context` survives, since every grafted edge and neuron is overwritten. Count 171 = 153 + 9 τ + 9 bias. The relays can receive recurrent inputs, as §3 states.
- **P-sel** `assembly.py:58-59` is the seed with 13 selector parameters from `ga_draw`, clamped. Count 13.
- **Frozen sets** (`tuning.py:49-56`, `samplers.py:122-125`): relays' τ and bias, W2's two neurons and their outputs, the worm block, every gap junction. Verified by the tests. The `factor` argument changes only the nonzero entries, so `assert_frozen`'s default is unchanged.
- **Interface parity:** B-task's noses are at gain 1.0 and the relays at 3.0 (`samplers.py:159-162`), which is what L1's `module.json` and E's selector give the seed. Same 8 turn neurons, same W2, same carrier turn. Common across arms as §1 requires.
- **Reproducibility:** each run draws from `default_rng([seed, 0xE3C])` (`e3c.py:211`), run seeds 1 200 000 to 1 200 022 appear nowhere else in the repo, and the vectorised draws make the 32 strains independent. Tested.

## 2. Pilot against §5: correct

Runs, seeds, batching (`e3c.py:215-222`), 100 × 8, checkpoints at 0/25/50/75/99 via `evolve_batch`, block 7600-7727 (disjoint from every block in E3b-0/1/2 and all smoke ranges; the test's list is E3b-2's plus E3b-2's own blocks), training ids 30M-40M above E3b-1's 10M-20M, references on the same block (`:229-233`), criterion strictly above W2 + 1 (`:139-142`), branches (`:145-149`). All match.

## 3. Units: one unit throughout

`task_score` (`maze_world.py:408-410`) is visits summed over weys divided by colony size, which is what `colony_mean(ev["visits"])` computes in `outcomes` (`e3c.py:176`). Checkpoint `validation_mean`, generation-0 counts, `best_fitness` and both references are all colony-mean visits per wey, averaged over mazes. The floor comparison is same-block and same-unit. One caveat: `share_above_w2` at `e3c.py:257` compares per-strain means over 8 training mazes with W2's mean over the 128-maze block. It is a cross-block diagnostic, fine as labelled.

## 4. What could make the hours worthless

Organisms, mask, and shared-trail access (`e3c.py:122, 201, 231, 245`, dispatched in `rollout.py:77`) are right. The problems are elsewhere:

**The cap cannot absorb the likely runtime.** `cap_gpu_hours: 3.0` (`e3c.py:74`). From E3b-1's measured rates (`project.json:333-391`):

| Worlds per batch | s/generation | s/world |
|---|---|---|
| 4096 | 143 | 0.035 |
| 2048 | 74 | 0.036 |
| 1024 | 43 | 0.042 |

The pilot's two batches are 1536 and 768 worlds, so expect roughly 58 s + 36 s per generation, about 2.6 h for 100 generations, plus checkpoints, references, finals and the CPU preflight of 7 328 mazes. That lands near 2.8 h against a 3.0 h stop whose clock starts before the preflight (`registration.py:135-137`). The design's §5 promised a benchmark on the actual compositions first, and Astra's review asked for it explicitly. The runner has none. Worse, the clock aggregates every attempt in `runs/e3c/compute` (`e2.py:327-331`), so after a 2.5 h failure the rerun would have 0.5 h left and trip for certain.

**A failure loses everything.** The only partial write is `runs_done` (`e3c.py:225`), no `on_checkpoint` is passed, and `ctx.salvage` stays empty (`:276`). A crash in the S-dense batch discards S-mod's and P-sel's finished curves from memory. The `complete=False` branch of `decision` is unreachable (`:270`), so no record will ever say "inconclusive".

**The record is the only artefact and it is thin.** No genomes are saved, so nothing can be re-evaluated later. The per-checkpoint `validation_counts` that `evolve_batch` produces (`evolve.py:199-202`) are dropped (`e3c.py:253-254`), references and finals are stored as means only (`:233, :258`), and the generation-0 per-strain means are reduced to three numbers (`:256-257`). The power analysis needs the pilot's distributions. The per-generation `batch_seconds` are also dropped, which is exactly the benchmark §8 needs for the formal projection.

**Formal guard:** `require_formal` (`registration.py:85-91`) refuses a dirty guarded tree or an unpushed HEAD. The four new files and `tuning.py` must be committed and pushed before the run, which rule 2 wants anyway.

## 5. Fix first

1. Either add a two-generation timing of both compositions and set the cap from it, or raise the pilot's stop to about 4.5 h so one rerun can also fit. Record `batch_seconds` per generation in the record either way.
2. Pass an `on_checkpoint` that writes the learning curves so far, and set `ctx.salvage` to return the completed arms plus `"decision": "inconclusive"`.
3. Keep `validation_counts` per checkpoint, the references' and finals' per-maze `visits`, and the 32 generation-0 per-strain means per run. Optionally save the final candidates locally as `.npz`.
4. Recommended, not blocking: after training, assert every parameter at `scales == 0` equals the draw's strain 0 bitwise, per arm, as E3b-1 did. `T.assert_frozen` uses E's mask so P-sel needs `stage2_scales`.
5. Commit and push before invoking without `--smoke`.