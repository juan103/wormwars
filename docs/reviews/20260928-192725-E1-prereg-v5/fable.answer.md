# E1 pre-registration v5: final confirmation

I ran nothing: I have no shell, so no test suite and no `git show HEAD`. I read the working tree, which the starting git status shows as matching HEAD for tracked files. The 577-test count is taken from the commit message, not checked.

## 1. My v4 points

| Point | Status |
|---|---|
| Must-fix 1: "reviewed it twice" | **Resolved.** `PREREGISTRATION.md:4-9` lists every version, v4 included. |
| Must-fix 2: the "did not start" cap refusals | **Resolved.** `tests/test_e1_commands.py:231-244` drives both commands and asserts the wording, no marker and no rollout. It fails if either `try` (`scripts/e1.py:424-427`, `617-620`) is removed or moved after the marker. |
| Analysis outside the handler | **Resolved.** `scripts/e1.py:655-674`; tested at `tests/test_e1_commands.py:198-211`. |
| `rules` kept in a "not completed" record | **Resolved in code.** The analysis is merged only on completion (`scripts/e1.py:676`). The test is weak, see §3. |
| Checkpoint rewritten in place | **Resolved.** `scripts/e1.py:575-583`; the test at `tests/test_e1_commands.py:247-259` fails on an in-place write. |
| Crash test raised only `RuntimeError` | **Resolved.** `tests/test_e1_commands.py:214-228` fails if the handler is narrowed to `Exception`. |
| Command tests used the formal id ranges | **Resolved.** `tests/test_e1_commands.py:29`. |
| §7 bullet under the wrong item | **Resolved, as far as I can tell.** Item 3 reads coherently (`PREREGISTRATION.md:295-303`); I could not diff against v4. |
| Zero-sample refusal comes after the marker | **Resolved.** `PREREGISTRATION.md:51-52`. |
| Committed-freeze git commands run by hand | **Open by design.** It is a commitment (`DECISIONS.md:3040-3041`), not yet an event. Record its output when done. |

## 2. New defects

Nothing I found would invalidate a result, and the code matches §4 and §5 as written. One registered statement is false as written.

**`PREREGISTRATION.md:41-43` lists two function-level tests under "through the stage commands themselves".**
- The atomic-checkpoint test calls `m.checkpoint` directly (`tests/test_e1_commands.py:250`, `257`).
- The same-code test calls `m.require_same_code_as_pilot` directly (`tests/test_e1_commands.py:286`, `290`). No test drives `cmd_gate` with that guard on, because every command test uses `smoke=True, guarded=False`.
- D098 repeats the claim under "New command-level tests" (`DECISIONS.md:3027-3032`).
- The same block attributes the pin refusals to `tests/test_e1_script.py` (`PREREGISTRATION.md:44-46`). That test is at `tests/test_e1_commands.py:186-194`.
- The project itself treated the command-versus-helper distinction as material in round 3, which is why I count this as must-fix.

**Fix (text only):** move the two bullets and "pin" to a third group, "as functions, in `tests/test_e1_commands.py`", and add a dated correction to D098 in the next decision. Coverage is unaffected: the tests exist and test what they name. The guard's wiring in `cmd_gate` is exercised by the guarded smoke run, on the positive path only.

## 3. Not blocking

- **The cap-after-analysis test does not pin my v4 point.** `tests/test_e1_commands.py:146-147` checks the outcome and the counts. The only `"rules" not in doc` assertion is in the analysis-crash test, where `rules` never exists, so it cannot fail. Add `assert "rules" not in doc and "failed_rules" not in doc` at line 147.
- **A checkpoint failure now ends the once-only gate.** `os.replace` can raise `PermissionError` on Windows when a scanner or sync tool holds the target open. The handler would record "the run stopped" and the gate worlds would be spent. The passing command tests are some evidence against it, but in a temp directory. Make sure the guarded smoke gate completes all 16 arms, and that `experiments/E1-navigation/` is not under a sync tool.
- **`not_completed` writes `gate.json` non-atomically** (`scripts/e1.py:594`). A second interrupt during that write leaves a truncated record. The arms survive in `gate_partial.npz`.
- **The docstring of `tests/test_e1_commands.py:1-4` is stale:** it describes v4's tests only.

I do not need another round for the must-fix item if the text is changed as described.

E1 pre-registration: revise (must-fix: at `PREREGISTRATION.md:41-46`, list the atomic-checkpoint, same-code and pin tests as function-level tests in `tests/test_e1_commands.py`, with a dated correction to D098).