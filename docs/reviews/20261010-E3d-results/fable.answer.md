Everything I need is in hand. Writing the review now.

## Review of E3d's results draft (d29fb3a)

**Verdict: fix then publish.** The registered verdict is the one the bound procedure gives, and the draft's numbers trace to committed files with three exceptions. The fixes are wording and traceability, not substance.

### 1. The verdict, recomputed

I recomputed all six criteria, the precondition and the feasible-share floor at each k_r from the gate quantities in `report.json`. Every value matches the draft's table. B_max is the maximum over every blind member including the 28 noses-removed champions, and the random walk holds it at each k_r. G1b fails alone, so `choose_k` returns "failed at calibration" with G1b named at 0, 2 and 4. The confirmation, tree reference and tangent diagnostic were correctly not played.

The failure is not marginal. The walk's 128 per-maze colony means at k_r = 0 have a spread of roughly 0.75, so the standard error of B_max is about 0.07, and 2.34 sits about five standard errors above 2.0. That is my rough estimate from the raw list, not a committed number.

### 2. Numbers: three to fix

1. **The seed at k_r = 0 is 9.01, not 9.02.** The record says 9.0146.
2. **"No visit at all (0.00 for every one, at every k_r)" is false.** Four S-mod champions made one or two visits over 1 024 weys at k_r = 0, and one did at k_r = 2. S-dense made none. The table's "0.00 (all 16)" is right to two decimals. Say "at most two visits in 1 024 weys" and correct D229's prose to match.
3. **"Refused in 3 s" is not in any committed file.** The only record is the local attempt file, which shows 2 s of wall time and 1.2 s timed. Drop the duration or cite the compute record's listing without one.

Two numbers are right but need a pointer. The E3c noses-removed range 6.59-6.79 traces to the per-champion values in E3c's `report.json`, but E3c's RESULTS.md shows that same range only under "trails off", so cite the file. The "0.25 h reserved" is 0.254 in `project.json`, which includes elapsed time, and is fine rounded.

### 3. Overclaims and omissions

- **"Not by following a ring"** goes beyond the record. The at-visit field gives the last component touched, not whether anything was followed, and the walk has no following behaviour to test. Keep the counts and drop the clause.
- **The trails-off follower is the missing fact.** At 2.93, 2.39 and 2.37 it sits within 0.6 of B_max. On this family, scent alone barely beats a random walk, and "navigation pays" means trail-following. The draft mentions it in one aside under the blind table. It belongs in the exploratory section, because it is what E4's navigators would face.
- **"Revisit G1b's absolute level"** should carry the round-trip share. The walk completes a round trip for 41-45% of its weys. A limit that admits it admits a blind control averaging more than one leg. The text is honest that the threshold cannot rescue E3d, but without that fact the bullet reads as an invitation.
- **"The horizon change was set aside before"** is not traceable. I found only D220's note that the horizon idea is untested. Cite or soften.
- **The S champions' collapse** is read carefully. One more difference is worth naming: the spawn rule changed too, not only the size and the family.

### 4. Missing against the design

1. **§6's records** are "reported on every block", but the draft reports throughput for a few members and contact for the walk only. Discovery, occupancy, later-leg rate, zero-visit share, first component and switches by class pair are in `calibrate.json` and unreported. One sentence naming those fields as the calibration block's §6 report would satisfy rule 5. The same for §5's "each blind member's round-trip share".
2. **§2's scent-reach split** was not computed, since the report stage builds it only on confirmation. The per-goal arrival data exist in `calibrate.json`. Compute it as exploratory or say plainly that it was not computed and why.
3. **A bootstrap on B_max** is not required at calibration. An exploratory interval would show readers that the failure is not a rounding accident.
4. **The README** lists D221-D228. D230 changed the hygiene guard for this folder's `calibrate.json` and should be listed.

### 5. What is sound

The procedure, the bound-text citations, the commit hashes, the g-e composition, both reviewers' "run" verdicts, the compute total, the blind-family table, the round trips, the coverage and maze-ness figures, and the at-visit counts all check out. "Nothing was tuned on these results" is consistent with the record.