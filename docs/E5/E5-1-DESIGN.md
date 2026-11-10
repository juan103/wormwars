# E5-1: evolving hunters on Task H, on N2 and on null graphs. Design

*Draft 2, 2026-11-11, after one round of review (Astra 6 and Fable 5.2: both "fix then proceed"; every must-fix
taken; [`docs/reviews/20261111-E5-1-design/`](../reviews/20261111-E5-1-design/), with draft 1 at `ae959a8`). For a
second look by both, then the owner. Not a pre-registration: nothing here has run on the GPU, and no Task H
evolution code is written. The owner said "sure" to this design round on 2026-11-10 (D389); the GPU needs their word,
separately, before any stage below runs on it. The scope is [`SCOPE.md`](SCOPE.md) (draft 2, D385) and E5-0's
results ([`experiments/E5-hunter/E5-0/RESULTS.md`](../../experiments/E5-hunter/E5-0/RESULTS.md), draft 2, D388). From
this round on the Anthropic reviewer is Fable 5.2; every earlier review in the repository was Fable 5.1's. What changed
from draft 1 is the last section.*

## 1. The two questions

The owner asked for two things in stage 05 (D385): a hunter built from what earlier stages made, and a null-graph arm,
"so 05 also asks whether N2's wiring helps a hunter". E5-1 asks both, kept apart.

1. **The build (descriptive).** Starting from the E4s-1 champions that E5-0 tested, which qualify at every rung
   zero-shot, does evolution on Task H give better hunters on fresh worlds and on prey speeds it did not train on, and
   how much of Task N do they keep?
2. **The test (confirmatory, to be pre-registered).** With the frozen L1 graft, the same interface, motor gains,
   generation-0 construction, GA and budget, do hunters evolved on N2 end with a higher held-out suite score than
   hunters evolved on the average graph of 03's SH-route ensemble?

**This answers a narrower question than the owner's** (both reviewers): whether N2 is a better *host for L1* than a
routing-constrained shuffle, at the end of a fixed budget. It does not isolate wiring from weight placement
(SH-route moves both), or evolutionary improvement from starting performance (O1c is the climb, O1 the endpoint). A
wiring-free anchor arm (§4) shows how much any host adds to the graft at all.

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
  checkpoint, and C and F differ in 13 of 16 runs (Astra). Every E4s-1 number below is C's.
- **E4s-1's champions decline at fast prey** (family mean 3.5 to 3.6 at route speeds 0.2 to 0.6, 2.04 at 1.0), where L1
  rises (4.51 at 0.8): room for the build arm.
- **The scale.** On the suite score (§3, defined after E5-0's reading, so exploratory), E4s-1's 16 champions average
  2.85 (SD 0.23, range 2.60 to 3.41), L1 on its carrier 3.01, E2d's 47 champions 0.76 (SD 0.22), generation 0 0.11
  (`scripts/e5_1_power.py` → `experiments/E5-hunter/E5-1/design-power.json`, `suite_score_e5_0`).
- **The host may add little.** In E4s-1, silencing the module left 0.11 targets, and unevolved L1 on a wiring-free
  carrier scores 3.01 on the suite against the evolved N2 champions' 2.85 (and 4.12 against 2.04 at route speed 1.0).
  Biases and τ on the read-out neurons evolve whatever the graph, so the difference between two hosts may be small,
  and may show which host interferes less rather than which helps (Fable). Hence the anchor arm and the host-wiring
  lesion probe (§4, §5).

## 3. The ladder: a fixed training mixture and a held-out suite, not a curriculum

**Why not a curriculum.** A curriculum that moves each run to harder prey when it succeeds gives each arm its own
training distribution, set by its own progress, which confounds the host with what it was trained on. A shared,
predetermined schedule would be fair too, but is not needed (Astra). The positive control's rise with speed also
removes the natural place to put rungs.

**The rule that replaces SCOPE.md §4:** train on a fixed mixture spanning the range E5-0 tested, and hold out speeds in
between and beyond. The rungs are chosen from E5-0's separation of the reused families (exploratory; said so).

**Training mixture.** Each strain's 8 training worlds per generation are one world per setting below; every strain
within a run sees the same 8 world ids (each run has its own schedule, `evolve_batch`):

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

**The selection fitness has the score's weights** (Astra; Fable's should-fix 1). Raw capture sums would weight the
strata 12.5%, 62.5% and 25%, against the score's thirds. The fitness is
(1/3)·[c₁ + (c₂ + … + c₆)/5 + (c₇ + c₈)/2], with c_k the captures in slot k: still unshaped captures, reweighted.
Raw counts are recorded.

**Validation:** 256 worlds, 32 per training setting, aggregated with the same weights, at every checkpoint (every 25
generations). The nine held-out settings never enter selection or checkpoint choice.

**The held-out test suite** (the formal reading; fresh world ids, never used in training, validation or any pilot):
every E5-0 setting under the bite rule, 17 in all, 512 worlds each (8 704), paired across hunters:
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

## 4. The arms

**The optimizer** is E2's GA, as E4s-1 ran it: population 32, 3 elites, truncation 8, 8 worlds per strain (§3),
checkpoints every 25 generations; the module's mutation at 0.25× 02's scales, the host's at 1×.

**500 generations,** fixed now, before any Task H data. E4s-1's M arm on Task N climbed from 2.22 at generation 0 to
6.86 at 500 and 7.08 at 999, 95% of its climb by 500 (`experiments/E4s-stereo-module/E4s-1/eval-training.json`,
`along`, the 16 M runs). That is another task and only N2. 02 found shuffles catching up late (Fable), so a shorter
budget may favour whichever arm starts ahead: the endpoint is read "at 500 generations", and Δ along training from the
validation checkpoints shows whether the gap is still closing.

**One composition for every arm: 4 runs per batch,** 128 strains × 8 worlds (Astra's must-fix 7). A batch holds one
graph (`evolve_batch` takes one `BrainSpec`), so each SH-route graph is one batch of its 4 runs, and N2's 32 runs are 8
batches of 4. Exactness is claimed within one composition only (rule 6); with one composition the arms differ in graph,
not in shape.

| Arm | Host | Generation 0 | Runs | Batches | Role |
|---|---|---|---|---|---|
| **G-N2** | N2 + L1 | L1 on random N2 (E4s-1's M construction, `embedded_population`) | 32 | 8 | the test, N2 side |
| **G-SHr** | SH-route + L1 | the same construction on each graph | 20 graphs × 4 | 20 | the test, null side |
| **A0** | none (the carrier) | L1 on its carrier (forward 1.0, turn 0.2); host-to-host weights pinned at 0, host biases and τ free | 8 | 2 | anchor, descriptive (Fable) |
| **P** | N2perm4, 5, 6 + L1 | the same construction | 3 graphs × 4 | 3 | weight placement, descriptive (Fable) |
| **B** | N2 + L1 | one E4s-1 C champion, 32 identical copies (C2's construction) | 16 | 4 | the build, descriptive; after the test |

**Why L1 is in both test arms.** Draft 1 said the no-graft comparison would be "a floor against a floor". That is
withdrawn: E2d's champions were evolved on Task N and transferred zero-shot, which says nothing about how ungrafted N2
or SH-route would evolve on Task H (Astra). The reason that stands: the test asks whether a reusable, competent
component does better in one host than another, under control. The module is competent; a starting *population* is not
(E4s-0 found most random N2 backgrounds score zero), and that is what the climb measures. L1 has its own noses and its
16 synapses onto the 8 turn read-out neurons (SMDDL/R, SMDVL/R, RMDDL/R, RMDVL/R), which every SH-route graph keeps by
name. L1 and the gains were designed and settled on N2 (E4s-0), which every claim states.

**SH-route,** described exactly (Astra): 03's ensemble that keeps N2's degree sequence and imposes upper bounds, at
N2's values, on the number and anatomical weight of direct edges from the six food pairs of M0, R1 and R2 onto the
read-out; it moves weight placement as well as edges, and does not match every routing property. 02's tripwire made
matched routing a requirement of later comparisons. **The graphs, by name:** 03r's `SH-route-1020000` to
`SH-route-1020019` for the formal run; `SH-route-1020020` to `SH-route-1020023` for the pilot (§7). They were never
selected on any measure; their 03r covariates (P4, calibrated gains) are reported against their E5-1 scores,
descriptively (Fable).

**Motor gains: 4.0 and 2.0 for every graph,** a scientific choice. Draft 1's engineering reason was wrong: with one
graph per world, a graph's own gains could go into its configuration, and `PreyBrain` inverts its commands through
whatever gains it is given, so the prey would be unchanged (both). The reasons that stand:
- calibration changes the host-plus-module phenotype, so it answers another question (Astra); in particular L1's
  output enters through the same read-out, so a calibrated turn gain rescales L1's drive as well;
- the gains and L1 were developed on N2, and that is stated, not corrected.

Draft 1's "a difference in drive counts as part of what the wiring does" is withdrawn. 03r's calibration (on 02's
foraging task, `experiments/03r-replication/supplement.json`) gives N2 a turn gain of 2.08 and the median SH-route
graph 2.95, so N2's random brains give about 1.4 times the turn drive at equal gain; but N2perm4 to 6, which keep N2's
edges and permute its weights, need 2.92 to 3.07 too. On three draws on another task this points to weight placement,
not edges (Fable). The direction of the bias is not known: a louder host may drown L1, a quieter one may move too
little. So: the achieved forward and turn drive, the signed turn offset and the read-out saturation are reported for
every graph at G0 and at C; G0 is also measured at each graph's calibrated gains (minutes); arm P separates N2's
weights from its edges, descriptively.

**Seeds** (a block no earlier stage used; E5-0's run seed was 1 500 001). G-N2 run i uses seed 1 510 000 + i; B run
i uses the same seed (B and G-N2 are paired, descriptively, on training worlds and breeding stream); G-SHr graph j (0
to 19), run r (0 to 3) uses 1 511 000 + 4j + r; A0 run i 1 512 000 + i; P graph k, run r 1 513 000 + 4k + r; the
pilot's N2 populations 1 519 000 to 1 519 003, its null runs 1 518 000 + 4j + r.

**World ids** (985 million, unused before): training from each run's seed, base 985 000 000, span 500 000;
validation 985 600 000 + 256; the suite 985 700 000 + 8 704; bridges 985 720 000 + 1 024; O0's populations
985 730 000 + 64; mutational sensitivity 985 740 000 + 256; the CUDA and composition checks 985 750 000 + 5 120;
the selection-signal pilot 985 760 000 + 256. A test checks that the blocks are disjoint from each other and from
every earlier range. G-N2 against G-SHr is **an independent-samples comparison with
clustering** (graphs) and paired evaluation worlds; there is no paired unit across those arms (Astra). B's 16 starts are
E4s-1's C genomes, fixed by run, checkpoint index and sha256 in the pre-registration.

## 5. Readings

**The registered genome is C,** the best validation checkpoint (§3's 256 worlds). F is chosen on 8 worlds, one per
setting, which is noisier than in E4s-1 (Fable); C is fixed now, before any data. **G0** is the generation-0 training
winner (checkpoint 0), evaluated on fresh worlds (Astra). F is reported from its training and validation numbers only.

Every C and G0 is one strain on all 8 704 suite worlds (§3).

**O1 (confirmatory): N2 against the average SH-route graph, on C's suite score.**
- **Estimand:** Δ = (the mean over G-N2's 32 runs) − (the mean over G-SHr's 20 graph means, each the mean of its 4
  runs). It compares N2 with the ensemble's average graph; "N2 ahead" does not mean N2 is unusual within the
  ensemble (Fable).
- **Interval:** 90%, over N2's runs and over the graph means, independently, at one level (`wormwars/e5/stats.py`).
  Draft 1's nested bootstrap counted within-graph noise twice (Astra). Inference is conditional on the frozen suite.
- **Rules, symmetric, in order** (`stats.label`, tested):
  1. lower bound above 0: **"N2 ahead, estimate at least δ"** if Δ ≥ δ, otherwise **"N2 ahead, estimate below δ"**;
  2. upper bound below 0: **"SH-route ahead, estimate at least δ"** if Δ ≤ −δ, otherwise **"SH-route ahead, estimate
     below δ"**;
  3. both bounds inside (−δ, δ): **"no difference of δ either way"**;
  4. otherwise **"inconclusive"**.

  Draft 1's rules had no outcome for a detected but small advantage (Astra) and needed a margin in one direction only
  (Fable). Neither label 1 establishes that the true difference exceeds δ (Astra).
- **δ = 0.25 captures per episode on the suite score,** fixed now: one more capture every four episodes, about the
  between-champion SD of E4s-1's champions (§2), and 9% of their mean. Its size against A0 is reported.
- **The interval's construction** is the percentile bootstrap unless the simulation below, rerun with a Welch-type
  interval beside it before the pre-registration, finds the Welch interval's coverage nearer 90% over the whole grid;
  then that is registered. A data-free choice.
- **Beside Δ:** the latent between-graph SD of SH-route, Δ over that SD, and how many of the 20 graph means exceed
  N2's mean (Fable).

**The simulation** (`scripts/e5_1_power.py`, 2 000 simulations × 2 000 resamples per cell, normal scores; the SDs are
assumptions, since no E5-1 data exists). At the chosen counts (32 N2 runs; 20 graphs × 4 runs):

| Run SD | Graph SD | Δ = 0: "no difference of δ" | Δ = 0: any "ahead" label | Δ = δ: "N2 ahead, ≥ δ" | Δ = 2δ: "N2 ahead, ≥ δ" | coverage at Δ = 0 |
|---|---|---|---|---|---|---|
| 0.2 | 0.15 | 0.89 | 0.11 | 0.49 | 1.00 | 0.89 |
| 0.3 | 0.3 | 0.72 | 0.11 | 0.50 | 1.00 | 0.89 |
| 0.3 | 0.45 | 0.40 | 0.12 | 0.50 | 0.98 | 0.88 |
| 0.45 | 0.45 | 0.19 | 0.12 | 0.50 | 0.96 | 0.88 |

- **A true difference of 2δ is found 96 to 100% of the time; one of exactly δ, about half the time,** at any count,
  because label 1 needs Δ̂ ≥ δ (Fable). The counts are chosen for the null and 2δ, not for δ.
- **A true null reads "no difference of δ either way" 72% of the time** at run and graph SDs of 0.3, and much less if
  graphs differ more. Draft 1's 16 runs and 16 graphs × 2 gave 38% there. More graphs help most: 24 graphs × 4 would
  give 78% at four more batches; 20 × 4 is chosen for cost.
- **The percentile interval under-covers slightly:** 86 to 90% against 90% over every simulated design, and 10 to 14%
  of true nulls get some "ahead" label against 10% nominal. Hence the Welch check above.

**Companion sentences, fixed in advance** (Fable), each completed with "under this GA, budget of 500 generations, task
mixture, motor gains and graft":
- *"N2 ahead, estimate at least δ":* "Hunters evolved on N2 ended with a higher held-out suite score than hunters
  evolved on the average SH-route graph, by an estimated Δ [lo, hi]." *"…below δ":* the same, "by less than δ in
  estimate". The SH-route labels mirror these.
- *"No difference of δ either way":* "No difference of 0.25 captures per episode or more between N2 and the average
  SH-route graph was found, in either direction." Never "the worm wiring is neutral" (the roadmap's table).
- *"Inconclusive":* "The data neither show a difference nor exclude one of 0.25."
- Always beside it: the anchor. If neither G-N2 nor G-SHr exceeds A0, "the host's wiring adds nothing measurable to
  the graft under this design, and O1 compares how much each host interferes." O1 is an endpoint, not "a better host
  for evolving" (that is O1c).

**Beside O1 (descriptive):**
- **O0, generation 0:** the same contrast on the generation-0 *populations* (all 32 strains of each run on 64 fresh
  mixture worlds), not on their best, which mixes host quality with an extreme draw (Fable).
- **O1c, the climb:** C − G0 per run, by arm, and the difference of the arms' climbs. Δ along training from the
  validation checkpoints (training settings only; free).
- **The anchor:** each arm's C against A0's on the suite; and the **host-wiring lesion** on every C (host-to-host
  weights zeroed, biases kept) (Fable).
- **P:** N2perm's three graphs beside N2 and SH-route; three graphs carry no inference.
- **Per stratum and setting,** trained speeds against held-out speeds.

**O2, the build (descriptive).** Per B run, C − its start (the E4s-1 C champion, zero-shot) on the suite: the mean and
a 90% bootstrap interval over the 16 runs; "B improved on its starting champion" needs the interval above 0. Read beside
L1 on its carrier, on the same worlds, and at fast route speeds (0.8 to 1.0). B against G-N2, run by run, compares two
starting protocols (32 copies of an evolved brain against 32 random backgrounds, at unequal total work), not the value
of pretraining (Astra).

**O3, Task N kept (descriptive).** For B: H1-ghost (Task N) of C against its start, paired, on 512 fresh worlds,
and at B's checkpoints 100 and 250 ("during adaptation", SCOPE.md §7). **"Keeps Task N"** if the loss's 90% upper bound
is below 0.5 targets per episode; otherwise the loss is reported (Astra). For the test arms H1-ghost is reported too
(free), but it is not inherited function: they never trained on Task N (Fable).

**Probes, on every C and G0,** at four settings (H1-bite, route 0.5, route 1.0, walk 0.5), 512 worlds each: an
expansion of the two settings E5-0 froze for its fixed probes, H1-bite and route 0.5 (Astra). They are `constant`,
`mirrored`, the world's `mean`, the module-only `mean` (L1's noses fed the mean while the host's sensors are real,
the intervention in E4s-1's D) and the body probe, reported as signed paired contrasts with intervals, per genome.
**No qualification is claimed** across the 17 settings; the probes are descriptive.

**References on the formal suite worlds:** the stationary and blind hunters, E1's frozen S-const, the pursuit
reference and L1 on its carrier, rerun on the 8 704 suite worlds, since E5-0's values are on other worlds (Astra).

**Never a reading:** energy from bites (logged only), damage shares (D026's lesson), training worlds.

## 6. Failure handling (fixed now; Astra's must-fix 10)

- **Admission order:** the 28 test batches interleaved in a fixed order, frozen in the pre-registration (N2 batch 1,
  then SH-route graphs 0 to 1, then N2 batch 2, …, proportionally), so a stop leaves a balanced set; then A0, P, and B.
- **A technical failure** (a crash, a non-finite state, a ledger outside tolerance, a target sequence exhausted) reruns
  the batch once from its seed on the same code. A second failure removes the batch's unit: 4 N2 runs, or one
  SH-route graph. No unit is ever replaced by another graph or seed, and no run is dropped for scoring poorly.
- **O1 is read** only if at least 28 of 32 N2 runs and 18 of 20 graphs (each with all 4 runs) complete. Otherwise it is
  withheld, the completed units are reported descriptively, and the shortfall is a dated deviation.
- **The cap:** if the cap stops training, the same rule applies to what completed. The evaluation reserve is frozen
  before training and cannot be spent on training.

## 7. Before the formal run: E5-1a (GPU; the owner's word first)

Exploratory, with stop rules fixed here. **No evolution on N2 in the pilot,** and no N2-against-null evolutionary
contrast (Astra: a pilot that evolves both sides runs an exploratory version of the confirmatory comparison, whatever
its seeds). Every count, δ and the generation number are already fixed above, so no choice depends on pilot data
except the projected cost and the owner's cap.

1. **Task H against itself, after the changes (rule 7; Astra's must-fix 8).** The mixed world and the route cache (§9)
   change task execution. On the CPU, the current Task H (E5-0's code) against the revised one, per setting and in the
   mixed world against each slot's single-setting run: capture counts, the event tables, prey trajectories, respawns
   and skipped sequence entries, damage and the ledger, bit for bit, on worlds with deliberately frequent captures.
   The new GA rollout against a serial reference (`play.py` tiles one world list across strains; `evolve_batch` gives
   each run its own schedule). E5-0's 68 arrays and the ghost against Task N are re-run. **Stop** on any difference.
2. **Task H on CUDA** (both reviewers):
   - CPU against CUDA, on 1 024 worlds per setting at H1-bite, route 0.5 and 1.0, walk 0.5, wall 0.5: E1's frozen
     S-const, the pursuit reference, L1 on its carrier, E4s-1 run 0's C, and a scoring grafted SH-route genome
     (from the pilot graphs). **Pass** if the 90% paired interval of CUDA − CPU lies within ±0.10 for each (a fixed
     ±0.05 on 512 worlds could fail by chance under bites; Fable);
   - prey paths with a motionless ghost hunter, CPU against CUDA, for each prey kind; early-tick traces of the pursuit;
     H1-ghost against Task N on CUDA; the attack-disabled check (zero captures and damage); respawns;
   - **state level:** CPU against CUDA, open loop under identical imposed input histories, 16 grafted N2 and 16
     grafted pilot SH-route genomes, the maximum absolute difference over 300 ticks at most 10⁻⁴, at the training and
     the evaluation shapes;
   - **composition:** the same 16 + 16 genomes scored in the training composition (4 runs × 32 strains × 8 worlds) and
     the evaluation composition (1 strain × 1 024): each mean within the same paired ±0.10 (Astra);
   - the ledger balances on CUDA at T0's tolerance on every episode above.
   **Stop** on any failure; diagnosis is a dated, reviewed amendment.
3. **The graphs.** The 20 formal and 4 pilot SH-route graphs and N2perm4 to 6 rebuilt from 03r's record and checked
   against both manifests (arrays everywhere, raw bytes where zlib allows, D106); L1's 16 output edges and noses
   present after grafting; every interface neuron present; each run record will carry its graph's hashes. **Stop** on
   any mismatch.
4. **The selection signal, on N2's construction only** (pilot seeds 1 519 000 to 1 519 003, never formal): each
   generation-0 population's 32 strains on the training mixture's actual 8-world batches (the fitness spread among
   strains) and on 256 mixture worlds (the module-only `mean` contrast of each strain). **Stop** if, in fewer than 3 of
   the 4 populations, at least one strain's module-only `mean` contrast has a 90% interval above 0: selection would
   have no scent-dependent signal to act on. "Any capture" is not used: a motionless hunter catches 0.21 to 0.26 per
   episode on routes from speed 0.4 (both).
5. **The null pilot:** the same measurements on the 4 pilot SH-route graphs, reported, never a stop (a failure on
   null graphs is a finding, Fable); then 2 of them evolved for 100 generations, 4 runs each, at the formal shape, for
   the rates and to see that a grafted null climbs on Task H. Not read beside N2.
6. **Mutational sensitivity** (SCOPE.md §7), sized: 64 mutants at the arms' scales around each of B's 16 starts and
   around 8 generation-0 bests (4 N2 pilot, 4 null pilot), on 256 mixture worlds (393 216 episodes): the median share
   of the parent's score and the share below 0.7, as E4s-0 reported. Measured, not a stop.
7. **The bench and projection:** every shape timed with route respawns; stage caps and an evaluation reserve frozen
   before training. If the projection exceeds the owner's cap, cuts in this order, fixed now: (1) B moves to a later
   stage; (2) P is dropped; (3) the probes shrink to H1-bite and route 0.5; (4) SH-route goes to 16 graphs (a true null
   then reads "no difference" 64% of the time instead of 72% at SDs of 0.3). The test arms and A0 are not cut further:
   if they do not fit, E5-1 comes back to the owner.

## 8. Cost (rough; replaced by the bench)

**Rates on Task N:** E4s-1's ten 8-run batches took 4 876 to 5 151 s for 1 000 generations (mean 4 984 s, 1.38 hours;
both reviewers corrected draft 1's 1.35), about 4.98 s per generation with breeding and checkpoints. E1 timed the
rollout alone at about 4.7 s at 8 runs and 3.04 s at 4 (`freeze.json`, `throughput_04a_shape`), so about 0.3 s per
generation is breeding and checkpoints, and **a 4-run batch takes about 3.35 s per generation, 0.47 hours per 500
generations.** Draft 1 compared a rollout-only null rate with N2's full rate (Fable).

**Task H's overhead, f, is unknown:** two swarms, combat, per-capture respawns, the mixed world. Fable's warning: eight
separate worlds per generation would be far worse (about 18 s per generation), which is why §9 builds one mixed world.

| Part | Batches or episodes | at Task N's rate | f = 1.5 | f = 2 |
|---|---|---|---|---|
| G-N2 + G-SHr (the test) | 28 batches | 13.0 h | 19.5 | 26.1 |
| A0 | 2 | 0.9 | 1.4 | 1.9 |
| P | 3 | 1.4 | 2.1 | 2.8 |
| B | 4 | 1.9 | 2.8 | 3.7 |
| Evaluation: C and G0 of 148 runs on the suite (2.58 M episodes), probes (3.03 M), lesions, bridges, O0 populations, references (about 0.8 M); 6.4 M at E4s-0's 306 to E4s-1's 465 episodes per second | | 3.8-5.8 | 5.7-8.7 | 7.6-11.6 |
| E5-1a: checks, null pilot, mutational sensitivity (0.39 M), bench | | about 1.5 | 2.2 | 3 |
| **Total** | | **22-25** | **34-37** | **45-49** |

**So E5-1 is likely 35 to 50 GPU-hours; the confirmatory part alone (the test, A0, their evaluation, E5-1a) about 28
to 40.** A reserve of 15% for reruns goes on top. Every number above is replaced by the bench; the cap is the owner's.

## 9. New code (each test-first; sabotage where a check cannot fail)

- **The mixed world** (Fable's must-fix 1): `play.py` takes one prey, one rule and one pin per `HuntWorld`;
  `PreyBrain` has one kind and one speed. The world gets per-world prey kind, speed and pin, so the 8 slots run in one
  rollout. Checked slot by slot against the single-setting path (§7.1).
- **The route cache:** `_route_for` loops in Python over worlds at every capture. It is replaced by a table pre-drawn
  per (run seed, world id, **sequence index**), the existing key: `HuntWorld._capture` can skip sequence entries, so a
  life is not a capture count (Astra). Equality with the current sampler tested.
- **The GA rollout for Task H:** the hunter as swarm 0 and the prey as swarm 1 in every world, the weighted fitness
  (§3), against a serial reference.
- **Guards** (both): `Genome.cat` and `Genome.assign` refuse mismatched specs, compared by value (`evo/genomes.edge_hash`
  and the node count, metadata and configuration), since `moved()` makes new spec objects. The regression case is two
  equal-sized grafted graphs wired differently; equal specs built separately must still combine. `Genome.cat` has many
  call sites, so the whole suite runs.
- **The publication guard:** a label of the form `SH-route-…+L1` has no entry in the anatomical reference set, so
  `tests/test_publication_hygiene.py` would report no offence. Null-graph genomes get an explicit prohibition, with a
  sabotage check (Astra).
- **Arms:** A0's mask (host-to-host weights at 0 and pinned, host biases and τ free) in `arm_scales`; P's graphs
  (03r's `exp03.py` builds N2perm4 to 6); the host-wiring lesion; G0 at calibrated gains.
- **Readings:** the suite score, `stats.py` (written and tested: `tests/test_e5_stats.py`, seen failing before the code
  existed and under a sabotage of the graph-mean bootstrap, `runs/e5-1/`), O0, O1c, O2, O3, the probes.

The per-tick host syncs in `hunt.py` are measured by the bench and removed only if they dominate, with §7.1 rerun.
Genome files stay local (rule 1). Null graph files are never committed: they carry permuted anatomical weights.

## 10. What E5-1 cannot show

- **That N2's wiring helps hunting in general.** Only whether N2 hosts L1 better than the average SH-route graph under
  this GA, budget, mixture, gains and arena. SH-route moves weights as well as edges; P's three graphs only hint at
  which matters.
- **The roadmap's gate** (captures from a frozen suite of competent prey on unseen maps): H3's organisms and H4's maps
  are not built. E5-1's suite is scripted prey in an empty arena.
- **Transfer to new prey:** the held-out settings are other speeds of trained prey kinds.
- **Anything about worm predation** or real chemotaxis (stereo is a game-design choice, E4s).
- **A history between G0 and C,** or why a host helps; the probes interpret, they do not decide.
- **Claims for stages 05 to 08 that need the collective-behaviour survey** the roadmap asks for; E5-1 makes none.

## 11. For round 2 and the owner

- **Round 2** (both reviewers): are the must-fixes met; is the anchor arm right; is 500 generations acceptable; is
  the Welch check enough for the interval; is anything in §7 still leaking the comparison.
- **The owner:** the cost (about 35 to 50 GPU-hours, 28 to 40 for the confirmatory part), and whether B belongs in
  E5-1 or a later stage.

## 12. Changes from draft 1

| Draft 1 | Draft 2 | From |
|---|---|---|
| B starts from F | From C, the genomes E5-0 tested (C ≠ F in 13 of 16 runs) | Astra 1, Fable M4 |
| An evolutionary pilot on N2 and null graphs | No N2 evolution in the pilot; N2 only in fixed-genome checks and generation-0 measures; null-only evolution | Astra 2, Fable M5 |
| Gains: "an engine change"; "drive is part of what wiring does" | A scientific choice; the engine claim and the drive claim withdrawn; drive at G0 and C; G0 at calibrated gains; arm P | Astra 3, Fable M2 |
| Raw capture sums for selection | Weighted to the score's strata; validation defined | Astra 4, Fable should-fix 1 |
| No outcome for a small detected difference; one-sided margin | Six symmetric labels; companion sentences | Astra 5, Fable M6 |
| Nested bootstrap | One level over N2 runs and graph means; simulated coverage; a Welch check | Astra 6, Fable 8 |
| 8 runs per batch for N2, 2 for nulls | 4 runs per batch everywhere; a composition check | Astra 7, Fable 9 |
| "Engine changes are none beyond the guard" | Task H against itself after the changes; the mixed world; the route cache by sequence index; a serial reference | Astra 8, Fable M1 |
| A `Genome.cat` guard | `cat` and `assign`, by value; the publication guard; graph hashes in run records | Astra 9, Fable 12 |
| No failure handling | §6 | Astra 10 |
| 16 N2 runs; 16 graphs × 2; δ after a pilot; 1 000 generations, maybe 500 | 32; 20 × 4; δ = 0.25 now; 500 generations now, from E4s-1's Task N curve | Fable M5, M6; simulation |
| — | A0, the wiring-free anchor, and the host-wiring lesion | Fable M3 |
| Stop if no strain captures anything | A module-dependent signal, on N2 only | Fable M5, Astra 10 |
| CUDA checks on four hunters at 0.05 | Wider set, paired ±0.10 on 1 024 worlds, 16 + 16 genomes at state level, prey paths, ghost on CUDA | both |
| "a floor against a floor"; "transfer"; "inherited" for G-N2; "E5-0's set" of probes; H probe | Withdrawn or corrected | Astra 12, 14, 16; Fable 2, 11, 15 |
| Cost 30-45 h | 35-50 h, recomputed on one basis, with a reserve | both |
| Graphs by index | By name | Astra, Fable 14 |
