**Revise.** The variants can provide a useful feasibility signal, but fix the decision rule and diagnostic records before running. I checked `1877a05` and its parent diff; I made no changes and executed no research code or tests.

1. **High — outcome (ii) can make a false statement.**  
   [scripts/e03a.py:1241](/D:/Claude/random/wormWars/scripts/e03a.py:1241), [PILOT-DEV.md:385](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:385).

   Suppose V1 restores reliably without enrichment, while V2 enriches but has unreliable refits. The code returns (ii), saying “none recovers partners.” That is false, and the written rule leaves this combination unassigned. The test at [test_e03a_script.py:253](/D:/Claude/random/wormWars/tests/test_e03a_script.py:253) explicitly enshrines this mismatch.

   Keep three outcomes by defining (ii) as **“some variant passes reliability, but no single variant passes both criteria.”** Record any recovery in unreliable variants separately. Restrict the interpretation accordingly.

2. **Medium — the restoration gate is nonmonotonic: better restoration can fail it.**  
   [scripts/e03a.py:1233](/D:/Claude/random/wormWars/scripts/e03a.py:1233), [stats.py:180](/D:/Claude/random/wormWars/wormwars/e03a/stats.py:180).

   With the actual margin \(p≈0.0983\), a difference interval `[0.08, 0.12]` is classified “undetermined”: it crosses **+p**, although every value indicates improvement over restoration. The gate rejects it.

   For this check, use **the restoration difference’s lower confidence bound ≥ −p**, alongside the SD criterion. Preserve the existing four-way comparison as descriptive output. This makes the gate reflect adequate restoration without rejecting improvements.

3. **High for interpretation — three refits provide a fragile reliability screen.**  
   [scripts/e03a.py:120](/D:/Claude/random/wormWars/scripts/e03a.py:120), [scripts/e03a.py:1312](/D:/Claude/random/wormWars/scripts/e03a.py:1312), [PILOT-DEV.md:374](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:374).

   The sample SD has only two degrees of freedom. The restoration interval bootstraps worlds **after averaging the refits**, so it excludes uncertainty from drawing new search initializations. Selecting a passing variant among four further favors lucky refit samples.

   **My numerical change would be five refits per variant**, keeping five free searches and SD ≤ p/2. Under the current rate model, that adds approximately **0.20 hours**, taking the projection to roughly **1.19 hours**. Five still supports a provisional screen, not a demonstrated population reliability bound. Report individual refit restoration differences.

   Keep enrichment **p < 0.0125**. Bonferroni over four aggregate tests is reasonable; sharing the permutation bank does not invalidate it. That correction protects the enrichment family, not the reliability claim.

4. **Medium — the re-evaluation reports the wrong denominator for one promised metric.**  
   [scripts/e03a.py:1218](/D:/Claude/random/wormWars/scripts/e03a.py:1218), [PILOT-DEV.md:347](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:347).

   `mean(acc & (tg < 0))` measures the fraction of **all proposals** that are accepted and estimated worse. “The share accepted that are truly worse” means the fraction **among accepted proposals**.

   Report both, with explicit names; the conditional quantity is `mean(tg[acc] < 0)`, or `None` when nothing is accepted. Also make `winner_is_true_best` tie-aware: comparing with the first `argmax` incorrectly marks other tied best offspring as failures.

5. **Medium — “truth” is an estimate, and the check discards evidence needed to assess it.**  
   [scripts/e03a.py:1203](/D:/Claude/random/wormWars/scripts/e03a.py:1203), [scripts/e03a.py:1315](/D:/Claude/random/wormWars/scripts/e03a.py:1315).

   One common 1,024-world block is a sensible reference, but it does not establish exact gain signs or the true best offspring. Near-zero gains can change sign through evaluation noise. The median SE across all offspring does not quantify uncertainty for the selected winners.

   Save the re-evaluation’s per-world reference scores, selection scores, world IDs and mutation kinds, plus each variant’s final per-world counts and aggregate ranking. `full` already retains final counts; this stage does not. These records permit uncertainty checks without another GPU run. Label the quantities **reference-estimated gain/best**, and retain paired uncertainty for selected gains. I would keep 1,024 worlds rather than increase this diagnostic’s cost.

6. **Medium — lesions and omitted random refits limit the reading of failure.**  
   [PILOT-DEV.md:340](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:340), [PILOT-DEV.md:386](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:386), [scripts/e03a.py:1153](/D:/Claude/random/wormWars/scripts/e03a.py:1153).

   Single-edge lesions measure marginal sensitivity **at the evolved restoration**. They do not measure the benefit of discovering those partners in arbitrary search states, and their effects need not add. Sorting and clipping noisy drops also biases apparent positive concentration.

   Omitting random-partner refits is acceptable for the narrow feasibility question. It means the old true-versus-random advantage cannot be assumed to persist under the new optimizer.

   Consequently, (ii) supports **“recovery was not demonstrated under this bounded check,”** not “cannot find them here” or “identity is unidentifiable.” Outcome (iii) supports a budget-based stop because no tested variant passed the screen; it does not establish that every feasible search would fail. I still favor stopping after either negative outcome.

7. **Low — retain the four variants and temperature 0.01; interpret them as candidate procedures.**  
   [scripts/e03a.py:111](/D:/Claude/random/wormWars/scripts/e03a.py:111), [PILOT-DEV.md:355](/D:/Claude/random/wormWars/experiments/03a-self-consistency/PILOT-DEV.md:355).

   None is obviously wasted. V1 tests the precision–offspring tradeoff; V2 tests temperature; V3 and V4 test affordable alternative procedures. V3/V4 change several factors together, so success will not isolate its cause.

   Temperature 0.01 is defensible but is not greedy: at 64 worlds, a one-count aggregate disadvantage is accepted with probability `exp(−1/64/0.01) ≈ 0.21`. Likewise, V4’s “confirmation” is a fresh Metropolis comparison, not a statistical guarantee of improvement.

8. **Medium for budget risk; episode arithmetic correct.**  
   [scripts/e03a.py:1259](/D:/Claude/random/wormWars/scripts/e03a.py:1259).

   The current projection correctly counts:

   | Component | Episodes |
   |---|---:|
   | Searches, including confirmation | 1,664,000 |
   | Fixed-state re-evaluation | 327,168 |
   | Lesions and final evaluations | 159,744 |
   | **Total** | **2,150,912** |

   V4 correctly costs `9×32 + 2×64 = 416` per search-generation. However, taking the slower historical rate is not a conservative bound for new batch compositions. V4 adds 100 confirmation calls with only `16 strains × 64 worlds`. Preserve the cap and timing records, and describe the hour estimate as an extrapolation.

9. **Informational — the specifically requested execution paths look correct by inspection.**  
   [search.py:255](/D:/Claude/random/wormWars/wormwars/e03a/search.py:255), [search.py:337](/D:/Claude/random/wormWars/wormwars/e03a/search.py:337), [scripts/e03a.py:1127](/D:/Claude/random/wormWars/scripts/e03a.py:1127).

   The `tell` split preserves the original operations and random-draw order. V4’s first `tell` selects candidates without advancing; its second performs acceptance, swaps and advancement. Its homogeneous `run_lockstep` batch therefore completes both phases correctly. The `after` callback now runs after each phase, despite its “generation” documentation; this stage supplies no callback.

   Re-evaluation uses independently keyed selection draws and a disjoint common reference block. Confirmation uses its own RNG stream, although draws can overlap selection IDs because they share a finite pool. Lesions remove both chemical and gap edges correctly: zeroing a gap conductance removes both directions and updates both neurons’ gap denominators when the brain is rebuilt.