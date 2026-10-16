**Verdict: revise.** The structure holds and the numbers quoted from 03m are right, but four things need a decision before the pre-registration can be written: the two-row probe's tolerance has no measured basis and no fallback, the pass-probability sketch ignores how Holm allocates thresholds and where Q-A's risk actually sits, Q-E's failure wording overclaims, and a corrected 03m overstatement reappears.

## Numbers checked against the committed files

All of these I recomputed from `lesions.json`, `synapses.json`, `decay.json` and 03's `supplement.json`:

| Claim in DESIGN.md | File | Result |
|---|---|---|
| RIA cuts response 62%, numerator 62%; AIY 53%, 53%; ΔP4 +0.005, −0.004 (lines 16-17) | lesions.json:128-131, 200-203 | 61.7/61.5, 52.8/53.1, +0.0049, −0.0043. Right. |
| Next largest cut ASE at 31% (line 18) | lesions.json:12794-12797 | 31.1%; no other pair below 0.112. Right. |
| 94 of 95 pairs within 0.02 (line 135) | all 95 `pair` rows | Only AIZ (0.9069, −0.024) is outside. Right. |
| Gaps off: N2 +0.014, nulls +0.051 to +0.143 (line 14) | synapses.json:75-112; reviewers' recount | +0.0144. Right. |
| 5 of 80 at or above N2 with gaps off (line 112) | RESULTS.md Corrections 4 | Right. |
| Tick 300: 2 of 80 above N2 (line 22) | decay.json `ratio_of_means_at_end` | SH-10007 (0.155) and SH-mirror-40014 (0.099) above 0.094. Right. |
| N2 above all 80 at every tick 5-50 (line 186) | decay.json tick-30 values | At tick 30 N2 keeps 0.470; nearest nulls 0.427 (SH-10007), 0.415 (SH-recip-50002), 0.397 (SH-recip-50014). Right. |
| 59 of 64 below N2, rank p near 0.08 (line 175) | Corrections 3 | Right. |
| SE 0.006, pooled median 0.82 (lines 133-134) | 03r PREREGISTRATION.md:26; Corrections | Right. |
| Holm cut-offs r = 0, ≤ 2, ≤ 5 at 128 graphs (lines 260-261) | arithmetic | Right. |
| Compute table (lines 284-291) | arithmetic from 6.6 s and 23.5 s | Sums are right. 23.5 s is extrapolated, not measured. |

## Findings

1. **The two-row probe's tolerance is a guess with no fallback.** `DESIGN.md:234-237` declares a relative 10⁻⁵ against 03's values. No test of a rows-1-versus-2 composition exists: `docs/REPRODUCIBILITY.md:46-61` lists the tested pairs and they vary strains, not rows per strain. `measures.history` (`wormwars/exp03/measures.py:92-121`) builds a `[S, 1, N]` current and reads `v[:, 0]`, so the two-row probe is new code, and `Brain.step` (`brain.py:478-483`) will hand cuBLAS a different `bmm` shape, which is exactly the path that gave 5e-5 per-op differences in T0. Over 3 680 substeps that may or may not stay under 10⁻⁵ on a mean of 2 048 genomes. If the check fails, the design is silent. At one row the whole plan is about 14 GPU-hours, over the cap. Fix: measure the B = 2 deviation on N2 and the 40 panel graphs now (03's genomes, no new information about the experiment), declare the tolerance from that with a margin, and write the fallback into the design: either one row with a raised cap, or one row with the null-graph deletions and the factorial dropped. Also name the tests rule 9 requires: the two-row function against `history` on the CPU at a stated tolerance, with a sabotage check, and the same `@counted("probe")` accounting.

2. **The pass-probability sketch tests the wrong thresholds.** `DESIGN.md:264-268` gives Q-D 0.99 "at r ≤ 5 in every ensemble", but r ≤ 5 is Holm's last slot. Q-D gets it only if Q-A's maximum rank p is strictly smaller. If Q-A and Q-D both land at r between 3 and 5, the third-ranked fails at 0.025 and Holm stops, so both fail although each passes alone at 0.05. From the 16 SH-recip curves at tick 30 I get roughly 0.7% per graph above N2 (the design says 1.5%). At 1.5% the chance of r ≤ 2 in 128 is about 0.70, not 0.99. Fix: the pre-registration's calculation should simulate the whole Holm procedure jointly, not each question at its most lenient slot.

3. **Q-A's risk is in graphs the panel did not contain.** `DESIGN.md:269` rests on 80 graphs none of which had intact P4 above 0.898. 03's full ensembles have about 5% of graphs above 0.889, one above N2 (03r PREREGISTRATION.md:11-12). By the design's own ceiling reading (`DESIGN.md:114`), a graph already at 0.93 intact is the one most likely to rise by less than 0.014 with gap junctions off. So r ≥ 1 in SH-route is plausible, and with finding 2 that matters. Fix: in the pre-registration's calculation, regress ΔP4 on intact P4 over the 80-graph panel and extrapolate to 03's and 03r's intact distributions, and say which slot Q-A then needs.

4. **Q-E's failure wording claims what a rank test cannot show.** `DESIGN.md:216-218`: "not distinctive on the pre-tanh read-out: N2's elevated P4 depends on the read-out's nonlinearity". Under 03r's rule a failure yields "inconclusive" or "consistent with ensemble X"; neither establishes dependence. Fix: "not confirmed on the pre-tanh read-out (counts …); whether the read-out's nonlinearity contributes is open". Also declare a validity floor for the pre-tanh denominator: 03's 10⁻⁴ is on the tanh scale.

5. **A corrected overstatement comes back.** `DESIGN.md:165`: "03m: all 128 permutations fell to the null range". RESULTS.md Corrections 3 (line 190-191) says the two designs reuse the same 64 permutations and are not 128 independent ones. Fix: "all 64 permutations, in both designs".

6. **"Takes up all of those suggestions" is not quite true.** `DESIGN.md:43`. Fable's tick-300 endpoint with 64 graphs per ensemble is demoted to a secondary; degree-matched random pairs and "thresholds from matched manipulated nulls" are replaced by the full 95-pair screen and by ranking ΔP4 against the ensembles. The replacements are defensible, arguably better, but say what was replaced and why, as Q-D already does for the endpoint.

7. **Fixed wording is incomplete.** `DESIGN.md:143, 173, 196` give "the parts that failed, by name" and "the count(s)" as fail wordings. 03r fixed full sentences for every case (PREREGISTRATION.md:313-319). Two cases have no wording at all: the replication failing (the design says at line 224 that every primary then "reads differently", but not how), and Holm stopping on a question that would have passed alone. Fix: write the sentences.

8. **Order under the cap puts a secondary before four verdicts.** `DESIGN.md:245-251` runs the factorial (step 3, secondary) before the ensembles (step 4), which carry Q-A, Q-D, Q-E and the replication. Move the factorial after the ensembles. Minor.

9. **Validity rules for Q-A and Q-D are implicit.** Q-A needs both the intact and the gaps-off measurement valid for a graph to count; Q-D needs a tick-0 mean above some floor (`p4m.py:556` used "greater than 0"). State both and the floor.

10. **Collision check should include hash-derived seeds.** `DESIGN.md:86-87`: 03r's secondary permutation seeds are `_gseed(name) + 2` (`exp03.py:106-110`), not a fixed range. The chance of hitting 1 000-1 255 is negligible, but the check is cheap. Minor.

## The five questions in §9

1. **Holm.** Keep it. Nothing aggregates the four questions into one claim, so per-question α would also be defensible, but the README will inevitably summarise them together and 03 set the precedent. The cost is the coupling in finding 2, which the pre-registration must quantify. A fixed sequence B, C, A, D at full α each would give Q-A and Q-D more power when the expected order holds. I would not switch unless the joint calculation shows Q-A or Q-D at real risk in the 0.025 slot.
2. **Tick 30.** Fine, and better than a 0-50 integral, which the same three graphs would dominate. The margin in 03m is 0.470 against 0.427; put those figures and the three nearest graphs in the pre-registration so the reader sees how the tick was chosen.
3. **Margins.** 40% also works as a specificity threshold: it sits between the third-largest pair cut (ASE, 31%) and AIY (53%). Say so. 0.02 is fine as an equivalence margin, but the relevant SE is the paired ΔP4's, not N2's unpaired 0.006. Compute it from the local lesion arrays before the pre-registration. The conjunction does establish "in proportion": a response cut above 40% with |ΔP4| < 0.02 bounds the numerator's cut within about one percentage point of the denominator's.
4. **ΔP4 as primary.** Yes. It is a paired within-graph contrast and is exactly "N2's lead over this graph narrows". The ceiling is an interpretation of a pass, not a confound of it. Keep the gaps-off level as the secondary with a verdict. The ceiling does create finding 3.
5. **Missing.** Findings 1, 4, 7 and 9, plus: the tests for the new probe code, the fallback if the equivalence check fails, and a statement that the deviations measured in the check are reported whatever they are.

## What I could not check

I could not run code, so the two-row probe's actual deviation, the paired SE of ΔP4 and the 1.5% per-graph figure were not recomputed; my 0.7% comes from a log-normal fit by hand to the 16 SH-recip tick-30 shares. The 13.0 s and 6.6 s timings rest on D285. I did not re-verify the +0.051 to +0.143 range graph by graph; both reviewers did on 2026-09-29.