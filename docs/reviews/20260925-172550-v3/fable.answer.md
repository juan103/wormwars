Files checked: `ROADMAP.md`, `DRAFT.md` v3, `DECISIONS.md` D045, `NOTES_FROM_02.md`, both prior answers, `exp02/grid.py`, `configs/interface.yaml`, 02's pre-registration budget and results.

**Q1. Were my points taken correctly?**

1. **Taken correctly, nothing misread:** candidate pool excludes the interface (8), no-headroom class and SC5 exploratory (9), three reference refits with the mean (10), search-level margin (11), real-model planted test as the pilot gate (12), SC3-paired on mirror-undecided candidates (13), t-intervals and more matched graphs (14), deletion operator and criticality map in 02b (7), task-specificity contrast, motor remap, class-preserving null and reversed N2 in 03 (17-20), 64 graphs (2), 04 ungated from 03 (3), narrow-not-stop (6). Fine.

2. **MINOR, a new asymmetry my point 8 caused.** `DRAFT.md:183-185` keeps X's true interface connections fixed in every search, including the random-partner refits. High-criticality targets are the ones most likely to touch the interface, so for them the random-partner refit already has X's real sensor input and motor output, and the free search only has to find interneuron partners. This raises the refit toward the reference and pushes targets into "not identifiable" by construction. Not wrong, but pre-declare a stratification by kept-connection count (0 versus more than 0) for SC1-SC4, and say in the hypothesis section that recovery here means recovery of the non-interface partners.

3. **MINOR, my point 11 was taken too literally.** `DRAFT.md:121-124` sets m = max(δ_eval, δ_search) with δ_search measured on *free* searches. If the free search is multimodal, δ_search is large, m is large, and steps 2 and 3 fire everywhere: the method's own search variance pushes the panel toward "no headroom" and "not identifiable". Measure δ_search on the original-partner refits (optimizer variance with partners fixed) and keep free-search spread as a reported quantity and as the step-4 test.

**Q2. New flaws in v3**

4. **MAJOR, the classification has a hole at step 4-5.** `DRAFT.md:139-145`. "Reaches within m" is an interval inside ±m (line 125-126). "More than m below" is undefined, and "otherwise" at step 5 catches every interval that straddles −m. So an undetermined free search is classified as reaching the reference and then scored for recovery. Define three states for each paired interval (inside ±m, entirely below −m, else) and add "inconclusive search" for the third; step 5 should require inside ±m or entirely above +m.

5. **MAJOR, the same one-sidedness in steps 2 and 3.** A reference *below* the deleted-brain score by more than m (possible in compensated NIP brains) escapes step 2. Random-partner refits *above* the reference by more than m escape step 3 and fall through to free-search recovery. Both should be caught: step 2 fires when the reference is not above the deleted score by more than m; step 3 fires when the random-partner mean is not below the reference by more than m.

6. **MAJOR, the per-target chance band is unreachable.** `DRAFT.md:127, 143-145`. With roughly 240 candidates and 3-8 true partners, the null SD of a single target's AUC is about 0.10-0.15, so a 5-search bootstrap interval (at most 126 distinct resamples) will almost never sit inside [0.45, 0.55]. "Functional substitution" will be near-empty and "inconclusive overlap" will absorb it, which defeats the three-way separation 03a exists for (line 40-44). Keep the fixed band for cell-level aggregates. Per target, define substitution as "reached the reference and AUC inside the central 90% of that target's label-permutation null", which the draft already computes for precision at k (line 252-253).

7. **MAJOR, the analysis set for SC1-SC4 is undefined.** `DRAFT.md:293-301`. Which targets enter the mean AUC: all non-excluded targets, or only those that reach step 5? If N2 has more identifiable targets than SH-matched, the two choices give opposite SC2 answers. Fix one primary (I would take all targets except reference failure, with step-5-only as secondary) before the tag.

8. **MAJOR, "tightly null" has no bands.** `DRAFT.md:288-289` needs an equivalence band registered per hypothesis, and none is given for SC2, SC3 or SC4. This is the omission that made 02's strength control unreadable. Also state that intervals in a Holm-corrected family are at the adjusted level, and whether SC3's two sub-tests count as one or two members.

9. **MINOR, "spread" and "disagree" are undefined.** `DRAFT.md:120-121, 132`: SD, range or interval? The number of final evaluation worlds and of search worlds per generation is also not stated anywhere, and δ_eval depends on it. Fix both numbers in the draft, not only in the config.

10. **Budget arithmetic checked:** 576 combinations × 15 searches × 3600 states = 31.1 million, 785 h at 11/s, cap binds below 4.7×. Correct. Three additions are missing:
   - Whole-brain evolutions: 12 intact plus 288 NIP brains, 150 generations × 32 = 4800 genome evaluations each. At 02's measured rate (2 min per 40-generation run, `02-screening/PREREGISTRATION.md:217`, about 10.7 genomes/s) that is about 37 h, 22% of the cap. Reduction step 1 lowers it to about 25 h. MINOR but it must be in the rule.
   - The 11/s figure is 02's batch-32 population throughput, not a serial rate. The required 5× must come from batches wider than 32, so the pilot should time the planned batch width. MINOR.
   - Pilot cost: 8 targets × 15 searches × 3600 is 432k evaluations per arm, about 11 h at 11/s before evolutions. `ROADMAP.md:141` gives 6-10 h for 3a and 3b together, which presumes the batching the pilot is meant to measure. MINOR, state it.

11. **MINOR.** `DRAFT.md:160-162`: how the 6 SH-matched graphs are picked from 03's 64 must be a fixed rule (first 6 by seed), written before 03's results exist. `DRAFT.md:199-200`: choose the pair member by seed first, then rank by that member's drop, or say the pair is ranked by its mean. `DRAFT.md:299-300`: targets with no true partner among mirror-undecided candidates have undefined AUC; exclude and count them. `DRAFT.md:356`: say which 4 of 6 survive step 1.

**Q3. Ready for code and the pilot?**

12. **Nearly. Two changes to `DRAFT.md:333-342` make it ready; the rest are before-tag items.**
   - Specify the pilot design: number of pilot graphs and brains, and the arm. Criterion 1 must run in the NIP arm, since headroom and identifiability are NIP problems (my point 9); criterion 2 is MIP by construction. As written, criterion 1 could pass on MIP alone and never test the primary arm. MAJOR.
   - Write criterion 1 as an interval statement ("the paired interval of reference minus random-partner mean lies entirely above +m"), and fix the worlds-per-score numbers (point 9). Otherwise m and the pass criterion are not computable.
   Points 4-8 and 10 go in before the tag, not before code.

**Q4. Is roadmap item 2 ready for pre-registration?**

13. **MAJOR, the 03 budget is unsupported by two orders of magnitude.** `ROADMAP.md:45, 60-68, 140`: 258 graphs × 3 tasks × 2048 genomes is 1.59 million genome evaluations per condition. At 02's measured throughput that is about 41 h *per condition*. Nine conditions one-at-a-time is about 370 h; the full 6 × 2 × 3 factorial is about 1480 h. "About 5-8 GPU-hours" would need a 50-200× gain from wide batching, or far fewer conditions, genomes or worlds per genome. The pre-registration must fix the condition list (factorial or one-at-a-time from a base), the worlds per genome, and a measured batch-2048 timing.

14. **What else the 03 pre-registration must fix that the roadmap leaves open:**
   - The control task, and what "matched" means (`ROADMAP.md:65-66`): same world, interface and reward scale. And how edges on different tasks are made commensurable for signal (d), for example N2's z-score within each ensemble per task.
   - The sampler for routing- and mirror-matched shuffles (`ROADMAP.md:54-55`): how 0.64 partial symmetry and the routing cap are enforced under degree preservation, whether gap junctions are mirrored, and numeric thresholds for the mixing, diversity and interface-local similarity checks.
   - Numeric margins per signal (`ROADMAP.md:72-77`), sourced from 02's observed effects.
   - Which claim drives the gate (`ROADMAP.md:79-86`): percentile or mean difference, with the percentile threshold stated (with 64 graphs the resolution is 1/65). And since the ensembles are nested, the gate should name the *narrowest* ensemble that explains a signal.
   - Signals (b) and (c) overlap: (c) is the T0 part of (b). Merge or say why both.
   - The "corrected input-response probe" (`ROADMAP.md:32`) is defined in 02b, which has not run; 03's pre-registration must define it itself.

15. **Fine:** the roadmap's order and gates now match both reviews; D045 records the delegation accurately; the 03a hypothesis section, arms, deletion versus silencing, parallel-tempering acceptance rules (`DRAFT.md:233-236` are correct for score maximisation), and the never-drop list are sound.