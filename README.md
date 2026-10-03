# WormWars: *C. elegans* wiring vs. shuffled and random graphs

> **This is the `roadmap` working branch.** The published record is `main`. This branch holds work
> in progress beyond it until it is merged. E4s-0, E4s-1, E3a and E3b-0 are on `main` (2026-10-03). E3b-1
> is pre-registered (bound 2026-10-03, D186); its implementation is next.

Many parallel 2D worlds on one GPU. In each world, swarms of small creatures called **weys** forage
and fight. Every wey's brain is a small continuous-time recurrent network whose wiring is the real
*C. elegans* connectome (302 neurons, chemical synapses and gap junctions) used as a fixed sparsity
mask. Weights, time constants and biases are evolved. All weys in a swarm share one genome, and
selection acts on team results.

**Start here:**
- **[Experiments at a glance](#experiments-at-a-glance):** one folder per experiment, each with a
  README giving its question, design, result, caveats and exact commands to rerun it.
- **[`ROADMAP.md`](ROADMAP.md):** what comes next and why.
- **[How to help, or get ahead of us](#how-to-help-or-get-ahead-of-us):** compute is our
  bottleneck, and others are welcome to overtake us.
- **[`AGENTS.md`](AGENTS.md):** for people and AI agents working with the code. It covers the
  repository layout and the rules the work follows.
- **[`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md):** what is exactly reproducible, and what
  is not.

## Experiments at a glance

| Experiment | Question | Status | Result, in one line |
|---|---|---|---|
| [01](experiments/01-foraging-n2-vs-controls/README.md) | Does the real wiring (N2) evolve better foragers than shuffled (SH) and random (RD) graphs? | Superseded: its chemical synapses ran backwards (D031) | Reported N2 improving more slowly; that does not hold for the real wiring |
| [01b](experiments/01b-direction-corrected/README.md) | 01's question with the synapses the right way round | Published; pre-registered | N2 reaches higher mean best-of-generation fitness than SH and RD, and a higher final score than RD. It is not shown to improve faster |
| [02](experiments/02-screening/README.md) | Does evolution find stereo foraging, and does N2 use it more? A 12 GPU-hour screening across tasks and food mappings | Published; pre-registered | "challenged: no meaningful N2 use" |
| [02b](experiments/02b-champion-analysis/README.md) | What did 02's champions actually learn? | Published; exploratory re-analysis | They circle and slow down on food. Selection built a slow memory of recent food. It does not revise 02 |
| [03](experiments/03-generation0/README.md) | Before any evolution, do N2's random brains differ from five null ensembles? | Published; pre-registered | History dependence (P4) is distinctive, but borderline: one more routing-matched graph at or above N2 would have failed the test (Holm p 0.047, then 0.070) |
| [03r](experiments/03r-replication/README.md) | A full, separately pre-registered replication of 03 | Published; pre-registered | "Replicated under the registered single-signal test and under 03's original three-signal rule." |
| [03a](experiments/03a-self-consistency/README.md) | Can a missing neuron's wiring be predicted from the rest of the brain plus a task? | Draft; a six-neuron proof of concept capped at 72 GPU-hours is planned (D094), not yet scheduled | None yet. As drafted, its searches alone need about 785 GPU-hours at 02's throughput, plus about 37 for whole-brain evolution |
| [E1](experiments/E1-navigation/README.md) | Can a scripted navigator reach moved targets on unseen layouts, beat blind search, and use the cue? The positive control before evolving a navigator | Published; pre-registered, public before its run | "E1 positive control: passed": 8.68 targets per episode (98.7% of an oracle); 0.03 with a mirrored decoy |
| [04a](experiments/04a-navigation-primitive/README.md) | Can evolution, from random weights on the N2 wiring, produce a brain that reaches moved targets, beats blind search and uses the cue? | Published; pre-registered, public before its run | "04a: passed": 8 of 12 shaped runs (4 of 4 unshaped); the champions use the cue but are weak navigators (2.0-2.8 targets, 23-32% of an oracle) |
| [03m](experiments/03m-p4-mechanism/README.md) | What drives 03's history dependence (P4)? | Exploratory; run, reviewed, corrected | N2's history fades more slowly than nearly all the shuffles'; its large food response depends on weight placement and on RIA and AIY; most weight permutations lower its P4, gap junctions narrow its lead, and no tested single or paired deletion removed it |
| [E2](experiments/E2-optimizer-screen/README.md) | At equal simulator work, does OpenAI-ES find better Task N navigators than 02's GA, with random sampling as a floor? | Published; pre-registered, public before its run | "E2: keep 02's GA": the ES led by 0.12 targets per episode (0.5 needed). The floor fired: random sampling came within 0.36 of the GA, so Task N is diagnosed before E3 builds on it |
| [E2d](experiments/E2d-taskn-diagnosis/README.md) | Why did random sampling come so close? Noise, the operators, budget and stereo use on Task N | Exploratory; plan and runner reviewed; run, reviewed, corrected | "A non-stereo plateau": no champion of 47 meets the "uses the left-right difference" criterion. No tested change (more worlds, gentler mutation, both, a smaller ES σ) leaves the plateau; gentler mutation improved all 8 paired runs but met the bar only with the failed run 2; the ES is budget-limited |
| [E3](experiments/E3-ab-organism/README.md) | Can two hand-built stereo modules be composed, with a one-neuron latch remembering which source is next, into an organism that shuttles between two sources; and can evolution find the selector? (E3a, the shuttle; mazes and colonies are E3b) | E3a pre-registered and public before its run; run, reviewed, corrected. E3b-0 exploratory; run, reviewed, corrected. E3b-1 pre-registered (bound 2026-10-03), not yet run | E3a: the engineered organism shuttles at 12.79 visits per episode (97% of a module fed the goal's scent). "Evolution found a working selector in 1 of 8 runs, not reliably"; a blind search over the whole range found working selectors in 7 of 8; the two scored "unclear" apart. Joint tuning added 2.36 visits. E3b-0: in 5 × 5 tree mazes, linear trails help a scripted follower (+3.57 legs per 1 000 ticks) and the seed with a wall reflex (+0.69); peers' trails speed later discoverers; trail direction is not shown to be used; the trail constants are adaptively selected |
| [E4s](experiments/E4s-stereo-module/README.md) | After E2d's plateau, can a hand-built stereo module grafted onto N2 steer, and what does evolution do to it? (Ahead of plan; stereo sensing is a game-design choice, not worm biology) | E4s-0 exploratory, E4s-1 pre-registered and public before its run; both run, reviewed, corrected | E4s-1, "supports": with the 4-neuron graft's output, evolved brains end +5.19 targets per episode above the same brains evolved without it (16 of 16 pairs), and +3.79 above random signs fixed for the run. The selected brains use the module at both endpoints in 16 of 16 runs (7.14 on average). Part of the benefit is not stereo use, and transfer into the host was not shown |

Next on the roadmap:
- **Published 2026-10-02:** E4s-0 and E4s-1, together; then E3a. **2026-10-03:** E3b-0.
- **Next in Track E:** E3b-1, the roadmap's E3 gate: the tuned colony against the frozen seed in mazes.
  It is pre-registered and bound (D186), at about 21 GPU-hours under a cap of 24. Its implementation is
  next.
- **In the biology track:** a confirmatory study of 03m's leads, then 03a's six-neuron proof of
  concept.

## Newest: mazes, trails and colonies (E3b-0)

**On 256 untouched tree mazes, colonies of 8 weys shuttling between two dead ends do better with shared
linear trails.**
- **The gain, in legs per 1 000 ticks,** shared trails against none:
  - a scripted trail follower: +3.57 [2.97, 4.19];
  - the engineered seed (E3a's organism E, plus a one-sided wall reflex): +0.69 [0.44, 0.93].
- **Peers' trails help:** later discoverers reach the second source 7% sooner (follower) and 13% sooner
  (seed) with shared trails than with their own only.
- **Peer fields the colony did not lay hurt:** a donor colony's trails replayed from another episode on
  the same walls, or the peers' trails scrambled.

**Not shown:**
- that the weys follow a trail's direction;
- that the seed's ability is its own. Most of it comes from the reflex: it makes only +1.09 visits per wey
  over the reflex alone, of 5.78.

**E3a's best tuned organism circles in the maze.**

**The trail constants are adaptively selected.** The search stalled twice, and the qualification rule
changed twice, each change reviewed by both reviewers before it ran.

It is exploratory, at 2.62 GPU-hours. Read
[`experiments/E3-ab-organism/E3b-0/RESULTS.md`](experiments/E3-ab-organism/E3b-0/RESULTS.md), with its
corrections. Its successor, E3b-1, asks whether evolution improves the seed in these mazes. It is
pre-registered.

## Which optimizer for the next stage? (E2)

**At equal simulator work, an evolution strategy did not beat experiment 02's genetic algorithm by
the margin fixed in advance, and random sampling came close enough to both that the task itself is
diagnosed next.** In the wording fixed in advance: *"E2: keep 02's GA (unshaped fitness; the ES did
not satisfy both replacement criteria after paying for its tuning)"*.

- **The screen:** 04a's task, 8 runs per method, each method given about 2.13 million episodes of
  selection. OpenAI-ES paid for its own tuning pilot out of that. Each run's champion was tested once
  on 1 024 unseen worlds.
- **Scores (targets per episode):**
  - the ES 2.09 and the GA 1.96: the ES led by 0.12, and 0.5 was needed;
  - random sampling 1.60: the best of 32 000 random genomes per run, chosen on validation worlds.
- **The floor fired:** random sampling came within 0.36 of the GA, inside the 0.5 set in advance, so
  the roadmap's rule applies: diagnose saturation, noise and budget before building on the task.
  - It is a trigger, not a finding that optimizing adds nothing: the GA gained 22% over random
    sampling, the ES 30%.
  - The trigger depends on one GA run that never learned to use the cue; without it the gap is 0.49.
- **Given more work, the ES kept improving:** 2.33 at 1 000 generations, still short of the margin,
  on 38% more episodes. Every method stayed far below a hand-written steering controller (8.65).
- **How it was done:** Claude Opus 5.5 designed, pre-registered, ran and wrote it up. Astra 6 and
  Fable 5.1 reviewed the design three times and the pre-registration four times before it was bound
  and pushed, and the results after: both asked for text corrections, now dated in its RESULTS.md.

Details: [E2's README](experiments/E2-optimizer-screen/README.md) and its RESULTS.md, and decisions
D117-D125.

## An evolved navigator on the real wiring (E1 and 04a)

**Evolution, starting from random weights on the real *C. elegans* wiring, produced brains that
find a moving scent by using it, reliably but slowly.** In the wording fixed in advance: *"04a:
passed"*.

**The task (E1's Task N):** one wey in an arena with a scent source that jumps somewhere else each
time it is reached; the score is the number of sources reached in 300 ticks.

- **E1, the positive control, first:** a hand-written steering controller reached 8.68 sources per
  episode, 98.7% of an ideal navigator; with the scent read at a mirrored decoy it reached 0.03, and
  blind search at most 0.65. So the task can be done with this body and these sensors.
- **04a:** 16 evolutionary runs of N2 brains, 1 000 generations each, with experiment 02's optimizer.
  12 had a small training bonus for closing in on the source, 4 had none. Each run's champion was
  tested once on 1 024 unseen worlds against five rules.
  - **8 of the 12 main runs passed** (6 were needed), and **all 4 runs without the bonus**. The
    four failures missed only the reliability rule (at least 2 sources in 80% of episodes).
  - **The champions use the cue:** with the scent mirrored, 97-100% of episodes end nearer the
    decoy than the source, and they reach about 0.15 sources; with a constant scent, about 0.2.
  - **But they are weak navigators:** 2.0-2.8 sources per episode, 23-32% of an ideal navigator,
    on indirect paths. Their behaviour looks more like comparing the scent over time than steering
    by left against right; how they use the cue is not shown.
  - **The training bonus was not needed** here (descriptive, 4 runs).
- **What it is not:** evidence that N2's wiring helps (no shuffled graphs were evolved on this task),
  or a measure of how good evolved navigators can get (E2 compared optimizers; above).
- **How it was done:** Claude Opus 5.5 designed, pre-registered, ran and wrote up both. Astra 6 and
  Fable 5.1 reviewed 04a's pre-registration in five rounds before it was bound and pushed, and its
  results after: both asked for text corrections, now dated in its RESULTS.md, and found that the
  run followed its registration.

Details: [E1's README](experiments/E1-navigation/README.md) and
[04a's README](experiments/04a-navigation-primitive/README.md), each with its RESULTS.md, and
decisions D094-D101 and D103-D112.

## Experiment 03 and its full replication, 03r

**At generation 0, before any evolution, the real wiring's random brains showed unusually high
normalised history dependence relative to all five null ensembles, and a full replication
reproduced it.** In the wording fixed in advance: *"Replicated under the registered single-signal
test and under 03's original three-signal rule."* The replication ran with the same probe,
stimulus bank and code; the replication tests sampling, not the probe.

**What was compared:** N2 against five ensembles of shuffled wirings, each keeping N2's degrees and
also, respectively:
- nothing else (SH);
- a cap on direct food read-out edges and weight (SH-route);
- its neuron-class structure (SH-class);
- its mirror-symmetric share, plus the routing cap (SH-mirror);
- its two-way connections (SH-recip).

Only unselected random brains were measured, before any evolution.

**History dependence (P4):** after two food histories converge to the same input, how much of the
earlier difference is still in the turning output.
- **In plain words:** each brain gets food held low for 100 ticks and then ramped up, or held high
  and ramped down, to the same final level. On the last tick the input is identical, so a brain
  with no memory of the two histories would turn the same way in both runs. P4 is the leftover
  difference, divided by how differently the brain turns while it is held low or high.
- **Reading the value:** 0 means no leftover difference in this read-out. N2's 0.93 means that,
  averaged over genomes, the leftover difference is about 93% of that yardstick. It is a ratio of
  averages, not the share of each brain's state that is kept.
- A fuller explanation of all three signals, and of what they do not show:
  [03's README](experiments/03-generation0/README.md#what-the-three-signals-measure-in-plain-words).
- **03:** N2 is above all 128 graphs in four ensembles and 127 of 128 in SH-route, with a
  Holm-adjusted p of 0.047 under 03's registered three-signal rule. One more SH-route graph would
  have made it 0.070.
- **03r** (768 fresh graphs, 256 of them routing-matched, and fresh random brains for N2 too): N2
  is above all graphs in four ensembles, including all 256 routing-matched ones, and 127 of 128 in
  SH-class.
  - **03r's registered primary test** (P4 alone): p = 0.0155.
  - **03's original rule:** p = 0.047 again. One additional SH-class graph would tip it, so it
    remains borderline under that rule.
- **Both runs under both rules:** P4 alone gives 0.0155 in both 03 and 03r; 03's rule gives 0.047
  in both. P4 alone is the registered primary for 03r only.
- **N2's P4 values are close:** 0.931 in 03 and 0.924 in 03r.

**The other two signals:**
- **Steering toward food (P1):** nothing distinctive, in either run.
- **Use of food information (P3):**
  - **03:** inconclusive.
  - **03r's registered label is "reversed against every ensemble"** (opposite-direction
    Holm-adjusted p 0.047; 0, 0 of 256, 0, 0 and 1 graphs at or below N2). The estimated mean score
    was slightly lower with the real food signal than with a constant one.
  - **The caveat:** it is small and unpredicted. N2's P3 measurement is much noisier than the
    ensembles', which undermines the rank test's exchangeability assumption and can make it
    anti-conservative. An exploratory noise-aware check gives about p = 0.07 after correction. It
    is reported as found, with no claim about its cause.

**What this is not:**
- **Not independent evidence.** 03 and 03r compare the same wiring with the same kind of null.
- **Not a wiring-only result.** The nulls move weights as well as wiring.
- **Not a mechanism, nor any advantage for the worm.** An exploratory mechanism study,
  [03m](experiments/03m-p4-mechanism/README.md), found leads (N2's history fades more slowly; its
  large food response depends on weight placement and on RIA and AIY), not a mechanism.

**Why a full replication, and who decided.** One graph decided 03's verdict. So a full,
separately pre-registered replication was run before 03 was merged into main and presented as a
result. 03's first-run results were publicly readable on the `roadmap` branch from 2026-09-27
while 03r ran; its pre-registration was pushed there mid-run, as its
[disclosure](experiments/03r-replication/DISCLOSURE.md) states. 03's own pre-registration was first
pushed to GitHub after its run; that it preceded the run rests on local commit records (D062,
D063).
- **Fable 5.1** (Anthropic) asked for replication before any public claim. It also argued for
  testing P4 alone, which was chosen after seeing 03.
- **Astra 6** (OpenAI) specified fresh random brains for N2 as well as fresh graphs. It did not
  require replication first.
- **Claude Opus 5.5** (Anthropic), who ran the experiments, leaned toward replicating first.
- **The owner decided** on the full replication.

Details: [`experiments/03-generation0/RESULTS.md`](experiments/03-generation0/RESULTS.md),
[`experiments/03r-replication/RESULTS.md`](experiments/03r-replication/RESULTS.md), and
decisions D050-D063 and D080-D083. Summaries and how to rerun:
[03's README](experiments/03-generation0/README.md) and
[03r's README](experiments/03r-replication/README.md).

## How to help, or get ahead of us

**Nearly everything is public:** the pre-registrations, the reviews verbatim from 25 September
on, the decisions with their reasons, and the roadmap. Earlier reviews (experiment 01's, Astra's
24 September roadmap review that found the reversed synapses, and 01b's pre-publication review,
D033) are summarised in `DECISIONS.md` and [`docs/REVIEW_TRAIL.md`](docs/REVIEW_TRAIL.md) but not
archived verbatim. Our bottleneck is compute: everything so far ran on one consumer
GPU. If you have more, you can get to the next answers first, and we would count that as a good
outcome. Useful things anyone can do:

- **Replicate on other hardware.** 03 took 19.75 GPU-hours, 03r 23.95 and 04a 2.91, on one RTX
  5080, and their READMEs give the commands. CUDA results are exact only on the same GPU, so an independent
  replication is a real test.
- **Re-analyse without a GPU.** Every verdict can be checked from committed files (`report.json`,
  `analysis.json`, `records.jsonl`, and E1's `gate.json` and 04a's `evaluation.json` with their event
  tables).
- **Take an open question from [`ROADMAP.md`](ROADMAP.md):**
  - [the mechanism behind 03's history dependence](ROADMAP.md#03-and-03r): 03m took an
    exploratory first look, and its RESULTS.md lists what a confirmatory study would register;
    inputs other than food are open too;
  - [whether N2's wiring helps navigation](ROADMAP.md#e1--04a-navigation-primitive): 04a on shuffled
    graphs, which we have not run;
  - [which optimizer finds better navigators](ROADMAP.md#e2-short-optimizer-screen) (E2);
  - [03a's redesign](ROADMAP.md#03a-redesign-after-03r-before-any-confirmatory-run), which does
    not fit our compute;
  - [the later biology questions](ROADMAP.md#later-biology-questions-unscheduled).
- **Try the variants** listed under "Extend it" in each experiment's README.
- **Check us.** Open an issue with the file, the line and what you expected. Most errors so far were
  caught by review ([`docs/REVIEW_TRAIL.md`](docs/REVIEW_TRAIL.md)). The CPU tests run on every push
  (GitHub Actions), with the connectome downloaded and hash-checked at run time.

If you build on this, please cite it (`CITATION.cff`) and Cook et al. 2019, and tell us, so we can
link your work here.

## Experiment 02, a screening

**Evolution did not find stereo foraging for the real wiring or for its shuffles, so the
pre-registered prediction that N2 would use it more is challenged.** Experiment 02 is a
12-GPU-hour screening, a fraction of a larger design. It crossed two foraging tasks (stereo, and
a more worm-like single-nose one) with the food signal entering through the biological sensory
neurons (AWA, AWC, ASE) or through matched wrong ones. It used 8 N2 runs and 8 shuffled graphs x 2
runs. It was pre-registered, and reviewed by Astra 6 and Fable 5.1 at every stage.

- **Primary:** removing the left-right food difference costs N2's evolved champions +0.027 and
  the shuffles' +0.023, against a threshold of 0.10 for meaningful use. The contrast is +0.004
  [−0.032, +0.044]. The verdict is "challenged: no meaningful N2 use".
- **Exploratory:** under the biological mapping, N2 starts ahead at generation 0 and the
  shuffles catch up. Their best random brains start worse under that mapping, and evolution
  removes the deficit, while N2's own preference barely moves. Random N2 brains are more
  sensitive to food input overall, not more selective for the left-right difference. Nothing
  suggests the advantage is concentrated in the more worm-like task.
- **What it found about the method:**
  - evolved champions forage well without detected stereo use, and there was no selection
    gradient for it;
  - degree-preserving shuffles break mirror symmetry (13-16% of chemical edges, against N2's 64%);
  - shuffles give the food neurons direct routes to the motor neurons, which N2's nearly lack.

Everything is in [`experiments/02-screening/RESULTS.md`](experiments/02-screening/RESULTS.md),
with the pre-registration, every review verbatim, and the decisions D034-D043. Summary and how to
rerun: [02's README](experiments/02-screening/README.md). The follow-up re-analysis of its
champions: [02b](experiments/02b-champion-analysis/README.md).

## Experiment 01b: the main confirmatory result

**On foraging, the real wiring (N2) reaches higher mean best-of-generation fitness than random
graphs and than shuffles of itself, and a higher final score than random graphs; against the
shuffles its final score is not detectably different.** *(Corrected 2026-09-28, D088: this line
said "does better than random graphs, and better than or level with shuffles of itself". "Level
with" is a non-inferiority claim that was never registered and that D033 had already withdrawn.)*
This is the pre-registered comparison with chemical synapses running the
right way round. Each condition has 15 independent evolutionary runs, and the controls are five
degree-preserving shuffles (SH) and five random sparse graphs (RD), three runs each. Intervals come
from a hierarchical bootstrap over graphs and runs.

| contrast | final held-out score (generation 25) | mean best-of-generation fitness (generations 0-24) |
|---|---|---|
| N2 − SH | +0.069 [−0.015, +0.169], no separation | **+0.068 [+0.034, +0.102]** |
| N2 − RD | **+0.094 [+0.029, +0.160]** | **+0.067 [+0.021, +0.105]** |
| SH − RD | +0.025 [−0.079, +0.116], no separation | −0.000 [−0.052, +0.045], no separation |

Six contrasts were tested. With Bonferroni-adjusted intervals, all three that separate still do.

- **N2 reaches higher mean best-of-generation fitness than both kinds of control,** and a higher
  final score than the random graphs. Against the shuffles, its final score is not detectably
  different.
- **This does not show that N2 improves faster.** The pre-registered "speed" measure averages every
  generation, generation 0 included, so it mixes where a run starts with how much it gains. Split
  apart (exploratory), N2's edge over the shuffles is, as a point estimate, all head start. Neither
  component separates on its own.
- **Preserving the real degree sequence did not help by itself:** SH and RD do not separate on
  either measure.
- N2 is one graph. By mean best-of-generation fitness it ranks first of the 11 graph means, and
  second on final score, but no rank test is offered: the graphs are not exchangeable.
- The comparison covers the whole pipeline, including recalibration. Motor calibration equalises
  drive only approximately: random populations reach 84-97% of the target drive depending on the
  graph, with the residual slightly favouring N2 over the shuffles.

Everything, including the exploratory analyses and a side-by-side with experiment 01:
[`experiments/01b-direction-corrected/RESULTS.md`](experiments/01b-direction-corrected/RESULTS.md).
It was pre-registered in
[`experiments/01b-direction-corrected/PREREGISTRATION.md`](experiments/01b-direction-corrected/PREREGISTRATION.md)
and reviewed before publication by Astra 6 and Fable 5.1 (`DECISIONS.md` D033). Summary and how
to rerun: [01b's README](experiments/01b-direction-corrected/README.md).

## Limitations

Stated here, by us, because they bound what the result means.

**Few tasks, one interface.** Evolved N2 against SH and RD has been compared only on single-swarm
foraging with automatic eating (01b, 02); 03 and 03r compare unevolved brains in probes, and 04a
evolved N2 alone, on navigation. Combat, coevolution and pump-gated eating were run only in experiment 01,
with the synapses reversed, and only on N2. The condition where the pharynx should matter is
untested. In N2, every route from a sensor to the pump neurons crosses the two-neuron `RIP↔I1`
gap-junction bridge (`DECISIONS.md` D008).

**A small evolutionary budget for the comparisons.** 01b ran 25 generations and 02 40, with
population 32 and 5 404 parameters per genome. In experiment 01, with the same budget, nothing had
demonstrably converged by generation 25, so a longer run could move the final-score contrasts in
either direction. 04a ran 1 000 generations, but on N2 only.

**Few control graphs, and one real one.** Five shuffles and five random graphs. N2's interval carries
only run-to-run variation, while the controls' also carries graph-to-graph variation. More compute
cannot fix that asymmetry, because there is only one real connectome.

**The interface is our invention, not biology.** Weys get separate left and right food readings, so
foraging can be solved by comparing the two sides. A real worm cannot do that: *C. elegans*
chemotaxis samples concentration over time while moving. The sensor and motor mapping onto named
neurons is chosen by hand.

**Numerics.** 01b ran with 8 integrator substeps. Motor read-out errors above 0.05, against 32
substeps, are rare (0 to 8 of 1440 weys, depending on the inputs used), and their effect on fitness
was not measured.

**A wey is not a worm.** No neuromodulation, no plasticity, no biophysics, no muscles, no body
mechanics. The body is a rigid three-point segment and the motor output is a linear read of named
motor neurons. The only things taken from biology are the wiring graph and a hand-chosen mapping of
game quantities onto individual named neurons.

## Superseded: experiment 01, with the synapses reversed

Experiment 01 ran every brain with **chemical synapses carrying signal backwards**, from the
postsynaptic neuron to the presynaptic one. So it compared the worm's wiring *reversed* against
shuffles of that reversed graph. It reported that N2 **improves measurably more slowly** than both
kinds of control and that final scores do not separate. That conclusion does not hold for the real
wiring:

| contrast | 01, synapses reversed | 01b, synapses correct |
|---|---|---|
| N2 − SH, mean best-of-generation fitness | −0.100 [−0.129, −0.070] | +0.068 [+0.034, +0.102] |
| N2 − RD, mean best-of-generation fitness | −0.112 [−0.150, −0.077] | +0.067 [+0.021, +0.105] |
| N2 − SH, final score | −0.047 [−0.148, +0.039] | +0.069 [−0.015, +0.169] |
| N2 − RD, final score | −0.041 [−0.113, +0.029] | +0.094 [+0.029, +0.160] |

The bug was introduced by Claude Code and found a week later by Astra 6 (OpenAI) reading the
source. It was then confirmed, fixed and rerun as 01b (`DECISIONS.md` D031). Experiment 01 also
found N2 driving the motors more weakly than every control, and removed that confound by
calibrating each graph's motor gain. With the synapses the right way round, N2 is among the
strongest drivers, so that confound was largely a product of the reversal. Calibration is kept.

Experiment 01's other results also describe the reversed graph:
- foraging with pump-gated eating;
- two-swarm coevolution, where swarms win by out-foraging rather than out-fighting their
  opponents;
- the retracted claim that swarms "learned to flank", an artifact of the damage rule (C1).

Frozen record: [`experiments/01-foraging-n2-vs-controls/`](experiments/01-foraging-n2-vs-controls/)
(start at its [README](experiments/01-foraging-n2-vs-controls/README.md)).
Every number, and the correction, is C5 in [`docs/RESULTS.md`](docs/RESULTS.md).

## How to reproduce

```
pip install -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cu130
python scripts/check_env.py              # runs a real CUDA kernel, not just is_available()
python scripts/fetch_connectome.py       # downloads + hashes + caches the connectome
python -m pytest
```

Each experiment's README gives the exact commands to rerun it, the commit it ran at, its compute
cost, and the committed files to compare against. The CPU tests also run on every push
([`.github/workflows/tests.yml`](.github/workflows/tests.yml)); the GPU tests need CUDA and are
run locally.

## Things to run

```
python scripts/watch.py --out runs/look              # one foraging world, rendered to PNG
python scripts/evolve_forage.py --runs 3             # evolve foragers, compare to random weys
python scripts/evolve_forage.py --runs 3 --stage 2   # ... with eating gated on pumping
python scripts/coevolve.py --runs 2                  # two-swarm coevolution
python scripts/experiment.py --k 5 --runs 3 --calibrate   # the N2/SH/RD experiment
python scripts/ablate.py --champions 'runs/m4/champion-*.npz'
python scripts/bench_scaling.py --showcase           # wey-ticks/s and peak VRAM
python scripts/showcase.py --a A.npz --b B.npz --size 2000
python scripts/e1.py pilot --smoke                   # E1's pipeline at tiny sizes, on smoke worlds
python scripts/e04a.py project --smoke               # 04a's pipeline at tiny sizes (then train, evaluate)
python scripts/e3a.py project --smoke                # E3a's pipeline at tiny sizes (then g-e, g0, ...)
python scripts/e3b0.py stage-a --smoke --device cpu  # E3b-0's maze pipeline at tiny sizes (then stage-b, ...)
```

The evolution scripts (`evolve_forage`, `coevolve`, `experiment`, `exp02`) write a run bundle (config, dataset hashes, package versions, git commit, seed
scheme) next to their output.

## What a wey is, and is not

**A wey is a worm-shaped neural network in a game body. It is not a simulation of a worm.**
It has no neuromodulation, no plasticity, no biophysics, no muscles and no body mechanics: the body
is a rigid three-point segment, and the motor output is a linear read-out of named motor neurons.
The only thing borrowed from biology is the *wiring graph* and a hand-chosen mapping of game
quantities onto individual named neurons.

## The claim under test, stated precisely

> Given this specific hand-chosen sensor and motor interface and this game, does the real wiring
> evolve faster, or end up better, than degree-preserving shuffles of it, or than random sparse
> graphs of the same size?

That is a test of **wiring plus interface on one task**. It is not a test of whether biological
wiring is better in general. A positive result would say that this graph suits this interface on
this game; a negative result would say it does not. Neither generalises on its own. Later
experiments ask narrower questions (03: unevolved brains; E1 and 04a: navigation on N2 alone), and
each README states its own.

## Conditions

| Name | Meaning |
|---|---|
| `N2` | the real connectome (named after the standard wild-type strain) |
| `SH` | degree-preserving shuffles of it — several independently generated graphs |
| `RD` | random sparse graphs with the same neuron and edge counts |

## Vocabulary

- **Connectome** — the wiring mask (`N2` / `SH` / `RD`; individual shuffles are `SH3`, `RD1`, …).
- **Strain** — one genome, i.e. one evolved tuning of a connectome.
  ID: `<graph>-run<run>-g<generation>-r<rank>`, e.g. `N2-run04-g0412-r1`.
  Hall-of-fame champions also get a deterministic adjective-animal nickname from a hash of the
  genome, e.g. `N2 brave-heron`.
- **Wey** (plural weys) — one creature running a strain. Weys are clones, identified only by swarm
  and index.
- **Swarm** — all the weys of one strain in one world.
- **Run** — one independent evolutionary run. **This is the unit of statistical analysis.**

## Data, and how to cite it

The connectome is real published data, never synthesised. **It is not redistributed here.**

> Cook SJ, Jarrell TA, Brittin CA, Wang Y, Bloniarz AE, Yakovlev MA, Nguyen KCQ, Tang LT-H,
> Bayer EA, Duerr JS, Bülow HE, Hobert O, Hall DH, Emmons SW (2019).
> **Whole-animal connectomes of both Caenorhabditis elegans sexes.** *Nature* **571**, 63–71.
> doi:[10.1038/s41586-019-1352-7](https://doi.org/10.1038/s41586-019-1352-7)

This project uses the hermaphrodite adjacency matrices (SI 5, corrected July 2020), distributed by
[wormwiring.org](https://wormwiring.org/pages/adjacency.html), which carries the notice
"Emmons Lab Copyright (c) 2020" and **states no licence granting redistribution**. No connectome
file is therefore committed to this repository. `python scripts/fetch_connectome.py` downloads it
from the original source and verifies its sha256 against the value recorded in `PROVENANCE.md`; the
loader fails with a clear message, and no fallback or synthetic substitute, if it is missing.

`PROVENANCE.md` records source URLs, hashes, the exact quantity used (`em_sections`, not synapse
counts) and every transformation applied.

If you use this repository, please cite both it (see `CITATION.cff`) and Cook et al. 2019.
The data terms are also stated in `NOTICE`; `LICENSE` (MIT) covers the code and documentation only.

## Status

[`ROADMAP.md`](ROADMAP.md) says where the project stands and what comes next. `DECISIONS.md`
records every non-trivial decision, and `docs/REPRODUCIBILITY.md` says exactly what is and is not
reproducible. `PLAN.md` is the original build plan (milestones 0-11 done, 12 deferred), kept for its measurements.

## How this was made

This project was designed and built almost entirely by AI models, directed by a human.

- Juan H. González Estefan: the original ideas (connectome-tuned agents, swarm battles, parallel
  worlds, side bites, publishing the null result as a numbered series, and the hypotheses behind
  experiment 02), direction, and the final say. Since 2026-09-27 the rest of the roadmap is
  delegated; since 2026-09-29, work that Claude Code and both reviewers agree on goes to main without
  waiting for his approval, and he is told afterwards. He publishes and answers for this repository,
  but has not independently verified the code line by line.
- Claude Fable 5.1 (Anthropic), in conversation: turned those ideas into the experimental design and
  specification, and reviewed the results. Later, consulted read-only, it reviewed experiment 01b
  before publication (D033), and since then every design, pre-registration and write-up: 02, 03,
  03r, T0, T1, E1, 04a, 03m, E2, E2d, E4s, E3a, E3b-0 and E3b-1.
- Astra 6 (a GPT model from OpenAI): adversarial review of the specification, which produced the
  statistical design, the resource accounting rules and the numerical stability requirements.
  Reviewing the roadmap, it found that the chemical synapses of experiment 01 ran backwards (D031),
  and it reviewed experiment 01b before publication (D033), and since then every design,
  pre-registration and write-up alongside Fable 5.1.
- Claude Code running Claude Opus 5 and, from 2026-09-24, Claude Opus 5.5 (Anthropic): every line
  of code, every measurement, and all implementation decisions recorded in DECISIONS.md. Opus 5
  built experiment 01 and found the motor-gain confound on its own. Opus 5.5 confirmed and fixed
  the reversed synapses, ran experiment 01b, and acted on its review. It also designed,
  pre-registered, ran and wrote up experiment 02, which the owner delegated to it end to end,
  with the two reviewers standing in for approval at each stage; then, with the roadmap delegated,
  03, 03r, the engineering work (T0, T1), E1, 04a, 03m, E2, E2d, E4s, E3a, E3b-0 and E3b-1's design and
  pre-registration.
- Claude Sonnet 5.5 (Anthropic), through the Claude CLI: a literature report for E4s's first designs.
  Most of its sources were search snippets and nobody checked its claims. It was wrongly called "a
  deep research" (corrected, D143).
- Claude Opus (Anthropic) and Astra 6 (OpenAI), run by the owner from one prompt: the literature
  review that replaced it (`docs/reviews/20261001-literature-review/`).
- An outside review by a separate Claude Opus 5.5 instance, shared by the owner on 2026-09-28
  ([archived](docs/reviews/20260928-outside-review/review.md)), suggested the automatic test runs
  and the checks behind 03m.

Errors and who caught them: the "learned to flank" claim was made by Claude Code and caught by
Claude Fable 5.1 in review (D026). The "N2 is deeper" explanation was made by Claude Fable 5.1,
built on a path length mis-measured by Claude Code, and caught by Claude Code when it re-measured
instead of writing the claim as dictated (C4). No single participant, human or AI, would have caught
both. The largest error, chemical synapses running backwards in every run of experiment 01, was
made by Claude Code and caught by Astra 6 (D031). Claude Code's first write-up of the corrected
rerun then overclaimed, and Astra 6 and Fable 5.1 each caught that independently (D033). More
recently, the reviewers caught a smoke test that trained on 04a's real training worlds and a plan
that would have published genomes carrying connectome weights (D104), and an overclaim that 04a's
champions "steer" (D111). In E2, they caught failure paths in four rounds of pre-registration
review, including a false claim that every test had been seen failing first (D119-D123), and a
first reading of its floor result that called the optimizers' gains "little" (D125). One error was
caught by a machine: the first automatic test run on Linux
showed that 03's graph files rebuild byte for byte only on Windows (D106). The full list, with
commits: [`docs/REVIEW_TRAIL.md`](docs/REVIEW_TRAIL.md).

The design and implementation came from Anthropic models and the specification review from an OpenAI
model. Reviewers from different model families are less likely to share the same blind spots.

Because the work is AI-generated and has had limited human verification, treat every result as
provisional until someone replicates it.
