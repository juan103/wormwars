**Verdict: revise.** The construction excludes goals from a strictly maintained outer-wall circuit. It does **not** establish that wall-following cannot solve the task, and G1 currently omits a blind strategy that the design itself identifies as a threat.

I verified HEAD is `40bd50f`, read the specified code and earlier results, and checked the proposed geometry independently in memory. No files were changed. Python was unavailable in this environment, so I did not run the repository’s dynamics.

Required changes:

1. **Separate the geometric guarantee from the behavioural claim.**

   The closed 5 × 5 block is a sensible rule **including the corner posts**. For this particular lattice, it is more conservative than “one grid cell of margin” suggests: excluding those posts from the perimeter component also excludes the wall segments attached to them. The goal block has at least four world-grid units of continuous clearance from perimeter-connected walls. I would retain this rule, rather than enlarge it speculatively. This follows from the carving geometry in [maze.py](D:/Claude/random/wormWars/wormwars/e3/maze.py:89).

   But clearance does not guarantee that W2—or a controller using two collision sensors—remains attached to that component. The statement in [design §6.1](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:139), “the scripted one will not,” is unsupported before its policy and dynamics are specified.

   There is another loophole: **both goals may touch the same island.** I checked a valid `k=6` construction with island-safe goals at zero-based cells `(1,1)` and `(2,2)`, graph distance six, touching a common wall component. Transferring onto that island could restore a circuit visiting both goals.

   Either require that **no wall component touches both goal blocks**, or explicitly retain and test this possibility while narrowing the claim to *perimeter-circuit exclusion*. Even the stronger placement rule would not defeat arbitrary exploration or component switching.

2. **Correct the spawn claim and qualify the wall-follower operationally.**

   [Design §2](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:49) says perimeter-adjacent spawn cells put a follower on the outer circuit. They do not: [MazeWorld](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:215) starts animals at cell centres with uniformly random headings. A cell may also border both perimeter-connected and island walls.

   Perimeter-adjacent spawning is acceptable as a declared task condition. It is favourable to demonstrating perimeter-follower failure, however; it is not the hardest adversarial test of blind success.

   Specify the new controller completely, test both handednesses, and measure initial wall acquisition and subsequent component changes. A separate diagnostic can initialise a follower beside a known wall with a tangent heading. Do not silently give that initialisation to only one competitive baseline.

   Also be precise about “collisions”: crowding and pushing are disabled here. Wall encounters cause rejection or axis sliding, which can change the trajectory; animals are not physically knocked onto islands by their neighbours. See [maze_world.py](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:317).

3. **Include every credible blind baseline in calibration and G1/G3.**

   The current definition of “best scent-free control” excludes the random walk and apparently standalone W2. That is a substantive error. If random bouncing solves the open maze, E3d must not pass merely because a strict wall-follower fails.

   Use the maximum over the declared blind-control family, including the random walk, neural W2, W2-turn and both wall-following directions. A small, fixed persistence/turn-rate grid for the random walk would be more persuasive than relying entirely on parameters chosen for another task.

   Two implementation details matter:

   - **Scripted and neural W2 are different baselines.** E3b-1 explicitly documents that its neural W2 scores are not comparable with E3b-0’s scripted W2 scores. Specify which implementation each row uses. [E3b-1 results, G](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:94)
   - **E3c’s W2-turn grid was already inadequate at its upper boundary.** Its best point was 1.4 and validation scores were still rising. Extend the fixed grid within valid parameter bounds before calibration, or justify retaining that limitation. [E3c results, references](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:80)

4. **Validate discovery and repeated navigation, not just reachability and average score.**

   The underlying distance code supports loops: `free_distance` is ordinary BFS over free cells, and `tree_distance`, despite its name, is BFS over the supplied graph. The oracle also constructs BFS next hops. **Ensure every added opening is recorded in `Maze.edges`**, so graph and raster geometry agree. [maze.py](D:/Claude/random/wormWars/wormwars/e3/maze.py:43), [MazeOracle](D:/Claude/random/wormWars/wormwars/e3/maze_controls.py:127)

   The important limitation is scent range. Scent is zero beyond nine grid cells, and at distance nine its scaled value is approximately `0.00389`, below the scripted follower’s `0.005` switching threshold. Without detectable scent or a useful trail, the follower uses W2. Thus the construction can impair the navigator’s discovery phase through the very mechanism it is designed to impair in blind controls. Graph connectivity does not resolve this. [Scent construction](D:/Claude/random/wormWars/wormwars/e3/maze_world.py:234), [follower policy](D:/Claude/random/wormWars/wormwars/e3/maze_controls.py:60)

   Report first-A discovery, first-B discovery, zero-visit share, completed round trips and later-leg rate. Restore a repeated-journey qualification for the seed; E3b-0 and E3b-1 already used a median-leg requirement. [E3b-1 results](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3b-1/RESULTS.md:98)

   **Keep H = 2,400 initially.** It preserves comparability and tests whether blind strategies eventually succeed. Shortening it merely to suppress them would change the question.

5. **Make preservation of maze structure an explicit selection consideration.**

   At `k=6–10`, **75–85% of all internal cell connections are open**. A navigator beating blind controls does not establish that substantial maze navigation remains: an almost open arena can also reward scent sensing.

   Report shortest-path detour relative to unobstructed distance, junction/dead-end counts, and direct visibility between relevant locations. The accepted distribution matters: rejection for eligible goals conditions the maze family, differently at each `k`.

   My preferred selection rule is **the smallest k meeting the calibration feasibility criteria**, with a declared structural requirement if “maze-ness” is important. Maximising the raw follower-minus-blind gap can instead favour opening away the problem.

   Targeted openings are a reasonable alternative, not inherently objectionable because they are “designed.” A small family that isolates goal-adjacent wall components while retaining other barriers could satisfy the owner’s intention with fewer openings. Randomise its orientation and placements and validate it with the same controls. Merely moving goals off the outer row is insufficient for the intended anti-circuit objective.

6. **Align calibration with the gate and fully specify confirmation.**

   Calibration followed by an untouched confirmation block is sound. The current optimisation criterion is poorly aligned with the gate: a large absolute gap can coexist with a failing blind/follower ratio or a failing follower/oracle ratio. Select among candidates meeting the calibration requirements, rather than choosing the largest gap unconditionally. [Design §4](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:88)

   Before play, fix maze seeds/IDs, episodes, placement sampling, controller parameters, stochastic streams, aggregation, and failure handling. Define whether confirmation evaluates:

   - the W2-turn setting selected on calibration; or
   - every prespecified setting, with their maximum used as the benchmark.

   Both are defensible. Taking the confirmation maximum is a conservative adversarial benchmark, not automatically invalid test-set tuning; it simply needs to be declared.

   If confirmation fails, report failure. A revised construction needs a fresh confirmation block.

7. **Tighten the interpretation and practical adequacy of G1–G3.**

   - **G1’s 0.25 ratio:** reasonable as an operational separation target, but it does not mean “rarely reaches goals.” A blind score of ten passes against a follower scoring forty. Add an absolute blind-success or repeated-shuttling criterion if *rare success* is the intended claim.
   - **G2’s 50% of oracle:** defensible as a demanding efficiency target, but not a necessary condition for meaningful navigation. The oracle is a privileged waypoint controller, not a proven optimal ceiling. Validate its loop behaviour and require a positive absolute performance floor.
   - **G3’s strictly positive difference:** too weak to establish a useful engineered navigator. Require a declared practical margin and repeated shuttling, rather than an arbitrarily small advantage.

   Define scores as means of colony-level per-wey outcomes, with mazes paired across controllers. For claims about the maze family, report uncertainty by resampling mazes, preserving the eight interacting animals within each colony. Alternatively, explicitly describe the gate as acceptance on this fixed block; do not imply population-level certainty.

8. **Keep champion transfer descriptive, but do not ignore a contradictory result.**

   I agree with keeping the 28 champions outside parameter selection and the primary gate. However, selection on another maze family is **not** a statistical reason that they cannot be adversarial controls.

   If S champions still shuttle effectively, “scripted gate passed” must not become “the E4 task now defeats coverage.” That result would directly qualify the motivation for E3d.

   The P-joint prediction should also remain tentative: E3c found four partial and four nose-dependent champions, with a substantial nose-free component. Retaining half their score is not equivalent to retaining navigation. Add the existing noses-removed intervention on the new confirmation mazes for the seed and champions if making mechanistic interpretations. [E3c results, nose dependence](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3c/RESULTS.md:142)

9. **Expand the specific tests and make equivalence reviewable.**

   [Design §5](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:120) is directionally correct but underspecified.

   Require tests for graph/raster agreement, exactly `k` added edges, connectivity, complete placement feasibility, same-island goal adjacency, episode-independent redraws, and oracle operation on loops. The wall-follower needs coverage and component-retention tests across representative layouts; “scores like E3c’s coverers on a tree maze” is not a precise qualification.

   **Do not reuse E3c’s tour-match interpretation unchanged.** It assumes a 48-directed-move tree circuit; loops have different boundary circuits. Replace it with a declared loop-appropriate recurrence/component measure, or label the old statistic strictly as tree-period matching. [scripts/e3c.py](D:/Claude/random/wormWars/scripts/e3c.py:381)

   For Rule 7, retain the maze-reference check and compare complete tree rollouts against **pre-change `40bd50f` outputs**, at zero tolerance, separately on CPU and the intended GPU composition. Include trajectories/state and event outcomes, not just final means. This follows the existing [T1 equivalence contract](D:/Claude/random/wormWars/docs/foundations/T1.md:111).

   Finally, provide the sizing script and seed. “At least two island-safe cells” is not full placement feasibility: the distance and spawn constraints must also hold. The published sizing table should measure both quantities.