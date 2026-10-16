**Verdict: ready for the pre-registration**, with three things to do before it is pushed (findings 1-3) and the rest as text fixes in it. No design decision needs to change. The v1 findings are fixed, `power.py` computes what §6 reports, and the two-row probe is equivalent to 03's and 03m's one-row code.

## 1. The v1 findings

| v1 finding | Status | Where |
|---|---|---|
| 1 tolerance unmeasured, no fallback | Fixed: measured first, declared with margins, stop rule. One quantity still unmeasured (finding 1 below). `twin.history` lacks the `@counted("probe")` decorator that `measures.history` has (`measures.py:91`); the equivalence script wraps it in `acct.category("probe")`, so counts land, but the formal driver must do the same. Minor. | §5, `equivalence.json` |
| 2 Holm sketch | Fixed: `power.py:155-165` is a correct step-down Holm (thresholds 0.05/4, /3, /2, /1 in p-order, stop at the first failure). | |
| 3 Q-A extrapolation | Fixed: regression on intact P4 over the 80 panel graphs, extrapolated to 03's and 03r's pools (`power.py:76-87, 124-130`). | |
| 4 Q-E wording, pre-tanh floor | Fixed. 03r's margin gate is 0.5 τ_E on the ratio scale, so it carries over to the pre-tanh ratio without change. | §4 Q-E |
| 5 "128 permutations" | Fixed. | §0 item 3 |
| 6 replacements named | Fixed. | §0 |
| 7 fixed wording | Mostly fixed. Q-D's fail sentence is still an ellipsis (finding 5). | `DESIGN.md:248` |
| 8 order | Fixed. | §5 |
| 9 validity rules | Fixed. | §4 Q-A, Q-D |
| 10 hash-derived seeds | Fixed. | §3 |

## 2. `power.py`

I checked the model and the arithmetic against the inputs; I could not run it.

- **Q-A** (`power.py:76-87, 124-130`): intercept per ensemble plus one slope, residual SD with ddof 6, fresh intact P4 drawn with replacement from the 03 + 03r pools (sizes 256/384/256/256/256 match 128 + 128 and 128 + 256), N2's change drawn at √2 × its paired bootstrap SE (03m's estimate uncertainty plus the fresh 2 048 draw). N2's change 0.014405 equals `decay.json` N2 gaps_off P4 0.94526 − 0.93088. Right. The regression residual already contains each graph's 2 048-genome noise, which the fresh graphs share, so no second noise term is needed. Right.
- **Q-D** (`power.py:131-141`): per ensemble, SD from the scaled inverse χ²(15), mean from N(x̄, sd/4), 128 draws: the standard flat-prior normal posterior predictive. N2's share 0.4705 = tick-30 mean over tick-0 mean of the local array, matching the design's 0.470. Right. By hand, SH-recip (mean −1.269, SD 0.208 on log share) gives a 0.66% per-graph tail at N2's log share −0.754, which is what makes Q-D the weakest rank test.
- **Q-B** (`power.py:142-151`): true values drawn at the 2 048-genome SE, estimates at SE/√k, the registered one-sided and TOST p-values exactly as §4 writes them (`norm.sf(x)` = Φ(−x)). Right. The 0.78 is essentially the probability that AIY's true ΔP4 lies inside ±0.02 given 03m's −0.004 ± 0.0117: Φ(1.67) − Φ(−0.93) = 0.776, which matches 0.7755 reported. So the number is right and §6's reading of it (the limit is 03m's uncertainty, not the fresh sample) is right.
- **Q-C** (`power.py:152`): r = 0 is assumed, not simulated. The assumption holds on 03m's data: the largest permutation response in `weights.json` is 0.0520, N2's is 0.1286, the pooled null maximum 0.0732. §6's table should mark Q-C's 1.00 as assumed (finding 6).
- **Reported probabilities** match `power.json` at all three genome counts, including the fixed-sequence row (D 0.8368, B 0.648) and the 2 048 and 16 384 figures quoted for Q-B.

## 3. `twin.py` and its tests

Traced against `measures.history` (`measures.py:92-121`) and `history_full` (`p4m.py:491-537`): same warm, ramp and follow schedules; row 0 is the rising start, row 1 the falling; `raw()` reads each row through `_readout` (`twin.py:59-60`); steady contrast is falling − rising, differences are rising − falling; hold and end ranges take the max over both rows, which equals 03m's `np.maximum` of the two runs; the slope's mean over rows and neurons equals 03m's average of the two per-run means; the tick list is identical for follow = 300 (`equivalence.json` ticks_match is true for all 81). Equivalent. The hold-turn and end-turn ranges that 03m also kept are not computed; nothing in the design needs them.

The declared tolerances versus the measured worst cases (`equivalence.json:1259-1281`): P4 terms 2.03 × 10⁻⁷ against 10⁻⁵ (49×); ramp end 7.19 × 10⁻⁶, steady 4.30 × 10⁻⁶, tick 30 2.23 × 10⁻⁵, slopes 1.1 × 10⁻⁶ against 10⁻⁴; curve 1.30 × 10⁻⁴ against 2 × 10⁻³ (15×). Justified, with two exceptions in findings 1 and 4.

## Findings

1. **The tick-30 retained share tolerance was declared without being measured.** `DESIGN.md:314-315` declares a relative 10⁻⁵ on each graph's share at tick 30 "50 times the worst measured", but `p4mc_equivalence.py:78-86` never computes the share; it records only the per-genome tick-30 deviation (worst 2.2 × 10⁻⁵ of the largest |difference|). The aggregate's deviation is bounded by that times max|d₃₀|/mean|d₃₀|, which can exceed 10⁻⁵ unless errors cancel, and the per-genome arrays from the run were not saved, so it cannot be computed after the fact. Fix: add `share30 = |diff[30]|.mean() / |diff[0]|.mean()` against `decay.json`'s `mean_abs_difference` to the equivalence script and rerun it on the pre-run check set (N2 plus four graphs per ensemble, about 0.15 GPU-hours), then declare from that. Or declare the tolerance on the per-genome curve only and drop the aggregate share from the check.

2. **"Tick 30 has the highest simulated pass probability among ticks 10-50" has no committed computation.** `DESIGN.md:240` cites §6, but `power.py:40` simulates one tick (`TICK = 30`) and `power.json` holds only tick 30. Rule 5. Fix: either loop `TICK` over 10, 20, 30, 40, 50 in `power.py` and commit the per-tick Q-D probabilities, or delete the clause and keep the stated margin (0.470 against 0.427) as the reason.

3. **The settling-label check lives only in prose.** `DESIGN.md:309-312` and D286 report "0 of 2 048 changed" and the counts 26, 171, 0, 37 from an uncounted 1.6-minute run with no output file; `runs/p4mc-equivalence/` holds only compute records, and the pre-run check's strict rule "identical on N2" rests on it. Fix: add the settled-with-separation count per graph to the equivalence script's output and commit it with the rerun from finding 1. Also consider whether a strict identity on a label with a 10⁻⁴ threshold, on a quantity whose relative deviation reached 0.33 (`equivalence.json:1264`), should stop the whole study rather than be reported: one genome crossing the threshold on the formal GPU pass would halt everything for a secondary descriptive count. A tolerance of a few genomes, or "reported, not stopping", is defensible; say which.

4. **"At least 4.5 times the worst measured" is wrong for the hold range.** `DESIGN.md:317`: the hold-state range's worst is 2.66 × 10⁻⁵ (`equivalence.json:1265`, and the design's own table says 2.7 × 10⁻⁵), so 10⁻⁴ is 3.8×. Fix the sentence or raise that one tolerance.

5. **Q-D's fail wording is an ellipsis.** `DESIGN.md:248`. Write it as Q-A's is: "the registered criterion was not met: [r of n] graphs per ensemble retained as much as N2 or more".

6. **Q-C's 1.00 is an assumption in a table of simulations.** `DESIGN.md:375` beside `power.py:152`. Add "assumed r = 0; no 03m permutation within 0.07 of N2's response" to the table's note.

7. **The pre-tanh read-out has no reference test.** `test_exp03_twin.py:57-65` checks shape, "not allclose" to the tanh contrast, and the slope's range. Swapping `plus` and `minus` in `pre()` (`twin.py:56-57`), or reading the wrong neurons, would pass every test. Q-E carries a verdict. Fix: a CPU test that recomputes the pre-tanh contrast from an exposed final state, or that checks `tanh`-of-pre against the raw turn on a one-neuron-per-side interface where the two coincide after tanh.

8. **The matched-control claim mixes a conjunction with Holm.** `DESIGN.md:193-194`: "RIA's cut exceeds each of its four controls' cuts (one-sided bootstrap tests, Holm over the four at 0.05)". If the claim is "exceeds each", it is intersection-union and the p is the maximum of the four; Holm is for claiming the individual comparisons. Say which. Separately, the degree list checks against `lesions.json`: RIA 135; AIB 141, AVJ 119, RIM 116, AVH 114. PVP is also 114, so the alphabetical tie-break actually decides the fourth control; say so. AIY 58; AWB 59, RIF 59, RIP 59, RIV 57, with nothing else within 1. Right. Note that the controls' cuts in 03m are all below 31%, so running the eight controls on all 32 batches (256 of Q-B's 384 probes) buys precision the comparison does not need; batch 0 would do, saving about 0.47 GPU-hours. Optional.

9. **`equivalence.json` was measured on a dirty tree.** `equivalence.json:7` records `dirty: true` at 6e948d7; D286 says the only later change was `allow_pickle=False`. The pre-run check re-measures on the registered commit, so this is acceptable, but §1's disclosures should say it.

## 4. The questions in §10

1. Yes, as tabled above.
2. **Keep the normal-theory test with the paired bootstrap SE.** At 65 536 genomes a ratio of means is close to normal even with 03m's heavy tails (the top 5% carry 40% of the numerator), the Monte Carlo error of a 10 000-resample SE is under 1%, and the test is then a fixed formula a reader can recompute. Report the percentile 90% interval beside it as a check, not a test. The one thing to add: the SE is treated as known, so say so.
3. **Total degree is a reasonable match and four per target is enough**, given that the controls are expected at 31% or below against 53% and 62%. The one alternative worth a sentence is matching on chemical in-degree alone, since RIA's and AIY's role is on the sensory-to-steering route; the design need not adopt it, only say why total degree was chosen.
4. Findings 1-3 and 5-7. Nothing else is missing for a reader to trust either outcome.

## What I could not check

I could not run code: `power.py`'s outputs, the tests, and the equivalence run were not re-executed. I did not recompute the paired SEs from the local arrays beyond checking them against Astra's v1 figures (0.0189/0.0075 and 0.0300/0.0117, consistent). The degree sums are from `lesions.json`'s per-neuron entries, not the connectome. The 13.0 s and 6.6 s timings rest on D285.