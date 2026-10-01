**1. Verdict: adopt with changes.** I've finished reading the proposal, both v1 reviews, D143, `graft.py`, `brain.py`, the motor read-out in `world.py` and design v3. The sequence is right and most must-fixes are resolved. Four items need fixing before the amendment; none needs a new design round. Nothing was run; the arithmetic below is by hand from the code.

## 2. The v1 must-fixes

**Resolved:**
- **Plateau wording:** E2d's corrected form is used.
- **Comparator buildable:** it fits `Module` as written — one signal per nose at gain 1, signed weights in `w`, and 20 edges all within ±3.
- **Turn factor:** confirmed as 1 (`world.py:745-750`, `turn_gain: 2.0` in `configs/default.yaml`).
- **E3 fallback:** rule 1 and both "What would change" entries now agree.
- **Repository state:** v3 carries its superseded note and D143 holds the dated correction. I could not run git, so I take the commit hashes from the log you gave me.
- **Arms, ownership, gates, literature qualifications:** done as the map says.

**Not fully resolved:**
- **Residual-sweep readings (Fable 6):** the classes exist but have a hole (3b).
- **Exclusive outcomes (Fable 7, Astra 5):** the table is exclusive, but it dropped v3's "acquired" class (3c).
- **The ladder (Fable 3):** it is fixed in advance, but L3's grid cannot work and L5 is undefined (3a).

## 3. New problems

**a. The ladder.**
- **L1 arithmetic holds.** At the signal sizes v3 records (d about 0.004-0.017, level up to 0.35), every stage is in its linear range.
  - Each comparator sits at ±w_n·d and each turn neuron at ±2·w_o·w_n·d, so the turn is 4·w_o·w_n·d, at most 36·d.
  - Small corrections: sech²(level) at the noses (about 0.89 at the peak) and sech²(b_t) from the carrier's turn bias (about 0.96).
  - The path has three lags (nose, comparator, motor relay) that E1's scripted k = 32 did not have. "Near the line" is fair, and probably slightly below it.
- **L3's grid is dead on arrival (must-fix).** With mutual inhibition w_m, the differential mode obeys τẋ = −x + |w_m|·tanh x + w_n·d.
  - At w_m = −2 this is Astra's latch: fixed points ±1.915 and a switching threshold of about 0.53. The available drive, w_n·d, is at most about 0.05, so the pair latches on the first transient and the scent never flips it.
  - At w_m = −3 it is worse. At w_m = −1 it is marginal: a slow cube-root amplifier.
  - If L3 is cumulative on L2 (the "Added" column does not say), every grid point has w_s + |w_m| > 1 and is bistable.
  - Fix: require w_s + |w_m| < 1, for example w_m ∈ {−0.5, −0.8, −0.95} without L2, and say whether steps are cumulative.
  - L4 inherits this; base it on L1 or L2 instead.
- **L2 is sound, with two notes.**
  - It needs a self-edge in a graft. `graft_connectome` looks as if it accepts one, but no test covers it. The proposal schedules that test only for E3's latch; E4s-0 needs it first.
  - Bias −0.5 with w_s = 0.95 moves the rest point to about −1.3, where the net gain is about 0.3. The grid will avoid it, so it is harmless.
- **L5 is undefined.** A relay through tanh adds no gain. The neuron count (10 + 4 = 14 against "at most 16") does not pin the wiring. Define it or drop it.
- **Unpinned details:**
  - which of the 5 re-scored candidates goes to qualification;
  - whether each step's qualification attempt gets its own fresh 1 024 worlds;
  - whether "turn bias" means b_t or the command 2·tanh(b_t).

**b. Residual-sweep classes (must-fix).**
- **The likeliest outcome lands in "unclear".** With d at most 0.017, k ≤ 1 adds at most 0.017 to the turn command. E1's curve suggests the first improving k will be around 4-32 for most champions. A champion that first improves above k = 1 with no dip matches no named class. Add "rises late", or drop the ≤ 1 cut-off and report the first improving k.
- **"No benefit" hides harm.** It includes champions harmed at every k; split off "harmed".
- **Multiplicity.** Twelve unadjusted 95% intervals per champion give roughly a 25-30% chance of a spurious rise or dip in a null champion. Require two adjacent k values, or adjust the intervals, or state the rate.
- **Units.** Pin L and R as the scaled `food_left` and `food_right` (E1's units), and the sign convention (turn > 0 is left).
- **Materiality.** The classes use "lower bound above 0", while E2d's criterion has a materiality threshold. Say which applies.

**c. E4s-1's outcome table and arms.**
- **"Acquired" is gone (must-fix).** Row 2 labels any run whose G0 is not D as "never used", even if F is D. v3 had "acquired" for that case. It is R's most interesting outcome, and it is possible for M on random backgrounds. Split row 2 by D at F.
- **Scope of the table.** In N, D is impossible by construction. Say the table applies to M, R, F0, U and C2, and that N reports H only.
- **The 25% reading does not match the 12-of-16 rule.**
  - If, say, 30% of backgrounds are D at G0, E4s-1 proceeds, yet "retained in 12 of 16" may be unreachable.
  - The reading is per background, while the table uses each run's G0 best of the population.
  - Pin the E4s-0 statistic as the one the table uses: the share of simulated populations whose G0 best is D. Set its threshold consistent with 12 of 16.
- **R's draw unit is unpinned.**
  - One draw per run, shared by the population, tests designed against random weights.
  - One draw per individual lets generation-0 selection pick among sign patterns, which is a different question.
  - At 0.25× mutation, a weight of magnitude about 3 will not cross zero, so R cannot repair itself. That is acceptable, but the reading of M − R should say so.
- **H by silencing (should-fix).** Silencing removes whatever constant drive the host adapted to, so "not H" may be a lesion artefact. An alternative with existing probes: noses on the module "mean" probe (alive but blind) against the world "mean" probe on everything.
- **M − N is close to a foregone conclusion** once the module qualifies. M − R is the informative comparison. Say whether the two 90% intervals are read separately.
- **Budget:** 72 runs checks out.

**d. The E3 rule.** It is consistent, with three gaps:
- **Failed re-qualification.** The rule does not say what E3 uses if the frozen module fails E4s-1's re-qualification.
- **Rule 2's choice.** "Chosen by validation mean" should say "among retained runs". It should also say when the swap is allowed relative to E3's own pre-registration.
- **What the artefact is.** The comparator on the carrier is a hand-built circuit on a silent worm, with no evolved N2 in it. E3's claims must say so, as option (a) already requires for E4s.

## 4. To pin before the amendment and E4s-0's script

1. L3's stability constraint, whether steps are cumulative, and L5's wiring (or its removal).
2. A self-edge graft test, seen failing first, before L2 runs.
3. The sweep's "rises late" and "harmed" classes, its multiplicity handling, and its units.
4. The "acquired" row, and the table's scope by arm.
5. The G0 statistic and a threshold consistent with 12 of 16.
6. R's draw unit and seed.
7. World ranges per qualification attempt, and the candidate-selection rule.
8. A compute estimate against the 2-hour cap. I did not check this against a measured rate. The load is roughly 313k rollouts for the sweep, about 400k for ladder tuning, plus the 256-background measurement with probes.