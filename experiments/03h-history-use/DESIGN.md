# 03h: does the history random brains hold predict how well they forage? Design v3.2 (draft, for review)

**Status:** design v3.2, 2026-10-18. Not coded, not run.
- **Review rounds:**
  - round 1 reviewed v1 (`de22cc4`, D321-D322; run 20261018-152829);
  - round 2 reviewed v2 (`e0efdd8`; run 20261018-154121). Both said "revise" and accepted the task change and the
    merged points, except the cap (Fable).
- **v3 takes every round-2 finding** (§10; D323).
- **Round 3 reviewed v3** (`0ddf41f`; run 20261018-155410). Fable said "ready for code and the pilot's registration,
  with small fixes"; Astra said "revise", with one blocking point (B's inference). v3.1 takes every finding (§11;
  D324).
- **v3.1 was confirmed** (run 20261018-160748). Fable said "ready for code and the pilot's registration"; Astra said
  "revise" only for the power rule. v3.2 makes their fixes (§12; D325).
- **GPU:** any GPU work, step 0 and the pilot included, needs the owner's word.

## 1. The question

**The memory thread** (`ROADMAP.md`, "The thread worth following") says N2 starts with more capacity to hold recent
history, and that evolution then builds such memory into every graph.

**What the repository already shows:**
- **N2's random brains hold a past food level unusually strongly.** P4 is 0.931, 0.924 and 0.926 in 03, 03r and
  03mc, against ensemble means of 0.75-0.85. These are approximate reference-ensemble tests.
- **Selection builds turn-history dependence into champions** (02b, in the four task and group combinations it
  studied). 02b also states: "Whether it helps foraging is not tested".
- **No file relates a genome's history to its fitness.**

**Two questions, at generation 0:**
- **A, the link:** does the history a random genome holds predict its foraging score, within a graph? Is that
  association weaker when the need for memory is relieved than under a sham input?
- **B, N2's head start:** does N2's upper-tail advantage over the null graphs shrink when the relief is given,
  compared with the sham? Under the hypothesis, the null graphs gain more from the relief than N2 does. And does N2
  have a generation-0 advantage at all?

**Wordings, fixed now:**
- **A, positive** (Astra): "history predicts fitness positively under level, and its association is stronger under
  sham than under relief", in random brains, on this task, interface and probe. It is an association. It is not
  evidence that the history is used as memory, and not a mediation of N2's advantage.
- **A, null:** it closes this screening route. It does not show that useful history is absent.

**Stage C,** evolution, runs only on §6's gate, with its own pre-registration and the owner's word.

## 2. The task: 02's T1

The task is 02's T1, single-nose foraging (`wormwars/exp02/grid.py` `task_config(…, "T1")`, mapping M0), with 02's
T1 brain configuration (32 substeps). Single-strain padding is pinned off by `task_config`.

**The world** (Astra): one swarm of 20 weys sharing food, with crowding, hazards, energy costs and corpse pellets. A
genome is evaluated through the group's performance; its weys are interacting parts of one evaluation, not
replicates. Worlds are the resampling unit.

**The score** is T1's foraging score (`wormwars/evo/rollout.py` `foraging_score`): the swarm's surviving energy as a
fraction of its starting energy. It is not a count of targets.
- **It is graded at generation 0, measured** from 03's pilot (`experiments/03-generation0/pilot.json`; 16 SH graphs ×
  256 random genomes × 16 worlds). The numbers are from `development-records/t1_generation0.py`, whose output is
  `t1-generation0.json`:
  - the graph means are 0.865-0.911, with no zero scores;
  - the SD of genome means is 0.26;
  - **the crossed decomposition** (genome, world, residual) gives variance components of 0.067, 0.049 and 0.019. The
    world effect is shared by every genome, so it does not affect ranking;
  - **the ranking reliability of a genome's mean** is var_genome / (var_genome + var_residual / W): 0.98 at W = 16
    and 0.96 at W = 8.
  - Reliable fitness means do not by themselves make ρ or D precise: shared-world uncertainty stays in the inference
    (Astra).
- **Memory pays:**
  - 02's registered tripwire measured scripted M − K = +0.942 [+0.928, +0.956];
  - 02's exploration measured memory against graded kinesis at +0.98 (`experiments/02-screening/exploration/README.md`).

**The history probe's bank is already T1's** (Fable, Astra):
- 03 collected it from T1 generation-0 replays (`scripts/exp03.py` `cfg_for("T1")`);
- its food level is 0.2234 on both sides, with T1's own hazard and collision inputs;
- its values are already scaled signal values.

## 3. The manipulation

**The signal:** `food_fell`, injected into **ASKL and ASKR**.
- **Why ASK:** they are sensory neurons whose own channel, ally pheromone, has its sense scale at 0 in T1. Their
  pheromone input is zero; the neurons are not silent, and the field is still deposited (Astra).
- **Its amplitude:** 0.25 in injected-current units, about the bank's food current (0.2234), so its drive is
  comparable to the food channel's and far below the clamp of 5. A gain of 1.0 would have been 4.5 times the food
  scale (Fable).

**Its definition** (Fable, Astra): the bit is computed on the injected food current, after gain and clamp. That is the
observation the brain and `ScriptedBrain` receive.
- It is 1 on a tick where that current is strictly below its value on the previous tick, and 0 otherwise.
- It is 0 on the first tick, and per wey. Dead weys carry 0.
- It does not reset on hidden events, so it carries nothing beyond the observed level history.
- When the clamp binds, two clamped readings are equal and the bit is 0, exactly as `MemoryKinesis` would read them.

**Three conditions, with the same channel, neurons and amplitude:**
- **level:** the bit is 0 on every tick;
- **relief:** the bit is live;
- **sham:** a two-state Markov sequence, generated without observing food. Sham-driven actions can still come to
  correlate with food through the world (Astra).
  - **Its rates:** p̂01 = N01 / (N00 + N01) and p̂10 = N10 / (N10 + N11). They are counted from relief bits computed,
    but not injected, along level trajectories in the pilot's restricted part (§7), with these conventions:
    - over adjacent ticks of the same trajectory on which the wey is alive at both ends;
    - nothing across episode boundaries;
    - the forced-zero first tick is excluded as a transition's start.
    - **If a denominator is zero,** 03h stops for redesign.
  - **Its start:** the initial state is drawn from the chain's stationary distribution. Its occupancy is
    p̂01 / (p̂01 + p̂10), so it matches the relief bit's pooled occupancy and persistence only approximately (Astra).
  - **Its randomness:** keyed random streams per world and wey, not per strain or graph. Every genome and graph sees
    the same sham sequence for a given world and wey, which reduces variance in the paired contrasts (Fable).
- **What the sham matches, and what it does not** (Astra, Fable):
  - it approximately matches the relief bit's pooled occupancy and persistence on level trajectories;
  - it does not match each genome's drive (a stationary genome has no falls), the bit's statistics under relief
    trajectories, or the correlation between weys;
  - realised occupancy and transitions are reported per condition.
- **What a sham test can and cannot show:** it tests performance neutrality within the scripted families. It does not
  show that random stimulation could never help a policy.

**The routing control:** ASKL and ASKR are added to 03's routing cap (`constrained_neurons` in
`wormwars/exp03/samplers.py`), as a parameter, with a test of both chemical and gap counts and the weight cap.
- **N2's own values** are the caps: ASK's direct read-out count and weight.
- **The ensembles:** **SH-mirror-ASK**, the primary, and SH-route-ASK, built and tested but not run.
- **A covariate:** each graph's ASK direct read-out (`direct_readout`) is reported.

**Rule 7** (Fable): with the bit at 0, the interface variant injects nothing at ASK. Under level, T1 scores for the
same genomes and composition must equal the pinned interface's bitwise:
- on the CPU;
- on CUDA, in the same composition and inside `replay_mode()` (AGENTS.md rule 6; Fable, Astra).

## 4. The scripted gate

**The families** are nested, and each includes the settings that ignore the bit and the internal history:
- **memoryless:** `LevelKinesis` and `GradedKinesis`;
- **memoryless reading the bit:** an extension of `ScriptedBrain` to read the ASK current, with a test (Fable, Astra).
  At fall threshold 0, it reproduces exactly `MemoryKinesis`'s zero-threshold member. 02's tuned T1 winner had
  threshold 0 (Astra);
- **memory:**
  - `MemoryKinesis` (one tick, with its threshold grid);
  - **a slow-memory family** ported from 03a's KTS memory mechanism only, into `MemoryKinesis`'s policy (Astra). It
    does not take KTS's level-dependent turning or its collision avoidance:
    - each tick, it turns by `fall_turn` when the level is below m_{t-1} − `fall_threshold`;
    - it then updates m_t = m_{t-1} + (x_t − m_{t-1}) / T;
    - T is tuned in {1, 2, 5, 10, 20}, the threshold on `MemoryKinesis`'s grid;
    - at T = 1 it stores the current level directly (m_t = x_t), so it is exactly `MemoryKinesis`, including the
      threshold (Fable, Astra);
  - the union with `GradedKinesis` (Astra);
- **memory reading the bit:** the same, with the bit available. The policy turns when either the internal
  comparison or the bit says the level fell. Each source can be switched off by a tuned flag.

**The protocol** (Astra):
- each family is tuned on registered tuning worlds, with its choice among timescales frozen there;
- each is then scored once on registered check worlds, with every comparison paired by world.

**The criteria,** in T1's score:
- **level:** the lower bound of the paired 95% interval of (best memory − best memoryless) is ≥ 0.5, about half of
  02's measured +0.94 and +0.98;
- **relief:** the paired 90% interval of (best memory with the bit − best memoryless with the bit) lies inside ±0.3.
  That is two-sided equivalence at 5%.
  - The margin is about a third of the historical 0.94 gain, and 60% of the minimum accepted 0.5. It is a chosen
    screening margin, not an established equivalence tolerance (Astra).
  - Because the slow-memory family is included, this asks whether memory beyond one tick adds more than the margin
    once the bit is given. It is not an identity (Fable);
- **sham** (a sanity check, since a weight of zero on the bit is inside every family): the paired 90% interval of
  (best memoryless reading the sham − best memoryless) lies inside ±0.3 (Fable). A failure stops 03h for redesign,
  because tuning can select a worse policy even inside a nested family (Astra).
- **The recovered share** (Fable) is reported: (best memoryless with the bit − best memoryless) / (best memory − best
  memoryless), the share of memory's gain that the bit gives a memoryless controller.
- **If the level part fails,** 03h stops and is reported.
- **If the relief part fails** because slower memory beats the bit by more than 0.3, 03h stops for redesign: for
  example, a bit defined against a tuned average, under a new design round (Fable).

## 5. Graphs, genomes, worlds, measures

**Graphs:**
- N2;
- **SH-mirror-ASK, 64 graphs** (the primary; fixed at 64, because at 32 the rank floor 1/33 cannot pass Holm's 0.025);
- SH, 64 graphs (the secondary, run only if the pilot's timing leaves room under the cap).
- **Seeds** are outside every earlier range.
- **Failures:** a failed sampler is retried with the next seed; a failed calibration excludes the graph and draws the
  next seed. Every exclusion is reported.
- **Seeds:** graph, genome, sham and world seeds, and world-id ranges (tuning, check, selection, test, calibration,
  pilot), are all disjoint from one another and from every earlier range. They are listed in the pilot's registration
  and the pre-registration (Astra, Fable).
  - *Annotated 2026-10-19 (D328):* the sham has no root seed of its own. It is the world's keyed stream 0x03F under a
    bank's run seed, separated from the map's streams by its tag.
  - So each bank uses one run seed for every condition, genome and graph, and the sham sequence for a world and wey is
    then the same across them (Fable, Astra).

**Motor calibration:** once per graph under level, then frozen for every condition (Astra).

**Genomes:**
- G = 256 random genomes per graph, N2 included. The allocation is equal (Astra);
- the same genome objects are used for history and for every condition;
- genome seeds are disjoint from the calibration genomes.

**Fitness:**
- **the selection bank:** W = 16 worlds, shared across every genome, graph and condition, which gives a ranking
  reliability of 0.98 (§2);
- **the test bank:** W_t = 64 worlds, disjoint, used only for each graph's selected decile in B. B's inference is
  conditional (§6), so the genomes outside the decile need no test scores (Astra).

**History:** 03's `history()`, extended to return each history's read-outs, with a test (Fable).
- Its bank and parameters are frozen at 03's: a 100-tick warm-up, a 10-tick ramp, starts at 0.25 and 1.75 times the
  final level, measured at the final tick.
- It runs under level, with the bit at 0.

**The history measures, per genome:**
- **H,** the primary: |raw-turn final difference|, the per-genome numerator of P4;
- **S,** the covariate: |raw-turn steady contrast|;
- **H_dir,** the key secondary: |motor turn after the falling history| − |motor turn after the rising history|, at
  the final tick.

**The batch composition** (stated; Fable, Astra): fitness runs in chunks of 4 096 worlds, as 03 did, with 20 weys per
world. The selection and test banks run as separate rollouts. The actual chunks are recorded.

## 6. Readings (fixed in the pre-registration)

**A** (one claim, two conjunctive parts):
- **The statistic:** per graph and condition c, the partial Spearman ρ_c of H with fitness, given S.
  - It is the correlation of the residuals after regressing the ranks of H and of fitness on the ranks of S (with an
    intercept, ties at average ranks).
  - **Degenerate graphs:** a graph with constant fitness, constant H, or zero residual variance gets ρ_c = 0, is
    flagged, and stays in every average.
    - This is not conservative for A2 in every case: a constant relief score with a positive sham correlation creates
      a positive D (Astra).
    - So a flagged graph is reported with its components, and A2 is also reported without the flagged graphs. If the
      two disagree in sign, A2 is withheld as "undetermined".
- **A1:** the equal-weight mean of ρ_level over SH-mirror-ASK > 0.
- **A2:** the mean of D = ρ_sham − ρ_relief over SH-mirror-ASK > 0. "Meaningful" requires the lower bound of D's
  interval to exceed δ_A (Astra).
- **Inference** comes from crossed resampling, B = 10 000:
  - one shared resample of the selection worlds across graphs and conditions;
  - genomes resampled within each graph;
  - graphs resampled within the ensemble.
  - Each part's one-sided p is the bootstrap share at or below 0, plus one, over B + 1.
- **The claim's p** is max(p_A1, p_A2), and it enters Holm (Astra). If A2 is withheld as "undetermined", A fails
  Holm and the gate (Fable).
- **Reported:**
  - N2's ρ and D with intervals (N2 is one fixed connectome);
  - ρ_level − ρ_relief;
  - the top-against-bottom quartile difference of fitness by H, which describes the effect but is not a conversion of
    it (Astra);
  - H_dir's readings, worded in advance.

**B:**
- **The statistic:** T_{g,c} is the test-bank mean of graph g's selected decile under condition c.
  - The decile is selected separately per condition, on that condition's selection-bank scores (Fable).
  - It is the top 26 of 256, with ties broken by genome index (Astra).
- **The primary** (Fable): U_g = T_{g,sham} − T_{g,relief}.
  - **The direction** (Fable): under the hypothesis, the nulls gain more from the relief than N2, so their U is more
    negative and N2's U ranks high.
  - **The rank:** r counts the null graphs whose U is at or above N2's, with p = (1 + r) / 65. That is 03's formula
    (`wormwars/exp03/mc.py`), one-sided, p ≥ 1/65.
  - Only the formula is imported, not 03's effect-margin gate. The rank test is approximate (Astra).
- **The labels:**
  - **"Head start larger when memory is needed"** requires the rank p, and also N2's level advantage
    T_{N2,level} − mean T_{e,level} > 0 by its 95% interval. The interval conditions on N2's one draw of 256 genomes,
    and the label says so: "for this genome draw" (Fable);
  - **an interaction without an established initial advantage** is labelled as such.
- **The intervals are conditional** (Astra's first option):
  - each graph's selected decile is frozen, and the test-bank worlds are resampled, one shared resample across graphs
    and conditions;
  - graphs are resampled within the ensemble for ensemble means;
  - the intervals condition on the genome draws and on the selection bank, and say so;
  - reselection inference would need test scores for all 256 genomes, about 3.9 GPU-hours at W_t = 32.
- **Reported:**
  - both component advantages;
  - U computed against level (level − relief);
  - the expected best of 32 by order statistics: 01b's and 02's head-start statistic, Fable's round-1 secondary. It
    is computed on the selection bank, and is optimistic by selection, so it is descriptive (Astra).

**Multiplicity:** Holm at α = 0.05 over the two claims, A (with p = max of its parts) and B.

**The neural manipulation check,** reported but not gated: the mean within-graph shift of the selected decile's
test score, relief against sham.
- If it is not detected, the wording is "no improvement from the relief was detected in random brains at generation
  0". An adverse shift is reported as adverse (Astra).

**The gate to stage C:** A holds under Holm, or B's label "head start larger when memory is needed" holds under Holm.

**Outcome wordings,** fixed for every combination of A1, A2, B and the check.

## 7. Order of work

1. **The code and its tests** (CPU), reviewed by both:
   - the bit and the sham;
   - the ASK cap;
   - the `ScriptedBrain` extension and the slow-memory family;
   - the `history()` extension;
   - rule 7's check.
2. **Step 0, exploratory and disclosed** (about a minute of GPU, the owner's word). It may precede the pilot's
   registration.
   - **The recipe** (Astra; `scripts/exp03.py`):
     - graphs `pilotSH101` to `pilotSH116`, rebuilt with their integer seeds and 20 passes;
     - genomes from `genome_seed(name, "")`, without `+1`. The `+1` seed is the separate probe population;
     - one CUDA `Genome.random(…, 256, …)` call per graph, with 03's configuration, keeping the genome order;
     - a narrow helper, not `measure_graph()`, which recalibrates.
   - **The verification first** (Fable): replay T1-M0 for at least one pilot graph on the current engine, and compare
     with `pilot.json` at T1's declared equivalence tolerance. If it fails, step 0 is dropped and reported.
   - **Then:** H and S are measured on the same genomes, and related to the committed T1-M0 fitness, under level only.
   - **What it gives:** the spread of ρ_level across SH graphs. It estimates neither D's variance nor
     SH-mirror-ASK's (Astra). It sets nothing by itself.
   - *Annotated 2026-10-19, before step 0 ran (D328; the code review, round 2, Fable):* a last-bit difference in a
     400-tick fitness replay cannot tell a wrong recipe from 03's own nondeterminism (03 ran in the default mode).
     So the verification has two checks on `pilotSH101`:
     - (a) the fitness replay;
     - (b) a world-free check: `history()` on 03's 2 048-genome probe population (seed + 1), against the per-genome
       history committed in `pilot.json`.

     Each check runs in 03's default mode and inside `replay_mode()`, each mode in its own process, and each
     comparison is bit-equality. **If any check is bit-equal in either mode,** step 0 proceeds. **Otherwise** it is
     dropped, and §7.7's s_graph uses the pilot's estimate alone.
3. **The pilot's registration,** reviewed by both, bound and pushed before any registered gate or pilot
   measurement (Fable, Astra). It covers steps 4-7, and fixes:
   - the controller grids, the world counts and ranges, and the interval methods;
   - the pilot's size: 3 graphs, fixed in advance;
   - every adaptation rule below, in numbers.
4. **The scripted gate, level and relief parts.**
5. **The pilot's restricted part,** on the 3 SH-mirror-ASK pilot graphs (pilot seeds, never N2): level trajectories
   only. It gives the sham's rates, and the T1 timing at the formal composition.
6. **The sham frozen, then the gate's sham part.**
7. **The rest of the pilot:** all three conditions on the same 3 graphs. Its rules, fixed in its registration:
   - **W:** stays at 16 unless the crossed-decomposition ranking reliability (§2's estimator, under level, averaged over
     the 3 graphs) falls below 0.85. In that case W becomes 32, and the budget is re-checked against the cap;
   - **G:** stays at 256;
   - **detectability:**
     - **δ_A is fixed in the pilot's registration,** at 0.05 in ρ, before the pilot is seen (Fable);
     - the projected SE of the 64-graph ensemble-mean D is SE = sqrt(s_graph² / 64 + s_shared²). Here s_graph is the
       between-graph SD of D over the pilot graphs, and s_shared is the SD of the pilot's ensemble-mean D over
       shared-world bootstrap replicates. The shared-world part does not shrink with the graph count (Fable, Astra);
     - the power of A2's one-sided test at α = 0.025 (Holm's first threshold), for a mean D of 2δ_A, is
       1 − Φ(1.96 − 2δ_A / SE);
     - if it is below 0.8, 03h stops for redesign;
     - s_graph rests on three graphs (two degrees of freedom), so its value enters as the larger of the pilot's
       estimate and step 0's between-graph SD of ρ_level; the shared-world term is estimated from 16 worlds
       (Fable);
   - **the manipulation** (Fable): the selected decile's shift, relief against sham, on the pilot graphs, and the
     bit's effect on the turn read-out under the history bank. If neither moves beyond its interval, the amplitude
     doubles to 0.5 once, by this rule, and the pilot's three-condition part reruns. If neither moves at 0.5, 03h
     stops for redesign.
8. **The pre-registration,** with everything fixed, reviewed by both, bound and pushed. Then the formal run, with the
   owner's word.

## 8. Budget

**Per graph:** 3 conditions × (256 × 16 + 26 × 64) = 17 280 episodes.

**At T1's measured 171 per second** (03's fitness stage: 11 264 episodes in 65.9 s per graph; Fable):

| Item | GPU-hours |
|---|---|
| SH-mirror-ASK, 64 graphs, and N2 | 1.82 |
| Calibration (11.4 s per graph) | 0.21 |
| History (256 genomes per graph) | about 0.1 |
| **Primary total** | **about 2.2** |
| SH, 64 graphs (if the timing allows) | about 2.1 more |
| Step 0 | under 0.05 |
| Pilot | under 0.5 |
| Scripted gate | about 0.1 |

- **The rate:** 171 per second predates the T1 throughput work, so the budget is probably conservative; the pilot
  measures it (Fable). `t1-generation0.json` gives 172.9 per second, averaged over 03's 16 pilot graphs.
- **CPU costs** are not counted as GPU-hours: the SH-mirror-ASK sampler, and the crossed bootstrap (10 000 resamples
  over 65 graphs × 256 genomes × 3 conditions). The bootstrap is vectorised over resamples, and its time is reported.
- **The cap:** 6 GPU-hours, the ceiling (accepted by both as a ceiling), set from the pilot's timing.
- **Cut order:** SH first, then W_t from 64 to 32. The primary ensemble stays at 64 graphs, and W stays at the
  pilot-selected value (16, or 32 by §7.7's rule) (Fable, Astra).
- **Incomplete runs:** a run stopped by the cap is reported as incomplete. It never becomes a smaller successful
  experiment.

## 9. What it cannot show

- **Not memory capacity:** the relief changes memory demand for one strategy, not memory capacity.
- **Not usefulness as memory:** A is an association in random brains, not use of history as memory.
- **Not a missing head start:** a null B does not show that N2 has none.
  - For B to pass Holm's first threshold of 0.025 on its own, N2 must rank first of 65 (2/65 = 0.031 fails).
  - Once A has passed, at most two null graphs may rank above N2 (3/65 = 0.046) (Fable).
- **Not about evolved brains:** stage C is gated.
- **One configuration:** one task (T1, swarm performance), one interface variant (the ASK channel; its hash differs
  from the pinned one), one probe bank.

## 10. Changes from v2 (round 2: run 20261018-154121)

**Taken:**
- **The budget** at T1's measured 171 per second, not Task N's 892, re-sized with W = 16 from 03's measured
  reliability. The test bank is used only for the selected decile, and SH is optional (Fable 1).
- **The relief gate is no longer an identity:** a slow-memory family is ported from 03a's KTS, and `GradedKinesis` is
  in the union (Fable 2, Astra 4).
- **The units:** T1's score is the surviving energy fraction, and the thresholds are restated in it (Fable 3,
  Astra 2).
- **B's baseline is the sham** (Fable 4).
- **The order:** the gate, the pilot and the sham are ordered, and the sham estimator is specified (Fable 5,
  Astra 5).
- **The bit** is defined after the clamp (Fable 6, Astra 4).
- **The cut order** keeps the primary ensemble at 64 graphs (Fable 7, Astra 7).
- **Rule 7's check** (Fable 8).
- **The bank's provenance** is corrected: it is T1's (Fable 9, Astra 3).
- **03's T1 data** sets W and the reliability (Fable 10).
- **`ScriptedBrain`'s extension** (Fable 11).
- **The bit's amplitude,** with its reason (Fable 12).
- **The composition and padding** (Fable 13, Astra 8).
- **Wordings:**
  - A's conclusion;
  - "meaningful" needs an interval bound;
  - the manipulation check reads "no improvement was detected" (Astra 6).
- **The statistical contract** (Astra 7, Fable 14):
  - equal weights;
  - the bootstrap p;
  - max(p_A1, p_A2) into Holm;
  - degenerate graphs set to 0;
  - B's selected count, interval and selection resampling;
  - the rank formula only;
  - equal genome allocation;
  - the failure rules.
- **Added:** step 0, exploratory, on 03's committed T1 fitness.

## 11. Changes from v3 (round 3: run 20261018-155410)

**Taken:**
- **B's inference is conditional:** the selected deciles are frozen, and the test worlds and graphs are resampled.
  The test bank therefore needs only the deciles (Astra 1, the blocking point). The alternative is priced in §6.
- **B's one-sided direction and counting rule** are stated (Fable 1).
- **Step 0** (Fable 2, Astra 5):
  - its regeneration recipe;
  - a verification replay against `pilot.json` first;
  - what it can and cannot estimate.
- **The pilot's registration** is a step of its own, with numeric rules (Fable 3, 5, 6; Astra 6):
  - for W, the estimator and the action;
  - for detectability, the power formula with shared-world uncertainty;
  - for the manipulation, a decile shift and a turn response, with one registered amplitude change;
  - a fixed pilot size of 3 graphs.
- **The derived numbers are committed:** `development-records/t1_generation0.py` and its output (Fable 4, Astra 2).
  - It uses the crossed decomposition: ranking reliability 0.98 at W = 16 and 0.96 at 8, not v3's 0.94 and 0.90 from
    a simple ratio.
  - The graph means' minimum is 0.865, and the rate is 172.9 per second, over a five-cell mix.
- **The sham's estimator conventions** (Fable 7, Astra 4):
  - alive at both ends;
  - nothing across episode boundaries;
  - zero denominators;
  - "approximately matches";
  - "generated without observing food";
  - keyed per world and wey.
- **The gate:**
  - the slow-memory family's update and decision rules, and how the bit and the internal comparison combine;
  - the sham criterion as an interval, and a failure stops for redesign;
  - the recovered share;
  - a relief failure stops for redesign;
  - the margin's reference to the historical 0.94 (Astra 3, Fable 8, 9).
- **Degenerate graphs:** zero is not conservative for A2. A sensitivity reading without flagged graphs is added
  (Astra 6).
- **The best of 32** is explained, and kept descriptive (Fable 10, Astra 1).
- **Holm's attainable ranks** (Fable 11), and the CPU costs (Fable 12).
- **The seed and world-id disjointness rule** (Astra 7, Fable 14).

**Noted** (Astra): the frozen-champion check stays a separate exploratory item outside 03h (§9 of v2's merge). It is
not in this design, and it does not block 03h.

## 12. Changes from v3.1 (the confirmation: run 20261018-160748)

- **The power rule's SE** keeps the shared-world variance unshrunk, SE = sqrt(s_graph² / 64 + s_shared²) (Fable 1,
  Astra 1).
- **δ_A is fixed at 0.05** in the pilot's registration (Fable 2).
- **s_graph** takes the larger of the pilot's three-graph estimate and step 0's spread (Fable 3).
- **An "undetermined" A2** fails A (Fable 4).
- **B's decile** is selected per condition (Fable 5).
- **The label "head start"** says "for this genome draw" (Fable).
- **The budget's cut order** keeps the pilot-selected W (Astra 2).
- **Rule 7's CUDA check** runs inside `replay_mode()` (Fable 6, Astra 3).
