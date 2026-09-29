# E4s literature report (Claude Sonnet 5.5, 2026-09-30)

*Archived verbatim. Commissioned by the owner's instruction (2026-09-30): a deep research by Claude Sonnet 5.5 through the Claude CLI (model `claude-sonnet-5-5`, CLI 2.1.285, effort xhigh, web search and fetch allowed, no file edits), before E4s's design. The brief is `brief.md` beside this file. Its claims are marked [E] established, [P] plausible, [G] guess, and † where the source was read only from an extract. Numbers it derived from this repository were checked against the code before use (D139).*

---

# E4s literature report: a fly-style stereo module for the connectome brain

**How to read this**
- **[E]** means established in the cited work. **[P]** means a plausible extrapolation. **[G]** means our guess or derivation, untested.
- **†** means I saw only a search snippet or an automated page extract, not the full text. Nature, Cell, Springer and PubMed pages mostly refused to load, so check numbers marked † before relying on them.
- I could not run code in this session. Every number labelled "our arithmetic" is analytic and needs a short numeric check on the world code.
- Several 2026 preprints (arXiv 2607.*, bioRxiv 2026.05) are unreviewed and each rests on a single study. I flag them where used.

---

## Executive summary

1. **The ring recipe is well established [E].** The fly compass is local recurrent excitation (E-PG, P-EG) plus global inhibition (Δ7). It is rotated by P-EN "shifter" cells that carry angular velocity. Rate-model ports with explicit equations exist. Goulard et al. use 8 columns ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8491911/)†). Stone/Sun use 8 columns ([Sun 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7365663/)†). A ring can be as small as 4 units but then needs precise tuning ([Noorman 2024](https://www.janelia.org/news/small-brains-can-accomplish-big-things-according-to-new-theoretical-research)).
2. **Steering readout [E].** Two lateralised populations read the same bump with opposite phase offsets. Their left minus right output drives turning ([PFL3, Westeinde 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10881397/)†). The simplest port is a hemifield readout with no goal memory.
3. **Gap.** I found no published model where a bilateral *chemical* difference anchors a ring. The nearest analogues are:
   - a wind compass built from a left-right antennal comparison ([Okubo 2020](https://www.cell.com/neuron/fulltext/S0896-6273(20)30476-1)†);
   - odour-gradient control of saccade direction with compass memory between saccades ([PNAS 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13015376/)†);
   - silkmoth-style bistable "flip-flop" steering with direct olfactory input ([Adden 2022](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1.full)†).
4. **The real worm does not compare its two noses.** Its amphids are about 8 µm apart†. It steers by temporal comparison during head sweeps ([Izquierdo & Lockery 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3422662/)†). Stereo here is a design choice, as `configs/interface.yaml` already says. It is fly-inspired, not worm-faithful.
5. **Prior work on grafting is thin.** I found no study that inserts a hand-designed module into a connectome-constrained network and tracks its fate under evolution. Section 5 lists the nearest work and the measurement tools.
6. **The main design finding is about signal scale [G].** The left-right difference is tiny, about 0.004–0.017 in current units, against a common mode of about 0.02–0.25. Scripted stereo needs a gain of roughly 250 to reach 97% of ceiling. The evolved champions match a gain of about 4. The module's real job is roughly 60× differential gain plus common-mode rejection, and a saturating or bistable stage can supply that. Section 6 has the derivation.
7. **Recommendation.** Build a ladder and let the "remove neurons one by one" study run on it:
   - E4s-0: a 2-cell flip-flop core.
   - E4s-1: an 8-column ring.
   - E4s-2: the ring plus shifters and turn copy.
   - Task N alone cannot tell the ring from the 2-cell core, because scripted stereo has no memory and scores 8.7. The existing `food_probe: hold` mode is a ready-made memory test.

---

## 1. The fly ring attractor as a portable model

**Motifs, counts, signs**

| Type | Count | Transmitter / sign | Role | Source |
|---|---|---|---|---|
| E-PG | ≈46–50, one PB glomerulus and one EB wedge each | ACh, excitatory | compass bump; local recurrence | [Turner-Evans 2020](https://www.biorxiv.org/content/10.1101/847152v2)†; counts [Hulse 2026 preprint](https://www.biorxiv.org/content/10.64898/2026.05.18.725766v1.full)† |
| P-EN (PEN_a 20, PEN_b 22) | 42 | ACh, excitatory | E-PG→P-EN→E-PG loop shifted one wedge; conjunctive heading × angular velocity | same |
| P-EG | 18 | excitatory | E-PG↔P-EG recurrent loop | same |
| Δ7 | ≈42 | glutamate; inhibitory via GluCl | long-range inhibition; bump about 180° from E-PG bump | same |
| Ring (R) neurons | many | GABA | sensory anchoring onto E-PG | [Fisher 2019](https://wilson.hms.harvard.edu/publications/sensorimotor-experience-remaps-visual-input-heading-direction-network)† |

The EB has 16 wedges (22.5°) and the PB 9 glomeruli per side ([Turner-Evans 2020](https://www.biorxiv.org/content/10.1101/847152v2)†). A connectome analysis suggests that E-PG self-recurrence, not only P-EG, carries the local excitation ([Chang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10353971/)†). A small P-EG loop is therefore optional in a port.

**Anchoring and rotation**
- **Global inhibition with local excitation is the core [E].** Optogenetically overwriting the bump shows it is maintained by the circuit ([Kim 2017](https://pubmed.ncbi.nlm.nih.gov/28473639/)).
- **Rotation [E].** P-EN cells provide clockwise and anticlockwise shifts, driven by angular velocity, so the bump moves in the dark ([Green 2017](https://pubmed.ncbi.nlm.nih.gov/28538731/), [Turner-Evans 2017](https://elifesciences.org/articles/23496), [Seelig & Jayaraman 2015](https://www.nature.com/articles/nature14446)).
- **Anchoring [E].** Sensory cues reach E-PG through inhibitory ring neurons whose mapping is plastic ([Fisher 2019](https://wilson.hms.harvard.edu/publications/sensorimotor-experience-remaps-visual-input-heading-direction-network)†). Reliability-weighted cue integration fits a "circular Kalman filter" view, with bump amplitude encoding certainty ([Bayesian ring-attractor preprint](https://www.biorxiv.org/content/10.1101/2021.12.17.473253v1.full)†).
- **Older double-ring theory.** Two mirror-symmetric rings with velocity-modulated asymmetry produce a travelling bump ([Xie, Hahnloser & Seung 2002](https://ics.uci.edu/~xhx/publications/PhysRevE_66_041902.pdf)).

**Models with explicit, reusable parameters**

| Model | Type | Size | Explicit? |
|---|---|---|---|
| [Goulard 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8491911/)† | rate | 8 E-PG + 8 P-EG + 16 P-EN | Yes. Extracted: `EPG_i = VU_i + 1.0·PEG + 2.5·PEN − 0.2·ΣEPG`; `PEN = 0.75·(EPG + Nod)`. Verify against the paper's Eq. 2. |
| [Stone 2017](https://www.cell.com/current-biology/fulltext/S0960-9822(17)31090-4) via [Sun 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7365663/)† | rate | 8 TB1, 16 CPU4, 16 CPU1 | Yes: `W = cos(Δθ) − ½`; coupling c; accumulation r = 0.0025; k_motor = 0.125 |
| [Noorman 2024](https://www.biorxiv.org/content/10.1101/2022.05.23.493052v1.full)†, code [Zenodo](https://zenodo.org/records/12789923) | threshold-linear | N = 4–20 plus side rings | Cosine weights; N−3 optimal excitation values |
| [Connectome-derived exact ring](https://www.biorxiv.org/content/10.1101/2024.11.01.621596v2.full)† | threshold-linear | 8 compartments | Weight matrix from synapse counts, rescaled by cell-type factors |
| [Kakaria & de Bivort 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5306390/)† | spiking LIF | 60 neurons | Yes, but spiking |
| [Pisokas 2020](https://www.biorxiv.org/content/10.1101/854521v4.full)† | spiking | 18 columns, fly and locust | Matrices, spiking |

**Robustness: the sources disagree**
- **Tolerant.** The Kakaria model tolerated 20% Gaussian noise on all parameters. Most synapse signs could even be flipped, except the Δ7 inhibition. About 1.5% of random configurations at 100% noise still gave a bump. The non-spiking version works, but worse†.
- **Fragile.** In connectome-based spiking models, 2% weight heterogeneity broke most trials, and better dynamics traded off against persistence ([Chang 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10353971/)†).
- **Size versus precision.** Smaller rings need tighter tuning, and tolerance scales with N ([Noorman](https://www.biorxiv.org/content/10.1101/2022.05.23.493052v1.full)†).
- **Not all-or-nothing.** Perturbed continuous attractors leave a slow invariant manifold, so function degrades gracefully ([Back to the Continuous Attractor](https://arxiv.org/abs/2408.00109)†).
- **Heterogeneity fix.** Cloning units restores tolerance to weight noise as large as the weights themselves ([Hulse 2026 preprint](https://www.biorxiv.org/content/10.64898/2026.05.18.725766v1.full)†, single preprint).

Implication for evolution [P]: an exact continuous attractor will not survive mutation, but a leaky ring with a few preferred positions will. That is enough for steering.

**Optimizers find rings unaided.** RNNs trained on head-direction integration develop compass and shifter units ([Cueva 2020](https://arxiv.org/abs/1912.10189)†). A learning rule can build fly-like connectivity ([Vafidis 2022](https://elifesciences.org/articles/69841)†).

---

## 2. Direction → steering command

- **PFL3 / PFL2 / FC2 [E†].**
  - EPG (heading) and FC2 (goal) both feed PFL3. Left and right PFL3 read shifted copies of the heading code; offsets are about ±67.5° in [Westeinde 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10881397/)† and 50–70° in [Mussells Pires 2024](https://www.biorxiv.org/content/10.1101/2022.11.10.516026v1.full)†.
  - Right minus left PFL3 activity tracks rotational velocity.
  - PFL2 peaks when the fly is oriented away from the goal and acts as a gain.
  - The model form is `f(cos(H−φ) + d·cos(G−θ))`.
- **Descending stage [E†].** PFL3 drives DNa02 through excitation of the ipsilateral side and inhibition of the contralateral side (a "see-saw"), and right minus left DNa02 is close to linear in turn rate. DNa02 *also* receives direct multimodal sensory input, including olfactory ([Rayshubskiy 2025](https://elifesciences.org/articles/102230)†). A parallel reflex path is therefore biological.
- **Bee model (Stone 2017) [E†].** CPU1 sums are offset by one column left or right of the memory, and the turn is `k·(ΣCPU1_left − ΣCPU1_right)`. It needs a TB1 sinusoid and a CPU4 accumulator ([Sun 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7365663/)†).
- **Landmark steering (Goulard 2021) [E†].** The bump is *egocentric*: visual azimuth maps retinotopically onto EPG, and `Δsteer = ΣPFL3_right − ΣPFL3_left`, clipped to ±2.5°/step. This is the closest port to our situation ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC8491911/)).
- **Moth model (Adden 2022) [E†].** A flip-flop pair (excitatory onto the contralateral motor) plus bilateral inhibitory PBN cells. Its inputs are either direct olfactory signals or CX output, and it has a rate version ([bioRxiv](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1.full)).

**Simplest to port, in order**
1. The flip-flop pair (4 neurons, no memory).
2. A PFL3-style hemifield readout of a ring. It equals `sin(bump angle)` and needs no memory.
3. Stone's CPU1/CPU4 system, which is unnecessary here.

**Not portable as-is.** The fly's FC2 + allocentric heading architecture needs a world-fixed compass. Task N has only a boundary wall, so the wey has no allocentric reference. Use an egocentric bearing ring, as Goulard does.

---

## 3. Odour direction in such circuits

**Bilateral comparison is real**
- Flies need both antennae to track gradients in flight ([Duistermars 2009](https://www.sciencedirect.com/science/article/pii/S0960982209012950)).
- Asymmetric transmitter release lateralises odour within the first synapse ([Gaudry 2013](https://www.nature.com/articles/nature11747)).
- Larvae with one functional olfactory neuron can still chemotax, and bilateral input adds signal-to-noise ([Louis 2008](https://www.nature.com/articles/nn2031)).
- Rats and humans use inter-nostril timing and intensity ([Rajan 2006](https://science.sciencemag.org/content/311/5761/666.abstract), [Porter 2007](https://www.nature.com/articles/nn1819)).
- Stereo beats temporal sensing when relative concentration changes are large ([Tootoonian & Schaefer](https://arxiv.org/abs/2607.20307), 2026 preprint).
- A larval-taxis model uses temporal, single-sensor comparison ([Wystrach 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC5117870/)†).

**Ratio-type coding has precedent.** Wind direction is an "intensity-invariant representation computed by comparing left-right mechanosensory signals" and rotates the compass ([Okubo 2020](https://www.cell.com/neuron/fulltext/S0896-6273(20)30476-1)†, from the abstract snippet).

**Memory across the animal's own turns**
- In flight, saccade direction is influenced by the static odour gradient across the antennae. E-PG compass neurons provide "a stable metric of heading … for turns separated by several seconds". Olfactory and mechanosensory feedback alone were insufficient to stabilise the plume ([PNAS 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13015376/)†).
- The wind/odour fan-shaped-body circuit shows *no* sustained directional memory ([Matheson 2022](https://www.biorxiv.org/content/10.1101/2021.04.21.440842v3.full)†).
- Plume-tracking RNNs learn head direction, but without demonstrated ring structure ([Singh 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10601839/)†).
- **Rotating a bump by a copy of one's own turn is established for heading** (P-EN, section 1). Applying it to an *odour-bearing* bump is our extrapolation [P/G].

---

## 4. The worm side

- **Klinotaxis and pirouettes [E].**
  - ASE and AIZ are essential for both the weathervane and pirouette mechanisms in salt chemotaxis ([Iino & Yoshida 2009](https://www.jneurosci.org/content/29/17/5370)†).
  - Evolved minimal circuits need only an ON/OFF sensory pair plus two neck motor neurons with antiphasic oscillatory input, and turning bias is set by changes sensed during head sweeps ([Izquierdo & Lockery 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3422662/)†).
  - ASEL and ASER are ON and OFF cells that compute a temporal derivative ([Suzuki 2008](https://www.nature.com/articles/nature06927)†, [Thiele 2009](https://www.jneurosci.org/content/29/38/11904)).
  - An ensemble of connectome-derived klinotaxis models (ASE, AIY, AIZ, SMB) makes AIZ crucial ([Izquierdo & Beer 2013](https://pmc.ncbi.nlm.nih.gov/articles/PMC3567170/)†).
- **Bilateral versus temporal [E†].** Amphids are about 8 µm apart, so temporal sampling is favoured (Ward 1973 and Dusenbery 1980, as cited in [Izquierdo & Lockery 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3422662/)†). Turning rate scales with sin(bearing) ([Martinez 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4132367/)†). Section 6 shows why this matters for our task.
- **Graft-point anatomy**
  - Single-pair AIY asymmetric excitation turns the animal toward the side of its head bend; symmetric excitation only changes reversals ([Kocabas 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC4229948/)†).
  - AWC→AIY→AIZ→SMB/RME is the sequence ([same](https://pmc.ncbi.nlm.nih.gov/articles/PMC4229948/)†; [Luo 2014](https://www.cell.com/neuron/fulltext/S0896-6273(14)00396-1)).
  - RIA's dorsal and ventral compartments encode head bending, driven by SMDD and SMDV ([Hendricks 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3393794/)†).
  - SMDD ablation causes ventral circling, and SMDD is a proprioceptive sensory-motor cell ([Yeon 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6010301/)†).
- **Suggested graft points**
  - *Outputs:* SMD and RMD dorsal/ventral sets. These are already the interface's turn readout (`interface.yaml:59-61`). Later, add AIY, AIZ and RIA as worm-native routes.
  - *Turn copy:* read SMD/RMD directly. RIA already receives SMD input, so this is worm-native.
  - *Caveat:* real head bending and the interface's "dorsal = left" are different things. The interface comment already warns that its mappings are "modelling choices". Direct SMD/RMD output avoids a head-bend-phase dependence.

---

## 5. Grafting and seeding prior work

I found no study that tracked the fate of a hand-designed module inside a connectome-constrained network under evolution. I also found nothing matching "neural prosthesis" for this purpose. What exists is indirect:

- **KBANN.** A symbolic domain theory becomes network structure and initial weights, then is refined by backprop. Rules can be extracted afterwards ([Towell & Shavlik 1994](https://ftp.cs.wisc.edu/machine-learning/shavlik-group/towell.aij94.pdf)†).
- **Evolution on a fixed anatomical scaffold.** Izquierdo & Beer's ensemble is the closest methodological precedent: evolve unknown parameters on a connectome-derived circuit, then ablate to find what matters ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3567170/)†).
- **Modularity.** Connection cost yields modular, more evolvable networks ([Clune 2013](https://arxiv.org/abs/1207.2743)). Hardwired versus duplicated modules were compared in [Nolfi's work](https://link.springer.com/chapter/10.1007/978-3-642-18272-3_5)†.
- **Dependence.** Knockout is the operational test of whether an evolved feature is needed ([Lenski 2003](https://www.nature.com/articles/nature01568)).
- **Erosion analogue.** Engineered gene circuits lose function under evolution when they impose a burden, because mutants that reduce expression win ([Sleight & Sauro line of work](https://pmc.ncbi.nlm.nih.gov/articles/PMC12487889/)†). This is an analogy, not a neural result.
- **Seeding risk.** Seeds taking over a population is common EC lore, but I found only patent text for it, so I do not cite it.

**Consequence.** Treat "keep, improve or dismantle" as an empirical outcome to be measured, not predicted. Two limits apply on Task N:
- The ceiling is 8.85 (oracle) against 8.78 (S-const), so "improve" is unobservable on it.
- Selection keeps a module's *function* only where removing it costs fitness. Its *structure* can drift neutrally.

---

## 6. Practical recommendations for our rate network

**6.1 Where the gain must come from (our arithmetic, [G])**

Inputs and motor mapping, from the repo:
- The scent is `A·exp(−d²/2σ²)` with σ = 6 (`experiments/E1-navigation/RESULTS.md:51-59`) and A = 1. It is scaled by 0.35 (`config.py:113`), so the peak current is 0.35.
- The sensors sit 0.6 ahead and ±0.5 lateral.
- The turn readout is `clamp(mean(tanh dorsal) − mean(tanh ventral))`. The factor is `0.5·turn_gain = 1` (`world.py:742-752`, `config.py:98`).
- Heading changes by `0.30·turn` rad per tick (`world.py:800`).

For an untruncated Gaussian, `ln(L/R) = y/σ²` exactly, where y is the source's lateral offset from the heading axis. So `L−R = 2·c̄·tanh(y/72)`, with c̄ ≈ 0.35·exp(−d²/72). The truncation at 18 cells and the bilinear sampling make this approximate.

| Case | c̄ | L−R |
|---|---|---|
| d=5, bearing 30° | 0.247 | 0.017 |
| d=10, 30° | 0.087 | 0.012 |
| d=14, 30° | 0.023 | 0.0045 |
| d=10, 10° | 0.087 | 0.0042 |

E1's scripted `S-const` acts on these injected currents (`exp02/scripted.py:27-28,43`; `StereoKinesis:186`):

| k | 1 | 2 | 4 | 32 | 256 | 8192 |
|---|---|---|---|---|---|---|
| best tuned mean (E1 tuning worlds) | 0.88 | 1.13 | 2.38 | 5.63 (4.23 at turn 0) | 8.51 | 8.78 |

Source: `experiments/E1-navigation/RESULTS.md:98-102`.

So a k of about 250 turns a 0.004 difference into a full command. The E2d champions perform like k = 4 and use no stereo at all. The missing ingredient looks like about two orders of magnitude of differential gain, not a missing topology. A random mutation that adds gain 2 out of 250 gives almost no fitness gradient. That plausibly explains the plateau, and it is a testable hypothesis, not a finding. A cheap test is to measure the champions' turn response to a synthetic L−R at fixed common mode, which the existing `exp02/probes.py` machinery can do.

**6.2 Ring size [P]**
- **8 columns.** This matches the fly's eight-fold symmetry ([Pisokas](https://www.biorxiv.org/content/10.1101/854521v4.full)†) and every rate port above (Goulard, Stone/Sun, Biswas). Noorman shows 6–8 units can work with tuning.
- **Our input is a 1-D signed lateral offset**, so a 4-unit ring, a 2-cell flip-flop, or a linear strip may suffice. Make these the minimisation arms, not just the removal study.
- **The two frontal noses give no rear-hemisphere information.** A source directly behind gives L ≈ R and puts the bump at "ahead". The sign of y still gives the right turn direction for anything off-axis (for example, bearing 150° has y > 0, so a left turn is correct). Only near ±180° is it ambiguous.
  - The wrap-around half of the ring is occupied only by turn-copy memory.
  - The temporal channel the champions already have (turn hard when scent falls, as in M-avg) resolves this. That favours a seeded-on-champion arm.

**6.3 Mapping L and R onto the ring [G]**
- **Two input variants:**
  - (a) *Bilateral noses.* NL gets `+g·L`, NR gets `+g·R`, and the ring does the comparison. With g·0.35 ≈ 1, g ≈ 2.5–3, tanh stays in its linear range. The 17× common-mode range (0.02–0.35) is only partly handled. Calibrate g on logged S-const rollouts so the 95th-percentile common mode maps to about 1.
  - (b) *Differential injection.* A neuron gets `g·(L − β·R)`. Signed gains are accepted by `interface_from_spec` (`interface.py:116`) and sum before saturation (`world.py:734-739`). β = 0.7 is Gaudry-like (ipsilateral 1.4× contralateral†). β = 1 is pure difference and removes the common mode entirely; g up to about 100–200 stays under the ±5 clamp (0.017 × 200 = 3.4). But this does the comparison in the interface, so the scientific claim changes. Label it as a control arm.
- **Cosine mapping onto the ring:** `w(NL→E_i) = w_in·cos(θ_i − φ)`, `w(NR→E_i) = w_in·cos(θ_i + φ)`.
  - The physical sensor azimuth is `atan(0.5/0.6) ≈ 40°`, which is the natural retinotopic φ.
  - A larger *virtual* φ (75–85°) stretches the tiny ratio range (δ ≈ 0.02–0.14) over the ring. With `tanψ = δ·tanφ`, φ = 80° gives ψ ≈ 6°–39° over that range; φ = 40° gives only about 1°–7°.
  - φ is effectively a gain knob, and the synapse weights are free to evolve it.
- A supercritical ring normalises amplitude, so the bump angle depends on the L:R ratio, not on absolute size. That is our derivation, in line with the intensity-invariance of [Okubo 2020](https://www.cell.com/neuron/fulltext/S0896-6273(20)30476-1)†.

**6.4 Readout [P]**
- **Hemifield sum.** `T_L = Σ w_r·sinθ_i·r_i`, `T_R = −T_L`. This equals a PFL3 pair with ±δ offsets, since `cos(ψ−δ) − cos(ψ+δ) = 2 sinψ sinδ`.
- **Push-pull onto the motors.** T_L drives dorsal (left-turn) neurons and inhibits ventral ones; T_R does the reverse. This cancels the bipolar tanh baseline. A 16-synapse fan-out at |w| ≈ 1.0–1.5 already saturates the turn command (2·w·(T_L−T_R)).
- **Parallel direct path.** Add `NL/NR → T_L/T_R` at ±1.0, following [Rayshubskiy 2025](https://elifesciences.org/articles/102230)† and [Adden 2022](https://www.biorxiv.org/content/10.1101/2020.08.25.266247v1.full)†.
- **Saturation trap.** If the worm network already saturates SMD/RMD (|v| ≫ 1), extra module drive has no effect. Test on both random and champion backgrounds.

**6.5 Initial τ, bias and weights [G]**
- **Mapping from published sigmoid-rate models.** With σ the logistic function, `tanh(v) = 2σ(2v) − 1` gives `J = 4W` and `h = 2b − 2ΣW` (equivalently `b = h/2 + ΣW`, derived by hand). Any published sigmoid model with |J| ≤ 12 is expressible within w_max = 3. Threshold-linear ports (Noorman, Xie, Biswas) must be re-fit with saturating tanh.
- **Time constants are in ticks,** not fly milliseconds:

| Group | τ (ticks) | Reason |
|---|---|---|
| Nose | 0.5–1 | Fast relay |
| Δ7-like | 1 | Faster than E, for stability |
| Ring | 2–4 | Settle in ≤ 5 ticks |
| Shifter | 1–2 | |
| Readout | 1 | Loop delay ≈ 1 tick |

- **Persistence should be modest.** The scent source relocates, so a stale bump is harmful. A slightly supercritical ring (cos-mode gain about 1.1–1.2) gives roughly one leg of memory (about 10–20 ticks). Let evolution set the persistence.
- **Biases** in [−2, 2]: ring about −0.3, shifters about −0.5 to −0.6, others 0. Every initial weight magnitude should be ≤ 1.5, leaving at least 2× headroom to the ±3 bound.
- **Timing check.** The brain input is held for all 32 substeps of a tick (`brain.py:376-410`), so the module cannot respond faster than one tick. Even τ = 0.5 tick is 16 substeps, which is numerically benign in the semi-implicit scheme (`brain.py:13`).

**6.6 What evolution may change [G]**
- **Tier 1 (always free):** module→worm output weights, T biases and τ.
- **Tier 2:** input and readout weights, ring biases and τ.
- **Tier 3 (structure):** ring recurrence and shifter weights. Run this as a factor:
  - "frozen structure" (tiers 1–2 free);
  - "free structure" (all free);
  - "open mask", with every intra-module edge allowed.
- **Mutation scale.** Give the module 0.25× the default (`w_sigma 0.08 → 0.02`, `bias_sigma 0.05 → 0.0125`, `tau_sigma 0.15 → 0.04`). Justification: E2d C0 found the default kills 78% of children and halving helped every paired run (a lead, not a finding, per the E2d corrections). A supercritical ring sits near a bifurcation.
- **Optional heterogeneity guard.** Use two "clone" units per column ([Hulse 2026 preprint](https://www.biorxiv.org/content/10.64898/2026.05.18.725766v1.full)†).

**6.7 How the module could fail here**
1. **Dynamic range.** Common-mode saturation kills the differential (section 6.1).
2. **Bipolar tanh outputs.** Silent units emit negative values that offset downstream sums. Use push-pull pairs and bias correction.
3. **Uniform-mode saturation.** All ring units can go "on" if inhibition is weak.
4. **Stale bump** after the target relocates, if persistence is too long.
5. **Turn-copy gain.** A miscalibrated shifter rotation speed makes the bump overshoot. Sensory anchoring corrects it only if the anchor is strong enough.
6. **Background interference.** The worm net's own circling, or its saturated SMD/RMD, can override the module.
7. **Front/back ambiguity** (section 6.2).
8. **Neutral drift** erodes ring structure without harming function, so "ring-ness" is a weaker signal than lesion cost.
9. **Selection noise.** E2d C0 showed 8 worlds rank close siblings poorly; this matters more at the smaller mutation scales suggested here.

---

## 7. Measurement

**Behavioural**
- **Keep the existing probes.** The `mean` and `swapped` probes, as in Part B. Also keep the E1 `mirrored` and `constant` probes.
- **Attribute stereo use to the module.** The probes edit `food_left/right` for *all* consumers (`world.py:693-696`), so worm-side and module-side stereo use are confounded. Give the module its own signal names so the probes can act on the module alone.
- **Effective gain.** Measure the stereo-gain slope: turn response per unit L−R at fixed common mode, compared against E1's k table.
- **Memory test.** `food_probe: hold` refreshes the reading only every `food_probe_hold` ticks (`world.py:766-769`; `config.py:148`). A reflex steers on a stale bearing, while a ring with turn copy should not. This is the natural discriminator between E4s-0 and E4s-2.
- **Standing measure.** Log all of this along training, not only on champions, as Fable's E2d review advised (`docs/reviews/20260929-233515-E2d-results/fable.answer.md:72`).

**Causal**
- **Lesion.** Silence the module (`Brain.silence`; note the grounded-cell gap-junction caveat at `brain.py:327-346`). Compare the score against the intact brain.
- **Transplant.** Move an evolved module onto a fresh background, and a fresh seeded module onto an evolved background.
- **Reset-to-seed.** Restore the module's parameters to their seed values inside an evolved brain.
- **Shapley attribution.** Use multiperturbation Shapley analysis across module neuron groups ([Keinan 2006](https://direct.mit.edu/artl/article/12/3/333/2530/Axiomatic-Scalable-Neurocontroller-Analysis-via)†). At about 30 neurons, sampling is enough.

**Erosion versus retention**
- **Neutral-drift control.** Evolve an identical module with its motor outputs masked off. Its parameter drift is the mutation-only baseline. Compare with the working module's drift.
- **Structure-retention indices.** Cosine-ring fit of the recurrent weights, sign flips, and distance from seed.
- **Ring signatures.** Bump present and localised, bump angle against a decoded bearing, decay time after input off, and ring topology of population states ([Chaudhuri 2019](https://www.nature.com/articles/s41593-019-0460-x)†).

**Controls**
- A same-size random-weight module.
- An inert module (outputs cut).
- The 2-cell core.
- Pairing, sign-flip tests and world counts as in E2d.

---

## Proposed design

Tags: **[E]** established structure, **[P]** plausible, **[G]** our guess. All numbers are starting values, tested by the acceptance checks below.

**Ladder**
- **E4s-0:** NL, NR, T_L, T_R with mutual inhibition and the direct path. About 4 neurons. [P]
- **E4s-1:** add the ring and Δ7-like pool (8 + 2), no shifters. [P]
- **E4s-2 (main):** add shifters and turn copy. 30 neurons, 302 → 332.

**E4s-2 groups**

| Group | n | Connections (sign, initial weight) | τ / bias | Tag |
|---|---|---|---|---|
| Noses NL, NR | 2 | In: `food_left/right`, new sensor entries, gain about 2.5 (variant a) or `g(L−βR)` (variant b). Out: → ring `w_in·cos(θ_i ∓ φ)`, w_in 1.5, φ 75°; → T_L/T_R direct ±1.0 | 0.7 / 0 | [G] |
| Ring E0–E7 (θ = 0, 45°, …; + = left) | 8 | Self +0.6; ±45° neighbours +0.35; ±90° and beyond 0. Readout to T (below). | 3 / −0.3 | [P] |
| Δ7-like D1, D2 | 2 | E→D +0.35 each; D→every E −0.45 | 1 / 0 | [P] |
| Shifters Pcw_i, Pccw_i | 16 | E_i→P +0.6; Pcw→E_{i−1} and Pccw→E_{i+1} +0.6; efference: T_L→Pcw +0.6, T_R→Pccw +0.6 (a left turn moves the source bearing clockwise, toward −θ) | 1.5 / −0.6 | [P]/[G] |
| Readout T_L, T_R | 2 | E_i→T_L `+w_r·sinθ_i`, E_i→T_R `−w_r·sinθ_i` (w_r 1.0); direct ±1.0 from noses; mutual −0.5 | 1 / 0 | [P] |
| Motor fan-out | 16 syn | T_L→SMDDL/R, RMDDL/R +1.2; T_L→SMDVL/R, RMDVL/R −1.2; T_R the reverse | — | [P] |

**Consistency checks on those values**
- Cos-mode gain of the E–E weights is `0.6 + 2·0.35·cos45° = 1.095`. That is slightly supercritical, before tanh slope < 1 reduces it, so it is marginal. Raise self or neighbour weight a little if the acceptance test shows no bump.
- Uniform mode is about `1.3 − 2.5` after Δ7 inhibition, which is strongly damped.
- An alternative is cosine weights with negative far lobes and no D. Evolution can pick the split.

**Graft points**
- *In:* two new sensor entries in `interface.yaml`, on the new noses. The existing AWA/AWC/ASE entries stay unchanged.
- *Out:* the eight turn-set neurons already named in `interface.yaml:59-61`. Later add AIY, AIZ and RIA.
- *Worm→module:* none at first. A later variant reads SMD/RMD for the turn copy.
- *Mask policy:* designed-sparse versus open, as a factor (section 6.6).

**Acceptance tests before any evolution** (the module-alone gate, in the spirit of E1's positive control):
1. With the worm net inert, a module-only wey scores far above M-avg's 2.2 on Task N. The scripted family reaches 5.6 at k = 32 with no evolution, so a target of about 5 or more is reasonable [G].
2. A ring pulse at a column forms a bump that holds for at least 10 ticks and moves the right way under turn copy.
3. For δ = ±0.05 the bump reaches the correct side within about 5 ticks, and the turn command has the correct sign for L>R.
4. Under `hold`, E4s-2 beats E4s-0 (otherwise the ring is not earning its neurons).

**Arms**
- Module on a random N2 background.
- Module on E2d champions (the seeded start Fable advised, but with a working stereo module instead of a low-gain genome).
- Frozen-structure versus free-structure versus open-mask.
- Neutral-drift, inert, random-weight and 2-cell controls.

---

## Open questions and risks

1. **My central inference is untested.** The claim that the plateau is a gain and dynamic-range problem is derived from repo constants. A gain probe on the champions and a module-alone simulation would confirm or kill it in an afternoon.
2. **Does Task N need a ring at all?** S-const has no memory and scores 8.7. If E4s-0 matches E4s-2 everywhere, the ring is decoration on this task. A memory-demanding Task N variant (`hold`, scent dropouts) is needed for the ring to have a job.
3. **Front/back ambiguity** may need the temporal channel or a symmetry-breaking bistability.
4. **Differential injection changes the claim.** Variant (b) makes the interface do the comparison. Report it as a control, not the stereo module.
5. **Retention is only observable off-ceiling.** With S-const at 8.78 of an 8.85 ceiling, "improve" cannot show on Task N. Use a harder variant such as weaker coverage or added noise.
6. **Biological framing.** The real worm samples over time; the fly borrows are engineering, and the write-up should say so. A worm-native alternative is an ON/OFF temporal-derivative module with an oscillating turn, as in [Izquierdo & Lockery](https://pmc.ncbi.nlm.nih.gov/articles/PMC3422662/)†. E1's design already anticipated "head oscillation for sensing over time".
7. **Source risk.** Equations for Goulard, Stone/Sun, Westeinde and Mussells Pires were read from automated extracts (†). Several 2026 preprints rest on single unreviewed studies. Nature, Cell, Springer and PubMed were mostly unreadable, so counts (E-PG 46 vs 50) differ between sources.
8. **Nothing found on prosthesis-style grafting or seeded-module fate.** The "keep, improve or dismantle" question is genuinely open, and the neutral-drift control is the strongest way to ask it.
