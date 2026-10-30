Verification is complete. Here is my review.

## 1. Numbers against the records

Everything in `reading.json` is quoted correctly, and the derived figures I re-computed from `run.json` hold, with one exception.

| Claim in the draft | Re-derived | Verdict |
|---|---|---|
| Held 54 (F0), 55 + 1 unresolved (Z) | 109 held rows; 110 with the unresolved one | matches |
| Recovered 53 (F0), 54 (Z) | 107 recovered rows | matches |
| F0: all held recovered but one, which is "other" | 53 recovered + seed 7806's genome 559 | matches |
| Z: 53 held and recovered, 1 held then merged, 1 held with new roots, unresolved one recovered | the 55 held rows split 53 / 1 (seed 7808, last switch) / 1 (genome 559); genome 775 of seed 7700 is the unresolved recovered one | matches |
| Merged roots: F0 114 / 1, Z 112 / 2, one of Z's "both at 1" held in B | both arms' not-held "both at 1" is the same seed 7806 genome; Z's second is the seed 7808 held-then-merged one | matches |
| Separation medians and maxima | all 12 medians match to the digits shown; maxima 8.57 to 8.68 | matches; "near 8.7" should read "8.6 to 8.7" |
| Wilson intervals, shares, by subclass, by panel range, compute 731 s, 0.20 h, commit, 23 sabotages | all match | matches |
| A-root medians 5.37 vs 3.84, read-out 0.52 vs 0.36 | held (55): 28th value 5.371, 0.524; not held under Z (113): 57th value 3.838, 0.358 | matches, if "merged" means the 113 not-held genomes, excluding the unresolved one. Say so. |
| **"F0 and Z agree on 163 of the 169 genomes"** | On *held*: 163 agree (5 differ plus the Z-unresolved one). On the *outcome after restoration*: **162** agree, 7 differ (seeds 7700, 7802, 7803 one each; 7805 and 7808 two each). | **correct for one measure, wrong for the other; the draft names neither** |

## 2. Reader versus plan

The reader applies the plan's measures and wordings exactly. Held is from B alone, the outcome from C alone, both subclasses count as held, oscillation counts as not held, the root match uses the classifier's 1e-6 level, no ambiguous cases arose, the wordings carry the gap and the "(u unresolved)" clause, and the three inconclusive guards are present. Nothing in `reading.json` goes beyond the plan.

Two things in the draft are read beyond the plan without being labelled. The F0/Z agreement count is not a planned reading and is ambiguous, as above. The held/recovered cross-tabulation is a natural product of two planned measures but comes from `run.json`, not `reading.json`. Say where it comes from. The A-root and read-out medians are correctly labelled.

Three small description slips:

- **"The other 113 merged during the removal."** 112 faded to one state. One (seed 7600) converged, under both arms, to a single persistent oscillation. The plan's "merged" means fading, so name the oscillation.
- **"Other in C: 1 (new roots)."** Genome 559's C distances show one history back at its own A root to 1e-15 and the other at a third root. Also, that genome was read-out silent in B under both arms, and C's read-out difference is 0.001, about 0.1% of A's 0.82. It counts as "separate states" only relative to B's end, as the plan intended. Worth a sentence.
- **"33% to 33%"** should be "32.5% to 33.1%".

## 3. The interpretation

**The main fix is the "known kind" paragraph.** First, the quoted phrase is not in `M6-3-LITERATURE.md`. It is the D378 annotation in `SYNTHESIS.md`, so cite that. Second, the logic misreads what M6-3 recorded. Its section 6 lists two precedents: Kunert-Graf's coexisting states under constant input, and Liu J et al. 2022, where a state is kept "when external input terminates". The third that held under Z is exactly Liu's kind. So "attractors of a known kind" holds for all 169, not for two thirds. The honest refinement is a sorting into the two known kinds M6-3 already listed, roughly one to two. Delete "does not apply".

**What "held under Z" establishes, and the draft could say so.** By the classifier's rules a B class of "separate states" means two located fixed points, each linearly stable and each reached by its history, under zero sensory current. That is stronger than "still apart at tick 2000", and it is why "multistable" is a fair word.

**What it does not establish, and the draft should add:**

- Nothing about basin size or robustness. The model is deterministic and noiseless. "The bit outlasts the gap" is true for a quiet gap.
- The input-free states are not A's states. Roots move under Z (for example 4.85 against 5.06 for seed 7600's genome 227). "Recovered" shows each one maps back, which is the right test, but "the network alone holds the two states" should not be read as "holds A's two states".
- "Two states only under the held input" is slightly stronger than the data. From these two starts, the states do not survive the removal. Other input-free attractors are not excluded, as the plan's own caveat says. Reword to match it.
- "Without any input" should read "without sensory input". The biases remain, by design.

**One thing the draft could add in its favour.** F0 and Z agree almost everywhere, so for the two thirds that merge, it is the food channels specifically, not sensory drive in general, that sustain the bistability.

**One optional softening.** Both censuses ran on the CPU of the tested machine, so an exact 0.0 root match is plausible. But the compared roots are Newton-refined in float64. Exact coincidence shows the same roots were located; the float32 trajectories were not compared. "Changed nothing" is a shade strong.

## 4. Verdict

**Fix then publish.** The run is sound, the reader is faithful to the plan, and every number I could re-derive is right except the unqualified agreement count. The fixes, in order of weight:

1. Rewrite the "known kind" paragraph as a sorting into M6-3's two listed kinds, citing SYNTHESIS.md's D378 annotation.
2. Make the agreement count name its measure: 163 on held, 162 on the outcome, with the seven differing genomes by seed.
3. Name the oscillating genome among the 113, and describe genome 559's C state accurately.
4. Add the three "does not establish" points and the classifier-based meaning of "held".
5. "Without sensory input", "32.5% to 33.1%", "8.6 to 8.7", and state that the medians' comparison group is the 113 not-held genomes.