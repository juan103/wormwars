**Verdict: fix then run.** The engine and the registered core match the pre-registration as far as I read them, but the runner has several deviations, one of which can flip a registered label. I ran nothing (read-only) and did not diff against 989da99; everything below is from reading the code.

## Fixes before the run

1. **S2-b rule 1 reads only the paired runs** (`scripts/e3a.py:962-963`). The pre-registration says "no champion in either arm is working". Under reduction 5, or with any unread random-sampling run, a working GA champion in an unpaired run is ignored. S2-b would then say "neither found a working selector" while S2-a reports one. Pass every read champion's flag.

2. **Random sampling's champion tie goes to the lower index, not the lower j** (`e3a.py:793`, `champion_of`). The top 32 are stored by (−selection score, j), so index order is not j order. Validation means are integer sums over 256 worlds, so ties are plausible. Break ties on `rec["top32"][i][k]["j"]`.

3. **The gates do not gate each other** (`e3a.py:441`, `:486`). `g0` only requires that `g-e` exists, and `g1` only that `g0` exists; neither checks `passed`. G0 would run on the gate worlds after a failed G-E, and G1 on the gate and assay worlds after a failed G0. Only `calibrate-e` onward uses `require_gates`.

4. **Admission is not the registered rule.**
   - `remaining_eval_hours` (`e3a.py:618-620`) uses `per_champion × champions + 0.5 × fixed`. It ignores `b`, and the 0.5 is not in §9.
   - The recomputation after stage 6 with the actual qualifier count (§5) is absent.
   - `per_champion` (`:366`) prices validation as 256 episodes per run; it is 32 × 256.
   - `cmd_evaluate` has no admission check (spent + projected ≤ 30).
   - Nothing reads `plan["fits"]`, so E3a starts even when the minimum exceeds 30 h.
   - None of this is likely to bind at about 13 h, but it is registered behaviour, and test 17 pins the 0.5.

5. **A failed Stage 3 assertion blocks the registered readings** (`e3a.py:767-768`). `champions-3` exits, and `calibrate` and `evaluate` both require its record, so S2-a, S2-b and S2-c could never be read. §7 says the batch is "not read"; mark the arm `not_read` and continue.

6. **The end-of-run assertions are incomplete and untested** (`e3a.py:677-705`).
   - B-task has no assertion at all (relays' τ and bias, worm block).
   - "The mask is unchanged" is checked in no arm.
   - Stage 3 does not check `g`.
   - I found no test calling `assertions()` in `tests/test_e3*.py`, though §11 item 13 promises one.
   - I also found no test for "calibration refuses unfrozen champions" or "test worlds refused before stage 14" (item 16); only the train-3 dependency is tested.

7. **`champions-N` accepts a batch that is absent, killed or awaiting its rerun** (`e3a.py:764-771`). It records the arm as `not_read`, permanently. Refuse unless the state is completed, skipped, final-stopped or refused.

8. **The composition differs from §5's table.** Test-world scoring and calibration are registered at 32 × 256. The code scores each organism at 1 padded × 256 (`e3a.py:868`, `:914`; `assays.py:229`). It is internally consistent, since E and the champions share it, but it needs a dated §13 amendment or a code change before the run.

9. **Registered descriptive measures are missing.** Implement them or amend before stage 14, since `evaluate` runs once.
   - The hysteresis sweep.
   - The per-tick logs (q, RA, RB, u, turn contributions).
   - Each logged generation's offsets.
   - Stage 3's module skill at checkpoints.
   - B-shared's memory results.
   - Stage 3's rule-1 ("working") branch: `compare()` drops it at `e3a.py:973`.
   - B-task against Stage 2 under reduction step 1: `e3a.py:975` switches only when Stage 3 is absent.

10. **The window is one tick long, as I read it** (`assays.py:58-61`). §6 starts W at the stimulus's last tick; the code runs `stim + W` ticks. It matters only for borderline slow settlers. Decide and record.

## What matches the pre-registration

- **Events and level timing:** entries, confirmed visits, the goal switch before t + 1, and levels sensed at t + 1 (`world.py:608-628`).
- **The cue:** `at_b` at ticks 0-4, never in the ledger (`world.py:602`).
- **Geometry:** joint redraw, box [4, 20], inclusive limits, own stream.
- **Samplers and masks:** the GA and random-sampling ties (9 coordinates), B-task's blocks and its 171 parameters, the Stage 2 and Stage 3 masks, the seeds.
- **The probe:** q, RA and RB held, on a copy of the state.
- **The fixed-point finder, classes, assignment rule and release start.**
- **The reset:** the write lands 10 ticks after the level reaches 0; unwritten worlds fail.
- **Calibration:** censored levels excluded, D over legs after the first visit.
- **World pairing:** the same `train_ids`, world seed and composition as the GA.
- **G0, G1, S2-a and S2-c wording.**

## Crash risks

- **The G-E GPU leg has never run through `cmd_ge`**, because the smoke skips it. It mirrors `e4s_equivalence.py`, and I saw no error in it.
- **`_SHUTTLE_LEGS` = 128** is safe: about 42 visits is the kinematic ceiling.
- **Device handling** is fine: mutation scales are moved in `mutate`, and the assertions run on CPU copies.
- **Registered worlds:** I found no access to registered worlds or seeds before their stage.

## Engine changes beyond the equivalence check

Low risk, with one gap. `graft_interface`'s "mean" and "swapped" paths were generalised (`PAIRS`, `probe_on`), and G-E exercises only the real probe. Add an E4s-1 mean and swapped case to the CPU leg, or cite a test that pins them.

The GPU leg covers Task N at one composition only. Combat and multi-swarm paths are not covered, but I saw no shuttle code on those paths.