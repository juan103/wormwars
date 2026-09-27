One part of the numerical-coverage blocker remains at `8802e49`.

- **Champions still lack T0/T1 coverage.** [The new test](D:/Claude/random/wormWars/tests/test_t0_items345_b.py:259) uses 600 ticks, stereo sensing, no food odour and 8 brain substeps. The declared T0/T1 settings use 200 ticks, odour, stereo/mono respectively and 32 substeps. Parametrize champions over both tasks, ensuring `Brain(champ)` receives the task’s brain configuration.
- **New inaccurate claim:** [D075](D:/Claude/random/wormWars/DECISIONS.md:2106) says the loader verifies reconstructed graph hashes. None of these three NPZ files contains `edge_hash`. I confirmed SH1 and RD1 also load against different seed-2 graphs under matching labels. Correct that claim or add actual validation.

The eight-world mapping, uniform and mixed corners, jitter comparison and behavioural NaN test address their respective findings.

Verification: **38 tests passed, 1 deselected**—the file-writing round-trip test. No files changed. I did not independently rerun all 463 tests.

not yet