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

## Corrections (2026-09-29, D137)

Both reviewers checked these results against the records (`docs/reviews/20260929-233515-E2d-results/`)
and said "fix", for text only. Both recomputed every registered reading and confirmed it. The
corrections below quote what was written above, which is left as it was; each figure was checked
against the records before it was written here.

1. **"Knowing that module is near its ceiling on this task."** (For E3.) **Withdrawn** (Fable). It
   contradicts the plan, which says the diagnosis does not establish a ceiling, and the records:
   - the ES is "budget-limited";
   - non-stereo champions reach 2.64, 2.84 and 2.92.
2. **"Why random sampling came close, as far as this shows: every method lands in the same non-stereo
   basin, whose level is about 2.2."** Not measured (both).
   - Nothing compared the champions' genomes or behaviour, so "basin" claims more than the probes
     can.
   - Random sampling's champions sit below the plateau: median 1.64, and only 35 of the 47 distinct
     champions lie in the 1.90-2.50 band.
   - On these worlds the GA averages 1.98 against random sampling's 1.62. Without run 2 the gap is
     0.49.
   - **Supportable:** random sampling's champions also meet no "uses" criterion (0 of 8), so all
     three methods differ within one operational class, and none approaches 8.7.
3. **"There is at least one stereo strategy at the plateau's level; evolution did not find even
   that."** Too strong (both). The k = 4 reference is a scripted controller. It shows the probes are
   sensitive at that score, not that an N2 genome can express stereo steering through this interface,
   nor that selection would prefer it at equal score. The sensing geometry, the interface, shaping
   and a seeded start are **hypotheses to test**, not established routes.
4. **"No champion uses the left-right difference"**, **"None of the 47 evolved champions steers by
   the left-right difference"**, and **"Part B shows only that they do not benefit from intact
   bilateral input"**. Too absolute (Astra). What the records show:
   - **no champion meets the plan's "uses the left-right difference" criterion.** "A non-stereo
     plateau" is the plan's operational reading;
   - 43 distinct champions show no material benefit;
   - 4 are unclear, with small detectable benefits from intact bilateral input.
5. **The sign-flip tests, required beside each interval, were omitted** (both). Two disagreements
   were unstated.

   | Contrast | 90% interval | Sign-flip p, 8 runs | Without run 2 |
   |---|---|---|---|
   | C1 | excludes 0 | **0.125 (disagreement)** | p 0.250 |
   | C2 | excludes 0 | 0.008 | p 0.016 |
   | C4 | excludes 0 | 0.023 | p 0.047 |
   | C3 | includes 0 | 0.781 | p 0.453 |
   | the interaction | excludes 0 (−0.659 to −0.044) | **0.148 (disagreement)** | −0.140 (−0.314, +0.007) |

   The interval decides, as registered.
6. **The interaction.** Without run 2 the estimate is −0.140 (−0.314 to +0.007). Run 2 supplies
   −1.589 of the −2.570 total (62%): each single change rescued run 2, so the difference of
   differences is mechanically negative there. "Not claimed" stands (both).
7. **"Inconclusive" for C4 − C1 and C4 − C2′.** The plan fixes no reading for these two contrasts;
   the label is the runner applying the arm rule (Fable). C4 − C1, the cleanest mutation contrast,
   is small and positive both ways: 8 runs +0.083 (+0.039 to +0.122); 7 runs +0.076 (+0.029 to
   +0.120).
8. **"That one pair supplies most of each arm's mean."** False for C2 (both).
   - **Run 2's share of the total paired gain:** C1 81%, C4 64%, C2 50%.
   - **C1's and C4's 32 training worlds already score non-zero at generation 0,** so their run 2
     changes the initial selection signal. C2's run 2 rescues the original all-zero start (Astra).
   - **C2's other seven runs all improve;** its qualified reading reflects missing the +0.3 bar
     without run 2 (+0.247), not a vanishing gain.
   - **No control with fresh mutation draws at unchanged settings exists** (Fable). So the rescue of
     run 2 cannot be attributed to either change.
9. **Narrow margins, flagged for C0 only** (Fable):
   - C4's mean gain is 0.3044 against the 0.3 bar. Against E2's registered champion it is 0.279,
     which would read "inconclusive";
   - 04a's unshaped set is exactly three-quarters (3 of 4). One more "unclear" would make it "mixed"
     and remove the plateau reading.
10. **C0's per-champion rates, promised by the plan, were omitted** (both).
    - **Middle bin at 02's scale, by parent:** 0.87, 0.86, **0.75** (run 2), 0.83, 0.84, 0.85, 0.82
      and 0.84.
    - Run 2's parent supplies 601 of the 2 343 pairs. Without it, the pooled rate is 0.84.
    - **At × 0.5 and × 0.25, the scales C2 and C4 use,** the pooled rates are 0.794 and 0.772,
      below the 0.8 line. Selection noise matters more after mutation is made gentler.
11. **The ledger's total** is 14 036 s (14 036.1 summed over the attempts), not "14 037 s", which
    summed rounded rows (both). 3.90 hours stands.

**Added from the reviews** (checked against the records):
- **C2's mean, 2.41,** equals 04a's four unshaped runs at 02's unchanged mutation (2.39), whose
  runs had different seeds and worlds (Fable).
  - Two of C2's eight gains (+0.009, +0.051) are near the hold-out's error.
  - Its arm-reference correlation is −0.17, so pairing removed little variation.
  - Gentler mutation is a lead to retest with fresh paired seeds, separating the rescue of failed
    starts from gains among successful ones (Astra).
- **C3's run 2** never moved from its start genome. Its champion is the start genome, so its "no
  material benefit" class is vacuous; the "31 of 32" above includes it (Fable). A conditional escape
  problem at σ 0.25 from an all-zero start, not a general case for larger σ (Astra).
- **Scores of 2.5 or more per arm:** C1 0, C2 2, C4 0, C3 1.
- **Chance for the top-8 overlap** (8 of 64) is 0.125. Run 2's parent sits at 0.09-0.26 (Fable).
- **C2′'s run 5** is "unclear" (real − swapped +0.19 to +0.49) at a matched checkpoint, while C2's
  final run 5 shows no benefit. Partial dependence on bilateral input appears during a run and is
  not kept (Fable).
- **Arm C3's accounting attempt** ends at commit `937e8b9`, not `6ec1761`. Two documentation
  commits (the READMEs and the roadmap) landed while it ran; no guarded file changed (Fable).
