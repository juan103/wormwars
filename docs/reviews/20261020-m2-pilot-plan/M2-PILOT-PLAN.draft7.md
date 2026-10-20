# M2 pilot: validating a dynamical census — the plan

*Draft 7, 2026-10-20, after six rounds of review (both "revise" each time; drafts 1 to 6 and the reviews are archived in
[`docs/reviews/20261020-m2-pilot-plan/`](../reviews/20261020-m2-pilot-plan/)). Exploratory: nothing here is a
pre-registration. Step M2 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md) begins with "a small pilot first, then several
graphs per ensemble". This plan is the pilot's. Its job is to build a per-genome classifier and to test whether it
can be trusted before a census uses it at scale. The census gets its own plan, written after the pilot. M1's results
([`M1-RESULTS.md`](M1-RESULTS.md)) supply the inputs: the settling cohort carries 30-38% of the mean tick-30 lead and
66-68% of the tick-300 lead, and under the frozen ramp-end Jacobian, transient growers with radius below 1 are more
common in N2 than in the five null graphs sampled. CPU only.*

**Facts used in this draft,** from a spike ([`scripts/memory_m2/spike_equilibria.py`](../../scripts/memory_m2/spike_equilibria.py),
output `runs/memory-m2/spike_equilibria.txt`):
- on 64 N2 genomes drawn directly with seed 7600, 2000 ticks of follow-up took 22 s in the committed output (earlier runs
  took 26 to 72 s, depending on what else shared the CPU). These 64 are **not** a
  subset of M1's 1024-genome panel: `Genome.random` draws parameters in batches, so a draw of 64 differs from the
  first 64 of a draw of 1024 (Astra). The pilot draws 1024 and selects;
- Newton's method in float64 from the tick-2000 states converges to residuals of 10⁻¹⁵, at distances of 7 × 10⁻⁵
  (median) to 2.2 × 10⁻⁴ (largest) from the float32 end states. 2 of the 64 end in two distinct roots, both with
  negative continuous rates (largest real parts −0.05 and −0.04);
- built from the float64 brain's own matrices, a root moves by less than 3 × 10⁻¹⁴ under one tick of the float64
  integrator at 8, 32 and 64 substeps (at most 5.7 × 10⁻¹⁴). Built from the float32 brain's matrices cast to float64,
  it moved by up to 1.8 × 10⁻⁷, so the pilot builds H from the brain it integrates with.

## What can be verified, and what cannot

The brain's substep is v ← (v + c (d + tanh(v) M + v G)) / (1 + c (1 + g)), with c = h/τ and h = 1/k for k substeps,
d the bias plus the input, M the chemical drive matrix (`W_drive`, row-vector convention), G the symmetric gap matrix
and g its row sums (`wormwars/brain.py`, `Brain.step`). M1's probe uses no silence mask, clamp or output gate, any of
which would change what follows. Under the follow-up's constant input, a state is fixed by **one substep** if and only if

  H(v) = d + tanh(v) M + v G − v ∘ (1 + g) = 0,

which contains neither τ nor h. So the substep map's fixed points are the continuous system's equilibria
(τ ∘ dv/dt = H(v)) for every substep count and every set of time constants, and Newton's method on H can locate
them in float64 whatever precision the trajectory ran at.

Two limits (Fable, Astra):
- **The tick map is the substep map applied k times.** Its fixed points also include substep cycles whose period
  divides k. H = 0 does not find those.
- **A stable continuous equilibrium need not be stable for the integrator.** Write A[i, j] = ∂H_j/∂v_i (the
  substep's row-vector convention: the state is a row, the target neuron a column) and D = diag(h / (τ + h (1 + g))).
  Linearised at a root of H, one substep maps a row perturbation x to x (I + A D); in column form, x ← P x with
  **P = I + D Aᵀ** (Fable, Astra, round 2). Explicit in the chemical and off-diagonal gap terms, it can flip (an
  eigenvalue through −1) where the continuous system is stable. All eigenvector statements below use P's column
  form: right eigenvectors are mode shapes, left eigenvectors give a perturbation's excitation of a mode.

So the classifier's **stability is P's spectral radius**, the integrator's own. The continuous sign (the largest real
part of diag(1/τ) Aᵀ) is reported beside it, and a disagreement between the two is a reported quantity, not a silent
class. P is checked against the integrator itself: at a root every substep has the same linearisation, so the
automatic derivative of one full float64 tick of `Brain.step` must equal P³² (R4′). `Brain.step(substeps=1)` would
take one substep of length 1, not 1/32, so it is not used (Astra). "Verified" is too strong for what Newton gives (Astra): a small
residual establishes an accurate root only up to its conditioning, and nearness to a root does not establish that the
trajectory converges to it, least of all near a basin boundary. The plan says **located** for a root, and
**reached** only where a float64 continuation confirms it (below).

## The sample

- **Genomes:** M1's fresh panels, seed 7600, 1024 genomes per graph, regenerated in full, so M1's per-genome numbers
  (a, |δy(30)|, the cohort) apply to the same brains. M1's probe, unchanged: 100 ticks of warm-up at 0.25× or 1.75×
  the final food level, a 10-tick ramp, then the follow-up at the final level, 32 substeps, float32.
- **Graphs (5):**
  - N2;
  - the two selected graphs that beat N2 on M1's fresh panels and lean much more on settling (M1-RESULTS, part A):
    SH-recip-2050039 and SH-class-2030099;
  - two of the random reference graphs, the first of SH and the first of SH-mirror in `runs/memory-m1/panel.json`:
    SH-2010013 and SH-mirror-2040045.
- **Groups per graph:**
  - **the carriers:** the eligible genomes ranked by |δy(30)|, from the largest, up to and including the one that
    brings the total to half of the graph's eligible tick-30 numerator, capped at 64. The part of the numerator the
    capped set holds is reported;
  - **the cohort:** M1's settling cohort (settled and remaining at tick 300), all of it;
  - **the growers:** M1's growers were found on another draw (512 genomes, seed 7602; `growers.py`), so they are not
    these brains (Astra). The pilot computes the same midpoint Jacobian at the ramp's end on all 1024 genomes and takes
    the eligible genomes whose linear state norm grows over 10 ticks with radius below 1, up to 32 at random
    (`default_rng(20261023)`). This replicates M1's grower diagnostic on a new draw; it does not classify M1's own
    growers;
  - **the controls:** 32 further eligible genomes drawn at random (`default_rng(20261023)`, after the growers) from
    those in no other group.

  A genome in two groups is simulated once and counted in each. Expected size: about 450 genomes.
- **Planted genomes** (Fable; a sabotage check under rule 9): constructed brains with known behaviour on N2's mask,
  with every other weight set to zero:
  - a mutually excitatory pair (weights 3, bias 0, τ = 2) that includes a turn read-out neuron, which has two stable
    states that the read-out shows: expected **separate states**, exactly;
  - the same construction on a pair away from the read-out, with a read-out neuron given a start difference that
    decays: expected **separate states, read-out silent** (Fable, round 6: a pair away from the read-out gives a = 0
    and the read-out rule is not exercised);
  - the same pair with weights 0.5, which fades to one state;
  - a directed inhibitory three-neuron cycle at gain 3 (τ = 4), which oscillates;
  - the same three-cycle at gain 1.99999. Its continuous system is stable at the root (largest real part
    −1.25 × 10⁻⁶ per tick), but the integrator's P is not (radius 1.00009 per substep): the explicit chemical term
    adds about (ωh)²/2 per substep to a weakly damped rotation, and the integrator cycles. The right class for the
    integrator is a persistent oscillation; P's radius and the continuous sign at its root are recorded beside it.
    Found while building the damped spiral below, in a smoke test of the code;
  - the same three-cycle with its gain set by bisection so that **the integrator** damps the spiral by 5 × 10⁻⁶ per
    tick (P marginal by the plan's margin): a slowly damped spiral that is still a candidate at tick 2000 and decays
    by less than a tenth over the 20,000-tick continuation, so the root condition, not the range rule, has to reject
    it (Astra, rounds 2 and 3). It must **not** be classed oscillating.

  The three-cycle's τ is 4, which puts the oscillating ring's period (about 14 ticks) inside the detection window (at
  τ = 1 and w = 3 it would be about 2.4 ticks; Fable, round 2).

  The script first confirms each by a long direct simulation in float64. A construction that does not behave as
  intended is replaced or reported, not used. The classifier must name each correctly. If N2's mask has no suitable
  three-cycle, the oscillating case is built on a small spec of its own and said so.

## What is recorded

For each pilot genome, both histories:
- the full state every tick from 0 to 300 of the follow-up, every 10th tick to 1800, and every tick from 1801 to 2000
  (float32, local; about 220 MB for the last stretch, Fable);
- the read-out difference δy(t) every tick;
- 03mc's settling range over ticks 291-300, 1891-1900 and 1991-2000, per history, from these records (Fable,
  round 5: `_Range` takes the largest over both rows);
- the midpoint Jacobian at the ramp's end: its spectral radius, and whether the linear state norm grows over 10 ticks.

## The classifier (provisional; the pilot tests it)

**Locating a root.** From a history's state at tick 2000, damped Newton (backtracking on |H|) in float64, at most 100
iterations. A root is **located** if max |H| falls below 10⁻¹²; non-convergence is recorded, not hidden. Recorded with
it: the final residual, the size of the last step, the smallest singular value σ of A (conditioning), the distance to
the starting state, and the float32 residual |H| at the starting state (a precision-aware second reading, Fable).
**Root accuracy gates the class** (Astra, round 2): the error bound of a located root is e = max(the size of one
further Newton step at the root, residual / σ). The last accepted step measures the previous iterate's error, so it
is not used. The residual is a max norm and σ a 2-norm quantity, so the second term can understate the 2-norm bound by
up to √N ≈ 17; the margin below covers that (Fable, round 3). If e is above 10⁻⁹, a thousandth of the distinct-root
threshold, the root's identity is uncertain and the genome is **unresolved (ill-conditioned)**. A line search that
fails to lower the residual leaves the iterate where it was and is counted; after three, the strain is not located. A
singular A is solved by least squares and counted (Fable, round 3). The give-up is permanent: a strain given up
is never re-admitted while others iterate (Fable, Astra, round 4; a test pairs a strain that always fails with one
that converges slowly and requires exactly three failures).

**Stability.** Stable if P's spectral radius is below 1 − 10⁻⁶ per substep (raised to the 32nd power, below
1 − 3.2 × 10⁻⁵ per tick), unstable if above 1 + 10⁻⁶, otherwise **marginal**. The continuous sign is reported
beside it.

**Reaching it, at the root's own rate, tick by tick** (Fable, round 2: a fixed 10⁻⁸ within 2000 ticks would send
slow, stable roots to "unresolved" for the rule's sake). Let x₀ be the history's tick-2000 state minus the root, and
d₀ its max norm (about 10⁻⁴ is float32's floor, not decay). The **forecast** is the linear propagation of the
history's own difference, x(t) = (P³²)ᵗ x₀ (column form), which carries non-normal transient growth and the
excitation of each mode, as a spectral radius alone does not (Fable, Astra, round 3; the growers group is selected for
exactly that growth). The float64 continuation from the tick-2000 state runs until the forecast's max norm stays below
10⁻³ d₀ over 100 consecutive ticks, at least 200 and at most 20,000 ticks; call its length T. The history **reaches**
the root if the root lies within 10⁻³ of its tick-2000 state and, **at every tick of the last 100**, the continuation's
distance is at most max(10⁻¹², 10 e, 10 × the forecast's max norm *at that same tick*), and at T it is at most d₀/2.
The 10 e term (e the root's error bound) is there because the continuation converges to the true root, which the
accuracy gate lets sit up to 10⁻⁹ from the located one; without it a fast root would fail on the floor (Fable,
round 4). Distances
are compared with forecasts at matching times, so a trajectory that follows its forecast exactly passes, whatever its
rate (Fable, Astra, round 3: draft 3 compared a window's maximum with the forecast at the window's end, which fails
exponential convergence by construction). If at the cap the forecast is still above 0.1 d₀, the decay is too small to
test; the history is **unresolved (slow)**, named, with its rate. A history whose distance falls but leaves the
forecast's bound is reported as **forecast failure**, apart from one that does not approach the root at all. The
continuation runs only where its verdict is needed (Fable, round 5): a root not within 10⁻³ of the state is "not
approaching" and an unstable root "not tested", without it. The forecast is clipped at 10³⁰ so that it cannot overflow.
The continuation and its forecast use the same substep count (R3 runs at 64; Astra, round 5; a test checks it). The
pilot reports, for every history, the tick-2000 distance against the continuation's verdict, so the census can use
the cheaper rule (distance alone) only if the two agree.

**Classes,** per genome, in this order of precedence (Astra, round 2: the classes must not overlap). A confirmed
oscillation is tested ahead of every unresolved verdict, so an ill-conditioned root in one history cannot hide a
confirmed oscillation in the other (Fable, round 5):
- **separate states:** both histories reach stable roots, distinct (max-norm distance above 10⁻⁶), with a read-out
  difference between them of at least 0.1 a (03mc's "remaining");
- **separate states, read-out silent:** the same with a read-out difference below 0.1 a: the state differs, the
  read-out does not show it;
- **fading:** both histories reach the same stable root (distance at most 10⁻⁶);
- **persistent oscillation over the observed horizon** (its asymptotic status unresolved; Astra, round 3): at least
  one history reaches no root and is a **confirmed** candidate. A history is a
  **candidate** if its settling range is above 10⁻⁴ in both 1891-1900 and 1991-2000. Candidates are rerun at 64
  substeps with every substep recorded through `Brain.substep_hook`, so that a cycle of a few ticks (τ can be as
  small as 0.5) is not mistaken for a quasi-periodic orbit by tick sampling (Fable, round 2). A candidate is
  **confirmed** if, at substep resolution, there is a period L between 2 substeps and 50 ticks at which **the whole of
  the last three periods repeats the period before it, sample by sample**, within 1% of the range of the stretch
  compared (its last four periods). L may be fractional: the integer lags' 20 deepest local minima are refined in
  steps of 0.02 samples with linear interpolation, in ascending order, so the fundamental period is found before its
  multiples (Fable, round 5: a period that is not a whole number of substeps would otherwise fail by construction).
  Comparing whole periods rather than three isolated endpoints rejects a tail whose excursions differ between returns
  (Astra, round 5). At 64 substeps a tick, a cycle has at least 64 samples per tick of period, and the interpolation
  error is far inside the tolerance. A finite tolerance cannot exclude a quasi-periodic orbit that repeats closely.
  The 64-substep rerun repeats the whole probe (warm-up, ramp, 2000 ticks) and searches ticks 1801-2000 (12,800
  substeps, four periods at L = 50 ticks); the search costs up to about 70 s per candidate history.
  Beyond the period, since a repeating stretch can still be a damped oscillation (Astra, round 1): a float64
  continuation of 20,000 further ticks keeps its range (the range over the continuation's last 200 ticks is at least 90% of the main
  float32 run's range over ticks 1801-2000); Newton, from the orbit's final state and from its mean over the last
  period, **locates at least one root**; and **none of the roots located is stable or marginal under P**. The 64-substep
  rerun is in float32, as the main run. Each located root's distance from the orbit's mean is recorded, since Newton
  from the mean can land on a root unrelated to the cycle (Fable, round 4).

  The root condition is a **conservative veto**, not a contradiction. A stable cycle can coexist with a stable root
  (in the plane, r′ = −r(r² − 1)(r² − 4) with θ′ = 1 has a stable origin and a stable cycle at radius 2; Astra,
  round 4), so the veto can exclude genuine cycles. What it buys is that a slow spiral cannot pass: the 90% rule
  alone would accept a spiral decaying at 10⁻⁶ per tick (Astra, round 3), whose root is marginal. A vetoed candidate
  is **unresolved (candidate around a stable root)**, with the pairing recorded (Fable, round 3); one with no root
  located is **unresolved (no root located from the orbit)**, not confirmed vacuously (Fable, Astra, round 4). Even
  confirmed, a candidate is persistent only over the 22,000 ticks observed. Cycles longer than 50 ticks and
  quasi-periodic orbits stay unresolved;
- **unresolved:** anything else, named by its reason: ill-conditioned, slow, an unstable or marginal root, a located
  root not reached, a Newton failure, an unconfirmed candidate oscillation.

The distinct-root threshold, 10⁻⁶, is a thousand times the largest root error the accuracy gate allows (10⁻⁹). The
class counts are also reported with it at 10⁻⁴ and 10⁻⁸, as a sensitivity check.

**Descriptions beside the class:**
- for fading genomes, the decay of the difference near the common root: P³²'s eigenvalues give the discrete rates
  per tick (column form, as above). A mode's part in δy is its read-out visibility (c ⊙ sech² on its right eigenvector) times its
  excitation (its left eigenvector on δv at tick 300) (Astra). The predicted late decay is set against the observed
  slope of log |δy| fitted over windows above the numerical floor. Complex pairs are taken by modulus, and
  cancellations are reported;
- for every genome, M1's tanh-consistent midpoint forecast of r(30) against the observed r(30).

## The checks (the pilot's readings)

Each check has a threshold fixed here. A check that fails does not stop the pilot; it says what the census must
change, and the census plan answers each failure before it is written. **Every check reports the tick-30 and tick-300
numerator held by the genomes it flags** (Astra): 5% of genomes can carry most of the signal.

- **R1, the 03mc criterion against the classifier.** Among genomes settled at tick 300 by 03mc's criterion (both
  histories, range below 10⁻⁴), the fraction whose histories both reach stable, accurate roots. Passes at 95% or
  more. *Contemporaneous* classification too (Astra, rounds 2 and 6): **the full rules** (Newton, the accuracy gate,
  P's verdict and the float64 reaching continuation) applied to the tick-300 states, without the oscillation
  procedure, whose windows lie after tick 1800. Reported: each genome's class at tick 300, whether each history's
  tick-300 root is the one it reaches by tick 2000, and the table of transitions from the tick-300 class to the
  tick-2000 class, so the census knows what a 300-tick follow-up can classify. M1's cohort against "separate states"
  is reported both ways.
- **R2, resolution.** The fraction of pilot genomes unresolved at tick 2000, and their numerator. Passes at 5% or
  less of genomes overall and per graph, **and** at 10% or less of each graph's tick-30 numerator. Class changes
  between the tick-300 and the tick-2000 classification are tabulated by pair of classes.
- **R3, integration and batch.** Representatives: every genome not classed fading (both "separate states"
  subclasses included), and 20 fading genomes per graph (`default_rng(20261024 + the graph's index)`). They are rerun at 64 substeps, in
  float64 at 32 substeps, and at 32 substeps in float32 in a different batch composition (the representatives alone,
  in batches of 16). Passes if the class agrees in at least 95% of representatives under each, and if each history
  of every "separate states" genome reaches the same root (within 10⁻⁶ after Newton) under all four. A genome whose
  basin changes is named: basin choice that depends on rounding, substeps or batch would make the census noisy near
  basin boundaries. For oscillating genomes, the 64-substep rerun also checks that the cycle is not an artefact of
  the substep count (aliasing).
- **R4, local stability by perturbation.** At every root that a representative reaches and that P calls stable,
  distinct roots only,
  (unstable and marginal roots are named instead; R4 does not apply to them; Fable, round 2), perturbations of max norm
  10⁻⁸, 10⁻⁶ and 10⁻⁴, 8 random ones and the eigenvectors of P's two slowest modes, are integrated in float64 at 32
  substeps. The horizon is chosen from the discrete decay rate so that the linear forecast falls to 10⁻³ of the
  initial size, capped at 20,000 ticks. The perturbations of a root run as rows of one strain, so that they share its
  matrices (Fable, round 4). "Returns" if the final distance is below max(10⁻¹², 10 e, 10 × the linear forecast)
  **and** below half the initial size, so that an unchanged or growing perturbation cannot pass (Astra, round 2). If
  the cap leaves the forecast above 0.1 of the initial size, the test is **inconclusive** and reported as such. Each
  row's endpoint is taken at its own stopping time, and where it ends is decided by Newton from that endpoint: a
  located, accurate root within 10⁻⁶ of the other history's root, and farther than 10⁻⁶ from its own, is a **small
  basin**, counted apart (by perturbation size), not a failure to return (Astra, Fable, round 6). Passes if every
  conclusive test that is not a small basin returns; a failure is investigated and reported. Seeds:
  `default_rng(20261026)`. A
  10⁻⁴ perturbation that ends at the other history's root is counted apart, as a small basin (Astra: finite
  perturbations can leave a basin). This **supports** local stability; it does not prove agreement with an
  eigenvalue sign.
- **R4′, P against the integrator.** At 20 roots (or all, if fewer; `default_rng(20261027)`), P³² is compared with the
  automatic derivative of one float64 tick of `Brain.step` at the root. Passes if they agree within 10⁻⁸ (max norm).
  In the classifier, H and P for a continuation are built from the same strain-selected float64 brain the
  continuation integrates with, and the root's residual under that brain is recorded (Fable, round 6). Where P's radius and the continuous
  sign disagree, the genome is named.
- **R5, the family of histories.** For every "separate states" genome and 20 fading genomes per graph
  (`default_rng(20261025 + the graph's index)`): nine ramp starts, 0.25 to 1.75 of the final level in steps of 0.1875, each followed
  for 2000 ticks and Newton-located as above. Reported: the number of distinct stable roots reached per genome, as a
  **lower bound** on the states the histories can reach; which starts reach which root; and how many genomes reach
  more than two. Nine starts cannot show a continuum, nor show that two separate runs of starts reaching one root
  are one basin (Astra). So R5 reads only "two states" against "more than two" among those reached. A continuum is
  non-generic for this system, and what would look like one is near-degenerate slow fading (Fable); it is not
  claimed either way.
- **R6, the planted genomes.** The classifier names each planted genome's class exactly, the damped spiral
  included. Passes only if all do.

## Descriptive outputs for the census

- Per graph and group (carriers, cohort, growers, controls): the class counts, and each class's part of the group's
  tick-30 and tick-300 numerators. These are not population rates: the groups are chosen, and the census estimates
  rates.
- Where the growers fall among the classes.
- The forecast and decay-rate comparisons: per class, the Spearman correlation of M1's midpoint forecast of r(30)
  with the observed r(30); for fading genomes, the predicted against the observed late slopes of log |δy|, with the
  cancellations counted. The observed slopes come from a float64 continuation of both histories from tick 300,
  because **the float32 trajectories stall**: the two histories stop at slightly different float32 points near
  their common root, and their read-out difference freezes (in a smoke test on six N2 fading genomes, at 4 × 10⁻⁸
  to 7 × 10⁻⁵; from the float64 continuation, the predicted and observed slopes then agreed to three digits).
- The float32 stall level of every fading genome (|δy| at tick 2000), against 0.1 a. A stalled fading genome is
  "settled" by 03mc's criterion (its range is zero), and if its stall exceeds 0.1 a it is also "remaining", so it
  would enter 03mc's and M1's settling cohort without separate states. The pilot counts such genomes; the census
  must know whether the cohort it inherits is contaminated.
- The tick-30 and tick-300 numerator held by the genomes each check flags: R1's settled genomes that do not reach
  stable roots, R2's unresolved genomes, R3's discordant representatives per variant, and R4's genomes with a
  perturbation that does not return (Astra, rounds 2 and 6).
- Timing per genome and per check, for the census's cost.

## What the pilot hands the census

- the classifier, revised wherever a check fails, and frozen before the census runs;
- the follow-up length: 300 or 2000 ticks, or longer if R2 fails at 2000;
- whether the cheaper "reaches" rule (distance at tick 2000 alone) agrees with the float64 continuation;
- whether the census needs float64, finer integration or fixed batches (R3);
- whether the histories reach two states or more (R5), which decides whether the census counts states;
- the cost per genome.

The census then answers the roadmap's split: how much of N2's excess over the nulls is separate states, and how much
is fading. It runs on randomly sampled graphs per ensemble, the high-settling null graphs, and batch 7's core-frozen
and hub-frozen graphs. Genomes the classifier leaves unresolved enter the split as an explicit uncertainty band, not
as zero.

## Outputs and cost

Scripts in `scripts/memory_m2/` (a README beside them), inside `wormwars.accounting`; outputs in `runs/memory-m2/`
(JSON committed; trajectories and arrays local, the every-tick record of ticks 1801-2000 about 220 MB, Fable). Cost,
from the spike's 22 to 30 s per 64 genomes for 2000 ticks: the main run about 4 minutes; the midpoint Jacobians on
5 × 1024 genomes about 20; R3 about 15; R5 about 10. The float64 continuations of about 900 histories (up to 20,000
ticks for slow roots, plus R1's from tick 300) and R4 (capped at 20,000 ticks) could take hours where roots are slow
(Fable). So the script benchmarks the continuations on the first graph and reports the projection before going on.
Under about 4 hours of CPU is expected; if the projection exceeds 8, the run stops and the caps are revisited. Each oscillation candidate runs
alone: a whole-probe rerun at 64 substeps, up to about 70 s of period search, and a 20,000-tick float64 continuation,
and slow histories with a late range above 10⁻⁴ are candidates too. The projection after the first graph is the
only guard, and N2 may not be representative of the others (Fable, round 6); the stages resume, so a stop loses
little. No GPU. The plan and its scripts are reviewed by Astra and Fable before anything runs, and the results before they
are committed.
