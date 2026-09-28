You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are checking public documentation in the WormWars repository (your working directory), a research codebase: C. elegans connectome-wired rate brains evolved in batched PyTorch worlds, with pre-registered experiments. The repository is public on GitHub. The owner asked for clearer documentation so that others, people and AI agents, can understand, reproduce, extend or overtake the work, because compute is the project's bottleneck.

New or changed on branch `roadmap` (see `git show --stat HEAD` and the commit's diff):
- a README.md in every experiment folder: `experiments/01-foraging-n2-vs-controls/`, `01b-direction-corrected/`, `02-screening/`, `02b-champion-analysis/`, `03-generation0/`, `03r-replication/`, `03a-self-consistency/` (a draft, not run);
- `AGENTS.md` (repository layout and the rules the work follows);
- the main `README.md`: a "Start here" list, an "Experiments at a glance" table, a "How to help, or get ahead of us" section, links to the experiment READMEs, and a corrected Status section;
- `ROADMAP.md`: a dated status block (28 September) and an amendment to T1's gate.

These READMEs summarise; the sources of truth are each folder's RESULTS.md, PREREGISTRATION.md, DESIGN.md, DISCLOSURE.md, CORRECTIONS.md, the committed JSON files, DECISIONS.md, and the code in `scripts/` and `wormwars/`. The drafts were written by Claude subagents and edited by Claude Opus 5.5; numbers have been this project's most frequent source of error.

Please check, against the sources:
1. **Every number and every claim** in the new READMEs and the changed main README and ROADMAP text. A README must not make a claim its sources don't make, must not round differently, and must quote registered wordings exactly. List each discrepancy with file:line and the source.
2. **Registered and fixed wordings:** 03r's outcome sentence, 02's verdict, 01b's registered claims, the D063 amendment. Are they quoted exactly and not weakened or strengthened anywhere, including in the main README's one-line table?
3. **Reproduction commands:** do the subcommands and flags exist in the code at the commit each README names? Would the described procedure work from a fresh clone? (For 03 and 03r a new `scripts/exp03.py rebuild-graphs` subcommand regenerates the uncommitted graph files from the committed `ensembles.json` and checks each against `graphs_manifest.json`; a full rebuild of both instances was run to verify it, see DECISIONS.md D087 if present.)
4. **Fairness and completeness of caveats:** corrections, deviations, disclosures, what each result does not show. Is anything important missing or softened?
5. **AGENTS.md:** are its rules accurate descriptions of how this repository actually works? Anything false or overstated?
6. **Privacy and data:** no email addresses, no personal data beyond what the main README already states, no connectome data or instructions that would redistribute it.

Finish with one line: "Docs: ready to publish", "Docs: ready with fixes" (list them), or "Docs: not yet" (list the must-fix items). Be concrete; cite files and lines.
