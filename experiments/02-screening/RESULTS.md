# WormWars 02: results of the screening

**The primary prediction is challenged: in the primary cell, neither group of evolved champions
meaningfully uses the left-right food difference.** In stereo foraging with food entering the
biological neurons, removing the difference costs N2's champions +0.027 [+0.000, +0.060] and
the shuffles' +0.023 [+0.003, +0.047]. The pre-registered threshold for meaningful use is 0.10.
The contrast is +0.004 [−0.032, +0.044]. Under the registered reading, 40 generations of this
search found stereo use in neither group. So the experiment could not test whether N2's wiring
helps stereo foraging.

Two things are still worth knowing:
- **N2's wiring is structurally different where the prediction expected.** Random N2 brains'
  turn read-out responds 3.5-11 times more strongly to a left-right food difference than random
  shuffles do, under the biological mapping, and on average in the right direction. That
  structure did not turn into stereo use by the champions. The generation-0 champions show no
  stereo advantage either.
- **Under the biological mapping, the gap between N2 and the shuffles closes with evolution.**
  At generation 0 the mapping interaction favours N2 in both tasks. N2's own preference for the
  biological mapping stays the same through generation 39. What changes is the shuffles: their
  best random brains start worse under the biological mapping than under the wrong ones, and
  evolution removes that deficit.

This is a screening experiment: a 12-GPU-hour fraction of a larger design, meant to find failure
modes and size the full experiment ([`DESIGN.md`](DESIGN.md)). It was pre-registered in
[`PREREGISTRATION.md`](PREREGISTRATION.md) before any N2 run, with the disclosures in its §2.
Only the primary outcome (§4) carries a verdict. Everything under **Secondary** was registered as
exploratory. Everything marked **post hoc** was computed after seeing the data, most of it at the
reviewers' request.

Run: `runs/exp02-screening/`. 190 runs, 5.64 GPU-hours of evolution and 7.44 GPU-hours in total
with the probes, of a 12-hour cap; no probe step was dropped; one RTX 5080. The evolution ran
from commit `225e8f8`, and the probes and report from `971bbb3`. The only difference between the
two is Fable's review amendments, which touch probes, analysis and wording (D041).

---

## Primary (pre-registered, §4)

For each generation-39 champion in cell T0-M0 (stereo foraging, food into AWA, AWC and ASE): the
mean over 64 probe worlds of the real score minus the score with the bilateral mean fed to both
sides. N2 averages its 8 runs. SH averages the means of its 8 graphs (16 runs). The interval is a
hierarchical bootstrap, 20 000 resamples.

| | use of the left-right difference [95% bootstrap] | t-interval | class |
|---|---|---|---|
| N2 | +0.027 [+0.000, +0.060] | [−0.012, +0.067] | below threshold |
| SH | +0.023 [+0.003, +0.047] | | below threshold |
| **N2 − SH** | **+0.004 [−0.032, +0.044]** | Welch [−0.038, +0.047] | |

**Verdict: challenged: no meaningful N2 use.** N2's whole interval lies below 0.10. The data are
complete: all registered runs and seeds are present, and no probe entry is malformed.

Registered companions (§4, reported with no verdict):

| | estimate |
|---|---|
| N2 − SH at generation 0 | −0.007 [−0.071, +0.060] |
| acquisition, Delta(g39) − Delta(g0) | +0.011 [−0.069, +0.083] |
| mapping interaction of Delta, generation 39 | +0.001 [−0.055, +0.065] |
| N2's own use under R1 and R2 | +0.016 and +0.024, the same as under M0 (+0.027) |

No SH graph shows detected meaningful use in T0-M0 (0 of 8; graph estimates −0.001 to +0.072).
The mirror-symmetry reading registered for a supported result does not arise.

---

## Secondary (registered as exploratory; intervals, no claims)

### Capability use by the evolved champions

Real minus probed score, generation 39, cell T0-M0:

| probe | N2 | SH |
|---|---|---|
| bilateral mean (primary) | +0.027 [+0.000, +0.060] | +0.023 [+0.003, +0.047] |
| left-right swap | +0.079 [+0.000, +0.179] | +0.082 [+0.021, +0.158] |
| single nose | +0.032 [+0.007, +0.061] | +0.026 [+0.007, +0.050] |
| jitter 1 (T0: spatial noise) | −0.001 [−0.010, +0.008] | +0.001 [−0.004, +0.006] |
| jitter 3 (T0: spatial noise) | +0.050 [+0.006, +0.103] | +0.036 [+0.021, +0.054] |
| food replaced by a constant | +1.458 [+1.314, +1.587] | +0.999 [+0.864, +1.150] |
| collision sensing off | +0.40 | +0.52 |

Jitter 3 costs the scripted stereo controller 0.535, but kinesis only 0.057
(`probe_validation.json`). Champions losing about 0.04-0.05 therefore fits little stereo use.

**Single-nose foraging (T1): jitter.** Jitter 1 moves no cell by more than 0.010. Jitter 3 costs
N2's T1-M0 champions +0.031 [+0.009, +0.051] and the shuffles' +0.027 [+0.016, +0.038]. Jitter
measures history *sensitivity*, not history use (D039). A controller integrating over several
ticks averages jitter 1 out, so **these data neither show nor exclude history use.**

**Champion by champion** (all 72 T0 champions, all mappings):

| class | bilateral mean | swap |
|---|---|---|
| meaningful | 1 | 10 |
| inconclusive | 7 | 12 |
| below threshold | 64 | 50 |

- The one meaningful bilateral-mean user is a shuffle: T0-R1-SH1 run 0, at +0.43 [+0.34, +0.52].
  It was already at +0.35 at generation 0. The seven inconclusive ones are all among the ten
  swap-sensitive champions.
- Swap sensitivity is already present in random brains: 8 of the 72 *generation-0* champions
  (the best of 32 random genomes) show it meaningfully.
- So a few champions depend on the side the food is on, but the probes cannot say whether that
  is a left-right comparison or one-sided sampling. The registered reading covers only
  "meaningful under the mean, not under the swap"; this is the reverse case.

**Continuation runs** (T0-M0 and T1-M0; the bilateral-mean probe exists for the four T0 ones).
No generation-79 champion newly shows meaningful bilateral-mean use. T0-M0 N2 run 0 has the
highest N2 point estimate, 0.123 at generation 39 and 0.091 at 79, and its class is
inconclusive.

### The fitness interaction, generation 0 and 39

The screening interaction I(t) = A(t, M0) − mean(A(t, R1), A(t, R2)), where A is N2 − SH, on
scores normalised per world to the best scripted controller:

| | generation 0 | generation 39 | change, g39 − g0 (post hoc, paired) |
|---|---|---|---|
| I(T0), stereo | **+0.068 [+0.019, +0.117]** | +0.007 [−0.033, +0.043] | **−0.061 [−0.108, −0.014]** |
| I(T1), single nose | **+0.069 [+0.026, +0.111]** | +0.030 [−0.015, +0.086] | −0.039 [−0.096, +0.021] |
| I(T1) − I(T0) | +0.001 [−0.022, +0.023] | +0.024 [−0.034, +0.088] | |

On raw scores the pattern is the same (generation 0: I(T0) +0.223 [+0.066, +0.385], I(T1)
+0.215 [+0.082, +0.343]; generation 39: both straddle zero).

**What changes is the shuffles, not N2** (post hoc). N2's own preference for M0 over the remaps,
normalised, is +0.026 at generation 0 and +0.026 at 39 on T0, and +0.028 at both on T1. The
shuffles' best random brains start *worse* under M0 than under the remaps (−0.042 on T0, −0.041
on T1). By generation 39 that deficit is gone (+0.019 and −0.002). One plausible reason, not
tested: in the shuffles, AWA, AWC and ASE carry direct edges onto the motor read-out (below). That
could make random brains' responses to food input erratic, and evolution would tune the deficit
away.

The generation-0 values are best-of-32 champions, not average random brains. The task contrast is
near zero at both times, so there is **no sign of an advantage concentrated in the more worm-like
task** (single-nose foraging). As a point estimate this resembles 01b's exploratory split, where
N2's edge over the shuffles was a higher starting point and did not separate statistically.

At generation 39, one cell shows an N2 advantage: T0-R1, +0.046 [+0.010, +0.081] (raw +0.147
[+0.027, +0.265]). It is one of seven cell advantages, with no multiplicity adjustment.

### Generation-0 structure

**Input response.** Corrected probe (D039): random brains, 256 per graph, outside the world. The
turn read-out's response to a left-right food difference at a fixed total, mean over 40 ticks. No
across-brain uncertainty was saved.

| mapping | N2, absolute | 8 shuffles, absolute | N2, signed (+ = toward the stronger side) | shuffles, signed |
|---|---|---|---|---|
| M0 | **0.0146** | 0.0014-0.0042 | **+0.0029** | −0.0002 to +0.0003 |
| R1 | 0.0040 | 0.0010-0.0044 | −0.0000 | −0.0015 to +0.0003 |
| R2 | 0.0050 | 0.0019-0.0048 | +0.0001 | −0.0002 to +0.0003 |
| MS | 0.0010 | 0.0013-0.0044 | +0.0000 | −0.0006 to +0.0004 |

Under M0, N2's absolute response is 3.5-11 times the shuffles'. Under R2 it is marginally above
their range, and under MS below it. Only under M0 is N2's mean signed response clearly toward the
stronger side. The common-mode turn response under M0 is also higher for N2 (motor 0.029 against
0.004-0.013). This is consistent with the one N2 measurement disclosed before the
pre-registration (§2), made with a different probe on a different scale. It describes random
brains, not the evolved champions.

**Valence symmetry:** exact without gap junctions (0.0); with gaps, a mean discrepancy of 0.063
(N2) and 0.052 (SH1).

**Magnitudes at generation 0:** N2 with permuted magnitudes scores at least as well as with its
anatomical magnitudes under every mapping (M0: 0.982 against 0.950); uniform magnitudes score
lower (0.879).

### Food dependence

Real minus constant-food score, generation 39: N2 − SH is +0.459 [+0.254, +0.648] on T0-M0 and
+0.324 [+0.139, +0.516] on T0-R1. The T0 mapping interaction is +0.328 [+0.036, +0.599], the T1
interaction +0.061 [−0.229, +0.357]. At generation 0, T0-M0 Delta is +0.391 [+0.021, +0.735],
with an interaction of +0.370 [−0.030, +0.758].

**This measures an intervention, not how strongly food is read.** On the T0-M0 probe worlds, N2
and SH score 2.835 and 2.742 with real food, but 1.377 and 1.742 with the constant. Most of N2's
larger loss is worse performance when food is replaced. The constant is each world's initial mean
food level, so the replacement also changes the input distribution.

### Graph covariates

| | chemical edges kept under the left-right relabelling | food pairs' direct read-out weight (AWA / AWC / ASE) |
|---|---|---|
| N2 | 0.64 | 0 / 1 / 0 |
| SH1-SH8 | 0.13-0.16 | 1.5 to 43 per pair |

Shuffles destroy mirror symmetry. They also give the food neurons direct edges onto the motor
read-out, which N2's food neurons do not have. D036 applied the no-shortcut rule to N2's remaps
only, not to the shuffles.

### Other registered estimates

- **Fitness per cell at generation 39** (normalised, N2 − SH):
  - T0: M0 +0.021 [−0.006, +0.047]; R1 +0.046 [+0.010, +0.081]; R2 −0.017 [−0.064, +0.028].
  - T1: M0 +0.019 [−0.011, +0.048]; R1 +0.009 [−0.030, +0.044]; R2 −0.032 [−0.118, +0.029];
    **MS −0.094 [−0.164, −0.024]**.
- **Strength control** (T1-M0): permuted-magnitude N2 minus N2 +0.000 [−0.025, +0.026]; minus SH
  +0.019 [−0.006, +0.043]. No effect of this permutation was detected under this procedure. No
  equivalence margin was registered, so this does not show that magnitudes do not matter.
  Mutation over 40 generations (sigma 0.08 per generation against an initial scale of 0.2) also
  erodes the initial magnitudes, so this late test is weak.
- **Variance components** of the SH mapping contrast: between-graph 0 (the estimate is truncated
  at zero, so graph-to-graph variance is not shown to be negligible); within-graph 0.0019 (T0),
  0.0033 (T1). Leaving out any one SH graph moves I(T1) between +0.024 and +0.037.
- **Convergence:** 0 of 17 fitted cells complete 90% of their fitted improvement after generation
  40.
- **Behaviour** (T0-M0, generation 39, N2 / SH):
  - speed 0.27 / 0.27, and |turn| 0.40 / 0.32;
  - the turn keeps its sign on 99.6% of ticks, so champions circle;
  - time on food 0.42 / 0.39.
- **Intake composition:** pellets are 0.15% of what champions eat.
- **Generation-0 drive per run** (32 genomes, reported, never tripwired): mean error per graph
  0.08-0.28, against about 0.12 expected from sampling. The independent 2048-genome validation is
  within 3.8% for every graph.
- **Scripted context** (post hoc, descriptive): champions' raw held-out means are 2.69-2.84 in
  T0/T1 cells (MS 2.35-2.65), from the records. The tuned memoryless controller scores ~2.1 and
  the memory or stereo controller ~3.1-3.2, both on the gate worlds.

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
| **shortcuts differ** (T1) | **FIRED**: MS advantage minus matched −0.082 [−0.129, −0.020] |
| the remaps disagree (computed on T1) | not fired: +0.041 [−0.046, +0.140] |
| SH cares about mapping (T1) | not fired: −0.002 [−0.032, +0.024] |
| valence is broken | not fired: exact (0.0) without gap junctions |

**The shortcut tripwire fired against N2.** With food entering FLP, PHB and PVD, N2 does worse than
the shuffles (−0.094). MS changes neuron identity and routing together, so this shows a mapping
effect, not that direct edges caused it. The registered consequence stands: routing must stay
matched in the full design.

**The remaps would have disagreed on T0** (post hoc). The report computed the R1 − R2 tripwire on
T1 only, and §6 did not name a task. On T0 at generation 39, the R1 − R2 advantage difference is
+0.063 [+0.011, +0.116]; at generation 0 it is −0.007 [−0.087, +0.068]. R1 (ASJ, ASI, ASG) and R2
(PLN, IL2D, IL2V) differ in sensory modality (D036). Two remaps are too few for the full design.

---

## What this decides (§10)

**§4 was challenged ("no meaningful N2 use").** By the registered rule, the capability question
needs longer evolution or a different search before a full design. What the screening adds, all
of it exploratory:

1. **What is N2-specific here shows up at generation 0.** A generation-0 study, with thousands of
   random genomes, many shuffles and gap-free variants, costs minutes. It could settle the
   structural questions before any evolution is bought.
   - One suggestion from review, untested: the directional turn response may run through gap
     junctions, which have no random sign and are 62% mirrored in N2. Run the input-response
     probe with gaps off.
2. **The search found champions that forage well without using stereo, and their strategy is
   unknown.** They circle, beat the memoryless scripted controller, and lose more from losing
   collision sensing than from losing the left-right difference. Before redesigning the task:
   - test richer memoryless baselines with the same inputs;
   - replay matched current input after different histories;
   - measure evolved champions' steering responses directly.
   Kinesis carries most of the scripted gain (straight 0.67, K 2.12, S 3.23). A task that forces
   stereo would need K close to straight.
3. **The control graphs need constraints:**
   - the no-shortcut rule applied to shuffles too (direct read-out weight 1.5-43, against N2's
     0-1);
   - a mirror-symmetric shuffle variant (mirror share 0.13-0.16, against 0.64);
   - more than two remaps, since R1 and R2 disagree on T0.
4. **A strength control has to come early,** at generation 0 or with smaller mutation, because
   mutation erodes the initial magnitudes.
5. **Sizing.** At generation 39 the interaction intervals are about ±0.05 wide (T1 reaches
   +0.086). Excluding zero for an interaction of +0.03 would need roughly 3 times the units, and
   80% power roughly 6 times. That rough sum assumes the present allocation and ignores
   graph-to-graph variance, whose estimate here is truncated at zero. It does not justify trading
   graphs for repeated runs.

Failure modes the screening process found before any N2 result (D034-D041): scripted gates show
that a capability pays, not that evolution finds it; a history jitter on a stereo task is also a
stereo ablation; and shuffles break mirror symmetry and create food-to-motor shortcuts. The result
adds one more: champions can beat the scripted memoryless baseline without the capabilities the
task was built to reward.

---

## Deviations from the pre-registration

- Fable 5.1's review of the pre-registration arrived after the evolution had started and before
  any probe or result. All ten points changed probes, analysis or wording only. They were
  committed before any probe ran (`971bbb3`, D041), and the pre-registration's §11 lists them.
- The run itself: 190 of 190 runs, no crash, no rerun, no dropped probe step.

## Reviews of these results

The first version of this file (`6dc7d71`) was reviewed by Astra 6 and Fable 5.1
(`reviews/20260925-135918-results/`). Both confirmed every traceable number. Both found the
readings stated too strongly and several registered outcomes missing. This version makes these
changes (D042):

- **"Evolution erodes N2's advantage" → the shuffles catch up.** The change is now tested with a
  paired bootstrap, and N2's own mapping preference is shown to be constant (Astra).
- **"Nobody used stereo" → scoped to the primary cell,** with the one shuffle champion that does
  (both).
- **"Stereo steering is real but worth little" → removed.** Swap sensitivity is already present at
  generation 0, and inconclusive is not "little" (both).
- **"Not on its history" → removed.** The jitters neither show nor exclude history use (both).
- **"N2 reads food more strongly" → reported as an intervention effect,** with the ablated scores
  (both).
- **"Topology, not strengths" → "no effect detected under this procedure"** (both).
- **Additions:**
  - the registered §4 companions, jitter 3, the common-mode response, the magnitude probe, the
    gap-on valence check, behaviour and intake;
  - the T0 remap disagreement, the T0-R1 cell advantage, and the per-generation drive errors.
- **Corrected:** the input-response wording ("3.5-11 times" is the absolute response; R2 is
  marginally above the shuffle range), the sizing arithmetic, and the rounding of the symmetry
  range.
