**Verdict: start the formal stages.** Every blocking finding from both reviews is fixed in the current code, and I found no new blocking problem. I checked the code itself, not D188. I could not run the suite or diff against d0410a8 in this read-only session, so the "tests pass" claim rests on the commit message.

**Blocking findings, checked against the code**

- **Kill tail (Astra 1).** `REGISTERED` carries `rerun_kill_tail_seconds: 900`, and the frame's `files` list includes the partial record, so `reconcile_kill` takes its last-write time from it. Training writes the partial at every checkpoint, including index 0 of each in-stage attempt. `champions` and `evaluate` write it per read point and per chunk, calibration chunks included. Confirmed.
- **Kill inside in-stage attempt 2 or 3 (both).** `requires` no longer refuses an exhausted sequence. On the rerun, `train_attempts` closes the open entry as "crash or kill", `next_attempt` returns final, the body raises, and the frame writes a record with final true via salvage. The rerun costs no rollout. Confirmed.
- **In-stage admission (both).** `stage_admit` passes `ctx.cap.t_start`, and `spent_hours` adds the process's running time to the aggregate. Confirmed.
- **In-stage refusal (both).** `refuse` writes the refusal file both at stage level and after a non-admitted attempt. `stage_state` checks it first, `check_order` stops later training, and `trained_records` returns None for it and for absent stages after it. Cap stops label runs `not_run_runs` through the live exception. Confirmed.
- **Non-finite validation names runs (both).** Both error branches in `evolve_batch` set `err.runs`. `_counts` keeps fractions only when a value is non-whole, so integer records elsewhere are unchanged. Confirmed.
- **Validation chunk (Fable B4).** One chunk of strains times mazes in `validate_read_point` and in `project`'s timing. The record's [32, 128, 8] is now true. Confirmed.
- **Denominators (Astra 6).** G and S-gen gate on the seed's shared mean, S-trail additionally on the seed's none mean, S-peer on the seed's own first-B mean only. Since `later_first_b` puts nonarrivals at the horizon, that denominator is never zero in practice. Confirmed.
- **Secondary labels and Holm (Astra 7).** `secondary` drops the gate's better/worse label, reports the alternative, raw p, Holm p, a bound in its own direction, and a conclusion only under Holm. S-trail's wording is "increased trail dependence". Confirmed.
- **Readings after a final champions stop (Astra 8).** `readings_from` returns four "not read" entries with a Holm block without touching the champions key. Confirmed.
- **S-trail's four means (Astra 9).** Computed over the same complete pairs per schedule with equal schedule weights. I checked the algebra: estimate times the seed's shared mean equals (T shared minus seed shared) minus (T none minus seed none) exactly. Confirmed.

**Residual non-blocking points** (none should delay the start)

- **Charge after a kill is bounded by one checkpoint interval.** For T-A that interval is near 57 minutes against a 15-minute tail, so a kill could go about 40 minutes undercharged. It follows E2's registered rule. Worth one sentence in the results.
- **A final-killed training record lacks `attempts` and `failed_runs`.** `final_killed_record` builds from the progress record, which holds only generation and runs in batch. `completed_runs` handles it, but §5's "all runs failed" would then rest on the uncommitted attempts journal in `runs/`. Adding the attempts entries to the partial written by `training_progress` would close this cheaply.
- **A settle-only rerun is admitted under the full stage projection.** After two failures with a tight budget, a rerun that will run nothing could be refused and block N and R. Compliant with §10's letter, but conservative.
- **The body's final error text** says "non-finite" even when a kill ended the sequence. Cosmetic.
- **`readings` still crashes** if the champions record file is absent, which only happens in an unsettled state.