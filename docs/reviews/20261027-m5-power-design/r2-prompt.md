# Design round 2: M5's power calculation — the merged design and a pilot before it

Round 1: both "revise" (`docs/reviews/20261027-m5-power-design/r1-fable.md`, `r1-astra.md`). You agree that no host
count can be given yet, that a pilot must come first, and on most of the rest. Below is the merged design. Points
marked **(choice)** are where you differed or I had to choose; please say whether you accept them. Read-only.

## 1. The control: K\* = M4d's Rr, built on fresh hosts (choice)

Fable proposed K\* as Rr plus N2's autapses, keeping out-strengths (the tighter null). Astra accepted K\* as primary
"with that wording" and noted that Rr keeps each source's outgoing weights while M4e's K shuffles weights globally.
M4d's Rr already is that construction (`scripts/memory_m4/m4d.py`, `rewire(..., keep_recip=True)`): N2's 260 edges
rewired by double-edge swaps at N2's labelled in- and out-degrees, each edge moving with its weight from its source
(out-strengths and each source's outgoing weight collection kept), a swap accepted only if the 75 reciprocal pairs
stay, 20 accepted swaps per edge; and N2's 8 C3 autapses exactly as T (Astra: the actual labelled diagonal, with the
same paired genome signs). So **K\* = Rr**, and the primary estimand is worded (Astra): *T − Rr tests N2's weighted
arrangement inside C3 beyond its labelled degrees, each neuron's outgoing weights, its diagonal and its count of
reciprocal pairs.* It does not separate edge positions from weight placement. The null is defined by the algorithm
(not claimed uniform); the pilot reports chain-length sensitivity (5200 against 10,400 accepted swaps) and each draw's
edge overlap with T (Fable, Astra). M4e's K and the S3-matched control are dropped from M5 (Fable); I is dropped
(T − I has replicated twice). M5 has two arms, T and Rr.

## 2. The estimand and the unresolved genomes (choice)

Fable proposed reading on resolved genomes; Astra showed that conditioning on resolution changes the estimand and can
hide a selection bias as large as the target, even at equal unresolved rates. Merged:
- **Primary:** the share of **all** sampled genomes **confirmed as separate states by the specified protocol** (first
  pass, second pass to 22,000 ticks, audit), unresolved genomes counted as not confirmed; per host, T − Rr; the
  conclusion worded "confirmed by this protocol" (Astra's narrower primary). This is M4e's counted rate.
- **Secondary, reported:** the share **not fading** (separate states + persistent oscillation + unresolved; Fable: it
  has no unresolved problem, and T had 30 oscillations against K's 10); each arm's unresolved share; the resolved-only
  share as a conditional description; the envelope as a sensitivity (scalable version, below).
- **Qualifier, fixed in advance:** if Rr's unresolved share exceeds T's by more than a margin (to be set from the
  pilot), the primary reading is reported "qualified: the control's unresolved genomes could carry the difference"
  (Fable's qualifier, aimed at control-arm enrichment, which Astra notes is what can create a false "raises").

## 3. Target and criterion

- Primary field: **direction**, "raises" if the lower bound of a two-sided 95% interval (hull of host bootstrap,
  stratified within the five ensembles, and Student-t) is above 0: a nominal 2.5% false "raises" at zero (Astra).
- **Planning effect 0.002 at 80% power**, power also at 0.001, 0.003, 0.004 and 90% beside 80% (both). The rationale:
  0.002 is about a third of T − I, the size of each of M4e's three steps, and roughly the smallest effect this
  classifier can resolve (Fable); worth an experiment if two more genomes per thousand switch with N2's exact wiring
  (Astra asked for the rationale to be stated). Not chosen from an observed contrast.
- **Secondary size field:** an exclusion at 0.002 ("no effect of 0.002 or more"), with a scalable guard (below).
  The guard stays on exclusions only, never on direction (Astra).

## 4. The audit (choice)

Each arm's audit sized so that zero transitions bound its rate below 0.001 (about 3000 audited fading genomes per arm;
Fable: a few seconds each). Astra asked for an explicit error budget and for the global fallback (one transition
anywhere reverts every panel to the first pass) to be reconsidered, since at a transition rate of 0.0005 a large audit
detects one about half the time. Proposed: the budget is 0.001 per arm; **on any audited transition, the reading
becomes "classification not validated at the 22,000-tick horizon"**, reported with the first-pass and second-pass
readings beside it, rather than silently reverting. The simulation models transitions, audit detection and that
branch. Is this better than M4e's fallback, or should a transition trigger a further, pre-specified classification of
that arm's fading genomes?

## 5. The pilot (exploratory, before the power calculation; on M4e's ten published hosts)

Both asked for it. Specification, fixed before it runs:
- **(a) Rr panels on M4e's hosts:** for each of M4e's 20 host-draws, one Rr block (seeds in a new family, 20261701 +
  10 (2h + d)) on the same 512-genome panel and signs as M4e's T, classified exactly as M4e (first pass, second pass,
  40 audit ids). Outputs: Rr's rate, unresolved and not-settled shares, T − Rr on 20 host-draws with M4e's T panels
  (paired), shared switch ids (pairing benefit; Fable expects none), S3 and edge overlap with T per draw, and the
  chain-length check (a second Rr block per draw at 10,400 swaps: S3 and overlap only, no panels). About 20 panels at
  0.25 h: about 5 to 6 CPU hours.
- **(b) The longer horizon:** every genome still unresolved after M4e's second pass in T and K (70) and after (a) in
  Rr, continued from its tick-22,000 state to 100,000 ticks and classified by the same rules. Output: how many settle,
  and as what. Stopping rule: one pass, no extension. About 7 to 10 CPU hours (Fable).
- **(c) A large audit:** 1500 fading genomes per arm from M4e's T and K panels and (a)'s Rr panels, drawn by a fixed
  seed (20261801 + arm), continued to 22,000 ticks: the missed-transition rate at this scale. About 4 to 5 CPU hours.
- Nothing in the pilot touches M4e's published reading; its outputs are design inputs, committed with a short note.
  M5's formal hosts will be fresh (a new seed offset), so pilot data never enter M5's reading.

## 6. The power calculation, after the pilot

- **Variance:** fitted on the per-host-draw differences (Fable), a parsimonious contrast model (Astra): host, draw
  (Rr only: T has no block draw; Astra) and genome components, the genome part analytic from the rates with the
  observed pairing; ensembles as fixed strata with equal allocation (Astra); the host component carried as a **range**
  over M4e's T − K, M4d's T − R and T − Rr, and the pilot's T − Rr (Fable's table: the host residual differs about
  tenfold between them), never only by host bootstrap; per-host base rates from a fitted overdispersed distribution.
- **Simulation of the whole procedure:** joint outcome per genome and arm (separate / fading / oscillation /
  unresolved), first-to-second-pass transitions, the audit and its branch, the stratified bootstrap and t hull, the
  qualifier. Scenarios: effects 0, 0.001, 0.002, 0.003, 0.004 on the marginal probability scale of the estimand;
  constant, uniform-random, sparse (each host a responder with probability 0.2), one-ensemble, and ± host effects with
  mean zero; switch-enriched unresolved genomes in T and, separately, in Rr. Grid: H from 10 to 300 in multiples of 5,
  D ∈ {1, 2}, G ∈ {512, 1024}.
- **Answer:** both the fewest hosts and the cheapest allocation reaching 80% at 0.002 under each scenario (Astra),
  with Monte Carlo uncertainty and the selection rule fixed in advance (a cell qualifies if its power's lower 95%
  Monte Carlo bound is at least 0.80), and the range over the host-variance sources. Cost from M4e's measured T and K
  panel times (about 0.25 h per panel with the second pass) plus the pilot's Rr times, the larger audit and any longer
  pass; the probability of exceeding a cap.
- **Scalable rules:** the envelope's bootstrap at its two ends plus a conservative t bound (the all-low mean with the
  largest achievable spread), validated against exhaustive enumeration at H ≤ 12; it is a sensitivity, not computed in
  every replicate. The exclusion's guard becomes a leave-one-host-out check: the exclusion stands only if it holds
  with each host left out in turn.
- **Calibration and sabotage:** simulate M4e's design at the fitted parameters and check that the simulated T − K
  half-width covers the observed 0.0039 and the unresolved rates.
- Script `scripts/memory_m5/m5_power.py`, tests, committed with its output and reviewed (one round on the power
  output, both); then M5's plan and pre-registration, committed and pushed before the formal run; batches registered,
  nothing read before the last batch.

## Questions

1. Do you accept K\* = M4d's Rr, worded as in 1, with T and Rr as M5's only arms?
2. Do you accept the primary "confirmed by this protocol" over all genomes, with not-fading, unresolved share,
   resolved-only and the envelope as secondaries, and the qualifier?
3. The audit: "classification not validated" on any transition, or a pre-specified further classification?
4. The pilot (a), (b), (c): anything to add, drop or fix before it runs?
5. The power calculation's design: anything still missing?

Verdict: agree (the pilot may run) / revise.
