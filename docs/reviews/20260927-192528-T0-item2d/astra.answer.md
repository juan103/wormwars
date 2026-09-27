One blocker remains at `0c65e42`: **02b skips aggregation when a stage raises.** The call at [analyse.py:466](D:/Claude/random/wormWars/experiments/02b-champion-analysis/analyse.py:466) executes only after successful completion of `attempt`.

I reproduced both cases using the actual `__main__` block with stubbed stages and in-memory persistence:

- First stage fails: the failed attempt is recorded, but `compute.json` is absent.
- Success followed by failure: `compute.json` stays stale, reporting one attempt and zero failures despite two saved attempts.

Put aggregation in a `finally` block that runs after `attempt` exits, and add a regression test for a raising stage.

**I approve the amended plan text** in [T0.md:34](D:/Claude/random/wormWars/docs/foundations/T0.md:34), including the explicit untested paths and the previously stated `SparseBrain` exception. The five parser changes, aggregate identification fields, and nonzero-exit handling check out.

All **28 accounting test functions passed on CPU**, with filesystem persistence mocked in memory. CUDA identity remains unverified. No files changed.

not yet