**Fix first.** The arms, masks, schedule and units check out. I found three recording/recovery defects.

1. **Training progress is not durably recorded.** The `evolve_batch` call supplies no `on_checkpoint`; the only intermediate write contains `runs_done`, after an entire batch finishes. A failure during S-dense therefore loses the completed S-mod/P-sel learning records too. See [scripts/e3c.py:218](D:/Claude/random/wormWars/scripts/e3c.py:218) and [scripts/e3c.py:225](D:/Claude/random/wormWars/scripts/e3c.py:225).

   This also affects the budget: killed-run reconciliation charges time through the last file write plus 900 seconds. A hard kill during the first batch can therefore charge approximately 15 minutes for substantially more work. See [scripts/e2.py:525](D:/Claude/random/wormWars/scripts/e2.py:525). Persist checkpoint results and progress timestamps frequently enough for that reconciliation rule.

2. **Incomplete pilots never receive `decision: "inconclusive"`.** That branch exists in the helper, but the runner only calls it with `complete=True`, at successful completion. Failure handling uses the stage frame’s default empty salvage callback. Injecting either a cap exception or a second-batch crash produced a failure record with no `decision` or learning results. It avoids triggering the fallback, but does not record the required branch. See [scripts/e3c.py:270](D:/Claude/random/wormWars/scripts/e3c.py:270), [scripts/e2.py:609](D:/Claude/random/wormWars/scripts/e2.py:609) and [scripts/e2.py:628](D:/Claude/random/wormWars/scripts/e2.py:628).

3. **The generation-0 diagnostics discard the specified distributions.** Visits are reduced to median, maximum and share above W2. Offsets/K_D are calculated for only the first run of each arm and then reduced to summaries. The per-genome values and the other two runs’ probes are absent. Preserve these arrays with their run IDs; they are small. See [scripts/e3c.py:250](D:/Claude/random/wormWars/scripts/e3c.py:250) and [scripts/e3c.py:261](D:/Claude/random/wormWars/scripts/e3c.py:261).

For your individual checks:

- **Draws and masks:** correct. S-mod takes B-task values on E’s edge mask; S-dense retains the full controller mask; P-sel replaces exactly the selector parameters. W2, carrier parameters, relay τ/bias and gap junctions remain frozen. The mutable counts are:

  | Arm | Weights | τ | Biases | Total |
  |---|---:|---:|---:|---:|
  | S-mod | 47 | 9 | 9 | 65 |
  | S-dense | 153 | 9 | 9 | 171 |
  | P-sel | 7 | 1 | 5 | 13 |

  All active factors are 1.0; `tuning.scales()` still defaults to 0.25. Draws use independent random values across strains and reproduce with the same seed and population size. See [assembly.py:44](D:/Claude/random/wormWars/wormwars/e3/assembly.py:44), [assembly.py:56](D:/Claude/random/wormWars/wormwars/e3/assembly.py:56) and [tuning.py:49](D:/Claude/random/wormWars/wormwars/e3/tuning.py:49).

- **Pilot:** correct successful-run configuration: three runs per arm, population 32, 100 generations × 8 mazes; seeds `1200000–1200002`, `1200010–1200012`, `1200020–1200022`. S-mod/P-sel share `[192,8,8]`; S-dense uses `[96,8,8]`. Checkpoint indices are **0, 25, 50, 75, 99**. Learning IDs are **7600–7727**, disjoint from the earlier maze blocks checked; training IDs are **30000000–39999999**. Both references use the learning block. See [scripts/e3c.py:66](D:/Claude/random/wormWars/scripts/e3c.py:66), [scripts/e3c.py:215](D:/Claude/random/wormWars/scripts/e3c.py:215) and [evolve.py:186](D:/Claude/random/wormWars/wormwars/e04a/evolve.py:186).

- **Units and criterion:** correct. Rollout scores divide colony visits by colony size; reference outcomes average individual visits over weys. Generation-0 counts already have that unit. Their subsequent means average over mazes. The criterion is strictly `validation_mean > W2 + 1`, using the training-selected generation-best. Generation-0 diagnostics use eight training mazes, whereas W2 uses the 128-maze learning block; that is a sampling difference, not a unit mismatch. See [maze_world.py:408](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:408), [scripts/e3c.py:176](D:/Claude/random/wormWars/scripts/e3c.py:176) and [scripts/e3c.py:139](D:/Claude/random/wormWars/scripts/e3c.py:139).

- **Access and live cap:** shared trails are correctly configured for training and explicitly requested for references/evaluation. The three-hour cap is checked before training/checkpoint rollouts and can stop the run; it does not interrupt an already-running rollout. The killed-attempt accounting defect is finding 1.

All **11 non-smoke tests passed**. I additionally verified frozen parameters after ten mutation steps per arm and exercised the cap/crash paths using in-memory mocks. I did not run GPU work or modify files; the 2.5-hour estimate remains unverified.