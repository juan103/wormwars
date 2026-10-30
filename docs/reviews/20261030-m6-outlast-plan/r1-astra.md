**Verdict: agree with fixes.** Keep the 169-genome A–B–C check and both removal arms. The main problems are the interpretation, several plan/code mismatches, and incomplete test coverage—not the basic experiment.

I checked the source and census JSON. The counts are correct: 28 M2 switches plus 141 M4c switches, including four read-out-silent genomes. Both plan copies are identical. I read the existing test and sabotage logs; I did not rerun simulations or the mutation harness.

The classifier reuse looks correct. In [`phase_from`](/D:/Claude/random/wormWars/scripts/memory_m6/outlast.py:123), both `follow_from` and `full_classify` execute inside the changed-input context. Root finding, stability and continuation use `run["cur"]`; the oscillation rerun uses the supplied `initial`, so it does not replay the original ramp. C starts from B’s actual tick-2000 state, not its Newton root or its classifier continuation endpoint. Those are the right choices.

One inherited qualification: [`full_classify`](/D:/Claude/random/wormWars/scripts/memory_m2/pilot.py:365) calculates `a` from each phase’s starting read-out difference. Consequently, “read-out silent” in B/C is relative to that phase’s start, not the original ramp. This does not affect held/recovered counts because both switch subclasses count, but it needs stating beside the subclass counts.

Required fixes:

1. **Separate persistence during removal from recovery after restoration.** The proposed headline uses recovery alone to answer both questions. That is wrong. B can retain two stable states while C swaps their identities or reaches new roots; the histories remain distinguishable despite failing your “recovered” criterion. Conversely, recovery after a finite gap does not require two stable attractors under B.

   Report separately: **held under B**, **returned to the original history-labelled roots under C**, and **merged/swapped/new/oscillating/unresolved**. Reserve “the network maintains two states without sensory input” for Z’s held result. F0 retains other sensory drive.

2. **Cut or rewrite the majority-based wording.** [`words()`](/D:/Claude/random/wormWars/scripts/memory_m6/outlast_read.py:66) says “the switches’ states do not outlast…” whenever the recovery interval lies below 50%. That permits a substantial recovered minority while sounding categorical. An interval crossing 50% also does not establish the proposed “some do and some do not” interpretation.

   My preference is to remove this decision rule and report counts, shares and uncertainty. If retained, the wording must explicitly concern **whether a majority recovers its original roots after this 2000-tick interruption**. Wilson intervals describe sampling uncertainty for a specified genome-draw population; the observed fraction among these 169 genomes is already known.

3. **Correct the root-match specification.** [`classify.py`](/D:/Claude/random/wormWars/scripts/memory_m2/classify.py:9) uses `DISTINCT = 1e-6`, whereas the plan and driver call `1e-4` “the classifier’s distinctness level.” That statement is false. A separate `1e-4` cross-phase matching tolerance can be defensible; name and justify it as such.

   The promised read-out sign check is also absent: the classifier records an absolute difference, and `outcome()` receives no signed values. Either implement it or explicitly remove it from the draft. I would remove it: history-labelled root matching already defines the intended recovery, including silent switches.

   This is not evidence that the current census roots are ambiguously matched: their smallest recorded separation is approximately **0.696**, far above either tolerance. Save the four A–C root distances in JSON so the eventual matching decisions are inspectable without local arrays.

4. **Handle uncertainty in the held share too.** [`arm_reading()`](/D:/Claude/random/wormWars/scripts/memory_m6/outlast_read.py:46) places every consistent genome in the held denominator but counts only B switches as successes. Thus B-unresolved cases silently become non-held cases. Give held-share bounds using **B-unresolved** cases. C being unresolved should not obscure a known B result.

5. **Make the advertised guards real.**
   
   [`read()`](/D:/Claude/random/wormWars/scripts/memory_m6/outlast_read.py:74) treats an existing `run.json` without a true `stopped` flag as complete. Validate the unique `(seed, genome)` set against the manifest and recompute the consistency failures; otherwise a valid but partial/stale JSON can receive a definitive reading.
   
   [`stage_run()`](/D:/Claude/random/wormWars/scripts/memory_m6/outlast.py:162) checks consistency only after all B/C work finishes. Stop once failure is unavoidable under the fixed denominator—nine failures among 169—and preserve the diagnostic records.
   
   The one-hour cap is checked before a panel and before each B–C pair, not between B and C or after the final pair. It can overrun and still publish a completed run. Add checks at phase boundaries and before completion; describe it as a checkpointed cap unless long phases themselves can be interrupted.

6. **Test the new execution path, not just its components.** The continuation test calls `P.follow_from` directly; it never calls `O.phase_from`. The genome test checks ID lists; it never calls `O.build`. See [`tests`](/D:/Claude/random/wormWars/tests/test_memory_m6_outlast.py:57).

   Add small tests that exercise the wrapper and catch removing its context, dropping `initial`, restarting C, and rebuilding from the wrong panel size/seed. Force the oscillation branch for the `initial` check. Add partial-manifest and B-unresolved reader cases. The recorded 14/14 sabotages do not cover these failures.

There is also a scope correction: “every N2 switch genome classified so far” is too broad. M6-0 already reports N2 switches under other mappings/banks, including the MS champion and R1 drift cases ([results](/D:/Claude/random/wormWars/docs/memory/M6-0-RESULTS.md:105)). Say **“all switches from the two M2 and eight M4c N2 census panels under M0/03mc.”** Keep the intended sample; do not expand it.

On the smoke result: **do not add a duration sweep or partial-input sweep.** Complete removal for 2000 ticks is a useful, bounded question. If all 169 merge under B and fail recovery under C, that is informative evidence about these selected histories under these interventions. It does not establish that every shorter interruption erases them, that partial reductions do, or that no other autonomous attractors exist. State those limits rather than running another study.

The smoke disclosure is adequate as exploratory disclosure, including the post-smoke “both at” labels. Those labels describe where merging occurred and do not manufacture recovery. I would retain all four seen genomes.

What to cut: the majority-based headline, the redundant sign requirement, and any proposed dose/duration expansion. Keep C—it distinguishes loss of stable separation under removal from failure to recover after the finite gap.