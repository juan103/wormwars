**Fix first.** The training inputs match the pilot. The defects are in the production guard, tour metric, path retention, and failure records.

I inspected the existing smoke record and ran an independent, read-only CPU comparison: three strains, four mazes, 600 ticks. Every event array from `play_recorded` matched `play_batch`. I did not run GPU training or modify files.

**1. Replay**

The S-dense replay matches the pilot’s numerical setup:

- Runs 10–12, seeds 1200010–1200012, independently seeded draws and the same mutation mask.
- Population 32; 100 generations; eight training mazes per genome; checkpoints at 0, 25, 50, 75 and 99.
- The same training-ID function/range, learning IDs 7600–7727, world seed, interface, brain specification and zero shaping.
- Training composition `[96, 8, 8]`; checkpoint composition `[3, 128, 8]`.

Compare [pilot construction and call](D:/Claude/random/wormWars/scripts/e3c.py:235) with [replay construction and call](D:/Claude/random/wormWars/scripts/e3c.py:443). I also checked that the resolved-config hash matches the stored pilot and that the engine has no changes since the pilot commit. Training and breeding use independent run-specific generators, so skipping the earlier S-mod/P-sel batch does not consume different random streams. [evolve.py:63](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:63), [evolve.py:147](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:147)

**I found no additional numerical mismatch beyond rule 6’s limits.** Neither stage enables `replay_mode`; CUDA equality remains a check, not a guarantee. [bundle.py:126](D:/Claude/random/wormWars/wormwars/evo/bundle.py:126)

**However, the production replay cannot start after this code is committed.** It calls `require_earlier("pilot")`, which requires every guarded path to match the pilot commit. `scripts` is guarded, and this change modifies `scripts/e3c.py`. Smoke bypasses that check. This needs a narrowly defined compatibility check allowing the reviewed replay additions while checking the training inputs and engine. [e3c.py:65](D:/Claude/random/wormWars/scripts/e3c.py:65), [e3c.py:519](D:/Claude/random/wormWars/scripts/e3c.py:519), [e2.py:432](D:/Claude/random/wormWars/scripts/e2.py:432), [registration.py:149](D:/Claude/random/wormWars/wormwars/registration.py:149)

**2. Probes**

**`play_recorded`: correct layout and simulation.** For strains numbered `0…S−1`, its repeated strain IDs, tiled maze IDs, episode-zero defaults and reshaping match `play_batch`. The recorder reads positions after movement without changing them. My CPU comparison confirmed equality of all event arrays. [e3c.py:375](D:/Claude/random/wormWars/scripts/e3c.py:375), [maze_runs.py:353](D:/Claude/random/wormWars/wormwars/e3/maze_runs.py:353), [world.py:1019](D:/Claude/random/wormWars/wormwars/world.py:1019)

**`without_scent`: correct interfaces.** Champions receive the dense interface; seed and W2 receive their own. I checked that the dense and seed interfaces each lose exactly four scent gains, preserving everything else. W2 alone has no A/B nose entries, so this intervention is appropriately a no-op there. [e3c.py:479](D:/Claude/random/wormWars/scripts/e3c.py:479), [attribution.py:182](D:/Claude/random/wormWars/wormwars/e3/attribution.py:182)

**`cell_index`: correct**, with the stated convention assigning connecting corridors to the preceding column/row. The `−1`, division by four and row-major indexing agree with the maze geometry. [e3c.py:343](D:/Claude/random/wormWars/scripts/e3c.py:343), [maze.py:3](D:/Claude/random/wormWars/wormwars/e3/maze.py:3), [maze.py:83](D:/Claude/random/wormWars/wormwars/e3/maze.py:83)

**`tour_match`: not the measure D205 specifies.** Forty-eight is correct for a complete tree contour: 24 edges traversed twice. But the implementation compares **cells**, not directed `(from, to)` moves. It also permits a comparison when there are exactly 48 moves, when no move has a predecessor 48 moves earlier. [e3c.py:351](D:/Claude/random/wormWars/scripts/e3c.py:351), [D205](D:/Claude/random/wormWars/DECISIONS.md:6621)

Concrete counterexample I executed: on the valid tree `1—0—5`, take `[0,1]` repeated 24 times, then `[0,5]` repeated 24 times, then `0`. Current score: **25/49 = 0.5102**. Directed-move match: **0**. Exactly 48 alternating moves currently score **1**, rather than undefined. Compare compressed directed-edge pairs and require more than 48 moves.

**`world.pos[:, 0]`: correct.** Positions are `[worlds, swarms, weys, 2]`; maze worlds enforce one swarm. The slice contains every wey’s head. [world.py:308](D:/Claude/random/wormWars/wormwars/world.py:308), [maze_world.py:192](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:192)

**Path retention is incomplete.** `sample_paths` selects worlds `0…3`, which all belong to the first champion. Runs 11 and 12 have no saved paths. Compression also discards timing. Return samples separately for each strain, with maze/wey identities and transition ticks. [e3c.py:406](D:/Claude/random/wormWars/scripts/e3c.py:406), [e3c.py:485](D:/Claude/random/wormWars/scripts/e3c.py:485)

**3. `w2_turn`**

**Correct under `carrier_turn`’s definition.** It sets dorsal bias to `atanh(rest/2) − resting_reflex_push("W2")`, with the opposite ventral bias. I verified that requesting W2’s own resting turn reproduces all its parameters exactly. [e3c.py:410](D:/Claude/random/wormWars/scripts/e3c.py:410), [maze_organisms.py:126](D:/Claude/random/wormWars/wormwars/e3/maze_organisms.py:126)

The sweep is a fair exploratory scent-free reference: same carrier/reflex, environment, horizon and maze block; only the resting-turn bias changes. “Constant” describes the bias, not angular velocity during collisions.

**4. `consequence` and thresholds**

The inequalities and “every champion” requirement are implemented correctly, including the inclusive boundaries and missing retained fractions falling into “mixed”. [e3c.py:423](D:/Claude/random/wormWars/scripts/e3c.py:423)

Two operational details should be explicit beside D205: coverage and tour match come from the **intact** condition; coverage averages across weys/mazes, while tour match excludes undefined weys. [e3c.py:401](D:/Claude/random/wormWars/scripts/e3c.py:401)

The thresholds are defensible **exploratory classification rules**, once the tour metric is fixed. They do not establish statistical equivalence or uniquely identify wall-following. Even directed lag-48 matching can detect shorter periods dividing 48; trajectory inspection remains necessary. I would not change the numerical thresholds based on anticipated results.

**5. Missing records and failure handling**

Replay drops the pilot’s durable progress and salvage machinery. It saves genomes only after evolution finishes, installs no `on_checkpoint`, and leaves `ctx.salvage` empty. A failure during probes—or the final cap check—therefore loses completed results from the stage record. [e3c.py:454](D:/Claude/random/wormWars/scripts/e3c.py:454), [e2.py:609](D:/Claude/random/wormWars/scripts/e2.py:609)

More seriously, hard-kill accounting uses the last tracked file’s timestamp plus 900 seconds. With no partial record and no genome files passed into the stage’s tracked-file list, a long killed replay can be charged approximately **15 minutes**. The pilot’s periodic writes prevent this. [e2.py:521](D:/Claude/random/wormWars/scripts/e2.py:521), [e2.py:585](D:/Claude/random/wormWars/scripts/e2.py:585), [e3c.py:256](D:/Claude/random/wormWars/scripts/e3c.py:256)

The successful record also retains only hash-match counts, not the actual per-generation replay hashes. Preserve those arrays for diagnosing divergence. Its unconditional note calls the champions a replay even when hashes differ; D205 explicitly requires the **exploratory retraining** description in that case. [e3c.py:337](D:/Claude/random/wormWars/scripts/e3c.py:337), [e3c.py:517](D:/Claude/random/wormWars/scripts/e3c.py:517), [D205](D:/Claude/random/wormWars/DECISIONS.md:6612)

**6. Verdict: fix first**

1. Fix the predecessor compatibility guard without broadly disabling provenance checks.
2. Compare directed moves in `tour_match` and correct its minimum-length condition.
3. Retain identifiable trajectory samples for all three champions.
4. Restore periodic progress, checkpoint saving and salvage; include saved genomes in rerun preservation.
5. Preserve replay hash arrays and label mismatching runs as exploratory retraining.

Add regression checks for those failures. The current smoke uses only one champion and bypasses the production guard, so its success cannot expose the two corresponding defects. [e3c.py:529](D:/Claude/random/wormWars/scripts/e3c.py:529), [test_e3c_runner.py:181](D:/Claude/random/wormWars/tests/test_e3c_runner.py:181)