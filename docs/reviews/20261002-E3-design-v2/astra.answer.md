**Verdict: revise.** The latch and gate are now numerically credible. The budget and several experimental definitions remain unresolved.

I checked `roadmap` commit `5aaa314`, both reviews, D156, the implementation and E4s records. I also ran in-memory CPU component checks using `Brain.step`. No files changed.

**V1 must-fix status:**

| Item | Status |
|---|---|
| Pulse strength and latch initialization | Resolved |
| Entry, rearming and event ledger | Mostly resolved; movement-to-input latency remains unspecified |
| Gate bias, bounds and component thresholds | Arithmetic resolved; measurement protocol still open |
| L1 positive control, scripted gains, blind circle | Resolved |
| Causal memory tests | Added; criteria distinguishing retention from decay remain incomplete |
| Drop the N2 interface | Resolved |
| Stage 2 initialization, mutation, census, random sampling | Addressed; parameter ownership/tying still ambiguous |
| Stage 3 host freeze and descriptive scope | Resolved; initialization and component-training allocation remain open |
| B-shared/B-task | Partial: controller-owned memory resolved; capacity matching and budget unresolved |
| Compute budget | **Not resolved** |
| Narrow engine-equivalence claim | Resolved at design level |
| Geometry | Improved; Fable’s requested maximum spawn distance remains absent |
| Graft generalization, copied L1 parameters, dtypes | First two addressed; **dtypes are not declared**, despite the change map |

The concrete findings are:

1. **Latch numbers work.** With the specified 32-substep recurrence, opposite-state switching crosses zero after **0.75 ticks**; after one tick, \(q=\pm0.8122\). Two- and four-tick levels also switch. The five-tick start cue produces \(q≈4.9592\), subsequently relaxing toward \(1.9150\). It establishes the correct sign, but the initial condition is temporarily overdriven, so include startup in the component tests. Specify that occupancy after movement at tick \(t\) supplies the next tick’s input. [Latch specification](D:/Claude/random/wormWars/docs/E3/DESIGN.md:50)

2. **Gate arithmetic passes a reasonable small-signal check.** The actual settled output is \(\tanh(q^*)≈0.957504\), giving offsets **+0.001008** and **−3.829008** with bias −1.914. Using \(d=±0.001\), common levels 0.02–0.35 and carrier turn 0.2, CPU checks gave active \(K_D≈31.60–35.62\), inactive \(K_D≈0.059–0.068\): approximately **0.19% leakage**. Thus the 30/1% thresholds are feasible. But define the probe amplitude, common levels, preconditioning, other module’s input, and recovery measurement. Use **absolute** leakage and offset limits; a large negative gain must not pass. Shared nonlinear motor neurons also make “each module’s turn contribution” require an explicit definition. [Component requirements](D:/Claude/random/wormWars/docs/E3/DESIGN.md:87)

3. **The budget adds correctly to 15.5 hours, but its scaling is wrong.** E4s-1 used **8 worlds/genome**; v2 specifies 16 but doubles cost only for 300→600 ticks. Actual throughput needs projection; proportional scaling requires another factor of two for training work. Separately, B-task receives Stage 2 **plus** Stage 3’s budget in the text, yet only one stage’s **3.2 hours** in the table. Even before correcting world counts, that line should be **6.4 hours** under the stated assumptions. Account explicitly for B-shared and component-training evaluations. [Budget](D:/Claude/random/wormWars/docs/E3/DESIGN.md:163), [E4s training configuration](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md:64)

4. **Seven selector parameters requires unstated tying.** The count works only with **one shared comparator bias**, tied gate edges within each pair, and opposing visit gains tied through one \(w_s\). Separate biases per pair give eight parameters; per comparator gives ten. Also specify how \(w_s\) evolves: existing `Genome.mutate` does not mutate sensory-interface gains. B-task’s dense connectivity does not match trainable capacity merely by matching nine neurons. [Parameter specification](D:/Claude/random/wormWars/docs/E3/DESIGN.md:139)

5. **Stage gates and memory classification remain incomplete.** Give the scripted controls an absolute success requirement, define Stage 1 failure consequences, and specify Stage 2 success and admission to Stage 3—including its starting genomes. A leaky state can retain its **sign** throughout 600 ticks while its magnitude vanishes; require retained magnitude/function and a bistability criterion. L1-switch is a reference benchmark, not a demonstrated upper bound. [Stages](D:/Claude/random/wormWars/docs/E3/DESIGN.md:107)

The pre-registration must additionally pin: all numerical gate fractions and effect thresholds; confidence procedures and run-level replication; disjoint tuning/selection/test worlds; exact control constructions; mutation bounds and tying; Stage 3 fitness allocation; geometry sampling and failure handling; array dtypes; equivalence compositions and tolerances; and an approved cap with deterministic reductions and minimum viable replicate counts. The final change map should describe these as pending wherever they remain unspecified.