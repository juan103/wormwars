You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Confirmation review: the evolutionary E4-D's pre-registration, draft 2 (WormWars), before binding

You reviewed draft 1 (1bec549) read-only in this repository; both of you said "bind after these fixes". Your reviews
are archived in `docs/reviews/20261014-E4-D-evo-prereg/`. Draft 2 is
`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`; its §12 lists every change, and DECISIONS D272 records them.
Also changed: `wormwars/e4/evo_stats.py` and `tests/test_e4d_evo_stats.py` (strict edges tested independently,
malformed inputs refused, the exact integer sign-flip), and `scripts/e4d_evo_power.py` → `power.json` (rerun: the
timing corrected, structured-population and champion-level-mixture sensitivity cases, R up to 48).

**A choice to attack:** R stays 32. The harsh champion-level mixtures (successes at a perfect 0.5, or failures at
−0.10) give 0.71 and 0.77 at R = 32 and 0.80 and 0.85 at R = 40; draft 2 states the power as conditional on failures
near E-G and successes near the pilot's level rather than raising R. The conservative cost of R = 40 is about one more
GPU-hour each for L and S, within E4's remaining 23.95.

**What I want:**
1. Is each of your draft-1 findings resolved? Name any that is not, or that was resolved wrongly.
2. Anything new that draft 2 introduced: the S-against-start reading and the joint table; the failure taxonomy
   ("not evaluable", "not completed", no reduced arm); the stage order and separate caps; the `check` stage's replay
   (11 generations, snapshot index 10, the digest), its timing refusal; the registered assertions (exact per-maze
   balance for the cue-removed, cue-fixed, cut and E-G conditions); `evo_stats`'s integer sign-flip and refusals.
3. R = 32 against R = 40 (above).
4. Is the text now sufficient to write the formal stage code test-first from it alone?

**The answer I want:** a verdict ("bind as is", "bind after these fixes", or "revise"), then numbered findings with
severity, section or file:line, and the fix. Terse.
