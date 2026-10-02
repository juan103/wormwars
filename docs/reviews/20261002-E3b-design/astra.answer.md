**Verdict: revise.** Keep the staging. Before proceeding to E3b-0’s plan, clarify what the controls establish, replace the tautological alternation measure, and make trail formation and exploration explicit feasibility gates. I checked `ea06ce4`, the cited records, and the engine.

My answers to the seven questions:

1. **Staging and budget:** exploratory E3b-0 followed by a separate pre-registration is appropriate. The proposed E3b-1 workload is not yet budgeted credibly. E3a’s Stage 3 took **1.47 hours** for eight runs, population 32, 16 worlds, 500 generations, 600 ticks, one wey. Scaling work by eight weys and twice the horizon gives **23.5 hours per arm; 47 hours for shared-trail and no-trail training**, before additional evaluation. Actual GPU scaling may be substantially better; measure it. Reduce generations/worlds before sacrificing independent runs or the no-trail arm. [Committed timing](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3a/summary.json:152)

2. **“Better than the seed”:** yes—jointly tune an explicitly frozen **maze-adapted seed**, then compare on untouched mazes. Seed and descendants must receive identical reflexes, trail rules, scents and movement mechanics. Joint tuning already evolves selector parameters and responses to the combined scent/trail signal. No separate selector search is required. Correct the motivation: E3a’s **+2.36 was against Stage 2 champions**, not against engineered E; its rare-success finding concerns one particular GA initialization and mutation scheme.

3. **Wall reflex:** engineer it, label it, and freeze it across arms. Demonstrate corners, junctions, head-on encounters and dead-end exits. Sliding alone does not establish navigability. Include the carrier-plus-reflex baseline so that maze performance attributable to the reflex is visible.

4. **Local scents:** retain short-range path-distance scents. They provide an interpretable endpoint approach mechanism. Freeze their actual spatial support and gain. Beyond that support, the organism needs an explicit exploration mechanism: the E3a carrier’s fixed turn is not evidence of adequate exploration.

5. **Trees or loops:** trees first. They satisfy the branching-maze gate while limiting scope. They support claims about discovery and reuse of routes; competing-route optimization needs loops. A wall follower may already perform strongly, so measure its ceiling.

6. **Literature:** yes, before fixing E3b-0’s trail algorithm. The references are materially different. **Panait–Luke uses two agent-deposited pheromones, but its principal algorithm tops concentrations up using neighbouring values**, rather than your time-decaying additive deposits. **StarLogo uses a nest scent** for returning home. These are useful precedents, not interchangeable implementations. [Panait–Luke paper](https://cs.gmu.edu/~lpanait/papers/panait04ant.pdf), [MIT’s StarLogo description](https://web.mit.edu/mitstep/starlogo/samples/ants.htm)

7. **Own-trail approximation:** no, unless demonstrated equivalent to exact attribution. A spatial ownership mask cannot separate overlapping, diffused contributions. Use per-wey fields initially. At 4,096 simultaneous worlds, eight weys, two channels and 33×33 float32 grids, those fields occupy **272 MiB before working buffers**—worth benchmarking before weakening the control.

The main threats to informativeness are:

- **Decreasing deposition does not guarantee a sourceward gradient.** In a simplified single-pass trail, exponential deposition decay at rate λ and evaporation at rate μ give concentration proportional to `exp[(μ−λ)s]`, where `s` is departure-to-deposition time. The gradient points backward only when λ exceeds μ; otherwise it is flat or reversed. The engine’s default decay, **0.93 per tick**, gives a half-life of **9.55 ticks**. Measure direction, persistence, stationary accumulation and neural saturation under the chosen settings. [Current dynamics](D:/Claude/random/wormWars/wormwars/fields.py:128)

- **The colony must bootstrap from empty fields.** Nobody deposits before reaching A; nobody establishes a B trail before reaching B. Thus both first discoveries require exploration. A successful BFS oracle proves geometric reachability, not seed feasibility. The scripted trail follower must use the organism’s sensory access and movement limits; declare whether “perfect memory” means only a goal bit or also route knowledge.

- **Replay and scrambling answer different questions.** Same-maze replay preserves useful route information and tests dependence on live coupling. Matching replay does not establish that peers were useless. A deterministic replay of identical starting conditions may reproduce the live treatment. Keep each recipient’s live own trail, replace only peer contributions, and specify independent donor episode randomness. A destructive scramble must respect open cells and match signal amount adequately. Count donor-generation cost.

- **Confirmed-visit alternation is guaranteed by the scorer.** `_advance_shuttle` accepts only the current goal and immediately switches it. Its confirmed sequence necessarily alternates. Measure wrong/repeated **raw entries**, completed round trips, and the fraction of weys completing repeated trips. A mean can conceal one productive wey and seven failures. Treat unfinished journey times as censored; later-wey speed-up alone is not causal evidence of peer assistance. [Event implementation](D:/Claude/random/wormWars/wormwars/world.py:608)

- **“Walls block diffusion” is insufficient.** Pin the accessible-cell graph, corner rules and absorbing versus no-flux boundaries. Test movement and bilateral sensing for shortcuts across walls. Current movement checks only the proposed head cell; collision signals combine **WALL + BODY**, and body density is blurred without wall masking. A purported wall reflex would therefore also react to peers and body signals across walls. Prefer wall-only reflex inputs for this experiment, or explicitly retain and control those interactions. [Collision and movement code](D:/Claude/random/wormWars/wormwars/world.py:855)

- **Several changes extend beyond the listed engine survey.** The rollout scorer also assumes one score per world and must aggregate per-wey visits correctly. The inherited Task N configuration disables pheromone deposition and sensing gain. Freeze arena geometry independently of colony size, separate maze and episode randomness, and preserve the existing energy-off task. [Rollout scoring](D:/Claude/random/wormWars/wormwars/evo/rollout.py:87), [Task configuration](D:/Claude/random/wormWars/wormwars/e1/task.py:23)

**Before E3b-1 is pre-registered, E3b-0 must establish:**

1. **Correct mechanics:** test-first evidence for per-wey events/timers, exact own/peer separation, wall isolation, and task-off equivalence—including E3a.
2. **A usable task:** oracle success under actual movement limits; seed exploration and repeated journeys from empty fields; measured blind-baseline performance, with neither universal failure nor a trivial ceiling.
3. **A usable signal:** demonstrably navigable trails across relevant delays and junctions, plus a scripted example where the peer-control intervention removes useful information.
4. **A feasible full workload:** timings and peak memory at intended compositions, including both training arms, validation, replay production, assays and reserve within approximately 30 hours.
5. **A frozen inference plan:** seed artifact, mutation mask, controls, untouched maze blocks, minimum repeated-journey criterion, meaningful improvement margin and run-level paired inference. Wey observations within a colony are not independent replicates. Recalibrate memory-assay durations to maze journeys rather than copying E3a’s timing.

E3b-0 need not demonstrate an evolutionary advantage. It must establish that E3b-1 can detect one, and that a null result would be interpretable.