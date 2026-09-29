**revise**

The specific v2 must-fixes are addressed, with targeted tests. The new extension skip rule introduces three issues.

Must-fix items:

1. **A skipped extension bypasses the commit requirement.** [scripts/e2.py:426](/D:/Claude/random/wormWars/scripts/e2.py:426) returns before `require_committed()`. Consequently, evaluation can start immediately after an uncommitted skip record is written, contrary to §§7 and 10. Require the skipped record to be committed and pushed before accepting it. Add a guard-enabled test; lack of simulation provenance does not justify bypassing publication.

2. **The skip branch can misclassify a killed extension as “not run.”** [scripts/e2.py:905](/D:/Claude/random/wormWars/scripts/e2.py:905), with `run_stage` at line 588. A first-attempt marker does not block execution before `requires()` writes the skip record. Concrete sequence: extension killed → `--rerun` charges it → setup interrupted before writing the rerun note → plain `extend` encounters insufficient remaining budget and writes a final skip. This bypasses the obligatory rerun and omits surviving extension champions. Permit skipping only a genuinely unstarted extension; reject an existing marker before this branch. Test that sequence.

3. **The evaluation reserve is not protected as §6 claims.** [scripts/e2.py:905](/D:/Claude/random/wormWars/scripts/e2.py:905) explicitly exempts reruns, and training uses the full seven-hour clock at [line 746](/D:/Claude/random/wormWars/scripts/e2.py:746). An admitted extension can overrun its projection; a failed attempt followed by its obligatory rerun can consume the reserve even at the projected rate. Either enforce a separate extension spending limit across attempts, with registered finalization and champion preservation, or explicitly register this as a first-attempt admission estimate and disclose that evaluation can still lose its budget. The current “never takes” promise is false. Test rerun admission and elapsed-time overruns; the existing skip test resets spent time to zero before evaluation.

Suggestions:

- Restore the proposed guard-wiring tests. They can mock CUDA/Git boundaries, as `tests/test_registration.py` already does; they do not require a live pushed tree.
- Remove §10’s stale definition that a rerun is used when its note is written; the following paragraph correctly requires an applied note **and** its own marker or record.
- Add a killed-extension test using a real partial record whose winning champion comes from the extension. Current new evaluation tests principally exercise formal fallbacks.

Checked and found correct:

- The two-phase rerun note, attempt-numbered markers, resumable archive moves, and retrying replacements address the v2 setup failures. Corresponding interruption and retry tests exist.
- Initial fallback partials, reconstruction without a partial, and `analyse()` iterating `champions_over_both` address both v2 champion-loss issues.
- Generation 0 validates the original start genome. The new hash test covers this; the latest local smoke records show matching GA/random/ES hashes.
- §11 and D121 disclose all three smoke chains. The local accounting contains the corresponding 24 stage attempts.
- ES update rules, allowance arithmetic, extension selection, and decision thresholds remain consistent with the registration.

I inspected HEAD `31beeda`, the v2 diff, both archived review rounds, D120/D121, all requested code/tests, shared guards, and local smoke records. I did not execute the suite or independently verify the claimed fail-before-pass/sabotage history. No files were modified.