**Verdict: bind as is.** All seven of my draft-2 findings are resolved, and resolved correctly. Nothing draft 3 introduced is wrong. Only wording-level notes remain; none changes a registered quantity, rule or stage.

## What I checked

- **Pinned hashes:** all six in §2 match the files after CRLF → LF (recomputed with `sed`/`sha256sum`; Python is not on the Monitor shell's PATH, so I did not rerun the tests or recompute the `gen010` digest, which Astra verified at draft 2 and whose files are unchanged).
- **Power numbers:** every figure in §8 matches `power.json`. Main grid rows for R = 8, 16, 24, 32, 40 (including the bracketed μ = 0.20 values), R = 24's 0.79, the false rates 0.026–0.065, the structured cases (M 0.939/0.983, U 0.956/0.944, correlations 0.244–0.257 and 0.398–0.430), the mixtures (0.896, 0.708, 0.793; R = 40: 0.799, 0.873), and the new tie cases (worst: realised 0.2464–0.2487, power 1.00/0.871/0.974; best: 1.00/0.892/0.976). The main grid is unchanged by the rerun, as D273 says: the tie block runs first on the `SEED + 2` stream, so only the structured and mixture cases moved.
- **Tie sensitivity's implementation** (`e4d_evo_power.py:150-165`): among exact validation ties it picks the lowest or highest true p, so it brackets any deterministic tie rule, including the registered fitness-then-norm one. Correct.
- **Budget:** F row = `hours(4)` (0.43/0.49), L and S rows = `hours(32)` (2.31/3.92); 8 + 1.5 + 6 = 15.5 ≤ 23.95. A rerun of `train-l` fits the 8 h cap at the pilot-based rate (≈2.35 h with the 20% against a ≈5.9 h remainder) and fails the 80% refusal at the conservative rate (≈4.28 h against ≈3.3 h), exactly as §9 states.
- **`evo_stats.improvement`:** range [−1, 1], the 1/128 grid, exact count, one-sided LB from `bounds`, strict `LB > 0` via `improvement_state`; the tests cover the paired range above 0.5, malformed input, the count, and the strict edge (a `>=` sabotage would fail `improvement_state(0.0)`). Correct.
- **`TrialResult` authorization:** the arrays exist in the rollout as `rf`/`df` [S, W, 2] (`evo_trial.py:84-85`); `evolve_batch` reads only `score` and `progress`, so additive fields cannot change training, and the replay is a valid equivalence check.
- **`check`'s replay inputs:** seeds 1 420 100 + 10j + k, factors 0.25/1/2/4, base 70 000 000 span 10 000 000, checkpoint ids `block("validation")[:8]` = 53 700–53 707 (`e4d_evo.py:306`), snapshot before breeding (`evolve.py:194`) so index 10 of 11 reproduces `gen010`. All match the records.
- **`check`'s formal-evaluation exercise:** the w = 3 control under `none` and `fixed0`, its cut version (= E-G) and E-G are all assignment-blind, so the per-maze balance assertion must hold there; the oracle is exempt and played with `check=False`, matching `trial_rollout`.
- **Dependency table:** S depends on `report-l` and the owner's word only; `require_same_env` exists (`registration.py:156`).
- **Block arithmetic:** L's test blocks end at 59 095 < 60 000; F's at 60 511 < 61 000; S's at 65 095; training 100M–110M is disjoint from the pilot's timing ids (base 90M, span 10M, so ≤ 99 999 999).

## Notes (wording only)

1. **§5 dependency table, `train-f` row.** If L reads "not evaluable" or "not completed", `evaluate-l` or `train-l` stopped, so `report-l` never completes and `train-f` cannot start; the owner is asked anyway. §3 says this explicitly for S; say it for F ("F's stages then wait on the owner's decision, by amendment"), so the undefined case is defined.
2. **§10, second bullet:** `control_genome(E-G, "comparator", 0.5)` omits `cx`; §3 has the full signature.
3. **§8, "Ties bounded":** add "σ = 0", which the script's docstring states and the text does not.
4. **§4:** the pilot's timing ids are "90 000 000 onward"; the record is base 90 000 000, span 10 000 000, so write 90 000 000–99 999 999 and the disjointness from the formal training range is explicit.
5. **`e4d_evo_power.py:80`** comment says the shared effects give correlations 0.23 and 0.40; the record shows 0.24–0.26 and 0.40–0.43. Script comment only.

**R = 32:** keep, as before. The tie bound removes the one approximation that could have favoured 32, and the worst case still clears 0.80 in every main scenario.