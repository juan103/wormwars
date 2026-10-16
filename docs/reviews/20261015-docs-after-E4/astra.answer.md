**fix first**

1. **[ROADMAP.md:26](D:/Claude/random/wormWars/ROADMAP.md:26) — The unevolved-duplicate control did run.**  
   `docs/E4/E4-DESIGN.md:233` explicitly identifies it as E-G. E4’s `RESULTS.md:38` reports generation 0, and `pilot-attempt1-summary.json` records its mean as 6.2265625. E-G also appears in the diagnostics and evolutionary E4-D controls. **Fix:** remove this control from the “has not run” list; distinguish completed exploratory controls from the abandoned formal comparison. Correct D282’s corresponding description.

2. **[ROADMAP.md:15](D:/Claude/random/wormWars/ROADMAP.md:15) — The inventory is incomplete against original v3.**  
   At `4e40471`, “Later biology questions” already included topology × optimizer × normalisation, activity-anchored fitness, a neuromodulatory layer, and temporal versus stereo sensing with scripted controls. These remain listed at lines 599–605, with no completed studies recorded, but disappear from the new inventory. Conversely, the pruning protocol was added later under D144, not planned at `4e40471`. **Fix:** include the outstanding later-biology directions, and distinguish original-v3 commitments from subsequent amendments—or explicitly label this a selective summary.

3. **[ROADMAP.md:28](D:/Claude/random/wormWars/ROADMAP.md:28), also line 642 — The survey’s absence does not establish that its corrections were never applied.**  
   I found no committed survey v2. Original v3 says a survey existed with corrections pending; that does not establish its current state outside the repository. **Fix:** say “Survey v2 is not committed here; completion of its corrections cannot be verified from this repository.” I could not check the external survey.

4. **[README.md:709](D:/Claude/random/wormWars/README.md:709) and [docs/REVIEW_TRAIL.md:130](D:/Claude/random/wormWars/docs/REVIEW_TRAIL.md:130) — The machine-caught-error counts disagree and omit documented cases.**  
   The README says two, naming D106 and D279. The trail says three, naming episodes 16, 27 and part of 46, but omitting D279. I checked those rows and D279: together they describe at least four distinct cases. **Fix:** use “Examples include…” without an exhaustive count, or reconcile both summaries and include D279 in the trail summary.

5. **[AGENTS.md:82](D:/Claude/random/wormWars/AGENTS.md:82) — The CPU qualification is supported, but its correction record does not satisfy rule 4’s quotation requirement.**  
   The parent says “CPU runs repeat exactly”; this commit replaces it with a narrower claim. D202/D218 support that narrowing. However, neither D282 nor the new reproducibility annotation quotes the replaced claim. **Fix:** append a dated correction quoting “CPU runs repeat exactly” and explaining the machine/platform and composition limits. The corrected rule itself can remain.

6. **Living pages still contain stale next-step statements.**
   - **[README.md:154](D:/Claude/random/wormWars/README.md:154):** “The owner chooses the next construction” after E3d. D236/D241 document the subsequent E3e/E3f results. **Fix:** link those completed successors.
   - **[README.md:233](D:/Claude/random/wormWars/README.md:233):** Task N “is diagnosed next.” E2d already performed that diagnosis, recorded in D138. **Fix:** use past tense and link E2d.
   - **[experiments/E3-ab-organism/E3b-1/README.md:102](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/README.md:102):** asks what organisms use “in place of the designed selector,” immediately after adding evidence that they still use its switching. E3b-2’s results and D197 establish that distinction. **Fix:** narrow the open question to how the tuned comparators operate.

I verified that the commit changes only documentation, leaving registered texts, results and archived reviews untouched. The local `main`/parent difference is confined to README’s banner. E4’s added headline figures agree with the committed records; I also recomputed the 32-run mean and checked the recorded cut/E-G outcomes. No broken targets appeared among 296 relative file links or 31 heading fragments checked.

I did not rerun simulations or smoke commands, independently verify GitHub receipt times, or verify D282’s claimed earlier smoke/link-check executions.