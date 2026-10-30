Verdict: **fix first**, small wording edits only, plus one condition on the merge commit. Every number in the diff traces to a committed file. The problems are two overstatements, one untraceable figure, and one stale line.

**Checked** against M4E-RESULTS ("In short", the reading table), M5-POWER-RESULTS (section 5), M6-0-RESULTS ("In short", comparisons, fading profile), M6-3-LITERATURE ("In short", sections 3 to 6, "What this means"), SYNTHESIS (table, annotations), `summary.json`, D377, D378, M6-OPTIONS, and the reflogs of `main` and `roadmap`. These match: 1 of 102 against 5 of 408; the fixed wording quoted verbatim; "shortened" with "relative to its own size"; about six times drift's at the start (0.161 against 0.026); a few tens of ticks (median τ_stay 39 to 46.5); N2's 260 edges; "lowers" by a thin margin; 0.004; 110 to 160 hosts and 72 to 91 CPU hours; RMD from one report with its mechanism open; the phase memory the probe does not assay; multistability known in earlier models; RIA as an integrator; D366 to D378 are the 13 commits since `main` at 7a6036f. The quoted owner's order matches D378's listed options.

Findings, in order of weight:

1. **ROADMAP "The thread worth following" note: "a fading transient of a few tens of ticks, not a switch (M6-0)".** Overstated. One g39 champion is a switch on the primary bank, and M6-0-RESULTS says in so many words that the result "does not show that switch-mediated behaviour is absent: the primary bank holds one switch champion". Fix: "for 101 of the 102 champions a fading transient of a few tens of ticks, not a switch".

2. **README row and ROADMAP bullet: "selection on T1 did not make switches more common than drift".** The fixed wording is "We did not detect enrichment". The interval's upper bound, +0.013, is above the drift rate itself (1.2%), so an enrichment of that size is not excluded. The ROADMAP bullet quotes the fixed wording beside it, which saves it. The README row has no such quote. Fix the row to "no enrichment of switches was detected (1 of 102 champions, against 5 of 408 drift genomes)". The already committed README annotation at line 64 carries the same phrase; a reader of `main` will see it, so bring it to the same wording in this commit or leave it with the row corrected.

3. **ROADMAP "Next": "about 1 to 5 CPU hours" for the foraging test.** Not traceable to any committed file. The only committed "1 to 5 CPU hours" is option 0's cost in M6-OPTIONS and the M6-0 plan prompt. Option 5, the nearest thing to the foraging test, says only "small (CPU hours)". Either record the estimate and its source in D379 or drop the number (rule 5).

4. **D379 is cited twice in the new text and does not exist in DECISIONS.md.** Fine if the merge commit writes it, as D365 did, quoting the owner's order. State this as a condition of the merge, not an afterthought.

5. **README "Next on the roadmap" (line 64) ends "Next is the owner's choice."** The owner has chosen. A `main` reader finds the order only in ROADMAP. Add a dated annotation with the three steps, or a pointer to the 30 October entry.

6. **"no effect of 0.004 or more" (README row, ROADMAP M4e bullet).** M4e's size field reads "no effect of 0.004 or more, as a mean across these ten hosts (a response confined to a minority of host graphs may be missed)". The qualifier is dropped in both places. Add "as a mean across ten hosts".

Low, only if convenient:
- "a bounded, verified literature check" (ROADMAP bullet). "Verified" is the project's own term from M6-OPTIONS, but M6-3 itself says an exact match "verifies the transcription, not the context", 13 of 44 sources are abstract-only, and two context errors were caught in review. "A bounded literature check, its quotes checked against the sources" is safer.
- The RIA note in ROADMAP: M6-3's own sentence is "No source checked shows it holding a state, and none excludes it". The note keeps the first half only, which reads as evidence against.
- The README row now says M6 was done "the same way" with "one disclosed exception". M6-0's plan discloses a 16-genome timing spike seen before the plan. It is labelled and included, so this is a judgment call.

**Q3, what should not go to `main`:** nothing found. The full texts of M6-3's sources are not committed; `reading/` holds metadata, scripts and short attributed quotes. M4e's `blocks.json` and M6-0's state files and 02's genomes stay local. The untracked `runs/ci-*` and `runs/consult-*` logs do not merge.