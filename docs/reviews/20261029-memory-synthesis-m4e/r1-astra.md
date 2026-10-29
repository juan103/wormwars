**Verdict: fix then publish.** The new numerical values match the records. The main problems are the wording of M5’s target, an unsupported ranking of M4e’s explanations, and omitted limits on the classifier evidence.

1. **M5 does not test whether the advantage is at least 0.002.** [SYNTHESIS:250](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:250) says “by 0.002 or more”; the table repeats this at line 291. The agreed success criterion is a lower confidence limit **above zero**, with **0.002 as the planning effect**. Those are different claims. [M5-POWER-DESIGN:59](/D:/Claude/random/wormWars/docs/memory/M5-POWER-DESIGN.md:59) and the reader’s `direction()` agree. Suggested wording: “Does T raise the protocol-confirmed share over Rr? Power was planned at a true difference of 0.002.”

   Also, Rr preserves the **count of reciprocal pairs**, not N2’s particular pairs. Correct line 251 and the inherited wording at line 197. D369 explicitly records this same correction.

2. **“More than its size” overstates what M4e established.** [SYNTHESIS:40](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:40) ranks explanatory contributions that were not estimated. The supported findings are narrower: spreading fixed total weight over more equal-magnitude random edges lowered the rate; replacing equal magnitudes with N2’s uneven weights raised it descriptively. How much of the transplant benefit concentration explains remains unresolved—explicitly so in [M4E-RESULTS:266](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:266).

   Remove the ranking. In “What it adds up to,” retain the tested construction conditions. At line 303, prefer “the equal-magnitude block at N2’s count and total weight did not reproduce T’s observed rate” over “neither … edge count nor … total weight.” The threshold-like interpretation is acceptable **with the existing qualification that these arms cannot distinguish a step from a steep continuous rise**.

3. **Restore the scope of “every assignment.”** The synthesis omits [M4E-RESULTS:143](/D:/Claude/random/wormWars/docs/memory/M4E-RESULTS.md:143): the envelope conditions on every other genome’s classification and does **not** cover missed transitions among unaudited fading genomes. This matters particularly for the thin Δ_count and W−U_HH margins. Add that qualification beside the audit or in the classifier limits.

   Also clarify [SYNTHESIS:285](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:285): “every host, every assignment” must not imply a strictly positive contrast in each host under every assignment. In M4e’s SH-recip-2051100, T has 10 confirmations; I has 9 plus one unresolved, allowing a tie. Say: “positive counted contrasts in every host; the aggregate contrast remains positive over every assignment.”

4. **The attribution to a bound on latent switches is wrong.** [SYNTHESIS:390](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:390) credits Fable with “the bound the pilot puts on latent switches.” The final agreed account explicitly says the pilot does **not** bound states the classifier cannot confirm. It bounds later protocol confirmations under the tested continuation. See [DECISIONS:11956](/D:/Claude/random/wormWars/DECISIONS.md:11956). Credit Fable with bringing the pilot’s continuation evidence into the budget decision, without calling it a latent-state bound.

   Likewise, “a class, not a backlog” is defensible as a **protocol treatment**, not an established dynamical category. State that the unchanged classifier could not resolve these genomes; the pilot did not distinguish classifier limitations from hard dynamics.

5. **Make the power costs explicitly conditional means.** At [SYNTHESIS:259](/D:/Claude/random/wormWars/docs/memory/SYNTHESIS.md:259), 72 and 91 hours are simulated **mean costs** under the central and core scenarios, not a runtime range or cap. The recommended policy has a 145-hour cap; the above-core scenario gives about 96 hours and 0.75 power. “Would need 110 to 160 hosts” should become “the recommended allocation uses 110 initially, up to 160, under the simulation model.”

   The postponement itself is represented fairly and matches D373. The new lesson is reasonable as an argument for **early rough scoping**. I would add that the rough calculation could not replace the pilot and full power calculation: those resolved control variance, audit treatment and the identification limit. It should not read as though the final answer was already available before that work.

6. **Correct three smaller factual slips.**

   - Line 255: **94% of the estimated variance**, not “SD … is 94% genome sampling.” The decomposition truncates a negative host component to zero.
   - Lines 258–259: the third power-results review round was **Astra only**, according to D372 and the archive. The six-round total remains correct.
   - Line 361: “All three ran” implies M5 ran. Say the first two were completed and M5’s preparation reached the host-count recommendation.

7. **Update the entry point for readers of `main`.** [README:60](/D:/Claude/random/wormWars/README.md:60) still says “M5’s power calculation is next.” Add the completed preparation and postponement there.

I checked the new counts, intervals, envelopes, transitions, block summaries and adopted power outputs. The compute records sum to **112.4340546 hours**, correctly reported as **112.43**. The summary extraction code matches the source fields; no numerical repair is indicated. I inspected the saved failing/passing test logs, but could not independently rerun the five tests because no usable Python interpreter was available. No files were changed.