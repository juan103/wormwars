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

## Corrections (2026-10-05, after both reviewers; `docs/reviews/20261005-E3c-pilot/`, D204)

1. **The Q2 comparison was wrong** (both reviewers).
   - **The text said:** "on a different block, E3b-1's tuned champions made about 1.3 visits per wey above the
     seed".
   - **Why it is wrong:** +1.32 is E3b-1's gain pooled over T-A and T-F. E3c reuses T-F alone, which made
     +2.23 visits above the seed (d = +0.381; `E3b-1/RESULTS.md`, `evaluate.json`).
   - **What holds:** in units of the seed's mean, the S arms' gain on the pilot block (about +0.38) equals
     T-F's on E3b-1's block. Q2's direction is open; it is not suggested by the pilot.
2. **The block difference was overstated** (both).
   - **The text said:** "with a per-maze SD of 3.7, the seed's block means move by about a visit between blocks
     of this size".
   - **Why it is wrong:** with 128 and 256 mazes, the block means' standard errors are about 0.33 and 0.23.
     The 1.02 difference is about 2.5 standard errors: unusual, not typical.
   - **What holds:** the comparisons within one block are unaffected.
3. **The diagnostic's compute is charged** (Astra): about 0.03 GPU-hours. E3c has used about 2.85, not 2.82.
4. **`share_above_w2` is not interpretable** (Fable). It compares each strain's mean over its own 8
   generation-0 training mazes with W2 alone on the 128-maze block. Runs 11 and 12 show 0.0 and run 10
   shows 0.97 because their training mazes differ, not their draws. It is dropped from any reading.
5. **The factor** (Astra): D203 says §5's rule "keeps E3c in the mazes, at factor 1.0". The branch is fixed by
   the rule. Keeping the factor at 1.0 is a choice §5 permits, supported by the pilot.

**Added evidence on the scent question** (from the reviewers; checked against `pilot.json`):
- **On maze 7658,** W2 alone makes 12.1 visits and the seed 20.4. The S champions make only 5.75-7.0, below
  the blind reflex on the maze where the reflex does best. That argues against "merely reliable
  navigation" (Fable).
- **The champions' per-maze maxima are 7.75-8.0.** Fable's estimate of the ceiling for a full traversal of a
  25-cell tree at maximum speed is about 8.7 visits per wey; the analysis is Fable's and has not been checked
  here.
- **The champions' per-maze scores correlate weakly with the seed's** (Spearman 0.14-0.25). They correlate
  with each other more strongly (Pearson 0.56-0.90, Astra).
- **The reading that fits** is goal-agnostic coverage of the tree, helped by the wall reflex. It is still an
  inference: no champion has been probed.

## The replay and probe (exploratory; D205; `replay.json`)

**When and what:** 2026-10-05, 1.10 GPU-hours, code at ec69134. Both reviewers checked the code first and
said "fix first"; all findings were taken (D205's note).

**The replay is exact.**
- Every generation's best-genome hash of the pilot's S-dense batch matches the pilot's: 100 of 100 in each of
  runs 10-12.
- The champions' intact plays equal the pilot's per-maze records, and so do the seed's and W2 alone's.
- The saved genomes (local, `runs/e3c/genomes/`) are therefore the pilot's own champions.

**The outcome fixed in advance is "coverage."** All three champions meet every condition (pilot block, 128
mazes; visits per wey):

| | Intact visits | Noses removed | Retained | Coverage (intact) | Tour match (intact) |
|---|---|---|---|---|---|
| S-dense run 10 | 6.789 | 6.832 | 1.006 | 0.998 | 0.990 |
| S-dense run 11 | 6.739 | 6.745 | 1.001 | 0.993 | 0.992 |
| S-dense run 12 | 6.649 | 6.644 | 0.999 | 0.990 | 0.985 |
| The seed E + W2 | 4.824 | 1.662 | 0.345 | 0.793 | 0.070 |
| W2 alone | 1.720 | 1.720 | 1.000 | 0.826 | 0.058 |

**What the table shows:**
- **Removing the noses changes the champions' visits by −0.1% to +0.6%.**
  - They cover essentially the whole maze.
  - 98.5-99.2% of their moves repeat the move 48 earlier, the period of a full circuit of a 25-cell tree.
- **The seed keeps 35% of its visits without its noses,** and its moves do not repeat at that period.
- **The champions' resting turn is offset** by about +0.49 to +0.52 from the seed's. Their module A's K_D at
  q = 0 is about 0 (−0.017 to 0.004).
- **The reading:** the from-scratch champions solve these mazes as wall-followers. A standing turn bias
  presses them against one wall, W2's reflex turns them away from it, and they circle the whole tree,
  collecting both sources on every lap. They do not use the scent.

**A scent-free reference: W2 alone with a constant resting turn** (Fable's suggestion; a sweep, not tuned
beyond its grid):

| Resting turn | −0.8 | −0.4 | 0.0 | 0.2 | 0.4 (W2) | 0.6 | 0.8 | 1.0 | 1.2 | 1.4 |
|---|---|---|---|---|---|---|---|---|---|---|
| Visits | 0.02 | 0.26 | 0.46 | 0.73 | 1.72 | 1.92 | 3.35 | 4.17 | 5.64 | 5.81 |
| Tour match | 0.81 | 0.34 | 0.37 | 0.29 | 0.06 | 0.06 | 0.24 | 0.90 | 1.00 | 1.00 |

**What the sweep shows:**
- **W2 with a resting turn of 1.2-1.4 makes 5.6-5.8 visits,** above the engineered seed's 4.82 on this block,
  with no module at all.
- **Its coverage is 0.87-0.89 against the champions' 0.99,** so its circuit misses part of some mazes.
- **The point at −0.8 barely moves** (0.02 visits, coverage 0.10). Its tour match of 0.81 comes from
  circling in place, not from a circuit of the tree.
- **The champions add about 1 visit per wey to this reflex circuit** and complete it.

**What follows, as D205 fixed:**
- the coverage hypothesis is registered;
- the stereo-assembly language is narrowed;
- the formal noses-removed reading is kept;
- by the owner's choice, E3c then runs as designed, with these readings interpreting Q1 and Q2.
