**revise.** Two small C0 corrections remain before implementation. The other v2 must-fixes are resolved at the plan level.

Must-fix items:

1. **C0 / seed table — contradictory noise streams.** [C0](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:145) requires identical noise across scales, but the [seed table](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:270) adds `scale index`. Remove that addition: use `1131000 + 10*r` for GA and `1131100 + 10*r` for ES, resetting the generator or reusing the draws at each scale. Test equality of the underlying noise. Qualify “half as far” as applying before clamping and in the mutation coordinates; multiplicative τ changes and bounds prevent that statement holding literally for decoded genomes.

2. **C0 / truncation ties — the claimed correspondence with E2 is wrong.** [Line 161](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:161) says lower-index ties are “as in E2’s sort.” E2 uses unstabilized [`np.argsort(-fitness)`](D:/Claude/random/wormWars/wormwars/evo/evolve.py:75). I reproduced a tied example where its top-eight membership differs from lower-index ordering. Keep the explicit lower-index convention for C0, implement and test it, and remove the claim that E2 uses it.

Suggestions:

- C0’s reference changes with each 8/248 split. Specify that bin membership is recomputed per split and whether the minimum of 30 counts distinct sibling pairs, rather than repeated pair observations.
- Describe C4 − C2′ as a **work-allocation contrast**: increasing worlds also reduces generations. The matched difference-of-differences remains appropriate for these allocation policies.
- The budget components sum to **5.95 hours**, so “about 6.0” is clearer than “about 5.9.”

What I checked and found correct:

- **Run 2:** “supports” now requires both the eight-run and seven-run checks; dependence on run 2 is separately labelled.
- **Replay:** generation-0/25 references exist. The engine, reused E2/E1 runners and requirements are unchanged from `69f4163`. The planned replay gate is appropriate; I did not run it.
- **Part B:** two-sided negligible-effect intervals, named sets, denominators, shared-genome treatment, mixed outcome and control-failure handling resolve the earlier gaps.
- **Budget reading:** disclosed extension differences reproduce exactly; the eight-run mean is **0.24585**. Per-run costs and 42 checkpoint opportunities are correctly stated.
- **C4 and reserve:** the matched interaction contrast is correct. Rerun admission, the 6.5-hour training stop and evaluation of completed arms address the reserve issue.
- **C0 otherwise:** parent evaluations, surrogate qualification, disjoint reference worlds, compositions and zero-reference handling address the earlier omissions.
- **Part A:** the entire JSON regenerated exactly in memory; all three test bodies passed. All three table corrections are correct.
- **Pairing:** verified the eight-world prefix for all eight runs through generations 0–999. Selection-episode totals are correct.

Read-only review; no files changed or GPU experiments run.