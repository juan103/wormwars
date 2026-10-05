You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code check: E3c's replay-and-probe stage, before about 1.5 GPU-hours

You are reviewing code in the WormWars repository (the current directory), read-only. After your reviews of
E3c's pilot (`docs/reviews/20261005-E3c-pilot/`), the owner chose Astra's bounded step:
- replay the pilot's S-dense batch with genome saving;
- probe the three champions with their noses removed, and inspect their paths.

D205 at the end of `DECISIONS.md` describes the step and fixes its outcomes before the run. The code is
uncommitted in the working tree:
- `scripts/e3c.py`: everything from `compare_hashes` to `cmd_replay`, plus `REGISTERED["replay"]` and the
  smoke changes in `use_smoke`;
- `tests/test_e3c_runner.py`: the tests after "the replay and probe".

The CPU smoke reproduces the pilot's hashes exactly, and its intact plays equal the pilot's records.

**Please check, and answer each, citing file and line:**
1. **The replay:** is it the pilot's S-dense batch exactly? Check the draws, masks, ids, schedule,
   composition and the `evolve_batch` arguments against `cmd_pilot`. Can anything make the GPU hashes
   differ, other than rule 6's limits?
2. **The probes:**
   - Does `play_recorded` reproduce `play_batch`'s layout and results?
   - Is `without_scent` applied to the right interface for every organism?
   - Is `cell_index` right for the maze geometry (`wormwars/e3/maze.py`, `maze_world.py`)?
   - Does `tour_match` measure what D205 says: a circuit of a 25-cell tree repeats every 48 moves?
   - Is `world.pos[:, 0]` the heads in [worlds, weys, 2]?
3. **`w2_turn`:** does it set the resting turn as `maze_organisms.carrier_turn` defines it? Is the sweep a fair
   scent-free reference?
4. **D205's outcome rule** (`consequence`): does the code implement it as written? Are the thresholds sensible
   as fixed in advance, given that the result is not yet known?
5. **Anything that would make the run worthless,** or a record that would be missing.
6. **Your verdict:** "run it", or "fix first" with a numbered list. Real defects only.
