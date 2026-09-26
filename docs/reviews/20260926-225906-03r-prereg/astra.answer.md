**The primary measurement path is faithful, but I would not bind this draft unchanged.** The main problems are incomplete outcome rules, an undisclosed retained permutation, overstated power interpretation, and a supplement that cannot handle outcomes the protocol permits.

I checked `roadmap` at `3f3bf10`, the diff from `132acae`, and the actual graph files. All **768 manifest hashes match**. Across 03 and 03r, all **1,408 ensemble graph arrays are distinct**, and the fitness/probe genome-seed streams have no collisions. The graph seeds, N2 genome salt, worlds, run seed, calibration/validation seeds, N2perm4–6 configuration, and proportional run order match the draft. No 03r measurement files exist.

**Must fix before running**

1. **Complete the outcome and publication rules, especially disagreement between the two criteria.**

   **Locations:** [PREREGISTRATION.md §6](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:147), [§10](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:217), [cmd_report](/D:/Claude/random/wormWars/scripts/exp03.py:595).

   “Replicated” versus “anything else” is insufficient. §6 permits withholding a verdict, but §10 provides no corresponding publication outcome. Moreover, `cmd_report` omits `replication_primary` entirely when P4 is incomplete.

   Register these cases explicitly:

   | Outcome | Required interpretation |
   |---|---|
   | Primary passes; P4 also passes 03’s Holm rule | Passes both registered criteria. |
   | Primary passes; P4 fails 03’s Holm rule | Replicates under the new P4-only criterion; does **not** reproduce 03’s full significance criterion. |
   | Complete primary fails | The registered replication criterion was not met; report which rank or margin gates failed. |
   | Invalid N2 or insufficient valid graphs | Verdict withheld; replication attempt incomplete or unevaluable, with the reason published. |

   A split result also needs explicit treatment. In [single_signal](/D:/Claude/random/wormWars/wormwars/exp03/report.py:109), **every** ensemble receives the global maximum p. I verified that four comparisons with `p=.01` and one with `p=.06`, with all margins satisfied, produce five “inconclusive” labels. This implements the inherited rule correctly, but those labels alone conceal the split.

   Require a table containing each ensemble’s valid count, exceedance count, raw rank p, effect interval, margin, and numerical gate outcomes. Four passing comparisons cannot rescue the conjunction.

   Finally, commit to presenting both runs separately with both decision rules, regardless of outcome. Keep pooled analyses exploratory, as §11 already says, and prohibit using them to replace a failed registered verdict.

2. **“Every random draw fresh” is false for the secondary permuted-magnitude condition.**

   **Locations:** [PREREGISTRATION.md §4](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:99), [measure_graph](/D:/Claude/random/wormWars/scripts/exp03.py:329), [BrainConfig](/D:/Claude/random/wormWars/wormwars/config.py:50), [magnitude permutation](/D:/Claude/random/wormWars/wormwars/brain.py:41).

   The `M0-permuted` branch changes the magnitude mode but leaves `init_permutation_seed` unchanged. For N2 and N2-rev, that remains **0**. The permutation uses a separate generator seeded from this value, so the new genome salt does **not** redraw their weight placements.

   Thus N2 and N2-rev reuse their 03 secondary permutation. Their random signs, biases, and time constants are fresh. **Primary P4 is unaffected.**

   Prefer registering and implementing a fresh secondary permutation seed for 03r while preserving instance 03. Alternatively, explicitly disclose this retained construction and narrow the freshness claim.

   Also list the intentionally retained remaps from `02-screening/remaps.json` and bootstrap seeds 0/1. Keeping them as fixed probe/analysis choices is defensible; presenting the stimulus bank as the only retained random construction is inaccurate. The replication tests currently check configuration constants, not this downstream permutation path.

3. **The power figures are numerically correct, but they are not power for the complete registered procedure.**

   **Locations:** [PREREGISTRATION.md §7](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:171), [power.py:28](/D:/Claude/random/wormWars/experiments/03r-replication/power.py:28).

   I ran `power.py`; every printed figure agrees with the draft. I also independently evaluated the corresponding [beta-binomial predictive probabilities](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.betabinom.html):

   | Fixed N2 comparison value | P4 rank gate | Rank gate at α/3 |
   |---|---:|---:|
   | 0.9309 | 0.9651 | 0.4113 |
   | 0.925 | 0.9651 | 0.4113 |
   | 0.915 | 0.8937 | 0.1803 |
   | 0.905 | 0.3523 | 0.0032 |

   The method is reasonable **conditional posterior prediction of rank-count success**. However:

   - It omits the effect-margin gate, exclusions, and completeness.
   - It fixes N2’s *measured comparison value*. Calling the rows N2’s “true P4” is inaccurate without simulating its fresh measurement.
   - The “03’s full rule” calculation uses α/3. This matches P4’s Holm threshold when P4 is first in the ordering; it does not simulate the actual three-signal Holm procedure.
   - With four zero-exceedance ensembles, the prior matters. Replacing Jeffreys’ prior with a uniform Beta(1,1) prior changes the first row to approximately **0.911 and 0.175**. That does not invalidate Jeffreys’ prior, but it shows that 0.97/0.41 are assumption-sensitive predictions.

   “SE 0.006, small against the ensembles’ spreads” is not a sufficient justification for ignoring N2 noise: the relevant sensitivity is near the upper-tail thresholds. As an illustrative calculation, adding Gaussian measurement noise with 03’s N2 SE around a true value of 0.915 reduces the primary rank prediction from **0.894 to about 0.794**, retaining the same empirical-tail model.

   Rename the table and disclose these omissions, or implement a fuller operating-characteristic calculation. Also replace “the Gaussian figure … is pessimistic” with “lower under this alternative model.” Sparse observed tails do not establish that the Gaussian prediction understates future success.

4. **The newly registered supplement fails on allowed outcomes and does not produce every promised summary.**

   **Locations:** [PREREGISTRATION.md §5](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:127), [supplement.py:31](/D:/Claude/random/wormWars/experiments/03-generation0/supplement.py:31), [summarise](/D:/Claude/random/wormWars/experiments/03-generation0/supplement.py:51), [main](/D:/Claude/random/wormWars/experiments/03-generation0/supplement.py:68).

   The script unconditionally opens every planned measurement and assumes every record contains history, response, calibration, and gains. Therefore:

   - A permitted budget stop causes a missing-file failure.
   - A permitted calibration failure causes a `KeyError`; I reproduced `KeyError: 'history'` with a failure record.
   - An absent or invalid descriptive variant can break the rank summaries.
   - Forward-ratio validity has no registered finite-value/denominator-floor policy.

   The promised per-ensemble summaries “for each” quantity also exceed implementation: `summarise` includes turn gain, but not forward gain or calibration-validation quantiles. Validation is instead summarized by one maximum deviation across validated graphs.

   Fix the extractor and register its masks, missingness counts, and exact outputs now. Make its provenance checks consistent with the main report. Change its output note from “Exploratory (§11)” to the correct 03r status.

**Should fix**

5. **Distinguish fresh Monte Carlo sampling from independent evidence about another biological observation.**

   **Locations:** [PREREGISTRATION.md §2](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:40), [§6](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:158), §10.

   The post-03 selection of P4 is disclosed clearly. I accept P4 alone at α=.05 **as a pre-registered sampling-stability criterion**, with the original rule reported alongside. I would not require an arbitrary stricter α, a pooled primary analysis, or replacement of the rank test by an effect-size-only rule.

   However, both runs retain the same N2 connectome and reference-generating procedure. Under an exchangeability model, an unusually high latent N2 value remains unusually high across reruns. Fresh seeds do not make the two rank tests independent evidence under that null, or erase the original signal-selection history.

   State this limitation explicitly. Do not multiply the p-values or use an ordinary independent-test combination; those methods require assumptions this design does not establish. [SciPy’s combination documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.combine_pvalues.html) also identifies independence and discreteness limitations.

   The unchanged probe/code is appropriate for this replication’s stated purpose. It also preserves systematic implementation errors and probe-specific effects. §2 already acknowledges much of this correctly; successful replication should not be presented as validating the probe or identifying a memory mechanism.

6. **Reconsider the 120-valid-graph floor for a 256-graph SH-route ensemble.**

   **Locations:** [PREREGISTRATION.md:168](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:168), [report.py:146](/D:/Claude/random/wormWars/wormwars/exp03/report.py:146).

   The inherited floor allows SH-route to lose **136/256 graphs** while still receiving a verdict. The other ensembles can lose only 8/128.

   I recommend a floor of **240 for SH-route**, preserving the original retained fraction, or an explicit justification for tolerating substantially more missingness. Report planned, measured, calibration-failed, signal-invalid, and valid counts separately.

   The allocation itself is reasonable, though not demonstrated optimal. Under the draft’s fixed-threshold Jeffreys model, increasing only SH-route from 128 to 256 raises primary success from approximately **0.950 to 0.965**. Its main benefit is greater precision on the previously decisive tail.

**Minor**

7. **Correct the discussion of the old rule’s discrete cutoffs.**

   **Location:** [PREREGISTRATION.md:160](/D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:160).

   “Whether one or two graphs land above N2” no longer describes SH-route. At α/3, its cutoff is **three versus four exceedances** with 256 graphs. The other ensembles retain one versus two. `power.py` gets this right.

   Also specify that the denominator is the **actual valid n**, and that the stated 5/11 primary cutoffs assume the complete planned samples.

8. **Pin the N2 cache in run provenance.**

   **Locations:** [use_instance](/D:/Claude/random/wormWars/scripts/exp03.py:80), [load_connectome](/D:/Claude/random/wormWars/wormwars/connectome/loader.py:100).

   The ensemble graphs are verified against their manifest, but the locally loaded N2 cache is not among `INPUT_FILES` and its hash is not checked by the loader. I verified that the current cache matches `PROVENANCE.md`, so there is **no current discrepancy**. Recording and checking that hash would close this avoidable provenance gap.

9. **Keep “P1/P3 verdicts replicated” separate from evidence of absence.**

   **Locations:** PREREGISTRATION.md §2 and §10.

   Repeating “not distinctive” reproduces a decision label. It does not establish equivalence or absence of either property, particularly for the low-power P3 test. Commit to that wording distinction.

**Overall judgement:** Yes, this can run once the must-fix items are addressed. The core P4 implementation matches the proposed maximum-p-plus-margin rule, and I found no accidental reuse affecting primary P4 sampling. Keep the proposed allocation and P4-only primary if the publication explicitly distinguishes that criterion from reproducing 03’s Holm verdict.

Fourteen report/verdict tests passed. The replication test module was blocked during Torch/dill import by the read-only temporary-directory restriction, so I do not claim that suite passed. I ran no brains and changed no repository files.