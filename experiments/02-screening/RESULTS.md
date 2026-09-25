# WormWars 02: results of the screening

**The primary prediction is challenged: 40 generations of evolution found meaningful stereo use for
nobody, N2 included.** Removing the left-right food difference costs N2's stereo-task champions
+0.027 [+0.000, +0.060] and the shuffles' +0.023 [+0.003, +0.047], against a pre-registered
threshold of 0.10. The contrast is +0.004 [−0.032, +0.044].

Before any evolution, N2's wiring does carry the advantage the prediction was built on. Random N2
brains turn toward the stronger food side 3-10 times more than random shuffles do, and only when
food enters through the biological neurons. Random N2 brains also forage better under that mapping
than under the wrong ones, relative to the shuffles. **Evolution does not keep either advantage.**
By generation 39 the mapping-specific fitness advantage has shrunk to an interval straddling zero,
and the evolved champions do not use stereo.

This is a screening experiment: a 12-GPU-hour fraction of a larger design, meant to find failure
modes and size the full experiment ([`DESIGN.md`](DESIGN.md)). It was pre-registered in
[`PREREGISTRATION.md`](PREREGISTRATION.md) before any N2 run, with the disclosures in its §2.
Only the primary outcome (§4) carries a verdict. Everything under **Secondary** was registered as
exploratory, and everything under **Not registered** was chosen after seeing the data.

Run: `runs/exp02-screening/`. 190 runs, 5.64 GPU-hours of evolution and 7.44 GPU-hours in total
with the probes, of a 12-hour cap. No probe step was dropped. One RTX 5080. The evolution ran from
commit `225e8f8` and the probes and report from `971bbb3`; the only difference is Fable's review
amendments, which touch probes, analysis and wording (D041).

---

## Primary (pre-registered, §4)

For each generation-39 champion in cell T0-M0 (stereo foraging, food into AWA, AWC and ASE): the
mean over 64 probe worlds of the real score minus the score with the bilateral mean fed to both
sides. N2 averages its 8 runs; SH averages the means of its 8 graphs (16 runs). The interval is a
hierarchical bootstrap, 20 000 resamples.

| | use of the left-right difference [95% bootstrap] | t-interval | class |
|---|---|---|---|
| N2 | +0.027 [+0.000, +0.060] | [−0.012, +0.067] | below threshold |
| SH | +0.023 [+0.003, +0.047] | | below threshold |
| **N2 − SH** | **+0.004 [−0.032, +0.044]** | Welch [−0.038, +0.047] | |

**Verdict: challenged: no meaningful N2 use.** N2's whole interval lies below 0.10. The data are
complete: all registered runs and seeds are present, and no probe entry is malformed. No SH graph
shows detected meaningful use either (0 of 8; graph estimates −0.001 to +0.072). By the
registered reading, **the search found stereo for nobody**. That says nothing either way about
whether N2's wiring is better or worse for stereo, which this experiment therefore could not test.

The mirror-symmetry reading registered for a supported result does not arise. The covariates are
still reported below.

---

## Secondary (registered as exploratory; intervals, no claims)

### Evolved champions barely use any fine capability

Real minus probed score at generation 39, T0-M0 (N2 / SH):

| probe | N2 | SH |
|---|---|---|
| bilateral mean (primary) | +0.027 | +0.023 |
| left-right swap | +0.079 [+0.000, +0.179] | +0.082 [+0.021, +0.158] |
| single nose | +0.032 | +0.026 |
| jitter 1 (T0: spatial noise) | −0.001 | +0.001 |
| food replaced by a constant | **+1.458 [+1.314, +1.587]** | **+0.999 [+0.864, +1.150]** |

On T1, the history jitters change nothing measurable: jitter 1 moves no cell by more than 0.010
for either group. **The champions depend heavily on food, but not on the left-right difference or
on its history.** This is what the pilot on a shuffle showed (D038), and it now holds for N2 too.

Champion by champion, across all 72 T0 champions and all three mappings:
- The bilateral mean costs 1 of the 72 meaningfully: a shuffle, T0-R1-SH1 run 0 (+0.43).
- The swap costs 10 of them meaningfully (+0.14 to +0.96): 3 N2 and 7 SH champions.

So some champions do steer by the difference. Reversing it misleads them, but removing it costs
them little. Their stereo steering is real but worth little to their score.

The eight continuation runs' generation-79 champions show the same thing. No generation-79
champion shows meaningful use under the bilateral mean, and none gains use between 39 and 79.
T0-M0 N2 run 0 has the highest N2 point estimate (0.123 at generation 39, 0.091 at 79), but not
meaningfully: its interval reaches below 0.10.

### N2's advantages are at generation 0, and evolution erodes them

The screening interaction I(t) = A(t, M0) − mean(A(t, R1), A(t, R2)), where A is N2 − SH, on
scores normalised per world to the best scripted controller:

| | generation 0 | generation 39 |
|---|---|---|
| I(T0), stereo | **+0.068 [+0.019, +0.117]** | +0.007 [−0.033, +0.043] |
| I(T1), single nose | **+0.069 [+0.026, +0.111]** | +0.030 [−0.015, +0.086] |
| I(T1) − I(T0) | +0.001 [−0.022, +0.023] | +0.024 [−0.034, +0.088] |

On raw scores the pattern is the same: at generation 0, I(T0) = +0.223 [+0.066, +0.385] and
I(T1) = +0.215 [+0.082, +0.343]; at generation 39 both straddle zero. The task contrast is near
zero at both times. So there is **no sign that the advantage is concentrated in the more worm-like
task** (single-nose foraging).

This matches 01b, where N2's edge over the shuffles was, as a point estimate, a head start.

### The generation-0 structure behind it

Corrected input-response probe (D039): random brains, 256 per graph, turn read-out response to a
left-right food difference at a fixed total. Mean over 40 ticks:

| mapping | N2, absolute (raw) | N2, toward the stronger side | 8 shuffles, absolute | shuffles, toward |
|---|---|---|---|---|
| M0 | **0.0146** | **+0.0029** | 0.0014-0.0042 | −0.0002 to +0.0003 |
| R1 | 0.0040 | −0.0000 | 0.0010-0.0044 | −0.0015 to +0.0003 |
| R2 | 0.0050 | +0.0001 | 0.0019-0.0048 | −0.0002 to +0.0003 |
| MS | 0.0010 | +0.0000 | 0.0013-0.0044 | −0.0006 to +0.0004 |

Only under M0 does N2 stand outside the shuffle range, and there it turns in the right direction.
This replicates, with the corrected probe, the one N2 number disclosed before the pre-registration
(§2). The routing exists and points the right way; the evolved champions do not use it.

Food dependence (real minus constant food) shows the same thing on the evolved side. N2
champions under M0 depend on food more than the shuffles do: T0 Delta +0.459 [+0.254, +0.648].
The T0 mapping interaction is +0.328 [+0.036, +0.599]. The difference is already there at
generation 0 (Delta +0.391 [+0.021, +0.735]). So N2 reads food more strongly through its
biological sensory neurons from the start, but not stereo.

### Graph covariates

| | chemical edges kept under the left-right relabelling | food pairs' direct read-out weight (AWA / AWC / ASE) |
|---|---|---|
| N2 | 0.64 | 0 / 1 / 0 |
| SH1-SH8 | 0.13-0.17 | 1.5 to 43 per pair |

Shuffles destroy mirror symmetry, and they hand the food neurons direct edges onto the motor
read-out that N2's food neurons do not have. D036 enforces the no-shortcut rule on N2's remaps,
not on the shuffles. Neither covariate produced stereo use here.

### The other estimates

- **Fitness per cell at generation 39** (normalised, N2 − SH): T0-M0 +0.021 [−0.006, +0.047];
  T0-R1 +0.046 [+0.010, +0.081]; T0-R2 −0.017; T1-M0 +0.019 [−0.011, +0.048]; T1-R1 +0.009;
  T1-R2 −0.032; **T1-MS −0.094 [−0.164, −0.024]**.
- **Strength control** (T1-M0): N2 with its magnitudes permuted within its own mask scores the
  same as N2 (+0.000 [−0.025, +0.026]). Whatever N2 has here comes from its topology, not its
  synapse strengths.
- **Variance components** of the SH mapping contrast: between-graph ≈ 0; within-graph 0.0019 (T0)
  and 0.0033 (T1). Run-to-run noise, not graph-to-graph difference, dominates the contrast.
  Leaving out any one SH graph moves I(T1) between +0.024 and +0.037.
- **Convergence:** 0 of 17 fitted cells complete 90% of their fitted improvement after generation
  40.
- **Scripted context:** the champions (held-out ~2.7-2.8 on T0/T1) sit between the tuned
  memoryless controller (~2.1) and the memory or stereo controller (~3.1-3.2). They beat a
  controller without fine capabilities without using those capabilities, and must do it some
  other way.

---

## Tripwires (pre-registered, §6)

| tripwire | result |
|---|---|
| champions do not use food | not fired: +1.072 [+1.022, +1.123] |
| memory is not worth anything on T1 | not fired: scripted M − K +0.942 [+0.928, +0.956] |
| the anchor disagrees with 01b | not fired: same sign, N2 − SH +0.014 [−0.009, +0.037] (01b: +0.069) |
| drive is off target | not fired: largest validation error 3.8% (SH7) |
| the integrator matters | not fired: largest shift 0.0024, chaos floor 0.0018, both under 0.02 |
| convergence is late | not fired: 0 of 17 cells |
| **shortcuts differ** | **FIRED**: MS advantage minus matched −0.082 [−0.129, −0.020] |
| the remaps disagree | not fired: +0.041 [−0.046, +0.140] |
| SH cares about mapping | not fired: −0.002 [−0.032, +0.024] |
| valence is broken | not fired: exact (0.0) without gap junctions |

**The shortcut tripwire fired against N2.** With food entering FLP, PHB and PVD, N2 does worse than
the shuffles (−0.094), and its champions depend on food only half as much (0.49 against 0.99).
The mapping with strong direct edges onto the command interneurons did not hand N2 a shortcut; it
cost it. The registered consequence stands: routing must stay matched in the full design.

---

## What this decides (§10)

**§4 was challenged ("no meaningful N2 use").** By the registered rule, the capability question
needs longer evolution or a different search before a full design. The screening adds a sharper
reason. Stereo routing exists in N2 at generation 0, in the right direction and only under the
biological mapping, yet selection does not build on it. In this setup the task can be solved well
enough without stereo or history, since the champions beat the memoryless scripted controller
without either. So a full design has to make those capabilities necessary, not merely valuable to
a scripted controller.

For the fitness interactions, the planning ranges are:
- the generation-0 interaction is about +0.07 (normalised) and survives the bootstrap;
- at generation 39 the interaction is within ±0.04 of zero, with between-graph variance near zero;
- detecting an interaction of +0.03 at generation 39 would need about ten times the present
  replication. The interval's half-width is 0.05, and it shrinks roughly with the square root of
  the units.

Failure modes this screening found, none of them visible at the design stage:
1. Scripted gates prove a capability pays, not that evolution will find it (D038).
2. On a stereo task, a history ablation is also a stereo ablation (D041).
3. Degree-preserving shuffles break mirror symmetry and create food-to-motor shortcuts.

---

## Deviations from the pre-registration

- Fable 5.1's review of the pre-registration arrived after the evolution had started and before
  any probe or result. All ten points changed probes, analysis or wording only, and were
  committed before any probe ran (`971bbb3`, D041). The pre-registration's §11 lists them.
- None in the run itself: 190 of 190 runs, no crash, no rerun, no dropped probe step.

## Not registered (chosen after seeing the data)

- The comparison of evolved champions' held-out scores with the scripted controllers' means, in
  "The other estimates", is descriptive context. It was not a planned contrast.
- The phrase "evolution erodes N2's generation-0 advantage" joins two registered estimates
  (generation 0 and 39). The registered acquisition contrast was only for capability use.

## Reviews

This file had not yet been reviewed when written. The team's review of these results goes in
`reviews/`, and any change it causes is listed here.
