You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Confirmation pass, read-only, before binding: draft 3 of `experiments/03mc-p4-confirm/PREREGISTRATION.md` and its code
(branch roadmap, commit e136fe3; compare with 8b77b57).

On draft 2 (run 20261016-032746), Fable answered "bind" with small items and Astra answered "fix first" with five
findings. DECISIONS.md D291 lists each finding and its fix. The diff is `git diff 8b77b57 e136fe3`. A fresh CPU smoke
run of every stage on the committed code (e136fe3, clean), with a resume and two reports, is in `runs/p4mc-smoke/`.

Binding freezes this text (only appended amendments after it), and the next stage after binding draws the 640 fresh
graphs, so please check:
1. Is each finding from your draft-2 review fixed, correctly and without a new error?
2. Anything in draft 3's text or code that should change before the text is frozen.

Answer "bind" or "fix first", then numbered findings with file:line, evidence and a proposed fix. Keep to what you
verified; say what you could not check. Please run no GPU work and draw no fresh graph or genome.
