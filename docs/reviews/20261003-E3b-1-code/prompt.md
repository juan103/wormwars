You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code review: E3b-1's implementation, before any formal stage runs

You are reviewing code in the WormWars repository (your working directory). You may read any file. Please
check claims against the code rather than trusting this summary.

## What E3b-1 is

A confirmatory experiment whose pre-registration is bound and must not change:
`experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md`. In short: a GA tunes a hand-built circuit (the seed
"E + W2") that shuttles between two sources in 5 × 5 tree mazes, with colonies of 8 and shared trails. Four arms:
- T-A: 8 runs × 125 generations × 16 mazes;
- T-F: 8 × 300 × 8, with a read at index 124;
- N: 6 runs, trails not sensed;
- R: 2 runs from a degraded start.

The champions are then evaluated against the frozen seed on 256 untouched test mazes. The gate G is a
stratified one-sided Welch test. The pre-registration's §12 lists 20 tests the code must pass before the
formal run. Its §5, §6, §7, §9 and §10 fix the stages, failure rules, evaluation blocks, readings, benchmark,
admission and cuts.

## What to review

The implementation, written test-first:
- `scripts/e3b1.py`: the runner, with eight stages in E2's stage frame (`scripts/e2.py`, `run_stage`) and a
  `readings` command;
- `wormwars/e3/tuning.py`: the mutation mask, the frozen-parameter assertion, the start organisms, and the
  registered statistics (gate, sign-flip, paired, Holm);
- `wormwars/e04a/evolve.py`: the new `snapshot_at` hook, and non-finite runs named on the error;
- `wormwars/e3/maze_runs.py`: `play_batch`, the batched evaluation chunks, replay donors per strain, and the
  per-world nose counts;
- the tests: `tests/test_e3b1_runner.py`, `tests/test_e3b1_tuning.py`, the E3b-1 additions at the end of
  `tests/test_e04a_evolve.py`, and the `play_batch` tests in `tests/test_e3b_maze_runs.py`.

Commit 81b3883 holds part 1 (tuning, the hooks, play_batch). The runner and its tests are the newest
commit on the `roadmap` branch. A CPU smoke of every stage has run (`runs/e3b1-smoke/`, local; the
test `test_a_smoke_of_every_stage` repeats it). At smoke sizes the registered readings are "not read",
with 2 runs per schedule.

## The question

**Does the code implement the pre-registration faithfully, so the formal stages can start?**

For each problem, give:
- the file and line;
- what the pre-registration says (with its section);
- what the code does;
- a severity: blocking (it would change a registered reading, the selection, the compute accounting or
  the admission, or make a stage unrecoverable) or non-blocking.

Look especially at the following.

1. **The arms and the GA:**
   - the mask (W2's neurons and 16 output edges, the relays' τ and bias, and the worm block frozen);
   - the initial population (32 copies);
   - the training mazes and run seeds;
   - the checkpoint schedule;
   - T-F's read at index 124, before selection and breeding;
   - N trained and validated with access "none".
2. **The failure rules (§5).** E2's frame allows one rerun. The runner layers training attempts on it:
   - a non-finite score is retried inside the stage (`train_attempts`);
   - a crash or kill uses the frame's rerun;
   - `ctx.salvage` marks the record final when §5 allows no further attempt;
   - every in-stage attempt after a non-finite score is admitted under §10, as its stage was. A refusal
     ends the stage, and its runs are not run;
   - a refusal file settles a stage, even a refused rerun after a stop (`stage_state`);
   - the hours spent in `project`'s planned total include its own running time.

   Is every path of §5 right, including a kill during an in-stage attempt?
3. **The champions (§6):** all 32 per read point, validated under the arm's own access, with ties to the
   lower index. A rerun restarts whole.
4. **The evaluation (§6):**
   - the order of blocks;
   - the chunk composition (16 × 256, or 8 × 256 plus donors);
   - per-chunk resume;
   - the replay pre-pass on the calibration block (a shared leg, then a replay leg at coefficient 1), with
     zero donor exposure as "not read";
   - the nose recorder in blocks 1, 4 and 6 under shared trails;
   - the probes and their thresholds.
5. **The readings (§7):**
   - d per run, normalised by the seed's shared mean;
   - G's estimand, test, labels, zero-SE rule, descriptors and the "concentrated" rule;
   - S-gen, S-trail and S-peer, each with its measure, denominator and direction;
   - Holm with an unread test at p = 1;
   - "A run counts as read only if its every needed condition covers all 256 mazes";
   - what each reading needs.
6. **The benchmark, cuts and admission (§9, §10),** including the use of the N timing at 4 runs under cut 1,
   the pre-pass projection, and `champions`/`evaluate` admission over completed runs.
7. **Anything that could silently differ between the smoke path and the formal path** (for example REGISTERED
   values mutated by `use_smoke`, `T.MIN_RUNS` defaults, device moves).

## Rulings made during implementation (claims to attack, not settled)

- **"W2 alone on the carrier"** (block 6, and the descriptor "seed − W2 alone") is E3b-0's carrier with the
  W2 module grafted (`scripts/e3b0.py` `carrier_variant(con, cfg, "W2")`), played as a brain organism.
  E3b-0's own "+1.09 above W2 alone" used the scripted `MC.w2_alone` controller instead. The scripted one is
  not run in E3b-1.
- **The g-e "snapshot hook off is bit-identical on E2's CPU smoke" leg** compares the hook off against the hook
  on, on an E2-sized CPU smoke batch. It does not compare against the code before the change; the GPU leg
  (E2's formal batch against `train-ga.json`) covers the code change itself.
- **`project` times t_ckpt separately** (a validation rollout of the runs' candidates), and sets t_gen to the
  mean of the two generations' batch seconds minus t_ckpt. Both timed generations carry a checkpoint.
- **The evaluate projection** charges every chunk, including a block's short last chunk, at the full chunk
  time. The probes are charged for every champion, and the singles (W2 alone and the scripted controllers) at
  the timed single.
- **Training uses `rollout`'s plain `Brain`, not the organism's `StartedBrain`.** They are equal because W2 has
  no oscillator; the runner refuses a seed with E3B_M1.
- **The champion read at index 124 is saved as "snap124"** (index 1 in smoke).

Please end with a verdict: "start the formal stages", "fix then start" (listing the blocking fixes), or
"revise" (with the reasons).
