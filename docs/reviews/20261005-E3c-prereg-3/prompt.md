You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3c pre-registration, draft 3: please review before it binds

You are reviewing, read-only, the WormWars repository in the current directory, at commit 65cd529 (branch
`roadmap`).
- **Your reviews of draft 2** are in `docs/reviews/20261005-E3c-prereg-2/`. Fable said "revise, narrowly",
  Astra "revise".
- **Draft 3** is `experiments/E3-ab-organism/E3c/PREREGISTRATION.md`. Its §16 lists the changes; D208 in
  `DECISIONS.md` is the log entry, with a dated correction to D207.

**The main change, for both of you to judge** (§7.1):
- **The confirmatory decision is now an exact two-sided permutation test** per contrast, at 0.025. It runs over
  every split of the pooled runs, with the difference in mean d as the statistic.
  - Its null is exchangeability, so its level is exact whatever the failure rates.
  - Its label claims only that the distributions differ, with the direction described from the sample. It can
    reject at equal means when the spreads differ (0.042 in `power.json` for Q2), and is not read as a claim
    about means.
- **Every Welch margin label is approximate (model-based),** with the owner's dual margin, the failed-run
  counts and a decomposition beside it.
- **Why this route:** it is Astra's "register a validated procedure" option, combined with Astra's other option
  of downgrading Welch. Fable had held that disclosure sufficed, so this is the more conservative side.

**Also changed:**
- `e3c_stats.py`: `permutation_p`, `decomposition`, the coverage rule's undefined case in any arm (Astra's
  counterexample, now a test), and "no runs";
- `e3c_power.py` and `power.json`: the exact test, every false label assertion counted, joint interval
  coverage, analytic means. Checked against `readings` on 15 040 trials;
- §5's `g-e` gate, the cut compositions, the 256-maze benchmark block, the learning-curve references,
  eligibility per reading, the trails-off scope, and 21 checkpoints.

**Please check, and answer each, citing section and line:**
1. Is each of your required changes from draft 2 taken correctly?
2. Is the exact permutation test sound as the confirmatory decision?
   - Its null and its claim.
   - The "X higher" description.
   - Bonferroni at 0.025.
   - `permutation_p`'s correctness, including ties.
   - Is anything about it overstated?
3. Is §8 correct against `power.json`, and is the power analysis faithful to the registered procedure?
4. Anything new that is wrong, or still missing for the formal stages to be written against this text?
5. **Your verdict:**
   - "bind it";
   - or "revise", with a numbered list of required changes, separated from optional suggestions.
