You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a pre-registration for WormWars, an open-science project that evolves brains on
the C. elegans connectome in a small game world. The repository is your working directory; read
`AGENTS.md` for its rules (pre-registration before confirmatory runs, tests that fail before they
pass, exactness only where tested, compute counted, numbers traceable to files).

**What to review:** `experiments/E2-optimizer-screen/PREREGISTRATION.md` (v1), for experiment E2,
"a short optimizer screen": 02's genetic algorithm (GA) against OpenAI-ES, with random sampling as
a floor, at equal additional simulator work, on Task N (E1/04a's navigation task), 8 runs per
method, to choose E3's provisional default optimizer.

It carries `docs/E2/DESIGN.md` v2.2, which you both reviewed three times (your reviews are in
`docs/reviews/20260929-100947-E2-design/`, `...-101958-E2-design-v2/`, `...-102907-E2-design-v21/`;
decisions D117 and D118 in `DECISIONS.md`). At v2.1 Fable said "proceed to pre-registration" and
Astra asked for specification corrections only; v2.2 made them. §13 of the pre-registration lists
where it departs from the design.

**The code it binds** (please read it, not only the prose):
- `scripts/e2.py`: the runner; `REGISTERED` holds every number; `allowance()`, `training_plan()`,
  `decide()`, `select_sigma()`/`select_rate()`, the stage frame `run_stage()`, the rerun rule, the
  extension's resume, the evaluation's hash checks;
- `wormwars/e2/optimizers.py` (encoding, utilities, the ES update, best-since-checkpoint) and
  `wormwars/e2/loops.py` (the batched random-sampling and ES loops, mirroring 04a's
  `wormwars/e04a/evolve.py::evolve_batch`, which the GA uses unchanged);
- tests: `tests/test_e2_optimizers.py`, `tests/test_e2_loops.py`, `tests/test_e2_commands.py`.
  04a's runner `scripts/e04a.py` and its pre-registration
  `experiments/04a-navigation-primitive/PREREGISTRATION.md` are the models it follows.

**Please check, in particular:**
1. Does the pre-registration faithfully carry design v2.2, and are §13's departures acceptable
   (paired starts across methods by a shared run seed; the pilot's pairing; "final" for a training
   stage that stops twice; no mechanical reduction after an over-limit projection)?
2. Does the code do what the text says? Especially: the allowance arithmetic (2 131 968 vs
   2 131 712), the ES update and flat rule, projection only after a real update, the checkpoint
   candidates per method, the champion rule, the extension's resume and its champion over both
   parts, the decision in exact arithmetic (≥ margin, strictly above the GA's median, the floor),
   the incomplete-batch branches, and the hash checks before the hold-out.
3. Are the outcome wordings in §8 complete and unambiguous for every case the code can produce?
4. Id ranges and seeds: disjoint from earlier experiments and each other? Anything exposed?
5. Budget (about 5.0 GPU-hours, cap 7, projection limit 5.5 h for training): plausible?
6. Anything that would let the ES lose, or win, for a trivial reason we have not addressed.

**Answer format:** a verdict first, one of "ready to bind", "revise" or "redesign"; then must-fix
items (numbered, each with file and line or section, and what to change), then suggestions, then
anything you checked and found correct. Be concrete and brief. You are read-only: do not attempt to
edit files or run commands.
