**Revise.** The main v2 fixes are implemented, but result retention is still incomplete. Q1b also misstates one regenerated rank, and the new graph-rebuild command bypasses the cap.

I checked the files at branch HEAD `fecf8d4`. I did not run the runner, tests, or statistical recomputations.

My six v2 must-fixes stand as follows:

| V2 requirement | V3 assessment |
|---|---|
| Replace endpoint-only settling | **Fixed.** `WindowRange` examines every sampled tick for both histories and holds. The oscillation regression case addresses the original failure. |
| Retain completed measurements and arrays | **Partly fixed.** Successful runs retain substantially more, but cap-stop losses remain below. |
| Export accounting after finalization | **Fixed.** Export occurs in `finally` after `run_script` exits. Tests cover completed and cap-stopped attempts. |
| Correct SH membership and regenerate | **Fixed.** `cmd_tails` uses exact membership; the regression includes all five ensembles; regenerated output reports 128 graphs per ensemble. |
| Narrow Q1 interpretations | **Fixed in substance.** Denominator-mediated association remains acknowledged; noise is not excluded; overlap and trimmed P4 are calculated. One new rank statement is wrong. |
| Narrow the empty-screen conclusion | **Fixed.** The wording now concerns tested valid deletions and the declared thresholds. |

The immediate empty-deletion check, pre-named target ordering, revised compute estimate, response floor for follow-ups, float64 averaging, and enforced Q4 reproduction checks are also implemented.

**Must-fixes**

1. **Finish retaining completed work before another cap check.** This remains my v2 requirement, rather than a new request.

   | Location | Remaining loss |
   |---|---|
   | [Weights loop](/D:/Claude/random/wormWars-p4/scripts/p4m.py:422) | Checkpointing occurs after both designs. A cap stop before the paired design discards the completed independent condition. The Changes section incorrectly says “after every condition.” |
   | [Decay loop](/D:/Claude/random/wormWars-p4/scripts/p4m.py:574) | The completed long history is not saved before the cap check preceding gaps-off. That check can discard the whole completed decay measurement. |
   | [Lesion checkpoint](/D:/Claude/random/wormWars-p4/scripts/p4m.py:715) | Arrays are saved every 20 results, with no exception-path flush. A cap stop loses up to 19 completed deletions’ arrays, although their summaries survive. |
   | [Lesion follow-ups](/D:/Claude/random/wormWars-p4/scripts/p4m.py:730) | `history_in_chunks` receives no checkpoint callback. A cap stop within one synapse type discards that type’s completed follow-ups. |

   Additionally, decay’s gaps-off histories are reduced immediately to summary terms; their per-genome arrays are discarded.

   Save each completed condition before proceeding, or flush accumulated completed results on controlled exits. Add mocked cap-stop tests at these boundaries. The existing accounting test verifies accounting export, not measurement retention.

2. **Correct Q1b’s SH-recip numerator-concentration rank.**

   [PLAN.md:74](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/PLAN.md:74) says N2 is above “all but one in SH-recip.” But [tails.json:111](/D:/Claude/random/wormWars-p4/experiments/03m-p4-mechanism/tails.json:111) reports a share strictly below N2 of **0.96875 = 124/128**. Thus **four graphs are at or above N2**, not one. The one-exception count applies to the denominator-concentration statistic immediately below it.

   Use “above 124 of 128 SH-recip graphs” unless the underlying values are checked for ties.

   The other Q1b numbers are read fairly:
   - Split-half correlations: **0.94264–0.98560**.
   - Cross-half Spearman: **−0.60812 to −0.25333**.
   - N2 numerator/denominator concentration: **39.96% / 38.04%**; overlap **92.16%**.
   - Trimmed N2 P4: **0.89465**, above **96.875%–100%** of equivalently trimmed ensemble graphs.

   Those support the narrowed interpretation that N2’s elevated ratio survives removing this particular top-5% subset.

3. **Apply the cumulative cap to graph rebuilding.**

   The new [cmd_graphs](/D:/Claude/random/wormWars-p4/scripts/p4m.py:346) calls `ensure_graphs` without constructing or checking a cap clock. Consequently, it can rebuild the entire missing panel even when prior attempts have already exhausted five hours. Accounting that work afterwards does not enforce the limit.

   Check the cumulative cap before rebuilding and between graph rebuilds. Keep completed graph files and export accounting on a stop, as already intended.

**Suggestions**

- Record Q1b’s actual input directory: `cmd_tails` currently writes a fixed directory string despite accepting `--measures`. Both regenerated analysis files also retain a dirty `0916f41` stamp; a clean rerun or explicit source hash would improve traceability.
- Q2 promises numerator changes from intact, but `row()` records only P4 and denominator changes. Add the numerator difference.
- In Q3, explicitly define each null graph’s change relative to **its own intact measurement**. The current “difference from intact N2” wording is ambiguous when extended to the panel.

**03m plan: revise**