# 03h: does the history random brains hold predict how well they forage? Design v2 (draft, for review)

**Status:** design v2, 2026-10-18. Not coded, not run.
- **v1** (`de22cc4`, D321) was reviewed by both (run 20261018-152829, `docs/reviews/20261018-03h-design/`); both said
  "revise". v2 takes every finding (§9; D322).
- **Merged:** where the two reviewers disagreed, v2 merges their positions and says so (§9, "Merged").
- **GPU:** any GPU work, the pilot included, needs the owner's word.

## 1. The question

**The memory thread** (`ROADMAP.md`, "The thread worth following") says N2 starts with more capacity to hold recent
history, and that evolution then builds such memory into every graph.

**What the repository already shows:**
- **N2's random brains hold a past food level unusually strongly.** P4 is 0.931, 0.924 and 0.926 in 03, 03r and
  03mc, against ensemble means of 0.75-0.85. These are approximate reference-ensemble tests, not exact randomisation
  tests (`experiments/03-generation0/RESULTS.md`).
- **Selection builds turn-history dependence into champions,** in the four task and group combinations 02b studied.
  02b also states: "Whether it helps foraging is not tested".
- **No file relates a genome's history to its fitness.**

03h tests that relation at generation 0, where P4 is measured.

**Two questions:**
- **A, the link:** within a graph, does the history a random genome holds predict its foraging score? Does it predict
  it less when the need for memory is relieved, compared with a sham that changes the input equally?
- **B, N2's head start:** is N2's generation-0 upper tail more advantaged over the null ensembles when memory is
  needed than when it is relieved? Does N2 have a generation-0 advantage in the first place?

**What a positive answer means, worded now:**
- **A:** "probe-measured history predicts fitness positively, and more strongly than under relief", in random brains,
  on this task, interface and probe. It is not evidence that the history is used as memory, and it does not mediate
  N2's advantage (Astra).
- **A null A** closes this screening route. It does not show that useful history is absent: history could have an
  optimal timescale or a direction, or the probe could miss it (Astra).

**Stage C,** evolution under the conditions, runs only on §5's gate, with its own pre-registration and the owner's
word.

## 2. The task: 02's T1, not Task N

**v1 used Task N-mono. At generation 0 that task's fitness is nearly binary** (Fable):
- 74% of 256 random N2 genomes scored zero on all 64 worlds, with a mean of 0.031 targets per episode
  (`experiments/E1-navigation/RESULTS.md`);
- 78-97% of 04a's generation-0 genomes scored zero on every training world.

**v2 uses 02's T1, single-nose foraging** (`wormwars/exp02/grid.py` `task_config(…, "T1")`, mapping M0). It suits
generation 0 for three reasons:
- **Graded fitness:** T1 is foraging on patches with odour, so random brains eat a graded amount. 03's T0-M0, the
  same world with stereo sensing, gave a random-genome mean of 0.90 with a top decile of 1.69. The pilot (§6)
  measures T1's distribution and zero share before anything is fixed.
- **Memory pays:** 02's registered tripwire measured scripted M − K = +0.942 [+0.928, +0.956] on T1 (02 RESULTS,
  "Tripwires").
- **The controllers are nested:** `MemoryKinesis` is `LevelKinesis` plus one tick of memory (`wormwars/exp02/scripted.py`).
  `GradedKinesis` is the strongest simple memoryless rival.

**The brain configuration is 02's T1 configuration** (32 substeps), the one 03's P4 used. Single-strain padding does
not apply to batches of 512-1 024 strains.

## 3. The manipulation: three conditions on one new channel

A new signal, `food_fell`, is injected into **ASKL and ASKR**. These are sensory neurons whose own channel, ally
pheromone, is silent in T1 (the pheromone sense scale is 0 in `task_config`). Gain 1.0, unclipped below the input
clamp. Their pheromone input is zero; the neurons themselves are not silent (Astra).

**Three conditions, the same channel, neurons and gain:**
- **level:** `food_fell` is 0 on every tick.
- **relief:** `food_fell` is 1 on a tick where the food reading at the nose is strictly below the previous tick's
  reading, and 0 otherwise.
  - On an episode's first tick, it is 0.
  - The reading is the one the brain receives: after any food probe, before gain and clamp.
  - When a patch is eaten, the bit follows the readings like any other tick. There is no reset on hidden events, so
    it carries nothing beyond the observed level history (Astra).
  - A memoryless controller reading level and `food_fell` can do what `MemoryKinesis` does, first tick included.
- **sham:** `food_fell` is replaced by a two-state Markov sequence, independent of the food trend. Its on and off
  transition rates are matched to the relief bit's, as measured in the pilot under level (§6), on keyed random streams
  per world and wey.
  - It matches the bit's rate and its persistence. A delayed copy of the real bit would still be informative,
    because falls persist (Fable).
  - It controls the added drive: under relief, every genome's fitness gains a component from how its random weights
    route ASK to the motors, which attenuates any correlation mechanically (Fable, Astra).

**The routing control: a new ensemble name.** 03's routing cap (`constrained_neurons`, `wormwars/exp03/samplers.py`)
covers only the six food pairs, and in 02 shuffles gave food neurons direct read-out weights far above N2's (Fable,
Astra). v2 adds ASKL and ASKR to the constrained set, as a parameter of `constrained_neurons`, with its own test:
- the ensembles **SH-mirror-ASK** and **SH-route-ASK**;
- each graph's ASK direct read-out count and weight (`direct_readout`), reported as a covariate.

**The scripted go condition,** before any neural run:
- **The protocol** (Astra):
  - each family is tuned on registered tuning worlds, with its selection among timescales frozen there;
  - each is then scored once on registered check worlds;
  - all comparisons are paired by world.
- **The families,** each including the settings that ignore the bit or internal history (nested; Astra):
  - memoryless (`LevelKinesis`, `GradedKinesis`);
  - memoryless reading `food_fell`;
  - one-tick memory (`MemoryKinesis`).
- **Under level:** the lower bound of the paired 95% interval of (best memory − best memoryless) is ≥ 0.5 targets
  (02 measured +0.94).
- **Under relief:** the paired 90% interval of (best memory with the bit − best memoryless with the bit) lies inside
  ±0.3. That is two-sided equivalence at 5%.
  - Since `LevelKinesis` reading the bit is `MemoryKinesis`, this tests whether the memory families gain more than
    0.3 beyond one tick (Fable).
- **Under sham:** the best memoryless controller reading the sham bit is within ±0.3 of the best memoryless
  controller, by the same equivalence test. The sham carries no usable information.
- **If any of these fails,** 03h stops and is reported. No neural measurement follows.

## 4. Graphs, genomes, worlds, measures

**Graphs:**
- N2;
- **SH-mirror-ASK** (64 graphs), the primary ensemble (Astra's preference; Fable accepts it). It adds mirror symmetry
  to the routing cap;
- **SH** (64 graphs), secondary, unconstrained.
- 03 used 128 graphs per ensemble; 03h uses half (Fable).
- Seeds are outside every earlier range.
- Failed samplers are retried with the next seed, a registered rule, and every failure is reported (Astra).
- SH-route-ASK is described in §3, but not run unless the review prefers it to SH-mirror-ASK.

**Motor calibration:** once per graph under level, then frozen for every condition (Astra). Achieved drive and clipping
are reported per condition.

**Genomes:**
- G random genomes per graph, from the generation-0 distribution;
- the same genome objects are used for the history measure and for every condition's fitness (Astra: 03's driver
  draws its fitness and probe genomes separately).

**Fitness:**
- T1's mean count over W worlds per genome;
- the selection bank of W worlds is shared by every genome, graph and condition, and so is a disjoint test bank of
  W_t worlds (for B);
- G, W and W_t are fixed from the pilot, under a registered rule. The provisional values are G = 512 and W = W_t = 32.
  If the budget binds, graphs are cut before worlds (Fable);
- a registered graded secondary score, if the pilot's zero share exceeds 50%.

**History** (`wormwars/exp03/measures.py` `history()`):
- run under level, with the bit at 0;
- on 03's stimulus bank, which is the primary. It comes from 02's task family, and its transfer to T1 is stated;
- a T1-specific bank is a sensitivity analysis (Astra);
- `history()` is extended to return each history's read-outs as well as their differences, with a test (Fable).

**Per genome, the history measures:**
- **H,** the primary (Astra): |raw-turn final difference|, the per-genome numerator of P4;
- **S,** the covariate: |raw-turn steady contrast|, the response magnitude;
- **H_dir,** the key secondary (Fable): |motor turn after the falling history| − |motor turn after the rising
  history| at the final tick. It is the direction that `MemoryKinesis` uses;
- forward read-outs, and the signed differences, descriptive.
- A is about the per-genome quantity, not P4 itself, which is a ratio of population means (Astra).

## 5. Readings (fixed in the pre-registration)

**A, the link** (one claim, two conjunctive parts).
- **The statistic:** per graph and condition c, the partial Spearman ρ_c between H and fitness, given S.
  - It is the correlation of the residuals after separately regressing the ranks of H and of fitness on the ranks of
    S, with an intercept. Ties take average ranks (Astra).
  - A graph whose fitness is constant, or whose residuals are degenerate, is reported and kept, never silently
    dropped. The handling is registered.
- **A1:** ρ_level > 0 in the primary null ensemble (SH-mirror-ASK). N2's ρ_level is reported separately.
- **A2:** D = ρ_sham − ρ_relief > 0 in the primary null ensemble, with D > δ_A for a "meaningful" reading.
  - δ_A is provisionally 0.05 in ρ. The pilot also expresses it in targets: the fitness difference between the top
    and bottom quartiles of H.
  - ρ_level − ρ_relief is descriptive.
- **The claim** holds only if A1 and A2 both hold (Astra, Fable).
- **N2's own ρ and D** are reported with intervals; N2 is one fixed connectome, not a draw from the mixture (Astra).
- **SH** is reported beside the primary ensemble.
- **Uncertainty** comes from crossed resampling: one shared resample of the selection worlds across every graph and
  condition, genomes resampled within each graph, and graphs resampled within the ensemble (Astra; 8 shared worlds
  would not have supported inference over worlds).

**B, N2's head start.**
- **The statistic:** T_{g,c} is the test-bank mean of graph g's top decile, the genomes selected on the selection bank
  under condition c. Ties at the cut are broken by genome index, independently of the test scores (Astra). That is
  "the test performance of the selected decile".
- **The primary:** U_g = T_{g,level} − T_{g,relief}, with N2's U ranked against SH-mirror-ASK's U by 03's rank rule
  (one-sided; p ≥ 1/65).
- **The labels:**
  - **"Head start larger when memory is needed"** requires both this rank p and N2's level advantage over the
    ensemble mean (T_{N2,level} − mean T_{e,level} > 0, by its interval). An interaction alone is not a head start
    (Astra);
  - **an interaction without an established initial advantage** is labelled as such.
- **Reported:**
  - both component advantages: Δ_e = (T_{N2,L} − T̄_{e,L}) − (T_{N2,R} − T̄_{e,R});
  - the sham's U;
  - the expected best of 32 by order statistics, secondary;
  - SH beside the primary ensemble.
- **A positive interaction can arise because N2 does worse under relief.** The components show which (Astra).

**Multiplicity:** A and B are one family under Holm at α = 0.05 (Fable, Astra). A's two parts are conjunctive, and B
uses one primary ensemble.

**The neural manipulation check** (Fable), reported but not gated: the within-graph shift of the selected decile's
test score, relief against sham.
- If no ensemble shows a shift beyond its interval, the outcome is worded "the relief was not exploited by random
  brains at generation 0", and A and B are read in that light.

**The gate to stage C,** in numbers: C may be proposed if A holds under Holm, or B's label "head start larger when
memory is needed" holds under Holm. It still needs its own pre-registration and the owner's word.

**Outcome wordings,** fixed for every combination of A1, A2, B and the manipulation check.

## 6. The pilot (registered before it runs; GPU, the owner's word)

The pilot runs on 2-4 graphs from SH-mirror-ASK, with seeds outside the formal range, and never on N2. It runs at
G = 512, at W = 32 and 64.

**What it measures:**
- the T1 generation-0 fitness distribution, and its zero share;
- the relief bit's on and off rates under level, which set the sham;
- the timing, per graph and condition;
- the variance of ρ and of D across genomes and worlds.

**What it sets, by rules fixed before it runs:**
- W, from the precision of ρ;
- G;
- the graded secondary, if needed;
- δ_A in targets;
- the cap.

Nothing from the pilot is a test.

## 7. Budget (provisional)

**The formal run:** (64 + 64) null graphs × 3 conditions × 512 genomes × 64 worlds (selection and test), plus N2 at
1 024 genomes.
- That is about 13 M episodes. At 03a's 892 per second (a different batch composition), it is about 4 hours.
- Calibration takes about 0.9 hours and the history probe about 0.5.
- The formal cap is set from the pilot's timing, and is at most 6 GPU-hours (Fable). Astra would start from 4, as a
  feasibility ceiling.

**The pilot:** at most 0.5 GPU-hours.

**The scripted gate:** about 0.1 hours.

**Incomplete runs:** a run stopped by the cap is reported as incomplete. It never becomes a smaller successful
experiment (Astra).

## 8. What it cannot show

- **Not memory capacity:** the relief changes memory demand for one strategy, not memory capacity.
- **Not usefulness as memory:** a positive A is an association, not a demonstration that history is used as memory. A
  filter that smooths input could also predict fitness.
- **Not a missing head start:** a null B does not show that N2 has no head start. At 64 graphs, and under Holm, N2 must
  exceed nearly every null graph.
- **Not about evolved brains:** stage C is gated.
- **One configuration:** one task (T1), one interface variant (the ASK channel; its hash differs from the pinned
  interface's), one probe bank.

## 9. Changes from v1 (the review: run 20261018-152829)

**Taken:**
- **The task:** T1, not Task N-mono, whose generation-0 fitness is nearly binary (Fable 1).
- **Worlds per genome:** set by the pilot (Fable 1, Astra 5).
- **The sham condition:** with the relief tested against sham (Fable 2, Astra 3).
- **The routing cap** extended to ASK, as a new ensemble name (Fable 3, Astra 2).
- **A1 and A2, conjunctive** (Fable 4, Astra 1).
- **The partial Spearman, defined:** residuals of ranks, average ties, degenerate graphs kept (Astra 4, 5).
- **Crossed resampling** (Astra 5).
- **B:** the selected decile's test performance; the head-start label needs a level advantage; both components
  reported (Astra 6).
- **Holm over A and B; one primary ensemble** (Fable 7, Astra 7).
- **The scripted gate's protocol:** tuning against check, equivalence intervals, nested families (Astra 8, Fable 8).
- **The history measure:** the same genome objects, the bank stated, the extension (Astra 9, Fable 5).
- **The neural manipulation check** (Fable 6).
- **The pilot** (Fable, Astra).
- **Disjoint world ranges;** failed-sampler and incomplete-run rules (Astra 13).
- **Facts:**
  - the ensemble means run to 0.85;
  - 02b's quotation;
  - 03 used 128 graphs per ensemble;
  - the approximate-test caveat.

**Merged** (the reviewers differed; for confirmation):
- **The primary history measure:** Astra's |raw turn| (P4's numerator, the measure the thread is about) is primary,
  and Fable's directional H_dir is the key secondary.
- **The ensembles:** SH-mirror-ASK primary and SH secondary (Astra), with the ASK cap that both asked for.
- **The frozen-champion check** (Astra: alongside A, not gated on it; Fable: after A, outside 03h):
  - a separate exploratory item, outside 03h's family;
  - designed on its own, after 03h's pre-registration is bound, so it does not delay A;
  - not gated on A's result.
- **The cap:** at most 6 GPU-hours, set from the pilot. Astra would start from 4.
