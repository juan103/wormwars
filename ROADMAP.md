# WormWars roadmap (draft, 2026-09-25)

**Status: a proposal, reviewed by Astra 6 and Fable 5.1 (`docs/reviews/20260925-163118-roadmap/`,
DECISIONS D044); a revision waits for the owner's decisions on the open points.** Each item has a question, a
cost, and a gate that decides what follows. Costs are GPU-hours on the one RTX 5080. Nothing
below is pre-registered.

## Where the series stands

- **01** (published, superseded): the chemical synapses ran backwards. Its conclusions do not
  hold for the real wiring.
- **01b** (published): with the synapses right, N2 reaches higher mean best-of-generation fitness
  than shuffles (SH) and random graphs (RD) on stereo foraging. As a point estimate, its edge over
  SH is a head start. Final score against SH does not separate.
- **02** (screening, done, reviewed, not yet public):
  - Evolution found meaningful stereo use for neither N2 nor SH. The primary prediction was
    challenged ("no meaningful N2 use").
  - Under the biological mapping, the shuffles start worse and catch up. N2's own mapping
    preference barely moves.
  - N2's random brains are more sensitive to food input overall, not more selective for the
    left-right difference.
  - Shuffles break mirror symmetry (0.13-0.16 of chemical edges kept, against N2's 0.64) and give
    the food neurons direct routes to the motor read-out.
  - Champions forage well without detected stereo use, and whether they use history is
    unresolved.

**The owner's question** is whether the worm connectome is shaped for worm-like tasks under
worm-like plasticity. What the series has so far: any N2-specific signal shows up at generation 0,
and the controls used so far have two generic structural differences from N2 (mirror symmetry
and food-to-motor shortcuts).

## Pipeline

### 0. Publish 02 (no GPU)
Merge `exp02-screening` into `main` and push, once the owner says go.

### 1. 02b: what the champions compute (under 1 GPU-hour, saved genomes only)
- **Question:** how do 02's champions forage well without stereo?
- **Method:**
  - replay the champions with per-tick logging;
  - measure speed and turning against food level, food change, the left-right difference and
    collision;
  - replay matched current input after different histories;
  - run the corrected input-response probe on evolved genomes, not only random ones;
  - measure how far anatomical magnitudes are eroded.
- **Gate:** none. It is descriptive and informs 04's task design.

### 2. 03: generation-0 structure (about 2-5 GPU-hours, no evolution)
- **Question:** is anything about N2 at generation 0 specific to N2, beyond mirror symmetry and
  routing?
- **Method:**
  - N2 against three shuffle ensembles of 16 graphs each: ordinary; routing-matched (no direct
    food-to-motor shortcuts beyond N2's); routing plus mirror-matched (matching N2's *partial*
    symmetry);
  - M0 and several remaps; gap junctions on and off; magnitude permutations;
  - about 2048 random genomes per graph, with per-brain values saved;
  - measures: input response, signed and common-mode, and generation-0 fitness (mean and
    best-of-32).
- **Gate:**
  - If symmetry and routing account for N2's generation-0 signal, the series' N2 effect has a
    generic graph explanation. Write that up, then stop or pivot.
  - If N2 still stands out, the new ensembles become the standard controls for everything after.
- **Also builds** the control ensembles 03a and 04 need.

### 3. 03a: self-consistency panel study (draft v2, `experiments/03a-self-consistency/`)
- **Question:** can a deleted neuron's wiring be recovered from the rest of the brain plus a task?
- **Needs, before its pre-registration tag:**
  - another review;
  - the notes from 02 (`NOTES_FROM_02.md`);
  - probably the 03 control ensembles as extra conditions;
  - a batched timing pilot (the draft estimates 280 GPU-hours unbatched and caps at 168).
- **Gate:** its own four-way outcome distribution. 03b (full map) only if 03a separates the
  outcomes.
- **Placed after 03** so it can use better controls. It does not depend on evolution discovering
  a new capability, which is where 02 stalled.

### 4. 04: a task where the capability is necessary, with search validation (about 12 GPU-hours)
- **Question:** given a task where stereo or memory is necessary and a search shown to find it,
  does N2 acquire or use it better than the 03 controls?
- **Method:**
  - design the task so that kinesis scores close to straight running;
  - run a scripted gate against a richer memoryless baseline;
  - run a shuffle-only feasibility pilot *before* the pre-registration, requiring that evolved
    champions use the capability. That gate failed in 02.
- **Gate:** if no search finds the capability in shuffles, stop here and report it.
- **Only if 03 shows N2 still stands out.**

### 5. Later
- **Plasticity:** deferred until there is a within-lifetime adaptation task. Recurrent memory is
  not plasticity.
- **03b:** the full self-consistency map.
- **More tasks,** leave-k-out, missing synapses, a full self-consistent-field loop (from the 03a
  draft).

## Budget

Items 1-2 cost under 6 GPU-hours. 03a's cost is unknown until its batched pilot. 04 is about 12.
The whole roadmap up to 03a's pilot is under a day of GPU.

## Claims to attack

1. The generation-0 structural study should come before 03a and 04.
2. 03a is worth running whatever 03 finds, because it asks a different question.
3. Plasticity should stay deferred.
4. The series should stop, not pivot, if 03 finds a generic explanation.
