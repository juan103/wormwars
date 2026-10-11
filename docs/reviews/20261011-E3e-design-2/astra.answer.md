**Verdict: revise.**

The previous required changes are correctly incorporated **as design requirements**: both designs guarded; complete runner adaptation, including reduction 3, smoke paths, accounting and labels; and full calibration-failure reporting with multi-strain B_max handling. I verified the parent-design hash, 228 pairs and 96-move tour. Implementation remains to be checked after binding.

1. **The new G2a reading overstates what the result establishes.** [§1a](D:/Claude/random/wormWars/docs/E3/E3e-DESIGN.md:68) asserts that discovery cost grows faster than the oracle’s route and makes that the explanation of failure. [G2a](D:/Claude/random/wormWars/wormwars/e3/e3d_gate.py:59) measures only the follower/oracle throughput ratio. Failure could instead reflect slower later shuttling or different oracle performance on the newly sampled mazes. It also cannot exclude a simultaneous blind-control failure.

   Replace that reading with:

   > A G2a failure means the shared scripted follower falls below the required one-third of oracle throughput on this block. Increased discovery cost associated with fixed scent reach and trail decay is a possible explanation, to check against discovery, scent-reach, no-first-visit and later-leg records—not an identified cause. Blind-control performance is assessed separately by G1.

That is the only remaining binding blocker I found. No change to the experimental settings is required.