# E3a results: the shuttle

Status: **first draft, for review**, 2026-10-02.
- **Its pre-registration:** `PREREGISTRATION.md`, bound at 989da99 (D165), with Amendment 1 (D167),
  added before any stage ran.
- **Every number below** comes from the committed stage records in this folder: `evaluate.json` and
  the others. They are collected in `summary.json` (`scripts/e3a_summary.py`).

**The frame:** stereo sensing is a game-design choice. The organisms are hand-built or evolved circuits
on a silent worm, outside the N2 mask. Nothing here is about worm behaviour or its circuits. E3a does
not meet the roadmap's E3 gate (branching mazes); that belongs to E3b.

## What ran

- **When:** every registered stage, once, from 12:20 to 18:20 on 2026-10-02, on one RTX 5080. Every
  record was committed and pushed before the next stage began.
- **Compute:** 5.97 GPU-hours (21 490 timed seconds), against the owner's cap of 30.
  - The projection planned 9.26 hours, including its 25% reserve, so no reduction applied.
  - B-task trained its full 800 generations, and every arm its 8 runs.
- **No stage stopped. Every end-of-run assertion passed.**

| Stage | Result |
|---|---|
| G-E, the engine check | passed. On the CPU, every case was identical to the engine at 989da99 (Task N, foraging and its rollout score, E4s-1's graft and its two probes). On the GPU, E2's GA reproduced E2's committed hashes in all 26 generations of all 8 runs |
| G0, the controls | passed |
| G1, the engineered organism | passed |
| Training | Stage 2's GA 0.88 h; random sampling 0.87 h; Stage 3 1.47 h; B-task 2.36 h |

## The gates

**G0** (1 024 gate worlds; confirmed visits per 600-tick episode):

| Control | Mean | Requirement | |
|---|---|---|---|
| S-oracle | 19.18 | at least 0.6 of the straight-run reference's mean, 18.71 | passed |
| S-shuttle, k 8192 | 19.01 | at least 0.5 of S-oracle | passed |
| L1-switch | 13.65 (lower bound 13.46) | lower bound at least 0.5 of S-shuttle at k 32 (15.82) | passed |
| Constant motion | 0.55 (90th-percentile world 1) | mean at most 0.25 of L1-switch's, 90th-percentile world at most 0.5 | passed |
| Random walk | 0.63 (90th-percentile world 2) | the same | passed |
| The carrier's circle | 0.68 (90th-percentile world 1) | the same | passed |

S-oracle exceeds the straight-run reference. That is consistent with the reference being a model, not
a bound: the engine turns and moves in the same tick (§5).

**G1** (the engineered organism E; the same gate worlds):
- **E's lower bound** is 13.08, against the 0.8 × 13.65 required. Passed.
- **E against its controls:** "uses" (E2d's rule).
  - Against the no-latch control (both modules always on): +5.21 (95% 5.02 to 5.39).
  - Against one module: +11.42 (11.27 to 11.58).
- **Its component tests passed:**
  - the active module's K_D was 31.6 to 35.6 at every level and state;
  - the inactive module's |K_D| was 0.060 to 0.067;
  - switching and startup passed.
- **Its memory assays passed:**
  - the clamp assays: the first entry was into the clamped goal in 96.5% (A) and 96.9% (B) of the 256
    assay worlds;
  - settable and the hold;
  - the reset: 231 of 256 worlds.

**E's calibration** (256 calibration worlds):
- **D:** E's median leg after the first visit is 39 ticks.
- **E's level** at a visit lasts 7 ticks at the median. E's assays use 2 ticks by design.
- **Its release test,** reported, passed from both states.

## The registered readings

**S2-a: "evolution found a working selector in 1 of 8 runs, not reliably."**
- The working champion is run 4's. Its class is "bistable, not a latch" (see below).
- The other 7 runs' champions are monostable, with "no memory".

**S2-b: "unclear."**
- **The test:** the GA's champions against random sampling's, paired by run.
- **The result:** −1.49 visits (90% −2.98 to +0.24).
- The point estimate favours random sampling.
- **Why "unclear":** the interval includes 0 and is not within ±0.5. So none of "evolution better",
  "random sampling better" or "as good" applies.
- **The fixed description:** evolution from a start near the ungated pair, with untied mutation,
  against a blind search over the whole range with the comparator pairs permanently tied. It does not
  isolate the search algorithm.

**S2-c:** for both censuses, "none of 1024 draws passed the screen and the full check; that rate is
below 0.0036".
- **The screen** asked for 10.45 visits on the 16 census worlds (0.8 × E's 13.06).
- **The GA distribution:** its 1 024 draws averaged 7.15, with a best of 9.81.
- **Random sampling's distribution:** 2.83, with a best of 9.81.
- The GA distribution's count is 0, so "answered at generation 0" does not apply.

**Stage 3 (descriptive): "better."**
- **The test:** joint tuning, each run's champion against its own Stage 2 champion.
- **The result:** +2.36 visits (90% 1.32 to 3.52).

**B-task (descriptive): "worse."**
- **The test:** its champions against Stage 3's.
- **The result:** −3.73 visits (90% −5.96 to −1.55).
- **The fixed description:** the same neurons, inputs and outputs, not the same trainable capacity.
  B-task started with weak sensing and no latch structure.

## The champions on the test worlds (descriptive)

The 256 test worlds were read only in stage 14.

| Organism | Test mean | Structure | Memory class | Working |
|---|---|---|---|---|
| E (engineered) | 12.79 | bistable | (latch, by G1) | (the reference) |
| GA run 0 / 1 / 5 / 6 / 7 | 7.29 / 7.91 / 8.10 / 8.09 / 8.10 | monostable | no memory | no |
| GA run 2 | 11.20 | monostable | no memory | no (clamp assays 82.0% and 92.2%) |
| GA run 3 | 12.12 | monostable | no memory | no (clamp assays 87.5% and 89.8%) |
| GA run 4 | 14.98 | bistable | bistable, not a latch | **yes** |
| Random sampling runs 0, 1, 2, 4, 5 | 11.43, 11.02, 11.83, 10.81, 11.97 | bistable | latch | yes |
| Random sampling run 3 | 10.75 | monostable | slow trace | yes |
| Random sampling run 6 | 10.25 | bistable | latch | no (lower bound 9.96 < 10.23) |
| Random sampling run 7 | 11.66 | bistable | bistable, not a latch | yes |
| Stage 3 runs 0, 1, 5, 6 | 8.92, 8.78, 8.53, 9.54 | monostable | no memory | no |
| Stage 3 run 2 | 14.68 | monostable | no memory | yes |
| Stage 3 run 3 | 15.98 | bistable | bistable, not a latch | yes |
| Stage 3 run 4 | 15.77 | bistable | bistable, not a latch | yes |
| Stage 3 run 7 | 14.50 | monostable | no memory | no (clamp assays not applicable) |
| B-task runs 0-7 | 6.89 to 9.88 | — | (no assays) | — |
| B-shared (engineered) | 12.30 | bistable | latch | — |
| L1-switch | 13.13 | — | — | — |

"Working" needs a test lower bound of at least 0.8 of E's test mean (10.23), and both clamp assays
passing (§6).

**"Bistable, not a latch" here means a leaky gate, not a lost memory.**
- In all four such champions (GA run 4, random sampling run 7, Stage 3 runs 3 and 4):
  - q is settable both ways;
  - after the 580-tick hold, q is still at its fixed point;
  - the active module's K_D is unchanged.
- They fail the hold only on its gate condition: the inactive module's |K_D| must be at most 0.1 of the
  active one's. In each, the larger of the two states' ratios is 0.18 to 0.48 (`summary.json`,
  `hold_inactive_ratio`).
- For a latch the bound text requires both. These are memories that hold, behind gates that leak.

**Memory-less champions can still score.**
- GA runs 2 and 3 score 11.20 and 12.12 with a monostable q that fails the release test.
- Stage 3 run 2 scores 14.68 and passes the clamp assays, yet its q also fails the release test.
- The modules' own neurons stay fast in every Stage 3 champion: comparator τ ≤ 2.3, nose τ ≤ 2.82.
  Where else its memory might live, or whether behaviour substitutes for it, was not examined. "No
  memory" is operational: these assays failed (§6).

**Every champion uses both modules' stereo.**
- With one module's noses fed their mean, E drops from 12.79 to 0.85 (A's noses) and 1.63 (B's).
- The selector champions drop to between 0.07 and 2.05.
- Stage 3 run 7 is the exception: it keeps 4.14 and 5.80. Two of its noses (A_NR, B_NR) evolved
  τ of 2.39 and 2.82, against 0.5 to 0.7 elsewhere. Whether part of its steering uses something other
  than the left-right difference was not examined.

**E against its ablations on the test worlds:**
- the no-latch control: +4.83 (95% 4.46 to 5.21);
- one module: +11.05;
- q clamped to 0: +11.45.

**Generation 0** (the first 64 census draws from the GA distribution):
- turn offsets at zero nose difference are at most 2.1 × 10⁻⁶;
- A's K_D with q at 0 is 9.4 to 35.5.

Over training, the Stage 2 runs' checkpoint candidates reached offsets of 0.40 to 0.61, as the design
expected once mutation is untied.

## What E3a shows, and what it cannot

- **Two engineered stereo modules compose.** A one-neuron latch with saturation gating shuttles between
  two sources at 12.79 visits per episode on the test worlds. That is 97% of L1-switch's 13.13 on the
  same worlds, where L1-switch is fed the goal's scent directly. Removing the latch costs 4.83 visits.
- **Evolution from a near-ungated start rarely built a working selector** (1 of 8). A blind search over
  the whole range, with the pairs permanently tied, found working selectors in 7 of 8 runs. Their
  difference in score is "unclear".
  - The two arms differ in their distributions, and in random sampling's permanent tie as well as in
    the search. E3a cannot say which of these explains the difference in working selectors.
- **Joint tuning added 2.36 visits** over the Stage 2 champions. Four tuned organisms beat E (15.98,
  15.77, 14.68, 14.50). A dense controller of the same neurons did worse than Stage 3, but it is not matched in
  trainable capacity.
- **It cannot show:**
  - anything about worm behaviour;
  - mazes, trails or colonies (E3b);
  - whether modularity pays (E3c);
  - where the memory of the monostable high scorers lives.

## Deviations

1. **The implementation tests touched registered worlds before the run (D166).** They ran E on 16
   assay worlds and 8 calibration worlds with the evaluation seed, and an exploratory check ran 16
   calibration worlds.
   - Nothing depended on it: E and every rule were bound.
   - E's later registered calibration on all 256 worlds gave D 39 and a level of 7 ticks, as the peek
     had.
2. **Amendment 1 (D167)** settled one conflict in the bound text (§6 against §8 on module skill) and
   several places it left open, before any stage.
3. **No confirmation round after the code review.** Both reviewers said "fix then run". The runner was
   then substantially rewritten to take their fixes, and the run started without a further round, on
   that verdict and at the owner's request to use the GPU (D167). The fixes are listed in D167, each
   with its test.

## Reproduce it

```
python scripts/e3a.py project        # then g-e, g0, g1, calibrate-e, census, train --batch 1..4,
                                     # champions-2, champions-3, calibrate, evaluate (in the order of §5)
python scripts/e3a_summary.py        # summary.json from the committed records
```

- **G-E's CPU leg** compares against `development-records/equivalence-reference.json`, made at 989da99 by
  `scripts/e3_equivalence.py`.
- **Exactness:** CUDA results are exact only on the same GPU and environment, at the same compositions
  (rule 6). Every record states its composition.
