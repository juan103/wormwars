You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

Design consultation, before any spec exists: attack the shape of the next experiment.

## Where the project stands (read these rather than trusting this summary)

The working directory is the WormWars repository. Swarms of simulated worms ("weys") forage in 2D
worlds; each brain is a leaky rate network whose wiring is the C. elegans connectome (N2), compared
with degree-preserving shuffles (SH) and random sparse graphs (RD) of the same size. Weights,
time constants and biases evolve; there is no plasticity within a lifetime.

- `experiments/01b-direction-corrected/RESULTS.md` - the current result: on one foraging task with
  one hand-chosen sensor/motor interface, N2 reaches higher mean best-of-generation fitness than SH
  and RD, and a higher final score than RD. It is a single graph, 25 generations, and calibration
  matches motor drive only approximately.
- `DECISIONS.md` D031 (reversed synapses in experiment 01), D032 (8 integrator substeps are too few
  for strongly evolved genomes), D033 (review of 01b and what it changed).
- `configs/interface.yaml` and `wormwars/interface*` - which neurons receive which sensory signals
  and which neurons are read out as motor commands. Sensors available in the world: food scent
  left/right, ally and enemy pheromone, hazard, damage, collision (front/rear).
- `.codex-remote-attachments/**/1-ROADMAP.md` - an earlier draft roadmap (tasks x plasticity x
  neuron budget). `Astra6/reviews/2026-09-24-roadmap-v1.md` - a review of that draft.

## The proposed next experiment (agreed in outline with the project owner, not yet specified)

**Question 1, generalisation.** Does the N2-vs-controls result hold beyond one arbitrary scenario
and beyond fixed weights?
**Question 2, specialisation.** If N2 has an advantage, is it concentrated where conditions are
worm-like, perhaps under a particular kind of within-lifetime plasticity? This would be a pattern
consistent with specialisation; it cannot show evolution optimised the wiring for it.

**Design.** A grid: brains (N2, SH, RD) x tasks x plasticity. The neuron-budget axis of the earlier
roadmap is dropped. "Worm-likeness" is manipulated two ways:
- *By task:* two or three tasks, some mirroring real worm behaviour (e.g. chemotaxis, avoidance of a
  noxious stimulus), some not.
- *By interface:* each task is run with the biologically correct sensor/motor mapping (food scent
  into chemosensory neurons such as ASE and AWA) and with a deliberately wrong mapping (the same
  signal into, say, touch neurons). Only the interface's biological correctness changes, and the
  task stays identical. The prediction: N2's advantage appears with correct mappings and not with
  wrong ones, while SH and RD are indifferent to which mapping they get.
- *Plasticity columns:* none (as now), plus one or two within-lifetime learning rules on the fixed
  wiring mask (e.g. Hebbian, reward-modulated, short-term synaptic plasticity). The wiring never
  changes; only synapse strengths adapt.

Everything will be pre-registered, as 01b was.

## What I want from you

Be concrete and brief. Numbered points, each marked MAJOR or MINOR, with reasons.

1. **Is the correct-vs-wrong mapping a valid test of specialisation?** What confounds it? For
   example: a wrong mapping changes graph distances from sensors to motors, which differ between
   N2, SH and RD; motor calibration; a wrong mapping may accidentally favour the controls. How
   should wrong mappings be constructed (how many, matched on what) so the comparison is fair?
2. **Tasks.** Which two or three, feasible with the sensors above, give the sharpest contrast
   between worm-like and not worm-like? How should each be validated with simple diagnostic
   controllers, so a task is known to demand what we claim before it counts?
3. **Plasticity.** Which one or two rules give the sharpest test? How do we avoid crediting
   plasticity for what recurrent activity could do with fixed weights? What must be matched
   (parameter counts, evolutionary budget, reward access)?
4. **The statistical test.** What exactly should be pre-registered for the interaction (the test,
   the smallest effect of interest, how many control graphs, runs and generations)? The last
   comparison cost about 1 GPU-hour for 45 runs of 25 generations on one RTX 5080; give a rough
   budget for your design.
5. **What would make the whole grid uninformative,** and what should be cut first to make it
   affordable?

Finish with the single change you would make to this design if you could make only one.
