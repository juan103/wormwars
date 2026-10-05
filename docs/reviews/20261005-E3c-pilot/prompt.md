You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# E3c: the pilot's results, before the power analysis and the pre-registration

You are reviewing, read-only, the WormWars repository in the current directory.
- **The design you agreed:** `docs/E3/E3c-DESIGN.md` v2.1 (D200).
- **The pilot code you reviewed:** `scripts/e3c.py`, which ran after your fixes (D201).
- **The pilot has run.** Read `experiments/E3-ab-organism/E3c/PILOT.md` first (my summary), then check it
  against `pilot.json` (the record) and `diagnostics/seed-check.json`. D203 in `DECISIONS.md` is the log entry.

**In short:**
- **§5's fixed branch is "mazes":** all three arms left the floor (W2 alone + 1 = 2.72 visits per wey).
- **S-mod and S-dense** reached 6.6-6.8 by generation 99. They were at about 6.2 already by generation 25,
  against the seed's 4.82 on the same block.
- **P-sel** succeeded in 1 of 3 runs.
- **The S champions score almost the same on every maze:** per-maze SD about 0.5, against the seed's 3.7. One
  explanation would be a maze-independent, possibly scent-free routine; I have not tested it.
- **The pilot saved no genomes.** The champions cannot be probed without retraining.
- **The seed's 4.82 here against 5.84 in E3b-1** was checked: both play paths reproduce both numbers exactly,
  so the difference is between the blocks.

**Please answer each question, citing files and lines where relevant:**
1. **The branch and the factor:**
   - Is "mazes" the right application of §5's rule?
   - Should the mutation factor stay at 1.0, the only thing §5 lets the pilot change?
2. **Do the S champions use scent?** Do you read the per-maze pattern as I do, or is there a better
   explanation? Check `pilot.json`'s per-maze arrays: the references' and every final's `per_maze`.

   What should establish it, and when?
   - (a) A registered reading in the formal run: champions played with their noses silenced (E3b-2's
     `without_scent`, `wormwars/e3/attribution.py`). Should it be a primary guard, a secondary reading, or
     descriptive?
   - (b) A scripted wall-follower reference (new code).
   - (c) A short exploratory step before the pre-registration, such as retraining one S-dense run with genome
     saving (about 1 GPU-hour) and probing it.
   - (d) Something else.
3. **Does a scent-free solution, if confirmed, undermine E3c's question?**
   - §1 compares assemblies of stereo navigators. §5 forbids changing the task: no shaping, no easier maze,
     no other fitness.
   - If the S champions do not use their noses, should E3c still run as designed, with the scent reading
     interpreting Q1 and Q2? Or does the design need to change? If so, how, given §5?
4. **Q2's registered expectation** is "P-joint better" (§1, §6). The pilot suggests S-mod may pass the seed
   by more than E3b-1's tuning did. Those numbers are on different blocks, and P-joint itself is not yet
   measured on E3c's block.

   Should the expectation stand as written, with the pilot disclosed? Or should it be revised before
   registration, labelled post-pilot?
5. **The power analysis:**
   - the S arms' run-to-run spread is tiny (SD about 0.05-0.07 visits per wey);
   - P-sel looks bimodal.

   What should it model? And what practical margin for Q1 and Q2 is scientifically relevant (§6 says the
   margin is chosen for relevance, not detectability)?
6. **Your verdict:**
   - "proceed to the power analysis and the pre-registration", with a numbered list of changes;
   - or "one more exploratory step first", saying which, its cost, and what result would change what.

The compute used so far is 2.82 GPU-hours of E3c's 30.
