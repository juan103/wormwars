## 1. Verdict

**Fix then run.** The fixes are five text pins and one code change, and I do not think they need another review round. I ran nothing; everything below comes from reading the plan, `maze.py`, its test, `champions-3.json` and `summary.json`.

What would make E3b-0 misleading or infeasible as written:

1. **The seed rule reopens "highest score picks W2".** §2c compares the two candidates on raw later-leg rate, but each carries its own variant. A seed that only passes with W2 will beat a seed that passes with W0 or W1, because the wall follower does the work.
   - Fix: prefer the less engineered variant first, and use the rate only between equal variants.
   - The 0.25 tie band has no scale; a paired `world_ci` on the difference would be better.

2. **The seed's trail effect is only tested on the selection mazes.** §2b runs up to 14 one-sided tests (7 variants × 2 seeds) and takes the first pass. On the report mazes, criterion 3 only reports the seed's shared − none.
   - If every true effect is zero, the chance of at least one false pass is large.
   - §6's row for a null seed trail effect points back to §2b, so there is no branch.
   - Fix: require the chosen seed's shared − none lower bound above 0 on the report mazes, with a failure row.

3. **The power criterion rests on an unstated assumption that decides the pass.**
   - **The comparison is not named.** Astra's 23.4% is a one-sample figure: (1.645 + 0.842) × 0.267 / √8. If the gate compares two arms with independent runs, the figure is about 33% and criterion 6 fails. State what is paired with what, and the assumed SD of the difference.
   - **The test's size is not checked.** A percentile bootstrap on 8 runs is anticonservative, so simulated power will flatter the design. Report the simulated false-positive rate under the null, and read the minimum detectable effect at a calibrated size.
   - **The variance shape is wrong.** From `summary.json`, the eight Stage 3 test means are 8.92, 8.78, 14.68, 15.98, 15.77, 8.53, 9.54 and 14.50. That is two clusters, not a normal, and four of the eight are below E's 12.79. Simulate from this empirical shape as well.
   - **The CV divides by E's mean.** The champions' own mean is 12.09, which gives 0.282, not 0.267. At a 23.4% against 25% margin this matters.
   - **Nothing E3b-0 measures enters this criterion.** It is CPU-trivial, so run it first; a failure redesigns E3b-1 whatever else happens.

4. **`maze.py` contradicts §1a.**
   - `draw` redraws the walls from the maze stream when placement fails (`maze.py:147-151`). The plan says placement never redraws walls and an infeasible maze raises.
   - `place` draws one A-B pair and returns `None` if that pair has no spawn candidates (`maze.py:134-139`). Feasibility therefore depends on the placement stream, not on the walls.
   - The replay donors use episode index + 1000 on the same walls, so a maze that is feasible at episode 0 can raise at episode 1000.
   - Fix: draw only among pairs that have at least one spawn candidate. Add a test of the (run seed, maze id, episode) keying, and of feasibility across episode indices.
   - The test file only exercises `draw`, with 30 seeds.

5. **Stage A is not rechecked after Stage B.** The maze size and horizon are chosen with pilot constants, then the constants change. Re-evaluate Stage A's conditions 2, 4 and 5 at the chosen constants, with a row in §6 if they fail.

## 2. The v1 items

All of mine are resolved, except that item 6 (variant selection) is reopened by the seed rule above. Astra's are resolved except these, all minor:

- **The seed's single-wey evaluation** is still absent. Only the oracle has a colony of 1.
- **M's target amplitude** is not pinned, only "measured".
- **W2's "gain at 1.5 and 3"** is ambiguous. W1 has an input gain of 1 and output weights of ±3; say which one W2 changes.

## 3. Other new problems (pins, not blockers)

- **The second seed:**
  - Its parameters are committed and hashed (`champions-3.json:1121-1123`), so it is reproducible.
  - If it is chosen, E3b-1 starts from an organism already tuned for 500 generations. The variance assumption comes from runs started at E, so say it may not transfer.
  - Say whether the other candidate is tried if the chosen seed fails criterion 2 on the report mazes. I would say no.
- **The nested searches:**
  - The filter λ > m removes 3 of the 9 (μ, λ) pairs, so 24 of the 36 settings are live. Say so.
  - "Reads 0.2 at the noses" depends on where the head sits in its cell. Pin d₀ as a number.
  - Stage B maximises the follower's own later-leg rate, not the peer effect. The winner may not show shared > own; that is acceptable, since it has a branch.
- **The polarity test:**
  - With diffusion, λ = m is not exactly flat: older deposits near the source have spread more. Report the flat trail's measured gradient share, which should be near 50%.
  - Pin that the follower's goal is the trail's source.
  - Pin whether the trail is a single pass or a shuttling steady state.
  - Pin that the 256 placements are one per selection maze.
- **The peer criterion:**
  - Shared and own diverge from the first A visit, because peers' A trails are sensed. The "first discoverer" can therefore be a different wey in each condition.
  - Pin the colony summary: for example, the mean first-B time over all weys but the colony's earliest, with censored weys counted at H.
  - There is no magnitude threshold, so a tiny effect passes on 256 paired mazes. Report it as a share of own's time.
- **Replay and scramble:**
  - Exposure matching is circular: the factor changes behaviour, which changes exposure. Pin one pre-pass at factor 1 with no iteration.
  - A permutation already conserves the field's mass, so scramble needs no scaling. Report its exposure instead.
- **The failure table:**
  - It lacks rows for the report-maze trail null and the Stage A recheck, both above.
  - There is only one fresh report block. The "adaptively selected" label covers a second retry, which is fine.