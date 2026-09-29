**Verdict: revise.** Most v1 must-fixes are fixed in the code, but two are only partly fixed, v2 adds three bugs, and four Q1 sentences do not match the files. None needs GPU time to fix. I ran nothing; everything is from reading the code, the committed JSON and the smoke outputs.

## v1 must-fixes, checked in the code

| v1 must-fix | Status | Evidence |
|---|---|---|
| 1. "highest P4" | Fixed | `PLAN.md:45`; `tradeoff.json` has one graph at or above N2 in each instance |
| 2. Ranges | Fixed | 4.70–7.09 and 1.55–2.69 in `tradeoff.json` |
| 3. Estimate, cap, partial writes, record | **Partly** | Cap checked before every batch in all four commands. Estimate, partial writes and the record have gaps (M2, M5). |
| 4. Composition, empty deletion | **Partly** | `per_chunk` 2048, other values refused, recorded. The check runs too late (M3). |
| 5. By-type seeds | Fixed | Seeds 100–107; `Genome.random` draws signs, tau and bias in the same order in every magnitude mode, so the pairing holds |
| 6. Per-genome arrays | **Partly** | Kept for lesions and decay only (M4) |

Astra's items (invalid never placed, smoke on CPU, formal size, three classes, paired Q5) are in the code. The invalid case has a test.

## Must-fix: code

- **M1. `cmd_tails` pools all 640 graphs under "SH"** (`p4m.py:244`). `startswith("SH-")` also matches `SH-route-…` and the rest. `tails.json` shows `"SH": {"graphs": 640}`, and its maximum equals SH-recip's to every digit. Use the filter in `ensemble_rows`, add a test, regenerate.
- **M2. `compute-record.json` omits the command that writes it** (`p4m.py:172-178`). `finish()` aggregates inside `main`, but the accounting writes the attempt file only when `main` returns. The committed record would lack lesions, the largest command. Copy it after `run_script` returns.
- **M3. The empty-deletion check runs after all ~386 deletions** (`p4m.py:353-356`). A failure is found after about 1.4 GPU-hours. Check it after the first batch.
- **M4. Per-genome arrays.**
  - Synapses and weights still discard them (`p4m.py:398, 407, 559`). Q5's question of whether permutations keep the persistent minority needs them.
  - The lesions `.npz` is written only after the follow-up (`p4m.py:367`), so a cap hit in the last command loses it.
- **M5. The estimate is stale; I project about 3.5 h, not 2.9.**

  | Item | Hours |
  |---|---|
  | Lesions (386 histories) | 1.36 |
  | Decay (81 graphs × 820/230 ticks) | 1.02 |
  | Gaps-off on the 81 panel graphs, new in v2 | 0.29 |
  | Weights (128 histories) | 0.45 |
  | Synapses and gates | 0.08 |
  | Rebuilding about 70 graphs on the CPU, inside the cap clock | about 0.3 |

  - The rebuild figure comes from smoke: decay took 177 s with 10 graphs rebuilt and 21 s without. This worktree holds only those 10 graph files.
  - At the pilot's slowest timing (13.9 s) the total is about 3.8 h against the 4 h cap.
  - Fix: rebuild the graphs beforehand, correct the estimate, and run the pre-named targets first in lesions. Pairs run last today, so a cap hit loses RIA and AIZ first.
  - Weights writes no partial file, against the plan's text.

## Must-fix: Q1 text

- **M6. Split-half "0.94 to 0.99".** The file gives 0.943 to 0.985, and SH's value is the pooled one from M1.
- **M7. The heavy-tail sentence is one-sided.**
  - N2's 40% is compared with medians only. The ensemble maxima are 0.31 to 0.44, and one SH-recip graph (0.435) exceeds N2. Give N2's rank in each ensemble.
  - "About 19%" is the numerator's share; the file has no null figure for the denominator.
  - The two top-5% sets are sorted separately, so the sentence implies the same genomes without computing the overlap.
- **M8. The log-log slope is not a separate arithmetic component.** The slope of log P4 on log response is exactly that slope minus 1, so it restates the association. "Without any dynamical trade-off" does not follow. The ratio creates a spurious correlation only through noise in the denominator, which the reliability and `common_turn_M0` checks address.
- **M9. The routing sentence holds in 03 only, and the error was mine in v1.** In 03r, SH-class (−0.36) is weaker than SH-mirror (−0.45).

The other Q1 numbers match `tradeoff.json`. `common_turn_M0` is more negative than the denominator's correlation in all ten runs, which supports the reading. It is measured on the same 2 048 genomes, so say so.

## Suggestions

- **Q2 thresholds are asymmetric.** The pooled 95th percentile of P4 is about 0.89 (by my count of the supplement) and the pooled maximum response is 0.0732. "P4 only" needs a drop of 0.04; the response classes need a 43% drop. Record the thresholds and each deletion's change from intact.
- **The hold-settling check cannot discriminate.** It is 0.0 for all 11 smoke graphs, because 100 ticks is 5 of `tau_max`. Record the read-out's change over the window instead.
- **End settling** compares two endpoints, over 11 ticks, not 10 (`p4m.py:445`). Save `end_change` per genome.
- **Q3's reading rule** does not define "change", and chemical-off has no matched null. It was invalid in smoke.
- **The follow-up's five lowest P4** may pick deletions near the denominator floor; require a minimum response.
- **The formal gate has never run at 2 048 on the GPU.** `p4_of` averages float32, while 03's supplement averaged float64; cast to be safe.
- **Provenance.** Both Q1 files are stamped `4c8848e`, dirty. Regenerate at a clean commit, refuse a dirty tree in formal runs, and push before running.
- **Cross-half check.** Correlate P4 from even genomes with the response from odd genomes.
- **Tests.** None covers `cmd_tails`, `decay_summary` or the cap. I cannot verify rule 9 by reading.

**03m plan: revise**