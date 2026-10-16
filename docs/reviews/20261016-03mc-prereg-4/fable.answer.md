**Verdict: bind.** All six of my draft-3 items are fixed as described, Astra's two are fixed correctly, and the smoke on e728abe includes a real resume. Nothing in the pre-registration text needs to change. One code-only line is worth changing in the bind commit itself.

**My draft-3 items, checked**

1. **Repeat check wording matches the code.** `PREREGISTRATION.md:137-140` now says the ramp-end difference and the steady contrast, bit for bit. `scripts/p4mc.py:367` compares exactly `final` and `steady_contrast` with `np.array_equal`. Since the empty-deletion stop at `p4mc.py:611` compares the means of those two arrays, bitwise equality of the arrays is sufficient. Correct.
2. **Q-B's failure sentence uses the Holm threshold.** `wormwars/exp03/mc_report.py:197-205` names a part when its p exceeds `h["threshold"]`; `mc.holm` always sets it. The fallback sentence at `:207` is reachable only when every part cleared the threshold and an earlier question stopped the step-down, which is exactly what it says. `PREREGISTRATION.md:213-215` matches. Test at `tests/test_p4mc.py:520` covers the gap case.
3. **Units outside the plan are refused.** `p4mc.py:755-757`, tested at `tests/test_p4mc.py:531`.
4. **A failed repeat check stops before the equivalence set.** `p4mc.py:390-391`, after the repeat record is written, before `EQ.main`. Consistent with §5's "a check that stops before writing its records is not rerun".
5. **No dead smoke key.** Every key in `SMOKE_SIZES` (`p4mc.py:79-81`) is read through `R()`.
6. **The smoke includes a resume.** `runs/p4mc-smoke/record/measurements.json:614-652` has two attempts on e728abe, both clean. The ten null-deletion array files carry modification times after the first attempt's end, so they were re-measured by the second.

**Astra's two, checked**

- **Inputs bound to the commit.** `p4mc.py:196` passes `MEASUREMENT_INPUTS` with `CODE` to `require_same_code`, and `guarded()` keeps them under the clean-tree check. Test at `tests/test_p4mc.py:490`.
- **Withheld Q-B keeps a descriptive estimate.** `mc_report.py:141-153`: the question stays withheld (`p` is None), the estimate is labelled, and both batch counts are reported. Test at `:506` checks the counts and the value.

**Findings**

1. **Code only, one line, low:** `scripts/p4mc.py:196` checks the measurement inputs against `code_commit`, while `PREREGISTRATION.md:318-322` says the inputs are unchanged since the bound commit and only the code moves with an amendment. After a code amendment, an input changed between the two commits would pass. Check `MEASUREMENT_INPUTS` against `bd["commit"]` in a separate call. The text is right as written and needs no change.
2. **Note, not blocking:** the smoke's partial record was made by deleting the ten units' arrays as well as their records (the second attempt has `replaced_orphan_arrays: []`), so the orphan-replacement branch at `p4mc.py:702-703` ran in neither the smoke nor any test. A real interruption lands between the array save and the record write more often than before it. This code predates draft 4.

No GPU work run, nothing drawn.