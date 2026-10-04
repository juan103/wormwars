**Verdict: start the GPU run.** Every blocking finding from both reviews is fixed in the code as committed, and I found no new defect that would need a code change before `project` binds the commit.

What I checked, against the code rather than D195:

- **Switching definitions** (`wormwars/e3/attribution.py:233-256`). A leg opens at the visit tick; pre-aligned if q is already on the new side; otherwise crossed at the first later tick on the new side, latency `t − t_visit`; overwritten uncrossed by the next visit; censored if still open at `result()`. I re-derived the scripted test by hand (`tests/test_e3b2_attribution.py:178-201`) and every count matches, including the last-tick visit now landing as censored. The stuck-latch case now reads one pre-aligned leg and zero crossings in both directions.
- **Vectorised recorder vs `SwitchTally`** (`attribution.py:309-349`). The branch order is identical: crossings of earlier legs first, then new legs with pre-alignment, then agreement on `prev_goal`/`prev_visited`. `strain = slot_of // n_slots` is correct given `world.py:145`. The `where(new, new & ~pre, open)` also clears a stale open leg on a pre-aligned visit, as the tally does. The real-run cross-check test sums the tally over weys and compares every key.
- **Middle-half counters.** Both bands, split by goal, in both implementations with the same `(high−low)/3` and `/4` margins; `latch_summary` reports agreement, opposite (`decided − agree`), undecided, equal-weight mean, occupancy and eligible weys per band, with maze-bootstrap intervals.
- **`--out` refusal** (`scripts/e3b2.py:917-918`). `accounting.run_script` reads only the exact forms `--out` and `--out=`; the refusal matches both and fires before `run_script` opens any ledger. `main`'s parser has `allow_abbrev=False`, so no abbreviated route exists. The test runs both forms as subprocesses.
- **Trail-dependence split** (`e3b2.py:625-643`). One `idx` for shared, none and the denominator; the mazes are the same ids in both conditions, so the pairing is real. Per-champion t interval plus a schedule bootstrap on the mean of per-champion resample vectors.
- **Lesion units** match plan §5C exactly: visits over the seed's shared mean, the rest raw, median legs as a difference of medians, all outcomes per schedule.
- **Benchmark** (`e3b2.py:438-452`). Each repeat unlinks and replays through `run_chunk`, so compression and the atomic replace are timed; `cap.check()` before each repeat; the project partial is written after each repeat, and `partial_path` is in the `files` list that `reconcile_kill` takes its last mtime from (`e2.py:585`, `:528`).
- **Pinned inputs**: the three hashes are set and the test runs `check_inputs()` against the committed files. I have no shell in this session, so I did not recompute them myself.
- **Resting-turn check**: the probe keys (`"ta:0:final"` → `"one_nose"` → `"A@0.001"` → `"u_none"`) match `evaluate.json`, and `u_none` is identical across m values, so the m = 0.001 concern is moot.

Non-blocking, for the record:

- `settled()` accepts a cap-stopped stage without `require_committed` or `require_same_code`; note it in the report if it is ever used.
- `attribution_report` raises `StopIteration` if no A-shared chunk completed at all. Only reachable if the cap hits inside the first chunk.
- The real-run equivalence test does not guarantee the pre-aligned or censored branches fire in the vectorised path; I verified those by reading, not by a test.
- Excluding censored legs from the switched denominator biases the share upward slightly. The plan states the definition and the censored count is beside it, so this is fine for a descriptive reading.

Start the GPU run.