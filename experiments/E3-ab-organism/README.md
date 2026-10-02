# E3: the minimal A/B organism

**Status (2026-10-02):** E3a's design is agreed (`docs/E3/DESIGN.md` v2.4, D163), and its
pre-registration is drafted, for review (`E3a/PREREGISTRATION.md`). Nothing has run.

## What it asks

Can two hand-built stereo modules, one per scent, be composed into an organism that shuttles between
two sources? A one-neuron latch remembers which source is next and gates which module steers. With
the modules frozen, can evolution find such a selector?

**The frame:** stereo sensing is a game-design choice. The organism is a hand-built circuit on a
silent worm, outside the N2 mask. Nothing here is about worm behaviour.

## Its parts

- **E3a, the shuttle:** one wey, an open arena, two fixed sources. This folder's first experiment.
- **E3b:** trails, branching mazes and the colony. It holds the roadmap's E3 gate.
- **E3c:** the assembly comparison.

**The owner's ceilings:** 30 GPU-hours for E3a, and about the same for each of E3b and E3c (D159).

## Where things are

- **The design and its five review rounds:** `docs/E3/DESIGN.md`; `docs/reviews/20261002-E3-design*/`;
  D156-D163.
- **The geometry check:** `scripts/e3_geometry_check.py` and `docs/E3/geometry-check.json`.
- **The module it builds on:** E4s-0's L1 (`../E4s-stereo-module/E4s-0/module.json`).
