Round 2 of the review of `docs/memory/MEMORY-ROADMAP.md`, now draft 2. Your round-1 reviews (both "revise") are in
`docs/reviews/20261020-memory-select/roadmap-review-r1.{astra,fable}.md`. Claude took every finding:
- finding 2 is rewritten with counts, "consistent with" a saddle, ramp-end states named as not fixed points, the stable-genome eigenvector baseline, and 03mc's committed settled census. Claude checked Fable's census point and added `scripts/memory_spikes/check_settled_census.py` → `runs/memory-spikes/settled_census.json`: N2's 26 settled genomes are reached by 3 to 7 of 128 graphs per ensemble, and within each ensemble the settled count tracks the tick-30 share (Spearman 0.36 to 0.48);
- the other factual fixes, the provenance fixes and the attributions;
- the plan: the cheap kills and the anatomy predictor move into M1; M2 starts with a validated pilot; M3 has no veto; M4 gains matched erasures, paired genomes, write-only and read-only comparisons, a pulse-written history, and an exploratory transplant screen; M5 is split, with what registration fixes listed; the decision points are restated; costs are stated with and without Jacobians.

Separately, CI found a real test failure that is not part of this review (a retry test hit the amplitude check's own
time budget on GitHub's slow runners). It is fixed in the test only and will be recorded with the roadmap.

Please check that draft 2 represents the files and your input correctly, and give a verdict: "agree" (push it, perhaps
with small fixes you list) or "revise" (what must change first). Keep it short if you agree. Read the repository as
needed. Do not edit files or run anything.
