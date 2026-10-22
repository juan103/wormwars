# M3: a core defined without the result — closed as a completed screen

*2026-10-22. Exploratory. The direction (close M3 on M1's part C plus one table; M4's first slice next) was agreed
with Astra 6 and Fable 5.1 in one round, and this note checked in the next (with the M4a plan, round 1; one wrong
sentence about the selected graphs corrected) ([`docs/reviews/20261022-m3-m4-direction/`](../reviews/20261022-m3-m4-direction/)),
both "revise" with corrections taken here. Step M3 of [`MEMORY-ROADMAP.md`](MEMORY-ROADMAP.md).*

## What M3 asked, and where it was done

The roadmap's M3: define a core from the anatomy alone, correlate anatomy predictors within ensembles with the
outcomes across 03mc's 640 graphs, inspect the top graphs, and freeze any formula before validating it on unused
graphs. **M1's part C did this** ([`M1-RESULTS.md`](M1-RESULTS.md), "Part C"; `runs/memory-m1/anatomy.json`), with
its predictors fixed in M1's plan before they were computed:
- K, the turn read-out with its one-step chemical in-neighbours; C1, the density inside K; C1′, the same against a
  stub-model expectation; C2, the write-read walks from the food sensors to the read-out;
- **C3, the anatomy core:** the top 30 of N2's K by internal degree. It is **a core from N2's anatomy**, a fixed set
  of N2's neurons, not a rule applied to each graph (Fable). It shares 18 neurons with batch 7's `top30_start`, the
  core chosen on the result, and 5 with batch 7's hubs.

M1 found that N2 is outside the null graphs' range on local density (K smaller, C1 and C1′ larger than every null
graph), and that **within ensembles the tested predictors have no strong association** with the share, the upper
quartile, the settled cohort or the growth fraction (Spearman −0.19 to 0.21 over all 640 graphs, unstable between
halves).

**Scope, not a null** (Fable, Astra): N2 lies outside the nulls' range on all three measures, so variation within the
null ensembles cannot test whether N2's own density is the handle. M3 is closed as a completed screen of these
predictors, not as a finding that no structural handle exists. The roadmap's "no veto" stands: this does not cancel
M4's interventions or a controlled transplant.

## One addition: the frozen predictors against M2's census measures

Description only, no simulation, no new formula ([`scripts/memory_m3/close.py`](../../scripts/memory_m3/close.py);
`runs/memory-m3/close.json`, printed in `runs/memory-m3-close.txt`). The measures are M2's per-graph census values:
the fraction of eligible genomes with separate states, S(30), fading retention ρ_F(30) and the share s(30). One new
quantity, labelled so: **C3_kept**, the fraction of N2's chemical edges inside C3 that a graph keeps (N2-relative).

| | K | C1 | C1′ | C2 | C3_kept |
|---|---|---|---|---|---|
| N2 | 84 | 0.118 | 1.72 | 10.32 | 1 |
| 30 reference graphs (median) | 133 | 0.069 | 1.05 | 9.90 | 0.142 |
| N2's rank against them | smaller than all 30 | above all 30 | above all 30 | above 29 | above all 30 |
| 10 selected graphs (range) | 119 to 140 | 0.062 to 0.091 | 1.03 to 1.16 | 9.75 to 10.39 | 0.11 to 0.21 |
| Core-frozen shuffles (3) | 117 to 120 | 0.077 to 0.082 | 1.07 to 1.09 | 10.15 to 10.29 | 0.58 to 0.60 |
| Hub-frozen shuffles (3) | 129 to 138 | 0.065 to 0.068 | 1.03 to 1.06 | 9.82 to 9.94 | 0.29 to 0.32 |

- **Over the 30 reference graphs** (six per ensemble, pooled), the Spearman correlations of the predictors with the
  four census measures run from −0.17 to +0.46. The largest are C2 with ρ_F(30) and with s(30) (+0.46 each), C1′
  with the separate-states fraction (+0.36), and C3_kept with ρ_F(30) and s(30) (+0.32). Thirty graphs, 19 with no
  separate states, and pooled across ensembles: weak to moderate associations, not tests. M1's within-ensemble
  correlations on 640 graphs, the better-powered measure, were at most about 0.2.
- **Batch 7's arms:** the core-frozen shuffles sit above the hub-frozen ones on C1, C1′, C2 and C3_kept, and they
  keep more separate states and more fading retention (M2). The density difference is largely by construction (the
  frozen core is a dense set of N2's head neurons), and all six arms remain far from N2 on C1 (0.065 to 0.082
  against 0.118). Three graphs per arm.
- **The selected graphs,** chosen in 03mc for their share or their settled cohort, are not distinguished by these
  predictors: their values overlap the reference's, a few lying just outside it (C1 up to 0.091 against the
  reference's largest 0.086, C2 up to 10.39 against 10.35, C3_kept down to 0.112 against 0.123; Fable, Astra).

## What M3 hands to M4

- **C3, frozen,** as the anatomy-defined set of N2's neurons for M4's interventions, distinct from batch 7's
  result-defined `top30_start`. The eight read-out neurons lie inside C3, so "C3's internal edges" includes the
  read-out's own afferents within it (Fable).
- No within-ensemble anatomy predictor to carry forward; the structural question moves to M4's interventions on the
  wiring itself.
