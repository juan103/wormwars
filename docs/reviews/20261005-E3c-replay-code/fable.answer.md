**Verdict: fix first.** Two real defects, one of which stops the stage from starting at all. Everything else checks out, and the CPU smoke record confirms the key claims.

## 1. The replay

It is the pilot's S-dense batch. I compared `cmd_replay` against `cmd_pilot` item by item:

- **Config and context.** Same `cfg_for("shared", 8)` and `AS.context` (`scripts/e3c.py:444-446` vs `:236-238`).
- **Runs.** `pilot_runs()` filtered to S-dense keeps the pilot's order and seeds (`scripts/e3c.py:448` vs `:240, 271-273`).
- **Draws and masks.** Same rng key `[seed, 0xE3C]`, same `arm_scales("s_dense")` (`scripts/e3c.py:450-451` vs `:247-248`).
- **Schedule and ids.** Same `generations`, `checkpoint_every`, `validation_ids`, `world_seed`, `id_base`, `id_span` (`scripts/e3c.py:454-458` vs `:274-278`). The only differences are `check` without partial writes and no `on_checkpoint`. Neither touches numerics.
- **Composition.** R = 3 runs gives `chunk_worlds = 3·32·8` for training and `3·128` for validation, both as in the pilot (`wormwars/e04a/evolve.py:157, 190-191`). The record's `[96, 8, 8]` is right.

The CPU smoke's `all_match: true` (`runs/e3c-smoke/replay.json:263`) also rules out one hidden hazard: if the pilot's first batch had consumed any global RNG, the replay's S-dense hashes would have diverged on the CPU too. Nothing outside rule 6 can make the GPU hashes differ. Neither the pilot nor the replay uses `replay_mode`, so they are consistent with each other.

**But the stage will refuse to start.** The `requires` lambda calls `E.require_earlier` (`scripts/e3c.py:519`). In a formal run that calls `reg.require_same_code(pilot_commit, GUARDED)` (`scripts/e2.py:432-435`), which fails on any diff in the guarded paths since e2f0273 (`wormwars/registration.py:149-153`). `GUARDED` includes `scripts` (`scripts/e3c.py:65`), and the replay code lives in `scripts/e3c.py`. It must be committed for `require_formal`'s clean-tree check to pass (`registration.py:85`), so the diff is guaranteed non-empty. The smoke never exercises this path because `formal = not smoke or guarded` (`scripts/e2.py:334-335`). The repository has the right pattern already: E3b-0's `require_historical` loads a record made on earlier code, checking completed, committed, same environment and a pinned hash, but not same code (`scripts/e3b0.py:190-204`, D178).

## 2. The probes

- **`play_recorded` vs `play_batch`.** Same layout: `strain_of = repeat(arange(S), n)`, `world_ids = tile(ids, S)`, reshape to `[S, n, ...]` (`scripts/e3c.py:381-390` vs `wormwars/e3/maze_runs.py:356-357, 373`). With `n_strains = 1` it equals `MR.world`'s zeros layout, so the seed and W2 match the pilot's `play` (`maze_runs.py:131-132`). The recorder is passive and fires at the end of the tick, after `_post_move` (`wormwars/world.py:984, 1019-1020`). The smoke's `intact_matches_pilot` is true for all three (`runs/e3c-smoke/replay.json:971-974`).
- **`without_scent`.** Applied to each organism's own interface (`scripts/e3c.py:479-481, 488`). It zeroes `sensor_gain` for the four scent channels (`wormwars/e3/attribution.py:182-188`), which `_build_current` multiplies (`world.py:889`). The dense module's noses read exactly those four (`wormwars/e3/samplers.py:159-160`), as does E. W2's carrier has no noses (`wormwars/e3/organism.py:125-127`), so for W2 it is a no-op and its retained fraction is 1.0 by construction. Note that `at_a`/`at_b` stay on, so a champion without scent still gets visit cues through the relays. That is E3b-2's definition, but the record should say it.
- **`cell_index`.** Correct. Cell (i, j) owns rows and columns 1+4i..3+4i (`wormwars/e3/maze.py:4-6, 103-104`); the code assigns the corridor column 4+4j to cell j (`scripts/e3c.py:346-347`), consistent with `cell_centre` and `_src_lo` (`maze.py:86`, `wormwars/e3/maze_world.py:237`) and with `sample_bilinear`'s cell convention (`wormwars/fields.py:32-35`).
- **`tour_match`.** An Euler circuit of a 25-node tree is 48 edge traversals, so the period is right (`scripts/e3c.py:395`). The code compares destination cells at lag 48 after collapsing repeats (`:355-358`), not (from, to) pairs. That over-counts slightly against D205's wording. Negligible. See §4 for its sensitivity.
- **`world.pos[:, 0]`.** `pos` is `[worlds, swarms, weys, 2]` and is the head (`world.py:308-310, 748`). MazeWorld has one swarm (`maze_world.py:192-193`), so `[:, 0]` is `[worlds, weys, 2]`, the same expression `_post_move` uses for visits (`maze_world.py:375`).

## 3. `w2_turn`

It sets what `carrier_turn` defines. `carrier_turn` is `2 tanh(atanh(rest/2) − push)` (`wormwars/e3/maze_organisms.py:136-140`) and `carrier_genome` stores `±atanh(turn/2)` on the turn neurons (`wormwars/e4s/comparator.py:70-76`). `w2_turn` computes the same k and writes `±atanh(k/2)` to the same neurons (`scripts/e3c.py:413-419`). The test recovers W2 bitwise at 0.4 (`tests/test_e3c_runner.py:168-178`).

As a reference it is fair but low. A blind W2 with a constant bias is a floor for scent-free play. A champion without scent still has the relays' visit cues and 171 tuned scalars, so beating every sweep point is not evidence of scent use. Also, the sweep's composition (10 strains) differs from `w2_alone`'s (1 strain), so on the GPU its 0.4 point need not equal `w2_alone` bitwise. Do not read that as a bug.

## 4. The outcome rule

`consequence` implements D205 as written (`scripts/e3c.py:423-433`), with `None` falling to "mixed". It reads "covers ≥ 0.95 of its maze" as intact, per-wey coverage averaged over weys and mazes. D205 does not say either; the reading is the natural one but should be annotated beside D205.

The retained-fraction thresholds are fine. The tour-match threshold is the weak one. At max speed 0.35 and cells 4 apart, the champions' 8 visits per maze imply roughly 190 moves and 140 lag-48 comparisons per wey. One deviation (a bump, a reversal, a flicker at a gap the wey does not take) misaligns the next 48 comparisons, giving about 0.66. Two give about 0.3. A genuine wall-follower can land in "mixed" through a metric artefact. Since "mixed" means proceed, the failure is conservative. Keep the fixed rule, but record an exploratory companion beside it, such as the best lag in 44 to 52 or the share of directed moves seen before. Also, `consequence` has no unit test, only the smoke's membership check (`tests/test_e3c_runner.py:196`). Rule 9.

## 5. Worthless runs and missing records

- **The guard above.** Nothing runs.
- **Sample paths cover only run 10.** `range(min(4, n))` indexes worlds 0 to 3, which are strain 0's first four mazes (`scripts/e3c.py:407`). Runs 11 and 12 get no paths. D205 says the three champions' paths are inspected.
- **No salvage.** A crash or cap inside the batch leaves the "stopped" record with `ctx.salvage()` empty (`scripts/e2.py:609, 631`): no genomes, no hash comparison. E2's `save_genomes` pattern exists (`scripts/e2.py:658`). Not blocking. The cap has room:

| Item | Value |
|---|---|
| Spent, as the clock sees it | 2.82 h (`compute-record.json:55`) |
| S-dense batch in the pilot | about 1.08 h (`pilot.json:8186-8286`: 95 × 37.4 s + 5 × 66 s) |
| Probes and sweep | a few minutes |
| Cap | 5.0 h |

- **Cosmetic.** The "final" genome file carries `generations=[checkpoint generations]` (`scripts/e3c.py:469-470`), misleading for the final population.
- **Scratch files.** `runs/e3c/replay_block.py` and `patch_replay.py` are not gitignored (only npz, log and json patterns are). `replay_block.py` passes `cfg=cfg.brain`, which writes empty world meta. Keep them out of the commit.

## 6. Fix first

1. Replace the replay's `requires` with a historical loader: the pilot record must be completed, committed, same environment, and its commit recorded in the replay record, with no same-code check (`scripts/e3c.py:519`; pattern at `scripts/e3b0.py:190-204`). Add a sabotage test that makes `reg.require_same_code` raise and asserts the replay's loader still returns the record.
2. Sample paths per champion: index worlds `s·n + m` for each strain s (`scripts/e3c.py:407`).

Recommended, not blocking: save candidates in `on_checkpoint` and return the hash comparison so far from `ctx.salvage`; a unit test for each `consequence` branch; the exploratory companion tour metric; a dated note beside D205 that coverage is intact and per wey, and that the relays' visit cues stay on under "noses removed".