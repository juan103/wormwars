# E5-1's code and E5-1a's driver, before E5-1a runs (round 1)

`docs/E5/E5-1-DESIGN.md` is draft 3 (your two design reviews are in `docs/reviews/20261111-E5-1-design/`). The owner
has now said "Yes and build": E5-1a may run on the GPU, stopping at the bench where they set the cap, and B stays in
E5-1. I have written §9's code and E5-1a's driver. Nothing formal has run; smoke runs only (`runs/e5-1a-smoke/`, world
ids from 987 100 000 on, outside every E5-1 block; 40 ticks, tiny populations), CPU and CUDA, every stage end to end.
**§14 of the design (new, at the end) lists what the code fixes that the design left open: please check it too.**
The changes are uncommitted in the working tree (`git status`, `git diff`).

The code:
- `wormwars/brain.py`: `BrainSpec.same_as`, and the guards in `Genome.cat` and `Genome.assign` (configurations
  compared without their `init_*` fields; the frozen opponent suite, `wormwars/evo/coevolve.py`'s
  `make_frozen_suite`, spreads them on purpose and the first version of the guard refused it);
- `wormwars/e04a/evolve.py`: `evolve_batch(..., weights=None)` (`git diff -- wormwars/e04a/evolve.py`);
- `wormwars/e5/hunt.py` (one pin per world), `prey.py` (`RouteTable`, the vectorised `_route_for`, `MixedPrey`),
  `play.py` (per-strain ids, per-column pins, `max_index`), and new: `settings.py`, `mixed.py`, `ga.py`
  (`TaskHRollout`), `plan.py` (every fixed number), `graphs.py` (SH-route rebuilt and checked against 03r's content
  manifest; the graft's checks; 03r's calibrated gains), `arms.py` (generation 0 per arm, masks, lesion, P, identity);
- `tests/test_publication_hygiene.py`: the null-graph prohibition (`NULL_GRAPH`);
- `scripts/e5_1a.py` (the stages equivalence, graphs, cuda, bench, cap, then signal, pilot, composition,
  sensitivity), `scripts/e5_1_reference.py` (the old-against-new side, run in a worktree at 7d25460);
- tests: `tests/test_e5_genome_guards.py`, `test_e5_mixed.py`, `test_e5_ga.py`, `test_e5_arms.py`; logs in
  `runs/e5-1/` (first-fail logs, and `scripts/e5_1_sabotage.py` with `runs/e5-1/sabotage_log.txt` for the code written
  before its tests).

Smoke results: old against new identical on 1 045 arrays (18 settings × 3 hunters on 64 worlds, plus traces); E5-0's
68 arrays identical; H1-ghost equals Task N; the mixed world equals each slot alone at the same composition, and the
GA rollout equals that serial reference, with the weighted fitness equal to the design's formula; every CUDA smoke
check passed (40 ticks, 16 worlds); bench, signal, pilot, composition and sensitivity ran.

Read-only; please keep it proportionate.
1. **Does the code do what the design says** (§3's mixture, weights and worlds; §4's arms, seeds, graphs and P; §6's
   overflow and ledger checks; §7's steps and stop rules; §9's list)?
2. **Bugs:** anything that would make an E5-1a stage wrong, let a check pass that should fail, or make a later
   formal run wrong (the GA rollout, the weights, the mixed prey, the route cache, the guards).
3. **The engine changes:** are the defaults no-ops for every existing caller (`evolve_batch` without `weights`,
   `HuntWorld` with one pin, `PreyBrain` of one kind, `play` with shared ids)? Is the route cache the same draw?
4. **§14's numbers:** acceptable as fixed before E5-1a runs, or should any change?
5. Your verdict: agree, fix then run (list the fixes), or revise.
