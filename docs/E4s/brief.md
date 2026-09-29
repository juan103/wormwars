You are doing a deep literature research for WormWars, an open-science project that evolves brains
on the C. elegans connectome in a simulated 2D world. The repository is your working directory
(read-only for you); `README.md`, `ROADMAP.md` and `experiments/E2d-taskn-diagnosis/RESULTS.md` give
the context. Use web search and fetch freely. Cite every claim with a link (journal page, PMC,
arXiv, or bioRxiv), and say when you are unsure or when a claim rests on a single study.

## What we have

- **The brain:** a continuous-time rate network whose wiring is the real C. elegans connectome (302
  neurons; chemical synapses and gap junctions) used as a fixed sparsity mask. Per neuron: a time
  constant τ in [0.5, 20] and a bias in [−2, 2]. Per chemical synapse: a weight in [−3, 3]. Per gap
  junction: a conductance in [0, 2]. 32 integration substeps per world tick. `wormwars/brain.py`.
- **The interface** (`configs/interface.yaml`, `wormwars/interface.py`): world quantities are
  injected as currents into named sensory neurons. The goal scent reaches left and right sensor
  points on the head, into AWA, AWC and ASE (left and right). Motors are read from named motor
  neurons: turn = the activity of the "turn plus" set minus the "turn minus" set, and forward speed
  similarly.
- **The task (Task N, from E1):** one agent (a "wey") in an arena; a scent source relocates each time
  it is reached; the score is the number of sources reached in 300 ticks.
- **What happened:** a scripted stereo steerer (turn rate proportional to left − right, "S-const")
  reaches 8.7 sources per episode. Every evolved brain (GA, OpenAI-ES, random sampling, and several
  operator variants; 47 champions) plateaus near 2.2. None of them benefits from intact left-right
  input: with the two sensors averaged or swapped, they score the same. They behave like a scripted
  controller that reads only the mean of the two sensors (2.20). A low-gain scripted stereo steerer
  scores 2.27 and does collapse under those probes.

## What we want to build: "E4s", a hand-built stereo module grafted onto the connectome

Two noses (left and right scent inputs), a small **ring attractor borrowed from the fly's
head-direction system**, and a readout in which the active part of the ring biases turning left or
right. The module's neurons are added to the 302, connected to the sensory inputs and to the turn
motor neurons, and then evolution tunes everything together. A later study may remove neurons one by
one to find the minimum.

## Please research, in depth

1. **The fly's ring attractor, as a model we can port into a small rate network:**
   - the minimal circuit motifs (E-PG, P-EN, P-EG, Δ7, and anything else needed);
   - their connectivity patterns and signs, and how many neurons a working model needs;
   - how the bump is anchored by sensory input and rotated by angular velocity;
   - which published models give explicit, reusable connectivity matrices and parameters (rate or
     spiking), and how robust they are to noise and parameter changes.
2. **Turning a direction representation into a steering command:**
   - the fly's goal-directed steering circuits (FC2, PFL3, PFL2 and related): how a heading bump is
     compared with a goal and turned into left/right turning;
   - the bee central-complex steering model (Stone et al. 2017);
   - which is simplest to port.
3. **Odor direction in such circuits:**
   - how flies or other animals encode where an odor comes from relative to the body (bilateral odor
     comparison, wind direction, the fan-shaped body);
   - models in which a bilateral chemical difference, not vision, anchors a ring or a bump;
   - how a memory of the odor's direction is kept across the animal's own turns (a copy of the turn
     command rotating the bump).
4. **The worm side:**
   - C. elegans klinotaxis and weathervane circuits (ASE, AWC and AWA; AIY, AIZ, RIA; SMB, SMD, RMD
     and the head motor neurons);
   - which worm neurons would be natural graft points for inputs and outputs;
   - what is known about bilateral versus temporal sampling in the real worm.
5. **Prior work on grafting hand-designed modules into evolved or connectome-constrained networks:**
   - seeding evolution with a designed circuit; "neural prosthesis" models;
   - modular neuroevolution that keeps or erodes a seeded function;
   - whether evolution tends to keep, improve or dismantle a seeded circuit, and how people measured
     it.
6. **Practical recommendations for our rate network,** with reasons:
   - the ring size (number of neurons), and whether a linear or two-cell simplification suffices,
     given that we have only two noses;
   - how to map left and right scent onto the ring;
   - how to read out left/right turning;
   - initial τ, bias and weight ranges compatible with our bounds;
   - which parameters of the module evolution should be allowed to change;
   - what could make the module fail in our setting, for example the time scales (32 substeps per
     tick), saturation, or our motor readout.
7. **Measurement:** how to show that the grafted module is used, stays used through evolution, or is
   eroded. We already have the averaged and swapped sensor probes.

**Answer format:** a structured report with a short executive summary first; then one section per
topic above, each with citations; then a concrete proposed design (neurons, connections, signs,
initial parameters, graft points), marking clearly what is established, what is plausible, and what
is our guess; then open questions and risks. Be concrete and honest about uncertainty. Do not edit any
files.
