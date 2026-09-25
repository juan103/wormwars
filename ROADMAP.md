# WormWars roadmap (v2, 2026-09-25)

**Status: v2, revised after review by Astra 6 and Fable 5.1** (`docs/reviews/20260925-163118-roadmap/`;
D044, D045). The owner delegated the open decisions. Each is recorded in D045 with its reason.
Costs are GPU-hours on the one RTX 5080. Nothing below is pre-registered yet: each experiment gets
its own pre-registration and review before its confirmatory runs.

## Where the series stands

- **01** (superseded): chemical synapses ran backwards; its conclusions do not hold.
- **01b:** with synapses right, N2 reaches higher mean best-of-generation fitness than shuffles
  (SH) and random graphs (RD) on stereo foraging. As a point estimate, its edge over SH is a head
  start.
- **02** (screening): evolution found meaningful stereo use for neither N2 nor SH, so the primary
  prediction was challenged. Under the biological mapping, the shuffles start worse and catch up.
  N2's random brains are more sensitive to food input overall, not more selective for the
  left-right difference. Shuffles break mirror symmetry and give food neurons direct routes to
  the motor read-out.

**The owner's question:** is the worm connectome shaped for worm-like tasks, under worm-like
plasticity? Every N2-specific signal so far appears at generation 0. Every control so far differs
from N2 in two generic ways, symmetry and routing. Worm-task *specificity* has never been tested
against a matched non-worm-like task.

## Pipeline

### 1. 02b: what the champions compute, plus the deletion operator (about 1 GPU-hour)

No evolution; experiment 02's saved genomes.
- **Replay champions with per-tick logging.** Measure speed and turning against food level, food
  change, the left-right difference and collision. Replay matched current input after different
  histories.
- **Run the corrected input-response probe on evolved genomes,** at generation 0 and 39. Did
  evolution grow or shrink the directional response, and does it track each champion's use of
  stereo?
- **Measure magnitude erosion:** the correlation of |w| at generation 39 with anatomical
  magnitude.
- **Build a true deletion operator.** It removes a neuron's chemical and gap terms, time constant
  and bias, and is tested against a network built without the neuron. The code has only silencing
  (D044).
- **Map deletion criticality** over every non-interface neuron of each evolved T1 champion. 03a's
  panel and headroom depend on it.
- **Gate:** none. It is descriptive, and it informs 03a and 04.

### 2. 03: generation-0 structure and task specificity (about 5-8 GPU-hours, no evolution)

**Question:** is anything about N2 at generation 0 specific to N2 beyond generic graph structure,
and specific to worm-like tasks?

**Graphs:**
- N2, and N2 with the chemical direction reversed;
- 64 graphs from each of these ensembles:
  - ordinary degree-preserving shuffles;
  - routing-matched shuffles (the food pairs get no direct read-out weight beyond N2's);
  - routing- and mirror-matched shuffles (N2's *partial* symmetry, about 0.64 of chemical edges);
  - class-preserving shuffles (swaps within neuron-class blocks).
- Each ensemble is validated for mixing, diversity and residual similarity to N2 near the
  interface.

**Conditions:**
- mappings: M0; four remaps; and a remap of the motor read-out, which is new;
- gap junctions on and off;
- magnitudes anatomical, uniform and permuted.

**Tasks:** 02's stereo (T0) and single-nose (T1) foraging, and a matched non-worm-like control
task on the same interface and world, such as a reward for staying away from food.

**Measures:** about 2048 random genomes per graph, with per-brain values saved:
- input response: directional (signed and absolute), common-mode, and their ratio;
- generation-0 fitness: the mean, and the best of 32.

**Registered signals**, each with an effect margin and an equivalence margin fixed before the
run:
- (a) N2's signed directional response under M0, relative to its common-mode response;
- (b) the generation-0 mapping interaction, and its shuffle-deficit component;
- (c) N2's generation-0 head start on stereo foraging (01b);
- (d) the task-specificity contrast: N2's edge on T0 and T1 minus its edge on the control task.

For each signal, N2 is placed within each ensemble as a percentile, and compared with the
ensemble mean. These are two different claims, and both are reported.

**Gate:**
- **A signal inside an ensemble's equivalence band** is explained by that ensemble's structure.
  The claim narrows accordingly. It does not stop the series (D045).
- **A signal outside every ensemble** stands as N2-specific at generation 0.
- **(d) inside its equivalence band** means N2's edge is general, not worm-task specific.

**Also builds the control ensembles** every later experiment uses, whatever 03 finds.

### 3. Three pilots, in any order (about 6-10 GPU-hours in total)

**3a. Reconstruction feasibility** (for 03a; pilot shuffles only, never N2).
- A refit screen: original-partner refits against random-partner and structural-baseline
  partner sets.
- A real-model planted test: from a brain trained with the neuron, the free search must
  recover that neuron's own evolved wiring where the reference is reachable.
- Timing for the batched search.
- **Pass criterion** is registered in 03a v3.
- **If it fails:** 03a's panel is not run, and the pilot is reported.

**3b. Capability task and search** (for 04; shuffles only).
- Design a task where matched current observations require different actions, so memory or
  stereo is necessary.
- Validate the task against expressive memoryless controllers with the same inputs, and a
  capable positive control.
- Then show that some search finds the capability in evolved champions.
- **If no search finds it,** that procedure stops and is reported, and the capability question is
  not closed.

**3c. Plasticity design** (no GPU; D045).
- Define one within-lifetime adaptation task, for example a food-odour association that
  reverses mid-life.
- Choose one explicit plasticity rule, for example reward-modulated Hebbian on chemical synapses.
- Plan three controls: frozen weights, recurrent memory without plasticity, and the rule on
  shuffled graphs.
- Write it up as a design document and have it reviewed.
- It runs only after 3b shows a task and search can be validated.

### 4. The substantial experiment, chosen by the pilots (budget set at that point)

- **03a,** the self-consistency panel (`experiments/03a-self-consistency/`, v3): if pilot 3a
  passes. It uses 03's matched ensembles as its control graphs.
- **04,** capability use with the 03 controls: if pilot 3b passes. It does *not* require a
  positive 03 (D045).
- **P,** plasticity × topology on the 3c task: if 3b validated its task and search, and 3c's
  design survived review.

If more than one qualifies, the owner chooses. Each needs its own pre-registration and review.

### 5. Later

03b (the full self-consistency map), more tasks, leave-k-out, missing synapses, and a full
self-consistent-field loop, all from the 03a draft.

## Budget

| item | cost |
|---|---|
| 02b | about 1 GPU-hour |
| 03 | about 5-8 GPU-hours |
| pilots 3a and 3b | about 6-10 GPU-hours |
| subtotal, up to the choice of the substantial experiment | under a day of GPU |
| 03a panel | set by its batched pilot; v3 as written is about 31 million genome evaluations, 785 GPU-hours unbatched, so its one-week cap binds unless batching gives more than 5 times the speed |

## Decisions taken for this version (D045)

1. **03 comes first,** with registered margins, 64 graphs per ensemble, a task-specificity
   contrast and the controls both reviewers named. Both reviewers.
2. **04 does not depend on 03 favouring N2.** It depends on 03's controls and its own
   feasibility pilot. Both reviewers.
3. **A generic explanation narrows the claim; it does not stop the series.** Both reviewers.
4. **03a is gated by its own feasibility pilot, not by 03's outcome.** Fable and Astra.
5. **Plasticity: design now, run later.** This follows Astra, because the owner's question names
   plasticity. It keeps Fable's condition: the run needs a task and search validated first.
