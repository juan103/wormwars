# E4 / 04c, the main task: results (exploratory)

**What this is.** E4 asked whether two grafted navigation modules come to use information crossing between them,
through 32 optional cross-links, under evolution (`docs/E4/E4-DESIGN.md` v3). Its main formal run was **not run**: the
pilot and its follow-ups showed that it would most likely spend about 20 GPU-hours on an inconclusive null, and the
owner re-scoped E4 to its diagnostic task, E4-D (D258), on both reviewers' recommendation (D257). Nothing of the main
run was pre-registered. Everything below is exploratory, and was decided after seeing data.

**Compute:** 4.20 of E4's 30 GPU-hours (the pilot's attempt 1, 3.01; the diagnostics, including a run that failed at
its last step, and stage A, 1.19), on one RTX 5080; `compute-record.json` and `compute-record-diagnostics.json`.

## 1. The pilot's attempt 1 (D250-D252)

**Set-up:** X0 (no cross-links) and X+ (32 mutable cross-links), 4 runs each, paired by run seed, from 32 copies of
E-G, population 32, elites 3, truncation 8, 100 generations, T-F's mutation mask at factor 0.25 (w_sigma 0.08,
tau_sigma 0.15, bias_sigma 0.05), 8 training mazes per strain per generation, 6 × 6 island mazes at H = 1 800.

**What happened:** about 56 seconds per generation (4 runs); the attempt reached its 3-hour cap in X+'s generation 80
(`pilot.json`). X0's 4 runs completed; X+'s training was in memory and is lost.

**What X0's runs show** (`pilot-attempt1-summary.json`, from the saved selection matrices):
- generation 0's population (32 copies of E-G) averages 6.23 visits per wey; from generation 1 on, the population mean
  sits near 2.4-3.4 for 100 generations;
- the children (excluding the 3 copied elites) average 2.5-2.8 in generations 1-10 and 2.9-3.1 in 90-99; the elites
  5.5-5.9 and 5.5-6.0;
- each generation's best strain on its own 8 mazes averages 6.3-6.7 in generations 0-9 and 6.3-6.9 in 90-99, but this
  measure is mostly noise (E-G's per-maze SD is about 3.7);
- **on 64 validation mazes, no final strain of any run beats E-G** (E-G 7.63; the runs' best 6.16, 6.52, 7.08 and
  6.68; `diagnostics.json`, `final_x0_validation`). The best of 32 is selected on the same mazes, so even these are
  optimistic.

**The generation-1 load** (`pilot.json`): bred once from E-G, X0's population averaged 1.94 and X+ cost a further
0.21 at cross-link factor 0.25, rising to 1.14 at 4.0. These were measured on a population already at the floor
(below), so they understate the cross-links' cost.

## 2. The diagnostics (D253-D254; `diagnostics.json`)

Generation 1, **children only**, paired on the same 8 mazes and 4 generator seeds:

| condition | children's mean (visits per wey) |
|---|---|
| E-G, unbred | 4.03 |
| bred with every scale at 0 | 4.03 (identical: no defect in the breeding or evaluation path) |
| X0's mask at 0.25 / 0.10 / 0.05 | 1.97 / 3.11 / 3.60 |
| weights only, at 0.25 | 4.14 |
| τ only | 4.16 |
| the gated comparator → motor edges only | 4.13 |
| one parameter per child, on average | 4.04 |
| **biases only** | **1.98** |
| module A only / module B only | 2.80 / 2.80 |

On these mazes, the whole generation-1 load came from the biases of the 8 module neurons; a bias step of σ 0.0125 was
enough. It is not a property of E4's gate or arena: the ungated seed E + W2 lost as much on the same mazes (3.66 →
2.00 at 0.25), and on 5 × 5 tree mazes at H = 2 400 both organisms lost about a third (E-G 6.59 → 4.38; E + W2 6.52 →
4.34).

## 3. Stage A, the calibration (D255-D257; `calibration.json`)

Generation 1, children only, paired on a fresh block of 16 mazes (E-G 7.97 there), under rules fixed in advance
(`wormwars/e4/calibration.py`).

**The biases.** At factor 0.25, nose biases alone gave 3.38 and comparator biases alone 6.86, a ratio of losses of
about 4, as predicted from the module's gains (Fable: 18 from a nose bias to a turn neuron, 6 from a comparator bias).
With weights and τ at 0.25, the biases at 0.05, 0.02, 0.01, 0.005 and frozen gave 6.73, 7.20, 7.40, 7.41 and 7.40. By
the declared rule no factor qualified: the frozen-bias children kept 93% of E-G, below its 95% condition (weights' and
τ's own load on this block), and the confirmation on a second block failed too (94%).

**The cross-links.** With the biases frozen (X0's children 7.40), X+'s children gave 4.53, 3.09, 2.08, 1.11 and 0.64 at
cross-link factors 0.25, 0.5, 1, 2 and 4; every factor failed the load bound (a loss of at most min(0.25, 5%)). The
share of children at 5 visits or more was 42% at 0.25: the loss is mostly the share of children that break.

**What the cost is,** with only the 32 slots mutated (every inherited parameter frozen; all links cut is E-G, 7.97):

| | factor 0.25 | factor 1.0 |
|---|---|---|
| intact | 4.58 | 2.07 |
| mean-substituted (the links' constant part kept, their fluctuation cut) | 5.33 | 1.93 |
| centred (the constant part removed, the fluctuation kept) | 4.98 | 1.49 |
| the nose-origin links cut | 6.26 | 3.81 |
| the comparator-origin links cut | 4.98 | 2.05 |

Both the constant and the fluctuating parts cost, and removing the nose-origin links rescues most. That cut removes the
nose-origin links of both modules, into both modules' noses and comparators, and the noses read trails as well as
scent, so **the mechanism is unresolved** (Astra; a correction to D256's first reading, D257).

**A reading, not a result** (Fable, D257): B's own scent is out of range (9 grid cells) for most of a B-leg, so B's
comparators steer on any input of about 0.01-0.02, and that is also the size at which a link would carry a useful
signal. A link small enough to pass the load bound would then be too small to drift into usefulness, and selection on
8 noisy mazes would be too weak to accumulate signed steps.

## 4. Headroom (D259; `headroom.json`, CPU)

On stage A's block: E-G 7.12, the scripted follower 11.29 (shared trails) and 3.20 (none), the oracle 32.98. E-G
reaches 22% of the oracle, so navigation has headroom; whether anything A holds could use it is not shown. (E-G's 7.12
here and 7.97 in stage A are the same genome on the same mazes, on the CPU and the GPU: a chaotic rollout, not
reproduced across devices, D082.)

## 5. What E4's main task can and cannot say

- **It can say:** E-G's comparator modules are mutationally fragile; at T-F's mutation strength the population sits far
  below E-G and 100 generations did not recover it; random cross-links cost heavily at every registered size; and the
  cost cannot be attributed to one mechanism from these tests.
- **It cannot say:** that evolved sharing could not help, or that the modules hold nothing useful for each other.
  Random perturbations can harm a circuit even where selected connections would help (both reviewers, D257).
- **Why the formal run was dropped:** at any cross-link size that passes the load bound, recruitment by drift is
  implausible, so P1-cut would read "equivalent" by construction and P2 "unclear" at R = 8 (Fable); a null would mostly
  be inconclusive (Astra). E4-D, where transfer is necessary by construction and the chance level is exactly one half,
  asks the question directly.

## Corrections

- D256 (2026-10-13) first read stage A as "cross-talk from A's noses" and "mostly harmful cross-talk"; both overreached
  and are corrected in D257, quoted there.
