You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Plan review: E3b-2, where E3b-1's gain comes from (exploratory)

You are reviewing a plan in the WormWars repository (your working directory). You may read any file.

## Context

E3b-1 is published (`experiments/E3-ab-organism/E3b-1/RESULTS.md`; `PREREGISTRATION.md`; `evaluate.json`).
You reviewed it. A GA tuned the seed E + W2 (two stereo comparator modules, a latch and a wall reflex on a
silent worm) in 5 × 5 tree mazes, with colonies of 8 and shared trails.
- **The gate read "better":** +0.225 of the seed's mean (T-A +0.069, T-F +0.381).
- **The probes:** no tuned champion meets the seed's comparator criteria.

The owner chose to ask where the gain comes from before choosing between E3's assembly comparison and E4
(D193 in `DECISIONS.md`).

**The plan:** `docs/E3/E3b-2-PLAN.md`, draft 1. It is exploratory, with no gate and a cap of 5 GPU-hours.
It covers:
- **exact attribution** of each champion's gain over two partitions of the tuned parameters: functional
  (sensing, gating, output, latch) and by side (module A, module B, selector). Each uses all seed/champion
  hybrids, with Shapley values, reversions, transplants and interactions;
- **lesions;**
- **a recorder of in-maze latch–goal agreement;**
- **the resting turn,** from E3b-1's probes;
- **a replication** of the intact champions on fresh mazes.

The relevant code includes:
- `wormwars/e3/tuning.py` (`scales`: what was mutable);
- `wormwars/e3/organism.py` (the organism's parts);
- `wormwars/e3/maze_world.py` (per-wey goal);
- `wormwars/world.py` (brain state, the recorder hook);
- `scripts/e3b1.py`.

## The question

**Will this plan answer "where does the gain come from" well enough to inform the choice between E3's
assembly comparison and E4, within about 5 GPU-hours? What should change before code is written?**

Please check in particular:
1. **The partitions.** Do the four functional groups and the three side groups cover the mutable set
   correctly, against `tuning.scales` and the organism? Are they the right cuts for the question? For
   example, should the comparator biases sit with gating, and should the relays' frozen parameters or the
   frozen reflex feature anywhere?
2. **The attribution method.** Hybrid parameter swaps can create organisms off the path either the seed or
   the champion lives on, and Shapley values average over them. Is that interpretable here? Are reversion and
   transplant the right companions? Is anything better for 16 champions?
3. **The lesions.** Do they test what they claim? For example, does "latch frozen" by cutting the relay
   inputs hold q at a meaningful state, given the started brain and q's own dynamics? Is "gate cut" well
   defined when comparator biases were tuned?
4. **The latch recorder.** Is sign(q) against the goal, after the first visit, a fair measure of tracking
   (coding flips, undecided states, per-wey goals)?
5. **The mazes and the inputs.** A fresh block 7000-7255. Any risk of contaminating E3b-1's records, or of
   reusing its test block?
6. **The reporting rules (§8).** Do they avoid overclaiming? Is anything missing that the follow-up
   decision will need, such as N's or R's champions, the "none" condition for attribution, or the later-leg
   rate?
7. **The compute and the drop order.**

Please end with a verdict: "go" (code may be written), "go with changes" (list them), or "revise".
