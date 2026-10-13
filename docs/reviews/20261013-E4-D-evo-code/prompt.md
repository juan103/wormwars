You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review request: the evolutionary E4-D's pilot code (WormWars), before its GPU pilot

You are reviewing code in the WormWars repository (your working directory), read-only. The design is
`docs/E4/E4-D-EVO-DESIGN.md` v2.1 (you reviewed v1; D265-D266 record your findings and the owner's choices). D267 lists
the code. **Review:**
- `wormwars/evo/evolve.py` (`ranking`, `breed`'s `tie_rng`), `wormwars/e04a/evolve.py` (`random_ties`, `tie_rng`),
  `wormwars/e4/lineage.py` (`replay`'s `random_ties`, `Capture`);
- `wormwars/e4/evo_trial.py` (the trial rollout, qualifying ids, the integrity check, the champion rule);
- `scripts/e4d_evo.py` (precheck, screen, f);
- tests: `tests/test_e4d_ties.py`, `tests/test_e4d_evo_trial.py`.

**What I want:**
1. Does the code implement design v2.1 §3-§5 exactly (fitness = real-first count / 2W, zero progress, random ties for
   elites and parents, the integrity check every generation, the champion from the whole final population with its
   ties, selection visibility and the W rule, the factor's rule and safeguard, F's keep rule)?
2. Is the flag-off path of `breed` / `evolve_batch` bitwise unchanged (rule 7)? Is the lineage replay right with random
   ties (the deep-copied stream peeked before `breed` draws)?
3. Anything that would make the pilot's numbers wrong or lost (the visibility draws' construction, the timing
   measurement, the entry rates at generation 1 with random ties, the tie-share curve, saving, the cap).
4. Tests that would pass with a broken implementation.

**The answer I want:** a verdict ("run the pilot", "fix first", or "revise"), then numbered findings with severity,
file:line and the fix. Terse.
