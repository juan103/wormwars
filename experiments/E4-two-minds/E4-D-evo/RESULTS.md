# The evolutionary E4-D: results

**The formal run, 2026-10-14/15, as pre-registered** ([`PREREGISTRATION.md`](PREREGISTRATION.md), bound at c3fe432,
D274; Amendment 1, D276; the formal code 5237304, D278). Every number here is in [`summary.json`](summary.json),
derived from the committed records in [`formal/`](formal/) by `scripts/e4d_evo_summary.py`.

## The answer

**L, the confirmatory arm: "practically relevant transfer found."** Starting from E-G with the 32 cross-link slots at
0 and mutating only those slots, selection on the trial's outcome recruited cross-links that carry A's engineered cue
into B, in all 32 independent runs.

| | L (confirmatory) | F (secondary) |
|---|---|---|
| runs | 32 | 4 |
| the champions' mean real-first share on their own test blocks | **0.912** | 0.891 |
| the mean gain over 0.5, one-sided 95% bounds [LB, UB] | **0.412** [0.401, 0.423] | 0.391 [0.358, 0.423] |
| the reading (δ = 0.15) | **practically relevant transfer found** | practically relevant transfer found |
| the exact one-sided sign-flip p | 2.3 × 10⁻¹⁰ (= 1/2³², the smallest possible) | 0.0625 (= 1/2⁴, the smallest possible) |
| the champions' shares, lowest to highest | 0.805-0.969 | 0.867-0.930 |
| the champion minus E-G on the same block, mean (lowest) | 0.418 (0.313) | 0.398 (0.375) |

- **The rule:** LB > 0.15, the owner's margin, is the first of §7.1's five states. The interval is approximate
  (model-based); the sign-flip p is distributional (sign symmetry).
- **S, the seeded follow-up, was not triggered:** it runs only if L reads "practical gain excluded; transfer not
  detected" or "inconclusive" (§3).
- **The limits, as registered (§7.1):** an engineered cue, 32 links between engineered modules, selected junction
  starts, and this GA at 100 generations of 8 mazes. The result says that this GA, at this budget, recruited the
  transfer from E-G. It does not say anything about naive modules, other tasks or cues that are not engineered.

## Each champion's controls (§7.3)

Each champion was also played on its own test block with A's cue altered, and with its links cut. Shares of the 128
trials, mean over the champions (lowest-highest):

| condition | L real-first | L decoy-first | L neither | F real-first | F neither |
|---|---|---|---|---|---|
| **intact** | **0.912** (0.805-0.969) | 0.043 | 0.045 | **0.891** | 0.062 |
| the cue **reversed** (A told the decoy) | 0.043 | **0.912** | 0.045 | 0.047 | 0.062 |
| the cue **held fixed** | 0.477 (0.445-0.500) | 0.477 | 0.046 | 0.465 | 0.070 |
| the cue **removed** | 0.094 (0-0.500) | 0.094 | **0.812** | 0.033 | **0.934** |
| the links **cut** | 0.494 (0.484-0.500) | 0.494 | 0.011 | 0.359 (0.258-0.500) | 0.281 |
| E-G | 0.494 | 0.494 | 0.011 | 0.492 | 0.016 |

- **The champions use A's cue.** Reversing it sent every champion to the decoy (32 of 32 in L, 4 of 4 in F), with each
  champion's real-first, decoy-first and neither counts exactly swapped. Holding it fixed left every champion balanced on every maze, as asserted.
- **In L the links carry all of it:** cutting them gave E-G exactly, bitwise, as asserted.
- **In F** the module itself also evolved, so cutting the links does not give E-G. Cut champions stay balanced on every
  maze (asserted), but enter less (0.28 of trials enter neither candidate, against E-G's 0.016).
- **Removing the cue mostly stops the evolved champions from entering at all.** In L, 0.81 of trials entered neither
  candidate; per champion, from 0 to 128 of 128 trials, with 24 of 32 champions at 100 or more. The hand-built control
  did not do this: with its cue removed it entered all 128 trials, at 0.5 (`formal/check.json`). So the evolved
  champions do not only steer by A's cue; most of them need it to approach a candidate at all. This was not predicted,
  and its mechanism was not measured.

## How the champions wired the links (§7.4; descriptive)

The hand-built control copies A's comparators into B's comparators (A_CL → B_CL and A_CR → B_CR at w = 3; D262). **The
evolved champions did not.** Their strongest consistent slots run from A's comparators into **B's noses**, with small
weights:

| slot | L mean weight | L champions with a positive weight |
|---|---|---|
| A_CL → B_NL | +0.24 | 29 of 32 |
| A_CL → B_NR | −0.22 | 1 of 32 |
| A_CR → B_NL | −0.25 | 4 of 32 |
| A_CR → B_NR | +0.19 | 26 of 32 |

Four signed contrasts summarise each champion's slots into B. **They were chosen after seeing L's data, so they are
exploratory:**

| contrast (½ × same side − opposite side) | the hand-built control | L mean (lowest-highest) | L positive | F mean | F positive |
|---|---|---|---|---|---|
| A's comparators → B's noses | 0 | **0.45** (0.16-0.87) | **32 of 32** | 0.34 | 4 of 4 |
| A's comparators → B's comparators | 3 | 0.08 (−0.31-0.52) | 21 of 32 | 0.05 | 3 of 4 |
| A's noses → B's comparators | 0 | −0.01 (−0.42-0.45) | 15 of 32 | −0.04 | 1 of 4 |
| A's noses → B's noses | 0 | 0.07 (−0.39-0.49) | 20 of 32 | 0.06 | 3 of 4 |

- **Every champion, in both arms, carries a positive comparator → nose contrast.** The weights are far smaller than
  the hand-built control's 3: the feasibility check needed w ≈ 2-3 for its comparator-origin wiring (D262). Read
  descriptively, evolution fed A's steering signal into B's sensory input, upstream of B's comparators, rather than
  copying it into the comparators.
- **The other slots are not near zero.** The summed |weight| of each class of 8 slots is about 1.1-1.6 on average,
  into A as well as into B (`summary.json`, `wiring.by_class`). Much of it may be unselected drift, since most strains
  tie on fitness (below); this was not measured.

## Training (§7.4; descriptive)

- **The checkpoints** (the 8-maze checkpoint block, 16 trials, noisy): L's mean real-first share rose from 0.50 at
  generation 0 to 0.72 at 10, 0.81 at 20, 0.87 at 40 and 0.93 at 99. F's rose to 0.78 at 10 and 0.95 at 99.
- **The champions' validation shares** (64 mazes each) averaged 0.939 in L, against 0.912 on the fresh test blocks:
  the champion choice is optimistic by about 0.03 (validation above test in 25 of 32 runs). The registered estimand
  uses the test block, so this does not enter the reading.
- **Ties and turnover:** on average 0.95 of a generation's strains tie with another strain's fitness (at least 0.78 in
  every run's every generation; 16 trial outcomes per strain); 0.89 of each breeding's parents were mutated children of the previous one; a champion's lineage
  carries a median of 88 mutations (L, 80-94).

## The check (§5)

`check` passed before any training (`formal/check.json`, 787 s):
- **the positive control:** the hand-built comparator-origin control at w = 3 made 0.875 real-first (112 of 128),
  above the registered 0.75; E-G made exactly 0.5 (64 and 64); the oracle 0.914;
- **the evaluation path:** reversing the control's cue exactly swapped its counts (14 and 112); with the cue removed,
  held fixed and the links cut, it was balanced on every maze;
- **the replay:** the pilot's first 11 generations replayed bitwise, with the registered digest;
- **the timing:** 76 s per generation, projecting 2.53 GPU-hours for L's training against an allowance of 6.23.

## Compute

| group | GPU-hours | cap |
|---|---|---|
| check + L (`formal/compute-record-l.json`) | 2.75 | 8 |
| F (`formal/compute-record-f.json`) | 0.46 | 1.5 |
| S | not run | 6 |

**E4's total is now about 9.30 of 30 GPU-hours** (6.09 before the formal run, including a 128 s dry run that was not
recorded automatically and was added by hand, D278).

## What went wrong along the way, openly

- **Smokes had played formal ids** under the formal maze seed. Astra found it in the code review. Amendment 1 moved
  the whole formal layout to fresh ids before any formal stage ran, and the smokes now use their own seed (D276).
- **Three record commits were pushed without the hygiene tests** (D279). GitHub's suite failed on them, because the
  per-maze 0/1 outcome arrays look like edge lists to the connectome guard. No connectome data was involved. A narrow
  exemption fixed it, and every record commit since runs the hygiene tests first.

## Reproduce it

```
python -m pytest tests/test_e4d_evo_stats.py tests/test_e4d_evo_formal.py tests/test_e4d_evo_formal_stages.py tests/test_e4d_evo_trial.py tests/test_e4d_evo_summary.py
python scripts/e4d_evo_formal.py check --smoke --device cpu     # every stage has a toy-size smoke, in its own folder
python scripts/e4d_evo_summary.py                              # regenerates summary.json from the committed records
```

**A formal rerun** needs a disposable checkout: each stage runs once and refuses if its record exists, and `check`
needs `--owner-word`. The populations and selection matrices stay local (`runs/e4d-evo-formal/`); the records keep
their sha256. The GPU stages repeat exactly only on the same GPU, in the pinned environment, with the same batch
composition (rule 6). There, `check` replayed the pilot bitwise, and `train-l` and `train-f` rebuilt every final
population bitwise from the saved selections.
