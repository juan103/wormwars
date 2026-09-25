1. Against my original 11 points, at `b10a63f`:

| Point | Status | Evidence |
|---|---|---|
| 1. Exclusions/completeness | **PARTLY** | [report.py:126](D:/Claude/random/wormWars/wormwars/exp03/report.py:126) correctly filters and withholds, but an empty valid P3 reference set crashes before withholding at line 115. Reproduced. |
| 2. Ensemble-only margins | **FIXED** | [report.py:114](D:/Claude/random/wormWars/wormwars/exp03/report.py:114) excludes N2/variants/unregistered graphs; variance truncation is registered. |
| 3. Exchangeability claim | **PARTLY** | [PREREGISTRATION.md:42](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:42) appropriately qualifies exactness; line 91 still incorrectly says measurement symmetry *makes* graphs exchangeable. Delete that sentence. |
| 4. Power simulation | **PARTLY** | [exp03.py:427](D:/Claude/random/wormWars/scripts/exp03.py:427) fixes shared N2 and observed effects. But `z=0` fixes N2’s latent value at the ensemble mean; it does **not** simulate a randomly drawn member. The new “consistent if member” column is mislabeled. |
| 5. Negative P3 interpretation | **FIXED** | [PREREGISTRATION.md:228](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:228) removes the invalid upper-bound claim. |
| 6. Resume/provenance | **PARTLY** | [exp03.py:498](D:/Claude/random/wormWars/scripts/exp03.py:498) still skips existing files without verification. `check_provenance` at line 83 checks mutual agreement, not agreement with the binding/current code and inputs, and ignores device. Successful saved durations accumulate; failed attempts do not. Order and graph-hash checks are fixed. |
| 7. Validation/reporting | **PARTLY** | [exp03.py:211](D:/Claude/random/wormWars/scripts/exp03.py:211) implements independent calibration validation. [report.py:85](D:/Claude/random/wormWars/wormwars/exp03/report.py:85) adds secondary values, but promised secondary SEs/ranks and ensemble response-condition summaries remain absent. |
| 8. Magnitude pairing | **FIXED** | [PREREGISTRATION.md:114](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:114) explicitly registers unpaired draws. |
| 9. Hop constraint | **FIXED** | [PREREGISTRATION.md:71](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:71) explicitly retires it. |
| 10. Directional error budgets | **FIXED** | [PREREGISTRATION.md:171](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:171) states separate budgets and combined 10%. |
| 11. Run-value justification | **PARTLY** | [PREREGISTRATION.md:232](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:232) corrects the reliability estimate; the remaining implementation/reporting gaps still prevent launch approval. |

2. Additional launch-relevant problems:

- **Report command crashes:** [exp03.py:521](D:/Claude/random/wormWars/scripts/exp03.py:521) references undefined `complete`. Reproduced; it writes the JSON first.
- **Registered calibration-failure handling is absent:** [exp03.py:206](D:/Claude/random/wormWars/scripts/exp03.py:206) lets nonconvergence abort the run, instead of saving/counting an exclusion. Restart retries the same graph indefinitely.
- The empty-profile crash and erroneous member simulation are described above.

Twelve report/verdict tests passed; all 640 graph hashes and five committed input hashes match. Runner tests were limited by the read-only environment.

3. **NO-GO for `python scripts/exp03.py run --max-hours 24` now.** Minimum: fix both report crashes; persist calibration failures as counted exclusions; validate existing measurements before resuming and bind reporting to their registered provenance; implement or explicitly defer the missing secondary outputs; correct the member-simulation claim and residual exchangeability sentence. Add focused regression checks, then commit before starting.