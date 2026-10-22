# M4a (memory roadmap): does the head core help maintain the history difference?

Exploratory; the arms, controls, measures and readings are fixed in
[`docs/memory/M4A-PLAN.md`](../../docs/memory/M4A-PLAN.md), reviewed by Astra and Fable before anything ran
([`docs/reviews/20261022-m4a-plan/`](../../docs/reviews/20261022-m4a-plan/)). CPU only.

| Script | What it does | Output |
|---|---|---|
| `m4a.py` | The arms (C3's internal edges cut for a window), the sampled external cuts (20 degree-, 10 weight-stratified), uniform sets, the whole exterior, the flagged effect-matched controls; Part 2 from the separate-states roots (float64); the reference comparison; the cost guard. Stages `n2`, `part2`, `reference`. | `runs/memory-m4a/`: `<panel>.json`, `part2__<panel>.json`, `guard.json`, `stages.json` (arrays `<panel>.npz` local) |
| `m4a_read.py` | The readings, with `test_rules()`. | `runs/memory-m4a/readings.json` |
| `m4a_tables.py` | *After the data:* the tables behind the results write-up (the sampled sets' ranges, each class's share of the separation, beside-the-reading numbers for every arm, Part 2's outcomes and edge counts, each reference graph); no simulation. | `runs/memory-m4a/tables.txt` |
| `sabotage_m4a.py` | Rule 9: each guarded behaviour broken in turn; the matching test must fail. | `runs/m4a-sabotage.txt` |
| `smoke_isolation.py`, `smoke_count_matched.py` | The smoke diagnostics behind draft 3's redesign (64 N2 genomes per seed, other draws). | `runs/memory-m4a-smoke/` |

The results are in [`docs/memory/M4A-RESULTS.md`](../../docs/memory/M4A-RESULTS.md); the run's log and compute record are committed as `runs/memory-m4a/m4a_log.txt` and `m4a-compute-record.json`. Inputs: the connectome, M2's census records and arrays (`runs/memory-m2-census/`, the arrays local). The tests are in
`tests/test_memory_m4a.py`.
