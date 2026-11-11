# E5-1: evolving hunters on Task H, on N2 and on null graphs. Design

*Draft 3, 2026-11-11, after two rounds of review (Astra 6 and Fable 5.2; round 1 and round 2 both "fix then proceed";
every must-fix taken; [`docs/reviews/20261111-E5-1-design/`](../reviews/20261111-E5-1-design/); draft 1 at `ae959a8`,
draft 2 at `c645dc5`). Fable judged a third full round unnecessary: the round-2 fixes are checked at the
pre-registration's review. Not a pre-registration: nothing has run on the GPU, and no Task H evolution code is written.
The owner said "sure" to this design round on 2026-11-10 (D389); the GPU needs their word, separately, before any stage
below runs on it. The scope is [`SCOPE.md`](SCOPE.md) (draft 2, D385) and E5-0's results
([`experiments/E5-hunter/E5-0/RESULTS.md`](../../experiments/E5-hunter/E5-0/RESULTS.md), draft 2, D388). From this
round on the Anthropic reviewer is Fable 5.2; every earlier review in the repository was Fable 5.1's. What changed is
in §12 and §13.*

## 1. The two questions

The owner asked for two things in stage 05 (D385): a hunter built from what earlier stages made, and a null-graph arm,
"so 05 also asks whether N2's wiring helps a hunter". E5-1 asks both, kept apart.

1. **The build (descriptive).** Starting from the E4s-1 champions that E5-0 tested, which qualify at every rung
   zero-shot, does evolution on Task H give better hunters on fresh worlds and on prey speeds it did not train on, and
   how much of Task N do they keep?
2. **The test (confirmatory, to be pre-registered).** With L1's topology and initial values fixed (its parameters then
   mutate), the same interface, motor gains, generation-0 construction, GA and budget, do the validation-selected
   hunters obtained on N2 within 500 generations have a higher held-out suite score than those obtained on the average
   graph of 03's SH-route ensemble?

**This answers a narrower question than the owner's** (both reviewers): whether N2 is a better *host for L1* than a
routing-constrained shuffle, at the end of a fixed budget. It does not isolate wiring from weight placement (SH-route
moves both), or evolutionary improvement from starting performance (O1c is the climb, O1 the endpoint). Two
wiring-free anchor arms (§4) put the hosts beside the graft alone.

It is the first evolutionary comparison against a null ensemble since 02. 03a evolved on one SH-mirror graph in a
pilot; 03, 03r, 03h and the memory thread measured random brains only.

## 2. What E5-0 gives this design

- **Task H works on the CPU** (old engine against new, and H1-ghost against Task N, bit for bit), and every one of the
  18 read settings is solvable and not too easy. **It has never run on CUDA.**
- **The ladder has no fall-off point.** The positive control and both fixed-parameter references catch fast route prey
  more often than slow ones (4.57 to 7.72 for E1's frozen navigator), so SCOPE.md §4's rule cannot be applied (§3).
- **The families separate:** E4s-1's 16 champions and L1 on its carrier qualify everywhere; E2d's 47 N2-only champions
  stop once the prey moves; generation 0 never qualifies. **The E4s-1 genomes E5-0 tested are the validation
  champions (C),** not the final generation's best (F): `wormwars/e5/hunters.py` reads each record's `champion`
  checkpoint, and C and F differ in 13 of 16 runs (Astra). Every number below for the reused E4s-1 hunters is C's;
  E4s-1's own lesion numbers are its F genomes', and its training curve is its generation winners' (Astra, r2).
- **E4s-1's champions decline at fast prey** (family mean 3.5 to 3.6 at route speeds 0.2 to 0.6, 2.04 at 1.0), where L1
  rises (4.51 at 0.8): room for the build arm.
- **The scale.** On the suite score (§3, defined after E5-0's reading, so exploratory), E4s-1's 16 champions average
  2.85 (SD 0.23, range 2.60 to 3.41), L1 on its carrier 3.01, E2d's 47 champions 0.76 (SD 0.22), generation 0 0.11
  (`scripts/e5_1_power.py` → `experiments/E5-hunter/E5-1/design-power.json`, `suite_score_e5_0`).
- **The host may add little.** Silencing the module left E4s-1's final brains (F) 0.11 targets, and unevolved L1 on its
  carrier scores 3.01 on the suite against the evolved N2 champions' 2.85 (and 4.12 against 2.04 at route speed 1.0).
  Biases and τ on the read-out neurons evolve whatever the graph, so two hosts may differ little (Fable). Hence the
  anchors and the host-wiring lesion (§4, §5).

## 3. The ladder: a fixed training mixture and a held-out suite, not a curriculum

**Why not a curriculum.** A curriculum that moves each run to harder prey when it succeeds gives each arm its own
training distribution, set by its own progress, which confounds the host with what it was trained on. A shared,
predetermined schedule would be fair too, but is not needed (Astra). The positive control's rise with speed also
removes the natural place to put rungs.

**The rule that replaces SCOPE.md §4:** train on a fixed mixture spanning the range E5-0 tested, and hold out speeds in
between and beyond. The rungs are chosen from E5-0's separation of the reused families (exploratory; said so).

**Training mixture.** Each strain's 8 training worlds per generation are one world per setting below; every strain
within a run sees the same 8 world ids (each run has its own schedule, `evolve_batch`). One mixed world holds all 8
(§9).

| Slot | Setting | Stratum | Why |
|---|---|---|---|
| 1 | H1-bite | static | the static rung |
| 2 | route, s = 0.2 | route | slow route |
| 3 | route, s = 0.4 | route | where most E2d champions stop |
| 4 | route, s = 0.6 | route | where none of E2d qualifies |
| 5 | route, s = 0.8 | route | where E4s-1 declines and L1 peaks |
| 6 | route, s = 1.0 | route | the fastest |
| 7 | random walk, s = 0.5 | movers | an unpredictable mover |
| 8 | wall follower, s = 0.5 | movers | a wall-bound, weakly reactive mover |

**The selection fitness has the score's weights** (Astra; Fable). Raw capture sums would weight the strata 12.5%,
62.5% and 25%, against the score's thirds. The fitness is (1/3)·[c₁ + (c₂ + … + c₆)/5 + (c₇ + c₈)/2], with c_k the
captures in slot k: still unshaped captures, reweighted; raw counts are recorded. **Its cost** (Fable, r2): one static
world carries a third of the weight, so with equal per-world variance it carries about 59% of the fitness noise, and
the fitness has 1.5 times the variance of an unweighted mean. Accepted, so that selection and the reading agree.

**Validation:** 256 worlds, 32 per training setting, aggregated with the same weights, at every checkpoint (every 25
generations). The nine held-out settings never enter selection or checkpoint choice. `evolve_batch` aggregates
validation by a plain mean (`v.score[i].mean()`); the Task H adapter changes it to the weighted one, with a test (§9).

**The held-out test suite** (the formal reading; never used in training, validation or any pilot): every E5-0 setting
under the bite rule, 17 in all, 512 worlds each (8 704), paired across hunters:
- **trained settings on new worlds:** H1-bite, route 0.2, 0.4, 0.6, 0.8, 1.0, walk 0.5, wall 0.5;
- **held-out speeds:** route 0.1, 0.3, 0.5, 0.7, 0.9, walk 0.25 and 0.75, wall 0.25 and 0.75. No prey kind is unseen,
  and route 0.1 lies between the static rung and 0.2, so this tests other speeds of trained prey, not transfer to new
  prey (both). H3 and H4 are the transfer tests.

**The suite score** of a genome: the mean of three strata, equally weighted: static (H1-bite), route (the mean over the
10 route speeds), movers (the mean over the 6 H2b settings). Each stratum and setting is reported beside it, trained
and held-out apart.

**Bridges, descriptive:** H1-ghost (Task N exactly) and H1-reach, 512 worlds each.

**Known limits carried over:** the random-walk prey spends up to 27% of its moves against the wall at s = 0.75; the
wall follower is weakly reactive. Unchanged, so E5-0's numbers stay comparable.

**Worlds** (Astra, r2: the world-generation seed, not only the ids, decides a world, `world.py`'s `world_seed`). One
world-generation seed for every E5-1 world, formal and pilot: **1 520 001**. The id blocks (985 and 986 million, used
by no earlier stage), each with its settings:

| Phase | World ids | Settings |
|---|---|---|
| formal training | 985 000 000 + [0, 500 000), by each run's schedule | the 8 slots |
| formal validation | 985 600 000 to 985 600 255 | 32 per training setting |
| the suite (C, G0, references) | 985 700 000 + 512k + i, setting k in §3's order | the 17 |
| probes and lesions | the suite's 512 ids of their 4 settings (intentional reuse, so they pair with the suite) | 4 |
| bridges | 985 720 000 to 985 721 023 | H1-ghost 512, H1-reach 512 |
| O0's populations | 985 730 000 to 985 730 063 | 8 per training setting |
| mutational sensitivity | 985 740 000 to 985 740 255 | 32 per training setting |
| the selection-signal pilot | 985 760 000 to 985 760 255 | 32 per training setting |
| the CUDA checks' SD block | 985 790 000 to 985 791 023 | per check |
| the CUDA and composition checks | 985 800 000 + up to 40 960 | per check |
| pilot training | 986 000 000 + [0, 100 000), by each pilot run's schedule | the 8 slots |
| pilot validation | 986 200 000 to 986 200 255 | 32 per training setting |

A test (to be written, §9) checks that the blocks are disjoint from each other and from every earlier range, and
that formal and pilot training schedules share no id.

## 4. The arms

**The optimizer** is E2's GA, as E4s-1 ran it: population 32, 3 elites, truncation 8, 8 worlds per strain (§3),
checkpoints every 25 generations; the module's mutation at 0.25× 02's scales, the host's at 1×.

**500 generations** (`evolve_batch(generations=500)`, generations 0 to 499), fixed before any Task H data. E4s-1's M
arm on Task N climbed from 2.22 at generation 0 to 6.86 at 500 and 7.08 at 999, 95% of its climb by 500
(`experiments/E4s-stereo-module/E4s-1/eval-training.json`, `along`, the 16 M runs). That supports the cost, not
convergence on Task H or fairness at the asymptote (Astra). 02 found shuffles catching up late (Fable), so a shorter
budget may favour whichever arm starts ahead: the endpoint is read "within the 500-generation budget", and §5 registers
a statistic for whether the gap is still closing.

**One composition for every arm: 4 runs per batch,** 128 strains × 8 worlds. A batch holds one graph (`evolve_batch`
takes one `BrainSpec`), so each SH-route graph is one batch of its 4 runs, and N2's 32 runs are 8 batches of 4.
Exactness is claimed within one composition only (rule 6); with one composition the arms differ in graph, not in
shape. N2's 8 batches give a placebo: their between-batch SD, by the same estimator as SH-route's between-graph SD, is
reported (Fable, r2).

| Arm | Host | Generation 0 | Runs | Batches | Role |
|---|---|---|---|---|---|
| **G-N2** | N2 + L1 | L1 on random N2 (E4s-1's M construction, `embedded_population`) | 32 | 8 | the test, N2 side |
| **G-SHr** | SH-route + L1 | the same construction on each graph | 20 graphs × 4 | 20 | the test, null side |
| **A0r** | none | G-N2's own generation-0 draws (runs 0 to 7), with every host-to-host weight and gap conductance zeroed and pinned | 8 | 2 | the like-for-like anchor, descriptive (Fable, r2) |
| **A0** | none | 32 identical copies of L1 on its carrier (forward 1.0, turn 0.2; `carrier_genome`), host weights and conductances zero and pinned | 8 | 2 | the designed-carrier anchor, descriptive (Fable, r1) |
| **P** | N2 + L1, N2's initial weight magnitudes permuted | L1 on random N2 initialised with 02's `permuted` magnitudes, permutation seeds 4, 5, 6 | 3 × 4 | 3 | initial weight placement, descriptive (Fable) |
| **B** | N2 + L1 | one E4s-1 C champion, 32 identical copies (C2's construction) | 16 | 4 | the build, descriptive; after the test |

In A0 and A0r the host's biases and τ mutate at 1× and the module at 0.25×; only the host's chemical weights `w` and
gap conductances `g` are held at 0.

**Why L1 is in both test arms.** The test asks whether a reusable, competent component does better in one host than
another, under control. The module is competent; a starting *population* is not (E4s-0 found most random N2
backgrounds score zero), and that is what the climb measures. Draft 1's "a floor against a floor" is withdrawn: E2d's
champions were evolved on Task N, which says nothing about how ungrafted N2 or SH-route would evolve on Task H (Astra).
L1 has its own noses and its 16 synapses onto the 8 turn read-out neurons (SMDDL/R, SMDVL/R, RMDDL/R, RMDVL/R), which
every SH-route graph keeps by name. L1 and the gains were designed and settled on N2 (E4s-0), which every claim states.

**SH-route,** exactly (Astra): 03's ensemble that keeps N2's degree sequence and imposes upper bounds, at N2's values,
on the number and anatomical weight of direct edges from the six food pairs of M0, R1 and R2 onto the read-out; it
moves weight placement as well as edges, and does not match every routing property. 02's tripwire made matched routing
a requirement of later comparisons. **The graphs, by name:** 03r's `SH-route-1020000` to `SH-route-1020019` for the
formal run (if §7's cut (4) applies, `SH-route-1020000` to `SH-route-1020015`); `SH-route-1020020` to
`SH-route-1020023` for the pilot, of which `1020020` and `1020021` evolve (§7). Never selected on any measure; their
03r covariates (P4, calibrated gains) are reported against their E5-1 scores, descriptively (Fable).

**P,** exactly (Astra, r2): no N2perm graph file exists. In 03r, `exp03.py`'s `_load_graph` returns N2 unchanged for
every N2perm name, and `exp02/grid.py`'s `brain_config_for_graph` sets the chemical and gap initial magnitudes to
`permuted`, with the permutation seed from the name. P applies those settings to the ungrafted N2 host's
initialisation, then embeds L1's designed values (permuting over the grafted edge list would permute L1 too). The
permutation configurations and the resulting host magnitude hashes are recorded; a check confirms P's edges and L1's
initial values equal G-N2's and its host magnitudes differ. P measures sensitivity to *initial* weight placement;
evolution then changes the weights. N2perm's initial direct food-to-read-out weights are reported against SH-route's
caps (Fable).

**Motor gains: 4.0 and 2.0 for every graph,** a scientific choice. Draft 1's engineering reason was wrong: with one
graph per world, a graph's own gains could go into its configuration, and `PreyBrain` inverts its commands through
whatever gains it is given (both). The reasons that stand:
- calibration changes the host-plus-module phenotype, so it answers another question (Astra); L1's output enters through
  the same read-out, so a calibrated turn gain rescales L1's drive as well;
- the gains and L1 were developed on N2, and that is stated, not corrected.

03r's calibration (on 02's foraging task, `experiments/03r-replication/supplement.json`) gives N2 a turn gain of 2.08 and
the median SH-route graph 2.95, so N2's random brains give about 1.4 times the turn drive at equal gain; N2perm4 to 6,
on N2's edges with permuted weights, need 2.92 to 3.07 too. On three draws on another task this points to weight
placement, not edges (Fable). The direction of the resulting bias is not known. So: the achieved forward and turn
drive, the signed turn offset and the read-out saturation are reported for every graph at G0 and at C; generation 0 is
also measured at each graph's calibrated gains (O0's populations, §5, at 03r's gains); P separates N2's initial weights
from its edges, descriptively.

**Seeds** (a block no earlier stage used; E5-0's run seed was 1 500 001). G-N2 run i uses 1 510 000 + i; B run i uses
the same seed (B and G-N2 are paired, descriptively, on training schedule and breeding stream; records are keyed by arm
and run, never by seed alone); G-SHr graph j (0 to 19), run r (0 to 3) uses 1 511 000 + 4j + r; A0r run i uses G-N2
run i's seed (its generation 0 is G-N2's draw, with the host zeroed); A0 run i 1 512 000 + i; P draw k (0 to 2), run r
1 513 000 + 4k + r. The pilot's N2 populations use 1 519 000 to 1 519 003, its null runs 1 518 000 + 4j + r. G-N2
against G-SHr is **an independent-samples comparison with clustering** (graphs) and paired evaluation worlds (Astra).
B's 16 starts are E4s-1's C genomes, fixed by run, checkpoint index and sha256 in the pre-registration.

## 5. Readings

**The registered genome is C,** the best validation checkpoint (§3). F is chosen on 8 worlds, one per setting, which is
noisier than in E4s-1 (Fable); C is fixed now. **G0** is the generation-0 training winner (checkpoint 0), evaluated on
fresh worlds (Astra). F is reported from its training and validation numbers only. C's generation is reported by arm.

**Evaluation composition** (Astra, r2): each batch's C and G0 genomes (8 strains) together, per setting, 512 worlds per
chunk; validation is 4 strains × 256 worlds of the mixed world. §7 checks these shapes.

**O1 (confirmatory): N2 against the average SH-route graph, on C's suite score.**
- **Estimand:** Δ = (the mean over G-N2's 32 runs) − (the mean over G-SHr's 20 graph means, each the mean of its 4
  runs). It compares N2 with the ensemble's average graph; "N2 ahead" does not mean N2 is unusual within it (Fable).
- **Interval: Welch's 90% t interval** over N2's 32 run scores and the 20 graph means (`stats.welch_interval`, tested),
  registered now (Fable, r2), with no resample count or seed. The one-level percentile bootstrap is reported beside it.
  Draft 1's nested bootstrap counted within-graph noise twice (Astra). Inference is conditional on the frozen suite.
- **Rules, symmetric, in order** (`stats.label`, tested; invalid input is an error, not an outcome):
  1. lower bound above 0: **"N2 ahead, estimate at least δ"** if Δ ≥ δ, otherwise **"N2 ahead, estimate below δ"**;
  2. upper bound below 0: **"SH-route ahead, estimate at least δ"** if Δ ≤ −δ, otherwise **"SH-route ahead, estimate
     below δ"**;
  3. both bounds inside (−δ, δ): **"no difference of δ either way"**;
  4. otherwise **"inconclusive"**.

  A detected difference takes precedence over rule 3; when both hold (an interval inside (0, δ)), both are reported.
  Neither label 1 establishes that the true difference exceeds δ (Astra).
- **δ = 0.25 captures per episode on the suite score,** fixed: one more capture every four episodes, about the
  between-champion SD of E4s-1's champions (§2), 9% of their mean. Its size against the anchors is reported.
- **Beside Δ:** SH-route's latent between-graph SD (`stats.latent_graph_sd`: the variance of the graph means less the
  mean within-graph variance over 4, truncated at 0), Δ over it ("undefined" when it is 0), and how many of the 20
  graph means exceed N2's mean (Fable).
- **Is the gap still closing?** (Fable, r2.) Per unit, the validation score at the last checkpoint (475) minus at
  checkpoint 300; the arms' difference of these changes with Welch's 90% interval; sentence: "Between generation 300
  and the last checkpoint, the gap on the validation worlds changed by X [lo, hi] captures per episode."

**The simulation** (`scripts/e5_1_power.py`; 2 000 simulations per cell, 2 000 resamples for the bootstrap; Welch's
labels; the SDs are assumptions, no E5-1 data exists). At the chosen counts (32 N2 runs; 20 graphs × 4):

| Scenario (run SDs N2/SH, graph SD) | Δ = 0: "no difference of δ" | Δ = 0: any "ahead" label | Δ = 2δ: "N2 ahead, ≥ δ" | coverage at Δ = 0 |
|---|---|---|---|---|
| normal 0.2/0.2, 0.15 | 0.90 | 0.10 | 1.00 | 0.90 |
| normal 0.3/0.3, 0.3 | 0.70 | 0.10 | 1.00 | 0.90 |
| normal 0.3/0.3, 0.45 | 0.32 | 0.10 | 0.98 | 0.90 |
| normal 0.45/0.45, 0.45 | 0.14 | 0.11 | 0.96 | 0.89 |
| no graph effect 0.3/0.3, 0 | 0.89 | 0.11 | 1.00 | 0.89 |
| unequal 0.2/0.4, 0.3 | 0.74 | 0.11 | 1.00 | 0.90 |
| unequal 0.4/0.2, 0.3 | 0.58 | 0.10 | 0.99 | 0.90 |
| 10% of graphs "dead" (2 captures lower), 0.3/0.3, 0.3 | 0.05 | 0.14 | 0.95 | 0.87 |
| 30% "dead" | 0.00 | 0.10 | 0.70 | 0.90 |
| right-skewed scores, 0.3/0.3, 0.3 | 0.69 | 0.10 | 1.00 | 0.90 |

- **Welch's coverage** is 85.6 to 91.5% over every design, scenario and true Δ (the worst cell with 10% dead graphs);
  the bootstrap's is 83.1 to 90.2%. Hence Welch.
- **A true difference of 2δ is found 95 to 100% of the time** unless many graphs fail to host L1 (70% with 30% dead).
  One of exactly δ is found about half the time at most, because label 1 needs Δ̂ ≥ δ under a symmetric error; the
  significance requirement can only lower that (Astra). The counts are chosen for the null and 2δ.
- **A true null reads "no difference of δ either way" 70% of the time** at run and graph SDs of 0.3, and rarely if
  graphs differ a lot or some fail to host L1: **with a heterogeneous ensemble the test can find a difference but
  cannot establish its absence.** 24 graphs × 4 would give 76% at 0.3/0.3 for four more batches; 16 × 4 (§7's cut)
  57%.

**Companion sentences, fixed in advance** (Fable), each completed with "under this GA, budget of 500 generations, task
mixture, motor gains and graft":
- *"N2 ahead, estimate at least δ":* "The validation-selected hunters obtained on N2 had a higher held-out suite score
  than those obtained on the average SH-route graph, by an estimated Δ [lo, hi]." *"…below δ":* the same, "by less
  than δ in estimate". The SH-route labels mirror these.
- *"No difference of δ either way":* "The 90% interval excludes a difference of 0.25 captures per episode or more, in
  either direction, between N2 and the average SH-route graph." Never "the worm wiring is neutral" (the roadmap's
  table).
- *"Inconclusive":* "The data neither show a difference nor exclude one of 0.25."
- O1 is an endpoint, not "a better host for evolving" (that is O1c).

**The anchors** (Fable; Astra, r2). Each test arm's C suite score against each anchor's: the difference of means with
Welch's 90% interval (G-N2's runs or G-SHr's graph means against the anchor's 8 runs). The primary anchor is A0r, the
like-for-like one; A0, the designed carrier with its hand-qualified start, is reported beside it. Sentences, fixed now:
- both test arms' intervals above 0: "Both hosts, evolved from random backgrounds, ended above the same starts with
  the host's wiring zeroed, evolved for the same budget";
- one: "Only [N2 / SH-route] ended above …";
- neither: "Neither evolved-host arm demonstrated higher performance than the same starts with the host's wiring
  zeroed."

None of these says the host adds nothing, or interferes: failing to show superiority is not evidence of no
contribution (Astra). **Claims about the host's wiring rest on the lesion:** for every C, intact − lesioned (every
host-to-host `w` and `g` zeroed, biases and τ kept, the module intact) at the 4 probe settings, with 90% paired
intervals, summarised by arm.

**Beside O1 (descriptive):**
- **O0, generation 0:** the same contrast on the generation-0 *populations* (all 32 strains of each run on 64 fresh
  mixture worlds), at the fixed gains and at each graph's 03r calibrated gains; not on their best, which mixes host
  quality with an extreme draw (Fable).
- **O1c, the climb:** C − G0 per run, by arm, and the difference of the arms' climbs; Δ along training from the
  validation checkpoints.
- **P:** N2perm's three draws beside N2 and SH-route; three draws carry no inference.
- **Per stratum and setting,** trained speeds against held-out speeds.

**O2, the build (descriptive).** Per B run, C − its start (the E4s-1 C champion, zero-shot) on the suite: the mean and
a 90% bootstrap interval over the 16 runs; "B improved on its starting champion" needs the interval above 0. Read beside
L1 on its carrier, on the same worlds, and at fast route speeds (0.8 to 1.0). B against G-N2, run by run, compares two
starting protocols (32 copies of an evolved brain against 32 random backgrounds, at unequal total work), not the value
of pretraining (Astra).

**O3, Task N kept (descriptive).** For B: H1-ghost (Task N) of C against its start, paired, on the bridge worlds, and
at B's checkpoints 100 and 250 ("during adaptation", SCOPE.md §7). **"Keeps Task N"** if the loss's 90% upper bound is
below 0.5 targets per episode; otherwise the loss is reported (Astra). For the test arms H1-ghost is reported too, but
it is not inherited function: they never trained on Task N (Fable).

**Probes, on every C and G0,** at four settings (H1-bite, route 0.5, route 1.0, walk 0.5), 512 worlds each: an
expansion of the two settings E5-0 froze for its fixed probes, H1-bite and route 0.5 (Astra). They are `constant`,
`mirrored`, the world's `mean`, the module-only `mean` (L1's noses fed the mean while the host's sensors are real, the
intervention in E4s-1's D) and the body probe, reported as signed paired contrasts with intervals, per genome. **No
qualification is claimed** across the 17 settings.

**References on the suite worlds** (Astra), seven: the stationary hunter, `constant`, `random-walk` and `wall-follower`
at E5-0's tuned parameters per setting (`calibration.json`), E1's frozen S-const, the pursuit reference, and L1 on its
carrier.

**Never a reading:** energy from bites (logged only), damage shares (D026's lesson), training worlds.

## 6. Failure handling (fixed now; Astra, Fable)

- **Admission order,** the 28 test batches, fixed (N = an N2 batch of 4 runs, S = an SH-route graph's batch):
  N1, S0, S1, S2, N2, S3, S4, N3, S5, S6, S7, N4, S8, S9, N5, S10, S11, S12, N6, S13, S14, N7, S15, S16, S17, N8, S18,
  S19 (Sj is `SH-route-10200jj`; N_k holds G-N2 runs 4k − 4 to 4k − 1). Then A0r, A0, P, and B. Under cut (4), S16
  to S19 are left out.
- **External interruptions** (a power cut, a driver reset, a killed process): the batch restarts from its start, same
  seed, code and composition, and is logged.
- **Behaviour-dependent or numerical failures** (a non-finite state, a ledger outside tolerance, a target sequence
  exhausted): **O1 is withheld.** Dropping such units could select graphs by behaviour (Astra), and a rerun of a
  deterministic failure repeats it (Fable). The failure is diagnosed, and a dated, reviewed amendment says what must be
  repeated before any O1 number is computed. If it is a bug, every batch run on the faulty code that it could affect
  is rerun on the fixed code: O1 uses one code version.
- **Sequence exhaustion** is a design error, not a unit's failure: good hunters cause it (64 centres per world,
  `target_sequence_length`). The GA rollout checks the world's overflow flag on every rollout (`_capture` clamps
  silently, and only `hunt_events()` raises; Fable). §7 reports the highest sequence index reached; the
  pre-registration requires it at most 32, half the sequence, or the length is raised first, after a test that
  raising it leaves the earlier centres unchanged.
- **The cap:** the owner's cap and §7's cut level are fixed from the bench, with the evaluation reserve and a 15%
  rerun reserve frozen before training. O1 needs every admitted test unit complete. If the cap still stops training
  first, O1 is withheld (a run's time depends on its captures, so which units finish could be informative) and the
  completed units are reported descriptively.

## 7. Before the formal run: E5-1a (GPU; the owner's word first)

Exploratory, with stop rules fixed here. **No evolution on N2 in the pilot,** and no N2-against-null evolutionary
contrast (Astra). Every count, δ, the interval and the generation number are fixed above. **Comparative numbers from
the pilot** (steps 5 and 6 put generation-0 measures of N2 and null graphs side by side) **may not change the
initialisation, gains, mutation scales, settings, counts or stop rules;** any departure is disclosed as exploratory
redesign (Astra, r2). In order:

1. **Task H against itself, after the changes (rule 7).** On the CPU, the current Task H (E5-0's code) against the
   revised one, per setting, and the mixed world against each slot's single-setting run: capture counts, the event
   tables, prey trajectories, respawns and skipped sequence entries, damage and the ledger, bit for bit, on worlds with
   deliberately frequent captures. The new GA rollout against a serial reference, including the weighted training
   fitness and the weighted validation aggregation (`evolve_batch`'s plain mean replaced). E5-0's 68 arrays and the
   ghost against Task N re-run. **Stop** on any difference.
2. **The graphs and P.** The 24 SH-route graphs rebuilt from 03r's record and checked against both manifests (arrays
   everywhere, raw bytes where zlib allows, D106); L1's 16 output edges and noses present after grafting; every
   interface neuron present; P's configurations and host-magnitude hashes recorded, its edges and L1 values equal to
   G-N2's. **Stop** on any mismatch.
3. **Task H on CUDA, fixed genomes** (both reviewers):
   - **The tolerance's world count, first** (Fable, r2): on the SD block, each check's per-world SD of CUDA − CPU, σd;
     then the check's worlds are n = (54.8 σd)², rounded up to 512 and at most 8 192, so that its 90% interval's
     half-width is at most 0.03. **Pass** if the paired interval of CUDA − CPU lies within ±0.10.
   - **Score level,** CPU against CUDA, at H1-bite, route 0.5 and 1.0, walk 0.5, wall 0.5 and the mixed world at the
     training shape: E1's frozen S-const, the pursuit reference, L1 on its carrier, and E4s-1 runs 0 to 3's C;
   - prey paths with a motionless ghost hunter, CPU against CUDA, for each prey kind; early-tick traces of the pursuit;
     H1-ghost against Task N on CUDA; the attack-disabled check (zero captures and damage); respawns;
   - **state level:** CPU against CUDA, open loop under identical imposed input histories, the 16 E4s-1 C genomes and
     16 grafted generation-0 genomes on pilot SH-route graphs, the maximum absolute difference over 300 ticks at most
     10⁻⁴, at the training, validation and suite shapes;
   - the ledger balances on CUDA at T0's tolerance on every episode above.
   **Stop** on any failure; diagnosis is a dated, reviewed amendment.
4. **The bench and projection:** every shape timed with route respawns and the mixed world; the projection, the
   evaluation reserve and the 15% rerun reserve. **The owner sets the cap here,** which fixes the cut level below,
   before steps 5 to 8 are read (Fable, r2). If the projection exceeds the cap, cuts in this order: (1) B moves to a
   later stage; (2) P is dropped; (3) the probes shrink to H1-bite and route 0.5; (4) SH-route goes to the 16 graphs
   `SH-route-1020000` to `SH-route-1020015` (a true null then reads "no difference" 57% of the time instead of 70% at
   SDs of 0.3). The test arms and A0r are not cut further: if they do not fit, E5-1 comes back to the owner.
5. **The selection signal, on N2's construction** (pilot seeds 1 519 000 to 1 519 003, never formal). In each of the
   4 generation-0 populations, the training winner on its actual 8-world batch, then its module-only `mean` contrast on
   the 256 selection-signal worlds (one preselected genome per population: no search over 32, Fable and Astra, r2).
   **Stop** if, in fewer than 3 of the 4 populations, that contrast's 90% interval lies above 0, or if in any
   population all 32 strains have the same fitness (no selectable variation). The finding is then worded "no
   scent-dependent signal was detected", not "there is none".
6. **The null pilot:** the same measurements on the 4 pilot SH-route graphs, reported, never a stop (a failure on null
   graphs is a finding, Fable); then `SH-route-1020020` and `SH-route-1020021` evolved for 100 generations, 4 runs each,
   at the formal shape, on the pilot's training and validation worlds: the rates, the highest sequence index, and a
   check that a grafted null climbs on Task H. Not read beside N2.
7. **The composition check** (Astra; Fable, r2: on genomes that score): the 16 E4s-1 C genomes and the pilot-evolved
   null champions, scored at the training shape (mixed, 4 × 32 × 8), the validation shape (4 × 256) and the suite chunk
   (8 × 512 per setting), against one strain × 512, CPU-free, on CUDA: each paired interval within ±0.10, worlds sized
   as in step 3. CUDA score checks of the pilot null champions as in step 3. **Stop** on any failure.
8. **Mutational sensitivity** (SCOPE.md §7): 64 mutants at the arms' scales around each of B's 16 starts and around
   8 generation-0 winners (step 5's 4 and step 6's 4), on the mutational-sensitivity worlds (393 216 episodes): the
   median share of the parent's score and the share below 0.7, as E4s-0 reported. Measured, not a stop.

## 8. Cost (rough; replaced by the bench)

**Rates on Task N:** E4s-1's ten 8-run batches took 4 876 to 5 151 s for 1 000 generations (mean 4 984 s, 1.38 hours),
about 4.98 s per generation with breeding and checkpoints. E1 timed the rollout alone at about 4.7 s at 8 runs and
3.04 s at 4 (`freeze.json`, `throughput_04a_shape`), so about 0.3 s per generation is breeding and checkpoints, and
**a 4-run batch takes about 3.35 s per generation, 0.47 hours per 500 generations**: an extrapolation (Astra).

**Task H's overhead, f, is unknown:** two swarms, combat, per-capture respawns, the mixed world. Eight separate worlds
per generation would be far worse (about 18 s per generation, Fable), which is why §9 builds one mixed world.

**Evaluation, by count** (Astra, r2): C and G0 of 156 runs on the suite, 2 715 648 episodes; five probes at four
settings on C and G0, 3 194 880; the host-wiring lesion on every C at the four probe settings, 319 488 (on the whole
suite it would be 1.36 M); two bridges on C and G0, 319 488; O0's populations, 229 376; seven references on the suite,
60 928; B's two intermediate Task N readings, 16 384; the mutational parents, 6 144. **6.86 M episodes,** 4.1 to 6.2
hours at E4s-0's 306 to E4s-1's 465 episodes per second.

| Part | Batches or episodes | at Task N's rate | f = 1.5 | f = 2 |
|---|---|---|---|---|
| G-N2 + G-SHr (the test) | 28 batches | 13.0 h | 19.5 | 26.1 |
| A0r + A0 | 4 | 1.9 | 2.8 | 3.7 |
| P | 3 | 1.4 | 2.1 | 2.8 |
| B | 4 | 1.9 | 2.8 | 3.7 |
| Evaluation | 6.86 M episodes | 4.1-6.2 | 6.1-9.3 | 8.2-12.5 |
| E5-1a: checks (CPU sides on the CPU), null pilot, mutational sensitivity (0.39 M), bench | | about 1.5 | 2.2 | 3 |
| **Total** | | **24-26** | **36-39** | **48-52** |
| **With the 15% rerun reserve** | | | **41-45** | **55-60** |

**So E5-1 is likely 41 to 60 GPU-hours with the reserve; the confirmatory part alone (the test, both anchors, their
evaluation, E5-1a) about 34 to 50.** Every number above is replaced by the bench; the cap is the owner's.

## 9. New code (each test-first; sabotage where a check cannot fail)

- **The mixed world** (Fable): `play.py` takes one prey, one rule and one pin per `HuntWorld`; `PreyBrain` has one kind
  and one speed. The world gets per-world prey kind, speed and pin, so the 8 slots run in one rollout. Checked slot by
  slot against the single-setting path (§7.1).
- **The route cache:** `_route_for` loops in Python over worlds at every capture. It is replaced by a table pre-drawn
  per (world-generation seed, world id, **sequence index**), the existing key: `HuntWorld._capture` can skip sequence
  entries, so a life is not a capture count (Astra). Equality with the current sampler tested.
- **The GA rollout for Task H:** the hunter as swarm 0 and the prey as swarm 1 in every world, the weighted fitness and
  the weighted validation (§3), the overflow check on every rollout (§6), against a serial reference.
- **Guards** (both): `Genome.cat` and `Genome.assign` refuse mismatched specs, compared by value
  (`evo/genomes.edge_hash` and the node count, metadata and configuration), since `moved()` makes new spec objects.
  The regression case is two equal-sized grafted graphs wired differently; equal specs built separately must still
  combine. `Genome.cat` has many call sites, so the whole suite runs.
- **The publication guard:** a label of the form `SH-route-…+L1` has no entry in the anatomical reference set, so
  `tests/test_publication_hygiene.py` would report no offence. Null-graph genomes get an explicit prohibition, with a
  sabotage check (Astra).
- **Arms:** A0's and A0r's masks (host `w` and `g` at 0 and pinned, host biases and τ free) in `arm_scales`; P's
  initialisation and its checks; the host-wiring lesion (`w` and `g`); O0 at 03r's calibrated gains; each run record
  carries its arm, run, graph name and graph hashes.
- **Worlds:** the id blocks' disjointness test (§3).
- **Readings:** the suite score; `stats.py` (written and tested: `tests/test_e5_stats.py`; the labels refuse
  non-finite input; Welch's interval, the bootstrap, the latent graph SD; seen failing before the code existed and
  under sabotages of the graph means, `runs/e5-1/`); O0, O1c, O2, O3, the anchors, the probes, the closing-gap
  statistic.

The per-tick host syncs in `hunt.py` are measured by the bench and removed only if they dominate, with §7.1 rerun.
Genome files stay local (rule 1). Null graph files are never committed: they carry permuted anatomical weights.

## 10. What E5-1 cannot show

- **That N2's wiring helps hunting in general.** Only whether N2 hosts L1 better than the average SH-route graph under
  this GA, budget, mixture, gains and arena. SH-route moves weights as well as edges; P's three draws only hint at
  which matters.
- **That the host contributes nothing,** or interferes, from the anchors alone; the lesion is the evidence on the host.
- **Equivalence with a heterogeneous ensemble** (§5's simulation): if some graphs fail to host L1, "no difference"
  becomes nearly unreachable.
- **The roadmap's gate** (captures from a frozen suite of competent prey on unseen maps): H3's organisms and H4's maps
  are not built. E5-1's suite is scripted prey in an empty arena.
- **Transfer to new prey:** the held-out settings are other speeds of trained prey kinds.
- **Anything about worm predation** or real chemotaxis (stereo is a game-design choice, E4s).
- **A history between G0 and C,** or why a host helps; the probes interpret, they do not decide.
- **Claims for stages 05 to 08 that need the collective-behaviour survey** the roadmap asks for; E5-1 makes none.

## 11. For the owner

- **The cost:** about 41 to 60 GPU-hours with the reserve, 34 to 50 for the confirmatory part. The first GPU step is
  E5-1a (§7, a few hours), which ends with the bench, when the cap is set.
- **Whether B belongs in E5-1** or a later stage.
- After E5-1a, a pre-registration, reviewed by both, pushed before the formal run.

## 12. Changes from draft 1 (round 1)

| Draft 1 | Draft 2 | From |
|---|---|---|
| B starts from F | From C, the genomes E5-0 tested (C ≠ F in 13 of 16 runs) | Astra 1, Fable M4 |
| An evolutionary pilot on N2 and null graphs | No N2 evolution in the pilot; N2 only in fixed-genome checks and generation-0 measures; null-only evolution | Astra 2, Fable M5 |
| Gains: "an engine change"; "drive is part of what wiring does" | A scientific choice; the engine claim and the drive claim withdrawn; drive at G0 and C; G0 at calibrated gains; arm P | Astra 3, Fable M2 |
| Raw capture sums for selection | Weighted to the score's strata; validation defined | Astra 4, Fable should-fix 1 |
| No outcome for a small detected difference; one-sided margin | Six symmetric labels; companion sentences | Astra 5, Fable M6 |
| Nested bootstrap | One level over N2 runs and graph means; simulated coverage | Astra 6, Fable 8 |
| 8 runs per batch for N2, 2 for nulls | 4 runs per batch everywhere; a composition check | Astra 7, Fable 9 |
| "Engine changes are none beyond the guard" | Task H against itself after the changes; the mixed world; the route cache by sequence index; a serial reference | Astra 8, Fable M1 |
| A `Genome.cat` guard | `cat` and `assign`, by value; the publication guard; graph hashes in run records | Astra 9, Fable 12 |
| No failure handling | Added | Astra 10 |
| 16 N2 runs; 16 graphs × 2; δ after a pilot; 1 000 generations, maybe 500 | 32; 20 × 4; δ = 0.25 now; 500 generations now | Fable M5, M6; simulation |
| — | A0, a wiring-free anchor, and the host-wiring lesion | Fable M3 |
| Stop if no strain captures anything | A module-dependent signal, on N2 only | Fable M5, Astra 10 |
| CUDA checks on four hunters at 0.05 | A wider set | both |
| "a floor against a floor"; "transfer"; "inherited" for G-N2; "E5-0's set" of probes; H probe | Withdrawn or corrected | Astra 12, 14, 16; Fable 2, 11, 15 |
| Cost 30-45 h | 35-50 h, on one basis | both |
| Graphs by index | By name | Astra, Fable 14 |

## 13. Changes from draft 2 (round 2)

| Draft 2 | Draft 3 | From |
|---|---|---|
| "If neither … exceeds A0, the host's wiring adds nothing … O1 compares how much each host interferes" | A0r, a like-for-like anchor (G-N2's own draws, host zeroed), primary; A0 beside; a Welch comparison and three fixed sentences; wiring claims rest on the lesion; `g` as well as `w` in the masks and the lesion | Fable 1, Astra 12 |
| P "rebuilt" from N2perm graph files | No such files: P is 02's `permuted` initial magnitudes on the ungrafted host, then L1; recorded and checked | Astra 13 |
| A second failure removes a unit; O1 read with 28 of 32 and 18 of 20 | Behaviour-dependent failures withhold O1 pending an amendment; external interruptions restart; sequence exhaustion a design error with an overflow check and a headroom rule; every admitted unit required | Astra 14, Fable 2 |
| The 16-graph cut conflicted with "18 of 20" | Resolved: the cut names its 16 graphs, and completeness is every admitted unit | Astra 14 |
| Stop if one strain of 32 shows a contrast | The training winner, preselected, tested on fresh worlds; plus a no-variation stop | Fable 3, Astra 15 |
| A Welch check "nearer over the whole grid" | Welch registered now; the simulation widened (unequal SDs, no graph effect, dead graphs, skew, the 16- and 24-graph designs); worst-cell coverage reported | Fable 4, Astra 16 |
| World-id blocks only | One world-generation seed; every phase's ids and settings, pilot training and validation included | Astra 17, Fable 13 |
| Composition check at 1 × 1 024 on generation-0 genomes | The actual training, validation and suite shapes, on scoring genomes; the weighted validation tested | Astra 18, Fable 6 |
| CUDA tolerance at fixed world counts | σd measured first, worlds sized to a 0.03 half-width | Fable 5 |
| The cap after the pilot | The cap at the bench, before the generation-0 comparisons are read | Fable 8 |
| Evaluation "about 0.8 M" beside the main items; no reserve in the total | Every item counted (6.86 M); lesions at four settings; 15% reserve; 41-60 h | Astra 19 |
| "ended with a higher score"; "frozen L1"; "No difference … was found"; "about half … at any count" | Reworded | Astra 20, 21; Fable 11 |
| `label` returned "inconclusive" on NaN; latent SD undefined | Refuses invalid input; the estimator defined, "undefined" at 0 | Astra 22, Fable 14, M6 |
| "Every E4s-1 number below is C's" | Restricted to the reused hunters | Astra 23 |
| — | A statistic for whether the gap is still closing; C's generation; N2's between-batch SD as a placebo; the fitness weighting's noise cost; P against SH-route's caps | Fable 7, 9, 10, 12 |
| D389 cited, absent | Written with this draft | both |

## 14. E5-1a's code, and the numbers it fixes (added 2026-11-11, D390)

The owner answered "Yes and build" (2026-11-11) to §11's two questions: E5-1a may run on the GPU (it stops at the
bench, where they set the cap), and B stays in E5-1. §9's code is written test-first (tests seen failing before the
code existed are logged in `runs/e5-1/*first-fail*.txt`; the rest are seen failing under sabotage,
`scripts/e5_1_sabotage.py` → `runs/e5-1/sabotage_log.txt`):

- **Guards:** `Genome.cat` and `Genome.assign` refuse genomes on different specs (`BrainSpec.same_as`: node count,
  label, weight kind, edge lists and anatomical weights) or with different brain configurations. The `init_*` fields
  are exempt: they decide how a genome is drawn, never how it runs, and 02's frozen opponent suite spreads them on
  purpose (`make_frozen_suite`, which the first version of the guard refused).
- **The mixed world:** `HuntWorld` takes one pin per world; `MixedPrey` gives each world its own kind and speed;
  `wormwars/e5/mixed.py` plays named settings, one per column.
- **The route cache:** `RouteTable`, keyed by (world seed, sequence index), with the spacing, drawing box and start in
  the key. It is filled on first use and kept, not pre-drawn for every index: drawing 64 routes for every world of
  every generation would cost more than it saves. The draw is E5-0's, and a life's waypoints are written in one step.
- **The GA rollout:** `wormwars/e5/ga.py`'s `TaskHRollout`, with the overflow (`SequenceOverflow`) and ledger
  (`LedgerError`, 1e-5) checks on every rollout and the highest sequence index kept; `evolve_batch` takes integer
  `weights` for the fitness and validation (off by default, which changes nothing).
- **The publication guard:** labels of 03's ensembles, N2permK, N2-rev and pilotSH, with or without a module, are an
  offence (`tests/test_publication_hygiene.py`, `NULL_GRAPH`); 01's SH1-SH5 and RD1-RD5 stay checked by proportion.
- **The fixed numbers:** `wormwars/e5/plan.py` (seeds, id blocks, graphs, admission), `settings.py`, `graphs.py`,
  `arms.py`; a test scans every tracked Python file for literals near E5-1's id and seed blocks.

**Numbers the design left open, fixed here before E5-1a runs** (`scripts/e5_1a.py`, `REGISTERED`):

- E5-1a's own cap: 6 hours, every stage and device together.
- Seeds for checks and the bench (never a reading): 1 517 000 + i; the mutation streams of step 8: 1 517 500 + k.
- Step 1: the old engine is `7d25460`, E5-0's formal code (Task H is unchanged from it to `a9ad7d9`); 18 settings ×
  3 hunters (the pursuit, E4s-1 run 0's C, L1 on its carrier) on the first 64 ids of the check block, with per-tick
  traces of 8 worlds per setting. The training shape is checked on 4 generation-0 G-N2-construction populations
  from the check seeds; the validation shape on E4s-1 runs 0 to 3's C over 256 ids. The weighted fitness and
  validation must equal the design's formula within 1e-12, with the same ranking.
- Step 3: σd from 512 of the SD block's 1 024 worlds per check. The scripted hunters play on the worm's interface, as
  in E5-0. Prey paths (a motionless hunter, 256 worlds per kind at route 0.5, walk 0.5 and wall 0.5) and the
  pursuit's first 30 ticks (64 worlds, H1-bite and route 0.5) agree if a world's largest absolute difference is at
  most 10⁻³ cells; a check passes if 99% of worlds agree. H1-ghost against Task N on CUDA passes within ±0.10 (the
  bitwise share is reported). Attack disabled: 256 worlds at H1-bite and route 0.5. Respawns: 64 worlds at
  H1-bite, route 0.5 and walk 0.5. State level: inputs uniform on [0, 1] times each sensor's gain at every sensor
  neuron, 300 ticks.
- Step 4: 6 generations (checkpoints at 0 and 5) of an N2 batch and of `SH-route-1020022` (a pilot graph the pilot
  does not evolve); the evaluation rate from 8 E4s-1 C genomes × 512 worlds at H1-bite, route 0.5 and walk 0.5.
- Step 5: the contrast is the score-weighted mean of per-world differences, with a normal 90% interval (z = 1.645)
  from the per-slot variances. The winner is chosen on generation 0's batch of pilot-training worlds.
- Step 6: the null graphs' signal is measured on generation 0 of run 0 per pilot graph (seeds 1 518 000 + 4j).
- Step 7: the suite chunk is checked at the four probe settings. In the batch shapes the genomes are tiled; the
  reference plays one strain × 512.
- Step 8: every parent's mutants are drawn at G-N2's scales (the module at 0.25, the host at 1).

### 14.1 After the code review (round 1, 2026-11-11; both "fix then run"; `docs/reviews/20261111-E5-1a-code/`)

Every fix taken. What changes from §14 above (kept as written; this replaces it where they differ):

- **Corrections of §14's text:** "18 settings" should read 19: E5-0 has 19 settings (`scripts/e5_0.py`'s
  `settings()`, and the 19 entries of `experiments/E5-hunter/E5-0/reading.json`), and the reference script plays all
  19. (§2's "18 read settings" is checked against E5-0's records before the pre-registration.) Step 5's interval is no
  longer normal: see below.
- **Old against new is now always against 7d25460**, in a smoke too (the first smoke compared the working tree with
  itself; Fable, Astra). The smoke's reference worlds are smoke ids at a 40-tick horizon; the formal run uses the
  check block's first 64 ids at 300 ticks.
- **Non-finite states stop Task H** (`play` checks positions, headings, energies and brain states; Fable): captures
  are integers and Task H has no progress, so nothing else in the GA would show a NaN.
- **Every comparison of per-world counts** (CPU against CUDA, H1-ghost against Task N on CUDA, the batch shapes
  against one strain × 512) is sized and judged the same way:
  - the SD comes from 512 SD-block worlds, per hunter or genome;
  - the check uses the largest required count over them (Astra), and records whether the half-width reached 0.03;
  - on mixed worlds, the estimate is the score-weighted mean with a stratified interval (t, Welch–Satterthwaite
    degrees of freedom), and the sizing uses the weighted mean's SD (Astra: a plain mean lets slot differences cancel);
  - every genome plays every world (Fable, Astra: the first composition code gave most genomes few or none);
  - plays hold at most 4 096 worlds, the suite chunk's 8 × 512 (the CUDA stage's largest is 4 × 512; corrected in
    round 2, where this line said 1 024).
- **The training-shape CUDA check and the ghost check are sized like the others** (Fable). Before, one was a single
  batch and the other a fixed 512 worlds.
- **Prey paths:** the motionless hunter has its attack disabled. The engine has no ghost mode for a hunter, so its
  body stays, alike on both devices. Path and trace checks use 256 worlds each, so "99%" allows two differing worlds.
- **Respawns** must occur (a check with none fails). Hand-stepped worlds check the ledger, the overflow and
  finiteness.
- **State level:** every genome at every shape (in groups of the shape's strains); a non-finite state fails.
- **Step 5's interval:** the stratified t interval above, which is conservative where one static slot carries a third
  of the weight (Fable).
- **The bench:**
  - It times a scoring batch (B's construction, 32 copies of a C champion per run) as well as generation 0, since
    captures drive respawns and host syncs (Fable).
  - The projection gives a low and a high total for every cut level. Each cut is recomputed from what it removes
    (§8's itemised evaluation; the first code subtracted 8 times the suite's episodes for cut 4; both).
  - The owner's cap is judged on the high projection. It covers the formal run, its evaluation and the 15% reserve;
    E5-1a runs under its own 6 hours.
  - The cap record is bound to the bench record. Later stages refuse a cap that nothing fits, and accept an earlier
    stage only if it explicitly passed or completed (Astra).
- **E5-1a's cap is checked before every play** and in every loop (Fable, Astra).
- **Equal integer numerators give exactly equal fitness** (checked), in place of a ranking comparison that a
  last-bit difference in the formula could break (Fable). The training-shape equivalence also runs the C champions,
  for frequent captures (Fable).
- **P's stage checks `g`** as well as `w` (Fable). `PL.GA` is pinned to E2's registered GA by a test (Fable).
- **For the pre-registration** (not E5-1a): `evolve_batch` also checkpoints generation 499, so §5's "last
  checkpoint (475)" and the candidate set must be fixed there (both). §9's formal readers, O0 at calibrated gains and
  P's routing comparison are not written yet; they come with the pre-registration and its review (Astra).

### 14.2 After round 2 (2026-11-11; Astra "fix first", Fable "fix first, no third round needed")

- **The 0.03 half-width is not guaranteed.** The design caps a check at 8 192 worlds, and with a large SD the cap
  binds. Each check records the uncapped requirement and whether the 0.03 was reached. Passing is the design's rule:
  the interval lies within ±0.10 (Astra).
- **The projection's high end** takes the larger of the generation-0 and scoring rates for every part. O0 counts both
  gain conditions per retained test run (2 × 32 × 64 episodes). That gives 458 752 episodes, or 393 216 with 16
  graphs; **§8's 229 376 counted one condition** (Astra).
- **E5-1a's own cap:**
  - The old-against-new child gets what is left of it and checks it before every play.
  - The bench projects E5-1a's remaining stages, the null champions' CPU sides included, and records whether they fit
    (Fable).
  - **If E5-1a's cap stops a stage midway, E5-1a stops and comes back to the owner.** The stage's start marker
    blocks a rerun until a dated amendment, with the owner's word, says what reruns.
- **The C-champion equivalence rows must capture** something. The null champions' CPU-against-CUDA checks include the
  mixed training shape (Fable).
- The reference worktree is checked before the equivalence stage's start marker (Fable). The pilot's record says that
  its null signal plays one population's shapes, not N2's four (Fable).


### 14.3 Amendment 1: E5-1a's state-level check (2026-11-11, after its stop; for review)

**What happened.** E5-1a's steps 1 and 2 passed on `aa36440`:
- **Step 1:** E5-0's engine and the working tree are identical on 1 045 arrays, covering 15 185 captures across 19
  settings and 3 hunters on 64 worlds at 300 ticks. The mixed world equals each slot alone, and the weighted fitness
  equals the formula to 4e-16.
- **Step 2:** all 24 graphs match 03r's content and raw-byte manifests, and P's checks pass.

Step 3 stopped on one check, the state level. Over 300 ticks, CPU against CUDA differed by up to 0.0025, 0.0044 and
0.011 at the training, validation and suite shapes for the 16 E4s-1 C genomes, against the 1e-4 tolerance.
Generation-0 genomes on the 4 pilot graphs stayed at 2e-6 to 1e-5. Every other check passed:
- 42 score-level checks, with estimates between −0.010 and +0.026 captures and intervals within ±0.06;
- H1-ghost against Task N on CUDA, identical in every world;
- prey paths, within 7.4e-5 cells;
- the pursuit traces, 254 of 256 worlds within 1e-3 cells at H1-bite (the check's limit; the largest difference 0.19 cells) and 256 of 256 at route 0.5;
- attack disabled, with 0 captures and 0 damage;
- 886 respawns, all at least D − R from the hunter.

The records are kept in `experiments/E5-hunter/E5-1/E5-1a/attempt-1/`.

**Diagnosis** (exploratory; `experiments/E5-hunter/E5-1/E5-1a/diagnosis/`). The same genomes were run under the same
inputs, in float64 on the CPU, as a higher-precision reference. At the stage's shapes, CPU float32 is 0.15, 0.46 and 0.35
from float64, and CUDA float32 is 0.15, 0.45 and 0.34. **The evolved champions amplify float32 rounding on any device:**
CUDA is as close to the reference as the CPU is, and the two float32 runs are 30 to 100 times closer to each other
than either is to float64. At 16 strains × 8 rows, batch composition on the CPU adds nothing (identical), and the
motor commands differ by at most 2e-5. The 1e-4 came from E4s-1's gate 2. That gate met it at 2.7e-6, but with
random N2 genomes and 04a champions, under inputs up to 0.35. Here the genomes are grafted and evolved, and the
inputs are stronger (uniform on [0, 1] times each sensor's gain).

**The amendment.** The state-level criterion becomes relative to float32's own error: per genome group and shape,
max|CUDA float32 − CPU float64| ≤ 1.5 × max|CPU float32 − CPU float64| + 10⁻⁴. CPU against CUDA is recorded beside it.
Generation-0 genomes are still held to about 10⁻⁴, since their float32 error is about 10⁻⁵. A sabotage (the GPU's
biases moved by 10⁻³) fails it (`runs/e5-1/amend1-sabotage.txt`). **This criterion was chosen after the failure was
seen;** the score-level checks fixed beforehand are the operative evidence that CUDA plays Task H as the CPU does.

**What reruns:** steps 1, 2 and 3 on the amended code. The design's guard requires every later stage on the same
code. Then the bench, then the owner's cap.

**Corrections and changes after the amendment's review** (2026-11-11, `docs/reviews/20261111-E5-1a-code/a1-*.md`;
both "amend and rerun", after tightening; Fable: no further round if taken as written):

- **Corrections of the text above:**
  - The H1-bite pursuit trace agreed in 254 of 256 worlds, not 255.
  - "The evolved champions amplify float32 rounding" is too broad. At 16 strains × 8 rows only run 1 exceeds 10⁻⁴
    between CPU and CUDA, and 13 of the 16 stay within 4.5e-5. The amplification is a tail over genomes and input
    histories, and it grows with the rows played.
  - The 2e-5 motor difference was measured at 16 × 8, not at the stage's shapes.
  - "Generation-0 genomes' float32 error is about 10⁻⁵" had no record; the rerun records it per genome.
  - "No further from the reference" overstated the rule: it allows 50% more error plus the floor. Both numbers are
    engineering choices made after the failure, not demonstrated accuracy bounds (Astra).
  - The pursuit's mixed score check reached a half-width of 0.0303, just above the 0.03 aim; it passes ±0.10.
- **Better evidence that the amplification does not reach the task:** the champions' per-world capture counts were
  identical between CPU and CUDA in 99.0 to 100% of worlds at every score check (24 rows, `attempt-1/cuda.json`;
  the review's "99.6" was rechecked). The scripted S-const and pursuit agree in fewer worlds (66 to 96%), with their
  means still within ±0.03 captures per episode.
- **The check as amended** (`scripts/e5_1a.py`, `state_level`), judged per genome, not per batch (Astra, Fable):
  - **one step, resynchronised,** at the registered 10⁻⁴: every tick CUDA steps from the CPU's float32 state, and
    its result must lie within 10⁻⁴ of the CPU's step (Fable). Local error is not amplified;
  - **free running,** for the champions: max|CUDA float32 − CPU float64| ≤ 1.5 × max|CPU float32 − CPU float64| +
    10⁻⁴;
  - **free running, for the generation-0 genomes:** the original CPU against CUDA ≤ 10⁻⁴ (Astra).
- **The sabotage, at the formal shape** (`scripts/e5_1a_state_sabotage.py` → `runs/e5-1/amend1-sabotage-formal.txt`;
  128 × 8, 300 ticks, the 16 champions):
  - E4s-1 run 2's CUDA copy, a stable genome sharing the batch with run 1, the most sensitive, gets its biases moved.
  - At +10⁻³ both checks fail for run 2 alone (one step 0.0026, free running 0.0076 against a bound of 0.00018).
  - At +10⁻⁵ both pass: that is below what the check resolves.
  - The clean run passes, with one step at most 5.5e-6.
- **CUDA is not bit-reproducible between runs here.** The clean run's largest free-running CPU–CUDA difference at
  128 × 8 was 0.0010, where attempt 1 had 0.0025 for the same genomes and inputs. These runs are outside
  `replay_mode`, where no exactness is claimed (rule 6), and the evolved champions amplify any difference. Not
  investigated further: the score checks are the evidence for the task.
- **The rerun:**
  - **The record:** attempt 2 is the record. A check that passed in attempt 1 and fails in attempt 2 is a stop.
  - **The cap clock:** attempt 1's 0.69 hours stay in E5-1a's cap; the diagnosis and the sabotage ran outside it
    (`runs/e5-1a-sabotage/` has its own clock).


### 14.4 A bug in Amendment 1's code, and a correction (2026-11-11)

Attempt 2 (steps 1 to 3 on `4e68da8`) passed, and its records are kept in `E5-1a/attempt-2/`. Afterwards, checking
its numbers against the sabotage run, I found that `state_level` judged only the first copy of each genome. At the
training shape the 16 champions are tiled 8 times (and the generation-0 genomes 32 times), each copy with its own
input history; the other copies were measured but not judged. The code now judges every strain and records, per
genome and shape, the worst copy, the number of copies and the number failed. The formal-shape sabotage, rerun on the
fixed code, fails all 8 copies of the altered genome at +10⁻³ and passes at +10⁻⁵ (`runs/e5-1/amend1-sabotage-formal.txt`).

**Correction of §14.3 and D391:** "CUDA is not bit-reproducible between runs here: … 0.0010, where attempt 1 had
0.0025" is wrong. The two numbers came from different reductions: one over every strain, the other over first copies
only. Over every strain the clean run gives 0.00254, as attempt 1 did, so no run-to-run difference was shown.

Steps 1 to 3 rerun on the fixed code as attempt 3, which is the record.
