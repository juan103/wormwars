**fix first**

Reviewed `roadmap` at `c0f1020` (D289), with no tracked differences in the reviewed files. The main statistical calculations largely match the design. The binding, stop, input-integrity and reporting gaps below prevent binding this version.

1. **Formal graphs can be drawn before binding or pushing.**  
   [scripts/exp03.py:805](D:/Claude/random/wormWars/scripts/exp03.py:805) accepts `build --instance 03mc` and dispatches directly to the builder, without the binding, freshness or cap guards. Its other commands remain available for this instance too. Even through the intended wrapper, [scripts/p4mc.py:150](D:/Claude/random/wormWars/scripts/p4mc.py:150) skips `require_formal` for builds and checks only dirtiness; that omits the pushed-HEAD and environment checks. This contradicts pre-registration §1 and §9.  
   **Fix:** guard the actual formal-build entry point, reject unsupported `exp03` commands for 03mc, and require committed/pushed binding plus the pinned CPU environment before any graph draw.

2. **The pre-run gate does not establish that the registered check passed on the current code and inputs.**  
   [scripts/p4mc.py:310](D:/Claude/random/wormWars/scripts/p4mc.py:310) checks only `prerun-check.json["passed"]`. An in-memory check confirmed that `{"passed": true}` alone suffices. It does not verify the check set, composition, device, code commit, environment, references or start marker. A stale check can therefore survive a `code_commit` amendment. Similarly, `require_build` at line 285 checks only `"outcome": "completed"`. The guarded paths at line 158 omit build records, manifests, pilot inputs and the check record, so those need not even be committed before the initial run.  
   **Fix:** verify stage attestations and input hashes against the binding and current environment; require committed/pushed formal inputs. Bind the check to the applicable code commit and require another check after a relevant amendment.

3. **A smoke check can overwrite a formal file.**  
   [scripts/p4mc_equivalence.py:136](D:/Claude/random/wormWars/scripts/p4mc_equivalence.py:136) joins the smoke directory with unrestricted `--record`. Absolute paths replace the directory; `..` can escape it. The existing-file refusal explicitly excludes smoke mode. I verified path resolution to the formal `prerun-check.json` without writing anything.  
   **Fix:** accept a basename only, enforce the resolved output directory, and refuse overwriting existing records in smoke mode too.

4. **The empty-deletion stop is not persistent. Resume bypasses it.**  
   [scripts/p4mc.py:533](D:/Claude/random/wormWars/scripts/p4mc.py:533) records the failed empty-deletion unit before stopping. On resume, lines 525–527 skip that recorded unit without checking the failure. With I/O and measurements mocked, I reproduced continuation to `qb/0/RIA` and a new `"completed"` attempt after the fatal mismatch. Also, [scripts/p4mc.py:488](D:/Claude/random/wormWars/scripts/p4mc.py:488) compares only plan IDs: changing `seed_name` while retaining an ID passes.  
   **Fix:** persist and enforce a terminal-stop status; revalidate the empty-deletion result before continuation; compare the complete plan, registered settings and smoke/formal identity.

5. **Append-only protection covers the original binding and code amendment, but not necessarily subsequent amendments.**  
   [scripts/p4mc.py:146](D:/Claude/random/wormWars/scripts/p4mc.py:146) checks prefixes from `commit` and `code_commit`. A later text-only amendment can be edited or removed while both prefixes still survive. The last-line fix in D289 works, but does not address this case.  
   **Fix:** maintain an append-only amendment chain, or check each intervening committed version. Require an explicit amendment reference when advancing `code_commit`.

6. **Reporting bypasses the guards and does not verify the recorded array hashes; records can be overwritten.**  
   [scripts/p4mc.py:553](D:/Claude/random/wormWars/scripts/p4mc.py:553) never calls the binding/code/input guards. [scripts/p4mc.py:467](D:/Claude/random/wormWars/scripts/p4mc.py:467) loads arrays without checking `arrays_sha256`; resume also skips completed units without verifying their arrays. Reporting can consequently combine original summaries with changed arrays. `report.json` is overwritten non-atomically. Arrays are replaced unconditionally at line 463, including an orphan left by interruption between array saving and measurement-record saving. There is no exclusive run lock.  
   **Fix:** validate code, inputs and array hashes before resume/report; preserve versioned reports atomically; add exclusive execution and explicit recovery for orphaned unit outputs.

7. **The build’s cap boundary contradicts design v2.2.**  
   [scripts/p4mc.py:258](D:/Claude/random/wormWars/scripts/p4mc.py:258) calls the entire build one unit, citing DESIGN §7. But [DESIGN.md:482](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/DESIGN.md:482) explicitly makes each graph build a unit and claims an overrun under roughly a minute. The child queues every build job at once. The pre-registration’s “before the build and before every unit” does not clearly disclose this change. Build-wrapper auditing and post-build validation also sit outside the child’s accounting.  
   **Fix:** enforce the declared unit boundaries and count the complete stage, or explicitly revise the cap definition and overrun statement before binding.

8. **Several binding definitions need to be explicit.**  
   [PREREGISTRATION.md:147](D:/Claude/random/wormWars/experiments/03mc-p4-confirm/PREREGISTRATION.md:147) gives a general 120-graphs completeness rule without restricting it to ensemble questions. Q-B does not explicitly say whether missing double-deletion units withhold the primary; the code permits that omission. “Valid permutation” is not explicitly defined as P4 validity. The settled-state threshold `1e-4` appears in code/design but is absent from the binding prose’s settling definition. Finally, line 272 requires CUDA for “every formal stage,” although the build is explicitly CPU.  
   **Fix:** state question-specific completeness, validity, settling and stage-environment rules. Also identify the estimates requiring intervals and their resampling units; the broad promise at lines 201–202 leaves this underspecified.

9. **The single-signal calculations discard the detailed records needed to audit their verdicts. Q-E’s registered wording is missing.**  
   [wormwars/exp03/mc_report.py:49](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:49) computes effect intervals, latent SDs, margins and ensemble summaries, then passes them through `R03.single_signal` and returns only its reduced result. Those numerical components are lost. The smoke report confirms their absence. At line 328, Q-E receives the generic overall verdict rather than either registered sentence. The underlying helper can also return `"reversed against every ensemble"`, outside the pre-registration’s stated three outcomes.  
   **Fix:** retain the full per-ensemble records and explicitly implement Q-E’s wording and the treatment of reversal.

10. **The report does not deliver all registered counts, intervals and descriptives.**  
    [wormwars/exp03/mc_report.py:185](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:185) gives Q-A and Q-D point estimates/ranks without their promised intervals or separate planned/measured/valid counts; Q-C likewise lacks the full count breakdown. Missing measurements become indistinguishable from invalid measurements in the rank inputs. The descriptive section at line 246 provides pair-screen response cuts without the corresponding numerator cuts and paired intervals. Null-deletion output discards individual graph cuts. Retention output lacks ensemble eligible/remaining fractions, and the slope comparison reports only hold slopes.  
    **Fix:** implement a field-by-field output checklist from §6–§7, including explicit missingness and numerical components. Test partial and invalid datasets, not only completed synthetic records.

11. **Allowed zero and negative-effect cases are not handled safely.**  
    [wormwars/exp03/mc.py:81](D:/Claude/random/wormWars/wormwars/exp03/mc.py:81) divides by the intact numerator although validity requires only finite terms and valid denominators. I reproduced `ZeroDivisionError` with zero final differences and unit steady contrasts—a valid P4 of zero. Descriptive cuts at [mc_report.py:249](D:/Claude/random/wormWars/wormwars/exp03/mc_report.py:249) similarly divide without validating the intact denominator, and retention curves at line 302 ignore the tick-zero floor. At line 299, the kept-share interval reverses its endpoints when N2’s excess over the null median is negative.  
    **Fix:** make undefined descriptive quantities explicitly unavailable without crashing valid primary calculations; apply the declared floors consistently; compute quantiles after transforming bootstrap samples.

What I verified positively: the registered measurement order and streams, permutation pairing, deletion implementation, Q-A’s signed change, Q-D’s share, Q-C’s batch-0 reference, pooled paired Q-B calculations, control definitions, and four-member Holm are consistent on inspection. The formal seed-name audit returns **2,016 new derived seeds, 4,530 old seeds, no collisions**.

**Validation:** 30 tests across `test_p4mc.py`, `test_exp03_mc.py` and `test_p4mc_equivalence.py` passed with filesystem-writing pytest features disabled. All **58/58** smoke array hashes match. The smoke equivalence record itself says **`passed: false`**, which smoke mode deliberately bypasses; it is not evidence of a successful formal gate. I inspected but did not execute the twin dynamics tests, ran no GPU work, drew no graphs or genomes, and did not verify remote push history or the historical sabotage-test sequence.