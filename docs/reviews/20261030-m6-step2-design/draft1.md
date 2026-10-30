# M6, step 2: does the champions' fading history effect matter for their foraging? — design note

*Draft 1, 2026-10-30, before consultation. The owner's order (D379): step 1, then this test, designed and costed
first, then stop. Astra proposed it in M6-3's review. This note sets out the intervention, its controls, what it can
and cannot show, and the cost, for review before a plan. CPU only.*

## The question

Selection on T1 built a larger history effect than drift (02b; M6-0). On the probe it is a fading transient of a few
tens of ticks in 101 of 102 champions, about six times drift's at the start. **Does the champions' foraging depend
on it?** A null would not show memory useless. A drop would show that the champions' slow dynamics matter, and the
controls below decide how far that points at the history effect itself.

## The intervention: speed up every neuron

Every time constant is multiplied by a factor k: `tau → k·tau` for all neurons.
- **What stays the same.** The fixed points do not depend on tau (`0 = −v + b + W tanh v + G(...) + I`), so each
  champion's steady-state map from input to output is unchanged.
- **What changes.** Every transient is k times as long, and so is the history effect. k < 1 shortens it; k > 1
  lengthens it.
- **Arms:** k = 1 (intact), 0.5, 0.25 (shorter memory), and 2 (longer, a symmetry check).
- **The confound, stated now.** Faster dynamics also mean faster responses to input. In a linear filter, the time
  scale of memory and the latency of response are the same quantity. This intervention cannot separate them. It
  tests whether the champions' slow dynamics matter for foraging, which include the history effect.
- **The tuned-optimum problem.** Any change to an evolved genome may lower its score, because selection left it near
  a local optimum. The k = 2 arm and the controls below address this; a drop at k < 1 alone does not.

## Controls and comparisons

- **Validation on the probe,** per genome and k: the history effect on each run's own bank (M6-0's a, d(5)/a and
  τ_stay) must shrink with k < 1. If it does not, the intervention has not done what it claims, and the reading is
  inconclusive.
- **Generic cost of a time-scale change:** the same intervention on the same runs' g00 champions and on one drift
  genome per run. These have small history effects (M6-0). If their scores fall as much as the champions', the drop
  is not specific to what selection built.
- **Dose-response across champions:** does each champion's drop at k = 0.25 grow with the size of its history effect
  (M6-0's a and d(5) on the own bank)? This is a correlation over 102 champions, with the 30 graph-and-run blocks as
  the unit.
- **Symmetry:** the score at k = 2 against k = 1. If slowing down also costs, the champions sit at a tuned optimum,
  and the k < 1 drop says less about memory.

## Measures and a first sketch of the readings

- **Score:** T1's foraging score (`rollout(...).score`) on 02b's 32 criticality worlds (`grid.PROBE_IDS[:32]`), the
  same worlds for every arm, so comparisons are paired.
- **Primary:** per run, the champion's relative change at k = 0.25, `score(0.25)/score(1) − 1`, minus the mean
  change of that run's controls (g00 and drift). It is averaged over the 30 blocks, with a cluster bootstrap as in
  M6-0.
- **Wording, to be fixed in the plan:** "the champions' foraging depends on their slow dynamics beyond the generic
  cost of a time-scale change" if that interval lies below zero, with the validation passed. Otherwise "not
  distinguishable from the generic cost" (or the reverse direction).
- **Secondary:** the dose-response, the k = 0.5 and k = 2 arms, and the absolute changes.

## Seen before this note

A timing run on one champion (T1-M0-N2 run 0, g39), on the 32 worlds, gave these mean scores:

| k | 1 | 0.5 | 0.25 | 2 |
|---|---|---|---|---|
| Mean score | 2.82 | 2.62 | 2.08 | 2.84 |

The k = 1 copy reproduced the intact score exactly, and scaling took about 3.5 s per genome and arm. This one
champion is disclosed and would stay in the run.

## Cost and likely size of the answer

- **Cost.** About 3.5 s per genome and arm on 32 worlds:
  - the champions alone: 102 champions × 4 arms ≈ 24 minutes;
  - with the controls: (102 g00 + 102 drift) × 4 arms ≈ 48 minutes more;
  - validation probes: minutes.

  **About 1.5 CPU hours in all, capped at 3.**
- **Likely answer.** The single champion above already loses about a quarter of its score at k = 0.25 and nothing at
  k = 2. The open question is whether the controls lose as much. With 30 blocks, a difference of about 10% of score
  should be visible if the block-to-block spread is like M6-0's. A smaller one would read as "not distinguishable".

## Alternatives considered

- **Reset the history directly:** at intervals, move each brain's state toward the steady state for its current
  input. This targets memory without changing latency, but it needs a fixed point per world and tick, roughly 100
  times the cost, and the reset itself perturbs behaviour.
- **Scramble the sensory input in time:** this breaks the loop between action and sensing, so it tests more than
  memory.
- **Erase the probe-defined history difference during foraging:** no history difference is defined during
  foraging, only on the probe.

## Questions for the reviewers

1. Is the time-scale intervention, with these controls, an honest test of whether the history effect matters? What
   would you change?
2. Are the controls (g00, drift, dose-response, k = 2) the right ones? Is anything missing, for example a scaling of
   only the neurons outside the read-out?
3. Is the primary contrast right, and what should its fixed wording say?
4. Is anything here not worth its cost?
