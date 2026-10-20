# M2 pilot: validating a dynamical census — the plan

*Draft 1, 2026-10-20. Exploratory: nothing here is a pre-registration. Step M2 of
[`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md) begins with "a small pilot first, then several graphs per ensemble". This
plan is the pilot's. Its job is to build a per-genome classifier and test whether it can be trusted, before a census
uses it at scale; the census gets its own plan, written after the pilot. M1's results ([`M1-RESULTS.md`](M1-RESULTS.md))
supply the inputs: the settling cohort carries 30-38% of the mean tick-30 lead and 66-68% of the tick-300 lead, and
under the frozen ramp-end Jacobian, transient growers with radius below 1 are more common in N2 than in the five
null graphs sampled. CPU only.*

**Facts used in this draft,** from a spike on 64 of N2's seed-7600 genomes
([`scripts/memory_m2/spike_equilibria.py`](../../scripts/memory_m2/spike_equilibria.py), output
`runs/memory-m2/spike_equilibria.txt`):
- after the ramp, 2000 ticks of follow-up for 64 genomes took 30 s;
- Newton's method in float64 from the tick-2000 states converges to residuals of 10⁻¹⁵, at distances of 7 × 10⁻⁵
  (median) to 2.2 × 10⁻⁴ (largest) from the float32 end states;
- 2 of the 64 genomes end in two distinct equilibria, both stable (largest real part of the eigenvalues −0.05 and
  −0.04).

## Why equilibria can be verified exactly

The brain's substep is v ← (v + c (d + tanh(v) M + v G)) / (1 + c (1 + g)), with c = dt/τ, d the bias plus the input,
M the chemical drive matrix, G the gap matrix and g its row sums (`wormwars/brain.py`, `Brain.step`). Under the
follow-up's constant input, a state is fixed by a substep if and only if

  H(v) = d + tanh(v) M + v G − v ∘ (1 + g) = 0,

which does not contain τ or dt. So the equilibria of the tick map are those of the continuous system τ ∘ dv/dt = H(v),
for every substep count and every set of time constants. They can be found by Newton's method on H in float64,
whatever precision the trajectory ran at, and their stability read from the eigenvalues of diag(1/τ) ∂H/∂v. This is
what "Jacobians at candidate equilibria, not at relaxing states" (the roadmap) needs. A stable equilibrium of the
continuous system need not be stable for the integrator; the perturbation check below tests that with the integrator
itself.

## The sample

- **Genomes:** M1's fresh panels, seed 7600, 1024 genomes per graph, so M1's per-genome numbers (a, |δy(30)|, the
  cohort) apply to the same brains. M1's probe, unchanged: 100 ticks of warm-up at 0.25× or 1.75× the final food
  level, a 10-tick ramp, then the follow-up at the final level, 32 substeps.
- **Graphs (5):**
  - N2;
  - the two selected graphs that beat N2 on M1's fresh panels, SH-recip-2050039 and SH-class-2030099, which lean
    much more on settling (M1-RESULTS, part A);
  - two of the random reference graphs, the first of SH and the first of SH-mirror in `runs/memory-m1/panel.json`
    (SH-2010013 and SH-mirror-2040045).
- **Genomes per graph:**
  - **the carriers:** the eligible genomes ranked by |δy(30)|, from the largest, up to and including the one that
    brings the total to half of the graph's eligible tick-30 numerator, capped at 64;
  - **the cohort:** M1's settling cohort (settled and remaining), all of it;
  - **the controls:** 32 further eligible genomes drawn at random, `default_rng(20261023)`, per graph in the order
    above, from those in neither group.

  A genome in two groups is simulated once and counted in each. Expected size: about 400 genomes.

## What is recorded

For each pilot genome, both histories:
- the full state every tick from 0 to 300 of the follow-up, and every 10th tick to 2000 (float32, local);
- the read-out difference δy(t) every tick;
- 03mc's settling range over ticks 291-300 and over ticks 1991-2000;
- the midpoint Jacobian at the ramp's end (M1's growers method): its spectral radius and whether the linear state
  norm grows over 10 ticks.

## The classifier (provisional; the pilot tests it)

**Equilibrium verification.** From each history's tick-2000 state, Newton's method on H in float64, at most 50
iterations. A history **reaches a verified equilibrium** if the iteration converges (max |H| below 10⁻¹²) to a point
within 10⁻³ (max norm) of its tick-2000 state. Its **stability** is the sign of the largest real part of the
eigenvalues of diag(1/τ) ∂H/∂v at that point.

**Classes,** per genome:
- **separate states:** both histories reach verified, stable equilibria, distinct (max-norm distance above 10⁻⁶),
  and the read-out difference between them is at least 0.1 a (03mc's "remaining");
- **separate states, read-out silent:** the same with a read-out difference below 0.1 a (the state remembers, the
  read-out does not show it);
- **fading:** both histories reach the same verified stable equilibrium (distance at most 10⁻⁶);
- **oscillating:** no verified equilibrium for at least one history, and its settling range over ticks 1991-2000 is
  above 10⁻⁴ with a near-return: some lag L from 2 to 100 ticks at which the state comes back to within 1% of the
  window's range. These genomes are rerun with every tick of 1801-2000 recorded (the run is deterministic on this
  machine), so the main record stays small;
- **unresolved:** anything else, including a verified equilibrium that is unstable.

**Two descriptions beside the class:** for fading genomes, the slowest decay rate of the difference near the common
equilibrium (the least negative real part among the modes the read-out sees, i.e. with a non-negligible projection of
c ⊙ sech² onto the eigenvector), against the observed late slope of log |δy| over ticks 300-1000; for every genome, the
tanh-consistent midpoint forecast of r(30) (M1's) against the observed r(30).

## The checks (the pilot's readings)

Each check has a threshold fixed here. A check that fails does not stop the pilot; it says what the census must
change, and the census plan answers each failure before it is written.

- **R1, the 03mc criterion against verification.** Of the genomes settled at tick 300 by 03mc's criterion (both
  histories, range below 10⁻⁴), the fraction whose histories both reach verified equilibria by tick 2000.
  Passes at 95% or more. Reported beside it: the agreement of M1's cohort (settled and remaining at tick 300) with
  "separate states", both ways.
- **R2, resolution.** The fraction of pilot genomes unresolved at tick 2000. Passes at 5% or less, overall and per
  graph. The number of genomes whose class at tick 300 (the same rules applied to the tick-300 states) differs from
  their class at tick 2000 is reported, by pair of classes.
- **R3, integration.** For representatives (every genome not classed fading, and 20 fading genomes per graph drawn
  with `default_rng(20261024)`), the same probe at 64 substeps, and in float64 at 32 substeps. Passes if the class
  agrees in at least 95% of representatives under each, and if, in every "separate states" genome, each history
  reaches the same equilibrium (within 10⁻⁶ after Newton) under all three integrations. A genome whose basin
  changes is reported by name: basin choice that depends on rounding would make the census's classes noisy near
  saddles.
- **R4, perturbation return.** At every verified equilibrium of the representatives, 8 random perturbations of max
  norm 10⁻³ and 8 of 10⁻², integrated for 500 ticks at 32 substeps in float64. "Returns" if the final distance is
  below 10⁻⁶. Passes if return and the eigenvalue sign agree at every equilibrium. A 10⁻² perturbation that crosses
  into the other history's equilibrium is counted apart (a small basin).
- **R5, the family of histories.** For every "separate states" genome and 20 fading genomes per graph
  (`default_rng(20261025)`), nine ramp starts, 0.25 to 1.75 of the final level in steps of 0.1875, each followed for
  2000 ticks and Newton-polished. Reported: the number of distinct verified equilibria per genome (distance above
  10⁻⁶), and the end read-out against the ramp start. **Read:** discrete if every genome's equilibria number at most
  4 and each is reached from a contiguous run of starts; a continuum is suggested if some genome's distinct equilibria
  number more than 4 or its end read-out varies smoothly with the start. A continuum of finite-time states could still
  be slow fading; the verified equilibria make that distinction.

## Descriptive outputs for the census

- Per graph and group (carriers, cohort, controls): the class counts, and each class's part of the group's tick-30
  and tick-300 numerators. These are not population rates; the groups are chosen, and the census estimates rates.
- Where M1's transient growers fall: the classes of the genomes whose midpoint state norm grows over 10 ticks with
  radius below 1.
- The forecast and decay-rate comparisons, per class.
- Timing per genome and per check, for the census's cost.

## What the pilot hands the census

- the classifier, revised if any check fails, and frozen before the census runs;
- the follow-up length (300 or 2000 ticks, or longer if R2 fails at 2000);
- whether the census needs float64 or finer integration (R3);
- whether "separate states" is two states or several (R5), which decides whether the census counts states;
- the cost per genome.

The census then answers the roadmap's split, how much of N2's excess over the nulls is separate states and how much
is fading, on randomly sampled graphs per ensemble, the high-settling null graphs and batch 7's core-frozen and
hub-frozen graphs.

## Outputs and cost

Scripts in `scripts/memory_m2/` (a README beside them), inside `wormwars.accounting`; outputs in `runs/memory-m2/`
(JSON committed; trajectories and arrays local). Cost, from the spike's 30 s per 64 genomes for 2000 ticks: the main
run about 3 minutes; R3 about 10; R4 about 10; R5 (nine starts for perhaps 100 genomes) about 7; Newton and the
eigenvalues a few minutes. Under an hour of CPU in all. No GPU. Reviewed by Astra and Fable before anything runs;
the results reviewed before they are committed.
