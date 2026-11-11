**Verdict: fix then run.** The engine changes and the arms read correctly, but the driver has one crash at formal size, several checks that can false-stop or pass vacuously, and the smoke evidence for rule 7 is weaker than your summary says.

Limits of this review: I could not run `git diff` or any code, so the "defaults are no-ops" judgement comes from reading the current files, not the diff.

## 1. The smoke "old against new" is new against new

In `stage_equivalence`, `--smoke` sets both roots to `ROOT`. `runs/e5-1a-smoke/equivalence.json` records `"reference_worktree": {"path": "D:\\Claude\\random\\wormWars", "smoke": true}`, and I found no worktree at `../wormWars-e5-1ref`. The 1 045 identical arrays show determinism only.

- The only real regression evidence so far is E5-0's 68 arrays against the stored `runs/e5-0/reference-old.npz`.
- The smoke's training-shape mixed-against-alone check had `captures_mean: 0.0`, so it compared zeros.
- **Fix:** let the smoke use the 7d25460 worktree (CPU, minutes) and run it before committing. Correct the summary wherever it is quoted (rule 4).

## 2. Bugs that make a stage wrong

**a. `composition_rows` crashes at formal size (must fix).** `idx = [i % gen.n_strains for i in range(S)]` never advances across batches. With the 16 E4s-1 champions, the validation shape (S = 4) plays only genomes 0–3 and the suite shape (S = 8) only 0–7. `np.concatenate(played[lab][0])` then raises on an empty list for the rest. The smoke had 2 genomes and no validation shape, so it could not see this.

**b. The same function sizes its intervals wrongly (must fix).**
- At the training shape each genome gets 64 × ceil(n/1024) episodes, about n/16. The half-width is then about 0.12, not 0.03, so with σd near 1 every genome fails the ±0.10 rule by construction.
- At n = 512 the 1 024 slots wrap, so each champion plays 32 worlds twice and the interval counts 64.
- The reference is 1 × 64 or 1 × 192, not 1 × 512, whenever a genome's count is below 512.
- Decide the rule and write it in §14. I would pool per (family, shape) with n sized from σd as the stop, and report per-genome differences. Giving each genome n worlds costs up to about 1.6 M episodes.

**c. Two ±0.10 checks in the CUDA stage are not sized from σd (must fix).** These are the mixed world at the training shape (one batch, 1 024 pairs) and H1-ghost against Task N (512 worlds). If σd is about 1, the first false-fails about 12% of the time and the second about half the time; at 1.5 the first fails most of the time. I do not know σd: the smoke gave 0 everywhere at 40 ticks. Size both like the others.

**d. The bench times generation-0 populations (must fix; the cap is set from it).** §7.4 asks for timing "with route respawns", and §6 notes a run's time depends on its captures. Generation 0 scores about 0.1 per episode, so the capture path (host syncs, `_route_for`'s Python loop) barely runs. The projection for 28+ batches is therefore a lower bound, and an under-set cap withholds O1. Add a B-construction batch (32 copies of a C champion, 4 runs), use it for B, and give the test arms a range.

**e. The projection's cut (4) term.** `16 * 2 * 8 * PL.SUITE_WORLDS * 17` is 2.23 M episodes. The suite for 16 runs is 278 528, and by my count all per-run evaluation for them is about 0.7 M. The term overstates the saving, and `stage_cap` picks the cut level mechanically from it.

**f. Non-finite states are not detected in Task H.** `evolve_batch` tests `isfinite(count)` and `isfinite(progress)`. On Task N, progress carried a NaN position; here captures are integers and progress is zeros, so neither can fire. `world.py`, `brain.py`, `hunt.py` and `play.py` have no finiteness check. Only the ledger remains, and I have not traced whether a NaN brain state reaches it. §6 names "a non-finite state" as a failure that withholds O1, so add a check on the final `pos` and `v` in `play` and raise in `TaskHRollout`.

**g. The cap is enforced only inside the pilot's `evolve_batch`.** §14 says 6 hours for "every stage and device together". No other stage calls `cap().check()`, and the CPU sides of the CUDA checks (up to 8 192 worlds each) are likely the largest cost. Put the check in the `play` helper.

## 3. Smaller points

- **`same_ranking` can fail spuriously.** It compares a stable argsort of the exact integer-weighted fitness with one of the float formula. Two strains with equal numerators from different slots could differ by an ulp in the formula. Rank on integer numerators and keep the 1e-12 value check.
- **Training-shape equivalence needs scoring genomes.** §7.1 says "deliberately frequent captures"; add the C champions tiled to 128 × 8.
- **Untested world sizes.** `paired_check` can build 4 × 8 192 = 32 768 worlds in one `HuntWorld` on the GPU, and sensitivity builds 65 × 256 = 16 640. The smoke's largest was far smaller. Chunk them or do a one-tick memory run first.
- **State level** covers only the first 4 and 8 champions at the validation and suite shapes, not 16.
- **The 64-world trace checks** make "99% of worlds" mean all 64. Say so or use more worlds.
- **P's stage check** tests `w` magnitudes only; the unit test covers `g`. Add `g` to the stage.
- **Design text:** §5 says "the last checkpoint (475)", but `evolve_batch` also checkpoints at 499. Fix this in the pre-registration.

## 4. Engine changes

- **`evolve_batch` without `weights`:** both branches fall through to the old expressions. No-op.
- **`HuntWorld` with one pin:** `np.ndim(pinned) == 0` gives `bool(pinned)` and the old branch. No-op.
- **`play` with shared ids and a scalar pin:** same tiling as before, plus `max_index`. No-op.
- **`PreyBrain` of one kind:** `step` is unchanged; only `_route_for` now goes through `RouteTable`.
- **Route cache:** same stream key `[world_seed, 0x5E7B, life]`, same rejection loop, and every other input (spacing, box, start bytes) is in the memo key. It is the same draw. The test compares against a verbatim copy, which is weaker than the real old-against-new run in section 1.
- **`MixedPrey`:** the wall follower is stateless, the walk's draws are keyed per world and tick, and route state is masked. I found no cross-world leak.
- **Guards:** `same_as` and the `init_*` exemption are sound. The cost per `Genome.cat` is negligible.
- **Weights, blocks, seeds, admission, masks, lesion, P, A0, A0r, B:** all match §3, §4 and §6. I did not check `PL.GA`'s sigmas against E4s-1's driver, only against `config.py`'s defaults; a test pinning them would help.

## 5. §14's numbers

- **Acceptable as fixed:** the check and mutation seeds, 7d25460 as the old engine, σd from 512 worlds, the 10⁻³ path tolerance, 6 bench generations (with fix d), run 0 per pilot graph, mutants at G-N2's scales.
- **Should change:** step 7's wording (fix b); the cap's enforcement (fix g).
- **Mildly liberal:** step 5's normal interval (z = 1.645) favours passing the stop, because the static slot's 32 worlds carry a third of the weight. A t interval with Satterthwaite degrees of freedom is the conservative choice; I would accept either if stated.

## Fixes before E5-1a runs

1. Run the real old-against-new once, and correct the smoke summary.
2. Rewrite `composition_rows` (crash, per-genome counts, duplicates, reference shape) and fix the rule in §14.
3. Size the training-shape and ghost CUDA checks from σd.
4. Bench a scoring population; correct the cut (4) term.
5. Add a finiteness check to the Task H rollout.
6. Enforce the cap in every stage.
7. Rank on integer numerators; add champions to the training-shape equivalence.