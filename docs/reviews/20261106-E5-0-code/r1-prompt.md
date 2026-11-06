# E5-0's code, before its runs (round 1)

`docs/E5/E5-0-PLAN.md` is now draft 2 (your plan reviews and both answers are in `docs/reviews/20261105-E5-0-plan/`;
every fix taken). Please review the code that implements it, before any formal stage runs. Nothing formal has run;
smoke runs only (`runs/e5-0-smoke/`, small sizes, world ids from the plan's ranges cut to 8).

The code:
- `wormwars/world.py`: three hooks (`_spawn_swarms`, `attack_scale`, `_wants_food_field`) and the `hunt` task guard;
  `git diff ab749bb -- wormwars/world.py` shows all of it;
- `wormwars/e5/hunt.py` (`HuntWorld`, `HuntLedger`, `e1_task_n`, `hunt_config`), `prey.py` (the scripted prey and
  the pursuit reference), `play.py` (batched episodes), `hunters.py` (the reused hunters' loaders);
- `scripts/e5_0.py` (the stages: calibrate, equivalence, bench, evaluate, probe, read) and
  `scripts/e5_0_reference.py` (the old-against-new engine check's one side, run in a worktree at ab749bb);
- `tests/test_e5_hunt.py`, and `scripts/e5_0_sabotage.py` with its log `runs/e5-0/sabotage_log.txt` (the code came
  before the tests, so each test was seen failing under a sabotage of what it checks).

Smoke results so far: the old and new engines agree bit for bit on all 64 compared arrays; H1-ghost equals Task N
for all nine hunters under the real, constant and mirrored probes; E_prey 1.25 on 8 worlds (predicted 0.6 to 1.2).

Read-only; please keep it proportionate.
1. **Does the code do what the plan says?** Especially §2 (the scent, the capture rules, respawn at D - R, the
   ledger, the body probe), §3 (E_prey's held contact and the driven approaches; the route follower and its check;
   the tuning per setting), §4 (the equivalence checks, and whether they could pass while something is wrong), §6
   (the bootstrap with the best baseline recomputed per resample, the readings, falls-off), §8 (the cuts and the cap).
2. **Bugs:** anything that would make a formal stage wrong, or let it pass a check it should fail.
3. **The hooks:** are they really no-ops for every existing task?
4. Your verdict: agree, fix then run (list the fixes), or revise.
