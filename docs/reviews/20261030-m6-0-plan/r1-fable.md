**Verdict: agree with fixes.** The design answers the question it asks, the budget is safe, and the genomes, settings and read-out check out against the files. Five things need fixing before the run, two of them in the fixed readings, and the code change needs different tests from the ones listed.

## 1. Will the answer be read honestly

What I verified: the local files hold exactly the table's counts of g39, g00 and T1 g79 genomes. The mutation settings match 02's bundle, including a mutation probability of 1. The turn read-out is four neurons a side, so the classifier's read-out vector equals 02b's mean difference and the start difference a is 02b's raw turn. The remap touches only the food channels, and the drafted guard asserts that. The five-switch threshold is the smallest count that can reach one-sided p below 0.05 with no negative runs, so the two halves of the first reading agree.

Fixes, by weight:

1. **Comparison 3 pairs genomes that are not the same.** 02b's drift genomes were a GPU draw; the plan draws new ones on the CPU. A Spearman "across g00, g39 and drift" against 02b's values pairs a third of its points wrongly. Pair g00 and g39 only. Compare drift as two per-run sets of four, unpaired.

2. **The runs are not independent across mappings.** The evolution driver seeds the generation-0 population from the run seed alone at `wormwars/evo/evolve.py:139`, and the grid's seed ignores the mapping. So the four mappings of one graph and run index start from the same 32 genomes, and their g00 champions are each the best of those 32 under their own fitness, often the same genome. Astra raised this in the options review and the plan does not take it up. Report the count of distinct g00 genomes by stored hash, run the sign tests per mapping, and label any pooled test as over dependent units.

3. **The "otherwise" wording over-reads.** Three g39 switches against none among the drift genomes would fail the rule yet falsify "did not build switches detectable by this probe". Keep the rule, change the sentence to "not shown to build switches more often than drift; N were found".

4. **The persistence comparison's "mean of drift's τ10" is undefined once a replicate is beyond 2000.** Use the fraction of the four drift replicates that g39's τ10 exceeds, with beyond 2000 ranking highest, and the sign test over runs where that fraction is not one half. That is the form comparison 1 already uses.

5. **The loaded genomes' configuration is never checked.** Loading with no configuration gives a genome its stored one at `wormwars/evo/genomes.py:214`, and the brain runs under the genome's own, while the probe's input uses the constructed configuration for its gain and clamp. The spike compared two constructed configurations, not the stored one. Assert that every loaded genome's configuration equals the constructed brain configuration.

Smaller: the second-pass cost is overstated. M4e's second pass averaged about five seconds a genome at `docs/memory/M4E-RESULTS.md:70`; the 75 s figure was the smoke's estimate for unresolved genomes. The budget only gets safer. Key the drift seeds to the run key rather than the line index of the records file, which is committed but is an ordering, not an identity.

## 2. The code change

The draft already in the working tree at `scripts/memory_m1/common.py:125` has the right shape: one module dict read at call time by the input and read-out builders, swapped under try/finally, with a guard that refuses a non-M0 read-out. What it does not yet reach is the food level. The probe, the planted follow-up and M4e's hold still compute it from the spikes module's bank at `scripts/memory_m2/pilot.py:54`, line 408 of the same file, and `scripts/memory_m4/m4e.py:366`. Those must call the new food-level function.

The tests should be:

- **Equivalence to the library's history measure** in `wormwars/exp03/measures.py:92`. That is 02b's test in library form and takes the interface and bank explicitly. Inside the context, with a remapped interface and a bank whose food level differs from 03mc's, the probe's tick-0 and tick-5 read-out differences must match its "final" and "after" to float32 tolerance. The plan's "remapped sensors and nowhere else" test exercises only the input builder and would pass while the probe still used the old food level. This test is the 02b consistency check in miniature and costs nothing.
- **A leakage sabotage.** The oscillation rerun only runs on candidates, and a small random panel has none, so the listed test is vacuous. Test the rerun path directly: the substep hook's recording inside the context equals the first pass's tail recorded inside it, and the same rerun outside the context differs.
- Restoration after an exception, and the guard refusing an interface with another turn read-out.

Two implementation traps. Importing the M4e module for its hold imports M4d and M4a, which create their run folders at import time at `scripts/memory_m4/m4a.py:29`. Copy the two functions, or move them into the pilot module with a bitwise test. And 02b's analysis module picks CUDA when available at `experiments/02b-champion-analysis/analyse.py:49`, so the bank stage must force its device to CPU and assert CUDA was never initialised. Otherwise the GPU hold is broken silently.

## 3. What to cut

Nothing. The whole run is under an hour by M4e's measured rates. The secondary bank's audit is the only item I would drop if asked, and it costs minutes.