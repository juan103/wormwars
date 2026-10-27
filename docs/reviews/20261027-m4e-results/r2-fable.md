**Verdict: fix then publish.** Every number I could check traces to the files, and the round-1 fixes are in. One of them is wrong, and it is mine: draft 2's explanation of why Δ_count's envelope clears zero attributes it to the wrong arm. The rest is minor wording and attribution.

## What I verified against the files

- **Readings, intervals, envelopes, per-host counts, class totals, transitions, first-pass numbers:** all match `readings.json`, including the interaction envelope's +0.0001, U_HH's 5 then 3 and U_LH's 59 then 39 unresolved (summed from the log's per-panel lines), and the audit's 783 to 800. Zero-event bounds recompute to 0.00374 and 0.00382, and 2995 for 0.001.
- **Blocks table, S1 to S3 ranges, autapses, the S3 medians 1.47, 1.45, 1.53, 1.71, "9 to 23 times" (26.52 / 2.862 and 26.52 / 1.142), the digest prefix, "matched" in all 20 draws:** match `blocks-summary.json`, `tables_log.txt` and `m4e_log.txt`.
- **Predictor medians, AUCs, both bands' counts and shares:** match `tables.json`. Two U_LH genomes are saved as exactly 1.2, so 7256 is plausible but I could not recount at full precision.
- **Dose:** excluded hosts, the four fitted, slope, deviations and "3 of the four" (W's S2 exceeds U_LH's in 6 of 10 hosts overall but in 3 of the 4 fitted) match.
- **Compute, dates, commit, clean tree, panel range 517 to 1660 s:** match. 32.7 h is just under 33.
- **M5 inputs:** T − K host SD recomputes to 0.00547, M4d's T − R to 0.00353, the identification interval to −0.00166 and +0.00518, the SD multiplier 0.69 to 1.83, and the host counts agree with both reviews' tables. M4d's +0.0059, 64, 4 and 10 of 10 match its results file.

## Findings, ranked

1. **"It clears zero because the second pass settled 2 of U_HH's 5" is wrong. I proposed that mechanism in round 1 and did not check it.** The envelope is the maximum over all 2¹⁰ corners of the Student-t bound, and the first-pass upper bound did not come from the all-for-U_HH corner. Per host, in genomes of 1024, the first-pass all-for-U_HH corner is −6, −3, −3, −2, −2, 0, 2, −2, 0, −6, whose t upper bound is already negative. Switching SH-recip-2051101 alone to its other end (its 11 unresolved U_LH genomes as separate states, −6 to −17) raises the spread enough that the upper bound becomes +0.47 of 1024 = +0.00046, which is the reported first-pass envelope. After the second pass that host's U_LH unresolved fell from 11 to 5; the same corner gives −0.41 of 1024 = −0.00040, the reported envelope. Counterfactually, settling U_HH's 2 alone leaves that corner at about +0.0002 (zero not cleared); settling recip-2051101's 6 alone gives about −0.0001 (cleared). So the direction stands because the second pass settled U_LH's unresolved genomes in the host that carried the most of them, with U_HH's 2 contributing little. Rewrite the "In short" sub-bullet accordingly, and confirm with the reader rather than my hand arithmetic (I used the t bound only; the bootstrap ends are lower at both passes). The "only just" and "about four genomes" stand.

2. **"Both reviewers reproduced the readings, the tables and the block file's digest independently" overstates my round 1.** Astra's review says it regenerated the constructions and reproduced the readings in memory. Mine says it checked every entry against the committed files, summed the panel times, and matched the digest. Say that.

3. **The threshold-like bullet needs the gap stated.** No arm has S3 between 0.96 and 1.26, so the arms cannot locate a threshold or tell a step from a steep rise. "That is why Δ_weight is flat" turns the description into an explanation; "Δ_weight compares two arms on that floor" is what the data show. And "the predictor bands show the same floor below 1.0" rests on 354 to 629 strong-arm genomes below 1.0 with 0 to 3 switches, and the within-arm AUCs are 0.41 to 0.66, so the per-genome predictor neither confirms nor refutes a step. Say so in one sentence.

4. **The in-band medians 1.38, 1.39, 1.42, 1.46 are not in any committed file.** `tables.json` has only each arm's overall median and the band counts. They are Astra's computation. Either add them to `m4e_tables.py`'s output or attribute them and say they can be recomputed from the saved per-genome values (five decimals is enough for two).

5. **W − U_HH's envelope clearance is thin too.** Its lower bound of 0.0005 is about five genomes. The roadmap's first bold claim rests on Δ_count and W − U_HH together; both should carry the caveat, not only Δ_count.

6. **Small numbers.**
   - "About a third of the unresolved genomes" is 56 of 201, which is 28%. Give the counts.
   - "About ten cheap draws per block" needs its tolerance: 3 of 20 K draws at or above 1.67, so matching within 0.05 of 1.71.
   - "U_HH is the lowest of the eight arms" and U_HH − I −0.0008 are pooled; in nine hosts I and U_HH have 3 and 2, and SH-recip-2051100 (9 against 2) makes the difference. Fine as a description, but say that U_HH − I has no interval in `readings.json` and is dominated by one host.

Everything else in the round-2 list is done as described: Astra's coupling wording, the ladder, the interaction's caveat, the predictor's definition and rounding note, the entangled-features list, the T − K package, the two estimands, the identification interval, the decomposition, the qualified allocation, the orientation-only host counts and the simulation instruction, the audit bounds, the envelope's limit, the floor wording and the reported byte check. No new overreach beyond items 1, 3 and 5.