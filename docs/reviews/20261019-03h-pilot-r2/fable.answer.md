**Verdict: bind and run.** Every round-1 finding from both reviewers is fixed in the code and in PILOT.md draft 3, and I found nothing that would mislead G1, S1, G2, P or the sizing. Three small code fixes below (2, 3, 4) do not touch PILOT.md. Draft 3 is ready to bind once its status line has its final wording.

## 1. Round-1 findings, checked against ab2d7bb

| Round-1 item | Where it is fixed | Verdict |
|---|---|---|
| Fable 1 / Astra 5: calibration failure, P rebuilds S1's seeds | `scripts/e03h.py:253-280` catches `SamplerFailure` and `RuntimeError`, records each failure; P rebuilds from `s1["graphs"]` at `:373-382`, checks graph and genome sha256; test at `tests/test_e03h_pilot_driver.py:123` | correct, complete |
| Fable 2: gate outside `replay_mode()`, G2 re-tunes | `_gate` runs under `mode()` at `:233`; `tune_families(base=…)` reuses K, Graded, memoryless (`gate.py:87-91`); test `test_e03h_gate.py:108` | correct, complete |
| Fable 3 / Astra 8: edges, quartile, realised counts, arrays | `gate.py:45` and `_out`; `pilot.quartile_difference`; `realised_food_fell_counts` per condition at `:419`; `.npz` with sha at `:425-426, :448` | correct (see finding 3 for noise in the flags) |
| Fable 4 / Astra 3: cut order and budget precedence | `pilot.projection_table` matches DESIGN.md:363 (SH dropped before W_t); `:439` puts the budget first; tests at `test_e03h_pilot.py:71`, driver test `:188` | correct, complete |
| Fable 5 / Astra 7: unregistered bootstrap seed | `boot_seeds` 3 653 000 and 3 653 001 at `:79`, PILOT.md §5.3, §5.4, §7 | correct |
| Fable 6: Slow over T × FALL_GRID; fallback base | `gate.py:104` and `:107`; PILOT.md §2 states both | correct |
| Fable 7: genome identity | `genome_sha` recorded in S1, checked in P at `:381` | correct |
| Fable 8: status line, P′ command, sha normalisation, push, cap in gate | `sha()` uses `reg.file_sha256`; `require_pushed` at `:488`; `check` passed into every tuning unit and check score | correct |
| Astra 1: cap in G1/G2 | `ck.check()` before the stage (`:511`), each tuning unit (`gate.py:77-78, :94`), each check score, each calibration and each rollout | correct (see finding 2) |
| Astra 2: stale chain | `read()` at `:128-130` verifies each record's upstream hashes transitively; P also compares G2's rates with S1's at `:355`; test `:100` | correct, complete |
| Astra 4: banks played by smoke | fresh banks in `CFG`, smoke from 3 690 000 in `SMOKE_CFG`, disjointness test `:64`, disclosure in PILOT.md §7 | correct, complete |
| Astra 6: gate cost and restriction wording | PILOT.md §2 "What the restriction means" and the cost line | correct |
| Astra 7: P′ retry after a failed P′ | `_escalation_allowed` scans every attempt; only a completed 0.5 blocks; test `:146` | correct |
| Astra 9: calibration world ids | PILOT.md §3 registers ids 0-1 023 under seed 3 661 000 and defines disjointness both ways; matches `calibration.py:201` | correct |
| Astra 11: `rollout_brain` | forwards at `rollout.py:139` | correct, untested (finding 6) |
| Astra 8, unchanged: code may change between stages | only PILOT.md and DESIGN.md are bound; each record carries its commit | acceptable for a pilot; the formal pre-registration should bind the commit |

Step 0b is in the cap clock: `runs/e03h/step0/compute.json` lists the step0b attempt, total 158 s.

## 2. New findings

2. **Low. `over_cap_at_end` double-counts the finished stage.** `scripts/e03h.py:521` calls `ck.over()` after the `acct.recorded` block has already written this attempt into `compute.json` (`accounting.py:319-320`), then adds the same wall time again from `t_start`. The error is conservative (a false overrun flag), never a missed one. Fix: evaluate `over()` inside the recorded block, or use `spent_hours()` alone after it.

3. **Low. The grid-edge flags carry noise.** `gate.py:52` flags any two-valued, non-physical key, so every Slow-kind family reports `use_memory=…` and `use_bit=…` as edges; the CUDA smoke gate record shows exactly that (`runs/e03h-smoke-cuda/pilot/records/gate.json:167-171`). Also, Bit's and M's speed and turn parameters are flagged against the 3-wide local neighbourhood, where 02 flagged M only over the fall keys (`scripts/exp02.py:127`). Reported items only, no verdict reads them. Fix: skip the `use_*` keys and either flag the speed and turn keys against `K_GRID` or say in the record that the flags are local.

4. **Low. A refused rerun relocates the completed record first.** `run_stage` moves the old record to `attemptN` at `:498-508` before `device()`, `ck.check()` and `_escalation_allowed()` run. A P′ refused by the cap leaves no `pilot.json` (the `check()` at `:511` is outside the try); one refused for eligibility leaves a failed record in its place. Nothing is lost, but the committed P record then lives in an attempt file. Fix: run the eligibility and cap checks before the move.

5. **Informational, sizing.** The projection's fixed term includes the sampler's CPU seconds through S1's `seconds_graphs_and_calibration` (`:466`), which DESIGN §8 excludes from GPU-hours. PILOT.md §5.5 registers "plus graph building", so the code matches the registration, and the direction is conservative. 03 measured 111 s per graph all-in against 66 s of fitness, so the overhead is tens of seconds per graph, well inside the 6-hour margin. No change needed.

6. **Low, test gap.** `rollout_brain`'s forwarding of `food_fell_counts` has no test (rule 9). One assertion in `tests/test_e03h_food_fell.py` covers it.

7. **Low, registration.** `max_failures: 10` (`:75`, `:262`) is a stop that PILOT.md §3 does not state. 03 and 03r saw no calibration failures, so it is unlikely to fire. Adding one clause before binding is free; adding it after binding would be an annotation.

8. **Before `bind`:** the status line "draft 3, 2026-10-19, for review" is frozen into the bound hash. Give it its final wording first.

## 3. Readiness

PILOT.md draft 3 matches the code at every point I checked: the family construction and fallbacks, the G1 and G2 criteria, S1's seeds, calibration, genomes, worlds and rate formula, P's reuse of S1's level scores at 0.25, the decile selection, the reliability rule, A2's power with step 0's floor (0.0600 in `step0.json:240`), the decile shift and U, the decision table, and the seeds and banks. Under level the bit is never injected (`world.py:928-929`), so P′'s re-run of level at 0.5 reproduces S1's scores and the registration's wording holds. Bind it.