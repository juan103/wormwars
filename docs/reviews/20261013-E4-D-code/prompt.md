You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review request: E4-D's feasibility code (WormWars), before the CPU feasibility check is played

You are reviewing code in the WormWars repository (your working directory), read-only. The owner has re-scoped E4: its
main formal run is dropped and E4-D is the confirmatory direction (D258 in `DECISIONS.md`). E4-D's feasibility check
(CPU) comes first. **Design: `docs/E4/E4-D-DESIGN.md` v2.2** (you reviewed v1 and v2; v2.1 took your findings, v2.2
adds smaller control weights).

**The code under review** (committed at bee61e3, with v2.2's weights at ba0cbfd):
- `wormwars/e4/trial.py`: `TrialWorld` (a `MazeWorld` subclass), `start_cell`, `latch_first`, `control_genome`;
- `wormwars/e4/feasibility.py`: the readout, σ_D's choice, the control's selection, the per-maze bootstrap bound,
  the reversal mapping check, the verdict;
- `scripts/e4d.py`: the scout, calibrate and evaluate stages;
- tests: `tests/test_e4d_trial.py`, `tests/test_e4d_feasibility.py`.

**What I want:**
1. **Does the code implement v2.2 exactly?** Check every rule in §1-§4 and §6 against the code: the start-cell rule
   (distances, the separation walk, the tie-break, min distance > 2), the channel mapping (A: real / decoy / fixed /
   none; B: sum / real), the relays and the start cue silenced, the goal pinned, the latch's start, first-entry
   latching (including an entry on the last tick and simultaneous entries), σ_D untruncated, the oracle, the
   control's two wirings with B's four signed edges, the selection rule and ties, the blocks and manifests, the
   success criteria, the bootstrap, and the reading of a failure with the oracle beside it.
2. **The exactness argument (§3):** the X0 invariance test compares positions and non-A states over 150 ticks within
   one batch. Is that sufficient, and are the three sabotages real? Does `paired_identical` in `scripts/e4d.py`
   (first candidate, first tick, final position) test enough for the evaluation's invariance checks?
3. **Deviations I made, as rulings to accept or reject:** the design's "flag" is a subclass (no engine file changed,
   so rule 7 holds by construction); in the smoke only, a σ is forced when none qualifies; mazes without a qualifying
   start raise inside `TrialWorld` (the runner filters them first); `trial_events` reports the start cells.
4. **Anything that would make the scouting, calibration or evaluation results wrong or uninterpretable** (file:line,
   failure scenario, fix). Name tests that would pass with a broken implementation.

**The answer I want:** a verdict ("play the check", "fix first", or "revise"), then numbered findings with severity
(critical / important / minor), file:line and the fix. Terse.
