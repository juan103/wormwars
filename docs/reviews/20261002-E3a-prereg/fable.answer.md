I've finished reading the draft, the design, D163, both v2.4 reviews, `freeze.json` and the engine code; here is the review. I ran nothing, so every behavioural estimate below is a hand estimate.

## 1. Verdict: bind after fixes

No new design round is needed. Fixes 1–3 can change a gate or a registered outcome; fixes 4–8 are things the implementation cannot do as written; fixes 9–15 are small pins.

**Can change an outcome**

1. **The reset's timing puts G1 at risk.** The write comes "10 ticks after the first confirmed visit".
   - A wey aimed at A's centre crosses a chord of up to 3 cells, about 8.6 ticks at 0.35, and longer if it curves. B is then directly behind, so the stereo difference is near 0 and the turn starts near the carrier's 0.06 rad/tick.
   - In a large share of worlds the head is therefore still inside A at t + 10. `at_a` is still 1, RA overrides the write within a tick, the next entry is B, and the world fails.
   - Fix: time the write from the level's end (10 ticks after `at_a` returns to 0), and list it in §12. I am fairly confident of the mechanism and unsure of the share.
2. **The clamp assays do not say which stable state belongs to which goal for a bistable champion.** "The first entry is into that state's goal" is only defined for E (q > 0 means A) and for monostable champions (phase medians). Mirrored champions are allowed, so "working" and S2-a depend on this.
   - Fix: pass if one one-to-one assignment of the two states to the two goals passes both assays, and report the assignment. The hold's "active module" then follows that assignment.
3. **B-task's nose pairs lack the symmetry the comparators got.** The noses now feed the comparators in L1's pattern, so NL must equal NR at equal input.
   - "Each edge into it from another neuron" leaves the self-loops and the NL↔NR pair to "every other edge", drawn independently. Generation 0 then has a turn offset, and §7's stated result and test 12 fail.
   - Fix: add NL→NL = NR→NR and NL→NR = NR→NL, as for the comparators. Also state B-task's τ range ([0.5, 20]).

**Cannot be done as written**

4. **Calibration is placed at stage 4, but it needs champions that exist only after stage 7.** Census qualifiers also need calibration (medians, stimulus) before their clamp assays. Fix: E's calibration (D, its medians) at stage 4; champions' and qualifiers' calibration in stage 8, before their assays.
5. **The selection world seed and the checkpoints are not pinned.** `evolve_batch` takes one `world_seed` for selection and validation, and requires `checkpoint_every`.
   - "Every evaluation: world seed 1 171 000" does not clearly cover selection. Random sampling's "GA run i's selection worlds" needs it: `train_ids(1 170 000 + i, g, 16, 944M, 500 000)` at that world seed.
   - The design's validation every 25 generations is missing, and Stage 3's "checkpoints" are undefined. State `checkpoint_every`, and that checkpoints do not choose the champion (`RunRecord.champion_index` does otherwise).
6. **The inactive module's offset test is one-sided.** "|u| with it, minus |u| without, below 0.02" passes any large negative change. Write |u_with − u_without| < 0.02.
7. **B-task has no definition of "working".** Its comparison uses S2-b's rule 1, but the clamp assays and classes exclude B-task. Either drop rule 1 for that comparison or define working there by the score criterion alone.
8. **The geometric maximum needs its integer rule.** For example: 0 if t₁ > 600, else 1 + ⌊(600 − t₁) / t_leg⌋. Call it a model of an ideal mover, not a strict bound.

**Small pins**

9. S2-a and S2-b when a run is "not read": say "k of n read", and make S2-b descriptive below 8 pairs.
10. Admission: say whether × 1.25 applies to the evaluation alone or to the sum.
11. "It is 2 for E" reads as a measurement. Say it is fixed at 2 by design and report E's measured median; by the arithmetic in fix 1 the real level is probably 6–10 ticks.
12. Settable and the hold: state the start (the other stable state, relays at rest).
13. The random walk's seed (0, `random_walk_seed`) is missing; so is the random-sampling champion's tie index (lower j).
14. B-shared: its routing rows are missing, and "its 16 output edges at 0" does not translate to a nose pair (use the 4 nose-to-comparator edges).
15. "The controls where stated" in the component tests: nothing is stated. Remove it or name them.

## 2. D163's pins

All ten are carried in:
- the gate block (947 200 000–947 201 023);
- tolerances against the separation, read at the end of W;
- the stimulus's fallback, rounding, pooling and censoring;
- S2-c's zero wording with a Clopper-Pearson interval;
- S2-b's wording on the distributions and the permanent tie;
- B-task's self and mutual comparator edges and output range;
- the reset as a one-time write;
- Stage 3 runs 0–3 under reduction;
- the "proposed" numbers fixed;
- "bistable, not a latch" including slow settling.

Two are carried with caveats:
- **B-task's blind start** became weak sensing instead, declared in §12. That is acceptable, but it created fix 3.
- **B-task's τ draws** have no stated range.

## 3. The departures in §12

- **S-shuttle at k 8192: correct.** `freeze.json` "tuned" gives S-const k 8192, speed 1, turn 0 (mean 8.777), and "S-const k<=32" gives k 32, speed 1, turn 0.2 (5.633). The oracle (k 2, speed 1), constant motion (0.8, 0.1) and the random walk (1, 1, 0.5) also match.
  - One untested risk: at turn 0 with the goal directly behind after every visit, the controller relies on a tiny stereo difference being amplified. The gate asks only half the oracle, so I would keep it.
- **The geometric maximum and 0.6: acceptable.** The formula is sensible: the turn rate does not depend on speed, so a reversal costs about π / 0.30 ticks.
  - From E1's oracle (8.85 targets in 300 ticks) I estimate the shuttle oracle at roughly 0.8–0.9 of this maximum. So 0.6 is a loose sanity gate, and 0.8 would be marginal.
  - Changing the definition and the threshold together is fine because nothing has run and it is declared.
- **The blind controls' 90th-percentile rule:** I estimate the carrier's circle crosses both discs in about 3–5% of worlds, under the 10% that would fail it. That is rough, and it ignores wall effects.
- **The other departures** (D over legs after the first visit, the blind controls' tuned parameters, the new seeds) are fine.

## 4. Other checks

- **Seeds and worlds:** blocks 944M–948M and seeds 1 170 000–1 179 999 appear in no `.py` or `.json` file. `train_ids` depends only on (run seed, generation), so random sampling's pairing is implementable once fix 5 is in.
- **Engine:** chemical autapses are supported (q → q). The `initial` and `mutation_scales` hooks exist. The box [4, 20] and the 18-cell support match `world.py`.
- **Statistics:** `world_ci` (seed 0, 2.5th and 97.5th percentiles), `classify` and `_boot_means` match §2.
- **Budget:** the arithmetic checks against E4s-1's rate.
- **The clamp assays in G1** (90%, a final gate) carry some risk from paths that cross the wrong disc first. I estimate a few percent of worlds; this was agreed in the design and I would not change it.