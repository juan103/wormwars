**Verdict: agree, with one text correction to the plan before the first formal arm.** Every round-1 finding is implemented in the code as described, and I found no defect that needs a code change before the run. The remaining items are a stale pair of seed numbers in the plan's fixed sections, one untested new check, and two overstated sentences.

## Round-1 fixes, checked against the files

- **Dose model** (`scripts/memory_m4/m4e_read.py:118`): returns None for fewer than two U arms with switches, a singular step, a non-finite value, or no convergence in 100 steps. With distinct S2 per U arm, two nonzero arms suffice for the MLE to exist, so the two-arm rule is the right condition. Readings are written at line 369 before the dose model runs. Outside-range counts are recorded. Tests cover `[0,0,0,5]` and `[0,1,0,0]`.
- **Seeds**: blocks 20261301 to 20261499, signs 20261511 to 20261530, reader 20261541 to 20261543, audits 20261601 to 20263509; smokes shifted by 900,000. No family overlaps. Coverage rerun and committed.
- **Tests**: 24 in the file, all passing in `runs/pytest-m4e.txt`. The 3-strain versus 1-strain continuation, the second-pass code check, the seed jump, the audit fallback through `load_counts`, the size sub-field intersection, and the dose model with a slopeless host are all present and sensitive (their sabotages fail by assertion).
- **Validation**: `validate` checks both passes' columns and codes; `check_host_list` requires skipped seeds to equal the full range before the chosen one; `load_hosts` calls `check_skips`, which regenerates each skip in the same `taken` order as `stage_hosts`.
- **Classifier equivalence**: the two new parameters in `pilot.py` default to the frozen path; the before/after script compares R6's planted genomes and 64 host genomes record for record; identical. M2's 14 tests include the one slow-marked test and the log shows 14 passes.
- **Tables and stage 0**: `m4e_tables.py` writes the block summaries with the digest stop and the per-arm AUC. The quoted Spearman values, the 9-of-10 count, the AUCs, the bands and the S3 ranges all match `stage0.json`.
- **Audit**: 40 per panel; about 790 fading per arm; zero flips bounds the per-arm flip rate near 0.38%, just under the 0.4% margin, as Astra's arithmetic requires. The first-pass reading sits beside the main one. The interaction's envelope assigns each arm's unresolved genomes independently, which is correctly the conservative direction.

## Findings, ranked

1. **Two stale seeds in the plan's fixed sections** (`docs/memory/M4E-PLAN.md:116` and `:167`). The genome section says the sign matrix comes from `default_rng(20261311 + 2h + d)` and the readings section says the bootstrap uses `default_rng(20261341)`. Those are draft 1's overlapping seeds. The code uses 20261511 and 20261541, and line 90 of the same plan says so. Since the plan is the pre-run record, fix the two numbers before the first arm. While there, line 86's range ends at 20261499, not 20261498: U_HX has arm index 8 and the last host-draw index is 19.

2. **`check_skips` has no test and no sabotage** (`scripts/memory_m4/m4e.py:142`). It is new behaviour added for Astra's round-1 point, and rule 9 asks for a test first seen failing. The seed-jump test and its sabotage exercise `check_host_list` only. A record with a skip whose seed regenerates fresh should stop `load_hosts`; monkeypatching `m4d.fresh` keeps it fast.

3. **Two sabotages fail through an exception in the sabotaged function, not through the test's check** (`runs/m4e-sabotage.txt:485` and `:523`). "The dose's MLE taken when it does not exist" and "the dose model keeping a host without a slope" both die with `LinAlgError` inside `old_slope`. The plan's sentence "each by its test's own check" is therefore not true for these two. This is the same category as Astra's round-1 signature finding. Have `old_slope` catch the error and return its last β, so the `is None` assertion is what fails.

4. **"The production shape" overstates the batched test** (plan line 252 to 254; `tests/test_memory_m4e.py:278`). The test compares a 3-strain continuation with a 1-strain one. Production continues up to 128 strains. Rule 6 claims exactness only for tested compositions. Either add a 128-strain case (cheap at 60 ticks) or say "three strains". Astra's independent 3, 8 and 128 check is not committed. Either way the second pass is no looser than the frozen path, whose own rerun is a single-strain rerun of a batched probe.

5. **Minor.** The audit's extra cost is nearer 4 to 5 hours than 3 by the two smokes' per-genome slope (about 3 s per audited genome, 32 more per panel, 160 panels); immaterial against the 48-hour cap. `m4e_tables.predictor` reads panel files without `validate`, though the reader validates them.

## On the declined items

Declining the 1% rule is right, and the plan now says why. Keeping two draws over 20 single-draw hosts is a defensible choice given Astra's reason; the plan states the trade. U_HX out by the pre-set rule is correctly recorded and dated.