**Verdict: fix then publish.** The primary reading is correct. The necessary changes concern interpretation and M5 planning, plus a few technical wording fixes.

I regenerated all 20 host–draw constructions, validated all 160 panels, and reproduced the readings, first-pass comparison, audit, transitions, dose model, predictor tables, block summaries and block-file digest exactly, in memory with filesystem writes blocked. I also checked the draft’s counts, ranges, timings and M4d comparison against the records.

1. **High priority: remove “mostly a coupling-strength effect.”**

   [The roadmap interpretation](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:219) goes beyond what these contrasts establish.

   “Concentration matters” is defensible **as an operational description of these interventions on C3**: spreading fixed weight over more equal-magnitude edges lowers the rate, and introducing uneven weights on fixed support raises it. Neither establishes how much of M4d’s transplant benefit concentration explains. T − K remains unresolved, including effects large enough to matter substantially.

   Suggested replacement:

   > Changing weight concentration changes switching frequency, making a coupling-based explanation of the transplant benefit plausible. How much of that benefit it explains remains unresolved.

   Also change “did nothing measurable” to the actual Δ_weight reading, and qualify “the interaction is negative”: its counted interval is negative, but its envelope reaches **+0.0000935**. The interaction’s direction therefore does not survive the unresolved-genome analysis.

2. **High priority: M5 needs two explicit estimands, and 0.0055 is only a starting variance estimate.**

   [The M5 paragraph](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:244) only partly implements the plan’s “After the reading” rules. It omits the required distinction between **total wiring advantage and residual advantage beyond a coupling summary**.

   A suitable distinction is:

   - **T − K:** advantage over the specified degree-and-weight-matched null, including differences mediated by S3.
   - **T − K with an additional prespecified S3 match:** residual advantage beyond that summary.

   Matching S3 changes the question: S3 itself depends on wiring. A null residual after matching it would not establish that wiring has no total effect. T − I measures the transplant benefit and should not substitute for an exact-wiring contrast.

   Furthermore, current T − K includes **autapse differences**—T has eight, K has two to four—and **reciprocity differences**, 75 versus 34–44 pairs. Calling it an advantage of the exact off-diagonal wiring alone would be wrong. M5 must either control those features or explicitly retain a package estimand.

   The observed SD **0.0054664** is correct, but it is the SD of estimates based on **two draws × 512 genomes**, not pure between-host heterogeneity. My rough method-of-moments decomposition gives approximately **51% host, 8% draw and 41% genome-sampling contributions** to that observed variance. These estimates are very uncertain with ten hosts and two draws.

   Therefore replace “more hosts, not more genomes” with a qualified allocation statement: prioritize independent hosts, but compare host/draw/genome allocations using the paired data. The present data do not justify treating additional genomes as useless.

3. **Medium priority: the strong-arm comparison does not demonstrate failure of a common predictor curve.**

   [“The summaries do not collapse the strong arms”](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:229) is too categorical.

   Similar medians do not mean matched predictor distributions. The reported upper band is **[1.2, ∞)**, a broad interval. Within it, predictor medians are approximately **1.38, 1.39, 1.42 and 1.46** for U_LH, W, K and T. Host composition also differs after conditioning on that band.

   The reported counts and rates are correct. They show descriptive differences; they do not establish an arm effect conditional on the predictor. Suggested wording:

   > Similar summary values coexist with different counted switching rates. These comparisons do not establish whether a common relationship with the summaries explains those differences.

   The subsequent caveats about K − W and T − K should remain. Also avoid presenting “S3 or labelled degrees” as exhaustive alternatives: weight placement, reciprocity, autapses and other topology remain entangled.

4. **Medium priority: correct the predictor’s definition.**

   [Line 208](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:208) says “largest real eigenvalue.” The implementation computes **the largest real part of the eigenvalues**, `ev.real.max(1)`. These differ when the leading eigenvalues are complex. Stage 0 separately computes the largest purely real eigenvalue; the tables use the former.

   All quoted predictor medians, AUCs and band counts match the generated tables.

5. **Lower priority: clarify the dose interpretation and small reporting details.**

   The six excluded hosts really do have all their U-arm switches at U_LH’s maximum S2. Their finite MLE slopes do not exist, and their exclusion follows the fixed plan. I agree that the remaining four-host mean **must not be treated as evidence against an overall rise with S2**.

   Replace “hosts with the steepest pattern” with “hosts showing positive boundary separation.” Sparse counts at the maximum do not establish a precisely estimated steep biological response. Specify that the deviations and extrapolation counts concern the **four fitted hosts**: three of those four extrapolate for each of W and K.

   Other small corrections:

   - **32.7 hours** is slightly below, rather than “within,” the stated 33–34-hour estimate.
   - The actual zero-transition audit bounds range from **0.003738 to 0.003819**. “About 0.0037–0.0038” is more accurate.
   - Saved per-genome predictor values are rounded to five decimals, whereas aggregate bands use full precision. Consequently, thresholding the saved U_LH scores at 1.2 produces **7256**, while the correct full-precision band count is **7255**. Disclose this precision convention or save sufficient precision; do **not** change the reported 7255.

**The primary reading should remain unchanged.** The two-field rule, intersection of size sub-fields across interval and envelope, guard, coverage response and global second-pass choice all follow the plan.

| Contrast | Recomputed mean | Interval | Envelope | Final reading |
|---|---:|---|---|---|
| Δ_weight | −0.00078125 | [−0.0017010, +0.0001385] | [−0.0018913, +0.0003984] | Direction unresolved; stipulated 0.004 exclusion |
| Δ_count | −0.00263672 | [−0.0041113, −0.0011621] | [−0.0093603, −0.0004020] | Lowers; size unresolved because of unresolved genomes |

The coverage table permits exclusions under the fixed response rule. Neither relevant single-host guard changes these readings. The second-pass audit has zero fading-to-separate transitions, and its use is prescribed, not a post hoc choice. The first-pass Δ_count envelope crosses zero exactly as reported.

The envelope covers assignments of the **recorded unresolved genomes**, conditional on the adopted classifications. It does not incorporate possible missed transitions among unaudited fading genomes. The draft appropriately acknowledges the audit’s insufficient precision at 0.001; retain that caveat.

The remaining numerical tables check out, including the class totals, transitions, per-host counts, descriptive contrasts, compute totals and M4d comparison. The low-coupling pattern is also accurate: outside the three named hosts, those four arms contain **one separate-states observation in 28,672**. Keep it descriptive rather than treating those hosts as an established biological subgroup.

For M5’s power calculation, I recommend the following assumptions:

- **Choose the contrast and success criterion first.** Detecting a positive mean, establishing an effect above 0.001, and excluding effects of 0.004 are different power targets. Include multiplicity if both total and residual advantages are primary.
- **Use paired genome outcomes**, preserving cross-arm dependence. With independent panels nested within draws and hosts, a useful planning model is  
  \[
  \operatorname{Var}(\widehat\Delta)\approx
  \frac{\sigma_H^2+\sigma_D^2/D+\sigma_G^2/(DG)}{H}.
  \]
  Account for the five-ensemble allocation and examine uncertainty in all components. A new S3-matched control needs its own variance assessment.
- **Evaluate effects of 0.001, 0.002 and 0.004**, alongside zero and heterogeneous/sparse host responses. Do not select the target effect solely from the observed +0.00195.
- **Simulate the final reading procedure**, including unresolved outcomes, audit fallback, envelopes and any guard—not merely a test on fully classified Bernoulli observations.

For orientation only, using SD 0.0054664, unchanged panel sizes, normally distributed independent host differences and a **single two-sided 5% t-test**, I obtain:

| True mean effect | Hosts for 80% power | Hosts for 90% power |
|---|---:|---:|
| 0.001 | 237 | 316 |
| 0.002 | 61 | 81 |
| 0.004 | 17 | 22 |

These are conditional reference calculations, **not final M5 sample sizes**. Round upward for ensemble balance. Establishing “at least 0.001” when the true effect is 0.002 requires resolving a gap of only 0.001, so the first row is the relevant reference.

Unresolved genomes are the larger obstacle. For T − K, the 20 counted excess switches, 37 unresolved K cases and 33 unresolved T cases give the mean identification interval

\[
[(20-37)/10240,\ (20+33)/10240]
=[-0.0016602,\ +0.0051758]
\]

**before sampling uncertainty**. At comparable unresolved rates, additional sampling will not eliminate this ambiguity. Carry the second pass and separate dynamics outcome, but also plan classification precision against M5’s target effect. An audit of about 800 per arm does not validate a 0.001-scale claim; even the simple zero-transition, one-sided 95% calculation requires **2995 audited fading cases per arm** to bound that arm’s transition rate below 0.001.

On publication, **I found no direct rule-1 violation in the proposed artifacts**. The panels contain outcomes and identifiers, not connection matrices. The block summary contains aggregate statistics and degree ranges, not N2’s labelled degree vectors or edges. The predictor table contains derived scalar results, not signed blocks. Keeping `blocks.json` local is appropriate; its recorded digest matches.

Finally, the reader crash occurs after its final JSON write, so the documented console failure does not undermine the result. I reproduced the current result exactly. The first invocation’s bytes are not independently verifiable from the listed artifacts, so byte identity remains a reported observation rather than something this review independently confirms.