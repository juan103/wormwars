You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

A design decision for experiment 03 of the WormWars repository (branch roadmap, HEAD; local).
Read `experiments/03-generation0/DESIGN.md` (v3.1) and `DECISIONS.md` D050-D052. The shuffle-only
pilot ran (`experiments/03-generation0/pilot.json`, 16 pilot shuffles, no N2); the five ensembles
are built and validated (`ensembles.json`). No N2 brain has been run.

The registered precision check failed for every primary signal. A pilot shuffle stands in for N2;
its bootstrap SE (genomes and worlds resampled; code: `scripts/exp03.py` cmd_precision) against
the between-graph SD of the 16 pilot shuffles (margins are 0.5 of that SD; the check requires
SE < 0.25 x margin):

| signal | stand-in SE | between-graph SD | implied true between-graph SD |
|---|---|---|---|
| P1 directional selectivity (512 probe genomes) | 0.0258 | 0.0461 | ~0.038 |
| P2 own mapping preference (64 genomes x 16 worlds) | 0.0122 | 0.0171 | ~0.012 |
| P3 food-information dependence (64 x 16) | 0.0126 | 0.0179 | ~0.013 |
| P4 history dependence (512 probe genomes) | 0.0130 | 0.0733 | ~0.072 |

Measured cost per graph (seconds): calibration 11, fitness 41 (7 task-mapping cells, about 6 s each
at 1024 genome-worlds), coverage 6, input response 17 (7 conditions x 512 brains), history 3.
645 graphs (N2, N2-rev, 3 N2perm, 5 x 128). Throughput is compute-bound at about 168
genome-worlds per second. No hard budget from the owner; the design set a cap of 18 GPU-hours.

Claim to attack (my proposal):
(a) P1 and P4 stay primary, with more random brains: P1 at M0 with 8192 brains, P4 with 2048
    (about +47 s per graph, +8.4 GPU-hours).
(b) P2 and P3, the fitness signals, cannot reach the precision at 645 graphs (they need roughly
    30x more samples per graph). They become secondary, reported with their SE and an explicit
    power statement; no compatibility claim is possible for them.
(c) Margins are re-derived from the pilot after de-attenuating measurement noise, and the rank
    tests stay the primary inference (valid under exchangeability even with noise, since N2 and
    every ensemble graph are measured the same way).

Questions:
1. Is (a)-(c) sound? Is there a better allocation: for example a high-precision subset of graphs
   per ensemble for P3 (the signal closest to the owner's question: food-task specificity), fewer
   ensembles, fewer graphs, or a different estimator (per-graph shrinkage, a mixed model)?
2. Is the precision criterion itself right: margins at 0.5 SD of a spread that includes noise,
   and SE < 0.25 margin? What should it be?
3. Anything else the pilot numbers reveal that the pre-registration must handle?

Numbered points, MAJOR or MINOR, concrete, with file:line. Be brief about what is fine.
