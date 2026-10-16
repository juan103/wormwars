**fix first**

1. **Draft-2 finding 1 is only partly fixed: measurement inputs are still not pinned to binding.**  
   [scripts/p4mc.py:167](D:/Claude/random/wormWars/scripts/p4mc.py:167) includes the stimulus bank and remaps in cleanliness checks, but [line 196](D:/Claude/random/wormWars/scripts/p4mc.py:196) compares only `CODE` against the bound commit. A committed change to either input between binding and checking is therefore admitted without an amendment. I reproduced this with an in-memory guard test. The new check-to-run digest, both environment comparisons, and repeat-record dirty rejection work correctly.  
   **Fix:** separately compare `MEASUREMENT_INPUTS` against the binding commit, with an explicit amendment mechanism for changes. Test a *committed* input change, not just a dirty file or check-to-run mismatch.

2. **Draft-2 finding 4 is improved, but the new reporting promise remains broader than the implementation.**  
   [PREREGISTRATION.md:170](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/PREREGISTRATION.md:170) promises available estimates and intervals for withheld questions. At [mc_report.py:142](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:142), any missing Q-B batch suppresses that deletion’s entire pooled estimate. Removing `qb/1/AIY` from the saved smoke record produces only `complete: false` and counts, despite a complete first batch being available. Counts also describe deletion units without separately reporting intact-reference availability.  
   **Fix:** report explicitly labelled descriptive estimates from available paired batches, keeping the confirmatory question withheld; alternatively, narrow the text before freezing to explain this deliberate omission. Include intact and paired-batch counts. The invalid-N2 ensemble counts and incomplete-Q-C response/interval fixes are correct.

3. **Draft-2 finding 2 is fixed.**  
   [scripts/p4mc.py:740](D:/Claude/random/wormWars/scripts/p4mc.py:740) validates binding, settings, plan, inputs, attempt code/cleanliness and every completed array before statistics. The saved smoke passes validation. In-memory checks confirmed foreign bindings and dirty attempts are rejected, while terminal-stopped records remain reportable. **No further fix required for that finding.**

4. **Draft-2 finding 3 is fixed.**  
   [mc_report.py:413](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:413) now bootstraps the median and names the interval `median_cut_95`. The skewed-data regression and controls-path tests pass. **No further fix required.**

5. **Draft-2 finding 5 is fixed.**  
   [scripts/p4mc.py:725](D:/Claude/random/wormWars/scripts/p4mc.py:725) reserves report destinations exclusively and retries collisions. **No further fix required.** Fable’s reference preflight, Q-A resample floor and README changes are also present.

Verification: **37 selected CPU tests passed**; eight filesystem-writing tests were excluded. All **63/63** smoke array hashes match; both reports agree apart from metadata; both control paths completed. Recorded stage and resume provenance is clean `e136fe3`. All four local reference hashes match their pins.

The CPU smoke equivalence record still says `passed: false`; it does **not** establish that the formal CUDA gate passes. I ran no GPU work and drew no graphs or genomes. I did not verify remote push history or the historical sabotage sequence.