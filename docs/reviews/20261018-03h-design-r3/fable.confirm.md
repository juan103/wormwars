**Verdict: ready for code and the pilot's registration, with two text fixes required before that registration is bound.** Both are in §7.7's detectability rule. Nothing else needs a redesign.

## 1. Round-3 findings

**Fable, round 3**

| # | Finding | Status |
|---|---|---|
| 1 | B's one-sided direction | Resolved. §6 states U, the direction, and "at or above", matching `rank_p` in `wormwars/exp03/mc.py:19-29`. |
| 2 | Step 0 recipe and verification replay | Resolved (§7.2). |
| 3 | No reading of the manipulation | Resolved (§7.7, decile shift and turn response, one registered amplitude change). |
| 4 | Derived numbers uncommitted, estimator undefined | Resolved. Record committed; §7.7 names the crossed estimator. |
| 5 | Detectability not numeric | Resolved in form. The formula has an error (new finding 1). |
| 6 | Pilot's registration step | Resolved (§7.3). |
| 7 | Sham estimator details | Resolved (§3). |
| 8 | Sham criterion as interval, recovered share | Resolved (§4). |
| 9 | Relief failure stops for redesign | Resolved. |
| 10 | Best of 32 explained | Resolved. |
| 11 | Holm ranks | Resolved. Arithmetic checked: 2/65 fails 0.025, 3/65 passes 0.05. |
| 12 | CPU costs, conservative rate | Resolved (§8). |

**Astra, round 3**

| # | Finding | Status |
|---|---|---|
| 1 | B's bootstrap repeated selection without scores | Resolved. Conditional inference, stated conditioning, alternative priced. |
| 2 | Reliability overstated, numbers | Resolved. Crossed decomposition, 0.865 minimum, mean timings, the "reliable means do not make ρ or D precise" caveat. |
| 3 | Gate rules | Resolved. Update and decision rules, threshold, bit-plus-internal combination, T = 1 exact, sham interval and failure action. |
| 4 | Sham conventions | Resolved. |
| 5 | Step 0 | Resolved. |
| 6 | Pilot decision procedure | Partly. W, detectability, size and degenerate graphs are rules. Rule 7's CUDA check says "same composition" but not `replay_mode()`, which AGENTS.md rule 6 requires for a bitwise CUDA claim (new finding 6). |

## 2. B's conditional inference (§6)

Acceptable as written. The data collected now match the intervals computed. The rank test needs no resampling at all; it conditions on everything and is valid under exchangeability of N2 with the nulls. The one caveat is the label "head start larger when memory is needed": its component "N2's level advantage > 0 by its 95% interval" does not cover N2's own genome-draw uncertainty, since N2 is one draw of 256 and only worlds and null graphs are resampled. The design says the intervals condition on the genome draws. The label's wording should carry that too, since the claim reads as being about N2 the connectome.

## 3. The record

Correct and traceable. The script reads the committed `pilot.json`, whose structure I confirmed holds `T1-M0` at 256 × 16 and `seconds` with fitness, calibration and history per graph. Its five-cell count matches `FIT_CELLS` and the 256/64 allocation in `scripts/exp03.py:142-146`. Its decomposition is the same estimator as `_crossed_se` at `scripts/exp03.py:580-595`. Internal consistency holds: the SD of genome means squared (0.068) equals genome variance plus residual over 16 (0.067 + 0.0012). Every number quoted in §2, §8 and D324 matches the JSON. The script has no self-check assertion; a development record can live without one.

## 4. Remaining findings

1. **§7.7, medium. The detectability formula shrinks the shared-world variance by √64, which it does not do.** Shared worlds are common to all 64 graphs, so that component of D's uncertainty does not fall with the graph count. Astra raised exactly this in round 3. The rule should use SE = sqrt(s_graph² / 64 + s_shared²), where s_shared is the SD over shared-world bootstrap replicates of the pilot's ensemble-mean D. As written the rule overstates power.

2. **§6, §7.7, medium. δ_A has no value and no stated place where it is fixed.** Both "meaningful" and the power rule use it. If it is chosen after the pilot's s_D is seen, the power rule can be met by choice. State that δ_A is fixed in the pilot's registration, with a number.

3. **§7.7, low.** s_D across 3 graphs has two degrees of freedom. A stop rule on it is close to a coin flip. Either lean on the shared-world term, which is estimated from 16 worlds, or make the between-graph term advisory.

4. **§6 A, low.** When A2 is "undetermined", the claim's fate under Holm and at the gate is unstated. Say A fails the gate.

5. **§6 B, low.** Say explicitly that the decile is selected per condition on that condition's selection-bank scores. The budget implies it, the text does not.

6. **§3 rule 7, low.** The bitwise CUDA check should be inside `replay_mode()`, per AGENTS.md rule 6.

Findings 1 and 2 belong in the design text and the pilot's registration before it is bound. The rest can be folded into the pre-registration.