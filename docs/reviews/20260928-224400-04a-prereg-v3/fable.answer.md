# Review: 04a pre-registration, draft v3 (`082210e`)

**Verdict: revise, narrowly.** Every v2 must-fix is fixed in the code. Three small gaps remain, one of them created by v3's new kill rerun. None needs a redesign; a confirmation of the diff is enough, not a full round.

I could not run anything. Tests are read, not executed.

## 1. The v2 must-fixes

| v2 must-fix | Status | Evidence |
|---|---|---|
| Formal seeds | Fixed | Formal 1 105 000, projection 1 109 000, smoke 1 108 000 (`scripts/e04a.py:76,96,101`); the pilot is pinned to 1 104 000 (`e04a_pilot.py:41`). The derived streams (2 × seed, 2 × seed + 1) are disjoint too. `runs/e04a/` does not exist and the experiment folder holds no formal record. |
| Effective brain configuration | Fixed | `check_genomes` (`e04a.py:574`) runs before the marker. `load_genome` lets a file override only padding (`genomes.py:223`), and `select`, `moved` and `Brain` all carry `genome.cfg`. |
| Rerun rule | Fixed, with residue | Kill, projection, archived genomes, reason and second-stop refusal are all in `archive_attempt` and tested. The residue is must-fixes 1 and 2. |
| `AMENDMENTS.md` | Fixed | Exists; not in `GUARDED`. |
| Record before genome save | Fixed | `_train_not_completed` (`e04a.py:444`). |
| Decoy error record | Fixed | `extras` (`e04a.py:712`). |
| Exposure wording, ledgers | Fixed | §9 and the exposure record say "not directly verified"; both ledgers are committed. |

## 2. The tests

- **The second-stop test is now real.** The rerun itself crashes, so the last refusal comes from the `-attempt1` check.
- **The padding test** changes metadata only and asserts no marker.
- **Untested:** the evaluation's `--rerun`, and the projection's rerun after a stop or a kill. `test_the_projection_is_rerun_after_a_stop_or_over_its_limit_only` covers only the completed and over-limit cases, despite its name.

## 3. New in v3

- **`training_plan`** gives 2 000 and 82, and matches `evolve_batch`'s checkpoint condition.
- **The budget table** adds up to 10 760 s.
- **§6's figures:** 820 episodes is right, and a Poisson mean of 3 gives a share of 0.801.

## Must-fix

1. **A killed attempt's compute is never counted.**
   - `accounting.attempt` writes its file in `finally` (`accounting.py:273`), which a hard kill never reaches. `CapClock` reads only `compute.json`.
   - v3 registers the kill rerun, so §8's "counted by the accounting across all attempts" is false on that path. The cap decides "not completed".
   - With a projection at its 4.5-hour limit, two killed batches could put real compute near 9 hours while the clock reads about 4.6.
   - **Fix:** on the kill path, write an estimated attempt record (start marker to the last file written) and re-aggregate before the cap check, with a test. Or state the gap in §8.
2. **The over-limit rerun is not tied to an amendment.**
   - §8 says "on an amended commit". `archive_attempt` accepts an unchanged one, and the test reruns that way.
   - A projection at 4.52 hours could be rerun unchanged until timing noise passes it.
   - **Fix:** require the current plan's generations to be below the archived record's, or reword.
3. **Two factual slips in text that binding makes permanent.**
   - §6: "nearly every episode reached exactly 2" is wrong. The lowest passing mean, 1.60, has 820 episodes at exactly 2 and 204 at none.
   - §9: "v1's projection 41 s". The committed record says 33.79 s. 41.3 s is the whole smoke folder's total, from an ignored local file, and it includes the CPU smoke run the same sentence lists separately.

## Suggestions

- **Run all four stages unguarded on smoke ids before binding.** The local ledger's last `e04a.py` run is at `8e21cc7` (v1). Rule 4's arm, `check_genomes` and the extras have run only with fake rollouts.
- **Archive after the refusal checks.** A rerun refused by the projection, environment or cap check has already consumed the one rerun, and the later plain run records `rerun: None`.
- **Make the rerun obligatory** after a crash or kill. "May" leaves a choice after partial curves or arms are visible.
- **Say "one rerun in total"** for the projection, and by how much generations are reduced.
- **Projection genomes** are not archived on a rerun, and nothing discards them, against the comment at `e04a.py:339`.
- **`secondary` and `equivalent_k`** run inside `analyse`, so an error there voids a finished hold-out. §7 registers this; wrapping them is safer.
- **`decoy_capture`** fails for a whole run if one world has no unfinished leg.
- **A crash caused by guarded code** has no path: the fix moves the binding commit, and a completed projection cannot be rerun. Say what happens.
- **Roadmap:** still 2.75 GPU-hours, and omits rule 4.

## D106

Skimmed only. Hashing array content rather than zip bytes is the right remedy.

## What I checked

- **Code:** `scripts/e04a.py` in full, `wormwars/e04a/evolve.py`, `registration.py`, `accounting.py`, `evo/genomes.py`, and the relevant parts of `brain.py`, `rollout.py` and `world.py`.
- **Tests (read only):** both 04a files in full, and the last test of `test_e1_task.py`.
- **Records:** the exposure record, one ledger, the arm timing, v1's projection, and the pilot's seeds.
- **Not checked:** that the tests pass or were seen failing, the diff between v2 and v3, and the remote.

**04a pre-registration: revise**