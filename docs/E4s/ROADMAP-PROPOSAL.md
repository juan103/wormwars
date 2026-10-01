# Proposed roadmap change: E4s after the literature review (v2.1, 2026-10-01)

Status: v2.1, adopted. It goes into `ROADMAP.md` as a dated amendment (D144). Nothing here has run.
- **v1** (cc13ff8): both reviewers said "adopt with changes"
  (`docs/reviews/20261001-roadmap-proposal/`).
- **v2** (fdddee4): both said "adopt with changes" again
  (`docs/reviews/20261001-roadmap-proposal-v2/`). Fable added that none of its items needed a new
  design round.
- **v2.1** takes every v2 item; the maps are the last two sections.

The details of E4s-0's script are pinned in its own plan (`docs/E4s/E4s-0-PLAN.md`), which is
reviewed before it runs.

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
- **Units:** L and R are the scaled `food_left` and `food_right` the interface injects (E1's units),
  and turn > 0 is a left turn.
- **Checked first:**
  - the residual is inserted before the clamp;
  - at k = 0 the wrapped world reproduces the unwrapped champion's per-world counts exactly.
- **Per champion, the paired difference from k = 0 at each k.** The materiality threshold is 0:
  this is descriptive, not E2d's criterion.
- **Adjacency, against multiplicity** (Fable): "improves at k" needs lower bounds above 0 at k and at
  the next larger k. "Is harmed at k" needs upper bounds below 0 at k and at the next larger k. The
  first improving k is the smallest k that improves.
- **The pre-stated classes:**
  - **rises early:** the first improving k is at most 1, and no smaller k is harmed;
  - **rises late:** the first improving k is above 1, and no smaller k is harmed. This is the likeliest
    case: k ≤ 1 adds at most about 0.017 to the turn command;
  - **dips first:** an improving k exists, and some smaller k is harmed;
  - **harmed:** no improving k, and some k is harmed;
  - **no detected benefit on the tested grid:** neither (Astra: broad intervals fall here too);
  - otherwise **unclear**.
- **Reported:** the count in each class, and each champion's first improving k. Even with adjacency,
  these are exploratory results from scanning many pointwise intervals.
- **Its reach (Astra):** this tests one externally inserted change of policy. A dip shows a valley
  along that intervention, not along every route evolution could take, and it says nothing direct
  about what weight mutations produce. It informs E4s-1's interpretation; it does not gate it.

**2. Where the champions' response to the difference is attenuated** (descriptive; demoted, as
both suggested).
- **Method:** the differential gain K_D = ∂u/∂d and the common-mode gain K_C = ∂u/∂m (d = L − R,
  m = (L + R)/2), with gain probe v3's controls, read at:
  - the sensory neurons ASE, AWA and AWC (left and right);
  - the first-layer interneurons AIY, AIZ, AIA and AIB (left and right);
  - RIA;
  - the turn motor neurons SMDD, SMDV, RMDD and RMDV.
- **The sensory neurons are not trivial** (Astra corrects v2's "1 by construction"). The injected
  currents have derivatives of +½ and −½ with respect to d. A sensory neuron's activity in a recurrent
  brain is not fixed by that.
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
  4.23 without.
  - Corrections: sech²(m) at the noses (about 0.89 at the peak level, so about 32·d) and sech²(b_t)
    from the turn bias.
  - The path has three lags (nose, comparator, motor relay) that E1's scripted steerer did not have.
  - It assumes the outputs reach all eight turn neurons, as wired.
  - So the first step sits near the line, probably slightly below it (Fable). E1's scores do not
    predict the graft's closed-loop score.

**The ladder, fixed in advance.** Each step is defined against L1; the steps are not cumulative. The
first step that qualifies, in this order, is used:

| Step | Built from L1 by adding | Neurons |
|---|---|---|
| L1 | nothing | 4 |
| L2 | self-excitation on CL and CR, w_s ∈ {0.5, 0.8, 0.95} (gain about 1/(1 − w_s) near rest, slower) | 4 |
| L3 | mutual inhibition between CL and CR, w_m ∈ {−0.5, −0.8, −0.95} | 4 |
| L4 | 2, then 4, parallel comparator pairs on the same noses, each built as the better of L1-L3 on the tuning worlds | 6, 10 |

- **Keeping the comparator monostable.** In the differential mode, τẋ = −x + |w_m|·tanh x + w_n·d.
  - At |w_m| ≥ 1 the pair is bistable: a latch whose switching threshold (about 0.53 at |w_m| = 2)
    is far above the available drive w_n·d ≤ 0.05. It would latch on the first transient and never
    flip (Fable). So v2's grid of −1, −2 and −3 is replaced.
  - Any combination of self-excitation and mutual inhibition must satisfy w_s + |w_m| < 1.
  - Bistable candidates are latches, not amplifiers. They belong to E3, not to this ladder (Astra).
- **v2's L5 (relay noses) is dropped:** a relay through tanh adds no gain (Fable).
- **The self-edge L2 needs is tested,** and that test was seen failing under a sabotage (D144).

- **Each step's tuning grid:**
  - w_n and w_o ∈ {1, 2, 3}, and each step's own parameter;
  - comparator τ ∈ {0.5, 2} and bias ∈ {−0.5, 0};
  - the carrier's forward command ∈ {0.5, 1}, and its turn command ∈ {0, 0.1, 0.2}. These are command
    values: the bias b_t = atanh(command / 2), since the turn is 2·tanh(b_t) with dorsal +b_t and
    ventral −b_t.

  Each step is tuned on 128 tuning worlds, and its best 5 are re-scored on 512. The best of those 5
  (ties to the first in grid order) goes to qualification.
- **Qualification,** as design v3's gate, on 1 024 fresh worlds for each step's attempt (a new
  range each time), on the carrier:
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
  - **The statistic is the one E4s-1's outcome table uses** (Fable): the G0 best of a population.
    - 16 simulated populations are drawn, 32 random N2 genomes each, as E4s-1 will draw them.
    - Each population's G0 best is picked by fitness on 8 training worlds, as the GA's generation 0
      does.
    - Each G0 best is then classified for D on 256 worlds.
  - **If fewer than 12 of the 16 simulated G0 bests are D,** a "retained" majority in E4s-1 is out
    of reach by construction. E4s-1's design must then change its background, its reading, or both.
    One option is the 47 distinct champions, one per run (Fable). That choice is made in E4s-1's
    design review, not here.
  - Otherwise E4s-1 proceeds on random N2.
  - The share of the 256 individual backgrounds that are D is reported beside it.
- The chosen step is frozen in a module file, and its hash is committed and pushed before E4s-1's
  pre-registration.

**4. Mutational robustness** (Astra: v3's mutation-scale fallback needs it). The qualifying
comparator is mutated on the carrier, module parameters only:
- 256 mutants at each of 0.125×, 0.25× and 1× 02's scales;
- 64 worlds of their own;
- measured: the median child's score as a share of the parent's.

v3's fallback rule applies to E4s-1: if the median child at 0.25× keeps less than half its parent's
score, and at 0.125× keeps at least half, the module's factor becomes 0.125×.

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
| **R** (random graft) | M's topology and access, with the designed weight magnitudes permuted across the module's edges and each sign drawn at random; τ and bias as designed; **one draw per run**, from a seed derived from the run seed, shared by the whole population | as M | 16, paired with M | **Confirmatory 2:** the designed weights against an added path of the same shape (M − R) |
| F0 (frozen) | as M | none | 8, paired with M 1-8 | descriptive |
| U (uniform) | as M | 02's scale | 8, paired with M 1-8 | descriptive |
| C2 (case study) | the comparator on 04a run 2 | as M | 8 | descriptive |

- **R is matched** in parameter count, sensory and motor access, and mutation treatment, not only
  in neuron count (Astra). It isolates the designed weights from the new sensor-to-motor path
  outside N2 (Fable).
  - One draw per run tests designed against random weights. A draw per individual would let
    generation-0 selection choose among sign patterns, which is a different question (Fable).
  - At 0.25× mutation a weight of magnitude about 3 will not change sign, so R cannot repair itself.
    The reading of M − R says so.
- **M − N is close to a foregone conclusion once the module qualifies. M − R is the informative
  comparison.** The two 90% intervals are read separately, with no multiplicity adjustment, and that
  is stated.
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
  - **H, host stereo:** the host meets "uses" while the module is alive but blind (Fable).
    - The module's noses get the mean of the two sides (the module "mean" probe), and the host's
      sensors get the real input.
    - This is contrasted with the host's sensors on the world's mean probe, and on its swapped
      probe.
    - Silencing the module would also remove the constant drive the host adapted to, so it is
      reported as a secondary measure, not as H.
- **Beside them:** the lesion cost, and the reset-to-seed probe.

**Outcome classes per run** (exclusive; read in order; "unclear" whenever a deciding measurement is
in E2d's unclear class). The table applies to M, R, F0, U and C2. In N, D is impossible by
construction, so N reports H at G0 and at F only.

| Order | Condition | Class |
|---|---|---|
| 1 | the run did not complete | not read |
| 2 | G0 is not D, and F is D | **acquired** |
| 3 | G0 is not D, and F is not D | **never used** |
| 4 | F is D and Mc | **retained** |
| 5 | F is D, not Mc | **used, module changed** (the host compensates or co-adapts) |
| 6 | F is not D, and is H | **host stereo** |
| 7 | F is not D, not H, and Mc | **bypassed** |
| 8 | F is not D, not H, not Mc | **lost** |

- **H at G0 and at F are reported for every class.**
  - "Retained" with H flags redundancy.
  - **Host acquisition** means H at F without H at G0 (Astra: H at F alone shows only host
    competence).
- **What M against N and R can show** (Astra corrects v2, which said R's output never reached the
  motors: R remains connected):
  - M against N can support graft-assisted host acquisition: the H-acquisition rates of M and N,
    compared.
  - M against R tests the contribution of the designed weights.
  - Neither alone shows that a particular computation transferred into the host. That comparison is
    reported, not classified.
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
1. E3 starts after E4s-0, without waiting for E4s-1 (both reviewers).
   - It uses E4s-0's frozen comparator on the carrier, as one complete genome, if a step qualified.
     That artefact is a hand-built circuit on a silent worm, with no evolved N2 in it, and E3's claims
     say so (Fable).
   - Otherwise it uses 04a run 2, with its measured limits stated.
   - If the frozen module later fails E4s-1's re-qualification, E4s-1 stops for diagnosis, and E3
     falls back to 04a run 2, by a dated amendment.
2. E4s-1 decides only whether an evolved host-plus-graft genome replaces it.
   - That needs "retained" in at least 12 of 16 M runs.
   - The genome is chosen by validation mean **among the individually "retained" F genomes** (Astra).
   - The swap happens before E3's pre-registration is bound, or by a dated amendment to it.
3. E3 runs its own navigation positive control on its own task, whichever artefact it uses, and a
   replacement must pass it too. A module that is useful in one host is not assumed portable
   (Astra).

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
    - About 0.85 M episodes: the sweep 0.31 M, the ladder about 0.25 M, the backgrounds and simulated
      populations about 0.2 M, robustness 0.05 M, and qualification and probes.
    - That is about 0.25-0.6 h at Task N's measured 434-1 027 episodes per second, before overheads.
      The plan checks it against a smoke measurement.
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

## Changes from v2

| v2 review item | v2.1 |
|---|---|
| L3's grid latches; steps cumulative?; L5 undefined (Fable 3a; Astra 2) | Steps defined against L1, not cumulative; L3 at w_m ∈ {−0.5, −0.8, −0.95}, and w_s + \|w_m\| < 1; bistable candidates are E3 latches; L5 dropped |
| The self-edge needs a test before L2 (Fable 3a) | `test_a_module_neuron_may_excite_itself`, which failed under a sabotage that drops self-edges |
| Candidate selection, fresh worlds per attempt, turn bias units (Fable 3a) | The best of 5 (ties to grid order); a new 1 024-world range per attempt; turn command values, b_t = atanh(command / 2) |
| The sweep's classes have a hole; "no benefit" hides harm; multiplicity; units; materiality (Fable 3b; Astra 3) | "Rises early", "rises late", "dips first" (only with an improving k), "harmed", "no detected benefit on the tested grid"; adjacency for both directions; units and sign pinned; threshold 0, descriptive; k = 0 must reproduce the champion exactly |
| "K_D at sensory neurons is 1 by construction" (Astra 3) | Withdrawn: the derivatives are ±½ and recurrent activity is not fixed; sensory neurons are measured |
| "Acquired" dropped; table scope; H at F is not acquisition; R remains connected (Fable 3c; Astra 1) | An "acquired" row; scope M, R, F0, U, C2, with N reporting H; host acquisition needs H at G0 against F; v2's false statement about R corrected |
| The 25% reading does not match 12 of 16 (Fable 3c) | The statistic is the simulated populations' G0 bests, with a threshold of 12 of 16 |
| R's draw unit (Fable 3c; Astra 4) | Permuted magnitudes, random signs, τ and bias designed, one draw per run; R cannot repair its signs at 0.25× |
| H by silencing (Fable, should-fix) | H with the module alive but blind; silencing reported as secondary |
| M − N foregone; the two intervals (Fable 3c) | Said; read separately, without adjustment |
| E3: failed re-qualification; "among retained"; timing of a swap; what the artefact is (Fable 3d; Astra 5) | All four added to E3's rule |
| The robustness measurement for the mutation fallback (Astra) | E4s-0 item 4 |
| A compute estimate against the 2 h cap (Fable 4.8) | About 0.85 M episodes, about 0.25-0.6 h, checked in the smoke |
| The script's details (both) | Pinned in `docs/E4s/E4s-0-PLAN.md`, reviewed before it runs |
