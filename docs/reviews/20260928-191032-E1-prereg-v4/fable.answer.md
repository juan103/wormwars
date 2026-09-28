# E1 pre-registration v4: final confirmation

I ran nothing: I have no shell, so no test suite and no `git show`. I read the files at HEAD (`a84d30f`), D097, the third-round reviews and the development records. v4's commit message gives no suite count, unlike v2 and v3, so run the full suite on the binding commit.

## 1. My two must-fix points

| # | Point | Status |
|---|---|---|
| A | Crash retention and its wording | **Resolved.** Every arm is checkpointed (`scripts/e1.py:650`), and any exception or interrupt writes the result and re-raises (`653-654`). The wording matches `PREREGISTRATION.md:189` exactly (`scripts/e1.py:571-572`). The crash test drives `cmd_gate` itself (`tests/test_e1_commands.py:91-104`). |
| B | The guard-test claim | **Resolved as I stated it.** The once-only refusals, the untracked-freeze branch and both cap branches are tested through the commands. The modified-freeze branch and the zero-sample refusal are listed as untested (`PREREGISTRATION.md:40-44`). v4 added one gap of the same kind (must-fix 2). |

## 2. New defects

Nothing I found would invalidate a result. Two registered statements are wrong as written.

1. **`PREREGISTRATION.md:4` says "reviewed it twice"**, and lines 6-8 list three reviews. This round is the fourth. Drop the count ("reviewed each version below") and add v4's line.
2. **The untested list omits v4's own new refusals.**
   - The "did not start" cap branches (`scripts/e1.py:424-427`, `612-615`) have no test: no test makes the first `check_cap` call raise.
   - D097 says the list is "exactly what no test exercises" (`DECISIONS.md:2993`).
   - **Fix:** add two short tests with the existing harness (assert `SystemExit`, no marker, no rollout), or add a bullet and a dated note on D097.

## 3. Not blocking

- **The analysis is outside the handler** (`scripts/e1.py:655-672`). An exception there writes no `gate.json`. The arms survive in `gate_partial.npz`, and the error is recorded only in the git-ignored attempt file. Extend the `try`.
- **The committed-freeze check first runs real git at the formal gate** (`602-606`). If it misbehaves, the fix is a code change, which the same-code guard refuses. Run both git commands by hand with an absolute path on a tracked file before binding.
- **The command tests use the formal id ranges** (`tests/test_e1_commands.py:21-30`). They build no world at HEAD, but only because the rollout is faked and the pilot test refuses early. Rebind the ids to `SMOKE_IDS` in `_module`.
- **The checkpoint is rewritten in place** (`scripts/e1.py:575-578`), so a kill during the write loses every arm. Write to a temporary file, then `os.replace`.
- **The crash test raises only `RuntimeError`.** Changing `BaseException` to `Exception` would still pass. Add `KeyboardInterrupt`.
- **`PREREGISTRATION.md:288-289` sits under the wrong item.** It belongs to item 3, the second smoke pair.
- **A cap hit after the analysis keeps `rules` in `gate.json`** (`scripts/e1.py:666-670`), so a "not completed" record can carry `passed: true`. Report from `outcome` only.

**Correction to my third review:** I wrote that all the untested refusals come before the start marker. The zero-sample refusal (`scripts/e1.py:317-318`) comes after the pilot's marker (`430`), so it would spend the pilot. The risk is negligible, since every smoke run recorded samples.

Both must-fix items are small text or test changes, and I do not need another round if they are applied as described.

E1 pre-registration: revise (must-fix: correct "reviewed it twice" at `PREREGISTRATION.md:4`; test the two "did not start" cap refusals or add them to the untested list at `PREREGISTRATION.md:40-44`).