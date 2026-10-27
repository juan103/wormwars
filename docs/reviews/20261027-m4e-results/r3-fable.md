**Verdict: agree.** Every round-2 finding is in draft 3 as described, and every number I checked traces to a committed or to-be-committed file. Nothing blocks publication beyond the publication commit itself.

**Fixes confirmed, each against the files**

- The Δ_count envelope sentence now matches Astra's recomputation. The per-arm figures −0.0001 and +0.0002 round correctly from r2-astra's −0.000106 and +0.000178, and the transition counts 20 and 2 match `readings.json`.
- The reproduction statement is split by reviewer and describes each round-1 review accurately.
- The threshold passage states the S3 gap. U_HH's largest S3 is 0.956 and K's smallest is 1.259, so no arm lies between 0.96 and 1.26. The below-1.0 counts 354 to 629 and the 0 to 3 switches match the band sums in `tables.json`. The "wrong shape", "That is why" and "outside the block" sentences are gone. Attributing "threshold-like" to Fable is correct per r1-fable's item 2.
- Band shares, in-band attribution, AUC range, arm medians, and the U_HH switches below 0.8 all match `tables.json`.
- W − U_HH's lower envelope of 0.000515 is 5.3 genomes, so "about five" and the roadmap caveat are right.
- 56 of 201 settled, 54 fading and 2 separate, and 6837 second-pass genomes all sum from the transitions block. The 75 s figure is correctly labelled as the smoke's estimate, and the plan's line 280 says exactly that.
- Two of twenty K draws lie within 0.05 of 1.714, namely 1.718 and 1.671, so ten proposals per acceptance follows.
- The M5 additions, the 51/8/41 decomposition and the 0.89 multiplier match r2-astra.
- Blocks table ranges, the S3 medians 1.47, 1.45, 1.53, the reciprocity matching within 2 in all 20 draws, the compute totals, dates, commit and clean tree all check.

**One dependency, not a defect.** At HEAD 46869e7 the results file, the review archive and `runs/memory-m4e/` are untracked, and no D368 entry exists yet in DECISIONS.md. The draft's "committed" statements become true only when D368 lands. `.gitignore` already excludes `blocks.json` and `compute.json`, so adding the directory is safe under rule 1. The directory also holds `stage0.json` and `pilot-equivalence.json`, which the draft does not name. Both are harmless summaries. Decide explicitly whether they go in.

**Optional wording, non-blocking**

- The headline bullet says "putting it on the host's own 92 to 126". U_LH uses U_LL's random positions at the host's edge count, not the host's own edges. "On 92 to 126 random edges, the host's count" would remove the ambiguity. The same reading applies to "N2's 260 edges".
- If a sentence is wanted on the predictor, `tables.json` offers one: U_HH has 1189 genomes with predictor 1.0 or above and zero switches, where the strong arms' 1.0 to 1.2 band runs at 0.17% to 0.32%. That is mild extra support for "neither confirms nor refutes", and the draft is already long, so I would leave it out.