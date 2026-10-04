**Revise before pre-registration.** The draft can become a useful comparison within 30 GPU-hours, but its current labels overstate what it identifies. Q1 compares two particular wiring and search recipes. Q2 measures the advantage of engineered initialization. The proposed cost ledger does not yet demonstrate cumulative reuse value.

I checked the design, roadmap, prior results, training records, implementation, and code changes since T-A’s training commit.

1. **Task: keep mazes provisionally, subject to a stronger feasibility pilot.**

   Mazes are the appropriate continuation of the gate, but passing that gate establishes that an already functional organism can improve. It does not establish that these mazes provide enough learning signal for random controllers.

   The existing evidence warrants caution: E3a’s dense baseline remained below joint tuning after **800 generations**, and E3b-1’s degraded organism started at **0.48 visits per wey** and remained well below the seed after training. Neither establishes that scratch learning will fail, but neither supports assuming 125 generations is adequate. [E3a results](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/RESULTS.md:99), [E3b-1 results](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:175)

   Use the open shuttle as the fallback if the pilot cannot establish an informative maze comparison within budget. That would answer a narrower assembly question honestly. Changing maze difficulty or fitness would also be legitimate before registration, but would invalidate historical P-joint as an exactly matched training arm.

2. **Reusing P-joint: acceptable, with population reselection and a narrower claim.**

   The different commit is presently a smaller problem than the draft suggests. T-A trained at `47f660d`; comparing that commit with current `HEAD`, the only change under `wormwars/` is the added `e3/attribution.py`. The existing engine, maze implementation, tuning code, and `scripts/e3b1.py` are unchanged.

   Different validation blocks do not automatically bias a comparison on untouched test mazes. However, using a common validation procedure removes an avoidable difference. **All eight T-A and all eight T-F final populations exist locally.** Revalidate all 32 candidates per run on E3c’s validation block, using the same selection rule as the new arms. Verify their recorded hashes first. Do not choose between the old champion and the newly selected champion afterward. The existing rule is highest validation mean, ties to the lower population index. [Selection implementation](D:/Claude/random/wormWars/scripts/e3b1.py:933)

   Retain all eight runs of the chosen schedule. Record the historical training blocks as an explicit exception to “the training blocks are new.” Check any subsequent E3c engine changes against the old implementation at declared compositions.

   Most importantly, rename Q2 **“engineered initialization advantage.”** P-joint versus S-mod changes the initial values of the modules **and the selector**, including a working latch. It does not isolate pretrained navigation modules.

3. **Matched controller: the current proposal is not dense, and parameter count is not capacity.**

   The exact mutable count is **47 weights + 9 time constants + 9 biases = 65**. Of those weights, **32 are motor-output edges**, leaving just **15 internal edges**. The existing full dense controller has **171 mutable parameters**. [Parameter accounting](D:/Claude/random/wormWars/docs/E3/E3b-2-PLAN.md:75), [Dense implementation](D:/Claude/random/wormWars/wormwars/e3/samplers.py:153)

   Sampling 47 edges indiscriminately from internal and output possibilities changes motor access, connectivity, recurrence, and sensory reachability simultaneously. A registered random seed makes this reproducible; it does not make the comparator adequate.

   My preference for the proposed five-arm budget is **S-unstructured**, with exactly 65 parameters: preserve the 32 output positions and input interface, and specify a valid unstructured internal-mask distribution with sensory and visit-input paths to the outputs. Sample masks across independent runs and make inference explicitly about that distribution. Alternatively, use the genuine 171-parameter dense controller and call it neuron-matched. Either is defensible; “dense and capacity-matched” is not.

   Resolve “its τ and biases are the same as E’s.” Does this mean identical mutable positions, identical distributions, or identical engineered values? Specify every initial distribution, symmetry, bound, and whether populations contain independent draws or copies of one draw.

   The inputs also need precise wording. `at_a` and `at_b` are **source-occupancy levels**, plus an artificial startup cue; they are not persistent goal bits or confirmed-visit pulses. [Maze sensing](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:356) Giving only the nonmodular arm a persistent goal bit would change the information supplied. Keep that out of the primary structure contrast.

   Nevertheless, D144’s shared navigator with persistent state deserves an explicit comparison. The existing engineered `b_shared` provides a cheap additional reference when combined with W2; label its construction and size accurately. It would not substitute for the trained nonmodular arm. [Shared navigator](D:/Claude/random/wormWars/wormwars/e3/organism.py:100)

   Finally, common W2 is acceptable scaffolding, but all scratch claims must mean **“the mutable 11-neuron controller from scratch, with engineered W2 and interfaces.”** Frozen W2 does not imply equal functional contribution: other outputs can oppose or saturate its motor effect. Preserve the carrier biases and relay dynamics too; allowing recurrent inputs into dense-arm relays would make those relays different computational elements despite frozen τ and bias.

4. **P-sel’s start: the draft mischaracterizes what it tests.**

   `no_latch()` zeros the gate weights and comparator biases. It retains the engineered latch self-weight **2**, relay-to-latch weights **±3**, and latch τ **1**. Thus P-sel begins with an engineered memory circuit whose output gates are disconnected. It tests **restoring gating**, unlike E3a’s weak random selector initialization. The E3a 1-of-8 result is not a directly comparable feasibility estimate. [Selector construction](D:/Claude/random/wormWars/wormwars/e3/organism.py:63)

   For a practical assembly comparison, I would start P-sel from **intact E** and train only its declared selector/interface parameters. Then P-fixed, P-sel, and P-joint compare freezing, selector tuning, and joint tuning from the same functional assembly.

   If ungated recovery is itself the intended question, retain it but name that question explicitly and include P-sel in the pilot.

   Also qualify “modules frozen”: the 13-parameter definition includes **four comparator biases**. This is the existing interface convention, but those biases affect component operating points and resting motor output. The module boundary is not innocuous.

5. **Matching effort: use equal training evaluations, and report total cost separately.**

   Equal population × generations × mazes × horizon is a sensible primary resource constraint. Specify the optimizer completely, including mutation factors. E3b-1 used **0.25× mutation scales**; adopting a more suitable scratch-arm scale changes the comparison from initialization alone to different training recipes. That may be worthwhile, but must be stated.

   Equal schedules do not imply equal total compute. Account separately for initialization search, checkpoints, champion validation, qualification, and historical artifact production. Benchmark the actual implementations.

   Do not equalize cost by spending unnecessary evaluations on P-fixed. Its negligible adaptation cost is part of the comparison. Present performance against both training exposure and accumulated cost.

   The old and new learning curves also need a common measurement block, or explicit labels that prevent direct curve comparisons. Final champion reselection alone does not fix historical checkpoint curves measured on another block.

6. **Schedule: prefer investigating 300 × 8, rather than defaulting to 125 × 16.**

   E3b-1’s normalized gains were **+0.069 for T-A** and **+0.381 for T-F**. Its within-T-F comparison supports a benefit from continuing past generation 124. This does not establish the best scratch schedule, but it argues against selecting 125 chiefly because T-A is available. [Schedule results](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:47)

   T-F’s recorded training time is 6.438 hours. Using the draft’s other allowances gives approximately:

   | Revised allowance | Hours |
   |---|---:|
   | Three new arms at T-F’s measured cost | 19.32 |
   | Draft pilot, projection, validation, evaluation allowances | 4.40 |
   | Reselect eight historical populations | 0.32 |
   | Additional 25% training reserve | 4.83 |
   | **Total** | **28.86** |

   This is an extrapolation, not a measured E3c projection. It shows that the longer schedule is plausible within 30 hours, though with little spare capacity. Benchmark scratch arms and fix the reduction order before registration. I would cut repeated descriptive trail conditions before weakening the primary comparisons.

7. **Cost accounting: E4s-0’s GPU-hours are not the cost of producing the assembled organism.**

   E4s-0 reports **0.23 hours**, but that includes diagnostics beyond producing L1. Conversely, it excludes unmeasured design work and later engineering of the latch, interfaces, W2, and maze-ready organism. Calling the entire figure “pretraining cost” is misleading in both directions. [E4s-0 accounting](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/RESULTS.md:9)

   Use separate entries for measured artifact-production and selection compute, shared infrastructure/engineering, downstream adaptation and validation, and unmeasured human/model design effort. Do not invent hours for the last category. Do not charge all shared engineering only to P arms: S-mod inherits the engineered mask, and every arm inherits W2 and the task interface.

   Keep **incremental E3c expenditure** separate from **historical first-use cost**. Reusing T-A saves this experiment training time; it does not erase that training from the method’s first-use ledger.

   The cumulative-reuse claim needs more revision. P-sel does not reuse P-joint’s tuned modules; it returns to the original library. Two constructions on the same task can illustrate sharing a library’s fixed cost, but do not establish savings for later useful organisms relative to matched scratch alternatives.

   Define the ledger as library cost paid once plus each downstream adaptation cost, and compare against scratch costs **at comparable performance**. With only this task, report prospective amortization scenarios explicitly as scenarios. If empirical cumulative reuse is required of E3c, add a defined second downstream construction and its scratch comparator, and reduce the current scope to fund it. Eight optimization replicates are not eight demonstrated reuse applications.

8. **Pilot: “both near zero after 25 generations” is an inadequate criterion.**

   W2 alone scored about **1.72 visits per wey** in E3b-1. Both scratch arms could plateau around a nonzero scaffold-driven score and still provide little evidence about learned assembly. Conversely, early zeros need not predict failure after 300 generations.

   Before running the pilot, specify its initialization, mutation recipe, held-out pilot mazes, controls, diagnostics, maximum expenditure, and decision branches. Examine performance relative to W2 alone and P-fixed, improvement over generation zero, repeated journeys, and sensitivity to the task inputs. Include P-sel if retaining its degraded start.

   Use 25 generations as an initial screen, with a budgeted continuation of selected **prespecified pilot runs** far enough to assess the proposed formal horizon. Two runs per arm cannot reliably estimate rare success or power; acknowledge that limitation.

   Crucially, **do not require both arms to learn**. One learning while the other fails can be the relevant result, provided the failing arm is correctly implemented and has meaningful input/output access. If both fail, the conclusion is failure of these recipes at this budget—not equivalence of modular and nonmodular structure.

   If the pilot leads to shaping, a curriculum, different dynamics, or altered mutation rules, re-evaluate whether historical P-joint still belongs in the matched contrast.

9. **Registered tests: specify estimands, multiplicity, practical margins, and failure handling.**

   Keep the training run as the independent unit. The colony’s eight weys and its 256 maze outcomes do not create additional independent optimization runs.

   For each champion, calculate mean visits per wey over the common test block. The two proposed mean contrasts can be retained:

   \[
   \Delta_1=\frac{\bar V_{\mathrm{Smod}}-\bar V_{\mathrm{Sunstructured}}}{\bar V_{\mathrm{seed}}},
   \qquad
   \Delta_2=\frac{\bar V_{\mathrm{Pjoint}}-\bar V_{\mathrm{Smod}}}{\bar V_{\mathrm{seed}}}.
   \]

   Call the second initialization advantage. Report absolute visits alongside normalized effects.

   Use **two-sided Welch tests with Holm correction across the two primary contrasts**, since the intended labels include either direction. Report confidence intervals and fix a practically relevant margin before testing. “Unclear” must remain distinct from “equivalent.” Equivalence requires a separately registered test with a justified margin; eight runs per arm may be inadequate.

   P-sel versus P-fixed is an important roadmap reading. Register it explicitly as descriptive, or include its test in the multiplicity plan. Do not imply a confirmatory evolved-selector result from informal comparisons.

   Historical and fresh run indices do not create pairs. If pairing new arms through common training environments is desired, build it into their generation procedure and analysis in advance.

   State whether inference is conditional on these 256 mazes, as in E3b-1. A supplementary crossed resampling analysis can address maze variation while preserving the common maze block across arms. Fix handling of zero denominators, training failures, cap stops, incomplete validation, and ties.

   Finally, run a prospective power analysis for these **two-sample contrasts**, including mixtures of successful and failed scratch runs. E3b-1’s power calculation and T-A’s small observed variance are not adequate substitutes.

The practical revision I would pursue is a first-use assembly and initialization comparison: retain the roadmap arms, repair the nonmodular comparator, start selector tuning from intact E, reuse and reselect a complete historical P-joint cohort, and investigate the longer schedule through the pilot. Report historical and incremental costs transparently, with cumulative reuse left as an explicitly conditional projection unless a second downstream comparison is actually funded.

**Verdict: revise.** Resolve the controller specification, P-sel interpretation, pilot decision rule, and reuse claim before writing the pre-registration.