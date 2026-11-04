# E5 (stage 05, the hunter): scope and design note, draft 1 (round 1)

The owner chose roadmap stage 05, the hunter (2026-11-04): "For the hunter let's start with a static prey, and then
let the prey increase in complexity. Like one that has a defined route. Then we use the ones we develop in the
previous experiments. Maybe we can use some of the things we built before?"

Please review `docs/E5/SCOPE.md` (draft 1). Nothing has run; no code is written. The note proposes a task (Task H:
Task N with a living target), a prey ladder (the owner's: static, a defined route, earlier organisms), the code it
needs, and a first CPU-only feasibility step (E5-0) with scripted and frozen controllers. Check its claims about the
existing code against the repository (`wormwars/world.py`, `wormwars/e1/`, `wormwars/exp02/scripted.py`,
`wormwars/graft.py`, `wormwars/evo/coevolve.py`, `configs/interface.yaml`) and the earlier results it cites
(E1, 04a, E2d, E4s-1, D026).

Read-only; please keep it proportionate.
1. **Is the task right** for the owner's ladder and for the roadmap's stage 05 row (ROADMAP.md, "Direction after
   E4")? Answer §7's questions 1 to 5 with a recommendation each.
2. **Reuse:** are the reused pieces (Task N's machinery, the scripted controllers, E4s-1's and E2's navigators as
   hunters, 02's champions and the navigators as prey, the inert graft) used correctly, and is anything reusable
   missed?
3. **E5-0:** are its controls enough, and what decision rule ("solvable", "too easy", where a reused hunter "falls
   off") should be fixed before it runs? Is its cost estimate plausible?
4. **Risks:** what is most likely to go wrong (D026's lesson; E2d's plateau; E4's fragile modules), and what should
   the note say about it?
5. Your verdict: agree, fix then proceed (list the fixes), or revise.
