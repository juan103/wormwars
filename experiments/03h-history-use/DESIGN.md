# 03h: does the history random brains hold help them forage? Design v1 (draft, for review)

**Status:** design v1, 2026-10-18. Not reviewed, not coded, not run. It follows the scoping round with both reviewers
(`docs/reviews/20261018-memory-thread-scope/`, D321). GPU work needs the owner's word.

## 1. The question

**The memory thread** (`ROADMAP.md`, "The thread worth following") says N2 starts with more capacity to hold recent
history, and that evolution then builds such memory into every graph, which would explain why N2's early advantages
fade. Two links in that chain are established, and one is not:
- **Established:**
  - N2's random brains hold a past food level unusually strongly (P4: 03, 03r, 03mc; 0.931, 0.924, 0.926 against
    ensemble means of 0.75-0.84);
  - selection builds history dependence into every group's champions (02b).
- **Untested:** that this history helps performance. No file here relates a genome's history to its fitness (Fable,
  scoping round), and 02b says whether history helps foraging "was not tested".

03h tests that link first, at generation 0, where P4 is measured, and on the task where memory pays: Task N with one
nose (Task N-mono). There, a scripted memoryless controller (KT) scores 1.20 and one tick of memory (KTM) 2.84
(`experiments/03a-self-consistency/DESIGN.md` §2).

**Two questions, both at generation 0:**
- **A, the link:** within a graph, do random genomes that hold more history forage better on Task N-mono, and less so
  when the need for memory is removed?
- **B, N2's head start:** is N2's generation-0 advantage over the null ensembles larger when memory is needed than when
  it is not?

**Stage C,** evolution under both conditions (the roadmap's "shrinks over generations"), runs only if A or B meets its
criterion. It is designed then, with A's and B's variance in hand. Both reviewers advised against running it first.

## 2. The manipulation: a relief signal

The level sense is left exactly as it is. A separate binary channel, `food_fell`, is added: 1 on a tick where the food
level at the nose is below the previous tick's, and 0 otherwise (and 0 on an episode's first tick).
- **Why this form** (Fable; Astra's critique of "change only"):
  - it removes no information, because the level is untouched;
  - it is non-negative and scale-free, at the collision channels' scale;
  - a memoryless controller reading level and `food_fell` can do exactly what KTM does.
  - A "change only" sense loses the level that KTM uses, so it cannot act as KTM. A mixed level-plus-change scalar
    needs memory to separate (both reviewers).
- **The conditions:**
  - **level** — `food_fell` is present but held at 0 on every tick;
  - **relief** — `food_fell` live.

  Both conditions have the same channel, the same neurons and the same gain, so the network and the injection sites
  are identical. Only the signal differs.
- **The receiving neurons, to be registered:**
  - **Candidate:** ASKL and ASKR. They are sensory neurons already in the interface, whose channel (ally pheromone)
    is silent in one-wey Task N.
  - **The alternatives,** for review: AWC (the worm's odour-OFF neurons, which already receive the level), or a
    non-sensory pair.
  - The null ensembles keep neuron identity, so the receiving pair is the same pair in every graph.
- **Target relocation** (Astra): when a target is captured and the next appears, the level jumps. The bit is computed
  from successive readings like any other tick, with no hidden reset, so it carries no information the level does
  not.
- **What it does not do** (Fable, Astra): it varies memory demand for one strategy, not memory capacity. Every graph
  keeps its slow neurons and recurrence in both conditions. It is a temporal-assistance contrast, not "memory versus
  no memory".

**The scripted go condition,** checked before any neural run, on registered tuning and check worlds. Each family is
tuned separately, and the families are nested:
- **Under level:**
  - best memory controller (KTM, KTS T = 2, 5, 10) − best memoryless (KT) ≥ 1.0 targets;
  - D303 measured +1.64.
- **Under relief:**
  - the best memoryless controller that reads `food_fell` must be within 0.3 targets of the best memory controller,
    which also reads it (an equivalence margin, not a non-significant difference; Astra);
  - this shows the relief removes the benefit within these families. It does not show no better memory strategy
    exists.
- **If either fails,** 03h stops and is reported. No neural run follows.

## 3. Graphs, genomes, worlds

- **Graphs:** N2; SH (64 graphs); SH-route (64 graphs). 03's samplers (`wormwars/exp03/samplers.py` `build`), seeds
  outside every earlier range (Fable: SH-route caps direct sensor-to-readout edges, 02's post hoc explanation of its
  one separated effect). SH-mirror, Astra's primary, is the open choice for review: it adds mirror symmetry to
  SH-route's constraint.
- **Motor calibration:** once per graph, under level, then frozen for both conditions (Astra). Achieved drive and
  clipping are reported per condition.
- **Genomes:** 1 024 random genomes per graph from the generation-0 distribution (`Genome.random`, 03's). The same
  genome seeds are used in both conditions.
- **Fitness:** Task N-mono's mean count over 8 worlds, the same 8 for every genome, graph and condition (paired).
- **History:** 03's `history()` (`wormwars/exp03/measures.py`), run under level only, with the bit absent. Under
  relief, the rising and falling ramps would present different inputs (Astra). Per genome, it records:
  - the rising-minus-falling difference on the raw turn read-out (and forward), the numerator of P4;
  - the steady contrast, its denominator, as the response magnitude.

## 4. Readings (to be fixed in the pre-registration)

**A, the link** (primary). For each graph:
- compute the partial Spearman correlation of |history| with fitness across its 1 024 genomes, controlling for the
  response magnitude (Fable: both depend on input gain), under level (ρ_L) and under relief (ρ_R);
- take D_g = ρ_L − ρ_R.

The test:
- a one-sided test that the mean of D_g over the 129 graphs exceeds 0, with graph as the unit;
- reported for every graph, with N2's own D and genome-bootstrap interval;
- a smallest effect of interest is to be fixed, for example 0.05 in ρ.

Reading: D > 0 says the history random brains hold helps them forage when memory is needed, as measured by this
probe. It says nothing about N2 in particular.

**B, N2's head start** (primary).
- **The upper tail:** for each graph and condition, take the expected best of 32 genomes (by order statistics over
  the 1 024 sampled) and the top-decile mean (Fable: best-of-32 champions at generation 0 are too noisy).
- **The statistic:** U_g = (upper tail under level) − (upper tail under relief), and N2's U against each ensemble's
  U, by 03's rank rule (64 graphs: the smallest p is 1/65).
- **Report both components** (Astra). An interaction can be positive because N2 does worse under relief rather than
  better under level.

**Descriptive:**
- every graph's ρ_L, ρ_R, upper tails and population means;
- P4 per graph, against 03's values;
- the generation-0 distribution under each condition.

## 5. Stage C (gated; outline only)

C runs only if A's or B's criterion is met, and only with the owner's word. The scoping round's choices, to settle
then:
- the champion of generation g, scored on held-out test worlds after validation selection;
- generations 0, 5, 10, 25, 50, 100, 250;
- paired worlds and initial populations across conditions;
- graphs and runs sized from A's and B's variance. Astra estimated 20-45 GPU-hours for a full design; Fable estimated
  about 5 for a smaller one;
- the fade tested directly, not as "significant early, not late";
- RIA, AIY and AIZ lesions on its champions, descriptive (prediction 3).

## 6. Budget

**Stage A and B together:** 129 graphs × 2 conditions × 1 024 genomes × 8 worlds = 2.11 M episodes.
- At the scan's measured 892 per second (03a's large batches), that is about 0.7 GPU-hours.
- Per-graph calibration costs about 25 s, about 0.9 hours for 129 graphs.
- The history probe costs about 13 s per graph, about 0.5 hours.
- The scripted controls are small.
- **Estimate:** about 2.5 GPU-hours, inside a proposed cap of 4.

## 7. What it cannot show

- **Not memory capacity:** the relief changes memory demand for one strategy, not memory capacity.
- **Not usefulness itself:** a positive A shows that a probe-measured history predicts foraging more when memory pays,
  in random brains. It does not show the history is used as memory: a filter that smooths input could predict fitness
  too.
- **Not an absent head start:** a null B under these graph counts does not show N2 has no head start. With 64 graphs
  per ensemble, a rank p near 0.05 needs N2 at the top three.
- **Not about evolved brains:** A and B are about generation 0. Stage C is gated on them.
- **One task, one interface:** Task N-mono and the pinned interface only.

## 8. Open questions for review

1. The receiving neurons for `food_fell`.
2. SH-route or SH-mirror, and whether 64 graphs each are enough.
3. A's statistic: partial Spearman, the history read-out (turn, forward, or both), and the smallest effect of
   interest.
4. B's statistic: the expected best of 32, or the top decile.
5. Whether Astra's frozen-champion check (controlled sensory-history replay on existing champions) should come
   alongside A, or after it.
6. The cap.
