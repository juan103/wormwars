# E2d: diagnosing Task N. Results

**Exploratory.** Every measure, threshold and reading below was fixed in the plan
([`PLAN.md`](PLAN.md), v4), reviewed, committed and pushed before any GPU work. Every number is from
the committed records in this folder:
- `part-a.json`, `part-b.json`, `part-c0.json`, `replay.json`;
- `arm-c1.json` to `arm-c4.json`, `evaluation.json`;
- `compute-attempts/`.

The formal stages ran once each, in order, on 2026-09-29 (17:37-21:32 UTC), on the agreed code
(runner at `a337d48`), with no stop, rerun, skip or amendment: 3.90 GPU-hours against a cap of 7.

## The readings (in the plan's words)

| Part | Reading |
|---|---|
| B, stereo use | **"a non-stereo plateau"**: every read set is "non-stereo", and every set's median lies in 1.90-2.50 |
| B, budget | **"budget-limited"**: the extended ES beats the formal ES by +0.24 on average (90% interval +0.12 to +0.38) |
| C0, selection noise | **"selection noise is not material by this rule"**, narrowly: 0.82 against a threshold of 0.8 |
| C1, 32 worlds | **inconclusive** |
| C2, halved mutation | **"supports, carried by run 2"** |
| C4, both | **"supports, carried by run 2"** |
| C3, the ES at σ 0.25 | **inconclusive** |
| Leaves the plateau | **no arm** |
| Interaction (C4) | **not claimed** |

**What the plan says this points to** (its guidance, fixed in advance): no arm leaves the plateau,
and Part B finds a non-stereo plateau, so *"these changes do not reach the stereo strategy. The next
design question is whether to make it reachable (the sensing geometry, the interface, shaping toward
left-right steering, or a seeded start), or to build E3 on the non-stereo module knowingly."* It
also says this does not show that the optimizer is not a bottleneck. "Budget-limited" makes longer
runs a promising setting for the ES. Neither C2 nor C4 reached a plain "supports", so neither
setting is recommended by the rule.

## The controls' replay

E2's GA and ES, generations 0-25, replayed twice with E2's seeds, ids and composition on CUDA in the
default mode. **Both replays reproduced E2 exactly:**
- the generation-0 and generation-25 checkpoint hashes;
- the validation counts;
- every logged best genome;
- the configuration hash.

E2's own runs are therefore valid paired controls (`replay.json`).

## Part B: do the champions use the left-right difference?

**The checks passed** (`part-b.json`). Under `mean` (the difference removed) and `swapped` (the
difference reversed), the stereo controllers collapse and M-avg does not move:

| Reference | Real | Mean | Swapped | Class |
|---|---|---|---|---|
| S-const (E1's stereo navigator) | 8.70 | 0.04 | 0.00 | uses |
| **S-const at k = 4** (a low-gain stereo steerer) | **2.27** | 0.07 | 0.02 | uses |
| M-avg (reads only the mean) | 2.20 | 2.20 | 2.20 | no material benefit |

The k = 4 reference scores at the champions' level and still collapses. So the probes do detect
stereo steering at the plateau's performance.

**The champions** (47 distinct genomes; hold-out means on 1 024 new worlds):

| Set | Uses the difference | No material benefit | Unclear | Median (real) | Reading |
|---|---|---|---|---|---|
| E2's GA | 0 | 7 | 1 | 2.17 | non-stereo |
| E2's ES (formal) | 0 | 8 | 0 | 2.17 | non-stereo |
| E2's extension | 0 | 8 | 0 | 2.32 | non-stereo |
| 04a, shaped | 0 | 11 | 1 | 2.27 | non-stereo |
| 04a, unshaped | 0 | 3 | 1 | 2.29 | non-stereo |
| random sampling (classified, not read) | 0 | 7 | 1 | 1.64 | — |

- **No champion uses the left-right difference.** Over all 47, real − mean ranges from −0.07 to
  +0.18, and real − swapped from −0.10 to +0.54.
- **The four "unclear" champions** show small but detectable benefits from intact bilateral input,
  well short of a stereo steerer's:
  - E2's GA run 4: real − swapped +0.54, with a lower bound of 0.48, just under the 0.5 threshold,
    but real − mean only +0.06;
  - 04a run 12: +0.18 and +0.33;
  - 04a run 8 and random sampling's run 2: smaller still.
- **Named in the plan:**
  - 04a run 2 (the module chosen for E3): 2.64 under every probe, no material benefit;
  - 04a run 12: 2.84, unclear;
  - the extension's run 3, the best E2 champion: 2.92, no material benefit.

**The budget reading.** The extended ES against the formal ES, paired by run, on the new worlds:
- mean gain **+0.243**, median +0.165;
- 7 of 8 runs improved (run 6's champion is the same genome in both);
- 90% interval +0.120 to +0.379; sign-flip p 0.016.

The plan disclosed that this reading was expected from E2's own hold-out (mean +0.25); on fresh
worlds it holds. The extension spent 100 608 more selection episodes per run on top of 166 144, and
chose its champion over 42 checkpoints.

## Part C0: how reliably do 8 worlds rank what selection compares?

A local surrogate: each of E2's 8 GA champions and 64 of its children, and each formal ES mean and
32 antithetic pairs, all on 256 probe worlds (`part-c0.json`).

**Mutation at 02's scale is very destructive:**

| Mutation scale | Parent (mean) | Children (mean) | Children under half the parent | Children at 0 | Top-8 overlap |
|---|---|---|---|---|---|
| × 1 (02's) | 1.97 | 0.41 | 78% | 11% | 0.73 |
| × 0.5 | 1.97 | 0.68 | 61% | 5% | 0.69 |
| × 0.25 | 1.97 | 1.10 | 40% | 2% | 0.54 |

**Ranking siblings by 8 worlds, scored against the other 248** (at 02's scale; pooled over the 8
parents):

| Gap between the siblings | Pairs | Correct | Tied | Ties counted half |
|---|---|---|---|---|
| 0.05-0.15 | 3 073 | 0.50 | 0.37 | 0.69 |
| 0.15-0.30 | 2 343 | 0.74 | 0.16 | **0.82** |
| 0.30-0.60 | 2 737 | 0.91 | 0.05 | 0.93 |

- **The reading uses the middle row: 0.82 ≥ 0.8, so "not material by this rule".** At the smallest
  gaps, 8 worlds are right half the time and tie more than a third of the time.
- **The ES's pairs:** an 8-world pair difference has the sign of the 248-world difference 74% of the
  time at σ 0.5 (11% tied), and 60% at σ 0.25 (16% tied).
- **The references' own error:** 0.038-0.045 (bootstrap).

## Part C: one change each, paired with E2's runs

Each arm's 8 champions against their paired reference, on the same 1 024 hold-out worlds
(`evaluation.json`). Every arm completed and passed its pairing check.

| Arm | Against | Mean gain (8 runs) | 90% interval | Median | Improved | Without run 2 | Reading |
|---|---|---|---|---|---|---|---|
| C1, 32 worlds | E2's GA at matched checkpoints | +0.222 | +0.016, +0.551 | +0.059 | 5/8 | +0.049 | inconclusive |
| C2, halved mutation | E2's GA | +0.432 | +0.163, +0.770 | +0.187 | 8/8 | +0.247 (+0.112, +0.398) | supports, carried by run 2 |
| C4, both | E2's GA at matched checkpoints | +0.304 | +0.079, +0.642 | +0.151 | 7/8 | +0.125 (+0.049, +0.197) | supports, carried by run 2 |
| C3, the ES at σ 0.25 | E2's formal ES | −0.157 | −0.640, +0.208 | −0.035 | 3/8 | +0.106 | inconclusive |

**Run 2.** E2's GA run 2 started from a generation-0 population that scored 0 everywhere. Its
champion scores 0.69 on these worlds, both the registered one and the one re-chosen at matched
checkpoints (0.75 on E2's own hold-out).
- Every GA arm's run 2 escaped: C1 2.12, C2 2.42, C4 2.25. That one pair supplies most of each
  arm's mean.
- **C3's run 2 never left zero:** from the same all-zero start, no perturbation at σ 0.25 scored in
  622 generations. E2's ES, at σ 0.5, left it at generation 52.

**Leaving the plateau:** no arm has 4 champions that either use the difference or score 2.5 or more.
- Of the 32 arm champions, none uses the difference; 31 show no material benefit and 1 (in C2) is
  unclear.
- The best scores are C2's 2.64 and C3's 2.62.

**The combined arm, contrasted** (all at matched checkpoints):
- **C4 − C1** (only mutation differs): +0.083 (+0.039, +0.122), inconclusive;
- **C4 − C2′** (a work-allocation contrast): −0.099 (−0.266, +0.039), inconclusive;
- **the interaction** (C4 − C1) − (C2′ − E2's GA′): −0.321, with an 8-run interval of −0.659 to
  −0.044. It is **not claimed**, because the rule needs both the 8-run and the 7-run intervals to
  exclude 0.

## The ledger

From the accounting's attempt files, committed in `compute-attempts/`. Episodes equal worlds built,
and each matches the plan's arithmetic.

| Stage | Episodes | Wall time |
|---|---|---|
| projection | 121 344 | 158 s |
| Part B | 153 600 (150 arms × 1 024) | 400 s |
| C0 | 665 600 (40 batches × 65 × 256) | 584 s |
| replay | 229 376 (2 × 2 × 8 runs × 28 × 256) | 516 s |
| C1 | 2 070 528 (8 × 258 816) | 2 016 s |
| C2 | 2 131 968 (8 × 266 496) | 4 880 s |
| C4 | 2 070 528 | 2 003 s |
| C3 | 1 329 152 (8 × 166 144) | 3 092 s |
| Part C's pass | 147 456 (48 genomes × 3 probes × 1 024) | 388 s |
| **total** | | **14 037 s, 3.90 GPU-hours** |

The plan estimated about 6.0 hours. The projection measured a 32-world generation at 7.8 s, where the
plan had scaled E2's 8-world time by four, and estimated 3.86 hours in all; the run took 3.90.

## What this means (not registered: interpretation)

- **The plateau is a non-stereo plateau.** None of the 47 evolved champions steers by the left-right
  difference, whichever optimizer or setting produced them. Nearly all score like M-avg, the scripted
  controller that reads only the mean of the two sensors. The stereo strategy, which reaches 8.7 on
  this body and task, is not found. The low-gain stereo steerer scores 2.27, like the champions, so
  there is at least one stereo strategy at the plateau's level; evolution did not find even that.
  How the champions navigate is not measured here: Part B shows only that they do not benefit from
  intact bilateral input.
- **Why random sampling came close,** as far as this shows: every method lands in the same non-stereo
  basin, whose level is about 2.2. The optimizers add something within it (E2: 22-30%). The gentler
  mutation adds a little more (C2 improved all 8 runs). None moves out of it.
- **Mutation is the clearest operator lead.** 02's mutation leaves most children far worse than
  their parent, and halving it improved every paired run. By the registered rule this is "supports,
  carried by run 2", not "supports", so it is a lead for E3's design, not a finding.
- **Noise is real but did not cross the rule's line.** 8 worlds tie or misrank close siblings often,
  yet 32 worlds per genome (C1) did not reliably help at equal work.
- **A smaller σ has a cost at the zero plateau:** one run never started. A larger σ, or a start that
  scores, matters for the ES from an all-zero population.
- **Budget:** the ES was still gaining when E2 stopped it; the extension's gain holds on new worlds.

**For E3, as the plan frames it:** these changes do not reach the stereo strategy. The design
question is whether to make stereo steering reachable, or to build E3 on a non-stereo navigation
module knowingly, knowing that module is near its ceiling on this task. The ways to make it reachable
are:
- the sensing geometry;
- the interface;
- shaping toward left-right steering;
- a seeded start.

This is the owner's and the reviewers' decision at E3's design, informed by these readings.

## What E2d does not establish

- Whether other operators, representations, budgets or combinations would reach stereo steering.
- How the champions navigate; Part B measures dependence on intact bilateral input only.
- Anything beyond N2, Task N and these settings.
- Confirmatory claims: this is an exploratory diagnosis with 8 paired runs per arm.

## Deviations and disclosures

- **None from the plan:**
  - no stage stopped, reran or was skipped;
  - the admission rule and the hard stop never triggered;
  - the replay passed before Part C;
  - every arm passed its pairing check.
- **This file was written after the chain finished.** Every number was taken from the committed
  records, and checked against them before committing.
