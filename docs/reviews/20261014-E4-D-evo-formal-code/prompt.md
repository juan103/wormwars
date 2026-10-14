You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review request: the evolutionary E4-D's formal stage code (WormWars), before its GPU run

You are reviewing code read-only in the WormWars repository (your working directory). The pre-registration is bound
(`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`, at c3fe432; you confirmed draft 3, D274). Its §0.2 requires
the formal stage code to be written after binding, test-first against §10, and reviewed by both of you; its commit is
then recorded in a dated amendment. D275 lists the code.

**Review:**
- `scripts/e4d_evo_formal.py` (every stage: check, train-<arm>, evaluate-<arm>, report-<arm>; the frame's
  configuration, `requires`, the integrity mapping, the replay, the timing);
- `wormwars/e4/evo_formal.py` (the registered constants and helpers);
- the authorized additive change to `wormwars/e4/evo_trial.py` (`TrialResult`'s per-maze fields);
- tests: `tests/test_e4d_evo_formal.py`, `tests/test_e4d_evo_formal_stages.py`, the new test in
  `tests/test_e4d_evo_trial.py`;
- for reference: the pilot's `scripts/e4d_evo.py` (reviewed at D268), E2's frame `scripts/e2.py` (`run_stage`,
  `rerun_plan`, `_not_completed`), `wormwars/e04a/evolve.py`, `wormwars/e4/lineage.py`, `wormwars/e4/arms.py`.

**What was run:** the fast CPU suite; a CPU smoke and a GPU smoke of all ten stages at toy sizes (S triggered); a
sabotage check for each stage guard (each made its test fail); a dry run of the pilot replay on the GPU for 3
generations, whose per-generation best hashes and fitnesses equalled `screen.json`'s for all 16 runs; the real
pre-flight (every block resolves without replacement, disjoint).

**What I want:**
1. Does the code implement the bound text exactly: §2-§5 (blocks, seeds, runs, compositions, the stage order and
   dependency table, the owner's word, the registered assertions and their consequences, the rerun rule, the caps per
   group), §6 (the champion), §7 (the readings, only through `evo_stats`), §0.3 (only the authorized change outside the
   new files)?
2. Anything that would make a formal number wrong, lost or unrecoverable: the champion's final-generation fitness
   (from the saved selections), the frozen-set checks at checkpoints, the lineage replay, the S₀ start, F's mask, the
   per-maze records, the reports, the cap clocks per group, salvage after a stop.
3. Ways a defect in descriptive or check code could cost the primary arm (a "not evaluable" that should not be).
4. Tests that would pass with a broken implementation.

**The answer I want:** a verdict ("run it", "fix first", or "revise"), then numbered findings with severity,
file:line and the fix. Terse.
