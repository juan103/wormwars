**Verdict: fix then run.** I checked `roadmap` at `20e6cab`, both v1 reviews, D174 and the relevant code. No files changed.

Four substantive fixes remain:

1. **Power is still underspecified.** Specify the simulated distribution of **paired run differences**, the gate margin, and the exact rejection rule; simulate false positives as well as power. A 90% percentile bootstrap with eight runs does not guarantee one-sided 5% error: my in-memory normal-null check rejected **7.9%** of 4,000 trials. Also, **0.267 is SD divided by E’s mean**, not the Stage 3 champions’ CV. Their committed mean is 12.0874 and SD 3.4098, giving **CV 0.2821**. Keeping 0.267 as an explicitly chosen seed-relative scaling assumption is defensible. [Power specification](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:288)

2. **The “flat” polarity control is not established.** Setting λ = m cancels deposition decay against evaporation in the simplified single-pass calculation. It does not guarantee a flat profile with unequal residence times, differently aged diffusion, junctions and revisits. Validate the null’s longitudinal gradient and control its intensity; otherwise real-versus-flat can distinguish concentration or deposition history rather than polarity. [Polarity test](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:175)

3. **Replay/scramble exposure matching is circular as written.** Scaling changes movement, which changes nose exposure, so a ratio measured on one trajectory need not match exposure after rerunning. Specify an executable calibration—for example, selection-only reference trajectories and a frozen coefficient—and report actual residual mismatch, including zero-exposure cases. Different episode seeds also do not guarantee different endpoints; enforce that requirement or explicitly report exceptions. [Peer controls](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:201)

4. **Failure handling must cover every failed threshold and requalification.** A positive effect below the required 0.5 is not “null”; a harmful or inconclusive peer contrast is not “shared = own.” Branch on the actual criterion failing. After changing horizon, deposition scale or trail chemistry, rerun affected downstream qualification; fresh report mazes alone do not establish that the revised task still passes. [Failure table](D:/Claude/random/wormWars/docs/E3/E3b-0-PLAN.md:299)

The requested specific checks:

- **Second seed:** acceptable. Its score and partial-gate figures match committed records. Selecting complete seed-plus-variant packages on selection mazes is legitimate exploratory work. Clarify that component qualification tests each candidate’s actual modules, and whether inactive-gain failures exclude S3r3; the existing E3 component-test function includes such a failure.
- **Nested searches:** pilot constants resolve the circular dependency. This is a sequential search, not an exhaustive geometry-by-trail search; failure only concerns the searched settings.
- **Peer criterion:** the required contrast and interval resolve the v1 threshold objection. Pin the endpoint completely: for example, average capped first-B order statistics 2–8, retaining nonarrivals at H and defining ties/no-discovery colonies. Also define later-leg rates for weys with no first visit.

**Not every v1 item is resolved.** Remaining items are power, polarity-null validity, executable replay matching, complete failure handling, and some implementation pins: d₀’s calibration geometry, W2’s “fires” condition/circuit, and remaining tie-breaks. Single-wey seed evaluations are still absent. Also, [`maze.draw()` still redraws walls](D:/Claude/random/wormWars/wormwars/e3/maze.py:144), contrary to §1a.

The other v1 changes are resolved **at plan level**, pending their promised tests and measurements. The revised oscillator search/drop rule is acceptable; adaptation is not necessary for every possible CTRNN oscillator.