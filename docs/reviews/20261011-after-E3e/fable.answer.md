**Recommendation: option 4, the 6 × 6 family at k_r = 0, but with a different control structure for E4 than the claim proposes, and with one free analysis done first.** I checked the claim against both results files, both designs, the two summaries, the E3e reviews, and the per-maze records in E3d's calibrate file. Two of the claim's reasons are wrong in direction or size; the conclusion survives anyway.

## 1. What the records say about each option

**Option 1 (7 × 7, longer horizon) is dead on the committed numbers, more firmly than the claim says.** G2a is follower ÷ oracle. From E3e's summary at k_r = 0, the post-discovery rates are:

| | later-leg rate per 1 000 ticks | arrival at A | steady-state visits per 1 000 ticks |
|---|---|---|---|
| oracle | 14.63 | 1.00 | 14.6 |
| shared follower | 2.33 | 0.84 | 2.0 |

The ratio of steady-state rates is 0.13, below the current 0.158, and 0.16 even at full arrival. So the follower's share of the oracle does not rise with the horizon to first order. It falls. The only escape is if the follower's shuttling accelerates late, which Fable's results review noted as a bimodal later-leg distribution. That would need most mazes to "ignite", and nothing in the records shows it. The problem at 7 × 7 is a threefold collapse in the follower's shuttling rate, not discovery.

**Option 2 (6 × 6, shorter horizon) is more viable than the claim says, and its outcome can be computed exactly for free.** The claim's mechanism is misdescribed: a shorter horizon does not cut discovery time, it cuts the time after discovery, so fixed discovery overheads weigh more. At 6 × 6 the follower's overhead is small (first entry at A: median 169 ticks against the oracle's 58), and the steady-state ratio is 0.947 × 7.15 ÷ 17.71 = 0.38, the same as the current 0.389. Using the walk's per-maze later-leg rates (0.18 to 1.97, mean about 0.9) and first-entry medians (mostly 200 to 1 300 ticks) from the calibrate file, my first-order estimate at H = 1 800 is:

| | H = 2 400 (measured) | H = 1 800 (estimate) |
|---|---|---|
| walk, B_max | 2.34 | about 1.7 |
| follower | 16.5 | 11 to 12 |
| oracle | 42.5 | about 32 |
| G2a | 0.389 | 0.35 to 0.37 |

So G1b would pass and G2a would stay narrow, a possible fail on a fresh block, not a probable one. The point is that no GPU is needed to settle this. Every condition's per-wey `visit_tick` array is saved in `runs/e3d/records/` and hashed in the calibrate file, and the horizon only stops the run (the tick limit in `wormwars/world.py:1286`). Truncating those arrays at any H' and recomputing the full gate with intervals is exact, provided one check passes: that nothing in the maze shuttle's dynamics reads the tick limit (the one other use I found allocates buffers by it). That analysis costs an hour of scripting and answers option 2 definitively.

**Option 3 is the most invasive and the one that really risks forking paths.** It needs a grid over scent reach or trail persistence, and any change to the scent field forces a re-qualification of the navigation module that E4 relies on. It also changes the colony signal the roadmap wants as a control dimension. Not recommended.

**Option 4, k_r = 0, is right.** At k_r = 0 the blind ceiling is lowest (2.34), G1a and G2a are best (0.141, 0.389), the open share is lowest (0.69), and the design's own rule prefers the smallest k_r. The seed's margin over the blind family is 6.7 visits, ample.

**Unlisted:** fewer openings around each goal (E3d's second owner bullet) attacks G1b directly but needs a new construction with its own island-safety proof. Too costly for the gain.

## 2. What E4's design must do

The claim's control structure is the weak part. "Require E4's effects to clear the random walk" is a category error: E4's effects are differences between arms (cross-links against none) and ablation contrasts. A blind reference is something each arm's *navigation* must clear as a precondition, not something the effect clears.

- **Record the inheritance as a decision.** A D-numbered task-design decision that quotes G1b's failure and the walk's 41 to 45 % round-trip share, and says E3d's verdict stands.
- **Fold the gate into E4 as a precondition stage.** Play the scripted blind family and the navigators on E4's own test block before any evolution, at the fixed H and k_r. Declare in advance which criteria stop E4 if they fail. The ratio criteria at least. G1b reported at 2.0, gated or not by the owner's choice, fixed first. This costs about 0.3 GPU-hours and removes the need for an E3f.
- **Choose H from the truncation analysis, labelled exploratory.** If some H' between 1 600 and 2 000 passes every criterion on E3d's block with margin, E4 may adopt it. The precondition stage then confirms it on fresh mazes.
- **The real blind ceiling is evolved, not scripted.** If any E4 arm trains from random weights, add a noses-removed arm from generation 0 at matched budget. If every arm starts from the seed, the coverage trap is weak (blind coverage is a drop from 9 to under 2.5) and the probe below suffices.
- **Per-champion nose classes as an evaluability rule.** E3c's registered classification (retained fraction with noses removed) decides whether a champion enters the primary contrast. Fix the rule first.
- **Arm-level precondition.** Each navigator arm's champion mean must exceed the best blind reference by E3c's dual margin, max(0.5, 0.10 × the arm). An arm that fails reads "not evaluable: coverage".
- **Report trails-off for the seed and every champion.** On this family the scripted follower's navigation is trail-borne (2.93 off against 16.5 on). E4's question about information crossing between modules is then partly about trail signals read through the same nose channels. Say so.

## 3. Where the claim is wrong on the facts

- **"Option 2 would probably fail G2a because a shorter horizon cuts the follower's discovery time."** Wrong mechanism and overstated size. The records put G2a at roughly 0.35 to 0.38 at H = 1 800.
- **"Option 1 would need the follower's ratio to more than double."** True (0.158 to ⅓) but understated. The steady-state ratio is 0.13 to 0.16, so a longer horizon does not raise it at all.
- **"A third tuning round risks a garden of forking paths."** Task validation against a fixed gate is engineering, not hypothesis testing. The cost of another round is calendar time and the owner's known concern about process weight, not statistical validity. E4's own pre-registration is where forking paths matter, and binding it before the run handles that.
- **Fixed references "about 2.3" carried from E3d's calibration block.** E4 plays fresh mazes. The references must be re-played on E4's blocks, not quoted.
- The rest checks out: the follower at 6.5 to 7.1 × B_max, the seed at 3.9 to 4.2 ×, G2a at 0.37 to 0.39 with intervals crossing ⅓, wall-following defeated for the tested controllers and starts, and G1b's level a choice rather than a measurement.

**What I did not do:** rerun any rollout, open the local `.npz` records, or recompute the bootstrap. The horizon estimates are first-order arithmetic from the committed summaries and per-maze records, and the truncation analysis I recommend would replace them with exact numbers.