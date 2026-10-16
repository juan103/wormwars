You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are reviewing a research design in the repository you can read (read-only). Please review
`experiments/03a-self-consistency/DESIGN.md` (design v4, commit eeeeb60 on branch `roadmap`).

Context:
- 03a tests the owner's "self-consistency hypothesis": delete a neuron X from an evolved brain on the C. elegans
  connectome, reinsert it with random wiring, search only X's wiring for a task, and see whether its original
  partners come back. Draft v3.2 (`experiments/03a-self-consistency/DRAFT.md`), a 24-neuron panel, was reviewed by you
  both in September (`docs/reviews/20260925-*`, DECISIONS D045-D047) and never ran: it needed about 785 GPU-hours.
- The owner then fixed a six-neuron proof of concept (3 high, 2 medium, 1 low foreseeable relevance) capped at 72
  GPU-hours, pilot included (DECISIONS D094; ROADMAP.md, section "03a: redesign after 03r, before any confirmatory
  run", which also lists what the redesign must keep and change).
- Since then: P4 (a history dependence of N2's random brains) replicated three times; 03mc confirmed that RIA and AIY
  carry its response (`experiments/03mc-p4-confirm/RESULTS.md`). Task N, the one-wey navigation task, was built and
  evolved on (E1, 04a, E2, E2d). Throughput records are in those experiments' `compute-record.json` and
  `projection.json` files and `docs/foundations/T1.md`.
- Code you may want: `wormwars/world.py` (`food_sensing` "mono"), `wormwars/deletion.py`, `wormwars/brain.py`
  (Genome), `wormwars/e1/` (Task N and its scripted controls), `wormwars/e04a/` (lockstep GA), `wormwars/graft.py`
  (mask surgery), `wormwars/exp03/samplers.py` (null ensembles), `configs/interface.yaml`, `configs/mirror_pairs.yaml`.

Please:
1. Answer each of the design's open questions (§10), with your reasons.
2. Check the facts the design relies on against the repository (the E1 controller scores, throughputs, 04a's
   success count, 02b's interface-adjacency finding, what `food_sensing = "mono"` does, the budget arithmetic) and say
   which you checked.
3. Find what would make the proof of concept uninformative or misleading: a task that evolved brains solve without
   memory or without interneurons; a recovery measure that is biased toward true partners (for example through
   degree, mirror symmetry, the union mask, initialisation, or interface candidates); targets with no headroom; a
   search too weak or too noisy at these sizes; an expansion reading that can pass by chance; anything in the arms
   (MIP/NIP) that does not measure what §1 says.
4. Say what is missing that a pre-registration would need, and what could be cut.

Answer with a verdict first: "ready for the pre-registration" (possibly with small fixes), or "revise" (list what
must change). Then numbered findings with file and line where possible, and severity. Do not edit files or run GPU
work.
