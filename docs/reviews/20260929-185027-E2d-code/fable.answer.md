# Verdict: **fix**

The rules are implemented faithfully, but the stage logic has three defects that would either block the hold-out pass or draw readings the plan forbids. All are small changes; nothing needs rethinking. I could not execute anything, so every finding is from reading the code, and the twelve sabotage checks in D132 are unverified.

## Must-fix

1. **A hard-stopped arm blocks everything after it** (`scripts/e2d.py:399-402`).
   - `require()` does not treat `E.OUTCOMES["cap"]` as final, so it falls through to `E.require_earlier` (`scripts/e2.py:426-431`), which raises "did not complete".
   - The next arm never reaches `admit`, and `cmd_evaluate` (`e2d.py:803`) cannot start. The reserve is protected and then unusable.
   - Change: count the cap outcome as final under `final_ok`.
   - Test: hard stop on C1, later arms run or skip, the pass runs with C1 "not drawn".

2. **An incomplete arm gets a reading** (`e2d.py:811-821`, `846-848`, `859`).
   - A stopped or capped arm keeps `records` with a `champion` per run from its last checkpoint (`e2.py:645-647`, `738`). The runs are in lockstep, so all 8 are present.
   - `have` is then complete and `arm_reading` is drawn from a truncated arm; `ok()` does the same for the contrasts and the interaction.
   - Change: decide by `arms[x]["outcome"] == "completed"`, and do not load incomplete arms' champions (or label them descriptive).
   - Test: an arm stopped after at least one checkpoint, rerun refused.

3. **The check-failure fallback is missing** (`e2d.py:597`, `851-856`; plan lines 105-106).
   - Set readings are still written when `checks["passed"]` is false.
   - `analyse_c` never reads `b["checks"]["passed"]`, so `leaves_plateau` uses classes regardless.
   - Change: set readings "not drawn"; `leaves_plateau` on scores alone, with the fallback recorded.

4. **Arm records carry the base configuration** (`e2d.py:752`).
   - `run_stage` writes `resolved_config` and its hash (`e2.py:605-608`) before the body swaps `ctx.cfg`.
   - C2's record would show `w_sigma` 0.08, and C1's 8 worlds beside a composition of `[256, 32, 1]`.
   - Change: update both fields in the body and keep the base hash beside them.

5. **A missing 04a record is skipped silently** (`e2d.py:343-344`). In a formal run this must raise. Also assert the plan's denominators: 31 distinct E2 genomes, 12 shaped and 4 unshaped.

6. **The reference's uncertainty is not a bootstrap** (`e2d.py:672`, `686`). It is SD/√248, where the plan says "bootstrap standard error … (not assumed)". The numbers will barely differ; implement it or declare the deviation in `DECISIONS.md` before the run.

7. **Tests that pass with the rule broken**, including ones the plan promised (lines 348-349):

   | Rule | Gap |
   |---|---|
   | `world_ci` | No test at all; the 95% level is unpinned. |
   | `run_summary` | `0.3 < lo90 < mean < hi90 < 0.7` passes at any level. |
   | `arm_reading` | Dropping the interval condition passes all four cases (the inconclusive case has mean 0.25). "Harmful, carried by run 2" is untested. |
   | `interaction` | The without-run-2 half is untested. |
   | `budget_reading` | Threshold and interval are never separated. |
   | `set_reading` | A share of 0.5 passes; add 5 of 8 and 6 of 8. |
   | `_pair_rates` | The first test passes if scored against all worlds; add a reversed complement. |
   | `analyse_c0` | Tested only through fakes, where every bin is empty: the 0.8 rule, minimum pairs, overlap and ES signs are unpinned. |
   | `es_pairs` | Same noise at both σ, and the plus/minus order, are untested. |
   | C0 seeds | `seed + 10 × champion` is unpinned. |
   | `pairing_check` | Never seen failing. |
   | `training_clock` | Using 7.0 instead of 6.5 would pass. |
   | Probes on Task N | `tests/test_exp02_stereo_probe.py` uses the default task, not Task N. |

## Suggestions

- **Replay:** also compare validation counts, the log's `best_sha256` for generations 0-25, and the config hash against E2's record. This costs nothing and separates config drift from engine drift.
- **Pairing:** carry `pairing["passed"]` into the evaluation beside each reading; today it is never read.
- **Reported beside, per the plan, but absent:**
  - E2's registered champion for C1 and C4;
  - classes for GA′ and C2′;
  - Part B's pooled distinct-genome counts and the three named genomes;
  - the budget reading's episodes and validation curves;
  - the ES mean's score in C0.
- **Missing contrasts:** write "not drawn" for C4 − C1 and C4 − C2′, as for the interaction.
- **Interval convention:** state that `lo95` is the 2.5th percentile, not E1's one-sided 5th (`registration.lower_bound`).
- **Smoke sources:** regenerate `runs/e2-smoke` and `runs/e04a-smoke` on CUDA at the current commit first. Otherwise the replay reports drift and the smoke never reaches the arms and the pass, where must-fix 1-3 live.
- **Smoke seeds:** C0 keeps its formal seeds in smoke, against "Smoke: 1 138 000 and up".
- **Provenance:** record the sha256 of `SOURCE_RECORDS` in each record.

## Checked and found correct

- **Rules:**
  - `classify`, `set_reading`, `plateau_reading`, `budget_reading`, `leaves_plateau`, `top_k` and `sign_flip_p` match the plan.
  - Intervals are 2.5/97.5 over worlds and 5/95 over runs, with 10 000 resamples and seed 0.
  - C0 uses one set of 400 draws without replacement, scores each draw against its complement, excludes zero complements per draw, bins once by the 256-world gap, and counts ties half.
  - Random sampling is classified but not read.
- **C0's genomes:** `children` resets the generator per scale, and `es_pairs` reuses the noise at both σ. Its interleaving matches `analyse_c0`, and the compositions are (65, 256, 1).
- **Replay:** E2's seeds, ids, σ 0.5 and learning rate 0.15, composition (256, 8, 1), 26 generations with checkpoints at 0 and 25. No genome files are written.
- **Arms:** settings, references, matched generations, first-best ties and episode counts (258 816, 266 496, 166 144) match the table. Admission covers reruns.
- **Ids:** I found no earlier use of 991-992 million in any Python file.
- **04a:** runs 0-15 have unique labels; 0-11 are shaped and 12-15 unshaped.
- **Frame reuse:** safe for what is called. Every path, cap, outcome and registered number is read from module globals at call time, and `E` is a private module instance, so nothing writes to E2's folders. The only leftover is the wording of `OUTCOMES["skipped"]` ("kept for the evaluation").