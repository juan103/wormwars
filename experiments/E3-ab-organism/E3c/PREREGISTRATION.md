# E3c pre-registration: the assembly comparison in the maze shuttle

**Status: draft 4, for a confirmation pass by both reviewers.** Drafts 1 (54f6f5f), 2 (0e27083) and 3
(65cd529) were reviewed by both. Each time they said "revise", the last time narrowly (D207-D209). §15-§17 list
the changes. This text binds at the commit that is pushed after their agreement. From then
on, registered text is never changed or removed. Amendments are added beside it, dated (AGENTS.md, rule 2).

**Its sources:**
- the design, `docs/E3/E3c-DESIGN.md` v2.1 (D200);
- the exploratory pilot and its replay and probe (`PILOT.md`, D203-D206);
- the owner's choices:
  - E3c then E4 (D198);
  - the replay first, and running as designed if scent-free (D205);
  - the dual practical margin (2026-10-05).

Changes made after the pilot are marked **post-pilot** and listed in §13.

## 0. The binding sequence (both reviewers)

1. **This text** binds at its commit, together with:
   - the registered statistics, `wormwars/e3/e3c_stats.py` and their tests;
   - the power analysis, `scripts/e3c_power.py` → `power.json`.
2. **The formal stages of §5 are not yet written.** They are written after binding:
   - test-first, against §12's list;
   - reviewed by both reviewers;
   - their commit is recorded in a dated amendment (§14) and in every formal stage's start marker.
3. **What the formal stages may not change:** this text, the registered statistics and the engine paths
   (`wormwars/` outside `e3c_stats.py` and the new E3c stage code, `configs`, `requirements.txt`). Any change
   to them after binding is an amendment, with an equivalence check where it touches the engine (rule 7).

## 1. The question, narrowed by the pilot

**The pilot changed what E3c can say.**
- **What it found,** for the three replayed S-dense champions (D206):
  - they keep 99.9-100.6% of their visits with the noses removed;
  - they cover 99-100% of the maze, and repeat a full circuit of the tree.
- **A scent-free reference does nearly as well:** on the pilot block, W2's reflex with a constant turn bias makes
  5.6-5.8 visits, above the engineered seed's 4.82.
- **What remains open:** S-mod's champions were not probed. That they do the same is the hypothesis of §7.3.
- **The consequence:** E3c's questions compare **training routes on a task that a scent-free circuit solves**.
  They do not compare assemblies of stereo navigators.
- **The task is not changed,** as the design's §5 requires.

**The primary questions** (the design's §1, narrowed in wording):
- **Q1, structure under one training recipe:** from random weights, at equal training evaluations, does an
  organism on E's modular mask score differently from a dense controller of the same 11 neurons? It compares
  two masks under one start distribution and one search recipe. It is not a test of modularity in general.
- **Q2, the engineered initialization and its tuning recipe:** at equal training evaluations, do the engineered
  seed E + W2 plus tuning (P-joint) score differently from E's mask trained from scratch (S-mod)? The two arms
  differ in their starting values and in their mutation recipe (factor 0.25 against 1.0). The label names
  both.

**Registered mechanistic readings, post-pilot** (§7.3; descriptive classifications, not calibrated tests):
- **The coverage hypothesis:** the S arms' champions are coverers, and P-joint's champions are coverers less
  often.
- **Nose dependence,** measured directly: whether P-joint's champions depend more on their noses than the S
  arms'.

**Descriptive:**
- **P-sel:** selector-only training with E's modules frozen. How many runs end above the floor.
- **R-shared**, the engineered shared navigator, against P-fixed.
- **W2-turn,** the scent-free reference (§3).

**What the labels claim:**
- **The two bounded-equivalence statements:**
  - "no relevant difference": the contrast's interval lies inside the smaller margin, on this score and this
    test block;
  - "no material loss" (§7.3).

  Both are approximate (model-based), like every margin label. "Unclear" is never read as equivalent.
- **Not claimed:**
  - cumulative reuse savings;
  - anything about stereo navigation that the noses-removed reading does not support.

## 2. Fixed inputs

**The task:** E3b-1's maze shuttle, unchanged:
- c = 5, H = 2 400;
- colonies of 8 on up to 4 spawns;
- shared trails (μ 0.01, λ 0.02, δ 0.05, d₀ 1.142);
- maze run seed 1 180 000, with Amendment 1's redraw rule (`maze.walls_for`);
- W2 frozen;
- E2's GA (population 32, elites 3, truncation 8), with unshaped fitness (visits per wey).

**Pinned files** (sha256 after CRLF → LF; each checked before use, refusing on a mismatch):

| File | sha256 |
|---|---|
| E4s-0's `module.json` | 9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4 |
| the pilot's `pilot.json` | 6f6402ebecdf34633a77f8e4df97f8cf9a1e86316179116a63a668286d9ee41e |
| E3b-1's `train-tf.json` | 68f485107eefb9609d192b50b7e227c50732e6c1159cd656d2118d05ba05f01b |
| E3b-1's `maze-reference.json` | 11b726a05ef5e0ff5b6d6a01d4eb59abc51a48b516c785cf35151fc9e0e6358d |

**P-joint's genomes:**
- **The populations:** its 8 final populations (index 299) and its 8 snapshots at index 124, local.
- **The check:** they are checked against `train-tf.json`'s recorded hashes (all 256 + 256).
- **On a mismatch:** the `champions` stage refuses to start. It is not repaired, and no substitute is used.

**The engine:** E3b-1's T-F cohort trained at f881308. `g-e` (§5) reruns E3b-1's three legs at E3c's formal
commit: the GPU hashes, the CPU equivalence and the maze reference.

## 3. The arms

| Arm | Mask | Start | Mutates | Factor | Runs |
|---|---|---|---|---|---|
| **P-fixed** | E | the seed E + W2 | nothing | — | — |
| **P-sel** | E | E's modules frozen; the 13 selector parameters drawn by `samplers.ga_draw` | the selector's 13 | 1.0 | 4 |
| **P-joint** | E | the seed | E's 65 | 0.25 | 8, **reused:** E3b-1's T-F cohort |
| **S-mod** | E | B-task's draw projected onto E's mask (`assembly.draw`) | E's 65 | 1.0 | 8 |
| **S-dense** | B-task's full mask | B-task's draw (`assembly.draw`) | 171 | 1.0 | 8 |
| **R-shared** (reference) | E3a's `b_shared` plus W2 | engineered | nothing | — | — |
| **W2-turn** (reference, post-pilot) | W2 alone with a constant resting turn | a grid, one chosen on validation | nothing | — | — |

**The schedule:** every trained arm runs T-F's schedule, 300 generations × 8 mazes per genome. Equal training
evaluations is the matching unit.

**The seeds:**
- **The run seeds:** 1 300 000 + run. S-mod's runs are 0-7, S-dense's 10-17, P-sel's 20-23.
- **The draws:** `default_rng([run seed, 0xE3C])`, as in the pilot.
- **The training ids:** base 40 000 000, span 10 000 000. They are disjoint from E3b-1's (10-20 M) and the
  pilot's (30-40 M).

**The frozen sets** are as in the pilot (`assembly.arm_scales`). They are checked bitwise against each run's
draw, in every saved population (D201).

**The mutation factor stays 1.0.** The pilot permitted changing it (design §5); the from-scratch arms learned at
1.0.

**W2-turn** (post-pilot):
- **The grid:** resting turns −0.8, −0.4, 0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.2, 1.4.
- **The choice:** the best mean visits on the validation block. Ties go to the smaller |turn|, then to the
  earlier grid position.
- **The test:** the chosen turn is played on the test block.

## 4. The maze blocks and ids (new, and disjoint from every earlier block)

| Block | Ids | Use |
|---|---|---|
| Validation | 10 000-10 127 (128) | champion selection; the W2-turn choice |
| Learning curve | 10 200-10 327 (128) | the checkpoints; P-joint's two points |
| Test | 10 400-10 655 (256) | every reading |
| Benchmark | 10 700-10 955 (256); training ids 50 000 000-50 099 999 | `project`'s timings only |
| Training | 40 000 000-49 999 999 | the new arms' training mazes |

**The check:** every id, including every training id the schedule will draw, is pre-flighted by `walls_for`
before training. Redraws are recorded (Amendment 1's rule).

**Unused by E3c:**
- the earlier blocks: E3b-0's, E3b-1's, E3b-2's, the pilot's 7 600-7 727 and the smokes';
- the audit ids 9 900-9 902.

## 5. The stages, in order

**The frame:** every stage runs on E2's frame (`scripts/e3c.py`). Each has:
- a start marker carrying the formal commit;
- the once-only rule, and one rerun with a stated reason;
- a partial record each minute;
- a salvage record if it stops.

**Batch compositions** are given as (strains per chunk, worlds per strain, weys per world). The single-strain
padding is on (`pad_single_strain`).

1. **`project`:** the benchmark, on the benchmark ids only.
   - **What it times:** one generation of each training composition, a checkpoint chunk, a champions chunk and
     an evaluation chunk.
   - **What it decides:** it projects the formal total and applies §10's admission rule.
2. **`g-e`:** E3b-1's three legs at E3c's formal commit. It is read on the tested platform (Windows, the
   RTX 5080). Off that platform, the CPU leg's bitwise reference is not expected to match (rule 6; D202).
   - **No training stage starts unless `g-e` completed and passed** (E3b-1's rule; Fable).
   - **Any mismatch stops E3c.** The owner is asked. P-joint's reuse, trained at f881308, would then need an
     amendment before anything else runs.
3. **`train-s`:** S-mod and S-dense, as two batches.
   - **Each batch:** [256, 8, 8], that is 8 runs × 32 strains. Under the last cut, [192, 8, 8].
   - **The checkpoints** (post-pilot, denser early): 21 per run, at generations 0, 5, …, 50, then 75, 100, …,
     275, and 299.
   - **Each checkpoint:** each run's generation-best by training fitness is played on the learning-curve block,
     in chunks of [8, 128, 8] ([6, 128, 8] under the cut).
   - **Saved locally:** every run's final population and checkpoint candidates, with their hashes in the
     record.
4. **`train-psel`:** P-sel, [128, 8, 8], with the same checkpoints ([4, 128, 8]) and the same saving. Under the
   cut, [64, 8, 8] and [2, 128, 8].
5. **`champions`:**
   - **Each run's final population** is played on the validation block, as one chunk of [32, 128, 8] per run.
     P-joint's populations are checked first (§2).
   - **W2-turn:** the grid is played as [10, 128, 8].
   - **P-joint's learning-curve points:** at index 124 and 299, the population's generation-best by training
     fitness. That is the genome whose hash is `train-tf.json`'s logged `best_sha256` for that generation, as
     for the new arms. Each is played on the learning-curve block, [8, 128, 8].
   - **The learning-curve references:** W2 alone and P-fixed are played on the learning-curve block, [1, 128, 8]
     each (Astra). They are the cost curve's thresholds.
6. **`evaluate`:** every champion, P-fixed, W2 alone, the chosen W2-turn and R-shared, on the test block under
   shared trails.
   - **Chunks:** each arm's champions are one chunk, [runs, 256, 8]. Each reference is [1, 256, 8].
   - **The noses-removed condition:** every champion and P-fixed again, with each wey's cell path recorded in
     both conditions.
   - **The secondary condition, trails off:** every champion, P-fixed and W2 alone, intact only, on the test
     block, in the same chunks. It is the first cut (§10).
7. **`report`:** the readings of §7, computed from the records by one function.

**Eligibility after interruption:**
- **A run counts** for the primary readings only if it completed all 300 generations and its champion was played
  intact on every validation and test maze. No shorter run enters a reading.
- **For §7.3** a champion also needs its complete noses-removed play and its paths. Without them it is
  "undefined" there, and it still counts for the primary readings.
- **A missing checkpoint record** makes that run's cost-curve entry undefined. It is reported, and is neither a
  success nor a censoring.
- **Below the minimum:**
  - if fewer than 6 runs of an S arm count, the contrasts using that arm are "not read: too few runs";
  - if fewer than 6 of P-joint's count, Q2 is not read;
  - P-sel is described with whatever runs count.
- **A stopped stage** is rerun once, as a whole, under the frame's rerun rule, with the same batch membership.
  Mazes are never dropped from a reading.

## 6. Champions

**The rule, the same for every trained arm:**
- **The candidates:** the 32 genomes of the run's final population (index 299).
- **The champion:** the genome with the best mean visits per wey on the validation block, ties to the lower
  index.
- **P-joint's champions** are reselected by this rule on E3c's block. The new champion is used, never a choice
  between E3b-1's and E3c's.

**Saved and published:**
- **Saved locally:** every champion's genome.
- **Published:** every champion's grafted parameters by name (design §3, reaffirmed; D200), so that an
  outsider can rebuild each champion.

## 7. The readings

### 7.1 The unit and the primary contrasts

**The unit:** d = (the champion's mean visits per wey on the 256 test mazes − P-fixed's) / P-fixed's mean.
- **P-fixed's mean** must be finite and positive. Otherwise both contrasts read "not read: P-fixed's mean is not
  positive".
- **The run** is the independent unit.
- **Inference** is conditional on the test block.

**The contrasts** (`wormwars/e3/e3c_stats.py`, tested):
- Q1 = mean d (S-mod) − mean d (S-dense);
- Q2 = mean d (P-joint) − mean d (S-mod).

**The confirmatory decision** (post-review, D208): an exact two-sided permutation test per contrast
(`e3c_stats.permutation_p`).
- **The statistic:** the absolute difference in mean d, compared over every split of the pooled runs.
  - **The p-value:** the share of splits whose absolute difference is at least the observed one (ties
    included).
  - **The number of splits:** 12 870 for 8 runs against 8. Under the cut, 3 003 for 6 against 8 (Q2) and 924
    for 6 against 6 (Q1).
- **The level:** each contrast is tested at 0.025 (Bonferroni over the two).
- **Its null:** the two arms' runs are exchangeable, that is drawn from one distribution. Under that null its
  finite-sample type I error is at most 0.025, whatever the failure rates.
- **Its labels:**
  - "distributions differ (exact test); observed mean higher for X": rejected. The direction describes the
    sample only. It is not a calibrated claim about population means or about stochastic ordering;
  - "no difference detected (exact)": not rejected. It does not establish identical distributions.
- **What the test does not claim:** a difference in means.
- **For Q2, the null is expected to be false before any data, on spread alone** (Fable).
  - **Why:** under §8's model, P-joint's runs spread about 15 times more than S-mod's.
  - **What a Q2 rejection therefore carries:** no 0.025 guarantee about means. In the simulation it rejects at
    equal means in 0.02-0.055 of trials without failed runs (0.042 in the base case), and in up to 0.18 when
    S-mod has failed runs (0.05-0.18).
  - **For Q2,** the exact test is read as "the arms' outcomes differ". Any reading about means rests on the
    approximate margin label.

**The margin labels,** approximate (model-based) (post-review; both reviewers; the owner's dual margin):
- **The interval:** each contrast has a two-sided Welch interval at 97.5%, that is 1 − 0.05 / 2.
- **Every margin label** comes from that interval and is prefixed "approximate (model-based): ".
  - They are calibrated only under the no-failure model of `power.json` (§8).
  - Draft 2's attempt to make them confirmatory when no failure is observed is withdrawn: an observed absence
    of failures cannot confer that status (Astra).
- **Holm's adjusted p-values** are reported beside, never as labels.
- **Q1's floor guard:** Q1 is "not read: both at the floor" unless at least one S arm's mean test visits exceed
  W2 alone + 1. Neither its exact test nor its margin label is then read. It enters Holm with p = 1.

**The practical margin** (post-pilot; the owner's choice, keeping both reviewers' proposals):
- **The two margins:**
  - 0.10 of P-fixed's mean (Fable; E3b-1's "at least 10%");
  - 0.5 visits per wey (Astra), that is 0.5 / P-fixed's mean in d.
- **How they combine:**
  - m_lo is the smaller of the two, m_hi the larger;
  - "beyond the margin" needs the interval to clear m_hi, strictly;
  - "no relevant difference" needs it strictly inside ±m_lo.
- **What it means:** both margins must agree before a difference is called relevant, or negligible.

**The labels** (Q1: "modular" / "dense"; Q2: "engineered initialization and tuning" / "from scratch"):

| The 97.5% interval | Label |
|---|---|
| excludes 0, and clears m_hi on X's side | "X better, beyond the margin" |
| excludes 0, and lies inside m_lo on X's side | "X better, within the margin" |
| excludes 0, otherwise | "X better, margin unresolved" |
| includes 0, and lies inside ±m_lo | "no relevant difference" |
| includes 0, otherwise | "unclear" |

**Failed runs** (post-review; Fable's count):
- **A failed run** is one whose champion's mean test visits are not above W2 alone + 1. The counts are reported
  with every label.
- **The decomposition, beside each contrast** (descriptive):
  - the failed-run counts compared by Fisher's exact test;
  - Welch's two-sided 95% interval among the runs that did not fail. It is "not computed" when an arm has fewer
    than 2 such runs.
- **What the counts cannot show:**
  - failures absent from the sample;
  - failures above the line. In the simulation, about 8% of failure draws from N(2.3, 0.3²) lie above
    W2 alone + 1;
  - partial or bimodal outcomes above the floor, such as a champion stuck near 4-5 visits. These are neither
    detected nor simulated.

**The supplements:**
- a two-sided Mann-Whitney U test per contrast, unadjusted, never a label;
- a maze-paired percentile bootstrap of each contrast. It resamples the 256 test mazes with replacement,
  10 000 times, seed 20 261 007. On every resample, P-fixed's mean and each run's d are recomputed. Its 95%
  interval is the 2.5th and 97.5th percentiles.

**The expectations, registered:**
- **Q2:** the design registered "engineered initialization better" (§1, v2.1). That sentence stands.
  - **Annotation (post-pilot):** the direction is now uncertain. On different blocks, the S arms' gain over the
    seed (+0.38 in d) and T-F's (+0.381) were alike.
  - **What follows, under the assumed scenarios** (§8): if the true difference is within about half a visit, the
    exact test most likely reads "no difference detected" and the margin label "unclear".
- **Q1:** if no run fails and the S arms vary as little as in the pilot, "no relevant difference" (approximate) is
  expected (post-pilot). The two S arms differed by about 0.08 visits per wey in the pilot.
  - **Why the exact test may still reject:** the runs barely vary, so the test can detect a difference that
    small.
  - **How that pair reads:** "the arms' outcomes differ (exact); the mean difference is within the smaller
    margin (approximate)".

### 7.2 The cost curve (secondary)

**What it measures:** each new run's generations to threshold. That is the first learning-curve checkpoint
whose generation-best exceeds:
- W2 alone + 1;
- P-fixed's level, both measured on the learning-curve block.

**The checkpoints** are denser early (post-pilot). In the pilot, both S arms passed both thresholds before
generation 25.

**The rules:**
- A threshold is right-censored at 299.
- A run reaching it at 299 is a success; one not reaching it is censored.

**Per arm:**
- the number of runs reaching each threshold, with Fisher's exact test of S-mod against S-dense, and Holm
  over the two thresholds;
- the median generation, with censored runs as +∞ (`e3c_stats.censored_median`):
  - "not reached" when the median touches a censored run, that is when half or fewer reach it;
  - "no runs" when an arm has no eligible run.

### 7.3 Nose dependence and the coverage hypothesis (secondary; post-pilot; descriptive classifications)

**"Noses removed":**
- **What it does:** the four A/B nose channels at gain 0.
- **What stays on:** the relays' source-occupancy inputs and W2's collision sensing.
- **What it can show:** a small loss means the intervention is tolerable. It does not show that the intact
  controller ignores its noses (Astra).

**Per champion,** and for P-fixed, on the test block:
- **The intact and noses-removed visits,** with their maze-level differences, all published.
- **The retained fraction** r = noses-removed visits / intact visits.
  - **Its class:** r ≥ 0.9 "nose-independent", r ≤ 0.5 "nose-dependent", otherwise "partial"
    (`e3c_stats.nose_class`).
  - **Undefined:** when intact visits are 0 or a record is missing, the class is "undefined", never another
    class.
- **The path measures,** intact:
  - the coverage of the 25 cells, averaged over weys and mazes;
  - the tour match: directed moves at lag 48, averaged over weys with more than 48 moves;
  - the best lag over 44-52, beside it;
  - a champion with no eligible wey has an undefined tour match.
- **"Coverer"** (D205's criterion): r ≥ 0.9, coverage ≥ 0.95 and tour match ≥ 0.5. It is undefined when any of
  the three is undefined.

**Per arm:**
- **Nose classes and coverers,** counted separately.
- **The paired loss** L, per run: the mean over test mazes of (intact − noses removed) visits.
  - **The arm's interval:** a two-sided 95% t-interval for its mean L over runs.
  - **P-fixed** has no runs. It gets the maze-paired percentile bootstrap of its L instead (10 000 resamples,
    seed 20 261 008).
  - **"No material loss":** the interval's upper end is below m_lo in visits.

**The coverage hypothesis** (`e3c_stats.coverage_rule`; proportions, so the cut to 6 runs keeps the rule):
- **"supported":** each S arm's coverer share is ≥ 0.75, and P-joint's share is below both S arms' shares;
- **"not supported":** both S arms' shares are ≤ 0.25;
- **"mixed":** anything else, by this precedence:
  1. any arm, P-joint included, with an undefined champion: "mixed" (Astra; D208-D209);
  2. otherwise, both S arms low: "not supported", whatever P-joint's share;
  3. otherwise, both S arms high and P-joint lower than both: "supported";
  4. otherwise "mixed". That includes S arms high with P-joint's share equal to or above an S arm's.
- **Shares** are over defined champions.
- **Reported apart** (`e3c_stats.coverage_rule`):
  - the S arms' part, from the S arms alone: "high", "low", "mixed", or "undefined" if an S champion is;
  - whether P-joint is lower than both, or undefined when any champion of the three arms is.

**Nose dependence,** directly (descriptive):
- P-joint's mean r against each S arm's, as Welch differences with two-sided 95% intervals;
- P-fixed's r beside them.

**The qualifier:** the arms' nose-class and coverer counts are appended to Q1's and Q2's labels, both shown.
They never change a label.

### 7.4 Descriptive

- **P-sel:**
  - the runs whose champion exceeds W2 alone + 1, a selector-only training outcome above the floor. E3a had
    1 of 8; the pilot 1 of 3;
  - each run against P-fixed and P-joint.
- **R-shared and W2-turn** against P-fixed and W2 alone, with W2-turn's coverage and tour match.
- **The learning curves,** with P-joint's two points (§5).
- **The secondary outcomes,** as in E3b-2: the later-leg rate, and the unvisited and round-trip shares.
- **Per champion:**
  - the Spearman correlation of its per-maze test visits with P-fixed's, and with the A-B tree distance
    (Fable);
  - its resting turn offset and module A's K_D at q = 0.
- **Trails off,** if not cut.
- **Declined:** Fable's analytic coverage ceiling (about 8.7 visits per wey). Its derivation has not been
  checked, so it is not used as a reference.

## 8. Power (`power.json`, `scripts/e3c_power.py`; regenerated for draft 3, D208)

**The simulation:**
- 376 scenarios, 5 000 trials each, seed 20 261 009, with Monte Carlo standard errors.
- **The decisions are vectorized.** On every run, 15 040 trials are checked against the registered `readings`,
  label for label, for both the exact and the margin labels. All match.
- **The scenarios are centred on the true arm means,** and each stores its analytic means.
- **The S arms:**
  - S-mod's successes at 6.7 visits per wey. S-dense's successful component is placed so that its mixture has
    the scenario's mean;
  - spread 0.06 (0.4 as a sensitivity case);
  - failures at N(2.3, 0.3²), or N(1.8, 0.2²).
- **P-joint:**
  - T-F's spread (d SD 0.177), times 1, 0.75 or 1.5;
  - normal, or T-F's 8-atom empirical shape, an anti-conservative sensitivity case;
  - always 8 runs.
- **P-fixed's test mean:** 5.0, with 4.82 and 5.84 as sensitivity cases.

**The exact test** (the confirmatory decision):
- **Its false rejections** where Q1's two distributions are identical (equal means and failure rates; 93
  scenarios): 0.019-0.031. That is consistent with the exact 0.025, given a Monte Carlo SE of about 0.002 and
  the maximum of 93.
- **At equal means but different spreads** (Q2 at a true difference of 0: P-joint's spread is about 15 times
  the S arms'), it rejects in 0.02-0.055 over the 24 no-failure scenarios (0.042 in the base case). When S-mod
  has failed runs, 0.05-0.18.
  - The arms' distributions then differ, so "distributions differ" is not false; a claim about means would be.
  - For the same reason, Q2's exact power below is not comparable with Welch's at equal false-rejection rates.
- **Its power** (8 S runs, no failures):
  - Q1 at 0.5 visit: 1.00. With 6 S runs: 1.00;
  - Q2 at ±0.5 visit: 0.27;
  - Q2 at ±1 visit:

    | Condition | Power |
    |---|---|
    | base | 0.76 |
    | 6 S runs | 0.61-0.62 |
    | P-joint's spread × 0.75 | 0.94 |
    | P-joint's spread × 1.5 | 0.42-0.43 |
    | T-F's empirical shape | 0.66 (+1) and 0.82 (−1) |
    | P-fixed's test mean 4.82 | 0.79-0.80 |
    | P-fixed's test mean 5.84 | 0.63-0.64 |
    | S spread 0.4 | 0.67-0.68 |
- **With failures:**
  - Q1 at a true 1 visit: 0.34 (both S arms failing at 1/8) and 0.14 (at 1/4);
  - with unequal failure rates at equal means, it rejects in 0.33-0.34 with 8 S runs, and 0.44-0.45 with 6:
    correctly, since the distributions differ;
  - its largest "wrong direction" rate, 0.108, comes from such a case: the failing arm's successful runs
    out-score the other arm while its mean is lower. "X higher" describes the sample, as the label says.

**The margin labels** (approximate):
- **Without failures, in the base scenarios:** the joint rate of any false label assertion over both contrasts,
  counting a false "beyond", "within" or "no relevant difference" as well as a wrong direction (Astra), is at
  most 0.049. The joint coverage of the two 97.5% intervals is 0.948-0.959.
- **Under T-F's empirical shape** they are at worst 0.066 and 0.934: the 8-atom artifact.
- **With failures:** up to 0.47, and coverage down to 0.52 (6 S runs, S-dense failing at 1/8). This is why they
  are labelled approximate.
- **Base examples** (8 S runs, no failures):

  | True Q1, Q2 (visits) | Q1's margin label | Q2's Welch rejection | Any false label assertion |
  |---|---|---|---|
  | 0, 0 | "no relevant difference" 0.98 | 0.02 | 0.048 |
  | 0.5, 0 | rejected 1.00 (the truth sits at m_hi) | 0.03 | 0.049 |
  | 0, 1 | "no relevant difference" 0.98 | 0.64 | 0.024 |
  | 1, 1 | "beyond the margin" 1.00 | 0.65 | 0.000 |

**What follows:**
- **Q1, margin label:** decisive only if no run fails **and** the S arms vary as little as in the pilot (spread
  0.06).
  - At spread 0.4 without failures, it reads "unclear" in 0.82 of trials at a true difference of 0, and "no
    relevant difference" in 0.15 (Astra).
  - The absence of observed failures is not evidence of the no-failure model.
- **Q1, exact test:** it detects a 0.5-visit difference with power 1.00 at spread 0.06, with 8 or 6 runs. It
  answers "do the outcomes differ", not "is the difference relevant".
- **Q2** needs a true difference near a visit or more for a likely detection, by either decision.
- **With failures,** Q1's margin label is mostly uninformative, and the exact test answers the narrower question
  of whether the distributions differ.

**The pilot's failures:**
- the pilot saw 0 failures in 6 S runs;
- **pooled** over both S arms (a common rate), that bounds the rate below about 0.39 (one-sided 95%);
- **per arm,** with 3 runs each, the bound is 0.63;
- both concern the pilot's 99-generation endpoint, not the formal one (Astra).

**P-sel** (descriptive): the chance that none of its 4 runs ends above the floor is 0.59 at E3a's rate (1/8),
and 0.20 at the pilot's (1/3).

**Not simulated** (named as limits; Astra):
- separate spreads for S-mod and S-dense;
- the uncertainty of the 300-generation endpoint;
- partial failures above the floor.

## 9. The benchmark (`project`)

**What it times,** on the benchmark ids:
- one generation of each training composition, uncut and cut: [256, 8, 8] and [192, 8, 8] for the S arms,
  [128, 8, 8] and [64, 8, 8] for P-sel;
- a checkpoint chunk and a champions chunk on the first 128 benchmark mazes (10 700-10 827), as in their formal
  compositions;
- an evaluation chunk on all 256 (no id repeated).

**The projection:** the formal total, with × 1.25 on training, checked against §10 before any training.

## 10. The cap, admission and cuts

**The ceiling:** 30 GPU-hours for all of E3c (D198).
- It is a running total over every compute record, and is what the cap clock reads.
- So far 3.946 hours: the pilot 2.82, the replay 1.10, the seed diagnostic 0.03 (charged in the record, D207).

**The projected formal total,** from E3b-1's and the pilot's measured rates:

| Part | GPU-hours |
|---|---|
| `project`, `g-e` | about 1.5 |
| S-mod, S-dense (8 × 300 × 8 each) | 2 × 6.44 = 12.9 |
| P-sel (4 × 300 × 8) | about 3.6 |
| The checkpoints (21 per run; T-F had none) | about 0.6-0.9 |
| Champions (28 runs × 32 × 128) and W2-turn | about 1.0 |
| Evaluation (both conditions, with paths) | about 1.5 |
| **Formal total** | **about 21.4**; 25.5 with × 1.25 on training |
| **With the 3.95 spent** | **about 25.3**; 29.4 with × 1.25 |

**The admission rule:** if `project`'s projection exceeds the remaining budget, the cuts apply in order until it
fits:
1. the trails-off condition;
2. P-sel to runs 20-21;
3. S-mod to runs 0-5 and S-dense to runs 10-15.

If it still does not fit, E3c's formal run does not start, and the owner is asked.

**What is kept:** the primary contrasts, the noses-removed reading and the path measures are kept whole as long
as possible.

**The stop:** every stage checks the cap before each rollout. A stage stopped by the cap records what it
finished. The eligibility rule of §5 then decides what is read.

## 11. The cost ledger (descriptive; the design's §7, restored)

| Line | GPU-hours | What it bought |
|---|---|---|
| E4s-0 | 0.23 | L1's calibration and diagnostics |
| E4s-1 | 16.6 | L1's confirmatory validation |
| E3a | 5.97 | the selector, E and its gates |
| E3b-0 | 2.62 | W2, the maze-ready additions and the task |
| E3b-1's T-F | 6.44 | P-joint's tuning |
| E3c's pilot, replay and diagnostic | 3.95 | the branch, and the coverage finding |
| E3c's new arms | measured | S-mod, S-dense, P-sel |

**How it is kept:**
- **The categories,** separately: measured artifact production and selection; shared infrastructure; the
  downstream adaptation and validation; and unmeasured design and review effort. No hours are invented for the
  last.
- **P-joint's first-use cost** is a range: from 6.7 hours (T-F plus E4s-0) to 31.9 hours (the full lineage, T-F
  included).
- **Common costs:** S-mod inherits E's mask, and every arm inherits W2 and the interface. These costs are common
  and noted as such.
- **E3c's incremental cost** is reported apart from the historical first-use cost.
- **The reuse cost** is the library cost paid once plus each downstream adaptation (P-sel here). It is shown as
  scenarios, not as a measured saving.

## 12. Tests before the formal run

Each test is seen failing first. Where a check could not otherwise fail, it gets a sabotage test.

**Already written:**
- **The arms:** masks, frozen sets and draws (`tests/test_e3c_assembly.py`).
- **The statistics** (`tests/test_e3c_stats.py`):
  - the exact permutation test, against a direct enumeration;
  - Welch;
  - the fixed 97.5% intervals and Holm beside them;
  - the dual margin with strict boundaries;
  - the labels;
  - the floor guard;
  - the failed-run counts and the decomposition;
  - the coverage rule, with undefined champions in any arm;
  - the censored median and the "no runs" case.
- **The power simulation** (`tests/test_e3c_power.py`):
  - centred mixtures, and the analytic means;
  - the false-assertion counter. It was written beside its code, so it has a sabotage check: draft 2's
    narrower counter fails it;
  - the vectorized exact test against the registered one;
  - the check against the registered readings, sabotaged.

**To be written** with the formal stages:
- the blocks' disjointness and the pre-flight of every id;
- the stage order, the once-only rule and the rerun;
- the salvage, and the eligibility rule;
- a CPU smoke of every stage;
- P-joint's hash check, sabotaged: one changed byte must refuse;
- the champion rule's ties;
- the W2-turn choice, on the validation block only, with its ties;
- P-joint's learning-curve genomes found by their logged hashes;
- the noses-removed condition and the path measures (as for the replay, D205);
- the report function on synthetic records, for every label;
- the cut plans: their run ids and compositions;
- **the engine freeze** (Fable): every formal stage's start marker records the diff from the binding commit
  under `wormwars/`, `configs/` and `requirements.txt`. The stage refuses unless it lists only added files, or
  files named in an amendment.

## 13. Post-pilot and post-review departures from design v2.1

**After the pilot:**
1. **The question's wording is narrowed** (§1). E3c does not compare assemblies of stereo navigators. D206.
2. **The coverage hypothesis and the nose-dependence reading are registered,** as descriptive classifications
   (§7.3). D205's consequence for "coverage"; both reviewers.
3. **The noses-removed reading** gets Astra's paired loss and its "no material loss" bound (§7.3).
4. **The W2-turn reference is added** (§3; Fable).
5. **The practical margin is dual** (§7.1). The owner's choice.
6. **The Mann-Whitney supplement** (Fable).
7. **Q2's expectation is annotated, and Q1's is added** (§7.1). Both reviewers.
8. **The early checkpoints are denser** (§5; Fable).
9. **New run seeds, training ids and benchmark ids** (§3, §4).
10. **`share_above_w2` is dropped** (Fable).
11. **New descriptives:** each champion's Spearman correlations, resting turn and K_D (§7.4; Fable).
12. **The cuts' first item:** the design's "the evaluation's secondary conditions" becomes trails off only. The
    noses-removed condition is kept.

**After the review of draft 1** (D207):

13. **The intervals:** fixed 97.5% (Bonferroni) for both contrasts, replacing draft 1's Holm-level intervals
    (Astra).
14. **The failed-run rule** and the decomposition (Fable's count; Astra's fallback).
15. **The coverage rule** by proportions, its parts reported apart, and its undefined cases (both).
16. **The binding sequence, the execution contract and the eligibility rule** (§0, §5; both).
17. **The cost ledger is restored** (§11; Astra).
18. **Two more files are pinned,** and P-joint's hash-check failure refuses (§2; Fable).

**After the review of draft 2** (D208):

19. **The confirmatory decision is the exact permutation test** (§7.1). Every Welch margin label is approximate
    (model-based) (Astra; Fable concurring in substance, D208).
20. **The `g-e` gate before training** (§5; Fable).
21. **The undefined case of the coverage rule** in any arm (§7.3; both).
22. **The execution details:**
    - the cut compositions and the 256-maze benchmark block;
    - the learning-curve references;
    - eligibility per reading, and whole-stage reruns;
    - the trails-off scope and the missing-checkpoint rule;
    - 21 checkpoints (§4, §5, §9, §10; both).
23. **The engine-freeze check** in the start markers (§12; Fable).

**Reaffirmed, not departures:** publication of the champions' grafted parameters by name (design §3, D200).

## 14. Amendments

None yet.

## 15. Changes from draft 1 (the reviews, D207)

**Both reviewers said "revise".**

> **Correction (2026-10-05, after the review of draft 2; rule 4).** The next sentence said "Every required change
> is taken". Astra showed that overstated it:
> - the calibration fallback had been applied as "confirmatory unless a failure is observed", which is not what
>   Astra proposed;
> - the coverage rule's undefined case was incomplete for P-joint.
>
> Both are fixed in draft 3 (§16).

Every required change is taken:
- **The binding sequence** (§0; both).
- **The power analysis, corrected and regenerated** (§8; both):
  - centred mixtures;
  - P-joint kept at 8 under the cut;
  - unequal failure rates, Q1 in both directions, P-joint's spread varied;
  - joint error rates and Monte Carlo standard errors;
  - §8's figures, recomputed from `power.json`.
- **The intervals** (§7.1; Astra).
- **The mixture calibration** (§7.1, §8). Fable held that disclosure suffices; Astra that it does not.
  - **What is taken:** the failed-run rule makes such contrasts "approximate", with the decomposition beside
    them, and the limit for unobserved failures is stated in advance.
  - **No procedure was tuned to the pilot.**
- **The coverage rule and nose dependence** (§7.3; both).
- **The secondary statistics defined:** L's interval, the bootstraps, the censored median, P-joint's
  learning-curve genomes (§5, §7; both).
- **The execution contract:**
  - the benchmark ids, the compositions, the cut run ids, the admission and eligibility rules (§4, §5, §10;
    Astra);
  - the diagnostic charged in the compute record (§10; Astra).
- **§13's inventory completed; the cost ledger restored** (§11, §13; both).
- **The wording:**
  - the replayed S-dense champions named;
  - "nose-independent";
  - Q2's label names the recipe;
  - P-sel's outcome described as selector-only training;
  - "no relevant difference" stated as the one equivalence claim;
  - 99.9-100.6%;
  - the pilot block named;
  - the analytic ceiling declined (§1, §7; both).

## 16. Changes from draft 2 (the reviews, D208)

**Both reviewers said "revise":** Fable narrowly (three items), Astra on the calibration and the execution
details. Taken:
- **The confirmatory status** (§7.1; Astra's required change 1).
  - **The exact permutation test** gives the confirmatory decision. Its null is distributional, so its level
    needs no assumption about failures.
  - **Every Welch margin label** is approximate (model-based).
  - Draft 2's "confirmatory unless a failure is observed" is withdrawn.
- **The power audit** (§8; Astra):
  - the joint counter now counts every false label assertion;
  - the joint interval coverage is recorded;
  - the analytic means are stored;
  - the counters are tested;
  - the component-mean wording and the pilot's failure bound are corrected.
- **The coverage rule** (§7.3; both): an undefined champion in any arm gives "mixed"; numpy booleans count; the
  "mostly coverers" sentence is corrected.
- **The `g-e` gate** (§5; Fable).
- **The limits of the failed-run counts** (§7.1; Fable): failures above the line, and partial outcomes.
- **The execution and secondary statistics** (§5, §7, §9; Astra):
  - the cut compositions;
  - the benchmark construction;
  - the learning-curve references;
  - eligibility per reading;
  - whole-stage reruns;
  - the trails-off scope;
  - the bootstrap level;
  - the decomposition's and P-sel's no-data cases;
  - 21 checkpoints.
- **The wording:**
  - the two bounded-equivalence statements (§1; both);
  - §15's completion claim, corrected beside it (rule 4; Astra);
  - the exact label says "distributions differ", since the test can reject at equal means when the spreads
    differ (§8).

## 17. Changes from draft 3 (the reviews, D209)

**Both reviewers said "revise, narrowly".** Taken:
- **Q2's exact test, disclosed** (§7.1, §8; Fable):
  - its null is expected to be false on spread alone, so a rejection carries no guarantee about means;
  - the equal-means rejection rates are given from `power.json`: 0.02-0.055 without failures, up to 0.18 with
    them. Fable's examples were 0.04-0.05 and 0.09-0.10; the full ranges are wider;
  - its power is not comparable with Welch's.
- **The exact label** names the direction as the observed mean: "distributions differ (exact test); observed mean
  higher for X" (both).
- **The coverage rule's components** (§7.3; Astra):
  - the S-arm part comes from the S arms alone;
  - the P-joint comparison is undefined when any champion is;
  - shares are over defined champions;
  - the precedence is stated. Tests assert the components.
- **§8's Q1 conclusion is qualified:** no failures and narrow spread; the exact and margin readings are
  distinguished (Astra).
- **Smaller fixes:**
  - the 6-run figures (Fable);
  - "not read" for a non-positive P-fixed mean (Fable);
  - P-fixed's mean recomputed in the bootstrap (Fable);
  - the split counts (Fable);
  - the Q1 sentence template (Fable);
  - the 128-maze benchmark subsets (Astra);
  - "at most 0.025 under exchangeability" (Astra);
  - the module docstring (Fable).
