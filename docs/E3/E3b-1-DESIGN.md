# E3b-1's design: the E3 gate in mazes (v1, 2026-10-03, for review)

**Status: v1, for both reviewers.** E3b-1 is confirmatory. A pre-registration follows this design, is
reviewed, bound and pushed before any run (rule 2).

**It builds on:**
- E3b-0's results, published on main (D180; `experiments/E3-ab-organism/E3b-0/RESULTS.md`);
- the E3b design v2 (`docs/E3/E3b-DESIGN.md`, D173).

**The owner's decision on the schedule (2026-10-03, D181):** both reviewers' training proposals run side by
side in the trails arm, with a check at generation 125.

## 1. The question

Does joint tuning of the maze-ready seed improve the colony's shuttling in branching mazes with shared
trails, and does the tuned colony use the trails more than the seed does? **"Better" means the tuned colony
against the frozen seed** (E3b design v2), on untouched mazes, under identical mechanics.

E3b-1 makes **no claim of directional trail use**: behavioural polarity was not shown in E3b-0.

## 2. Fixed by E3b-0 (not reopened)

- **The task:**
  - 5 × 5 tree mazes (Wilson's algorithm), a colony of 8 weys on up to 4 spawns, H = 2 400 ticks;
  - A and B at dead ends, with per-wey goals;
  - supercover movement with sliding, occlusion, and crowding off.
- **Trails:** linear; μ 0.01, λ 0.02, δ 0.05, d₀ 1.142.
- **Scents:** σ 3 path cells, zero beyond 9. The nose scale is 0.35.
- **The seed:** E3a's engineered E with W2 (a one-sided wall reflex, resting turn +0.4, D176), on the
  silent carrier.
- **The peer controls:**
  - own, peers, none and scramble;
  - replay, from a donor at episode + 1000 with different endpoints, its coefficient frozen from a
    selection pre-pass. Each champion's coefficient is re-derived on its own selection-maze pre-pass,
    because its exposure differs (Fable).
- **The peer measure:** the first-B time of later discoverers, the mean of order statistics 2-8.
- **The power:** a calibrated one-sided test (t, with the exact sign-flip test beside it), 5%.
  - At 12 runs and a CV of 0.282 it detects 0.20-0.22 of the seed's mean; at 16 runs, 0.17-0.19
    (`power.json`).
  - The run-level CV in mazes is unknown until these runs.

## 3. The arms and the schedule

**T, tuned with shared trails: 16 runs.**
- **T-A** (Astra's proposal): 8 runs of 125 generations, 16 mazes per genome per generation.
- **T-F** (Fable's proposal): 8 runs of 300 generations, 8 mazes per genome, with a champion also taken at
  generation 125.

**N, tuned without trails** (the access mode "none": trails are laid but not sensed): 6 runs of 125
generations at 16 mazes. It is secondary and descriptive; the owner's ceiling does not allow more.

**The GA:** E3a's Stage 3 (population 32, elites 3, truncation 8).
- **Mutated:** every grafted edge and grafted neuron (τ and bias) of E's modules and selector, except the
  relays' τ and bias, at 0.25 × the base sigmas.
- **Frozen:**
  - W2's two neurons and their 16 output edges;
  - the carrier, so the worm block stays silent;
  - E3a's relay settings.
- **Every run starts from the seed.**
- **The fitness:** a genome's colony mean of visits per wey, averaged over its training mazes, the same
  mazes for every genome of a generation (common random numbers).
- **Training mazes** come from a new block, drawn per generation as in E3a.

**The champions:**
- **Selection:** at generation 125 (every run) and at the end (T-F's generation 300), the top 4 genomes by
  their last 5 generations' training fitness are scored on 128 validation mazes. The best validation mean
  is the champion; ties go to the lower index.
- **Why this departs from E3a:** E3a validated every checkpoint's whole population, which would cost about
  12 GPU-hours here.
- **The champions to read:**
  - T-A: 8, at generation 125;
  - T-F: 8 at generation 300, and 8 at generation 125;
  - N: 6.

## 4. The readings

**The registered gate (G):**
- **The champions:** the 16 final T champions (T-A at generation 125, T-F at 300), pooled.
- **The statistic, per run:** the champion's mean visits per wey on the test mazes, with shared trails,
  minus the seed's on the same mazes.
- **The test:** a one-sided t-test on the 16 differences.
- **The labels:**
  - "better" if p ≤ 0.05 and the exact sign-flip test agrees;
  - "worse" if the mirror test passes;
  - otherwise "unclear".
- **The margin** is an open question (§6).

**Secondary readings (registered, labelled underpowered where they are):**
- **S-gen, the effect of generations at 8 mazes:** T-F's 300 against its own 125 champion, paired within
  the 8 runs.
- **S-worlds, the effect of mazes per genome at 125 generations:** T-A against T-F's 125 champions, 8
  against 8, independent runs, descriptive. The fourth cell (300 generations, 16 mazes) is not run.
- **S-trail, does tuning raise trail use?**
  - Each T champion is played with trails on and off. Its (on − off) is compared with the seed's
    (on − off), over the 16 runs.
  - The N arm's (on − off), and T against N with trails on, are descriptive.
- **S-peer, on the 16 T champions:**
  - shared − own on the peer measure;
  - replay − own and scramble − own on the later-leg rate.
  - These are reported beside the seed's values in E3b-0.

**Descriptive:**
- the training curves;
- the champions' component tests at E3b-0's levels, and whether their latch survives (E3a's
  classification);
- each champion's share of inputs above 1.0;
- the run-level CV, read against the power assumption.

## 5. The compute

From E3b-0's timing (0.057 s per tick at 4 096 worlds, assumed linear in worlds), at H = 2 400:

| Item | GPU-hours |
|---|---|
| T-A: 8 × 125 × 16 mazes | 4.7 |
| T-F: 8 × 300 × 8 mazes | 5.7 |
| N: 6 × 125 × 16 mazes | 3.5 |
| Training | 13.9 |
| With the 25% reserve | 17.4 |
| Validation (about 30 champion selections × 4 genomes × 128 mazes) | about 0.2 |
| Test evaluation, on and off, peer controls with replay donors, for about 31 organisms × 256 test mazes | about 0.5 |
| The owed GPU equivalence leg and a retiming at the actual compositions (T-A 4 096 worlds, T-F 2 048, N 3 072) | about 0.3 |
| **Total** | **about 18.4** |

About 27.4 hours remain of the owner's E3b ceiling (30 less E3b-0's 2.62). **The plan's limit of 24 hours
holds.**

**The retiming comes first.** If the actual compositions project above 24 hours, the cut order is:
- N to 4 runs;
- then T-F's maze count stays and its generations fall to 250;
- then the owner is asked.

## 6. Open questions for the reviewers

1. **The pooled gate.** Is pooling two schedules into one 16-run gate sound, given that its mixture of
   run distributions may be bimodal? Or should the gate be T-A alone, with only 8 runs? Is the exact
   sign-flip agreement the right guard?
2. **A margin for "better".** Should there be one, for example 0.10 × the seed's mean, or the MDE (0.22)?
   What is a meaningful improvement when the seed's visits are mostly the reflex's (E3b-0: +1.09 over W2
   alone, of 5.78)?
3. **The champion rule.** The top 4 by recent training fitness, on 128 validation mazes, at two points
   only. Is that adequate, given the between-maze CV of 0.74?
4. **N as "none" access, not deposit off.** With "none" the colony still lays trails it cannot sense.
   For the seed's behaviour this is identical; is it right for the arm?
5. **S-trail's measure:** visits per wey, or the later-leg rate (E3b-0's trail measure)?
6. **Is anything missing:**
   - memory assays at D = 141;
   - a positive control for tuning in mazes;
   - the no-trails-from-start arm of the E3b design v2, which N approximates?
