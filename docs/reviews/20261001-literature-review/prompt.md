# Literature review request: WormWars (evolving brains on the C. elegans connectome)

## Who we are and what we have
WormWars is an open-science project (public repo: https://github.com/juan103/wormwars; see README.md,
ROADMAP.md, DECISIONS.md, docs/E4s/DESIGN.md). We evolve controllers ("weys") that live in a 2D game
world. Each brain is a continuous-time rate network (CTRNN-like) on the C. elegans hermaphrodite
connectome (302 neurons; chemical synapses and gap junctions as a fixed mask):
- per-neuron time constant τ ∈ [0.5, 20] ticks, bias ∈ [−2, 2], output tanh(v); chemical weights
  w ∈ [−3, 3], gap conductances g ∈ [0, 2]; 32 integration substeps per world tick;
- sensors inject currents into named sensory neurons (food scent left/right → AWA, AWC, ASE L/R);
  motors are read from named neurons (turning = SMD/RMD dorsal minus ventral; forward = AVB/PVC
  minus AVA/AVD/AVE);
- optimizer: a plain genetic algorithm (population 32, truncation selection, elitism, Gaussian
  mutation); we also screened an OpenAI-style evolution strategy and random sampling.

## What we found (the reason for this review)
On a chemotaxis task (one scent source, Gaussian, relocating; score = targets reached per episode),
every evolved champion (47 of them, across optimizers and settings) sits on a "non-stereo plateau":
about 2.2 targets per episode, about the level of a scripted controller that uses only the MEAN of
the two sensors. None exploits the left-right difference. A scripted stereo steerer
(turn = bias + k·(L − R)) reaches 8.5 at k ≈ 256, but the left-right difference at the sensors is
tiny (about 0.004–0.017) against a common level of about 0.02–0.35. The evolved champions' open-loop
stereo gain is about 0.1.

## Where we want to go
- E4s (now): hand-build a stereo module (two "noses", a ring attractor borrowed from the fly
  head-direction system that keeps an egocentric memory of where the smell came from, a left/right
  readout onto the turning neurons), graft it onto the 302-neuron connectome as extra neurons, then
  let evolution optimise the whole brain. Question: does evolution keep, improve or erode it?
- E3 (next): a minimal A/B organism: two copies of a navigation module (one for goal A, one for goal
  B) switched by a set-reset latch (flip-flop), shuttling between two places and laying trails.
- E4 (later): "gluing" modules or connectomes together with a flip-flop and letting evolution merge
  them; then pruning neurons one by one to find the minimal circuit that still does the job.

## What we need from you
Above all: **what has already been built, measured or released that would save us from developing
it again?** For each item, tell us what we can reuse (equations, parameters, code, datasets, results)
and what it would save us. Also tell us where our plan repeats known failures.

Please research these, in priority order:

1. **Evolved or trained controllers on the C. elegans connectome, for chemotaxis.** Who has done it
   (for example Izquierdo & Beer, Izquierdo & Lockery, Olivares et al., BAAIWorm, OpenWorm/c302;
   these are leads to verify, not a complete list)? Model type, which neurons and synapses were kept,
   the optimizer, the task and the results. Is their code available, and under what licence?
2. **Stereo (tropotaxis) versus temporal (klinotaxis) steering, in worms and in models.**
   - Can C. elegans compare its two sides at all? Give the amphid separation, with a source.
   - Which circuits implement klinotaxis and weathervaning (AIY, AIZ, RIA, SMB, SMD, …)?
   - Has any connectome-constrained model evolved or learned bilateral steering?
   - Is our plateau a known phenomenon: evolved agents ignoring a small bilateral difference? What
     remedies are known (shaping, curricula, noise, sensor geometry, gain, seeding)?
3. **Minimal stereo-steering circuits.**
   - Braitenberg vehicles and their formal analyses;
   - bilateral-comparison circuits in insects (for example Drosophila antennal lateralisation; silkmoth
     flip-flop steering);
   - how much gain and common-mode rejection they need, and whether a 2–4 neuron circuit suffices.
   We suspect we may not need a ring at all for this task.
4. **Ring attractors as portable rate models.**
   - Minimal models with explicit equations and parameter values (for example Goulard et al. 2021,
     Stone et al. 2017, Noorman et al. 2024, Kakaria & de Bivort 2017), with the equation numbers
     you checked.
   - Rotation by angular velocity (the P-EN shifters).
   - Any ring anchored by a bilateral chemical or wind signal (for example Okubo et al. 2020).
   - Released code.
   - Is an egocentric odour-direction memory known to help odour navigation, and in which tasks?
5. **Seeding or grafting designed modules into evolved or connectome-constrained networks,** and what
   evolution then does to them: retention, erosion, redundancy, transfer into the host. Include:
   - NEAT-style seeding;
   - incremental or modular neuroevolution;
   - protecting modules with lower mutation rates;
   - "neural prosthesis" or augmentation models;
   - catastrophic forgetting in neuroevolution.
6. **Modular organisms switched by a latch or flip-flop** (our E3/E4): behaviour arbitration, action
   selection with a set-reset memory, evolved versus designed selectors, and cross-talk or sharing
   between modules.
7. **Finding minimal circuits by pruning or lesioning** evolved networks: methods and pitfalls.
8. **Software we could reuse:** C. elegans simulators with chemotaxis tasks, CTRNN or neuroevolution
   libraries, and ring-attractor code. Give licences and how maintained they are.

## Output format (important)
- Start with **"Reuse now"**: a ranked list of what would save us the most development time, with a
  link and what exactly to take from it.
- Then **"Our plan versus prior work"**: for each part of E4s/E3/E4, whether it is novel, done before
  (by whom), or known to fail.
- Then one section per topic above.
- **Tag every claim:**
  - [READ] you read the full text;
  - [ABSTRACT] you saw only the abstract;
  - [SECONDARY] from a review or another paper's citation;
  - [INFERENCE] your own reasoning.
- Give a DOI or stable link for every source. Never invent a citation. If you are unsure a paper
  exists, say so.
- **Quote the exact equations and parameter values** you took from a paper, with the equation or
  table number.
- **Mark preprints and single studies.**
- **End with "Open questions"**: what the literature does not answer, which we would have to test
  ourselves.
