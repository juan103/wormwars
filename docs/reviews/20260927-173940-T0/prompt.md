You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review: roadmap v3's T0 (correctness on the path we use)

The owner has delegated roadmap v3 (`ROADMAP.md`, see "T0: correctness on the path you use").
Decisions where Claude and both of you agree go ahead, and the owner is informed; disagreements go
to the owner. You are read-only on branch `roadmap`.

**Please review two things.**

**1. The island-path fixes already made** (commit 54ad0a9, `DECISIONS.md` D064):
- the code: `wormwars/evo/evolve.py`, specifically `evolve`, `_breed_islands` and `_migrate`;
- the tests: `tests/test_evo_islands.py`, and the correction to `tests/test_evolve.py`.

Please check:
- Are the three bugs real?
- Are the fixes correct and complete?
- Did the fixes change the single-island path, which every published run used?
- Are there other island-path bugs?

The roadmap says three were "suspected from reading the code", but no record says which. Do the
three found here plausibly match what a careful reader would find?

**2. The T0 plan:** `docs/foundations/T0.md`.
- Is it complete against the roadmap's T0 text?
- Are the accounting choke points right? Check `wormwars/evo/rollout.py` `_play`, `wormwars/brain.py`
  `Brain.step`, and any other place a World is built or a Brain is stepped: calibration, the exp02
  and exp03 probes, and exp03's measures.
- Is the declared CUDA tolerance of 1e-4 sensible, and should the energy-ledger bound be fixed now?
- Is anything missing that would let a pairing or inheritance bug through?

**Answer format:** findings ranked **must fix**, **should fix**, **minor**, each with the file,
the line and the evidence. End with one line each:
- "island fixes: accept" or "not yet";
- "T0 plan: proceed" or "revise".
