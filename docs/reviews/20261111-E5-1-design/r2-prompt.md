# Review request, round 2: E5-1's design, draft 2 (WormWars, stage 05, the hunter)

You reviewed draft 1 of `docs/E5/E5-1-DESIGN.md` (both of you: "fix then proceed"). Your round-1 answers are
archived in `docs/reviews/20261111-E5-1-design/r1-astra.md` and `r1-fable.md`; draft 1 is at commit `ae959a8`
(`git show ae959a8:docs/E5/E5-1-DESIGN.md`). Draft 2 is the working-tree `docs/E5/E5-1-DESIGN.md`, with a table of
changes in its last section (§12).

New since round 1, and worth checking:
- `wormwars/e5/stats.py` and `tests/test_e5_stats.py`: O1's labels and its one-level bootstrap.
- `scripts/e5_1_power.py` and its output `experiments/E5-hunter/E5-1/design-power.json`: the effect scale from E5-0
  and the simulated labels and coverage under assumed SDs. `runs/e5-1/` holds the tests' first failure and a sabotage
  log.
- The 500-generation choice rests on `experiments/E4s-stereo-module/E4s-1/eval-training.json` (`along`, M runs).

**What I want from you:**
1. **Is each of your round-1 must-fixes met?** Go through them by number and say met, partly met or not met, quoting
   draft 2 where it falls short.
2. **New problems draft 2 introduced:** the anchor arm A0 (its construction and how §5 reads O1 against it), arm P,
   the 4-runs-per-batch composition, 500 generations, the weighted fitness, the six labels and companion sentences,
   the Welch check, §6's failure handling, §7's pilot (does anything still leak the confirmatory comparison?), the
   seeds and world-id blocks, the cost table.
3. **Check the numbers** draft 2 cites (the simulation table, the 03r gains, E4s-1's curve, the cost arithmetic)
   against the files, and say which you checked.
4. Anything that must be settled before a pre-registration is written.

**Format:** a verdict first ("proceed", "fix then proceed", "revise"), then the must-fix status by number, then new
must-fix items, then should-fix, then anything else. Number your items and quote the text you object to. Be direct.
