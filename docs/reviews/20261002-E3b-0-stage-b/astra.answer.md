**Verdict: amend and continue—with corrections, not the amendment exactly as proposed.** Retaining linear trails is defensible for exploratory work. The claim that both tests fail “by construction” is not established.

I checked the code, records and all 24 `.npz` files; their rate and polarity means agree with the JSON. No files were changed.

1. **The diagnosis identifies a controller–test mismatch, but overstates its explanation.**

   Exact backward alignment on a symmetric longitudinal gradient gives L = R. But the registered start includes jitter: a bilateral controller can then receive a turning signal without temporal memory. I verified nonzero steering under a longitudinal gradient with ±0.3-radian headings. Wall interactions and transverse gradients further complicate matters. “Cannot turn around” is false as a general statement.

   There is also a **diagnosis bug**: [`_start()`](/D:/Claude/random/wormWars/wormwars/e3/maze_runs.py:138) implements “toward A” by adding π to the heading toward B. At a bend, that points away from the B branch, not along the A branch. **45/64 diagnosis mazes have such a bend at the start.** Use the previous route cell to define toward-A heading.

   The oracle receives the same position and heading, so I found no obvious unfair-start timing bug. Its recorded median time is 39 ticks: the deadline is indeed 78 ticks, with deadlines ranging from 34–124. That can penalize slow reorientation. Also, the trail is aged one full leg **after the B-arrival snapshot**; deposits nearer A are already older, and aging continues during the test. Heading, deadline and signal age remain competing explanations. The diagnosis has not separated them.

   One factual correction: **the gradient did not pass everywhere.** Two settings—μ=.005, λ=.01, δ=.05, both d₀ values—score **0.7974527**, below .8. Preserve those failures.

2. **The range objection supports replacing the gate, but does not establish adequate sensing.**

   With approximately 14% occluded noses, these observed trajectories cannot achieve 90% in range. That is a property of these trajectories, not a universal impossibility for every controller or setting. And only about 40% of unoccluded readings qualify: occlusion explains only part of the failure.

   Stacking exposes a real qualification gap. At the diagnosed winner, about 31% of readings exceed .35. Calling those readings “saturated” is misleading: .35 is the qualification boundary; the interface clamp is 5.

   **Criterion 4 currently cannot replace this gate.** [`cmd_report()`](/D:/Claude/random/wormWars/scripts/e3b0.py:581) tests a fixed list ending at .35; `level_quantiles()` supplies counts, not measured quantiles. Specify an executable qualification protocol covering the selected seed’s actual input distribution, including high levels, low positive levels and asymmetric zero/nonzero nose pairs. Keep zero/occluded exposure reported separately. Component gain cannot establish usable information where no signal exists.

3. **Amend explicitly; do not declare the original Stage B passed.**

   “Controller failures never change the trail rule” supports retaining linear chemistry while repairing its qualification. It does not automatically authorize deleting failed gates. The amendment must explicitly supersede the no-setting-passes branch, preserve the original failure record, and freeze replacement qualification and failure handling before further selection.

   Making behavioural polarity descriptive is reasonable. Retain the gradient gate, but describe it narrowly: it measures gradient signs, not readable magnitude or behavioural polarity. Moreover, [`gradient()`](/D:/Claude/random/wormWars/wormwars/e3/maze_runs.py:213) measures aged, repeatedly deposited oracle trails; the behavioural probe uses a single pass. Add bounded diagnostic checks with known gradient direction, corrected headings and deadline/age sensitivity before attributing the failure to the controller.

   Keep criterion 3 unchanged. The diagnosis is encouraging, but **own − none’s lower bound is .393, below the required .5**, and shared − own in later-leg rate is **not the registered peer endpoint**, which is later discoverers’ first-B time. Peer feasibility remains unestablished.

4. **Keep the shared-rate ranking; fix implementation blockers before continuing.**

   For fixed geometry, horizon, controller and paired mazes, the no-trail baseline is independent of μ, λ, δ and d₀. Therefore maximizing mean shared rate and maximizing mean **shared − none give exactly the same ranking**. Changing that objective buys nothing. Report paired effects and unvisited shares, retain the original tie-breaks, and bound the widening in advance.

   Reusing selection mazes for diagnosis is legitimate exploratory development. However, these bootstrap intervals are not independent validation of a setting selected using overlapping data. Freeze everything before opening report mazes; apply the fresh-report rule after adaptations prompted by report results.

   Two additional code fixes are required:

   - **Replay calibration is broken.** [`_components()`](/D:/Claude/random/wormWars/wormwars/e3/maze_world.py:276) puts the entire shared field into `base`, leaving `other=0`; exposure measures `other`. I reproduced positive peer fields with zero recorded shared exposure. Consequently, [`coefficient()`](/D:/Claude/random/wormWars/scripts/e3b0.py:475) produces coefficient zero whenever donor exposure is positive, collapsing replay to own-only. Measure live-peer exposure correctly and add a failing regression test, preserving shared trajectories.
   - **Enforce the recheck’s result.** [`cmd_stage_c()`](/D:/Claude/random/wormWars/scripts/e3b0.py:415) requires a completed recheck record but never checks its `passed` value. Completion must not permit advancement after failed conditions.

The evidence supports another bounded exploratory qualification of linear trails. It does **not** yet support “the trails are qualified; only impossible tests failed.”