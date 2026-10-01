# E4s: a hand-built stereo module grafted onto N2

**Status (2026-10-01):** E4s-0, the diagnostics, has run and is under results review. E4s-1, the
graft under evolution, is next; it will be pre-registered. The plan is
[`docs/E4s/ROADMAP-PROPOSAL.md`](../../docs/E4s/ROADMAP-PROPOSAL.md) (v2.1, adopted, D144). The
owner set a ceiling of 96 GPU-hours for all of E4s.

## Why

E2d found a "non-stereo plateau": none of E2's and 04a's 47 distinct champions meets the "uses the
left-right difference" criterion, and no tested optimizer change left the plateau. E3 needs a
navigator. The owner asked for stereo steering to be built by hand and settled into N2 by evolution,
ahead of the roadmap's plan (D139).

**Stereo sensing is a game-design choice** (the owner's option (a), D144). The real worm steers by
temporal sensing. In E4s the stereo computation lives in a small graft with its own noses and its
own path to the motors, outside the N2 mask.

**How the plan changed:**
- **The first designs used a fly-style ring attractor.** They rested on a literature report that was
  not a checked review (corrected, D143).
- **A real literature review** (`docs/reviews/20261001-literature-review/`) found that a small
  comparator suffices on a smooth scent, and the plan moved to one. The ring is deferred to a task
  that needs memory.

## E4s-0: diagnostics (exploratory; run 2026-10-01; 0.23 GPU-hours)

[`E4s-0/RESULTS.md`](E4s-0/RESULTS.md), from the plan [`docs/E4s/E4s-0-PLAN.md`](../../docs/E4s/E4s-0-PLAN.md)
(v2; reviews in `docs/reviews/20261001-E4s-0-plan/` and `…-E4s-0-code/`).

- **A valley along the stereo-gain direction.** Adding k(L − R) to the champions' own turns:
  - small k adds at most +0.08 targets per episode (one champion +0.19);
  - k = 2-16 harms 42 of 47 champions (median score 2.19 → 0.69-0.83);
  - k ≥ 32 helps all 47 (median 5.75 at 32, 8.38 at 256).
- **The champions' differential response shrinks at every stage,** from the sensory neurons to the
  turn neurons, while the common-mode response stays several times larger.
- **A 4-neuron comparator (L1) qualifies:** 5.18 targets per episode on the carrier (lower bound
  5.10), and it uses the left-right difference.
- **Grafted onto random N2, it is used at generation 0** in 16 of 16 simulated populations, so E4s-1
  proceeds on random N2.
- **It survives mutation at 0.25× 02's scales** (the median child keeps 78%), **but not at 1×** (0%).

## Reproduce it

```
python scripts/e4s0.py project
python scripts/e4s0.py sweep
python scripts/e4s0.py attenuation
python scripts/e4s0.py ladder
python scripts/e4s0.py populations
python scripts/e4s0.py robustness
```

- **Each stage runs once.** Its record must be committed and pushed before the next stage starts.
  Add `--smoke` for toy sizes in `runs/e4s0-smoke`.
- **Requirements:** the fetched connectome, and E2's and 04a's local champion genomes, which are not
  published (rule 1).
- **CUDA results repeat exactly only on the same GPU and environment, at the recorded compositions**
  (`docs/REPRODUCIBILITY.md`).

## Extend it

- **E4s-1** grafts `E4s-0/module.json` onto random N2 and evolves the whole brain. The arms are main,
  no added output, a random graft of the same shape, frozen, uniform mutation, and a case study on 04a
  run 2.
- **Open questions:**
  - why intermediate stereo gains hurt the champions;
  - whether temporal sensing would avoid the valley;
  - whether a ring helps when the scent drops out.
