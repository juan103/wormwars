You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Final confirmation before main (commit 35c9f70, branch roadmap)

Two items, for a short confirmation, not a full round. You may read any file; you cannot run anything.

1. **03m's corrections.** Your confirmation round (`docs/reviews/20260929-064250-03m-results-confirm/`)
   asked for small fixes. They are the "Further corrections, from the confirmation round" list at the
   end of `experiments/03m-p4-mechanism/RESULTS.md`. Also updated: the 03m rows and lines in the root
   `README.md` and `ROADMAP.md`. Check that each fix is right and that the new README and ROADMAP
   lines do not overclaim.
2. **A test change** (`tests/test_world.py`, commit 4b6ad01). `test_batching_worlds_does_not_change_a_world`
   compared a world simulated alone with the same world in a batch of 4, to 1e-5 after 40 ticks, and
   failed once on a Linux CI runner (D112). It is replaced by
   `test_batch_mates_do_not_change_a_world`, which keeps the composition fixed (1 strain, 4 worlds)
   and changes only the batch-mates, and requires exact equality; the world-generation test just above
   it already covers different batch sizes at tick 0. Is this the right claim to test (D082, D091,
   docs/REPRODUCIBILITY.md), and is anything lost?

If both are right, 03m and the test change go to main. End with one line: **"ready for main"** or
**"fix"**, and what to fix.
