# E3b-2 plan: where E3b-1's gain comes from (exploratory) — draft 2

**Status:** draft 2, 2026-10-04. Nothing has run.
- **Why:** the owner chose this step after E3b-1 (D193).
- **Kind:** exploratory. Every analysis is fixed here before it runs, and none is a registered test. The
  results will be reported as descriptions with intervals, not as verdicts.
- **Draft 1** (cdc62e0) was reviewed by both reviewers. Both said "go with changes"
  (`docs/reviews/20261004-E3b-2-plan/`, D194). This draft takes every change; §10 maps them. Where the two
  differ, the ruling is stated.

## 1. The question

**What do E3b-1's tuned colonies use to beat the frozen seed, and does the engineered selector still
switch in the maze?** E3b-1's gate read "better": +0.225 of the seed's mean on the test mazes, with T-A at
+0.069 and T-F at +0.381. Its probes found that no tuned champion still meets the seed's comparator
criteria. The resting turn command is above the seed's +0.4 in every final T champion, and at +1 in both
latch states for T-F finals 2, 3 and 7.

**Why it comes first:** the roadmap's next steps are E3's assembly comparison and E4 (information crossing
between the modules). E3b-2 cannot establish the value of modular assembly or of information transfer. It
can say whether those experiments have a suitable starting organism.

**The frame:**
- the organism is a hand-built circuit on a silent worm, so nothing here is about worm behaviour;
- stereo sensing is a game-design choice;
- E3b-2 evolves nothing.

## 2. Inputs (fixed, hash-checked at load; read-only)

- **The organisms:**
  - E3b-1's 16 final T champions: T-A runs 0-7 at generation index 124, T-F runs 0-7 at generation index
    299. `champions.json`'s `index` is the selected population member;
  - N's 4 champions, for C, D and E only;
  - the frozen seed E + W2.
  - Each champion's genome (local, `runs/e3b1/genomes`) is checked against its sha256 in E3b-1's
    `champions.json`.
- **Not used:** R's champions, and T-F's champions at index 124.
- **The task:** E3b-1's configuration exactly: c = 5, H = 2 400, colonies of 8 on up to 4 spawns, the trail
  constants μ 0.01, λ 0.02, δ 0.05, d₀ 1.142, maze run seed 1 180 000, episode 0. Amendment 1's redraw rule
  applies.
- **The fixed-input hashes:**
  - E3b-1's `champions.json`, `evaluate.json` and `PREREGISTRATION.md`;
  - E3b-0's `report.json` (the seed's own probe readings);
  - E4s-0's `module.json`.
- **E3b-1's records are inputs only.** E3b-2 has its own experiment folder
  (`experiments/E3-ab-organism/E3b-2/`), run folder (`runs/e3b2/`), compute ledger, markers and chunk paths.
  - The runner does not import E3b-1's runner, which configures E2's stage frame for E3b-1's folders on
    import.
  - A test checks that every output path lies outside E3b-0's and E3b-1's folders.

## 3. The mazes

- **A fresh block:** ids 7000-7255 (256 mazes), at maze run seed 1 180 000.
  - It lies outside every block of E3b-0 and E3b-1: their test, validation, learning, calibration, training,
    projection and smoke ids, and the audit trace's 9900-9902. No organism has played it.
  - A pre-flight lists its feasibility and any redraws before the first stage.
- **Smoke ids:** 9800-9899, never results.
- **Not used:** E3b-1's test block and every other registered block.
- **The outcomes,** all as colony means per maze, each reported for every variant:
  - visits per wey;
  - the later-leg rate;
  - the unvisited share;
  - the round-trip share;
  - median legs.

**A variant's gain** in condition a (shared trails or none) is
v_a = (its mean visits in a − the seed's mean visits in a) / the seed's mean visits *with shared trails*.
The denominator is the same for both conditions, so allocations under "shared" and "none" can be
subtracted.

## 4. The parameter groups

Tuning in E3b-1 could change 65 scalars: 47 chemical edges, 9 τ and 9 biases (`tuning.scales`). The W2
reflex, the relays' τ and bias, the worm block (the carrier's turn and forward biases) and the gap junctions
were frozen.

Frozen does not mean irrelevant to the gain. Tuned comparator outputs can change how the unchanged reflex and
carrier act on the motors, and C's reflex and scent diagnostics address that.

The groups are **parameter groups defined from the seed's design,** not isolated functions:
- a comparator's bias sets both its gating and its resting output (× 16 output edges, a constant turn push);
- a comparator's τ affects its responses to the noses and to q.

A large "gating" allocation would not by itself show more use of the selector.

**The functional partition (4 groups, 65 scalars):**

| Group | Parameters | Scalars |
|---|---|---|
| **sensing** | the 8 nose → comparator edges, the 4 nose neurons' τ and bias, the 4 comparators' τ | 20 |
| **gating** | the 4 comparators' biases, the 4 latch → comparator edges | 8 |
| **output** | the 32 comparator → turn-neuron edges | 32 |
| **latch** | the latch's self-edge, the 2 relay → latch edges, the latch's τ and bias | 5 |

**The side partition (3 groups):**

| Group | Parameters | Scalars |
|---|---|---|
| **module A** | A's 4 nose → comparator edges, its 16 output edges, its 4 neurons' τ and bias | 28 |
| **module B** | the same, for B | 28 |
| **selector** | the latch's self-edge, the relay → latch edges, the latch's τ and bias, the 4 latch → comparator edges | 9 |

The side partition puts the comparator biases inside A and B, where the functional partition puts them in
gating. So its "selector" and the functional "gating" answer different questions; they are not two estimates
of one quantity.

A test checks that each partition covers every mutable scalar exactly once, and no frozen one.

## 5. The analyses

### A. The functional attribution, under shared trails and under none

- **The hybrids:** for each of the 16 T champions, all 2⁴ = 16 hybrids. Each takes every group's values from
  either the champion or the seed. The all-seed hybrid is the seed and the all-champion hybrid is the
  champion, each checked bitwise.
- **Played:** every hybrid, with shared trails and with none.
- **Per champion and condition:**
  - **the endpoints, reported first:**
    - each group's **reversion effect** (the champion with that group set back to the seed's values);
    - each group's **transplant effect** (the seed given that group's champion values);
  - **the Shapley allocation** of each group: its average marginal contribution over the 24 orders, in units
    of the seed's shared mean and in visits per wey. It is signed, can be negative, and can exceed the net
    gain;
  - **the interaction terms** (Harsanyi dividends): the largest ones first, then the full table.
- **The trail dependence, decomposed:** under this intervention scheme, the difference between a group's
  allocation under "shared" and under "none" is that group's part in the change of trail dependence.
  - It addresses why T-F's gain came with more trail dependence and T-A's did not.
  - "None" removes the own and the peers' trails together, so this does not isolate peer effects.
- **Every hybrid's absolute visits** are reported beside the seed's and W2 alone's (C5). A hybrid below W2
  alone is flagged wherever its allocation is discussed.
- **Summaries:**
  - per champion;
  - each schedule's mean, with a two-sided 95% t interval over its runs, and a maze-paired bootstrap interval
    (the mazes resampled jointly across every variant and champion, 10 000 resamples, seed 0);
  - schedule-level shares only, as the sum of allocations over the sum of gains;
  - no per-champion shares for T-A, whose gains (+0.03 to +0.13 on the test block) are near the per-variant
    noise.

**The wording:**
- "Under the specified seed–champion substitutions, group X's Shapley allocation was … visits per wey (… of
  the seed's shared mean)."
- Allocations are exact for this baseline, partition and table of hybrid performance. They are not the
  route evolution took, nor unique contributions.

### B. The side attribution, under shared trails

The same over the side partition, with 2³ = 8 hybrids per champion, shared trails only.

### C. Lesions and diagnostics (shared trails and none)

Applied to every T champion, N's 4 champions and the seed.

1. **Latch clamped at its own A state,** and separately **at its own B state.**
   - Each organism's two stable latch states come from its own q self-weight and bias (`latch.roots`).
   - q is clamped there (`Brain.clamp`) from the first tick, its state initialised to the clamped value.
   - A test checks that q stays at the value for the horizon.
   - Both conditions are reported; neither is chosen as "the" lesion.
   - With everything else at the organism's own values, this is the cleanest "the selector does not switch"
     test.
2. **Visit input disconnected:** the 2 relay → latch edges at 0, so q follows its own dynamics from 0. This is
   not a frozen latch:
   - for the seed (q bias 0) q stays at its unstable point 0, which closes both comparators;
   - for champions, q drifts to the state their bias selects.

   It is reported under that name, as a diagnostic.
3. **Gate cut:** the 4 latch → comparator edges at 0, the comparators' tuned biases kept. Its meaning differs
   by organism:
   - for the seed it closes both modules;
   - for a champion whose comparator biases drifted toward 0 it leaves both open.

   It is read with E's effective comparator biases.
4. **Scent removed:** the interface gains of the 4 A/B nose channels (`a_left`, `a_right`, `b_left`,
   `b_right`) at 0. The nose neurons keep their biases and τ, and the wall sensing and latch inputs stay.
   - This tests whether scent-driven modulation matters beyond the circuit's tonic output.
   - The one interface change, applied to a whole chunk, is checked by a test.
5. **Reflex held at rest:** W2's two neurons clamped at their resting state, v = −0.5 (their bias; they have
   no other inputs). This removes the wall response and keeps the resting push the carrier compensates.
   Zeroing W2's outputs would change the resting turn as well, so it is not used.
6. **Outputs silenced:**
   - **A's outputs:** A's 16 output edges at 0;
   - **B's outputs:** B's 16 output edges at 0;
   - **both:** all 32 at 0. This disconnects every tuned parameter from the motors, leaving W2 and the
     carrier. It is one organism for all, run once as the **W2-alone reference**. A CPU test checks that every
     champion with both outputs silenced is bitwise the seed with both silenced, on smoke mazes.

**Reported:** each lesion's cost, (lesioned − intact) / the seed's shared mean, per organism, by schedule and
for the seed, for every outcome in §3.

### D. Does the latch switch in the maze?

A recorder runs with shared trails on the 16 T champions, N's 4 and the seed, all intact.

**The data:** every tick, each wey's q (decoded through the strain assignment into world and wey order) and
the goal in force when q was computed. The goal switches after the move, in the same tick; on a visit tick
the recorder uses the goal from before the switch.

**The organism's coding:**
- the threshold is the organism's own unstable middle root (`latch.roots`), not 0;
- **"undecided"** is the middle third of the interval between its two stable states. As a sensitivity
  reading, the middle half is reported too;
- **the intended coding** follows from its relay → latch signs: an A visit drives q toward the B state if
  RA → Q < 0.

**The measures:**
- **agreement by goal:** the share of decided ticks matching the goal under the intended coding, for goal A
  and goal B separately, and their equal-weight mean. The opposite coding is computed with its own
  denominator;
- **switching after a confirmed visit,** in both directions:
  - the share of legs in which q crosses the threshold toward the new goal before the next visit;
  - the latency in ticks from the visit to the crossing;
  - the seed is the reference, since the relays read the position after the previous move and q needs
    ticks to cross;
- **the denominators:** eligible weys, decided ticks, undecided ticks, goal occupancy, and the number of
  transitions in each direction, including organisms with none;
- **the uncertainty** is over mazes (colonies), not ticks.

A stuck latch can score high agreement: a wey that visits A once and then seeks B for ever with q low agrees
on almost every tick. Agreement is therefore read only beside switching.

**Strong evidence of useful selection** would be both:
- high agreement with switching after visits;
- harm from both clamps (C1).

Either alone is weaker.

**Recorder off and on:** a test checks that the recorder changes nothing in the simulation, bitwise on the
CPU.

### E. Genome descriptives (no simulation)

For each champion and the seed:
- **the latch:** its relay → latch edge signs, its two stable states and its unstable root;
- **the gate edges;**
- **each comparator's effective bias** at each latch state: bias + gate weight × tanh(q state);
- **the resting turn command** at each latch state, computed from the genome. It is checked against E3b-1's
  probe values for the champions and E3b-0's for the seed.

### F. Replication on fresh mazes

The 16 intact champions' gains on this block (from A), beside their E3b-1 test-block d: the per-champion
pairs, their correlation, and each schedule's mean. Descriptive.

## 6. How the result would bear on the next step (written before the run; not binding)

**If the selector is not in use**, both E3's assembly comparison and E4 lose their starting premise for this
organism. That would show as:
- the selector's side allocation (B) and the latch allocation (A) both small;
- both clamps (C1) costing little;
- the latch rarely switching after visits (D).

The next step would then be a redesigned starting organism, or stronger controls, before either experiment.

**If the clamps cost much and the latch switches after visits,** the tuned organisms still use dynamic
selection. E3's assembly comparison and E4 keep their premise.

**Mixed outcomes are reported as mixed.** One example: the gain carried mostly by output edges and tonic
steering (C4, C5, E), while the latch still switches but matters little.

An assembly comparison can itself test the value of modular structure; it does not require assuming it.
Which step follows is the owner's decision, with both reviewers.

## 7. Compute and admission

**The projection,** from E3b-1's timed chunk of 16 organisms × 256 mazes (148.5 s, GPU):

| Analysis | Variants | Chunks |
|---|---|---|
| A | 256 hybrids × 2 conditions | 32 |
| B | 128 hybrids | 8 |
| C | (16 + 4 + 1 organisms) × 8 lesioned variants (two clamps, the input cut, the gate cut, scent, reflex, A's and B's outputs) × 2 conditions, plus the W2 reference | about 21 |
| D | 21 organisms with the recorder | 2 |
| F | shared with A | |

That is about 63 chunks, about 2.6 GPU-hours.

**A GPU benchmark** (`project`) times, on smoke mazes:
- a plain chunk;
- a clamped chunk;
- a chunk with the recorder;
- the saving.

The plan is admitted if the hours spent plus the projected remaining work, × 1.25, is at most the cap.

**The cap:** 5 GPU-hours, counted through `wormwars.accounting`, failed attempts included.

**If the projection exceeds the cap, the drop order:**
1. N's champions;
2. B, the side attribution;
3. C's "none" condition.

The ruling: Fable would drop B last and Astra first. B goes second because A's shared-and-none attribution,
C's clamps and D answer the selector question more directly than B's selector allocation.

## 8. How it runs

- **A runner, `scripts/e3b2.py`,** with:
  - stages `project`, `attribution` (A, B and F), `lesions` (C), `latch` (D) and `report` (E and the
    summaries);
  - E2's stage frame, configured for E3b-2's own folders; each stage once, with one rerun after a crash or
    a kill.
- **Each stage:**
  - checks its fixed inputs and the champions' hashes;
  - runs the maze pre-flight;
  - saves per-maze arrays as each chunk completes, and resumes at the first incomplete chunk;
  - on resume, validates a chunk's full specification: its maze ids, configuration, condition, every
    organism's genome and intervention identity, and its batch composition.
- **Fixed batch compositions:**
  - each hybrid chunk holds one champion's 16 hybrids;
  - the seed is the all-seed hybrid in each chunk, so its 16 score vectors, in one composition, must be
    bitwise equal. That is a free exactness check, and a mismatch is reported.
- **Tests first** (rule 9), each seen failing:
  - each partition covers every mutable scalar exactly once;
  - the endpoint hybrids are bitwise the seed and the champion;
  - each lesion changes exactly its parameters, or its interface gains or clamps;
  - the latch clamp holds;
  - with both outputs silenced, every organism behaves as the seed with both silenced (CPU);
  - **the Shapley and dividend calculator** on hand-computed cases: additive, a dummy group, a pure pair
    interaction and a higher-order interaction, plus the hybrid table reconstructed from the dividends;
  - the recorder:
    - decodes several weys and strains with different goals;
    - takes the pre-switch goal on visit ticks;
    - gives the per-goal agreement, switching and latency on scripted cases;
    - changes nothing in the simulation (recorder off against on);
  - the fresh block is disjoint from every earlier block;
  - every output path lies outside E3b-0's and E3b-1's folders;
  - the hash check refuses a changed genome;
  - a smoke run of every stage.
- **The reviews:**
  - both reviewers review the code before the GPU run, and this draft's changes with it;
  - the results are reviewed by both before publication.

## 9. What would be reported, and how

- **Every number is descriptive.** There is no gate, no "better" or "worse", and no p-value used as a
  verdict.
- **The schedules are reported separately and prominently.**
- **The intervals are conditional on this maze block,** apart from the maze-paired bootstrap.
- **The attribution wording** is that of §5A. Reversion, transplant and Shapley answer different questions:
  - reversion: whether the champion benefits from keeping the group's tuned values;
  - transplant: whether those values help in the seed;
  - Shapley: the average over the substitutions.

  None of them measures whether a component is necessary or sufficient for the behaviour.
- **Not claimed:**
  - that a group with a small allocation is unused;
  - any mechanism beyond what C and D measure directly;
  - any statement about E3's assembly comparison or E4 beyond §6's reading.

## 10. Changes from draft 1 (the reviews, D194)

| Point | From | Change |
|---|---|---|
| "Latch frozen" by the relay cut does not hold q: the seed stays at its unstable 0, and champions drift by their bias | both | Two clamps at each organism's own A and B states (C1); the relay cut kept as a named diagnostic (C2) |
| A scent lesion, to separate stereo use from tonic steering | both (Fable: nose edges; Astra: scent inputs) | C4, scent inputs at 0, keeping the nose neurons' tonic activity |
| Frozen is not irrelevant; the reflex's wall response | Astra | C5, the reflex held at rest |
| Lesion 5 is one organism | Fable | The W2-alone reference, run once, with a CPU equivalence test |
| The recorder: sign(q), the undecided band, timing, per-goal agreement, the stuck-latch trap, switching latency, mapping | both | §5D rewritten |
| "Share of the gain" wording; per-champion shares on small gains; weak calculator tests | both | Signed allocations, endpoints first, schedule-level shares only, hand-computed tests |
| Attribution under "none" decomposes trail dependence | Astra | A runs under both conditions |
| Outcomes beyond visits | both | §3's five outcomes for every variant |
| Hybrids off the evolutionary path | both | Absolute scores beside W2 alone; hybrids below it flagged |
| N's champions | Fable (Astra optional) | In C, D and E; not in the attribution |
| Genome descriptives; the effective comparator bias | Fable | §5E |
| A non-binding reading for the next step | both | §6 |
| Output isolation from E3b-1; resume validates the full specification | Astra | §2, §8 |
| Smoke ids overlapped the projection ids | Fable | 9800-9899 |
| "Index 124" meant the population member | Astra | Generation index, stated |
| The seed's probe readings are in E3b-0's report | Astra | Added to the fixed inputs |
| A GPU benchmark, the recorder overhead, admission with a reserve | Astra | §7 |
| The drop order | Fable and Astra differ | The ruling in §7 |
| The seed in every hybrid chunk as an exactness check | Fable | §8 |
