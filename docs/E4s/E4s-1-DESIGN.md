# E4s-1: the comparator graft under evolution (design v2, 2026-10-01)

Status: v2, for a confirmation round by Astra 6 and Fable 5.1; a pre-registration follows only if
both agree. Nothing has run on E4s-1's worlds or seeds.
- **v1** (commit 2c31e8c): both said "revise"
  (`docs/reviews/20261001-E4s-1-design/`). v2 takes every must-fix; the map is the last section.
- **Its basis:** the adopted plan (`docs/E4s/ROADMAP-PROPOSAL.md` v2.1, D144) and E4s-0's corrected
  results (`experiments/E4s-stereo-module/E4s-0/RESULTS.md`, D147).
- **Its budget:** the owner's 96-hour ceiling for E4s; E4s-0 used 0.23 h.

## The question

E4s-0's 4-neuron comparator, L1, steers by the left-right difference on its own carrier. Grafted onto
random N2 brains, the best brain of each starting population uses it. **When the whole brain evolves:**
- does the graft's output lead to a better final brain than the same brain without it?
- do the graft's designed signs matter, against a graft of the same shape with random signs?
- how do the endpoints compare? Is the module used at generation 0 and at the end; is it still
  competent on its own; does the host steer by the difference itself?

Stereo sensing is a game-design choice (the owner's option (a)). The stereo computation starts in a
graft with its own noses and its own path to the motors, outside the N2 mask. Every claim says so.

## What E4s-0 established that the design uses (D147)

- **L1 qualified on its carrier with a constant turn command of 0.2.** It scored 5.18 targets per
  episode; in tuning, the same module scored 3.86 with no turn bias. The turn offset is therefore
  measured, not controlled (below).
- **An empirical reference near 5.** By E1's scripted steerer, a gain of about 32 scores 5.63 with
  turn bias 0.2. L1's direct path gives about 36, the most two synapses of weight 3 give. This is a
  reference for reading scores, not a proven ceiling: the brain may find other routes (Astra).
- **Generation-0 bests start near the plateau:** median 2.06, against the champions' 2.19. So a
  final difference of M over N needs M to climb (Fable): O1 is not a manipulation check.
- **Severe score loss under module mutation on the carrier:** at 0.25×, 122 of 256 mutants scored
  below 0.7. That is score loss, not shown to be lost function. Elitism keeps the best of 8 training
  worlds, not a guaranteed hold-out champion.
- **R varies only signs.** All 20 of L1's edges have magnitude 3. Random signs on the four nose edges
  make a comparator respond to the common level with probability ½, so many R draws inject a
  scent-driven turn: **R is often a harmful graft, not a neutral one** (Fable).
- **On 04a run 2 the graft was harmful** (real minus mean input to the module, −1.76). No ungrafted
  run was made on those worlds, so the cause is not attributed.

## Gates before any evolution (registered; a failure stops E4s-1)

1. **Re-qualification.**
   - L1 (`module.json`, sha256 `9613cd15…77d4`) on its carrier (forward 1.0, turn 0.2), on 1 024
     fresh worlds.
   - It passes if the mean's 95% lower bound (E2d's `world_ci`) is at least 5.0, **and** it meets
     "uses".
   - **The chance of a fail by chance alone is about 4-5%** (Fable). That is a plug-in estimate,
     conditional on E4s-0's mean and its error: a pass needs a fresh mean of about 5.08 or more.
   - **A failure stops E4s-1.** It is reported. Diagnosis may check the code and the environment, but
     the module is not re-tuned within E4s-1, and any continuation is a dated, reviewed amendment.
2. **The CUDA state tolerance.**
   - **The test:** the maximum absolute discrepancy in the 302 neurons' state, under identical
     imposed input histories, is at most 10⁻⁴ over 300 ticks. That is open loop, so trajectory
     divergence does not enter (Astra).
   - **The comparison:** for each genome, an ungrafted copy against **E4s-1's actual N construction**
     (the full mask, output edges present and at 0).
   - **The genomes:** 32 random N2 and 04a's 16 champions.
   - **The shapes, all E4s-1 uses:**
     - training, 8 runs × 32 strains × 8 worlds;
     - validation, 8 strains × 256;
     - single-genome evaluation, 1 padded strain × 1 024.
3. **The score-level check.**
   - **The genomes, all of which score** (Fable: random genomes mostly score 0, which would make the
     check vacuous):
     - E4s-0's 16 simulated generation-0 bests (seeds outside E4s-1's), with their own grafted
       backgrounds;
     - and 04a's 16 champions.
   - **The comparison:** each genome with N's construction against ungrafted, on 256 worlds.
   - **The test:** each mean within ±0.05; the share of identical per-world counts reported.

## The arms

02's GA as E2 kept it: population 32, 3 elites, truncation 8, 8 worlds per strain, 1 000
generations, checkpoints every 25; Task N, unshaped.

| Arm | Generation 0 | Module mutation | Runs | Role |
|---|---|---|---|---|
| **M** | L1 on random N2 (04a's `initial_population` on N2, embedded) | 0.25× | 16 | main |
| **N** | M's genomes; the 16 output edges present at 0 and pinned throughout | 0.25× | 16, paired with M | **Confirmatory 1:** M − N |
| **R** | M's genomes with each of L1's 20 edge signs drawn at random (magnitudes 3); one draw per run | 0.25× | 16, paired with M | **Confirmatory 2:** designed signs against random signs (M − R) |
| F0 | as M | 0 (frozen) | 8, paired with M 1-8 | descriptive |
| U | as M | 1× | 8, paired with M 1-8 | descriptive |
| S | as M | 0.125× | 8, paired with M 1-8 | descriptive |
| C2 | L1 on 04a run 2, 32 identical copies | 0.25× | 8 | descriptive case study |

**Mutation masks.** These are a new function, `arm_scales(ext, module_factor, pinned)`. The existing
`module_scales` pins the host and must not be used here (Astra, Fable):
- host parameters at 1 (02's scales);
- module parameters at the arm's factor;
- N's output edges at 0;
- F0's module at 0.

Tests check each factor exactly. Mutation counts are logged per parameter block (the adopted plan).

**End-of-run assertions:**
- N's 16 output edges are exactly 0 in every final genome;
- F0's module is bit-identical to L1 in every final genome.

**Pairing:** M, N, R, F0, U and S share run i's seed (1 160 000 + i). So they share its background,
its training worlds (`train_ids`) and its breeding generator (`breed_seed`): the pairing is
deliberate. R's sign draw comes from seed 1 165 000 + i, and C2's runs use 1 166 000 + i.

**Run order:** ten batches of 8 runs each:
1. M 1-8;
2. N 1-8;
3. R 1-8;
4. M 9-16;
5. N 9-16;
6. R 9-16;
7. F0;
8. U;
9. S;
10. C2.

The confirmatory arms finish first, in E2's composition.

**World ids:** a new block at 942 million, disjoint from every earlier range, E4s-0's included (a
test checks):
- training: base 942 000 000, span 500 000;
- validation: 942 600 000 + 256;
- hold-out: 942 700 000 + 1 024;
- re-qualification: 942 800 000 + 1 024;
- along-training probes: 942 900 000 + 256;
- the score-level check: 942 950 000 + 256.

## Measures (on the hold-out of 1 024 worlds; each genome is one strain on all of them)

**The genomes, per run:**
- **F,** the final generation's best: the registered reading;
- **C,** the champion (the best validation checkpoint), beside F;
- **G0,** the generation-0 best (the checkpoint-0 candidate).

G0 and F are the selected representatives at two endpoints. They are not shown to be ancestor and
descendant, so no history between them is claimed (Astra).

**On each genome:**
- **The score:** the mean count.
- **D:** E2d's three-state class under the module probes (real against module mean, and against
  module swapped), **with the signed contrasts and their intervals.**
- **Mc:** the genome's module (its parameters) transplanted onto the carrier.
  - It is tested at turn +0.2 and at −0.2, because a module that co-adapted to a host with a negative
    offset can be asymmetric (Fable).
  - Mc holds if it meets "uses" at either.
  - Its carrier score is reported as a share of L1's on the same worlds.
- **H:** the host's three-state class while the module is alive but blind. The module's noses get
  the mean, and the host's sensors get real, against the world's mean and swapped probes.
- **Motor measures:**
  - **open loop:** the turn command u(m, d = 0) at m ∈ {0.02, 0.08, 0.25}, the signed K_D and K_C at
    those levels (E4s-0's attenuation probe, the module included), and the forward command (Astra,
    Fable);
  - **closed loop, with no stereo cue:** the mean turn and forward commands and the share of saturated
    turn neurons, with the module's noses on "mean" and the world on its mean probe;
  - **closed loop, real input:** the same three measures.
- **Secondary:**
  - the lesion cost (the module silenced);
  - the reset-to-own-seed probe (the module's parameters reset to their own generation-0 values, which
    for R are its random signs);
  - **the L1 rescue probe:** the module replaced by L1. This is an intervention, reported apart from
    the reset (Astra).
- **For R only:** each draw's open-loop K_D and K_C at generation 0, and its final edge signs and
  magnitudes. Sign flips from ±3 at σ = 0.02 per generation are unlikely; shrinkage under selection
  is not excluded, and it is measured, not assumed (both).

**At generation 0 only:** the population's count of "uses" members, among its 32, on 256 worlds. An
"acquired" or "never used" reading depends on which founder 8 worlds picked (Fable).

**Along training:** at generations 0, 100, 250, 500, 750 and 999, for each run's best of the
generation, on 256 worlds:
- D, with the signed contrasts;
- the open-loop u(m, 0), K_D and the forward command.

**The final populations of M:** all 32 strains, D's contrast real − module mean, on 256 worlds.

**References on the hold-out:**
- L1 on its carrier;
- 04a run 2 ungrafted, for C2.

## Outcomes (proposed; fixed in the pre-registration)

**O1 and O1b, confirmatory, paired by run.**
- **The estimand:** the mean over the 16 runs of the paired difference in F's hold-out mean, M − N
  (O1) and M − R (O1b).
- **The interval:** 90% percentile bootstrap over runs, 10 000 resamples, a fixed seed. The two
  intervals are read separately, with no adjustment, and that is stated.
- **The rules, in order:**
  1. **"Reversed"** if the upper bound is below 0 (Fable);
  2. **"Supports"** if the lower bound exceeds 0 and the estimate is at least 0.5;
  3. **"Does not support"** if the upper bound is below 0.5;
  4. **"Inconclusive"** otherwise.
- **The sign-flip p** is reported beside each, not used.
- **O1b's wording:** "designed signs against random signs". R is often harmful at the start, so M − R
  > 0 can mean R is worse than no graft. **R − N** is reported beside it, descriptive (Fable).
- **The power, simulated with these exact rules** (16 runs, normal paired differences, 600
  simulations each):

  | SD of the differences | Effect 0 | Effect 0.5 | Effect 1.0 | Effect 1.5 |
  |---|---|---|---|---|
  | 1.3 | "supports" 5%, "reversed" 8% | "supports" 47% | 92% | 100% |
  | 2.0 | "supports" 8% | 29% | 65% | 89% |

  **16 runs detect effects of about 1 target per episode; effects of 0.5 are found only about half
  the time.** The design says so.

**O1c, how much each arm climbs (descriptive; Astra).**
- **Per run:** F − G0 in hold-out score.
- **The differences of these changes:** M against N, and M against R.
- **What can be called improvement by evolution:** only these changes. A final difference alone
  cannot.

**O2, the endpoints of the module's use, per run** (M, R, F0, U, S; three-state E2d classes;
`unclear` kept as its own state).

| D at G0 | D at F | Label (endpoint-based) |
|---|---|---|
| uses | uses | uses at both endpoints |
| not uses | uses | uses at F only |
| uses | not uses | uses at G0 only |
| not uses | not uses | uses at neither endpoint |

- **"Not uses"** splits into "no material benefit" and "unclear", and the full 3 × 3 counts are
  reported. Any "unclear" endpoint is shown as such, not folded into a label.
- **Beside D, never folded into its label:**
  - Mc at F;
  - H at G0 and at F;
  - the signed contrasts at both endpoints;
  - the G0 population's user count.
- **The arm's reading** is descriptive:
  - a label is named if at least 12 of 16 runs (6 of 8) carry it, with every count reported;
  - retention among G0 users, the share of G0 "uses" runs that also use at F, is reported (Astra);
  - "mixed" is never given without the counts showing whether "unclear" or incomplete runs dominate.

**O2b, score with use (Fable).** For each run with "uses at both endpoints", F's score as a share of
L1 on its carrier on the same worlds. The bands are: at least 0.9; 0.5 to 0.9; below 0.5. The arm's
O2 reading is reported jointly with O2b.

**C2's reading:** its own, from the signed contrasts at G0 and F.
- **"harmful":** real − module mean has an upper bound below 0;
- **"uses":** E2d's criterion;
- **"neutral":** both contrasts inside ±0.25;
- otherwise **"unclear"**.

It is reported beside its ungrafted champion on the same worlds. All 32 copies are identical, so its
G0 class is "unclear" by construction under E2d's rule (Fable).

**O3 (descriptive):**
- F0, U and S against M;
- the trajectories along training;
- M − N and the classes split by G0's |open-loop turn offset| (below or above the median, stated now
  as descriptive; Fable).

## E3's artefact rule (amends the adopted plan, D144; a dated note in the proposal)

An evolved host-plus-graft genome replaces E4s-0's frozen module on its carrier as E3's navigator
only if all of these hold:
- at least 12 of 16 M runs "use at both endpoints";
- the chosen genome (the best validation mean among them) has O2b of at least 0.9;
- it passes E3's own positive control (Fable).

## Budget, measured before the run

| Part | Estimate |
|---|---|
| Training: 80 runs in 10 batches; E2's measured 1.35 h per batch × 1.03 for 306 neurons | about 14 h |
| Evaluation at E4s-0's measured rates (306 episodes per second at 1 × 1 024): endpoints about 3 M episodes; along training, final populations, open loop and probes | about 3-4 h (Astra) |
| Gates and projection | about 0.3 h |
| **Total** | **about 17-19 h** |

- **Proposed cap: 24 GPU-hours.**
- **The projection stage** times every actual shape: training, validation, single-genome evaluation,
  instrumented 1 × 256 probes, and the open loop. It freezes stage caps and an evaluation reserve
  before training starts. Admission is the hours spent plus the projected remaining work, as in E4s-0.

## Engineering

**Reused:**
- E2's stage frame (as E4s-0 and E2d);
- `evolve_batch` with its hooks (GPU-checked, D144);
- `graft`, `wormwars/e4s`;
- E2d's `world_ci` and `classify`, unchanged.

**New, each test-first with sabotage checks:**
- `arm_scales`;
- R's sign draw;
- N's construction and its pinning;
- the H probe;
- Mc at ±0.2;
- the open-loop motor measures;
- the endpoint table and C2's reading;
- the end-of-run assertions;
- L1 registered in `graft.MODULES`.

Genome files stay local (rule 1).

## What E4s-1 cannot show

- Anything about worm chemotaxis.
- A history between G0 and F, or why a use changed. The probes interpret; they do not decide.
- Transfer of a particular computation into the host.
- Effects much below about 1 target per episode, with 16 runs.
- Whether another module would fare better (L4×P was never tried).

## Changes from v1

| v1 review item | v2 |
|---|---|
| O1 is not a manipulation check (Fable 1); final superiority is not evolutionary improvement (Astra 1) | Deleted; O1c (F − G0 per arm, and its differences) |
| "Reversed" missing (Fable 11) | Added as the first rule |
| R often harmful; "cannot repair itself" wrong (Fable 3, Astra 4) | "Designed against random signs"; R − N beside it; R's K_D and K_C at G0 and its final signs and magnitudes measured |
| Endpoint labels claim histories; Mc and H hidden; three states (Astra 3) | An endpoint-based D table with three states; Mc, H, signed contrasts and the G0 user count reported beside it, never folded in |
| C2 "unclear" by construction (Fable 2) | Its own signed reading, beside its ungrafted champion |
| "Retained" says nothing about score; E3's swap (Fable 4) | O2 read with O2b; E3's rule requires O2b ≥ 0.9 and E3's positive control |
| Mc only at turn +0.2 (Fable 5) | ±0.2, either; its carrier score as a share of L1's |
| The turn offset measured confounded (Fable 6, Astra 2) | Open-loop u(m, 0), signed K_D and K_C and forward at fixed levels; closed loop with no cue; saturation kept; not controlled (both) |
| The ceiling, "cannot repair", "lethal" overclaims (Astra 4) | An empirical reference; measured, not assumed; "severe score loss" |
| 04a run 2's cause implied (Fable 7) | Reworded |
| Gate 1's 1% (Fable 8, Astra 5) | 4-5%, a plug-in estimate; what diagnosis allows |
| Gate 2's definition and shapes (Astra 5) | Identical imposed inputs; N's actual construction; validation's 8 × 256 added |
| Gate 3 nearly vacuous (Fable 9) | Scoring genomes |
| Mutation masks (both) | `arm_scales`, with tests; mutation logging restored |
| Reset against rescue for R (Astra 6) | Reset to its own seed; L1 rescue reported apart |
| Budget (Astra 7) | Evaluation re-estimated at measured rates; every shape projected; stage caps and a reserve |
| Unpinned details (Fable 10) | C2's seeds; shared training worlds and draws stated; end-of-run assertions; ten batches named |
| Power (both) | Simulated with the exact rules and stated |
| The G0 founder effect (Fable, should-fix) | The G0 population's user count |
