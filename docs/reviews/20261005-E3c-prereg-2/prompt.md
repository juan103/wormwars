You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3c pre-registration, draft 2: please review before it binds

You are reviewing, read-only, the WormWars repository in the current directory, at commit 0e27083 (branch
`roadmap`).
- **Your reviews of draft 1** are in `docs/reviews/20261005-E3c-prereg/`; both said "revise".
- **Draft 2** is `experiments/E3-ab-organism/E3c/PREREGISTRATION.md`. Its §15 lists how each required change
  was taken; D207 in `DECISIONS.md` is the log entry.

**What changed behind it:**
- `wormwars/e3/e3c_stats.py` and `tests/test_e3c_stats.py`:
  - fixed 97.5% intervals for both contrasts, with Holm beside them;
  - strict margin boundaries;
  - the failed-run rule ("approximate");
  - the coverage rule by proportions;
  - the censored median.
- `scripts/e3c_power.py`, `tests/test_e3c_power.py` and `power.json`, rebuilt:
  - centred on true arm means;
  - P-joint kept at 8 under the cut;
  - vectorized, and checked against `readings` on 15 040 trials;
  - joint errors and Monte Carlo standard errors.
- `experiments/E3-ab-organism/E3c/compute-record.json`: the seed diagnostic is charged.

**One point where you disagreed:** calibration under failure mixtures. Draft 2 takes Astra's fallback, labelling
contrasts with a failed run "approximate", plus Fable's count and a decomposition. It also states in advance a
limit both of you may want to examine: failures absent from the sample cannot be caught. §8 quantifies it.

**Please check, and answer each, citing section and line:**
1. Is each of your required changes from draft 1 taken correctly? Say which, if any, are not.
2. Are the revised statistics and their tests right? Is the failed-run rule sound as a pre-registered fallback,
   and is its stated limit honest and correctly quantified?
3. Is the rebuilt power analysis faithful to the registered procedure? Is §8 correct against `power.json`?
4. Is §0's binding sequence, and §5's execution contract (compositions, eligibility, cuts, admission),
   complete enough that the formal stages can be written and checked against it?
5. Anything new that is wrong, or any claim stronger than the evidence?
6. **Your verdict:**
   - "bind it";
   - or "revise", with a numbered list of required changes, separated from optional suggestions.
