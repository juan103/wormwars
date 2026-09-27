You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Confirmation: T0 plan v2, and T0 item 1's code

You reviewed T0 plan v1 and the island fixes (`docs/reviews/20260927-17394*-T0/`). Both of you
said "revise". Plan v2 adopts every must-fix: `docs/foundations/T0.md` and `DECISIONS.md` D065.
Item 1 of v2 is now implemented (commit f6af625, D066). You are read-only on branch `roadmap`.

**Please check:**
1. **Plan v2:** are your must-fix and should-fix items resolved? Is anything in v2 wrong, or
   missing?
2. **Item 1's code:**
   - `wormwars/brain.py`: `Genome.PARAMS`, `with_params`, `cat`, `assign`, `clone`, `select`;
   - `wormwars/evo/evolve.py`: `breed`, `_breed_islands`, `_migrate`, and the champion and
     saved fitness at the end of `evolve`;
   - `wormwars/evo/coevolve.py`; `wormwars/deletion.py`; `wormwars/exp02/probes.py`;
   - `wormwars/evo/genomes.py`: `genome_hash` and the load-time check;
   - `wormwars/world.py`: the jitter noise (`_keyed_uniform`, `_hash32`, `_mul32`, `_mix32`);
   - the tests: `tests/test_t0_pairing.py`.
   Is each change correct? Does any change alter results that were not meant to change? In
   particular:
   - the non-jitter rollout path;
   - one-island evolution, apart from the champion now being the final generation's logged
     best;
   - loading of committed genomes.
   Is the jitter hash sound: correct 32-bit arithmetic, no correlations between streams, points
   or ticks that matter at this use, and uniformity good enough?
3. **Is the claim about 02's jitter estimates in D066 correct?** They are "unaffected in
   expectation, not bit-reproducible".

End with one line each:
- "T0 plan v2: confirmed" or "not yet";
- "item 1: accept" or "not yet".
