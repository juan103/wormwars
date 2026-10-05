# E3c pre-registration draft 2: review

**Verdict: revise, but narrowly.** Three small required changes, none touching the design, the registered decisions or the power numbers. After them it can bind on a diff check without another full round.

What I checked: draft 2 against both draft 1 reviews, `e3c_stats.py` and its tests line by line, `e3c_power.py` and its tests, about thirty §8 figures against `power.json`, the compute record and the attempt file it re-sums, the T-F values against E3b-1's `evaluate.json`, and E3b-1's `g-e` rule. I could not run the tests or compute hashes, so the sha256 of `train-tf.json` at line 87 is unverified by me. The `maze-reference.json` hash matches E3b-1's `g-e.json`.

## 1. Draft 1's required changes

All six of mine are taken correctly: §0 lines 17-28 (binding sequence); §8 (figures, SE, normal base case, 8-atom artifact); §7.1 line 231 (the Q1 floor wording) and the fixed level replacing the rank formula; §7.3 lines 325-337 (L's interval, P-fixed's bootstrap, "below both", "mixed" made explicit); §13 items 3, 11, 12; §2 lines 90-93 and §5 line 184 (hash-failure refuses, two files pinned, P-fixed in the noses-removed condition). My suggestions were also taken, including the failed-run count and Astra's two power asks named at lines 433-437.

Astra's seven are taken, with two residues that are my required items 1 and 2 below: the coverage rule's undefined case is incomplete for P-joint, and the execution contract lacks E3b-1's `g-e` gate. The diagnostic charge is now executable: `runs/e3c/compute/diagnostic-seed-check-20261005.json` exists in the directory `aggregate` re-sums, and the cap clock reads `totals.seconds_timed`.

## 2. Statistics and the failed-run rule

`e3c_stats.py` is right. `contrasts` gives both intervals at 0.975 and Holm beside; `label` matches the table at lines 246-252 with strict boundaries; `failed` and the floor guard use the same threshold consistently ("not above" versus "exceed"); `censored_median` matches line 297-298, including the exactly-half case. The tests cover each. One stale note: the module docstring of `tests/test_e3c_stats.py` lines 1-3 still describes draft 1's Holm-level intervals.

The failed-run rule is sound as a pre-registered fallback. Its limit for unobserved failures is honest and correctly quantified. The limit statement is incomplete in one respect: the rule sees only failures below W2 alone + 1. In the simulation about 8% of failure draws from N(2.3, 0.3²) sit above 2.72 and are not caught, which is why Q1 is "approximate" in 0.86 of trials rather than 0.88. Real partial failures, such as a champion stuck near 4-5 visits, would create the same miscalibration and would not be flagged or simulated. Line 409's "The rule catches observed failures" overstates.

## 3. Power analysis against `power.json`

Faithful: the vectorized labels replicate `label` and `contrasts`, one S-mod sample enters both contrasts, the floor guard and the approximate rule are applied, 15 040 trials are cross-checked with a sabotage test, and the centring test uses unequal failure rates. Every §8 figure I pulled matches:

| §8 claim | `power.json` |
|---|---|
| Null table row (0, 0): NRD 0.98; Q2 rej 0.02; joint 0.045 (SE 0.003) | 0.9786; 0.0244; 0.0454 (0.0029) |
| Row (0.5, 0): false beyond 0.014; joint 0.027 | 0.0138; 0.0274 |
| Row (0, 1.0): Q2 rej 0.65, beyond 0.19 | 0.6448, 0.1902 |
| 6-run full null joint 0.050 | 0.0504 |
| Q2 power ±1: base 0.65; ×0.75 0.89; ×1.5 0.28-0.32; empirical 0.58/0.63; seed 4.82 0.68; 5.84 0.50; S 0.4 0.60-0.62 | 0.6448-0.6526; 0.8886/0.8932; 0.2822/0.3186; 0.5808/0.634; 0.6778/0.681; 0.4966/0.496; 0.598/0.6218 |
| Failures 1/8 both: approx Q1 0.86, Q2 0.62; joint 0.079; 1/4: 0.075 | 0.861, 0.6228, 0.0794; 0.0752 |
| One arm 1/8: 0.34-0.35; 6 runs 0.44-0.46 | 0.3348/0.352; 0.4414/0.4576 |
| Worst Q2 0.14; Q1 power with failures 0.14 | 0.1402; 0.1366 |

Two wording points. Line 371's "successes at 6.7" holds for S-mod only; under centring S-dense's successful component moves, to 7.33 in the (0, 1/8) null. The row (1.0, 0.5) "0" is 0.0002.

## 4. §0 and §5

Complete enough to write the stages against, with one gap. §5 step 2, lines 163-165, says `g-e` is read on the tested platform but never says the training stages require it to pass, nor what a GPU-hash mismatch does. E3b-1's pre-registration fixed this: no training stage starts unless `g-e` passed, and it fails on any mismatch. E3c reuses P-joint trained at f881308, so a mismatch invalidates Q2. §0 lines 26-28's "engine paths" freeze is stated but not mechanised; nothing in §12 tests it.

## 5. New issues

- `coverage_rule`, `e3c_stats.py` lines 141-153: an undefined P-joint champion counts as a non-coverer in P-joint's share, so it can only push toward "supported". §7.3 lines 331-336 are silent on this case and there is no test for it.
- §10 line 459 budgets 20 checkpoints per run; §5 line 168's schedule has 21.
- §1 line 65 says "no relevant difference" is the only equivalence asserted; §7.3 line 329's "no material loss" is also a bounded-equivalence claim.

## 6. Required changes

1. **§5 step 2:** state that no training stage starts unless `g-e` completed and passed, and that a mismatch stops E3c and asks the owner, with P-joint's reuse requiring an amendment.
2. **§7.3 and `coverage_rule`:** define P-joint's undefined champions. Either any undefined champion in any arm gives "mixed", or state that P-joint's count as non-coverers. Add the test either way.
3. **§7.1 lines 254-261 and §8 line 409:** state that the rule detects only failures below W2 alone + 1, that about 8% of simulated failure draws lie above it, and that bimodal outcomes above the floor are neither detected nor simulated. Change "catches" to "catches most".

Optional, best done before binding since `power.json` binds:

- Report joint coverage of the two 97.5% intervals in `power.json`. It answers Astra's 92.6% finding directly.
- Add to §12 a check recorded in the start marker: the diff from the binding commit to the formal commit under `wormwars/`, `configs/` and `requirements.txt` lists only added files.
- State the cut compositions ([192, 8, 8], [64, 8, 8], and the checkpoint chunks), since `project` times the uncut ones.
- Say what a missing checkpoint record does to a run in §7.2.
- Give the decomposition's Welch-among-successes a level at line 264.
- Carry the failed-run counts and the "no-failure model" caveat beside every confirmatory label in the results template.
- Fix the 21 checkpoints, the "successes at 6.7" wording, the §1 equivalence sentence, the "0" at line 386, and the stale test docstring.