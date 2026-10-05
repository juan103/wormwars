# E3c pilot (exploratory)

The pilot of `docs/E3/E3c-DESIGN.md` v2.1 §5, run before the pre-registration. Nothing here is a registered
result.
- **Code:** commit e2f0273 (`scripts/e3c.py pilot`), reviewed by both reviewers (D201).
- **When:** 2026-10-04, 21:22 to 00:11 UTC; 2.82 GPU-hours of wall time (`compute-record.json`).
- **The record:** `pilot.json`.

## What ran

- **The arms:** S-mod (runs 0-2), S-dense (runs 10-12) and P-sel (runs 20-22).
- **The schedule:** 100 generations × 8 mazes, at mutation factor 1.0.
- **The checkpoints:** every 25 generations and at 99, on the pilot block (mazes 7600-7727, 128 mazes).
- **The references,** on the same block: W2 alone and the seed E + W2.
- **The mazes:** 7 327 checked before the run; 6 redrawn under Amendment 1.
- **A check:** every frozen parameter was verified bitwise against its draw, in every final population and
  checkpoint candidate.

## The decision branch (fixed in advance): "mazes"

**The criterion:** an arm is off the floor if a checkpoint exceeds W2 alone + 1 visit per wey, that is
1.720 + 1 = 2.720.
- All three arms were off the floor.
- §5's rule therefore keeps E3c in the mazes as designed.
- The mutation factor stays at 1.0: the from-scratch arms learned at it.

## The numbers (visits per wey, pilot block)

**References:** W2 alone 1.720; the seed 4.824.

| Arm | Run | Gen 0 | 25 | 50 | 75 | 99 | Legs per wey at 99 |
|---|---|---|---|---|---|---|---|
| S-mod | 0 | 1.63 | 6.20 | 6.35 | 6.63 | 6.60 | 5.63 |
| | 1 | 1.77 | 6.03 | 6.59 | 6.59 | 6.63 | 5.64 |
| | 2 | 1.75 | 6.29 | 6.65 | 6.69 | 6.70 | 5.71 |
| S-dense | 10 | 1.68 | 6.33 | 6.38 | 6.65 | 6.79 | 5.79 |
| | 11 | 1.65 | 6.20 | 6.66 | 6.65 | 6.74 | 5.75 |
| | 12 | 1.75 | 6.31 | 6.37 | 6.20 | 6.65 | 5.66 |
| P-sel | 20 | 0.71 | 0.88 | 1.66 | 2.09 | 2.34 | 1.44 |
| | 21 | 0.76 | 1.66 | 1.70 | 2.14 | 2.29 | 1.42 |
| | 22 | 0.73 | 1.54 | 4.41 | 5.06 | 5.22 | 4.41 |

**Checkpoints** are each run's generation-best by training fitness, played on the pilot block. Legs per wey
come from the final generation-best's play on the same block.

## What stands out (exploratory; for the reviewers)

1. **The from-scratch arms beat the seed by a wide margin, and early.**
   - **The levels:**
     - by generation 25 both S arms were at 6.0-6.3, from 1.6-1.8 at generation 0;
     - by 99 they were at 6.6-6.8, about 1.8-2.0 visits per wey above the seed on the same block.
   - **The spread between runs is small:**
     - S-mod 6.60-6.70;
     - S-dense 6.65-6.79.
   - **The design's registered expectation for Q2** is "P-joint better" than S-mod. For comparison only,
     on a different block, E3b-1's tuned champions made about 1.3 visits per wey above the seed. The two
     numbers come from different blocks and schedules; the formal run compares them on one block.
2. **The from-scratch champions score almost the same on every maze; the seed does not.**
   - **Per-maze SD:**
     - the S champions: 0.47-0.58;
     - P-sel: 0.88-0.99;
     - the seed: 3.68, ranging from 0.25 to 20.4.
   - **Against the seed, maze by maze:** the S champions are better on 76-80% of mazes.
   - **What would explain it, untested:**
     - a maze-independent, possibly scent-independent routine, such as a stereotyped traversal helped by
       W2's wall reflex;
     - or scent-guided navigation that is merely reliable.
   - **Why it is untested:**
     - the pilot saved no genomes, so the champions cannot be probed now;
     - no scripted wall-follower exists among the controls. E3b-1's "walk" is a random walk with W1's
       reflex, at 1.94 visits.
   - **Why it matters for E3c:** if the S champions do not use their noses, Q1 and Q2 compare routes to a
     scent-free strategy, not assemblies of navigators.
3. **P-sel found a working selector in 1 of 3 runs** (run 22: 5.22). The other two stayed near 2.3.
   - **Its generation-0 draws score below W2 alone** (medians 0.36-0.53), so random selectors fight the
     reflex, as §4 anticipated.
   - **E3a's open arena:** 1 of 8 runs.
4. **Generation 0's offsets are 0 by construction** (a check), for every arm:
   - the draws are mirror-symmetric, so the maximum |offset| is ≤ 1.5 × 10⁻⁷;
   - module A's K_D at q = 0 is near 0 for the S draws (medians −0.004 to 0.023), against about 30 for P-sel,
     whose comparators are E's.

## A check on the seed's level (diagnostic, not a stage)

**The puzzle:** the seed makes 4.82 here but 5.84 on E3b-1's test block.

**The check** (`diagnostics/seed_check.py`, about 2 GPU-minutes, not counted in the compute record):
- it played the seed both ways:
  - E3c's way: `play` on the started organism;
  - E3b-1's way: `play_batch` on the seed genome;
- on both blocks.

**What it found** (`diagnostics/seed-check.json`):
- both ways agree exactly: 5.840 on E3b-1's test block, reproducing E3b-1, and 4.824 on the pilot block;
- so the difference is the block, not the code;
- with a per-maze SD of 3.7, the seed's block means move by about a visit between blocks of this size;
- the pilot's comparisons are within one block, so they are unaffected.

## What the formal run needs from this (for the reviewers and the pre-registration)

- **Save the champions' genomes** (locally), so any reading can be rerun.
- **A reading of scent dependence,** if the reviewers agree. It would play each champion with its noses
  silenced (E3b-2's `without_scent`), plus possibly a scripted wall-follower reference. Either would be
  labelled as added after this pilot.
- **The power analysis:**
  - the S arms' run-to-run spread is about 0.05-0.07 visits per wey (d of about 0.01-0.015);
  - P-sel's outcome looks bimodal (1 success in 3).
