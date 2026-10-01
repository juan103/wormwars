# E4s: a hand-built stereo module grafted onto N2 (design v3)

> **Superseded, 2026-10-01 (D143).** This design was not sent for review. It is kept for the record,
> and its engineering parts are reused by E4s-1 (`docs/E4s/ROADMAP-PROPOSAL.md`). Three corrections:
> - "A deep research by Claude Sonnet 5.5" (below, and in D139): it was a single CLI session whose
>   sources were mostly search snippets, and nobody checked its claims. It was not a deep research.
>   A real literature review followed (`docs/reviews/20261001-literature-review/`).
> - "The world's turn is clamp(2·[mean tanh(dorsal) − mean tanh(ventral)])": the factor is 1, not 2
>   (0.5 × `turn_gain` 2.0; `world.py`), so gain estimates built on it halve (Fable, D143).
> - The ring is deferred: the literature review and both reviewers found it unnecessary for Task N.

Status: design v3 for a third review by Astra 6 and Fable 5.1, 2026-09-30. Nothing has run on
E4s's worlds or seeds. The exploratory, design-informing measurements are disclosed below. A
pre-registration follows only if both reviewers agree.

**Earlier versions:**
- v1 (commit 3557a2a, D139): both reviewers said "revise"
  (`docs/reviews/20260930-014518-E4s-design/`, D141).
- v2 (commit 68812ac, D141): Fable said "proceed to pre-registration", conditionally; Astra said
  "revise" (`docs/reviews/20260930-020427-E4s-design-v2/`, D142).

What changed, and why, is in the last section.

## Why, and why now (the owner's direction, 2026-09-30)

- **Evolution has not found stereo smell.** E2 and its diagnosis E2d (published) found what E2d
  calls a **"non-stereo plateau"**.
  - No champion among E2's and 04a's 47 distinct champions meets E2d's "uses the left-right
    difference" criterion.
  - 43 show no material benefit from intact bilateral input. 4 are unclear, with small, detectable
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
  estimate of about 19 (see Budget).

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
   - **Not found by the report's search:**
     - a published model that anchors a ring on a bilateral *chemical* difference;
     - published work that grafts a designed module into a connectome-constrained network and
       follows its fate under evolution.
   - **Biology, stated plainly:** the real worm steers by comparing the scent over time as its head
     sweeps (klinotaxis; for example Izquierdo and Lockery), not by comparing two noses a few
     micrometres apart. The report's figure of about 8 µm is not verified.
     - Stereo here is a design choice, fly-inspired engineering, not worm-faithful.
     - The readout is a hemifield sum inspired by PFL3, not a faithful port: the fly's model
       combines heading, a goal input and nonlinear responses.
     - The interface already says its mappings are modelling choices.
2. **The signal is small.** The left-right difference at the sensors is about 0.004-0.017 in
   injected current, against a common level of about 0.02-0.25, with a peak of 0.35. The reviewers
   re-derived this: the report's table is approximate and omits the forward-offset correction.
   E1's scripted stereo steerer, turn = bias + k(L − R), scores:

   | k | 4 | 32 | 256 | 8192 |
   |---|---|---|---|---|
   | score, turn bias 0.2 | 2.38 | 5.63 | 8.51 | 8.78 |

   At zero bias, k = 32 scores 4.23.
3. **An open-loop probe of the champions** (exploratory and design-informing; not a registered
   measure). The script is `scripts/e4s_gain_probe.py`, v3; its output is
   `experiments/E4s-stereo-module/development-records/gain-probe.json`.
   - **Method:** each of the 47 distinct champions receives fixed scent currents at its left and
     right sensory neurons (common level 0.02, 0.08 and 0.25), with every other input at zero. The
     turn command is read as the world reads it. Measured:
     - **the small-signal gain:** a central difference at δ = ±0.001, from a zero start, after 40
       ticks, averaged over the last 10;
     - **a signed response curve,** δ from −0.1 to +0.1;
     - **the step response, against a control:** after 40 ticks at δ = 0, a step to +0.01 against
       staying at 0;
     - **a carried-state reversal, against a control:** after 40 ticks at +0.01, switching to −0.01
       against staying at +0.01, expressed as a gain;
     - **the history effect:** the switched arm against a zero start at −0.01;
     - **each turn neuron's activity** at δ = 0.

     v1's least-squares slope is dropped: it capped at 66.7 even for an ideal clipped k = 256.
     v2's transient and reversal had no unchanged-input control, so they also measured drift (Fable,
     D142).
   - **Result:**
     - the median |small-signal gain| is 0.098, and the maximum 0.68;
     - the carried-state gain is similar: median 0.096, maximum 1.60;
     - the median largest step response, against its control, is 0.0012;
     - the history effect has a median of 0.033 and a maximum of 0.33. This mixes history with slow
       settling, which the probe does not separate;
     - on average 4.8% of the turn neurons are saturated at δ = 0.
   - **What it shows:** a weak differential response under these conditions (static, other inputs
     zero).
   - **What it does not show:**
     - whether the plateau comes from gain or from topology;
     - that the champions use a temporal route;
     - anything about latching.

     Low gain is what a non-stereo controller looks like under either reading. So the result is
     consistent with the report's gain hypothesis, not evidence for it (a correction to v1 and to
     D139, in D141).
   - **Not added to the probe, from Astra's v1 list:** collision-context inputs, individual motor
     derivatives, and an accounting record. The inference is narrowed instead. The probe runs on the
     CPU in seconds.

## The modules

Every module is appended to N2's 302 neurons as named extra neurons ("E4S_…"), through
`wormwars/graft.py` (D140).
- **Designed synapses** are new chemical edges with an anatomical weight of 1. Their signed weights
  live in `Genome.w`. Dale's law is off, and a graft refuses it.
- **Synapse direction:** pre → post. A module synapse onto SMDDL drives SMDDL. This was checked by
  simulation; a test in `tests/test_graft.py` pins it before the pre-registration.
- **Noses** use the worm's own interface gain of 1.0, which is not tuned. All gain comes from
  synaptic weights within the genome's bounds: w ∈ [−3, 3], τ ∈ [0.5, 20], bias ∈ [−2, 2].
- **Turn sign:** a positive turn command steers toward the left sensor, as S-const's k > 0 does.
  - So a "left" readout excites the dorsal turn neurons (SMDD, RMDD) and inhibits the ventral ones
    (SMDV, RMDV).
  - Positive ring angles are to the left.
  - The world's turn is clamp(2·[mean tanh(dorsal) − mean tanh(ventral)]); the heading changes by
    0.30 × turn per tick.
- **Signed activity:** neurons emit tanh(v), which is signed. A neuron at rest with a negative bias
  sends a constant negative drive to its targets. Every design choice below keeps such constant
  drives uniform around the ring, so they act as a common bias, not a direction.

### M2, the ring (the owner's design; 32 neurons; 334 in total)

Every parameter is pinned here. The names in *italics* are the tuned ones (Stage A); the rest are
fixed.

| Part | Neurons | Inputs (weight) | τ | bias |
|---|---|---|---|---|
| Noses | NL, NR | the interface's `food_left` / `food_right`, gain 1 | 0.5 | 0 |
| Ring | E0-E7, at θᵢ = −157.5° + 45°·i (positive = left) | NL: *a*·c(θᵢ − *φ*); NR: *a*·c(θᵢ + *φ*); Eᵢ±1: *w_e*; Δa, Δb: *w_i*; Pᴸᵢ₊₁ and Pᴿᵢ₋₁: 1 | *τ_E* | *b_E* |
| Global inhibition | Δa, Δb | every Eᵢ: 0.5 | 0.5 | 0 |
| Turn copy | TC_L, TC_R | TC_L: +0.5 from each dorsal and −0.5 from each ventral turn neuron; TC_R the reverse | 0.5 | 0 |
| Shifters | Pᴸᵢ, Pᴿᵢ (i = 0…7; indices modulo 8) | Pᴸᵢ: Eᵢ 1, TC_L *s*; Pᴿᵢ: Eᵢ 1, TC_R *s* | 0.5 | −1 |
| Readout | T_L, T_R | T_L: E4-E7 at *r*; T_R: E0-E3 at *r*; each other: *m* | 0.5 | 0 |
| Outputs | (worm) | T_L → SMDD*, RMDD* at +*w_o*, → SMDV*, RMDV* at −*w_o*; T_R the reverse | — | — |

- **The nose weights:** c(x) is cos x, or max(0, cos x) (both are Stage A options; Fable). They
  are indexed so that NL feeds the left-side columns.
- **The shifters:**
  - An egocentric odour estimate must move *opposite* to the turn. When the wey turns left, a fixed
    source moves to its right, to lower θ.
  - So Pᴸᵢ, gated by the left-turn copy TC_L, projects to Eᵢ₋₁ (to the right). Pᴿᵢ, gated by TC_R,
    projects to Eᵢ₊₁.
  - This is v2's direction, which Fable checked. v2 called these P⁺ and P⁻.
  - At rest, every column receives exactly one Pᴸ and one Pᴿ input at the same resting output, so
    the resting drive is uniform.
- **What the ring encodes (Astra):**
  - The bump sits at about tan ψ = [(L − R)/(L + R)]·tan φ.
  - For the Gaussian scent, that is the normalised lateral contrast, not the smell's physical
    bearing independent of distance.
  - We call ψ **the odour-side estimate**.
  - The shifters make it **a heuristic rotating memory:** its usefulness is tested behaviourally
    (the cue-off probes), not claimed as bearing-accurate.
- **The turn copy** reads the same eight turn neurons as the world's readout, so it includes the
  background's contribution. It is not the executed turn: the world clamps the command and scales it
  by 0.30. It is an approximate internal command.
- **There is no direct nose-to-readout path in M2** (Astra: v1's let M2 pass without its ring).

### M1: M2 without the shifters and the turn copy (14 neurons)

NL, NR, E0-E7, Δa, Δb, T_L and T_R, with M2's values. It is a Stage A ablation (both reviewers),
and the pre-stated fallback module (see the shifter check).

### M0, the minimal core (4 neurons)

- NL → T_L and NR → T_R at *w_d*.
- T_L and T_R inhibit each other at *m*: a flip-flop-like pair.
- The same outputs as M2.
- τ is 0.5 and the bias 0.

It asks whether the ring earns its neurons, and it connects to the owner's flip-flop idea for E4.
A recurrent M0 is not automatically memoryless.

### The feedforward control: M2 with *w_e* = *w_i* = 0

A Stage A control (Fable): M2 has more stages than M0, so it could win on feedforward gain alone.

## Engine changes (AGENTS.md rules 7 and 9)

v1 claimed the graft needed no change to existing code. That was wrong for the GA (both reviewers).
All items below have been implemented, test-first and sabotage-checked, except the CUDA and
score-level checks, which run in the smoke (D142).

1. **The graft functions** (`wormwars/graft.py`, D140):
   - the extended connectome;
   - the seeded genome, with the background placed edge by edge and built through `with_params`;
   - Dale's law refused;
   - the interface with the noses, and the module-only probes (`mean`, `swapped`).

   An inert graft is equivalent to the ungrafted brain **only up to rounding.** Adding rows
   regroups the floating-point sums: at most about 1.4 × 10⁻⁶ over 300 ticks on the CPU.
2. **Per-parameter mutation scales** in `Genome.mutate`. A scale of 0 pins a parameter.
   - Tests: no scales and scale vectors of ones are bit-identical to the plain mutation; a scale
     multiplies the perturbation; a zero scale pins its parameters over 50 mutations; wrong shapes
     are refused.
   - Sabotage checks: ignoring the scales, and changing the random stream.
3. **Hooks in `evolve_batch`:** `initial(run_spec)` and `mutation_scales(run_spec)`, both
   defaulting to the current behaviour.
   - Tests: hooks restating the defaults change no hash; the initial hook sets generation 0; the
     scales reach every mutation; a population of the wrong size is refused.
   - Sabotage checks: ignoring each hook.
   - **The GPU check** (`scripts/e4s_equivalence.py`): with the defaults, E2's GA batch reproduces
     E2's committed best-genome hashes for generations 0-25, on the GPU, at E2's composition (8 runs
     × 32 strains × 8 worlds). It runs three ways: the defaults, the restated hooks, and scale
     vectors of ones.
   - **If it fails,** the previous commit is run in a separate worktree in the same session, to
     separate an engine change from environment drift (Fable), before anything else runs.
4. **The initial populations are drawn on N2, then embedded** (both reviewers).
   - Each run's background is 04a's `initial_population(N2 spec, run seed)`, placed by
     `seeded_genome`. So B1, B3, B5 and B6 share backgrounds run by run.
   - A test checks that the worm block equals the N2 draw exactly.
   - B4 embeds 04a run 2's genome, loaded by `load_genome` on N2 (which checks its label and edge
     hash).
5. **Tolerances, declared now:**
   - **CPU trajectory:** ≤ 10⁻⁵ over 100 ticks (tested).
   - **CUDA:** ≤ 10⁻⁴ in the 302 neurons' state over 300 ticks. The shapes are the real ones:
     training (8 runs × 32 strains × 8 worlds) and single-genome evaluation. The genomes are 32
     random N2 genomes and 04a's 16 champions, each with an inert M2.
   - **Score level:** the same 48 genomes, inert-grafted against ungrafted, on 256 worlds.
     - Each genome's mean must lie within ±0.05.
     - The share of worlds with identical counts is reported.
     - The 16 champions make the check able to fail: random genomes score about 0.03 (Fable).
   - **A genome that fails either check stops E4s** before Stage B, for diagnosis. It is not
     excluded silently.
   - Exactness across compositions is not claimed (rule 6).
6. **The hygiene guard** (`tests/test_publication_hygiene.py`; Fable) now also checks grafted
   genomes. Genome labels have the form "<graph>+<module>".
   - Modules whose genomes may be saved are registered in `wormwars.graft.MODULES`. An unregistered
     grafted label is itself an offence.
   - The worm block is extracted by edge identity (`graft.worm_parameters`), because turn-copy edges
     interleave with the worm's chemical edges (Astra).
   - A square matrix wider than 302 neurons is flagged as structure.
   - **Its sabotage check builds the offending genome in memory,** from the fetched connectome,
     during the test. **No anatomical fixture is committed** (Astra: that would break rule 1).
     Disabling the worm-block extraction makes the test fail. The first version of the test did not
     fail under that break: the toy module has no gap junctions, so `g` fired anyway. It now requires
     the offence on `w`.
7. **Tests for the probes and cuts** (Astra), each with a sabotage check, before the
   pre-registration:
   - the module probes change only the noses' currents; the native sensors' currents are unchanged;
   - B3's cut outputs remain exactly zero after mutation and clamping;
   - a lesioned module neuron emits zero.

## Stage A: the module works on its own (a positive control, as E1 was)

### The carrier (both reviewers' v1 must-fix)

With the 302 worm neurons silent, the forward command is zero, and the wey cannot move. Every Stage
A controller therefore runs on the same declared **carrier**:
- **The worm's weights, conductances and biases are zero, except for two parts.**
  - **A forward drive:** a bias b_f on AVBL/R and PVCL/R. The forward command is 2·tanh(b_f),
    clamped.
  - **A turn bias:** a bias b_t on the dorsal turn neurons, and −b_t on the ventral ones. It is the
    search turn, as E1's turn bias 0.2 was.
- **Every worm neuron's τ is 1 tick,** so the turn neurons are motor relays.

M0, M1, M2 and the feedforward control share the carrier grid.

### A0: component checks (open loop: the brain alone, no world; cheap)

The checks run with the carrier's turn bias at 0. Fable: with a turn bias, calibrated shifters must
move the bump, so persistence would contradict them.

**Grid:**
- the ring: *w_e* ∈ {0.5, 1, 1.5, 2, 2.5, 3}, *w_i* ∈ {−0.5, −1, −1.5, −2, −3}, *τ_E* ∈ {0.5, 1,
  3}, *b_E* ∈ {−1, −0.5, 0};
- the noses: *a* ∈ {0.75, 1.5, 3}, *φ* ∈ {30°, 60°, 80°}, rectified or not.

That is 4 860 candidates. The checks apply to each candidate at its own nose values (Fable). The
readout does not feed the ring when the turn is 0, so it is not part of A0.

**The bump.**
- Its position is the circular mean of the columns' tanh activity, weighted by activity above the
  column mean.
- Its contrast is the peak minus the column mean.
- A single peak means one contiguous run of above-mean columns.

**Inputs.** Common levels 0.02, 0.08, 0.25 and 0.35 (the peak), and δ ∈ {±0.004, ±0.01} (Fable).
Each check runs for 60 ticks, and reads the mean over the last 10.

**A candidate qualifies if all five checks pass:**
1. **Formation:** a single peak, with contrast above 0.3, at every input.
2. **Correct side, from a zero start:** the peak lies in the stronger nose's hemifield, for both
   signs of δ, at every level.
3. **Correct side, from a carried state** (Fable, Astra):
   - after 60 ticks at +δ, the input switches to −δ;
   - the peak crosses to the other hemifield within 30 ticks;
   - at δ = ±0.01 and every level.
4. **Persistence:** after the scent is removed (turn 0), the peak stays within one column, with
   contrast above 0.3, for at least 20 ticks.
5. **No spontaneous bump** (Fable: from an exact zero state, a symmetric ring stays symmetric even
   when unstable):
   - zero input, from a state perturbed by Gaussian noise of σ = 10⁻³ (a fixed seed);
   - 100 ticks;
   - no peak with contrast above 0.3.

   A sabotage check: a ring built to be unstable must fail it.

Checks 3 and 4 pull in opposite directions: a ring that latches fails check 3, and a ring that
forgets fails check 4. **If no candidate passes all five, E4s stops for a redesign.**

### A0: the shifter check (M2 only)

Each qualified ring is tested with *s* ∈ {0.5, 1, 2, 3}.
- The input: a bump formed as in check 1, then the scent removed.
- The imposed turn commands: 0, ±0.25, ±0.5 and ±1, through the carrier's turn bias.
- Also (Astra) a background turn: the same turn commands imposed while the scent is present.

**A value of *s* passes if:**
- at turn 0, the bump is stable as in check 4;
- the bump moves opposite to the imposed turn, in both directions;
- it moves further at a larger turn (monotone over 0.25, 0.5 and 1);
- no shifter neuron is saturated (|tanh| > 0.99) at turn 0.

There is no rate target. v2's one-column-per-45° calibration treated ψ as a bearing (Astra).
Instead, *s* is chosen in closed loop, and the memory's usefulness is read from the cue-off probes.

**Pre-stated fallback (Fable):** if no *s* passes for any qualified ring, M1 becomes the module for
Stage B, and the shifters are reported as not working.

### A1: closed loop (on tuning worlds; the grid is registered)

1. **A1a** (128 tuning worlds, the carrier at forward 1.0 and turn 0.1):
   - the qualified rings (all of them, or a sample of 40 stratified by contrast quartile if more
     qualify; Fable: "best by contrast" would select the deepest attractors);
   - × their passing values of *s* (at most 3, the smallest);
   - × *r* ∈ {1, 2};
   - × *m* ∈ {−1, −2, −3};
   - × *w_o* ∈ {1, 2, 3}.

   That is at most 40 × 3 × 18 = 2 160 candidates.
2. **A1b:** the best 5% of A1a × the carrier grid: forward ∈ {0.5, 0.75, 1.0} × turn ∈ {0, 0.1,
   0.2}, on 128 worlds.
3. **A1c:** the best 10 of A1b, re-scored on 512 new tuning worlds. The best mean is chosen.

Ties go to the first in the grid order.
- **M0** gets A1a-A1c with *w_d* ∈ {1, 2, 3} in place of the ring and shifter parameters.
- **M1** takes M2's chosen values, without the shifters.
- **The feedforward control** takes M2's chosen values, with *w_e* = *w_i* = 0.

### The freeze

After A1, the chosen modules' definitions (every value) are written to a module file. Its hash is
committed and pushed **before the gate runs.**

### The gate (on 1 024 fresh gate worlds; registered)

**G1:** M2's Task N mean has a lower bound of at least 5.0 targets per episode.
- The bound is the 95% percentile bootstrap over worlds, with 10 000 resamples and a fixed seed.
- For reference: M-avg scores 2.20, and S-const k = 32 scores 5.63.

**G2:** M2 meets E2d's "uses" criterion under the module probes.
- The paired contrasts are real − module mean and real − module swapped.
- Both need 95% lower bounds above 0.5, by the interval method E2d registered.

**G3:** at its frozen values, the chosen M2 passes the five A0 checks and (unless the fallback
applies) the shifter check.

**If M2 fails any of them,** E4s stops for a redesign (a new, reviewed design version) before any
evolution.

**M0 needs G1 and G2 before B2 runs.** If M0 fails, B2 is not run, and that is reported.
- Fable estimates M0's feedforward gain at k ≈ 11-18, so it may fail.
- Astra: M0 must show competence before "the ring earns its neurons" can be read.

**Reported, not gating:**
- M0, M1, M2 and the feedforward control on the gate worlds, each under the world's probes and the
  module probes.
- **Cue-off and reacquisition probes** (Astra), on a fixed source:
  - the source is placed at distances of 2, 4 and 8 cells, and bearings of ±30°, ±60° and ±120°;
  - the scent is shown for 20 ticks, then hidden for 10 or 30 ticks, then shown again;
  - measured: the heading change during the gap, and the ticks until the heading error falls below
    30° after the scent returns;
  - for M0, M1 and M2.

  This is the behavioural test of the rotating memory.
- **Mutational robustness,** on the carrier:
  - only the module's parameters mutate; the carrier is fixed (Fable);
  - 256 mutants of the frozen M2 at each of 0.125×, 0.25× and 1× 02's scales;
  - 64 robustness worlds of their own;
  - measured: the median child's score as a share of the parent's.

### The generation-0 measurement (reported before Stage B)

Random N2 backgrounds move at about 0.2 of full speed, carry random turn biases, and give their turn
neurons τ drawn log-uniformly over 0.5-20 ticks. So the carrier does not stand for B1's start
(Fable).
- **The genomes:** B1's 512 generation-0 backgrounds (16 runs × 32) and 04a run 2.
- **The worlds:** 256, with their own id range.
- **Three forms each:** M2 grafted; M2 with no added module output (B3's form); ungrafted.
- **Measured:** the Task N mean, the forward command, the turn bias, and each turn neuron's
  saturation.

It is descriptive. Each run's own generation-0 classification (below) is what the outcomes use.

## Stage B: evolution settles the graft (confirmatory)

### The optimizer

02's GA as E2 kept it: 04a's `evolve_batch`, population 32, 3 elites, truncation 8, 8 worlds per
strain.
- 1 000 generations, on Task N, unshaped.
- Checkpoints every 25 generations, as in E2.
- Runs go in batches of 8, in a registered order:
  1. B1 runs 1-8 with B3 runs 1-8;
  2. B1 runs 9-16 with B3 runs 9-16;
  3. B5; B6; B2; B4.

  So the confirmatory pairs finish first under the cap.

### Mutation, and who owns which parameters

- **The module owns:**
  - its neurons' τ and bias;
  - every edge with a module neuron at either end, including the output edges onto the turn neurons
    and the turn-copy edges from them.

  The module has no gap junctions.
- **The module mutates at 0.25× 02's scales:** w 0.02, log-τ 0.0375, bias 0.0125. The worm mutates
  at 02's scales.
- **The 0.25× factor is a choice, not an optimum:** neither E2d nor the literature establishes it.
  B5 tests 1×.
- **A registered fallback:** if, in the robustness check, the median child at 0.25× keeps less than
  half its parent's score, and at 0.125× keeps at least half, the module's factor becomes 0.125×.
  - It then applies to B1, B2, B3 and B4.
  - B5 stays at 1×, and B6 at 0.
- The interface gains are fixed; they are not evolvable.

### Arms

| Arm | Generation 0 | Module mutation | Runs | Role |
|---|---|---|---|---|
| **B1** (main) | M2 grafted onto random N2 (drawn on N2, embedded) | 0.25× | 16 | Does evolution retain, acquire or lose the stereo use? |
| **B3** (control) | B1's genomes, with the module's output edges at 0 and pinned (scale 0): **no added module output** | 0.25× | 16, paired with B1 by run | Same neurons, parameters and noise stream; no route to the motors |
| B2 | M0 on B1's backgrounds, runs 1-8 | 0.25× | 8 | The ring against the minimal core (only if M0 passes its gate) |
| B4 | M2 on 04a run 2: 32 identical copies at generation 0 | 0.25× | 8 | A case study of merging with an existing non-stereo navigator, closest to E4's gluing |
| B5 | as B1, runs 1-8 | 1× (02's scale) | 8 | Whether the mutation scale sets the loss rate |
| B6 | as B1, runs 1-8 | 0 (the module frozen) | 8 | Attribution: does freeing the module help? |

- **Registered, confirmatory:** B1 against B3.
- **Descriptive:** B2, B4, B5 and B6. Each pairs with B1's runs 1-8.
- **B3 is not a pure neutral-drift null.** Its module is inherited under selection on the
  background, hitchhiking included. B1 and B3 share each run's seed, and so its backgrounds and
  first noise draws. Their lineages diverge through selection.
- **Logged for every lineage:** the mutation counts per parameter block.

### Measures (on a fresh hold-out of 1 024 worlds; each genome is one strain on all of them)

For each run, both of:
- **F, the final generation's best:** the generation-999 strain with the highest training fitness,
  as `evolve_batch` logs it. This is the registered reading. Fable: E2's champion rule can pick
  generation 0 and hide a loss.
- **C, the champion** (the best validation checkpoint), read beside F.

And **G0, the generation-0 best:** the checkpoint-0 candidate, the generation-0 strain with the
highest training fitness.

**On F, C and G0:**
- the mean count;
- the module probes (module mean, module swapped) and the world's probes (mean, swapped), each
  classified by E2d's criterion;
- the module-lesion cost: the score with every module neuron silenced (`Brain.silence`), against
  intact.

**On F only:**
- the reset-to-seed probe: F with the module's parameters reset to their generation-0 values;
- the transplant probe: F's module on Stage A's carrier. Did the module's own function survive, or
  did the worm take over?

**Along training** (Astra):
- at generations 0, 100, 250, 500, 750 and 999, on 256 worlds: the best-of-generation's module
  probes, its lesion cost, and the distance of the module's parameters from their seed;
- on B1's final populations (all 32 strains, 256 worlds): real against module mean.

**Stage A's frozen controller** (M2 on the carrier) is scored on the same 1 024 hold-out worlds.

### Registered outcomes (proposed; fixed in the pre-registration)

**O1 (usefulness), B1 against B3, paired by run** (one estimand; the rules are ordered and
exclusive):
- **The estimand:** the mean over the 16 runs of the paired difference in F's hold-out mean,
  B1 − B3. It has a 90% percentile bootstrap interval over runs (10 000 resamples, a fixed seed).
- **The rules, in order:**
  1. **"Supports: the module's output improves the evolved brain"** if the interval's lower bound
     exceeds 0 and the estimate is at least 0.5.
  2. **"Does not support"** if the interval's upper bound is below 0.5.
  3. **"Inconclusive"** otherwise.
- The sign-flip p is reported beside it and does not enter the decision.
- **A sensitivity reading,** reported: without the pairs whose B3 generation-0 best scores zero on
  the hold-out, as E2d did for run 2.
- **Stated in advance:** if the graft works at generation 0, O1 is close to a manipulation check.
  The information is in O2.

**O2 (the stereo criterion over evolution), B1's runs, each classified by G0 and F:**

| G0 under the module probes | F under the module probes | Class |
|---|---|---|
| uses | uses | **retained** |
| uses | no material benefit | **lost** |
| not "uses" | uses | **acquired** |
| not "uses" | no material benefit | **never used** |
| any other combination (either "unclear") | | **unclear** |
| the run did not complete | | **not read** |

- **"Retained" means that the stereo criterion is kept, not that Stage A's performance is**
  (Astra).
- **"Lost" names what the probes show:** the module's nose difference no longer benefits F. It does
  not name why. Astra: redundancy, a transfer into the worm and lost function all read the same.
  The lesion, reset-to-seed and transplant probes are reported beside it to interpret it. A graft
  that never worked cannot be called lost.
- **The arm's reading:** "retained", "lost", "acquired" or "never used" if at least 12 of the 16
  runs fall in that class; otherwise "mixed". "Not read" runs count against every class. Against a
  50% null, 12 of 16 has a one-sided binomial p of 0.038. The four readings are descriptive labels,
  not four significance claims.

**O2b (performance retention), descriptive with registered bands:**
- Each B1 run's F hold-out mean, as a share of Stage A's frozen controller's (Fable).
- The bands are: at least 0.9; 0.5-0.9 ("partly"); below 0.5.

**O3 (beyond the module), descriptive:**
- B1's F against Stage A's frozen controller, with an interval;
- B6 against B1: does freeing the module help?

**Transparency:** E2d's plateau is stated as the reason for E4s. If B1 loses the stereo use, never
uses it, or does not beat B3, that is the result, in the wording fixed in advance.

## What E3 takes

E4s supplies two artefacts:
- Stage A's frozen module file;
- B1's F genomes classified "retained" or "acquired", ranked by their validation mean.

E3's own design chooses between them. E4s does not.

## Worlds, seeds, budget

- **World ids:** new ranges, disjoint from every earlier range and from each other (a test checks
  it):
  - A0 needs no worlds; tuning (A1a-A1b, then A1c); the gate; cue-off; robustness;
  - the generation-0 measurement; training; validation; the hold-out; along-training.
- **Seeds:** new and disjoint. B2, B5 and B6 reuse B1's runs 1-8 seeds, by design.
- **Budget:** estimated from E2's rate. E2's GA training was about 2.05 M episodes in 1.35 h, and
  the recorded rates are 434 to 1 027 episodes per second (Fable). Times (334/302)² ≈ 1.22 for the
  dense matrices (both). The actual overhead is measured in the smoke.

  | Part | Episodes | Estimate |
  |---|---|---|
  | Equivalence checks, smoke, projection | — | about 0.5 h |
  | A0 (open loop; brain only) | — | under 0.2 h |
  | A1 (a, b, c), the gate, cue-off, robustness | about 0.5 M | about 0.5 h |
  | The generation-0 measurement (513 × 3 forms × 256 worlds) | about 0.4 M | about 0.3 h |
  | Stage B: 64 runs, 8 batches of 8 | about 16 M | about 13.2 h |
  | Hold-out, probes, lesions, along-training, final populations | about 1.6 M | about 1.5-3 h |
  | **Total** | | **about 17-19 h** |

- **Proposed: a cap of 30 GPU-hours** for this registration, with per-stage caps:
  - Stage A: 3 h;
  - the generation-0 measurement: 1 h;
  - Stage B: 20 h;
  - evaluation: 5 h;
  - reserve: 1 h.

  E2's projection rule applies.
- **The rest of the owner's 96-hour ceiling** is kept for pre-registered follow-ups:
  - a memory task (`hold`, once S-const has run under it);
  - the pruning study;
  - N2's open-loop gain optimised by gradient (Fable's gain-against-topology diagnostic).
- **Guards:** E2's and E2d's stage frame: markers, the cap, reruns, not-completed records, and the
  replay checks.

## The roadmap

A dated amendment (the owner's decision, 2026-09-30), made with the pre-registration:
- E4s is added ahead of plan, as a preliminary to E4's hand-building;
- the tripwire ("no new infrastructure before the minimal A/B organism") is relaxed for the graft
  functions and the GA hooks only;
- E2d's plateau and the absent stereo smell are stated as the reason.

## What E4s cannot show

- Anything about the real worm's steering; the design is fly-inspired engineering.
- That the ring represents a physical bearing: it encodes normalised lateral contrast, and its
  rotation is a heuristic memory.
- Why a stereo use was lost, if it is: the probes interpret, they do not decide.
- Whether other modules, tasks or optimizers would do better.
- The minimal circuit (the pruning study, later).
- "Improves" near Task N's ceiling: S-const reaches 8.78 against the oracle's 8.85.
- Why the plateau exists: the gain probe is consistent with the gain hypothesis, but does not test
  it.

## Changes from v2 (for the third review)

| v2 review item | v3 |
|---|---|
| O1's rules overlap: a mean interval, a median threshold (Fable 5, Astra 1) | One estimand, the mean paired difference; ordered, exclusive rules; the sign-flip p reported only; the manipulation-check remark; a sensitivity reading |
| O2 overstates "eroded"; the trigger is ambiguous; "kept" is a low bar (Fable 6 and 7, Astra 2) | Each run classified by its own G0 and F: retained, lost, acquired, never used, unclear. "Retained" is defined as keeping the criterion. O2b, performance retention with bands. No global trigger. The generation-0 measurement has its own worlds |
| Persistence contradicts the shifters (Fable 1) | The checks run at turn 0 |
| Qualification undefined; it favours latches; zero-start side only (Fable 2) | The checks apply at each candidate's nose values inside A0; a carried-state crossing check; a stratified sample, not the deepest |
| "No spontaneous bump" cannot fail (Fable 3) | A seeded 10⁻³ perturbation, 100 ticks, a sabotage check |
| Counts: M1 is 14; the factor uses 334 (Fable 4, Astra 4) | Corrected |
| The shifter's computation unspecified; the 45° calibration treats ψ as a bearing (Astra 3) | Every weight, τ and bias pinned; signed resting drives kept uniform; the shifter check is direction, monotonicity, zero-turn stability, saturation and background turns, with no rate target; the claim restricted to a heuristic rotating memory, tested by cue-off and reacquisition probes across distances and bearings; a fallback to M1 |
| The probe's transient and reversal measure drift; "one genome" and "not a latch" are wrong (Fable 8, Astra 5) | Probe v3 adds unchanged-input controls. The three weak cases are three genomes (e2 GA run 3, e2 random run 6, 04a run 3), corrected by dated correction in D142. Items not adopted are listed |
| The score-level check is nearly vacuous (Fable 9) | 04a's 16 champions added; a failure stops E4s |
| Stage A underestimated at 43 740 configurations (Fable 10, Astra 4) | A0/A1 restructured and bounded (at most 2 160 + 108 × 9 + 10 closed-loop candidates); budget re-estimated at 17-19 h; per-stage caps |
| The anatomical fixture would break rule 1; the worm block interleaves (Astra 6) | Built in memory during the test; extracted by edge identity; implemented and sabotage-checked |
| Suggestions taken | τ 0.5 in the grid; the feedforward control; unrectified nose weights as an option; δ ±0.004 and level 0.35; robustness at 0.125× too, module-only on a fixed carrier; the fallback applied consistently; a same-session old-engine comparison if the hash check fails; B6 and B5 paired with B1's runs 1-8; a registered batch order |
| Pinned for the pre-registration (both) | The module file and its hash (the freeze); M0's grid; world ranges and seeds; the interval methods; the "not read" rule; the CUDA tolerance's genomes and the failure rule; the synapse-direction test; the roadmap amendment |

### Changes from v1 (kept for the record)

v2 answered the v1 review (D141):
- a carrier for Stage A;
- a generation-0 measurement;
- F as the registered reading;
- exclusive outcome classes;
- GA hooks with bit-identity checks;
- the populations drawn on N2 and embedded;
- B3 pinned;
- the gain ≥ 32 gate dropped;
- the text corrected against E2d;
- declared tolerances;
- the hygiene guard;
- the nose gain fixed at 1;
- no direct path in M2;
- component checks;
- an expanded tuning grid;
- 16 runs for B1 and B3;
- the arms B5 and B6.
