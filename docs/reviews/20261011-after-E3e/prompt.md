You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# After E3d and E3e: what next before E4?

You are reviewing, read-only, the WormWars repository in the current directory, at 6bc3bfc (branch `roadmap`).

**The situation:** E4 asks whether information crosses between two navigation modules. It needs a maze task where
scent-free coverage cannot win and navigation pays (`ROADMAP.md`; E3c's results). Two exploratory validations ran:
- **E3d** (`experiments/E3-ab-organism/E3d/RESULTS.md`): 6 × 6 island mazes, "failed at calibration" on G1b alone.
  A random walk made 2.34-2.53 visits per wey against an absolute limit of 2.0. G1a passed (the walk ÷ the
  follower, 0.14-0.15), G2a narrowly (0.37-0.39 of the oracle, intervals crossing ⅓), and G3 widely. Wall-followers
  and E3c's scent-free champions scored almost nothing.
- **E3e** (`experiments/E3-ab-organism/E3e/RESULTS.md`): the same at 7 × 7, "failed at calibration" on G1a and G2a.
  The walk fell under 2.0, but the scent follower collapsed to 0.13-0.16 of the oracle. With trails off, the
  follower no longer beats the walk.

Both are within a horizon of 2 400 ticks. The designs are `docs/E3/E3d-DESIGN.md` and `docs/E3/E3e-DESIGN.md`.

**The owner's options**, from E3e's results:
1. 7 × 7 with a longer horizon;
2. 6 × 6 with a shorter horizon;
3. a stronger navigation signal (the scent's reach, or the trails' persistence) at 7 × 7;
4. use one of the two families for E4 as it is, with its blind and navigator references reported;
5. stop maze validation and decide E4's direction otherwise.

**A claim to attack (Claude's recommendation):**
- **Option 4,** using E3d's 6 × 6 family at k_r = 0 for E4.
- **E4's pre-registration** would name the random walk (about 2.3) and the wall-follower as fixed blind references,
  and require its effects to clear them, stating openly that E3d's absolute cap was not met.
- **The reasons given:**
  - at 6 × 6 navigation pays (the follower about 7 × B_max, the seed about 4 ×), and coverage by wall-following
    is defeated;
  - G1b's 2.0 was a choice about the claim, not a measurement;
  - option 2 would probably fail G2a, which is already narrow, because a shorter horizon cuts the follower's
    discovery time;
  - option 1 would need the follower's ratio to the oracle to more than double, while the walk also gains;
  - a third tuning round risks a garden of forking paths.

**Please answer:**
1. **What do you recommend, and why?** Weigh the claim above against the alternatives, including any not listed.
2. **If option 4:** what must E4's design do so that a task that failed its own validation gate does not weaken
   E4's question or its reading? Is k_r = 0 the right choice?
3. **If another option:** what would it cost, and what would make it pass or fail?
4. **Is anything in the claim wrong** on the facts in the committed records?
