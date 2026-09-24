# Corrections to experiment 01

This file is **not** part of the frozen record. Everything else in this folder is exactly as it was
frozen (tag `exp01-v1.0`) and must stay that way: corrections go here instead, and the frozen files'
hashes stay verifiable (`DECISIONS.md` D033).

**Verifying the frozen files.** `bundle-hashes.txt` was written on Windows, where Git checks text
files out with CRLF line endings, and it pins that form. On Linux or macOS, convert a file to CRLF
before hashing it, for example `sed 's/$/\r/' SUMMARY.md | sha256sum`, or run
`pytest tests/test_frozen_records.py`, which does this for every pinned file.

Corrections C1-C4 are already inside the frozen `RESULTS.md`. C5 was found after freezing.

### C5 — every run in this document used chemical synapses running backwards

**Everything above describes a brain whose chemical synapses carried signal from the postsynaptic
neuron to the presynaptic one.** `Genome.dense` stored weights pre-by-post and `Brain.step`
multiplied by their transpose. The bug was present from M2, before any run. Gap junctions are
symmetric and were unaffected. It was found by Astra 6 (OpenAI) while reviewing the roadmap,
confirmed on the real brain, and fixed. The old update is kept behind a switch, and a test replays
one published held-out score from this document in that mode and requires it to the last bit
(`DECISIONS.md` D031, D033).

**What the experiment actually tested** was the worm's chemical wiring *reversed*, with its real gap
network, against degree-preserving shuffles and random graphs *of that reversed graph*. That
comparison is internally valid. It is not a test of the real *C. elegans* wiring, and every sentence
above that reads it as one is wrong. Path arguments are affected too: the hop counts in C4 (in `RESULTS.md` here) and in
`DECISIONS.md` D008 were counted in the true direction, not the one the simulation ran.

**The headline arm was rerun with the synapses the right way round,** pre-registered before any run
and otherwise identical, as [experiment 01b](../01b-direction-corrected/RESULTS.md). The pre-registered contrasts:

| | synapses reversed (above) | synapses correct (01b) |
|---|---|---|
| N2 − SH, mean best-of-generation fitness | −0.100 [−0.129, −0.070] | **+0.068 [+0.034, +0.102]** |
| N2 − RD, mean best-of-generation fitness | −0.112 [−0.150, −0.077] | **+0.067 [+0.021, +0.105]** |
| N2 − SH, final held-out score | −0.047 [−0.148, +0.039] | +0.069 [−0.015, +0.169] |
| N2 − RD, final held-out score | −0.041 [−0.113, +0.029] | **+0.094 [+0.029, +0.160]** |

The sign of the "speed" contrast reverses with the direction of the synapses. The 01b write-up does
not claim that the real wiring *improves* faster. That measure averages all 25 generations,
generation 0 included, and N2's edge over the shuffles is, as a point estimate, a higher starting
point with the same gain. Neither starting level nor gain separates on its own. N2 is also one
graph, calibration equalises motor drive only approximately (a residual that favours N2 slightly),
and nothing here shows N2 lies outside the distribution of individual control graphs.

The uncalibrated arm, pump-gated foraging, coevolution and the combat tactics were **not** rerun,
and still describe the reversed graph.

Both are kept. Nothing above has been edited; this entry is the correction.
