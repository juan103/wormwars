**fix — one test-only must-fix before formal stages.** All eight original code fixes are present. I found no new runner defect; the guarded smoke can proceed.

Must-fix:

1. **The expected final-generation ID prefix remains untested.** At [tests/test_e2d_commands.py:391](D:/Claude/random/wormWars/tests/test_e2d_commands.py:391), the tampering changes one strain, testing row consistency. I removed `(block[0, :W8] == want).all()` from [scripts/e2d.py:885](D:/Claude/random/wormWars/scripts/e2d.py:885) **in memory**, and the strengthened direct test still passed. Add a case that changes the first ID identically across all `P` rows of one run, leaving its roster and generation-0 record intact. Assert pairing fails, and sabotage-check removal of the prefix comparison. The current implementation correctly rejects this case.

Suggestions:

- Strengthen [tests/test_e2d_commands.py:338](D:/Claude/random/wormWars/tests/test_e2d_commands.py:338): compare recorded IDs with the final training call received by the fake rollout. Currently it asserts only dimensions.
- Add a completed-C2/missing-matched-checkpoint case and assertions for the added analysis outputs. The stopped-arm test does not independently exercise C2′’s completeness condition.

Checked and correct:

- **Cap and incomplete arms:** capped arms are accepted as final prerequisites; reruns remain forbidden. Stopped arms are excluded from evaluation and readings. Unpaired arms receive no paired readings or dependent contrasts. C2′ requires every matched checkpoint.
- **Part B propagation:** failed checks suppress set readings and make Part C use scores alone. Both behavioral cases pass; restoring class-based plateau decisions under failed checks is caught.
- **Configuration and capture:** arm configuration and hash are refreshed before partial records, including generation count. `run_method` resolves the wrapped rollout dynamically. An in-memory harness confirmed capture of the final 2-D training IDs, exclusion of validation calls, and restoration of the original rollout.
- **Statistics and projection:** bootstrap SE, paired percentile levels, and inclusion of spent time plus current projection time are correct. The SE test catches substitution of SD/√n.
- **Outputs:** continuous contrasts, matched-reference classifications, registered-champion comparisons, disagreement notes, budget costs/curves and named genomes are present. D134 explicitly records the real-only budget reading when probe checks fail.
- **Sources:** independently verified all 48 champion references against local parameter hashes: 47 distinct genomes, with 04a’s 12/4 split. Budget costs match 166,144 and 100,608 episodes per run.

Reviewed `f67614b`. Ran 31 pure analysis cases, two plateau cases, and targeted in-memory checks. Full command tests were inspected, not executed because they write files. No GPU work or file changes.