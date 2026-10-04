# E3b-2: where E3b-1's gain comes from (exploratory)

**Status (2026-10-04):** run at 3.00 of 5 GPU-hours. The results draft is under review by both reviewers
(`RESULTS.md`).

**The question:** E3b-1's tuned colonies beat the frozen seed. What do they use to do it, and does the
engineered selector still switch in the maze?

**How it asks it.** On 256 fresh mazes, with E3b-1's 16 final T champions, N's 4 and the seed:
- **attribution:** the seed/champion hybrids over four functional parameter groups (with shared trails and with
  none), and over three side groups;
- **lesions:** the latch clamped at each own state, the visit input cut, the gate cut, the nose inputs removed,
  the reflex held at rest, and the outputs silenced;
- **latch recording** in the maze;
- **genome descriptives.**

**The frame:** a hand-built circuit on a silent worm; nothing here is about worm behaviour. It evolves nothing.

## Where things are

- **The plan:** `docs/E3/E3b-2-PLAN.md` (draft 3).
- **The decisions:** D193-D196.
- **The reviews:** `docs/reviews/20261004-E3b-2-*`.
- **The code:**
  - `wormwars/e3/attribution.py`: the partitions, hybrids, Shapley values, lesions and latch recorder;
  - `scripts/e3b2.py`: the runner.
- **The records:** this folder:
  - the stage records `*.json`;
  - the per-maze chunks `chunks/*.npz`, each with its full specification;
  - `summary.json`;
  - `compute-record.json`.

E3b-1's genomes stay local (`runs/e3b1/genomes`), hash-checked at load.

## Reproduce it

```
python scripts/fetch_connectome.py
python -m pytest tests/test_e3b2_attribution.py tests/test_e3b2_runner.py
python scripts/e3b2.py project --smoke --device cpu      # then attribution, lesions, latch, report (stand-in champions)
python scripts/e3b2.py summary                          # rebuild summary.json from the committed chunks (CPU)
python scripts/e3b2.py project --device cuda            # formal: needs E3b-1's local genomes
```
