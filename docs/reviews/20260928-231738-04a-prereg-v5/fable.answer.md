I've finished reading the runner, the tests, the pre-registration, D108 and the local smoke ledger; here is the confirmation.

# Confirmation: 04a pre-registration, v5 (`627b886`)

**Verdict: ready to bind.** Astra's v4 gap and my v4 points are fixed in the code, and the diff adds no blocking problem. Three text corrections belong in the binding commit; none needs another round.

I could not run anything, including the tests and `git diff`. I read the files at HEAD (`627b886`, confirmed from `.git/refs/heads/roadmap`) against both v4 reviews.

## 1. The v4 points

| v4 point | Status | Evidence |
|---|---|---|
| Astra: stale total after a kill between the two writes | Fixed | `reconcile_kill` writes to `*.json.partial`, which the aggregate's `*.json` glob does not read, then `os.replace` (`scripts/e04a.py:296-298`). An existing record is reused with its stored charge (`:293-294`). `write_aggregate` runs unconditionally (`:299`). |
| Fable: decision labels | Fixed | Lines 101, 237 and 290 now cite D107 or D108. The remaining D104 and D105 labels are correct. |
| Fable: §13's stale reason | Fixed | §13 says what v4 claimed and why it was wrong. |
| Fable: a killed rerun is never charged | Fixed | The reconciliation runs before the "rerun once already" refusal (`:242-244`). |
| Fable: a token reduction passes | Fixed | `amended_plan_fits` requires fewer generations and a fit at the archived rates (`:261-269`). |
| Fable: the rerun note can differ from the charge | Fixed | The stored seconds are returned. |
| Fable: "obligatory" meets a deterministic crash | Fixed | §8 sends a guarded-code crash to the amendment route. |
| Astra: "ends normally" | Fixed | §8 says "when its cleanup handlers run"; D107 is left as written and D108 notes it. |

No other stage can read the stale total in Astra's scenario: after a killed stage, every later stage is refused until the rerun, and the rerun reconciles first.

## 2. The tests

By reading, each new test would fail on v4's code:
- **Aggregate lost** (`tests/test_e04a_commands.py:329`): v4 skipped the rebuild, so the cap check would read 0 and the rerun would start.
- **Killed rerun** (`:357`): v4 refused before charging, so the total would not rise.
- **Fit at its own rates** (`:346`): v4 accepted any reduction. The margin is thin but correct: 4 generations × 100 s = 400 s against a 360 s limit.

Not verified: that they pass, or D108's sabotage check.

## 3. Correct in the binding commit

1. **"Rebuilt before every cap check" overstates the code.** It appears in §8, §14 and D108. The aggregate is rebuilt only inside `reconcile_kill`, so only when a rerun finds a marker and no record. An ordinary stage start and the per-rollout checks read `compute.json` as it stands. Either say "rebuilt at every reconciliation, before the cap check that follows", or rebuild in `clock()`. I prefer the second: it makes the sentence true and closes the same gap in `acct.recorded`, which writes the attempt file and then the aggregate.
2. **The killed rerun's charge is not automatic.** It happens only if the operator invokes `--rerun` once more and takes the refusal. §8 should name that step, or the compute record will understate.
3. **§9's "v5's CPU smoke run" ran on a dirty tree.** The four attempt files (`runs/e04a-smoke/compute/20260928T2111*.json`) record commit `1653809` with `code_dirty: true`. The rest of the claim checks out: CPU, all four stages completed, "04a: not passed", no errors in the extras, 34 arms on 16 worlds. State that it ran on the working tree before the v5 commit.

Optional: `REGISTERED["rerun"]` still gives the looser over-limit condition, and it is copied into every record.

## 4. Residual gaps, none blocking

- **A stopped record with no accounting file is still not reconciled**, and the text does not disclose it. A second Ctrl+C during unwinding produces it. It remains the only gap that can affect the cap. Close it or add one sentence to §8.
- **A kill during the extras** still loses the evaluation's accounting. Nothing runs afterwards.
- **`write_aggregate` is not atomic.** A kill mid-write leaves an unreadable `compute.json`; the next cap check crashes, so it fails closed.
- **Who decides a crash is "caused by the guarded code"** is a judgement made after the crash. It is disclosed and the amendment route is costly, so I accept it.

## What I checked

- **Code:** `scripts/e04a.py` (lines 1-530 and 640-914), `wormwars/accounting.py`, `wormwars/registration.py`.
- **Tests (read only):** `tests/test_e04a_commands.py`, lines 1-500.
- **Text and records:** `PREREGISTRATION.md` in full, `AMENDMENTS.md`, D105-D108, both v4 reviews, the local smoke ledger.
- **Not checked:** test execution, CI, the remote, the literal diff.

**04a pre-registration: ready to bind**