You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

A go/no-go decision for experiment 02's screening, before any N2 run. You reviewed its design (v2);
much has happened since. Read `DECISIONS.md` D034-D037, `experiments/02-screening/DESIGN.md`,
`experiments/02-screening/diagnostics.json` and `experiments/02-screening/pilot.json`. Code is in
`wormwars/exp02/` and `scripts/exp02.py` (branch exp02-screening; nothing is pushed).

## Evidence (all scripted controllers or pilot-only shuffles SH101-SH108; no N2 fitness data)

1. **Task world** (D034). T0 is stereo and T1 is single-nose, both with odour sigma 1, 200 ticks,
   food x2 and a halved sensing scale. Scripted gate: T1 memory share 0.399 [0.383, 0.415]; T0
   stereo share 0.435 [0.418, 0.452]; the best controllers eat 70-74% of the food; memory beats a
   tuned graded memoryless controller by +0.98.
2. **History probe** (D037): jitter of 1 cell is the only valid ablation on scripted controllers.
3. **Evolved champions on SH101 use food heavily, but not the fine capabilities:**
   - T1 at 40/80/120 generations: held-out 2.655/2.730/2.877 (scripted memoryless 2.117, scripted
     memory 3.077). Loss under 1-cell jitter: ~0 throughout. Under 3-cell jitter: +0.039 [+0.014,
     +0.065] only at 120. Food replaced by a constant: -0.78 to -1.33.
   - T0 at 40/80/120: loss when reduced to one nose +0.025, +0.005, -0.010 (scripted stereo is
     worth ~1.1). Four times the training worlds per strain: +0.024 [-0.002, +0.052]. Four times
     the population: +0.058 [+0.031, +0.091], held-out 2.874.
4. **A structural cause.** Random brains' turn response to a left-right food difference, measured
   outside the world (the planned input-response probe), is 0.009-0.030 (median 0.014) across
   eight pilot-only shuffles. **Disclosure:** I also saw N2's value under the M0 mapping, 0.12,
   4-13 times higher than any shuffle. I deliberately did not look at N2 under the remaps. This is
   generation-0 structure, not fitness, but it is N2 information seen before pre-registration.
5. **Cost:** ~2 min per 40-generation run. The grid as designed takes 4.5 h plus 0.9 h of probes,
   against a 12 h cap.

## The claim to attack (my proposal, not a conclusion)

Option B+: run the screening at 40 generations, and make each champion's *capability use* an
outcome, measured with probes on every champion: stereo use (T0: real minus one-nose), history use
(T1: real minus 1-cell jitter, and minus 3-cell jitter), and food use (real minus constant). The
interaction estimates stay. The new mechanistic question is whether N2's champions use stereo or
history where shuffles cannot, given the routing difference in point 4. Spend the freed budget on
replication: N2 4 -> 8 runs, SH 6 -> 8 graphs x 2 runs, about 8.4 h in total. Disclose point 4 in
the pre-registration, and label any prediction it informs.

## Questions

1. Is option B+ sound, or does point 4 (and my having seen it) compromise it? Would you instead
   stop and redesign the evolutionary setup, or the tasks? What exactly?
2. If B+: what must be pre-registered about capability use (estimands, thresholds, which probe
   counts as "uses history" given that jitter-1 was validated only on one-tick scripted memory),
   and what would falsify "N2 uses what shuffles cannot"?
3. Anything that makes running now a mistake?

Numbered points, MAJOR or MINOR, concrete, checking files where you can.
