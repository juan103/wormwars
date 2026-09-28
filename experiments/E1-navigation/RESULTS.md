# E1: the positive control for navigation. Results

**The registered outcome, in the wording fixed in advance:** *"E1 positive control: passed"*. No
rule failed.

The declared body and sensors support navigation to a localised, relocating source on unseen
layouts, and a scripted navigator that uses the cue does it almost as well as an oracle that knows
where the target is. 04a, the evolved navigation primitive, can start. It gets its own
pre-registration.

**Timeline:**
- The pre-registration ([`PREREGISTRATION.md`](PREREGISTRATION.md), v6) was bound at `eb0b781` and
  pushed before any formal measurement. It is the first registration in this series to be public
  before its formal run.
- One guarded smoke run, on smoke worlds, passed every formal guard on that commit (the RTX 5080,
  the pinned environment, clean and pushed).
- **The pilot** ran at `eb0b781` and wrote the freeze by the registered rules
  ([`freeze.json`](freeze.json)). The freeze was committed and pushed at `a73a67d`.
- **The gate** ran once, at `a73a67d`, on gate worlds 996 201 000 to 996 202 023. It recorded the
  freeze's sha256 (LF-normalised, `c5c48f83…`) and found no change in code, the pre-registration or
  the environment since the pilot.
- **Compute:** the pilot took 316 s and the gate 36 s: about 6 minutes of the registered 8
  GPU-hours ([`compute-record.json`](compute-record.json)).

## The pilot (by rule; descriptive)

**σ = 6, flagged, as disclosed before registration (§7).** The share of leg starts where the next
target's scent is at least 5% of its peak, on 256 pilot worlds:

| σ | 2 | 3 | 4 | 6 |
|---|---|---|---|---|
| share at or above 5% of A | 0.000 | 0.000 | 0.309 | 0.878 |

No candidate reached the registered 90%, so the rule's fallback, the largest candidate, applied.
The flag is a limitation of the task's signal coverage, not a threshold any controller used.

**Other pilot measurements:**
- **The own-body collision level:** 0.452 (from 3 887 samples). The wall-follower's thresholds
  start above it.
- **Clamp saturation:** none. The peak input current is 0.35, against a clamp of 5.
- **Generation 0** (256 random N2 genomes on 64 pilot worlds, in one chunk):
  - 74% score zero on every world;
  - the mean count is 0.031 targets per episode, and the best genome's mean is 0.69.

  For 04a, this means random brains rarely reach a target, so selection will need the design's
  bounded shaping term. That decision belongs to 04a's pre-registration.
- **Throughput in 04a's evolution shape** (32 strains × 8 worlds × 1 wey, on ids outside E1's
  ranges): 110 strain-worlds/s for one run, 336 for 4 runs batched together, and 438 for 8.

**Tuning, on 256 tuning worlds** (mean targets per 300-tick episode, the winner of each registered
grid):

| Controller | Tuned mean | Episodes with ≥ 2 | Winner |
|---|---|---|---|
| **S-const** (stereo steering, one speed) | **8.78** | 1.00 | k = 8192, speed 1.0, turn 0 |
| S-const at k ≤ 32 (non-gating) | 5.63 | 1.00 | k = 32, speed 1.0, turn 0.2 |
| M-avg (memory on the stereo mean) | 2.16 | 0.93 | slow 0.7, fast 1.0, threshold 0.05, turn 0.2, fall turn 1.0 |
| K (level kinesis) | 1.03 | 0.27 | slow 1.0, fast 0.2, threshold 0.05, turn 0.2 |
| wall-follower | 0.66 | 0.15 | speed 1.0, seek −0.1, avoid 1.0, threshold 0.50 |
| constant (speed × turn) | 0.50 | 0.07 | speed 0.8, turn 0.1 |
| random walk | 0.36 | 0.05 | speed 1.0, rate 1.0, persistence 0.5 |
| oracle (ceiling, not tuned) | 8.85 | 1.00 | k = 2, speed 1.0 |

**The navigator, by rule:** S-const, since its tuned mean is above M-avg's.

## The gate (1 024 gate worlds, used once)

| Rule | Registered | Result | |
|---|---|---|---|
| 1. Reliability | at least 820 of 1 024 episodes with ≥ 2 targets | **1 023 of 1 024** | passed |
| 2. Beats constant | lower bound of (navigator − baseline) > 0.5 | mean 8.25, lower bound 8.19 | passed |
| 2. Beats random walk | same | mean 8.42, lower bound 8.37 | passed |
| 2. Beats wall-follower | same | mean 8.03, lower bound 7.97 | passed |
| 2. Beats K | same | mean 7.74, lower bound 7.68 | passed |
| 3. Uses the cue | lower bound of (0.5 × real − mirrored) ≥ 0 | mean 4.31, lower bound 4.29 | passed |

Lower bounds are one-sided 95%, from a paired bootstrap over worlds (10 000 resamples, seed 0).

**Every controller** (mean targets per episode on the gate worlds, and as a fraction of the
oracle's):

| Controller | Real cue | Constant probe (own blind level) | Fraction of oracle |
|---|---|---|---|
| **navigator (S-const)** | **8.68** | 0.05 | 0.987 |
| navigator, mirrored decoy | 0.03 | | 0.003 |
| S-const at k ≤ 32 | 5.62 | 0.30 | 0.639 |
| M-avg | 2.20 | 0.05 | 0.250 |
| K | 0.94 | 0.30 | 0.107 |
| wall-follower | 0.65 | 0.65 | 0.074 |
| constant | 0.43 | 0.43 | 0.049 |
| random walk | 0.26 | 0.26 | 0.029 |
| oracle | 8.79 | | 1 |

**Secondary measures:**

| | First arrival | Latency (mean ticks) | Finished leg (median ticks) | Path efficiency (median) |
|---|---|---|---|---|
| navigator | 0.999 | 34.0 | 32 | 0.82 |
| oracle | 1.000 | 33.3 | 31 | 0.83 |
| S-const at k ≤ 32 | 1.000 | 46.8 | 38 | 0.71 |
| M-avg | 1.000 | 119.2 | 116 | 0.42 |
| navigator, mirrored | 0.028 | 293.4 | 38 | 0.75 |

- Latency is the mean of min(first-arrival tick, horizon), so failures count.
- Path efficiency is the head's straight-line displacement over its path, for finished legs. Even
  the oracle stays below 1: the body has a turning radius.

## Reading

- **The task can be done with the declared body and sensors.** A stereo navigator reaches almost
  every target the oracle does (98.7%), at almost the oracle's speed.
- **It succeeds because of the cue, not good search:**
  - with the scent read at the mirrored point, its count falls from 8.68 to 0.03, below every blind
    baseline, because it steers to the decoy;
  - with a constant scent it falls to 0.05;
  - the blind baselines (constant, random walk, wall-follower) score the same under the constant
    probe, as a blind controller should;
  - the best blind search (wall-following) reaches 0.65.
- **Relocation works:** 1 023 of 1 024 episodes reached at least two targets.
- **Steering gain matters.** The winner is effectively bang-bang (k = 8192). At a gain a brain can
  plausibly produce (k ≤ 32), stereo steering keeps 64% of the oracle's count. That is still far
  above every blind baseline (5.62 against at most 0.94), but it is a realistic target for 04a,
  not the ceiling.
- **Memory on the stereo mean (M-avg) is a weak navigator here** (2.20, 25% of the oracle).
  Comparing the mean with the previous tick is much slower than comparing left with right.

## What this does not show, and caveats

- **It is a scripted control, not an evolved brain.** It shows the task is solvable and that the
  cue is usable. It says nothing yet about whether N2 brains can learn it: that is 04a.
- **The coverage flag.** σ = 6 did not reach the registered 90% coverage (0.878). The flag was
  expected from geometry before registration; it did not prevent passing.
- **The design's scope** (design §"What E1 does and does not establish"): a localised,
  relocating source, with no trails, junctions, occluding walls or colonies.
- **Composition and reproducibility:**
  - each gate arm is one scripted strain on 1 024 worlds, run in CUDA default mode;
  - the counts are exact integers, but no exact replay is claimed for CUDA default mode;
  - every per-world count and the full event tables are committed ([`gate.json`](gate.json),
    [`gate_events.npz`](gate_events.npz)).
- **Development exposure** is disclosed in the pre-registration (§7). The first smoke run and a
  debug run touched early pilot and tuning worlds, before the stages were offset to index 1 000.
  No gate world was evaluated before the gate.
- **Deviations from the pre-registration:** none.

## Files

| File | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The registration (v6, bound at `eb0b781`) and its review history |
| [`freeze.json`](freeze.json) | The pilot's measurements and every rule-chosen value; each tuning grid point's mean |
| [`gate.json`](gate.json) | The gate's rules, means, secondaries and every arm's per-world counts |
| [`gate_events.npz`](gate_events.npz) | Every arm's event table: per world and target, the activation and reach ticks, path length, target position, and the head's start and end |
| `pilot-started.json`, `gate-started.json` | The stages' start markers |
| [`compute-record.json`](compute-record.json) | The compute record for both stages |
| [`development-records/`](development-records/) | The smoke runs' compute records, disclosed in §7 |
| [`../../scripts/e1.py`](../../scripts/e1.py) | The runner, with every registered number in `REGISTERED` |
| `../../wormwars/e1/`, `../../wormwars/world.py` | Task N and the controls |
