Most points are resolved at `81a73cc`, but the previous numerical-coverage finding remains.

- **Only two distinct worlds per genome.** [test_t0_items345_b.py:139](D:/Claude/random/wormWars/tests/test_t0_items345_b.py:139) repeats each genome twice and tiles world IDs `[0, 1]`. Eight batch rows across four genomes do not provide the eight-world coverage declared in [T0.md:169](D:/Claude/random/wormWars/docs/foundations/T0.md:169). Use eight distinct IDs per genome.
- **The per-tick matrix still excludes the uniform-sign extremes and evolved champions.** Their existing tests call `w.run()` and inspect only final brain states and energies: [extremes](D:/Claude/random/wormWars/tests/test_t0_items345.py:88), [champion](D:/Claude/random/wormWars/tests/test_t0_items345.py:102). They also remain outside the declared graph/task matrix and omit score checks. Extend those cases into the per-tick numerical checks before claiming coverage is complete.

The other reviewed points are resolved: the two vacuous tests, additional island coverage, ledger adversarial cases, NaN aggregation sites, selection-fitness guard, and documentation corrections. I independently confirmed that identity jitter, old padded keys, and global breeding each fail the replacement tests.

Verification: **34 pytest tests passed**, plus the save/load/re-simulation test with storage redirected to memory. Functional probes confirmed NaN propagation through rollout, coevolution, the exp02 run-record expression, and `report.build`. No files changed.

I found no new production-code defect within this scope. The remaining blocker is the numerical coverage already requested.

not yet