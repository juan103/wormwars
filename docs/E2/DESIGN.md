# E2: a short optimizer screen (design v2)

Roadmap v3, Track E, step E2. This is a design, not a pre-registration. Nothing has been run.
- v1 (`docs/reviews/20260929-100947-E2-design/`): both Astra 6 and Fable 5.1 said "revise", with
  largely the same must-changes. v2 adopts them; the last section lists how.

## What E2 is for, and what it cannot show

**Its only job is to choose the optimizer for E3** (roadmap: "E2: short optimizer screen"). 04a showed
that 02's genetic algorithm (GA), on the N2 wiring, finds cue-following navigators in most runs, but
weak ones: 2.0-2.8 targets per 300-tick episode, 23-32% of an oracle, a performance-equivalent gain of
k 3.5-6.9 (04a RESULTS.md, with its corrections). E2 asks whether another optimizer, given the **same
additional simulator work**, finds better ones.

- **E2 measures learning from random initialisation.** E3 starts from validated modules, then evolves
  a selector and fine-tunes jointly (ROADMAP.md). Optimizer rankings need not transfer between those
  settings. E2 chooses a **provisional default** for E3; it does not show which optimizer is better
  for E3's stages (both reviewers).
- **If E2's winner produces a better navigation module,** that module does not inherit 04a's evidence:
  it needs 04a's reliability, baseline and cue checks before E3 uses it.
- It is not the topology × optimizer study, which belongs to Track B later.

## ENOMAD, the closest prior work (read first, as the roadmap asked)

Churchland and Garcia-Ojalvo, "Reinforcement learning in densely recurrent biological networks",
*iScience* 2025 (the journal version, PMC12803941; arXiv 2508.09618 v1 differs in places, noted
below).
- **Model and task:** the C. elegans connectome as a leaky integrate-and-fire network in the journal
  version (arXiv v1 describes no leak), all 3 682 weights trained, initialised from contact counts
  with GABAergic connections negated (the authors' loader), food foraging and chemotaxis tasks whose
  rewards include distance-based shaping, in deterministic arenas.
- **ENOMAD** couples a GA (population 64, truncation of half, fitness-weighted uniform crossover)
  with NOMAD's mesh-adaptive direct search on blocks of at most 49 weights, and a supralinear penalty
  on the number of weights changed. Variants rENOMAD and mENOMAD.
- **Baselines:** a pure GA (population 64), OpenAI-ES (population 512, noise 0.07 decaying toward a
  floor of 0.01, Adam at 0.02), a crossover-free NOMAD, and the untrained connectome, which collects
  little food. 30 runs per method.
- **Result:** both ENOMAD variants beat the pure GA and OpenAI-ES on their tasks.
- **Differences that matter for E2:**
  - they compared at **equal wall-clock time** (20 minutes), so methods ran very different numbers of
    evaluations (generation counts from 14 to 1 300 are not evaluation counts either, given the nested
    NOMAD calls). E2 compares at **equal simulator work** and reports wall time beside it;
  - their prior is a **parameterisation near useful solutions**, not a working controller; ours starts
    from anatomical magnitudes with random signs (02's initialisation). 04a's champions are now a
    working, if weak, prior: local refinement from them is a natural later test, not part of E2;
  - their rewards are shaped; E2's are not (below).
- The summary's figures are from the journal version's methods and results; the pre-registration
  will cite section and table for each.

## The task and the brains

- **Task N exactly as E1 and 04a ran it** (σ = 6, 300 ticks, one wey, energy off), with 04a's
  configuration hash check against E1's gate record.
- **N2 only,** the same 5 404 parameters per genome as 04a (chemical weights, gap conductances, time
  constants, biases), the same bounds (w ∈ [−3, 3], g ∈ [0, 2], τ ∈ [0.5, 20], bias ∈ [−2, 2]).
- **Fitness: the raw count, no shaping,** for every method. 04a's unshaped arm passed 4 of 4 with the
  GA; whether an ES is handicapped by a sparse integer fitness is untested, and the outcome wording
  will say that E2 compares the methods under unshaped fitness only.
- **New id ranges** for tuning training, tuning selection, formal training, validation and the
  hold-out, disjoint from E1's and 04a's, and seeds disjoint across the pilot and the formal runs.

## The methods

All draw their initial genomes from 02's distribution (`Genome.random`).

1. **Random sampling (the floor).** Each generation draws 32 fresh genomes, scores them on 8 worlds,
   and keeps the best so far **since the previous checkpoint** (by training score, ties to the
   earliest). At each checkpoint that genome is the candidate. So every sample can become champion;
   proposals stay independent (both reviewers).
2. **02's GA (04a's optimizer), unchanged:** 32 genomes, 3 elites, the top 8 as parents, Gaussian
   mutation (w 0.08, g 0.04, τ 0.15 multiplicative, bias 0.05), one island, 8 worlds per genome per
   generation. Run through 04a's own `evolve_batch`, so no new GA code; its settings are inherited, so
   it pays no tuning cost ("equal additional E2 work", not equal historical effort).
3. **OpenAI-ES (the one adaptive method)**, specified completely:
   - **Encoding:** z = (w / 0.08, g / 0.04, ln τ / 0.15, bias / 0.05), the GA's mutation scales, so one
     noise scale σ fits every coordinate. A candidate is decoded from z and clamped to the bounds;
     the gradient estimate uses the unclamped perturbations; clipping rates are recorded. After each
     update, the mean is projected back into the bounds in z.
   - **Start:** the best of 32 random genomes on one generation's worlds (its 256 episodes charged),
     because 78-97% of random genomes score zero everywhere (04a) and a single draw would usually start
     on a flat plateau (Fable).
   - **Sampling:** 16 antithetic pairs (32 candidates) per generation, all on the same 8 worlds, so
     each generation costs 256 episodes like the GA's.
   - **Utilities:** average ranks of the fitness, centred to [−0.5, 0.5]; equal fitness gives equal
     utility, and a generation with all fitnesses equal makes **no update** (both; OpenAI's reference
     code breaks ties and would manufacture a gradient on a flat batch).
   - **Update:** Adam (β 0.9, 0.999) on the estimated gradient, **no weight decay** (both), learning
     rate set as a multiple of σ (Fable), both from the pilot.
   - **Candidate at each checkpoint:** the current mean, declared now; the best sampled offspring is
     not used (Astra).
   - **Limitation, stated:** 32 directions on 8 worlds is the GA's shape, chosen for equal composition
     and batching; more directions on fewer worlds might suit an ES better (both).

No ARS and no sep-CMA-ES: spare budget goes to replication instead (both).

## Tuning, charged

- **The pilot** (the ES only): 3 settings, σ ∈ {0.5, 1, 2} with the learning rate at 0.3 σ, then the
  learning rate ∈ {0.1, 0.3, 1} × σ at the best σ, **3 runs each**, 200 generations, on the pilot's
  own worlds and seeds. The setting with the best mean validation count at generation 200 is chosen
  (ties: the smaller σ, then the smaller rate). One short run per setting would select on noise: 04a's
  runs with identical settings ranged 0.51-2.08 at generation 100 (Fable).
- **The charge** (Astra's method-level allowance): the pilot's training episodes are subtracted from
  the ES's total allowance of 8 × 256 000, and the remainder is divided equally among its 8 formal runs,
  which therefore run fewer generations than the GA's (about 780 against 1 000, with the pilot above).
  The pilot's episodes are reported as their own ledger line. *(Fable preferred charging by limiting
  which checkpoints may supply the champion; the pre-registration will fix one rule.)*

## Runs and evaluation

- **8 runs per method** (both reviewers; the roadmap said 3: a dated roadmap amendment records this).
  Each method's 8 runs are batched together in 04a's measured composition (256 strains, 8 worlds, 1
  wey), so a non-finite score stops one method's batch only. Seeds by run number.
- **Checkpoints** every 25 generations and at the last, on 256 validation worlds, raw count; the
  champion is the first checkpoint with the best validation mean. Validation composition (8, 256, 1).
- **The hold-out:** 1 024 fresh worlds, used once. Each champion is one strain on all of them, padded
  (1, 1 024, 1), with **the mirrored and constant probes** as in 04a (Fable), so "better" can be read
  as better cue use and not only more arrivals. E1's scripted controls re-run there for scale.
- **Champion hashes and every hyperparameter are committed before the hold-out.**
- **The ledger:** training, tuning, validation, the hold-out, probes and diagnostics, in episodes,
  ticks and neural updates (padding included), and wall time, per method.

## The decision rule (to be fixed in the pre-registration)

- **Primary:** each method's mean hold-out count over its 8 champions.
- **A challenger replaces 02's GA as E3's default only if** its mean exceeds the GA's by at least **0.5
  targets per episode**, **and** at least 6 of its 8 champions are above the GA's median champion. If
  both challengers qualify, the one with the higher mean; random sampling cannot be chosen. Ties,
  failures and incomplete runs: no replacement of runs; a method with an incomplete run cannot
  qualify.
- **With 8 runs and 04a's between-run spread (SD 0.17-0.30),** a false switch is unlikely and a true
  gain of 0.75 targets would usually be found (Fable's estimate; the pre-registration will state its
  own). This is a coarse switch-or-keep decision, not evidence of a population-level advantage (Astra).
- **If random sampling's mean comes within 0.5 of the GA's,** the roadmap's rule applies: diagnose
  saturation, noise and budget before building on the task (ROADMAP.md, "What would change this
  roadmap"). The chosen default is then reported as provisional.
- **The winner's hold-out score is subject to selection optimism;** E3 evaluates on new worlds.

## Budget

From E1's throughput record: 8 runs batched at (256, 8, 1) take 4.67 s per generation; 04a measured
4.75-5.2 s with its optimizer and checkpoints. Per method, 8 runs of 1 000 generations: about 1.4
GPU-hours. Three methods, the ES pilot (15 short runs, 3 000 generations, batched) and the evaluation:
**about 4.5-5 GPU-hours.** The pre-registration will fix a cap (about 7) after a measured projection of
each method's training shape, as 04a did.

## Tests and equivalence (AGENTS.md rules 7 and 9)

- The GA runs through 04a's `evolve_batch` unchanged; a test checks that E2's call reproduces 04a's
  genome hashes on the CPU for the same seeds.
- The ES update is tested on known functions (a quadratic whose optimum it must approach; a flat
  function on which it must not move; the tie rule), each sabotage-checked.
- Random sampling's best-since-checkpoint rule is tested with a fake simulator.

## Changes from v1 (review v1)

- **Budget:** one complete ledger; tuning charged once at the method level (Astra), with Fable's
  alternative noted.
- **Random sampling** keeps the best since the last checkpoint (both).
- **The ES,** specified: encoding, clamping and projection, a best-of-32 start, average ranks with no
  update on a flat batch, no weight decay, the learning rate in units of σ, the mean as candidate, and
  its shape as a stated limitation (both).
- **Tuning:** fewer settings, 3 runs each, disjoint seeds and worlds (both).
- **Runs:** 8 per method, with a decision rule on 6 of 8 (both suggested more than 3).
- **The decision rule** completed, with the roadmap's diagnose-first rule for random sampling (Fable)
  and a narrower interpretation (Astra).
- **E3's connection** stated as provisional (both); probes added to the hold-out (Fable).
- **The runtime projection** corrected from E1's record (both).
- **ENOMAD's summary** corrected: signed initial weights, not all positive; a nearby parameterisation,
  not a working controller; shaped rewards; the journal version cited (Astra).
- **Tests and equivalence** declared (Fable).
