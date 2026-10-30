# M6, option 3: does the real worm show anything like the model's history switch? — scope

*Draft 1, 2026-10-30, before consultation. The owner chose option 3 of [`M6-OPTIONS.md`](M6-OPTIONS.md) after option
0's results ([`M6-0-RESULTS.md`](M6-0-RESULTS.md)), "with consultation with Fable and Astra". A bounded literature
check under the project's standard (D143, D172): no compute, every source tagged with what was actually read. It is
not a deep research, and it is not a test of the model.*

## Why

The memory thread found history-dependent dynamics in random and evolved brains on N2's wiring. Nothing so far says
whether the real worm's head circuit does anything comparable. If it does, a model-to-worm comparison might be worth
designing later. If it does not, or if the literature cannot say, the thread's results stay facts about this model.

## What the model shows (the things to compare)

The model is a leaky rate network on N2's wiring: `tau dv/dt = -v + b + W tanh(v) + G (v_i - v_j) + I`. It has
chemical and gap-junction edges, random or evolved weights, time constants of 0.5 to 20 ticks, and no intrinsic
conductances, spikes, plateaus, neuromodulation or plasticity. Ticks have no calibrated mapping to seconds.
- **Input and read-out.** Food scent enters at AWA, AWC and ASE (left and right). Turning is read from eight head
  motor neurons: SMDD and RMDD on one side, SMDV and RMDV on the other.
- **The probe.** Two histories: a short food ramp from a low or a high level to the same final level. The history
  difference is how far the turn read-out stays apart afterwards.
- **Switches.** Fewer than 2% of random genomes on N2 settle into one of two stable states depending on the history
  (bistability set by recent sensory history). In N2 they are most vulnerable to cutting RIA's connections within
  C3, the head core: the 30 neurons with the highest internal degree, which include the eight read-out neurons and
  RIA. Head cores moved into shuffled graphs raise the switch rate there.
- **Evolved brains.** Champions evolved for foraging (02) hold a larger history effect than unevolved or drifted
  genomes. It fades within a few tens of ticks, and almost never becomes a switch (option 0).
- **03h.** In random brains, a history bit entered through ASK reached the read-out only weakly.

## The questions, bounded

1. **Bistability or persistent states** in RIA, RMD, SMD or their partners in the head-steering circuit:
   plateaus, up and down states, all-or-none or self-sustained activity. Mechanism (intrinsic or circuit) if known.
2. **History dependence in head steering or turning**: sensory history (food or odour level, a recent change)
   setting a state that outlasts the stimulus. On what time scale, and where it is held, if known.
3. **RIA specifically**: what is known of its compartmentalised activity, its role in head bending and in
   integrating sensory input, and any memory or state.
4. **What would make a comparison misleading**: rate model against graded potentials and calcium; neuromodulation
   (for example dopamine, serotonin, tyramine, neuropeptides) setting behavioural states; time scales; the head
   oscillation itself.

Not in scope: learning and plasticity (associative, imprinting, habituation), except where a short-term state is
the subject; whole-brain global state dynamics, except where they bear on the head-steering neurons.

## Method

- **Consultation, round 1 (blind, independent):** Astra and Fable each critique this scope and list candidate
  sources with what each is expected to say, tagged by how they know it.
- **The check:** Claude searches (web search, the Consensus index, direct fetches) and reads every source the
  report leans on, recording a level for each claim: **full text** (read), **abstract** (only the abstract read),
  **snippet** (a search result only, not verified), or **wrong** (the source does not say it).
- **The report:** `docs/memory/M6-3-LITERATURE.md`. A table of the model's features against the evidence, each
  claim with its source and level, then what it means and what it does not.
- **Consultation, round 2:** both review the report and check its load-bearing citations.
- Disagreements between the consultants are recorded, not resolved by vote.
