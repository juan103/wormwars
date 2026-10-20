**Verdict: agree.** Push it, with the small fixes below.

**What I checked against the files.** Every number and attribution that changed between the drafts holds:

- **Finding 2 against `batch8.json`:** 21 and 6 of 512, the 8 settled all within the 21 and none own-state unstable, 39% and 25% of the tick-30 numerator, 92% and 67% against the 43% and 24% baseline, 2 of 21 complex against 15%, SH-class's 9 and 6 with 0.483 against 0.504, seed 7500 with 512 genomes and follow 300.
- **The census against `settled_census.json` and 03mc's results page:** 26 of 1977 eligible, 3 to 7 graphs per ensemble at or above it, maxima 28 to 126, Spearman 0.36 to 0.48. The script reads the committed measurements, groups the five ensembles correctly, and its per-ensemble medians and maxima agree with what 03mc already published.
- **Findings 1, 3 and 4:** the 0.558 quartile with 0 to 3 graphs, ranks 17 to 46, the correlations, the gap penalties of 0.07 and 0.19, the 82% regrowth, the tau maxima of 0.10 and 0.12, the warm-up and food arms, the two triangle-surgery values.
- **Provenance:** 13 and 16 families, idea counts of 13, 17 and 18 plus the owner's 3, seven batches before round 3. The "carry each weight with its edge" wording matches the rewiring code's own docstring.
- **My input:** the growth-fraction threshold is now quoted as I wrote it. The amplitude design is Astra's and the pressing mine. The join is credited to both. The oscillator idea is reported as half held. The cheap kills, the two family kill-checks and the anatomy predictor sit in M1. Astra's round 2 is credited.

**Small fixes, none blocking:**

1. **"Two analyses"** on line 28 names three scripts and four results. Say three, or drop the count.
2. **M1 and M4 are named as decision points** in the roadmap's header, but neither step says what result would change the plan. M2 and M5 both do. One sentence each would close the gap, for example: M1 pivots if the lead vanishes at matched amplitude or the alignment term carries the excess; M4 pivots if no hold-only intervention beats its matched control.
3. **Draft 1 is not archived.** The `docs/memory/` folder is untracked, so draft 1 was never committed, and both round-1 reviews quote sentences from it that will exist nowhere in the repository. Archive draft 1 verbatim beside the reviews, as the project does for reviewed text.
4. **The census script's docstring** calls the settled-census point "Fable's round-3 review point". It came from the round-1 roadmap review, not round 3.

One observation, not a fix: the within-ensemble Spearman runs over counts whose median is zero, so it rests on the minority of graphs with any settled genomes. That is fine for a lead and the roadmap labels it exploratory, but M2's census should not inherit it as a tested association.