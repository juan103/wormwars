**Verdict: fix then publish.** The run and primary measurements check out. The draft has several reporting errors, and its claim that two thirds possess two states *only* under input is too strong. These fixes do not require another simulation.

I recomputed the reader output without writing files: it matches `reading.json` exactly. I also checked the manifest against the census records, all 338 arm-specific root-distance/match/outcome records against `roots.npz`, and all A roots against the local census arrays. Those checks passed. The recorded runtime is 730.916 seconds, or 0.203 CPU-only wall hours. The plan and scripts match `7e3e5e7`; the local remote-tracking reflog records its push before the run started.

The held/recovered cross-tabulation is:

| Arm | B status | C recovered | C merged | C other |
|---|---|---:|---:|---:|
| F0 | Held | 53 | 0 | 1 |
| F0 | Not held | 0 | 115 | 0 |
| F0 | Unresolved | 0 | 0 | 0 |
| Z | Held | 53 | 1 | 1 |
| Z | Not held | 0 | 113 | 0 |
| Z | Unresolved | 1 | 0 | 0 |

The draft’s cross-tabulation and main measures table are correct. In particular:

- **C merged roots:** F0 has 114 rising-start and 1 falling-start; Z has 112 rising-start and 2 falling-start.
- **Separations:** all twelve displayed medians round correctly. The maxima range from 8.548 to 8.676 across the recorded ticks and arms; every maximum comes from held genome `(7808, 795)`.
- **Wilson intervals:** correctly calculated and rounded. For Z held, the share bounds are **32.544%–33.136%**; the two intervals are **25.936%–39.928%** and **26.484%–40.538%**. Displaying **32.5%–33.1%** would preserve the distinction lost in “33% to 33%.”
- The subclass counts, four previously seen genomes, census consistency, and zero census-root differences all check out.

The numerical and reporting fixes are:

1. **“The other 113 merged during the removal” is wrong.** [Lines 25–26](/D:/Claude/random/wormWars/docs/memory/M6-OUTLAST-RESULTS.md:25) conflate “not held” with “fading.” Under Z, **112 faded, 1 oscillated, and 1 was unresolved**, alongside the 55 held. Of the 112 fading cases, **111** subsequently reached the rising-start A root and **1** the falling-start root. The oscillating case supplies the additional rising-start merge in C. Its histories remain separated by approximately **2.058** at B’s tick 2000, so calling it merged during B is particularly misleading.

2. **Specify what agrees between arms.** [Line 27](/D:/Claude/random/wormWars/docs/memory/M6-OUTLAST-RESULTS.md:27): **163/169** agree on the three-way B status—held/not held/unresolved. **162/169** agree on C outcome and on root-match category.

3. **Clarify the panel range.** [Line 85](/D:/Claude/random/wormWars/docs/memory/M6-OUTLAST-RESULTS.md:85): recovered **counts** range from 3 to 8. Recovery **rates** range from **4/21 = 19.0%**, seed 7806, to **8/19 = 42.1%**, seed 7802. “3 of 12 to 8 of 19” is not the range of rates.

4. **Correct the post-data comparison’s group label.** [Lines 87–89](/D:/Claude/random/wormWars/docs/memory/M6-OUTLAST-RESULTS.md:87): **5.37 versus 3.84**, and **0.52 versus 0.36**, compare the **55 held** against the **113 not-held** genomes, including the oscillator and excluding the unresolved genome. They do not compare held against B-fading genomes. Restricting the comparator to the **112 fading** genomes gives **3.85** and **0.35**. Either retain the numbers and fix the label, or change both.

5. **Make the reproduction command actually rerun.** [`stage_run()`](/D:/Claude/random/wormWars/scripts/memory_m6/outlast.py:196) immediately returns when `run.json` exists. Specify a fresh `MEMORY_M6_OUTLAST_OUT` directory; the displayed command otherwise skips simulation in a checkout containing the published records.

The implementation follows the plan’s main measures and wording. B runs under the changed input; C starts from B’s actual endpoint; classification uses the appropriate phase input and starting read-out difference; matching uses `1e-6`; held and recovered are counted independently with their respective unresolved bounds. The quoted fixed wordings are exact. The additional size/read-out comparison is appropriately labelled after-data, subject to its grouping correction above.

One small reporting limitation: the reader’s `by_panel`, `by_subclass`, and `seen_before_plan` summaries contain **C outcomes only**. If the plan’s stratified “counts” are intended to cover both principal measures, add stratified B-held counts from the existing records.

**The interpretation needs a substantive rewrite.** “About a third demonstrate multistability with zero sensory input” is supported. This is stronger than merely observing two separated trajectories for 2000 ticks: the [classifier](/D:/Claude/random/wormWars/scripts/memory_m2/classify.py:112) requires accurate, distinct roots, numerical local stability, and a successful convergence check.

What that establishes is **at least two locally stable fixed points under Z, reached from the selected histories**, with the network’s biases retained. It does not establish that these are the unchanged A equilibria, that there are exactly two attractors, or that every held history pair recovers its original identities after restoration. The cross-tabulation correctly distinguishes those questions.

Conversely, **merging does not establish absence of input-free multistability**. The two selected starting states can enter the same basin while other zero-input attractors remain. This experiment does not distinguish that possibility from disappearance of one of the relevant attractors. Thus [“the rest are two states that exist only under the held input”](/D:/Claude/random/wormWars/docs/memory/M6-OUTLAST-RESULTS.md:95) contradicts the draft’s own stated limitation. “Two thirds need their input” also overgeneralizes the tested abrupt, 2000-tick interruption.

**I disagree with restricting “attractors of a known kind” to the two-thirds group.** M6-3 already includes Liu 2022’s persistence after input termination, both in the [local literature review](/D:/Claude/random/wormWars/docs/memory/M6-3-LITERATURE.md:243) and in the [paper itself](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2022.808824/full). The new finding refines the measured input dependence of this sample; it does not remove the held third from known attractor mechanisms. A narrower comparison with Kunert-Graf’s particular driven regime can be qualified without making that broader claim.

Suggested replacement:

> Among these 169 census-selected switches, 55 reached two distinct stable fixed points during 2000 ticks with all sensory input removed; 112 faded to a common fixed point, one oscillated, and one remained unresolved. After restoration, 54 recovered their original pair of states. These results establish zero-sensory-input multistability in the held cases and loss of the tested distinction in the fading cases. They do not establish that the fading genomes lack other zero-input attractors. This refines the switches’ input dependence while remaining consistent with known attractor mechanisms.