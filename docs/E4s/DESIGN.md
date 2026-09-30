# E4s: a hand-built stereo module grafted onto N2 (design v2)

Status: design v2 for a second review by Astra 6 and Fable 5.1, 2026-09-30. v1 (commit 3557a2a,
D139) was reviewed by both, and both said "revise" (archived in
`docs/reviews/20260930-014518-E4s-design/`; D141). What changed, and why, is in the last section.
Nothing has run on E4s's worlds or seeds. The exploratory, design-informing measurements are
disclosed below. A pre-registration follows only if both reviewers agree.

## Why, and why now (the owner's direction, 2026-09-30)

- **Evolution has not found stereo smell.** E2 and its diagnosis E2d (published) found what E2d
  calls a **"non-stereo plateau"**.
  - No champion among E2's and 04a's 47 distinct champions meets E2d's "uses the left-right
    difference" criterion.
  - 43 show no material benefit from intact bilateral input; 4 are unclear, with small, detectable
    benefits.
  - Most score between 1.90 and 2.50 targets per episode: 35 of the 47. M-avg, the scripted
    controller that reads only the mean of the two sensors, scores 2.20.
  - No tested change to the optimizer left the plateau: more worlds, gentler mutation, both, a
    smaller ES σ.
  - E3, the minimal A/B organism, needs a navigator that steers by the smell's side.
- **The owner's plan:** build the stereo capability by hand, and let evolution settle it into the
  connectome.
  - Two noses, left and right scent inputs.
  - A ring attractor borrowed from the fly's head-direction system, since it is well studied. It
    keeps a memory of where the smell came from, relative to the body.
  - One side of the ring biases turning left, the other right.
  - Then evolution optimises the whole brain.

  Removing neurons one by one to find the minimal circuit is later work (E3 or E4).
- **This is ahead of the plan.** Hand-building was to start in E4 with the A/B wey: gluing
  connectomes with a flip-flop, then letting them merge under evolution. E4s ("E4-stereo") is a
  preliminary version of that line, run now because E3 needs it. Being early, it can still surprise
  us.
- **The owner's ceiling for E4s is 96 GPU-hours.** This registration proposes a cap of 30, with an
  estimate of about 16 (see Budget).

## What is known before designing (disclosed)

1. **The literature** (`docs/E4s/literature-report.md`: a deep research by Claude Sonnet 5.5 on the
   owner's instruction; the brief is in `brief.md`). The report marks some citations "†" as
   unverified, and neither reviewer verified its citations.
   - **Available to borrow:**
     - the fly's compass: local recurrent excitation (E-PG), global inhibition (Δ7), and shifter
       cells (P-EN) that rotate the bump by angular velocity;
     - rate-model ports with explicit equations (Goulard et al. 2021; Stone et al. 2017, via Sun et
       al. 2020; Noorman et al. 2024);
     - the fly's steering readout (PFL3), which compares shifted copies of the bump; its left minus
       right output drives turning.
   - **Not found by the report's search:** a published model that anchors a ring on a bilateral
     *chemical* difference, and published work that grafts a designed module into a
     connectome-constrained network and follows its fate under evolution.
   - **Biology, stated plainly:** the real worm steers by comparing the scent over time as its head
     sweeps (klinotaxis; for example Izquierdo and Lockery), not by comparing two noses a few
     micrometres apart. (The report's figure of about 8 µm is not verified.) Stereo here is a design
     choice, fly-inspired engineering, not worm-faithful. The readout is a hemifield sum inspired
     by PFL3, not a faithful port: the fly's model combines heading, a goal input and nonlinear
     responses. The interface already says its mappings are modelling choices.
2. **The signal is small.** The left-right difference at the sensors is about 0.004-0.017 in
   injected current, against a common level of about 0.02-0.25. The reviewers re-derived this: the
   report's table is approximate and omits the forward-offset correction. E1's scripted stereo
   steerer, turn = bias + k(L − R), scores:

   | k | 4 | 32 | 256 | 8192 |
   |---|---|---|---|---|
   | score, turn bias 0.2 | 2.38 | 5.63 | 8.51 | 8.78 |

   At zero bias, k = 32 scores 4.23.
3. **An open-loop probe of the champions** (exploratory, design-informing; `scripts/e4s_gain_probe.py`
   → `experiments/E4s-stereo-module/development-records/gain-probe.json`). v2 follows both
   reviewers' changes.
   - **Method:** each of the 47 distinct champions receives fixed scent currents at its left and
     right sensory neurons (common level 0.02, 0.08 and 0.25), from a zero state, with every other
     input at zero. The turn command is read as the world reads it. Measured:
     - the small-signal gain (a central difference at δ = ±0.001);
     - a signed response curve (δ from −0.1 to +0.1);
     - the transient after a step;
     - a reversal with the state carried over;
     - the share of saturated turn neurons.

     v1's least-squares slope over δ of ±0.02 is dropped: it capped at 66.7 even for an ideal
     clipped k = 256.
   - **Result:**
     - median |small-signal gain| 0.098, at most 0.68, matching v1's figures;
     - the median largest change after a step is 0.032;
     - with the state carried over, the output changes when the difference reverses in 138 of the 141
       genome-level pairs. The other 3 are one genome at the three levels: its turn bias (−0.15 to
       −0.40) dominates, and its response is below 10⁻³. That is a weak response, not a latch;
     - on average 4.8% of turn neurons are saturated at δ = 0.
   - **What it shows:** a weak, sustained differential response under these conditions (static,
     zero start, other inputs zero).
   - **What it does not show:**
     - whether the plateau comes from gain or from topology;
     - that the champions use a temporal route.

     Low gain is what a non-stereo controller looks like under either reading, so the result is
     consistent with the report's gain hypothesis, not evidence for it (a correction to v1 and to
     D139, D141).

## The modules

Every module is appended to N2's 302 neurons as named extra neurons ("E4S_…"), through
`wormwars/graft.py` (D140).
- **Designed synapses** are new chemical edges with an anatomical weight of 1. Their signed weights
  live in `Genome.w`, since Dale's law is off (`BrainConfig.dale = False`).
- **Synapse direction:** checked, pre → post. A module synapse T → SMDDL drives SMDDL; the reverse
  edge drives the module. Implementation adds this as a test.
- **Noses** use the worm's own interface gain of 1.0, and the gain is not tuned. All gain comes from
  synaptic weights within the genome's bounds (w ∈ [−3, 3]; τ ∈ [0.5, 20]; bias ∈ [−2, 2]).
- **Turn sign:** a positive turn command steers toward the left sensor, as S-const's k > 0 does. So
  a "left" readout excites the dorsal turn neurons (SMDD, RMDD) and inhibits the ventral ones (SMDV,
  RMDV). Stage A checks the sign in the world.

### M2, the ring (the owner's design; 32 neurons)

- **Noses NL and NR** get new interface entries: the same `food_left` and `food_right` signals
  that AWA, AWC and ASE receive.
- **An 8-column ring, E0-E7.** The columns sit at virtual azimuths θᵢ = −157.5° + 45°·i.
  - NL projects onto the columns with weights a·max(0, cos(θᵢ − φ)), and NR with
    a·max(0, cos(θᵢ + φ)).
  - Local excitation w_e runs between neighbouring columns.
  - Global inhibition runs through a Δ7-like pair (Δa and Δb): every column excites both, and both
    inhibit every column with weight w_i.
- **What the ring encodes (Astra):**
  - The bump sits at about tan ψ = [(L − R)/(L + R)]·tan φ.
  - For the Gaussian scent, that is the normalised lateral contrast. It is not the smell's physical
    bearing independent of distance.
  - We call ψ **the odour-side estimate**, and do not claim a bearing.
- **The turn copy and the shifters:**
  - Two relay neurons receive a copy of the executed turn command.
    - TC_L gets + from the dorsal turn neurons and − from the ventral; TC_R gets the reverse.
    - The relays read the same eight neurons the world's turn readout reads, so the copy includes
      the background's contribution, not only the module's.
    - It is not the executed turn: the world clamps the command and scales it by 0.30. **It is an
      approximate internal command,** calibrated in Stage A.
  - 16 shifter cells rotate the bump against the wey's own turn, so the odour side is remembered
    across turns (the fly's P-EN mechanism; applying it to an odour estimate is our extrapolation):
    - P⁺ᵢ gets Eᵢ and TC_L, and projects to Eᵢ₋₁;
    - P⁻ᵢ gets Eᵢ and TC_R, and projects to Eᵢ₊₁.
- **The readout:**
  - T_L sums the left-hemifield columns, T_R the right. A PFL3-inspired hemifield sum.
  - T_L and T_R inhibit each other: a flip-flop-like amplifier, the main source of gain.
  - Push-pull output: T_L excites SMDD/RMDD and inhibits SMDV/RMDV with weight w_o; T_R does the
    reverse.
- **There is no direct nose-to-readout path in M2.** v1's direct path let M2 pass without its
  ring (Astra). The direct path is M0.

### M1: M2 without the shifters and the turn copy (30 neurons)

Used in Stage A only, as an ablation (both reviewers).

### M0, the minimal core (4 neurons)

- NL → T_L and NR → T_R, with weight w_d.
- T_L and T_R inhibit each other: a flip-flop-like pair.
- The same push-pull output as M2.
- It asks whether the ring earns its neurons, and it connects to the owner's flip-flop idea for E4.
  A recurrent M0 is not automatically memoryless.

## Engine changes (AGENTS.md rules 7 and 9)

v1 claimed the graft needed no change to existing code. That is wrong for the GA (both reviewers):
`evolve_batch` hard-wires `initial_population` and `breed`, and `Genome.mutate` takes scalar
sigmas.

1. **The graft functions** (`wormwars/graft.py`, D140; done):
   - the extended connectome;
   - the seeded genome, with the background placed edge by edge;
   - the interface with the noses, and the module-only probes (`mean`, `swapped`).

   An inert graft is equivalent to the ungrafted brain **only up to rounding.** Adding rows
   regroups the floating-point sums: at most about 1.4 × 10⁻⁶ over 300 ticks on the CPU. The test
   tolerance is 10⁻⁵ over 100 ticks.
2. **Per-parameter mutation scales.**
   - `Genome.mutate` takes optional scale vectors for w, g, τ and bias. A scale of 0 pins a
     parameter.
   - Checks:
     - with no scales, the draws and results are bit-identical to the current `mutate`;
     - with scale vectors of ones, the same;
     - with a scale of 0, the pinned parameters never change over 50 mutations, including
       clamping;
     - a sabotage check: a mutate that ignores the scales fails the pinning test.
3. **Hooks in `evolve_batch`:** an optional `initial(run_spec) -> Genome` and optional mutation
   scales, both defaulting to the current behaviour.
   - Check: with the defaults, E2's GA batch reproduces E2's committed best-genome hashes for
     generations 0-25, on the GPU, at E2's batch composition (8 runs × 32 strains × 8 worlds).
     This costs about 2 minutes.
4. **The initial populations are drawn on N2, then embedded** (both reviewers).
   - `Genome.random` on an extended spec normalises by the mean over all edges and consumes the
     generator differently.
   - So each run's background is 04a's `initial_population(N2 spec, run seed)`, placed by
     `seeded_genome`.
   - B1, B3, B5 and B6 therefore share backgrounds run by run. A test checks that the worm block
     equals the N2 draw exactly.
   - B4 embeds 04a run 2's genome, loaded by `load_genome` on N2 (which checks its label and edge
     hash).
5. **Tolerances, declared now:**
   - CPU trajectory: ≤ 10⁻⁵ over 100 ticks (tested).
   - CUDA: ≤ 10⁻⁴ in the 302 neurons' state over 300 ticks, at the real batch shapes: training (8
     runs × 32 strains × 8 worlds) and single-champion evaluation.
   - Score level: an inert graft on 32 random N2 genomes and on 04a run 2, over 256 worlds.
     - Each genome's mean count must lie within ±0.05 of the ungrafted mean.
     - The share of worlds with identical counts is reported.

   Exactness across compositions is not claimed (rule 6).
6. **The hygiene guard is extended before any E4s genome is committed** (Fable).
   - `tests/test_publication_hygiene.py` keys on 302 and on known graph labels, so it would pass an
     E4s file silently.
   - It will also check:
     - the worm block of any genome whose label starts with a known graph plus "+";
     - any square matrix whose side is larger than 302 and whose leading 302 × 302 block is
       non-zero.
   - Sabotage check: a committed test fixture with an embedded anatomical block must fail.
7. **Tests for the probes and cuts** (Astra):
   - the module probes change only the noses' currents; the native sensors' currents are
     unchanged;
   - B3's cut outputs remain exactly zero after mutation and clamping;
   - a lesioned module neuron emits zero.

   Each gets a sabotage check.

## Stage A: the module works on its own (a positive control, as E1 was)

### The carrier (both reviewers' first must-fix)

With the 302 worm neurons silent, the forward command is zero, and the wey cannot move. Every Stage
A controller therefore runs on the same declared **carrier**:
- **The worm's weights, conductances and biases are zero, except for two parts.**
  - A forward drive: a bias b_f on AVBL/R and PVCL/R. The forward command is 2·tanh(b_f), clamped.
  - A turn bias: a bias b_t on the dorsal turn neurons against the ventral ones. It is the search
    turn, as E1's turn bias 0.2 was.
- **Every turn neuron's τ is fixed at 1 tick,** a motor relay.

M0, M1 and M2 get the same carrier grid.

### Tuning (staged and bounded; the grid is registered)

1. **A0, open loop** (the brain alone, no world). Choose the ring's regime across the bifurcation,
   from a grid of:
   - w_e ∈ {0.5, 1.0, 1.5, 2.0, 2.5, 3.0};
   - w_i ∈ {−0.5, −1, −1.5, −2, −3};
   - the ring's τ ∈ {1, 3};
   - the ring's bias ∈ {−1, −0.5, 0}.

   A configuration **qualifies** if it passes all four component checks:
   - **bump formation:** for L and R at common levels 0.02, 0.08 and 0.25 with δ = ±0.01, a single
     peak forms, and its contrast (peak minus the column mean, in tanh) exceeds 0.3;
   - **correct side:** the peak lies in the stronger nose's hemifield, for both signs of δ;
   - **persistence:** after the scent is removed, the peak stays within one column and above 0.3
     contrast for at least 20 ticks;
   - **no spontaneous bump:** zero input from a zero state forms no peak.
2. **A0, shifters.** Impose a turn command on the carrier's turn neurons, with the scent removed,
   in both directions and at three rates (turn command 0.25, 0.5 and 1).
   - Choose the shifter gain from {0.5, 1, 1.5, 2, 3} so that the bump moves opposite to the turn,
     by one column per 45° of executed heading change, within one column over a 180° turn.
   - This calibrates the approximate internal command against the actual 0.30 × turn and its
     delay.
3. **A1, closed loop, on 128 tuning worlds.** Every A0-qualified ring (at most the best 20, by
   bump contrast), crossed with:
   - b_f giving forward commands of {0.5, 0.75, 1.0};
   - b_t giving turn commands of {0, 0.1, 0.2};
   - φ ∈ {30°, 60°, 80°};
   - the nose weight a ∈ {0.75, 1.5, 3};
   - the readout weight ∈ {1, 2, 3};
   - the T mutual inhibition ∈ {−1, −2, −3};
   - w_o ∈ {1, 2, 3}.

   The best 5% are re-scored on 512 tuning worlds, and the best mean is chosen, as E1 chose.
   - M0 gets the same A1 grid, with w_d in place of the ring's parameters.
   - M1 gets M2's chosen values, without the shifters.
4. **Tested inside tuning:** the scent absent and weak, a sign reversal (the scent moved to the
   other side), and relocation. Task N's worlds relocate the source.

### The gate (on 1 024 fresh gate worlds; registered)

- **G1:** M2's Task N mean has a 95% lower bound, over worlds, of at least 5.0 targets per episode
  (M-avg 2.20; S-const k = 32 scores 5.63).
- **G2:** M2 meets E2d's "uses" criterion under the module probes: both paired contrasts (real −
  module mean, real − module swapped) have 95% lower bounds above 0.5.
- **G3:** the chosen M2 passes the four A0 component checks and the shifter check, at its tuned
  values, on the carrier.

If M2 fails any of them, E4s stops for a redesign (a new design version, reviewed) before any
evolution.

**M0 needs the same G1 and G2 before B2 runs.** If M0 fails, B2 is not run, and that is reported
(Astra: M0 must show competence before "the ring earns its neurons" can be read).

**Reported, not gating:**
- M0, M1 and M2 on the gate worlds, and each under the world's probes;
- **a cue-off probe:** the scent is hidden for 10 or 30 ticks, then returned. The measures are the
  heading error when it returns, and the score. This is Astra's controlled memory probe, in place of
  `hold`;
- **mutational robustness:** 256 mutants of the tuned M2 on the carrier, at 0.25× and at 1× 02's
  scales; the median child's score as a share of the parent's (see Mutation).

### The generation-0 graft measurement (Fable; reported, and it frames Stage B's reading)

Random N2 backgrounds move at about 0.2 of full speed, carry random turn biases, and give their turn
neurons τ drawn log-uniformly over 0.5-20 ticks. So the carrier does not stand for B1's start.
- **Before Stage B,** on B1's actual generation-0 backgrounds (16 runs × 32 = 512 genomes) and on
  04a run 2, measured on 256 worlds:
  - M2 grafted, M2 with no added module output (B3's form), and the ungrafted genome;
  - Task N means, the module probes, the forward command, the turn bias, and each turn neuron's
    saturation.
- **Stated in advance:** if the median B1 run's generation-0 best does not meet "uses" under the
  module probes, then Stage B's retention question becomes an integration question: whether
  evolution comes to use the module, not whether it keeps it. The outcome classes below are read in
  that wording.

## Stage B: evolution settles the graft (confirmatory)

### The optimizer

02's GA as E2 kept it (04a's `evolve_batch`, population 32, 3 elites, truncation 8, 8 worlds per strain), for 1 000
generations, on Task N, unshaped. Checkpoints come every 25 generations, as in E2.

### Mutation, and who owns which parameters

- **The module owns:**
  - its neurons' τ and bias;
  - every edge with a module neuron at either end, including the output edges onto the turn neurons
    and the turn-copy edges from them.
- **The module mutates at 0.25× 02's scales:** w 0.02, g 0.01, log-τ 0.0375, bias 0.0125.
- **The worm's parameters mutate at 02's scales.**
- **The 0.25× factor is a choice, not an optimum:** neither E2d nor the literature establishes it.
  B5 tests 1×.
- **A registered fallback:** if, in Stage A's robustness check, the median child at 0.25× keeps
  less than half its parent's score, the module's factor becomes 0.125× before Stage B.
- The interface gains are fixed; they are not evolvable.

### Arms

| Arm | Generation 0 | Module mutation | Runs | Role |
|---|---|---|---|---|
| **B1** (main) | M2 grafted onto random N2 (drawn on N2, embedded) | 0.25× | 16 | Does evolution keep, integrate or erode a working stereo module? |
| **B3** (control) | B1's genomes, with the module's output edges at 0 and pinned (scale 0): **no added module output** | 0.25× | 16, paired with B1 | Same neurons, parameters and noise stream, no route to the motors |
| B2 | M0 on B1's backgrounds | 0.25× | 8 | The ring against the minimal core (only if M0 passes its gate) |
| B4 | M2 on 04a run 2: 32 identical copies at generation 0 | 0.25× | 8 | A case study of merging with an existing non-stereo navigator, closest to E4's gluing |
| B5 | as B1 (its runs 1-8) | 1× (02's scale) | 8 | Whether the mutation scale sets the erosion rate |
| B6 | as B1 (its runs 1-8) | 0 (the module frozen) | 8 | Attribution: does freeing the module help? |

- **Registered, confirmatory:** B1 against B3.
- **Descriptive:** B2, B4, B5 and B6.
- **B3 is not a pure neutral-drift null.** Its module is inherited under selection on the
  background, hitchhiking included. B1 and B3 share each run's seed, and so its backgrounds and
  first noise draws. Their lineages diverge through selection.
- **Logged for every lineage:** the mutation counts per parameter block.

### Measures (on a fresh hold-out of 1 024 worlds; each genome is one strain on all of them)

For each run, both of:
- **F, the final generation's best** (the registered reading; Fable: E2's champion rule, the best
  validation checkpoint, can pick generation 0 and hide erosion);
- **C, the champion,** read beside F.

**On F and C:**
- the mean count;
- the module probes (module mean, module swapped) and the world's probes (mean, swapped), each
  classified by E2d's criterion;
- the module-lesion cost: the score with every module neuron silenced (`Brain.silence`), against
  intact;
- the reset-to-seed probe: F with the module's parameters reset to their generation-0 values;
- the transplant probe: F's module on Stage A's carrier. Did the module's own function survive, or
  did the worm take over?

**Along training (Astra):**
- At generations 0, 100, 250, 500, 750 and 999, on 256 worlds: the best-of-generation's module
  probes, its lesion cost, and the distance of the module's parameters from their seed.
- On the final population (all 32 strains, 256 worlds): real against module mean.

**Stage A's frozen controller** (M2 on the carrier) is scored on the same 1 024 hold-out worlds.

### Registered outcomes (proposed; fixed in the pre-registration)

**O1 (usefulness), B1 against B3, paired by run:**
- The measure is the difference in F's hold-out mean, over 16 runs. We report a 90% bootstrap
  interval over runs, and a sign-flip p, as E2d did.
- **"Supports: the module's output improves the evolved brain"** if the interval's lower bound
  exceeds 0 **and** the median difference is at least 0.5.
- **"Does not support"** if the interval's upper bound is below 0.5.
- **"Inconclusive"** otherwise.

**O2 (retention or integration), B1's runs classified by F, exclusively:**
- **kept:** F meets E2d's "uses" criterion under the module probes (both 95% lower bounds above
  0.5);
- **eroded:** F falls in E2d's "no material benefit" class under the module probes;
- **unclear:** otherwise;
- **not read:** the run did not complete.

**The reading:**
- **"kept"** if at least 12 of 16 runs are kept. Against a 50% null, the one-sided binomial
  p is 0.038.
- **"eroded"** if at least 12 of 16 are eroded.
- **"mixed"** otherwise.

It is worded "integrated" in place of "kept" if the generation-0 measurement triggered the
integration wording.

**Interpreting O2 (reported, not classified):**
- the lesion cost, the reset-to-seed probe and the transplant probe separate lost function from
  reduced dependence, or a transfer into the worm (Astra);
- a falling lesion cost alone is not read as erosion.

**O3 (beyond the module), descriptive:**
- B1's F against Stage A's frozen controller, on the same worlds, with an interval;
- B6 against B1 (does freeing the module help?).

**Transparency:** E2d's plateau is stated as the reason for E4s. If B1 erodes the module, or does not
beat B3, that is the result, in the wording fixed in advance.

## What E3 takes

E4s supplies two artefacts:
- Stage A's tuned module specification;
- B1's F genomes classified "kept", ranked by their validation mean.

E3's own design chooses between them. E4s does not.

## Worlds, seeds, budget

- **World ids:** new ranges for tuning, gate, training, validation and hold-out, disjoint from every
  earlier range (a test checks it).
- **Seeds:** new and disjoint. B5 and B6 reuse B1's runs 1-8 seeds, by design.
- **Budget:** estimated from E2's rate (8 runs of 1 000 generations in 1.35 h), times
  (332/302)² ≈ 1.21 for the dense matrices (Astra, Fable). The actual overhead is measured in the
  smoke.

  | Part | Estimate |
  |---|---|
  | Equivalence checks, smoke, projection | about 0.5 h |
  | Stage A (A0, A1, the gate, the generation-0 measurement) | about 1 h |
  | Stage B: 64 runs (8 batches of 8) | about 13 h |
  | Hold-out, probes, lesions, along-training and final populations | about 1.5 h |
  | **Total** | **about 16 h** |

- **Proposed: a cap of 30 GPU-hours** for this registration, with per-stage caps and the projection
  rule from E2. The rest of the owner's 96-hour ceiling is kept for pre-registered follow-ups: a
  memory task (`hold` once S-const has run under it) and the pruning study.
- **Guards:** E2's and E2d's stage frame: markers, the cap, reruns, not-completed records, and the
  replay checks.

## The roadmap

A dated amendment (the owner's decision, 2026-09-30):
- E4s is added ahead of plan, as a preliminary to E4's hand-building;
- the tripwire ("no new infrastructure before the minimal A/B organism") is relaxed for the graft
  functions and the GA hooks only;
- E2d's plateau and the absent stereo smell are stated as the reason.

## What E4s cannot show

- Anything about the real worm's steering; the design is fly-inspired engineering.
- That the ring represents a physical bearing (it encodes normalised lateral contrast).
- Whether other modules, tasks or optimizers would do better.
- The minimal circuit (the pruning study, later).
- "Improves" near Task N's ceiling. S-const reaches 8.78 against the oracle's 8.85, so improvement
  beyond a strong module cannot show there.
- Why the plateau exists: the gain probe is consistent with the gain hypothesis, but it does not
  test it.

## Changes from v1 (for the second review)

| v1 review item | v2 |
|---|---|
| The wey cannot move on a silent background (Fable 1, Astra 1) | The carrier: a declared forward drive, a turn bias, and turn-neuron τ fixed at 1, the same for every module |
| No generation-0 graft measurement (Fable 2, Astra 1) | Measured on B1's 512 generation-0 backgrounds and on 04a run 2; an integration wording fixed in advance |
| The champion rule hides erosion (Fable 3, Astra 7) | F, the final generation's best, is the registered reading, with C beside it; fixed-generation and final-population measures |
| Biased outcomes; "half the lesion cost" (Fable 4, Astra 7) | O1 with an interval and a test; O2's exclusive classes by E2d's criterion; lesion, reset-to-seed and transplant probes interpret it |
| The GA loop and mutation are not covered (Fable 5, Astra 8) | Per-parameter scales and `evolve_batch` hooks, bit-identity checks, and E2's generation 0-25 hashes |
| Initialisation on the extended spec (Fable 6, Astra 6) | Drawn on N2, then embedded; B4 through `load_genome` |
| B3 undefined, and its outputs regrow (Fable 7, Astra 6) | Outputs pinned at scale 0, the same parameterisation and noise stream; "no added module output"; mutation counts logged |
| The gain ≥ 32 gate (Fable 8, Astra 3 and 5) | Dropped. The probe now takes a small-signal central difference, a curve, a transient, a carried-state reversal and saturation |
| Text against E2d's corrections (Fable 9, Astra 5) | "All near 2.2" → 35 of 47; "temporal route" removed; "supports" → "consistent with" (here and in D139, by dated correction in D141) |
| "Exactly on the CPU" (Fable 10, Astra 8) | Tolerances declared (CPU, CUDA, score level); rounding-level equivalence stated (D140) |
| The hygiene guard (Fable 11) | Extended, with a sabotage fixture, before any E4s genome is committed |
| The nose gain (Fable 12, Astra) | Fixed at 1.0, untuned |
| The bearing and turn-copy argument (Astra 2) | ψ is an odour-side estimate, not a bearing; the copy reads the executed command's neurons and is calibrated against 0.30 × turn, both directions, three rates |
| The gate tests the ring (Astra 3) | No direct path in M2; component checks gate; M0 has its own gate; M1 is a Stage A ablation |
| Tuning dimensions (Astra 4) | Forward drive, turn bias, recurrence, inhibition, τ, bias, shifter gain, φ, nose, readout, mutual-inhibition and output weights, staged and bounded |
| Suggestions taken | 16 runs for B1/B3; B5 (1× scale); B6 (frozen module); B4 as a case study of 32 copies; `hold` out, cue-off in; mutational robustness with a fallback; budget ×1.21; biology wording; which artefact E3 takes |
| Suggestion not taken | Optimising N2's open-loop gain by gradient (Fable): a useful diagnostic of gain against topology, but a separate question. Proposed as a follow-up within the ceiling |
