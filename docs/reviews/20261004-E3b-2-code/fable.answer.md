**Bottom line:** the partitions, hybrids, calculator, lesions, clamps, chunk plans, resume and isolation match draft 2, and draft 2 does carry every plan-review change. Two defects in the latch recorder would change §5D's readings and cannot be repaired after the run, because the recorder saves only aggregated counts. Since `require_same_code` pins every later stage to `project`'s commit, both must land before `project` runs. Verdict at the end: fix then start.

## Blocking

**1. A pre-aligned leg counts as a crossing with latency 0.** `wormwars/e3/attribution.py:236-240` and `:313-318`. The plan (§5D) defines switching as "the share of legs in which q *crosses* the threshold toward the new goal", and introduces it precisely because a stuck latch scores high agreement. The code marks a leg crossed when q *is on* the new goal's side, from the leg's first tick. A latch stuck on the B side therefore reads `switched_to_b = 1.0` with latency 0 and `switched_to_a = 0`. Your own test shows it: in `tests/test_e3b2_attribution.py:195-202` the to_b leg of the stuck latch is crossed at latency 0, and the test only asserts on to_a. For T-F finals 2, 3 and 7, whose resting turn is saturated in both latch states, this is the realistic case. Fix: at a leg's start, record whether q on the previous tick (the visit tick, computed before the cue) was already on the new goal's side; count such legs as "pre-aligned" separately and exclude them from `crossed`. Mirror it in `SwitchTally` so the cross-check test still runs.

**2. The middle-half sensitivity band is not recorded.** `attribution.py:215-216`, `:281-282`. §5D: "'undecided' is the middle third… As a sensitivity reading, the middle half is reported too." The recorder has one band. Add a second set of `decided/agree/undecided` counters at the middle half. While there, split `undecided` by goal, since §5D asks for goal occupancy and the current counters give it only for decided ticks.

## Non-blocking

- **Latency origin.** `attribution.py:239`, `:317`: latency counts from the leg's first tick, which is one tick after the visit. The plan says "from the visit". State it, or add 1.
- **Censored legs sit in the switched denominator.** `scripts/e3b2.py:651`, `:659`. Say so in the report, or report crossed/(legs − censored) beside it.
- **Opposite coding** (§5D) is not printed. With undecided excluded it is exactly `decided − agree`, so print it rather than leaving it to the reader.
- **§5E check missing.** `e3b2.py:678-681` computes the resting turn but never compares it with E3b-1's or E3b-0's probe values. Note the probes record `u_none` at m = 0.001, not 0, so the check needs the same m or a declared tolerance.
- **Fixed inputs recorded, not checked.** `e3b2.py:58-62`: champions.json, evaluate.json and the pre-registration have `None` hashes. §2 says "hash-checked at load". They are committed, so pinning is free.
- **Exactness checks could be wider.** `e3b2.py:549-553` checks the seed only across the 16 A-shared chunks. The A-none chunks and the 8 B chunks (same composition) carry 32 more copies. And the intact variant in C against the all-champion hybrid in A is also same-composition for every organism but the seed, so the ruling "the difference is not reported" throws away a free check. Report it.
- **Admission formula.** `e3b2.py:277` applies ×1.25 to the remaining work only. §7's sentence can be read either way; say which.
- **Benchmark block.** The 7300-7555 ruling is sound (the smoke block is too small) but §7 says "on smoke mazes"; add a dated annotation.
- **A cap stop leaves no report.** `cmd_report` requires every stage "completed". If the cap hits mid-latch, the report refuses without a code change, which would then trip `require_same_code`. Consider accepting completed chunks.
- **Minor:** the clamp test holds 60 ticks, not the horizon; `per_maze_agree` at `e3b2.py:644-648` is dead; Shapley in visits per wey (§5A) is not output, though it is one multiplication.

## Checked and found faithful

Partitions (20/8/32/5 and 28/28/9, frozen set excluded, edge classification exhaustive); endpoint hybrids bitwise; Shapley, dividends, rebuild, reversion, transplant on hand cases; `read_table` subtracts each condition's own seed and divides by the shared seed, as §3 requires; the bootstrap resamples mazes jointly with one index set across variants and champions; the clamps use each organism's own roots, held from tick 0 by `HeldBrain`, and the A = high convention when signs disagree is unreachable for these champions (relay edges start at ±3, σ 0.02); input and gate cuts, scent gains, reflex at −0.5, W2 reference once; recorder timing matches `World.tick` (record after `_post_move`, goal taken from before the switch); all 30 probed champions are bistable so `latch_states` will not raise; chunk plans, drop order, resume specification, output paths and E3b-1 hash checks all as planned. E3b-1's runner is not imported and nothing writes under its folders.

## Verdict

**Fix then start.** Blocking: the pre-aligned-leg crossing (1) and the middle-half band (2), both in `attribution.py`'s recorder, with the matching `SwitchTally` and test changes. Commit and push before `project`, since every later stage is bound to its commit.