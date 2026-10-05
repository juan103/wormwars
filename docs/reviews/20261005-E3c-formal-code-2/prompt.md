You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3c's formal stages: recheck of the fixes and Amendment 1, before about 21-25 GPU-hours

You are reviewing, read-only, the WormWars repository in the current directory, at commit 9d76251 (branch
`roadmap`).
- **Your code review** of the formal stages is in `docs/reviews/20261005-E3c-formal-code/`. Both of you said
  "fix first".
- **D211** lists what was taken.
- **Amendment 1** is in `experiments/E3-ab-organism/E3c/PREREGISTRATION.md` §14, dated, before any formal
  stage ran. The text before §14 is unchanged; its hash is pinned.

**The changes, in short:**
- `train-smod` and `train-sdense` are separate stages (Fable);
- populations are saved before the checkpoint plays;
- a rerun reuses a completed, hash-verified training;
- later stages read stopped records through their salvage, under §5's eligibility (minimums, exclusions, the
  undefined cases);
- the report runs after the cap;
- every wey's path in both conditions is saved locally;
- partial records in every stage;
- the consistency check compares hashes and per-maze counts, and refuses;
- `train-sdense` and `train-psel` follow in order;
- benchmark training ids are pre-flighted;
- the projection counts 23 checkpoint plays per batch;
- the report adds the missing §7 outputs and the qualifiers inside the labels;
- the pre-registration is guarded, and its registered text pinned in every marker.

**The tests:** `tests/test_e3c_stages.py`, `tests/test_e3c_formal.py`, `tests/test_e3c_stats.py` and
`tests/test_e3c_power.py`. Among them:
- every eligibility case Astra reproduced;
- the margin labels;
- the stop-and-rerun test, where retraining is made to fail;
- sabotage checks;
- a full CPU smoke of all eight stages.

They pass; the full suite is running.

**Please answer:**
1. Is each of your required defects fixed correctly? Name any that is not.
2. Is Amendment 1 sound, and does the code implement it? Does anything in it weaken the registered
   protections?
3. Did the fixes introduce a defect?
4. **Your verdict:**
   - "run it";
   - or "fix first", with required changes only.
