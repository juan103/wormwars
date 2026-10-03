You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Review E3b-1's pre-registration, draft 1, in this repository (WormWars, branch `roadmap`): `experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md`. Its design is `docs/E3/E3b-1-DESIGN.md` v2, which you confirmed: see its section "v2, as confirmed", D183, and your reviews in `docs/reviews/20261003-E3b-1-design*/`. Read files to check claims; you cannot edit anything. Answer in English, concisely.

Check:
1. Does it carry the design, and every pin from "v2, as confirmed", faithfully?
2. Is every registered rule fully specified and computable from what the stages record? Any ambiguity that would let a reading be chosen after seeing data? Check especially:
   - the gate's formula and its labels;
   - the three secondary tests' statistics, directions and Holm family;
   - the champion rule and the read points, against `wormwars/e04a/evolve.py`;
   - the evaluation roster and conditions;
   - "not read";
   - admission and the cuts.
3. Are the fixed inputs' hashes right? Compare them with `git show HEAD:<path> | sha256sum`.
4. Is the budget arithmetic right, against `experiments/E3-ab-organism/E3b-0/timing.json`?
5. Anything missing that must be registered before binding?

Verdict: "bind after fixes" (list them; no further round needed), or "revise" (another round).
