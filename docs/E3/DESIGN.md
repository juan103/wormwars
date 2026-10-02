# E3: the minimal A/B organism (design v1, 2026-10-02)

Status: a design for review by Astra 6 and Fable 5.1. Nothing has run. A pre-registration follows only
if both agree.
- **Its basis:**
  - the roadmap's E3 section, with its additions of 2026-10-01 (D144);
  - E4s's published results (`experiments/E4s-stereo-module/`, D147, D154);
  - the literature review's sections on latches, selectors and modular organisms
    (`docs/reviews/20261001-literature-review/`).
- **The framing, as in E4s:** stereo sensing is a game-design choice, and the stereo computation
  starts in hand-built grafts outside the N2 mask. Nothing here is about worm behaviour.

## What the roadmap asks, and a proposal to stage it

**The roadmap's E3 is one experiment with many parts:**
- two copies of the validated navigation module, one fed A's observations and one B's;
- a set-reset latch that switches the goal at each confirmed visit;
- trails (A and B pheromones, deposition weakening with time);
- unseen branching mazes;
- a colony with peer-signal controls;
- then an assembly comparison.

**None of the world machinery exists:** the world has one moving scent source (Task N), one
pheromone channel per swarm, no mazes, and no visit events.

**The proposal:** E3 in stages, each with its own design, pre-registration and gate.
- **E3a (this design): the shuttle.**
  - Open arena, one wey, two fixed sources A and B with distinct scents.
  - The organism must visit A, then B, then A, and so on.
  - The parts it tests are the latch and the two-module organism.
- **E3b: trails, mazes and the colony** (the roadmap's peer-signal controls). Designed after E3a.
- **E3c: the assembly comparison.** Designed after E3b.

The roadmap gets a dated amendment saying so, and that E3b holds the original gate on unseen
branching mazes. **Reviewers: is this staging right, or should E3a already include trails or mazes?**

## E3a: the task (a new task, "shuttle")

- **The arena:** Task N's, with one wey and the wall ring.
- **The sources:** two, A and B, at fixed positions per world (drawn from the world's seed, as Task
  N's targets are).
  - They are at least D_AB apart (proposed: 12 to 18 cells) and keep Task N's wall clearance.
  - The spawn is at least 8 cells from both.
- **The scents:** each source has its own Gaussian scent (σ = 6, amplitude 1, as Task N's), sensed
  bilaterally as `a_left`/`a_right` and `b_left`/`b_right`, scaled as food is.
  - The two scents are separate channels: neither masks the other.
- **The goal:** it starts as A (proposed; or drawn per world).
  - A **confirmed visit** is the head entering the current goal's radius (1.5 cells, Task N's R),
    after which the goal switches.
  - A visit to the non-goal source does not count and does not switch.
- **The score:** confirmed visits per episode (alternating journeys), from an event ledger like Task
  N's: the tick of each visit, the leg's path length, and the goal at each tick.
- **The horizon:** 600 ticks (proposed: about 5-10 legs for a good steerer at Task N's speeds).
- **Visit signals to the brain:** the world emits a one-tick pulse `at_a` (`at_b`) when the head is
  within the radius of A (B), whether or not it is the goal.
  - This is the sensory event that sets or resets the latch.
  - The goal itself is never given to the brain: the brain must remember it.
- **The interface:**
  - **For the hybrid organisms,** on the carrier, only the grafted modules' noses and the latch read
    these signals.
  - **For organisms with an N2 host,** a proposal: A's scent goes to AWA/AWC/ASE (as food), B's to
    another amphid set (ASI, ASJ and ADF, left/right), and `at_a`/`at_b` to a pair of
    mechanosensory neurons (ALM or AVM).

    These are game-design choices, labelled as such (`configs/interface.yaml`'s rule).
- **The engine change:** the new task, its fields, its events and its signals.
  - **The equivalence check (rule 7):** with the task off, every earlier task is bit-identical to the
    previous engine. That means reproducing E2's generation 0-25 hashes on the GPU, as E4s did, and E1's
    and E4s-0's Task N scores on the CPU.

## E3a: the organisms and the stages

**Stage 0, the positive control (as E1 was), scripted:**
- **S-shuttle:** E1's S-const steering on the current goal's scent, with a perfect, scripted memory
  of the goal. It is the ceiling for a stereo steerer.
- **S-oracle:** an oracle steering straight to the current goal.
- **Blind baselines:** a persistent random walk, and constant motion.
- **The gate:** the task must be solvable (S-shuttle reaching a registered fraction of S-oracle) and
  not solvable blind, before any organism is built.

**Stage 1, frozen modules with a fixed selector** (the roadmap's step 1; hybrid, engineered).
- **The modules:** two copies of E4s-0's L1 comparator.
  - **L1-A**'s noses read A's scent and **L1-B**'s read B's.
  - Both drive the same turn neurons on the carrier (the silent worm with the carrier's forward and
    turn biases).
- **The latch:** one self-exciting neuron q, τq̇ = −q + 2 tanh q + S − R (Hülse and Pasemann's
  analysis, as the roadmap's addition proposed). Its fixed points are ±1.915 and its switching
  threshold about 0.53.
  - `at_a` resets it (goal B) and `at_b` sets it (goal A), through weights of 1.
  - It is tested in our integrator for initialisation, pulse duration and simultaneous inputs.
  - The roadmap's addition also requires a test that a graft accepts a self-edge; it exists (D144).
- **The gate:** the latch must silence the inactive module, and a rate network cannot multiply. The
  proposal:
  - the latch adds a strong common input to both comparators of the inactive module, driving CL and
    CR into the same saturation, so their push-pull difference vanishes;
  - for example, q excites both L1-A comparators with weight g, and L1-B's with −g, and the comparator
    biases are shifted so that one module is linear and the other saturated.

  This is tuned on tuning worlds and tested open loop (the inactive module's K_D at most a registered
  fraction of the active one's).
- **The inactive module's semantics** (the roadmap's addition): it **continues updating**, gated at
  its output, never frozen or reset. That is the simplest semantics in a rate network.
- **The gate for Stage 1:**
  - its shuttle score has a registered lower bound against S-shuttle;
  - it beats a **no-latch control** (both modules always on);
  - it beats a **one-module control** (L1-A only).

**Stage 2, an evolved selector** (the roadmap's step 2).
- The modules are frozen and the latch's parameters evolve (its weights, bias, τ, the gate weights),
  from random starts.
- 02's GA, as E4s-1 used it.
- **The questions:**
  - does evolution find a working selector?
  - is it a clean latch, or transient modes (Agmon and Beer 2014, via the literature review)?

**Stage 3, joint fine-tuning** (the roadmap's step 3). Everything evolves at a reduced factor, as in
E4s-1, with a fraction of evaluations on the component skills: single-target navigation for each
module.

**The baselines** (the roadmap's addition):
- **B-shared:** one shared navigator plus a persistent goal bit. A single L1 whose noses receive A's
  or B's scent according to the bit; the input gating is done by the same saturation trick on two
  nose pairs.
- **B-task:** a task-conditioned controller of matched size: the same neurons, randomly wired,
  evolved from scratch.

**What it starts from:** E4s's artefact rule allows E4s-0's frozen L1 on the carrier, or E4s-1's run
10, a whole N2-plus-graft brain.
- **The proposal:** start from L1. It is 4 neurons per module, cheap, and its function alone is
  established. E4s-1's run 10 does not work as a module alone: its module scores 0 on the carrier.
- **Gluing two whole N2 brains** (2 × 306 neurons plus a latch) is E4's question, not E3a's.

## E3a: measures

- **Primary:** confirmed visits per episode on a fresh hold-out.
- **The latch's state** through the episode. Does it switch at each confirmed visit, and only then?
  Its hold time.
- **Module use:** each module's probes (its noses fed the mean or swapped) while it is active.
- **Confusion:** visits to the non-goal source; legs that end at the wrong source.
- **For Stages 2 and 3:** the evolved selector's dynamics. Is it bistable, with hysteresis? Does it
  fall back to transient modes?

## Budget and engineering

- **The engine:** the shuttle task, its fields, events and signals; the latch and gating modules; the
  stages' runners. Each is test-first, with the equivalence check for the world change.
- **Compute:**
  - Stage 0 and Stage 1 cost minutes: scripted controllers, and tuning tiny modules on the carrier.
  - Stage 2 is small: few evolving parameters, but full rollouts of 600 ticks.
  - Stage 3 is about E4s-1's scale, if it evolves the modules on the carrier, without N2.
  - **Proposed cap: 12 GPU-hours for E3a.** The owner has not set a ceiling for E3; this asks for one.
- **The tripwire** ("no new infrastructure before the minimal A/B organism") does not block this: this
  is the minimal A/B organism's infrastructure.

## What E3a cannot show

- Anything about worm behaviour or its circuits.
- Trails, mazes or colonies: that is E3b.
- Whether modularity pays (the assembly comparison): that is E3c.
- Whether two whole N2 brains can be glued (E4).

## Questions for the reviewers

1. The staging (E3a, then E3b, then E3c), and whether E3a should include trails or mazes.
2. The task: separate scent channels, the visit pulses, the horizon, the starting goal, and the
   geometry (D_AB, the spawn).
3. The interface for N2-hosted organisms (which neurons receive B's scent and the visit pulses), or
   whether E3a should avoid an N2 host entirely.
4. The latch and the gating by saturation. Is it sound in tanh rate units, and are there better known
   designs?
5. The stages' gates and the baselines. Is B-shared well posed?
6. Starting from L1 rather than E4s-1's run 10.
7. Anything that would make E3a succeed or fail for a trivial reason.
