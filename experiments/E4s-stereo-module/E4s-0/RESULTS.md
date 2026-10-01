# E4s-0 results: diagnostics before the comparator graft (exploratory)

Run 2026-10-01, on the plan `docs/E4s/E4s-0-PLAN.md` v2 (with its D146 corrections), at the commits
named in each record's provenance.
- **Exploratory:** these results inform E4s-1's design. They are not confirmatory.
- **Reviewed** by Astra 6 and Fable 5.1: both said "fix", text only
  (`docs/reviews/20261001-E4s-0-results/`). The text below is corrected; the Corrections section at
  the end quotes what was wrong (D147).
- **Compute:** 0.23 GPU-hours of the 2-hour cap (`compute-record.json`). The projection was 0.30 h at
  full sizes, so no size was shrunk.
- **The accounting holds 11 attempts.**
  - The first five stage commands were refused within 15 seconds at 706a3fa. The projection's record
    had not yet been committed and pushed, which the stage frame requires before the next stage.
  - Each stage then ran once and completed.

**Where the numbers come from:**
- the stage records in this folder (`sweep.json`, `attenuation.json`, `ladder.json`,
  `populations.json`, `robustness.json`, `module.json`);
- `summary.json`, which `scripts/e4s0_summary.py` derives from those records (rule 5);
- three references from elsewhere:
  - the champions' open-loop gain of 0.098, from `../development-records/gain-probe.json`;
  - 04a run 2's 2.64 on E2d's hold-out, from `experiments/E2d-taskn-diagnosis/part-b.json`;
  - E1's best tuned S-const at k = 256, 8.51 with turn bias 0.2 on E1's 256 tuning worlds, from
    `experiments/E1-navigation/freeze.json`.

## In short

1. **For 42 of the 47 champions, a valley along the stereo-gain direction.** Adding k(L − R) to a
   champion's own turn command:
   - small k changes little: at most +0.27 targets per episode at k ≤ 1;
   - k between 2 and 16 harms most champions;
   - k = 32, 64 and 256 help all 47.

   **Five champions are never harmed,** and three of them rise almost monotonically. This is one
   externally inserted change of policy, not what mutations produce.
2. **The champions' differential response falls from the sensory neurons to RIA, then levels off.**
   The common-mode response stays four to seven times larger at every stage (descriptive).
3. **The smallest comparator, L1 (4 neurons), qualified, with the carrier's help.** On the carrier its
   mean is 5.18 targets per episode; the 95% lower bound, 5.10, clears the 5.0 line narrowly. It meets
   E2d's "uses" criterion.
   - **That needed the carrier's constant turn command of 0.2.** The same module scored 3.86 on the
     tuning worlds with a turn command of 0, and 5.27 with 0.2.
   - **It sits at a corner of the grid,** with its weights and τ on the genome's bounds. Its gain,
     about 36, is the most two synapses of weight 3 can give.
4. **Grafted onto random N2, it is used at generation 0.** All 16 simulated populations'
   generation-0 bests meet "uses", so by the pre-stated rule **E4s-1 proceeds on random N2.** Most
   individual random backgrounds score 0.
5. **On 04a run 2, the graft fails "uses" and costs the score.** With the module's noses fed their
   real input, the champion scores 1.76 targets per episode less than with them fed the mean.
6. **Mutational robustness is bimodal.** At 0.25× 02's mutation scales, the median mutant keeps 78% of
   its parent's score, but 122 of 256 mutants score below 0.7. At 1×, 195 of 256 score 0. The module's
   factor stays 0.25× (the fallback did not trigger).

## 1. The residual stereo-gain sweep (`sweep.json`, `summary.json`)

**Set-up:**
- the 47 distinct champions;
- 512 worlds, paired across k;
- one fixed composition (8 strains × 512 worlds per chunk);
- with k = 0, the wrapped world reproduced the unwrapped counts exactly.

**The classes, by the plan's pre-stated rules.** Adjacency applies in both directions, and k = 256
is only ever a neighbour.

| Class | Champions |
|---|---|
| rises early (first improving k ≤ 1, no harm before it) | 24 |
| rises late | 0 |
| dips first (harmed at some k below the first improving k) | 23 |
| harmed | 0 |
| no detected benefit on the tested grid | 0 |

**The 24 that rise early:**
- **Their first improvements are small.** At the first improving k, 23 gain +0.018 to +0.080
  targets per episode, and one +0.191.
- **The largest gain at k ≤ 1 is +0.27** (e2 es run00), then +0.21 (e2 extension run04).
- **19 of the 24 are harmed at a larger k.**

**The 23 that dip first:** the first improving k is 32 for 21 of them, and 16 for 2.

**Harm:**
- **42 of 47 are harmed at some k** by the adjacency rule: at k = 4 (41 champions), 8 (39), 2
  (35), 1 (16) and 0.5 (7).
- **The rule cannot mark k = 16 as harmed** for a champion that improves at 32, since its neighbour
  helps. Pointwise at k = 16, 40 of 47 have an upper bound below 0, and 7 a lower bound above 0
  (descriptive).
- **Five are never harmed:** 04a run12, e2 es run00, e2 extension run00, e2 extension run04 and e2 ga
  run02.
  - e2 es run00, e2 extension run04 and e2 ga run02 rise almost monotonically (e2 es run00: +0.27,
    +0.42, +0.77, +1.36, +2.62 and +4.52 at k = 1 to 32).
  - e2 extension run00 is pointwise harmed at k = 16 (−0.57), which the adjacency rule does not
    count.

**Improvement:** all 47 improve at k = 32, 64 and 256 (each lower bound above 0).

**The median across champions, taken separately at each k** (not one champion's trajectory). The
champions' own means at k = 0 range from 0.79 to 2.96.

| k | 0 | 0.25 | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 256 |
|---|---|---|---|---|---|---|---|---|---|---|
| median score | 2.19 | 2.22 | 2.16 | 1.57 | 0.83 | 0.69 | 0.77 | 5.75 | 7.03 | 8.38 |

At k = 256 the champions score 7.59-8.48.

**What this does and does not show:**
- **For 42 of 47 champions, along this one intervention,** the path from their weak stereo response
  (open-loop gain about 0.1) to a strong one crosses a valley. Small added gains change little,
  intermediate ones cost up to more than a target per episode, and large ones pay.
- **It does not show** what weight mutations produce, that this valley causes the plateau, or why
  intermediate gains hurt.
- **The five exceptions** sit on the plateau with no valley on this path. So the plateau is not
  explained by this valley for every champion.

## 2. Where the response is attenuated (`attenuation.json`, `summary.json`; descriptive)

**Set-up:**
- open loop, zero start, other inputs zero;
- for each champion and group, the mean of the group's absolute gains, then the median across
  champions;
- the ratio K_D / K_C, per champion, then its median.

| Level m | Sensory (ASE, AWA, AWC) | AIY, AIZ, AIA, AIB | RIA | Turn motor neurons | Turn command |
|---|---|---|---|---|---|
| 0.02: \|K_D\|, \|K_C\|, ratio | 0.26, 0.80, 0.28 | 0.17, 0.82, 0.25 | 0.11, 0.76, 0.17 | 0.10, 0.59, 0.19 | 0.09, 0.66, 0.19 |
| 0.08 | 0.27, 0.82, 0.28 | 0.18, 0.93, 0.23 | 0.14, 1.01, 0.15 | 0.12, 0.72, 0.17 | 0.12, 0.81, 0.16 |
| 0.25 | 0.25, 0.77, 0.29 | 0.16, 0.81, 0.25 | 0.12, 0.74, 0.19 | 0.12, 0.50, 0.21 | 0.10, 0.63, 0.16 |

- **The differential gain falls** from the sensory neurons (0.25-0.27) to RIA (0.11-0.14), and
  stays about level from RIA to the turn neurons and the turn command.
- **The ratio of differential to common-mode gain falls** from about 0.28 at the sensory neurons to
  0.15-0.21 downstream.
  - Part of the sensory ratio is built in: the probe gives each sensor ½ per unit of d and 1 per unit
    of m, so a passive sensor would show 0.5.
  - The ratio's fall downstream is not built in.
- **The turn command's differential gain** (0.09-0.12) matches the gain probe's 0.098.
- **What this does not establish:** serial attenuation through a recurrent circuit, or lost
  information. Individual champions need not follow the medians.

## 3. The comparator ladder (`ladder.json`, `module.json`, `summary.json`)

**L1 qualified at the first attempt,** so the ladder stopped; L2-L4 were never tried.

**The chosen candidate:**
- tuned on 216 candidates × 128 worlds;
- re-scored as the best of 5 on 512 worlds (5.19, against 4.51-4.80 for the others);
- **parameters:** w_n = 3, w_o = 3, τ = 0.5, bias 0;
- **carrier:** forward command 1.0, turn command 0.2.

**Qualification on 1 024 fresh worlds:**
- mean 5.18, 95% lower bound 5.10 (≥ 5.0);
- "uses" under the module probes.

**What the qualification depends on:**
- **The carrier's turn command.** The same module (same w_n, w_o, τ, bias and forward) scored 3.86,
  4.74 and 5.27 on the tuning worlds at turn commands 0, 0.1 and 0.2. The candidate with no turn bias
  was not among the top five, so it was never re-scored or qualified.
  - The 5.0 line was cleared only with a constant turn bias that is not part of the graft.
  - On random N2 there is no such bias: the background's own turn offset takes its place.
  - The plan allowed the turn command in the grid, so this is within the plan; it was not stated.
- **The grid's corner:** w_n, w_o, the forward command and the turn command are at their grid
  maxima, and τ at its minimum. Only the bias is interior.
- **The genome's bounds:** w_n, w_o and τ are on the hard bounds (|w| = 3, τ = 0.5).
  - The gain of about 36 is the most this circuit can reach within |w| ≤ 3. Mutating those weights
    can only lower it.
  - Mutation proposals that push past a bound are clipped. That happens with probability about ½ per
    bounded parameter, so the effective mutation distribution there differs from the interior. How
    much this changes the robustness below is not measured.
- **The ceiling:** by E1's scripted steerer, a gain of about 32 scores 5.63 with turn bias 0.2. E4s-1
  should assume a module ceiling near 5, not the 8.4-8.5 of k = 256.

**Its open-loop dynamics on the carrier** (turn command 0):
- a step of d = +0.01 changes the turn command by +0.34 to +0.36, an effective gain of about 34-36;
  the arithmetic 4·w_o·w_n = 36 predicted about that;
- the reversal from +0.01 to −0.01 changes it by −0.67 to −0.71, twice the step;
- every response settled, and reached 90% by the fourth update after the change (`t90 = 3` is a
  zero-based index);
- no flag was raised.

**The module file** is `module.json` (sha256 `9613cd15…77d4`).

## 3b. The generation-0 populations (`populations.json`, `summary.json`)

**The simulated populations:** 16 populations of 32 random N2 genomes, each with L1 grafted. Each
population's generation-0 best was picked on 8 selection worlds, as `evolve_batch` picks it.
- **All 16 generation-0 bests meet "uses"** on 1 024 worlds: 16 "uses", 0 "unclear", 0 "no material
  benefit".
- **The pre-stated reading:** at least 12 of 16, so E4s-1 proceeds on random N2.
- **Their scores:** a median of 2.06 targets per episode (1.09-3.30). That is about the champions'
  plateau level (2.19), and well below the carrier's 5.18.
- **A design trigger, not a prediction:** 16 pilot populations are neither necessary nor sufficient
  for a "retained" majority in E4s-1.

**The individual backgrounds** (all 512 genomes, 64 worlds each; descriptive):
- **Classes:** 41 "uses", 107 "unclear", 364 "no material benefit".
- **Most score 0:**
  - 398 of 512 score 0 with real input;
  - 294 score 0 under all three probes;
  - the median score is 0.
- **53% drive backwards** (mean forward command below 0); the median forward command is −0.06.
- **The median absolute turn command is 0.25,** and the median share of saturated turn neurons 0.10.
- **The population's median fitness on the selection worlds is 0.** Generation-0 selection picks one
  of the few backgrounds that score at all, and each population has about 41/512 × 32 ≈ 2.6 users on
  average, so founder effects will be strong.

**04a run 2 with L1 grafted** (1 024 worlds, paired probes of the module's noses):

| Module input | Mean score |
|---|---|
| real | 0.89 |
| mean of both sides | 2.64 |
| swapped | 0.02 |

- **Real minus mean is −1.76** (95% interval −1.82 to −1.70). **Real minus swapped is +0.87** (+0.83 to
  +0.90).
- **So the class is "unclear":** the module's real differential input reduces the score sharply
  against mean-only input, and swapped input is worse still. This is a harmful host-graft
  interaction.
- **The forward command is 0.98 and the turn command −0.28.** No ungrafted run on these worlds was
  made, so the turn bias is not attributed to the graft.
- **The external residual on the same champion behaves differently:** k = 32 adds +3.46 (sweep). A
  grafted gain of about 35 is therefore not equivalent to the residual on an evolved background.

## 4. Mutational robustness (`robustness.json`, `summary.json`)

**Set-up:** the qualified module on its carrier; 256 mutants per scale, module parameters only; the
scales are paired (the same draws); 64 worlds. The parent scores 5.23 on these worlds.

| Scale (× 02's) | Median share of the parent's score | Children at 0 | Below 0.7 | Keep at least half | Above the parent |
|---|---|---|---|---|---|
| 0.125 | 0.92 | 36 | 60 | 192 | 52 |
| 0.25 | 0.78 | 78 | 122 | 134 | 34 |
| 1 | 0.00 | 195 | 215 | 39 | 7 |

- **The distribution is bimodal.** At 0.25×, children either keep most of the score (the survivors
  score 3.83-5.44) or lose nearly all of it. The median falls on the survivors' side by a narrow
  margin: 134 keep at least half against 122 below 0.7.
- **The fallback did not trigger,** since the median at 0.25× keeps at least half: E4s-1's module
  factor stays 0.25×.
- **What is not established:**
  - whether a destroyed child lost its amplification, or gained a turn offset (Fable's hypothesis,
    which fits the carrier's sensitivity to its turn command);
  - whether mutants still "use" the difference (no differential gain or "uses" was measured on them);
  - survival under selection while the host evolves too (that is E4s-1).
- **The parent and the children ran in different compositions** (one padded strain against chunks of
  64), so the share is descriptive.

## What E4s-1 takes from this

- **The frozen module:** `module.json`, L1, re-qualified on fresh worlds before any evolution.
- **The background:** random N2 (16 of 16 by the pre-stated rule).
- **The module's mutation factor:** 0.25×.

**What its design must take into account:**
- **The turn offset is a first-order variable.**
  - The module qualified with a carrier turn command of 0.2.
  - Random backgrounds have a median absolute turn command of 0.25, of either sign.
  - 04a run 2 sits at −0.28, and there the graft fails.
  - So record each background's turn offset at generation 0, and track a run's turn offset and its
    differential gain separately.
- **A ceiling near 5, not 8.5:** the module's gain is capped by the bounds.
- **Generation-0 bests start at the plateau's level (about 2).** Score alone cannot separate
  "retained" from "replaced", so D must be read along training, not only at the end.
- **Mutational load:** about half of the 0.25× module mutations are lethal on the carrier.
  - Report the destroyed fraction.
  - Consider a 0.125× sensitivity arm.
  - Frozen-against-free will partly measure this load.
- **R's control varies only signs:** all 20 of L1's edges have magnitude 3, so permuting magnitudes
  does nothing.
- **C2 (04a run 2) starts in a harmful interaction.** Report signed probe effects beside its class,
  and include the ungrafted champion on the same worlds.
- **The gates stay gates:** the CUDA state tolerance and the score-level inert-graft check are still
  pending.

## Not shown

- What mutations produce, or why the plateau exists: the sweep is one external intervention.
- Anything about the worm's own chemotaxis. Stereo sensing here is a game-design choice, and the
  computation lives in a 4-neuron graft outside the N2 mask.
- Whether L1 keeps its function under evolution: that is E4s-1.

## Corrections (2026-10-01, results review; D147)

The first version (commit 7eac620) said, now corrected above:

1. "the 24 champions gain +0.018 to +0.080 targets per episode, and one gains +0.191". Twenty-three do,
   and one gains +0.191. And the README's "small k adds at most +0.08 (one champion +0.19)" is wrong:
   at k ≤ 1 the largest gain is +0.27 (both reviewers).
2. "Along this one intervention, the path … crosses a valley", unqualified. Five champions are never
   harmed, and three rise almost monotonically (Fable).
3. "The harm is mostly at k = 4 (41 champions), 8 (39) and 2 (35)". By construction the rule cannot
   mark k = 16. The pointwise count at k = 16 is now given (Fable).
4. "The median champion's score". It is the median across champions at each k. The README's
   "k = 2-16 … 0.69-0.83" omitted 1.57 at k = 2, and "k ≥ 32 helps all" now reads "the tested
   k = 32, 64 and 256" (Astra).
5. "The champions' response to the difference shrinks at every stage". The table pooled
   champion-neuron observations, and RIA to the turn neurons is level. It is now one value per
   champion, and "falls … then levels off". The sensory |K_C| at m = 0.02 was 0.81 when pooled, not
   0.82 (Astra, Fable).
6. "Their turn command answers several times more to the common level". Part of the ratio is built
   into the probe (Fable).
7. L1's qualification was reported without its dependence on the carrier's turn command of 0.2, and
   without its position at the grid's corner (Fable).
8. "Mutation is clamped there, so half of each perturbation of those parameters is removed. That makes
   the robustness below look better than it would at an interior point." Mutation does not halve each
   perturbation; proposals past a bound are clipped. The comparison with an interior point was not
   measured (Astra, Fable).
9. "A mutation at 02's full scale destroys the module in the median child", and the README's "It
   survives mutation at 0.25×, but not at 1×". These turned one-generation carrier scores into
   claims about function and survival. The distributions are now reported (both).
10. "the valley, which predicts that free mutation at 02's scale will not keep a strong gain (U)". The
    sweep does not measure mutations, and this contradicted the plan's stated reach (both).
11. "the graft does not work on this background at generation 0", for 04a run 2. The paired probes
    show a harmful interaction, now reported (both).
12. "On 64 worlds most are expected to be unclear or no-benefit". This attributed both classes to the
    sample size; the observed inactivity is now reported (Astra).
13. "reached 90% within 3 ticks". `t90` is a zero-based index: by the fourth update (Astra).
14. "every number below comes from a committed record in this folder". Three references come from
    elsewhere, and several summaries had no generator; `summary.json` now holds them (both).
15. "E1's scripted stereo steerer scores 8.51 at k = 256" omitted the turn bias of 0.2 and E1's tuning
    worlds (both).
