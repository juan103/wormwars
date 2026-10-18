You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a results write-up in the repository you can read (read-only): **03a's exploratory results**, at
commit a3df220 on branch `roadmap` (DECISIONS.md D318). The write-up will be published on `main` once both of you
agree it is ready.

## Context

- 03a stopped before its pre-registration. Pilot-dev ran on one shuffled graph (D312, corrected in D313), followed by
  the bounded search check you both recommended (D314-D316). The check's rule gave outcome (iii) (D317).
- **The write-up:**
  - `experiments/03a-self-consistency/RESULTS.md`, labelled exploratory;
  - `experiments/03a-self-consistency/summary.json`, built from the committed records in
    `experiments/03a-self-consistency/pilot-dev/` by `scripts/e03a_summary.py`. `tests/test_e03a_summary.py` checks
    that the committed file is exactly what the records give;
  - dated status updates in 03a's `README.md`, the project `README.md` (the experiments table and "Next on the
    roadmap") and `ROADMAP.md` (the status section).
- D318 lists three errors Claude found in its own draft and fixed, and corrects an overclaim in D317. Check that the
  fixes are right.

## Please

1. **Check the numbers.** Check every number in RESULTS.md against `summary.json` or the named record. Name each error
   with its line.
2. **Check the claims.** Is anything overstated, understated or missing?
   - "What this shows, and what it does not" deserves a close look.
   - So does "What 03a leaves for a later design".
   - So does the probe's reading, given that the KTS calibrators barely moved.
   - Is "exploratory" applied correctly?
   - Does any sentence read as evidence about N2, or about the hypothesis itself?
3. **Check the dated updates.** Do the README and ROADMAP updates say the same as RESULTS.md, without contradiction or
   overstatement? Are earlier statements kept and annotated rather than silently changed (AGENTS.md rule 4)?
4. **Check traceability.** Is any number neither in `summary.json` nor in a record the page names (rule 5)? Is
   anything said about reproducing it wrong?

Answer with a verdict first: "publish" (possibly after small fixes) or "fix first". Then give numbered findings, each
with file and line and a severity. Do not edit files or run anything.
