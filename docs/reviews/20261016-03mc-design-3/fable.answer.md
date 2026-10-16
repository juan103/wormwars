Status: I have read the design v2.1, D287, both JSON records, `power.py`, the check script, `mc.py`, `twin.py`, the tests and my own v2 review. All checks are done; writing the answer now.

**Verdict: ready for the pre-registration.** Every v2 finding is fixed without a new error that I could find, and every number the design quotes from `equivalence-check.json` and `power.json` is in those files. The findings below are small text and code items to take into the pre-registration and its code review, not reasons to revise the design again.

## 1. The v2 findings, checked against v2.1

| v2 finding (mine) | Status | Evidence |
|---|---|---|
| 1 tick-30 share tolerance unmeasured | Fixed | `p4mc_equivalence.py:143,161` computes the aggregate share against `decay.json`; worst 4.07e-7 at SH-10000 (`equivalence-check.json:1179-1182`); 1e-5 is 24.6× ("25 times", `DESIGN.md:350`) |
| 2 tick comparison uncommitted | Fixed, and the claim withdrawn | `power.py:212-216`; `power.json:174-195`: 0.6798, 0.8306, 0.8464, 0.8482, 0.7796 match §6's 0.68/0.83/0.85/0.85/0.78 |
| 3 settling labels in prose only | Fixed | `p4mc_equivalence.py:69-74,162-166`; labels and counts per graph for all 24; `LABELS = 2` at line 48; the counts 26/171/37 are in `label_counts.both` for N2, SH-10007, SH-mirror-40003 |
| 4 "at least 4.5×" wrong for the hold range | Fixed | tolerance 3e-4 (`TOL`, line 46); worst 2.66e-5 → 11.3× ("11 times", `DESIGN.md:354`) |
| 5 Q-D fail wording | Fixed | `DESIGN.md:269-270` |
| 6 Q-C assumed | Fixed, modelled | `power.py:154,185-187`: normal fitted to the 64 paired permutations' log denominators (−3.72, 0.28), posterior draws, rank against N2's drawn response |
| 7 no pre-tanh reference test | Fixed | `test_exp03_twin.py:113-138`: a one-row sequential reference, both terms at 1e-5; the script's `one_row_pre` is the same computation on the GPU (`p4mc_equivalence.py:78-95`) |
| 8 controls: conjunction vs Holm, PVP tie, batch 0 | Fixed | `DESIGN.md:194-213`; the exclusion set in `test_exp03_mc.py:100` matches `configs/interface.yaml:60-61` (SMDD, RMDD, SMDV, RMDV) |
| 9 dirty-tree disclosure | Fixed | `DESIGN.md:62-65` |
| `twin.history` lacked `@counted` | Fixed | `twin.py:38` |

Astra's v2 findings, as far as they touch the files: joint draws (`power.py:129-134,160-164`; the pooled error has variance cov/k, I checked the algebra at line 163-164), Q-A's coefficient and variance posterior (`167-168`), the t₅ sensitivity at the same SD (`104-107`), Q-D's prior named (`DESIGN.md:411-412`), "model-based predictive" wording (`DESIGN.md:400-401`), the worst settling graph renamed and included (`EXTRA`, line 52). All present.

## 2. The quoted numbers

Every figure in §5's table and §6's table traces to the two files. Checked: 2.0e-7, 7.2e-6, 4.3e-6, 2.2e-5, 1.3e-4, 1.1e-6, 2.7e-5, 7.6e-7, 4.6e-8, 0.33 (`equivalence.json:1259-1281`); 4.1e-7, 3.9e-6, 4.8e-6, 2.1e-7, 0/0/0 (`equivalence-check.json` "worst"); 0.24 GPU-hours (864 s, line 1202); the Holm table and the "all four" rows (`power.json:110-151`); 0.60 at 16 384 (line 162); the fixed sequence 0.83/0.64 (lines 127-128); the correlations 0.45 and 0.38 (lines 47, 33); the slope −0.26 ± 0.03 (lines 54-55); AIY's SE 0.012 (line 27). The 49×, 25×, 47×, 11× and 15× margins recompute correctly.

## Findings

1. **The formal pre-run check will overwrite the committed file the design quotes.** `scripts/p4mc_equivalence.py:116-117` writes `experiments/03mc-p4-confirm/equivalence-check.json` for every non-smoke `--set check` run. The design says the formal check reruns at the bound commit (`DESIGN.md:65`) and that no exact repeat is claimed (`DESIGN.md:368-370`), so the rerun will replace the numbers §5 cites with slightly different ones, and the stamp with a clean one. Rule 5. Fix: a `--out` argument or a fixed second name (for example `prerun-check.json`) for the formal run, and keep the design-time file untouched; say in the pre-registration which file is which.

2. **The reference arrays of the pre-run check are local and unhashed in its record.** The check compares against `runs/p4m/*-per-genome.npz` (`p4mc_equivalence.py:121-122`), which are not committed. `power.json` records their sha256 (`local_arrays_sha256`); `equivalence-check.json` does not. A reader cannot tell that the formal check used the same references as the design-time run. Fix: add the four arrays' sha256 to the stamp, and assert they equal the hashes in `power.json` for the three it shares.

3. **A non-finite N2 value passes `rank_p`.** `mc.py:26`: with `n2 = nan`, both comparisons are False, r = 0, p = 1/(n + 1): a pass. The design withholds the question when N2 is invalid (`DESIGN.md:129,255-256`), so the runner must guard; the function and its tests do not. Fix: return p = 1 (or raise) for a non-finite `n2`, with a test. Same class: `paired_bootstrap` does not apply the floor to the full-sample estimate (`mc.py:72-75`), only to resamples.

4. **The check set's third extra graph is justified by neither stated reason.** `p4mc_equivalence.py:50-52` and D287 say the extras are "the three worst or busiest settling graphs". SH-recip-50015 is neither: its end-range deviation is 0.030 (`equivalence.json:1223`; SH-10005 at 0.181 and SH-10014 at 0.168 are worse) and it has 0 settled-with-separation genomes (`equivalence-check.json:1079-1082`). It is a leftover of v2's misnaming. The design lists it without a reason (`DESIGN.md:322`). Not harmful, but the pre-registration should either give the true reason ("kept from v2") or swap it for SH-10005.

5. **"Within simulation error (about ±0.01)" overstates the tie across ticks 20-40.** `DESIGN.md:260-261,436`. At 5 000 studies the SE of each proportion is about 0.005, so tick 20 (0.8306) sits about two SE of a difference below ticks 30 and 40 (0.8464, 0.8482), which are tied. The withdrawn claim stays withdrawn and the choice of tick 30 does not depend on this, but say "30 and 40 are tied; 20 is marginally lower".

6. **"At least 4.5 times" is 4.47.** `DESIGN.md:353`: the worst per-genome tick-30 deviation is 2.235e-5 (`equivalence.json:1263`), so 1e-4 is 4.47×. Write "about 4.5" or "4.4".

7. **"v2's independent model gave 0.01 at 2 048" has no file at HEAD.** `DESIGN.md:428-429`. The current `power.json` has no 2 048-genome row. Cite the commit whose `power.json` holds it (1673ad5) or drop the parenthesis.

8. **The audit's permutation check depends on the caller, and the test does not plant that case.** `mc.py:132-137` puts 03r's `_gseed + 2` in the genome-seed set, but in 03r it is a permutation seed (`scripts/exp03.py:126-130,484`), used through `2 × seed + type`. The collision the design promises (`DESIGN.md:105-106`) is only found if the caller passes every 03r `_gseed(name) + 2` in `old_perm_seeds`; `test_exp03_mc.py:104-117` plants only a literal 1000. Fix for the build command: pass them, and plant one as a sabotage test. The probability of a real collision is about 1e-4, so this is a completeness item.

## What I could not check

I had no shell, so I ran nothing: not the tests, not `power.py`, not the git diff. The matched-control list and degrees rest on the test's assertion and on my v2 check from `lesions.json`. The claim that the plus/minus swap sabotage was caught (D287) is unverified. The 100 s versus 22 s timings in §5 have no committed record. §0's 03m figures were verified by both reviewers in D286 and I did not redo them.