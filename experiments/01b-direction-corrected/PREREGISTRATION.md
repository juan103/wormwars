# WormWars 01b: experiment 01's headline comparison, with synapses running the right way

**Status: pre-registered.** Written and committed before any 01b run existed. Nothing below may be
changed after the first run starts. Any deviation goes in `DECISIONS.md` with the reason.

## Why this exists

Every run of experiment 01 used chemical synapses that carried signal from the postsynaptic neuron
to the presynaptic one (`DECISIONS.md` D031, found by Astra 6). So 01 compared the worm's chemical
wiring *reversed* against shuffles and random graphs of that reversed graph. Its comparison is
internally valid, but it is not a test of the real wiring. 01b asks 01's question again, with the
synapses the right way round.

## The one thing that changes

`--chem-direction pre_to_post` instead of the reversed update 01 ran.

Nothing else. This is checked, not assumed: the current code run with `--chem-direction post_to_pre`
reproduces 01's `m9-calibrated` N2 run 0 (seed 40001) and SH1 run 0 (seed 40016) to the last bit
(held-out score, survival, training score, AUC, and SH1's calibrated motor gains). It also steps
01's N2, SH1 and RD1 champions bit-identically for 300 ticks.

## Design, identical to 01's headline arm (`m9-calibrated`)

```
python scripts/experiment.py --k 5 --runs 3 --generations 25 --population 32 --worlds 8 \
    --ticks 400 --holdout 32 --base-seed 40000 --conditions N2,SH,RD --calibrate \
    --chem-direction pre_to_post --device cuda --out runs/exp01b-direction-corrected
```

- **Conditions:** N2 (Cook et al. 2019), SH1-SH5 (degree-preserving shuffles), RD1-RD5 (random
  sparse graphs with matched neuron and edge counts). These are the same ten control graphs, from the
  same seeds.
- **Runs:** 15 per condition (N2 15 runs; each control graph 3 runs), 45 in total, with the same run
  seeds as 01.
- **Budget:** 25 generations x 32 strains x 8 worlds x 400 ticks; held-out score on 32 world ids
  never used for selection.
- **Motor gain calibration:** the same protocol. Each graph's random population is matched to N2's
  mean |forward| and |turn|. The gain *values* will differ from 01's, because reversing the synapses
  changes what N2's random population does. That is the protocol working, not a change to it.
- **Integrator:** 8 substeps, as in 01. It is adequate in this generation range (`DECISIONS.md` D032:
  0 of 1440 weys of 01's champions have a read-out error above 0.05). It is kept so that exactly one
  thing changes.

## Analysis, identical to 01's

The report `scripts/experiment.py` writes, unchanged:

- a hierarchical bootstrap with runs nested in graphs, over 20 000 resamples;
- the contrasts N2-SH, N2-RD and SH-RD, on final held-out score and on speed of improvement (the
  mean of the best-of-generation fitness over the 25 generations);
- the unit of analysis is the run.

**A contrast "separates" when its 95% interval excludes zero.** Otherwise it is reported as no
detectable difference, with its interval, and never as equality.

## Predictions, made before any 01b data

1. **Final held-out score: no contrast separates.** 01 found no difference for the reversed graph,
   and I know of no mechanism by which the true direction should help foraging within 25
   generations.
2. **SH vs RD: no separation** on either measure, as in 01.
3. **Speed of improvement, N2 against the controls: no prediction.** 01 found N2 clearly slower and
   could not say why. The reversal is now a candidate explanation, but I cannot say in advance
   whether it is the explanation. Both outcomes are reported with equal prominence.

## What each outcome will mean

- **If N2 is no longer slower** (both N2-control intervals for speed include zero or lie above it):
  01's "N2 is slower" is attributed to the reversed wiring, and 01's correction says so.
- **If N2 is still slower** (both intervals below zero): the slower start belongs to the real wiring
  under this interface and budget. It is still unexplained.
- **If N2 separates above the controls on final score:** it is reported as a result of 01b, limited
  to this interface, this task and 25 generations.
- **In every case,** 01 stays published as it is, with a correction (C5) saying what it actually
  tested. 01b becomes the result to cite for any claim about the *real* worm wiring.

## Not rerun here, and why

- **The uncalibrated arm** (`m9-uncalibrated`), **pump-gated foraging** (`m8`) and **coevolution
  and combat tactics** (`m7`, `m7-varied`) are not rerun. 01b reruns only the headline comparison,
  so the first corrected answer comes quickly and cheaply. Those results remain results about the
  reversed graph, and 01's correction will label them that way. They can each be rerun later under
  their own pre-registration.

## Cost

01's arm took 0.897 GPU-hours. Two reproduction runs today took 126 s and 356 s against 01's 71 s
per run, so 01b is budgeted at up to 4.5 hours of wall time on the same RTX 5080.
