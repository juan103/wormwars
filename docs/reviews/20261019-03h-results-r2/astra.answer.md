**publish**

Checked `0cf9aec` on `roadmap`. Static inspection only; no project scripts or tests executed, no files changed.

My round-1 findings:

| # | Confirmation |
|---|---|
| 1 | N2 statement corrected and complete. |
| 2 | Scenario wording, unknown N2 response, and full scenario range corrected. |
| 3 | History conclusions appropriately narrowed; causal and mediation claims excluded. |
| 4 | Both post-data decisions explicitly disclosed. |
| 5 | Separate decile selection and one-tick diagnostic correctly explained. |
| 6 | Sham wording and interval conditioning corrected. |
| 7 | Earlier reproduction blockers resolved; minor ordering ambiguity remains below. |
| 8 | No-arrays output correctly preserves the committed power record; regression test covers it. |
| 9 | Positive interval endpoint now preserved correctly. |
| 10 | +0.006 rounding and D339 correction correct. |
| 11 | Review status and counts now supported. |
| 12 | “Before 03h” correctly fixes the historical statement. |

Rechecked every changed numerical field in `summary.json` against its source, including the added decile means. The added upper-SD rates correctly represent **zero simulated passes** and **0.06473 → 0.065**. The ASK clarification and README annotation preserving bound DESIGN.md are appropriate.

Two **low-severity, nonblocking** documentation issues:

- [RESULTS.md:297](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:297): “Everything needs the connectome” is false. Neither CPU script loads it; the summary builder uses only standard-library JSON processing.
- [RESULTS.md:325](/D:/Claude/random/wormWars/experiments/03h-history-use/RESULTS.md:325): Specify **`b_power.py` first, then `e03h_summary.py`**. The reproduction branch starts without `b-power.json`; executing the scripts in their listed order makes the summary builder fail on that missing input.

No new numerical errors or publication-blocking overclaims found.