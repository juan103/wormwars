**revise.** The pairing is sound for an exploratory screen; fresh control runs are not necessary. Most v1 fixes are resolved, but the group interpretation, C4 guidance and reserve policy still need changes.

Must-fix items:

1. **[Part B: classes and reading](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:96).** “At most 2 use the difference” can classify a set containing six **unclear** champions as a “non-stereo plateau.” Require a specified fraction to satisfy the small-effect upper-bound rule; otherwise report the group as unclear. State whether “most” means within each set or pooled, and specify denominators for the shared ES genome. Rename “no detectable use” to “no material benefit detected”: the rule also accepts large negative contrasts and does not establish absence of sensory use.

2. **[Decision guidance: C4 and noise](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:181).** C4 supporting while C1/C2 do not **does not demonstrate interaction**. Replace this with “the combined setting is promising.” If retaining an interaction claim, estimate the paired contrast `(C4 − C1) − (C2 − GA)`, using **11-checkpoint champions for C2 and GA**, with uncertainty. Also change C0 alone implying “E3 should spend more work per evaluation” to “test increased evaluation effort”: noisy rankings do not establish that this allocation improves search.

3. **[C0: finish the analysis specification](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:116).** Specify:
   - parent evaluations on the same 256 worlds;
   - pooling across champions for the 0.8 threshold, empty-bin handling, top-eight tie handling, and zero-reference ES differences;
   - exact rollout compositions and seed/scale mappings.
   
   Top eight of **64** differs from E2’s top eight of **32**, and champion-centred siblings omit its mixed-parent population and elites. Label this a local selection surrogate, or match the population size. Estimate reference uncertainty from these candidates instead of assuming SE ≈ 0.05.

4. **[Budget and incomplete arms](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:231).** The reserve is an admission estimate, not protection against overruns. Explicitly apply admission checks to **reruns**, and allow an unaffordable retry to become final/incomplete without blocking later evaluation. E2’s inherited code exempts extension reruns from its reserve check. If “protected” is intended literally, stop training before the reserved final-evaluation allowance is consumed, allowing for an in-flight rollout.

5. **[Part A table](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/PLAN.md:36).** Correct three rounded entries from the committed JSON:
   - gap 0.05–0.15, k=32 tied: **0.06**, not 0.07;
   - same gap, k=128 strictly correct: **0.86**, not 0.87;
   - gap 0.30–0.60, k=32 tied: **0.00**, not 0.01.

Suggestions:

- Pin the low-gain reference explicitly to **k=4, speed=1, turn=0.1**, the frozen gain-curve winner.
- Describe C3’s projection as **one eight-run batch at (256,8,1)**. The listed budget components sum to approximately **5.8 hours**.
- Report all eight extension differences, including run 6’s zero, in the mean/median. Add the previously requested validation curves against cumulative work; extension gains combine more generations with more checkpoint opportunities.
- Bind 04a’s source records too, and check historical engine/configuration compatibility separately from the new E2d runner’s binding.

What I checked and found correct:

- **Part A’s entire JSON regenerates exactly.** All three test bodies passed with output held in memory. Independent calculations confirmed pair counts **74/113/106**, SD **0.6046–1.0794**, nomination means/correlations, population ranges and validation endpoints. Apart from the rounding errors, the statements are fair.
- **Pairing works:** all eight recorded generation-0 world schedules match; the eight-world prefix holds through generations 0–999. Reused engine/runner files are unchanged from E2’s binding commit. Reusing training/validation worlds introduces no treatment-specific confound, but inference remains conditional on those finite samples and the already-observed runs. Fresh diagnosis worlds do not make this an independent training replication.
- **C1’s checkpoint fix works:** all 88 required candidates exist and their parameter hashes match. Validation does not affect breeding. All four selection-episode totals are correct; historical accounting should still retain E2’s actual 41 validations.
- **C3 is resolved:** σ alone changes, with learning rate 0.15.
- Probe placement, continuous effects, the middle class, control checks, `swapped` for C, and separate improvement/plateau outcomes resolve the corresponding v1 issues. The budget comparison is useful screening evidence; failure of its threshold would not establish a ceiling.

Read-only review; no files changed or GPU experiments run.