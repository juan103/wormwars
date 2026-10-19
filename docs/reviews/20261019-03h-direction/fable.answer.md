**Recommendation:** continue to the pilot with B as the sole Holm claim, keep A's read-outs as pre-specified secondaries outside the gate (your option b, with the history measurement retained), and run the cheap step 0b read-outs in parallel without waiting on them. Before the pilot's registration is bound, fix two defects in B that are visible regardless of step 0.

1. **Why not (a).** Keeping A under Holm after step 0 halves B's alpha for nothing. Step 0's mean is about 5 SE below δ_A on 16 graphs, and the formal A1 would be the same measurement on nearly the same family, since SH-mirror-ASK differs from SH only by the ASK cap and the variant is bitwise the pinned interface under level. A formal A would be a 64-graph replication of a known null. Its marginal GPU cost is about 0.1 hour, so keep the measurement and the fixed wordings, but take it out of Holm. The gate difference is what matters:

   | Registration | B passes if |
   |---|---|
   | A and B under Holm, A null | N2 ranks first of 65 (p = 1/65) |
   | B alone at 0.05 | at most two nulls above N2 (p = 3/65) |

   Record in DESIGN v3.3 that this was decided after step 0, which bears on A only and precedes any B data.

2. **Why not (c).** The pilot costs under 0.5 GPU-hour and has stop rules. B is the only direct test of the roadmap's prediction that N2's early advantage is larger when memory is needed. Step 0 lowers B's prior, because the within-graph mechanism link is absent in SH random brains, but it does not test B. The right stopping point is after the pilot, if the bit does nothing to fitness.

3. **(d), yes, but not as a fork that waits.** H_dir, the motor-scale read-outs, and the plain Spearman of H and of S with fitness on the same 16 × 256 genomes cost about a minute. S alone is the one I would want: 02 and 03 agree that N2's random brains give a food-evoked read-out five to seven times the ensemble medians, so if S predicts fitness in SH, the head start may be responsiveness rather than memory. There is no committed per-genome N2 fitness, as 03's README line 254 says the 640 MB of per-genome measurements stay local, so N2's ρ needs one fitness replay plus history, still minutes. One graph at 256 genomes only detects |ρ| above about 0.13. Report all of it as exploratory and use none of it to re-pick a primary.

4. **Two defects in B to fix before the pilot registration is bound.**
   - **B's label is not conditional on the manipulation's sign.** U is sham minus relief, and N2 ranking high means N2 gains least from the relief, or is hurt most by it. DESIGN §6 says an adverse shift is "reported as adverse" but leaves the label reachable. Fix: "head start larger when memory is needed" requires the ensemble's mean decile shift, relief minus sham, to be above zero by its 95% interval. Otherwise B gets a fixed "not interpretable" wording.
   - **PILOT.md §5.4's "neither moves" rule is toothless for fitness.** A 0.25 current into two sensory neurons of responsive random brains will very likely move the motor turn read-out by 0.02, so the amplitude doubling and the stop would never fire even if fitness never moves. Fix: key the doubling and the go/no-go on the decile shift, and keep the turn response as a diagnostic. After step 0, a formal B with no fitness effect of the bit is the likeliest way to spend 2.2 GPU-hours on an uninformative null.

5. **Bookkeeping changes.** Holm covers B alone, §9's attainable ranks become r ≤ 2, and the gate to stage C is B's label at 0.05. The §7.7 and PILOT §5.3 power rule belongs to A2, so it should be reported rather than a stop. It would pass anyway: with s_graph at 0.060 the graph term is 0.0075, so power is near 1 unless the shared-world SD exceeds 0.035. Keep 64 graphs, since at 32 only rank 1 of 33 passes 0.05. Add to PILOT §5.2 the per-graph U and its between-graph SD against the shared-world SE, so the formal rank test can be read.

6. **D329's reading.** I recomputed the mean, SD, positive count, quartile mean and its range from step0.json, and both verification files are bit-equal on every part. Four points:
   - "B is untouched" is wrong in one respect. A's expected failure changes B's Holm threshold from rank ≤ 2 to rank 1 if A stays registered, which is the whole substance of the direction question.
   - The title "history does not predict T1 fitness" is broader than the measurement, which is the raw-turn history magnitude given S. The quartile split on unconditioned H also shows nothing, which supports the broader reading, but S against fitness is unreported.
   - "(−0.079 to +0.069)" reads like an interval. It is the per-graph range.
   - The 1/√256 argument is sound, but 16 graphs cannot exclude small heterogeneity, so "no link in any graph" should be "no detectable variation in the link".