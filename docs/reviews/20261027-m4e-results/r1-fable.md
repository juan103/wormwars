**Verdict: fix then publish.** The reading is the plan's, computed as fixed, and every number I checked traces to the files. What needs fixing is in the interpretation and the M5 guidance, not the data. None of the fixes changes a reading.

## What I verified

- **The reading.** Both fields follow the code's rules exactly as the plan fixed them. Δ_count's size reads "unresolved" because "at least 0.001" holds on the interval but not on the envelope, and no sub-field holds on both. The guard, the coverage response and the global second-pass choice are applied as written. The first-pass reading beside it is right.
- **Numbers.** Every entry in the reading, descriptive, per-host, transition and class tables matches readings.json. S1 to S3 ranges and the medians 1.47, 1.45, 1.53, 1.71 match blocks-summary.json. The predictor medians, AUCs and bands match tables.json. The reciprocal matching is within 2 in all 20 host-draws. I summed the 160 panel times from the log and got 32.5 h with per-arm totals of 3.1 to 3.2 h for the four low arms and 4.5 to 5.4 h for the strong ones. The 6837 second-pass genomes are the sum of the transition tables. Compute, commit, dates and the sha256 match.
- **Rule 1.** No breach. The panel records carry classes, reasons, amplitudes, root distances, read-out differences, write measures, audit ids and a hash. No weights. The K and T degree ranges are the same four integers M4d already committed for R and T. The per-genome predictor for T is one scalar of a sign-flipped block whose sign matrix cannot be rebuilt without the connectome, so it is not invertible in practice.

## Findings, ranked

1. **"M4d's finding is read here as mostly a coupling-strength effect of how concentrated the block's weight is" overreaches, and the draft's own numbers contradict it.** Decompose T − I along the ladder: U_HH − I is −0.0008 (4 against 12), so N2's count and total weight at equal magnitudes add nothing over the intact host. The whole +0.0062 arrives in three steps of about the same size, and two of them hold S1 and S2 fixed:

   | Step | Mean |
   |---|---|
   | W − U_HH (weight shape) | +0.0026 |
   | K − W (labelled degrees, S2 fixed) | +0.0023 |
   | T − K (exact wiring, S2 fixed) | +0.0020 |

   Only the first is a concentration step. Calling the rest "coupling strength" only works if S3 is silently renamed concentration, and the next bullet of the draft then says these arms cannot separate S3 from the degrees. Rewrite the bullet to what the data show: the equal-magnitude arms do not reproduce N2's block's effect, and the effect arrives with N2's weight shape, degrees and wiring, with only the first step resolved on the envelope.

2. **"Each of these moves with S2 and S3" is false for Δ_weight.** From U_HL to U_HH, S2 rises 10 to 20 fold and S3 from 0.21 to 0.78 up to 0.92 to 0.96, and the rate does not move. U_HH is in fact the lowest of all eight arms, below I. The pattern across the eight arms is a floor for every block with S3 below 1 and a rise only in the four arms with S3 above about 1.3. The predictor bands show the same floor below 1.0. Say threshold-like rather than dose. This also strengthens the dose-model paragraph: a log-linear Poisson slope is the wrong shape for a floor and a jump, so the slope is uninformative regardless of which hosts are excluded. The "3 hosts each" for W and K outside the U range should say "of the four hosts with a slope".

3. **The M5 guidance needs three additions, or the power calculation will be mis-specified.**
   - **The unresolved floor.** The envelope shifts each host's difference by the arm's unresolved share, and that shift does not shrink with more hosts. With K's and T's unresolved shares at 0.0036 and 0.0032, "raises" on the envelope needs an effect above about 0.0035 plus the interval's half-width. At the observed T − K of about +0.0016 no number of hosts resolves it under the plan's envelope rule. M5's pre-registration must fix the unresolved rule before the power calculation: either a budget for the unresolved rate with a longer or third pass, or a reading on the resolved genomes with the per-arm unresolved share as its own contrast and the envelope as a sensitivity. I lean to the second. The second pass settled only a third of the unresolved genomes at a cost of about 75 s each.
   - **Match S3.** The plan asked for controls matching "a summary that predicts across constructions". S2 does not predict across the strong arms. S3 orders them, weakly. So the control should be K with S3 matched to T's by rejection among rewirings. K's S3 ranged 1.26 to 1.81 over 20 draws with three at or above 1.67, so matching within 0.05 of 1.71 costs about ten cheap draws per block. Keep unmatched K as the secondary to measure the S3 step.
   - **Pool the variance and state the effect.** M4d's T − R per-host SD is 0.0035 and M4e's T − K is 0.0055, both at 1024 genomes per host. Pooled, about 0.0046, and a 10-host SD has a confidence interval of roughly 0.7 to 1.8 times itself. Hosts for 80% power on the direction field, paired two-sided at 0.05:

   | Effect | SD 0.0046 | SD 0.0055 |
   |---|---|---|
   | 0.0016 (pooled T − K, T − R) | 67 | 95 |
   | 0.002 | 44 | 62 |
   | 0.003 | 20 | 28 |
   | 0.004 | 12 | 17 |

   At about 1.05 CPU hours per host for two T and two K panels with the second pass, that is 45 to 100 hours for the realistic effect. One K draw per host suffices: M4e's two K draws differ about as binomial noise predicts. Genomes buy little: at these rates 1024 genomes contribute about 40% of the host-difference variance, so doubling them cuts the SD by about 10%. The plan's "more hosts, not more genomes" is right. Reuse the coverage simulator with host count and unresolved counts as parameters rather than the formula.

4. **The interaction's caveat is missing.** Its interval is below zero but its envelope reaches +0.0001. "The interaction is negative" needs "on the counted genomes, not over every assignment".

5. **Say that Δ_count's envelope clearance is thin.** The envelope's upper bound of −0.0004 is about four genomes in 10,240, and it cleared zero because the second pass settled two of U_HH's five first-pass unresolved genomes. The draft reports both facts separately. Put the link in "In short" so a reader does not weight the envelope direction as if it were comfortable.

6. **"Among genomes with the same predictor band, K and T still switch more than U_LH and W" holds only in the band above 1.2.** In the 1.0 to 1.2 band the four arms are at 0.30%, 0.17%, 0.32% and 0.31%. Restrict the claim.

7. **Minor wording.** 32.7 h is just under the plan's 33 to 34, not "within". The audit bound is 0.0037 to 0.0038 across arms. The low-arm switches sit in the three hosts where I itself switches, which supports reading them as a host property and the low arms as a floor; one sentence after the data would help. The per-host pattern and the dose-exclusion observations are fair as written.