# E2: a short optimizer screen (design v1)

Roadmap v3, Track E, step E2. This is a design, not a pre-registration. Nothing has been run.
Written 2026-09-29 for review by Astra 6 and Fable 5.1.

## What E2 is for

**Its only job is to choose the optimizer for E3** (roadmap: "E2: short optimizer screen"). 04a showed
that 02's genetic algorithm, on the N2 wiring, finds cue-following navigators in most runs, but weak
ones: 2.0-2.8 targets per 300-tick episode, 23-32% of an oracle, a performance-equivalent stereo gain
of about k = 4 (04a RESULTS.md). E2 asks whether another optimizer, at the **same simulator work**,
finds better ones. It is not the topology × optimizer study, which belongs to Track B later.

## What ENOMAD teaches (the roadmap asked for it to be read first)

Churchland and Garcia-Ojalvo, *iScience* 2025 (arXiv 2508.09618), is the closest prior work: food
foraging and chemotaxis on the C. elegans connectome, a leaky integrate-and-fire model, all 3 682
weights trained, starting **from the connectome's contact counts** as weights.
- **ENOMAD** couples a genetic algorithm (population 64, truncation of half, fitness-weighted uniform
  crossover) with NOMAD's mesh-adaptive direct search on small blocks of at most 49 weights, plus a
  supralinear penalty on the number of weights changed. Two variants: rENOMAD (random blocks) and
  mENOMAD (few, large edits).
- **Baselines:** a pure genetic algorithm (population 64), **OpenAI-ES** (population 512, antithetic
  noise σ 0.07 decaying to 0.01, Adam at 0.02), a crossover-free NOMAD, and the untrained connectome.
  30 runs per method.
- **Result:** both ENOMAD variants beat the pure GA and OpenAI-ES on their tasks.
- **Two differences that matter for us:**
  1. **They compared at equal wall-clock time** (20 minutes each), so the methods ran very different
     numbers of evaluations (14 to 1 300 generations). E2 compares at **equal simulator work**, as the
     roadmap requires, and reports wall time beside it.
  2. **They start from a strong prior** (the anatomical weights, all positive, as a working
     controller) and make sparse edits. Our genomes start from anatomical magnitudes with **random
     signs**, random time constants and biases (02's initialisation), so there is no working prior to
     refine. An ENOMAD-style local search is therefore less obviously suited here; the roadmap keeps
     an ENOMAD-inspired hybrid as a later option.

## The task and the brains

- **Task N exactly as E1 and 04a ran it** (σ = 6, 300 ticks, one wey, energy off), with 04a's config
  hash check against E1's gate record.
- **N2 only,** 02's initial distribution (`Genome.random`), the same parameters evolved as in 04a
  (5 404 per genome: chemical weights, gap conductances, time constants, biases).
- **Fitness: the raw count, no shaping.** 04a's unshaped arm passed 4 of 4 and produced its best
  champion; dropping shaping removes a free parameter that would interact with the methods.

## The methods

All start from 02's initial distribution. Each method gets the same **simulator budget: 256 000
strain-episodes per run** (04a's per-run budget: 32 genomes × 8 worlds × 1 000 generations),
**including any tuning** (see below).

1. **Random sampling (the floor):** fresh random genomes, no adaptation. Each "generation" draws 32
   new genomes on 8 worlds; the best is kept by the same checkpoint rule as the others.
2. **02's genetic algorithm (04a's optimizer),** unchanged: 32 genomes, 3 elites, top 8 as parents,
   Gaussian mutation (w 0.08, g 0.04, τ 0.15 multiplicative, bias 0.05), one island, 8 worlds per
   genome per generation, 1 000 generations.
3. **OpenAI-ES (the adaptive evolution strategy):** a single search distribution over the parameter
   vector (w, g, log τ, bias, each scaled to its mutation σ in the GA so one σ fits all), antithetic
   sampling, fitness ranks centred to [−0.5, 0.5], Adam on the estimated gradient, weight decay
   0.005. Population 32 (16 antithetic pairs) on 8 worlds per generation, so the same 256 per-generation
   strain-episodes and 1 000 generations as the GA. The mean is evaluated at every checkpoint.
   *Why this one:* it is ENOMAD's main adaptive baseline, and it adapts through the gradient estimate
   rather than per-coordinate variances, which scale well to 5 404 parameters. CMA-ES with a full
   covariance does not; sep-CMA-ES is an alternative for review.
4. **Optionally, Augmented Random Search (ARS),** labelled adaptive: antithetic directions, the top b
   of N kept, the step scaled by the reward standard deviation. Included only if the budget allows
   (below).

**Tuning, within the budget.** OpenAI-ES and ARS have a step size and a noise scale that the GA does
not need to tune (its settings are 02's). To keep "equal simulator work including tuning": each
adaptive method gets a small pilot grid (for OpenAI-ES: σ ∈ {0.5, 1, 2} × the GA's mutation scales,
Adam learning rate ∈ {0.01, 0.03}; 6 settings) of short runs (100 generations, 25 600 episodes each,
on smoke-range worlds), chosen by a registered rule, and **the pilot's episodes are charged to that
method's total**, which shortens its formal runs accordingly. The GA and random sampling pay no
tuning cost. The alternative, charging nothing and reporting the pilot separately, is for review.

## Runs and evaluation

- **3 runs per method** (roadmap), each with its own seeds, batched as in 04a where the method allows.
  3 runs cannot rank close methods; E2 can only pick out a clear winner (below).
- **Champion:** as in 04a, the first checkpoint (every 25 generations) with the best mean count on
  256 validation worlds. The ES's checkpoint candidate is its current mean; the GA's and random
  sampling's, the generation's best genome.
- **Hold-out:** 1 024 fresh worlds from a new, reserved range, used once, each champion one strain on
  all of them; E1's scripted controls re-run there for scale.
- **Also recorded:** each run's validation curve (best-so-far against episodes spent), wall time, and
  the E1 secondary measures of each champion.

## The decision rule (to be fixed in the pre-registration)

- **Primary:** the mean hold-out count of each method's 3 champions.
- **A method replaces 02's GA for E3 only if** its mean over 3 champions exceeds the GA's by at least
  0.5 targets per episode **and** its worst champion is at least as good as the GA's median champion.
  Otherwise E3 keeps 02's GA, which has 04a's validation behind it.
- **Random sampling** is the floor: if it comes within 0.5 of the GA, that is reported as the GA adding
  little at this budget.
- Descriptive: the curves (whether a method is still climbing at the budget's end), and the hold-out
  controls.

## Budget

At 04a's measured 4.75-5.2 s per 256-strain generation batch (8 runs), a method's 3 runs cost about
0.45 GPU-hours if batched 3 at a time (1 000 generations at about 1.6 s per 96-strain batch, from E1's
throughput curve; to be measured). Three required methods plus tuning: about 2 GPU-hours; with ARS,
about 3. A cap of about 5 GPU-hours, fixed in the pre-registration after a projection, as in 04a.

## Questions for review

1. Is OpenAI-ES the right single adaptive method, or sep-CMA-ES, or should ARS be required?
2. Charging tuning episodes to the method's budget, or reporting them separately?
3. Is dropping shaping right, given 04a?
4. Is the decision rule (0.5 targets and the worst-against-median condition) sensible with 3 runs? Should
   E2 use more runs per method, given how cheap it is (the roadmap says 3)?
5. Should an ENOMAD-like local refinement be tested now, given that our start is not a working prior?
6. Anything that would make E2's choice unfair or uninformative for E3.
