You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review request: 04a's pre-registration, draft v1

You are reviewing a pre-registration before it is bound, pushed and run. The repository is
WormWars (an evolutionary-simulation project on the C. elegans connectome). You may read any file in
the working directory; you cannot run anything.

## What to read

- `experiments/04a-navigation-primitive/PREREGISTRATION.md` — the draft under review (v1).
- `scripts/e04a.py` — the runner. `REGISTERED` holds every number; the rules are applied mechanically.
- `wormwars/e04a/evolve.py` — several independent evolutionary runs in lockstep, as one batch.
- `wormwars/evo/rollout.py` — changed so a rollout takes one row of world ids per strain, and returns
  progress and the final head position.
- `wormwars/registration.py` — E1's guards as shared functions.
- Tests: `tests/test_e04a_evolve.py`, `tests/test_e04a_commands.py`, `tests/test_registration.py`,
  and the new tests at the end of `tests/test_e1_task.py`.
- Context: `docs/E1/DESIGN.md` ("04a"), `experiments/E1-navigation/PREREGISTRATION.md`,
  `experiments/E1-navigation/RESULTS.md`, `DECISIONS.md` D100-D103, and your own E1-results reviews
  in `docs/reviews/20260928-194709-E1-results/` (the list of what 04a's registration must take).

## What E1 established (for orientation)

E1's positive control passed: a scripted stereo navigator reached 8.68 targets per 300-tick episode
on 1 024 unseen worlds (98.7% of an oracle), 0.03 with a mirrored decoy; blind baselines reached at
most 0.65. 74% of 256 random N2 genomes scored zero on all 64 pilot worlds (mean 0.031). E1 measured
04a's training shape at 4.676 s per rollout of 256 strains × 8 worlds.

## Questions

1. **Does the draft take everything the E1-results reviews asked of 04a's registration** (Task N
   frozen and hashed; baselines re-run paired on 04a's hold-out; an exact bounded shaping formula,
   training only, with an unshaped arm; a committed budget with a margin and a cap; compositions;
   per-run streams; generation-0 baseline; gain against the curve with no threshold; runs as the
   unit with a declared passing share)? Is any of it done wrongly?
2. **The shaping formula and its bound:** is count + 0.5 × (final progress on the unfinished leg,
   clipped to [0, 1]) sound, and can it be gamed (for example, by never finishing a leg, or by
   parking near a target)? Is c = 0.5 a reasonable fixed choice?
3. **Batching and independence:** do the lockstep batches keep runs independent and reproducible
   enough for runs to be the unit (`evolve_batch`, the rollout change, the seeding)? Anything in the
   code that couples runs?
4. **The champion and the generation-0 baseline:** champion = the first checkpoint with the best
   mean on 64 shared validation worlds over 41 checkpoints; baseline = the generation-0 checkpoint.
   Are these fair, and is the validation set large enough?
5. **The rules and the outcome:** the per-run rules (E1's three plus beating generation 0 by a lower
   bound above 0.5), and "04a: passed" at 6 of 12 shaped runs. Right thresholds? Anything missing
   (for example a correction for 16 per-run tests, or a rule that the champion must beat S-const at
   some level)?
6. **The budget and guards:** 1 000 generations × 2 batches at the measured 4.749 s, cap 6 GPU-hours,
   a guarded projection before the formal stages, no resume. Enough, or too little evolution for the
   question? Are the guards and their tests adequate; which untested paths matter?
7. **Anything else** that would make the result uninterpretable or overclaimed.

Please end with one line: **"04a pre-registration: ready to bind"** or **"04a pre-registration:
revise"**, and list must-fix items separately from suggestions. Say which claims you checked in the
code.
