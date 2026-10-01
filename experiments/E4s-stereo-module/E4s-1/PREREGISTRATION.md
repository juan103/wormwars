# E4s-1 pre-registration: the comparator graft under evolution

Status: **draft for review** by Astra 6 and Fable 5.1, 2026-10-01. Nothing has run on E4s-1's worlds
or seeds.
- **Binding:** it becomes binding when committed and pushed after both reviewers agree, before any
  gate or training runs (rule 2). From then on, the text is never changed; amendments go in the last
  section, dated.
- **Its design:** `docs/E4s/E4s-1-DESIGN.md` v2, reviewed twice (D148).
  - Confirmation round: Fable said "proceed to pre-registration"; Astra said "revise", with
    specification items only.
  - Those items, and the pins both listed, are fixed here (D149).
- **Its basis:**
  - the adopted plan (`docs/E4s/ROADMAP-PROPOSAL.md` v2.1, D144, with its dated notes);
  - E4s-0's corrected results (`experiments/E4s-stereo-module/E4s-0/`, D147).

## 1. The question and its frame

E4s-0's 4-neuron comparator, L1, steers by the left-right difference on its carrier. Grafted onto
random N2 brains, each simulated starting population's best brain used it. When the whole brain then
evolves on Task N under 02's GA:
- **O1:** does the graft's output lead to a better final brain than the same brain without it (M − N)?
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

- **The module:** `experiments/E4s-stereo-module/E4s-0/module.json`, sha256 `9613cd15…77d4` (checked
  in full before any stage).
  - L1: noses E4S_NL and E4S_NR (τ 0.5, bias 0) and comparators E4S_CL and E4S_CR (τ 0.5, bias 0).
  - 20 edges of magnitude 3: 4 from the noses, 16 onto the turn neurons.
  - **Its carrier:** forward command 1.0, turn command 0.2.
  - It is registered in `wormwars.graft.MODULES` as `comparator-L1`.
- **Task N:** E1's frozen configuration (checked against E1's gate record), world seed 1 100 001.
- **The GA:** 02's GA as E2 kept it (`evolve_batch`):
  - population 32, 3 elites, truncation 8;
  - 8 worlds per strain, 1 000 generations, validation checkpoints every 25 on 256 worlds;
  - unshaped fitness;
  - 02's mutation sigmas: w 0.08, g 0.04, log-τ 0.15, bias 0.05.
- **E2d's rules, imported unchanged** from `scripts/e2d.py`:
  - `world_ci`: a paired percentile bootstrap over worlds of the mean difference, two-sided 95%,
    10 000 resamples, seed 0;
  - `classify`: "uses" if both lower bounds > 0.5; "no material benefit" if both intervals lie
    inside (−0.25, 0.25); else "unclear".

## 3. Gates before any training (each failure stops E4s-1; a dated, reviewed amendment is the only way on)

**G1, re-qualification.**
- **The test:** L1 on its carrier, on worlds 942 800 000-942 801 023. It passes if `world_ci`'s
  lower bound of the mean against 0 is at least 5.0, **and** `classify` gives "uses" (real against
  module mean, real against module swapped).
- **The chance of a fail by chance alone** (`development-records/power.json`, from
  `scripts/e4s1_power.py`):
  - 0.9% if E4s-0's mean of 5.18 is the truth (plug-in);
  - 4.7% allowing for that mean's own error (predictive, a flat prior);
  - a pass needs a fresh mean of about 5.08 or more.
- **On failure:** E4s-1 stops and the failure is reported. The code and the environment may be
  checked. The module is not re-tuned within E4s-1.

**G2, the CUDA state tolerance.**
- **The genomes, 48:** 32 random N2 genomes (`initial_population` on N2, run seed 1 167 000) and 04a's
  16 champions.
- **The comparison:** each genome ungrafted, and with **N's construction**: L1 grafted, its 16 output
  edges present in the mask at weight 0.
- **The input history:** both brains receive the same imposed history for 300 ticks.
  - On each tick, a current uniform in [0, 0.35] at every sensory neuron the interface names, drawn
    from `numpy.random.default_rng(1 168 000)`.
  - The module's noses receive the food signals as the interface routes them.
- **The test:** the maximum absolute difference in the 302 host neurons' states, over all ticks and
  rows, is at most 10⁻⁴.
- **The shapes** (strains × rows), filled by tiling the 48 genomes in order:
  - training, 256 × 8;
  - validation, 8 × 256;
  - single-genome evaluation, 1 (padded) × 1 024;
  - single-genome probes, 1 (padded) × 256.
- **The basis for 10⁻⁴:** declared in advance (rule 7). It is about 70 times the CPU rounding
  measured for an inert graft (1.4 × 10⁻⁶, D140), allowing for CUDA's reduction orders. It is not
  derived from behaviour.

**G3, the score-level check.**
- **The genomes, all of which score:** 04a's 16 champions and E2 GA's 8 champions. (E4s-0's
  generation-0 bests are dropped: their host-only scores were 0.02-0.44; Astra, Fable.)
- **The comparison:** each genome ungrafted against N's construction, on worlds
  942 950 000-942 950 255.
- **The test:** each genome's mean lies within ±0.05 of the other's.
  - 0.05 is about 13 worlds changing by one target, out of 256.
  - The share of worlds with identical counts, and every genome's two means, are reported.
- **A narrow failure** is still a failure: it stops E4s-1 for diagnosis of closed-loop divergence.

## 4. Arms, masks, seeds, worlds

| Arm | Generation 0 | Module factor | Runs (i) | Role |
|---|---|---|---|---|
| **M** | L1 on random N2: `initial_population(N2 spec, run seed, 32)`, embedded by `graft.seeded_genome` | 0.25 | 16 (0-15) | main |
| **N** | M's genomes with the 16 output edges at 0, pinned (factor 0) throughout | 0.25 | 16, paired with M | confirmatory |
| **R** | M's genomes with L1's 20 edge signs redrawn | 0.25 | 16, paired with M | confirmatory |
| F0 | as M | 0 | 8 (0-7), paired with M 0-7 | descriptive |
| U | as M | 1 | 8 (0-7), paired | descriptive |
| S | as M | 0.125 | 8 (0-7), paired | descriptive |
| C2 | L1 on 04a run 2 (loaded by `load_genome`, label and edge hash checked): 32 identical copies | 0.25 | 8 | descriptive |

**Seeds:**
- run i of M, N, R, F0, U and S uses run seed 1 160 000 + i. So the arms share the run's background,
  its training worlds (`train_ids`) and its breeding generator (`breed_seed`), which is deliberate;
- C2's runs use 1 166 000 + i.

**R's draw:**
- `numpy.random.default_rng(1 165 000 + i).choice([-1, 1], size=20)`, applied in the order of
  `module.json`'s synapse list;
- no draw is rejected;
- one draw per run, shared by all 32 strains;
- each draw's signs and sha256 are recorded and committed before training.

**The mutation masks:** `arm_scales(ext, factor, pinned)`.
- Every host parameter is at 1 (02's sigmas).
- The module's parameters are at the arm's factor: its 4 neurons' τ and bias, and every edge with a
  module neuron at either end.
- N's 16 output edges are at 0; its nose edges mutate harmlessly.
- F0's module parameters are all at 0.
- A parameter at factor 0 never changes: its noise is 0, and clamping leaves an in-bounds value
  unchanged.
- Tests check every factor. Mutation counts per block (host, module, output edges) are logged per
  generation.

**End-of-run assertions:**
- N's 16 output edges are exactly 0 in every final genome;
- F0's module parameters are bit-identical to L1's in every final genome.

**Run order:** ten batches of 8 runs, E2's composition (8 runs × 32 strains × 8 worlds):
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
- **C**, the champion: the first checkpoint with the highest validation mean.
- **G0**, the generation-0 best: the checkpoint-0 candidate.

G0 and F are selected representatives. No history between them is claimed.

**On each of F, C and G0** (hold-out, 1 024 worlds; one padded strain):
1. **Score:** the mean count.
2. **D:** `classify` of real against module mean and real against module swapped (`graft_interface`
   probes), with both signed contrasts and their 95% intervals.
3. **H:** `classify` of the host, with the module alive but blind.
   - The module's noses are on "mean" with the world real, against the module's noses on "mean" with
     the world on its mean probe.
   - Likewise against the world on its swapped probe.
4. **Mc:** the genome's module parameters transplanted onto the carrier, by `graft.seeded_genome`
   with no background, plus the carrier's biases.
   - **What moves:** the module's 4 neurons' τ and bias, and every edge with a module neuron at
     either end. The turn neurons' biases are the carrier's.
   - **Two carriers:** forward 1.0 with turn +0.2, and with turn −0.2.
   - **Mc holds** if `classify` gives "uses" at either carrier.
   - Each carrier's score is reported as a share of L1's on that carrier, on the same worlds.
5. **Motor measures:**
   - **Open loop** (zero start, 40 ticks, the mean of the last 10; other inputs 0; the food currents
     reach every `food_left` and `food_right` sensor, the module's noses included):
     - the turn command u(m, 0) at m ∈ {0.02, 0.08, 0.25};
     - the signed K_D (central difference in d of ±0.001) and K_C (m ± 0.01) at those m;
     - the forward command.
   - **Closed loop, no stereo cue:** the module's noses on "mean" and the world on its mean probe. The
     mean turn and forward commands, and the share of saturated turn neurons (|tanh| > 0.99), over the
     episode's ticks.
   - **Closed loop, real input:** the same three.
6. **Secondary:**
   - the lesion cost: the score with the module's 4 neurons silenced (`Brain.silence`);
   - reset-to-own-seed: the module's parameters reset to the run's own generation-0 values, which for
     R are its random signs;
   - **L1 rescue:** the module's parameters replaced by L1's. This is an intervention, reported apart
     from the reset.

**For R:** each draw's open-loop K_D and K_C at generation 0, and its final edge signs and magnitudes.

**At generation 0, per run of M and R:** the population's count of "uses" members among its 32, on
the G0 population worlds.

**Along training,** at generations 0, 100, 250, 500, 750 and 999, for each run's best of the generation
(the checkpoint candidate), on the along-training worlds:
- D, with its signed contrasts;
- the open-loop u(m, 0), K_D and forward command.

**The final populations of M:** all 32 strains, D's contrast real − module mean, on the final-population
worlds.

**References on the hold-out:** L1 on its carrier at turn +0.2 and at −0.2, and 04a run 2 ungrafted.

**Compositions:** every rollout records its composition, and every measure its per-world counts.

## 6. Outcomes

**O1 (M − N) and O1b (M − R), confirmatory, paired by run.**
- **The estimand:** the mean over complete pairs of the difference in F's hold-out mean.
- **The interval:** a 90% percentile bootstrap over runs, 10 000 resamples, seed 20 261 001.
- **The rules, in order:**
  1. **"Reversed: M is worse"** if the upper bound is below 0;
  2. **"Supports: the graft's output leads to a better final brain"** (O1), or **"supports: the
     designed signs beat random signs"** (O1b), if the lower bound exceeds 0 and the estimate is at
     least 0.5;
  3. **"Positive, below 0.5"** if the lower bound exceeds 0 and the estimate is below 0.5;
  4. **"Does not support an effect of at least 0.5"** if the upper bound is below 0.5;
  5. **"Inconclusive"** otherwise.
- **The two are read separately,** with no adjustment. Under no true effect, the chance of at least
  one false "supports" is about 11-14% (`power.json`).
- **The sign-flip p** is reported beside each, not used.
- **The power, from `power.json`** (normal differences, SD 1.3): "supports" 6% with no effect, 44% at
  0.5, 91% at 1.0. If half the runs keep a benefit of +2 and the rest none, 93%. **Effects of about 1
  target per episode are detected; effects of 0.5 about half the time.**
- **O1b's reading:**
  - R is often a harmful graft at the start: random nose signs make a comparator respond to the
    common level. So "designed signs beat random signs" does not mean the designed graft beats no
    graft.
  - **R − N** is reported beside it, descriptive.
  - R's final edge signs and magnitudes are reported.
- **M − N > 0 does not require M to climb:** N may end lower. O1c reports the climbs.
- **Minimum pairs:** O1 and O1b are read only with at least 12 complete pairs. Otherwise they are
  "not read".

**O1c (descriptive).**
- **Per run:** F − G0 in hold-out score.
- **The differences of the climbs:** M against N, and M against R.
- **Stated in advance:**
  - M's and N's G0 bests are picked with and without the graft's output, so (F_M − F_N) − (G0_M − G0_N)
    subtracts the graft's immediate benefit;
  - a negative climb difference is expected even if M ends higher;
  - G0_M − G0_N is reported beside it.

**O2, the module's use at the two endpoints** (M, R, F0, U, S; per run).
- **The full 3 × 3 table** of D at G0 against D at F, with E2d's three states. **The named labels:**

  | D at G0 | D at F | Label |
  |---|---|---|
  | uses | uses | uses at both endpoints |
  | no material benefit or unclear | uses | uses at F only |
  | uses | no material benefit or unclear | uses at G0 only |
  | no material benefit | no material benefit | uses at neither endpoint |
  | unclear | no material benefit, or the reverse, or both unclear | unclear at an endpoint |

- **Never folded into the label:** Mc at F, H at G0 and at F, the signed contrasts at both endpoints,
  and the G0 population's user count are reported beside it.
- **The arm's reading, descriptive:**
  - a label is named if at least 12 of 16 runs (6 of 8 in F0, U and S) carry it, with every count
    reported;
  - retention among G0 users is the share of runs that use at G0 and also at F;
  - "mixed" is never given without the counts.

**O2b, score with use.**
- **Defined for** each run that "uses at both endpoints".
- **The share:** F's hold-out mean divided by L1's on its carrier at turn +0.2, on the same worlds
  (the point estimate).
- **The bands:** at least 0.9; at least 0.5 and below 0.9; below 0.5.
- O2 is reported jointly with O2b.

**C2's reading,** its own, per run at G0 and F, from the module's signed contrasts:
1. **"uses"** if `classify` gives "uses";
2. **"harmful"** if real − module mean has an upper bound below −0.25;
3. **"neutral"** if both contrasts' intervals lie inside (−0.25, 0.25);
4. otherwise **"unclear"**.

The rules apply in that order, so each run gets one reading. The direction of real − module mean is
reported separately. C2 is reported beside its ungrafted champion on the same worlds. E4s-0 found its
G0 harmful (real − mean −1.76), and its new G0 is classified on the hold-out.

**O3 (descriptive):**
- F0, U and S against M (their F, O1c, O2);
- the trajectories along training;
- M − N and M's O2 split by G0's open-loop |u(0.08, 0)| (M's 16 G0 bests; below or above their
  median).

## 7. E3's artefact rule (the proposal's rule, as amended in D148)

E3 starts from E4s-0's frozen L1 on its carrier, labelled as a hand-built circuit on a silent worm.
An evolved host-plus-graft genome replaces it only if all of these hold:
- at least 12 of 16 M runs "use at both endpoints";
- the chosen genome, the F with the highest final validation mean among those runs (ties to the
  lowest run index), has O2b of at least 0.9;
- it passes E3's own positive control.

## 8. Failures, reruns, caps

**The stage frame:** E2's, as E4s-0 used it.
- Each stage runs once. Its record is committed and pushed before the next stage starts.
- A stage that stops leaves a not-completed record. **One rerun is allowed per stage,** with a stated
  reason; a stopped rerun is final.
- A non-finite score stops its batch.

**A run that does not complete** is "not read":
- its pair drops from O1, O1b and O1c, and the dropped pairs are named;
- O2 counts it as "not read".

**The cap:** 24 GPU-hours for E4s-1, counted through `wormwars.accounting`, the gates and the
projection included.

**The projection** times every actual shape before training: training, validation, the evaluation
shapes (1 padded × 1 024 and × 256, instrumented), and the open loop. It freezes:
- **stage caps:** gates 0.5 h, training 16 h, evaluation 6 h, reserve 1.5 h;
- an evaluation reserve.

**Admission:** before each training batch, the hours spent plus the projected remaining training
plus the evaluation reserve must fit within 24 h.
- If they do not, the remaining batches are not started. The confirmatory batches 1-6 come first.
- Arms not run are reported as not run.
- The evaluation then covers whatever completed.

## 9. Budget

- **Training:** E2's measured 1.35 h per batch (`experiments/E2-optimizer-screen/train-ga.json`,
  4 862 s) × about 1.03 for 306 neurons. Ten batches come to about 14 h.
- **Evaluation:**
  - per run: F, C and G0, each on 1 024 worlds under about 11 rollouts;
  - along training: 6 × 3 × 256 per run;
  - the G0 population counts: 32 × 3 × 256 per M and R run;
  - the final populations: 16 × 32 × 2 × 256.

  About 3.7 M episodes; at E4s-0's measured rates (306-863 episodes per second), about 3-4 h.
- **Expected total:** about 17-19 h.

## 10. Tests before the formal run (each seen failing first; sabotage where a check could not fail)

1. `arm_scales`: every factor, for each arm.
2. R's draw: its order, the seed, and its recorded hash.
3. N's construction, with its edges at 0, and the end-of-run assertions.
4. The H probe, which changes only the intended currents.
5. The Mc transplant: what moves, and the carrier's biases.
6. The open-loop measures.
7. The O2 table and C2's reading on synthetic classes; O1's rules on synthetic differences, every
   label reached.
8. The world ranges.
9. L1's registration in `graft.MODULES`, for the hygiene guard.
10. A smoke of every stage.

## 11. What E4s-1 cannot show

- Anything about worm chemotaxis.
- A history between G0 and F, or why a use changed. The probes interpret; they do not decide.
- Transfer of a particular computation into the host.
- Effects much below about 1 target per episode, with 16 runs.
- Whether another module would fare better (L4×P was never tried).

## 12. Amendments

None yet.
