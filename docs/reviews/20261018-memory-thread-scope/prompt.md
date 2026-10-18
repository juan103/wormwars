You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are being consulted, read-only, in the repository you can read (branch `roadmap`, commit 72c1a76). This is a
**scoping round** for the next experiment, before any design is written. Nothing has been coded or run for it.

## Background

**The memory thread** (`ROADMAP.md`, "The thread worth following: memory (a hypothesis)"): N2 starts with more
capacity to hold recent history. Evolution then builds such memory into every graph, which would explain why N2's
early advantages fade. The roadmap's untested predictions:
- (1) N2's early advantage over null graphs should be larger on tasks that require memory than on tasks that do not;
- (2) it should shrink over generations;
- (3) the history effect should localise to identifiable circuitry.

03mc partly addressed (3) for random brains (RIA, AIY, gap junctions).

The owner left the choice of the next step to Claude ("Do as you consider best", D318). Claude chose this thread.
GPU runs need the owner's word.

## What the repository already shows (please check these claims)

- **N2's head start is small, and never separated statistically:**
  - 01b: the best at generation 0 was N2 1.236, SH 1.162, RD 1.215, with the same gains afterwards
    (`experiments/01b-direction-corrected/RESULTS.md` 80-90).
  - 02: the normalised N2 − SH advantage on 8 SH graphs went from +0.062 [−0.015, +0.134] (T0) and +0.072 [−0.002,
    +0.138] (T1) at generation 0 to +0.021 and +0.019 at generation 39. "What changes is the shuffles, not N2"
    (`experiments/02-screening/RESULTS.md` 179-207, `runs/exp02-screening/analysis.json`).
  - 02's task contrast at generation 0, I(T1) − I(T0), was +0.001 [−0.022, +0.023]. But both T0 and T1 reward
    memory.
- **No fitness head start for random brains:** 03 found, on T0-M0, a genome mean of N2 0.90 against the SH median
  0.89 (`experiments/03-generation0/RESULTS.md` 165-166).
- **P4, the history effect on 2 048 random genomes,** is distinctive for N2 in 03, 03r and 03mc (0.931, 0.924,
  0.926). It is measured by `wormwars/exp03/measures.py` `history()`.
- **Selection builds history into every group** (02b): the turn |rising − falling| at generation 0 and generation 39
  was N2 0.095 and 0.452 against SH 0.030 and 0.111 on T0.
- **No clean memory-free task exists here:**
  - stereo Task N has a memoryless stereo solution (8.78, E1), but evolved brains never find it (E2d's non-stereo
    plateau, 04a mono ≈ stereo);
  - Task N-mono rewards memory: KT 1.20 against KTM 2.84 (`experiments/03a-self-consistency/DESIGN.md` 84-102);
  - 02's T0 and T1 both reward memory.
- **E3a's shuttle** (bridge 2's task) runs on a hand-built circuit on a silent worm. No N2 neuron is in its loop
  (`experiments/E3-ab-organism/E3a/PREREGISTRATION.md` 31, 43, 121), so it cannot test N2 as it stands.
- **The machinery:**
  - 03's five null ensembles (`wormwars/exp03/samplers.py` `build`, about 1.5 s per graph);
  - per-graph motor calibration;
  - `wormwars/e04a/evolve.py` `evolve_batch` (one `BrainSpec` per batch, so one graph per batch);
  - about 200-420 episodes per second;
  - 03a's bounded-history probe (`wormwars/e03a/probe.py`).
- **Food sensing modes:** "stereo" and "mono", both levels (`wormwars/world.py` 839).

## Claude's candidate, as a claim to attack

**A within-task manipulation of memory demand.** Keep Task N-mono, and change only what the food sense reports.
- **"Level"** (the current mono): a memoryless controller scores about 1.2, and one tick of memory about 2.8.
- **"Change"** (new): the same neurons receive the change in the food level since the last tick, possibly mixed with
  the level. A memoryless controller can then act as KTM does.
  - Before any GPU work, check with scripted controllers that memory adds little there.
- **Measure:** N2 against two or three of 03's ensembles (SH-mirror and SH-route?), with several graphs each and
  evolutionary runs within graphs. Score at several generations, for example 0, 25, 100 and 250.
- **Primary contrasts:**
  - (1) the interaction (N2 − null) under "level" minus (N2 − null) under "change", early;
  - (2) its change over generations.
- **History use** measured on every champion with the bounded-history probe.

## Please answer

1. **Is the manipulation sound?**
   - Is "level" against "change" a valid way to vary memory demand while holding the task and the interface fixed?
   - What does it confound? For example: input statistics and scaling, which neurons carry the signal, and whether
     "change" makes the task easier for every graph.
   - Is there a better contrast available in this codebase?
2. **Is the question worth a run, given 02's null task contrast and 03's absent head start?** What effect size could
   plausibly be detected, and with how many graphs and runs? Use 02's variance if you can; say if a reliable estimate
   needs a pilot.
3. **The design choices:**
   - which ensembles, and how many graphs each;
   - runs per graph;
   - the generations to score;
   - what "early advantage" means operationally: best of the population, a top quantile, or the validation score of
     the champion so far;
   - the controls (scripted calibrators per sensing mode);
   - the history-use measure.
4. **Alternatives worth preferring:**
   - prediction (2) alone on one memory task;
   - prediction (3) for evolved brains;
   - wiring N2 into the shuttle (bridge 2 proper);
   - or something else.
5. **A rough budget,** and what should be pre-registered.

Be direct. Disagree with the candidate if it is weak. Answer with a recommendation first (one line), then numbered
points. Do not edit files or run anything.
