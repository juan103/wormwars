## Verdict: ready to bind

No must-fix remains on the design, the rules or the code's behaviour. I have two text-only corrections I would make in the binding commit; neither changes a rule, so neither needs another round from me.

I could not run the suite or `git diff` (no shell). I read the working tree, which the session's git status shows clean at `1e4b7f5` for tracked files. Test and sabotage results are taken as reported.

## Must-fix

None.

## Correct in the binding commit (text only)

1. **`PREREGISTRATION.md:42` says "each test was seen failing first", which the decision log contradicts.**
   - D121 (`DECISIONS.md:3603`) records one regression pin written after its fix. D122 (`DECISIONS.md:3629-3630`) records that the fourth v4 test "passed at once".
   - Both were sabotage-checked, so rule 9 is met, but the sentence is false as written and becomes immutable at binding.
   - Change to something like: "each test was seen failing first, except two pins of existing behaviour (D121, D122), which fail under their sabotage".
   - I missed this in v3, where it was already true of D121.
2. **`scripts/e2.py:121-122` still says the reserve means the extension "can never use up the budget of the primary result".**
   - This is the claim §6 now corrects, in a guarded file.
   - Change to "an admission estimate for the first attempt (§6)".

If you bind without these, a dated note in `AMENDMENTS.md` covers both.

## Suggestions

- **Extension-sourced champions are still not exercised through `evaluate`** (`tests/test_e2_commands.py:802-828`). With the fake scores every tie goes to the formal checkpoint, so all sources are "formal". I traced the path by reading and found it correct.
- **The admission check reads `projection.json` without the guards** (`scripts/e2.py:903`). Using `require_projection(a, prov)` would check it is committed and unchanged.
- **A cap reached mid-stage has no E2 test** (`scripts/e2.py:615-617`). The pre-registration only claims the start-of-stage case, so the text is accurate.
- **§15's "not taken" reason is weakened by v4's own test.** It says guard-on tests need a clean pushed tree and CUDA, but the new skip test stubs those. The same stubs would cover a reconstructed record.
- **Run the guarded smoke chain before the formal projection.** The projection runs once, and a wiring fault found afterwards would need an amendment and a new projection.
- **A skip exits through `SystemExit` with a message,** so the accounting records that attempt as "failed". Say so in the results.
- **Nit:** §11 gives 10:07:57 for the fourth smoke run's start; the marker and the accounting both say 10:07:59.

## Checked and found correct

- **§6, option (a):** the text matches `scripts/e2.py:903-910`. It covers the first attempt only, exempts the rerun, and discloses the remaining risk. The exemption test would fail without the exemption.
- **Skip record through the guards:** it now carries `provenance_at_start`, and `require_earlier` (`:426-436`) falls through to `require_committed`, `require_same_code` and `require_same_env`. The evaluation handles a skipped extension with no arms.
- **Plain-run refusal:** `run_stage:591` refuses before `requires`, so Astra's sequence (kill, interrupted setup, plain run) no longer writes a skip. `--rerun` cannot bypass the skip for an extension that never started, or rerun a skipped one.
- **§10's "final":** includes the skip, and the definition of a used rerun matches `rerun_state`.
- **§11:** `runs/e2-smoke/compute/` holds four chains of 8 attempts, at `8966e5b`, `12725de`, `99f06a9` and `31beeda`, the last one dirty, with none after 10:08:29. No E2 id or formal seed appears in the smoke records.
- **Killed rerun with a real partial record:** the genome files are written before the partial record, so champion indices stay valid wherever the kill lands.
- **Counts and arithmetic:** 79, 17 and 14 tests by my count; the budget sums to 17 870 s, with 142 checkpoints; the README cites D117-D122.

## Not checked

- Whether the tests pass, and whether the sabotage checks were run.
- The ENOMAD citations.