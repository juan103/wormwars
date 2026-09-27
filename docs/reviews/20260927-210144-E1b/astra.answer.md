**Yes—ready to implement the pilot.** I checked `roadmap` HEAD `d492836`, both v1 reviews, D077, and the relevant code. I ran nothing and changed nothing.

My six must-change points are resolved at the design level: cue-use evidence, explicit energy and scoring mechanics, pilot-calibrated gates, target pairing, preserved E3 input mapping, and deterministic replay requirements.

My should-change points are also addressed: corrected and strengthened controls, diagnosis before sensor/body redesign, limited E3 claims, preserved controller state, and a small but complete pilot with accounting and event records. The missing numerical thresholds are appropriately deferred until after the pilot.

Three details need attention during implementation; none warrants another design round:

- **The scent cutoff wording is wrong.** [DESIGN.md:57](D:/Claude/random/wormWars/docs/E1/DESIGN.md:57) describes `3σ + R` as a radial cutoff. [gaussian_blur](D:/Claude/random/wormWars/wormwars/world.py:56) truncates each axis separately; diagonal support extends farther. Measure coverage from the actual sampled field.
- **Choosing R introduces geometry constraints.** [DESIGN.md:56](D:/Claude/random/wormWars/docs/E1/DESIGN.md:56) makes R pilot-selected, while D has no numerical value and wall clearance stays fixed at three cells. Specify D in the pilot configuration, keep consecutive goal discs disjoint (`D > 2R`), and check wall clearance against the chosen R. Otherwise a second arrival need not demonstrate a new approach. The quoted wall-slider percentage is tied to the earlier geometry.
- **“Scent, not energy” must be implemented literally.** The current [total_energy](D:/Claude/random/wormWars/wormwars/world.py:932) includes `fields[FOOD]`. Simply writing a relocatable blob there does not establish the claimed energy separation. A sensing-only source fits the design; the ledger test must cover relocations.

I see no new conceptual blocker. The freeze must include the concrete task configuration, gains, selected navigator and tuned baselines, numerical thresholds, confidence-interval method, cue intervention, sample sizes, and execution mode. Exact replay requires the original evaluation and replay to share the deterministic device/mode and code version.

The sequence is correct: retain the stated T0/T1 prerequisites, implement and pilot on development worlds, freeze, use the scripted gate worlds once, and proceed to 04a only after a pass. This confirms readiness to implement, not that the navigator or gate has already been validated.

E1 v2: ready to implement