**Verdict: revise.** Draft 1 turns evidence for possible multistability into a demonstrated two-state latch. Batch 8 does not establish that. Several earlier qualifications also disappear between the “weaknesses” section and the conclusions or decision rules.

I inspected the roadmap, archived reviews, spike scripts and outputs, and relevant engine, sampler and 03mc files. I ran no analyses or experiments.

The main blocker is the batch-8 interpretation.

> “in 4.1% of N2 genomes, the network is unstable at the midpoint between the two histories’ end states, but stable at each history’s own end state. That is a saddle between two stable states”

This is unsupported for three separate reasons:

- **The Jacobians are at the ramp-end states**, before the 300-tick follow-up, and their arithmetic midpoint. They are not evaluated at verified final attractors. See [batch8.py:59](/D:/Claude/random/wormWars/scripts/memory_spikes/batch8.py:59).
- Neither the midpoint nor either history’s state is checked for being a fixed point. A spectral radius above one at an arbitrary point does not establish a saddle; a radius below one at another arbitrary point does not establish a stable state.
- The saved output does not give the intersection needed to say that **all 21 midpoint-expanding genomes** have both own-state radii below one. Six eligible N2 genomes have an own-state radius above one, but their overlap with those 21 is not reported.

The relevant counts are:

| Batch-8 quantity | N2 | SH-2010000 | SH-class-2030000 |
|---|---:|---:|---:|
| Eligible genomes | 502 | 498 | 487 |
| Eligible, midpoint radius > 1 | 21 | 0 | 9 |
| Meets script’s “settled” rule | 8 | 0 | 6 |
| Eligible, either own-state radius > 1 | 6 | 1 | 14 |
| Tick-30 numerator share from midpoint-expanding group | 39.2% | 0% | 35.1% |
| Tick-30 numerator share from “settled” group | 25.2% | 0% | 30.4% |

The percentages defining the first two classes use **512 total genomes**; the numerator shares use **eligible genomes’ numerator**. These are directly recoverable from [batch8.json](/D:/Claude/random/wormWars/runs/memory-spikes/batch8.json).

> “every N2 genome whose difference stays at full size to tick 300 is one of these”

The file supports a different statement: **all eight N2 genomes meeting the script’s “settled” rule have midpoint radius above one**. The rule is:

\[
|d(0)|\ge10^{-3},\qquad
|d(300)|/|d(0)|>0.1,\qquad
|d(300)-d(250)|/|d(0)|<0.02.
\]

It checks one scalar output at two late times. It neither requires full-size retention nor checks that the difference stayed there throughout the follow-up. The **median** retention of those eight is approximately 1.005 at tick 300; that does not establish the claim for every member. See [batch8.py:64](/D:/Claude/random/wormWars/scripts/memory_spikes/batch8.py:64).

This “settled” definition is also weaker than 03mc’s: 03mc checked the maximum full-state range over the last ten ticks, across both histories and all neurons, against \(10^{-4}\). Even that study explicitly declined to claim stable states. See [twin.py:23](/D:/Claude/random/wormWars/wormwars/exp03/twin.py:23), [p4mc.py:553](/D:/Claude/random/wormWars/scripts/p4mc.py:553), and [03mc results:149](/D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:149).

> “these 4% carry 39% of the tick-30 signal”

Numerically correct **for the midpoint-expanding group and the eligible numerator**. It is not the contribution of demonstrated latches, and it is not 39% of N2’s *excess over nulls*. The eight operationally settled genomes contribute 25.2%.

> “their unstable direction lies 92% on a 30-neuron head core and 67% on RMD and SMD alone”

The numbers check out, with an important definition: these are **averages of normalized squared components of the leading right eigenvector**, across the 21 midpoint-expanding genomes. They are not measurements of where the actual history difference lies, nor proof that this mode carries that difference. The script does not measure its excitation by the histories or its contribution to turning. The 10% and 3% references are set-size fractions, not statistical null distributions. See [batch8.py:42](/D:/Claude/random/wormWars/scripts/memory_spikes/batch8.py:42).

For SH-class, 33% means mass on **N2’s selected 30-neuron set**. It does not characterize that graph’s own best-localized core.

> “it is almost never oscillatory”; “so it is a latch, a flip-flop … not an oscillator”; “the unstable modes are real, not complex”

These overreach. Two of the 21 leading midpoint eigenvalues are complex. Their frequency is lower than in the remaining eligible N2 genomes—9.5% versus 15.2%—so **Fable’s proposed enrichment of complex leading eigenvalues is not observed**. That is the defensible negative result.

A leading eigenvalue at a transient midpoint does not classify the subsequent trajectory. Furthermore, the script’s separate `oscillating` flag means at least three sign changes in a sparsely sampled scalar difference. Samples are at 0, 5, then every ten ticks; there is no late-amplitude floor. This can miss oscillations or count tiny numerical sign changes, and `oscillating` and `settled` are not mutually exclusive. See [spikes.py:28](/D:/Claude/random/wormWars/scripts/memory_spikes/spikes.py:28) and [batch8.py:69](/D:/Claude/random/wormWars/scripts/memory_spikes/batch8.py:69).

Consequently, “SH-class … has latches too (1.8%)” also mislabels its nine midpoint-expanding genomes. Six, or 1.17% of the panel, meet the operational settling rule; neither percentage is a verified latch fraction.

A replacement reading could be:

> Batch 8 strengthens the hypothesis of localized multistability. In N2, 21 of 512 genomes have an expanding ramp-end midpoint Jacobian. Eight meet a late-output plateau criterion; all eight belong to that group, and none has an own-ramp-end spectral radius above one. Leading midpoint eigenvectors are concentrated on the selected head core. Fixed points, basin structure and oscillatory trajectories remain to be checked.

The remaining factual corrections are as follows.

| Roadmap claim | What the files support |
|---|---|
| “All numbers are from fresh CPU panels” | False. The median ranks, amplitude correlations and structural regressions use the original 03mc arrays. Distinguish those analyses from fresh CPU spikes. [check_mixture.py](/D:/Claude/random/wormWars/scripts/memory_spikes/check_mixture.py), [check_structure.py](/D:/Claude/random/wormWars/scripts/memory_spikes/check_structure.py). |
| “The typical N2 brain does not forget more slowly”; “the same median rate” | The reported medians are ordinary relative to graph variability. **Equivalence was not tested.** The 0.197/0.192/0.200 values are tick-30 **voltage-norm retention ratios**, not fitted decay rates. [batch4.py:74](/D:/Claude/random/wormWars/scripts/memory_spikes/batch4.py:74). |
| “the genomes with large differences lose less of them” | The reported association is still negative. It is Pearson correlation of **log starting amplitude** with retention, whose denominator contains starting amplitude. Say “the negative association is weaker in N2.” [check_mixture.py:35](/D:/Claude/random/wormWars/scripts/memory_spikes/check_mixture.py:35). |
| “It is driven by N2’s upper quarter of genomes” | The elevated retention upper quartile and concentration among large late contributors are supported. They are different selections; their overlap and contribution decomposition remain M1 work. [check_mixture.txt](/D:/Claude/random/wormWars/runs/memory-spikes/check_mixture.txt). |
| “Raising shuffles to N2’s triangle counts did nothing” | It did not recover N2-level retention. It did change values: for example, SH-2010001 goes from 0.353 to 0.264 under the cycle-count intervention; SH-2010002 goes from 0.234 to 0.282 under the feed-forward intervention. [batch1.json](/D:/Claude/random/wormWars/runs/memory-spikes/batch1.json), [batch2.json](/D:/Claude/random/wormWars/runs/memory-spikes/batch2.json). |
| “loops in general (triangle counts) are out” | Total triangle-count sufficiency is weakened. Triangles do not exhaust loops, and these interventions do not eliminate weighted feedback explanations. |
| “N2’s core is enough in a shuffled graph”; “73% of its edges shuffled” | The percentage concerns **off-diagonal chemical edges**. Every arm retains the entire N2 gap layer, all autapses, and roughly 27% of the original off-diagonal chemical edges. This is conditional preservation, not standalone sufficiency. [batch7.py:29](/D:/Claude/random/wormWars/scripts/memory_spikes/batch7.py:29), [batch7.py:97](/D:/Claude/random/wormWars/scripts/memory_spikes/batch7.py:97). |
| “a hub set with as many internal edges” | Approximately matched: **202 versus 199**, not equal. The six graph-panel pairs comprise three graphs evaluated on two panels. [batch7.json:67](/D:/Claude/random/wormWars/runs/memory-spikes/batch7.json:67). |
| “no neuron’s tau or bias predicts retention beyond \|rho\| 0.10” | Numerically false: N2’s maximum tau correlation is 0.100338; SH-class’s maxima are 0.120028 for tau and 0.106506 for bias. “Small observed marginal correlations” is accurate; “dead” is stronger than this screen establishes. [batch4.json:176](/D:/Claude/random/wormWars/runs/memory-spikes/batch4.json:176), [batch4.json:702](/D:/Claude/random/wormWars/runs/memory-spikes/batch4.json:702). |
| “a numerical artefact … dead”; M0 “ruled the artefact out” | The baseline correction is right: T1 uses 32 substeps. Sixteen produces very similar aggregate retention, not identical values. This is useful robustness evidence, but it does not exclude numerical effects on the rare dynamical classes now being claimed. The original M0 requested finer steps and individual-dynamics checks. [grid.py:53](/D:/Claude/random/wormWars/wormwars/exp02/grid.py:53), [batch1.json](/D:/Claude/random/wormWars/runs/memory-spikes/batch1.json), [ChatGPT roadmap](/D:/Claude/random/wormWars/docs/reviews/20261020-memory-diverge/chatgpt.roadmap.md). |
| “the signal regrows from the rest of the core” | Erasure establishes regrowth from outside the eight erased neurons. Its specific source within the remaining core is not isolated by that experiment. The proposed complement-erasure control is still relevant. |
| “gap junctions … not the cause” | Gaps-off increases retention in N2 and the one SH graph tested. Their different penalties could still help explain the **between-graph advantage**. Whole-probe changes also mix writing and maintenance. [batch1.py](/D:/Claude/random/wormWars/scripts/memory_spikes/batch1.py). |
| “the spike rewirings … keep N2’s 38 autapses” | Correct for N2-derived arms. Batch 2 also rewires null parents, preserving those parents’ diagonals. Say “preserve the parent’s autapses and carry weights with source slots.” [batch2.py](/D:/Claude/random/wormWars/scripts/memory_spikes/batch2.py). |

The numerical claims that do check out include the registered 0.436 versus 0.255–0.291 result; median ranks 17–46; panel values 0.469/0.396/0.504; batch-7 means 0.482/0.343/0.363/0.454; 140 dissolution swaps removing approximately 70% of original internal edges; and the listed core neuron classes. The pharyngeal erasure result also checks out, specifically for tick-30 output. Warm-up and food manipulations preserve the N2–SH lead over their tested settings; they do not establish general probe independence.

“Response about five times a null’s” is reasonable shorthand for the earlier comparison with **typical null responses**: 03m reports 4.7–7.1 times ensemble medians. Specify that comparator and distinguish this held-level response from the ramp-end separation. [03m results:36](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:36)

The regenerated extrapolation is present: 0.438, interval [0.398, 0.481]. That documentation issue is resolved. Its weak extrapolative fit still does not identify a mechanism. [check_structure.txt](/D:/Claude/random/wormWars/runs/memory-spikes/check_structure.txt)

There are also small provenance corrections:

- “Between 2 and 3 … **8 batches**” should be **seven**, with batch 8 after round 3.
- “13 mechanism families” describes the selection’s consolidation, not a shared round-2 taxonomy: Fable’s table includes a toolbox category, while Astra’s has sixteen families.
- The substeps issue was an incorrect description of an available configuration, not a number lacking a source.
- “The 2 to 5 high-retention null graphs per ensemble” needs a selection definition. At tick 30, the counts reaching N2 are **0, 0, 2, 1, 2**. “Inspect the top two to five graphs from each ensemble” would be a clear proposal.

**On fairness, the attribution is partly accurate, but “all accepted” is not.** The roadmap retains my decomposition, matched-norm objection, conditional parameter bookkeeping, boundary confound, tau controls and write–hold–read distinction. However, it repeats four statements I specifically qualified: median equivalence, “large differences forget less,” standalone core sufficiency, and the saddle inference.

In particular:

> “the saddle reading of the midpoint Jacobian (borne out by batch 8)”

I said it **could indicate** a separating saddle and explicitly warned that the midpoint need not lie on either trajectory. Batch 8 has not established that possibility as fact. My proposed object was **several history-selectable states**, not specifically a verified two-state flip-flop. See [my archived answer:29](/D:/Claude/random/wormWars/docs/reviews/20261020-memory-select/astra.answer.md:29).

The important omissions from my proposed plan are:

- **Internal persistence versus read-out alignment**, measured in the genomes carrying the numerator. With activity difference \(\delta a\), output retention factors into activity-norm retention and change in alignment with the turn read-out. This was a central competing explanation, not an optional elaboration.
- **Correcting the linear forecast’s observable**, and checking propagation along the actual history difference. Batch 3’s voltage projection is not the observed tanh-output difference.
- **A pulse-written history or independent read-out**, to delimit probe dependence.
- Matching erasures for **immediate output effect as well as norm**, using multiple intervention delays, and explicitly preserving unchanged signed parameters.

These are in [my proposed steps:91](/D:/Claude/random/wormWars/docs/reviews/20261020-memory-select/astra.answer.md:91). Not every suggestion needs adoption, but dropping these while declaring the latch mechanism substantially settled changes my position.

There is one clear misattribution to Fable: the proposed “under 1% to at least 3%” threshold concerned **growth fraction**, not latch fraction. Those endpoints cannot be substituted while calling them Fable’s draft thresholds. [Fable’s step 5:48](/D:/Claude/random/wormWars/docs/reviews/20261020-memory-select/fable.answer.md:48)

**The broad order is workable, but I would change the gates and allocation of effort.**

1. **Start with M1 accounting, then a small validated dynamical pilot before the large census.** M1 currently promises a latch fraction before M2 establishes how to identify one. Keep the registered ratio, report excluded small-start numerator and denominator contributions, and add state-persistence/read-out-alignment accounting. Separate randomly sampled null graphs from deliberately selected high-retention examples; panel standard errors do not describe graph variability.

2. **Keep the amplitude intervention, weaken its decision rule.** Reduced retention after shrinking separation demonstrates amplitude dependence. It does not establish that response size fully explains the original lead or that the structural mechanism is irrelevant: nonlinear basin selection can itself depend on amplitude. Report actual post-intervention state and output amplitudes, use consistent denominators, and compare matched amplitudes and alignment across graphs. Q-B and Q-C did not already answer the tick-30 maintenance question.

3. **Make M2 genuinely diagnostic.** Record full-state trajectories and speeds, inspect late-window convergence, evaluate Jacobians at candidate equilibria, and test return after perturbation. Use every-tick recordings for selected persistent contributors. Allow multiple discrete states and an unresolved category; “latched, fading or oscillating” need not exhaust the outcomes. A continuum of finite-time endpoints could also be slow fading. Check representative classifications under finer integration before treating them as mechanisms.

4. **Run cheap M3 anatomy calculations early, but remove the hard \(\rho<0.2\) veto.** A weak correlation rejects that predictor as a useful predictor; it does not show there is “no structural handle” or invalidate a controlled transplant. Anatomy-only formulas chosen after inspecting the results are still exploratory choices. Freeze them before validation on unused graphs. Also, the original arrays contain settling ranges, not verified latch identities or Jacobians; call any reused endpoint a proxy.

5. **Bring the inexpensive M4 controls forward and sharpen maintenance specificity.** Tau controls, gap-dissipation measurements and complement erasure need not wait for all 640 graph features. A hold intervention can still disrupt delivery to the output. Measure internal separation, restore a common read-out condition, and include write-only/read-only comparisons where necessary. Rescue should persist through a subsequent delay; immediate output restoration is weak evidence. Replace “the smallest structure” with “the smallest successful structure among those tested.”

6. **Move a modest exploratory transplant screen into M4/M5 preparation.** Independent hosts, exact block replacement, gap/autapse dependence, and preservation of untouched parameters should be checked before committing to an extensive dissection or confirmation. Off-read-out transplantation needs a way to observe the transplanted state independently of the original turn read-out.

The statement that only two decision points can change the plan also contradicts M2’s own branch. Maintenance specificity and portability should be additional explicit gates.

> “A failure in foreign hosts would mean the core needs N2’s surroundings”

That interpretation is too specific. Failure would reject portability **under the tested embedding and assay**. Failure to write or observe the state, altered parameters, or insufficient precision remain alternatives. The controls should distinguish those explanations.

**M1–M4 can remain exploratory**, provided their outcomes are reported that way. There is no need to pre-register every exploratory screen. However, a confirmatory transplant alone would not confirm the whole maintenance mechanism. M5 should also validate the narrow surviving maintenance claim on fresh draws, or that contrast should receive its own pre-registration after the exploratory work.

Before confirmation, fix the classification rules, eligibility floors, sampling units, graph/genome counts, primary contrasts, uncertainty method, exclusions and outcome wording—not only the three items currently listed. “Controls moving neither” needs an equivalence margin; nonsignificance is insufficient. Split M5 explicitly into exploratory construction/screening and a subsequently registered fresh test.

Finally, the cost estimates need qualification. Batch 8 records approximately **339 seconds per graph for 512 genomes**. Applying that complete three-Jacobian workflow to M1’s 36 panels of 1,024 genomes extrapolates to roughly **6.8 CPU hours**, before amplitude arms. That is a planning extrapolation, not a benchmark. M1 can be cheaper by postponing spectra and deeply characterizing a selected subset. Likewise, M3’s “under an hour” is plausible for anatomy and existing-array summaries, not a fresh validated latch census across all 640 graphs. [batch8.json:28](/D:/Claude/random/wormWars/runs/memory-spikes/batch8.json:28)

Before pushing, I would require the batch-8 rewrite, restoration of the state-versus-read-out distinction, removal of the amplitude/predictor overinterpretations, and correction of the factual and attribution errors above.