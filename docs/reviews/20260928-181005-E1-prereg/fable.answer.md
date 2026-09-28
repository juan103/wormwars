# E1 pre-registration review

I ran nothing. I read the draft, `scripts/e1.py`, the Task N code, both test files, design v2.1, T1 §7, and the local git logs and smoke outputs. The numbers below are hand calculations.

## 1. Does the implementation match the design?

Yes on the mechanics. I found no defect in Task N itself.

- **Sensing-only target:** added in `_sensed_food` (`world.py:642-643`), never written to `fields[FOOD]`. The cell-centre convention matches `sample_bilinear`, so the scent peak sits on the scored centre.
- **Energy off, pairing, score, oracle:** the target stream is separate and keyed by (run seed, world id) (`world.py:493`). The oracle's privilege is opt-in through `attach_world` (`world.py:369-371`); no control has it.
- **Overflow:** at most about 21 arrivals fit in 300 ticks against a sequence of 64, and overflow raises.

Defects, all in the runner:

| Where | Defect |
|---|---|
| `e1.py:124`, `e1.py:324` | **The freeze hash will not match the committed file.** `write_text` writes CRLF on Windows (the smoke freeze has 323 CRLF pairs), `.gitattributes` is `* text=auto`, and the gate hashes raw bytes. This is D056's class of bug. |
| `e1.py:305-308` | Path efficiency divides centre-to-centre distance by a path that starts and ends within R, so it can reach 8/5 = 1.6. |
| `e1.py:302-303` | Median leg time covers finished legs only. Label it so. |
| `e1.py:174-184` | If no sample is ever 3 cells from the wall, the own-body level is silently 0. Record the sample count and refuse 0. |
| `controllers.py:59-64` | The random walk's noise follows batch shape, not world id, so each grid point tunes on different noise. Disclose it. |

The gate's event tables are not saved, and the freeze keeps only each grid's winner. Store both, so the "first maximum" can be audited.

## 2. Are the registered numbers sensible?

Mostly yes. Fixing the thresholds before the pilot is stricter than the design, which left them to the pilot. I support that, but the draft should say so explicitly.

- **Gate numbers:** 80% with at least 2, margin 0.5, 1 024 worlds and the bootstrap are fine. The margin is weak; rule 3 is the real test.
- **Rule 3** treats 0.5 × the real mean as a constant. Bootstrapping the per-world value 0.5·real − mirrored against 0 is cleaner. Optional.
- **Cap:** 8 hours is ample. Tuning is about 470 000 world-episodes, which I estimate at well under an hour.
- **A × scale = 0.35** is inherited from 02 without a stated reason. Add one line.
- **Not fixed, and should be:**
  - the outcome wording if the cap is hit mid-gate;
  - the restart policy after a crashed pilot or gate;
  - that the freeze is pushed, not only committed, before the gate.
- **The design's pilot list** included shares of episodes with at least 1 and 2 arrivals. The runner does not record them.

## 3. The σ disclosure

Keep the rule. The handling is honest, but it needs three additions.

- **The outcome is geometry, not data.** The 5% floor is reached within 2.45σ: 4.9, 7.3, 9.8 and 14.7 cells.
  - σ = 2 and 3 can never qualify, because that radius is below D = 8.
  - I get expected shares of about 0.29 at σ = 4 and 0.88 at σ = 6, matching what was seen.
  - So σ = 6 is selected either way, and the pilot decides only the flag. Say this in §7.
- **The debug run left no record.** `runs/e1-smoke/compute/` holds four attempts, all smoke-sized. State that it ran outside the accounting.
- **The smoke runs' world ids cannot be checked.** "Before the smoke run was moved off the E1 ranges" implies it was once on them, and the smoke runs at 16:07-16:08 UTC ran on uncommitted code and record no ids. State explicitly whether any smoke pilot or gate ran on E1 ids. If there is doubt, start each stage at an untouched offset.

Adding σ = 8 or a maximum separation now would be data-driven. Do not.

## 4. Can the pilot or gate be gamed or fail silently?

Yes, in these ways:

- **Code drift:** the gate never compares its code with the pilot's commit (`e1.py:314-327`).
- **Hand-edited freeze:** any committed freeze with matching `registered` is accepted. Re-derive σ and the navigator from the freeze's own rows.
- **Gate-once** rests on `gate.json` existing. A crash or a deletion allows a rerun. Write a start marker.
- **CPU fallback:** the device defaults to CPU if CUDA is unavailable (`e1.py:422`). Refuse that outside smoke.
- **Dirty check** omits `experiments/E1-navigation/`, so an edited pre-registration does not block the pilot.
- **Push:** nothing checks it. `origin/roadmap` is at `857e0ce`, so neither E1 commit is public yet.
- **Binding commit:** "the one that first contains this file together with `scripts/e1.py`" is `f83bd19`, the draft. Any revision makes that wrong.
- **Cap:** it reads git-ignored local files. Commit the aggregate.
- **No guard has a test** (rule 9): gate-once, freeze checks, cap, smoke ids.

Smoke isolation itself is sound: ids and paths are rebound before anything is deleted.

## 5. Does T1's composition finding matter?

Little for the gate. Every arm runs as one strain on 1 024 worlds, so paired arms share a composition, as D092 asks.

- **Tuning chunks are unequal.** The constant grid has 65 points, so its last chunk holds one strain. There is no `bmm`, but state that tuning is specific to this chunking.
- **Generation 0** runs at (256, 64, 1), and the freeze records it. Its throughput will overstate 04a's 32 × 8 batches. Measure that shape separately, on non-E1 ids.
- **Reproducibility:** the draft makes no claim for the gate's counts. State one.

E1 pre-registration: revise

Must-fix:
1. Write the freeze with LF and hash it normalised.
2. Make the gate refuse code that differs from the pilot's commit, a freeze inconsistent with its own rows, and a non-CUDA device.
3. Redefine the binding commit, cover the pre-registration in the dirty check, and require the pushed state for the pilot and the freeze.
4. Complete §7: the smoke runs' ids, the debug run's missing record, and the analytic σ result; record world ids in the freeze and gate.
5. Fix the wording for a cap hit and a crashed run, and add a gate start marker.
6. Add tests for the guards.