**Verdict: revise** (small revisions; the numbers trace, the readings are right).

I checked every number in the draft against `summary.json`, `split.json`, `tables.txt`, the N2 panel record, the check files, `guard.json`, `stages.json` and the compute record, and the tick-20/26 peaks against the over-time arrays in `split.json`. All trace. The readings follow the plan: at seed 7600 lower(φ_S⁻) = 0.277 and upper(φ_S⁺) = 0.755, at 7700 0.140 and 0.555, so neither "most", "little" nor "a part" on either panel; rule 2 gives "inconclusive"; the branch needs "little", so it is not taken. Tick 300 is "most" on both (lower bounds 0.710 and 0.915), with 5 dropped resamples reported. The composition-retention identities add up. `census_tables.py` reads the eligible-only genome list, so its w_F and ρ_F match the plan's definitions.

Findings, ranked:

1. **"Real and N2-specific among these graphs" overclaims** (roadmap section, line 220). The core-frozen shuffles' ρ_F(30) are 0.411, 0.356 and 0.406, two of them above N2's 0.378 and 0.402, and hub-frozen-0's 0.355 is above every reference graph. The ranking is after the data, has no interval, and the seed-7600 panels share one genome draw. Say "above every reference and selected graph, descriptively" and drop "real" and "N2-specific".

2. **Hub-frozen-shuffle2 does not "lose" the separate states by contribution.** Its S(30) is 0.068, equal to N2's at seed 7700 (0.068), from 4 genomes. The "In short" and roadmap bullets ("nearly vanish") rest on counts. State that two arms lose it and the third keeps N2-level S(30) in few genomes, located half off the core.

3. **"By tick 100 the separate states carry more than half"** (line 217) rests on point estimates 0.58 and 0.63 with no interval, when the tick-30 intervals are ±0.2 wide. Say "by point estimate".

4. **The batch-7 regeneration check leaves no record.** The draft's "no arm failed to regenerate" is evidenced only by the absence of `.skipped.json` and by the raise in `census.py` line 116. The plan says each arm is checked against `batch7.json`; rule 5 wants the match (edge count, triangles, reciprocal pairs, kept fractions) in a file. Add it to the panel record or to the draft as a stated limitation.

5. **Timing source mismatch, minor.** The draft's "48 panels 42,743 s" is `stages.json`; the median and maximum are the per-panel `seconds`, which sum to 42,732. Name both sources or use one.

6. **Interpretation presented as fact, minor.** "C1's gaps are float32 rounding between one batch of 1024 and chunks of 128" (line 57) is plausible but untested; add "presumably".

7. **Nits.** Line 215 reverses the panel order ("13 and 15"); elsewhere it is 15 then 13. "At least a quarter" is a 90%-interval statement, as the plan's own wording, but one clause saying so would help.

Nothing the plan asked for is missing: the per-ensemble φ_O and φ_U are in `split.json` though not in `tables.txt`; the cohort 2×2, cheap rule, radius sensitivity, oscillation periods, unresolved reasons, where-the-states-differ, asymptotic rates and per-chunk costs are all present.

`census_tables.py`: no error in what it prints. Two latent issues: the glob on line 23 would also match a `.skipped.json` and crash on its missing keys, and line 47 would crash on a None share. Neither is triggered.