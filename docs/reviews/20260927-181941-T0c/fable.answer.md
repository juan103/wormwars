## Scope

Read-only, no shell: I read the code, tests, plan and record at the current tree but could not run the tests. The claims "each test failed before its fix" and "the rigged test fails on the old code" are taken from D067, not verified.

## Are my points resolved?

**Plan amendments: all three are in v2.1.**
- Pure-measurement accounting: `T0.md:55-56`.
- Migrants capped at half the smallest island: `T0.md:153-154`.
- `best_sha256` in `GenerationLog`: `evolve.py:37,147`.

**Should-fix 1–8: all resolved.**

| # | Point | Where |
|---|---|---|
| 1 | Hash pinned, uniforms and radius tested | `test_t0_pairing_confirm.py:175-202` |
| 2 | `assign` checks strain count and Dale parity | `brain.py:174-177` |
| 3 | Champion compared by full hash, with a rigged evaluator | `test_t0_pairing_confirm.py:84-107` |
| 4 | D066 corrected on the champion evidence | `DECISIONS.md:1714-1716` |
| 5 | Snapshot, holdout and mutation tests added | `test_t0_pairing_confirm.py:110-150` |
| 6 | Every graph's single-genome files checked from stored arrays | `test_t0_pairing_confirm.py:161-172` |
| 7 | Per-strain `genome_sha256s`, nicknames as labelled fallback | `genomes.py:136,225-230` |
| 8 | Hand-built genomes outside the library recorded as exceptions | `DECISIONS.md:1785-1787` |

**Minors and record items:** `with_params` clones everything, `flat()` iterates `PARAMS`, zero generations is refused, and the 02 artefacts, `gpu_seconds` and the 03r worktree are recorded.

**Astra's points,** as far as reading can tell, are also addressed: replay qualification, the 600-tick label, aliasing, full hashes, explicit jitter coordinates, and the full fitness vector.

## Did the fixes introduce anything new?

Nothing blocking. Five small items:

1. **Jitter draws changed a second time.** Going from one hash of a flat index to three hashes of coordinates changes the draws for every layout, single-swarm included. D067's "only multi-swarm layouts were affected" is true of the defect, not of the fix. Record that jitter outputs are comparable only from `59217da` onwards. `scripts/exp03.py` has no jitter, so 03r is untouched.

2. **`best_sha256` is never anchored independently.** The champion, holdout and snapshot assertions all compare against `best_sha256`, which `evolve` derives from the same `argmax(fit)`. One line closes it in the saved-fitness test: `genome_hash(seen["pop"], int(np.argmax(seen["fit"]))) == r.log[-1].best_sha256`.

3. **The 153-champion check is overstated and not reproducible.**
   - Old logs carry only `best_nickname`, so the check can only have been by nickname, about 12 bits. `T0.md:82` and D067 should say so.
   - I found no script or test for it. `runs/` holds 164 log files and at least 160 champion files, so state which 153 were included.

4. **The jitter-key test is not end-to-end.** It calls `_keyed_uniform` with test-only `n_swarms`/`n_weys` arguments. The property holds by construction, since `_jittered` uses the same function. Astra's actual reproduction was a (1,3) match beside a (2,2) match, and that would be the stronger test.

5. **`assign` now raises inside `_migrate` for unsupported island settings,** for example population 3, 2 islands, 2 migrants. That is correct, but the message is obscure until the §6 validation lands in item 5.

**Still open from before, unrecorded:** run seed bits above 32 are dropped from the jitter key (`world.py:510`). Harmless for the seeds in use.

T0 plan v2.1: confirmed
item 1: accept (items 1–3 above are owed before the T0 gate; none changes a used path)