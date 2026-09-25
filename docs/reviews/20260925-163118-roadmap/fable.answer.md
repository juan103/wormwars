Files checked: `ROADMAP.md`, the 03a draft and notes, 02 and 01b results, D038-D043, both earlier next-step reviews, and the model code (`brain.py`, `genomes.py`, `interface.yaml`, `exp02/grid.py`, `exp02/remaps.py`).

**Q1. Ordering and gates**

1. **Claim 1 (03 before 03a and 04): agree, but 03's gate is not yet a gate.** "If symmetry and routing account for N2's generation-0 signal" (`ROADMAP.md:59`) has no estimand or margin. 02 already paid for that omission once: the strength control could not conclude anything because no equivalence margin was registered (`02-screening/RESULTS.md:214-218`). Also, the signal being explained is already thin. The generation-0 interaction is a shuffle deficit, not an N2 gain (`RESULTS.md:140-146`), the directional response is ordinary relative to common mode (`RESULTS.md:170-172`), and 01b's head start never separated (`01b/RESULTS.md:88-90`). Name the three signals, name the ensemble each is tested against, and register margins in both directions.

2. **N2 is one graph, so 03's test is percentile placement in an ensemble.** With 16 graphs per ensemble (`ROADMAP.md:51`) the resolution is one in 17. Each graph costs minutes at generation 0. Use 64.

3. **Gating 04 on 03 (`ROADMAP.md:85`) points the wrong way.** Generation-0 structure on kinesis-dominated tasks says nothing about capability acquisition under evolution. 04's real dependency on 03 is the control ensembles. Its real gate is its own shuffle-only feasibility pilot (`ROADMAP.md:82-84`), which is the correct lesson from D038. Rewrite as: 04 uses 03's controls and runs only if its pilot passes.

4. **Claim 2 (03a whatever 03 finds): disagree as written.** If symmetry explains N2, SC2 is predetermined by the mirror share (notes point 1) and only SC3-paired on at most 6 targets remains informative. More importantly, 03a's gate should not be 03's outcome at all. It should be a feasibility pilot of its own, which the draft lacks: it has a timing pilot only (`DRAFT.md:159`). The roadmap's line that 03a "does not depend on evolution discovering a new capability" (`ROADMAP.md:73-74`) is misleading. It depends on a 3200-evaluation search discovering a specific wiring among roughly 260 candidates. That is a harder discovery problem, not an easier one.

5. **Claim 3 (plasticity deferred): agree.** Nothing to add.

6. **Claim 4 (stop, not pivot): false dichotomy.** A generic explanation would be a finding about this task family, where kinesis carries most of the scripted gain (`RESULTS.md:290-291`), not a finding about N2. The consequence should be: no further N2 claim on foraging, and any continuation must be a 04-style task with a passed feasibility pilot. The "pivot" is already implicit in 03a's class-model baseline, which is the next generic level up from symmetry.

7. **02b needs one addition: a deletion criticality map** over every non-interface neuron of each evolved champion. It costs about 2250 evaluations per brain and is what 03a's panel and headroom depend on. Note the code has only silencing (`brain.py:294-310`), while the draft rightly insists on deletion (`DRAFT.md:36`). Build the deletion operator once, in 02b, and 03a's deletion test (`DRAFT.md:147`) comes for free.

**Q2. The 03a draft**

8. **Biggest risk: the free search will wire shortcuts.** Partners are drawn "uniformly at random among all other neurons" (`DRAFT.md:90`), which includes the 20 sensor and 20 read-out neurons in `configs/interface.yaml:23-64`. For any critical neuron, the score-maximising wiring is input from AWA/AWC/ASE/ALM and output onto AVB/SMD. 02 showed shuffles with exactly such shortcuts score fine (`RESULTS.md:199-205`). Expected result: functional substitution nearly everywhere, which tests nothing about self-consistency. Exclude interface neurons from the candidate pool, as they already are from the target pool (`DRAFT.md:69`), or cap direct-route weight at N2's, and register the shortcut rate as an outcome.

9. **Headroom is unchecked in the NIP arm.** Criticality is measured by deletion from intact brains (`DRAFT.md:73`), but the NIP arm reinserts into brains evolved without X (`DRAFT.md:31`), which have compensated. If the ceiling refit sits within δ of the no-X score, "not identifiable" fires trivially and conflates "X is useless here" with "many wirings work". Add a fifth class, no headroom, and report it per cell. SC5's compensation deficit (`DRAFT.md:34,141`) is intact minus NIP-without-X, which for low-criticality targets with 3 seeds is run-to-run evolutionary noise. Make SC5 exploratory.

10. **The ceiling is a single stochastic search** (one original-partner refit, `DRAFT.md:109`). If it underperforms, free searches "beat the ceiling" and random refits "reach" it, and the target is misclassified. Use 3 original-partner refits, take the mean, and state whether "free search reaches the ceiling" uses the mean or the best of 5 (`DRAFT.md:51-53` does not say).

11. **δ measures evaluation noise, not search noise** (`DRAFT.md:46`). The spread among the 5 free searches will likely exceed it, and then classification is driven by search stochasticity. Measure a search-level margin in the pilot and use it in the rules.

12. **The planted-optimum test is synthetic only** (`DRAFT.md:152`). Add the real-model version, on a pilot shuffle so N2 is not peeked at: take a MIP brain, delete X, and check that the free search recovers X's own evolved wiring when the ceiling is reachable by construction. This is the feasibility pilot from point 4, with a registered pass criterion.

13. **SC3-paired is likely to fail for the wrong reason.** With N2's 0.64 mirror share, the mirror ranking is strong, and adding a noisy ranking at equal weight (`DRAFT.md:139`) will usually hurt. A fairer test: AUC of the task ranking restricted to candidates the mirror leaves undecided.

14. **Statistics.** Notes point 3 is right: resampling 3 control graphs gives 10 distinct resamples, and resampling N2's one graph is a no-op. Report t-intervals beside them and add graphs if the batched pilot allows.

15. **What is fine:** the NIP/MIP relabelling, deletion versus silencing, the four-way classification as the central descriptive result, the no-task control, and the budget rule. The NIP arm is the right primary.

16. **Before the tag:** points 8 through 13, plus the mirror-matched ensemble from 03 as a condition and the verdict mechanics from notes point 4.

**Q3. Missing**

17. **A task-specificity test at generation 0 is the cheapest direct attack on the owner's question.** "Shaped for wormy tasks" predicts a task-selective edge. 02 found none: the T1 minus T0 contrast is +0.001 (`RESULTS.md:125,147-149`). Add a task panel to 03 with a non-wormy control task on the same interface, such as reward for avoiding food. If N2's edge is the same on anti-foraging, it is a reservoir property, consistent with the general input sensitivity at `RESULTS.md:172`. Minutes per task.

18. **The motor read-out has never been remapped.** Every remap moves inputs (`exp02/remaps.py:12`). N2's generation-0 sensitivity could live in the read-out (`interface.yaml:55-61`). A cheap 03 addition.

19. **A class-preserving null** (edge swaps within neuron-class blocks) is the next generic explanation a reviewer will ask about if N2 survives symmetry and routing. Optional for 03, needed before 03b.

20. **Reversed-direction N2** is already listed as 03a exploratory (`DRAFT.md:173`). It belongs in 03: same graph, wrong direction, and 01 already showed it behaves differently. Minutes.

**Q4. One item**

21. **Fund 03**, extended with points 2, 17, 18 and 20, and bundle 02b's criticality map since it is under 1 GPU-hour. It is the cheapest item, every later item needs its ensembles, and it is the only one that can falsify the roadmap's premise rather than extend it. 03a would be second, and only after its feasibility pilot passes.