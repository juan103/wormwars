**Verdict: confirmed.** All three parts of my v4 must-fix are done as described, and so are the two suggestions you took up. I ran nothing and could not run `git diff`; I read the tree at HEAD, which is now `389daec` ("archive the v4 reviews"), one commit past `d7447ac`.

## v4 items

| Item | Status | Evidence |
|---|---|---|
| Smoke includes singles | **Done** | `p4m.py:694-695`: `entries[:3]` plus the first three singles, inside `if SMOKE:` only |
| A test stops inside the follow-up | **Done** | `test_p4m.py:201-220` stops at the last gap-pass check and requires the chemical rows, `len(top) - 1` gap rows, and the chemical arrays |
| Lesions smoke at the clean commit, follow-up non-empty | **Done** | `runs/p4m-smoke/lesions.json:41-43` is stamped `f71f6f9`, `dirty: false`, with three chemical and three gap rows for RIAR, AIZL, RIAL |
| Q1 files regenerated (suggestion) | **Done** | Both are stamped `f71f6f9`, clean, and `tails.json:15` records the directory |
| Decay test mocks the rebuild (suggestion) | **Done** | `test_p4m.py:192` |

- **The follow-up really ran.** The compute records show 765 440 neural updates at `f71f6f9` against 412 160 before, which is 13 histories against 7: exactly the six follow-up deletions.
- **The follow-up numbers are sensible.** RIAR with only its chemical edges deleted gives P4 0.869, matching the full deletion; with only its gap junctions deleted it gives 0.944, matching intact.
- **The test can fail.** Without the array save, `np.load` finds no file; without the partial write, the follow-up key is missing.
- **The plan's Q1 and Q1b figures all match the regenerated files.** I rechecked every one against `tradeoff.json` and `tails.json`.

## Not verified

- That the 19 tests pass, and that the new one failed under sabotage. The file does hold 19 tests.
- The contents of `lesions-follow-up-per-genome.npz`; it exists, but it is binary.
- That `f71f6f9` changed nothing else. The other four commands were last smoked on the v4 working tree, which is sufficient only if the diff is what you describe.

## Before the run (no further round needed)

1. **The branch is not pushed.** There is no `origin/p4-mechanism` ref, loose or packed, so `require_formal` will refuse to start. Pushing is the owner's call.
2. **`PLAN.md` does not record the v4 round.** Its status stops at v3, and its title still says v4. Line 217's "Each boundary has a test" was false at `e818ff0` and is true now. Add a dated v4/v4.1 line before the run, since `PLAN.md` is guarded.
3. **The test checks `final` but not `steady`, and no gap arrays.** Astra asked for "both per-genome arrays". It is a one-line strengthening, optional.
4. **The lesions estimate may be 10-15% low.** `delete_neurons` loops over 2 048 strains in Python per deletion, and the 8-strain CPU smoke cannot show that cost. This is my estimate, not a measurement; the cap's headroom covers it.
5. **03m still has no `DECISIONS.md` entry or README.** Both are needed before main, not before the run.

**03m plan: ready to run**