## 1. Verdict: bind after fixes

The fixes are three one-line pins and no redesign. None changes a threshold or an outcome rule; each closes a case where the text leaves the implementer a choice that could move a registered count. I ran nothing; the code checks below are by reading.

1. **Name census qualifiers in the state-to-goal rule (§6).** It says "For a champion"; qualifiers also get clamp assays and "working" (S2-c), and can be mirrored. Write "for a champion or a census qualifier".
2. **Say that a "not applicable" clamp assay does not pass (§6).** "Working" needs "both clamp assays pass", but the assays are "not applicable" when s < 0.1 or a goal phase never occurs. Add "not applicable counts as not passed, so not working".
3. **Give the reset's unwritten worlds a rule (§6).** If `at_a` never returns to 0, or returns within 10 ticks of the episode's end, no write happens. State that such a world stays in the denominator and fails. This reading is forced by "at least 70% of the worlds with a first confirmed visit by tick 500", but it is a final gate, so pin it.

If you prefer not to touch the draft again, fixes 1 and 3 are the only readings the text supports, and fix 2 is the only sensible one. I would still pin them, because the text can never be changed after binding.

## 2. My first-draft fixes

All fifteen are resolved.

| Fix | Status |
|---|---|
| 1. Reset timing | Resolved: timed from the level's end, listed in §12 |
| 2. State-to-goal assignment | Resolved, bar fix 1 above |
| 3. B-task nose symmetry and τ range | Resolved |
| 4. Calibration placement | Resolved: stages 5 and 13 |
| 5. Selection world seed, `checkpoint_every` | Resolved |
| 6. Two-sided offset test | Resolved |
| 7. B-task's "working" branch | Resolved: performance only, rules 2-5 |
| 8. Integer rule for the reference | Resolved, and renamed "straight-run reference" |
| 9-15. Small pins | All resolved |

## 3. The second draft, point by point

- **Stage order:** it works. Every dependency runs forward:
  - D (stage 5) comes before any release test.
  - Stage 2's champions are frozen (9) before Stage 3 (10).
  - Calibration (13) follows all freezing, and the test worlds are read only in 14.
  - The census screen (6) needs E's mean on the 16 census worlds. That is implied and not listed; compute it in stage 6.
- **`evolve_batch`:** the last generation is scored and not bred (`evolve.py:181`), so `final` is the population the champion rule needs. The checkpoint champion is separate, as the draft says.
- **State-to-goal assignment:** it is well defined. The two assignments cannot both pass, since one state cannot send 90% of first entries to both A and B. The fallback and the tie-break are deterministic. It costs no extra runs: both assignments are read from the same two clamp runs.
  - As written, the rule also covers monostable champions, overriding their phase labels. That is coherent; just implement it that way.
- **Root bracketing:** it is correct.
  - The stationary points ±acosh(√w) are right, and the bound |q| ≤ |w| + |b| is right.
  - Astra's case is consistent by hand. The stationary point is at 0.109327, and the root at −0.109339 lies 1.2e-5 outside it. That gives f′ ≈ −2.6e-6, which passes the −1e-6 threshold.
  - The continuous analysis holds for the engine: dt/τ ≤ 1/16 and f′ ≥ −4, so no discrete instability.
  - Two edge cases are not blocking. A tangent root can also be returned by its adjacent intervals; it is never stable, so counts are unaffected, but deduplicate it. And if no root passes the stability threshold (w sech² q within 1e-6 of 1), the release test has no start state. The probability is about 1e-6; I would leave it to an amendment if it ever occurs.
- **Reset timing:** fixed. The logic checks: after the write, the entry into A is not a confirmed visit because the goal is B. The level then flips q, and B's visit confirms.
- **B-task's draws:** correct.
  - The counts check: 121 + 32 = 153 edges, plus 18 τ and biases, gives 171.
  - With the full within-pair blocks, NL = NR and CL = CR at equal inputs. The opposite-signed outputs then cancel, so generation 0 adds no turn.
  - Nose-to-Q and nose-to-relay edges are untied, which is harmless.
  - The biases (±2) and weights (±3) sit inside `b_max` and `w_max`.
- **Census estimand:** correct, and the zero wording matches it.
  - One gap: the number of qualifiers is unknown at projection time. Evaluation's admission should use the projected time recomputed with the actual count. I read "its projected time" as allowing that.
- **Admission:** implementable, and the reduction order matches the batch order.
  - A refused batch 2 is not literally "stopped finally", but S2-b plainly cannot be read then.
  - Evaluation is admitted all-or-nothing, so an overrun in the descriptive arms could cost the registered readings. At about 13.4 h against 30 the risk is small. Running the registered evaluations first inside stage 14 would remove it; this is optional.

**One unpinned detail outside your list:** the batch composition for test-world scoring and for E's census-world mean is not stated. The projection lists "1 padded × 256" for assays only. Under rule 6, record the composition in the stage's output. It cannot move an outcome except at a float-level threshold tie.