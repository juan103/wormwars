# E4s-0 results: diagnostics before the comparator graft (exploratory)

Run 2026-10-01, on the plan `docs/E4s/E4s-0-PLAN.md` v2 (with its D146 corrections), at the commits
named in each record's provenance.
- **Exploratory:** these results inform E4s-1's design. They are not confirmatory.
- **Compute:** 0.23 GPU-hours of the 2-hour cap (`compute-record.json`). The projection was 0.30 h at
  full sizes, so no size was shrunk.
- **Records:** every number below comes from a committed record in this folder: `sweep.json`,
  `attenuation.json`, `ladder.json`, `populations.json`, `robustness.json`, and `module.json`.

## In short

1. **A valley along the stereo-gain direction.** Adding k(L − R) to the 47 champions' own turn
   commands:
   - small k barely helps;
   - k between 2 and 16 hurts most champions, a lot;
   - k of 32 or more helps every champion, a lot.

   This is one externally inserted change of policy, not what mutations produce.
2. **The champions' response to the difference shrinks at every stage,** from the sensory neurons to
   the turn neurons. Their turn command answers several times more to the common level than to the
   difference (descriptive).
3. **The smallest comparator, L1 (4 neurons), qualified.** On the carrier, its mean is 5.18 targets
   per episode; the 95% lower bound, 5.10, clears the 5.0 line narrowly. It meets E2d's "uses the
   left-right difference" criterion. Its weights and τ sit on the genome's bounds.
4. **Grafted onto random N2, it is used at generation 0.** All 16 simulated populations' generation-0
   bests meet "uses", so by the pre-stated rule **E4s-1 proceeds on random N2.** Most individual random
   backgrounds score 0.
5. **Robustness:** at 0.25× 02's mutation scales, the median mutant keeps 78% of its parent's score.
   At 1× it keeps 0%. The module's factor stays 0.25× (the fallback did not trigger).

## 1. The residual stereo-gain sweep (`sweep.json`)

**Set-up:** 47 distinct champions; 512 worlds, paired across k; one fixed composition (8 strains ×
512 worlds per chunk). With k = 0, the wrapped world reproduced the unwrapped counts exactly.

**The classes, by the plan's pre-stated rules** (adjacency in both directions; k = 256 only ever a
neighbour):

| Class | Champions |
|---|---|
| rises early (first improving k ≤ 1, no harm before it) | 24 |
| rises late | 0 |
| dips first (harmed at some k below the first improving k) | 23 |
| harmed | 0 |
| no detected benefit on the tested grid | 0 |

- **The early rises are tiny.** At the first improving k, the 24 champions gain +0.018 to +0.080
  targets per episode, and one gains +0.191.
- **19 of those 24 are then harmed at a larger k** (the "harmed at a larger k" flag).
- **Of the 23 "dips first",** the first improving k is 32 for 21 and 16 for 2.
- **In all, 42 of the 47 champions are harmed at some k.** The harm is mostly at k = 4 (41
  champions), 8 (39) and 2 (35).
- **Every champion improves at k = 32 and 64.** Both lower bounds are above 0 for all 47.

**The median champion's score** (its own mean at k = 0: 2.19; range 0.79-2.96):

| k | 0 | 1 | 4 | 8 | 16 | 32 | 256 |
|---|---|---|---|---|---|---|---|
| median score | 2.19 | 2.16 | 0.83 | 0.69 | 0.77 | 5.75 | 8.38 |

At k = 256 the champions score 7.59-8.48. For reference, E1's scripted stereo steerer scores 8.51 at
k = 256.

**What this does and does not show:**
- **Along this one intervention,** the path from the champions' own weak stereo response (open-loop
  gain about 0.1) to a strong one crosses a valley: small gains add little, intermediate gains cost
  more than a target per episode, and only large gains pay.
- **It is consistent with the plateau being hard to leave by small steps.** It does not show what
  weight mutations produce, nor that this valley is the cause of the plateau (the plan's stated
  reach).
- **Why intermediate gains hurt is not measured here.**

## 2. Where the response is attenuated (`attenuation.json`; descriptive)

**Set-up:** open loop, zero start, other inputs zero; medians over the 47 champions of the absolute
gains, by group of neurons.

| Level m | Sensory (ASE, AWA, AWC) | AIY, AIZ, AIA, AIB | RIA | Turn motor neurons | Turn command |
|---|---|---|---|---|---|
| 0.02: \|K_D\|, \|K_C\| | 0.22, 0.82 | 0.12, 0.64 | 0.08, 0.59 | 0.06, 0.40 | 0.09, 0.66 |
| 0.08 | 0.24, 0.81 | 0.13, 0.70 | 0.07, 0.51 | 0.07, 0.49 | 0.12, 0.81 |
| 0.25 | 0.22, 0.75 | 0.12, 0.50 | 0.07, 0.44 | 0.07, 0.36 | 0.10, 0.63 |

- **The differential gain halves from the sensory neurons to the first interneurons, and roughly
  halves again by the turn neurons.** The common-mode gain stays several times larger at every stage.
- **The turn command's differential gain** (0.09-0.12) matches the gain probe's 0.098.
- **A weak gain shows an attenuated response, not necessarily lost information** (the plan's stated
  reach).

## 3. The comparator ladder (`ladder.json`, `module.json`)

**L1 qualified at the first attempt,** so the ladder stopped.

**The chosen candidate:**
- tuned on 216 candidates × 128 worlds;
- re-scored as the best of 5 on 512 worlds (5.19, against 4.51-4.80 for the others);
- **parameters:** w_n = 3, w_o = 3, τ = 0.5, bias 0;
- **carrier:** forward command 1.0, turn command 0.2.

**Qualification on 1 024 fresh worlds:**
- mean 5.18, 95% lower bound 5.10 (≥ 5.0);
- "uses" under the module probes.

The margin over 5.0 is small.

**On the genome's bounds:** w_n, w_o and τ all sit on hard bounds (|w| = 3, τ = 0.5).
- Mutation is clamped there, so half of each perturbation of those parameters is removed. That makes
  the robustness below look better than it would at an interior point.
- E4s-1's design must take this into account.

**Its open-loop dynamics on the carrier** (turn command 0):
- a step of d = +0.01 changes the turn command by +0.34 to +0.36, an effective gain of about 34-36;
  the arithmetic 4·w_o·w_n = 36 predicted about that;
- the reversal from +0.01 to −0.01 changes it by −0.67 to −0.71, twice the step;
- every response settled, and reached 90% within 3 ticks;
- no flag was raised.

**The module file** is `module.json` (sha256 `9613cd15…77d4`).

## 3b. The generation-0 populations (`populations.json`)

**The simulated populations:** 16 populations of 32 random N2 genomes, each with L1 grafted. Each
population's generation-0 best was picked on 8 selection worlds, as `evolve_batch` picks it.
- **All 16 generation-0 bests meet "uses"** on 1 024 worlds: 16 "uses", 0 "unclear", 0 "no material
  benefit".
- **The pre-stated reading:** at least 12 of 16, so E4s-1 proceeds on random N2.
- **Their scores:** a median of 2.06 targets per episode (1.09-3.30), well below the carrier's 5.18.
  The random background costs most of the module's performance, but the stereo use is there.
- **A design trigger, not a prediction:** 16 pilot populations are neither necessary nor sufficient
  for a "retained" majority in E4s-1.

**The individual backgrounds** (all 512 genomes, 64 worlds each; descriptive):
- **Classes:** 41 "uses", 107 "unclear", 364 "no material benefit". On 64 worlds most are expected to
  be unclear or no-benefit.
- **Most score 0:** the median is 0.
- **53% drive backwards:** their mean forward command is below 0. The median forward command is
  −0.06.
- **The median absolute turn command is 0.25,** and the median share of saturated turn neurons 0.10.
- **Generation-0 selection picks the few backgrounds that move forward and let the graft steer;** the
  population's median fitness on the selection worlds is 0.

**04a run 2 with L1 grafted** (1 024 worlds):
- mean 0.89, "unclear";
- forward command 0.98, turn command −0.28, a strong right bias;
- **the graft does not work on this background at generation 0.** For comparison only, E2d measured
  this champion at 2.64 on its own hold-out (other worlds).

## 4. Mutational robustness (`robustness.json`)

The qualified module on its carrier; 256 mutants per scale, module parameters only; the scales are
paired (the same draws); 64 worlds.

| Scale (× 02's) | Median child's share of the parent's score |
|---|---|
| 0.125 | 0.92 |
| 0.25 | 0.78 |
| 1 | 0.00 |

- The parent scores 5.23 on these worlds.
- **The fallback did not trigger,** since 0.25× keeps at least half: E4s-1's module factor stays
  0.25×.
- **A mutation at 02's full scale destroys the module in the median child.**
- **The bounds caveat above applies.**
- **The parent and the children ran in different compositions** (one padded strain against chunks of
  64), so the share is descriptive.

## What E4s-1 takes from this

- **The frozen module:** `module.json`, L1, re-qualified on fresh worlds before any evolution.
- **The background:** random N2. The pre-stated rule's statistic was 16 of 16.
- **The module's mutation factor:** 0.25×.
- **For its design:**
  - the parameters on the bounds;
  - 04a run 2 as a background where the graft does not work at generation 0 (the case study C2);
  - the valley, which predicts that free mutation at 02's scale will not keep a strong gain (U).

## Not shown

- What mutations produce, or why the plateau exists: the sweep is one external intervention.
- Anything about the worm's own chemotaxis: stereo sensing here is a game-design choice. The
  computation lives in a 4-neuron graft outside the N2 mask.
- Whether L1 keeps its function under evolution: that is E4s-1.
