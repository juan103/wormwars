Checked HEAD `60c5768`. Both findings are addressed.

- [Champion coverage](D:/Claude/random/wormWars/tests/test_t0_items345_b.py:250) now covers N2/SH1/RD1 × T0/T1, using each task’s brain configuration and eight worlds, with per-tick finiteness checks. **All six cases passed on CPU.**
- [D076](D:/Claude/random/wormWars/DECISIONS.md:2127) explicitly retracts the edge-hash claim. I independently confirmed all three champion files lack `edge_hash`. Graph reconstruction remains unverified pending historical CUDA replay.

No new findings in this change. No files changed; I did not rerun the full suite.

items 3-5 CPU: accept