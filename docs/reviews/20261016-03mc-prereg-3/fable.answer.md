**Verdict: bind.** Every one of my six draft-2 items and all five of Astra's findings are fixed as D291 describes, with tests, and I found no new error in the guards, the plan or the registered statistics. The items below are small. Items 1 and 2 touch the text and are cheapest folded into the binding commit; nothing here needs an amendment if left.

**My draft-2 items, checked**

1. Controls path never run: fixed. The synthetic set has the eight control pairs (`tests/test_p4mc.py:201-210`, asserted complete and passed at 465-479), and the smoke screen is those pairs (`scripts/p4mc.py:481-482`). The smoke report shows both targets complete with 10 pairs ranked (`runs/p4mc-smoke/record/report.json:1230-1299`, `1494`).
2. Null-deletion interval of the mean: fixed. `mc_report.py:413` passes `stat="median"`; the test at `test_p4mc.py:439-445` uses 31 zeros and a one, which separates the two statistics.
3. One-shot check burnt before any GPU work: fixed. `EQ.check_references()` runs at `p4mc.py:381`, before the start marker at 384. The pinned hashes equal `power.json:103-107`.
4. Smoke not on committed code: fixed. `build.json`, `prerun-repeat.json`, both run attempts and both reports record `e136fe3`, `dirty: false`.
5. Q-A interval without the floor: fixed. `mc_report.py:293-294` holds each resample to the floor, as Q-D does.
6. README status: fixed (`README.md:3`).

**Astra's five, checked**

- Inputs and environment tied to the run: `MEASUREMENT_INPUTS` are in the guarded list (`p4mc.py:112, 167`); the repeat record carries `inputs_digest` (388-389); `require_check` compares the environment of both records, the repeat record's clean flag and the digest (419-427); tested at `test_p4mc.py:366-379`.
- Report validation: `validate_measurements` (740-759) checks binding, attempts' code and clean flag, settings, plan, inputs, and hashes every unit's arrays; tested at 382-405.
- Counts for withheld questions: `rank_question` always writes planned, measured and valid; Q-B reports batches; Q-C reports N2's response and interval before completeness (`mc_report.py:308-313`); tested at 448-462.
- Report never replaced: exclusive creation (`p4mc.py:725-737`), tested at 482-487. The smoke produced `report.json` and `report-20261016T014219Z-1.json`.

**Also verified:** the seed table in §3 matches `exp03.py:71-79`; the permutation audit compares generator seeds 2·seed + type, which is what `brain.py:52` uses; `brain_config_for_graph` parses `N2perm1000` correctly (`grid.py:179-181`); graph files are checked against the manifest at load (`exp03.py:407-410`); the plan has 93 pairs, 96 factorial and 480 null units, primaries before secondaries (test at 38-60); the formal build token is the bound commit.

**Findings (all small)**

1. **§5's repeat-check wording is wider than the code.** PREREGISTRATION.md:137 says the probes "must agree bit for bit"; `p4mc.py:367` compares only the ramp-end difference and the steady contrast, which are the two terms the empty-deletion stop uses. Correct behaviour, slightly over-stated text. Fix: "…must agree bit for bit on the ramp end and the steady contrast".
2. **Q-B's failure sentence tests components at 0.05, not at the Holm threshold.** `mc_report.py:189-195` lists a part only if its own p exceeds 0.05. If Q-B's p lies between its Holm threshold and 0.05, no part is listed and the text says "see the components" inside the Holm-stop wrapper, whereas §6 line 209 promises "each failed part, with its estimate and 90% interval". Harmless, but either list the parts above `h["threshold"]` (a part can be empty only when an earlier question stopped Holm) or add "or, under a Holm stop, the components" to the text.
3. **The smoke resume exercised only the nothing-left path.** Both attempts in `runs/p4mc-smoke/record/measurements.json:614-652` are "completed"; the second verified 63 arrays and skipped everything in 0 s. A resume that continues measuring from a partial document was not smoke-run; `check_resume` is unit-tested on synthetic documents (`test_p4mc.py:84-128`). Optional: interrupt a smoke run after a few units and resume, minutes on the CPU.
4. **`validate_measurements` does not refuse a unit that is not in the plan.** It checks plan equality and every recorded unit's hash, but an extra `pair/XYZ` record would be read by the pair screen (`mc_report.py:373`). Low risk since the file is committed and diffed; a one-line `set(doc["units"]) <= {u["id"] for u in units}` closes it.
5. **Dead key:** `SMOKE_SIZES["pairs"] = 3` (`p4mc.py:80`) is no longer read. Cosmetic.
6. **If the repeat check fails, the 0.25 GPU-hour equivalence set still runs** before the refusal (`p4mc.py:390-393`). Not a rule breach; the records are still written and nothing formal follows. Leave it or raise first.

**Could not check:** I have no shell in this session, so I ran no `git diff 8b77b57 e136fe3`, no tests and no audit; I compared the committed files against my archived draft-2 review and D291's list. I did not verify the eight sabotage checks, the plateau and Jaccard rules inside 03's builder, or anything on the GPU.