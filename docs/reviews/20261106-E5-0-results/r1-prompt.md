# E5-0's results, before publication (round 1)

E5-0 has run: all six formal stages on commit `7d25460` (D387, after your code review in
`docs/reviews/20261106-E5-0-code/`), CPU only, 7.94 of the 8 recorded hours, one attempt each, no cuts. The records
are committed (`f2199d9`) in `experiments/E5-hunter/E5-0/`. Please review the write-up before it is published:

- `experiments/E5-hunter/E5-0/RESULTS.md` (draft 1) and `experiments/E5-hunter/README.md`;
- `scripts/e5_0_summary.py`, which writes `summary.json` (every number RESULTS quotes) and `genomes.md` (each genome
  on its own) from the committed records; `tests/test_e5_0_summary.py`;
- `scripts/e5_0_phases.py` and `phases.json`: written **after** seeing `reading.json`, exploratory (RESULTS §6);
- the plan it is read against: `docs/E5/E5-0-PLAN.md` (§6 the decision rules, §10 the amendments), and the scope
  `docs/E5/SCOPE.md`.

The large records (`evaluation.json`, `probes.json`, `reading.json`) are committed; the per-life event tables are local
(`runs/e5-0/evaluation/*.npz`, 440 MB), and only `phases.json` reads them.

Read-only; please keep it proportionate.
1. **Are the readings applied as the plan fixed them?** Solvable, too easy, qualifies, demonstrated failure,
   uncertain, falls off (§6), with H1-ghost as the bridge. Is anything read that the plan did not fix, or worded
   more strongly than the rule allows?
2. **Does every claim in RESULTS.md and the README follow from the records?** Re-derive what you can from
   `summary.json`, `reading.json` and the other committed files; name any number or sentence that does not match.
3. **The interpretations:** the stereo reading from the `mean` and `mirrored` probes (§5), the exploratory phases
   (§6), and "what this means for E5-1". Overclaimed, missing a caveat, or missing a reading that matters?
4. **Anything about the run itself** that should be disclosed and is not (for example the 0.06-hour margin under the
   cap, the random-walk prey's wall contact, the pursuit reference falling below the tuned positive control).
5. Your verdict: publish, fix then publish (list the fixes), or revise.
