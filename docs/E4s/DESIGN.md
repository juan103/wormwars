# E4s: a hand-built stereo module grafted onto N2 (design v1)

Status: a design for review by Astra 6 and Fable 5.1, 2026-09-30. Nothing has run on E4s's worlds or
seeds. Two exploratory, design-informing measurements have run and are disclosed below. A
pre-registration follows only if both reviewers agree.

## Why, and why now (the owner's direction, 2026-09-30)

- **Evolution has not found stereo smell.** E2 and its diagnosis E2d (published) found a
  **"non-stereo plateau"**. No champion of E2's and 04a's 47 meets the "uses the left-right
  difference" criterion. All sit near 2.2 targets per episode, beside M-avg, the scripted controller
  that reads only the mean of the two sensors. No tested change to the optimizer (more worlds,
  gentler mutation, both, a smaller ES σ) left the plateau. E3, the minimal A/B organism, needs a
  navigator that steers by the smell's side.
- **The owner's plan:** build the stereo capability by hand, and let evolution settle it into the
  connectome:
  - two noses (left and right scent inputs);
  - a ring attractor borrowed from the fly's head-direction system, since it is well studied;
  - its active region biasing turning left or right;
  - then evolution optimises the whole brain.

  Removing neurons one by one to find the minimal circuit is later work (E3 or E4).
- **This is ahead of the plan.** Hand-building was to start in E4, with the A/B wey: gluing
  connectomes with a flip-flop, then letting them merge under evolution. E4s ("E4-stereo") is a
  preliminary version of that line, run now because E3 needs it. Being early, it can still surprise us.
- **The owner's ceiling for E4s is 96 GPU-hours.** This design proposes using a fraction of it (see
  Budget).

## What is known before designing (disclosed)

1. **The literature** (`docs/E4s/literature-report.md`, a deep research by Claude Sonnet 5.5 on the
   owner's instruction; brief in `brief.md`):
   - **Available to borrow:**
     - the fly's compass is local recurrent excitation (E-PG), global inhibition (Δ7) and shifter
       cells (P-EN) that rotate the bump by angular velocity;
     - rate-model ports with explicit equations exist (Goulard et al. 2021; Stone et al. 2017, via
       Sun et al. 2020; Noorman et al. 2024);
     - the fly's steering readout (PFL3) compares shifted copies of the bump; its left minus right
       output drives turning.
   - **Not found:** no published model anchors a ring on a bilateral *chemical* difference. No
     published work grafts a designed module into a connectome-constrained network and follows its
     fate under evolution.
   - **Biology, stated plainly:** the real worm steers by comparing the scent over time during head
     sweeps, not by comparing its two noses, which are about 8 µm apart. Stereo here is a design
     choice, fly-inspired, not worm-faithful. The interface already says its mappings are modelling
     choices.
2. **The report's central hypothesis:** the plateau is a gain problem, not a missing topology.
   - The left-right scent difference at the sensors is tiny: about 0.004-0.017 in injected current,
     against a common level of about 0.02-0.25 (checked against the code: `sense_scale_food` 0.35,
     σ = 6, sensors 0.6 ahead and ±0.5 to the side).
   - E1's scripted stereo steerer needs a gain k of about 256 to reach 8.5, and k = 4 scores 2.38
     (E1 RESULTS).
3. **An open-loop gain probe of the champions** (exploratory, design-informing, run 2026-09-30;
   `scripts/e4s_gain_probe.py` → `experiments/E4s-stereo-module/development-records/gain-probe.json`):
   - **Method:** each of the 47 distinct champions received a fixed scent current at its left and
     right sensory neurons (common level 0.02, 0.08 and 0.25; difference −0.02 to +0.02), held for 40
     ticks. The turn command was read as the world reads it.
   - **Result:** its slope against the difference, the effective stereo gain k, has a **median |k| of
     about 0.1 (at most 0.68)**, with no saturation at zero difference. The champions reach 2.2
     without stereo gain, by the temporal route.
   - **Limits:** open-loop, static input, no world. This supports the hypothesis; it is not a
     registered measure.

## The modules

Both are appended to N2's 302 neurons as named extra neurons ("E4S_..."), with their own synapses.
Initial values are the report's starting points (its "Proposed design" section), then tuned (Stage A).

- **M2, the ring (the owner's design, the main module; about 30 neurons):**
  - **Noses NL and NR**, fed by new interface entries: the same `food_left` and `food_right` signals
    the worm's AWA, AWC and ASE already receive, unchanged.
  - **An 8-column egocentric ring (E0-E7),** encoding where the smell is relative to the body, not a
    world-fixed heading, since Task N has no compass cue:
    - noses map onto it with cosine weights at a virtual azimuth φ, which acts as the gain knob;
    - local excitation, and a Δ7-like inhibitory pair for global inhibition;
    - 16 shifter cells, which rotate the bump with a copy of the module's own turn command, so the
      smell's direction is remembered across the wey's turns (the fly's P-EN mechanism; applying it
      to an odour bearing is our extrapolation).
  - **A readout pair T_L and T_R** (a PFL3-like hemifield sum), with push-pull synapses onto the
    turn neurons the interface already reads (SMDD and RMDD against SMDV and RMDV), and a direct
    nose-to-readout path (as in the fly's descending steering neurons).
- **M0, the minimal core (4 neurons):** NL, NR, T_L and T_R, with mutual inhibition, a flip-flop-like
  pair, and the same motor fan-out. It is the comparator for "does the ring earn its neurons", and it
  connects to the owner's flip-flop idea for E4.

**Where the gain comes from:** the modules must turn a difference of about 0.01 into a turn command
near ±1, roughly two orders of magnitude, with the common level rejected. This is what Stage A tunes
and checks.

## The engine (AGENTS.md rule 7)

- **The brain and world code already work for any number of neurons.** `BrainSpec`, `Genome` and
  `Brain` take n from the connectome; only `load_connectome` checks for 302, and the interface
  resolves neurons by name.
- **So the graft is new code, not a change to existing code:**
  - a function that builds an extended connectome (N2's 302 neurons, then the module's, appended so
    every existing index is unchanged);
  - a seeded-genome builder that writes the module's designed parameters;
  - an interface variant with the noses' entries.
- **The equivalence check:** N2 without a graft runs through unchanged code, and a test checks it is
  bit-identical. A second test checks that an extended connectome with an **inert** module (no
  synapses out) leaves the 302 neurons' trajectories unchanged, exactly on the CPU, at a declared
  tolerance on CUDA.
- **Module-only probes need no engine change.** "Module mean" and "module swapped" are interface
  variants that feed the noses (only) the average, or the swapped signals. They show the module's
  own stereo use, apart from the worm's. The world's `mean` and `swapped` probes act on every
  consumer, as in E2d.

## Stage A: the module works on its own (a positive control, as E1 was)

- **The background:** the 302 worm neurons are made silent (all their weights, conductances and
  biases zero), so the turn neurons relay only the module's output.
- **Tuning** on new tuning worlds: a small registered grid (for example, the nose gain, φ, the
  readout weight and the motor fan-out weight), for M2 and M0 separately. The best mean is chosen,
  as E1 chose its controllers.
- **The gate,** on fresh gate worlds, for the tuned M2:
  - Task N mean at least 5.0 targets per episode (M-avg 2.2; E1's scripted k = 32 reaches 5.6);
  - it meets the "uses the left-right difference" criterion under the module probes;
  - its open-loop gain (the probe above) is at least 32.

  If M2 fails the gate, E4s stops for redesign before any evolution.
- **Reported, not gating:**
  - M0 against M2 on Task N;
  - the two under the `hold` probe, which refreshes the scent every few ticks and so rewards
    remembering the bearing. On Task N itself a memoryless steerer already scores 8.7, so Task N
    alone cannot show whether the ring earns its neurons;
  - the ring's bump signatures (formation, persistence, correct side, rotation under the turn copy).

## Stage B: evolution settles the graft (confirmatory)

- **The optimizer:** 02's GA, as E2 kept it, 1 000 generations, Task N, unshaped fitness.
  - The module's parameters mutate at 0.25× 02's scales and the worm's at 02's scales, because the
    tuned module sits near a bifurcation (the report's advice). E2d's gentler-mutation lead is not
    adopted wholesale.
  - Every parameter, module and worm, is free.
- **Arms** (8 runs each, paired where possible):

  | Arm | Brain at generation 0 | Role |
  |---|---|---|
  | B1 (main) | M2 grafted onto random N2 genomes (02's initialisation) | Does evolution keep, improve or erode a working stereo module? |
  | B2 | M0 grafted onto random N2 genomes | The ring against the minimal core |
  | B3 | M2 with its motor outputs cut (inert), on random N2 genomes | Same neuron count, no stereo route: the control, and the neutral-drift baseline for the module's parameters |
  | B4 | M2 grafted onto 04a's run 2 champion (the navigation module chosen for E3) | Merging a stereo module with an existing non-stereo navigator, closest to E4's gluing |

- **Measures, on a fresh hold-out of 1 024 worlds, each champion one strain on all of them:**
  - the mean count;
  - the module probes and the world's probes, classified by E2d's criterion;
  - **module lesion cost:** the score with the module silenced, against intact;
  - the open-loop gain;
  - the `hold` score;
  - **along training** (at the checkpoints, not only on champions): gain, module-lesion cost, and
    distance of the module's parameters from their seed.
- **Registered outcomes, to be fixed in the pre-registration.** Proposed:
  1. **Useful and kept:** B1's mean exceeds B3's by at least 0.5 targets, **and** at least 6 of B1's
     8 champions meet the "uses" criterion under the module probes.
  2. **Eroded:** B1's module-lesion cost at the champion is below half its cost at generation 0, in
     at least 6 of 8 runs.
  3. **Beyond the module:** whether evolution improves on the module alone (B1 champions against
     Stage A's module-alone score) is reported with an interval.
- **Transparency:** E2d's plateau is stated as the reason for E4s. If B1 erodes the module or does
  not beat B3, that is the result, in the wording fixed in advance.

## Worlds, seeds, budget

- **World ids:** new ranges for tuning, gate, training, validation and hold-out, disjoint from every
  earlier range (a test checks it).
- **Seeds:** new, disjoint.
- **Budget, estimated from E2's rates** (02's GA, 8 runs, 1 000 generations: 1.35 h; 332 neurons
  instead of 302, about 10% more):

  | Part | Estimate |
  |---|---|
  | Stage A (tuning and gate) | about 0.5 h |
  | Stage B, 4 arms | about 6 h |
  | the hold-out, probes, lesions and checkpoint probes | about 1 h |
  | projection and smoke | about 0.3 h |
  | **total** | **about 8 h** |

- **Proposed:** a cap of 24 GPU-hours for this registration. The rest of the owner's 96-hour E4s
  ceiling is kept for pre-registered follow-ups (a memory task for the ring; the pruning study).
- **Guards:** E2's and E2d's stage frame (markers, the cap, reruns, not-completed records, the
  replay-style checks).

## The roadmap

A dated amendment (the owner's decision, 2026-09-30):
- E4s is added ahead of plan, as a preliminary to E4's hand-building;
- the tripwire ("no new infrastructure before the minimal A/B organism") is relaxed for the graft
  functions only;
- E2d's plateau and the absent stereo smell are stated as the reason.

## What E4s cannot show

- Anything about the real worm's neural stereo steering; the design is fly-inspired engineering.
- Whether other modules, tasks or optimizers would do better.
- The minimal circuit (the pruning study, later).
- "Improves" at Task N's ceiling: S-const reaches 8.78 against the oracle's 8.85, so improvement
  beyond a strong module cannot show there.

## Questions for the reviewers

1. The ladder: M2 and M0 only, or also the report's intermediate ring without shifters (M1)?
2. The background:
   - random N2 (B1) against 04a's champion (B4): are both needed?
   - is a silent background the right Stage A test?
3. Mutation: should the module mutate at 0.25× and the worm at 02's scale, or is one scale for all
   cleaner?
4. Measures and outcomes: are the proposed outcomes the right primary questions? Is 6 of 8 enough?
   Should Stage B use 16 runs per arm, given the ample ceiling?
5. Should the `hold` memory task be a registered arm now, rather than only reported?
6. Anything that would make the graft win, or fail, for a trivial reason.
