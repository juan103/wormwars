**Verdict: revise.** The logic of v2 is sound and every structural round-1 finding is addressed. What fails is the sizing and the gate after the task change: the budget uses a throughput measured on one-wey Task N worlds, so T1 costs about five times what §7 says; the relief gate compares a controller with itself; and the registered thresholds are still written in Task N's units. These are not wording fixes, because they set G, W, the graph counts, the cap and the go condition.

## Findings

1. **§7, high. The throughput is Task N's, not T1's.** 03a's 892 episodes per second is from a one-wey world with no food field. T1 is a 20-wey odour world. 03's own pilot timed T1-class fitness at about 66 s per graph for 704 strain-cells on 16 worlds, which is about 171 episodes per second with 4 096-world chunks (`experiments/03-generation0/pilot.json:40681`, `scripts/exp03.py:142-147`, `:107`).

   | Rate used | Formal evaluation, 12.78 M episodes |
   |---|---|
   | 892/s, 03a Task N | 4.0 h |
   | 171/s, 03 T1 | 20.8 h |
   | 171/s, SH dropped | 10.5 h |

   Add calibration and the probe and the plan is about 22 h against a 6 h cap. Re-size §4 from 03's rate before the pilot is registered, and keep the plan to time a T1 smoke at the formal composition before the cap is fixed.

2. **§3, high. The relief gate is an identity.** The only memory family is `MemoryKinesis`, one tick. 02's tuned M has `fall_threshold` 0.0, so `LevelKinesis` reading the bit is exactly `MemoryKinesis` (`experiments/02-screening/diagnostics.json:8037-8045`). "Best memory with the bit minus best memoryless with the bit" therefore compares a controller with itself and the ±0.3 equivalence passes by construction. My round-1 finding 8 assumed 03a's KTS, the exponential-average memory with a tuned time constant (`wormwars/e03a/probe.py:102-116`). Port that to 02's family as a nested member, with T = 1 recovering `MemoryKinesis`, and tune T on the tuning worlds. Then the gate asks the real question: does memory beyond one tick add more than the margin.

3. **§2 to §6, medium. Units and zero share are Task N leftovers.** T1's score is surviving energy as a fraction of the start (`wormwars/evo/rollout.py:54-61`). A swarm that never eats ends near 0.42 and the score is zero only when all 20 weys die. "Targets", "count", "zero share" and the "graded secondary score" do not apply. The 0.5 lower bound and the ±0.3 margin were set against Task N's 1.64-target gap. Restate them in T1's score and argue them again. 02's exploration record supports a safe level gate: tuned graded kinesis scored 2.101 against binary kinesis 2.117, and memory beat graded kinesis by +0.98 (`experiments/02-screening/exploration/README.md:21-23`).

4. **§5 B, medium. B's baseline is level, A's is sham.** The sham exists because relief adds drive whether or not the bit carries information. That confound reaches the selected decile as much as ρ. Make U_g = T_sham − T_relief the primary and report level − relief descriptively, or say why B should differ from A.

5. **§3 and §6, medium. The order is circular.** The sham's rates come from the pilot, a neural GPU run. The gate, which includes a sham test, runs "before any neural run". Register the order: level and relief parts of the gate, then the pilot, then the sham part, then the formal run. Also state that the rates are measured on level trajectories where no bit is injected, that behaviour under relief changes them, and that one population rate does not match each genome's drive. A stationary genome has no falls.

6. **§3, medium. The bit's reading contradicts itself.** "The one the brain receives: after any food probe, before gain and clamp" cannot both hold. The brain receives the gained, clamped current (`wormwars/world.py:880-892`), and `MemoryKinesis` reads that current (`wormwars/exp02/scripted.py:43`). Define the bit on the injected food current after the clamp. The identity with `MemoryKinesis` then holds exactly, including when the clamp binds.

7. **§4 and §7, medium. "Graphs before worlds" undercuts B.** At 32 graphs the rank floor is 1/33, above Holm's 0.025, so B could pass only after A passes. Register the cut order as SH first, then G, then W, with the primary ensemble kept at 64 graphs. Dropping SH also halves the cost in finding 1.

8. **Rule 7, medium. The engine change needs its equivalence check.** `food_fell` adds a signal, a per-wey previous-reading state and a keyed Markov stream. Under level the new interface injects zero at ASK, so T1 scores for the same genomes and composition must match the pinned interface. Register that check and its tolerance.

9. **§4 History, low. The bank is already T1's.** 03's bank was taken from T1 generation-0 replays with mono food at 0.2234 on both sides (`scripts/exp03.py:498`, `experiments/03-generation0/pilot.json:2-18`). No transfer needs stating, and the "T1-specific bank" sensitivity analysis duplicates the primary. Say where the bank came from instead.

10. **§2 and §6, low. The T1 distribution exists.** 03 measured T1-M0 fitness for 256 random genomes on 16 worlds for every graph, P3's primary cell. Use it now for provisional G, W and δ_A in score units rather than citing T0-M0, and check whether the committed report holds the per-genome values.

11. **§3 Gate, low. The scripted brain cannot read the bit yet.** `ScriptedBrain` reads only the food currents (`wormwars/exp02/scripted.py:27-28`, `:43`). The bit-reading families need an extension and a test. Astra raised this in round 1 and v2 does not list it. The sham gate passes by nesting, since weight zero on the bit is in the family. Call it a sanity check.

12. **§3, low. The bit's magnitude is unexplained.** Gain 1.0 times input gain 1.0 gives one current unit against a mean food current of 0.22 and a clamp of 5.0. That is about 4.5 times the food scale, close to a collision input. Registering it is fine, but give the reason.

13. **§2 and §4, low. Composition and padding.** Padding is pinned off by `task_config`, not merely inapplicable (`wormwars/exp02/grid.py:56`). State the batch composition, including 20 weys per world, and whether selection and test banks run in one rollout.

14. **§5, low. Still undecided for the pre-registration:** A's aggregation over graphs, how a degenerate graph is "kept", whether 03's effect margin is imported into B's rank rule, N2's own ASK direct read-out as the cap value, calibration genomes against fitness genomes, and every world-id range.

## The four requested answers

**Round-1 findings.** 1 zero-inflated fitness: resolved in substance, the leftover wording is finding 3. 2 sham: resolved. 3 ASK cap: resolved. 4 A1 and A2: resolved, aggregation statistic pending. 5 directional predictor: resolved by the merge. 6 manipulation check: resolved. 7 multiplicity: resolved, effect margin pending. 8 relief gate identity: not resolved, and now vacuous, finding 2. Disjointness: partly, selection and test only.

**The task change.** T1 is right for generation 0: the score is graded by construction, memory pays by 0.94 to 0.98, and the controllers nest. The bank is T1-native, which removes a concern rather than adding one. The multi-wey world introduces the cost in finding 1 and a per-wey bit, nothing else. The scripted gate breaks as in findings 2 and 11. The pheromone silence holds in code: the sense scale is zero for T1 at `wormwars/exp02/grid.py:61`, so ASK's current is zero while the field is still deposited and costs compute only.

**The merged points.** H primary with H_dir as key secondary: accept, H is what the thread claims and H_dir's reading should be pre-worded too. SH-mirror-ASK primary with SH secondary: accept, the pilot should time the sampler. Frozen-champion check separate, exploratory and ungated: accept. Cap at most 6 h set from the pilot: cannot accept as written, since neither 4 nor 6 h holds the provisional design at T1's measured rate; re-size first, then set the cap from a timed T1 smoke.

**Readiness.** Not ready for the pilot's registration. Blocking: the re-sized budget and cut order, the slow-memory family and bit-reading scripted brain, the thresholds in T1's units, the bit's definition, B's baseline, the gate-pilot order, and the pilot's numeric rules for W, G and δ_A. Once those are fixed, the pre-registration still needs finding 14.