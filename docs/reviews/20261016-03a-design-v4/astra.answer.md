**Revise.** Before pre-registration, change the memory gate, address selection in favor of MIP, distinguish task-driven recovery from structural predictability, replace the expansion criterion’s uncorrected contrast, and measure the actual search/batching implementation.

I checked branch `roadmap`, HEAD `eeeeb60fbb47cd6ef6023e9c7b4f142157527bd0`, the design and inherited draft machinery, relevant results and JSON records, and the implementation paths below. No files were modified and no GPU work was run.

1. **[Major; §10 question 1] Task N-mono is a plausible candidate, but the proposed gate does not establish useful memory.**

   [DESIGN.md:192](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:192) requires beating K-mono and losing performance under constant scent. Both can occur in a memoryless controller with a better instantaneous input-to-action mapping. K only changes speed at one concentration threshold and otherwise turns constantly: [scripted.py:94](D:/Claude/random/wormWars/wormwars/exp02/scripted.py:94). It is a narrow baseline, not a bound on memoryless navigation. Neural controllers also receive collision inputs.

   Retain mono provisionally, but require:
   - A stronger memoryless baseline using the same current observations, with both speed and turning dependent on concentration and collision signals.
   - A matched-current-input history probe on evolved brains.
   - A behavioral intervention showing that the relevant history improves navigation, with a control for nonspecific disruption.

   A P4-style ramp establishes history dependence, not its usefulness. Scrambling scent can also destroy its relationship to current position; a performance loss under that manipulation alone would remain ambiguous.

   Apply the frozen diagnostic to formal N2 brains too. Passing on shuffled pilot brains cannot establish that N2’s eventual solutions use memory. If these checks fail, report feasibility failure or change the task before formal work.

2. **[Major; §10 question 4] Target selection can favor MIP in the contrast intended to measure imprinting.**

   The targets are selected by deletion damage in the same intact brains subsequently used for MIP: [DESIGN.md:85](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:85). Independent selection *worlds* prevent reuse of episode noise, but not selection of neurons on which those particular MIP brains depend. NIP brains have no corresponding selection advantage.

   This does not automatically invalidate a conditional description of those brains. It does weaken interpretation of MIP−NIP as a general imprinting effect. Prefer separate selector brains, or a properly specified cross-fitting scheme. Otherwise state explicitly that the estimand concerns targets selected for dependence in the evaluated MIP brains.

   The tiers also need revision:
   - “Above p, outside the top 10” does not define medium relevance; rank 11 could be nearly as important as rank 1.
   - Specify which intact score defines p when selection averages several brains.
   - Specify interval construction, ties, pair handling when only one member is eligible, and insufficient-medium/low cases.
   - “Take those that qualify and record the shortfall” conflicts with the fixed six-neuron design. Predeclare a feasibility stop if the required panel cannot be filled, or use genuinely fixed relative tiers with separately reported absolute relevance.

   Independent confirmation of the selected deletion effects is preferable to treating the selected neurons’ nominal 95% intervals as confirmation.

3. **[Major] MIP−NIP combines retained information, compensation, and available headroom.**

   [DESIGN.md:71](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:71) defines a meaningful comparison, but its interpretation needs narrowing.

   NIP is **task-trained reconstruction without prior exposure to X**, conditional on one frozen solution evolved in X’s absence. It is not a general test of what anatomy plus the task can identify: joint optimization of the remaining weights and X’s wiring is excluded. The inherited draft acknowledges this limitation at [DRAFT.md:84](D:/Claude/random/wormWars/experiments/03a-self-consistency/DRAFT.md:84); retain it explicitly.

   A fully compensated NIP brain can have no incentive to use X, while deleting X from MIP creates substantial demand for restoration. MIP superiority can therefore reflect this demand difference. Report, together, intact performance, each arm’s deleted baseline, original-partner refit performance, compensation deficit, headroom, and reconstruction performance.

   Neither NIP failure nor a positive MIP−NIP contrast alone establishes that anatomy is uninformative or that a uniquely recoverable imprint exists. Also, “trained-network information” includes information already present before training, including anatomical initialization; attributing the contrast specifically to *learning* would need an additional control.

4. **[Major; §10 questions 2 and 6] Search all connections, but require evidence beyond generic structural predictability.**

   I favor including interface candidates over selecting away interface-adjacent targets: [DESIGN.md:106](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:106). It addresses the actual intervention and avoids leaving useful original connections supplied to the search.

   However, preserving X’s degree does **not** prevent a sensor→X→motor shortcut. Such substitution is legitimate, but recovering a few obvious interface partners is weaker evidence than recovering the broader wiring.

   The current primary compares AUC against arbitrary label permutations. That can establish enrichment over that null while leaving degree, class, mirror symmetry, and interface routing as the explanation. The structural refits do not fix this: they compare functional scores, whereas the missing comparison concerns anatomical prediction.

   Restore a central comparison against the predeclared structural ranking. For paired targets, retain the old draft’s proposed reading on candidates left unresolved by the mirror baseline, where scoreable. Show interface and non-interface results alongside the whole-pool result.

   Knowing X’s true degree is acceptable **as supplied information**; keep it explicit. The problem is not that degree matching intrinsically invalidates AUC, but that the conclusion must remain conditional on this information.

   Keep the no-task control. It checks implementation bias, but cannot rule out anatomical enrichment caused by generic routing preferences that emerge only under task selection.

5. **[Major; §10 question 5] The expansion criterion can pass without an imprinting effect. Calling it a “reading” does not solve that.**

   [DESIGN.md:156](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:156) corrects anatomical enrichment but leaves the MIP−NIP contrast uncorrected across the high/medium targets.

   Suppose both arms truly recover anatomy equally well. The enrichment tests can then pass legitimately. Under ideal calibrated intervals, a two-sided 90% interval has a 5% probability of lying wholly above zero when the contrast is zero. Across five independent targets, the chance of at least one such result is approximately **22.6%**. Dependence changes that number; it does not provide multiplicity control.

   Moreover, a hierarchical bootstrap with **three independent brains per arm** cannot obtain reliable population-level uncertainty merely by resampling five searches within each brain.

   My preference is a registered **feasibility proof of concept with descriptive contrasts**, followed by independently replicated expansion evidence. If confirmatory tests remain:
   - Include the actual imprinting contrasts in the multiplicity strategy.
   - Specify a meaningful effect threshold, not merely “above zero.”
   - Validate the proposed inference under simulated nulls.
   - Show all brain-level contrasts and sensitivity to individual brains.

   Label permutations must be shared appropriately across rankings from the same target and graph; independently permuting each brain would manufacture independent anatomical evidence. Define dependence across connection types too.

   Finally, specify how aggregate anatomical enrichment and functional success must coincide. As written, different brains or searches could supply the two components of an apparent success.

6. **[Moderate; §10 question 3] Cut the formal null arm first; retain SH-mirror for the feasibility pilot.**

   Three formal null graphs cost about **24.1 hours** at the assumed rate while supporting only a descriptive graph comparison. I would spend that capacity on independent selection, search validation, resolution, and replication of the central contrast.

   If a formal null arm remains, choose **SH-mirror**. It already includes SH-route’s routing constraints, as well as symmetry preservation: [samplers.py:7](D:/Claude/random/wormWars/wormwars/exp03/samplers.py:7), [samplers.py:16](D:/Claude/random/wormWars/wormwars/exp03/samplers.py:16). These are not mutually exclusive controls for symmetry versus routing.

   Neither ensemble replaces a within-N2 structural-prediction baseline. Also, selecting different targets in each graph matches the selection procedure, not neuronal identity, criticality, or reconstruction difficulty. Keep any N2-versus-null conclusion at that procedural level.

7. **[Major] Several implementation contracts are incomplete or contradictory.**

   Relevant statements are at [DESIGN.md:106](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:106) and [DESIGN.md:124](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:124).

   - **Gap initialization:** “every inserted edge … random sign” is wrong for gap conductances. They are nonnegative, and `Genome.clamp_()` clips negative values to zero: [brain.py:228](D:/Claude/random/wormWars/wormwars/brain.py:228), [brain.py:246](D:/Claude/random/wormWars/wormwars/brain.py:246). Specify separate chemical and gap initialization.
   - **Excluded partners:** “all connections” conflicts with excluding pharyngeal candidates if an eligible target has original pharyngeal partners. Define eligibility or treatment of those edges so exact restoration remains possible.
   - **Self-connections:** specify whether only their presence is supplied or their learned values are retained, and whether their weights can change.
   - **Union masks:** copying weights by edge identity must preserve the frozen background exactly. Reinitializing on an enlarged mask can change anatomical normalization and random-number allocation: [brain.py:214](D:/Claude/random/wormWars/wormwars/brain.py:214).
   - **Deletion during evolution:** `without_neuron()` removes incident edges but retains indexing: [deletion.py:40](D:/Claude/random/wormWars/wormwars/deletion.py:40). A common-mask implementation must prevent those edges from regrowing throughout initialization and mutation.
   - **Equivalence:** test dynamics and scores, including gap contributions to neighboring neurons’ denominators, with tolerance declared beforehand and matched batch compositions.

   Add an information-boundary test: changing hidden truth labels while preserving the allowed inputs must not change free-search proposals or initialization. Deliberately sabotage mask pinning and truth isolation to demonstrate that the checks fail.

8. **[Major; §10 question 6] Search feasibility and “interneuron use” need stronger operational definitions.**

   [DESIGN.md:127](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:127) inherits a 100-generation search without evidence that it explores this enlarged candidate space adequately. Each lineage can make at most one partner move per generation under the inherited mutation scheme, and fewer when weight/parameter moves are chosen. High-degree targets may be particularly difficult.

   Pilot measurements should include partner turnover, accepted topology moves, convergence with additional search effort, and small-score-difference ranking accuracy on independent worlds. Swap acceptance alone is insufficient. The inherited best-of-eight replacement rule is a heuristic tempering optimizer, not ordinary equilibrium parallel tempering; do not infer sampling guarantees from that name.

   E2d gives a concrete warning: at fitness differences of 0.05–0.15, eight-world comparisons tied 37% of the time; gentler mutations also reduced ranking reliability. See [E2d RESULTS.md:93](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:93). This does not prove 16 worlds inadequate, but it does mean adequacy must be measured for X-only moves.

   Similarly, **512 evaluation worlds are plausible, not established**. I calculated estimated standard errors at 512 worlds from committed 04a counts: about 0.033 for run 0, 0.035 for run 12, and 0.026 for M-avg. Those concern stereo scores, not the paired differences or mono search variability that determine this experiment’s decisions.

   Finally, nonmapped neurons are not necessarily anatomically classified interneurons. Define whether “interneuron” means an unmapped computational intermediate or the dataset’s `inter` class. NIP refit headroom shows that adding X helps that frozen brain; it is not, by itself, evidence that the intact evolved navigator used interneuron-dependent memory.

9. **[Major; §10 question 6] Outcome diversity is not evidence that the experiment separated the intended mechanisms.**

   [DESIGN.md:161](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:161) passes its separation reading whenever two non-excluded outcome summaries occur. “Search failure” plus “inconclusive” therefore qualifies. So can differences arising from unequal measurement precision.

   Remove this success criterion or replace it with an explicit table of the substantive observations required. Retain the five attributes; they prevent no-headroom and unreliable-reference cases from masquerading as biological conclusions.

   Keep the distinction between “functional success, anatomy undetermined” and demonstrated substitution. Five random partner sets do not characterize all alternatives, and absence of enrichment is not equivalence to chance. At six targets, substitution should remain descriptive unless its equivalence criterion is demonstrably estimable.

   Also reconcile target-brain outcome labels inherited from the draft with target-level, three-brain tests in v4. The unit of classification is currently unclear.

10. **[Moderate; §10 question 7] The arithmetic is correct; the timing claim remains conditional.**

    I independently recomputed [DESIGN.md:216](D:/Claude/random/wormWars/experiments/03a-self-consistency/DESIGN.md:216):

    | Component | Episodes | Hours at 420/s |
    |---|---:|---:|
    | N2 searches | 31,104,000 | 20.57 |
    | N2 evolution | 5,376,000 | 3.56 |
    | Formal null searches and evolution | 36,480,000 | 24.13 |
    | Pilot | 16,384,000 | 10.84 |
    | Stated miscellaneous allowance | 3,000,000 | 1.98 |
    | **Total** | **92,344,000** | **61.07** |

    The measured selection rates also check out: **418.65/s** in 04a, **428.87/s** in E2, **422.71/s** in E4s-1, and **1,046.37/s** for E2d’s 256×32 projection.

    The missing step is mapping those rates to this implementation. `evolve_batch()` takes one `BrainSpec`: [evolve.py:124](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:124). Different NIP deletions have different masks, so eight-run batching does not follow automatically from using “04a’s GA unchanged.” Either implement equivalent common-mask batching or time the smaller batches actually available.

    Itemize the three-million-episode allowance: selection scans, checkpoints, calibration, diagnostics, reference evaluations, resolution estimation, and any added selector brains. Include failed attempts and tuning in the cap.

    Recommended cut order: formal null arm first; then redundant reporting and optional controls. Preserve independent brains and adequate evaluation precision before sacrificing them to search count. Rechecking reduced-search feasibility on the same pilot data is tuning, so freeze the resulting configuration before a reserved validation stage.

11. **[Factual corrections; checked against committed records and code] Most numerical claims are right, but several interpretations need correction.**

    | Claim | Check |
    |---|---|
    | E1 scores | Confirmed in [freeze.json](D:/Claude/random/wormWars/experiments/E1-navigation/freeze.json): M-avg 2.16015625; K 1.02734375; wall-follower 0.65625; oracle 8.84765625; S-const 8.77734375. These are tuning scores, as the design says—not mono-world validation. |
    | 04a: 12/16 successes | Confirmed in [evaluation.json:170](D:/Claude/random/wormWars/experiments/04a-navigation-primitive/evaluation.json:170): 8/12 shaped and 4/4 unshaped. Only four runs directly support the proposed unshaped training configuration. |
    | 02b: 94/96 interface-adjacent | Confirmed in [summary.json:344](D:/Claude/random/wormWars/experiments/02b-champion-analysis/summary.json:344). These are 96 target–champion observations, not 96 distinct neurons. Interface-only deletion accounts for a median **34.95%** of full deletion damage. Therefore DESIGN lines 103–104 overstate the finding: the remaining connections are not shown to be irrelevant. |
    | Mono samples the head’s center | Incorrect literally. It samples `P_FRONT_C`: [world.py:839](D:/Claude/random/wormWars/wormwars/world.py:839), located at `head + forward_offset × heading`: [world.py:759](D:/Claude/random/wormWars/wormwars/world.py:759). The configured offset is 0.6 cells. Both food inputs become identical; collision sensing remains bilateral. |
    | Stereo mean gives “the same information” | Only approximately. Averaging two spatial samples is not identical to sampling their midpoint in a nonlinear/interpolated field. The proposed mono retuning is necessary. |
    | 02 champions had “no detected history use” | Preserve the uncertainty explicitly. [02 RESULTS.md:149](D:/Claude/random/wormWars/experiments/02-screening/RESULTS.md:149) says the data neither show nor exclude history use. [02b RESULTS.md:93](D:/Claude/random/wormWars/experiments/02b-champion-analysis/RESULTS.md:93) subsequently demonstrates history-dependent readout, while leaving its fitness value untested. |
    | 03mc implicates RIA and AIY | Supported, with the design’s cautious wording: deletion substantially reduces response amplitude while normalized P4 remains within the registered margin. It does not establish memory’s behavioral usefulness: [03mc RESULTS.md:86](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/RESULTS.md:86). |

12. **[Required before pre-registration] Make the final protocol self-contained; cut breadth rather than interpretability.**

    The pre-registration needs the resolved task and controller grids; separate tuning/selection/validation/search/final world banks; target-selection and shortage rules; exact allowed information; mutation distributions and probabilities; temperature tuning and tie rules; all reference definitions; interval and permutation algorithms; exclusion/aggregation rules; formal-N2 feasibility diagnostics; runtime accounting and stopping rules; and outcome wording for failed gates.

    Freeze a pilot protocol before running its gates. If pilot observations change the method, distinguish development from the held-out feasibility check. Also replace “the draft’s machinery” with the actual retained definitions: the candidate pool, sample sizes, units of inference, and confirmatory family have materially changed.

    I would cut the formal graph-null comparison, panel-level generalizations, the “two different outcomes” success criterion, and redundant metric prominence. Keep both arms, reference refits, structural rankings, no-task checks, exact-restoration checks, and explicit headroom reporting. Those are what make a six-neuron result interpretable.