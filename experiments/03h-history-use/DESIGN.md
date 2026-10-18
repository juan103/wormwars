# 03h: does the history random brains hold predict how well they forage? Design v3 (draft, for review)

**Status:** design v3, 2026-10-18. Not coded, not run.
- **Review rounds:**
  - round 1 reviewed v1 (`de22cc4`, D321-D322; run 20261018-152829);
  - round 2 reviewed v2 (`e0efdd8`; run 20261018-154121). Both said "revise" and accepted the task change and the
    merged points, except the cap (Fable).
- **v3 takes every round-2 finding** (§10; D323).
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
- **B, N2's head start:** does N2's generation-0 upper tail lose more to the relief than the null graphs' do, compared
  with the sham? Does N2 have a generation-0 advantage at all?

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
- **It is graded at generation 0, measured** (03's pilot, `experiments/03-generation0/pilot.json`; 16 SH graphs ×
  256 random genomes × 16 worlds):
  - the mean is 0.87-0.91, with no zeros;
  - the SD of genome means is 0.26, and the per-world SD within a genome is 0.25;
  - so 16 worlds give a genome-mean reliability of 0.94, and 8 give 0.90.
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
- **sham:** a two-state Markov sequence, independent of the food trend.
  - **Its rates:** its off-to-on and on-to-off transition probabilities are the pooled maximum-likelihood estimates
    from relief bits computed, but not injected, along level trajectories in the pilot's restricted part (§7), over
    every live wey and tick.
  - **Its start:** the initial state is drawn from the chain's stationary distribution.
  - **Its randomness:** keyed random streams per world and wey.
- **What the sham matches, and what it does not** (Astra, Fable):
  - it matches the relief bit's pooled rate and persistence on level trajectories;
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
same genomes and composition must equal the pinned interface's bitwise, on the CPU, and on CUDA in the same
composition.

## 4. The scripted gate

**The families** are nested, and each includes the settings that ignore the bit and the internal history:
- **memoryless:** `LevelKinesis` and `GradedKinesis`;
- **memoryless reading the bit:** an extension of `ScriptedBrain` to read the ASK current, with a test (Fable, Astra).
  At fall threshold 0, it reproduces exactly `MemoryKinesis`'s zero-threshold member. 02's tuned T1 winner had
  threshold 0 (Astra);
- **memory:**
  - `MemoryKinesis` (one tick, with its threshold grid);
  - a slow-memory family ported from 03a's KTS (`wormwars/e03a/probe.py`), which compares the level with an
    exponential average over T ticks, T tuned in {1, 2, 5, 10, 20}. T = 1 recovers `MemoryKinesis` (Fable);
  - the union with `GradedKinesis` (Astra);
- **memory reading the bit:** the same, with the bit available.

**The protocol** (Astra):
- each family is tuned on registered tuning worlds, with its choice among timescales frozen there;
- each is then scored once on registered check worlds, with every comparison paired by world.

**The criteria,** in T1's score:
- **level:** the lower bound of the paired 95% interval of (best memory − best memoryless) is ≥ 0.5, about half of
  02's measured +0.94 and +0.98;
- **relief:** the paired 90% interval of (best memory with the bit − best memoryless with the bit) lies inside ±0.3,
  a third of the level gain. That is two-sided equivalence at 5%.
  - Because the slow-memory family is included, this asks whether memory beyond one tick adds more than the margin
    once the bit is given. It is not an identity (Fable);
- **sham** (a sanity check, since a weight of zero on the bit is inside every family): the best memoryless controller
  reading the sham is within ±0.3 of the best memoryless controller.
- **If either of the first two fails,** 03h stops and is reported.

## 5. Graphs, genomes, worlds, measures

**Graphs:**
- N2;
- **SH-mirror-ASK, 64 graphs** (the primary; fixed at 64, because at 32 the rank floor 1/33 cannot pass Holm's 0.025);
- SH, 64 graphs (the secondary, run only if the pilot's timing leaves room under the cap).
- **Seeds** are outside every earlier range.
- **Failures:** a failed sampler is retried with the next seed; a failed calibration excludes the graph and draws the
  next seed. Every exclusion is reported.

**Motor calibration:** once per graph under level, then frozen for every condition (Astra).

**Genomes:**
- G = 256 random genomes per graph, N2 included. The allocation is equal (Astra);
- the same genome objects are used for history and for every condition;
- genome seeds are disjoint from the calibration genomes.

**Fitness:**
- **the selection bank:** W = 16 worlds, shared across every genome, graph and condition, which gives a reliability
  of 0.94 (§2);
- **the test bank:** W_t = 64 worlds, disjoint, used only for each graph's selected decile in B.

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
    flagged, and stays in every average (conservative; Astra).
- **A1:** the equal-weight mean of ρ_level over SH-mirror-ASK > 0.
- **A2:** the mean of D = ρ_sham − ρ_relief over SH-mirror-ASK > 0. "Meaningful" requires the lower bound of D's
  interval to exceed δ_A (Astra).
- **Inference** comes from crossed resampling, B = 10 000:
  - one shared resample of the selection worlds across graphs and conditions;
  - genomes resampled within each graph;
  - graphs resampled within the ensemble.
  - Each part's one-sided p is the bootstrap share at or below 0, plus one, over B + 1.
- **The claim's p** is max(p_A1, p_A2), and it enters Holm (Astra).
- **Reported:**
  - N2's ρ and D with intervals (N2 is one fixed connectome);
  - ρ_level − ρ_relief;
  - the top-against-bottom quartile difference of fitness by H, which describes the effect but is not a conversion of
    it (Astra);
  - H_dir's readings, worded in advance.

**B:**
- **The statistic:** T_{g,c} is the test-bank mean of graph g's selected decile under condition c. The decile is the
  top 26 of 256 on the selection bank, with ties broken by genome index (Astra).
- **The primary** (Fable): U_g = T_{g,sham} − T_{g,relief}. N2's U is ranked against SH-mirror-ASK's by 03's rank
  formula (one-sided, p ≥ 1/65). Only the formula is imported, not 03's effect-margin gate. The rank test is
  approximate (Astra).
- **The labels:**
  - **"Head start larger when memory is needed"** requires the rank p, and also N2's level advantage
    T_{N2,level} − mean T_{e,level} > 0 by its 95% interval;
  - **an interaction without an established initial advantage** is labelled as such.
- **The intervals:** the selection and test banks are resampled separately, and selection is repeated within each
  resample (Astra).
- **Reported:**
  - both component advantages;
  - U computed against level (level − relief);
  - the expected best of 32 by order statistics.

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
2. **Step 0, exploratory** (seconds of GPU, the owner's word):
   - 03's pilot genomes are regenerated from their committed seeds on CUDA, on the 16 pilot graphs SH101-SH116;
   - H and S are measured on them, and related to the T1 fitness already committed in `pilot.json`, under level only;
   - this gives ρ_level's spread across graphs before any new fitness run. It sets nothing by itself, and it is
     labelled exploratory.
3. **The scripted gate, level and relief parts.**
4. **The pilot's restricted part,** on 2 SH-mirror-ASK pilot graphs (pilot seeds, never N2): level trajectories only,
   giving the sham's rates and the T1 timing at the formal composition.
5. **The sham frozen, then the gate's sham part.**
6. **The rest of the pilot:** all three conditions on 2-4 pilot graphs, giving the variance of ρ and D, and the
   timing. Its rules, fixed in its registration:
   - W stays at 16 unless the reliability falls below 0.85;
   - G stays at 256;
   - δ_A is 0.05 in ρ, unless the step-0 or pilot SD of graph-level ρ makes that undetectable at 64 graphs, in which
     case 03h stops for redesign.
7. **The pre-registration,** with everything fixed, reviewed by both, bound and pushed. Then the formal run, with the
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

- **The cap:** 6 GPU-hours, the ceiling (accepted by both as a ceiling), set from the pilot's timing.
- **Cut order:** SH first, then W_t from 64 to 32. The primary ensemble stays at 64 graphs, and W stays at 16 (Fable).
- **Incomplete runs:** a run stopped by the cap is reported as incomplete. It never becomes a smaller successful
  experiment.

## 9. What it cannot show

- **Not memory capacity:** the relief changes memory demand for one strategy, not memory capacity.
- **Not usefulness as memory:** A is an association in random brains, not use of history as memory.
- **Not a missing head start:** a null B does not show that N2 has none. Under Holm at 64 graphs, N2 must exceed
  nearly every null graph.
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
