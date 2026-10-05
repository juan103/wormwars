You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review: E3c's formal stages, before about 21-25 GPU-hours

You are reviewing, read-only, the WormWars repository in the current directory. Look at the working tree (the
formal stages are not committed yet) on branch `roadmap`, against the pre-registration bound at 69d7cd5:
`experiments/E3-ab-organism/E3c/PREREGISTRATION.md`. Its §0 says the formal stages are written after binding,
test-first against §12, and reviewed by both of you. This is that review.

**What to read:**
- `wormwars/e3/e3c_formal.py` (a new file), with `tests/test_e3c_formal.py`. It holds:
  - the runs and cuts, the compositions, the 21 checkpoints and the blocks;
  - the champion rule and the W2-turn choice, both with their ties;
  - P-joint's candidates found by logged hash;
  - the projection and admission rule;
  - the engine freeze.
- `scripts/e3c.py`, from "the formal stages" down to `cmd_report`, plus `REGISTERED["formal"]`, `use_smoke` and
  `main`. The stages:
  - `project`: the benchmark on benchmark ids, the projection and admission;
  - `g-e`: E3b-1's three legs, reused from `scripts/e3b1.py`;
  - `train-s` and `train-psel`;
  - `champions`: P-joint's hash check, the validation of the final populations, the W2-turn choice, P-joint's
    learning-curve points and the learning-curve references;
  - `evaluate`: the test block, intact and with the noses removed, with paths; the references; trails off;
  - `report`: `report_readings`, one function from the records.
- `tests/test_e3c_stages.py`:
  - P-joint's hash check, sabotaged;
  - the report on synthetic records, with a sabotage check;
  - the order refusal;
  - a slow CPU smoke of every stage.
- The registered statistics, `wormwars/e3/e3c_stats.py`, are bound and unchanged.

**One design choice to check:** the checkpoints.
- **The problem:** the registered schedule is irregular (§5). `evolve_batch` checkpoints only every k
  generations, and changing it would break the engine freeze.
- **What the code does:** it trains with E3b-1's `snapshot_at` hook at the 21 generations. After training, it
  plays each run's generation-best (found by the logged `best_sha256` in the snapshot) on the learning block,
  in [R, 128, 8] chunks.
- **A built-in check:** `evolve_batch`'s own in-loop checkpoints at generations 0 and 299 are compared with the
  post-hoc plays (`checkpoint_consistency`). The CPU smoke shows them equal.

**What the tests show:**
- the CPU smoke runs all 7 stages end to end;
- the new tests pass;
- the full suite is running.

**Please check, and answer each, citing file and line:**
1. Does each stage do exactly what §5 registers? Check the compositions, blocks, ids, seeds, saving,
   eligibility, the `g-e` gate and the admission. Name anything that departs from the bound text.
2. Is the checkpoint approach above equivalent to §5's registered checkpoints? Is the consistency check
   sound?
3. Does `report_readings` compute every §7 reading as registered? Check the unit d, the exact and approximate
   labels, the decomposition, the bootstrap, the cost curve, §7.3 and §7.4.
4. Can anything make the 21-25 GPU-hours worthless? For example:
   - a wrong organism or mask;
   - P-joint's populations or genomes misidentified;
   - a missing record;
   - a cap or admission error;
   - a crash late in a long stage that loses its work.
5. Is §12's list of tests covered? Name each missing test.
6. **Your verdict:**
   - "run it";
   - or "fix first", with a numbered list of real defects (style is out of scope).
