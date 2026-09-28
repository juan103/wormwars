**The v4 blocking defect is fixed.** I compared `1653809` with `627b886`, read both v4 reviews, and traced the affected callers. I found no new blocking defect. I executed no project code or tests and changed nothing.

- **Reconciliation now survives the identified interruption.** [reconcile_kill](/D:/Claude/random/wormWars/scripts/e04a.py:272) writes to `.json.partial`, which the aggregator’s `*.json` scan excludes, then publishes with `os.replace`. An existing record supplies the stored charge. Aggregation runs unconditionally before returning, so another invocation repairs a missing, stale or interrupted aggregate before admitting the rerun.
- **The regression targets the right state.** [The new test](/D:/Claude/random/wormWars/tests/test_e04a_commands.py:328) retains the reconciliation record while deleting or zeroing the aggregate, then requires cap refusal, unchanged charged time and no archiving. I have not independently verified test execution or the reported sabotage check.
- **The additional changes are consistent.** [rerun_plan](/D:/Claude/random/wormWars/scripts/e04a.py:242) reconciles a killed second attempt before refusing another rerun. [amended_plan_fits](/D:/Claude/random/wormWars/scripts/e04a.py:261) requires fewer generations and includes both generation and checkpoint costs at the previous projection’s measured rates.
- **The earlier text corrections are present:** cleanup-handler wording, D107 references, the corrected smoke-run explanation, and the explicit amendment route for a guarded-code crash.

One **nonblocking wording correction** remains: §8, §14 and D108 say the aggregate is rebuilt “before every cap check.” Literally, it is rebuilt **on every kill-reconciliation attempt, before the rerun’s admission check**; ordinary `CapClock.check()` calls only read it. Narrow that wording in the binding commit. This does not reopen the fixed interruption gap.

The local smoke records support the reported four completed CPU stages, “not passed” evaluation and empty extras errors. Their provenance is dirty `1653809`, so they support the development-smoke claim, not an exact-commit validation of `627b886`.

**04a pre-registration: ready to bind**