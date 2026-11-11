**Verdict: fix first.** Most round-1 fixes are present. I independently confirmed the 1,045 identical saved arrays and 530 captures, and verified with in-memory substitutes that all 16 genomes now receive all 512 worlds at every composition.

Four issues remain:

1. **Precision can still fail while the comparison passes.** In [judged](/D:/Claude/random/wormWars/scripts/e5_1a.py:312), `precision_reached` does not affect acceptance. Alternating differences of ±3 produced `passed=True` with half-width **0.05453**. The uncapped requirement is **27,136**, but `worlds_required` reports **8,192**. Preserve the uncapped requirement and stop on insufficient precision—or explicitly withdraw the original 0.03 guarantee.

2. **The projection still needs correction.** [The high estimate](/D:/Claude/random/wormWars/scripts/e5_1a.py:970) substitutes B’s timing without taking the maximum against generation-0 timing. The saved smoke already has **high 35.344 h < low 35.485 h**, although admission uses “high.” Also, [O0’s allowance](/D:/Claude/random/wormWars/scripts/e5_1a.py:109) counts only one gains condition: §5 requires fixed **and** calibrated gains, hence **458,752 episodes**, falling to **393,216** with 16 null graphs. Recompute this from retained runs.

3. **Reference children still bypass the cap internally.** [The parent](/D:/Claude/random/wormWars/scripts/e5_1a.py:426) checks before launching each child, but the reference script then runs its entire settings/hunters loop without checking the remaining budget. Pass the remaining budget into the child and check before each play/trace. “Every play” is not yet true.

4. **The stated 1,024-world maximum is false.** [counts_by_task](/D:/Claude/random/wormWars/scripts/e5_1a.py:350) constructs **2,048** worlds for CUDA’s `4×512` and **4,096** for composition’s `8×512`; sensitivity also reaches 4,096. Preserve the required composition, correct §14.1’s bound, and validate memory at the actual maximum.

The finiteness checks, weighted intervals, genome coverage, scoring bench construction, and bench-bound cap gate otherwise look correct. The 28-case sabotage log does not test these revised driver calculations. I did not rerun GPU stages; the whole-suite log remains incomplete.