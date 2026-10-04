You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Results review: E3b-2 (where E3b-1's gain comes from; exploratory)

You are reviewing results in the WormWars repository (your working directory). You may read any file.

**E3b-2 has run.** You reviewed its plan (three drafts), its code and the confirmation pass:
`docs/reviews/20261004-E3b-2-*`, and D193-D196 in `DECISIONS.md`. The plan is `docs/E3/E3b-2-PLAN.md`
(draft 3).

**The records:** every stage record, the per-maze chunks (`chunks/*.npz`, each with its specification) and
`summary.json` are committed in `experiments/E3-ab-organism/E3b-2/`. The draft write-up is `RESULTS.md` in
the same folder.

**The question:** is `RESULTS.md` correct, complete and fairly worded against the plan and the committed
records, so that it can be published?

Please check each number against `summary.json` or the chunks, not against the text. Look especially at:
1. **The central reading.** It says the selector is in use (the latch clamps cost nearly everything, and the
   latch switches after every visit), and that the gain sits in co-adapted comparator parameters (the
   sensing × gating interaction). Is each supported, and stated with the right limits? The plan's §9 rules
   and its non-binding §6 reading apply.
2. **The latch-switching measure.** Is "switches after every visit" meaningful, given that the latch is
   driven by the visit relays by design? Is the clamps' cost the right companion?
3. **The hybrid attribution.** The text interprets the large negative reversions and transplants of sensing
   and gating, and the hybrids below W2 alone. Is it fair, and is the off-path caveat strong enough?
4. **The lesion table and the trail split.** Check the numbers, the units and what is claimed. Note the "nose
   inputs removed" naming: the lesion removes the trail and the path-distance scent together.
5. **The checks** (bitwise exactness, the resting-turn check, the replication) and the compute.
6. **Anything missing** that a reader, or the next design decision, needs. The plan's §5 lists every
   reported reading.

Please end with a verdict: "publish", "fix then publish" (listing the fixes), or "revise".
