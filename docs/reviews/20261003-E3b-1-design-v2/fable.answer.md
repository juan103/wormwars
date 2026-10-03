Verification is done; I've checked the power table against `power.json`, the compute against `timing.json`, the maze-id mechanics and W2's graft. Writing the review now.

## Verdict: proceed to the pre-registration, with the fixes below. No further design round.

v2 resolves every point in my v1 review and, as far as I can judge them, Astra's too. The two numeric claims you asked me to check reproduce.

## 1. Checks against files

**Power table (§5) against `power.json`.** Every row reproduces from the Welch entries, normal and empirical shapes:

| Row | File values (normal / empirical) | Design says |
|---|---|---|
| CV 0.282 | FP 5.2% / 4.9%, MDE 0.19 / 0.18 | 4.9-5.2%, 0.18-0.19 |
| CV 0.40 | FP 4.8% / 4.6%, MDE 0.27 / 0.25 | 4.6-4.8%, 0.25-0.27 |
| Unequal 0.15/0.40 | FP 5.3% / 4.8%, MDE 0.21 / 0.20 | 4.8-5.3%, 0.20-0.21 |
| Means ± 0.10 | FP 5.1% / 4.5%, MDE 0.19 / 0.18 | 4.5-5.1%, 0.18-0.19 |
| Opposite ± 0.15 | 4.4% / 5.0% | 4.4-5.0% |

The script computes the gate as §4 states it: stratified estimate, SE from within-schedule variances over 4, Satterthwaite df, one-sided. The sign-flip test is now enumerated over all 65,536 patterns. Two sentences in §5 are looser than the file: "pooled t and sign-flip keep 5.0-5.5% with equal effects" holds only at CV 0.282 (pooled t is 4.4% at empirical CV 0.267), and "0.28-0.31 against a shifted null" excludes CV 0.40, where it is 0.36. Add "at CV 0.282" to both. Rule 5, trivial.

**Compute (§6) against `timing.json`.** 0.056528 s per tick at 4,096 worlds, H 2,400: T-A 4.711, T-F 5.653, N 3.533, R 1.178, total 15.07, with reserve 18.84. Validation 32 × 4,096 episodes at 13.8 µs per world-tick gives 1.22 h. Learning curve 176 points × 128 mazes gives 0.21 h. All as stated. The 27.4 left is 30 minus E3b-0's 2.62. The linear-in-worlds assumption for T-F at 2,048 and R at 1,024 is the known weak spot and the benchmark covers it.

**Maze blocks.** `maze.py:155-159` seeds each maze from `[run_seed, maze_id]`, so disjoint ids are disjoint mazes only under the same run seed. E3b-0's was 1,180,000. The design does not name it. Name it.

**W2's freeze.** `reflex()` in `maze_organisms.py:94-101` builds two neurons with 8 output edges each and inputs through the interface, not through graft edges. So "two neurons and 16 output edges" is the complete set, provided the mask also freezes their τ and bias. Say so explicitly.

## 2. What must be pinned before the pre-registration

None of these changes the design. All are ambiguities a pre-registration cannot leave open.

- **The secondary tests have no named statistic.** S-trail and S-peer say "over the 16 champions, one-sided" and S-gen says "paired, one-sided". State for each whether it is the same stratified Welch as the gate, a pooled one-sample t, or a paired t on 8, and the direction of each one-sided alternative.
- **The evaluation roster is incomplete.** §4 promises Δ in units of E's contribution over W2 "re-measured on the test block" and of the seed-follower gap, and R is read as recovery. That requires W2 alone, the scripted follower, and R's degraded seed on the test block. The "about 33 organisms" count omits all three. List the roster.
- **"Population at generation 125" is undefined.** Pin it as the 32 genomes evaluated in generation 125, before that generation's selection and mutation, and state that their validation scores do not feed back into T-F's continuation.
- **The CV threshold (0.282) needs an operational definition.** Say it is the pooled within-schedule SD of d, in seed-mean units, matching the Welch variance. A between-schedule mean difference would otherwise inflate it.
- **"Trails off" in S-trail and the test evaluation** should be named as access "none", since that is the tested equivalence.
- **The repeated-journey median** should be defined as E3b-0 computed it: the median over all wey-episodes across the 256 test mazes.
- **Scope of the CV assumption.** E3a's 0.282 is the CV of the tuned champions' means. The simulation uses 0.282 as the SD of d in seed units at every effect size. If the CV holds at the tuned mean, the SD of d at Δ 0.19 is about 0.34, and the MDE is nearer 0.22-0.23 by interpolation between the 0.282 and 0.40 rows. The 0.40 row brackets it and the run-level spread in mazes is unknown anyway, so this is a sentence in the pre-registration's power section, not a redesign.

## 3. Not required, noted

A rule for a crashed or NaN run (rerun on the same seed under replay mode, or drop and report) is cheap to register now and awkward to decide later. The 25% reserve covers training only. Both are judgement calls.