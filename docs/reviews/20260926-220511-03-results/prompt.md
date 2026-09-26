You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Results review: WormWars experiment 03 (generation-0 structure against five null ensembles)

You reviewed this experiment's design and pre-registration earlier (see `docs/reviews/*-03-*` and
`DECISIONS.md` D050-D056). The run has now finished, and the results are written up. Please
review the write-up **adversarially** before anything is published. You are read-only in the
repository at its current commit (branch `roadmap`, commit f5ab9d9).

## Files

- **Binding pre-registration:** `experiments/03-generation0/PREREGISTRATION.md`, especially:
  - §5 signals;
  - §6 verdict rules;
  - §7 power;
  - §10 and §10b (what the results decide, and the deviation during the run);
  - §11 (what is exploratory).
- **The write-up under review:** `experiments/03-generation0/RESULTS.md`.
- **The machine report:** `experiments/03-generation0/report.json`, produced by
  `scripts/exp03.py report` → `wormwars/exp03/report.py`, `wormwars/exp03/verdict.py`. It has the
  per-graph values for every graph (`per_graph`), each signal's per-ensemble values, and the
  secondaries.
- **Decision record:** `DECISIONS.md`, D056 (the restart) and D057 (these results).
- **Context from earlier experiments:**
  - `experiments/02-screening/RESULTS.md` (generation-0 input-response table, around line 155);
  - `experiments/02b-champion-analysis/RESULTS.md` (history section 2).
- The raw per-graph measurements (`runs/exp03/measures/`, about 640 MB) are local and
  git-ignored, so you cannot read them. The exploratory P4 decomposition table in RESULTS.md was
  computed from them: mean |final|, mean |steady_contrast| and the common-mode turn, per graph,
  then medians and maxima per ensemble. If a number there looks inconsistent with report.json,
  say so.

## What to check

1. **Numbers.** Does every number in RESULTS.md match report.json, the pre-registration or the
   cited files? Spot-check as many as you can, and list any mismatch.
2. **Verdict fidelity.** Were the registered rules applied as written, with no rule chosen after
   seeing the data? Do the verdict labels in RESULTS.md match what §6 defines?
3. **Overclaiming.** Is any sentence stronger than the evidence supports? In particular:
   - the P4 headline;
   - "distinctive relative to every ensemble";
   - the exploratory paragraphs on responsiveness versus persistence, topology versus weights,
     and the comparison with 02b;
   - the corrections to 02.
   Is anything exploratory presented as if it were registered?
4. **Underclaiming or missing caveats.** Is the fragility section fair? Are the power statement
   and its explanation (smaller observed latent SDs than the pilot's) correct? Is anything
   important missing? For example:
   - whether P4's ratio is well behaved;
   - whether the latent SD estimates affect the margin but not the rank p;
   - the IUT and Holm logic;
   - the one-constraint-at-a-time limitation of the ensembles.
5. **Interpretation.** Is "N2's random brains carry more of their recent input" a fair plain
   reading of P4 as defined in §5? Is there an alternative reading of a high P4 that the
   write-up should mention, for example a calibration or gain artefact? Each graph is calibrated
   to the same target drive in the world before measurement.
6. **What should happen next.** Should the result be replicated on fresh ensemble draws before
   any public claim? Is anything else required before the owner is asked whether to publish?

## Answer format

Findings ranked by severity: **must fix before publishing**, **should fix**, **minor**. For each
finding give the file and line or section, what is wrong, and the evidence you checked. Then give
a one-paragraph overall judgement: is the write-up an accurate and honest report of this
pre-registered experiment?
