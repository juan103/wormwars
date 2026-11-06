**Verdict: fix then run.** The task mechanics match the plan and the ghost's bit-exactness holds by construction. I found one real bug in the cap, four places where the code is weaker than the plan's wording, and one piece of evidence that is incomplete. None needs a design change.

## 1. Does the code do what the plan says?

**§2, Task H.** Yes, checked line by line.
- Scent on the prey's head point, Task N's form and truncation; the hunter samples only the scent, the prey only food plus pellets (`wormwars/e5/hunt.py:155-183`). The `constant` value is Task N's (`hunt.py:112`).
- Ghost, reach and bite rules as written; ghost and reach at combat stage 0; the body probe keeps bites and drops the prey from the body field (`hunt.py:100-105, 187-196, 228-241`).
- Respawn at the first later centre at least D − R from the hunter's head, same tick, fresh heading from its own stream, activation at the next tick, hunter untouched, points cache cleared, prey policy reset (`hunt.py:243-279`). The triangle-inequality argument for the ghost holds; the only way it could skip is a float32 rounding of a centre stored from a float64 draw, which the 512-world check would expose.
- Ledger bookings as in the table; `done()` is the horizon; events as listed.
- Crowding arithmetic is right (6 points / 9 cells = 0.667 < 0.8), and the pin is a guard.

**§3, calibration.** The held fixture, the three driven approaches, the random walk's key, the route follower's waypoint rules, and the tuning (E1's grids, insertion-order keys as E1's `combos_of` used, first maximum) all match. Two deviations:
- **The route check's criterion (iii) cannot fail.** `_resolve_move` clamps to [1.02, side − 1.02] and only refuses a move whose cell is a wall; in an arena with just the boundary ring, no clamped position is ever a wall cell (`wormwars/world.py:1089-1099`). So `prey_wall_refused` is identically zero, and the smoke's `share_refused: 1.0` is vacuous. The real stall mode, sliding along the clamp, goes unmeasured except through path length. Count clamped moves instead (proposed ≠ clamped for the prey), or drop (iii) and say why.
- **The 95% is applied per criterion, not jointly.** Plan: "in at least 95% of worlds, (i), (ii) and (iii)". Code: `min(share_speed, share_lap, share_refused) >= 0.95` (`scripts/e5_0.py:290`). Separate shares of 0.95 allow a joint share of 0.90. One line to fix, or amend the plan.

**§4, equivalence.** Both checks are implemented as written and the smoke shows them passing. Could they pass while something is wrong? The ghost-against-Task-N check exercises the spawn hook, target placement, the scent, the body field without the prey, and the capture path, and the traces compare the hunter's input currents, so a wrong collision or damage channel would show. It does not exercise bites, the reach body field, the ledger with captures, or `attack_scale`; those rest on the unit tests and the attack-disabled run, which is adequate. One gap: the worktree is reused if it exists without checking that its HEAD is `REF_COMMIT` (`e5_0.py:404-406`). Verify and record it.

**§6, reading.** The bootstrap is paired, the best baseline is recomputed per resample for both the difference and the ratio, the criteria, demonstrated failure, falls-off, and the threshold-free readings all match. The qualification probes use the same `Boot` as the reading, so the probed set equals the set that reads "capture criteria met".

**§8, cuts and cap.** The four cuts and the staged qualification order are implemented. The cap itself is broken; see below.

## 2. Bugs

1. **The cap never counts the running process.** `cap()` builds a fresh `CapClock` on every call (`scripts/e5_0.py:114-115`, used at 305, 503, 521), so `t_start` is always "now" and `check()` reduces to "previous attempts' recorded hours > 8". Recorded hours are written only when a process ends (`accounting.recorded`'s `finally`). Inside `evaluate` or `probe`, the plan's "run until the cap" and "stop if the cap is reached" cannot trigger, however long they run. Fix: create one clock in `main()` and return it from `cap()`.
2. **The attack-disabled check reports but does not stop.** Plan §6: "anything else is a bug and stops E5-0". `run_scripted` records captures and damage (`e5_0.py:528-531`); `stage_read` prints them (`e5_0.py:790-793`). Nothing raises. Add the stop in `run_scripted`.
3. **The ledger tolerance is not enforced in the formal runs.** Plan §2: must balance every tick at 1e-5. `cfg_for` leaves `check_ledger_every_tick` off, and the final residual is reported as `ledger_rel_error_max` without comparison (`e5_0.py:781`). Turn the per-tick check on in `cfg_for` (measurement only, no effect on the simulation) and stop on a residual above 1e-5.
4. **The committed record lacks what the plan promises.** §9 names `evaluation.json` with per-world counts in the experiment folder; the code writes per-setting files under `runs/e5-0/evaluation/` only, and saves a subset of the events (captures, capture tick, contacts, bearing). Missing: activation ticks, both path lengths, attributed damage, first-contact tick, and the hunter's bite energy that §2 says is logged (`HuntResult.bite_energy` is computed and dropped at `e5_0.py:498-511`). Rule 5 needs the counts committed; the rest is a one-line change to save the whole `events` dict.
5. **Resume does not check the code.** `--resume` skips `guard()` (`e5_0.py:615-619, 699-703`). A resume after an edit mixes engines across settings in one record. Read the start marker's commit and call `require_same_code` and `require_pushed`.
6. **The full-suite evidence is incomplete.** `runs/e5-0/full-suite-hooks.txt` ends at 44% with no summary line and no exit status. Your own memory records four slips of exactly this kind. Rerun and capture the summary and `rc`.

Smaller points, fix or note:
- `_place` can put the hunter beyond the wall ring for the head and rear approaches (up to 5.4 cells past a centre that may be 4 from the edge); it is clamped on the first tick, so the "3 cells away" start is not uniform. Harmless for kill times measured from first contact; say so in the record, or clamp in `_place`.
- `e2d_champions` does not assert the count of 47 that the plan fixes, unlike `e4s1_champions`'s 16 (`wormwars/e5/hunters.py:79-102`).
- The copied grids are not compared with `freeze.json`'s registered grids; `Env` compares the config only. A one-line assert closes it.
- The plan says `bench` runs "before anything else"; the script runs it third, after calibration and equivalence, and needs their outputs. The projection still includes the spent time, so the logic is right, but the plan's sentence is wrong. Amend it, dated.
- The stop rule "E_prey not larger than the largest single-tick damage" works for the driven approaches only through equality on a one-tick kill, since those runs are capped at E_prey. Correct, but worth a comment.

## 3. The hooks

Yes, no-ops for every existing task. I compared against the pre-hook source in the `wormWars-e5ref` worktree:
- `_spawn_swarms`: the old loop was `for side in range(self.n_swarms)` with `if self.n_swarms == 1`; the new code substitutes `n_sides = self._spawn_swarms()` whose default returns `self.n_swarms` in the same three places (`world.py:472-490` against the old 467-484). Identical.
- `_wants_food_field`: the old inline `needs_field` expression (old 982-984) is the new method's body, character for character.
- `attack_scale`: `None` by default and skipped (`world.py:1172-1173`); the old line was `strength = ccfg.attack_strength * alive_f` with nothing after it.
- The `hunt` guard only fires for `task == "hunt"`. No other subclass (`MazeWorld`, `TrialWorld`) defines the new hook names, and the §4.1 check covers navigate and a two-swarm stage-1 fight bit for bit.

One design note, not a bug: `PreyBrain` is built on the ungrafted interface while a grafted hunter's world uses the grafted one. That is safe because `graft_interface` appends the noses after the worm's entries and leaves motor and collision indices in place (`wormwars/graft.py:159-177`). Worth a comment in `prey.py`, since it is load-bearing for the wall-following prey.

## 4. Verdict

**Fix then run.** Before any formal stage: the cap clock (1), the attack-disabled stop (2), the ledger gate (3), the committed counts and full events (4), the resume guard (5), the complete suite log (6), and the route check's vacuous criterion and joint share. Then the smaller items as you see fit. Nothing here changes a decision rule or a number; the plan can stand with two dated amendments (bench's position; the route check's wording if you keep per-criterion shares).