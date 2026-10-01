# E4s-1: the comparator graft under evolution (design v1, 2026-10-01)

Status: a design for review by Astra 6 and Fable 5.1. A pre-registration follows only if both agree.
Nothing has run on E4s-1's worlds or seeds.
- **Its basis:** the adopted plan (`docs/E4s/ROADMAP-PROPOSAL.md` v2.1, D144) and E4s-0's corrected
  results (`experiments/E4s-stereo-module/E4s-0/RESULTS.md`, D147).
- **Its budget:** the owner's 96-hour ceiling for E4s; E4s-0 used 0.23 h.

## The question

E4s-0's 4-neuron comparator, L1, steers by the left-right difference on its own. Grafted onto random
N2 brains, the best brain of each starting population uses it. **When the whole brain then evolves,
what happens to that use, and does the graft help?**
- Is the module's stereo use **retained, acquired, lost** or **never used**?
- Does the module stay competent on its own?
- Does the host acquire stereo steering of its own?
- Does the graft's output improve the evolved brain? Do its designed weights matter, against a graft
  of the same shape with random signs?

Stereo sensing is a game-design choice (the owner's option (a)). The stereo computation starts in a
graft with its own noses and its own path to the motors, outside the N2 mask. Every claim says so.

## What E4s-0 changes (D147)

- **The turn offset is a first-order variable.**
  - L1 qualified on the carrier with a constant turn command of 0.2: 5.18 targets per episode, and
    3.86 in tuning without the bias.
  - Random backgrounds carry their own offsets, a median |turn| of 0.25 of either sign.
  - On 04a run 2 (turn −0.28) the graft was harmful.
  - So **every measured genome's mean turn command and the brain's open-loop differential gain are
    recorded,** apart from its score.
- **The ceiling is near 5.** L1's gain (about 36) is the most its two synapses of weight 3 can give,
  and mutating them can only lower it. A higher score needs other paths; the host's are the only
  ones evolution can grow.
- **Generation-0 bests start at the plateau's level:** median 2.06, against the champions' 2.19. Score
  alone cannot separate "retained" from "replaced", so the module's use (D) is read along training.
- **Mutational load is high.** On the carrier at 0.25×, about half the module mutations are lethal.
  - Elitism protects the best, so free-against-frozen will partly measure this load.
  - **A 0.125× arm (S)** is added as a descriptive sensitivity check.
- **R's control varies only signs:** all 20 of L1's edges have magnitude 3.
- **C2 starts in a harmful interaction.** The ungrafted champion is measured on the same worlds, and
  signed probe effects are reported beside its class.

## Gates before any evolution (registered; a failure stops E4s-1 for diagnosis)

1. **Re-qualification:** L1 (`module.json`, sha256 `9613cd15…77d4`) on its carrier (forward 1.0,
   turn 0.2), on 1 024 fresh worlds. It passes if the mean's 95% lower bound (E2d's `world_ci`) is at
   least 5.0, **and** it meets "uses" under the module probes.
   - With E4s-0's mean of 5.18 and its interval, a fail by chance is unlikely, about 1% by our
     arithmetic.
   - Failing would stop E4s-1, not lower the bar.
2. **The CUDA state tolerance** (design v3's pending gate):
   - an inert L1 graft (outputs removed) against the ungrafted genome;
   - ≤ 10⁻⁴ in the 302 neurons' state over 300 ticks;
   - 32 random N2 genomes and 04a's 16 champions;
   - at E4s-1's real shapes: training, 8 runs × 32 strains × 8 worlds; and evaluation, one padded
     strain × 1 024.
3. **The score-level check:**
   - the same 48 genomes, inert-grafted against ungrafted, on 256 worlds;
   - each genome's mean within ±0.05;
   - the share of identical per-world counts reported.

## The arms (02's GA as E2 kept it: population 32, 3 elites, truncation 8, 8 worlds per strain, 1 000 generations, checkpoints every 25; Task N, unshaped)

| Arm | Generation 0 | Module mutation | Runs | Role |
|---|---|---|---|---|
| **M** | L1 on random N2 (04a's `initial_population` on N2, embedded) | 0.25× | 16 | main |
| **N** | M's genomes; every graft-to-host edge (the 16 output edges) at 0 and pinned throughout | 0.25× | 16, paired with M | **Confirmatory 1:** does the graft's output help? (M − N) |
| **R** | M's genomes with each of L1's 20 edge signs drawn at random (magnitudes are all 3); one draw per run, from a seed derived from the run seed | 0.25× | 16, paired with M | **Confirmatory 2:** the designed signs against a graft of the same shape (M − R) |
| F0 | as M | 0 (frozen) | 8, paired with M 1-8 | descriptive: protection by construction |
| U | as M | 1× | 8, paired with M 1-8 | descriptive: 02's scale |
| S | as M | 0.125× | 8, paired with M 1-8 | descriptive: lower mutational load |
| C2 | L1 on 04a run 2, 32 identical copies | 0.25× | 8 | descriptive case study: a harmful start |

**Ownership:**
- the module owns its 4 neurons' τ and bias, and every edge with a module neuron at either end;
- the host owns everything else, the turn neurons included;
- in F0 the module is pinned while the host evolves, so its function can still change through the
  host.

**Run order, in batches of 8 runs:**
1. M 1-8 with N 1-8;
2. R 1-8 with M 9-16;
3. N 9-16 with R 9-16;
4. F0;
5. U;
6. S;
7. C2.

The three confirmatory arms finish first. Each batch has E2's composition.

**Seeds:** run seed 1 160 000 + i. M, N, R, F0, U and S share i, and so their backgrounds; R's sign
draw comes from seed 1 165 000 + i.

**World ids:** a new block at 942 million, disjoint from every earlier range, E4s-0's included (a
test checks):
- training: base 942 000 000, span 500 000;
- validation: 942 600 000 + 256;
- hold-out: 942 700 000 + 1 024;
- re-qualification: 942 800 000 + 1 024;
- along-training probes: 942 900 000 + 256;
- the score-level check: 942 950 000 + 256.

## Measures (on the hold-out of 1 024 worlds; each genome one strain on all of them)

**The genomes, per run:**
- **F,** the final generation's best: the registered reading;
- **C,** the champion (the best validation checkpoint), reported beside F;
- **G0,** the generation-0 best (the checkpoint-0 candidate).

**On each genome:**
- **The score:** the mean count.
- **D, dependence:** E2d's class under the module probes, real against module mean and real against
  module swapped. "Uses" is D.
- **Mc, module competence:** the genome's module (its parameters) transplanted onto the carrier
  (forward 1.0, turn 0.2), classified for "uses".
- **H, host stereo:** the host's "uses" while the module is alive but blind. The module's noses get
  the mean, and the host's sensors get real, against the host's sensors on the world's mean probe,
  and on its swapped probe.
- **Turn offset and gain:**
  - the mean turn command over the episode (`motor_stats`);
  - the open-loop differential gain K_D at the turn command (E4s-0's attenuation probe, the module
    included).
- **Secondary:**
  - the lesion cost, with the module silenced;
  - the reset-to-seed probe, the module's parameters reset to L1's.

**Along training** (Fable, E4s-0): at generations 0, 100, 250, 500, 750 and 999:
- for each run, the best of the generation;
- on 256 worlds: D, the turn offset and K_D.

**The final populations of M:** all 32 strains, real against module mean, on 256 worlds.

**Stage A's reference:** L1 on its carrier is scored on the same 1 024 hold-out worlds. **C2's
reference:** 04a run 2 ungrafted, on the same worlds.

## Outcomes (proposed; fixed in the pre-registration)

**O1 and O1b, the confirmatory comparisons, paired by run.**
- **The estimand:** the mean over the 16 runs of the paired difference in F's hold-out mean, M − N
  (O1) and M − R (O1b).
- **The interval:** a 90% percentile bootstrap over runs (10 000 resamples, a fixed seed). The two
  intervals are read separately, with no adjustment, and that is stated.
- **The rules, in order:**
  1. **"Supports"** if the lower bound exceeds 0 and the estimate is at least 0.5;
  2. **"Does not support"** if the upper bound is below 0.5;
  3. **"Inconclusive"** otherwise.
- **The sign-flip p** is reported beside each, not used.
- **O1 is close to a manipulation check:** the graft works at generation 0. M − R is the informative
  comparison. Since R's signs cannot flip at 0.25× (|w| = 3), R cannot repair itself, and its reading
  says so.

**O2, each run classified** (M, R, F0, U, S, C2; exclusive; in order). "Unclear" applies whenever a
deciding measurement is in E2d's unclear class.

| Order | Condition | Class |
|---|---|---|
| 1 | the run did not complete | not read |
| 2 | G0 not D, F D | **acquired** |
| 3 | G0 not D, F not D | **never used** |
| 4 | F D and Mc | **retained** |
| 5 | F D, not Mc | **used, module changed** |
| 6 | F not D, H | **host stereo** |
| 7 | F not D, not H, Mc | **bypassed** |
| 8 | F not D, not H, not Mc | **lost** |

- **N reports H at G0 and at F only:** D is impossible there.
- **H at G0 and F is reported for every run.** Host acquisition means H at F without H at G0.
- **The arm's reading:** a class named if at least 12 of 16 runs (6 of 8 in the descriptive arms) fall
  in it; otherwise "mixed".
- **What can be claimed about transfer:** M against N's H-acquisition rates can support
  graft-assisted host acquisition. Transfer of a particular computation is not claimed.

**O2b (descriptive, with registered bands):** F's score as a share of L1 on the carrier on the same
worlds: at least 0.9; 0.5 to 0.9 ("partly"); below 0.5.

**O3 (descriptive):**
- F0, U and S against M;
- C2 against its ungrafted champion, with its signed probe effects;
- the along-training trajectories of D, the turn offset and K_D.

## Budget

- **The neuron count is 306** (302 + 4), so the cost factor on E2's rate is about (306/302)² ≈ 1.03.
- **Training:** 80 runs in 10 batches of 8. E2 measured 1.35 h per batch, so about 14 h.
- **Evaluation:**
  - F, C and G0 per run, each on 1 024 worlds, under 3 module probes, 2 H probes, Mc (3) and the
    lesion and reset probes: about 30 k episodes per run, 2.4 M in total;
  - along training: about 5 k per run;
  - the final populations: 0.26 M.

  About 1.5-2.5 h at E4s-0's measured 460-860 episodes per second.
- **Gates:** about 0.2 h.
- **Total:** about 16-17 h. **Proposed cap: 24 GPU-hours,** with stage caps and E2's projection rule
  measured on E4s-1's shapes.

## Engineering

**Reused:**
- E2's stage frame, as E4s-0 and E2d use it;
- `evolve_batch` with its `initial` and `mutation_scales` hooks (GPU-checked, D144);
- `graft`, `wormwars/e4s`;
- E2d's `world_ci` and `classify`, imported unchanged.

**New, each test-first with sabotage checks:**
- R's sign draw;
- N's pinning of every output edge;
- the H probe (the module's noses on "mean" with the world on "mean" or "swapped");
- the Mc transplant (a genome's module parameters onto the carrier);
- the class table;
- L1 registered in `graft.MODULES`.

Genome files stay local (rule 1); the hygiene guard checks grafted genomes.

## What E4s-1 cannot show

- Anything about worm chemotaxis.
- Why a use is lost, if it is: the probes interpret, they do not decide.
- Transfer of a particular computation into the host.
- Behaviour beyond a module ceiling near 5, unless the host grows a path of its own.
- Whether a different module would fare better: L4×P was never tried.

## Questions for the reviewers

1. Is the design ready for a pre-registration? What must change?
2. The turn offset: is recording it (and K_D) enough, or should E4s-1 control it? For example, a
   registered turn-neuron bias in the graft.
3. Is S (0.125×) worth its 1.4 h? Are 16 runs enough for the confirmatory pairs?
4. The class table and the 12-of-16 reading: right, given that the G0 bests start at the plateau's
   level?
