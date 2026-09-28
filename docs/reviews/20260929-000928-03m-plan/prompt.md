You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Review request: 03m, an exploratory plan for what drives P4 (plan v1)

This is the WormWars repository, in a worktree on branch `p4-mechanism`. You may read any file; you
cannot run anything.

Read: `experiments/03m-p4-mechanism/PLAN.md` (the plan), `scripts/p4m.py` (its runner),
`experiments/03m-p4-mechanism/tradeoff.json` (Q1's output, already computed from committed data).
Context: `scripts/exp03.py` (03's runner: `measure_graph`, `signals`), `wormwars/exp03/measures.py`
(`history`), `wormwars/deletion.py`, `experiments/03-generation0/PREREGISTRATION.md` and
`RESULTS.md`, `experiments/03r-replication/RESULTS.md`, `ROADMAP.md` (Track B), and DECISIONS.md
D080 onward.

The plan is exploratory, not a pre-registration: it declares its analyses before running them, and
a confirmatory study would follow with its own registration. Please judge:
1. **Q1's reading:** is the trade-off (within-ensemble Spearman, N2's residual above a trend in log
   response) sound, or an artefact, for example of the ratio's construction or tanh saturation?
   What would you check first?
2. **Q2-Q5:** do the deletions, synapse-type conditions, the long window and the weight permutations
   answer the roadmap's questions (where the effect lives; gaps or chemical synapses; what gives N2
   its strong response)? Are the "lead" criteria sensible? Anything missing that is cheap?
3. **The code:** does `p4m.py` reproduce 03's measurement faithfully (genomes, bank, config, read-out)?
   Any bug, for example in batching deletions (`history_in_chunks`), the pairs, the excluded read-out
   neurons, or the decay curve?
4. **Anything overclaimed** in the plan's text.

End with one line: **"03m plan: ready to run"** or **"03m plan: revise"**, must-fixes separate from
suggestions, and say what you checked in the code.
