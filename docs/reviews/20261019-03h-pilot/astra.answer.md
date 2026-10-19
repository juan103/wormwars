**revise.** I checked the files at `4fae0d1e85ff767cd1b03e51d96a02e4e77e2f3b` on `roadmap`. I did not edit files or execute tests or experiment code. The main statistical readings follow v3.3, but the budget controls, stage dependencies, and seed isolation need fixing before binding.

1. **High — G1 and G2 do not enforce the one-hour cap.**  
   [scripts/e03h.py:206](D:/Claude/random/wormWars/scripts/e03h.py:206) and [scripts/e03h.py:291](D:/Claude/random/wormWars/scripts/e03h.py:291) receive `ck` but never call `ck.check()`; neither does `_gate`. They can run even when previous attempts have already exhausted the allowance. P also has no final check after its last probe and bootstrap.

   Add checks before stages and between bounded units of gate work, with an explicit overrun convention. Accounting alone does not enforce a cap. Step 0b **is** included: it writes into the same step-0 compute directory that `Clock.spent_hours()` reads.

2. **High — upstream reruns can leave a stale gate authorizing P.**  
   At [scripts/e03h.py:305](D:/Claude/random/wormWars/scripts/e03h.py:305), P accepts any completed, passing G2, then independently reads the latest S1 and uses its rates. If S1 is rerun, an existing G2 can therefore authorize a sham with different rates from those it tested. G2 records its rates, but P never compares them.

   Bind each stage to its predecessor’s content hash, or invalidate downstream records when an upstream stage changes. Checking only `status` and `passed` is insufficient.

3. **High — the projection and its stop do not implement the complete sizing rule.**  
   [_projection, scripts/e03h.py:396](D:/Claude/random/wormWars/scripts/e03h.py:396) always projects 65 graphs with \(W_t=64\). It never evaluates the design’s permitted reduction to \(W_t=32\), nor produces the optional-SH inclusion decision. DESIGN §8 explicitly says to cut SH first, then reduce \(W_t\), while preserving 64 primary null graphs and the chosen W.

   There is also a direct PILOT mismatch at [scripts/e03h.py:384](D:/Claude/random/wormWars/scripts/e03h.py:384): an over-budget projection stops only when the decile shift moves. Otherwise the action requests P′ despite the failed budget criterion.

   Specify and implement the complete decision table before binding: primary at 64 test worlds, primary at 32 if necessary, optional SH, and the precedence of budget failure over amplitude escalation. The present projection’s separate selection/test timing estimates are reasonable extrapolations; the decision logic is the problem.

4. **High — the proposed banks have already been used by the smoke preflight.**  
   [scripts/e03h.py:70](D:/Claude/random/wormWars/scripts/e03h.py:70) gives smoke runs the same gate IDs and run seeds, and the same selection/test starting IDs and run seeds, as the registered configuration. The existing CUDA smoke records confirm those runs occurred.

   In particular, the six smoke gate-check worlds are actual members of the proposed 256-world check bank. The smoke pilot uses different graph construction settings, so it is not the full pilot, but its worlds are still reused.

   Reserve fresh registered banks before binding and keep smoke banks separate. Disclose the existing overlap; do not describe these banks as previously untouched.

5. **Medium — S1 does not implement calibration-failure replacement.**  
   PILOT §3 requires a failed calibration to take the next graph seed. At [scripts/e03h.py:255](D:/Claude/random/wormWars/scripts/e03h.py:255), the driver first constructs three graphs, then calibrates them without catching calibration failure. `calibrate_in_world` raises on nonconvergence, so S1 aborts instead of recording the exclusion and drawing a replacement.

   P’s reconstruction at line 324 also assumes that `_graphs()` alone reproduces S1’s accepted set. Once calibration replacement is implemented, P must rebuild the **recorded accepted seeds**, not independently select the first three sampler successes.

6. **Gate nesting is substantially correct; the cost statement needs qualification.**  
   [wormwars/e03h/gate.py:53](D:/Claude/random/wormWars/wormwars/e03h/gate.py:53) implements the registered local searches and fallbacks. T=1 preserves M; the source flags preserve memory without the bit; the memoryless+bit fallback covers the case where K or Graded wins the memory union. I do **not** find a general nesting failure.

   However, “at the memory optimum’s parameters” is inaccurate when that optimum is K or Graded: line 69 uses `mp`. The fallback preserves nesting, and G1’s level criterion would fail in that case, but the registration should define this branch explicitly.

   The episode arithmetic is:

   - G1 tuning: **95,552–145,472** episodes, depending on grid-neighbour counts.
   - G2 tuning: **84,736–97,216**, because K and Graded are tuned again.
   - Combined tuning: **180,288–242,688**, plus check episodes.

   Thus “about 150,000” is a reasonable upper approximation for **G1**, not the whole gate. The restricted slow-memory search is legitimate if its conclusion remains limited to these registered candidates; it does not establish equivalence against fully retuned slow-memory policies.

7. **The central amplitude, B, and power calculations are correct, with some registration omissions.**  
   [wormwars/e03h/pilot.py:60](D:/Claude/random/wormWars/wormwars/e03h/pilot.py:60) correctly computes condition-specific selected-decile means, \(U=T_{\text{sham}}-T_{\text{relief}}\), its between-graph SD, and shared-test-world bootstrap uncertainty. The manipulation passes only when the shift’s lower 95% bound exceeds zero. The turn response does not control escalation. This matches §13.

   The power formula also matches PILOT, retains step 0’s observed SD floor when its file is present, and does not stop the experiment. It is the specified normal approximation for **A2**, not power for B’s rank test or for establishing a lower bound above δ. Three pilot graphs do not establish B’s power.

   Fix two details:

   - B’s bootstrap actually uses **3,623,001**, at [scripts/e03h.py:374](D:/Claude/random/wormWars/scripts/e03h.py:374); PILOT lists only 3,623,000. Register both streams and explicitly state the manipulation bootstrap count.
   - P′ eligibility relies on the lexicographically last archived attempt, rather than a completed qualifying P. A failed P′ attempt can consequently prevent a legitimate retry. Define retries separately from the single permitted amplitude escalation.

8. **Medium — required reporting and binding checks are missing.**  
   [gate.py:76](D:/Claude/random/wormWars/wormwars/e03h/gate.py:76) emits no grid-edge flags, although PILOT §2 requires them. [scripts/e03h.py:360](D:/Claude/random/wormWars/scripts/e03h.py:360) emits no top-versus-bottom H-quartile fitness difference, required by PILOT §5.2.

   At [scripts/e03h.py:418](D:/Claude/random/wormWars/scripts/e03h.py:418), the driver checks a clean guarded tree and PILOT’s hash, but does not enforce push-before-run. The binding record itself is outside `GUARDED`; its recorded DESIGN hash is never checked, and committed code changes between stages are accepted. These are enforcement gaps, even if the operator follows the intended manual procedure.

9. **Medium — the seed specification needs a precise definition of disjointness.**  
   The explicit registered gate, selection, and test ranges are mutually separate. But calibration supplies no world IDs: [wormwars/calibration.py:201](D:/Claude/random/wormWars/wormwars/calibration.py:201) therefore gets IDs **0–1023** from `World`. These are neither listed nor numerically disjoint from earlier calibration IDs.

   Different run seeds mean this is **not evidence of repeated worlds**. Register calibration’s IDs and distinguish disjoint numeric IDs from distinct `(run_seed, world_id)` identities. A different genome salt defines a reproducible new stream; it does not itself prove literal seed-number disjointness.

10. **The tests miss the consequential failure paths.**  
    The following need targeted coverage before relying on the driver:

    - exhausted-cap refusal in G1/G2 and cap handling at stage completion;
    - stale G2 after S1 changes;
    - calibration failure, replacement, and reconstruction from accepted seeds;
    - projection cases requiring \(W_t=32\), optional-SH exclusion, and simultaneous manipulation/budget failure;
    - deterministic tests of both amplitude branches and failed-P′ retries;
    - heterogeneous world effects testing shared-bootstrap pairing and nonzero uncertainty;
    - required edge flags, quartile readings, and smoke/registered range separation.

    The amplitude test at [tests/test_e03h_pilot_driver.py:73](D:/Claude/random/wormWars/tests/test_e03h_pilot_driver.py:73) conditionally exercises refusal only if the smoke outcome happens to move. The B test uses an identical constant relief shift everywhere, so it cannot detect incorrect bootstrap pairing. The rollout-count test compares chunkings but, despite its docstring, does not independently compare the aggregate with a manually accumulated world-count oracle.

11. **The new `rollout` output does not change earlier experiments’ simulated results by inspection.**  
    The commit adds an optional trailing dataclass field, reads already-computed counts after simulation, and sums them across chunks. With `food_fell=None`, the field remains `None`; the existing score calculations and random draws are unchanged. This is a static conclusion, not a newly executed equivalence check.

    There is one API inconsistency: [wormwars/evo/rollout.py:136](D:/Claude/random/wormWars/wormwars/evo/rollout.py:136) does not forward the counts through `rollout_brain`, so scripted rollouts return `None` even with the channel enabled. That does not alter G1/G2 scores, but it prevents obtaining their counts through that result object.