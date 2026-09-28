**Revise before binding.** I checked `roadmap` HEAD `a6437be` against `f83bd19` and the archived reviews. **38 tests passed**; I excluded the two tests that write files. I also ran memory-only failure reproductions and compared the existing CPU oracle fixture against the previous engine: scores, energy and all pre-existing event arrays matched exactly. No files changed or registered worlds were evaluated.

The following original points are resolved correctly:

- **Cue inference:** `gate_rules` now bootstraps `0.5 × real − mirrored`. The counterexample regression test is appropriate.
- **Leg endpoints and secondary measures:** `_ev_start`/`_ev_end` record the actual head positions; subsequent starts equal preceding endpoints. `secondary` includes the first leg, uses displacement/path, and labels finished-leg statistics correctly. I found no new defect here.
- **Successful-run reporting:** full event arrays are retained, and every tuned controller—including the unselected navigator and small-gain variant—gets real and constant-probe arms.
- **LF handling:** writing LF and hashing normalized bytes fixes the Windows issue.
- **Stage markers:** exclusive creation occurs before world evaluation and survives interruption. The declared restart policy is clear.
- **Binding/code guards:** the registration is included in the guarded paths; fetched remote ancestry checks that HEAD was pushed; the gate compares guarded code/configuration files with the pilot commit.
- **Smoke isolation:** `use_smoke` redirects IDs, paths and marker deletions before use. I found no route from the normal smoke CLI into formal worlds or outputs.

The remaining must-fixes are:

1. **Cap enforcement still does not implement §5.**  
   [scripts/e1.py:372](D:/Claude/random/wormWars/scripts/e1.py:372) runs generation 0 and throughput without intervening cap checks; [throughput:283](D:/Claude/random/wormWars/scripts/e1.py:283) contains unchecked warm-up and measured rollouts. Thus more than one rollout can run after the budget expires.

   The gate’s final check at [e1.py:534](D:/Claude/random/wormWars/scripts/e1.py:534) precedes bootstrap analysis, secondary calculations and serialization. With a mocked clock crossing eight hours during `gate_rules`, the actual `cmd_gate` control flow wrote **“E1 positive control: passed” with `seconds=28801`**.

   Check before every rollout and make the final budget decision after analysis. Align the timing boundary with the accounting definition, explicitly stating any excluded output overhead.

2. **The `CapReached` path discards completed observations.**  
   [e1.py:535](D:/Claude/random/wormWars/scripts/e1.py:535) saves only status and completed-arm names. Counts and events already collected are lost. My simulated cap after two completed arms produced neither retained counts nor an event archive.

   Preserve completed-arm counts, events, IDs and elapsed time when reporting “not completed.” This remains an unresolved part of the original event-retention requirement and contradicts [PREREGISTRATION.md:180](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:180).

3. **`validate_freeze` does not validate the coverage experiment it re-derives σ from.**  
   [e1.py:406](D:/Claude/random/wormWars/scripts/e1.py:406) feeds arbitrary coverage rows directly into `choose_sigma`. I verified that it accepts:

   - a single coverage row with **σ=5**, with the freeze selecting 5;
   - an empty coverage table, selecting the flagged fallback;
   - missing candidates and an out-of-range share.

   Matching `registered` does not prevent these. Require exactly the registered candidates, valid finite shares and the prescribed observation counts before deriving σ. Validate finite tuning scores and the own-body measurement’s required evidence too. The existing tests cover altered selections, but miss malformed supporting measurements.

4. **Environment and input provenance remain incomplete.**  
   [e1.py:115](D:/Claude/random/wormWars/scripts/e1.py:115) records Torch, CUDA and GPU, but still omits the requested resolved configuration and connectome source/cache hashes. Python and NumPy versions are also absent. The cache is outside `GUARDED`, and [require_same_code_as_pilot:427](D:/Claude/random/wormWars/scripts/e1.py:427) cannot detect a changed cache or runtime environment. `requirements.txt` is outside that comparison too.

   Record and compare the relevant input identities, protect the dependency specification, and retain the resolved configuration. CUDA refusal fixes the old CPU fallback, but accepting any available CUDA installation does not enforce §2’s RTX 5080/pinned-environment restriction.

5. **The guard-test claim is false, and important failure paths remain untested.**  
   [DECISIONS.md:2896](D:/Claude/random/wormWars/DECISIONS.md:2896) says each guard has a test. There is no test of `require_same_code_as_pilot`, dirty/unpushed refusal, or `cmd_gate`’s cap path. [test_e1_script.py:144](D:/Claude/random/wormWars/tests/test_e1_script.py:144) checks an already-exceeded historical budget; it does not test crossing the boundary during work.

   Add refusal and boundary tests covering those paths, interrupted-stage re-entry, malformed coverage, and actual `use_smoke` path/ID rebinding. Include an accepted freeze/output-only commit case for the code comparison. These tests should first expose the relevant failures, as the repository requires.

6. **§7 introduces an incorrect deterministic claim about σ.**  
   [PREREGISTRATION.md:242](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:242) says geometry forces σ=6 and the pilot decides only the flag. That does not follow. Excluding σ≤3 does not exclude σ=4; geometrically valid sequences can have separations between 8 and approximately 9.8 throughout. Expected coverage around 0.29 makes σ=4 qualifying unlikely, not impossible.

   Describe σ=6 as strongly expected and preserve the actual selection rule. Correct the same assertion at [DECISIONS.md:2886](D:/Claude/random/wormWars/DECISIONS.md:2886).

   Also correct [§7:249](D:/Claude/random/wormWars/experiments/E1-navigation/PREREGISTRATION.md:249): a flag establishes coverage below 90%, not necessarily “about an eighth” below the floor. The 5% reporting floor is not a controller cutoff, so “must search before it can steer” is unsupported.

On the disclosure itself: **the material exposure categories are now described**, including the early smoke pilot and unaccounted debug calculation. The first failed smoke gate’s local accounting record confirms zero worlds built. The early pilot’s exact IDs and debug chronology were not recorded, so those remain development-history statements, not independently verified facts.

**Starting at index 1,000 is an adequate remedy for the disclosed world reuse**, provided that offset was selected without evaluating alternatives. It skips the exposed prefixes, preserves the sampling procedure and does not change thresholds in response to performance. It does not erase the earlier exposure; retaining the disclosure is essential. Keep the σ rule unchanged.

One non-blocking cleanup: `use_smoke` leaves an old `gate_events.npz` behind when clearing other outputs. Remove that stale smoke artifact too, so a failed subsequent smoke run cannot leave a misleading archive.

E1 pre-registration: revise — must fix cap enforcement, incomplete-run evidence retention, coverage validation, input/environment provenance, guard tests, and §7’s σ claims.