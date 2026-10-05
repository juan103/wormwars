At `265ed2c`:

1. **Champions: correct.** Per-run files close both interruption windows. In-memory probes confirmed that a failed second save, or a kill after that save but before progress publication, leaves every listed champion loadable.

2. **Cap recovery: incomplete; it introduces a guard bypass.** The killed-stage branch returns at [e3c.py:748](D:/Claude/random/wormWars/scripts/e3c.py:748), before the committed-input, code and environment checks. I reproduced acceptance with `smoke=False`, an uncommitted partial record and mismatched marker provenance; no guard ran. The crashed-stage branch retains those checks. The new smoke-only test misses this defect.

3. **Verdict: fix first.** Before returning killed-stage salvage, recover provenance from the start marker and enforce the same committed/unchanged-input, code and environment checks. Add guarded regressions accepting valid salvage and rejecting uncommitted or mismatched inputs.

Verification was read-only, using source inspection and in-memory probes; I did not run the writing smoke tests.