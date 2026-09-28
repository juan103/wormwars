# E1: the positive control for navigation. Results

**The registered outcome, in the wording fixed in advance:** *"E1 positive control: passed"*. No
rule failed.

The declared body and sensors support navigation to a localised, relocating source on unseen
layouts, and a scripted navigator that uses the cue does it almost as well as an oracle that knows
where the target is. 04a, the evolved navigation primitive, can start. It gets its own
pre-registration.

## Corrections (2026-09-28, D101)

Astra 6 and Fable 5.1 reviewed this file (`docs/reviews/20260928-194709-E1-results/`). Both answered
"fix", on text only; the registered outcome is unchanged. Astra independently recomputed every count,
secondary measure and bootstrap bound from the committed files, and all match. Each statement below
is corrected in place.
- *"the pilot took 316 s and the gate 36 s"* mixed two clocks: the pilot's figure came from the
  accounting, the gate's from its internal timer. By the accounting, the pilot took 316.2 s and the
  gate 37.6 s, 353.8 s in total.
- *"far above every blind baseline (5.62 against at most 0.94)"*: 0.94 is K, which reads the scent
  level, so it is not blind. The best blind baseline is the wall-follower, at 0.65.
- *"a gain a brain can plausibly produce (k ≤ 32)"* and *"a realistic target for 04a"*: the k ≤ 32
  bound came from design review as an assumption. It was never derived or measured for N2 brains.
  The full gain curve is now given.
- *"because it steers to the decoy"*: consistent with the data, but not measured. The event tables
  do not record where an unfinished leg's head ended.
- *"selection will need the design's bounded shaping term"* (and in D100): the generation-0 result
  meets the design's condition for the shaping term. It does not show that unshaped evolution
  cannot work.
- *"No gate world was evaluated before the gate"* was stronger than the pre-registration's §7, whose
  statement about the second smoke pair rests on command order. It is hedged as §7 is.

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
- **Compute,** by the accounting: the pilot took 316.2 s and the gate 37.6 s, 353.8 s in total,
  about 6 minutes of the registered 8 GPU-hours ([`compute-record.json`](compute-record.json)).
- **The guarded smoke run's records** are committed with the other development records
  (`development-records/guarded-smoke.json`).

## The pilot (by rule; descriptive)

**σ = 6, flagged, as disclosed before registration (§7).** The share of leg starts where the next
target's scent is at least 5% of its peak, on 256 pilot worlds:

| σ | 2 | 3 | 4 | 6 |
|---|---|---|---|---|
| share at or above 5% of A | 0.000 | 0.000 | 0.309 | 0.878 |

No candidate reached the registered 90%, so the rule's fallback, the largest candidate, applied.
At σ = 6, 1 124 of the 1 280 prescribed leg starts read at least 5% of A, and 156 fell below it.
- The flag is a limitation of the task's signal coverage, not a threshold any controller used.
- Below 5% is not zero: a high-gain controller can use weaker signals.
- The measure samples the spawn and the previous centres, not where each controller actually
  started its next leg.

**Other pilot measurements:**
- **The own-body collision level:** 0.452 (from 3 887 samples). The wall-follower's thresholds
  start above it.
- **Clamp saturation:** none. The goal cue's peak input current is 0.35, against a clamp of 5.
  Other channels can be larger: the own-body collision current above is 0.452.
- **Generation 0** (256 random N2 genomes on 64 pilot worlds, in one chunk):
  - 74% score zero on every world;
  - the mean count is 0.031 targets per episode, and the best genome's mean is 0.69.

  For 04a, this meets the design's condition for the bounded shaping term: counts mostly zero at
  generation 0. It does not show that unshaped evolution cannot work. At 0.031 targets per episode,
  a generation of 32 genomes × 8 worlds sees about 8 arrivals: the signal is sparse, not absent.
  The best random genome (0.69) scores about as well as the tuned blind baselines, so the likelier
  risk is convergence on blind search. That decision belongs to 04a's pre-registration.
- **Throughput in 04a's evolution shape** (32 strains × 8 worlds × 1 wey, on ids outside E1's
  ranges): 110 strain-worlds/s for one run, 336 for 4 runs batched together, and 438 for 8.

**Tuning, on 256 tuning worlds** (mean targets per 300-tick episode, the winner of each registered
grid):

| Controller | Tuned mean | Episodes with ≥ 2 | Winner |
|---|---|---|---|
| **S-const** (stereo steering, one speed) | **8.78** | 1.00 | k = 8192, speed 1.0, turn 0 |
| S-const at k ≤ 32 (non-gating) | 5.63 | 1.00 | k = 32, speed 1.0, turn 0.2 |
| M-avg (memory on the stereo mean) | 2.16 | 0.93 | slow 0.7, fast 1.0, threshold 0.05, turn 0.2, fall turn 1.0, fall threshold 0 |
| K (level kinesis) | 1.03 | 0.27 | slow 1.0, fast 0.2, threshold 0.05, turn 0.2 |
| wall-follower | 0.66 | 0.15 | speed 1.0, seek −0.1, avoid 1.0, threshold 0.50 |
| constant (speed × turn) | 0.50 | 0.07 | speed 0.8, turn 0.1 |
| random walk | 0.36 | 0.05 | speed 1.0, rate 1.0, persistence 0.5 |
| oracle (ceiling, not tuned) | 8.85 | 1.00 | k = 2, speed 1.0 |

**The navigator, by rule:** S-const, since its tuned mean is above M-avg's.

**The steering gain curve** (S-const, the best tuned mean at each k, on the tuning worlds):

| k | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 256 | 1024 | 8192 |
|---|---|---|---|---|---|---|---|---|---|---|
| best mean | 0.88 | 1.13 | 2.38 | 3.18 | 4.12 | 5.63 | 6.97 | 8.51 | 8.77 | 8.78 |

- The curve plateaus near k = 256. k = 8192 beats k = 1024 by two arrivals in 256 episodes.
- The k ≤ 32 winner relies on a constant turn of 0.2; at turn 0, k = 32 gives 4.23. So "S-const at
  k ≤ 32" is a separately tuned policy, not a pure reduction in gain.

**Grid edges.** Several winners sit at the edge of their registered grid:
- the wall-follower and the random walk, on every parameter;
- K on speed; M-avg on four of six parameters;
- S-const on k and speed.

The blind baselines may therefore be under-tuned. That cannot matter to E1's margins, which are
above 7.6 targets, but it matters for any later, closer comparison.

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
    baseline. That is consistent with steering to the decoy, which was not measured. Because the
    decoy captures the wey, 0.03 overstates the value of the information; the no-information
    comparisons are the constant probe (0.05) and the best blind search (0.65);
  - with a constant scent it falls to 0.05;
  - the blind baselines (constant, random walk, wall-follower) score the same under the constant
    probe, as a blind controller should;
  - the best blind search (wall-following) reaches 0.65.
- **Relocation works:** 1 023 of 1 024 episodes reached at least two targets. The one failure,
  world 996 201 898, reached none, while the oracle reached 8 there.
- **The oracle is a reference, not a per-world ceiling:** the navigator beat it on 15 gate worlds
  and fell short on 121.
- **Steering gain matters.** The winner is effectively bang-bang: it applies
  clip(8192 × (left − right), −1, 1), which saturates for a current difference above about 0.00012.
  - Restricted to k ≤ 32, stereo steering keeps 64% of the oracle's count. That is far above all
    four gating baselines, K included (5.62 against at most 0.94); the best blind baseline is
    0.65.
  - The k ≤ 32 bound is an assumption from design review, not a measured property of N2 brains.
    What gain an evolved brain reaches is for 04a to measure, against the curve above.
- **Memory on the stereo mean (M-avg) is a weak navigator here** (2.20, 25% of the oracle). That
  is a statement about this tuned one-step-memory family, not about temporal comparison in
  general.

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
  As far as the records and the session's command order show, no gate world was evaluated before
  the gate. The indices the gate used, 1 000-2 023, are past every touched world either way.
- **The mirrored arm's leg statistics** rest on its 29 arrivals, so they are strongly conditioned on
  rare successes.
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
