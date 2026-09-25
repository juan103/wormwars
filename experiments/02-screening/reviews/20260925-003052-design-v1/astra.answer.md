1. **MAJOR — This tests wiring–interface compatibility, not “biological correctness” in isolation.** The [interface file](D:/Claude/random/wormWars/configs/interface.yaml:3) explicitly describes modelling choices: three sensory pairs receive identical food signals, and motor outputs are hand-chosen combinations. Real ASEL/ASER, for example, have asymmetric responses to concentration increases/decreases; they are not simply stereo concentration sensors. [Suzuki et al., 2008](https://www.nature.com/articles/nature06927). Call the conditions **biologically motivated versus remapped**. A positive interaction would support specialisation under these modelling assumptions.

2. **MAJOR — “SH and RD should be indifferent” is wrong as a general prediction.** [SH preserves each named neuron’s degrees](D:/Claude/random/wormWars/wormwars/connectome/graphs.py:7), so moving inputs between high- and low-connectivity neurons can systematically affect SH too. RD is indifferent only in expectation over its graph ensemble, under an appropriately independent mapping construction.

   Use **at least four wrong mappings; preferably eight**, selected before fitness measurements. Keep the motor readout fixed initially. Preserve bilateral pairing, left/right orientation, channel multiplicity, gains, injected-current bounds, and absence of sensor–motor overlap. Approximately match receiving neurons’ chemical in/out-degrees and gap degrees using declared tolerances. Apply exactly the same mappings to every graph; evolve separately under each mapping.

   Sensor-to-motor distance is partly a **mechanism**, not merely a nuisance. Measure reachability, path lengths and initial input–output responses. A secondary distance-matched comparison asks whether anything remains beyond routing. Matching routing away in the primary experiment would remove part of the proposed effect. Never select mappings because controls perform equally well on them.

3. **MAJOR — Calibration and initialisation could manufacture the interaction.** In 01b, achieved forward drive was 95% of target for N2 versus 84–93% for SH. That discrepancy is directly relevant to an advantage largely expressed at initialisation.

   Choose a calibration target independently of N2; estimate gains using a common, task-independent input protocol, and freeze each graph’s gains across mappings and plasticity conditions. Verify actual drive, turning bias and saturation at the fitted gains. Report remaining mapping-dependent drive changes.

   Also, initial weights depend on anatomical strengths, whose placement is shuffled in controls. If the claim concerns the **wiring mask**, use a common edge-weight initialisation distribution independent of anatomical strength. Otherwise explicitly test topology plus anatomical initialisation.

4. **MAJOR — Use two core tasks and one optional task, with diagnostic gates.**

   | Task | Required validation before inclusion |
   |---|---|
   | **Temporal chemotaxis:** one concentration sample copied to bilateral inputs; random source directions and concentration scales. | A controller using concentration change must beat tuned memoryless concentration policies and unbiased search. Include identical current concentrations reached through rising versus falling histories. Mono sensing alone does not prove memory is necessary. |
   | **Artificial delayed conditional choice:** two successive ally/enemy pheromone pulses; choose left/right according to whether they match. Randomise the match-to-action assignment between lifetimes, with feedback trials before scored probes. | A small finite-state learner succeeds; reactive, last-cue-only, time-only and fixed-assignment controllers fail. Balance cue sequences and actions; prevent pose, pheromone trails or food scent from revealing the answer. |
   | **Optional: hazard avoidance while reaching food.** | A reactive attraction-plus-repulsion controller succeeds; food-only, straight-running and stationary controllers fail the joint success criterion. Survival alone rewards doing nothing. |

   The artificial task needs a new trial harness, although it uses existing sensor channels. Present it as an arbitrary computational task, not proof of something worms cannot do. Disable incidental social signals and self-deposited trails in these assays. Two natural navigation tasks alone provide a weak specialisation contrast.

5. **MAJOR — Pick one learning rule with a clear hypothesis.** I would use **none versus bounded reward-modulated Hebbian updates with decaying eligibility traces**. Fix the rule’s few hyperparameters using discarded pilots; evolve the same baseline weights, biases and time constants in both columns. This avoids adding thousands of evolvable plasticity coefficients.

   Short-term presynaptic depression is a reasonable later column for a specific temporal-filtering hypothesis. It does not, by itself, test acquisition of rewarded associations. Unmodulated Hebbian learning would be my first rule to cut.

   Match evolutionary evaluations, population, mutation/tuning budgets and reward information. Reward must be local experienced intake/damage, not privileged task labels or final fitness. The current [“damage” input is an enemy attack-field measurement](D:/Claude/random/wormWars/wormwars/world.py:469), and there is no intake-reward channel: reward instrumentation is additional work and must also feed the fixed-weight networks.

6. **MAJOR — Separate adaptation from where its memory resides.** Fixed-weight recurrent networks can adapt through activity; randomising contingencies does not establish a requirement for synaptic changes. [Wang et al., 2018](https://www.nature.com/articles/s41593-018-0147-8).

   Keep independently evolved fixed-weight competitors. On plastic champions, test updates disabled from birth, updates frozen after acquisition, neural activity reset before probes, and plastic weights/traces reset before probes. For retention specifically in weights, clear activity and eligibility traces while preserving acquired weights. Use controlled trial boundaries and report these as mechanism probes, not standalone proofs of necessity.

   Count dynamic state as well as evolved parameters. Crucially, [current weights are shared per strain](D:/Claude/random/wormWars/wormwars/brain.py:20). Plastic weights and traces must belong to individual weys/worlds, reset between lifetimes, and never be inherited accidentally. Sharing updates across worlds would invalidate the learning result.

7. **MAJOR — Preregister differences of differences, not a pattern of significance.** Let \(A_{t,p,m}\) be N2’s mean held-out advantage over SH for task \(t\), plasticity \(p\), mapping \(m\). Define

   \[
   I_{t,p}=A_{t,p,\mathrm{motivated}}
           -\operatorname{mean}_{m\in\mathrm{remapped}}A_{t,p,m}.
   \]

   Register three contrasts: the interface interaction \(I_{\mathrm{chemotaxis},0}\); its task dependence \(I_{\mathrm{chemotaxis},0}-I_{\mathrm{artificial},0}\); and its plasticity dependence \(I_{\mathrm{chemotaxis},1}-I_{\mathrm{chemotaxis},0}\). Treat RD as secondary corroboration.

   Use final held-out performance as the primary endpoint. Normalise each task against frozen diagnostic anchors—chance/uninformed performance and a competent scripted controller. My proposed smallest meaningful interaction is **0.05 of that performance span**; this is a design choice, not something established by 01b.

   Use paired bootstrap intervals preserving graph and run blocks; remappings are crossed with graphs, not nested within them. For these three confirmatory contrasts, use Bonferroni-adjusted **98.33% intervals**, with coverage checked in pilot simulations. An interval above zero establishes direction; entirely above 0.05 establishes a meaningful positive effect. Practical equivalence requires an interval inside ±0.05. A positive interaction alone does not establish an absolute N2 advantage.

8. **MAJOR — Replication makes the full grid expensive.** A concrete planning allocation is **10 independent SH graphs, 10 RD graphs, three evolutionary runs per control graph, and 20 N2 runs per cell; 100 generations**, population 32. Reuse graph identities and matched environmental seed blocks across cells. Use at least 64 held-out worlds per champion, with no champion selection on those worlds.

   Two tasks × five mappings × two plasticity conditions gives **1,600 runs**. Scaling 01b’s measured cost gives approximately **150 GPU-hours at its original throughput**, before extra evaluation and plasticity costs. A revised integrator taking 2–4 times as long makes that **300–600 hours**, before individual plasticity overhead. Benchmark that overhead before committing.

   These counts are a planning allocation, **not a power calculation**. Discarded pilots must estimate graph, mapping and run variance and demonstrate roughly 80% power for the registered effect. Increase graph replication before repeatedly sampling the same few controls. N2 remains one fixed graph; its runs are not biological graph replication.

9. **MAJOR — Numerical failure, shortcuts and floors/ceilings would make the grid uninformative.** D032 already shows that even 32 versus 128 substeps can disagree materially in strongly mutated genomes. Validate fitness and interaction estimates under refinement on evolved **plastic and nonplastic** controllers; choosing 32 automatically is insufficient. Plasticity rates must also remain consistent when integration resolution changes.

   Other failure conditions: both tasks reward the same simple movement policy; arbitrary tasks remain unsolved by every evolved condition; natural tasks saturate; reward leaks the answer; or inference depends on one remapping. More cells do not repair these problems.

   Cut the **second plasticity rule, optional avoidance task, RD, then plasticity altogether** before cutting mapping or SH graph replication. The N2–SH, fixed-weight, two-task subset above costs roughly **47 GPU-hours at old throughput**, plus integration overhead.

10. **MINOR — Keep the generalisation claim precise.** Evolving a fresh controller for every task tests whether the *architecture comparison replicates across tasks*. It does not demonstrate transfer by one controller. Likewise, report generation-zero performance and subsequent gains separately; 01b’s curve-average result does not establish faster evolutionary improvement.

**The single change I would make:** replace the immediate full grid with an interface-ensemble experiment—N2 versus SH, two validated tasks, fixed weights—before introducing plasticity.