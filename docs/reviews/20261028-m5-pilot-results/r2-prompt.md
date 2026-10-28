# Review request: M5's pilot results, draft 2

Round 2. Your round-1 answers are in `docs/reviews/20261028-m5-pilot-results/r1-astra.md` and `r1-fable.md` (both
"fix then publish"); draft 1 is `draft1.md` there. Please check `docs/memory/M5-PILOT-RESULTS.md` (draft 2). Read-only.

What changed:
- **The note:** every round-1 finding was taken: the compute subtotals with the unattributed 10,630 s; Rr's pooling
  with its own panel audits; Rr's rate attributed to hosts, not the second pass, with Rr/T 0.50 → 0.79; the
  unresolved genomes "not released by a longer horizon", with K 287 as a possible dynamical case; the chain's overlap
  wording with the paired t values (recomputed: shared edges +3.15, SD 8.0, t 1.8; reciprocal +3.8, SD 6.1, t 2.8);
  the estimand wording instead of "the arrangement of the rest"; the cross-arm bound labelled and not used; the
  fallbacks as "Newton failure" cases with normalized deviations and Astra's wording of what the rerun reproduced;
  the composition check's first-pass scope; acceptance over all 40 blocks; the completion cost (about 29 min per
  panel, 2.5 to 3 times, replay-based); the variance components, the truncation (0.00336 against 0.00365), M4d's
  combined residual, the host component's upper limit, "the larger historical source" instead of "the outlier"; the
  T/Rr host correlation; the qualifier's figures and agreed labels; the audit's open specification list; Fable's
  hash and Astra's composition recording for M5.
- **The reader** (`scripts/memory_m5/m5_pilot_read.py`): added the fallback details with both deviations and an
  overall maximum, per-panel audit bounds and any-change counts, first-pass and merged class breakdowns, per-host
  totals, the untruncated host moment, and a note that the timings are recorded phase costs. Four new tests in
  `tests/test_memory_m5_pilot.py`, each seen failing first. `report.json` was rewritten; every value present before is
  unchanged (compared key by key).

Please say whether draft 2 is ready to commit and push (agree / fix then publish / revise), and list anything still
wrong, with file and line references. Points for M5's plan rather than this note can be flagged as such.
