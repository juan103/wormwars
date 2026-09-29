The runs appear to follow v4.1, and the numerical summaries check out. **The interpretation needs correction before publication.** I found no execution failure requiring a rerun.

**What I checked.** I reviewed `roadmap` at `40fcbef`: PLAN, RESULTS, both READMEs, D113, all seven requested JSON files, the original 03/03r supplements, relevant runner and engine code, prior plan reviews, Git history and push reflog, and local compute records. I ran no simulations or tests and changed no files. I did not independently reconstruct the per-genome measurements from the NPZ files.

**Execution and arithmetic**

- The Git objects for **all five guarded paths are identical** at `66edaee`, `5312475`, `f6971ec` and `a3f2ec1`; the intervening history contains no guarded-file changes.
- Local records show 04a evaluation ended at **00:45:57 UTC**, followed by the plan merge at **00:47:12**, then graphs → synapses → weights → decay → lesions. Push reflog entries precede each command. Recorded cleanliness concerns the **guarded files**, rather than necessarily the entire working tree.
- The code and records agree on **2,048 strains, one state row per strain, 32 substeps**, with each deletion evaluated separately. The lesion order and five follow-up targets match the plan.
- All four N2 reproduction checks agree exactly with the original supplement. All **81 decay graphs**, including N2, reproduce their original numerator and denominator exactly. The empty deletion also matches.
- Compute totals are **11,962.888806 seconds = 3.323025 hours**, five completed attempts, no failures. The **13,894,287,360 neural updates** exactly match the planned histories, reproduction checks and follow-ups. These hours are synchronized wall-clock accounting, as the JSON states.
- I independently recalculated all **627 valid P4 ratios**, their threshold classifications, the lesion residuals, Q5 medians/counts, Q4 endpoint ratios/count fractions/ranks, and Q1 statistics from both original supplements. They agree, with only floating-point rounding differences in the regressions. The Q1b prose agrees with `tails.json`; its underlying per-genome statistics were not independently regenerated.

Selected verified results:

| Quantity | Recalculated |
|---|---:|
| Pooled P4 95th percentile | 0.888599534 |
| Pooled response median / maximum | 0.022893334 / 0.073173425 |
| Lowest deletion P4: AIZ pair | 0.906949498 |
| Q5 above pooled P4 95th percentile | 27/64 independent; 29/64 paired |
| Q5 below intact N2 P4 | 59/64 in each design |
| N2 separation remaining at tick 300 | 9.4116% |
| Null median separation remaining | 0.4236% |
| N2 eligible genomes retaining >10% | 49/1,987 |
| Eligible, retaining separation, and settled | 26/2,048 = 1.2695% |

**Must-fixes**

1. **Keep “response only” as the threshold classification; remove the stronger mechanistic dissociation.**  
   The RIA/AIY classifications are correct. But [the opening summary](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:26) incorrectly says these deletions bring response to the shuffles’ “typical level.”

   | Deletion | Response | Multiple of pooled median | Null graphs below it | Numerator reduction | Response reduction |
   |---|---:|---:|---:|---:|---:|
   | RIA pair | 0.049224 | 2.15× | 96.4% | 61.5% | 61.7% |
   | AIY pair | 0.060645 | 2.65× | 98.4% | 53.1% | 52.8% |

   These responses enter the null range but remain in its upper tail. More importantly, **the raw history difference falls almost proportionally to the response**. The normalized ratio survives; the history signal is substantially reduced. “They have different sources” in [Reading it together](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:135) is therefore unsupported. Say that the interventions reduce response amplitude while leaving P4 comparatively unchanged. Dependence on RIA/AIY is supported; a separate persistence mechanism is not established.

2. **Correct the universal weight-permutation claims and Q5’s comparison wording.**  
   The [README status](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/README.md:6) says high history dependence survives **every** weight permutation. That is false under the stated threshold: only **27/64 and 29/64** remain above it. P4 ranges down to **0.7330 and 0.7295**. Chemical-only permutations also cross below it in **2/8** seeds.

   [Q5’s “0 of 128 above any null graph’s”](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:78) should read **“0 of 128 above the pooled null maximum.”**

   “Wiring alone” also needs qualification: the permutations retain the anatomical magnitude distributions, interface and initialization scheme. A defensible statement is that **N2 topology under these magnitude permutations retains an elevated P4 distribution**. Relative to the pooled null median, the permutation medians retain approximately **60% and 58% of N2’s P4 excess**—weight placement makes a substantial contribution too. The two designs reuse the 64 magnitude permutations; they are not 128 independent permutations.

3. **Replace “distributed” and “not carried by any … synapse type” with the tested conclusion.**  
   [The opening and synthesis](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:29) go beyond a deletion screen. No tested single or bilateral-pair deletion crossed the P4 threshold. This does not establish network-wide distribution: redundancy within a smaller circuit, dependencies differing between genomes, and the excluded read-out neurons remain possibilities.

   Gap junctions are dispensable for these measured N2 properties. **Chemical-synapse dispensability was not established**, because chemical-off P4 is invalid.

   Also replace “no response”/“no route” with **“response below the validity floor.”** Chemical-off response is **3.5879 × 10⁻⁵**, not zero. The measurement does not establish absence of a path.

4. **Narrow the settling claim to the registered finite-window observation.**  
   [“A lasting different state”](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:31) is not established. “Difference intact” also suggests more than the criterion requires.

   Use: **“26 of 2,048 genomes retained more than 10% of their initial separation and met the full-state settling criterion over the final ten ticks at tick 300.”**

   “Consistent with distinct stable states” is fair, as the plan says. A ten-tick tolerance test does not demonstrate asymptotic stability. Likewise, the 26-versus-23 split partitions the **49 qualifying genomes**, not the magnitude of all remaining separation.

5. **Remove the causal inference from saturation.**  
   [The measured slopes](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:104)—N2 **0.4432**, null median **0.7340**—support greater saturation at the read-out neurons. They do **not** establish that saturation produces part of N2’s large response. Lower local slope can compress differences; its contribution requires another comparison. Keep the observation and state that it complicates interpreting the output ratio.

6. **Restore Q1’s uncertainty and propagate the corrections to D113.**  
   [The README’s “association is not estimation noise”](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/README.md:27) contradicts the agreed plan’s narrower statement. Use **“estimation noise alone is unlikely to explain the association.”** A separate response measure also does not remove the possible association transmitted through P4’s denominator.

   Correct the corresponding overstatements in [D113](/D:/Claude/random/wormWars/DECISIONS.md:3416). Follow the repository’s dated-correction rule.

**Findings I would retain, and suggestions**

The **gaps-off comparison is fair as a within-graph change comparison**: N2’s ΔP4 is **+0.014405**, below the null panel’s **+0.050797 to +0.143173**. N2’s response change, **+0.014067**, lies **inside** the null range, **+0.005605 to +0.028865**; say that explicitly. Five gaps-off null graphs exceed gaps-off N2’s P4, so this comparison should not imply exceptional P4 relative to the entire altered panel.

The **slower aggregate relaxation** reading is supported beyond the endpoint: at ticks 5, 10 and 50, N2 retains a greater fraction than all 80 panel graphs; at tick 300, greater than 78. Keep its scope as this probe and genome sample, without implying every N2 genome relaxes slowly.

For context around possible stable states, report the null comparison: **SH-10007 has 171 qualifying settled genomes and SH-mirror-40003 has 37**, versus N2’s 26. This feature is not unique to N2.

Update stale status text: the experiment README still says “What runs next”; the root README still says “simulations running.” The single-neuron response range also rounds to **0.089–0.104**, rather than 0.088–0.104.

**Confirmatory follow-up**

I would register two narrow questions:

- **RIA/AIY response reduction with preserved normalized P4.** Pre-name the pairs, matched control deletions, fresh genome batches and null graphs. Register response effect sizes and a justified **equivalence margin for P4**, rather than treating failure to reject a difference as preservation. Analyze numerator and denominator jointly. Retain threshold classes as secondary outcomes.
- **Greater retained separation in N2.** Register a primary endpoint—such as the tick-300 ratio of means—plus the full curve, eligibility floor, settling rule, exclusions and statistical unit. Use independent genome batches and fresh null graphs, with graph-level inference and multiplicity specified.

A claim about stable states needs a separate, stronger protocol: longer follow-up, sustained full-state convergence and perturbation/recovery checks. A claim that chemical weight placement acts specifically through RIA/AIY needs their **factorial combination**, not the juxtaposition of separate interventions.

Commit and push that registration before fresh data. Do not register “distributed persistence” as though 03m had already localized its mechanism.

**03m results: fix**