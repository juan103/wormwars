# M1: accounting, amplitude and the cheap kills — the plan

*Draft 1, 2026-10-20. Exploratory: nothing here is a pre-registration. This plan fixes the definitions, panels and
decision rules before the analyses run, as [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md) asks ("the definition of settling
fixed in advance"; formulas "frozen before validation"). Anything changed after seeing data is labelled as such in the
results. CPU only.*

## What M1 must decide

The roadmap's two decision points for M1:

- **D1, amplitude.** Does N2's lead in the registered share vanish when the genomes are compared at matched amplitude
  across graphs? If so, the focus moves to the size of the response.
- **D2, alignment.** Does the change in alignment with the turn read-out carry N2's excess, rather than the
  persistence of the activity difference itself? If so, the focus moves from a store to read-out geometry.

M1 also hands M2 an estimate of how much of the lead comes from settling genomes (03mc's census as a proxy), runs the
cheap kills from round 3, and runs M3's anatomy predictors, frozen here.

## Definitions (fixed)

From 03mc ([`scripts/p4mc.py`](../../scripts/p4mc.py), `REGISTERED` and `summarise`), unchanged:
- **The history difference** of genome *i* at tick *t* of the follow-up: δy_i(t), the raw turn read-out of the rising
  history minus the falling one. a_i = |δy_i(0)|, the difference at the ramp's end.
- **The share** at tick *t*: mean_i |δy_i(t)| / mean_i a_i, over all genomes. The primary tick is 30 (03mc's Q-D);
  ticks 100 and 300 are secondary.
- **Eligible:** a_i ≥ 10⁻³. **Per-genome retention:** r_i(t) = |δy_i(t)| / a_i, eligible genomes only.
- **Remaining:** eligible and |δy_i(300)| > 0.1 a_i. **Settled:** the state's largest range over the last 10 ticks of
  a 300-tick follow-up is below 10⁻⁴ (03mc's `_Range`). **Settled with separation:** settled and remaining. This is
  the settling definition for M1, on 03mc's arrays and on the fresh panels alike.
- **Activity** a = tanh v. The turn read-out is cᵀa, with c = +1/4 on SMDDL, SMDDR, RMDDL, RMDDR and −1/4 on SMDVL,
  SMDVR, RMDVL, RMDVR (`wormwars/exp03/measures.py`, `_readout`). So, exactly,
  |δy(t)| = ‖c‖ · ‖δa(t)‖ · |cos θ(t)|, where θ is the angle between δa and c.

## A. Accounting on 03mc's arrays (seconds)

Inputs: `runs/p4mc/arrays/N2__long.npz` and the 640 `graph__<ensemble>-<id>__long.npz` (2048 genomes each, local),
and `experiments/03mc-p4-confirm/measurements.json`. For every quantity: N2's value, each ensemble's median and
range, and N2's rank among the 128 graphs of each ensemble.

- **A1, the decomposition** on eligible genomes: share = E[r] + Cov(a, r) / E[a] (exact on that set). Plus the
  ineligible genomes' fractions of the overall numerator and denominator.
- **A2, amplitude standardisation.** Pool the eligible a_i of all 641 graphs and cut them at their deciles. For each
  graph, the standardised share is Σ_k π_k E[|δy(30)| | k] / Σ_k π_k E[a | k], with π_k = 0.1 the pooled proportions;
  an empty decile in a graph is reported, and that graph's standardised share is computed over the deciles it has.
  Also the per-decile share, N2 against each ensemble.
- **A3, overlap of contributors:** the fraction of the top 10% of eligible genomes by |δy(300)| that are also in the
  top 10% by |δy(30)|.
- **A4, trimming:** the share at tick 30 after removing each graph's top 2% and top 5% of genomes by |δy(30)|
  (removed from numerator and denominator).
- **A5, the settling proxy:** the settled-with-separation genomes' fraction of the tick-30 and tick-300 numerators,
  and the share at ticks 30 and 300 with them removed.

## B. Fresh CPU panels

**Graphs.** N2; **4 randomly sampled graphs per ensemble** (20), drawn with `numpy.random.default_rng(20261020)`
from each ensemble's 128 graphs after removing the selected ones; and **the selected graphs**, kept apart in every
summary: per ensemble, the graph with the highest 03mc tick-30 share and the graph with the most genomes settled
with separation (the next by settled count if they coincide), 10 in all. 31 graphs. Null-ensemble summaries use the
20 random graphs only; the selected ones are reported beside them.

**Genomes.** 1024 per graph, `Genome.random` with seed 7600 (fresh; CPU genomes are not 03mc's CUDA genomes). N2 also
gets a second panel, seed 7700, to show N2's own panel-to-panel spread. Graph-to-graph spread within an ensemble is
reported beside the within-graph bootstrap error.

**The probe** is 03mc's (warm-up 100 ticks at 0.25× or 1.75× the final food level, a 10-tick ramp, a 300-tick
follow-up at the final level, T1's 32 substeps), via `scripts/memory_spikes/spikes.py`, extended to record δv and δa
at ticks 0, 10, 30, 100 and 300 and the settling range. The interventions at the ramp's end run as extra row pairs
in the same batch, so every arm shares the intact arm's warm-up and ramp.

- **B1, persistence against alignment (D2).** Per genome, r = n · α with n = ‖δa(t)‖/‖δa(0)‖ and
  α = |cos θ(t)|/|cos θ(0)|. For a graph, with weights w_i = a_i / Σ a, share = Σ w_i n_i α_i. Write
  N = Σ w_i n_i (the amplitude-weighted activity retention) and A = share / N (the alignment factor, a weighted mean of
  α). Then, exactly, log(share_N2 / share_G) = log(N_N2 / N_G) + log(A_N2 / A_G) for each null graph G. Reported at
  ticks 30 and 100, on all genomes and on the top quartile by a.
- **B2, settling on the fresh panels:** counts, the settled genomes' numerator fraction, and the share without them,
  as A5.
- **B3, the amplitude arm (D1).** At the ramp's end, each pair is also continued with its difference scaled about
  the midpoint, v± ← m + k (v± − m), k ∈ {0.25, 0.5, 2} (k = 1 is the intact arm), on N2 and the 20 random graphs,
  with a 30-tick follow-up. Reported per k: the actual ‖δv(0)‖, ‖δa(0)‖ and a, and the share at tick 30; the median
  within-genome ratio r(k = 2) / r(k = 0.5); and an amplitude-standardised share as in A2, pooling each graph's
  genomes over all four k and cutting at the pooled deciles of a over N2 and the 20 graphs.
- **B4, the cheap kills** (N2 and the 20 random graphs unless stated):
  - **complement erasure:** at the ramp's end, every neuron outside a set is set to its two rows' midpoint; the share at
    tick 30 against the intact a. Two sets: batch 6's `top30_start` (chosen from N2's own residual, so labelled
    result-defined) and the anatomy core of C3 below. The erasure of each set itself runs beside it, for contrast.
  - **the gap dissipation ratio:** δvᵀ L_G δv / ‖δv‖², with L_G the graph's gap Laplacian under the genome's gap
    weights, at ticks 0 and 30, as a median and as an a-weighted mean. Fable's kill: if N2's ratio is not below the
    nulls', the gap-geometry idea's strong form is dead.
  - **the left-right antisymmetric share:** over the 99 mirror pairs (L/R names), Σ (δv_L − δv_R)² / 2 over
    Σ (δv_L² + δv_R²), at tick 30. Fable's kill: under 10% and N2's antisymmetric part no slower than the nulls':
    dead.
  - **the tau controls:** two more genome sets per graph, with the same seed: each genome's taus permuted across its
    neurons (seed 7601), and each genome's taus all set to its geometric mean. Full probe, 30-tick follow-up. If N2's
    lead survives both, the tau lottery is dead.
  - **growers and the forecast** (Fable): the midpoint Jacobian at the ramp's end (batch 3's method), on 512 genomes,
    for N2 and one random graph per ensemble. The fraction of genomes whose linear state norm grows over 10 ticks with
    spectral radius below 1 (Fable: under 2%, the transient-growth family is dead); the fraction of output growers
    (r(30) > 1) with radius below 1; and the Spearman between the linear forecast and the observed r(30), excluding the
    genomes with radius above 1.

## C. M3's anatomy predictors (minutes; frozen here)

For each of the 641 graphs, on the binary chemical adjacency without autapses; R is the 8 turn read-out neurons, S
the 6 food sensors (AWAL, AWAR, AWCL, AWCR, ASEL, ASER):
- **C1, local density** (Fable): K = R with its one-step and two-step chemical in-neighbours; the number of edges
  inside K over |K|(|K| − 1). **C1′**, the same count over its configuration-model expectation,
  Σ_{i,j∈K, i≠j} k_out(i) k_in(j) / E, where E is the graph's edge count.
- **C2, write-read walks** (Fable): w = 1_Sᵀ(A + A²), the walks of length 1 or 2 from S; r = (A + A²) 1_R, the walks
  of length 1 or 2 into R; C2 = log Σ_j w_j r_j.
- **C3, the anatomy core** (for B4's complement erasure): N2's K ranked by degree inside K (in plus out), the top 30,
  ties broken by name.

Spearman correlations within each ensemble (128 graphs) between C1, C1′, C2 and four outcomes from 03mc: the
tick-30 share, the upper quartile of r(30), the settled-with-separation count, and the growth fraction (r(30) > 1).
Reported on all 128 and on the two halves by graph id (even and odd), with N2's percentile on each predictor. **No
veto** (roadmap, M3): a weak correlation rejects that predictor, not a structural handle.

## Decision rules (fixed)

- **D1:** let f be the fraction of N2's excess over the median random null graph that remains after amplitude
  standardisation: f = (std share_N2 − median std share_null) / (share_N2 − median share_null). Computed on A2 (03mc's
  arrays, natural amplitudes) and on B3 (scaled amplitudes). **The lead vanishes at matched amplitude** if f < 0.25 in
  both; **it survives** if f > 0.75 in both; otherwise it is partial and both numbers are reported. Only "vanishes"
  changes the plan.
- **D2:** the median over the 20 random graphs of log(A_N2 / A_G) / log(share_N2 / share_G) at tick 30, on all
  genomes. **The alignment term carries the excess** if this is above 0.5 and the same holds on N2's second panel
  (seed 7700) against the same graphs. Only then does the focus move to read-out geometry.
- **For M2:** A5 and B2 give the settled genomes' fraction of N2's excess, compared with their fraction in the
  nulls. M2 measures it properly; M1 reports the proxy.
- Every other number is descriptive.

## Outputs and cost

Scripts in `scripts/memory_m1/` (a README beside them); outputs in `runs/memory-m1/` (JSON committed, logs local); the
results on `docs/memory/M1-RESULTS.md`, reviewed by Astra and Fable before they are committed as findings. The cost is
estimated from the spike timings, not measured: A and C take minutes; B about 2 to 3 hours of CPU (31 graphs × 1024
genomes × 410 ticks, the in-batch arms, the tau controls and five Jacobian panels).
