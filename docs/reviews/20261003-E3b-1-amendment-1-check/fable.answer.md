**Verdict: the commit carries out my changes correctly. One stale sentence remains in the code, and two small traceability gaps. Nothing blocks the rerun.**

What I checked, against my seven requested changes:

- **Streams and bound.** `walls_for` keeps k = 0 on `[seed, id, 0x3A11]`, uses `[seed, id, 0x3A11, k]` for k ≥ 1, redraws only on empty eligibility, and raises past 64. The placement stream is untouched. §14 states all of this exactly as coded.
- **Predicted redraw list.** `maze-redraws.json` holds 41 entries, all k = 1: 6073, 37 training ids (9 + 17 + 5 + 6 across the arms), 9585 at the projection seed, and 2067 and 2183. The reference's per-set infeasible lists sum to the same 37. §14 and D190 match the file.
- **E3b-0 untouched, plan corrected.** The "fresh" block appears in E3b-0's records only under a `fresh` configuration key. The dated correction sits beside plan line 39 with the registered sentence intact.
- **Real equivalence check.** The audit hashes walls, edges, episode-0 placements and donor placements over E3b-0's three blocks, E3b-1's four, every training id set and `project`'s ids, plus a 300-tick CPU trace. The compare recomputes digests over only the previously feasible ids, so the redrawn ones cannot mask a change. `identical_feasible`, `trace_identical` and `passed` are all true. The `hasattr` fallback is what let the reference be written at 171fcc5. §14's "finite corpus, not a proof" caveat is there.
- **`project` handling.** The frame's rerun path archives attempt 1's files as `-attempt1` rather than deleting them, and the compute record charges 1.13 s with zero worlds, ticks and neural updates. So "about 1 second" and "no world tick" are both correct. The projection-seed clarification is in §14 and in the stage's note.
- **Pre-flight.** It runs in every stage's `requires`, builds walls, the episode-0 placement and donors where replay is played, and refuses on donor exhaustion. Its id sets match the stage bodies: the `project` run seeds use the same `100 × j + k` ordering as the body and the audit, and training includes the learning-curve block. The record gets `mazes.redrawn` through the stage's doc, so a stopped attempt keeps it.
- **Donor exception path.** Covered by the pre-flight refusal and tested with a forced exhaustion.

Remaining fixes, none blocking:

1. **Stale statement in code.** The module docstring of `wormwars/e3/maze.py` line 11 still says "A maze with no eligible pair raises." That is now false below 64 redraws. Reword it to match the `walls_for` docstring. Plan line 438's table entry "never redrawn (60d0de9)" is historical and can stay.
2. **An untraceable claim.** §14 says no calibration or test maze exhausts the donor search. The audit folds the exception list into each hash but never reports it, so no committed file shows that. Either have the audit emit `donor_exceptions` or note that `evaluate`'s pre-flight is what enforces it. The pre-flight will catch it either way.
3. **A refusal with no record.** A pre-flight refusal happens inside `requires`, before the start marker and the record, so it leaves no file. The admission refusals write a `refused` record. Deterministic, so nothing is lost, but worth one line in `refuse()`'s style if you want every stop on disk.

Fix 1 is a one-line docstring edit and can go in with the rerun commit. The others can follow.

**rerun project**