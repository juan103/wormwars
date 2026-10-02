**Verdict: revise.** I checked `roadmap` at `0794db6`, both v2.1 reviews, D160, the code and training records. I reproduced the geometry JSON and ran in-memory CPU checks through `Brain.step`. No files changed.

Most v2.1 items are resolved at design level: the no-latch/q-zero distinction, corrected switching number, startup coverage, explicit sampler and null wording, census qualification and threshold, ordered S2-b outcomes, B-task’s parameters and reading, joint source sampling, corrected “blind” wording, neuron count, cap and reduction order.

The unresolved or newly introduced problems are:

1. **The hold test still rejects a correct latch.** It now compares against the state immediately after leaving a source, while that state is still relaxing from the visit drive. With the engineered organism, `Brain.step` gives:

   | Visit signal duration | q when signal ends | Settled q |
   |---|---:|---:|
   | 2 ticks | −3.0533 | −1.9150 |
   | 4 ticks | −4.7145 | −1.9150 |

   Those changes are 37% and 59%, despite successful retention. Measuring after the first unforced tick also fails the 10% rule. Use a predefined settling allowance and the champion’s own equilibrium/function as reference. Test both stored states: the present naturalistic hold only follows the first confirmed A visit. Also handle worlds that visit but never leave, late departures with negligible hold duration, and “not read” results explicitly. [Hold specification](D:/Claude/random/wormWars/docs/E3/DESIGN.md:227)

2. **The dynamical classification is mathematically wrong.** “Three fixed points **and** reachable by the levels; monostable otherwise” conflates bistability with controllability. For example, \(w_{qq}=2,\ b_q=0,\ w_{aq}=w_{bq}=0\) remains bistable although neither level switches it. Classify equilibrium structure independently, then record setting/reachability and retention.

   Champion-specific clamp values and mirrored polarity are improvements. The release test also addresses the previous clamp-only objection. But its gain-ratio rule needs a nondegenerate functional criterion: two zero gains satisfy the written inequality. Define the response measurement without resetting away the retained state, and specify missing or indistinguishable phase medians. [Classification and states](D:/Claude/random/wormWars/docs/E3/DESIGN.md:282)

3. **The new distribution is not functionally near the ungated pair.** Independent comparator biases with SD 0.5 break push-pull balance; unequal gate weights add further offsets. Using the frozen L1 wiring, 100,000 independent draws from the specified distribution gave **83.5% with a clipped turn command at settled zero differential input**. This is an equilibrium calculation, not a training result.

   The custom sampler and cautious 0-of-8 wording resolve the earlier implementation and interpretation issues. They do not establish a benign starting population. Either change initialization to preserve approximate comparator balance—parameters can still mutate independently—or remove the “close to no-latch” claim and acknowledge this starting behavior. [Initialization](D:/Claude/random/wormWars/docs/E3/DESIGN.md:256)

4. **The geometry’s component-coverage claim compares different units.** The script correctly reproduces the raw head scent minimum, 0.0285655. But Task N multiplies scent by **0.35**, giving approximately **0.0100**, below the component tests’ minimum injected level of 0.02. Actual nose readings also depend on heading and interpolation. The Euclidean cap and acceptance calculation are sound; the claimed qualification is not. Extend component coverage to the actual scaled nose range, or change the geometry/scaling. [Scent scaling](D:/Claude/random/wormWars/wormwars/world.py:707)

The other specifically requested checks pass:

- **No-latch:** zero comparator biases and gate edges correctly produce two ungated L1 modules. Keeping the biased q-zero construction as a descriptive ablation is appropriate.
- **B-task:** the specification gives **171 free parameters**: 121 internal weights, 32 output weights, nine biases and nine time constants. Its descriptive comparison is defined. The 121-edge mask permits recurrent inputs into the relays; only their intrinsic parameters remain fixed.
- **Budget/reductions:** measured batches are 1.3545–1.4308 hours. The stated scaling and allowances yield approximately **13.0–13.6 hours**, consistent with 13.4. Reductions now reach eight GA runs plus four paired random-sampling runs.

Beyond those repairs, pre-registration must pin only these outcome-sensitive choices:

- Exact control genomes and B-shared wiring; blind-policy settings, geometric maximum and gate denominators.
- Complete assay protocols: state initialization, settling, both-state mapping, hysteresis schedule, gain measurement, delay calculation, reset timing and unread-case rules.
- Which genomes receive validation at the final checkpoint, champion tie-breaking, and random sampling’s selection-world allocation.
- World-block spans, random-stream sharing, census screening/counting rules and exact confidence-interval procedures.
- Projection reserve/admission rules, retained Stage 3 runs, interpretation of reduced-budget B-task comparisons, and refusal to start if the minimum configuration exceeds the cap.