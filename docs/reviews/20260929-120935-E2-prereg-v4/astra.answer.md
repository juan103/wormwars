**ready to bind**

Must-fix items: **None.** All three v3 blockers are resolved. I found no new blocking regression.

Suggestions:

1. **[tests/test_e2_commands.py:809](/D:/Claude/random/wormWars/tests/test_e2_commands.py:809):** The new killed-extension test preserves real checkpoints, but still does not force an extension-sourced champion. Make an extension checkpoint beat the formal champion, then verify its hash, source and score through finalization and evaluation. This part of my v3 suggestion remains outstanding.

2. **[tests/test_e2_commands.py:774](/D:/Claude/random/wormWars/tests/test_e2_commands.py:774):** The guard test correctly catches the original commit-check bypass. Add an accepted-record case and code/environment rejection cases; currently it stops at commit rejection and stubs the remaining checks.

3. **Documentation cleanup:** [scripts/e2.py:121](/D:/Claude/random/wormWars/scripts/e2.py:121) still says the extension “can never use up” the evaluation budget. Align that comment with §6. Also qualify [the introductory testing claim](/D:/Claude/random/wormWars/experiments/E2-optimizer-screen/PREREGISTRATION.md:40) that *each* test failed first: D121 and D122 explicitly document exceptions.

Checked and found correct:

- **§6:** Fable’s option (a) is accurately registered: first-attempt admission estimate, obligatory rerun exempt, overruns and possible loss of evaluation budget disclosed. The exemption has a targeted test.
- **Skip guards:** `cmd_extend` records provenance; `require_earlier` now checks commitment, code and environment. The enclosing formal guard supplies the pushed-HEAD requirement.
- **Killed attempts:** `run_stage` refuses an existing marker before invoking stage-specific requirements, closing the killed-extension→skip path. A regression test covers it.
- **§10:** “Final” includes skipped extensions. Both descriptions of a consumed rerun now require an applied note and its own marker or record; the stale conflicting definition is gone.
- **§11:** Local accounting contains four eight-stage smoke chains, matching the disclosed commits. Current records confirm smoke projection seeds, matching generation-0 hashes, zero neural scores and nonzero controls.
- Optimizer rules, allowance arithmetic, extension selection and decision thresholds remain consistent with the registration.

I inspected HEAD `1e4b7f5`, its diff from `31beeda`, the archived reviews, D120–D122, all requested code/tests and shared guards. Three isolated checks using the actual source functions and in-memory stand-ins passed: skip-guard traversal/rejection, marker refusal before requirements, and admission versus rerun exemption. I did **not** run the filesystem-writing suite or independently verify the reported fail-first/sabotage history. No files were modified.