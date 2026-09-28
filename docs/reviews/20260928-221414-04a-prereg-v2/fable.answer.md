# Review: 04a pre-registration, draft v2 (`68f8aa3`)

**Verdict: revise.** The v1 must-fixes are fixed in the code, with one partial exception (the rerun rule). Two new gaps remain, both small to fix: the pilot ran on the formal run seeds, and the rerun rule in the text is wider than the code. I recommend keeping 1 000 generations and 02's optimizer.

I could not run anything. The tests, hashes and timings are read, not executed.

## 1. Are the v1 must-fixes fixed in the code?

| v1 must-fix | Status | Evidence |
|---|---|---|
| Genome files against the connectome rule | Fixed | Files go to `runs/e04a/`, ignored by `runs/**/*.npz`. `check_genomes` checks hashes and the regenerated population before the marker. |
| Text against code | Fixed | File names, "never breed", `equivalent_k`'s edges and the projection rule now match. |
| Projection enforced and tested | Fixed | `require_projection` in `cmd_train`; `--generations` is gone; marker, cap and once-only are present and tested. |
| `require_committed` exercised | Fixed as a function | Tested in a temporary repository. It is still skipped under `--smoke --guarded`, so its first live use is formal batch A, before the marker. Acceptable. |
| E1 inputs bound | Fixed | In `GUARDED`, hashed at each stage, compared before the evaluation. |
| Outcome wording | Fixed | `share_lower_bound` is Clopper-Pearson, and the test asserts 0.2453 for 6 of 12. |
| Development records committed | Fixed | With the gaps in section 2. |
| Engine equivalence | Fixed | Declared and run; both records show every array identical. |

Astra's must-fixes also hold in the code: `use_smoke` rebinds the training range, the fixture passes `folder=tmp_path`, rule 4 is in `run_rules` with Astra's case tested, and the progress tests are direct.

## 2. Development records

**Moving the training range is the right remedy.** It also makes the reconstruction's exactness immaterial.

- **"Reconstructed exactly" is stronger than the evidence.** The world counts match (48 per batch), but the run used uncommitted code, so the ids rest on assuming the schedule function was the committed one. A CPU replay against the surviving genome hashes would confirm it.
- **The cited attempt records are not in the repository.** `runs/**/compute/` is ignored.
- **`dev-arm-timing.json` says "4 repeats"** but lists 3 values, and its script loops 3 times.
- **The pilot record lacks what rule 1 measures.** It keeps validation means only, and no genomes, so neither the share of episodes with at least 2 targets nor cue use can be checked.

**The disclosure is incomplete on one point, which is must-fix 1 below.**

## 3. The plateau

**Keep 1 000 generations, 02's optimizer and every threshold.**

- **The pilot's numbers support §9.** The mean over the 8 runs was 1.63 at generation 25, 1.76 at 100, 1.78 at 175 and 1.73 at 199. The highest single checkpoint was 2.11.
- **"Many runs may not" understates it.** If counts were Poisson, which I have not checked, rule 1 needs a mean near 3. No run came close.
- **More generations will not fix it within the cap.** The slope is about +0.1 targets per 175 generations. About 1 500 generations is the most the 4.5-hour limit allows, and it would remove the rerun headroom.
- **Any optimizer change now would be a guess,** chosen on 8 runs that share the formal seeds. The design fixed 02's optimizer, and E2 exists to compare optimizers at equal work.
- **My reading of the pilot, untested:** the population's mean count is 0.3-0.7 while the best is 1.5-2.5, so most offspring lose most of their parent's performance. That points to mutation step size and noisy selection, which is E2's subject.
- **The run is still worth its 3 GPU-hours.** It adds the 200 to 1 000 generation range, the unshaped arm, and the first measurement of whether these partial navigators use the cue.

**Add one sentence to the registration:** the authors expect "not passed" or "some runs passed". If the owner would rather not spend the slot on a likely null, the alternative is to run E2 first, not to tune inside 04a.

## 4. New problems in v2

- **Rule 4 is sound.** The constant is each world's arena mean of the starting scent, so it is within the normal range. It removes level information as well as direction, so "helped by the real cue" is the right wording and "no direction information" is incomplete.
- **The rerun rule:** must-fix 2.
- **The projection formula** matches the code. Its figures (2 000, 82) are hard-coded separately from the evolution settings, with no test tying them together.
- **Local-only genomes** are the right trade-off. They make the local files a single point of failure between training and evaluation.
- **`extras` can fail without a record:** `decoy_capture` runs outside any `try` (`scripts/e04a.py:652`), against §7's text.

## Must-fix

1. **The pilot, the development projection and the smoke mode used the formal run seeds.**
   - `scripts/e04a_pilot.py:40` and `scripts/e04a.py:299` call `run_specs("A")`, and the pilot record shows seeds 1 104 000 to 1 104 007.
   - Generation 0 is drawn on the CPU from the seed, so formal runs 0-7 start from the populations the pilot played for 200 generations, with the same mutation streams.
   - §9 does not say so. By the standard applied to the 24 worlds, this is the larger exposure.
   - The guarded projection would repeat it.
   - **Fix:** move `seed_base`, give the pilot, projection and smoke mode their own base, add a test, and disclose it in §9.
2. **The rerun rule in the text is wider than the code.**
   - **A hard kill leaves a deadlock.** With a marker and no record, `--rerun` says "has not run" (`archive_attempt`, `scripts/e04a.py:213`) and a plain run says the marker exists. On Windows with CUDA this is the likely crash.
   - **`project --rerun` is ignored.** `cmd_project` never reads the flag, though the projection is stage 0.
   - **The over-limit path cannot be followed.** An amendment changes guarded files, so the same-code check fails and the projection cannot run again.
   - **Amendments have no declared place.** Any edit to the guarded `PREREGISTRATION.md` between stages blocks the next stage.
   - **The "once" limit is untested.** The test's last refusal comes from the completed outcome, not from the `-attempt1` check.
   - **Fix:** implement these cases or narrow the text, and name an unguarded amendments file.

## Suggestions

- State the expectation, and what follows each outcome (E2, then a new registration on fresh hold-out ids).
- Restrict interrupts to external causes written down before the rerun. Partial validation curves are visible during training.
- Archive the stopped attempt's genome files too; the rerun overwrites them.
- Rerun the pilot with genomes and per-world counts saved, then probe the plateau genomes on smoke ids.
- Record each arm's mean score and path length in the equivalence records, to show the check is not vacuous.
- Report development compute separately from the cap (the pilot alone was 0.29 GPU-hours).
- Correct the replay row of the budget: 16 replays at about 10 s is about 160 s, not the remainder of 100 s.
- Test the non-finite check at validation on its own.
- Update the roadmap's status, which still describes v1.

## What I checked

- **Code:** `scripts/e04a.py` in full, `wormwars/e04a/evolve.py`, `wormwars/registration.py`, `rollout.py`, `final_progress` and the constant probe in `world.py`, `Genome.random` and `mutate`, the accounting's attempt records, `.gitignore`.
- **Tests (read only):** `test_e04a_commands.py`, `test_e04a_evolve.py`, the end of `test_e1_task.py`, `test_registration.py`.
- **Records:** all six development records, one smoke attempt record, and §9's numbers against the pilot record.
- **Not checked:** that the tests pass, that the first two draws of a size-8 schedule equal a size-2 draw, and the state of the remote.

**04a pre-registration: revise**