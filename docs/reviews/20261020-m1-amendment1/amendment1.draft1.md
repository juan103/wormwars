## Amendment 1, 2026-10-20: D1's targeted replication (written after M1's results, before it runs)

*Added after M1's results ([`M1-RESULTS.md`](M1-RESULTS.md), D350); nothing above is changed. Exploratory, as M1.
The plan says an inconclusive rule changes nothing until a targeted replication resolves it. D1 was inconclusive on
its coverage condition: with k ≥ 0.25, N2's genomes in B3's used strata (a below 0.087) held only 34% (seed 7600) and
41% (seed 7700) of N2's intact-arm tick-30 numerator, against 75%. Both reviewers asked for smaller k on N2 only, with
coverage against the original population and the vacuous balance condition addressed (M1-RESULTS, "What this
changes").*

**What runs.** N2's two panels only (seeds 7600 and 7700, 1024 genomes each, M1's probe unchanged). The arm batch at
the ramp's end holds M1's four amplitude arms (k = 1, 0.25, 0.5, 2) and four new ones, **k = 1/8, 1/16, 1/32 and
1/64**, each scaling the difference about the midpoint as in B3, followed for 30 ticks. The erasure arms and the lone
300-tick run are not repeated. The new k come from M1's arrays: in N2, the genomes needed for 99% of the numerator have a
up to 2.57 (seed 7600) and 1.96 (seed 7700), which k = 1/32 brings below 0.087. Octave steps put every large genome's
a(k) in the used range for at least one k, if a(k) is close to linear in k (at k = 0.25, N2's mean a is 0.29 of its
intact mean). The null graphs are not rerun: a smaller k there would push most null genomes, mean a 0.021, below the
eligibility floor and change their population (Fable).

**The check before use.** In the rerun, the four arms that M1 ran must reproduce M1's arrays genome by genome (a and
|δy(30)|): with M1's batch policy, the run stops if more than 1% of genomes differ by more than 10⁻³; the largest gap
is reported. The four original arms are then taken from M1's arrays, so the population and the observations M1
analysed are unchanged; the rerun supplies only the new arms.

**Fixed from M1, not recomputed:**
- **the population:** N2's genomes eligible at every original k (a ≥ 10⁻³ at k = 0.25, 0.5, 1 and 2), 919 and 926
  genomes. A new arm's observation enters only if its own a is at least 10⁻³. Below the floor it is dropped, never put
  in stratum 0, and the genome stays in the population;
- **the strata, the used strata and the weights π:** M1's (`summary.json`, `D1_B3_a`: `edges`, `used_strata` 0 to 9,
  `pi`; and `D1_B3_da` for the ‖δa(0)‖ basis). The null graphs' observations and per-stratum values are M1's;
- **the reference:** the 30 random graphs' panels from M1, with the same B3 population.

**Computed as in D1, with N2's new observations added:**
- N2's per-stratum E[|δy(30)| | k] and E[a | k] are over all its observations in that stratum, the old and the new
  arms together. N2's genome count per used stratum is reported; it can only rise;
- the standardised share, the baseline (N2's observations in the used strata, old and new arms) and f = (standardised
  share_N2 − median standardised share_ref) / (baseline share_N2 − median baseline share_ref), on each N2 panel;
- the interval: M1's bootstrap (2000 resamples; one set of genome indices shared by N2's seed-7600 panel and the null
  panels, an independent one for seed 7700; graphs resampled within ensembles), with a fresh generator,
  `default_rng(20261022)`. A genome's arms are resampled together, the new ones included.

**The conditions** (all on both panels):
- **lead:** N2's baseline share at least 1.1 times the reference median (as M1);
- **coverage, against the original population:** an N2 genome of the population is covered if any of its eight arms
  above the floor falls in a used stratum. The covered genomes must hold at least 75% of N2's intact-arm tick-30
  numerator and 75% of its intact-arm denominator, both over the whole population;
- **balance, replacing M1's.** M1's condition looked only at used strata holding at least 10% of N2's *whole* pooled
  numerator, most of which lay in dropped strata. No used stratum reached 10% (the largest held 4.3% and 5.2%), so it
  tested nothing (`check_b3_balance.json`). Now: in every used stratum holding at least 5% of N2's numerator *within
  the used strata*, N2's E[a | k] must be within 25% of the reference median's. Every used stratum's ratio is
  reported, with the numerator-weighted mean imbalance.

**The readings** (M1's rule, unchanged):
- **Fires:** f's interval lies wholly below 0.25 on both panels. Wording: "at matched amplitude across graphs, most of
  N2's tick-30 lead is accounted for by amplitude (accounting, not mechanism)".
- **Does not fire:** f's interval lies wholly above 0.25 on both panels. Wording: "amplitude does not account for most
  of N2's tick-30 lead; at matched amplitude more than a quarter of it remains". Whether f exceeds 0.75 is reported
  descriptively.
- **Otherwise inconclusive,** as it is when a condition fails. The A2 check cannot intervene: every ensemble was
  unsupported in M1, and A2 is not rerun.
- **If it is inconclusive again,** D1 stays open on this probe. No further replication is planned, and M2 is not held
  for it.

**What the small arms measure** (stated before the run):
- shrinking the difference to between 1/64 and 1/8 of its size about the midpoint probes N2's genomes close to their
  linearisation there;
- where the midpoint expands (finding 2; M1's growers), a small difference can grow toward a basin, so a genome's
  retention at small k can exceed its retention at natural amplitude. The comparison is still the matched one D1 asks
  for, but at matched a, N2's observations come mostly from strongly shrunk arms and the nulls' from natural or
  enlarged ones;
- reported per stratum: the k composition. Reported for N2: the fraction of its used-strata numerator from each k;
  its share against each new arm's own start; the median within-genome ratios r(1/64)/r(1/32) and r(1/8)/r(1/4), as
  a sign of linearity and of float32 rounding at the smallest k. Neither ratio gates the reading;
- beside it, descriptive: the standardised lead against M1's intact eligible lead (0.444 − 0.275 on seed 7600), and
  the same computation on the ‖δa(0)‖ basis.

**Checks that can fail** (in the script's tests, run first): with the new arms left out, the computation must
reproduce M1's point values (N2's standardised and baseline shares, the reference medians, f and the coverage, on
both bases and both panels) from M1's arrays; a new observation below the floor must not enter stratum 0; the new
balance rule must fail a constructed heavy stratum that is out of balance.

**Script and cost:** `scripts/memory_m1/d1_small_k.py`, inside `wormwars.accounting`; output
`runs/memory-m1/d1_small_k.json` (committed), the new arms' arrays `runs/memory-m1/d1_small_k/*.npz` (local). Two
panels with 8 arm pairs for 30 ticks: a few minutes of CPU. This amendment, the script and its tests are reviewed,
committed and pushed before it runs.
