You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Pre-registration review: WormWars 03r, the full replication of experiment 03

You reviewed experiment 03's results (`docs/reviews/20260926-220511-03-results/`, `DECISIONS.md`
D058). Both of you recommended a pre-registered replication, and the owner chose a full one
before publishing (D059). Please review the replication's pre-registration **adversarially,
before any brain is run**. You are read-only in the repository (branch `roadmap`, commit
3f3bf10).

## Files

- **The draft under review:** `experiments/03r-replication/PREREGISTRATION.md`.
- **The code:**
  - `scripts/exp03.py`: the new `INSTANCES`, `use_instance`, `interleave`, `run_order`,
    `measure_graph` seeds and `cmd_report`;
  - `wormwars/exp03/report.py`: `single_signal`, and `build(..., descriptive=)`;
  - `wormwars/exp03/measures.py`: `genome_seed(name, salt)`;
  - `tests/test_exp03r_replication.py`;
  - `experiments/03r-replication/power.py`;
  - `experiments/03-generation0/supplement.py`.
  The code diff since 03's binding commit is `git diff 132acae..3f3bf10 -- scripts wormwars`.
- **The built ensembles:** `experiments/03r-replication/ensembles.json` and
  `graphs_manifest.json`.
- **Experiment 03, for reference:** `experiments/03-generation0/PREREGISTRATION.md`,
  `RESULTS.md` and `report.json`.

## What to check

1. **Is this a faithful replication?**
   - Is every random element of 03 redrawn, apart from the stimulus bank, which is deliberately
     kept? That covers graphs, N2's and every graph's genomes, worlds, run seed, calibration and
     validation, and the N2perm draws.
   - Is anything accidentally shared with 03?
   - Does the code do what §3-§4 say? Verify it in the code, not only in the text.
2. **The primary test.** The replication tests P4 alone: the maximum rank p over ensembles at α
   0.05, with 03's margin gate and no Holm across signals. 03's three-signal Holm rule is applied
   and reported as a secondary result.
   - This choice was made after seeing 03. Is it justified, and is it disclosed well enough?
   - Would you require a different primary rule? For example:
     - 03's rule unchanged;
     - a stricter α;
     - a combined analysis;
     - an effect-size criterion rather than a rank count.
   - Is 256 graphs for SH-route, and 128 for the others, the right allocation?
3. **The power (§7).** Is the method sound (Jeffreys posteriors on 03's tail counts)? Are the
   figures correct (re-run `power.py` mentally or check its logic)? Are the stated limits honest?
4. **The outcome rules and publication commitments (§10).** Are they complete? Do they prevent
   outcome-dependent choices? Is anything missing that must be fixed in advance? For example:
   - how to report a split result, such as passing four ensembles and failing one;
   - the wording if 03r passes but 03's rule fails;
   - how 03 and 03r's results are combined in the public write-up.
5. **Anything else** that would make the result uninterpretable, or that a sceptical reader would
   attack, including the fact that the probe and code are unchanged.

## Answer format

Findings ranked by severity: **must fix before running**, **should fix**, **minor**. For each
finding give the file and line or section, what is wrong, and the evidence you checked. Then give
a short overall judgement: can this run once the must-fix items are addressed?
