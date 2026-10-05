**Verdict: fix first, two one-line changes in the new killed-stage route. Everything else is right.** I read the HEAD code and tests only. I could not run the suite or `git diff` from this session, so I checked the described changes against the code as it stands.

**1. Are both fixes correct and complete?**

- **Champions: yes.** Each champion is saved once to its own file before its entry is appended, at `scripts/e3c.py:1179-1182`. A failed save propagates before the append, so the stopped record's salvage lists only saved champions. A kill after the save but before the append leaves an unreferenced file, which nothing reads. `load_champions` at `scripts/e3c.py:1123-1131` loads each listed champion and checks its hash. Both of Astra's windows are closed. The test at `tests/test_e3c_stages.py:648-679` injects the failed second save and loads the listed champions, so it exercises the real control flow.

- **`require_record`: correct for the two cases it names,** at `scripts/e3c.py:733-758`. A crashed first attempt is read through its stopped record only when the cap is exhausted, and it still passes the committed, same-code and same-environment checks. A killed stage is read from its partial. Before exhaustion both refuse. The sequence works in practice: the kill is charged by `reconcile_kill` when the rerun is planned, and the cap refuses the rerun afterwards, so the report sees the cap as exhausted. `CapClock.check` and `cap_exhausted` read the same aggregate against the same constant.

**2. Defects introduced? Two, both in the killed route.**

- **The partial record is not required to be committed.** The stopped route calls `require_committed` on the record. The killed route at `scripts/e3c.py:744-749` returns the partial with no such check. No partial has ever been committed in this repository, and the frame would let a formal report read an untracked file. That breaks rule 5 and Fable's third condition.

- **A killed rerun bypasses the frame's charge.** When `rerun_state` is "used" and the marker has no record, the frame's own path is one more `--rerun`, which charges the kill and writes a final record regardless of the cap (`scripts/e2.py:478-483`). The new route short-circuits that once the cap is exhausted, so the killed rerun's time never enters the compute record.

**Required changes:**

1. In the killed route, when `E.formal(args) and not args.smoke`, call `E.require_committed(part)` before returning.
2. Exclude the killed-rerun case from the route: add `E.rerun_state(stage) != "used"` to its condition, so the frame's existing message directs the owner to `--rerun`.

Extend the test at `tests/test_e3c_stages.py:682-700` with one case for each.

**Not required, but decide before `project`, since the guard blocks later changes:**

- A kill before the first partial write, within the cap's tail window, still leaves the report stuck. `formal_requires` could treat marker-without-partial as "never started" once the cap is exhausted.
- `save_atomic` leaves its `.tmp.npz` behind on failure. The T0 test at `tests/test_t0_pairing_confirm.py:166` loads every `.npz` under `runs/` and would go red until the file is removed by hand. An `unlink` in an except clause fixes it.
- Amendment 2 must state the new reading rule. The registered point 5 says a stopped stage is read "through that stage's salvaged record". A partial record is not that, and the pre-registration has no Amendment 2 yet.