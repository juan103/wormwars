**Verdict: revise, narrowly.** Three required changes, all wording or disclosure. None touches the design, the margins, the code's logic or `power.json`'s numbers. After them, bind on a diff check.

What I checked: draft 3 line by line against both draft-2 reviews, `e3c_stats.py` and its tests, `e3c_power.py` and its tests, every §8 figure against `power.json` by reading the cited scenario blocks, D207's correction and D208, `train-tf.json`'s per-generation hashes and the `configs/` path. I had no shell, so I ran no tests and computed no sha256. Astra verified the hashes and the 3.946 hours at draft 2 and nothing there changed.

**1. Draft 2's required changes.** All taken.
- Mine: the `g-e` gate is at `PREREGISTRATION.md:166-170`, with the mismatch stop and the P-joint amendment. The undefined case in any arm is at lines 365-370, `e3c_stats.py:179-188`, and `test_e3c_stats.py:186-191` with Astra's counterexample. The blind spots are at lines 290-295, with the 8% figure, which I confirm as P(N(2.3, 0.3²) > 2.72) = 0.081.
- Astra's: Welch labels all approximate at lines 253-258 and `e3c_stats.py:153`; draft 2's observed-failure rule withdrawn at line 257. The counter counts every false assertion, `e3c_power.py:166-180`, and the sabotage claim at line 565 holds: draft 2's counter fails `test_e3c_power.py:56`. Joint coverage at `e3c_power.py:199,207`; analytic means at 160-163; the component-mean wording at line 405; the pooled and per-arm bounds at lines 466-470, which I confirm as 0.393 and 0.632. The execution contract: cut compositions at lines 172, 175, 179; the 256-maze benchmark at line 141 and §9; learning references at 188-189; eligibility per reading at 199-211; trails-off scope at 195-196; bootstrap level at 300-301; no-data cases at 288-289, 331-332, 209; 21 checkpoints at 173 and 503. §15 and D207 carry dated corrections.
- Every optional item from both reviews is taken too, including the engine-freeze check at line 582 and the fixed test docstring. §5's `best_sha256` lookup is executable: `train-tf.json` has 2 400 entries, 8 runs × 300 generations.

## The exact test

**Null, claim and code are sound for what they say.** `permutation_p` is a valid exact test: the observed split counts toward p, ties count via ≥ with a 1e-12 slack, which is the conservative side, and |diff| is permutation-invariant, so it stays valid at 8 against 6 where the split distribution is not symmetric. Bonferroni at 0.025 holds under any dependence, and the floor guard can only remove rejections, so the level survives it. The discreteness is harmless: the smallest p is 2/12 870, or 2/924 at 6 against 6. The vectorized copy is tested against the registered one at `test_e3c_power.py:64-70`.

**What is overstated: Q2's confirmatory status.** Under the prereg's own model, S-mod's d spread is 0.012 and P-joint's is 0.177, the 15× at line 419. So Q2's exchangeability null is expected to be false before any data, on spread alone. A Q2 rejection then adds nothing by its registered claim, and what it will be read as, a mean difference, has no 0.025 guarantee. `power.json` shows the rate at equal means: 0.042 at line 1150, 0.045 at line 1600, 0.051 at line 10094, all with the same Q2 arms; and 0.09-0.10 under the failure model at lines 4277, 7902 and 19108. Lines 245-251 disclose the mechanism but not that the null is pre-refuted for Q2. This also bears on D208's "0.76 against Welch's 0.64": that is not like for like, since the exact test rejects at 0.042 where Welch rejects at 0.024, line 1141.

**"X higher."** Valid as a sample description, as line 248 defines it. But the label text will be read as a population claim. At equal population means with S-mod failing at 1/8, lines 7858-7872, the published label would say "modular higher" in a third of trials. One word fixes it.

## §8 against power.json

Every figure matches, with one incomplete sentence.

| §8 claim | `power.json` |
|---|---|
| Identical-distribution false rejections 0.019-0.031, 93 scenarios | 0.0188-0.031, 93 entries |
| Q2 at ±0.5: 0.27; at ±1: 0.76 | 0.2718, 0.2682; 0.7576, 0.7598 |
| 6 runs 0.61-0.62; ×0.75 0.94; ×1.5 0.42-0.43 | 0.611, 0.6184; 0.9422, 0.9418; 0.4202, 0.425 |
| Empirical 0.66, 0.82; seed 4.82 0.79-0.80; 5.84 0.63-0.64; S 0.4 0.67-0.68 | 0.6608, 0.8216; 0.791, 0.7978; 0.6434, 0.631; 0.6666, 0.6746 |
| Q1 at 1 visit with failures 0.34, 0.14 | 0.3442, 0.1376 |
| Unequal failure rates at equal means 0.33-0.34 | 0.3334, 0.3404 with 8 runs; **0.4432, 0.4494 with 6** |
| Largest wrong direction 0.108 | 0.1082 |
| Base no-failure joint false ≤ 0.049; coverage 0.948-0.959 | max 0.0492; 0.9478-0.9592 over all 50 |
| Empirical 0.066, 0.934 | 0.0662, 0.9338, the worst of six |
| With failures 0.47, coverage 0.52 | 0.472, 0.5232 at 6 runs, S-dense 1/8 |
| The four table rows | all match |

The simulation is faithful to the registered procedure: `vwelch` at `S.LEVEL`, `vlabels` mirrors `label`, the exact test at `ALPHA / 2`, the floor guard applied to both labels, one S-mod sample in both contrasts, P-joint fixed at 8, and 15 040 trials cross-checked on both label kinds, `e3c_power.py:211-223`.

**Still missing for the stages.** Nothing that blocks writing them. Small gaps: `margins` raises when P-fixed's mean is not positive, `e3c_stats.py:61-62`, while line 232 promises "no contrast is read"; the report function must turn that into a registered outcome. Line 299 does not say whether P-fixed's mean is recomputed on each maze resample; for a paired bootstrap it should be.

## Verdict

Revise, narrowly. Required:

1. **§7.1, lines 245-251:** state that for Q2 the exchangeability null is expected to be false on spread alone under §8's model, that its exact rejection therefore carries no 0.025 guarantee about means, and that the simulated rejection rate at equal means is about 0.04-0.05, or 0.09-0.10 with failures. Say in D208 that the 0.76-against-0.64 comparison is at unequal rejection rates under equal means.
2. **The exact label,** `e3c_stats.py:148`, `e3c_power.py:149`, `test_e3c_stats.py:179`, line 248: mark the direction as a sample description, for example "distributions differ (exact); observed mean higher: X". `power.json` stores no exact label strings, so no regeneration is needed.
3. **§8, line 439:** qualify "0.33-0.34" as 8 S runs and add 0.44-0.45 for 6. At line 420, say "about 0.04-0.05" rather than the single 0.042.

Optional, best done before binding since the files bind:

- `e3c_stats.py:1` still says "draft 2, D207", and line 5 still calls each contrast a Welch comparison.
- `coverage_rule` puts undefined champions in the share denominators and still reports `p_joint_lower_than_both` from them, lines 177 and 187. Report shares as k of n defined, or set that flag to None when any champion is undefined.
- Name the cut split counts at line 242, 924 and 3 003, so the discreteness is on record.
- Lines 309-311: give the sentence template for Q1 when the exact test rejects and the margin label says "no relevant difference", the likely pair at the pilot's spread.
- Line 448: "at worst 0.066 and 0.934".
- A studentized statistic, Welch's t permuted, would bring Q2's equal-means rate nearer 0.025 at 8 against 8. It would need its own power run, so I do not ask for it now.