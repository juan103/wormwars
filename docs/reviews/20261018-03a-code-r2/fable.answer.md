## Verdict: ready for pilot-dev, with small fixes

The round-1 findings are taken in the code, not only in the plan, and the CUDA preflight at a5760c4 (`runs/e03a-smoke-cuda/`) shows every control holding on the GPU: restoration exact, NIP equals deleted, full replay equals plain, KT and KTM unaffected. Two things should be fixed before the owner's word, both cheap: the partial-report path crashes (finding 1), and round B's option order predetermines its outcome against the planted check's evidence (finding 3). The rest is advice on order of stages and on what the budget question should be.

One premise correction. The prompt says nothing ran on the GPU since the exploratory checks. The repository shows the full CUDA preflight at a5760c4 (69 s, `runs/e03a-smoke-cuda/pilot-dev/compute.json`) and a non-smoke `setup` at a5760c4 (25 s; record at `experiments/03a-self-consistency/pilot-dev/setup.json`, 245 eligible, 170 representatives, gains 6.27/3.22). Both are recorded and count on the cap clock, which is fine. What is not explained is `runs/e03a/pilot-dev/genomes/run00-candidates.npz` and `run01-candidates.npz`: those are `evolve-intact`'s outputs in the non-smoke directory, with no attempt in `runs/e03a/pilot-dev/compute/`. Either an evolution was started and killed hard (unrecorded GPU time, a rule-8 gap) or they are stale from a patched test. `evolve-intact` overwrites them, so there is no correctness risk, but the owner should say which before the run.

## Round-1 findings, checked in the code

| # | Status | Where |
|---|---|---|
| 1 search scale | Resolved as a check; its answer is question 3 below | `planted_scale_check.py`, record committed |
| 2 longer searches | Resolved. Snapshots at generation 100 are scored beside generation 200, and the long searches get full diagnostics | `search.py:291-292`, `e03a.py:686-713`; preflight `full.json` has `longer-0/1` in `per_search` and the `longer` rows |
| 3 Spearman | Resolved. Jaccard per type with its hypergeometric expectation; I checked `expected_jaccard`: J = i/(2m−i) under hypergeom(K, m, m) is right | `null.py:246-253`, `e03a.py:611-624` |
| 4 budget margin | Partly. Checkpoints, rounds and target-brains survive a stop (`e03a.py:309-313, 516, 676`). But the partial report crashes (finding 1), there is no mid-course projection, and a cap hit in `full` blocks `probe` and so the report (finding 2) |
| 5 relevance memory | Resolved. [neurons, worlds] @ [worlds, B] with a count matrix; equivalent to the old bootstrap of the three-brain mean | `panel.py:81-85` |
| 6, 7 wording | Resolved | `PILOT-DEV.md` §2, §3; `e03a.py:572` |
| 8 null seed | Resolved. Seeded by target in both the test and the descriptive null | `e03a.py:636, 702-703` |
| 9 annotation | Resolved, dated | `DESIGN.md:148-153` |
| 10 tests | Resolved. `test_the_first_difference_is_exactly_at_action_2L_plus_1` asserts inequality at index 2L for L = 5, 10, 20; §5's row points at the arms test | `tests/test_e03a_probe.py:160-170` |
| 11 reporting | Resolved. A missing rate stops the report; interface AUCs, precision at k, PR-AUC, composite and mirror-zero subset are written (seen in the preflight record) | `e03a.py:820-823, 627-659` |

## Findings

**1. The partial report raises a KeyError, so the one scenario it was built for fails (medium; `scripts/e03a.py:866`).** When `full` stops early, the failed record holds only `progress`'s keys, which is `target_brains` (`e03a.py:676, 921`); `p` and `setting` are locals never put in `progress`. `stage_report` reads `full` with `partial=True` and then indexes `full["p"]` whenever any target-brain finished. Read the margin from the baseline record instead (it is the same number), and the smoke test should include a stopped `full` followed by `report`.

**2. Run `probe` before `tune` and `full` (low cost, protects the measurement; `scripts/e03a.py:753, 825`).** `probe` depends only on `baseline`, costs about 0.1 M episodes, and the report requires it completed. If the cap is hit inside `full`, which is the likeliest place, no probe timing exists and the report cannot run at all without an owner-approved cap extension. Reordering the stage list costs nothing. The same logic argues for a projection line after `evolve-nip` from the recorded `batch_seconds`, which round 1 asked for and is not there; it is optional if `probe` moves earlier.

**3. Round B's order decides its outcome, and the current order picks the setting the planted check found worst (medium; `scripts/e03a.py:93-95, 562-565`).** The rule keeps the first setting unless a later one beats the best by 0.02 targets, and the plan itself says the noise is far larger than 0.02. So round B will almost surely return (1/3, 1). From `planted-scale-check.json`, mean Q at generation 100 under the perfect signal:

| setting | AIYL | RIAL | AIZL |
|---|---|---|---|
| (1/3, 1) | 0.34 | 0.40 | 0.33 |
| (1/3, 3) | 0.37 | 0.44 | 0.40 |
| (0.6, 1) | 0.51 | 0.50 | 0.44 |
| (0.6, 3) | 0.52 | 0.52 | 0.51 |

Under the noisy oracle the four are within noise of each other. A rule that cannot be moved by data should start from the best prior evidence: set the default to p_move 0.6, max_moves 3, and list round B as (0.6, 3), (0.6, 1), (1/3, 3), (1/3, 1). The carry logic still reuses round A's searches for the first setting, since it equals the default. This is inside what §6 leaves to pilot-dev, so it is a plan change, not a design amendment.

**4. Question 3: keep the 100-generation budget, measure the signal on the real task first, and make the free change now (finding 3).** Reasons:
- The planted check shows discovery is proposal-limited even with an oracle: per replica and generation about p_move × 8 × (m − k)/(K − m) improving proposals, so Q rises roughly 0.35 → 0.5 from 100 to 200 generations at p_move 1/3. Generations give diminishing returns; move throughput is the lever, and it is free.
- The budget cannot absorb longer searches. The N2 target-brains are 29.7 of 56.3 hours at 420/s (DESIGN.md §10). Doubling the search makes the total exceed 72 hours, and the cuts of §10 recover about 15 percent, not 100.
- The real question is where the task sits between the two oracles, and only the real task can answer it. A rough estimate: a high-relevance target's whole deletion deficit is a few tenths of a target, spread over 40-70 partners, while the paired 16-world noise between states is a few tenths of a target. That is a weaker per-partner signal than the "noisy" oracle, where Q barely exceeds chance. If that is what pilot-dev finds, no affordable budget fixes it, and the honest result is the design's own "functional success, anatomy undetermined" route, which the pilot criteria already gate.
- Pilot-dev should therefore record the signal-to-noise directly, at no GPU cost: for each refit search, the SD across generations of the coldest replica's score (`trace.scores`, the 16-world noise under weight-only moves), and per generation the spread of offspring minus current scores on the same worlds (the paired noise the acceptance rule sees; a few floats per generation added to `Trace`). Beside the refit minus deleted difference on 2 048 worlds (the whole partner set's signal), this says which oracle the task resembles.
- Decision rule to write down now: if free-search Q at 100 is within noise of chance and the long searches do not gain by 200, the search is signal-limited and the budget stays; if Q is still rising at 100 and the long searches gain, propose a budget amendment with both reviewers, paid by §10's cuts and the move settings, before the pre-registration.

**5. Final scoring runs one chunk of 34 816 worlds, and the scan one of 87 552 (low; `scripts/e03a.py:463`, `arms.py:67, 106`).** The largest chunk this repository has run is 16 384 (E2d). Task N worlds are small (24-cell arena, one wey), so memory should be about 1-2 GB and fine, but the preflight cannot see it. The cost of being wrong differs: an OOM in `panel` loses minutes; an OOM in `_final_scores` loses the target-brain's 13-15 searches just run, since scoring follows the searches. Chunking final scoring at a tested size (8 × 2 048) changes no claim, because exactness is claimed only for the baseline controls, which stay single-strain.

**6. Smaller points in the new paths (low).**
- `e03a.py:656-658`: the mirror-zero subset takes candidates at zero in all three types at once, then scores each type on it. The design's "candidates the mirror ranking leaves tied at zero" reads more naturally per type. Either is defensible; the frozen protocol should say which.
- `e03a.py:586-592`: `_turnover` pairs indices 0..80 with 10..90, so the window ending at generation 100 (and 200) is dropped. Harmless, but the label "per 10 generations" overstates slightly.
- `e03a.py:695`: `base_rec["target_brains"][bi]` relies on `target_brains()` ordering; assert the labels match.
- `e03a.py:812-823`: the report excludes the current attempt, so its own CPU time cannot pollute the `measure` rate; the earlier non-smoke `family2` attempt added 0.8 s to `measure` with no worlds, negligible. Fine.
- `search.py:317-348` groups rollouts by reinsertion object, so the MIP and NIP target-brains of one target, which share a union spec, run as separate rollouts in `tune`. Grouping by X would halve tune's rollouts; optional, formal-driver material.

**Checked and correct in the new code:** snapshots are copies taken after `tell` and verified against a fresh 3-generation search (`search.py:291-296`, test at `test_e03a_search.py:433`); the simulator moves the concatenated genome and the states to the device (`search.py:332`, `reinsert.py:198-214`); `same_episodes` compares counts, final heads and every event with NaN-equal only on float tables, with a trajectory-not-counts test (`arms.py:70-82`, `test_e03a_arms.py:104`); `family2` withholds any non-finite or short vector with p = 1 before Holm (`stats.py:72-79`); `subset_recovery` guards the no-scoreable-type case (`null.py:235-243`); the ladder rule qualifies on every pair, picks by mean distance to 30 percent, and flags the nearest otherwise (`e03a.py:490-503`); tune's seeds (base + 1000 ri + 100 si + bi) cannot collide with full's (base + 10 000 + bi, + 10 500 + bi); the report's projection matches §10's counts (60 target-brains, 38 evolutions, 14 pilot-check evolutions, 16 pilot-check target-brains) and the 32-world rule.