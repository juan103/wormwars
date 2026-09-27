# Re-check: T0 items 3-5 (CPU) at 81a73cc

**Verdict up front: accept.** Both must-fix tests are now able to fail for the right reason, and the code fixes are correct. I could not run anything (read-only), so all of this is from reading, and D074 still does not state the full suite result.

Four small things remain. None needs another review round, but the first contradicts a claim in D074.

## My earlier points

| # | Point | Status |
|---|---|---|
| 1 | Jitter test vacuous | Resolved, with a caveat (below) |
| 2 | Isolation test vacuous | Resolved |
| 3 | Three missing island tests | Resolved |
| 4 | NaN swallowed in three places | Fixed in code; the test is weak for two of them (below) |
| 5 | Layout diagnosis understated | Resolved in D074 |
| 6 | Numerical coverage narrow | Partly resolved: champions unchanged (below) |
| 7 | Ledger gate never exercises deaths | Resolved; the test asserts that something died |
| minor | Island validation gaps, `evolve` and NaN fitness, per-tick NaN path, on/off identity | Resolved |
| minor | Flag splits a comment; flag enters bundles; item 3's test thin; suite result | Not addressed, not recorded |

## Still open

**1. Champions are still one N2 champion, final state only.**
- `tests/test_t0_items345.py:102` is unchanged: it takes `sorted(...)[0]` and checks after `w.run()`.
- Plan section 5 says "evolved champions", on N2, SH and RD. D074 says the promised coverage is "now added".
- The repo tracks 45 01b champions, including SH and RD. 02's champions are gitignored, so they can only be a skip-if-missing test.
- **Fix:** parametrise over one champion per family, checked at every tick. Otherwise record the deviation in D074.

**2. The NaN test for coevolution and exp02 is a source grep.**
- `tests/test_t0_items345_b.py:231` checks that three spellings of `max(` are absent from the source text. Only `_max_keeping_nan` is tested by behaviour.
- A renamed variable or a different swallowing pattern would pass it.
- The fixes themselves are right: `coevolve.py:198` uses `_nanmax`, and `scripts/exp02.py:348` is correct though clumsy.
- **Fix:** patch `World.energy_ledger_error` to return NaN, as the rollout test does, and call `play` with one match.

**3. The "mixed-sign corner" is mixed in `w` only.**
- `test_t0_items345_b.py:125` sets the bias to `+b_max` everywhere.
- `tests/test_brain.py:137` also randomises the bias sign, which is what pushes neighbours apart across gap junctions.
- **Fix:** one line, the same `torch.where` on the bias.

**4. The jitter test is not end to end, though its name says so.**
- It compares `_keyed_uniform` across the layouts. `_jittered` is only checked for moving points.
- If `_jittered` drew from another layout-dependent source, the test would pass.
- **Fix:** pass identical zero points through both worlds' `_jittered` and compare the (2, 2) slice exactly. With zero points, the offsets carry no rounding from positions.

## New

- **Coevolution has the same unguarded `argmax`** (`coevolve.py:362`). A NaN candidate becomes the best and enters the hall of fame. It can wait for the coevolution work, but D074's claim covers single-swarm `evolve` only and should say so.
- **The pairing test can pass vacuously on snapshots** (`test_t0_items345_b.py:83`). It loops over `r.snapshots` without asserting that the keys are {1, 2}.
- **The finiteness test uses 2 world ids per strain** across 4 strains. The plan says "8 worlds each". State which reading is meant.
- **`config.py:135` still says "costs a reduction per tick"**, which D074 corrected in the decision log only.
- **Pre-existing, outside this scope:** `coevolve.py:174` tests `lo == 0`, but `lo` is left over from the batching loop above. The recorder attaches to every batch or to none, depending on the last group's size.

## Checked and correct

- **`evolve` validation:** the order of checks is right, and all of them run before any genome is built.
- **Non-finite guard:** it sits before the snapshot, the log and breeding, and it rejects Inf as well as NaN.
- **Ledger adversarial tests:** the early-peak and early-NaN tests would fail on a final-residual implementation and on `torch.fmax` respectively.
- **Ring test:** I worked through the fitness values by hand; all three edges and the six untouched slots are asserted.
- **Isolation test:** it would fail on both global breeding and D064's block-concatenation bug.
- **Jitter docstring:** the note on run-seed bits above 32 is there (`world.py:509`).

items 3-5 CPU: accept