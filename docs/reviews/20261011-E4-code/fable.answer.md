**Verdict: fix first.** The library code computes the right numbers as far as I can check. The runner, as written, would not give the pre-registration two of the things it must take from the pilot, and the X+ factor ruling makes the P1 numbers likely uninformative. Those fixes are small and should land before GPU time is spent, since the pilot cannot be cheaply repeated.

## 1. Correctness checks you asked for

- **The gate is applied everywhere E-G plays.** Training: `evolve_batch` only ever calls `rollout_fn`, which is `Capture` wrapping `gated_rollout`, and `rollout` builds one `Brain` per chunk and calls `brain_hook` on it (`wormwars/evo/rollout.py:169-172`). Checkpoint plays go through the same `rollout_fn`. Evaluation: `champion`, `assess`, `source_means` and `generation1_load` all go through `gated_brain` or `gated_rollout`. The lineage replay plays nothing. No ungated path.
- **`mean_substitute` is right.** `w` is stored with any Dale sign already baked in (`brain.py:254`, `dense` at `brain.py:305` uses `w` as is), `chem_i` is the source under `pre_to_post`, `index_add_` sums over multiple links into one target, and nothing clamps: `with_params`, `cat`, `select`, `moved` all copy without `clamp_`, and `Brain` reads `genome.bias` directly (`brain.py:331`). Minor: `arms.py:87` hard-codes `chem_i` as the source; under the legacy direction it would be silently wrong. Add a one-line guard on `cfg.chem_direction`.
- **End-state means are not a material difference.** Over H·k substeps the two averages differ by at most 2/(H·k) per source, about 1e-4 at H = 1800. Say so in the pre-registration and move on.
- **The lineage peek is the parent `breed` uses.** Same `randint` shape, device and generator state (`lineage.py:49-52` against `evolve.py:82-86`), and `breed` then consumes the generator identically. Note that `test_the_replay_reproduces_the_final_populations` cannot catch a wrong peek, because `replay`'s `final` does not depend on `peek` at all. `test_the_recovered_parents_are_the_real_ones` does, and D246 says it was seen failing under sabotage. Fine, but say that in the test docstring.
- **Pairing across two batches holds.** Same run seeds give the same `train_ids` and the same `breed_seed`, both batches have the same composition (128 strains × 8 worlds, and 4 × 64 at checkpoints), and `breed` consumes the generator identically whatever the fitness order, so the noise streams stay aligned. One wording point for the pre-registration: after generation 1 the same draws land on different parents, so the pairing is mostly through the mazes. The design's "the noise draws for the shared parameters" overstates it.
- **Sign conventions are right.** d = intact − intervention, positive means cutting hurts; P2 "X+ higher" is `lo > m_hi`.

## 2. Findings

1. **Important, `scripts/e4.py:207`.** The re-evaluation block plays `intact` only. The recruitment band (design §2) is the noise of the *paired* cut effect on resampled mazes, which needs `cut_all` (and `meansub_all`) on the re-evaluation block too, in the same batch shape as the test block. As written the pilot cannot deliver Branch A's band. Fix: play the same condition dict on both blocks.

2. **Important, `scripts/e4.py:267-284`.** Nothing is saved except summaries: no final populations, no checkpoint candidates, no `parents` lists, no `generation0`, and `champion` (`:183-185`) keeps only the 32 validation means, not the per-maze visits. The pilot is the only data the power analysis and the pre-registration get. "Selection noise against W" needs `generation0` (32 identical E-G copies on 8 mazes gives it directly), "against the validation size" needs the per-maze validation visits, and the neutral-drift comparison is better on 4 × 32 final strains than on 4 champions. Save the populations locally as npz and record the rest.

3. **Important, D246 ruling, `scripts/e4.py:84`.** Reject training X+ at 0.5. At σ 0.08 × 0.5 a neutral slot has SD 0.04√n, about 0.3 after 60 lineage mutations, so the P1 effect sizes, maze SDs and recruitment band the pilot exists to measure would be measured at a factor the formal run will almost surely not use. Measure the generation-1 load first (it is minutes), then train X+ at the largest candidate meeting the load bound. If you keep the single-pass runner, train at 1.0.

4. **Important, `wormwars/e4/scale_rule.py:17,39-47` and claim (b).** Your arithmetic is right: reach ≥ 0.5 needs SD ≥ 1.48, so f√n ≥ 18.5, which at n = 100 means f ≥ 1.85 and at n = 300 means f ≥ 1.07. No candidate reaches it at plausible lineage counts, and the fallback picks 0.25, the one factor that guarantees X+ ≈ X0. What the pre-registration should do: make the rule "the largest candidate meeting the load bound", report reach descriptively, and add 2.0 and 4.0 to the candidates the pilot's load measurement covers (`scripts/e4.py:162`; two more populations of 32 on 8 mazes, trivial). Also state how the lineage count transfers to the formal G: the pilot measures the mutated fraction of a lineage at G = 100; count_formal = fraction × G_formal.

5. **Important, `wormwars/e4/stats.py:115-136` and claim (a).** Your claim holds: the design's table misses every case you list. But the proposed precedence keys on P1-cut, while the design names P1-info and P2 as the two confirmatory contrasts. Rows P5 and P8 demote a confirmatory P1-info positive to "reported beside" when P1-cut is not evaluable or inconclusive. Either key the precedence on P1-info with P1-cut as the qualifier, or declare P1-cut confirmatory as well and have the power analysis simulate the three-test table. If three tests gate the reading at 0.025 each, the family-wise rate of "some positive reading" is about 0.07, not 0.05, and the pre-registration must own that. Also D2's "through a constant drive at least in part" is unsupported when P1-info is inconclusive; use "tonic or unresolved" alone there.

6. **Important, `scripts/e4.py:81`.** `checkpoint_every` 25 gives five validation points, too coarse for "whether improvement continues near G". Every 10 costs about 2.5% of training.

7. **Minor, `tests/test_e4_means.py:55-64`.** Passes if the hook saw only the first substep, or only one maze. Assert `acc.count == ticks × substeps × B`, or compare against a hand-computed mean from a recorded short trajectory.

8. **Minor, pre-registration text.** P1-cut's α is not fixed in the design; the code uses 0.025 (`stats.py:26`). "Positive" uses the *larger* margin for P1 (`stats.py:68`) where the design says only "beyond the margin". Both need stating.

9. **Minor, `scripts/e4.py:191,203`.** The means come from a batch-of-one (padded) composition and the conditions play at S = 15, 2 or 1. Exactness across compositions is not claimed, so say in the record that the sham and the band include a composition term. Finding 1 removes most of it. A free CPU test is missing: in one batch, X0's `intact` and `cut_all` must be bitwise equal.

## 3. Tests that could pass with a broken implementation

`test_source_means_on_the_validation_play` (finding 7); `test_mutations_along_a_lineage` (`0 ≤ n ≤ 3`, covered by the unit test, fine); `test_the_conditions_apply_their_edits`'s `not torch.equal(bias)` (covered by the arms test); `test_play_reports_latch_switches` (shapes only, covered by `test_q_flips_counts_sign_changes_per_wey`). The rest fail for the right reasons, and the gate, cut-path and lineage sabotages are real.

## 4. The D246 rulings

- X+ refuses to build without a factor: **accept.**
- P2 "no relevant difference" on the interval alone, even when the exact test rejects: **accept**, provided the record carries p and the exact label beside it, which `_read` does. It is the same rule P1's "equivalent" uses.
- Two batches: **accept**, for the reasons under pairing above.
- X+ at 0.5 in the pilot: **reject**, finding 3.

## 5. The pilot's measurements

Missing: the paired conditions on the re-evaluation block (1), saved populations, parents, `generation0` and per-maze validation visits (2), load at factors 2 and 4 (4), finer checkpoints (6). Nothing recorded is wasted cost: the 8 source bundles, the three trail conditions and the E-G reference together are a fraction of one generation per champion, and the gating check on every condition under shared trails is right.