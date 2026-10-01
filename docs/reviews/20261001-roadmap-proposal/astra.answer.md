**Verdict: adopt with changes.** Deferring the ring is justified. The comparator experiment is a sensible next step, but the proposal overstates several diagnostic conclusions and leaves its controls and E3 fallback ambiguous.

I reviewed `cc13ff8`, the working-copy v3, relevant code and records, and both rounds of earlier reviews. Nothing was modified or run.

**Must-fix items**

1. **“Why a change” — respect E2d’s correction.** Replace “no evolved champion … steers” with “none meets the stereo-use criterion; 43 show no material benefit and four show small detectable benefits.” The stronger wording was explicitly withdrawn in [E2d’s corrections](/D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/RESULTS.md:249). Likewise, E1 establishes that memory is *unnecessary for high performance here*, not that memory cannot help with continuously available cues.

2. **E4s-0, comparator — specify an implementable circuit.** The equations inject `a(L−R)` directly. [graft.py](/D:/Claude/random/wormWars/wormwars/graft.py) currently assigns each added nose one scent channel; chemical connections transmit `tanh(v)`, and the motor neurons introduce further dynamics and clipping. Specify where subtraction and amplification occur. Either implement them through declared synapses or disclose fixed sensory preprocessing. Map `b` and `b_m` through the actual motor interface before calling this a two-neuron graft within the existing bounds.

3. **E4s-0 — narrow the interpretations and restore qualification.** A residual sweep tests an externally inserted policy change, not whether ordinary mutations can produce it. A dip demonstrates a valley along that intervention, not every evolutionary route. Weak intermediate derivatives identify attenuated responses, not necessarily lost information. Keep controlled transients and reversals, especially with recurrence: increased gain also brings slower responses. Before evolution, retain fresh-world performance **and stereo-use** qualification from v3. Replace “no comparator within ±3” with “none of the tested candidates passed within the search budget”; failure does not establish a bounds limitation.

4. **E4s-1, arms — name the confirmatory comparisons and define the cuts.** “The main arm and its paired controls” does not identify them. Main versus permanently disconnected output tests usefulness; main versus a matched random graft addresses the designed seed versus added capacity. Match parameter count, sensory/motor access and mutation treatment—not merely neuron count. Zero initialization must apply to **additional integration edges**, preserving the seed’s required motor connections. The disconnected control must block every graft-to-host route throughout evolution.

5. **E4s-1, outcomes — these are not an exclusive partition.** Retention can coexist with redundancy; erosion can coexist with host acquisition. Measure module competence, causal dependence and host competence separately, retaining v3’s generation-0/final/champion distinctions and uncertain outcomes. Host-only improvement over generation 0 establishes **acquisition**, not transfer from the graft. Compare against paired hosts evolved without functional graft output before claiming graft-assisted acquisition. Freezing module parameters also does not guarantee functional retention when the host and motor relays evolve.

6. **E3 and “What would change” — reconcile the fallback.** One section selects 04a run 2 when no retained module exists; another selects the frozen graft. State one rule and identify the artifact: complete evolved host-plus-graft, or comparator plus carrier. A comparator useful inside one evolved host is not automatically portable. Require E3’s own navigation positive control whichever artifact is used.

7. **“Other changes” — distinguish implementation from completed validation.** V3 explicitly leaves CUDA and score-equivalence checks pending. Preserve those gates when superseding it; “already built and tested” is insufficient. Count diagnostics, tuning, equivalence work and evaluation in the declared accounting. The 96-hour ceiling should remain a ceiling, not a reason to consume the remainder.

**Answers to the six questions**

1. **Sequence:** Yes—bounded diagnostics, comparator, ring deferred. E4s-2 should require demonstrated demand for directional memory.
2. **Measurements:** Keep all three, with the narrower readings above. Use paired worlds and uncertainty; extend the residual sweep to 64 and 256 to cover E1’s useful high-gain range. Prioritize actual closed-loop competence over increasingly elaborate static probes.
3. **Option (a):** Honestly framed. Temporal sensing and wider bounds are separate interventions, not an exhaustive choice forced by a failed small-circuit search.
4. **Arms/outcomes:** Keep frozen, reduced and uniform mutation treatments; clarify which comparisons are confirmatory. Repair the outcome definitions. Adopt interface calibration and controlled initialization; no need to add another optimizer now.
5. **E3 timing:** Start its task design, scripted positive control and minimal frozen 04a-based prototype in parallel. Do not make shipping the first A/B organism depend on finishing the graft-retention study. Keep its formal controller comparison separately frozen.
6. **Literature:** Several claims need qualification; details follow.

**Literature claims checked or requiring correction**

- **Opus’s gain-ceiling explanation is wrong.** A bound for one short path is not a bound for a recurrent network with converging paths. It also does not explain measured gain near 0.1. I checked the brain equations, gain-probe summary and E1 curve: `k≈256` approaches the performance plateau, but substantially lower gains already navigate. Do not import this argument as a diagnosis.

- **“Mirror-symmetric parameters” needs its axis stated.** Izquierdo–Beer explicitly uses dorsal/ventral symmetry while allowing left/right asymmetry. Opus’s allegation that these statements contradict each other is wrong. I checked the Methods and AIY analysis. Its ±15 ranges are real, but are not directly interchangeable with WormWars’s differently scaled dynamics. [Primary paper](https://doi.org/10.1371/journal.pcbi.1002890)

- **Adden does not establish that four ordinary WormWars neurons suffice.** Its rate model includes explicit threshold-triggered switching logic. The input-remapping result is supported and relevant; portability of the four-unit implementation is not. I checked the model-description and remapping passages. [Primary paper](https://doi.org/10.1162/neco_a_01540)

- **Noorman supports the pinning/tuning concern, not inevitable evolutionary erosion.** The analysed implementation uses threshold-linear dynamics. A tanh port requires revalidation. I checked the model and limitations; the released code declares MIT licensing. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11537979/), [license](https://raw.githubusercontent.com/HermundstadLab/DiscreteRingAttractor/main/LICENSE)

- **Tomko–Harvey supports cautious initialization, not universally optimal zero weights.** Its incremental-evolution advantage depends on the task and mutation regime. It does not justify disconnecting an intentionally functional seed. I checked its methods and discussion. [Primary paper](https://users.sussex.ac.uk/~inmanh/do-not-disturb.pdf)

- **Keep proposed equations labelled as proposals.** Astra explicitly labels both the comparator and continuous-time latch as its own constructions. The latch still needs initialization, pulse-duration and simultaneous-input tests. Hironaka–Sumi’s repository declares MIT, but I did not reproduce it; call it a candidate executable baseline until that check succeeds. [Repository](https://github.com/118-Oganesson/c_elegans_chemotaxis)