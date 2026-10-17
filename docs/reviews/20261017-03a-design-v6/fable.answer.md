**Verdict: ready for the pre-registration, with small fixes.** One item is medium and should be fixed in the pre-registration text and in family 2's simulated-null validation: the pooled imprinting test treats targets as independent, but the same five MIP brains serve every target. Everything else is low severity or a wording fix. The owner's decision (D305) is described accurately in §2, §8 criterion 8, §11 and the roadmap annotation.

## 1. Round-2 findings

My nine (fable.answer.md, v5 round):

1. Slow-memory calibrator: **resolved.** KTS was run (D304, `slow-memory-check.json`) and T = 5, 10, 20 are the probe's calibrators (`DESIGN.md:319-320`).
2. Undefined steady state: **resolved** by replacing the probe with the replay design (`DESIGN.md:312-321`). I checked that the brain is deterministic and starts from zeros (`wormwars/brain.py:431-434`, no noise in `step`), so "canonical initial state" and the full-replay control are well defined. Small fix in finding 3 below.
3. Family 2 power: **resolved.** The pooled test is registered, the per-target contrasts are descriptive with the 12-of-252 limit stated (`DESIGN.md:283-286`). A new dependence issue is finding 1 below.
4. "Kind" versus connection type: **resolved** (`DESIGN.md:48-50`).
5. One unlucky evolution: **resolved.** One re-evolution per graph for criterion 1, two budgeted (`DESIGN.md:353-354, 400`).
6. "Requires memory": **resolved** (`DESIGN.md:87`; the roadmap annotated by the owner, `ROADMAP.md:568`).
7. Stratified null specifications: **resolved** (`DESIGN.md:219-229`). One factual error remains, finding 4.
8. Criterion 1 as a gate: **resolved.** Re-measured, not re-tuned, not a gate (`DESIGN.md:368-369`).
9. Small points: **resolved.** The exploratory row names the estimated component; the no-task control runs on all five MIP brains.

Astra's round-2 findings, as far as they bear on mine: 2 (memory claim) resolved by wording plus the owner's choice; 3 (history ablation) resolved, the replay design was adopted; 4 (family 2) resolved except finding 1 below, the four-brain cut is gone; 5 (degree claim) resolved and narrowed (`DESIGN.md:51-54`); 6 (tiers, gate) resolved; 7 (resolution) resolved; 8 (frozen protocol, no-task path) resolved; 9 and 10 (numbers, budget) resolved, see §2 below.

## 2. Numbers checked

§2 table, against `slow-memory-check.json` (I read every KTS row myself):

| Row | Record | Design |
|---|---|---|
| KTM (T = 1) | 2.842 / 0.514 / 0.041 | 2.84 / 0.51 / 0.04 |
| T = 2 | 2.619 / 1.762 / 0.629 | 2.62 / 1.76 / 0.63 |
| T = 5 | 2.688 / 2.463 / 1.557 | 2.69 / 2.46 / 1.56 |
| T = 10 | 2.178 / 2.129 / 1.627 | 2.18 / 2.13 / 1.63 |
| T = 20 | 1.578 / 1.688 / 1.592 | 1.58 / 1.69 / 1.59 |
| T = 50 (omitted from the table) | 1.174 / 1.174 / 1.182 | reported only in D304 |

The 1.64 gap is 2.842 − 1.199. "Loses a quarter or more at r = 2" holds: T = 10 loses 25.3 percent, just inside the claim. The KT jitter values and the champion medians I did not re-reduce this round; they match Astra's round-2 recomputation from `jitter-check.json`. The "SEs 0.02-0.05" is slightly off: KTM at r = 2 has SE 0.009.

Compute: `compute.json` totals 1 668.5 seconds = 0.4635 hours and 2 330 112 worlds. The increment over the round-2 ledger is exactly 258 048 worlds = 6 × 162 × 256 tuning plus 6 × 3 × 512 check, so the slow-memory run is fully recorded. 0.46 + 0.07 = 0.53.

§10, every row recomputed at 420/s: 57 600 and 0.038 h; 748 800 and 0.50 h; 44.93 M and 29.71 h; 38 × 266 496 = 10.13 M and 6.70 h (41 checkpoints including generation 0 agrees with `evolve.py:198`); evaluations 1.79-1.80 M with 30 restorations and 8 intact scores; scan plus check 0.396 M; pilot-dev 9.07 M = 6.00 h; pilot-check I get 16.76 M against 16.73 M, within the rounding of what is itemised; totals 84.2 M and 56.2 h; reserve 15.8 h; wide-batch about 24 h; the 32-world option about 94 h at 420/s, so correctly excluded. One small count: the probes row assumes 12 episode-equivalents, but constant scent, two jitters, hold, a ramp with two phases and four L values counted double make 13 or 14. That adds about 0.1 h.

## 3. New findings

1. **Family 2's permutation null ignores the shared MIP brains. Medium.** `DESIGN.md:271-277` with `DESIGN.md:123`. The five MIP brains are the same brains for every target; the NIP brains are five fresh brains per target. Permuting arm labels independently across targets assumes a MIP brain's AUCs on different targets are not correlated through the brain. If a brain effect exists (a brain with more headroom or a more X-dependent solution scoring higher on all targets), the pooled statistic's true null variance exceeds the permutation variance and the test is anti-conservative. The planned validation (`DESIGN.md:281-282`) simulates unequal variances but not this. Fix: add a scenario with a shared MIP-brain random effect across targets (say intraclass correlation 0.3 and 0.5) to the simulated-null validation, report the rejection rate, state the exchangeability assumption in §7, and pre-specify a fallback if the rate exceeds a declared bound (for example a brain-level statistic, each MIP brain's mean AUC over the common set against the NIP target means, or family 2 reported as descriptive). Family 1 is unaffected: its null permutes anatomy with the brains fixed, and Holm tolerates dependence.

2. **The replay probe measures dependence on inputs older than L ticks, not "memory" in any stronger sense. Low.** `DESIGN.md:312-317`. Neuron time constants run to 20 ticks (`wormwars/config.py:37`), so a brain with slow neurons will lose at L = 5-20 by filtering alone, and that is exactly what the KTS calibrators also do. The design should say so where it names "history use" (§2, §7), and report each brain's τ distribution beside the probe. Two specifications are missing: KTM's expected result is "unaffected at every tested L" (L ≥ 5 exceeds its one tick), yet only KT is said to "must be unaffected" (`DESIGN.md:319`); and the full-replay control "exactly" (`DESIGN.md:317`) is bitwise only on CPU or on CUDA within one batch composition (rule 6), so say which.

3. **"No neuron is both" is false. Low, factual.** `DESIGN.md:220-221`. MCL and MCR are pharyngeal neurons and mapped pump motors (`configs/interface.yaml:62-63`). The "or otherwise" ordering already resolves them as "motor", so the null is unaffected, but the sentence must be corrected, and the design should say that the pump motors stay "motor" though the pump is inert with energy off, parallel to the unsignalled sensors.

4. **Pilot criterion 3 is marginal and scales with the pilot graph's score. Low.** `DESIGN.md:359` with `DESIGN.md:243-246`. From the committed mono counts the per-episode SD is about 0.78, so a paired 2 048-world comparison has a 95 percent half-width near 0.04-0.05, against p/2 ≈ 0.055 at an intact score of 2.2. On an SH-mirror graph whose brain scores lower, p shrinks and the gate can fail for a reason N2 would not share. State that criterion 3 is judged at the pilot graph's own p and report the same quantity projected at the N2 selector brains' p, so a narrow fail is read correctly.

5. **The §1 limits do not yet carry the consequence of D305. Low.** `DESIGN.md:37-57`. Since history use is measured and not required, a null anatomy or imprinting result cannot be separated from "the brains use little history on this task". One sentence in the limits saying every reading is conditional on whatever history use the probe reports would complete the owner's choice. The roadmap annotation and §2 are otherwise accurate.

6. **Small budget and table points. Low.** Put the 2.33 M exploratory worlds in the Episodes column, or footnote that the 84.2 M total excludes them (`DESIGN.md:391, 402`); 245 in §4 against 246 in §10; add the T = 50 row to the §2 table since D304 reports it; SEs "0.01-0.05".

7. **Tier order, stratified null, cut order: no new problems.** Sequential selection without replacement and the fallbacks are complete (`DESIGN.md:153-161`). The null's within-kind tertiles, tie rule, small-stratum merge and shared identity permutation are specified; the reported permutation count will show where strata of mapped motors (18 neurons) and sensors (21) are near identity. The cut order is right; note only that cutting free searches 5 → 4 changes the ranking statistic and the no-task control's input, which the frozen protocol must restate (`DESIGN.md:405-406`).