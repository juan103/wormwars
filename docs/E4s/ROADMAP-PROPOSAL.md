# Proposed roadmap change: E4s after the literature review (v2, 2026-10-01)

Status: v2, for a confirmation round by Astra 6 and Fable 5.1. Nothing here has run.
- **v1** (commit cc13ff8): both reviewers said "adopt with changes"
  (`docs/reviews/20261001-roadmap-proposal/`).
- **v2** takes every must-fix; the map is the last section.

If both agree, it goes into `ROADMAP.md` as a dated amendment (D143).

## Why a change

- **The plateau.** E2d found that none of E2's and 04a's 47 distinct champions meets the "uses the
  left-right difference" criterion: 43 show no material benefit, and 4 are unclear, with small
  detectable benefits (D136, corrected D137). No tested optimizer change left the plateau. E3 needs
  a navigator.
- **The owner's plan (2026-09-30):** a hand-built stereo module ("E4s") grafted onto N2, then
  evolution. The owner's design was two noses and a fly-style ring attractor. The ceiling is 96
  GPU-hours (D139), a ceiling and not a target.
- **Its designs rested on an unchecked report.**
  - Designs v1-v3 (D139-D142; v3 committed as superseded) rested on a literature report by Claude
    Sonnet 5.5.
  - It was a single CLI session; most of its sources were seen only as search snippets, and nobody
    checked its claims. It was wrongly called "a deep research".
  - The owner commissioned a real review.
- **The literature review** (`docs/reviews/20261001-literature-review/`): two reviews from one
  prompt, by Claude Opus and Astra 6. They are not verified by us as a whole. The four points this
  proposal uses, with the reviewers' qualifications:
  1. **A ring is not needed to steer on a smooth Gaussian scent.**
     - Two sensor-to-motor pathways with opposed signs suffice algorithmically: a Braitenberg
       vehicle (Rañó 2012; Simões et al. 2021).
     - Memory helps with outages, changing plumes and displacement (Singh et al. 2023; Sun et al.
       2021).
     - E1 shows that memory is unnecessary for high performance on Task N (a memoryless scripted
       steerer scores 8.7). It does not show that memory cannot help.
  2. **Small hand-built rings need fine tuning** and can pin the bump or fail to move under weak
     input (Noorman et al. 2024, threshold-linear units). A tanh port would need revalidation. This
     supports a tuning concern, not inevitable erosion.
  3. **Grafting has precedents, and the interface matters.**
     - Seeding (Koppejan & Whiteson 2011).
     - Cautious initialisation of added connections (Tomko & Harvey). Zero is not universally best,
       and nothing here justifies disconnecting a functional seed.
     - Adden et al. needed an input remapping before their steering module worked with a navigation
       network. Their four-unit model includes explicit threshold switching logic, so it is not four
       ordinary rate neurons.
     - No study found evolves a stereo graft inside a worm-connectome mask and separates its fates.
       That is a gap within a bounded search.
  4. **The worm's own chemotaxis is temporal.**
     - Klinotaxis: concentration change during head sweeps (Izquierdo & Lockery 2010; Izquierdo &
       Beer 2013; Matsumoto et al. 2024).
     - ASEL and ASER are ON and OFF cells, and our interface sends left scent to ASEL and right
       scent to ASER (`configs/interface.yaml`).
     - The successful models use temporal ON/OFF sensing, **dorsal/ventral symmetry on the motor
       side** (left/right asymmetry is allowed), logistic units with weights up to ±15, and, in
       Hironaka & Sumi, a sensory gain of 100.

       These ranges are not comparable to our ±3 under tanh.
     - Their models also need head oscillation, not only ON/OFF sensors.
- **Not used:** the Opus review's "gain ceiling" argument. Both reviewers reject it: a bound on one
  short path does not bound a recurrent network with converging paths, and it does not explain a
  measured gain of about 0.1.

## The owner's decision on the sensing interface (2026-10-01)

**Option (a): keep the bilateral left/right scent as an explicit game-design choice.**
- WormWars's weys get separate left and right food readings; the README already says a real worm
  cannot do this.
- E4s's claims are about evolving brains on the N2 mask under this game's sensing. They are not
  about worm chemotaxis.
- **Stated in every E4s claim:** the stereo computation happens in a graft with its own noses and its
  own path to the motors, outside the N2 mask (Fable).
- **Named alternatives, not scheduled:** temporal ON/OFF sensing with head oscillation, and other
  weight scalings. They are separate interventions, not one forced choice. They return to the owner
  under "What would change this roadmap".

## Proposed sequence for Track E

### E4s-0: diagnostics (exploratory; at most 2 GPU-hours; no evolution)

- **Compute:** counted through `wormwars.accounting`.
- **Worlds:** each measurement has its own new world range.
- **Paired worlds:** every comparison within a measurement uses the same worlds.
- **Intervals:** 95% percentile bootstraps over worlds (10 000 resamples, fixed seeds).

**1. A residual stereo-gain sweep on the 47 distinct champions** (Astra; widened by both).
- **Method:** turn += k(L − R) is added to the champion's own turn command before the world's
  clamp, at k ∈ {0, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8, 16, 32, 64, 256}. It runs on 512 worlds per
  k.
  - The champions' own gain is about 0.1, hence the small values. E1's useful range reaches 256.
  - The addition is made by the exploratory script around the world's motor readout. It is not an
    engine change.
- **Per champion, the difference from k = 0 at each k.** The pre-stated description:
  - **rises:** the smallest k whose lower bound is above 0 is at most 1, and no smaller k has an
    upper bound below 0;
  - **dips first:** some k below the first improving k has an upper bound below 0;
  - **no benefit:** no k has a lower bound above 0;
  - otherwise **unclear**.
- **Reported:** the count of champions in each class, and each champion's best k.
- **Its reach (Astra):** this tests one externally inserted change of policy. A dip shows a valley
  along that intervention, not along every route evolution could take, and it says nothing direct
  about what weight mutations produce. It informs E4s-1's interpretation; it does not gate it.

**2. Where the champions' response to the difference is attenuated** (descriptive; demoted, as
both suggested).
- **Method:** the differential gain K_D = ∂u/∂d and the common-mode gain K_C = ∂u/∂m (d = L − R,
  m = (L + R)/2), with gain probe v3's controls, read at:
  - the first-layer interneurons AIY, AIZ, AIA and AIB (left and right);
  - RIA;
  - the turn motor neurons SMDD, SMDV, RMDD and RMDV.
- K_D at the sensory neurons is 1 by construction, so it is not reported.
- **Its reach:** a weak gain shows an attenuated response, not necessarily lost information (Astra).
  It has no decision rule.

**3. The comparator ladder, measured where E4s-1 will use it.** How it is built, within the
genome's bounds:
- **Noses:** NL and NR, fed `food_left` and `food_right` at interface gain 1 (not tuned).
- **Comparators:** CL and CR. NL excites CL and inhibits CR; NR does the reverse. Each weight is
  w_n.
- **Outputs:** CL excites the dorsal turn neurons (SMDD, RMDD) and inhibits the ventral ones (SMDV,
  RMDV); CR does the reverse. Each weight is w_o.
- **Where the computation happens:** subtraction in the comparators' inputs, amplification across
  the stages. No signed or tuned interface gain, and no preprocessing outside the genome.
- **Our arithmetic (not yet measured; Fable's, re-derived):** the turn command is about
  4·w_o·w_n·d, up to about 36·d at w_n = w_o = 3. The world's turn is 1 × (mean tanh dorsal − mean
  tanh ventral), not 2× as design v3 said (D143). k = 32 scored 5.63 with a tuned turn bias, and
  4.23 without. So the first step sits near the line.

**The ladder, fixed in advance; the smallest step that qualifies is used:**

| Step | Added | Neurons |
|---|---|---|
| L1 | the circuit above | 4 |
| L2 | self-excitation on CL and CR, w_s ∈ {0.5, 0.8, 0.95} (gain about 1/(1 − w_s) near rest, slower) | 4 |
| L3 | mutual inhibition between CL and CR, w_m ∈ {−1, −2, −3} | 4 |
| L4 | L3 with 2, then 4, parallel comparator pairs on the same noses | 6, 10 |
| L5 | L4 with 2 relay noses per side | at most 16 |

- **Each step's tuning grid:**
  - w_n and w_o ∈ {1, 2, 3}, and each step's own parameter;
  - comparator τ ∈ {0.5, 2} and bias ∈ {−0.5, 0};
  - the carrier's forward command ∈ {0.5, 1} and turn bias ∈ {0, 0.1, 0.2}.

  Each step is tuned on 128 tuning worlds, and its best 5 are re-scored on 512.
- **Qualification (on 1 024 fresh worlds, on the carrier),** as design v3's gate:
  - the Task N mean's 95% lower bound is at least 5.0;
  - **and** E2d's "uses" criterion holds under the module probes.
- **Also measured for the qualifying step** (Astra): the step response and the carried-state reversal
  (v3's controlled forms), and the response time, since recurrence slows it.
- **Then, the step that qualifies, measured where E4s-1 starts** (Fable): grafted onto 256 random N2
  genomes (02's initialisation, drawn on N2 and embedded, on seeds disjoint from E4s-1's) and onto
  04a run 2. Measured:
  - the score;
  - "uses" under the module probes;
  - the forward command, the turn bias, and turn-neuron saturation.
- **Pre-stated readings:**
  - If no step qualifies: "none of the tested candidates passed within the search budget". It is not
    read as a bounds limit (Astra). The owner decides the next step.
  - If the qualifying step meets "uses" on fewer than 25% of the random N2 backgrounds, E4s-1's
    design must take its confirmatory background from somewhere else. One option is the 47
    distinct champions, one per run (Fable). That choice is made in E4s-1's design review, not here.
  - Otherwise E4s-1 proceeds on random N2.
- The chosen step is frozen in a module file, and its hash is committed and pushed before E4s-1's
  pre-registration.

### E4s-1: the comparator graft under evolution (confirmatory; pre-registered; cap set there)

**Re-qualification.** The frozen module re-qualifies on its own fresh gate worlds before any
evolution. It was selected on E4s-0's worlds.

**Background.** As E4s-0 decides; random N2 by default, drawn on N2 and embedded. 04a run 2 is a
descriptive case study of 32 identical copies.

**Arms** (02's GA as E2 kept it; 1 000 generations; Task N, unshaped):

| Arm | Graft at generation 0 | Module mutation | Runs | Role |
|---|---|---|---|---|
| **M** (main) | the frozen comparator | reduced (0.25×, fallback as v3) | 16 | |
| **N** (no added output) | M's genomes, every graft-to-host edge at 0 and pinned throughout | as M | 16, paired with M | **Confirmatory 1:** does the graft's output help? (M − N) |
| **R** (random graft) | M's topology and access, with weights drawn at random (the same magnitude distribution, random signs) | as M | 16, paired with M | **Confirmatory 2:** the designed weights against an added path of the same shape (M − R) |
| F0 (frozen) | as M | none | 8, paired with M 1-8 | descriptive |
| U (uniform) | as M | 02's scale | 8, paired with M 1-8 | descriptive |
| C2 (case study) | the comparator on 04a run 2 | as M | 8 | descriptive |

- **R is matched** in parameter count, sensory and motor access, and mutation treatment, not only
  in neuron count (Astra). It isolates the designed weights from the new sensor-to-motor path
  outside N2 (Fable).
- **Graft-to-host integration edges:** if E4s-1's design adds them (for merging), they start at zero
  or at a declared small value. The seed's own edges keep their designed values (Astra, Tomko &
  Harvey). In N, every graft-to-host route is pinned at 0 throughout.
- **Who owns which parameters.**
  - The module owns its neurons' τ and bias, and every edge with a module neuron at either end.
  - In F0, those are pinned; the host, including the turn neurons, still evolves.
  - So F0's module can still lose function through its host (Astra).
- **Mutation counts** are logged per block. The batches are ordered so that the confirmatory pairs
  finish first.

**Measures** (on a fresh hold-out of 1 024 worlds):
- **The genomes:** F (the final generation's best, the registered reading), C (the champion, beside
  it) and G0 (the generation-0 best), as in v3.
- **Three separate properties at each of G0 and F** (Astra):
  - **D, dependence:** the whole brain meets "uses" under the module probes;
  - **Mc, module competence:** the module transplanted onto the carrier meets "uses";
  - **H, host stereo:** the brain with the module silenced meets "uses" under the world probes.
- **Beside them:** the lesion cost, and the reset-to-seed probe.

**Outcome classes per run** (exclusive; read in order; "unclear" whenever a deciding measurement is
in E2d's unclear class):

| Order | Condition | Class |
|---|---|---|
| 1 | the run did not complete | not read |
| 2 | G0 is not D | never used (H at F reported) |
| 3 | F is D and Mc | **retained** |
| 4 | F is D, not Mc | **used, module changed** (the host compensates or co-adapts) |
| 5 | F is not D, and is H | **host stereo** |
| 6 | F is not D, not H, and Mc | **bypassed** |
| 7 | F is not D, not H, not Mc | **lost** |

- **H at F is reported for every class.** "Retained" with H flags redundancy.
- **"Host stereo" shows acquisition, not transfer.** Transfer would need host stereo above N's and
  R's hosts, whose output never reached the motors (Astra). That comparison is reported, not
  classified.
- **The arm's reading:** a class is named if at least 12 of 16 runs fall in it; otherwise "mixed".
- **The outcome statistics are design v3's:**
  - one estimand per confirmatory comparison (the mean paired difference in F's hold-out mean);
  - 90% bootstrap intervals over runs;
  - ordered, exclusive rules;
  - the sign-flip p reported only.

**Carried from design v3:**
- the carrier;
- the per-run G0 classification;
- the engine changes: per-parameter mutation scales and `evolve_batch` hooks, test-first and
  sabotage-checked (D142);
- **gates still pending, which stay gates:**
  - the GPU reproduction of E2's generation 0-25 hashes;
  - the CUDA state tolerance;
  - the score-level inert-graft check.

### E4s-2: memory (deferred)

It is designed only if a task shows demand for directional memory: scent outages, relocation with
stale memory, or displacement. E3's shuttle may be one.
- It starts from Noorman et al.'s released code, revalidated for tanh units: drift, velocity gain,
  dead zones and recovery.
- Two concentration samples give a lateral component, not a full bearing (Astra). Its design says
  what resolves the ambiguity.

### E3 (in parallel; three additions)

**One rule for its navigation artefact:**
1. E3 starts after E4s-0, without waiting for E4s-1 (both reviewers). It uses E4s-0's frozen
   comparator on the carrier, as one complete genome, if a step qualified. Otherwise it uses 04a run 2,
   with its measured limits stated.
2. E4s-1 decides only whether an evolved host-plus-graft genome replaces it. That needs "retained" in
   at least 12 of 16 M runs; the genome is chosen by validation mean.
3. E3 runs its own navigation positive control on its own task, whichever artefact it uses. A module
   that is useful in one host is not assumed portable (Astra).

**Two additions:**
- **A baseline:** one shared navigator plus a persistent goal bit, beside the two-module organism
  (Astra).
- **The latch:** a candidate is one extra neuron with self-excitation, τq̇ = −q + 2 tanh q + S − R.
  - Fable checked its fixed points by hand: about ±1.915, with a switching threshold of about 0.53.
  - It is Astra's construction, not a published parameter set.
  - It is validated in our integrator for initialisation, pulse duration and simultaneous inputs,
    with a test that a graft accepts a self-edge.
  - The inactive module's semantics (update, freeze or reset) are declared in advance.

### E4 (unchanged; one addition)

Pruning follows a protocol (Fakhar & Hilgetag 2022, via Astra's review):
- importance recomputed after each removal;
- several removal orders;
- interactions tested in pairs;
- acute and retrained results reported separately;
- the preserved function includes the stereo or latch property, not only the score;
- the claim is limited to "the smallest circuit found under this procedure".

## Other changes

- **Tripwire:** relaxed for the graft functions and the GA hooks only.
- **Related work:**
  - Link the literature review. Every claim cited later is verified first.
  - Izquierdo & Beer 2013 is the reference worm-chemotaxis model.
  - Hironaka & Sumi's MIT repository is a candidate executable baseline, not yet run. Its
    publication status (a reviewed preprint, by Astra's reading) is checked before it is cited.
- **What would change this roadmap,** two new entries, consistent with E3's rule:
  - "No comparator step qualifies in E4s-0": the owner decides among wider or rescaled weights,
    temporal sensing with head oscillation, and larger circuits. E3 proceeds on 04a run 2.
  - "E4s-1 finds no 'retained' majority": E3 keeps E4s-0's frozen module. The result is reported in
    the wording fixed in advance.
- **The budget:**
  - The owner's 96-hour ceiling covers all of E4s: diagnostics, tuning, equivalence work and
    evaluation, all counted in the accounting.
  - E4s-0: at most 2 h.
  - E4s-1: its cap is set in its pre-registration. Expected about 15 h: about 4-16 extra neurons,
    so a factor of about 1.03-1.11 on E2's rate, for 72 runs.
  - The rest is not a target.

## Changes from v1

| Review item | v2 |
|---|---|
| The plateau wording against E2d's correction (both 1) | E2d's corrected wording; E1 says memory is unnecessary, not useless |
| The comparator cannot be built as written (both 2) | Noses at gain 1, comparators, outputs, all within ±3; where the subtraction and amplification happen; no preprocessing |
| A ladder before any "bounds" reading; the reading narrowed (Fable 3, Astra 3) | L1-L5 fixed with their grids; "none of the tested candidates passed within the search budget" |
| Design v3's turn readout doubled (Fable 4) | Corrected: a factor of 1; checked in `world.py` and E1's freeze |
| Random N2 backgrounds (Fable 5) | Measured in E4s-0, with a 25% reading |
| Items 1 and 2 had no readings (Fable 6, Astra 3) | Item 1's classes pre-stated, k widened at both ends, its reach narrowed; item 2 descriptive, with named neurons |
| Qualification on fresh worlds and stereo use (Astra 3, Fable 8) | E4s-0's qualification and E4s-1's re-qualification |
| The outcomes are not exclusive; transfer against acquisition (both) | D, Mc and H measured separately; an ordered exclusive table; transfer only against N's and R's hosts, reported |
| Arms: confirmatory comparisons; random graft; cuts; ownership; zero start (Fable 8, Astra 4) | M − N and M − R named; R matched on parameters and access; N pins every route; ownership stated; zero only for added integration edges |
| E3's fallback contradicted (both) | One rule, the artefact named, E3's own positive control |
| Repository state (Fable 10, Astra 7) | Design v3, D142 and the engine changes committed (60bc85e, ab290f7); pending gates kept as gates; accounting covers everything |
| Literature qualifications (both) | Dorsal/ventral symmetry; ±15 not comparable; Adden's switching logic; Noorman threshold-linear; Tomko & Harvey cautious; the latch and comparator labelled as constructions; Hironaka a candidate; the gain ceiling not used |
