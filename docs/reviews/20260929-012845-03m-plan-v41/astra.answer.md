Confirmed: v4’s remaining blocker is resolved.

- [Smoke selection](/D:/Claude/random/wormWars-p4/scripts/p4m.py:694) now includes three singles. The smoke record reports completion at clean `f71f6f9`, with RIAR, AIZL and RIAL in both follow-up passes.
- I read the follow-up NPZ: all **12 arrays** exist, each contains eight finite values, and their absolute means exactly reproduce the JSON numerators and denominators.
- The [new stop test](/D:/Claude/random/wormWars-p4/tests/test_p4m.py:201) reaches the final gap-pass check and requires the completed chemical summaries and `final` arrays to survive. The decay test now mocks graph rebuilding.
- Comparing the Q1 files across `d7447ac` confirms unchanged numerical content, clean `f71f6f9` stamps, and the recorded tails input directory.

One nonblocking improvement: explicitly assert retention of `steady` arrays and completed gap arrays in the stop test. The callback currently saves them together.

I did not independently rerun the 19 tests or the reported sabotage check; this confirmation rests on code inspection and read-only verification of the saved artifacts.

**03m plan: ready to run**