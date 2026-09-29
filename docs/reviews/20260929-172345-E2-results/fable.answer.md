# Verdict: **fix**

The registered outcome and floor are stated verbatim and applied correctly. The problems are in the interpretation and in a few figures. RESULTS.md and D124 are already committed, so make these as dated corrections.

## Must-fix

1. **RESULTS.md §8, lines 172-174** ("1 000 generations of either optimizer add little…"). This is wrong for the ES and overclaims for both.
   - The compared ES ran 623 generations. The 1 000-generation ES is 0.73 above random sampling (2.331 − 1.605), outside the floor margin.
   - Paired by run, the GA beat random sampling in 7 of 8 runs (by 0.31-0.69) and the ES in 8 of 8 (0.28-0.72, mean +0.48).
   - The −0.356 owes about 0.14 to GA run 2. Without run 2 the gap is −0.495; by medians it is −0.540, which would not fire. The floor fires as registered, but this sensitivity must be disclosed.
2. **RESULTS.md §1, line 47** ("Run 2 carries most of the ES's lead"). It carries all of it and more. The other seven differences sum to −0.22; without run 2 the ES trails, 2.102 against 2.134.
3. **RESULTS.md §5, lines 124-125** ("'keep the GA' is partly a budget effect"). At 1 000 generations the ES still fails the margin (0.37 < 0.5), though it passes the spread (7 of 8 above 2.131). The lead grows with budget; the outcome does not change. Without run 2 the extended lead is 0.24.
4. **RESULTS.md §8, lines 178-179** (the GA "drifted up from about 1.6 to 1.8"). About 70% of that rise is run 6 leaving a plateau between generations 600 and 625 (validation 0.45 → 1.81). The other seven runs' mean moved 1.72 → 1.80.
5. **RESULTS.md §3, line 71.** The GA's mean at generation 100 is 3 082 / 2 048 = 1.505, so 1.50, not 1.51.
6. **RESULTS.md lines 13-14 and §7.** The per-stage wall times match `runs/e2/compute/*.json`, which `.gitignore` excludes (`runs/**/compute/`). The committed `compute-record.json` has only category totals, and the stage records' `seconds` differ by 1-2 s (4 861.75 against 4 863). "Every number below is from the committed records" is therefore false for that column.
7. **DECISIONS.md line 3677** ("10:38 to 15:20 UTC"). The projection started at 10:34:38 and is inside the 4.74 GPU-hours. 10:38-15:20 is only 4.70 hours.
8. **RESULTS.md line 15, README line 3, D124** ("bound at `60af3cf`"). The registration defines the binding commit as the one the projection records, and `projection.json` records `69f4163`. Say what `69f4163` adds; I could not inspect it.

## Suggestions

- **Selection optimism:** report validation → hold-out for every champion set. It is small and even, so it does not explain the ranking.

  | Champions | Validation | Hold-out | Change |
  |---|---|---|---|
  | GA | 2.012 | 1.961 | −0.051 |
  | ES | 2.136 | 2.086 | −0.051 |
  | random sampling | 1.665 | 1.605 | −0.060 |
  | extension | 2.363 | 2.331 | −0.031 |

- **Run 2's start:** its generation-0 population scored 0 for all 32 genomes. That start is shared by the GA's failed run, the ES's 51 flat generations and random sampling's lowest champion. Link them.
- **Line 142:** the extension's mean (2.33) is above M-avg, so say "every formal method's mean".
- **Lines 176-177** ("the ceiling is not the task's"): add that whether the network and interface can express more is untested.
- **Extension, run 3:** without it the validation rise is +0.22, not +0.29.
- **Cross-references:** "§6", "§7, §9" and "§12" point to the pre-registration, while "§3" and "§4" point to RESULTS.md. Disambiguate.
- **README line 33:** D117-D122 should now run to D124.

## What the diagnosis should look at first

1. **Noise, from existing records, with no GPU.**
   - Random sampling's candidates scored 1.25-2.0 in training but average 0.81 on validation.
   - GA candidates swing between adjacent checkpoints (run 5: 2.17 → 1.33 → 2.23).
   - My rough estimate of the standard error of an 8-world mean is 0.4, from 18 hold-out worlds of GA run 0. Compute it properly from `per_world_counts`.
2. **Search against selection.** Typical candidates are about 0.8 (random sampling), 1.7-1.8 (GA) and 2.0 (ES). The champion gap is small partly because random sampling gets 41 independent candidates for validation to choose among.
3. **The plateaus.** Six of 8 GA champions sit at 2.11-2.21, beside M-avg's 2.20. A second level near 0.7 held GA run 2 throughout and run 6 for 600 generations. Ask what the extension's run 3 (2.91) does differently.
4. **Budget last,** crossed with worlds per genome, on new world ids.

## Checked and correct

- **Decision:** means 1.9609, 2.0856 and 1.6047; GA median 2.1309; 5 ES champions above it; margins +0.1246 and −0.3562; all per-run differences.
- **Hold-out tables:** SDs, oracle fractions, probe ranges, controls, and the extension's champions and mean.
- **Training:** champion generations for all methods, the ES and extension validation curves, the GA's 1.47-1.90 range, random sampling's 0.60-1.06 range, and the 32 000 count.
- **ES details:** start scores, 54 flat generations (1-51, 53, 55, 56) and the clipping range.
- **Pilot:** all totals and the selection.
- **Ledger:** episodes, neural updates, the allowance, the totals and the projection's 5.11 hours.

I recomputed by hand from the JSON; nothing was executed. I did not check git history, the push order or the local genome files.