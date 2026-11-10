**Verdict: fix then proceed.**

The confirmatory question is answerable as **terminal hunting performance of N2 versus SH-route, with this frozen L1 graft, interface, motor gains, initialization, GA and budget**. It does not isolate wiring from weight placement, or evolutionary improvement from starting performance. Keep the grafted comparison, but correct the pilot, starting genomes, statistical rules and implementation checks before pre-registration.

1. **Must fix — B names different genomes from those E5-0 tested.**

   > “one E4s-1 M champion (F of run i)”

   E5-0 loaded **C, the validation champion**, not F. [hunters.py](/D:/Claude/random/wormWars/wormwars/e5/hunters.py:58) explicitly reads each record’s `champion` checkpoint.

   I checked E4s-1’s `train-1.json` and `train-4.json`: **C and F differ in 13 of 16 runs**; only runs 0, 10 and 11 coincide. Consequently, “qualify everywhere,” the 2.85 suite mean and the 7.41 Task N mean describe C’s genomes.

   **Recommendation:** use those same 16 C genomes for B, with checkpoint indices and hashes frozen. If you choose F instead, evaluate those starts separately and stop attributing E5-0’s results to them.

2. **Must fix — the proposed evolutionary pilot violates the standing pilot rule.**

   > “It never runs the confirmatory comparison”  
   > “2 runs on 2 pilot graphs and 2 on N2, 100 generations”

   Evolving both sides on Task H produces an exploratory version of the confirmatory comparison. Different seeds, graphs and worlds protect the formal samples; they do not change the comparison being run. Saying its numbers “are not read as a result” does not satisfy [ROADMAP.md](/D:/Claude/random/wormWars/ROADMAP.md:779).

   **Recommendation:** make evolutionary development null-only. Keep N2 in technical equivalence checks using fixed genomes. Obtain planning variances from null pilots and conservative sensitivity scenarios, without an N2–null evolutionary contrast.

   Also resolve the contradiction between §5’s variance estimate “on 4 graphs” and §6’s evolution on **two** graphs. Four generation-0 graph measurements do not estimate between-graph variance after evolution. Even four evolved graphs would provide a very uncertain variance estimate.

3. **Must fix — the engineering argument against calibrated gains is wrong.**

   > “per-graph hunter gains need per-swarm gains: an engine change”

   For the **scripted prey used here**, they do not. [ScriptedBrain.command](/D:/Claude/random/wormWars/wormwars/exp02/scripted.py:57) divides the requested commands by its supplied gains before applying `atanh`; the world multiplies by those gains during read-out. `PreyBrain` already accepts them. Since each evolutionary batch contains one graph, its world configuration can carry that graph’s gains while the scripted prey compensates, within the command’s representable range.

   I nevertheless recommend **fixed gains for the primary comparison**. Calibration changes the host-plus-module phenotype and therefore answers another question. State that scientific choice directly, including that the gains and graft were developed on N2.

   The other argument needs qualification: 3.22/2 rescales the **unclipped read-out**, not necessarily the achieved turn or hunting performance. E4s-0’s sweep also does not establish that increasing stereo gain always helps: intermediate residual gains harmed most champions.

4. **Must fix — specify the training objective and validation distribution together.**

   > “captures summed over the 8 training worlds”  
   > “three strata, equally weighted”

   The proposed training weights are **12.5% static, 62.5% route, 25% movers**. The primary evaluation weights are **one third each**. This is not an arm-specific confound, but it trains a substantially different objective from the one used to declare success.

   **Recommendation:** keep the eight settings, but select using
   \[
   \frac{1}{3}\left[c_{\mathrm{static}}+
   \frac{1}{5}\sum c_{\mathrm{route}}+
   \frac{1}{2}\sum c_{\mathrm{movers}}\right].
   \]
   These remain unshaped capture scores. Record raw counts separately.

   Define the 256 validation worlds’ settings and aggregation. A straightforward choice is 32 worlds per training setting, aggregated with the same stratum weights. Keep the nine held-out settings out of checkpoint selection.

   Also define G0 consistently: the **generation-0 training winner**, subsequently evaluated on fresh worlds. Choosing the pilot’s “best” using all 256 diagnostic worlds would describe a different founder-selection procedure.

5. **Must fix — restore the positive-but-small outcome.**

   > “‘no detected advantage’ if the upper bound is below δ”

   An estimate of 0.18 with interval [0.10, 0.24] would receive “no detected advantage,” despite detecting a positive advantage.

   This copies E4s-1’s **design**, not its final rule. Its [pre-registration](/D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md:290) added **“Positive; estimate below 0.5.”**

   Add the analogous outcome here, and call the upper-bound-below-δ outcome **“an advantage of at least δ is not supported”** or equivalent. “N2 ahead” can require a positive lower bound and an estimate ≥δ, but that does **not** establish that the true advantage exceeds δ.

6. **Must fix — validate the bootstrap, rather than treating “hierarchical” as sufficient.**

   The point estimator is appropriate: N2 runs versus equally weighted null graph means. The graphs must remain the independent null units.

   However, resampling graph means and then resampling their two constituent runs can count within-graph sampling noise twice: that noise already contributes to variation among observed graph means. With only two runs per graph, this deserves explicit calibration.

   **Recommendation:** use a bootstrap over N2 runs and over the 16 null graph means, with a Welch-style interval as a diagnostic; or retain the proposed nested procedure only after demonstrating acceptable coverage. Simulate null error rates, interval coverage and all decision labels—not just power—including unequal variances, weak graph effects and failed/low-performing runs.

   Specify whether inference is conditional on the frozen world suite. A run/graph bootstrap alone does not separately quantify uncertainty from drawing another world suite. If that broader inference is wanted, preserve the shared-world pairing when assessing world uncertainty.

7. **Must fix — the CUDA gates do not address the principal batching difference.**

   > “N2 at 8 runs per batch; a null graph at 2 runs per batch”

   Graph treatment is associated with training composition: 256 hunter strains versus 64, and validation at eight versus two strains. CPU–CUDA agreement within each shape is not a direct check that changing shape leaves a genome’s behavior acceptably unchanged.

   **Recommendation:** either use the same composition in both test arms or explicitly test the same scoring genomes across both compositions, with declared tolerances. Cover ordering, chunking and mixed prey slots as well as neural state.

   The task-level CUDA checks should also include a scoring grafted null hunter, fast route prey, wall-following prey, H1-ghost versus Task N, attack-disabled captures/damage, and prey resets. Four hunters at three settings omit several new execution paths. A single N2 and single null genome are also a thin state-level sample; E4s-1’s cited gate covered 48 genomes and tested a different comparison—ungrafted versus inert-grafted—not CPU versus CUDA.

8. **Must fix — these are behavioral implementation changes, and E5-0’s old-engine check is insufficient for them.**

   > “Engine changes are none beyond the guard”

   Replacing route generation, batching heterogeneous prey, and altering capture-time synchronization change task execution. Whether they are called engine changes is immaterial under rule 7.

   E5-0’s 68-array comparison principally protects pre-existing behavior; the ghost comparison cannot test moving-prey respawns. Add **current Task H versus revised Task H** checks covering capture counts, events, prey trajectories, resets, damage and ledger values, including deliberately frequent captures and skipped respawn candidates.

   For the route cache, preserve the existing key: run seed, world identity and **sequence-life index**, plus relevant configuration. `HuntWorld._capture` can skip sequence entries; life is not simply capture number. Pre-drawing by capture ordinal would change the task.

   The new rollout also needs a serial reference. [play.py](/D:/Claude/random/wormWars/wormwars/e5/play.py:35) currently tiles one world list across strains, whereas `evolve_batch` supplies a two-dimensional run-specific schedule. That interface adaptation is substantive.

9. **Must fix — extend the guards beyond the proposed `Genome.cat` example.**

   The `Genome.cat` claim is correct. [brain.py](/D:/Claude/random/wormWars/wormwars/brain.py:161) concatenates parameters and retains `base.spec` and, normally, `base.cfg`, without checking compatibility.

   Test mismatched ordered edge indices, node count, anatomical metadata and configuration—not just graph labels or tensor sizes. Equal-sized, differently wired grafted graphs are the important regression case. Equivalent separately constructed specs should remain usable.

   There is another relevant omission: [the publication check](/D:/Claude/random/wormWars/tests/test_publication_hygiene.py:59) returns no offences for unknown graph labels. Its anatomical reference set contains N2 and SH1–5/RD1–5, not these SH-route graphs. Thus the new grafted SH-route labels bypass this proportional-weight check. Add an explicit publication prohibition or checked handling for them, with sabotage coverage.

10. **Must fix — freeze formal failure handling and behavioral qualification.**

   The design specifies pilot stops but not what happens to O1 after an incomplete graph, one failed replicate, a non-finite rollout, sequence exhaustion or budget exhaustion. These cannot be resolved after performance is visible.

   Specify admission order, minimum completeness, retries, treatment of incomplete graphs and when O1 is withheld. Do not replace poor-performing graphs or selectively average surviving runs.

   Also:
   
   - “Any capture” is a weak selection-signal gate: all strains can tie, and moving prey can approach inactive hunters. Measure fitness dispersion on the actual eight-world selection batches and distinguish accidental capture from module-dependent performance.
   - Four settings’ `constant` probes cannot establish qualification across all 17. Either limit the claim or run the required qualification measurements wherever qualification is claimed.
   - Re-run frozen stationary/blind references on the formal worlds. E5-0’s baseline values on other worlds cannot supply the paired qualification contrasts.

11. **Must fix before requesting the GPU budget — complete and correct the cost ledger.**

   The main table’s arithmetic works: approximately **31.8–33.8 hours** at \(f=1.5\), and **42.2–45.2** at \(f=2\).

   I checked all ten E4s-1 training records: **4,876.28–5,150.75 seconds**, averaging **4,984.21 seconds**, or **1.3845 hours per batch**. E1’s one-run and four-run rates also support the quoted 2.33 and 3.04 seconds. Interpolating a two-run rate remains an assumption.

   The listed work includes:

   | Work | Episodes |
   |---|---:|
   | Training, 64 runs × 1,000 generations | 16,384,000 |
   | Validation, 41 checkpoints × 256 worlds × 64 runs | 671,744 |
   | F, C and G0 suite evaluation | 1,671,168 |
   | Five probes × four settings on F and G0 | 1,310,720 |

   Endpoints plus probes alone take **2.71 hours at 306 episodes/s**, before Task H overhead. That supports the rough evaluation range, but not its use without measuring the actual 512-world/probe compositions.

   Missing specifications include mutant-evaluation worlds and settings, parents and controls, bridge evaluations, qualification extensions, revised pilot size, route preparation, instrumentation and retries. For illustration, 256 mutants around 24 parents on 256 worlds already means **1,572,864 episodes**.

   The optional-arm prices are low under the table’s own assumptions: a no-graft pair costs roughly **22–29 training hours**, not +15, if its rates are comparable; 16 one-run SH batches cost roughly **15.5–20.7 training hours**, not +12. Benchmark those variants separately.

12. **Should fix — remove the unsupported no-graft floor prediction.**

   > “a floor against a floor”

   E2d’s genomes were evolved on Task N and transferred zero-shot. They do not establish how ungrafted N2 or SH-route would evolve on Task H. E5-0’s results explicitly say this.

   The defensible reason to retain L1 is to test a reusable competent component under a controlled host comparison. Even then, distinguish a competent **module** from a competent **starting population**: E4s-0 found most individual random N2 backgrounds scored zero.

   SH-route is a sensible primary null. Describe it precisely as preserving degrees and imposing **upper bounds** on specified direct food-to-read-out connections and anatomical weights. It does not exactly match every routing property or isolate wiring alone.

13. **Should fix — distinguish paired runs from independent samples.**

   > “the paired unit across arms is … the arm’s distribution of runs”

   There is no such paired unit. G-N2 versus G-SHr is an **independent-samples, clustered comparison**, with paired evaluation worlds. That is acceptable; shared training schedules are not required for unbiased comparison under the declared sampling scheme.

   Conversely, B and G-N2 have deliberately matched training/breeding seeds. Preserve that pairing in their descriptive contrast.

   Correct “every strain in a generation sees the same 8 world ids” to **every strain within a run**. `evolve_batch` gives different runs their own schedules.

14. **Should fix — narrow O2’s pretraining interpretation and strengthen O3’s wording.**

   > “the same construction, with and without E4s-1’s 1 000 generations”

   B starts with 32 identical copies of a selected evolved brain. G-N2 starts with 32 different random backgrounds, from different original founder populations. They also differ in evolved module parameters and total work. Their contrast is a comparison of **starting protocols**, not an isolated estimate of pretraining’s value.

   O0 and O1c are useful. F−G0 supports an endpoint improvement reading, not an ancestor–descendant history or a general claim about evolvability.

   O3 should report paired Task N losses against the actual starts on the same fresh worlds. “Keeps Task N” needs a predefined tolerated loss; failure to detect loss is insufficient. If SCOPE §7’s “during adaptation” is retained, add a few separate checkpoint measurements. Endpoint-only O3 does not meet that wording.

15. **Should fix — choose δ for practical meaning, then assess power.**

   The rough arithmetic is correct under the stated model:
   \[
   SE=\sqrt{0.3^2/16+0.3^2/16+0.3^2/32}=0.1186.
   \]
   The normal 90% half-width is about 0.195. Thus the rule finds a true 0.5 effect about 98% of the time and a true 0.25 effect about half the time, before finite-sample/bootstrap complications.

   But E4s-1’s champion SD is not evidence for E5-1’s within-graph or between-graph evolutionary variance. Fix δ on practical grounds—0.25 is one additional capture per four episodes under the score’s weighting—and simulate a broad variance range.

   With a rule requiring the point estimate ≥δ, power at a true effect exactly δ tends toward 50%, even with large samples. Do not choose counts expecting 80–90% power at that boundary.

16. **Should fix — correct several smaller factual references.**

   - “First evolution on null graphs since 02” should say **first ensemble evolutionary comparison**; 03a really did evolve on a null graph.
   - “E5-0’s set” for four probe settings is wrong. `scripts/e5_0.py` freezes **H1-bite and H2-0.5**. Your four-setting set is an expansion.
   - Module-only `mean` is an intervention used in E4s-1’s analysis, not by itself its complete **H** host-use assay.
   - A **100-generation** pilot cannot establish “flat late training” as grounds for cutting a 1,000-generation design to 500.
   - **D389 is absent** from the checked `DECISIONS.md`, which ends at D388. I cannot verify the cited design authorization there.

17. **Answers to §10 — my recommendations.**

   | Question | Recommendation |
   |---|---|
   | **10.1 Graft in both arms?** | **Keep it in both.** Accept the explicitly conditional host question. Do not add or substitute the no-graft pair now; withdraw the floor prediction. |
   | **10.2 One ensemble or two?** | **SH-route only.** Ordinary SH adds cost and reintroduces the routing difference that motivated the tripwire. |
   | **10.3 Gains?** | **Fixed 4.0/2.0 for the primary test**, with raw and achieved drive, signed forward motion, turn offset and saturation reported. Calibration is a different sensitivity analysis, not an engineering impossibility. |
   | **10.4 Mixture and suite?** | **Keep the fixed mixture, eight settings and three-strata score; align fitness and validation weighting.** Keep movers in training. Their held-out speeds already provide parameter transfer; entirely novel mover-family transfer can be a later question. A shared predetermined curriculum would also be fair, but is unnecessary here. |
   | **10.5 δ and counts?** | **0.25 and 16×2 are reasonable provisional choices.** Freeze δ independently of favorable pilot outcomes. Judge counts using conservative variance scenarios and power for effects above δ. |
   | **10.6 B’s start?** | **32 identical copies of each E5-0-tested C champion.** This gives an unambiguous starting organism and G0. Mutants arise after the first breeding step. |
   | **10.7 Does B belong?** | **Yes, as a separately budgeted descriptive component scheduled after the confirmatory training allocation is secured.** It addresses the owner’s build objective. It must not determine the test’s settings or consume its evaluation reserve. |

18. **Other findings — factual checks completed and their limits.**

   I read the requested design, scope and E5-0 results in order, then checked the cited implementation and records. The substantive confirmations are:

   | Source checked | Finding |
   |---|---|
   | E5-0 `RESULTS.md`, `summary.json`, `reading.json` | Confirmed 18 read settings solvable/not too easy; all E4s-1 champions and L1 qualifying; E2d’s reported fall-offs; generation-0 failures; stereo contrasts; route-speed means; wall-limited movement; 68-array equivalence summary and CPU-only recorded work. |
   | E5-0 `reading.json`, independently aggregated | E4s-1 suite mean **2.85114**, sample SD **0.22958**, range **2.60239–3.40898**; L1 **3.00690**; E2d **0.75577**, SD **0.21886**; generation 0 **0.11189**. The draft’s rounded arithmetic is correct. |
   | E4s-1 design, pre-registration, results, training records; `arms.py` | Confirmed GA settings, mutation factors, C2 cloning, F/C/G0 definitions and measured rates. Found the C/F mismatch and outdated outcome rule above. |
   | 02 README; 03 README and `samplers.py`; 03r ensemble/manifests and rebuild code | Confirmed the routing tripwire, degree preservation, routing caps, weight movement, 256 SH-route graphs and content/raw-hash distinction. Freeze graph **names**, not ambiguous ordinal indices. |
   | D014; 03a pilot/setup records; 03h calibration code | Confirmed fixed gain provenance, 03a’s single SH-mirror graph and gains **6.26545/3.22011**, and graph-specific calibration elsewhere. |
   | `graft.py`, `comparator.py`, `brain.py`, `e04a/evolve.py`, `e5/*`, scripted controllers | Confirmed the four-neuron graft, 16 output edges onto eight named turn neurons, embedding construction, concatenation defect, run-specific schedules, gain inversion, route sampling and capture-time host synchronizations. |
   | SCOPE §§4, 7–8 and ROADMAP standing rules | Confirmed the owner’s build-and-test scope, pilot restriction, independent graph/run structure, accounting and equivalence requirements, and that H3/H4 remain outside E5-1. |

   These checks establish what the files and committed records say. I did not rerun simulations, rebuild anatomical graphs, use CUDA or modify files. The claim about **every earlier reviewer’s model version** was not independently audited.