**Verdict: revise, narrowly. I accept the tolerance; I do not require the full original-composition replay. The remaining blocker is incomplete validation on resume and reading.**

1. **The tolerance is justified for this exploratory pilot.**

   The diagnostic isolates the observed discrepancy to the classifier’s float64 calculations: the float32 endpoint, tail and readout agree, and the original chunk reproduces the recorded fields exactly. Keeping class, reason and write amplitude exact, while allowing the two root-derived fields
   \[
   |\Delta|/\max(1,|\mathrm{recorded}|)\le10^{-9},
   \]
   is reasonable. This is a mixed absolute/relative tolerance.

   The composition check adds useful evidence. It does not establish general batch independence; keep the claim limited to tested compositions. Full original-composition replay is not warranted by the discrepancy shown.

2. **The round-3 stage-file validation requirement remains only partly implemented.**

   [`check_out`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:319) checks IDs, column lengths and final class codes. It never checks `host`, `draw`, `arm`, the contents of `recorded_*`, or agreement between `replayed_*` and the source records. Both resume paths and the [reader](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot_read.py:105) rely on it.

   I reproduced this in memory using the real SH-2011100 d0 T target IDs `[118, 319, 465]`: an output with the wrong host/draw/arm, a changed replayed first-pass class, and a changed replayed second-pass reason **passes validation**. The replay comparator rejects that discrepancy when called, but resumption and reading never call it.

   Before skipping or consuming a stage file:
   - Check its host, draw and arm against the expected panel.
   - Compare its stored `recorded_*` fields exactly against the validated source record.
   - Compare its `replayed_*` fields against those source fields using the registered tolerance.
   - Add failing tests for wrong identity, altered source copies and replay disagreement.

   This completes the requirement already stated in round 3; it introduces no new experimental condition.

3. **Validate the cached composition check too.**

   [`stage_longer`](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:333) skips the composition checks whenever `composition-check.json` exists, without reading it. Even `{}` bypasses the gate. Validate the expected applicable arms, selected panels/genomes/chunks and successful exact checks on resume, or rerun the checks. The reader should enforce the same gate.

The other substantial fixes are present and correct: T/K source-record validation with reconstructed hashes; Rr genome IDs and second-pass lengths; the M4d/M4e output-directory guard; the discarded singleton companion; paired covariance with the independent calculation beside it; incomplete-stage summaries with the horizon rule withheld; updated 100,000-tick counts and contrasts; fading denominators, reasons, phase timings and all three weight-overlap measures. The paired variance remains a pooled plug-in estimate rather than an average of within-panel estimates.

Three smaller corrections:

- The reader recomputes pairing for the 100,000-tick contrasts, but does **not emit the full paired class tables at that horizon**. Add them beside the existing 22,000-tick tables.
- The [replay docstring](/D:/Claude/random/wormWars/scripts/memory_m5/m5_pilot.py:236) and parts of the plan still promise exact comparison of every output. Update them to the registered comparison rule. The smoke’s pair replay passes that rule; it is not bit-for-bit reproduction.
- “21 sabotages fail by their tests’ own checks” overstates the evidence slightly: disabling `check_replay` produces a `TypeError` at `0 < None`. Make that mutant return `0.0` so the test fails by an assertion.

I changed no files. I reran seven arithmetic/validation tests through extracted definitions; all passed. I inspected the archived 19-test and smoke evidence rather than rerunning the experiment drivers.