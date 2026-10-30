# M6, option 3: does the real worm show anything like the model's history effects? — scope

*Draft 2, 2026-10-30, after one blind round of consultation (Astra 6 and Fable 5.1, each without seeing the other;
draft 1, the prompt and both answers are in [`docs/reviews/20261030-m6-3-scope/`](../reviews/20261030-m6-3-scope/)).
The owner chose option 3 of [`M6-OPTIONS.md`](M6-OPTIONS.md) after option 0's results
([`M6-0-RESULTS.md`](M6-0-RESULTS.md)), "with consultation with Fable and Astra". A bounded literature check under
the project's standard (D143, D172). No compute, and every source is tagged with what was actually read. It is not a
deep research, and it is not a test of the model.*

## Why

The memory thread found history-dependent dynamics in random and evolved brains on N2's wiring. Nothing so far says
whether the real worm's head circuit does anything comparable. If it does, a model-to-worm comparison might be worth
designing later. If it does not, or if the literature cannot say, the thread's results stay facts about this model.
Even then, other rate models on the same wiring may have found the same things, and the check looks for them
(Fable).

## What the model shows

The model is a leaky rate network on N2's wiring: `tau dv/dt = -v + b + W tanh(v) + G (v_i - v_j) + I`.
- **What it has:** chemical and gap-junction edges; random or evolved weights, with random signs and no Dale's law
  by default; time constants of 0.5 to 20 ticks.
- **What it lacks:** intrinsic conductances, spikes, plateaus, neuromodulation, plasticity, compartments and body
  feedback.
- **Time:** ticks have no calibrated mapping to seconds.

The features:
- **Input and read-out.** The same food signal enters AWA, AWC and ASE on each side, a modelling choice. Turning is
  read from eight head motor neurons: SMDD and RMDD on one side, SMDV and RMDV on the other.
- **The probe.** Two histories: a short food ramp from a low or a high level to the same final level. The history
  difference is how far the turn read-out stays apart afterwards. The probe runs open loop, with no head oscillation.
- **Fading, in most genomes and in evolved champions.** Most genomes return to one state. In 02's evolved champions
  the history effect is larger than in drifted genomes, and it fades within a few tens of ticks: 101 of the 102 are
  fading (option 0).
- **Switches, in a few random genomes.** Fewer than 2% of random genomes on N2 settle into one of two stable states
  depending on the history.
  - **Where they are vulnerable.** In N2 they are most vulnerable to a temporary cut of RIA's connections within C3,
    which shows vulnerability, not storage (the synthesis). C3 is the 30 neurons of highest internal degree within
    K, the turn read-out together with its one-step chemical inputs. It is an anatomical set of N2's neurons, not an
    established biological module (Astra). It includes the eight read-out neurons, RMDL and RMDR, RIA, RIM, AIB,
    RIB, RIC, RIS, SMBDR, SAAVR, the four CEPs, OLLR, RMGL and RMHL (Fable named RIM, AIB, RIB and RIS; the list is
    `core30_anatomy` in `runs/memory-m1/anatomy.json`).
  - **Moved into other graphs,** C3's block raises the switch rate there. How its weight is concentrated matters
    (M4d, M4e).

## The questions, bounded

The question, reframed (Astra): what evidence shows that recent sensory experience changes later head steering or
turning under matched current conditions? What dynamics carry that information, and which aspects are comparable to
this model? Fading effects stand equal with switches, because fading is the evolved brains' result (Astra).

1. **Persistent or multiple states (A)** in the head-steering and command neurons, wherever a C3 neuron carries
   them. That includes plateaus, up and down states and self-sustained activity, and the forward and reverse
   states held by AVA, AIB and RIM. It also includes their mechanism: intrinsic, circuit or neuromodulatory
   (Fable).
2. **History selecting the state or changing later steering (B).** Where the history is held matters: in the
   sensory neurons (adaptation, temporal filtering), the interneurons, the motor circuit, oscillation phase or a
   modulator. So do the time scale and whether it fades. Sensory adaptation and short-lived cellular processes count
   (Astra, Fable).
3. **RIA specifically:** integrator or store; its compartments; its sensory and motor inputs.
4. **Structure (C):** whether anything known about hub neurons, dense cores or anatomy against function bears on
   the model's structural finding, that a dense head core raises the switch rate (Fable). Kept short.
5. **Model precedents:** rate or other models on the connectome that report multistability or long transients, and
   evolved connectome-derived steering circuits (Fable). Half a page.
6. **What would mislead:** a list fixed before the report is written (below).

**Not in scope:** associative learning and long-term plasticity, except where a short-term state is the subject. A
general survey of global brain states or of every neuromodulator. Roaming and dwelling stay as a few mechanistic
comparators (Astra). 03h's ASK result is an implementation note, not a constraint on biology (Astra).

## Keeping the evidence apart (Astra)

The report keeps four claims separate. History changes neural activity. History changes behaviour. Activity
persists through a delay. A particular mechanism maintains information that later behaviour uses. None establishes
the next. Bimodality, regenerative responses, prolonged calcium and two stable equilibria are also different
observations. Strong evidence for bistability would show history-dependent occupancy under the same maintained
conditions, switching or resetting, and a test of stability.

## The guards, fixed before the report

- **Same word, different mechanism.** "Bistable" in RMD means an intrinsic plateau. *Corrected 2026-10-30 (round 2, Astra, Fable): the RMD plateau is modelled as intrinsic (Nicoletti 2019) or as circuit-based (Liu J 2022), and the experiments do not settle it; the guard holds as "the mechanism is not shown to be the model's".* In the model it means recurrent
  saturating synapses. Matching the word proves nothing (Fable).
- **The word "switch".** In Ouellette et al. it means routing RIA's output dorsally or ventrally. It is not evidence
  of memory (Astra, Fable).
- **RIA confirmation bias.** RIA's prominence in the literature is not support for M4c, which showed vulnerability
  to a cut, not storage (Fable, Astra).
- **An intervention is not a storage assay.** Erasing a distinction can disrupt input, upkeep, state changes,
  read-out or movement (Astra).
- **Signs and transmitters.** The model draws signs at random, so any comparison is topological only (Fable).
- **Anatomy is not function.** Measured signal propagation departs from anatomy in places (Fable).
- **Neuromodulators and the sensory layer.** These hold or compute much of the worm's history. The model injects
  one signal into six sensory neurons as leaky units (Fable, Astra).
- **Embodiment.** Steering is phase-dependent sampling during head sweeps, with proprioception. The probe is open
  loop, with no oscillation (Fable). Oscillation phase is also a candidate memory mechanism in its own right
  (Astra).
- **Time.** No tick-to-second comparison; calcium indicators are slow (both).
- **Population against individual.** "Fewer than 2% of random genomes" describes a weight ensemble. The worm is
  one parameter set, with wiring that varies between individuals (Fable, Astra).
- **Read-out lumping.** The model lumps RMD with SMD; the worm separates them (Fable).
- **Absence.** "Not found in the sources checked" is not "the worm has no such mechanism" (Astra).

## Method

- **The check:** Claude searches (web search, Europe PMC, the Consensus index, direct fetches) and reads every
  source the report leans on. Each claim gets a level:
  - **full text:** read;
  - **abstract:** only the abstract was read;
  - **snippet:** a search result only;
  - **secondary:** through another source;
  - **wrong:** the source does not say it;
  - **not found:** a bounded search found nothing (Fable).

  Pages behind a bot check are not worked around. The search strings and dates are recorded (Fable).
- **Sources named by only one consultant** get the most checking (Fable). Overlap between the two blind lists is
  reported.
- **The evidence table,** one row per claim: the claim, the source and version, the reading level, the
  preparation, the neuron or compartment, the stimulus history, whether the final conditions were matched, the
  measured variable, the duration, any intervention, and what remains unidentified (Astra).
- **The report:** `docs/memory/M6-3-LITERATURE.md`, then round 2, in which both consultants review it and check its
  load-bearing citations. Disagreements are recorded, not resolved by vote.
