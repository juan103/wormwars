# E1: the positive control for navigation. Pre-registration

**Status:** written 2026-09-28, before the pilot. It is pushed to GitHub before the pilot runs, so
for the first time in this series the registration is public before any registered measurement.
The binding commit is the one that first contains this file together with `scripts/e1.py`; the
pilot records its commit.

**Design:** [`docs/E1/DESIGN.md`](../../docs/E1/DESIGN.md) v2.1, agreed by Astra 6 and Fable 5.1
(D077, D078). This file fixes what the design left open. Where they differ, this file holds for the
positive control. 04a, the evolved navigator, gets its own pre-registration after the gate.

**Code:** Task N in `wormwars/world.py` (the `navigate` task) and `wormwars/e1/`. The runner is
[`scripts/e1.py`](../../scripts/e1.py), whose `REGISTERED` constant holds every number below. The
runner applies every rule mechanically, so nothing is chosen by hand after data are seen.

## 1. The question

Can a scripted navigator, with the declared body and sensors, reach **moved targets** on **unseen
layouts**, better than **simple movement baselines**, and **because of the cue**? Arrivals alone
are not enough: good search also collects hits. The gate asks whether target information improves
arrival. One valid passing navigator is enough to establish that the task can be done, and to start
04a.

## 2. Task N (the design's §"Task N", made concrete)

- **The world:** one swarm of one wey per world, and the boundary wall only. There is no food,
  hazard, pheromone or combat, so the arena side is 24.
- **Energy is off:** no metabolic drain, movement cost or eating, so the wey lives for the whole
  horizon of **300 ticks**.
- **The target is a sensing-only scent source:** A exp(-d² / 2σ²), truncated at ceil(3σ) cells
  along each axis. It is added to what the wey senses, never to the food field, so the energy
  ledger stays exactly balanced.
- **Fixed now:**
  - amplitude **A = 1.0**, with the sensing scale **0.35** (peak input current 0.35, against a
    clamp of 5);
  - radius **R = 1.5**: a target is reached when the head is within R of its centre;
  - separation **D = 8**: consecutive centres, and the first from the spawn, at least D apart;
  - no maximum separation, and centres at least **3** cells from the wall ring.
- **The target sequence:** a function of (run seed, world id, k) only, from a random stream of its
  own. Every controller faces the same destinations. Controller state persists across
  relocations.
- **The score:** targets reached in 300 ticks, an integer.
- **The run seed:** 1 100 001.
- **World ids:** pilot 996 000 000+, tuning 996 100 000+, gate 996 200 000+, and 04a's hold-out
  996 300 000+. The ranges are disjoint from each other and from earlier experiments.
- **Execution:** CUDA default mode, on one RTX 5080, in the pinned environment. Each controller is
  one strain on all of a stage's worlds, in one rollout; scripted controllers have no neural
  batch. Counts are exact integers.

## 3. The pilot (`e1.py pilot`), on pilot and tuning worlds only

It runs once, and writes `experiments/E1-navigation/freeze.json`.

1. **σ (the scent's width):**
   - candidates **2, 3, 4 and 6**;
   - on **256 pilot worlds**, at each world's first **5** leg starts (the spawn, then each previous
     centre), it measures the next target's scent from the actual sampled field;
   - **the rule:** the smallest σ at which at least **90%** of leg starts read at least **5% of
     A**;
   - **if none qualifies:** σ = 6 (the largest), flagged. The flag is reported as a limitation,
     and it changes no other number.
2. **The own-body collision level:** on 64 pilot worlds, 100 ticks at speed 0.5 and turn 0.2, the
   largest front or front-right collision current the wey's own body produces, while its head is
   at least 3 cells from the wall.
3. **Generation 0:** 256 random N2 genomes on 64 pilot worlds: the share scoring zero on every
   world, the mean count, and throughput. These are descriptive, for 04a's pre-registration.
4. **Clamp saturation:** peak input current against the clamp. It is expected to be zero by
   construction.
5. **Tuning,** on **256 tuning worlds.** Each grid point is one strain, in chunks of 64; the first
   maximum of the mean count in grid order wins.

   | Control | Grid |
   |---|---|
   | S-const (stereo steering at one speed) | k ∈ {1, 2, 4, 8, 16, 32, 64, 256, 1024, 8192} × speed ∈ {0.4, 0.6, 0.8, 1.0} × turn ∈ {-0.2, -0.1, 0, 0.1, 0.2} |
   | M-avg (memory kinesis on the stereo mean) | slow, fast ∈ {0.4, 0.7, 1.0} × threshold ∈ {0, 0.02, 0.05, 0.1} × turn ∈ {0, 0.1, 0.2} × fall turn ∈ {0.4, 0.7, 1.0} × fall threshold ∈ {0, 0.001, 0.005} |
   | K (level kinesis) | slow, fast ∈ {0.2, 0.5, 0.8, 1.0} × threshold ∈ {0.02, 0.05, 0.1, 0.2} × turn ∈ {0.05, 0.1, 0.2, 0.4} |
   | constant (speed × turn; covers circling) | speed ∈ {0.2, 0.4, 0.6, 0.8, 1.0} × turn ∈ {-0.6, -0.5, …, 0.6} |
   | random walk (persistent turn) | speed ∈ {0.4, 0.7, 1.0} × rate ∈ {0.2, 0.4, 0.8, 1.0} × persistence ∈ {0.5, 0.8, 0.9, 0.95, 0.99}; noise seed 0 |
   | wall-follower (collision inputs, wall on the right) | speed ∈ {0.4, 0.7, 1.0} × seek turn ∈ {-0.1, -0.2, -0.4} × avoid turn ∈ {0.4, 0.8, 1.0} × threshold = own-body level + {0.05, 0.1, 0.2, 0.4, 0.8, 1.6} |

   - S-const is also tuned with k ≤ 32 and reported. That version is non-gating.
   - **The oracle** steers at the true target (k = 2, speed 1). It is the ceiling, not a control,
     and it is not tuned.
6. **The navigator:** of the tuned S-const and M-avg, the one with the higher tuned mean. On a
   tie, S-const.

The pilot may not use gate worlds, and nothing in it is chosen by hand. **The freeze is committed
before the gate,** and the gate records its sha256.

## 4. The gate (`e1.py gate`): 1 024 gate worlds, used once

Each rule compares per-world counts on the same worlds. **The interval** is a one-sided 95% lower
bound: the 5th percentile of 10 000 bootstrap resamples of worlds (seed 0) of the mean paired
difference.

1. **Absolute reliability:** at least **80%** of gate episodes reach at least **2** targets. The
   second arrival tests relocation.
2. **Beats the baselines:** for each of the tuned **constant**, **random walk**, **wall-follower**
   and **K**, the lower bound of (navigator − baseline) exceeds **0.5 targets per episode**. No
   ratio is taken against a near-zero baseline.
3. **Uses the cue:** the navigator is also run under the `mirrored` probe, where the scored target
   is unchanged but its scent is read at the point reflection, a consistent decoy. The lower bound
   of (real − mirrored) must be at least **50% of the navigator's real mean**. The count may fall
   below the blind level: a navigator parks at the decoy.

**The outcome** is all three together (an intersection, so no multiplicity correction). The
wording is fixed:
- *"E1 positive control: passed"*;
- *"E1 positive control: not passed"*, followed by the failed rules.

**Reported, non-gating:**
- the `constant` probe for every controller, as its own blind level;
- every mean as a fraction of the oracle's;
- S-const at k ≤ 32;
- first-arrival success;
- latency, as the mean of min(first-arrival tick, horizon), so failures count;
- median leg time;
- path efficiency (straight line over path, for legs after the first).

## 5. Budget and rules

- **The cap: 8 GPU-hours** for the pilot, tuning and gate together, counted with T0's accounting
  (synchronised wall clock). It is registered in code and never extended.
- **A clean tree is required** for both stages. Provenance is recorded at the start.
- **The gate refuses to run** if its result already exists, if the freeze is not committed and
  unchanged, or if the freeze's registered numbers differ from the script's.
- **Deviations** are reported in the results, and none is made silently.

## 6. If no navigator passes

The design's rule applies. The implementation, the signal availability, constant-speed steering
and the search behaviour are diagnosed first. The body or sensors change only if that diagnosis
points there: head oscillation, or a stronger or wider cue. Any change gets a new pre-registration.
It never retunes on the gate worlds.

## 7. What was seen before this registration (disclosure)

- **The development runs:** the task's tests, and a smoke run of the whole pipeline at tiny sizes.
  From now on the smoke run uses world ids 0-9 999, outside every E1 range.
- **One debug run touched pilot worlds.** Before the smoke run was moved off the E1 ranges, a
  debug run computed the σ measure on the **first 32 pilot worlds**:
  - share of leg starts at or above 5% of A: σ = 2: 0.00; σ = 3: 0.00; σ = 4: 0.33; σ = 6: 0.875;
  - no controller, count or gate quantity was computed on E1 worlds.
- **What predates it:** the rule's numbers (the candidates, the 5% floor, the 90% share and the
  fallback) were already in `REGISTERED` before that run, and are unchanged.
- **The likely consequence:** the pilot will probably select σ = 6, flagged. About an eighth of leg
  starts would then begin with the scent below the floor, and a controller must search before it
  can steer.
- **What was not done:** no candidate was added (for example σ = 8), and no share was lowered after
  this was seen.
- Smoke runs outside the E1 ranges also exercised every controller at a 40-tick horizon. No
  quantity from them enters this registration.

## 8. What E1 establishes, and what it does not

**It establishes,** if passed, that the declared body and sensors support navigation to a
localised, relocating source on unseen layouts. It does not validate trails, junctions, walls that
occlude the scent, or colonies (the design's §"What E1 does and does not establish"). The input
mapping is a commitment: the goal cue enters at the food neurons AWA, AWC and ASE, left and right.
