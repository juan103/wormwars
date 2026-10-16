**fix first**

Reviewed `roadmap` at `8b77b57` against `c0f1020`. Most fixes are present, including the persistent empty-deletion stop, full-plan resume comparison, amendment-chain check, computed Q-A wording, retained single-signal records, and zero-numerator handling. The original input-attestation and reporting findings remain partly unresolved.

1. **The check is still not tied to the run’s inputs and environment.**  
   [scripts/p4mc.py:163](D:/Claude/random/wormWars/scripts/p4mc.py:163), [scripts/p4mc.py:399](D:/Claude/random/wormWars/scripts/p4mc.py:399), [scripts/p4mc.py:587](D:/Claude/random/wormWars/scripts/p4mc.py:587).  
   `guarded()` still omits `experiments/03-generation0/pilot.json` and `experiments/02-screening/remaps.json`, although `setup()` reads them. Their hashes protect subsequent resumes, but nothing compares the first run’s inputs with those used by the successful check. `require_check()` also ignores environment compatibility and the repeat record’s dirty flag. An in-memory test accepted deliberately wrong environment metadata and `prerun-repeat.json` provenance with `dirty: true`.  
   **Fix:** pin the measurement inputs to the binding, include them in cleanliness checks, record their hashes during the check, and compare them before running. Validate both check records’ environment and clean-code provenance.

2. **Reporting does not fully validate the measurements it reports.**  
   [scripts/p4mc.py:710](D:/Claude/random/wormWars/scripts/p4mc.py:710).  
   The new guards validate the current checkout, but `cmd_report()` does not validate the measurement document’s binding, settings, full plan, input digest or originating code. It also checks array hashes only when a statistic loads an array. Instrumenting the report on the smoke records showed **25 completed units whose arrays were never checked**, including permutations, factorial units, null deletions and the empty deletion. This falls short of §9’s explicit “each unit’s arrays” promise.  
   **Fix:** validate the measurement document against its recorded provenance and expected inputs, and verify every completed unit’s array hash before calculating statistics. Keep terminal-stopped runs reportable; do not simply reuse the resume refusal wholesale.

3. **The null-deletion interval estimates the wrong statistic.**  
   [wormwars/exp03/mc_report.py:401](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:401), [wormwars/exp03/mc_report.py:231](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:231).  
   Pre-registration §7 promises each ensemble’s **median with an interval**. The report supplies `median_cut` alongside `mean_cut_95`, bootstrapped from means. With 32 synthetic cuts—31 zeros and one one—the current interval is `[0, 0.09375]`; the registered median-bootstrap interval is `[0, 0]`.  
   **Fix:** bootstrap the median over graphs and name the field `median_cut_95`. Add a skewed-data regression test.

4. **Registered reporting remains incomplete for withheld and invalid cases.**  
   [wormwars/exp03/mc_report.py:32](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:32), [wormwars/exp03/mc_report.py:129](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:129), [wormwars/exp03/mc_report.py:301](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:301).  
   An invalid N2 makes `single_signal()` return before producing ensemble counts. Q-B lacks a consistent planned/measured/valid count breakdown. Q-C suppresses the valid N2 response and its interval whenever too few permutations are valid; I reproduced the missing fields with an incomplete record. §§6–7 promise these reporting components independently of confirmation.  
   **Fix:** compute counts before completeness checks, and report available estimates and intervals even when the verdict is withheld. Test invalid N2, invalid bootstrap and incomplete-permutation cases explicitly.

5. **“Never overwrites a report” is not guaranteed.**  
   [scripts/p4mc.py:726](D:/Claude/random/wormWars/scripts/p4mc.py:726).  
   Once `report.json` exists, the fallback uses a seconds-resolution timestamp without checking that destination. `write_json(..., atomic=True)` ultimately replaces existing files. With time and writes mocked, two calls selected the same already-existing destination.  
   **Fix:** reserve a unique output path exclusively; atomic replacement alone does not prevent overwriting.

**Verification:** 44 selected tests passed with filesystem-writing pytest features disabled; 13 writing tests were excluded. All **58/58** smoke array hashes match. Both smoke reports agree apart from timestamp/provenance. The repeat smoke check passed, but the smoke equivalence record says **`passed: false`**; it does not validate the formal gate. I ran no GPU work, drew no graphs or genomes, and did not verify remote push history or the historical sabotage sequence.