**Both pushes need fixes, but neither needs to wait for 03r to finish.** The main problems are publication-history wording and a correction that reintroduces a prediction already withdrawn in D051.

I verified the 41-commit range, scanned all 192 newly reachable blobs for common credential/email/session-link patterns, inspected the 29 historical JSON blobs for graph structures, and recomputed 03’s rank counts and Holm adjustments. I did not rerun pytest; no usable Python interpreter was available.

**Push 1 — `roadmap`**

**Blocking issues**

1. **Explicitly acknowledge that this push changes the publication plan.**  
   [03r PREREGISTRATION.md:333](D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:333) promises that the README will say “a full replication was run before publishing.” [DECISIONS.md:1406](D:/Claude/random/wormWars/DECISIONS.md:1406) records the stronger original decision: replication before *anything from 03* is published. This push makes those results public immediately. Merging into main later does not preserve that promise.

   Add a dated publication-plan amendment, preserving the frozen protocol: 03’s first-run results become public on this branch while 03r runs; the combined main-branch report follows completion; every registered outcome will be reported. Supersede the promised “before publishing” sentence explicitly.

2. **Narrow the timing claim and put the disclosure beside the protocol.**  
   [ROADMAP.md:22](D:/Claude/random/wormWars/ROADMAP.md:22) and [DECISIONS.md:1536](D:/Claude/random/wormWars/DECISIONS.md:1536) say GitHub’s receipt proves publication preceded “the results.” That overstates what it proves. Interim measurements already exist; receipt timestamps public availability, not when private results were generated or inspected.

   At inspection, there were **525 saved ensemble measurements and no N2 measurement files**. Sampled provenance identified `7c146fc`, and the registered code/configuration/protocol files have no subsequent changes. This supports the stated local chronology, but is not independent proof of noninspection.

   Add a clearly dated notice beside the frozen registration and in the branch README stating:
   - local freeze/binding commit;
   - public disclosure occurred after measurement began;
   - progress and N2 measurement status at disclosure;
   - what interim outputs had been inspected;
   - GitHub timestamps public disclosure, not pre-run registration.

3. **Reconcile 02b before this public push, not only before merging.**  
   [02b RESULTS.md:18](D:/Claude/random/wormWars/experiments/02b-champion-analysis/RESULTS.md:18) says champions “steer by which side the food is on” and that within-wey regression excludes circling geometry. That causal inference is unsupported: removing each wey’s mean does not eliminate time-varying trajectory confounding. The same document acknowledges correlations rather than causes at line 52, and its controlled probe shows no group-level change at line 56.

   There is **no necessary contradiction** between a turning association and 02’s failure to find a meaningful performance benefit. Say that explicitly. Replace the causal summary with the observed within-wey association and distinguish it from meaningful stereo use. [ROADMAP.md:11](D:/Claude/random/wormWars/ROADMAP.md:11) already identifies reconciliation as necessary before publication.

**Should fix soon**

- **Keep 03’s conclusion at the ensemble-comparison level.**  
  [03 RESULTS.md:307](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:307) still says none of the ensembles “matched” the property. Prefer “unusually high normalised history dependence relative to all five reference ensembles.” SH-route-20078 exceeds N2, as lines 8–9 correctly disclose. The numerical verdict itself checks out: counts **0, 1, 0, 0, 0**, Holm-adjusted **p = 0.0465116**.

**Minor**

- **The roadmap reverses the subtraction.**  
  [ROADMAP.md:8](D:/Claude/random/wormWars/ROADMAP.md:8) says “subtracts dorsal from ventral.” It is **dorsal minus ventral**, confirmed by [interface.yaml:60](D:/Claude/random/wormWars/configs/interface.yaml:60) and [probes.py:115](D:/Claude/random/wormWars/wormwars/exp02/probes.py:115). Say the *read-out* is invariant under left/right relabelling; that does not prevent an asymmetric network from computing a comparison.

- **Archived reviews contain local paths.**  
  For example, [astra.answer.md:8](D:/Claude/random/wormWars/docs/reviews/20260926-220511-03-results/astra.answer.md:8) contains `D:/Claude/random/wormWars/...`. These reveal a workspace layout and will not work as GitHub links. I found no sensitive username in those paths. They already exist in the proposed history, so changing HEAD would not remove them from publication.

- **Machine JSON retains `NaN`.**  
  [03 RESULTS.md:195](D:/Claude/random/wormWars/experiments/03-generation0/RESULTS.md:195) correctly discloses this. A separate standards-compliant export using `null` would improve interoperability.

On integrity: **publishing 03 now does not itself compromise 03r.** Its designers already knew all of 03’s results, explicitly disclosed at [03r PREREGISTRATION.md:25](D:/Claude/random/wormWars/experiments/03r-replication/PREREGISTRATION.md:25). The important conditions are unchanged analysis/stopping rules, disclosure of interim inspection, and reporting either outcome. The problem is the inaccurate publication narrative, not public access to already-known 03 results.

On hygiene: the inspected JSON contains measurements, aggregate structural statistics, seeds and hashes—not adjacency matrices, edge lists or anatomical-weight vectors. No new binary graph/data files or credential matches were found. Review prose does mention isolated anatomical connections, for example [fable.answer.md:7](D:/Claude/random/wormWars/docs/reviews/20260925-210723-03-design/fable.answer.md:7); therefore “no edges mentioned anywhere” would be too broad. I found no publication-blocking private material.

On D062: the response-magnitude correction checks out—approximately **4.8–7.4× ensemble medians and 1.50× the largest graph**. The group-mean qualification and fresh-N2-genomes/secondary-outcomes corrections are supported. The credits match the archived attributions, though repository records cannot authenticate model identity. The timing component needs the qualification above. The [carry-over section:260](D:/Claude/random/wormWars/ROADMAP.md:260) faithfully summarises v2.2’s question, plasticity controls, untested task specificity, old meaning of “04”, and later reconstruction ideas.

**Push 2 — `main`**

**Blocking issues**

1. **The correction incorrectly says 03 predicts reduced directional response.**  
   [main RESULTS.md:65](D:/Claude/random/wormWars-main/experiments/02-screening/RESULTS.md:65) says the mirror control is predicted to lower directional response and “That is how experiment 03 uses it.” This is false. [DECISIONS.md:1184](D:/Claude/random/wormWars/DECISIONS.md:1184) explicitly withdraws that prediction; [03 DESIGN.md:39](D:/Claude/random/wormWars/experiments/03-generation0/DESIGN.md:39) says **“with no predicted direction.”**

   Replace that passage with: symmetric wiring alone does not enforce symmetric dynamics; SH-mirror remains a structural control, without a predicted direction of effect.

2. **Make the symmetry argument’s assumptions explicit.**  
   [main RESULTS.md:55](D:/Claude/random/wormWars-main/experiments/02-screening/RESULTS.md:55) is correct for a **fully mirror-equivariant network under mirror-related inputs and initial states**. It is not guaranteed by symmetric connectivity alone. Random signs, biases and time constants can break that symmetry; the implementation draws them independently at [brain.py:172](D:/Claude/random/wormWars/wormwars/brain.py:172). One qualifying sentence prevents the correction from replacing one overgeneralisation with another.

**Should fix soon**

- **Correct the live docstring in the same corrective push.**  
  [main structure.py:3](D:/Claude/random/wormWars-main/wormwars/exp02/structure.py:3) still teaches the erroneous “comparison almost for free” rationale. There is no technical reason to wait for the roadmap merge. Preserve the quoted historical error in the Corrections entry and update the explanatory docstring. Add correction pointers beside the historical preregistration/D041 passages without rewriting their registered text.

**Minor**

- **Clarify the date’s meaning.**  
  [main RESULTS.md:43](D:/Claude/random/wormWars-main/experiments/02-screening/RESULTS.md:43) dates the correction September 26. Local commits record discovery/correction on September 25 (`d82591b`, `d0a3cd8`); this proposed publication is September 27. Distinguish discovery, preparation and publication dates.

The quoted registration text is accurate after Markdown/reflow normalisation. The unchanged-result explanation is also correct: the conditional symmetry reading was never triggered. The entry satisfies the owner’s quote-and-correct rule once the scientific explanation is fixed. I found no reason to alter the numerical results or main README as part of this mirror correction.

Push 1: **push after fixes**  
Push 2: **push after fixes**