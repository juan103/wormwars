# Confirmation review: T1 after D091, and the 03 signals text

I ran nothing: no Python and no git commands were available, so tests were not run. I read the files, the reflogs and the reference worktree, which is still on disk at `D:/Claude/random/wormWars-t1-ref`.

## 1. My earlier points

Resolved correctly:
- **Thresholds:** replaced by tested shapes (`T1.md:469-482`).
- **Post hoc label and 1-row probes:** both stated (`T1.md:497-503`).
- **Evidence now committed:** raw `bmm`, the chunk-3 rerun, 153 of 512, and the CPU's 1.2e-7.
- **Declared items:** starting food, 02's probes, a CPU leg, and the 64/128/256 chunkings are all done.
- **Documents:** the REPRODUCIBILITY and T0 corrections are in, dated and quoting what was wrong.
- **Code defects:** all seven are fixed.

Not resolved:
- **Compute records are still uncommitted.** `.gitignore:70-72` ignores them, and the index holds no `runs/t1-*` path. The 6.9 h at `T1.md:538` does add up (24 930 s), but only from local records in three working trees.
- **The amendment is not beside §3.** `T1.md:109-149` carries no dated pointer to §7.

## 2. Evidence against the committed files

Every count matches: 268/158/102-of-110 on CUDA, 250/146/104 on CPU, 47 of 110 before the change, 388 and 468 replays, 22 strains, and 0.95-1.01 for padding's cost. Identical reference hashes across modes back "same outputs".

Still overclaimed or untraceable:

| Where | Problem |
|---|---|
| `T1.md:543-545`, `:494-495` | "At 16 rows and at 1 row … (8 of 110)" is wrong. Only 6 of the 8 are there. The other 2 are `eaten` at 160 rows and at 20 rows (`compare-cuda.json:3066-3071`, `:3108-3113`). |
| `T1.md:462-467` | `eaten` at 1 world is not explained by a committed file. `eaten_cause` ran at 8 worlds only (`T1_diagnostics.json:453`), and `world_reduction` at 1 world shows no difference (`:399-403`). |
| `REPRODUCIBILITY.md:54-57`, `T0.md:248-249` | "2-15 worlds" is a range drawn through 2, 4, 8, 12 and 15, from one random field with 1-2 unequal values each. It also excludes the 1-world difference actually observed. |
| `T1.md:441` | "CPU (reduced sizes)" understates. The leg ran `--quick`: 20-tick rollouts, 30 for the stress test and proxy (`t1_equivalence.py:137, 159, 176`). The "T1-600" key is a 30-tick run. |
| `T1.md:497-499`, `REPRODUCIBILITY.md:63-65` | Brain states "equal at 16 rows" holds against a batch of 4 only. They were equal there before padding too, and raw `bmm` shows 2 and 4 strains both differ from 32. |
| `REPRODUCIBILITY.md:31-33` | "None at 16" was measured against a batch of 4 (`T0_gpu.json:499-503`). It now reads as contradicting `:51-52`. |
| `T1.md:422-423` | "Merged under measure" is true of HEAD's code, not of the reported runs. Their replay children counted under "other" (local `compute.json`, `uncategorised: true`). |

## 3. Code

No defect found in `brain.py:397-403`, `genomes.py:223-226`, `rollout.py` or `accounting.py:186-202`. The legacy-layout test can fail, as it should.

Minor:
- **Vacuous guard:** `t1_equivalence.py:236-241` builds `alone` with the same conditions as `pairs`, so `missing` is always empty. The test at `test_t1_equivalence_script.py:61-64` is named "refused" but tests a successful pairing.
- **No key-set check:** `compare()` (`:265-276`) iterates the reference's keys, so outputs present only in the new run are skipped silently.
- **Stale docstrings:** `t1_equivalence.py:18-22` lists the old shapes; `t1_diagnostics.py:1, 6` cite §6.
- **Silent override:** a padding mismatch is overridden quietly, while a direction mismatch raises. Defensible, but worth a warning.
- **Timing order:** `padding_cost` always times off before on.

## 4. The reference engine `ffeb541`

Honest, as far as I can check.
- **The worktree's engine is pre-change:** its `brain.py` has no padding, and the switch appears nowhere outside the script and a comment.
- **It computes the same numbers as pure `1598d56`:** the sensitivity values agree to every printed digit in both modes (`T1_equivalence_reference.json:1404-1408` against `v2_reference-cuda.json:2260-2265`, and four more cases).
- **An independent anchor exists:** the published replay ties the switch-off engine to 02's stored scores without any reference.

Not verified: byte identity of the engine files with `1598d56`, and that `wormwars/` is unchanged between `3c12e7c` and HEAD. `accounting.py` also carries `neural_padding`, which §7 does not mention.

## 5. Decisions

- **Padding as a mitigation:** confirm.
- **Contract amendment:** confirm, with a dated pointer under §3.
- **E1 guidance:** confirm, with one addition. Direct-step probes run at 1 row, where every tested strain count differs from 32. So fix and record the strains per batch for probes, and never compare across batch sizes as exact.
- **Closure text:** change it before adopting, since it cannot be edited afterwards. Suggested first sentence:

> T1.2's class E test failed as declared: 8 of 110 single-strain outputs differ from their batch. These are score and energy at 16 rows per strain, brain states at 1 row (four variants), and the reported `eaten` sum at 02-T1 on 8 worlds and on 1 world.

## 6. The signals text

Every number is accurate, and the P1, P3 and P4 procedures match the code (`measures.py:92-121`, `probes.py:85-138`). Five statements need fixing:

| Where | Problem |
|---|---|
| 03 `README.md:134-136` | "Already lean that way" conflicts with `RESULTS.md:285-290`: the comparison "does not show that N2 is born where selection took the champions", and shuffles' random brains sit at 0.75-0.84 too. |
| 03 `README.md:72-74`, main `README.md:62-63` | "Still mostly 'in' its past state" over-reads a ratio of mean absolute values. It presumes slow relaxation, which `RESULTS.md:271-276` says cannot be told apart from other readings. |
| 03 `README.md:128-131` | Lists candidate mechanisms that are not in the record, and omits RESULTS' readings: hysteresis, nonlinear saturation and the finite warm-up. |
| 03 `README.md:53-56` | The table shows "Final tick" as separate from ticks 101-110. The final tick is tick 110, the ramp's last step. |
| 03 `README.md:96-98` | "More than it simply reacts" is literally true only above 1. Say "strongly, relative to". |

Optional: `:117` could say "registered secondary label".

**T1: not yet** — documentation only, and no rerun or further review round is needed if these are applied: (1) correct the amendment's and `T1.md:494-495`'s account of the 8 failures; (2) run `eaten_cause` at 1 world or mark that case as inferred, and replace "2-15" with the tested counts; (3) commit a compute summary and say the reported runs' child counts are under "other"; (4) state that the CPU leg ran in quick mode with 20-30 ticks.

**Signals text: fix** — the 02b link, "still mostly in its past state" (both READMEs), the mechanism bullet, the timeline table, and the P1 "more than" wording.