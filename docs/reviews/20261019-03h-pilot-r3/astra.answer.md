**bind and run.**

Checked `ff1fd31` on `roadmap` against both round-2 reviews. No files changed; no tests or experiment code executed. Numbering follows Astra’s round-2 findings.

1. **Cap — fixed.** `over_at_end()` reads the aggregate after accounting finishes, counting the attempt once ([e03h.py:151](D:/Claude/random/wormWars/scripts/e03h.py:151)).

2. **Stage dependencies — remain correct.** Upstream hashes and the G2/S1 rate comparison remain enforced. Eligibility and cap checks now precede record relocation, also resolving Fable’s refused-rerun finding.

3. **Sizing — fixed.** S1 separates sampler and calibration timing; the projection excludes sampler seconds while retaining calibration and history costs. This now agrees with DESIGN §8 ([e03h.py:490](D:/Claude/random/wormWars/scripts/e03h.py:490)).

4. **Smoke contamination — remains fixed.** Banks remain separate. All five existing CUDA smoke records identify `ff1fd31` and completed status.

5. **Calibration replacement/reporting — fixed.** Failures enter `progress` immediately and survive handled interruptions or excessive-failure termination. Draft 4 explicitly registers the stop after more than ten failures ([e03h.py:265](D:/Claude/random/wormWars/scripts/e03h.py:265)).

6. **Gate families — remain correct.** The refactor preserves tuning, fallbacks and tie handling.

7. **Escalation — fixed.** A qualifying P must match the current upstream hashes. Failed P′ retries remain allowed; a completed P′ blocks another ([e03h.py:353](D:/Claude/random/wormWars/scripts/e03h.py:353)).

8. **Edges and binding — fixed.** Flags travel with each tuning result, use registered bounds and exclude fixed parameters/switches/T=1. Non-smoke stages enforce the recorded commit over `CODE` before relocation ([gate.py:88](D:/Claude/random/wormWars/wormwars/e03h/gate.py:88), [e03h.py:521](D:/Claude/random/wormWars/scripts/e03h.py:521)).

9. **Calibration identities — remain correct.** No relevant change.

10. **Test gaps — addressed by inspection.** Added coverage includes failed-P′ retry, stale-chain refusal, completion accounting, heterogeneous B uncertainty and the direct-World count oracle.

11. **`rollout_brain` counts — remain correct, now covered by that oracle.**

I found no new regression affecting G1, S1, G2, P or formal sizing. **PILOT.md draft 4 is ready to bind as it stands.**