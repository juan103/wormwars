# E4s: a hand-built stereo module grafted onto N2

**Status (2026-10-01):**
- **E4s-0, the diagnostics,** has run and been reviewed (both "fix", text only; corrected, D147).
- **E4s-1, the graft under evolution,** is pre-registered (`E4s-1/PREREGISTRATION.md`).
  - It was bound at 023267d and public before any stage ran, and amended once before any stage ran
    (D150, D152).
  - Its formal run started at 13:22 that day.
  - **The three gates passed:**
    - re-qualification: 5.19 targets per episode, lower bound 5.11;
    - the CUDA state check: a largest difference of 2.7 × 10⁻⁶;
    - the score check: identical counts in every world for all 24 champions.
  - Training is under way. The plan is
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

- **For 42 of 47 champions, a valley along the stereo-gain direction.** Adding k(L − R) to a
  champion's own turn command:
  - k ≤ 1 changes little (at most +0.27 targets per episode);
  - k = 2-16 harms most champions. The median across champions is 1.57 at k = 2 and 0.69-0.83 at
    k = 4-16, against 2.19 at k = 0;
  - the tested k = 32, 64 and 256 help all 47 (median 5.75, 7.03 and 8.38).

  Five champions are never harmed. This is one external intervention, not what mutations produce.
- **The champions' differential response falls from the sensory neurons to RIA, then levels off;**
  the common-mode response stays four to seven times larger.
- **A 4-neuron comparator (L1) qualifies, with the carrier's help:** 5.18 targets per episode
  (lower bound 5.10), and it uses the left-right difference.
  - It needed the carrier's constant turn command of 0.2: the same module scored 3.86 in tuning
    without it.
  - Its gain of about 36 is capped by the weight bounds.
- **Grafted onto random N2, it is used at generation 0** in 16 of 16 simulated populations, so E4s-1
  proceeds on random N2. On 04a run 2 it costs the champion 1.76 targets per episode against mean-only
  input to the module.
- **Mutational robustness is bimodal.** At 0.25× 02's scales, the median mutant keeps 78%, but 122 of
  256 score below 0.7. At 1×, 195 of 256 score 0.

## Reproduce it

```
python scripts/e4s0.py project
python scripts/e4s0.py sweep
python scripts/e4s0.py attenuation
python scripts/e4s0.py ladder
python scripts/e4s0.py populations
python scripts/e4s0.py robustness
```

- **These are the commands of the original run.** Each stage runs once. Its record must be
  committed and pushed before the next stage starts.
- **In this checkout the stages refuse to run,** because their records exist. To reproduce:
  - use a separate clone with `experiments/E4s-stereo-module/E4s-0/` emptied, and the compute files
    under `runs/e4s0/` absent;
  - or run with `--smoke` for toy sizes in `runs/e4s0-smoke`.
- `python scripts/e4s0_summary.py` re-derives `summary.json` from the records, on the CPU.
- **Requirements:** the fetched connectome, and E2's and 04a's local champion genomes, which are not
  published (rule 1).
- **No exact repeat is claimed.** E4s-0 did not run in `replay_mode()`, so CUDA results may differ in
  detail on a rerun (`docs/REPRODUCIBILITY.md`). The k = 0 check reproduced the unwrapped counts
  exactly within this run.

## Extend it

- **E4s-1** grafts `E4s-0/module.json` onto random N2 and evolves the whole brain (pre-registered,
  running).
  - **The arms:** M (main), N (no added output) and R (random signs) are confirmatory; F0 (frozen), U
    (02's mutation scale), S (half the module's scale) and C2 (04a run 2) are descriptive.
  - **The readings** come from `scripts/e4s1_report.py`.
- **Open questions:**
  - why intermediate stereo gains hurt the champions;
  - whether temporal sensing would avoid the valley;
  - whether a ring helps when the scent drops out.
