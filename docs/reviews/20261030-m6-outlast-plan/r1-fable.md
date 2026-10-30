**Verdict: agree with fixes.** The code does what the plan says, the classifier is applied correctly under the changed input, and the smoke result will be read honestly once a few pre-run points are tightened. Nothing here needs a second round.

**1. Will the answer be read honestly? Checks that passed**

- **The changed input reaches every path.** Newton, stability and the continuation take the input from the run's recorded current, which `follow_from` builds through the context. The oscillation rerun goes through `follow_from` with `initial` inside the same context. The current builder has no constant term (`wormwars/exp03/measures.py:75`), so Z is truly zero sensory current, with biases kept, as the plan implies.
- **Nothing in the classifier assumes the ramp.** The start difference `a` only splits "separate states" from "read-out silent" (`scripts/memory_m2/classify.py:123`), and both count as held. The candidate windows and the tail are relative to the follow, not the ramp.
- **The census class is a first-pass class.** M4c ran M2's census code unchanged; M4e's second pass writes its own records. So A's first pass is the right comparison.
- **"unresolved" is the exact class string**, so the outcome test on it works.

**Fixes before the run**

- **The root-match tolerance is not the classifier's level.** The plan and `outlast.py:43` call 1e-4 "the classifier's distinctness level". The classifier's is 1e-6 (`classify.py:9`); 1e-4 is the looser sensitivity level. The project's own same-root convention, in R3 and the tick-300 check, is 1e-6. Use `K.DISTINCT` and correct the sentence. Located roots carry an error bound of 1e-9, so the outcomes will not change, but as written the plan misstates a number. A switch whose A roots lie between 1e-6 and 2e-4 apart can also have a C root within 1e-4 of both A roots, and `match` then returns "same" by precedence. With 1e-6 this is an edge case; flag it as "ambiguous" or report A's root distance below twice the tolerance as context.
- **The sign clause is not implemented and not recordable.** "Recovered" in the plan requires the read-out difference's sign unchanged. The code checks only root identity, and the recorded read-out difference is an absolute value. Drop the clause from the plan, since root identity within tolerance covers it.
- **An unresolved B should not poison the recovered reading.** Recovery is a fact about A and C alone: C runs from B's end states whatever B's class. Under Z, B may be unresolved more often (slow reaches, candidates). Make recovered, merged and other depend on C only, and let B's class feed the held share only.
- **State that removal and restoration are steps.** B drops the food in one tick and C restores it in one tick, not over the probe's 10-tick ramp. C is then a rise from zero, so if the no-input state is unique, "merged at the rising-start root" is the expected signature of a path-selected attractor. Writing that expectation now is what makes the smoke result readable as the Kunert-Graf distinction the suggestion aimed at, and not as a surprise.
- **Name the gap in the fixed wordings.** "Do not outlast a 2000-tick removal of the food input." The result depends on the gap's length.
- **The plan's test list names a test that does not exist.** "The rebuilt genomes are exactly the census ids (skipped without the local census arrays)" is a JSON id check only. Align the text, or add the cheap stronger check: where the census `.npz` exists locally, compare A's roots with the stored roots and report the count. That pins both the rebuild and the batch-composition effect, since the census ran chunks of up to 128 and this run batches 13 to 18 per seed.
- **Update the cost line from the smoke.** The smoke gives about 7.5 s a genome, so about 21 minutes, before any oscillation checks.

**2. Design, given the smoke**

"All merge" is informative enough for the question asked. Do not add arms or a partial reduction. What is missing is free: record per genome and arm the max-norm state difference between the two histories at B's ticks 0, 10, 30, 100, 300 and 2000. `follow_from` already returns these states; `sub()` discards them. With that, "all merge" comes with "how fast", which answers whether a shorter gap would matter without a second B length. A partial reduction asks about the attractors' range over food level, which is a study.

On "baseline": the original suggestion said "food returned to baseline after the ramp". Reading it as no food (F0) plus no input (Z) fits its purpose. The other reading, each history back to its own warm-up level, is a hysteresis question, not this one.

**3. Anything to cut**

Only the sign clause and the wrong tolerance sentence. The Z arm answers the plan's first question separately from F0 and costs minutes; keep it. The intervals and breakdowns are already written and cheap.