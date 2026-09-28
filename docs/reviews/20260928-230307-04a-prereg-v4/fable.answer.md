# Confirmation: 04a pre-registration, draft v4 (`1653809`)

**Verdict: ready to bind.** All three v3 must-fixes are fixed in the code and text, and the diff introduces no blocking problem. Two small text slips sit in guarded files and should be corrected in the binding commit; neither needs another review.

I could not run anything: tests are read, not executed, and I could not run `git diff`, so I read the current files at HEAD (`1653809`, confirmed from `.git/refs/heads/roadmap`) against my v3 review.

## 1. The v3 must-fixes

| v3 must-fix | Status | Evidence |
|---|---|---|
| 1. A killed attempt's compute | Fixed | `reconcile_kill` (`scripts/e04a.py:257`) charges marker start to last file write plus 900 s, as an attempt file in `compute/`, and re-aggregates. It runs inside `rerun_plan`, before `clock()` and `cap.check()` in all three commands. It is written once (`e04a.py:274`). |
| 2. Over-limit rerun tied to an amendment | Fixed | `e04a.py:247` requires the current plan's generations to be below the archived record's. A record without `plan` fails closed. |
| 3. Two factual slips | Fixed | §6: 820 × 2 / 1 024 = 1.6015625, and Poisson mean 3 gives 0.801. §9: 33.8 s matches `dev-projection-v1.json` (33.79). |

**Adopted suggestions, checked:**
- `apply_rerun` comes after the cap check, preflight, `task_config` and `check_genomes`, so a refused rerun is not used up.
- The projection's scratch genomes are in its archive list.
- The roadmap now says 2.99 GPU-hours and five rules.

## 2. The tests

- **Kill accounting:** the charge is 3 600 + 900 s as the test expects; the cap refusal leaves the marker unarchived; a retry does not charge twice.
- **Over-limit:** the unchanged rerun is refused with no `-attempt1` file, then passes after the generations are reduced.
- **Stopped projection and evaluation reruns:** both now exist and test the real path.
- **Not verified:** that the tests pass, or were seen failing first (rule 9). D107 says "Tested" only.
- **Not covered:** kill accounting for the projection and the evaluation. The path is shared, so I accept that.

## 3. Correct in the binding commit

1. **Wrong decision labels in the guarded runner.** `e04a.py:101`, `:236` and `:272` cite D105 for the 900 s tail, the fewer-generations requirement and the reconciliation note. All three are D107. Line 272 is also written into every reconciled record.
2. **§13's reason for not running the unguarded smoke run is stale.** It says "The GPU is paused by its owner"; D107 says it was freed the same evening. The run also never needed the GPU: unguarded smoke mode accepts `--device cpu`. Either run it or state the real reason.

## 4. Residual gaps, none blocking

- **A killed rerun is never charged.** `rerun_plan` raises "rerun once already" before reaching `reconcile_kill`. The stage is final by then, so no decision depends on it, but the compute record would understate. Reconcile before refusing, or add it by hand in the results.
- **A stopped record with no accounting file is not reconciled.** A second Ctrl+C during unwinding would leave this. It is the only gap that could affect the cap, and it is narrow. A check that some attempt file covers the marker's start would close it.
- **A kill during the extras** loses the evaluation's accounting. Nothing runs afterwards.
- **A token reduction allows one re-roll on timing noise.** Reducing by one generation satisfies the check. Stricter: the amended plan must fit the limit at the archived projection's own rates.
- **A hang longer than 900 s before the kill is undercounted.** The estimate is registered, so this is disclosed; the reason could name the kill time when known.
- **"Obligatory" meets a deterministic crash in guarded code.** Read literally, the futile rerun must happen before the amendment. One clause would settle it.
- **The rerun note can differ from the charge.** On a retry, `reconcile_kill` returns recomputed seconds, not the ones in the file.

## 5. What I would still do before binding

Run the four stages unguarded on smoke ids on the CPU. The last real `e04a.py` run in the local ledger is v1's (19:22-19:23Z). Rule 4's arm, `check_genomes` and the extras have run only with fake rollouts. A bug found by the guarded smoke run after binding costs a re-bind; found now, it costs nothing.

## What I checked

- **Code:** `scripts/e04a.py` in full, `wormwars/accounting.py`, `wormwars/registration.py`, `wormwars/e04a/evolve.py`.
- **Tests (read only):** `tests/test_e04a_commands.py` in full.
- **Text and records:** `PREREGISTRATION.md` in full, `AMENDMENTS.md`, D104-D107, `dev-projection-v1.json`, both v3 reviews, the roadmap's 04a entry. `runs/e04a/` does not exist.
- **Not checked:** test execution, CI's reported counts, the remote, and the literal diff.

**04a pre-registration: ready to bind**