# 04a: an evolved N2 navigation primitive

**Status:** "04a: passed" (the wording fixed in advance); results written, review pending · **Run:**
2026-09-28/29 · **Registration:** bound at `e3d68be` after five review rounds, public before the run ·
**Compute:** 2.91 of a 6 GPU-hour cap, one RTX 5080

E1 showed that a scripted navigator can steer to a moving scent with this body and these sensors.
04a asks whether **evolution**, starting from random weights on the real *C. elegans* wiring (N2), can
produce a brain that does it: reaches moved targets on unseen layouts, better than blind search,
because of the cue, and better than where it started.

## The answer, in brief

- **Yes, in 8 of 12 shaped runs** (the bar was 6), and in all 4 runs trained without the shaping
  bonus. The four failures missed only the reliability rule, narrowly (70-77% of episodes with at
  least 2 targets, against 80%).
- **The champions follow the cue:** with the scent mirrored they go to the decoy and reach almost
  nothing (about 0.15 targets), and with a constant scent they reach about 0.2.
- **But they are slow navigators:** about 2.1-2.8 targets per 300-tick episode, 23-32% of an oracle,
  against 8.7 for E1's scripted navigator; their paths are indirect, and they perform like a stereo
  steerer with a small gain (k about 4).
- **Shaping was not needed:** the unshaped arm did as well, and produced the best champion.
- **What it does not show:** that N2's wiring helps (there is no null-graph comparison), or how well
  a better optimizer could do (that is E2).

Details and every number: [`RESULTS.md`](RESULTS.md).

## Design

- **Task N** exactly as E1 ran it (one worm, a scent that jumps when reached, 300 ticks).
- **16 evolutionary runs** of N2 brains, 1 000 generations each, with experiment 02's optimizer; 12
  with a bounded bonus for closing the distance to the current target (training only), 4 without.
  Runs were batched 8 at a time, each with its own random streams.
- **Champion:** each run's best checkpoint on 256 validation worlds, fixed before the hold-out.
- **The test:** 1 024 unseen worlds, used once, and five rules per run: reliability, beating four
  blind or level-only baselines, being misled by a mirrored cue, being helped by the real cue over a
  constant one, and beating the run's own generation 0.

Fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) (v5), reviewed by Astra 6 and Fable 5.1 in five
rounds (`docs/reviews/*04a*`).

## Files

| File | What it is |
|---|---|
| [`PREREGISTRATION.md`](PREREGISTRATION.md), [`AMENDMENTS.md`](AMENDMENTS.md) | The registration and its (empty) amendments |
| [`RESULTS.md`](RESULTS.md) | Results |
| `projection.json`, `train-A.json`, `train-B.json` | The budget projection and the training records (every generation, every checkpoint) |
| `evaluation.json`, `evaluation-extras.json`, `evaluation_events.npz` | The verdict, the non-gating extras, and the hold-out event tables |
| `*-started.json`, `compute-record.json` | Start markers and compute |
| [`development-records/`](development-records/) | Development runs, the exposure record, the engine-equivalence check, the pilot, the guarded smoke run |
| [`../../scripts/e04a.py`](../../scripts/e04a.py), [`../../wormwars/e04a/`](../../wormwars/e04a/) | The runner (`REGISTERED` holds every number) and the batched evolution |

## Reproduce it

Setup: [the main README](../../README.md#how-to-reproduce). The formal stages refuse to run anywhere
but the registered environment (an RTX 5080, Python 3.13, the pinned torch and numpy, a clean and
pushed tree).

```
python scripts/e04a.py project --smoke          # tiny sizes, smoke ids and seeds, runs/e04a-smoke/
python scripts/e04a.py train --batch A --smoke
python scripts/e04a.py train --batch B --smoke
python scripts/e04a.py evaluate --smoke
```

The genome files are not published (early genomes carry the connectome's weights; D028); the records
hold every genome's hash, and a formal rerun regenerates them. A rerun is a replication with its own
record.
