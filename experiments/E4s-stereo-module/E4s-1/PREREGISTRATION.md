# E4s-1 pre-registration: the comparator graft under evolution

Status: **final draft**, 2026-10-01.
- **Its reviews:** the first draft (commit 808e25f) was reviewed by Astra 6 and Fable 5.1, and both
  said "bind after fixes" (`docs/reviews/20261001-E4s-1-prereg/`). This text takes every fix they
  listed (D150).
- **Binding:** it binds when committed and pushed, before any stage of E4s-1 runs (rule 2). From then
  on the text is never changed; amendments go in §13, dated.
- **Its design:** `docs/E4s/E4s-1-DESIGN.md` v2 (D148, D149). The departures from it are listed in
  §12.

## 1. The question and its frame

E4s-0's 4-neuron comparator, L1, steers by the left-right difference on its carrier. Grafted onto
random N2 brains, each simulated starting population's best brain used it. When the whole brain then
evolves on Task N under 02's GA:
- **O1:** does an arm evolved with the graft's output end with a better final brain than the
  separately evolved arm with that output cut (M − N)? This compares two evolved arms, not one final
  brain ablated.
- **O1b:** do the graft's designed signs beat random signs on a graft of the same shape (M − R)?
- **O1c:** how much does each arm climb?
- **O2:** at the two endpoints, is the module used, is it still competent alone, and does the host
  steer by the difference itself?

**Frame, stated in every claim:**
- Stereo sensing is a game-design choice (the owner's option (a)).
- The stereo computation starts in a graft with its own noses and its own path to the motors,
  outside the N2 mask.
- Nothing here is about worm chemotaxis.

## 2. Fixed inputs

**The module:** `experiments/E4s-stereo-module/E4s-0/module.json`, with sha256
`9613cd155a20ed2cfb891c1bd10fed16814f24a04f912a1940524f2378e877d4` (of the file with LF line
endings).
- **L1:**
  - noses E4S_NL and E4S_NR (τ 0.5, bias 0);
  - comparators E4S_CL and E4S_CR (τ 0.5, bias 0);
  - 20 edges, each of magnitude exactly 3.0: 4 from the noses, 16 onto the turn neurons.
- **Its carrier:** forward command 1.0, turn command 0.2.
- **Registration:** implementation registers it in `wormwars.graft.MODULES` as `comparator-L1`, a
  required step, tested.

**L1 sits on the genome's bounds.** Its 20 weights are ±3.0 with `w_max` = 3.0, and its τ is 0.5
with `tau_min` = 0.5 (`ladder.json`: `on_bounds` w_n, w_o, tau). The same holds for R.
- Under mutation, the module's weights can only shrink in magnitude, and its τ can only grow.
- About half of each bounded parameter's proposals are clipped back.
- So a loss of use at F has two candidate readings: selection against the module, or one-sided drift
  from a boundary optimum. **F0 − M** (descriptive, 8 runs) is the comparison that addresses this.

**The source genomes** are listed by record, checkpoint and sha256 in
`experiments/E4s-stereo-module/E4s-1/development-records/source-genomes.json`.
- The list's sha256 (LF line endings) is
  `dbd09d0db196e8ff1170fcb8be42f18f795457f5554887b9df39bf263207e2c6`.
- It names 04a's 16 champions (`train-A.json`, `train-B.json`) and E2 GA's 8 champions
  (`train-ga.json`).
- Each is loaded by E2d's `e2_champions` or `e04a_champions`, which check `genome_hash` against the
  committed sha256.
- **C2's genome is 04a run 2,** sha256 `e8561228…` as listed there.

**Task N:** E1's frozen configuration (checked against E1's gate record); world seed 1 100 001
(`scripts/e2.py`).

**The GA:** 02's GA as E2 kept it (`evolve_batch`):
- population 32, 3 elites, truncation 8;
- 8 worlds per strain, 1 000 generations, validation checkpoints every 25 on 256 worlds;
- unshaped fitness;
- 02's mutation sigmas: w 0.08, g 0.04, log-τ 0.15, bias 0.05.

**E2d's rules, imported unchanged** from `scripts/e2d.py`:
- `world_ci`: a paired percentile bootstrap over worlds of the mean difference, two-sided 95%,
  10 000 resamples, seed 0;
- `classify`: "uses" if both lower bounds > 0.5; "no material benefit" if both intervals lie inside
  (−0.25, 0.25); else "unclear";
- `_boot_means`, for the run-level bootstrap (§6).

**The probe inputs:** L = m + d/2 and R = m − d/2, as E4s-0's attenuation probe. A turn command u is
the world's: the dorsal-minus-ventral mean of tanh, times 0.5 × `turn_gain`, clamped to [−1, 1].

## 3. The stages, in order (each writes a record committed and pushed before the next starts)

1. **Projection;**
2. **G1, re-qualification;**
3. **G2, the CUDA state tolerance;**
4. **G3, the score-level check;**
5. **R's draws, recorded;**
6. **training batches 1 to 10,** each its own stage;
7. **evaluation of the endpoints;**
8. **evaluation along training and of the final populations.**

**The projection** reads no scores.
- It runs on smoke ids (0-9 999) with seed base 1 169 000. Both lie outside every registered block.
- It records only timings, so nothing runs on E4s-1's registered worlds or seeds before the gates.
- It times one chunk of each actual shape, twice, using the second timing as E4s-0 did:
  - training 256 × 8;
  - validation 8 × 256;
  - single-genome evaluation 1 padded × 1 024;
  - probes 1 padded × 256, instrumented;
  - the open loop.

**G1, re-qualification.**
- **The run:** L1 on its carrier, worlds 942 800 000-942 801 023, one padded strain.
- **The test:** it passes if `world_ci`'s lower bound of the mean against 0 is at least 5.0, **and**
  `classify` gives "uses" (real against module mean, real against module swapped).
- **The chance of failing the score threshold by chance** (`power.json`): 0.9% if E4s-0's mean of
  5.18 is the truth (plug-in), and 4.7% allowing for that mean's error (predictive, a flat prior).
  This covers the score-threshold component only, under a fixed-standard-error normal model; it is
  not the whole gate's failure probability.

**G2, the CUDA state tolerance.**
- **The genomes, 48:** 32 random N2 (`initial_population` on N2, run seed 1 167 000), then 04a's 16
  champions, in that order.
- **The pair:** for each genome, the brain ungrafted and the brain with **N's construction** (L1
  grafted, its 16 output edges present in the mask at weight 0). Each runs in its own batch of the
  named shape, on CUDA, from a zero initial state.
- **The input history:**
  - `numpy.random.default_rng(1 168 000).uniform(0, 0.35, size=(300, S))`, where S is the number of
    interface signals, in `iface.signal_names` order;
  - drawn once and shared by every row, strain and shape;
  - injected each tick through the interface, so the module's noses receive the `food_left` and
    `food_right` values as routed.
- **The shapes and their coverage:**
  - training, 256 × 8: one batch, the 48 genomes tiled cyclically over the 256 strains;
  - validation, 8 × 256: six batches, genomes 0-7, 8-15 and so on to 40-47;
  - single-genome evaluation, 1 (padded) × 1 024: 48 runs, one per genome;
  - single-genome probes, 1 (padded) × 256: 48 runs, one per genome.
- **The test:** the maximum absolute difference in the 302 host neurons' states, over all ticks,
  rows and genomes, is at most 10⁻⁴.
- **The basis for 10⁻⁴:** declared in advance (rule 7). It is about 70 times the CPU rounding
  measured for an inert graft (1.4 × 10⁻⁶, D140), allowing for CUDA's reduction orders. It is not
  derived from behaviour.

**G3, the score-level check.**
- **The genomes, 24, all of which score:** 04a's 16 and E2 GA's 8 champions, from
  `source-genomes.json`.
- **The comparison:** each genome ungrafted against N's construction, each as one padded strain ×
  256 worlds (942 950 000-942 950 255).
- **The test:** each genome's two means lie within 0.05 of each other. That is about 13 worlds
  changing by one target, of 256.
- **Reported:** the share of worlds with identical counts, and every genome's two means.

**R's draws** (before training): `numpy.random.default_rng(1 165 000 + i).choice([-1, 1], size=20)`
for runs i = 0-15.
- Edge k's weight is **s_k × 3.0**, k in the order of `module.json`'s synapse list.
- No draw is rejected.
- One draw per run, shared by its 32 strains.
- The 16 sign vectors and their sha256 are recorded and committed before training batch 3.

**Gate failures and reruns:**
- **A gate that completes and fails its test is final.** E4s-1 stops, and the failure is reported.
- **The code and the environment may be checked.** Any re-gate is a dated, reviewed amendment, on
  fresh worlds. The module is never re-tuned within E4s-1.
- **A stage that did not complete because it stopped** (a crash, a kill, a non-finite score) may be
  rerun once, with a stated reason and unchanged seeds and inputs; a stopped rerun is final.
- **A stage stopped by the cap is not rerun** (as in E2).

## 4. Arms, masks, seeds, worlds

| Arm | Generation 0 | Module factor | Runs (i) | Role |
|---|---|---|---|---|
| **M** | L1 on random N2: `initial_population(N2 spec, run seed, 32)`, embedded by `graft.seeded_genome` | 0.25 | 16 (0-15) | main |
| **N** | M's genomes, with the 16 output edges at 0 and pinned (factor 0) throughout | 0.25 | 16, paired with M | confirmatory |
| **R** | M's genomes, with L1's 20 edges at s_k × 3.0 | 0.25 | 16, paired with M | confirmatory |
| F0 | as M | 0 | 8 (0-7), paired with M 0-7 | descriptive |
| U | as M | 1 | 8 (0-7), paired | descriptive |
| S | as M | 0.125 | 8 (0-7), paired | descriptive |
| C2 | L1 on 04a run 2: 32 identical copies | 0.25 | 8 (0-7) | descriptive |

**Seeds:**
- run i of M, N, R, F0, U and S uses run seed 1 160 000 + i. So the arms share the run's background,
  its training worlds (`train_ids`) and its breeding generator (`breed_seed`), which is deliberate;
- C2's runs use 1 166 000 + i.

**The mutation masks:** `arm_scales(ext, factor, pinned)`.
- Every host parameter is at 1 (02's sigmas).
- The module's parameters are at the arm's factor: its 4 neurons' τ and bias, and every edge with a
  module neuron at either end.
- N's 16 output edges are at 0; its nose edges mutate harmlessly.
- F0's module parameters are all at 0.
- A parameter at factor 0 never changes: its noise is 0 (τ is multiplied by exp(0) = 1), and
  clamping leaves an in-bounds value unchanged.
- Tests check every factor. Mutation counts per block (host, module, output edges) are logged per
  generation.

**End-of-run assertions:**
- N's 16 output edges are exactly 0 in every final genome;
- F0's module parameters are bit-identical to L1's in every final genome.

If one fails:
- that batch is "not read";
- E4s-1 stops for diagnosis, by amendment;
- if N's pin fails, O1 is not read.

**Run order:** ten batches of 8 runs, E2's composition:
1. M 0-7;
2. N 0-7;
3. R 0-7;
4. M 8-15;
5. N 8-15;
6. R 8-15;
7. F0;
8. U;
9. S;
10. C2.

**World ids:** a new block, disjoint from every earlier range (a test checks).

| Use | Ids |
|---|---|
| training | base 942 000 000, span 500 000 (`train_ids`) |
| validation | 942 600 000-942 600 255 |
| hold-out | 942 700 000-942 701 023 |
| G1 | 942 800 000-942 801 023 |
| along training | 942 900 000-942 900 255 |
| final populations | 942 910 000-942 910 255 |
| G0 population user count | 942 920 000-942 920 255 |
| G3 | 942 950 000-942 950 255 |

## 5. Measures

**The genomes, per run:**
- **F**, the final generation's best: the strain with the highest training fitness at generation 999,
  as logged; ties go to the lowest index. This is the registered reading.
- **C**, the champion: the first checkpoint with the highest validation mean. **C never changes an O1
  or O1b label.**
- **G0**, the generation-0 best: the checkpoint-0 candidate.

G0 and F are selected representatives. No history between them is claimed.

**The hold-out measures** (1 024 worlds; one padded strain per genome; recorded per world, with
compositions):

| # | Condition | Used for |
|---|---|---|
| 1 | real | score |
| 2 | module noses on mean, world real | D, H's baseline |
| 3 | module noses swapped, world real | D |
| 4 | module noses on mean, world on its mean probe | H |
| 5 | module noses on mean, world on its swapped probe | H |
| 6-8 | the module transplanted onto the carrier at turn +0.2: real, module mean, module swapped | Mc |
| 9-11 | the same at turn −0.2 | Mc |
| 12 | the module's 4 neurons silenced (`Brain.silence`) | the lesion cost, (1) − (12) |
| 13 | the module's parameters reset to the run's own generation-0 values (for R, its random signs) | reset |
| 14 | the module's parameters replaced by L1's | the L1 rescue, an intervention |

**Which measures apply where:**
- **N:** conditions 1, 2, 4 and 5 (its module has no output: D, Mc and the secondary measures are
  vacuous).
- **G0 genomes:** conditions 1-11 (reset and rescue equal real at G0).
- **F and C:** all 14, except for N.

**The classes:**
- **D:** `classify`(1 against 2, 1 against 3), with both signed contrasts and their 95% intervals.
- **H:** `classify`(2 against 4, 2 against 5): the host's use while the module is alive but blind.
- **Mc:** holds if `classify`(6 against 7, 6 against 8) or `classify`(9 against 10, 9 against 11) is
  "uses".
  - The transplant moves the module's 4 neurons' τ and bias and every edge with a module neuron at
    either end.
  - The turn neurons' biases are the carrier's.
  - Each carrier's real score is reported as a share of L1's at that turn, on the same worlds.

**The motor measures, on every genome:**
- **Open loop:** zero start, 40 ticks, the mean of the last 10, other inputs 0. The food currents
  reach every `food_left` and `food_right` sensor, the module's noses included. Measured:
  - u(m, 0) at m ∈ {0.02, 0.08, 0.25};
  - the signed K_D (a central difference in d of ±0.001) and K_C (m ± 0.01) at those m;
  - the forward command.
- **Closed loop, condition 4** (no stereo cue anywhere): the mean turn and forward commands, and the
  share of saturated turn neurons (|tanh| > 0.99), over the episode's ticks.
- **Closed loop, condition 1:** the same three.

**For R:** each draw's open-loop K_D and K_C at generation 0, and its final edge signs and magnitudes.

**At generation 0, per run of M and R:** the population's count of "uses" members among its 32
(conditions 1-3, on the G0 population worlds).

**Along training,** at generations 0, 100, 250, 500, 750 and 999, for each run's best of the
generation (the checkpoint candidate), on the along-training worlds:
- D (conditions 1-3), with its signed contrasts;
- the open-loop u(m, 0), K_D and forward command.

**The final populations of M:** all 32 strains, conditions 1 and 2, on the final-population worlds.

**References on the hold-out:** L1 on its carrier at turn +0.2 and at −0.2 (conditions 6-11), and
04a run 2 ungrafted (condition 1).

**Missing measures:** a measurement that did not complete makes every outcome that needs it "not
read" for that run, and the run is named.

## 6. Outcomes

**O1 (M − N) and O1b (M − R), confirmatory, paired by run.**
- **The estimand:** the mean over complete pairs of the difference in F's hold-out mean.
- **The interval:** `_boot_means(d, 10 000, 20 261 001)` from E2d, with the 5th and 95th percentiles
  by `numpy.percentile`. O1 and O1b use the same seed.
- **The rules, in order:**
  1. **"Reversed: M is worse"** if the upper bound is below 0;
  2. **"Supports"** if the lower bound exceeds 0 and the estimate is at least 0.5;
  3. **"Positive; estimate below 0.5"** if the lower bound exceeds 0;
  4. **"Does not support an effect of at least 0.5"** if the upper bound is below 0.5;
  5. **"Inconclusive"** otherwise.
- **The fixed wording of "supports":**
  - O1: "the arm evolved with the graft's output ends with a better final brain than the arm
    evolved without it";
  - O1b: "the graft's designed signs beat random signs".
- **Fixed companion sentences:**
  - with O1 "supports", if the 90% bootstrap interval (same method) of M's mean climb F − G0 includes
    0: **"N ended lower; M did not improve"**;
  - with O1b "supports", if R − N's estimate is below 0: **"random signs were worse than no graft"**.
- **The two are read separately,** with no adjustment. If the tests were independent, the chance of
  at least one false "supports" under no effect would be about 11-14% (`power.json`). They share M,
  so that is an illustration, not a property.
- **The sign-flip p** is reported beside each, not used.
- **The power, from `power.json`.** It uses 2 000 bootstrap resamples per simulated decision (10 000
  are registered), with normal paired differences of SD 1.3 or 2.0. There is no basis for the SD:
  E4s-0 has no paired run data.

  | SD of the differences | Effect 0 | Effect 0.5 | Effect 1.0 |
  |---|---|---|---|
  | 1.3: "supports" | 6% | 44% | 91% |
  | 2.0: "supports" | 7% | 28% | 64% |

  - **Bimodal, half the runs keeping +2:** 93%.
  - **So:** an effect of about 1 target per episode is detected if the SD is about 1.3; at SD 2.0,
    64% of the time.
- **O1b's reading:**
  - R is often a harmful graft at the start: random nose signs make a comparator respond to the
    common level. So "designed signs beat random signs" does not mean the designed graft beats no
    graft.
  - **R − N** is reported beside it, descriptive, with the companion sentence above.
  - R's final edge signs and magnitudes are reported.
- **M − N > 0 does not require M to climb:** N may end lower. O1c reports the climbs.
- **Minimum pairs:** O1 and O1b are read only with at least 12 complete pairs. Otherwise they are
  "not read", and the dropped pairs are named.

**O1c (descriptive).**
- **Per run:** F − G0 in hold-out score.
- **The differences of the climbs:** M against N, and M against R.
- **Stated in advance:**
  - M's and N's G0 bests are picked with and without the graft's output. So (F_M − F_N) − (G0_M −
    G0_N) subtracts the graft's immediate benefit, together with any difference between the two
    representatives' selections;
  - a negative climb difference is expected even if M ends higher;
  - G0_M − G0_N is reported beside it.

**O2, the module's use at the two endpoints** (M, R, F0, U, S; per run). The labels for the nine cells
of D at G0 (rows) against D at F (columns):

| G0 \ F | uses | unclear | no material benefit |
|---|---|---|---|
| **uses** | uses at both endpoints | uses at G0; F unclear | uses at G0 only |
| **unclear** | uses at F; G0 unclear | unclear at both endpoints | no use at F; G0 unclear |
| **no material benefit** | uses at F only | no use at G0; F unclear | uses at neither endpoint |

- **Never folded into the label:** Mc at F, H at G0 and at F, the signed contrasts at both endpoints,
  and the G0 population's user count are reported beside it.
- **The arm's reading, descriptive:**
  - a label is named if at least 12 of 16 runs carry it (6 of 8 in F0, U and S). The denominators
    stay fixed when runs are "not read";
  - if no label reaches its threshold, the reading is **"no label named"**, with every count;
  - **retention among G0 users:** the share of runs that use at G0 and also at F, among the G0 users
    whose F was read. It is "not applicable" if there are none.
- **A loss of use at F:** F0 − M is the descriptive comparison that addresses selection against
  clamped drift (§2).

**O2b, score with use.**
- **Defined for** each run labelled "uses at both endpoints".
- **The share:** F's hold-out mean divided by L1's on its carrier at turn +0.2, on the same worlds
  (the point estimate).
- **The bands:** at least 0.9; at least 0.5 and below 0.9; below 0.5.
- O2 is reported jointly with O2b.

**C2's reading,** per run at G0 and F, from the module's signed contrasts, in this order:
1. **"uses"** if `classify` gives "uses";
2. **"harmful"** if real − module mean has an upper bound below −0.25;
3. **"neutral"** if both contrasts' intervals lie inside (−0.25, 0.25);
4. otherwise **"unclear"**.

The direction of real − module mean is reported separately. C2 is reported beside its ungrafted
champion on the same worlds. E4s-0 found its G0 harmful (real − mean −1.76); its new G0 is classified
on the hold-out.

**O3 (descriptive):**
- F0, U and S against M (their F, O1c and O2);
- the trajectories along training;
- M − N and M's O2 split by M's 16 G0 bests' open-loop |u(0.08, 0)|. The split is 8 against 8 by
  rank, ties to the lower run index.

## 7. E3's artefact rule (the proposal's rule, as amended in D148)

E3 starts from E4s-0's frozen L1 on its carrier, labelled as a hand-built circuit on a silent worm.
An evolved host-plus-graft genome replaces it only if all of these hold:
- at least 12 of 16 M runs are "uses at both endpoints";
- the chosen genome, the F with the highest final validation mean among those runs (ties to the
  lowest run index), has O2b of at least 0.9;
- it passes E3's own positive control.

## 8. The cap, admission and the reserve

**The cap:** 24 GPU-hours for E4s-1, counted through `wormwars.accounting`, every stage included.

**The only binding limits** are the 24-hour cap (the cap clock) and admission.
- The stage figures below are for planning, not separate caps.
- A stage stopped by the cap clock leaves a not-completed record and is not rerun.

**The evaluation reserve** is the projection's estimate of both evaluation stages, times 1.25.

**Admission:**
- **Each training batch** b is admitted, in order, if the hours spent, plus batch b's projected
  time, plus the evaluation reserve, are within 22.5 h (24 h less a 1.5 h general reserve).
- **Once a batch is refused, no later batch starts.** The confirmatory batches 1-6 come first.
- **Arms not run** are reported as not run. The evaluation covers whatever completed.
- **The evaluation stages** are admitted if the hours spent plus their projected time are within
  24 h.

## 9. Budget

**Training:** E2's measured 1.35 h per batch (`experiments/E2-optimizer-screen/train-ga.json`,
4 862 s) × about 1.03 for 306 neurons. Ten batches come to about 14 h.

**Evaluation, by §5:**

| Part | Episodes |
|---|---|
| Endpoints: M, R, F0, U, S and C2 (64 runs) × (14 + 14 + 11 conditions, for F, C and G0) × 1 024 | about 2.56 M |
| Endpoints: N (16 runs) × 3 genomes × 4 conditions × 1 024 | 0.20 M |
| Along training: 80 runs × 6 generations × 3 × 256 | 0.37 M |
| G0 population counts: 32 runs × 32 × 3 × 256 | 0.79 M |
| Final populations: 16 × 32 × 2 × 256 | 0.26 M |
| References | about 0.01 M |
| **Total** | **about 4.2 M** |

At E4s-0's measured rates (306 episodes per second at 1 × 1 024, 863 at 4 × 1 024), that is about
1.5-4 h.

**Expected total:** about 16-19 h.

## 10. Tests before the formal run (each seen failing first; sabotage where a check could not fail)

1. `arm_scales`: every factor, for each arm.
2. R's draw: its order, its seed, the weight s_k × 3.0, and its recorded hash.
3. N's construction, with its edges at 0, and the end-of-run assertions.
4. The H conditions, which change only the intended currents.
5. The Mc transplant: what moves, and the carrier's biases.
6. The open-loop measures, with L = m + d/2 and R = m − d/2 and u clamped.
7. On synthetic inputs: O1's rules, the O2 table, C2's reading and the companion sentences, with
   every label reached.
8. The world ranges.
9. L1's registration in `graft.MODULES`, for the hygiene guard.
10. G2's input history and coverage.
11. A smoke of every stage.

## 11. What E4s-1 cannot show

- Anything about worm chemotaxis.
- A history between G0 and F, or why a use changed. The probes interpret; they do not decide.
- **Whether a loss of use is selection or drift from the bounds:** F0 − M addresses it,
  descriptively.
- Transfer of a particular computation into the host.
- Effects much below about 1 target per episode with 16 runs, and less than that if the SD is near 2.
- Whether another module would fare better (L4×P was never tried).

## 12. Departures from design v2

All arose in the pre-registration reviews:
- **C2's "harmful":** its bound moved from an upper bound below 0 to below −0.25, and "uses" now comes
  first. That is a threshold change, made so that "harmful" and "neutral" cannot overlap.
- **O2's labels:** an unclear endpoint is now named in the label (for example "uses at F; G0
  unclear"), not folded into it.
- **Run indices:** now 0-15, not 1-16.
- **G3's genomes:** E4s-0's generation-0 bests were replaced by E2 GA's 8 champions.
- **O1:** a "positive; estimate below 0.5" label was added.

## 13. Amendments

None yet.
