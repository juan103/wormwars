# M4e plan and code, round 2

Your round-1 answers are in `docs/reviews/20261026-m4e-plan/r1-{fable,astra}.md` (both "revise"). Draft 2 of the plan
is `docs/memory/M4E-PLAN.md` (draft 1 archived beside your answers). Every finding was taken:
- the dose model: no slope when switches fall in fewer than two U arms, or on a singular step, a non-finite value or no
  convergence; W's and K's S2 outside the U range counted; the readings written before the dose model runs;
- seed families moved apart (blocks, signs, the reader, audits; a smoke shifted by 900,000); coverage rerun;
- tests of the production shape (a batched continuation against one genome's own, and its single-genome rerun), of a
  second-pass code outside the classes, of a host seed jump, of the audit fallback through `load_counts`, of a size
  sub-field standing on both intervals, and of the dose model with hosts lacking a slope (24 tests pass; 27 of 27
  sabotages fail, each by its test's own check; the wrong-signature sabotage fixed);
- `validate` checks both passes' columns and class codes; `check_host_list` requires every earlier seed recorded as
  skipped, and `load_hosts` regenerates each skip and confirms it;
- the classifier change checked against the version before it (`scripts/memory_m4/m4e_pilot_equivalence.py`,
  `runs/memory-m4e/pilot-equivalence.json`: R6's planted genomes and 64 host genomes identical, record for record);
  M2's suite rerun (`runs/pytest-m2-after-m4e.txt`);
- `scripts/memory_m4/m4e_tables.py` writes `blocks-summary.json` (with the local blocks file's sha256 and a digest stop)
  and the per-genome predictor's AUC per arm; stage 0's quoted Spearman and S3 count are now in `stage0.json`;
- the audit raised to 40 ids per panel (about 800 fading genomes per arm; Astra's 748); the plan argues why fading to
  separate states should be zero by construction, keeps the global fallback, and reports the first-pass reading
  beside the main one (Astra's alternative);
- the interaction's envelope; K's target checked against W's count; the cap described as wall-clock and checked before
  each chunk, with the possible overrun stated; Fable's 1% rule declined, with the reason; the 20-host alternative
  declined, with the reason.
A 16-genome smoke ran every stage after the changes, then the reader and the tables (`runs/m4e-smoke16-log.txt`).

Read-only. Check the fixes and look for anything new. Verdict: agree / revise, with findings ranked.
