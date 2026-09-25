**Bottom line:** the verdict machinery is now right and tested; every point that could change a verdict is FIXED. Three things the revision introduced are not verdict-changing but will bite at run or report time, and all three are cheap. NO-GO for one small commit, then GO.

## 1. Point by point

| # | Point | Status | Where / why |
|---|---|---|---|
| 1 | Validity mask everywhere, N2-invalid withholds, counts | FIXED | `report.py:47-51` one `valid` per signal; `:126-129` every list filtered; `:129` N2 invalid withholds; tests `test_exp03_report_rules.py:41-55` |
| 2 | Completeness enforced, Holm divisor | FIXED | `report.py:129,147-149,154-156`; withheld enters `iut_holm` as p = 1; test `:57` |
| 3 | Calibration validation | FIXED | `exp03.py:211-216`, 2 048 genomes seed 1; achieved drive saved via `calibration.py:231` |
| 4 | Magnitude variants unpaired | FIXED | §4 wording matches `exp03.py:260-266` |
| 5 | Bootstrap sizes/seeds | FIXED | `report.py:28`; `--boot` removed from `main`; §6 |
| 6 | World profile without N2 | FIXED | `report.py:114-115`; test `:63` |
| 7 | N2 last, exempt from cap | FIXED | `exp03.py:469-475,500`; test `test_exp03_runner.py:25` |
| 8 | Calibration-failure rule | PARTLY | §4 registers "excluded and counted"; no code does it. `calibrate_in_world` raises a bare RuntimeError (`calibration.py:252`), `cmd_run` `:496-505` has no handler, so the run halts, and a restart hits the same deterministic failure. No stub is written, so the report cannot count it. |
| 9 | Manifest check at load | FIXED | `exp03.py:189-192`; test `:31`. Manifest generator still not committed (minor). |
| 10 | Within-ensemble pairwise Jaccard | PARTLY | Numbers in §3 and D054; no committed code computes them (grep finds none). Minor. |
| 11 | Secondary signals implemented | FIXED | `report.py:85-102,177-185`; test `:73` |
| 12, 13 | Two-direction rate; margin truncation | FIXED | §6 |
| 14 | P(consistent) added | PARTLY | Added (`exp03.py:434`, §7), but see new problem B: the number is wrong for P1 and P4. |
| 15-19 | P4 ratio units, expected z, min z across five, 150 GPU-h, score scale | FIXED | §7 |
| Q2 | Null = topology plus weight placement | FIXED | §2 |

## 2. New problems the fixes introduced

None changes a verdict. Three matter operationally:

- **A. `cmd_report` crashes.** `scripts/exp03.py:521` prints `complete`, which is not defined in that function. `report.json` is written on line 520, then NameError. Fixing it after the run is a code change past the binding commit.
- **B. The power simulation's "true member" has no latent scatter.** `exp03.py:428` draws N2 as `z*tau + N(0, se)`, so at z = 0 N2 sits at the exact ensemble mean. A member should be `N(0, tau) + N(0, se)`. Analytically per ensemble: P1 about 0.68 (table says 0.93), P4 about 0.87 (table says 1.00), P3 about 0.30 per ensemble and lower across five (table's 0.15 is coincidentally close). §7's "consistent if a member" column overstates P1 and P4; the P3 conclusion stands.
- **C. §8's provenance rule makes §9 unexecutable.** `check_provenance` (`exp03.py:83-87`) refuses any mixture of commits, so "completed graphs are kept only if the bug provably did not touch them" cannot happen: any mid-run code fix forces a full re-measure or an override. Combined with point 8, the one foreseeable mid-run failure (a calibration that does not converge on one of 512 never-calibrated SH-route/class/mirror/recip graphs) would cost either the whole run or a deviation.
- **D. Verify the §3 hashes match what the run records.** `.gitattributes` has `* text=auto`, and ripgrep finds CR bytes in the working-tree `ensembles.json`, `pilot.json`, and `graphs_manifest.json`. If those blobs are LF-normalized, `_sha` (`exp03.py:64-66`) of working-tree bytes will differ from "sha256 of the committed blob" in §3. I could not compute hashes (no shell). Run `provenance("cpu")` once and compare. Also, the dirty check at `:75` covers `wormwars`, `scripts`, `configs` only, so an uncommitted edit to `pilot.json` would run (recorded but not refused).

## 3. Verdict

**NO-GO now; GO after one commit.** Minimum change, all before the first measurement:

1. `scripts/exp03.py:521`: print `out["counts"]` (or delete the line).
2. Implement point 8: in `cmd_run`, catch the calibration RuntimeError from `measure_graph`, write a stub `{"name", "calibration_failed", "seconds", "provenance"}` and continue. In `report.build`, drop names whose measures carry `calibration_failed` from `use` at `report.py:111`. The existing logic at `:126-129` then lists them in `exclusions`, counts them, and withholds if it is N2. One test each.
3. `exp03.py:428`: at z = 0 draw N2's latent value from `N(0, tau)`; rerun `power`; update §7's last column and, since `pilot.json` changes, its hash in §3.

Recommended in the same commit: state in §9 that any other mid-run code change re-measures every graph (which is what the provenance rule enforces), and normalize line endings in `_sha` so §3 is checkable against the recorded provenance.