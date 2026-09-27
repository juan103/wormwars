# Re-check: 03r results and T0's GPU checks

**Checked:** the files named, my and Astra's earlier reviews, D082, `rollout.py`, `accounting.py`, `scripts/exp03.py` at HEAD and in the binding worktree, the attempt records in `runs/t0-gpu/compute/`, and 01b's and 02's bundles.

**Not checked:** I cannot run git or the tests. So the test suite, and whether the script at `bcee5a8` is byte-identical to HEAD's, are unverified.

## A. 03r results

**All my must-fix and should-fix points are resolved, and so are Astra's.**
- **The lead sentence** is now ensemble-level and says "reproduced".
- **The probe caveat** matches §10's words exactly.
- **P3** gives the registered label first, then the caveat, with the exploratory check labelled and its calculation stated (1.98 SE, 0.024, 0.072).
- **The §9 deviation** is under Deviations, with "evidence, not proof".
- **Both runs under both rules** are in the README, with P4 alone as the registered primary for 03r only.

I also checked the §9 argument against the binding worktree's `exp03.py`. Its `multiprocessing.Pool` is used only in the graph build, and the lazy imports on the measure path are of modules already loaded at start. The claim holds for the measurement stage.

### Should fix (no re-review needed)

1. **`remeasure.json` is not the script's output.**
   - `remeasure.py:55` writes only the results, to `runs/remeasure-03r.json`. That local file has no metadata.
   - The committed file's `code`, `device`, `run_at_utc` and `compared` fields were added by hand. Its timestamp (22:47:42Z) predates my last review, so it is the same run, annotated afterwards.
   - **What to change:** say so in the file, or have the script write those fields and rerun it.
2. **"Bit-for-bit" is slightly stronger than the comparison.** None of these is likely to matter, but either tighten the comparison or qualify the claim:
   - `remeasure.py:32` walks the saved keys only;
   - `:37` uses `zip`, which truncates on a length mismatch;
   - `:41` uses `nanmax`, which hides a position where only one side is NaN.

### Minor

- **`README.md:85`:** add D082 to the details line.
- **`DISCLOSURE.md:57-61`:** it still says "None of them reached the run" without the hedge, and points to the local `runs/remeasure-03r.json`.
- **`ROADMAP.md:30`** still reads "(03, borderline)", and `:36` keeps the moot sentence "If 03r does not replicate…".

## B. T0's GPU checks

### Resolved

- **Provenance:** recorded at the start, and the run refuses a dirty tree. The attempt record for the clean run (23:13:06Z to 23:41:09Z) ends on `bcee5a8` too, so no commit landed mid-run.
- **The declared cohort** (Astra): 02's N2 champions, 8 per cell, at 32 substeps. The 16 files exist.
- **Repeats and chunking are separated,** with 1, 2, 3, 4, 16 and 32 strains per chunk and a remainder of one, each with counts over 1e-4.
- **The failure of §2 and §4** is recorded, and the amendment is dated with the original text kept.
- **The CUDA ledger bound,** the regression's pass field, the historical-code deviation and the narrowed wording are all in.

### Does the gate pass under the amended contract?

**The GPU checks do.**

| Check | Result |
|---|---|
| Repeats, same composition | 0.0 in all six cases, both modes |
| Chunkings of two or more strains | 0.0 everywhere |
| Replay against default, same chunking | 0.0 |
| Ledger error on CUDA | at most 1.4e-7, all finite |
| Historical replay | 9 of 9 exact |
| Single-island regression | pass |

- **Chunking is by whole strains** (`rollout.py:117`), so rows per strain stay constant across the chunkings tested.
- **No published evolution run had a single-strain chunk in selection.** 01b and 02 used population 32 with `chunk_worlds` 512, which cannot leave a remainder of one.
- **03 and 03r use one chunk per rollout:** at most 256 genomes on 16 worlds with `chunk_worlds=4096`. D082's claim is right.

### Must fix before closing

1. **`REPRODUCIBILITY.md:33` cites a number the JSON no longer contains.** It says the 600-tick test "differed by up to 0.15". That came from the superseded run with 01b's champions at 8 substeps. The clean run's maxima are 0.073 for random genomes and 0.055 for champions.
2. **The test-suite result at the closing commit is not recorded.** The gate's first clause is "the tests pass". I asked for this last time, and D082 does not state it. Record the count and the commit.

### Should fix

3. **`accounting.attempt` is unchanged** (`accounting.py:219`). It still reads the commit in its `finally` block, with no dirty flag. D082's "every point was adopted" holds for the script only. Either fix it or record it as a known limit, since every experiment's compute record shares it.
4. **The `bmm` wording:** T0.md says the difference appears "at the row counts the world uses". The JSON shows none at 16 rows, and 4.2e-5 and 6.5e-5 at 64 and 320 rows. Say that.

### Minor

- **"3 of 512 worlds differed"** should read "exceeded 1e-4". It describes the random cohorts only; the champions show 8 and 2 of 128.
- **The input champion files** are not hashed in `T0_gpu.json`.

Neither must-fix item needs another review from me once done.

03r results: ready to publish
T0: not yet