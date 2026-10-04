**This can answer which parameter changes carry the gain, and whether useful goal switching survives, within five hours. Draft 1 needs changes before implementation.** Its main weaknesses are the latch lesion, the tracking measure, and the absence of trail-condition attribution.

I checked the implementation and committed records, and independently verified that all 16 local final T champion genomes match their recorded parameter hashes. I did not run simulations.

**1. The partitions cover the mutable set correctly, but their names imply cleaner functional boundaries than exist.**

Against [`tuning.scales`](/D:/Claude/random/wormWars/wormwars/e3/tuning.py:49), its `_grafted` helper, and the actual L1 wiring, there are **65 mutable scalars: 47 chemical weights, 9 time constants and 9 biases**.

| Partition | Group | Scalars |
|---|---|---:|
| Functional | sensing | 20 |
| | gating | 8 |
| | output | 32 |
| | latch | 5 |
| Side | module A | 28 |
| | module B | 28 |
| | selector | 9 |

Both partitions are exhaustive and disjoint as written.

Putting comparator biases with gating is defensible: the seed implements gating through the combination of comparator bias and q input. But those biases also change sensory sensitivity and tonic motor output. Similarly, comparator τ affects responses to both noses and q. Call these **parameter groups defined from the seed’s design**, not isolated functions. A large “gating” contribution would not by itself demonstrate increased selector use.

The side partition puts comparator biases inside A/B, whereas the functional partition puts them inside gating. Consequently, their “selector” and “gating” numbers answer different questions; they are not alternative estimates of the same quantity.

Keep frozen parameters outside both attribution partitions. However, **frozen does not mean irrelevant to the gain**: tuned comparator outputs can change how the unchanged reflex affects the motors. D193 explicitly mentioned the reflex and turn biases, and the current plan does not adequately diagnose that possibility.

**2. Keep the exhaustive hybrid experiment and Shapley values. Change what “exact attribution” means.**

These hybrids are legitimate interventions. Being outside the evolutionary trajectory does not invalidate their measured performance. It limits their interpretation: they reveal effects and incompatibilities of seed–champion substitutions, not the historical route by which evolution improved performance.

Shapley values are an exact allocation **for this baseline, partition and hybrid-performance table**. They are not uniquely correct biological or computational contributions. Strongly coadapted parameters, including coordinated changes in latch coding, can produce poor hybrids and large opposing allocations.

Reversion and transplant are the right companions:

- Reversion asks whether the champion benefits from retaining a group’s tuned values.
- Transplant asks whether those values help in the seed background.
- Neither measures whether the underlying component is necessary or sufficient for behaviour.

For four groups and 16 champions, exhaustive evaluation is preferable to an approximate attribution method. Keep the interaction terms, but put endpoint effects and major interactions ahead of an undifferentiated table of higher-order terms.

Replace §8’s “share of the gain attributable to…” with something like:

> “Under the specified seed–champion substitutions, this group’s Shapley allocation was X visits per wey, or Y units of the seed’s shared-trail mean.”

Report signed contributions. They can be negative or exceed the net gain; percentages of a small or negative champion gain are misleading.

Also strengthen the calculator tests. **“Shapley values sum to the gain” is insufficient:** a function returning one quarter of the gain for every group passes. Include hand-calculated additive, dummy-group, pure pair-interaction and higher-order-interaction cases, plus reconstruction of the hybrid table from the dividends.

**3. Replace “latch frozen”; distinguish removal of q input from removal of dynamic selection.**

The proposed relay cut does **not** freeze q at a meaningful initial state.

[`Brain.initial_state`](/D:/Claude/random/wormWars/wormwars/brain.py:402) starts at zero. [`maze_organisms.brain`](/D:/Claude/random/wormWars/wormwars/e3/maze_organisms.py:81) only supplies a special start for the oscillator, which these organisms lack. E3b-1’s batched evaluation uses plain `Brain`.

After cutting relay inputs, q still follows its self-edge, bias and τ. Therefore:

- The seed remains at q = 0, its unstable equilibrium, without the relay-delivered start cue.
- Champions with nonzero q bias move away from zero toward a bias-selected state.

The recorded champions all have nonzero q bias. This is a **visit-input disconnection with altered startup**, not a frozen operating latch.

Replace it with **two fixed-state conditions**, holding q at each organism’s own lower and upper stable equilibrium. Existing [`Brain.clamp`](/D:/Claude/random/wormWars/wormwars/brain.py:364) supports this. Initialize q to the clamped value before the first substep as well. Report both conditions; do not select the more damaging one. The relay cut can remain as a separate, correctly named diagnostic.

“Gate cut” is well-defined as setting four q→comparator weights to zero while preserving tuned biases. It is **not** equivalent to “both modules always on”: [`organism.no_latch`](/D:/Claude/random/wormWars/wormwars/e3/organism.py:89) also zeros comparator biases. A gate-cut cost can reflect loss of a useful constant operating offset, without useful switching. The two q clamps provide the essential companion.

The A-output, B-output and both-output lesions are correctly specified. Add an equivalence check: with both outputs silenced, every champion should behave like the seed with both outputs silenced, within the declared numerical conditions. All surviving motor-driving parameters are frozen.

I would add two inexpensive diagnostics before expanding the side attribution:

- **Remove the four scent inputs to A/B noses**, retaining biases, τ, latch inputs and wall sensing. This tests whether scent-driven modulation matters beyond the circuit’s tonic output.
- **Remove the reflex’s varying wall response while preserving its resting contribution**, for example by holding its neurons at their resting states.

Simply zeroing W2’s outputs also removes its tonic contribution. The carrier biases explicitly compensate for that contribution in [`carrier_turn`](/D:/Claude/random/wormWars/wormwars/e3/maze_organisms.py:136), so such a lesion mixes wall-response loss with a substantial resting-turn change.

This matters empirically: the saved probes show resting commands above the seed’s approximately 0.4 for every final T champion; T-F runs 2, 3 and 7 are at +1 in both imposed latch states. That supports investigating tonic steering, but does not establish that it explains the gain.

**4. Sign agreement is useful descriptive data, but insufficient evidence of tracking.**

All 16 recorded final champions have stable equilibria on opposite sides of zero, so sign(q) is a reasonable first reading for these endpoints. Fix the following before implementing it:

- **Timing:** [`World.tick`](/D:/Claude/random/wormWars/wormwars/world.py:937) updates the brain before movement, while [`MazeWorld._post_move`](/D:/Claude/random/wormWars/wormwars/e3/maze_world.py:383) changes goals before the recorder runs. On a visit tick, the recorder sees q computed without the new visit cue alongside the newly switched goal. Specify whether agreement uses the goal governing that tick’s action or the newly assigned goal. Report event-aligned switching latency with this delay accounted for.
- **Per-wey mapping:** decode `world.v` through the strain assignment into world/wey order, then compare with `world.goal[world, wey]`. Test multiple weys in one colony with different goals, and multiple strains.
- **Undecided states:** the existing [`MIN_SEPARATION = 0.1`](/D:/Claude/random/wormWars/wormwars/e3/latch.py:18) is a minimum distance between stable roots. It is not an established undecided band around zero. Define the band explicitly, preferably with a sensitivity reading.
- **Coding flips:** calculate both mappings explicitly. With undecided ticks excluded from either match category, flipped agreement is not simply `1 − agreement` on the original denominator.
- **Denominators:** report eligible weys, ticks and transitions, including organisms with no qualifying observations.

Most importantly, **a wey that visits A once, then remains seeking B with q permanently negative can score almost perfect agreement without ever switching again**.

Add agreement separately for goals A and B, an equally weighted A/B summary, and switching success/latency after confirmed visits in both directions. Report goal occupancy and transition counts alongside them. Aggregate uncertainty over colonies/mazes, not individual ticks.

High agreement plus harm from both constant-q conditions would be substantially stronger evidence of useful dynamic selection than either alone.

**5. The fresh block is appropriate; the larger contamination risk is runner reuse.**

Ids 7000–7255 are disjoint from the E3b-0 and E3b-1 blocks and training ranges I inspected. I found no recorded use of this block. Test identities using the maze seed and relevant configuration, not numeric ids alone. Bound the smoke block explicitly.

There is a concrete implementation trap: [`e3b1.py` calls `configure()` during import](/D:/Claude/random/wormWars/scripts/e3b1.py:120), configuring its E2 stage frame for E3b-1’s output directories and records. Its chunk-path helper also targets E3b-1.

Give E3b-2 its own experiment directory, run directory, compute ledger, markers and cache paths. Treat E3b-1 as immutable input. Add a test that every output destination lies outside the historical directories.

Do not reuse E3b-1’s chunk-resume validation unchanged: it checks organism names, not the complete evaluation specification. Resume must validate maze ids, configuration, condition, genome/intervention identity and batch composition.

Two smaller input corrections:

- “Index 124/299” means **generation index**, not `champions.json`’s `index`, which identifies the selected member of the population.
- The seed’s saved resting-turn readings are in E3b-0’s `report.json`; E3b-1’s `evaluate.probes` contains champions. Add that input hash if §5E reads the existing seed measurements.

**6. Make trail-condition attribution and later-leg outcomes part of the core. N/R are optional context.**

I would run the **functional hybrid cube under both shared and none**. This is more informative than the second partition.

Use one denominator—the fresh seed’s shared mean—and subtract the seed baseline within each condition:

\[
v_a(S)=\frac{\overline Y_a(S)-\overline Y_a(\text{seed})}
{\overline Y_{\rm shared}(\text{seed})}.
\]

Then the difference between shared and none Shapley allocations decomposes the change in trail dependence exactly under this intervention scheme. Report the underlying raw means too.

This addresses a central existing result: T-F’s gain is accompanied by increased trail dependence; T-A’s is not. Shared-only attribution cannot say which parameter changes account for that distinction. “None” removes access to both own and peer trails, so this would not isolate peer-specific effects.

Make **later-leg rate, unvisited share and round-trip share** explicit outputs for hybrids and lesions, rather than “where noted.” [`summary_arrays`](/D:/Claude/random/wormWars/scripts/e3b1.py:1053) already computes them. The unvisited share is necessary because later-leg rate conditions on making a first visit.

Omitting N and R is acceptable for the narrow question about the 16 T endpoints. I would not require full hybrid cubes for them. If budget remains, their intact shared/none results and core selector diagnostics are useful context: there are **four published N champions and two R champions**. Include the degraded start in any R comparison. T-F’s generation-124 representatives are another optional extension, especially if the question expands to what changed with longer training.

For reporting, retain schedule-specific results prominently. State that run-level t intervals are conditional on this maze block. If claiming stability across maze draws, add paired maze resampling that preserves pairing across all variants and champions.

Finally, add a decision interpretation. E3b-2 cannot establish the benefit of modular assembly or information transfer. It can establish whether those next experiments have a suitable starting organism. If dynamic selection appears dispensable, redesign or stronger controls may come before either. **An assembly comparison can itself test the value of engineered modular structure; its legitimacy does not require assuming that value in advance.**

**7. Five hours looks credible, but revise the projection and priority order.**

The timing is supported: [`project.json`](/D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/project.json:399) records **148.51 seconds** for the relevant evaluation chunk. Thirty-nine such chunks are approximately **1.61 hours**.

Adding functional attribution under none costs approximately another 16 chunks, or **0.66 hours** at that rate. The extra clamp and sensory/reflex conditions should still leave a plausible margin. This is a projection, not a measured guarantee.

Benchmark the actual GPU workload on smoke mazes, including recorder overhead, saving and representative intervention batches. A CPU benchmark cannot establish GPU throughput. Keep recorder counters on the GPU and transfer summaries at chunk completion. Count CPU work and failed attempts consistently with the existing accounting convention.

Dropping the side partition first is sensible. Preserve shared/none functional attribution, the corrected selector lesions, tracking and replication ahead of optional N/R or historical-timepoint extensions. Set admission from **spent time plus projected remaining work and reserve**.

Also fix batch compositions and endpoint reuse in advance. Bitwise-identical endpoint genomes do not guarantee identical CUDA outcomes across different compositions. Require recorder-on/off equivalence and declare any engine-equivalence tolerance before running those checks.

**Verdict: go with changes**—correct the latch interventions and recorder; add functional attribution under none and explicit later-leg reporting; include the tonic-steering/reflex diagnostics; narrow the attribution wording; isolate E3b-2’s outputs; and benchmark the revised core.