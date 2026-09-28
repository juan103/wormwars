# E1: the positive control for navigation

**Status:** passed; on the `roadmap` branch, awaiting the owner's go for main · **Run:** 2026-09-28 ·
**Commit:** bound at `eb0b781` (pilot), gate at `a73a67d` · **Compute:** 353.8 s of an 8 GPU-hour
cap, one RTX 5080

Experiment 02's evolved champions foraged well by circling and slowing near food, without steering
to it. Before evolving a navigation module (04a), E1 asks whether the task can be done at all with
the declared body and sensors. Can a *scripted* navigator reach **moved targets** on **unseen
layouts**, better than simple blind search, and **because of the cue**? It is the first experiment in
this series whose pre-registration was public before its formal run.

## The answer, in brief

- **The registered outcome, in the wording fixed in advance:** *"E1 positive control: passed"*. No
  rule failed.
- **Reliability:** 1 023 of 1 024 gate episodes reached at least 2 targets.
- **The navigator** (stereo steering at one speed) reached **8.68 targets per 300-tick episode,
  98.7% of an oracle** that steers at the true target.
- **Blind search** reached at most 0.65 (the wall-follower); level kinesis, which reads the scent,
  0.94.
- **Uses the cue:** with the scent read at a mirrored decoy, the navigator fell to **0.03**, and to
  0.05 with a constant scent.
- **Gain matters.** The winner is effectively bang-bang. With the gain limited to k ≤ 32 (an
  assumption about what a brain might reach, not a measurement), stereo steering reached 5.62, 64% of
  the oracle.
- **What it does not show:** anything about evolved brains. That is 04a. It covers a localised,
  relocating source only: no trails, junctions, occluding walls or colonies.

Details and every number: [`RESULTS.md`](RESULTS.md), including its dated Corrections section.

## Design

**Task N:**
- one wey per world in a 24-cell arena, with energy off;
- a sensing-only scent source, a truncated Gaussian, that jumps to the next position in a fixed
  per-world sequence when the head comes within 1.5 cells;
- the score is the number of targets reached in 300 ticks.

**Controls:**
- stereo steering (S-const);
- memory on the stereo mean (M-avg);
- level kinesis (K);
- constant motion, a persistent random walk, and a wall-follower using the collision inputs;
- an oracle, as the ceiling.

**The pilot,** applying registered rules mechanically:
- it chose the scent width (σ = 6, flagged, as expected before registration);
- it measured the own-body collision level, and generation-0 random N2 brains;
- it tuned every control on 256 tuning worlds, and picked the navigator.

**The gate:** 1 024 unseen worlds, used once. There are three rules, all required:
- reliability;
- beating each gating baseline by a paired one-sided 95% lower bound above 0.5;
- a cue test, (0.5 × real − mirrored) ≥ 0.

Fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) (v6), reviewed in five rounds by Astra 6 and
Fable 5.1 before binding.

## Caveats and corrections

- **σ = 6 is flagged:** 0.878 of leg starts had usable scent, against the registered 0.90. It was
  disclosed before registration.
- **Development exposure,** disclosed in the pre-registration's §7. A smoke run and a debug run
  touched early pilot and tuning worlds, before every stage was offset to index 1 000.
- **Several tuned winners sit at a grid edge,** so the blind baselines may be under-tuned. E1's
  margins are above 7.6 targets.
- **Results corrections (D101):** mixed clocks in the compute figure, K mislabelled as blind, and
  three claims narrowed.
- **The counts are exact integers,** but CUDA default mode does not guarantee repeatable
  trajectories, so no exact replay is claimed. Every per-world count and the full event tables are
  committed.

## Files

| File | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The registration (v6) and its review history |
| [`RESULTS.md`](RESULTS.md) | Results, with dated corrections |
| [`freeze.json`](freeze.json) | The pilot: every measurement, every grid point's mean, and the rule-chosen values |
| [`gate.json`](gate.json), [`gate_events.npz`](gate_events.npz) | The gate: rules, means, per-world counts, full event tables |
| `pilot-started.json`, `gate-started.json`, [`compute-record.json`](compute-record.json) | Start markers and compute |
| [`development-records/`](development-records/) | Smoke runs' records, and the guarded smoke run on the binding commit |
| [`../../scripts/e1.py`](../../scripts/e1.py) | The runner (`REGISTERED` holds every number) |
| [`../../wormwars/e1/`](../../wormwars/e1/), [`../../wormwars/world.py`](../../wormwars/world.py) | Task N and the controls |
| [`../../docs/E1/DESIGN.md`](../../docs/E1/DESIGN.md) | The agreed design (v2.1) |

## Reproduce it

The setup is in [the main README](../../README.md#how-to-reproduce). The runner refuses a formal
stage anywhere but the registered environment: an RTX 5080, Python 3.13, the pinned torch and
numpy, a clean tree and a pushed HEAD.

```
git worktree add ../wormWars-e1 a73a67d
cd ../wormWars-e1
python scripts/fetch_connectome.py
python scripts/e1.py pilot --smoke      # tiny sizes, ids outside E1's ranges, runs/e1-smoke/
python scripts/e1.py gate --smoke
```

- **Running the formal stages yourself** writes new outputs, and the committed ones already exist.
  Remove the stage markers and outputs from your copy first. Your result is then a replication,
  with its own record; it does not replace this one.
- **Compare against:** `freeze.json`'s tuned means, and `gate.json`'s rules and per-world counts.

## Extend it

- **04a:** evolve an N2 navigator on Task N, with its own pre-registration (ROADMAP.md, "E1 /
  04a"). It should measure the champions' effective steering gain against the gain curve in
  RESULTS.md.
- **Line-shaped sources, bends and junctions:** the checks E3 begins with.
- **Tune the blind baselines on wider grids** before any closer comparison.

## Record

Decisions D077-D078 (the design), D094-D099 (the pre-registration and its five reviews), and
D100-D101 (the results and their review). The reviews are in `docs/reviews/*E1*`.
