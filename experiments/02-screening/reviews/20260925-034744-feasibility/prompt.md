You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

A decision before any N2 run in experiment 02's screening. You reviewed its design (v2); much has
happened since. Please read `DECISIONS.md` D034-D037 first, then `experiments/02-screening/DESIGN.md`,
`experiments/02-screening/diagnostics.json` and `experiments/02-screening/pilot.json`. Code:
`wormwars/exp02/` and `scripts/exp02.py` (branch exp02-screening; nothing is pushed).

## Where things stand (all scripted controllers or the discarded pilot shuffle SH101; no N2 data)

- **Task world** (D034). T0 is stereo and T1 is single-nose, both with odour sigma 1, 200 ticks,
  food x2 and a halved sensing scale. The scripted gate passes. T1 memory share: 0.399 [0.383,
  0.415]. T0 stereo share: 0.435 [0.418, 0.452]. The best controllers eat 70-74% of the food.
  Memory also beats a tuned *graded* memoryless controller by +0.98 [+0.94, +1.01].
- **History probe** (D037). Jitter of 1 cell is the only one of six ablations that leaves the
  scripted memoryless controller unchanged and removes the scripted memory controller's advantage.
- **Pilot evolved champions** (SH101, 40 generations, scored on held-out worlds):
  - T1 champion: 2.689, against 2.117 for the scripted memoryless controller and 3.077 for the
    memory one. Real minus ablated: food constant +1.215; food mirrored +0.679; collision off
    +0.349; jitter 1, 2 and 3 cells: +0.004, -0.007 and +0.009, all intervals around 0. (Jitter 3
    hurts the scripted memoryless controller by -0.057.)
  - T0 champion: 2.729, against 3.231 for scripted stereo. Reduced to one nose: -0.071 [-0.118,
    -0.025]; jitter has no effect.
- The pre-registered feasibility gate required the T1 champion to beat scripted memoryless AND
  lose under the history probe. It beats it by +0.59, but it does not lose.
- **Running now:** the same pilot at 120 generations, snapshots at 40, 80 and 120, checking whether
  jitter or one-nose sensitivity appears with longer evolution.

My reading: after 40 generations, evolved brains use food heavily but at a coarse spatial and
temporal scale, perhaps integrating over many ticks (time constants reach 20), which averages the
jitter away. They also use collision. They do not use the fine-grained capabilities (one-tick
history, stereo steering) that the scripted gate shows the tasks reward. If the grid ran as is,
"worm-like" versus "not" could differ in task design only, not in what the brains do.

## Questions

1. Is that reading right? What else could explain an evolved champion that beats the memoryless
   controller by 0.59 yet is insensitive to 3-cell jitter? Is the jitter probe simply invalid for
   integrating brains, and if so, what history ablation would be valid for them (validated how)?
2. Options:
   (A) raise generations, if the 120-generation pilot shows the capabilities emerging;
   (B) run the screening as designed, measure each champion's actual capability use with the
       probes as an outcome, and interpret the interaction only through measured use;
   (C) change the tasks or the evolutionary setup further (what, specifically?);
   (D) something else.
   Which would you choose within a 12-GPU-hour screening (the grid itself is ~5.3 h at 40
   generations), and why?
3. What must the pre-registration say about this, whichever option is chosen?

Be concrete and brief; mark points MAJOR or MINOR. Check files where you can.
