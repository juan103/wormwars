You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are confirming, read-only, the fixes to 03h's pilot registration and code, at commit ab2d7bb on branch `roadmap`
(DECISIONS.md D333). This is round 2 of the review archived in `docs/reviews/20261019-03h-pilot/` (round 1 was at
4fae0d1: Fable "bind and run, after small fixes", Astra "revise").

**What changed since round 1:**
- `experiments/03h-history-use/PILOT.md` is now draft 3. It retires draft 1's world banks (the CUDA smoke preflight
  had played part of them) and registers fresh banks from 3 640 000, graph seeds from 3 660 001 and calibration seed
  3 661 000. Smoke has its own ranges from 3 690 000.
- `scripts/e03h.py` is rewritten: the cap is checked before each stage and each bounded unit; each record carries its
  predecessors' hashes and a stage refuses a stale chain; binding requires HEAD pushed and checks DESIGN.md's bound
  hash; calibration or sampler failures take the next graph seed and P rebuilds S1's accepted seeds, checking the
  genomes' sha256; the gate runs in `replay_mode()` and G2 reuses G1's K, Graded and memoryless families; the
  projection follows a decision table; the budget takes precedence over the amplitude rule; P′ needs a completed P at
  0.25 whose shift did not move, and only one completed P′ is allowed.
- `wormwars/e03h/gate.py`: the slow-memory family over T × FALL_GRID, memory + bit's base after a memory fallback,
  grid-edge flags, grids passed in.
- `wormwars/e03h/pilot.py`: `quartile_difference`, `projection_table`.
- `wormwars/evo/rollout.py`: `rollout_brain` forwards `food_fell_counts`.
- Tests: `tests/test_e03h_pilot_driver.py`, `test_e03h_gate.py`, `test_e03h_pilot.py`.
- D333 in DECISIONS.md lists every item and where it was taken. The full suite passes.
- CUDA smoke preflight at ab2d7bb: all five stages completed on CUDA, in their own smoke ranges (records in `runs/e03h-smoke-cuda/pilot/records/`, local, not committed). The smoke projection is an extrapolation from smoke compositions and is labelled meaningless.

**Please:**
1. For each of your round-1 findings, say whether the fix is correct and complete. The round-1 answers are in
   `docs/reviews/20261019-03h-pilot/astra.answer.md` and `fable.answer.md`.
2. Name anything the fixes broke or introduced that would mislead G1, S1, G2 or P, or the formal run's sizing, with
   file, line and severity.
3. Say whether PILOT.md draft 3 is ready to bind.

Answer with a verdict first: "bind and run" (possibly with small fixes that do not touch PILOT.md) or "revise". Then
give numbered findings. Keep it short: this is a confirmation, not a fresh review. Do not edit files or run anything.
