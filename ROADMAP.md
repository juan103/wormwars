# WormWars roadmap, v3

*27 September 2026. Replaces v2. Written from roadmap v2, Astra 6's review of v2, and Claude Code's status report of the same day. A local v2.2 exists on the `roadmap` branch and was not seen when this version was written, so merge anything it adds. (Merged: see "Carried over from v2.2" below. Four factual corrections were made on installation; they are listed in D062.) This is a living document, not a pre-registration. When a result changes it, the change is recorded here with the reason.*

## Status, 28 September 2026 (updates the section below; that section's later edits are recorded in DECISIONS.md)

- **Published on main:**
  - 02's D050 correction, as a Corrections entry (27 September, D063);
  - 03 and 03r together, reported by the pre-registered rule, and 02b (28 September, D085).
- **T0 (correctness) is closed** (D083). On CUDA, results repeated exactly for the same batch
  composition in the tested configurations; exact reproduction is guaranteed only inside
  `replay_mode()`. A chunk holding a single strain can differ from the same strain in a larger
  chunk (D082).
- **T1 (throughput) is in progress** (plan v2: [`docs/foundations/T1.md`](docs/foundations/T1.md),
  D086):
  - **the profile** (`docs/foundations/T1_profile.json`). On 02's task T1, at evolution's batch, the
    brain's matrix products take about 70% of GPU kernel time, and the world about 55% of a
    tick's wall time. On a Task N-like shape (one wey per world) the world's share is about 70%,
    so batching more worlds together pays much more there;
  - **single-strain padding** is implemented. Its declared equivalence test failed at 16 rows per
    strain and at 1 row. It is kept as a mitigation of the batch-of-one path, with little measured
    overhead, and it changes no published evaluation;
  - **T1's engineering is closed by a dated amendment,** not by passing its gate (D092). This
    authorises a bounded E1 pilot;
  - **T1's budget gate moves to E1's pilot** (D086): E1 measures Task N's own throughput, and
    04a's and E2's budgets are fitted to it.
- **Documentation for outsiders:** every experiment folder now has a README with its question,
  result, caveats and exact commands to rerun it, and [`AGENTS.md`](AGENTS.md) describes the
  repository and its rules. Others are welcome to take any open question here, and to get there
  first.
- **03a becomes a six-neuron proof of concept capped at 72 GPU-hours** (the owner, D094). It comes
  after E1, sized to E1's measured one-wey throughput. The full 24-neuron draft needed about 2.5
  times the measured throughput. The largest candidate found in T1, batching several runs
  together, gives about 1.35 times on 02's task and 3.2-4.2 times on a one-wey task; its
  exactness is not yet tested.

## Where the project stands

- **Experiment 01 / 01b.** Real C. elegans wiring (N2) against shuffled (SH) and random (RD) graphs on a foraging game. 01b is the rerun after a chemical-synapse direction bug was fixed. The README states exactly what it establishes; in particular, it does not establish faster improvement.
- **Experiment 02 (published).** The primary prediction failed: champions did not meaningfully use the left-right food difference. Its pre-registration's mirror-symmetry reasoning was wrong: the turn read-out is dorsal minus ventral, so symmetric wiring gives no left-right comparison for free. Correction D050 is prepared as a Corrections entry in 02's RESULTS.md on main *(published 27 September)*.
- **02b (re-analysis of 02's champions, reviewed, not yet on main *(published 28 September, D085)*):**
  - Champions circle and slow down on food and near obstacles, and N2 and shuffles do this equally well.
  - One statement, that champions "steer by which side the food is on", is now reconciled with 02's registered result: it is a replay association with the turn command, not fitness use, and it does not revise 02 (D063).
  - Selection built history dependence into the champions: a slow memory of the recent food level, not a response to its change.
  - N2 has a core of critical neurons (AIZ, RIA) that survives changes to the sensor mapping.
  - By generation 39, evolved weights keep only a weak resemblance to the anatomy (rank correlation 0.35).
  - Of 96 high-criticality targets (N2's 12 most critical neurons in each of 8 champions, counted with repeats), 94 connect directly to sensor or motor neurons.
- **Experiment 03 (random, unevolved brains; N2 against five null ensembles of 128 graphs each):** SH, SH-route, SH-class, SH-mirror and SH-recip.
  - **P4, history dependence:** borderline. N2 is above every graph in four ensembles and above 127 of 128 in the routing-matched one (adjusted p = 0.047).
  - **P1, steering toward food:** N2 is unremarkable.
  - **P3, use of food information:** no criterion met, with low power.
  - **Exploratory:** N2's random brains respond 5 to 7 times more strongly to food input than the typical shuffled graph, and more strongly than every one of the 640. That does not explain P4. Two readings from 02 do not hold for unselected random brains.
- **03r:** a pre-registered replication on 768 new graphs and new random brains for N2 too, **finished on 2026-09-28: "Replicated under the registered single-signal test and under 03's original three-signal rule"** (D080). P1 recurs as "not distinctive". P3 comes out *reversed*: an unpredicted secondary, weaker than its rank p suggests because N2's P3 measurement is noisy. Per "What would change this roadmap", the mechanism follow-up comes next in Track B, and bridge 2 gains priority.
  - **Timing, stated plainly:** neither 03's nor 03r's pre-registration was pushed before its run started. 03r's is pushed while the run is in progress, so GitHub's receipt time shows only when the text became public. That no 03r result had been seen by then rests on local records: at the push, N2 had not been measured, and no signal value from the formal run had been inspected since binding. The one exception is a disclosed preflight value from before binding (D063). The standing rule below applies from now on.
- **03a (your self-consistency hypothesis):** draft v3.2, nothing run. Estimated at about 31 million genome evaluations, roughly 785 GPU-hours. Measured throughput so far is about 2 times experiment 02's; the one-week cap needs about 5 times.
- **Related work:** a first survey exists, with corrections pending (see Related work below).

## The thread worth following: memory (a hypothesis)

Several results point the same way:

- N2's random brains hold on to past food levels unusually strongly relative to all five null ensembles (03, borderline; replicated in 03r, D080).
- Selection builds that kind of slow memory into the champions of every group, N2 and shuffles alike (02b, group means).
- N2's critical core, AIZ and RIA, belongs to interneuron classes worth comparing with the navigation circuitry described in the experimental and modelling literature.

**Hypothesis.** N2 starts with more capacity to hold recent history. Evolution then builds such memory into every graph, which would explain why N2's early advantages fade.

**Status.** 03r tested the first link, and it replicated (D080). So, the testable predictions include these: N2's early advantage should be larger on tasks that require memory than on tasks that do not; it should shrink over generations; and the history effect should localise to identifiable circuitry.

## Two tracks, one priority

| Track | Question | Success looks like |
|---|---|---|
| **E: engineering** (drives the schedule) | Does assembling validated neural skills reduce the total cost of evolving useful collective behaviour, and which structural or functional features survive further evolution? | Organisms that work on unseen situations, with controls showing what each component and each peer contributes |
| **B: biology** (runs independently) | Does the worm's wiring matter, and does behaviour identify anatomy? | Pre-registered comparisons against well-specified null graphs, reported whatever they show |

Failure in one track says nothing about the other. Track E may include optional **bridges**, meaning arms run on null graphs as well as N2. Each bridge is independent and uses several graphs per null ensemble. No single bridge can answer whether the worm wiring matters in general.

## Immediate sequence (deliberately small)

1. **Publishing housekeeping.**
   - Push the `roadmap` branch so 03r's pre-registration is public before 03r finishes.
   - Publish correction D050.
   - Reconcile and publish 02b.
   - Merge 03 and 03r into main together once 03r is done.
2. **T0 and T1:** correctness and throughput on the code path actually used.
3. **E1:** scripted navigation first, then the evolved navigation primitive (04a).
4. **E2:** a short optimizer screen on that task.
5. **E3:** the minimal A/B organism (04b).
6. **E4:** does useful information cross between the two modules (04c)?

Track B continues in parallel: 03r, then the mechanism follow-up or closure, then the 03a redesign.

**Tripwire.** No new infrastructure beyond T0, T1 and minimal module save/load until the minimal A/B organism runs. Everything after E4 is direction, not schedule.

## Shared foundations

### T0: correctness on the path you use

- **Compute accounting:** count every rollout, tick, neural update and GPU-second actually used, including checkpoints, validation, final evaluation and tuning.
- **Tests:** a genome and its score stay paired through every operation; every parameter is inherited completely; save, load and replay reproduce behaviour.
- **Replay:** exact only in a deterministic mode. Otherwise it must agree within a tolerance declared in advance.
- **Island-path bugs:** three are suspected from reading the code. Confirm each with a failing test, then fix it. These fixes block only experiments that use islands; single-island work proceeds.
- **Gate:** the tests pass, and the energy ledger and numerical checks pass.

### T1: throughput, profile first

- The repository already batches evaluations in chunks. Profile to find the actual bottleneck, then tune chunk size, memory use and batching.
- Any implementation change gets an equivalence check against the previous engine within a declared tolerance, recorded in DECISIONS.md.
- **Gate:** the next scheduled experiment fits its budget at the measured speed, which is currently about 2 times experiment 02's.
  - *Amended 28 September (D086, both reviewers): staged.* T1's engineering closes on its profile and the single-strain padding test. A bounded E1 pilot then measures Task N's throughput, and a committed budget calculation for 04a and E2 is made against an explicit cap. If it does not fit: shrink the experiment first, then batch several runs together (T1.3), then reopen T1.
- A port to another framework, such as a JAX toolkit, is considered only if profiling points at the framework itself and the next experiments cannot fit otherwise.

### Module save/load now, assembly later

04a needs to save and replay a module. The full assembly layer is built when 04b starts:

- the interface contract (identity, inputs, internal state, outputs, parameters, evidence);
- separate recurrent blocks;
- an explicit rule for what inactive modules do.

## Track E

### E1 / 04a: navigation primitive

- **Positive control first.** Experiment 02's champions circled rather than navigated. A scripted navigator must reach moved targets with the declared body and sensors before any evolution. If it cannot, redesign the body or sensors first, for example by adding head oscillation for sensing over time.
- **Gate:** reaches moved targets on unseen layouts and beats simple movement baselines. Food collection alone is not enough.
- **Bridge 1 (optional):** also build the module on two of experiment 03's validated null ensembles, such as SH and SH-route, with several graphs each and runs within graphs.

### E2: short optimizer screen

- Run on E1's task, with equal total simulator work including tuning, comparable initialisation, 3 runs per method, and GPU time reported. The methods:
  - independent random sampling, meaning fresh random genomes with no adaptation;
  - the current genetic algorithm, with a single island;
  - one adaptive evolution strategy;
  - optionally, Augmented Random Search, labelled as an adaptive method.
- **Its only job is to choose the optimizer for E3.** The full topology × optimizer study belongs to Track B, later.
- Read ENOMAD before this screen. An ENOMAD-inspired hybrid is a later option.

### E3 / 04b: minimal A/B organism

- **The organism:** two copies of the validated navigation module. A-related observations go to one copy and B-related observations to the other.
- **The selector:** a set-reset latch. A confirmed visit to A switches to "go to B", and a confirmed visit to B switches to "go to A". It is engineered starting structure, labelled hybrid.
- **Build it in order:**
  1. frozen modules with a fixed selector;
  2. then an evolved selector;
  3. then joint fine-tuning, keeping a fraction of evaluations on the component skills.
- **The trails:**

  | Current goal | Trail followed | Trail deposited after a confirmed visit |
  |---|---|---|
  | Find A | the A trail | the B trail |
  | Find B | the B trail | the A trail |

  Deposition weakens with time since the last confirmed visit; that timer is engineered state and labelled as such. Keep evaporation and exploration. Declare what walls block.
- **Gate:** repeated alternating journeys, counted with an event ledger, on unseen branching mazes, and better than the seed design.
- **Peer-signal controls:** shared trails, own trails only, and scrambled or replayed peer trails, plus a colony evolved without trails from the start.
- **After the minimal organism works, the assembly comparison:**
  1. one task-conditioned controller of matched size;
  2. pretrained modules with a fixed selector;
  3. the same modules with an evolved selector;
  4. a modular organism of the same size trained from scratch.

  Report first-use cost including pretraining, and cumulative reuse cost as later organisms reuse the modules. One loss on first use does not settle the value of modularity.
- **Bridge 2 (optional, independent of bridge 1):** the shuttle is a memory task by design. If 03r replicates, running it on N2 and matched null ensembles tests whether N2's memory head start matters for behaviour.

### E4 / 04c: do the two minds share?

Three separate questions, from easiest to hardest:

1. **Shared dependence:** does the same circuitry support both behaviours?
   - Delete each neuron in each mode. Module A's motor output is switched off during B mode, so an A-neuron whose deletion hurts B mode must act through the cross-links.
   - This detects influence between modules, but not whether that influence is useful.
2. **Useful transfer (the primary question of 04c):** does information crossing between modules improve behaviour?
   - Evolve with and without cross-links, matched in everything else.
   - In evolved organisms, cut or scramble the cross-links, and compare against cutting the same number of links inside a module.
   - Add a diagnostic task in which one module senses something the other needs; for example, only module A senses a hazard that module B must avoid.
3. **Consolidation:** can the organism keep both abilities with less circuitry or computation?
   - This needs a mechanism that lets evolution silence or bypass circuitry, such as a cost on active computation that actually differs between candidates, with the savings measured.
   - A cost on cross-links alone would simply delete the cross-links.
   - Without such a mechanism, this question moves to stage 09.

**Also report:**

- the prior results to compare against: goals varying across modular subtasks (Kashtan and Alon, 2005), connection costs (Clune, Mouret and Lipson, 2013), and duplicated modules specialising (Calabretta and colleagues, 2000);
- each run's gene-duplication fate, as description only;
- controls: cross-links impossible; the unevolved duplicates at generation 0; the selector removed.

### Direction after E4 (not scheduled)

| Stage | Build | Gate |
|---|---|---|
| 05: hunter | Prey progression: stationary, moving, obstacle-aware, then a frozen suite of competent prey; food other than prey limited | Captures moving prey from the frozen suite on unseen maps. Coevolution only after that, with historical opponents and a frozen evaluation suite |
| 06: hive logistics | Home, carrying and unloading, resource ledger | Sustained deliveries, balanced accounting, recovery after a blocked route or a moved food source |
| 07: defender | Foraging and homing plus hunter, with an alarm-responsive selector | Better hive outcomes than foragers alone, always-hunters, and fixed switching, across attacks and quiet periods |
| 08: adaptive roles | Identical capabilities, no assigned roles | Measured specialisation and benefit, and redistribution after workers are removed |
| 09: structural evolution | Mutable routing, module removal and duplication, rewiring within modules, and consolidation if it was deferred from 04c | Gains over parameter-only evolution at matched budgets |

The first social experiments use colonies of clones: one genome for every wey, each wey with its own state. Alarm starts as a simple local signal with a fixed lifetime and evolves only once responses to it can be measured.

### Scoring rules for Track E

- Log every raw outcome component. Fix coefficients and ranking rules before any comparison.
- Never reward how trails look, the number of alarms, or use of a particular brain.
- Use fixed horizons and comparable starting resources, not ratios with near-zero denominators.
- Shaping is training assistance: bounded, recorded, and removed from the final benchmark.
- The scorer may know the map; the controller gets only its declared observations.
- Keep separate training, validation and test suites, with the test suite used once.

## Track B

### 03 and 03r

- Merge both into main together when 03r finishes, reported by the pre-registered rule whatever the outcome.
- **If P4 replicates**, the mechanism follow-up asks:
  - where the history effect lives, using neuron and connection deletions;
  - whether it runs through gap junctions or chemical synapses;
  - whether it holds for inputs other than food;
  - what gives N2's random brains their 5 to 7 times stronger response to food input.

  Its label is assigned at pre-registration.
- **If it does not replicate**, it is reported as a borderline result that did not replicate. The memory thread leaves the plan.
- **Either way**, the five validated null ensembles become the standard controls for later experiments.

### 03a: redesign after 03r, before any confirmatory run

- **Keep:** the question; the feasibility pilot on shuffled graphs only, never N2; the three-outcome classification (anatomical recovery, functional substitution, search failure).
- **Change:**
  - **Task.** If P4 replicates, use a task that requires memory. In any case, the feasibility pilot must show that solutions to the task use interneurons.
  - **The 02b risk.** The connections that make neurons critical (to sensor and motor neurons) are ones v3.2 keeps fixed. Either search the targets' interface connections, or pick targets whose criticality does not come only from interface adjacency.
  - **Nulls.** Use experiment 03's validated ensembles, with several graphs each, instead of unconstrained SH.
  - **Budget.** Fit the design to the measured throughput. ~~Shrink the panel (24, then 16, then 12) or the searches before extending the cap, and say which was cut.~~ *Superseded 28 September by the owner's proof-of-concept decision below.*
  - **Wording.** Animal-to-animal variability is not a ceiling on recovery from one fixed graph.
- **The full map** (label assigned at pre-registration) runs only if 03a separates the three outcomes.

**The owner's decision (28 September 2026, D094): a six-neuron proof of concept, capped at 72 GPU-hours.**
- **The panel: 6 neurons,** by foreseeable relevance to the task: **3 high, 2 medium, 1 low.**
  - "Relevance" is defined by a rule fixed in the pre-registration, before any N2 search. One
    candidate is the draft's own rule: deletion criticality measured on target-selection worlds,
    which are never used for final evaluation.
  - Each tier's members are chosen by that rule, not by hand.
- **Expanding the panel:** only if the proof of concept shows an imprinting effect (anatomical
  recovery separated from functional substitution and search failure), and only for a stated
  reason. The expansion gets its own pre-registration.
- **The cap: 72 GPU-hours** for the proof of concept, pilot included, counted with T0's
  accounting. It is registered in code and never extended. If the design does not fit, the
  searches or the null arms are cut, not the six neurons, and the cut is stated.
- **The size of the gap.** At 02's throughput (about 11 genome evaluations per second), the
  draft's design cut to six neurons comes to about 196 GPU-hours of searches: 144
  target-arm-brain combinations, 15 searches each, of 100 generations × 4 replicas × 9 states.
  Whole-brain evolution adds about 10 more. Fitting 72 hours needs about 2.9 times the speed, or a
  leaner design. These are estimates from the draft's arithmetic, not measurements.
- **Where the speed can come from** (from T1's profile, D090-D092; each is measured before it is
  relied on):
  1. **Batch the searches.** The searches are independent, and each generation is a tiny batch
     (36 genomes × 8 worlds). Stepping many searches in lockstep is T1.3's batching of runs.
     Measured gain: about ×1.36 on 02's 20-wey task, where the brain is GPU-bound; ×3.2 and ×4.2 on a
     one-wey task at 4 and 8 runs per batch, where the world's fixed per-tick cost dominates.
  2. **Use a one-wey memory task.** The redesign already calls for a memory task. Built with one
     wey per world, like E1's Task N, it also unlocks lever 1's larger gain, and it cuts brain work
     per world about twentyfold.
  3. **Stage the design.** Run the cheap original-partner refits first. Buy the free searches
     only for targets whose refits are reliable, and stop a search early once it has clearly
     failed. The rules are fixed before the run.
  4. **A leaner search.** Fewer replicas or generations, if the pilot (on shuffles only, never N2)
     shows the search still converges.
  5. **Fewer brain substeps.** The brain's cost scales with them. 32 was chosen for accuracy in 02,
     so a lower count needs the timestep-accuracy check first.
  6. **A sister experiment, not a faster 03a:** score the reinserted neuron by how well the whole
     network reproduces the intact brain's activity on recorded inputs, with no world simulated.
     It could be one to two orders of magnitude cheaper. But it asks whether wiring can be recovered
     from dynamics, not from a task, so it would be a separate, separately registered question.
- **When:** after E1. E1's pilot measures a one-wey task's actual throughput, and the proof of
  concept is sized to that, not to these estimates. Track B's mechanism follow-up for P4 stays
  ahead of it in the queue unless the owner reorders them.

### Later biology questions (unscheduled)

- **Topology × optimizer × normalisation.** Matching spectral radius is one control, not a complete match.
- **A family of named nulls.** State what each preserves, including how the somatic–pharyngeal gap-junction bridge is treated.
- **Activity-anchored fitness.** Match a few recorded perturbation responses; task scores alone leave the wiring underdetermined.
- **A neuromodulatory layer.** The worm's real roaming and dwelling switch is largely neuromodulatory.
- **Sensing over time versus stereo sensing.** Use head oscillation and scripted positive controls for both.

## Standing rules

- **Develop and pilot openly.** Before confirmatory runs, freeze the hypotheses, comparisons, code version, analysis, budget and stopping rules. Keep pilot results separate. Pilots never run the confirmatory comparison itself.
- **Push each pre-registration to GitHub before its confirmatory runs start.** Commit dates are set locally, so only GitHub's receipt time proves the order.
- Change one thing per experiment. Record deviations in DECISIONS.md.
- **Unit of analysis:** the independent evolutionary run. Comparisons against wiring nulls use several independent graphs per ensemble, with runs within graphs.
- Every behaviour claim needs baselines: random or generation-0 strains, and scripted controllers. Every new task gets a scripted positive control before evolution.
- Compare methods at equal total simulator work, including tuning and pretraining, and report GPU time.
- Implementation changes get documented equivalence checks. A suspected bug gets a failing test before its fix.
- Name every null operation. Prefer experiment 03's validated ensembles.
- Publish corrections to public claims promptly, quoting the wrong text rather than deleting it.
- **Novelty wording:** "we did not find a matching study".
- Before each confirmatory freeze, get external review from a model family different from the designer's.
- **Data hygiene:** no connectome data redistributed in any form; `allow_pickle=False` everywhere.

**Reading negative results:**

| Result | Say | Don't say |
|---|---|---|
| Random sampling matches the GA | Check task saturation, optimizer effectiveness, noise and budget | "The task is too easy" |
| N2 matches the nulls | "No detected advantage under these tasks, controls and budgets" | "The worm wiring is neutral" |
| Assembly loses on first use | "This assembly method did not improve the tested cost–performance trade-off"; judge again on cumulative reuse | "Modularity fails" |
| A replication fails | "A borderline result that did not replicate" | Redesigning until it passes |

## Related work

- **Survey v2.** Apply the external review's corrections before citing the survey:
  - remove the claim that N2 learns faster;
  - state fading biological advantage as a hypothesis;
  - name each study's shuffle operation;
  - separate random sampling from Augmented Random Search;
  - drop the 43% animal-to-animal variability as a recovery ceiling;
  - cite the Creamer et al. preprint by version;
  - describe named neurons as solving gene correspondence, not co-adaptation.
- **ENOMAD** (Churchland and Garcia-Ojalvo) is the closest prior work. Read it in full before E2.
- **For the memory thread,** compare 02b's critical core and 03's history effect with the state-dependent mechanisms in evolved klinotaxis models (Izquierdo and colleagues) and with the navigation interneurons in the experimental literature, citing only what survey v2 has checked.
- **A collective-behaviour survey** is needed before claims for stages 05 to 08. It should cover double-pheromone mechanisms, evolved signalling, swarm robotics, task allocation, behaviour arbitration, predator–prey coevolution, and causal measures of cooperation.

## What would change this roadmap

- **03r replicates:** the mechanism follow-up comes next in Track B, 03a switches to a memory task, and bridge 2 gains priority.
- **03r does not replicate:** the memory thread leaves the plan, and 03a's task is chosen on other grounds.
- **The next experiment does not fit at measured speed:** shrink the experiment first. Change frameworks only if profiling points there.
- **The E1 positive control fails:** redesign the body or sensors before evolving anything.
- **E2 finds random sampling matching the GA:** diagnose saturation, noise and budget before building on the task.
- **The minimal A/B organism fails:** diagnose sensing, objective, controller capacity and optimizer progress separately before adding capability.
- **04c finds no useful transfer:** report it, and check whether the latch or the module interfaces block transfer before concluding anything about evolution.
- **Infrastructure keeps growing while the first organism does not exist:** the tripwire applies. Stop and ship the minimal A/B organism.

## Carried over from v2.2

Items v2.2 had that v3's text does not, kept here until the owner decides them:

- **The owner's question, as v2.2 put it:** is the worm connectome shaped for worm-like tasks,
  under worm-like plasticity?
- **Plasticity.** D045 recorded "design now, run later":
  - one within-lifetime adaptation task, for example a food-odour association that reverses
    mid-life;
  - one explicit rule, for example reward-modulated Hebbian learning on chemical synapses;
  - three controls: frozen weights, recurrent memory without plasticity, and the rule on
    shuffled graphs.
  It runs only after a task and search are validated.
- **Task specificity.** A matched non-worm-like control task on the same interface and world.
  "Avoid food" is not suitable: 03's design rejected it because it can be solved by not moving. Worm-task *specificity* has still never been
  tested. 03 compared N2 with null graphs, not tasks with control tasks.
- **The label "04".** v2.2 and older documents (the 03a draft, 03's pre-registration and
  DECISIONS) use "04" for *capability use with the 03 controls*, gated by a capability-task
  pilot (3b): a task where matched current observations need different actions, validated
  against memoryless controllers. In v3, 04a-c are Track E stages. Documents written before v3
  keep the old meaning.
- **Later, from the 03a draft:** the full self-consistency map, leave-k-out, missing synapses,
  and a full self-consistent-field loop.

## Credits

Ideas, direction and decisions: Juan H. González Estefan. Stage structure and two roadmap reviews: Astra 6 (OpenAI). Experiments 02b, 03 and 03r and the status report: Claude Code running Claude Opus 5.5 (Anthropic). Reviews of 02, 02b, 03 and 03r at every stage: Astra 6 (OpenAI) and Fable 5.1 (Anthropic); each review is archived in `docs/reviews/`, and the errors they caught are in `docs/REVIEW_TRAIL.md`. Roadmap versions, in conversation: Claude (Anthropic), using Claude Fable 5.1 and later Claude Opus 5.5.
