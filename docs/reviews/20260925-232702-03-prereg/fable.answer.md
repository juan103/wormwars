I've finished reading the pre-registration, the run and report code, the verdict and measures modules, the samplers, the committed inputs, and the D050–D053 history. Writing up the review now.

**Bottom line:** the primary verdict path matches sections 4–6 closely, exchangeability is delivered in substance, and the budget arithmetic checks out. Two registered rules are not implemented in the report code, the power section leaves out things a reader needs, and one cheap ordering change closes the main remaining loophole. Fix points 1, 2, 7 and 8 before the run; the rest can be wording.

**Q1. Does the code compute what §4–6 say?**

1. **MAJOR. The exclusion rule of §5 is not implemented in the report path, and an excluded graph silently kills verdicts.** `report.py:41-44` computes the P1/P4 ratio with no denominator threshold; only the pilot's `signals()` at `scripts/exp03.py:250-258` has the 10⁻⁴ rule. If any graph is non-finite: `report.py:84` filters `ev` for the rank test, but `report.py:85` (mean SE²), `report.py:87` (effect interval) and `report.py:104` (the list handed to `classify`) are unfiltered, so the margin, interval and quantiles become NaN and that ensemble can only return "inconclusive". A finite but tiny denominator is worse: the graph stays in with a huge ratio and shifts the rank, the mean and the interval. And if N2 itself is NaN, `verdict.py:21-27` gives r = 0, p = 1/129, which then feeds Holm and loosens the other two signals' thresholds. Trigger probability is low (pilot denominators sit far above 10⁻⁴) but the failure mode changes verdicts. Apply one validity mask per signal to every path, withhold when N2 is invalid, and report the counts §5 promises.

2. **MAJOR. Completeness is recorded but not enforced.** `scripts/exp03.py:429-432` counts *measured* graphs, not valid ones, and `build` prints and saves "overall" verdicts regardless. §6 says the verdict is withheld. Also unspecified: what Holm does across three signals when one is withheld (I'd keep the divisor at 3).

3. MINOR. §4 says N2's calibration is validated on 2 048 independent genomes and reported. Nothing in `measure_graph` does this (`scripts/exp03.py:158-161`), and only the gains are saved, not the achieved drive the design promised as a covariate. Either implement it or delete the sentence.

4. MINOR. §4 says the first 256 probe genomes serve every secondary condition. True for R1, R2, MS and gaps-off; the uniform and permuted modes at `scripts/exp03.py:205-209` are a fresh `Genome.random` of 256 with the same seed, and a 256-row draw does not align with the first 256 rows of a 2 048-row draw. Descriptive only, but the text is wrong. Build them from `small_g` by replacing magnitudes and keeping signs, or say they are unpaired.

5. MINOR. The measurement-SE bootstrap size and seed are unregistered: `report.py:64` uses 1 000, `scripts/exp03.py:294` (the pilot's τ) used 2 000. `--boot` can also change the effect interval from the command line. Fix both in the text.

6. MINOR. §6.2 says the margin uses no N2 data. The common world profile at `report.py:73` includes N2, N2-rev and N2perm (4 of 646 graphs). Harmless, but say "negligibly".

**Q2. Exchangeability**

7. **MINOR but change it: measure N2 last, not first.** `run_order` at `scripts/exp03.py:396-401` puts N2 first, so every mid-run decision §9 allows (which bugs count, whether to fix, whether to stop) is made with N2's numbers on disk. Exempt N2 from the cap and put it last. Zero cost, and it removes the only human choice that can still see N2 before the ensembles are done.

8. MINOR. No rule for a graph whose calibration fails. `calibration.py:252` raises after 8 iterations or at the 40× gain cap. SH-route and SH-mirror graphs have never been calibrated (the pilot used SH only). Register: exclude and count, or rebuild with the next seed, and what happens if it is N2.

9. MINOR. Nothing verifies the graph files against `graphs_manifest.json` at load time (`scripts/exp03.py:145-146`), and no committed code produced the manifest. Add a hash check that fails loudly. Note I could not verify the sha256 prefixes in §3 myself (no shell in this review).

10. MINOR. The design promised median pairwise Jaccard within each ensemble as a mixing diagnostic. `ensembles.json` has only Jaccard to N2. The plateau check is weaker evidence that the chains are exchangeable draws rather than "20 passes from N2". Compute it from the manifest graphs before the run.

What is fine: seeds hash the whole name and are pinned by a test; worlds and run seed match; calibration genomes share seed 0 across all graphs, which is symmetric because degree preservation gives identical draw shapes; the stimulus bank is shared; N2 runs through the same `with_masks` and `BrainSpec` path; the interleaved order and even-stop rule are correct. Residual asymmetry that is by design and disclosed: N2 keeps anatomical weights on their own edges and every ensemble permutes them, so the null tested is "topology plus weight placement", with N2perm only descriptive. §2 should say that in one line.

**Q3. Forking paths**

11. MINOR. None of the secondary signals in §5 (P2, ensemble-mean P2 against zero, T0 mean and top decile, coverage, absolute responses, P1 variants, P4 decay, N2-rev and N2perm ranks) is computed by `report.py`. Their operationalisation, including what "SE" means for a top-decile mean, will be written after the data exist. Implement them now or move them to §11.

12. MINOR. "Distinctive" and "reversed" are each tested at 0.05, so the two-sided rate per signal is 0.10. Defensible since only one direction is predicted, but state it.

13. MINOR. The margin can collapse to zero when var(values) < mean SE² (`report.py:86` clips at 0), which is plausible for P3 at reliability 0.41. Then "distinctive" needs only an interval excluding zero. The rank test still gates it, so this is not a loophole, but say it.

**Q4. Power and cost**

14. **MAJOR. The power section omits the probability of "consistent", and for P3 it is low even when N2 is a true member.** Under exchangeability, with the pilot's SEs and spreads, N2's 90% interval fits inside the ensemble's central 90% roughly 68% of the time for P1, 30% for P3 and 87% for P4. So the modal P3 outcome is "inconclusive" under the null and under most alternatives. §10's reading of "consistent" needs this next to it, and the simulation at `scripts/exp03.py:356-389` can produce the numbers.

15. **MAJOR. The P4 power table is in latent-SD units that exceed the signal's ceiling.** P4 is |final| over steady contrast (`measures.py:113-117`); the pilot mean is 0.78, SD 0.074, maximum 0.86. z = 3 is a ratio of about 1.00, and z ≥ 4 is above 1.08, which random brains are unlikely to reach. Restate the P4 rows in ratio units and say the attainable range tops out near z ≈ 3.

16. MINOR. No expected effect sizes. 02's M0 signed-over-common ratio for N2 is about 0.10 against a pilot mean near −0.004 and τ = 0.032, so z ≈ 3 and P1 is roughly a coin flip at the registered rule. 02b's gen-0 history numbers are absolute differences from a different bank, so P4's expected z is unknown. Say both.

17. MINOR. The simulation places N2 z SDs above every ensemble with one τ and SE. Real ensembles differ, so the effective z is the smallest across the five. One sentence.

18. MINOR. "Reliability 0.9 for P3 would take about 75 GPU-hours" looks low. From the pilot's components (genome 0.0174, world 2.4e-5, residual 0.0124) reaching SE² = τ²/9 needs about 3 300 to 4 500 genomes per P3 cell, roughly 110 to 150 GPU-hours. Check the arithmetic; the conclusion (not bought) stands.

19. Fine: 111 s × 645 = 19.9 h matches `pilot.json`; the cap leaves room; per-graph cost is structure-independent; the P3 SE from variance components is within about 4% of what the joint bootstrap will produce, so the simulation's interval condition is a fair approximation. Worth running: P1 and P4 are well measured, P3's minimum detectable effect (about 0.04 on a T1 score scale of about 0.8) is honestly stated, and the ensembles are reusable. State the score scale so "0.043 score units" can be judged.

**Q5. Must change before the run**

- Point 1 (validity mask everywhere, N2-invalid withholds, counts reported) and point 2 (withhold on incompleteness, Holm rule when withheld), with a test for each.
- Point 7 (N2 last, exempt from the cap) and point 8 (calibration-failure rule).
- Points 14 and 15 in §7, and point 3's sentence in §4.
- Points 5, 9, 11 and 12 are cheap and should go in the same commit.

What is fine and checked: rank p, intersection-union then Holm (thresholds r ≤ 1, 2, 5 of 128), the joint bootstrap with shared world indices, the crossed SE with the shared world profile removed, the verdict ordering and its mutual exclusivity, the P1/P3/P4 definitions against §5, the five fitness cells and genome allocations, the history-probe parameters and bank value, and every number I could check in §1, §3 and §7 against `ensembles.json` and `pilot.json`.