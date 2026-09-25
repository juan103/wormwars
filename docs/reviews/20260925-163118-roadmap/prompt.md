You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Review of a research roadmap for the WormWars repository (branch exp02-screening, commit on HEAD;
local, not public). The owner asked for the team's view before deciding.

Read `ROADMAP.md` (the proposal), then `experiments/03a-self-consistency/DRAFT.md` (the owner's
draft v2 of a self-consistency panel study, designed with Fable 5.1 and reviewed once by Astra 6)
and `experiments/03a-self-consistency/NOTES_FROM_02.md` (what experiment 02 found that bears on it).
Background: `experiments/02-screening/RESULTS.md`, `DECISIONS.md` D038-D043,
`experiments/01b-direction-corrected/RESULTS.md`.

The series asks whether the real C. elegans wiring (N2) is shaped for worm-like tasks. The owner's
framing: "could it be that the worm connectome is optimized for certain wormy tasks under certain
plasticity?" 03a is the owner's own hypothesis: the wiring of a deleted neuron can be partly
predicted from the rest of the brain plus a task.

Questions:
1. The ordering and gates. Attack the four "claims to attack" at the end of ROADMAP.md. Would you
   reorder, merge, or cut any item? Is any gate wrong or missing?
2. 03a draft v2 plus the notes from 02: what must change before its pre-registration tag? Is its
   central logic sound (NIP/MIP arms, refit ceiling and floor, four-way classification, AUC-based
   decision rules)? What is its biggest risk?
3. What is missing from the roadmap entirely: a question, a control, or a cheaper route to the
   owner's question?
4. If you could fund only one item after publishing 02, which, and why?

Numbered points, concrete, with file:line where you can. Be brief about what is fine.
