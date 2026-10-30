**Verdict: agree with fixes.** The scope is proportionate, but the comparison rules and fixed negative reading need correction before use.

I checked the files and genome metadata. The counts are correct: 102 g00, 102 g39 and four g79; graph calibration gains match the saved metadata. The mutation settings match. The two plan copies are identical. I inspected files only; I did not run new probes.

1. **The pooled sign tests are wrong for the intended comparison.**

   [The grid explicitly shares seeds, starting populations and worlds across mappings](/D:/Claude/random/wormWars/wormwars/exp02/grid.py:3). The 102 comparisons contain **30 graph/run seed units**, not 102 independent replicates. Some g00 champions are literally identical across all four mappings.

   There is a second problem: a binary champion indicator minus the mean of four binary drift indicators does **not** have equally probable positive and negative signs under equal switch prevalence. For example, with independent switch probability 0.1 in both groups, only **24.4% of non-zero differences are positive**, not 50%. The proposed sign test therefore does not test equal prevalence.

   Replace it with a prespecified analysis of the paired **rate difference**, accounting for shared graph/run blocks, or keep that comparison descriptive. An exploratory cluster bootstrap that resamples whole graph/run blocks and recomputes the mean run-level difference is a proportionate option. Keep mapping/family tables; specify exactly which primary comparison controls the decision.

2. **Replace the “otherwise” reading and give uncertainty precedence.**

   [Draft 1’s negative wording](/D:/Claude/random/wormWars/docs/reviews/20261030-m6-0-plan/draft1.md:115)—“selection on T1 did not build switches detectable by this probe”—does not follow from failing the enrichment criterion. Four convincing switches would fail it; numerous switches with similar prevalence under drift would also fail it.

   Use: **“We did not detect enrichment of probe-defined switches in g39 champions relative to the mutation-only control.”** Then report what classes actually occurred. Describe fading only where classified.

   Add an explicit **inconclusive** branch for incomplete work, failed consistency checks, an audit failure, or unresolved classifications that prevent the comparison. Report switch-share bounds \(S/n\) to \((S+U)/n\) whenever unresolved cases exist; the 25% threshold should not make smaller unresolved fractions count as non-switches. Show mapping-specific unresolved counts too.

   Counting read-out-silent separate states as switches is consistent with M4d/M4e. Keep them separate in the interpretation: they establish state separation, while their contribution to the measured turning-history effect is a different question.

3. **Persistence needs explicit rebound, eligibility and censoring rules.**

   [The proposed τ10](/D:/Claude/random/wormWars/docs/reviews/20261030-m6-0-plan/draft1.md:87) is a **first-crossing time**. A signed read-out difference can cross zero and subsequently grow again. Its first crossing is then a poor measure of how long history remains detectable.

   The inexpensive fix is to retain the metric under that name and record whether the difference subsequently returns above 0.1a. Alternatively, use the time after which it stays below threshold through the observed window. Either calculation uses the existing trajectory.

   Also fix these before running:
   - Apply the amplitude floor explicitly to τ10 as well as ratios; at \(a=0\), the current strict inequality never succeeds.
   - “Beyond 2000 ranks above finite values” does not define a **mean**, subtraction or ratio. Use a separately named restricted measure, such as \(\min(\tau_{10},2000)\), for arithmetic, and report censoring separately.
   - Specify paired eligibility when g39 passes the floor but some controls do not.
   - Resolve the discrepancy between comparison 2’s **median difference** and the reading’s promised **median ratio**.

4. **The banks are defensible; the 02b comparison has one invalid pairing.**

   Sharing each g39-derived bank across its run’s genomes is the appropriate way to revisit 02b. It estimates behavior under **g39-conditioned inputs**, not an input-independent property. Keeping 03mc secondary and contextual is appropriate. The disclosed spike is acceptable for an exploratory plan, provided those results remain labelled previously seen.

   Extend the consistency check to **d(5) versus |raw_turn after|**, which is already available at negligible cost. The proposed tolerance and stop-for-investigation rule are reasonable; a failure should remain documented if its resolution changes the protocol.

   **New CPU drift genomes cannot be paired with 02b’s old GPU drift measurements.** [02b generated its own four drift draws](/D:/Claude/random/wormWars/experiments/02b-champion-analysis/analyse.py:256). Restrict the historical genome-by-genome table to matching g00/g39 champions. For new drift, use its newly measured a and d(5).

   I would cut the pooled Spearman correlation. Classes have no natural rank, and pooling generations can manufacture an association from their group differences. The matched champion table answers the useful question.

   One implementation trap: [`analyse.py` automatically selects CUDA](/D:/Claude/random/wormWars/experiments/02b-champion-analysis/analyse.py:49), and `typical_input` uses that module’s device. Explicitly force its CPU path. Save each complete bank, genome hashes, record index and drift seed; `typical_food` alone cannot reconstruct the inputs.

5. **Cut the state-visits stage.**

   [The projection](/D:/Claude/random/wormWars/docs/reviews/20261030-m6-0-plan/draft1.md:105) establishes which side of a hyperplane the state occupies. A trajectory arbitrarily far from both roots can cross it repeatedly. It does not establish visits to either root’s neighbourhood or basin, especially under changing input.

   The plan’s “both sides” wording avoids the strongest overclaim, but this remains a weak answer for the implementation and interpretation effort. Defer meaningful state visitation to option 5.

`probe_input(iface, bank)` is a reasonable shape for this **serial research runner**. I would keep the context in `common.py`, with one active-input accessor used by every current builder and food-level calculation. Restore the previous context in `finally`; either support nesting correctly or reject it explicitly. The cached read-out vector `C` can remain fixed only because the supported interfaces preserve the read-out—assert that invariant.

Its tests should catch:

- **Actual legacy equivalence:** unchanged default currents, trajectories and classifications against the previous calculation. Comparing the new default path with the new context using default arguments is insufficient by itself.
- **Both parts of the override:** a changed food level and non-food sentinel signals, correct remapped destinations, gains and clamping. Check the food-induced current difference, since other signals legitimately drive other neurons.
- **Restoration:** normal exit, exception exit, nesting if supported, and successive runs using different banks.
- **Every continuation path:** `probe_states`, `follow_from`, M4e’s hold, and both oscillation-rerun routes. Compare trajectories while states are still moving, including the saved pre-tail restart. Preserve the original ramp-end amplitude during second-pass classification.
- **Production batching:** the relevant grouped and singleton reruns with the saved padding policy.
- **Reading failures:** unresolved cases, audit failures, censoring, missing pairs and a secondary-only positive must produce the intended wording. One “changed value changes summary” sabotage test is too weak.

Keep the fading audit and the five-hour ceiling. The quoted arithmetic is sound, but 0.75 seconds was measured in batches of eight, and the second-pass estimate is workload-dependent. Forecast from actual production batches before committing to the long pass; a capped run must remain explicitly incomplete.