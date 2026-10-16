You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Narrow confirmation pass, read-only, before binding: only the changes from draft 3 (e136fe3) to draft 4 (e728abe) of
`experiments/03mc-p4-confirm/PREREGISTRATION.md` and its code. The diff is `git diff e136fe3 e728abe`; DECISIONS.md
D292 lists what changed and why (your draft-3 findings, run 20261016-034232). A CPU smoke run on e728abe, including a
resume that continues from a partial record (10 units removed, then measured again), is in `runs/p4mc-smoke/`.

Please check only:
1. Are your draft-3 findings fixed, correctly and without a new error?
2. Does anything in this diff need to change before the text is frozen?

Answer "bind" or "fix first", then numbered findings with file:line and evidence. Please run no GPU work and draw no
fresh graph or genome.
