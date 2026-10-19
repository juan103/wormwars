**Verdict: publish.**

Every number that changed traces to its record, and each of my twelve round-1 findings is fixed. Static reading only; nothing was run.

**Round-1 findings, each checked against the files:**

1. **Placeholder review claims.** Fixed. `RESULTS.md:86` and `:292` now cite D341, and `docs/reviews/20261019-03h-results/` exists with both answers and a NOTE.
2. **"Could not separate".** Fixed. `RESULTS.md:45-49`, `:247-248`, `:255-256`, the README, the ROADMAP and the root README now say scenarios suggested the rank test would rarely have passed, with the full range including the upper-SD scenarios at `RESULTS.md:169-170` and the u = 0 caveat at `:171-172`. All seven rates match `b-power.json`.
3. **History wording.** Fixed in all four places. "Not shown" now excludes use as memory and mediation of an N2 advantage.
4. **Post-data decision.** Fixed at `RESULTS.md:14-17`. The Holm arithmetic there (first of 65 versus 3 of 65) matches D330 and DESIGN §13.
5. **Amplitude check's departure.** Fixed at `RESULTS.md:20-22` and `:184`. It matches `PILOT.md:190` and D338.
6. **ASK cap.** Fixed at `RESULTS.md:145-147`, `:242-243` and `:261-262`, and in both READMEs and the ROADMAP.
7. **Reproduce it.** Fixed and now consistent with the guards. I traced each step: step 0 and 0b's guarded list excludes `development-records/`, so their rewritten records do not block `bind`; `bind` checks only a clean tree, the later stages check `origin/<branch>`, and `pilot/` is unguarded until the amplitude check adds it; the amplitude record does not exist at `ff1fd31`, so its run-once guard is clear. The `b_power.py` no-arrays path writes to a separate file and the test would have failed before the fix.
8. **Stop decision's D-number.** Fixed, `ROADMAP.md:20`.
9. **Denominator.** Fixed. The decile test means are in `summary.json` and at `RESULTS.md:137`.
10. **Round count.** Fixed and consistent with D321 to D330.
11. **DESIGN.md status line.** Handled in the README instead. Correct, given the binding.
12. **"As fast as".** Fixed.

**Re-checked numbers that changed:** the 0.76 SDs, the 0.5 row's +0.006, the +0.00004 lower endpoint, the five-decimal shifts and intervals in `summary.json`, the 1.50 to 1.59 test means, the 0.014 to 0.019 u, and the compute total. All correct. The new claim that the scripted gate used N2's motor gains is true (`scripts/e03h.py:194-196`).

**Introduced or remaining, none blocking:**

- **Low, traceability.** Three page figures round correctly from the records but not from `summary.json`'s four-decimal intermediates, the hazard Astra's finding 10 named: A's third-graph D +0.001 (`RESULTS.md:155`; summary 0.0015, record 0.001494), H_dir +0.062 (`:224`; summary 0.0625, record 0.06249), and raw-forward +0.007 (`:228`; summary 0.0075, record 0.007467). Keeping five decimals there, as was done for the shifts, would close it. The page's numbers are right either way.
- **No change needed.** `RESULTS.md:5-6` says N2 was used "only" in the equivalence check and then adds its motor gains. Both are true, and the one-line forms in the READMEs and ROADMAP drop the gains. Two calibration scalars are not an N2 brain, so the short form is not misleading.