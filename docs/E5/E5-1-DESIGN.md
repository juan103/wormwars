# E5-1: evolving hunters on Task H, on N2 and on null graphs. Design

*Draft 1, 2026-11-11, for review by Astra 6 and Fable 5.2. Not a pre-registration: nothing here has run, no code is
written, and the GPU has not been used for Task H. The owner said "sure" to this design round on 2026-11-10 (D389);
the GPU needs their word, separately, before any stage below runs on it. The scope is [`SCOPE.md`](SCOPE.md) (draft
2, D385) and E5-0's results ([`experiments/E5-hunter/E5-0/RESULTS.md`](../../experiments/E5-hunter/E5-0/RESULTS.md),
draft 2, D388). From this round on the Anthropic reviewer is Fable 5.2; every earlier review in the repository was
Fable 5.1's.*

## 1. The two questions

The owner asked for two things in stage 05 (D385): a hunter built from what earlier stages made, and a null-graph arm,
"so 05 also asks whether N2's wiring helps a hunter". E5-1 asks both, kept apart:

1. **The build (descriptive).** Starting from E4s-1's champions, which already qualify at every rung zero-shot, does
   evolution on Task H give better hunters on held-out worlds and held-out prey settings, and do they keep Task N?
2. **The test (confirmatory, pre-registered).** From matched starts and matched budgets, do hunters evolved on N2 score
   higher on a held-out prey suite than hunters evolved on null graphs from one of 03's validated ensembles?

The second is the first evolution on null graphs since 02 (03a evolved on one SH-mirror graph in a pilot; 03, 03r, 03h
and the memory thread measured random brains only). It needs new engineering (§8) and its own checks (§6).

## 2. What E5-0 gives this design

- **Task H works on the CPU** (old engine against new, and H1-ghost against Task N, bit for bit), and every one of the
  18 read settings is solvable and not too easy. **It has never run on CUDA.**
- **The ladder has no fall-off point.** The observation-limited positive control, and both fixed-parameter references,
  catch fast route prey more often than slow ones (4.57 to 7.72 for E1's frozen navigator). SCOPE.md §4's rule
  ("set the ladder where the positive control falls off") cannot be applied (§3 replaces it).
- **The families separate:** E4s-1's 16 champions and L1 on its carrier qualify everywhere; E2d's 47 N2-only champions
  stop once the prey moves (route 0.1 to 0.6, movers 0.25 to 0.75); generation 0 never qualifies.
- **Stereo use is part of the gap, not all of it** (the `mean` probe costs E4s-1 1.13 at H1-bite, E2d 0.01).
- **E4s-1's champions decline at fast prey** (family mean 3.5 to 3.6 at route speeds 0.2 to 0.6, 2.04 at 1.0), where L1
  rises (4.51 at 0.8). That is room for the build arm to improve.
- **A scale for effects.** On a three-strata score (§3: static, route, movers, equally weighted; computed after the
  reading, exploratory), E4s-1's 16 champions average 2.85 with a between-champion SD of 0.23 (range 2.60 to 3.41);
  L1 on its carrier 3.01; E2d's 47 average 0.76 (SD 0.22); generation 0, 0.11. (Scratch arithmetic from
  `reading.json`; the pre-registration will cite a committed script.)

## 3. The ladder: a fixed training mixture and a held-out suite, not a curriculum

**Why not a curriculum.** A curriculum that moves each run to harder prey when it succeeds gives each arm its own
training distribution, set by its own progress. In the N2-against-null test that confounds wiring with what each arm
was trained on. A fixed mixture keeps the training distribution identical across arms. The positive control's
monotone rise (§2) also removes the natural place to put rungs.

**The rule that replaces SCOPE.md §4:** train on a fixed mixture spanning the range E5-0 tested, and hold out settings
in between and beyond, so the suite tests interpolation and transfer as well as fresh worlds. The rungs are chosen
from E5-0's separation of the reused families (exploratory; said so), not from the positive control.

**Training mixture** (each generation's 8 training worlds per strain; every strain in a generation sees the same 8
world ids, as E2's GA does; slot k of the 8 always holds setting k):

| Slot | Setting | Why |
|---|---|---|
| 1 | H1-bite | the static rung |
| 2 | H2 route, s = 0.2 | slow route |
| 3 | H2 route, s = 0.4 | where most E2d champions stop |
| 4 | H2 route, s = 0.6 | where none of E2d qualifies |
| 5 | H2 route, s = 0.8 | where E4s-1 declines and L1 peaks |
| 6 | H2 route, s = 1.0 | the fastest |
| 7 | random walk, s = 0.5 | an unpredictable mover |
| 8 | wall follower, s = 0.5 | a wall-bound, weakly reactive mover |

**The held-out test suite** (the formal reading; fresh world ids, never used in training, validation or any pilot):
every E5-0 setting under the bite rule, 17 in all, at 512 worlds each (8 704), paired across hunters:
- **trained settings on new worlds:** H1-bite, route 0.2, 0.4, 0.6, 0.8, 1.0, walk 0.5, wall 0.5;
- **held-out settings:** route 0.1 (below the range), 0.3, 0.5, 0.7, 0.9 (between), walk 0.25 and 0.75, wall 0.25 and
  0.75.

**The suite score** of a genome: the mean of three strata, equally weighted: static (H1-bite), route (the mean over
the 10 route speeds), movers (the mean over the 6 H2b settings). Equal strata stop the 10 route settings from
dominating. Each stratum and each setting is reported beside it, trained and held-out apart.

**Bridges, descriptive:** H1-ghost (Task N exactly) measures what is kept of Task N, the inherited function SCOPE.md §7
asks to be tested during adaptation. H1-reach is reported beside it.

**Known limits carried over:** the random-walk prey spends up to 27% of its moves against the wall at s = 0.75 (E5-0
§2); the wall follower is weakly reactive. Neither is changed, so E5-0's numbers stay comparable.

## 4. The arms

The optimizer is E2's GA, as E4s-1 ran it: population 32, 3 elites, truncation 8, 8 worlds per strain, checkpoints
every 25 generations on 256 validation worlds; unshaped (the score is captures summed over the 8 training worlds).
Generations: 1 000, as E4s-1, unless the bench (§7) forces fewer; the number is fixed before the formal run.

| Arm | Graph | Generation 0 | Module mutation | Runs | Role |
|---|---|---|---|---|---|
| **B** | N2 + L1 | one E4s-1 M champion (F of run i), 32 identical copies (C2's construction) | 0.25× | 16 (one per E4s-1 run) | the build, descriptive |
| **G-N2** | N2 + L1 | L1 on random N2 (E4s-1's M construction, `embedded_population`) | 0.25× | 16 | the test, N2 side |
| **G-SHr** | SH-route + L1 | L1 on random genomes of each graph, the same construction | 0.25× | 16 graphs × 2 runs | the test, null side |

**Why the graft is in both test arms, not neither.** Without it, the test compares two arms that, judging by E2d
(N2 only, 47 champions), do not get past the moving rungs: a floor against a floor. With it, both arms start from the
same competent stereo core with its own noses and its own 16 synapses onto the 8 turn read-out neurons (SMDD/V, RMDD/V,
which every null keeps by name), and the question becomes **whether N2 is a better host for evolving a hunter than a
routing-matched shuffle.** That is narrower than "does N2's wiring help a hunter", and every claim says so. A no-graft
pair is an option for the review (§10).

**Why SH-route.** 02's tripwire made matched food-to-motor routing a registered requirement of later comparisons
(02's README, "Tripwire fired"), and SH-route is 03's ensemble that keeps N2's degrees and caps direct read-out edges
and weight for the food pairs. It moves weight placement as well as wiring, so a difference does not isolate wiring
(03's caveat, carried over). **The graphs:** the first 16 of 03r's 256 SH-route graphs by index (validated, manifest-
checked, never selected on any measure), excluding any used in a pilot here (§6's pilot uses graphs 17 to 20 of the same list).

**Motor gains: N2's for every graph.** Task N and Task H run at fixed gains of 4.0 forward and 2.0 turn, chosen on N2
(D014). 02, 03 and 03h calibrated each graph in-world instead, and 03a's one Task N-mono calibration moved an SH-mirror
graph to 6.27 and 3.22. Here calibration is rejected, for two reasons:
- L1's output enters through the same turn read-out, so a calibrated turn gain rescales the graft's gain too (a gain
  of 3.22 against 2.0 is 1.6 times the graft's drive, and higher stereo gains help on Task N: E4s-0's sweep);
- the prey's scripted commands are inverted through the gains (`PreyBrain` takes them explicitly), and the world has
  one gain pair per world object, so per-graph hunter gains need per-swarm gains: an engine change.

Same body, same gains, same graft: the achieved drive of each graph's generation-0 brains is measured and reported
(§6), and a difference in drive counts as part of what the wiring does. The review may disagree (§10).

**Pairing.** G-N2 run i and B run i share seed 1 170 000 + i (training worlds and breeding stream); G-SHr graph j, run
r uses seed 1 171 000 + 2j + r. Training worlds come from each run's seed, so G-SHr's runs do not share G-N2's worlds;
the paired unit across arms is not the world but the arm's distribution of runs (§5).

## 5. Readings

All on the test suite (§3), each genome one strain on all 17 × 512 worlds.

**The genomes per run:** **F**, the final generation's best (the registered genome); **C**, the champion (best
validation checkpoint), beside it; **G0**, generation 0's best (checkpoint 0).

**O1 (confirmatory): N2 against the null, on F's suite score.**
- **Estimand:** Δ = (the mean over G-N2's 16 runs) − (the mean over G-SHr's 16 graph means, each the mean of its
  2 runs).
- **Interval:** 90% hierarchical percentile bootstrap, 10 000 resamples, seed fixed: resample N2's runs; resample
  null graphs, then runs within each drawn graph. The graph is the null's unit (the standing rule: "several
  independent graphs per ensemble, with runs within graphs").
- **Rules, in order** (E4s-1's form): "reversed" if the upper bound is below 0; "N2 ahead" if the lower bound exceeds
  0 and Δ ≥ δ; "no detected advantage" if the upper bound is below δ; "inconclusive" otherwise.
- **δ, proposed: 0.25 captures per episode on the suite score,** about the between-champion SD of E4s-1's champions
  (§2) and 9% of their mean. Fixed in the pre-registration after the power simulation (§6).
- **Wording** (the roadmap's table): "no detected advantage under these tasks, controls and budgets", never "the worm
  wiring is neutral".
- **The rough power:** with a run SD of 0.3, a between-graph SD of 0.3 and these counts, the standard error of Δ is
  about 0.12, so effects of about 0.5 are found almost always and effects of 0.25 about half the time. The
  between-graph SD is unknown until the pilot measures it on 4 graphs (§6), and the simulation, with these exact
  rules, decides the counts.

**O1 beside it (descriptive):**
- **O0, generation 0:** the same contrast on G0. 03 found N2 distinctive at generation 0 on P4; a hunter difference
  might also be present before selection.
- **O1c, the climb:** F − G0 per run, by arm, and the difference of the arms' climbs. Only this is "improvement by
  evolution"; a final difference alone is not.
- **Per stratum and per setting,** trained against held-out.
- **SH-route's spread:** the 16 graph means against N2's run distribution, as 03 reported ranks.

**O2, the build (descriptive).** Per B run, F − G0 on the suite (G0 is the E4s-1 champion itself, zero-shot): its
mean and a 90% bootstrap interval over the 16 runs. Read beside L1 on its carrier on the same worlds; "B improved on
its starting champion" needs the interval above 0. Also: B's F at fast route speeds (0.8 to 1.0) against L1; and B's
F against G-N2's F, run by run (the same construction, with and without E4s-1's 1 000 generations on Task N first):
what pretraining on Task N is worth on Task H, descriptive, at unequal total budgets (said so).

**O3, inherited function (descriptive).** For F of B and G-N2: H1-ghost (Task N) against the starting genome's.
E4s-1's champions score 7.41 there.

**Probes on every F and G0,** at four settings (H1-bite, route 0.5, route 1.0, walk 0.5), 512 worlds each (E5-0's set):
`constant`, `mirrored`, the world's `mean`, the module-only `mean` (L1's noses fed the mean while the host's sensors
are real, E4s-1's H probe), and the body probe. Reported as signed paired contrasts with intervals, per genome; the
`constant` qualification probe as E5-0 read it.

**What is never a reading:** energy from bites (logged only), damage shares (D026's lesson), anything from training
worlds.

## 6. Before the formal run (GPU; the owner's word first)

A stage **E5-1a**, exploratory, with stop rules fixed here. **It never runs the confirmatory comparison:** no formal
graph, seed or test-suite world is used.

1. **Task H on CUDA.**
   - **Score level:** E1's frozen S-const, the pursuit reference, L1 on its carrier and E4s-1 run 0's champion, on
     512 worlds at H1-bite, route 0.5 and walk 0.5, CPU against CUDA: each mean within 0.05 (E4s's score-level
     tolerance); the share of identical per-world counts reported.
   - **State level:** a grafted N2 genome and a grafted SH-route genome, open loop under identical imposed input
     histories, the maximum absolute state difference over 300 ticks at most 10⁻⁴ (E4s-1's gate 2), at every batch
     shape E5-1 uses.
   - **The ledger** balances on CUDA at T0's tolerance on every pilot episode.
   - **Stop** on any failure; diagnosis is a dated, reviewed amendment.
2. **The null graphs.** Each of the 16 formal and 4 pilot SH-route graphs is rebuilt from 03r's record and checked
   against both manifests (raw bytes where zlib allows, arrays everywhere, D106); L1's 16 output edges and noses are
   present after grafting; the 8 turn read-out neurons and every interface neuron exist. **Stop** on any mismatch.
3. **Generation 0, on pilot seeds and the 4 pilot graphs** (03r's SH-route graphs 17 to 20, none of them formal) and on
   N2 with 4 pilot seeds: each population's 32 genomes on 256 worlds of the training mixture. Reported: the best,
   the median, the share of strains with any capture (the selection signal), the module-only `mean` contrast of the
   best (is L1 used at generation 0 on a null host?), and the achieved forward and turn drive. **Stop** if, on any
   graph, no strain of any pilot population captures anything: selection would have nothing to act on.
4. **A pilot evolution, 2 runs on 2 pilot graphs and 2 on N2, 100 generations** at the formal shapes: the between-
   graph and between-run spread for the power simulation, and the measured rates. It does not compare N2 with the
   null; its numbers are not read as a result.
5. **Mutational sensitivity** (SCOPE.md §7): 256 mutants at the arm's scales around B's 16 seeds and around the pilot
   generation-0 bests; the median share of the parent's score and the share below 0.7, as E4s-0 reported. Measured,
   not a stop.
6. **The bench and projection:** every shape timed (N2 at 8 runs per batch; a null graph at 2 runs per batch;
   validation; single-genome evaluation at 17 × 512), with the route prey's respawns. Stage caps and an evaluation
   reserve are frozen before training, admission as in E4s-0.
7. **The power simulation** with the exact O1 rules, at the measured spreads, over graph and run counts; δ and the
   counts are then fixed in the pre-registration.

## 7. Cost (rough; replaced by the bench)

From E1's and E4s-1's measured rates on Task N (one wey, no prey, no combat):
- **N2, 8 runs per batch:** about 4.9 s per generation, so about 1.35 hours per 1 000 generations (E2's GA, E4s-1's
  ten batches at 4 876 to 5 151 s).
- **A null graph, 2 runs per batch:** one batch holds one graph (`evolve_batch` takes one `BrainSpec`), and E1
  measured 2.33 s per generation at 1 run and 3.04 at 4, so about 2.6 s, or about 0.73 hours per graph.
- **Task H's overhead, unknown:** two swarms, combat on, per-capture respawns, and a route sampler that runs in Python
  per world on every capture (`prey.py`'s `_route_for`). Call it a factor f, measured by the bench; it could be 1.3 or
  more than 2.

| Part | Runs | Task N-rate hours | at f = 1.5 | at f = 2 |
|---|---|---|---|---|
| G-N2 | 16 (2 batches) | 2.7 | 4.1 | 5.4 |
| G-SHr | 16 graphs × 2 (16 batches) | 11.7 | 17.5 | 23.4 |
| B | 16 (2 batches) | 2.7 | 4.1 | 5.4 |
| Evaluation (F, C, G0 of 64 runs on 8 704 worlds; probes at 4 settings) | | | about 4-6 | about 5-8 |
| E5-1a (gates, pilot, bench) | | | about 2 | about 3 |
| **Total** | | | **about 32-34** | **about 42-45** |

**So E5-1 is likely 30 to 45 GPU-hours,** most of it the null arm's per-graph batches. Cheaper variants for the
review: B alone, or the test alone (drop about 5); 12 graphs (drop about 4 to 6); 500 generations if the pilot shows
flat late training (about half). A cap is proposed after the bench, for the owner.

## 8. New code (each test-first; sabotage where a check cannot fail)

- **A guard in `Genome.cat`:** it keeps the first part's spec without checking the others (`brain.py`), and
  degree-preserving nulls have equal edge counts, so mixing graphs would silently run every genome on the first graph's
  wiring. It must refuse mismatched specs. A test with N2 and an SH-route genome.
- **Task H in the GA:** a hunt rollout for `evolve_batch` (the mixture's slot settings, the prey per slot, captures as
  the score), with the hunter as swarm 0 and the prey as swarm 1 in every world.
- **The route sampler on the device, or batched:** `_route_for`'s per-world Python loop runs at every capture; it is
  replaced by a pre-drawn table per (world id, life), with equality to the current sampler tested on the CPU.
- **Per-tick host syncs** in `hunt.py` (`bool(...any())`) measured in the bench; removed only if they dominate, with
  the CPU equivalence re-run.
- **Graphs:** the SH-route rebuild and check (03r's `rebuild-graphs`), the grafted null construction, the run-to-graph
  map.
- **Readings:** the suite score, O1's hierarchical bootstrap, O0, O1c, O2 and O3, the module-only `mean` probe on Task
  H.
- **Engine changes are none** beyond the guard, by design (§4's gains). The CPU equivalence of E5-0 is re-run after the
  changes (68 arrays and the ghost against Task N).

Genome files stay local (rule 1); null graph files are never committed (they carry permuted anatomical weights).

## 9. What E5-1 cannot show

- **That N2's wiring helps hunting in general.** Only whether N2 hosts L1 better than SH-route under this GA, budget,
  mixture and arena. SH-route moves weights as well as edges.
- **The roadmap's gate** (captures from a frozen suite of competent prey on unseen maps): H3's organisms and H4's maps
  are not built. E5-1's suite is scripted prey in an empty arena.
- **Anything about worm predation,** or about real C. elegans chemotaxis (stereo is a game-design choice, E4s).
- **Coevolution or evasion:** the prey never reacts beyond the wall follower's collision inputs.
- **Claims for stages 05 to 08 that need the collective-behaviour survey** the roadmap asks for; E5-1 makes none.

## 10. Open questions for the review

1. **Graft in both arms (§4).** Is "N2 as a host for L1" an acceptable reading of the owner's question, or should the
   test add a no-graft pair (N2 against SH-route, both from random genomes, about +15 GPU-hours), or replace the
   graft pair with it?
2. **One ensemble or two.** SH-route only, or SH as a descriptive second ensemble (01b's and 02's shuffle; about +12
   GPU-hours at 16 graphs × 1 run)?
3. **Gains (§4).** N2's for every graph, with drive reported, against per-graph calibration with per-swarm gains (an
   engine change, and the graft's gain rescaled).
4. **The mixture and the suite (§3).** Are the eight slots right; is a three-strata mean the right score; should the
   movers be held out entirely as a transfer test?
5. **δ = 0.25 and 16 graphs × 2 runs,** before the power simulation.
6. **B's start:** 32 identical copies of each champion (C2's construction), or the champion plus 31 mutants?
7. **Whether B belongs in E5-1 at all,** or should run after the test, which is the part that needs pre-registration.
