You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing code in WormWars, an open-science project that evolves brains on the C. elegans
connectome. The repository is your working directory; read `AGENTS.md`.

**What to review:** E3a's implementation (`roadmap` branch, commit 910fc7e), against its bound pre-registration
(`experiments/E3-ab-organism/E3a/PREREGISTRATION.md`, bound at 989da99; D165). Nothing has run on
registered worlds except what D166 discloses. The formal run starts only after this review.

**The code:**
- **The library:** `wormwars/e3/` (`task.py`, `organism.py`, `samplers.py`, `latch.py`, `probe.py`,
  `assays.py`, `readings.py`, `controls.py`).
- **The engine changes:**
  - `wormwars/world.py`: the shuttle task, `_build_shuttle`, `_shuttle_signals`, `_advance_shuttle`,
    `shuttle_events`, and `current_target`;
  - `wormwars/brain.py` (`Brain.clamp`);
  - `wormwars/graft.py` (`combine`, `nose_entry`, `probe_on`);
  - `wormwars/config.py` (the shuttle settings, omitted from `to_dict` while unset);
  - `wormwars/interface.py` (`KNOWN_SIGNALS`);
  - `wormwars/evo/rollout.py` (the shuttle's score, events and zero progress).
- **The runner:** `scripts/e3a.py` (its 14 stages, inside E2's stage frame `scripts/e2.py`).
- **The engine check's CPU leg:** `scripts/e3_equivalence.py`, with its reference
  `experiments/E3-ab-organism/E3a/development-records/equivalence-reference.json`.
- **The tests:** `tests/test_e3_*.py` and `tests/test_e3a_script.py`.
- **The development runs:**
  - a smoke of every stage at toy sizes passed (CPU, `runs/e3a-smoke/`, local);
  - the engine comparison against a worktree at 989da99 was identical in every case, and failed at tick
    0 under a deliberate sabotage.

**Please answer:**
1. A verdict: "run", "fix then run" (list the fixes), or "revise".
2. Does the code do what the pre-registration says? Check especially:
   - the event contract and level timing;
   - the start cue;
   - the geometry rule;
   - the samplers and their ties, and the mutation masks;
   - the probe (q, RA and RB held);
   - the memory assays and classes (windows, tolerances, the assignment rule, the release start);
   - the reset timing;
   - calibration;
   - the champion rule;
   - random sampling's world pairing;
   - the readings and their wording;
   - admission and the reductions;
   - the end-of-run assertions.
3. Anything that would change an outcome, crash a formal stage, or touch registered worlds or seeds
   before their stage. Name the file and line.
4. Whether any engine change could alter earlier tasks, beyond what the equivalence check covers.

Be concrete and brief. You are read-only: do not edit files.
