# Decisions

Modelling and engineering choices that the spec left open. Newest last. Each entry says what was
chosen, what else was possible, and why. When a choice was hard, that is noted explicitly.

## D001 — Interpreter and dependency install (M0)

Use the existing system Python 3.13 with its already-installed `torch 2.12.0+cu130` rather than a
fresh virtualenv. A venv would mean re-downloading ~3 GB of CUDA wheels for no benefit on a
single-user machine. `requirements.txt` pins the exact versions verified here, so the environment is
still reproducible. Missing pure-Python deps were installed into that interpreter.

## D002 — Connectome dataset and weight quantity (M1)

Dataset: Cook et al. 2019 hermaphrodite, file `SI 5 Connectome adjacency matrices, corrected July
2020.xlsx` from wormwiring.org. Chosen over SI 2 (synapse adjacency), SI 7 (cell-class level) and
the original uncorrected SI 5.

- SI 7 is collapsed to cell classes, which would destroy the left/right distinctions the whole
  sensor map depends on (AWAL vs AWAR). Rejected.
- SI 2 is "synapse adjacency"; SI 5 is the connectome the paper's figures use. The spec asks to
  prefer corrected files, so: corrected SI 5.
- Weight quantity is therefore **`weight_kind = "em_sections"`**: the total number of EM serial
  sections of connectivity, which folds together synapse count *and* synapse size. It is not a
  synapse count and the loader API says so. Initialisation scales |W| with this quantity, so the
  distinction is visible where it matters.

## D003 — Gap junction sheet (M1)

Use `hermaphrodite gap jn symmetric`, not `... asymmetric`. The July-2020 corrections exist
precisely to make values across the diagonal agree; the model requires a symmetric G, and taking the
already-reconciled sheet avoids inventing a symmetrisation rule of our own. The loader still asserts
exact symmetry after loading.

## D004 — The 302 neurons, and CANL/CANR (M1)

The chemical sheet lists 300 neurons as rows. `CANL` and `CANR` appear only in the gap-junction
sheet (and there, under the spreadsheet's `MUSCLES` block header, which is a layout artifact of that
sheet, not a claim about their identity). The canonical hermaphrodite nervous system is 302 neurons,
so the loader's neuron list is the 300 chemical-sheet neurons plus CANL and CANR = 302, ordered
pharynx → sensory → inter → motor → sex-specific → CAN.

CAN has no known chemical synapses; its rows and columns in the chemical matrix are all zero. It is
kept, not dropped, so that "302" means 302 and so that shuffled/random graphs are matched on the
same node set. Its class is recorded as `other`, because the dataset does not assign it one.

## D005 — Neuron class from sheet block headers (M1)

Class (`pharyngeal` / `sensory` / `inter` / `motor` / `other`) is taken from the spreadsheet's own
block headers rather than from an external annotation. This keeps the classification inside the
provenance chain of a single file. `SEX SPECIFIC` (HSNL/R, VC01–06) maps to `motor`, which is what
those cells are; the block name describes their dimorphism, not their function.

## D006 — Non-neuronal targets are dropped (M1)

The sheets include body-wall muscles, pharyngeal muscles, and end organs as columns. The brain model
is 302×302 over neurons only, so those columns are dropped. The motor read-out is taken from neuron
voltages, not from muscle cells. Recorded because it discards real anatomy: the weys' motor output
is a linear read of named motor neurons, and the muscle layer is not simulated.

## D007 — Autapses kept, gap self-edges dropped (M1)

The published chemical matrix has 38 autapses (117 EM sections in total). They are kept: they are
real published entries and `W_ii * tanh(v_i)` is a genuine dynamical term, not an artifact. To keep
the conditions matched, SH and RD graphs are allowed self-loops too.

The gap sheet has 14 self-entries. Those are dropped, because `G_ii * (v_i - v_i)` is identically
zero in the model; keeping them would only corrupt the implicit denominator of the integrator.

## D008 — Observation: the pharynx hangs off a two-neuron bridge (M1)

Measured, not assumed: the only wiring between the somatic and pharyngeal nervous systems is the
gap junction pair `I1L-RIPL` and `I1R-RIPR` (weight 2 each), plus one chemical synapse `M1 -> RIPL`.
Since the pump read-out is `MCL`/`MCR`, all pump control in N2 must pass through that bridge, while
SH/RD shuffles will connect the pharynx to the body broadly. This is a structural prediction, not a
bug: if SH/RD beat N2 specifically at pump-gated eating (milestone 8), this is the first suspect.
Recorded now so it cannot be rationalised after the fact.

## D009 — Bilateral sensors are directional wherever it is free (M1)

The spec pairs sensors left/right. Damage (`ASHL`/`ASHR`) and collisions (`ALML`/`ALMR`/`AVM`,
`PLML`/`PLMR`) are sampled at the same left/right offsets as the chemical senses rather than being
scalar broadcasts. It costs nothing (the bilateral sampling machinery already exists) and it makes
"turn to face what bit you" learnable, which milestone 10 measures. `AVM` gets the centre sample.

The three food pairs (`AWA`, `AWC`, `ASE`) all receive the *same* left/right food concentration.
They differ only in how they are wired, which is precisely the variable under test.

## D010 — Read-out and injection both use tanh(v) (M1)

Motors read the bounded output `tanh(v)`, not the raw voltage, so forward drive and turn are bounded
by construction and cannot be driven by a neuron running away to large |v|. Pump is
`sigmoid(gain * mean(tanh(v_MC)))` with gain 4.0, so the full [0,1] range is reachable.

## D011 — dt and substeps chosen by measured refinement, not by stability (M2)

Measured relative deviation between `substeps` and a 512-substep reference, over 40 ticks, max over
neurons, normalised by max|v| of the reference:

| genome | substeps=2 | 4 | 8 | 16 |
|---|---|---|---|---|
| random | 0.0423 | 0.0176 | 0.0083 | 0.0040 |
| extreme (every bound saturated) | 0.0127 | 0.00021 | 0.00001 | 0.00001 |
| all tau at tau_min, all G at g_max | 0.00054 | 0.00002 | 0.00001 | 0.00002 |

The scheme converges at first order (error halves per halving of dt), as expected.

Two things worth recording because they are counter-intuitive:

- The *extreme* corner is not the hard case. With every bound saturated, neurons slam into a fixed
  point within a tick or two and every dt agrees. The hard case is a **random** genome with tau
  spread across the allowed decade and a half, where the trajectory is genuinely transient.
- Raising `tau_min` therefore does **not** improve accuracy. Measured: at substeps=4 the random-genome
  error is 0.0176 at tau_min=0.5, 0.0303 at tau_min=1.0 and 0.0328 at tau_min=2.0. Slower neurons
  mean longer transients, and longer transients mean more accumulated dt error.

Chosen: **substeps = 8, dt = 0.125, tau in [0.5, 20] ticks**, worst-case relative deviation 0.83%.
substeps=4 would be twice as fast at 1.76%. The 2x compute is worth it for a tool whose conclusions
depend on the trajectories, and the brain is not the dominant cost of a tick.

## D012 — Dense masked matmul beats sparse, measured (M2)

At 6.46% mask density, one strain, 4096 weys, RTX 5080: dense `bmm` 0.467 ms/tick vs sparse CSR
`torch.sparse.mm` 2.513 ms/tick. **Dense is 5.4x faster**, so dense it is. The genome still stores
only the 5 404 values on the mask; dense matrices are materialised for the forward pass.

## D013 — Brains are batched per strain, not per world (M2)

The spec suggests weights shaped `[worlds, swarms, 302, 302]`. Since every wey in a swarm shares one
genome and many worlds run the same strain, the implementation uses `[strains, 302, 302]` with the
caller mapping (world, swarm) to a strain index. Same computation, but one strain's weights are
materialised once regardless of how many worlds use it. Measured throughput with this layout:
5-6 M wey-ticks/s (e.g. 64 strains x 2048 weys = 131 072 weys at 26.3 ms/tick, 1.29 GB peak VRAM).

## D014 — Motor gains, because the read-out is small near rest (M3)

The specified read-out is a difference of two means of `tanh(v)`. Near rest those means are both
close to zero and strongly correlated, so a random genome produces |forward| ~ 0.10 and |turn| ~ 0.16
after the /2 normalisation (measured over 32 random genomes, 60 ticks). Mapped straight onto speed
that is a mean step of 0.009-0.038 cells/tick against a 0.35 maximum: an unevolved population is
effectively motionless, and there is almost nothing for selection to act on.

Fix: `world.forward_gain = 4.0` and `world.turn_gain = 2.0`, applied before the [-1, 1] clamp. The
read-out formula itself is untouched. Measured afterwards: mean step 0.085 cells/tick (24% of
maximum), and per-strain final swarm energy over 32 random strains spans 0 to 447 (std 91) -- a
usable fitness gradient. `init_bias_std` also went 0.1 -> 0.5 so neurons have some spontaneous
activity to begin with.

## D015 — Food patches have hard support (M3)

Gaussian patches put a little food in every cell of the arena, so weys could feed wherever they
spawned and never had to travel. Patches are now `max(0, 1 - (d/r)^2)^2`, which is exactly zero
outside radius r. Visible in the viewer as compact patches with bare ground between them.

`metabolic_drain` also went 0.012 -> 0.035 per tick. At 0.012 a wey that did nothing at all survived
the whole 600-tick match on its 12 starting energy, so foraging was optional. At 0.035 a full match
costs 21 energy and doing nothing is fatal at around tick 340 -- which is what the viewer shows.

## D016 — Hazards keep clear of spawn boxes (M3)

Hazards are placed at random but rejected within `hazard_spawn_clearance` (6 cells) of a spawn box
centre, retried up to 20 times. Without it a swarm could be cooked where it stood before it had any
chance to act, which measures nothing about foraging.

## D017 — Measured crowding behaviour (M3)

Twenty weys forced into a 0.06-cell cloud, then left to run:

| tick | max body density | position std | weys in the densest cell |
|---|---|---|---|
| 0 | 5.78 | 0.07 | 20 |
| 10 | 4.33 | 0.79 | 6 |
| 40 | 1.78 | 1.93 | 4 |
| 120 | 1.33 | 2.60 | 2 |

So a swarm cannot collapse into a single cell: `crowd_threshold = 0.8` on the blurred body field,
with resistance `1 - 0.6*tanh(density - threshold)` and a push of 0.10 cells/tick down the density
gradient, disperses a maximally packed swarm within ~40 ticks.

## D018 — Sensors sample bilinearly, combat samples nearest-cell (M3)

Senses use bilinear sampling so gradients are smooth and climbable. Everything on the damage path
(attack deposit, damage sampling, bite credit) uses nearest-cell, because the bite-credit rule needs
the splat to be the *exact* adjoint of the sample, and nearest-cell splat/sample are exactly adjoint
by construction. `tests/test_fields.py` asserts the adjoint identity directly.

## D019 — The flank rule, measured and then tuned (M6)

The flank rule is a hypothesis about geometry, so it was measured before being believed.

**First attempt** (`body_length = 1.6`, `attack_offset = 0.9`, `attack_blur = 1`), exact lattice
positions: T-boned payback **0.556**, head-on asymmetry **5.0**. Both bad. The body was smaller than
the 3x3 blur, so a flanked wey's own bite cell reached back onto its attacker.

**The measurement was also wrong.** Placing weys on exact lattice coordinates measures the cell
grid's phase, not the geometry: weys move continuously and never sit on lattice points. Duels are
now averaged over a grid of sub-cell offsets applied to *both* weys, which leaves the relative pose
untouched and averages out the phase. Ratios are only taken at gaps where a fight is actually
happening (the victim takes at least half the peak damage for that pose); at long gaps the numbers
are lattice noise.

**Chosen**: `body_length = 2.4`, `attack_offset = 0.9`, `attack_blur = 1`, `head_armor = 0.25`,
`damage_k = 0.55`. Measured, 8x8 sub-cell phases, damage per tick:

| gap | head-on A / B | T-bone A / B | rear A / B |
|---|---|---|---|
| 0.40 | 0.0764 / 0.0840 | **0.0000** / 0.1203 | **0.0000** / 0.1241 |
| 0.90 | 0.0611 / 0.0687 | **0.0000** / 0.1203 | **0.0000** / 0.1146 |
| 1.40 | 0.0306 / 0.0382 | **0.0000** / 0.1203 | **0.0000** / 0.0840 |
| 1.90 | 0.0153 / 0.0153 | **0.0000** / 0.1203 | **0.0000** / 0.0611 |

- **T-boned payback: 0.000.** **Rear-bitten payback: 0.000.** (limit `max_flank_payback` = 0.10)
- **Head-on asymmetry: 1.17** (limit `max_head_on_asymmetry` = 1.5), and head-on peaks at 0.084
  damage against 0.120 for a flank -- so head-on is both even *and* weak, which is the point.
  Flanking is a **1.43x** better trade before counting that it costs nothing.

An alternative that also passed the ratios, `body_length = 1.6, attack_offset = 1.2`, was rejected:
its head-on damage (0.1375) equalled its flank damage, so head-on was even but not *weak*.

At 0.12 damage/tick a continuously flanked wey dies in about 100 ticks; a head-on grind takes about
170. Crowding was re-checked at the longer body: a maximally packed swarm still disperses (max
density 3.89 -> 1.44, spread 0.03 -> 2.45 cells in 120 ticks).

**Cost of this choice:** the milestone-4 numbers were measured at `body_length = 1.6`. They are
re-run at the final configuration rather than left stale.

## D020 — Bite credit follows the spec's rule, and the residue is booked honestly (M6)

Each attacker collects `(its deposit / the cell's total deposit) x blur(damage_received)[its bite
cell]`. Because the blurred damage grid also has mass on cells where nobody deposited, the total
collected is slightly less than the total damage dealt. That shortfall is not swept anywhere: the
inefficiency sink is defined as `damage taken by victims - energy gained by attackers`, so it
absorbs both the configured `transfer_fraction` loss and this geometric residue, and the energy
ledger balances exactly whatever the geometry does. Energy that would push an attacker past
`max_energy` is also booked there rather than silently created or dropped.

## D021 — Matches are grouped by total headcount before batching (M7)

Arena area scales with headcount so starting density stays constant, but a batch of worlds shares
one grid, and `arena_side` takes the largest matchup in the batch. Mixing a 50v50 with a 200v200 in
one batch would therefore hand the small match a four-times-emptier arena than its own headcount
calls for -- a silent fairness bug in exactly the varied-size evaluation the spec asks for.

`play()` now groups matches by **total** headcount before chunking, and restores the caller's order
afterwards. Grouping by the total (not by the pair) keeps 50v200 and 200v50 in the same batch, which
is what paired evaluation of lopsided matchups needs. A test plays a small match alone and again
inside a mixed batch and requires the same score.

## D022 — Varying swarm sizes are a property of the generation, not of the candidate (M7)

When `coevo_vary_sizes` is on, each generation draws `coevo_size_pairs` headcount pairs from
[50, 200], and **every** candidate plays **every** opponent at **every** drawn pair, from both
spawn sides, with the headcounts swapped as well. Size therefore varies the test without varying who
gets the easy draw. Measured on a sample schedule: 4 candidates x 2 opponents x 2 worlds x 2 pairs
x 2 side swaps x 2 headcount swaps = 128 matches, exactly 32 per candidate, exactly 32 of each of
the four (size_a, size_b) combinations.

## D023 — Food scales with headcount, in amount *and* in geometry (M11)

Arena area already scaled with headcount to hold starting density constant, but food did not, so a
2000v2000 match had the same absolute food as a 20-wey one. Worse, patch *radius* did not scale
either, so at large sizes all the food sat in a few tiny blobs lost in a huge arena. A showcase
match was therefore not a scaled-up small match but a different game -- a starvation scramble around
a handful of cells, with 11% survival.

Two factors, both referenced to the development size of one swarm of 20:

    amount per patch  x  (total_weys / 20)          -> constant food per wey
    patch radius      x  sqrt(total_weys / 20)      -> constant fraction of the arena covered

Hazard radii and the hazard/spawn clearance scale the same way. Measured afterwards:

| swarms x weys | arena | food per wey | weys per cell | arena covered by food |
|---|---|---|---|---|
| 1 x 20 | 24 | 28.9 | 0.0413 | 16.7% |
| 2 x 40 | 46 | 28.4 | 0.0413 | 24.8% |
| 2 x 100 | 72 | 21.7 | 0.0408 | 29.2% |
| 2 x 200 | 100 | 28.0 | 0.0416 | 26.6% |
| 2 x 2000 | 312 | 23.5 | 0.0416 | 16.3% |

(The spread comes from the per-world random patch count, not from the scaling.)

At 20 weys both factors are exactly 1, so **every number measured at the development size is
unchanged** -- M4, M5, M8 and M9 all stand as reported. The coevolution numbers, which were measured
at 40v40, were re-run.

## D024 — A genome is meaningless without the gains it was evolved under (M10)

Motor gains are calibrated per graph, so an SH1 champion evolved at `forward_gain = 2.093` behaves
like a different animal at N2's 4.0. The first ablation report did exactly that and produced
baselines of 0.40-0.68 for SH/RD champions whose real held-out scores were 1.4-1.6, which made every
sensitivity computed from them meaningless.

Fixes, in order of preference:

1. `save_genome`/`save_population` now record the world settings a genome was evolved under
   (`forward_gain`, `turn_gain`, `body_length`, `max_speed`, `max_turn`), and `apply_world_meta`
   restores them on load.
2. For genomes saved before that, the analysis scripts recover the calibration from the run
   `bundle.json` beside them, and say so.
3. Failing both, they run at the defaults and print a loud warning rather than silently producing
   a number.

`showcase.py` refuses outright to stage a match between two strains evolved at different gains: one
world holds one config, so it could not give both their own.

## D025 — The frozen suite is scored at a fixed headcount (M7)

When training headcounts vary, the frozen suite must be scored *inside* the training distribution,
or "progress" is really a measurement of generalisation to a size never trained on. The first
varied-size run trained at 50-200 but scored the suite at 40v40 and appeared to get *worse*
(+0.113 -> +0.072, 0/2 runs improving). Scored at 100v100 -- the spec's standard fight -- the same
setup improves (+0.132 -> +0.188, 1/2 runs), and fixed-size coevolution improves more
(+0.128 -> +0.343, 2/2 runs), which is the expected ordering: a non-stationary objective is harder.

## D026 — RETRACTION: the "learned to flank" claim was an artifact of the armor weights (M7/M10)

**What was claimed.** `RESULTS.md` (M7 and the M10 tactics section) and the README said that
coevolved swarms "learned to flank", on the evidence that **88.8%** of the damage they dealt landed
on an enemy's mid or tail rather than its head.

**Why it was wrong.** Damage is `k * (head_armor * a_head + a_mid + a_tail)`. If the attack field
were simply uniform across a victim's three body points, the mid+tail share would already be

    (1 + 1) / (head_armor + 1 + 1)  =  2 / 2.25  =  0.8889

at the shipped `head_armor = 0.25`. The metric is pinned near 0.889 by the armor weights whatever
the weys do. The measured 0.888 *is* the reference line, not a result.

Worse, the refutation was already sitting in my own output. `summary.json` records
`flank_share_first` alongside `flank_share_last`, and generation 0 scored **0.881** and **0.879**
against final values of 0.884 and 0.897. The metric never moved during coevolution. I quoted the
final number as evidence of learning without ever comparing it to the starting number.

**Who caught it.** External review before publication, not me. It was raised as arithmetic
(`2 / (2 + head_armor)` equals the reported value), and re-measurement confirmed it.

**What replaced it.** `wormwars/analysis/ablation.py` now exposes `chance_flank_share(ccfg)` and
`chance_placement_share(ccfg)`, computed from the config rather than written down, and
`World` accumulates three metrics per world and per *attacking* swarm:

- **placement share** — the same body-point distribution with the armor multipliers divided back
  out, so the reference line drops to 2/3 and any excess is real geometric concentration toward
  mid and tail;
- **unanswered damage share** — the fraction of a swarm's damage dealt by weys that took nothing
  back in the same tick, which is what flanking is actually *for*;
- **turns toward the bite** — how often a bitten wey turns toward the side it was bitten from
  (chance 0.5).

All three are O(N), computed from tensors the combat step already produces, and none of them feed
back into the simulation.

**Neither reference line is a null, and this is measured, not argued.** Weys converge on each other
head-first, so head contacts are more likely than a uniform share before any tactic exists. Dropping
unevolved weys into a dense heap with random headings measures a flank share of **0.793** and a
placement share of **0.489** -- both *below* the analytic lines of 0.889 and 0.667. The null has to
be measured. `scripts/tactics.py` measures it; `tests/test_combat.py` asserts that a real melee
falls below the reference line, so this cannot quietly regress.

**One methodological correction to the correction.** The three groups originally asked for -- random
strains, generation-0 populations, and the final coevolved populations -- are *not* comparable,
because the first two barely fight. Only 1-4 strains of the first two landed any damage at all,
so their ratios come from a handful of accidental contacts.

The reason is worth stating because it also explains an apparent oddity. **Contact is created by
whichever side approaches, and biting is automatic** once bodies are close. The same six frozen
strains, on the same worlds, dealt 94 and 2 damage against random opponents, and 38 063 and 13 244
against the coevolved ones. The suite did not get more aggressive; the coevolved swarms came to it.

**The frozen suite is a matched comparison, not a null.** Both sides' numbers come out of the same
engagements and are mechanically coupled -- a tick in which A bites B and B bites A is one event
counted from both sides -- and the approaching side and the approached side have different roles in
it. It answers "is the coevolved side's damage shaped differently from its opponent's", not "what
would happen by chance". The direction of any gap is therefore not interpreted.

**What the frozen suite is:** six **random-weight** strains, never evolved for anything -- not for
foraging, not for combat. Their spread comes from initialisation scale (0.5x to 2.0x), not training.

**n = 2 runs.** Every tactics figure is reported per run. No interval over runs is computed, because
an interval over two numbers says nothing.

**What the measurements say:** no evidence of learned flanking. Three of the four metrics change
sign between the two runs. The unanswered-damage gap is the one with a consistent sign and is
reported as suggestive at most, not interpreted.

**And what coevolution did improve, measured rather than inferred.** The energy accounting now
splits each swarm's gains into eating and biting. The coevolved populations took in 789 393 and
683 955 energy by eating, against 181 141 and 184 828 for the frozen opponents they beat -- 4.4x
and 3.7x more -- while biting supplied **0.1-0.3%** of their energy. Coevolution under these
settings produced better foragers; combat barely contributes.

See the Corrections section of `docs/RESULTS.md` for the full tables.

## D027 — The git history was rewritten once, before publication (publication)

The repository was developed with a personal email address as the git author and committer, and
every commit message carried a session-URL trailer. Both would have become permanently public in
the commit history on the first push.

Rewritten once, before anything was pushed, with `git filter-repo`: author and committer name and
email replaced with the author's name and a GitHub no-reply address across all refs, and the
session trailer stripped from every message. The `Co-Authored-By` attribution to the model that
wrote the code was kept deliberately -- that is a real attribution, not personal information.

`git filter-repo` was chosen over `git filter-branch` because `filter-branch` leaves the original
commits behind under `refs/original`, which would have defeated the purpose.

Rewriting history is normally forbidden in this project. This is the single exception, authorised
explicitly, and it is narrow in a way that matters: **nothing had been pushed**, so no published
history was rewritten and nobody's clone was invalidated. The rule stands for anything published.

Because commit hashes change, the hashes recorded inside the run bundles no longer resolve. They
are mapped in `experiments/01-foraging-n2-vs-controls/commit-hash-map.txt` and the situation is
described in `PROVENANCE.md`. Every tree hash and every author and committer date is unchanged, so
the code each bundle refers to is exactly the code that ran.

Verified afterwards: identical trees and dates for all 29 old/new pairs, exactly one identity in
`git log --all`, zero occurrences of either replaced string across all git objects, refs, the
reflog, `.git/config` and every tracked file, and no dangling or unreachable objects after
expiring the reflog and garbage-collecting.

## D028 — An unevolved genome is the connectome's weights in disguise (publication)

Found during a pre-publication audit, after the repository had been pushed to a private remote.

Genome initialisation sets `|W| = init_w_scale * anat / mean(anat)`, where `anat` is the
`em_sections` weight of each edge. The values are stored in mask order. So for a genome that has
**not** been evolved, `|w|` *is* the connectome's chemical weight vector, up to a single scale
factor. The frozen opponent suite is exactly that: six `Genome.random(...)` strains, never evolved.

Measured across all 102 committed `.npz` files, as the fraction of entries where `|w| / mean(|w|)`
matches `anat / mean(anat)` to a relative tolerance of 1e-3:

| file group | fraction proportional |
|---|---|
| `N2-frozen-suite-v1.npz` (unevolved) | **100.0%** |
| evolved champions and populations, N2 | 0.0-0.2% |
| evolved champions, SH1-SH5 and RD1-RD5 (each against its own graph) | 0.0-0.2% |

The gap vector `g` does **not** leak even when unevolved: `clamp_(0, g_max)` saturates the large
gap weights, destroying the proportionality. Measured 0.0% for every file.

**Correction, 2026-09-19. That sentence is wrong, and the test that produced it was blind.** The
0.0% is real but it measures the wrong thing. `g = init_g_scale * anat / mean(anat)` then
`clamp_(0, g_max)` clips the 4 junctions of 1091 that sit above 40x the mean. Clipping them lowers
`mean(g)` by about 8%, so *every* entry's mean-normalised ratio is inflated by that same 8% and the
rtol = 1e-3 comparison fails on all 1091 entries at once -- while the vector is still anatomical
edge by edge. Re-measured with the scale fixed by the **median** ratio, which four clipped entries
cannot move, an unevolved gap vector is **99.6% proportional**, and 99.8% of the anatomical gap
values are exactly recoverable from it. So the removed frozen suite leaked the gap weights too, not
only the chemical ones. Removing it was right for a reason I had not measured.

All 100 committed `.npz` were re-tested under both normalisations. The worst value anywhere is
**0.46%** (`g`, median-normalised, `runs/m9-uncalibrated/champion-RD2-run02.npz`), against the 1%
limit. Nothing committed is affected.

**What was done.** The two copies of the suite file were removed from every commit with a second
`git filter-repo` pass, and `*frozen-suite*.npz` is now in `.gitignore`. The suite is regenerated by
`make_frozen_suite`, which is deterministic from its seed, so nothing is lost: `scripts/tactics.py`
regenerates it rather than reading a file, and a test asserts it regenerates bit-identically.

**Why the evolved genomes are kept.** The decisive test is not correlation, it is recovery: fit one
scale factor by the median ratio, then round each entry to the nearest of the 58 distinct chemical
(34 gap) anatomical values, and count exact hits. Across all 160 committed strains that recovers a
median of 15.6% of the chemical values (worst case 22.8%) and 18.9% of the gap values (worst case
23.2%) -- **below the 30.5% and 36.1% you get by ignoring the file and guessing the single most
common value everywhere**. An evolved genome tells a reader strictly less about the anatomical
weights than the value histogram alone does. For contrast the same test on an unevolved genome
recovers 100.0% and 99.8%.

Correlation stays high and is the wrong statistic: `|w|` against anatomy runs 0.601-0.945 over all
160 committed strains, wider than the 0.71-0.84 first reported here, which covered only the N2
champions. Correlation tracks the broad shape of the weight distribution, not the values.

Publishing them is what makes the ablation and tactics results checkable against the exact
strains, and that is worth more than the residual family resemblance. This is a judgement about
degree, recorded so it can be revisited.

**Guards added**, in `tests/test_publication_hygiene.py`: no committed genome may exceed 1%
proportionality against any graph's weights **under either normalisation, mean and median**, the
frozen suite may never be committed, the suite must regenerate bit-identically, and every `np.load`
must pass `allow_pickle=False`.

**And a guard for the control graphs themselves.** The proportionality test cannot see an SH or RD
graph: SH carries the real anatomical weights in permuted positions and the real degree sequence, so
nothing about it is proportional to anything. `test_no_committed_file_contains_graph_structure`
therefore looks for the structures directly -- any 302x302 matrix, any integer array of index pairs,
any array equal to one of N2's three degree sequences, and any array whose sorted values are the
anatomical weight multiset up to one scale factor. It runs over every tracked file, whatever the
format: `.npz`, `.npy`, JSON at any nesting depth, and any text file with 200 or more numbers in it.

**Both guards were checked by planting the offence**, eight times, each staged in git and then
removed: an unevolved population (caught at 100.0% on `w` and 99.6% on `g`), SH1 as two 302x302
matrices in an `.npz`, RD2's edge list as nested JSON lists, N2's out-degree sequence alone in a
JSON file, SH3's edge list split into separate `i` and `j` arrays, N2's wiring as a nested-list
matrix in JSON, RD4's edge list as a plain text table, and the anatomical weight multiset permuted
with no positions at all. The first version of the guard **missed the nested JSON edge list**,
because a list of two-element lists decomposes into thousands of length-2 rows and no shape check
fires; the walker now assembles any list of equal-length numeric lists into one array, which also
catches a matrix written as nested lists. All eight are caught now, and the guard raises nothing on
the repository as it stands.

The same scan was also run once over **all 453 blobs in the entire rewritten history**, comparing
every 302x302 matrix it found against the edge sets of the 10 control graphs the reported runs
actually used. Nothing matched. The control graphs are built in memory by
`wormwars/connectome/graphs.py` from the fetched connectome plus an integer seed; that module has no
write path, and no graph has ever been serialised to a tracked file.

## D029 — allow_pickle=False on every np.load (publication)

Every `np.load` in the codebase passed `allow_pickle=True`. Loading a `.npz` with pickle enabled
executes whatever the file says to execute, and this project publishes `.npz` files that people will
download -- so the loaders were an arbitrary-code-execution path for anyone who fetched a malicious
lookalike. Nothing stored here needs pickle: the arrays are numeric and the metadata is a unicode
string array. All 240 `.npz` files on disk were verified to load with `allow_pickle=False` before
the change.

The guard test parses the source with `ast` rather than matching a regex, because
`np.load(Path(p), allow_pickle=False)` defeats a naive paren match and a guard that cries wolf gets
switched off.

## D030 — Gap strengths are truncated above `g_max` at initialisation (noted for experiment 02)

No code change. Recorded because experiment 02 will want to decide this deliberately.

Initialisation sets `g = init_g_scale * anat / mean(anat)` and then `clamp_(0, g_max)`. With the
values every reported run used, `init_g_scale = 0.05` and `g_max = 2.0`, any junction stronger than
**40x the mean** starts at exactly `g_max` regardless of its anatomical weight. In N2 that is 4 of
1091 junctions (0.37%), at 47.5x, 47.5x, 76.2x and 76.2x the mean; the largest would have started at
3.81. Those 4 junctions carry **22.7% of the total anatomical gap weight**, so a small fraction of
edges is a large fraction of the coupling. The four strongest junctions therefore begin electrically
*equal* rather than ordered, and the ordering has to be discovered by mutation instead of being
given.

Chemical weights are not affected: the largest starts at 2.654 against `w_max = 3.0`, so 0 of 3709
edges clip.

This cannot bias experiment 01's comparison, because SH and RD preserve the weight multiset exactly,
so the same four values clip in every condition. It does mean the sentence "initialisation is
anatomical" holds for 99.63% of junctions and fails at the top end.

For experiment 02, pick one on purpose: raise `g_max` above `init_g_scale * max(anat) / mean(anat)`
= 3.81, lower `init_g_scale` below `g_max * mean(anat) / max(anat)` = 0.0262, or keep the truncation
and say so. See D028 for how this same clipping hid a data leak from a mean-normalised test.


## D031 — Chemical synapses ran backwards in experiment 01; fixed, with a legacy switch

**Found by Astra 6** (OpenAI), reviewing the roadmap on 2026-09-24 (its finding R01), from source
inspection and a two-neuron NumPy calculation. Confirmed the same day on the real PyTorch `Brain`,
with every weight zero except the one synapse I1L -> I6: driving I1L left I6 at +0.0000, and
driving I6 pushed I1L to +1.99. Signal flowed from the postsynaptic neuron to the presynaptic one.

**Cause.** `Genome.dense` stores `W[pre, post]`, the orientation of `Connectome.chem`. `Brain.step`
then multiplied by `W.transpose(1, 2)`, following a comment that assumed `W[post, pre]`. One
transpose too many. It was introduced with the brain in M2, before any run, so **every run of
experiment 01 used the reversed chemical graph.** Gap junctions are symmetric and were unaffected.
No test ever sent a signal down a single synapse and checked where it arrived. The sparse path in
`scripts/bench_brain.py` was correct, so the benchmark timed two different formulas against each
other -- which did not change the timing conclusion, but an output comparison there would have
caught this in M2.

**What experiment 01 therefore tested.** The worm's chemical wiring *reversed* (with its real gap
network), against degree-preserving shuffles and random graphs of that reversed graph. Reversing a
degree-preserving shuffle of N2 gives a degree-preserving shuffle of reversed-N2, so the comparison
is internally valid -- but it is not a test of the real wiring. Every biological reading of 01 is
affected, and so is any argument about paths: D008's "three hops from the sensors to the pump" was
counted in the true direction, not the one the simulation ran.

**The fix.** `BrainConfig.chem_direction`, `"pre_to_post"` by default. The old update survives as
`"post_to_pre"`, only so experiment 01 reproduces:

- A **run bundle's** config without the field is read as `post_to_pre`, because every run
  recorded before the fix lacks it and every one of them ran reversed. That rule lives only in
  `Config.from_bundle`. Ordinary configs (`from_dict`, `from_yaml`) treat a missing field as the
  correct default, so a partial config cannot bring the bug back. The first version of the fix got
  this wrong (D033).
- Saved genomes carry their direction in their metadata; files without it are read as reversed.
  `load_genome` refuses to load a genome under the other direction, and the replay scripts
  (`ablate`, `showcase`, `watch`) take the direction from the genome file.
- `activity_bound` counts the receiving end of each synapse in either mode.

**Verified to reproduce experiment 01, within a stated scope.** Three checks:
(1) stepping the N2, SH1 and RD1 champions of `m9-calibrated` for 300 ticks on the GPU gave
bit-identical states before and after the change (a one-off script; not kept);
(2) re-running `m9-calibrated`'s N2 run 0 (seed 40001) and SH1 run 0 (seed 40016) end to end with
`--chem-direction post_to_pre` reproduced the held-out score, survival, training score, AUC and SH1's
calibrated motor gains to the last bit (one-off; not kept);
(3) `test_legacy_mode_reproduces_a_published_experiment_01_score_exactly` replays 01's N2 run-0
champion on its 32 held-out worlds in legacy mode and requires the published held-out score to the
last bit. It runs on CUDA, and it is the check anyone can repeat.
These cover the brain update and the foraging pipeline. They do not individually re-verify every
workload in experiment 01 (coevolution, the pump, ablations). Within that scope, the current code in
legacy mode reproduces experiment 01, and a rerun in the correct direction differs from it in the
synapse direction and in what follows from it (the motor gains recalibrate; see D033).

**One test changed, and why.** `test_timestep_refinement[extreme]` failed after the fix. At the
extreme corner (every weight +w_max) the network is bistable, and a wey that starts near the basin
boundary is tipped either way by the choice of dt. A one-off sweep over 50 input seeds x 4 weys
(script not kept) found such flips in 3 of 200 weys in either direction; seed 13 simply lands on a
boundary under the corrected wiring. The flip is itself a numerical sensitivity, and the changed
test does not guard against it (D033). The
test now compares weys only within the same attractor and requires at least 3 of 4 to agree. See
D032 for what the wider check found.

**Decision:** rerun experiment 01's headline comparison in the correct direction, as experiment
01b, pre-registered in `experiments/01b-direction-corrected/PREREGISTRATION.md` before any run.
Experiment 01 stays published as it is, with a correction saying what it actually tested.

## D032 — 8 substeps is under-resolved for strongly evolved genomes (noted for experiment 02)

The single-seed refinement test above had been read as "the configured dt is accurate". A wider
check says that holds only in the range experiment 01 evolved in. Comparing the bounded output
`tanh(v)` at 8 substeps with 32 and 128, for 8 strains x 16 weys over 40 ticks:

| genomes | direction | max error 8 vs 32 | max error 32 vs 128 | weys off by > 0.05 (8 vs 32) |
|---|---|---|---|---|
| initialisation | reversed / correct | 0.26 / 0.058 | 0.066 / 0.015 | 1 / 1 of 128 |
| 25 mutations | reversed / correct | 0.082 / 0.14 | 0.023 / 0.032 | 3 / 1 of 128 |
| 150 mutations | reversed / correct | 1.54 / 1.98 | 0.13 / 0.25 | 71 / 59 of 128 |

The 32-vs-128 error is about a quarter of the 8-vs-32 error: first-order convergence, so this is
under-resolution, not chaos. It is the same in both directions, so it predates D031. The cause is
that the chemical term is explicit: while a neuron crosses tanh's linear region its step gain is
`dt / tau_min * w_max * in_degree = 0.25 * 3 * 65 ~ 49`, far above 1.

**Experiment 01 was not materially affected.** On its 45 real champions (`m9-calibrated`, 32 weys
each), the motor read-out error between 8 and 32 substeps has median 0.0013-0.0020, maximum 0.023,
and 0 of 1440 weys above 0.05, alike for N2, SH and RD. A new test,
`test_motor_readout_is_resolved_in_the_evolved_range`, holds that line at initialisation and after
25 mutations.

**Decision:** experiment 01b keeps 8 substeps, so it changes one thing. Experiment 02 plans 150
generations, where 8 substeps is not adequate: before tagging it, either raise the substep count
or make the chemical term semi-implicit, and re-validate on evolved genomes, not on one seed.

## D033 — Pre-publication review of 01b by Astra 6 and Fable 5.1, and what it changed

Before publishing, the fix and 01b were sent to two models from different families, Astra 6
(OpenAI) and Fable 5.1 (Anthropic), for an adversarial read-only review. The prompt and both answers
are kept outside the repository. **Both said "do not publish as is".** Both found the code fix
correct and found no remaining orientation error. What they found, checked here before acting:

**Claims that went beyond the data (both reviewers).**
- *"The real wiring improves faster."* The pre-registered "speed" measure averages best-of-
  generation fitness over all 25 generations, generation 0 included, so it mixes starting level
  with gain. Re-measured: N2's generation-0 best is 1.236 against SH 1.162 and RD 1.215, and its gain
  to generations 20-24 is 0.446 against 0.437 and 0.405. Against SH the edge is, as a point estimate,
  all head start; neither component separates under the bootstrap. The claim is withdrawn. 01b now
  reports "higher mean best-of-generation fitness" and an exploratory decomposition.
- *"Ends at least level with the shuffles."* That is a non-inferiority claim that was never
  registered, and the interval (+0.069 [−0.015, +0.169]) does not support it. Now: "not
  detectably different".
- *"Every number below is from the pre-registered analysis."* False: the rank argument, the run
  counts and the motor-drive comparison were exploratory. 01b's RESULTS.md now separates
  pre-registered from exploratory sections.
- *The rank "p ≈ 0.09".* The graphs are not exchangeable (N2 averages 15 runs and the controls 3;
  two families; N2 is the calibration reference), so no rank p-value is offered.

**Bugs in the fix.**
- *The legacy default leaked (Astra: blocking; Fable: should fix).* `Config.from_dict({})` and any
  partial YAML without a brain section came out `post_to_pre`, and the test skipped exactly that
  case. The legacy default is now confined to `Config.from_bundle`, and a test covers empty,
  partial and brain-less configs.
- *The benchmark's sparse path ignored legacy mode (Astra).* It now uses the oriented matrix. Dense
  and sparse agree to 4e-7 in both directions.
- *Dale's law under legacy mode (Fable)* would fix one sign per receiving neuron. It is harmless for
  01 (Dale was off) and is now commented.

**Record-keeping.**
- *The frozen experiment-01 record had been edited and re-hashed (Fable),* erasing the proof of what
  was frozen. It is restored byte for byte to tag `exp01-v1.0`. Its correction now lives in an
  unfrozen `CORRECTIONS.md` beside it, and `tests/test_frozen_records.py` guards the pinned hashes.
  Doing this found a flaw from the original freeze: the hashes pin the Windows CRLF form of each
  text file, so on Linux or macOS they do not verify as written. The test normalises line endings,
  and `CORRECTIONS.md` explains how to verify by hand.
- *The reproduction claim was not checkable from the repository (both).* There is now a CUDA test
  that reproduces a published held-out score to the last bit, and D031 states its scope.

**Measurements the write-up lacked.**
- *Calibration (Astra).* At the fitted gains, a random population reaches 84-97% of the target
  |forward| (N2 95%, SH 84-93%, RD 86-97%) and 92-100% of |turn|. The residual favours N2 over the
  shuffles on average and could contribute to N2's higher starting point. This is now reported. The
  calibration docstring's table, measured with reversed synapses, now carries a note.
- *Integrator on 01b's own champions (both).* The pre-registration cited 01's champions. On 01b's:
  0 of 1440 weys above 0.05 with input seed 300 (max 0.049). The reviewer found 8 of 1440 (max 0.26)
  with other inputs. Both are reported.
- *Multiple comparisons (both).* With Bonferroni-adjusted intervals over the six pre-registered
  contrasts, all three that separate still do.
- *Score per GPU-hour* in the generated report is an artefact of wall time rising from 74-77 s to
  87-97 s per run partway through, with the machine shared. It is flagged as not a result.

**Declined:** nothing. The pre-registration was not changed; all of this is reported alongside it.

## D034 — Experiment 02's task world was chosen by a scripted gate, after three failure modes

Everything in this entry used scripted controllers or discarded pilot shuffles only. No N2 run
existed while any of it was decided.

**A gate that passed, then failed, then passed for the right reason.** T1 ("single nose": one
food sample at the head, copied to both sides) was meant to require memory. Its gate, set before
any N2 run, was that a scripted controller with one tick of memory must beat the best memoryless
one. On the first, narrow tuning grid it did (0.923 against 0.597 on 1408 held-out worlds). The
memoryless controller's tuned values sat on grid edges, and on a widened grid it scored 1.457
against the memory controller's 0.943. That comparison was itself flawed: it pitted pure memory
against pure kinesis ("slow down on food"), two different strategies. With nested families,
where memory and stereo are added on top of kinesis and fall back to it exactly, memory pays.
The gate now asks how much a capability adds, not which of two strategies wins. (Fable 5.1 reached
the same conclusion independently.)

**The food ran out.** Sensing read the food field directly, so there was no signal beyond a
patch's edge. And in 400 ticks the best controllers ate essentially all the food (a median of
98-100% of each world's food) in every arena size and odour width tried. At that ceiling, better
controllers cannot score higher, and differences between brains are compressed. This probably
also compressed 01b's comparison: its champions scored close to the scripted ceilings.

**The fix, chosen by a rule set before seeing results.** The rule was "the passing setting with
the fewest changes from 01b's world". T0 and T1 run with an opt-in food odour (the sensed food is
a Gaussian blur of the food field, sigma 1 cell), 200-tick episodes, and twice the food per
patch. The anchor cell keeps 01b's world exactly.

**Doubling the food saturated the input.** At the old sensing scale, 17% (T1) and 28% (T0) of
the best controllers' non-zero food readings sat at the input clamp, so the signal went flat near
every patch centre. The task world halves the food sensing scale: 1.1-1.2% at the clamp.

**The gate as passed** (scripted, tuned on 64 worlds, scored on 256 separate validation worlds):
memory adds 0.399 [0.383, 0.415] of the best T1 controller's advantage over straight-running;
stereo adds 0.435 [0.418, 0.452] on T0; stereo beats single-nose-with-memory; the best controllers
eat 70-74% of the food. No tuned value sits on a non-physical grid edge. Two edges checked to be
physical limits are declared as such: a threshold at the input clamp means "never slow down", and
stereo gains beyond 8192 change scores by less than 0.2%.

## D035 — Calibration uses 2048 random genomes; 24 carried about 12% sampling error

One random genome's motor drive has a standard deviation of 0.25-0.31 on a mean near 0.4. So a
calibration fitted on 24 genomes, as in 01b and the first attempt here, carries about 12% sampling
error per graph. The first in-world calibration converged to 2% on its own 24 genomes, but on an
independent 24 it validated at 0.35-0.64 forward and 0.26-0.51 turn (targets 0.5 and 0.4).
Fitting and validation now use 2048 genomes each, and every graph variant validates within 3.5%
on the independent sample (tolerance 4%, about two standard errors of the difference).

A single run's own generation-0 population is only 32 genomes, so its drive scatters about 12% by
sampling alone. It is reported, never tripwired.

**For 01b:** its per-graph gains carried about 12% sampling error, which is consistent with the
84-97% residual measured in its review (D033).

## D036 — Wrong food mappings: routing is a hard per-pair tolerance

The planned rule matched the average of each remap triple to the food neurons on six scaled
features. It admitted shortcut pairs twice. A triple-average rule let URX in (13 units of direct
read-out weight, one hop) behind a weakly connected partner. A scaled pairwise rule let BAG, OLQD
and OLQV in (12-20), because the extreme shortcuts (FLP, at 174) inflate the scale of the
direct-weight feature. So routing is now a hard per-pair tolerance: at least 1.5 hops to the
forward and to the turn read-out, and at most 2 units of direct read-out weight (the food pairs
have 0-1). Degree is matched pair by pair among the six pairs that qualify. The result:
R1 = ASJ, ASI, ASG (all amphid chemosensory); R2 = PLN, IL2D, IL2V; MS = FLP, PHB, PVD. With exactly
six eligible pairs, R1 and R2 are a forced partition that falls along sensory modality. The
screening's "R1 and R2 disagree" tripwire therefore also tests whether modality matters.

## D037 — The history-only ablation is jitter of 1 cell, chosen on scripted controllers

Replacing food with a constant, or with the mirrored signal, tests whether a champion uses food at
all, not whether it uses food history (Fable 5.1). Six candidate ablations were tried on the
scripted controllers of the final task world. To count as valid, an ablation had to leave the
memoryless controller unchanged within its interval and remove the memory controller's advantage.
Only "jitter" with radius 1 qualifies: food is read at a random point within 1 cell of the true
sample point, fresh every tick. It changes the memoryless controller by -0.002 [-0.008, +0.005]
and takes memory's advantage from +0.96 to -0.21. Larger jitter also degrades the memoryless
controller, and every "hold" setting changes it (+0.04 to +0.06).

## D038 — The feasibility gate failed; the screening measures capability use instead of assuming it

*Parts superseded by D040 (the verdict rule, the SH prevalence bound, the disclosure's count).*

The pilot's feasibility gate (D034) failed as pre-set: the 40-generation T1 champion on a pilot
shuffle beats the tuned memoryless controller by +0.59 but is not hurt by the validated history
ablation (+0.004 [-0.012, +0.019]). Exploration on pilot shuffles only
(`experiments/02-screening/exploration/`) showed that more generations (to 120), four times the
training worlds, or four times the population do not produce clear history or stereo use. So
the scripted gate shows the capabilities pay; it does not show that 40 generations of evolution
find them.

Options considered: redesign the evolutionary setup or the tasks (no candidate with evidence
that it would work), stop, or run the screening and make each champion's capability use a
measured outcome. Astra 6 reviewed the last as a conditional go (its decision review, 11 points,
all checked against the files) and the design adopts it with every fix it named:

- **Estimands.** For each frozen champion and probe p, U_p = mean over probe worlds of the real
  score minus the score under p (signed). N2's mean over runs, SH's mean over equally weighted
  graph means, and their contrast Delta_p; per task, the mapping interaction
  Delta_p(M0) - mean(Delta_p(R1), Delta_p(R2)). Every champion is probed at generation 0 and 39,
  so a starting advantage is separated from acquisition.
- **Primary mechanistic outcome:** Delta for the bilateral-mean probe on T0-M0 at generation 39.
  The prediction, motivated by preliminary N2 evidence (disclosed below) and so labelled: *under
  the registered 40-generation procedure, N2 champions show greater, meaningful dependence on
  bilateral food information than champions from the sampled shuffle distribution.*
- **Thresholds, frozen now:** meaningful use means the interval lies above 0.10 score units (about
  a tenth of the scripted stereo or memory gain); a probe is valid when a controller that cannot
  use the capability moves less than +-0.02, interval included. Supported: Delta above zero and
  N2's use meaningful. Challenged: N2's use tightly below 0.10, Delta reversed, or Delta
  straddling zero inside +-0.10. Otherwise inconclusive. Everything else (history jitters, swap,
  single nose, constant food, the fitness interactions) is secondary and exploratory, with no
  multiplicity-adjusted claims drawn from it.
- **Not claimed:** that shuffles *cannot* acquire a capability. With eight graphs, zero of eight
  showing use bounds the rate below about 31%; it never shows absence.
- **Replication raised** with the freed budget: N2 from 4 to 8 runs, SH from 6 to 8 graphs x 2
  runs (190 runs). Earlier units keep their seeds. SH7 and SH8 are calibrated and the new seeds'
  scripted reference scores computed with the frozen controllers (`scripts/exp02.py extend`),
  adding only missing values.
- **Implementation blockers fixed:** the report read diagnostic keys that were never written
  (`one_step_memory` / `level_kinesis` instead of `M` / `K`); a smoke test now runs the whole
  report on synthetic records with the committed diagnostics, calibration and schedule. Probes
  save per-world scores, world ids and the probe seed, on 64 dedicated probe worlds separate from
  convergence monitoring. Convergence is fitted per graph family.

**Disclosure.** Before this decision I saw one N2 number: the generation-0 turn response to a
left-right food difference under M0 (0.12, against 0.009-0.030 for eight pilot shuffles). It was
measured with a probe that confounded the difference with the total food level (Astra, point 3),
so it does not establish a routing difference. N2 under the remaps was not looked at. No N2
fitness, evolved or scripted, was seen.

## D039 — Stereo and history probes, validated on scripted controllers with an equivalence rule

The D037 validity rule accepted an interval that merely contained zero as "unchanged". It now
requires the whole interval inside +-0.02 (`probe_validation.json`). Jitter 1 still qualifies
(memoryless change -0.002 [-0.008, +0.005]); jitter 2 and 3, and every hold, do not.

Jitter probes are **history-sensitivity outcomes**, not a test of history use. Jitter 1 was
validated on one scripted memory strategy only; a controller integrating over several ticks can
average it out, and a memoryless nonlinear one can be hurt by it. Jitter 3 costs the memoryless
controller 0.057 by itself, so the 120-generation pilot's +0.039 under jitter 3 is not evidence of
history use. A stronger test (matched-current replay of different food histories) is deferred,
and so is any claim that a champion uses history.

Single-nose substitution ("mono") also moves the sample point and changes the common mode.
The primary stereo ablation is therefore the **bilateral mean**: (L+R)/2 fed to both sides, on raw
readings before scaling and the input clamp. It removes only the left-right difference. The
**swap** (L and R exchanged) reverses it and is supporting evidence of directional steering. On
the gate worlds (T0):

| probe | memoryless K changes by | stereo gain S - K (without: +1.113 [1.069, 1.156]) |
|---|---|---|
| bilateral mean | 0 exactly | -0.080 [-0.098, -0.063] |
| swap | 0 exactly | -1.846 [-1.896, -1.796] |
| single nose | -0.002 [-0.005, +0.001] | -0.079 [-0.097, -0.061] |

K reads only the bilateral mean, so its invariance under the mean probe holds by construction and
checks the implementation, not the probe's specificity.

The generation-0 input-response probe is corrected too: the left-right difference at a fixed
common mode, (b+d, b-d) against (b-d, b+d), signed and absolute, raw read-out and motor command,
through the interface's sensor gains and clamp. On the eight pilot shuffles its directional turn
response is 0.0015-0.0045 raw (b = 0.1, d = 0.05; `exploration/structure_and_timing.json`).
N2's value is a registered outcome, not yet measured.

## D040 — The pre-registration after Astra's review: nine fixes

Astra 6 reviewed the first version of `PREREGISTRATION.md`. Its verdict was no-go as written.
Each of its nine points was reproduced or checked, then fixed with a test that failed first. The
list is in the pre-registration's §11; the review is in `experiments/02-screening/reviews/`. Three
of the fixes change what D038 said:

- **Verdict rule.** "Challenged" no longer includes a Delta that straddles zero inside +-0.10.
  Support never required Delta to be large, so that branch tested a different hypothesis.
- **Incomplete data withholds the verdict.** With one N2 run and one SH graph, the old code
  returned "supported" with zero-width intervals. Now all 8 N2 runs and 8 SH graphs are needed in
  T0-M0, each with 64 finite probe scores on the registered worlds and seed. These units are the
  first 16 batches of the schedule.
- **No prevalence bound for SH.** "Zero of eight bounds the rate below 31%" assumed error-free
  binary outcomes. A graph's classification comes from an interval, and a capable graph can stay
  inconclusive. The count is reported as a detection count only.

The other fixes: the report crashed on a NumPy boolean, and the smoke test hid it. The probe
budget fallback was promised but not implemented; it is now staged and resumable, and a dropped
input reads "not assessed". The convergence criterion is named for what it measures (90% of the
fitted improvement). Variance components handle unequal replication. The stated scopes match the
code. D038's disclosure said "one N2 number", but the measurement gave two: difference 0.12 and
common mode 0.16.

A confirmation pass by Astra found three of the nine only partly fixed. Completeness checked graph
names, not the registered runs and seeds; removing every SH run 0 still gave "supported", and a
short probe vector crashed the report. A resumed probe run forgot measured costs, retried dropped
steps, and printed "not assessed" as "ok". The pre-registration still named 16 behaviour worlds in
one place. All three are now fixed. Every paired difference goes through one checked helper
(`analysis.paired_diff`), and malformed entries are listed and left out.

## D041 — Fable's review of the pre-registration: symmetry, jitter on T0, split verdicts

*Post-publication pointer (2026-09-27; the entry below is unchanged):* its mirror-symmetry rationale
is wrong. See `experiments/02-screening/RESULTS.md`, Corrections (D050).

Fable 5.1 reviewed the pre-registration at 08:00. The evolution had started at 06:25 from commit
225e8f8; no probe had run and no N2 result had been read. Fable found nothing that required
stopping the evolution. All ten of its points were checked and adopted, and they change only
probes, analysis and wording (the review is in `experiments/02-screening/reviews/`):

- **Mirror symmetry is an unnamed explanation of the primary.** A degree-preserving shuffle
  destroys left-right pairing, which N2 has and a bilateral turn read-out rewards. The remaps
  cannot control for it, because R1 and R2 are symmetric pairs too. This is confirmed
  structurally: the pilot shuffle SH101 keeps 15% of chemical edges under the left-right
  relabelling. The pre-registration now reads a supported primary with a comparable remap
  advantage as a symmetry effect. It also reports mirror symmetry and the food pairs' routing
  per graph (`wormwars/exp02/structure.py`).
- **On T0, jitter is not a history ablation.** It moves both noses independently. On scripted
  controllers it costs the memoryless stereo controller 0.029 at radius 1 (and 0.535 at 3), while
  the memoryless kinesis controller stays within equivalence. The T0 jitters are relabelled
  spatial-noise sensitivity. The rerun of `validate-probes` reproduced every earlier value exactly.
- **"Challenged" is split** into "no meaningful N2 use" and "contrast reversed". The rule is
  unchanged.
- t-intervals are reported next to the 8-unit bootstrap, and raw-score fitness estimates next to
  the normalised ones. The eight continuation runs' generation-79 champions are probed. The anchor
  tripwire now reads as a procedure change, not a bug. The wording on probe worlds is corrected.

## D042 — The results after review: the shuffles catch up; several readings withdrawn

Astra 6 and Fable 5.1 reviewed the first version of `experiments/02-screening/RESULTS.md`
(`6dc7d71`). Both confirmed every number they could trace. Both found the readings stated more
strongly than the registered rules or the data allow, and several registered outcomes missing.
Each point was recomputed before it was adopted:

- **"Evolution erodes N2's generation-0 advantage" was wrong in kind.** The paired change in the
  T0 interaction is −0.061 [−0.108, −0.014]. But N2's own normalised preference for M0 over the
  remaps is unchanged (+0.026 at generation 0 and 39 on T0). The shuffles' best random brains
  start worse under M0 (−0.042) and catch up (+0.019). Astra found this.
- **Withdrawn:** "not on its history" (jitter cannot show absence), "stereo steering is real but
  worth little" (swap sensitivity already exists in 8 of 72 generation-0 champions), "N2 reads
  food more strongly" (N2 scores 1.38 under constant food against SH's 1.74, so it is an
  intervention effect), and "topology, not strengths" (no equivalence margin; mutation erodes
  the initial magnitudes).
- **Added:** the §4 companions, jitter 3, the common-mode response, generation-0 magnitudes,
  gap-on valence, behaviour, intake and per-run drive. Added post hoc: the T0 R1 − R2 contrast
  (+0.063 [+0.011, +0.116]), which the T1-only tripwire did not compute.

## D043 — Last corrections to experiment 02's results; experiment 03 is open

A consultation on whether the revised results are ready and what experiment 03 should be
(`experiments/02-screening/reviews/20260925-153539-next-step/`). Every factual claim was checked
against the saved data before anything changed:

- **Astra was right** that N2's large directional response is general input sensitivity.
  Relative to its common-mode response, it is ordinary: 0.49, against 0.45-0.54 for the shuffles.
- **Fable's drive confound does not hold.** Motor gains were calibrated under M0 only, but the
  recorded generation-0 drive is the same under every mapping. It cannot explain the
  generation-0 interaction.
- **Fable was right** that the anchor was compared across units. Raw, it is +0.031
  [−0.049, +0.105] against 01b's +0.069 [−0.015, +0.169].
- **Computed at Fable's suggestion:** stereo use does not correlate with score within any T0
  cell (r ≈ 0), so there was no selection gradient for stereo. **Found by Astra:** all eight
  continuation runs kept improving.

Both consultants recommend that experiment 03 be a cheap generation-0 structural study (about
2-5 GPU-hours, no evolution). It would add routing-matched and mirror-matched shuffle ensembles,
gaps on and off, and per-brain values saved. Both rank a task that needs history or stereo second,
and both say to defer plasticity. The choice is the owner's.

## D044 — The roadmap review, and silencing is not deletion

Astra 6 and Fable 5.1 reviewed `ROADMAP.md` and the owner's 03a draft v2
(`docs/reviews/20260925-163118-roadmap/`).

**Where they agree:**
- Fund 03, the generation-0 structural study, first.
- Register effect and equivalence margins for its "N2 still stands out" gate, so that a noisy null
  cannot trigger "generic explanation, stop".
- Drop the rule that 04 runs only if 03 favours N2. 04 needs 03's controls and its own
  capability-feasibility pilot, not a positive 03.
- Run only a pilot of 03a before any full panel, and do not tag 03a v2 as written.
- Test task specificity: N2's edge on a matched non-wormy task.
- Reject the ROADMAP's "stop, don't pivot".

**Where they differ:** plasticity. Fable says defer it. Astra says to design one adaptation task
and one plasticity rule now, because the owner's question includes plasticity.

**03a, the biggest risks they name:**
- The free search will wire shortcuts through interface neurons (Fable).
- Non-identifiability under arbitrary fitted weights and a permissive task (Astra).

**03a, also needed before a tag:**
- a feasibility pilot with a registered pass criterion;
- a no-headroom class and a reference-failure class;
- several original-partner refits;
- a search-level margin;
- a curated left-right annotation;
- an initialisation independent of the hidden partners;
- a budget recount. Astra's recount of the written allocation is about 14 million genome
  evaluations, or 353 GPU-hours unbatched, not 280. This was checked.

**Checked in the code, and fixed:** only silencing exists (`Brain.silence`), and its docstring
claimed a silenced neuron "contributes nothing to the gap coupling". It does contribute: partners
keep their gap conductance in the implicit term, so a clamped neuron pulls them toward 0. The
draft's distinction between silencing and deletion is correct. The docstring is fixed, and a test
pins the behaviour. Experiment 01's ablation section used silencing and named it as such. Its
readings describe the reversed graph and are already superseded.

## D045 — The owner's delegated decisions: roadmap v2 and 03a v3

The owner published experiment 02 (`main` at `5706c7e`) and delegated three open decisions. They
are recorded here with their reasons.

1. **Plasticity: design now, run later.** Astra's view is adopted, because the owner's question
   names plasticity, and a pipeline without it could exhaust itself before testing that qualifier.
   Fable's condition is kept: the run waits until a task and search are validated (pilot 3b). The
   design is roadmap item 3c.
2. **Roadmap v2** (`ROADMAP.md`). The order is 02b, then 03, then three pilots, then the
   substantial experiment chosen by the pilots.
   - 03 grows to 64 graphs per ensemble, with registered margins, a task-specificity contrast
     against a matched non-worm-like task, motor-side remaps, class-preserving shuffles and
     N2 with the chemical direction reversed.
   - 04 no longer waits for 03 to favour N2.
   - A generic explanation narrows the claim; it does not stop the series.
3. **03a draft v3** (`experiments/03a-self-consistency/DRAFT.md`). It folds in both reviewers'
   points; the list is at its end. The largest changes:
   - candidate partners exclude interface neurons;
   - a six-way classification with a no-headroom class and a reference-failure class;
   - replicated refits;
   - pilot-derived margins;
   - the main control is routing- and mirror-matched shuffles;
   - a feasibility pilot with a pass criterion, which gates the panel.

   The budget recount for v3 as written is about 31 million genome evaluations, about 785
   GPU-hours unbatched. The one-week cap therefore binds unless batching gives more than 5 times
   the speed.

The owner's hypothesis and the authorship credits are unchanged. v3 goes to the reviewers before
any code.

## D046 — Fable's review of roadmap v2 and 03a v3: a cost error, and a leaky classification

Fable 5.1 reviewed roadmap v2 and 03a v3 (`docs/reviews/20260925-172550-v3/`). It found none of
its earlier points missed or misread. Astra 6's review failed on a usage limit and is pending.
Adopted, after checking:

- **Roadmap item 03 was costed two orders of magnitude too low.** "About 5-8 GPU-hours" came from
  extrapolating 02's small generation-0 stage. The written plan is about 1.6 million genome
  evaluations per condition, about 41 GPU-hours at 02's throughput. The cost is now set by 03's
  pre-registration, choosing a base fitness condition or fewer genomes per graph, after a
  measured timing. The pilot costs are restated in the same way.
- **03a's classification leaked** (v3.1 fixes it):
  - every comparison is now three-state, and each step is two-sided;
  - per-target overlap is judged against each target's permutation null, because a fixed AUC
    band is unreachable per target;
  - δ_search comes from original-partner refits;
  - the analysis set is fixed;
  - equivalence bands are fixed for every hypothesis;
  - the refit screen in the pilot runs in the NIP arm, as an interval statement;
  - the budget adds the whole-brain evolutions.
- **03a v3.1 is ready for code and the disclosed pilot**, in Fable's judgement, with the
  before-tag items now written in. Astra's review is still pending.

## D047 — Astra's review of v3.1, at maximum effort; where it and Fable disagreed

The owner upgraded their ChatGPT plan, so Astra 6 now reviews at maximum reasoning effort.
It reviewed roadmap v2.1 and 03a v3.1 (`docs/reviews/20260925-174815-v31/`). Its verdict: code can
start, but the go/no-go rule of the pilot needed revision. 03a v3.2 and roadmap v2.2 adopt all 13
points.

**A correction to D046.** D046 said 03a v3.1 was ready "in Fable's judgement". Fable had assessed
v3, not v3.1, and called it "nearly" ready if two changes were made. D046 overstated Fable's
endorsement. Astra caught this.

**Where Astra and Fable disagreed:**
1. **One-sided steps (Fable's point 5) against preserving uncertainty (Astra's point 1).** Astra's
   view is adopted. Fable was right that v3 missed the two-sided cases, but its fix counted
   "undetermined" as "no headroom" and "not identifiable", turning uncertainty into negative
   evidence. In v3.2, undetermined stays undetermined, and random partners beating the original
   are reported as a difference.
2. **Per-target overlap (Fable's point 6) against its reading (Astra's point 4).** Both are
   partly adopted. Fable's permutation null stays, since a fixed band is unreachable per target.
   Astra's reading replaces the labels: inside the null is "no enrichment detected", not
   substitution. Functional substitution is claimed only at cell level, with an equivalence band.
3. **"The ensembles are nested" (Fable) against "class-preserving is a separate branch"
   (Astra).** Astra is right, and the roadmap now reports compatibility with each ensemble.

**Also adopted:**
- attributes reported instead of an exclusive classification order;
- a scientific performance margin (5% of the intact score), separate from the noise estimates;
- a pilot that requires NIP headroom, not only an advantage over random partners;
- the N2 task controls moved after the freeze;
- mutually exclusive verdicts;
- a crossed-and-nested bootstrap, with common analysis sets for paired contrasts;
- 03's fitness plan keeps the remaps, which signal (b) needs;
- pilot evolutions 10, not 18.

The arithmetic was re-checked: 31 104 000 search evaluations, about 785 GPU-hours at 11 per
second, and whole-brain evolutions add about 37.

## D048 — 02b: a true deletion operator; criticality follows N2's hubs, not the food route

*Its readings are corrected by D049: several were stated too strongly.*

Roadmap item 1 ran, exploratory, in about 40 GPU-minutes (`experiments/02b-champion-analysis/`).

**Added to the code:**
- `wormwars/deletion.py`, which removes every edge touching a neuron, and its bias. It is tested
  to match a 301-neuron network built without the neuron, and to differ from silencing.
- `World.last_signals`, what each wey sensed on the tick it acted.
- A `genome` option on the input-response probe, so it can run on evolved champions.

**Findings:**
- **Deletion criticality in N2's T1 champions** picks out AIZ, RIA, AIY and RIB in nearly every
  run. A control with food entering through the wrong neurons (R1) keeps the same core: rank
  correlation 0.84, and even the unused AWC and ASE are critical. These are structural hubs, not
  the food route. N2 champions depend on fewer neurons than SH champions (54 against 88 of 245).
- **History dependence** after matched current input grows 2-6 times with evolution, most for N2,
  but its direction is inconsistent across runs.
- **Evolved N2 champions steer toward food; shuffles do not.** The swap cost is the same for both.
- **Anatomical magnitudes are eroded:** the rank correlation of |w| with anatomy is 0.35 at
  generation 39.

**Consequences:** 03a's high-criticality N2 panel will be hub-dominated, and 03's registered
signals should include N2's generation-0 history dependence.

## D049 — 02b after review: level memory, a mapping-independent core, no N2-specific steering

Astra 6 and Fable 5.1 reviewed 02b v1, both at maximum effort
(`docs/reviews/20260925-184331-02b/`). Both confirmed its numbers and the deletion operator. Each
point was checked before it was adopted, and 02b v2 was recomputed from the saved genomes.

**Bugs:**
- Turn persistence compared neighbouring weys, not the same wey over time. It is 0.997-0.999 in
  every group, so "N2 circles less" is withdrawn.
- The history table's forward values were censored by the motor clip.
- The rank correlations mishandled ties.
- `delete_neurons` accepted index −1 (it now raises, with tests).

**Controls added:**
- A mutation-only drift control, and one stimulus bank per run shared by every genome of that
  run.
- An R2 criticality control (non-amphid food).
- A kept-edge check for 03a.
- A null strain in every deletion batch.

**Readings changed:**
- History: selection, not drift, raised the turn read-out's history dependence in every group.
  But it is a persistent memory of the recent food level (about 0.9 of the steady-state contrast,
  about 0.85 left after 5 ticks), not a computation on change.
- Criticality: AIZ and RIA are critical under all three mappings. The rest shifts with the
  mapping, and "hubs" applies to RIA only.
- Steering: both groups steer by side equally within wey. "N2 steers toward food" rested on two
  champions and is withdrawn.

**For 03a:** about a third of a high-criticality N2 target's deletion cost is carried by edges to
interface neurons, which 03a keeps fixed. Its next review should weigh this.

## D050 — Experiment 03 design v2: mirror symmetry reversed, the throughput plateau is real

Astra 6 (maximum effort) and Fable 5.1 reviewed 03's design v1
(`docs/reviews/20260925-210723-03-design/`). Checked before adopting:

- **Mirror symmetry forbids a left-right comparison at this read-out (Astra).** The turn
  read-out is dorsal minus ventral, and each group contains left and right neurons. So a
  mirror-equivariant network turns identically for food on either side. D041's rationale ("a
  symmetric graph gets the comparison almost for free") and the registered reading in 02's
  pre-registration are therefore wrong. That reading was never triggered, because the primary
  was challenged. `structure.py`'s docstring is corrected. SH-mirror stays as a control, now
  predicted to *lower* directional response.
- **Throughput (both reviewers):** v1's benchmark ran at 512 worlds per chunk. Rerun at up to
  16 384 per chunk, it stays at about 168 genome-world evaluations per second, compute-bound. The
  "about 2 times 02, not 5" consequence for 03a stands.
- **The shuffle sampler's silent attempt cap (both reviewers)** did not fire for any shuffle used
  in 01b or 02: each reached its full swap target. New samplers must fail loudly.
- **Adopted in design v2:**
  - routing constrained on weighted graphs for every fitness mapping;
  - an orbit-based mirror sampler with exact symmetry;
  - a defined class-preserving null;
  - N2perm as a control for weight placement;
  - T1 with constant food as the primary control task, and coverage as descriptive only;
  - a primary set of four signals with expected signs and Holm correction;
  - prediction-interval tests, with rank statistics reported beside them;
  - margins from a shuffle-only pilot;
  - 16 shared worlds with genomes paired across tasks;
  - per-graph calibration;
  - the motor remap dropped;
  - R3 and R4 impossible under D036.

## D051 — Experiment 03 design v3: reversible samplers, exact rank tests, the correct Holm order

Astra 6's confirmation pass on design v2, at maximum effort, rated 4 of its 16 points addressed
and the rest partly addressed, and found new flaws. All are adopted in v3:
- **Routing:** v2's routing rule only removed direct edges, so its moves were irreversible, and
  it capped weights one at a time, not their sum. v3 has a reversible count-level state space,
  joint weight allocation under an aggregate cap, and a final weighted check.
- **Mirror:** the mirror sampler preserves degrees within orbit categories and nearly freezes the
  46 left-right homolog gap junctions. v3 states this stronger null and checks orbit membership
  on the complete post-move graph.
- **SH-mirror's predicted decrease is withdrawn:** symmetric wiring with random weights is not
  equivariant.
- **The Holm order was wrong** for a claim across all ensembles. The maximum p over ensembles
  comes first, then Holm across signals.
- **The parametric prediction test is replaced** by exact rank tests with 128 graphs per
  ensemble.
- **Other fixes:**
  - equivalence at 0.5 SD, since 0.25 SD had about 26% power;
  - the pilot's precision check no longer measures N2;
  - structural acceptance rules are fixed before construction;
  - P1 and P4 have numerical definitions.
- **Budget:** about 12.8 GPU-hours, with a cap of 15.

## D052 — Structural validation of 03's ensembles: a mirror-sampler drift fixed; a reciprocity ensemble added

The ensemble build (structure only) passed every pre-set check: plateau, acceptance, overlap
ceiling, and no substitutions. Its statistics showed two problems, both fixed before any N2
measurement:

1. **The mirror sampler drifted self-connections to zero.** SH-mirror graphs had 0 autapses,
   against N2's 38 and about 15 for ordinary shuffles. The chain could destroy autapses but not
   create them, which is irreversible. The chain now allows creating them (a test pins it), and
   SH-mirror was rebuilt.
2. **Reciprocity was uncontrolled.** N2 has 669 reciprocal chemical pairs; every ensemble had
   about 126. Reciprocal loops are a plausible generic source of history dependence. A fifth
   ensemble, SH-recip, keeps the number of reciprocal pairs exactly (its test pins it).

**A statistic of mine was wrong:** reciprocity counted autapses as half-pairs, giving N2 688.
The correct figure is 669, and the sampler was always exact.

**Budget:** about 15.5 GPU-hours.

## D053 — 03's pilot failed its precision check; a seed bug; allocation and criteria revised

The registered precision check failed for all four primary signals: the stand-in shuffle's SE
was about as large as the equivalence margin. Astra 6 and Fable 5.1 were consulted, both at
maximum effort (`docs/reviews/20260925-222802-03-precision/`). Their main points were checked and adopted:

- **A seed bug (Astra).** The per-graph genome seed kept only the first four characters of the
  graph's name. So all 16 pilot shuffles shared one set of random genomes, every graph of an
  ensemble shared another, and N2 would have had its own. That breaks the exchangeability the
  rank tests need. Seeds now hash the whole name, with a test. The pilot is rerun, and the
  first pilot's file is kept locally for the record.
- **The precision SE was overstated for the fitness signals (Fable).** The single-graph crossed
  bootstrap double-counts the residual, and shared worlds cancel in the registered comparison.
  SE is now computed on all 16 pilots, from crossed variance components with the world profile
  common to all graphs removed.
- **P3 stays primary (Astra).** It is the signal closest to the owner's question. P2 becomes
  secondary. With three primaries, Holm's thresholds allow rank r ≤ 1, 2 and 5 of 128, not r = 0.
- **Allocation:**
  - P3's two cells get 256 genomes (genome sampling is about 95% of their variance);
  - P1 and P4 get 2048 random brains (P1's reliability at 2048 is about 0.9);
  - the T0 remap cells are dropped;
  - the secondary response conditions get 256.
- **Criteria:**
  - the "precision" rule becomes a reliability target;
  - "compatible with the ensemble mean" becomes "consistent": N2's interval lies inside the
    ensemble's central 90%, which is membership, not closeness to the mean (both reviewers);
  - margins are computed at run time from each ensemble's own 128 graphs, de-attenuated. The
    rule is registered, not a number from 16 pilots (Fable).
- **Code fixes (both):** "reversed" now needs its own rank test, and the joint bootstrap accepts
  per-genome signals.
- **A power simulation** of the full decision rule goes in the pre-registration (both).
- **Budget:** about 20 GPU-hours, over the design's cap of 18. It is restated once the rerun
  pilot measures the new cost.

## D054 — 03's pre-registration after review: enforced rules, N2 last, honest power

Astra 6 and Fable 5.1, both at maximum effort, reviewed the first version of 03's
pre-registration. Both said not to start. Astra reproduced verdict-changing failures on synthetic
data: "distinctive" with 60 graphs per ensemble, and with an N2 whose denominator was 1e-6. All
points were checked and fixed before any N2 measurement:

- **The report now enforces the registered rules** (`wormwars/exp03/report.py`, with tests):
  - one validity mask per signal, used in every path;
  - completeness withholds the verdict, and a withheld signal counts as p = 1 in Holm;
  - the P3 world profile uses registered ensemble graphs only;
  - the bootstrap sizes and seeds are fixed;
  - the secondary signals are implemented.
- **The runner** (`scripts/exp03.py`, with tests):
  - N2 and its variants run last and are exempt from the cap;
  - the cap is cumulative across restarts;
  - every measurement records its provenance (commit, input hashes, device); the report refuses
    a mixture, and the run refuses uncommitted code;
  - graph files are verified against the manifest at load;
  - calibration is validated for N2 and 8 graphs per ensemble.
- **The power simulation** now uses one N2 draw compared with all ensembles, and margins and
  intervals from the observed values. It adds the probability of "consistent" when N2 is a
  member: P3 is only 0.15, so P3 will usually be inconclusive.
- **Honest wording:**
  - the tests are approximate reference-ensemble tests;
  - the greedy weight repair is disclosed;
  - the hop rule was never enforced and is retired;
  - a null P3 is "criterion not met", not an upper bound;
  - reliability 0.9 for P3 would cost about 150 GPU-hours, not 75;
  - the error rate across both directions is 10%.
- **Within-ensemble pairwise Jaccard** equals each ensemble's Jaccard to N2, which is evidence of
  mixing.

## D055 — 03's confirmation pass: the last fixes before launch

Fable 5.1 and Astra 6 checked the D054 revision. Both found the verdict path fixed. Both asked
for one more commit before launch, and every item was checked and done with tests:

- **Crashes fixed:**
  - `cmd_report` crashed on an undefined name after writing its JSON;
  - an empty P3 reference set crashed instead of withholding.
- **Calibration failures** are now saved as excluded, counted graphs (withholding every verdict
  if N2's fails), instead of halting the run.
- **Resuming** refuses measurements from other code, inputs or devices, and the provenance check
  includes the device. So any mid-run code change means re-measuring every graph, and §9 says so.
- **Hashes** normalise line endings. The recorded input hashes now equal the committed-blob
  hashes of §3, which was checked. The dirty-check covers the registered inputs.
- **The power simulation** draws a "true member" from the ensemble instead of placing it at the
  mean. "Consistent if a member" is 0.52 (P1), 0.11 (P3) and 0.77 (P4), not 0.93, 0.15 and 1.00.
- **Wording:**
  - one leftover sentence claiming exchangeability is corrected;
  - the secondary outputs are stated exactly: values and ensemble quantiles, with no SEs or
    ranks for N2's secondaries.

## D056 — Deviation: 03's first run stopped at graph 53 on a faulty hash check; restarted from zero

The run from commit 0ef9a3d stopped after 52 ensemble graphs. The graph-file check refused
SH-class-30010. The cause was D055's line-ending normalisation. It was meant for the text inputs,
but the same hash function also checked the binary graph files. A compressed `.npz` that happens
to contain CR-LF byte pairs hashed differently from the manifest, which records raw bytes. 69 of
the 640 graphs would have been refused. Every graph matches its manifest hash on raw bytes, and
none was altered.

- **Fix:** graph files are hashed raw; only text inputs are normalised. There is a test.
- **Registered rule (§9):** any mid-run code change means re-measuring every graph. The 52
  measurements are set aside, not deleted: `runs/exp03/measures-aborted-0ef9a3d/`, with its log.
  The run restarts from zero at the new commit.
- **No N2 data existed:** N2 and its variants run last.
- **Cost:** about 1.6 GPU-hours.

## D057 — Experiment 03's results: P4 distinctive relative to every ensemble; P1 and P3 not

The run finished at commit 132acae: 645 graphs, 19.75 GPU-hours, every signal with 128 valid
graphs per ensemble, no calibration failure. The registered report
(`experiments/03-generation0/report.json`) gives:
- **P4, history dependence:** distinctive relative to every ensemble. N2 = 0.931. The maximum p
  over the ensembles is 0.0155 and the Holm-adjusted p is 0.0465. One SH-route graph is at or
  above N2, and none in the other four ensembles.
- **P1, directional selectivity:** not distinctive (Holm-adjusted p 0.93). N2 is consistent with
  SH and SH-recip, and inconclusive against the rest.
- **P3, food-information dependence:** the criterion was not met (Holm-adjusted p 0.94), and N2
  is inconclusive against every ensemble. This is not a bound.

**Decisions:**
- **RESULTS.md separates** the registered verdicts and secondary values from exploratory analysis
  (§11). Exploratory: the P4 numerator and denominator decomposition, the reading of the N2
  variants beyond their values and ranks, the comparison with 02b, and the corrections to 02's
  readings.
- **The P4 verdict is reported as borderline.** Two graphs at or above N2 in any one ensemble
  would have given a Holm-adjusted p of 0.070. The registered power at the observed z (2.2-2.5)
  was low. It passed because three ensembles' latent SDs were about half the pilot's.
- **Two of 02's readings are marked as not holding at generation 0:**
  - the signed directional response (+0.0029 in 02, +0.0001 here);
  - "shuffles start worse under M0" (every ensemble's mean P2 is about 0).
- **The per-graph measurements (about 640 MB) stay local,** git-ignored. The report, with every
  per-graph value, is committed.
- **Next:** results review by Astra (xhigh) and Fable. Nothing is pushed without the owner's go.

## D058 — Experiment 03's results review: write-up corrected, verdicts unchanged, replication recommended

Astra 6 (xhigh) and Fable 5.1 reviewed RESULTS.md at f5ab9d9 independently
(`docs/reviews/20260926-220511-03-results/`). Both reproduced the registered verdicts; Astra
recomputed all 15 signal-by-ensemble classifications from `report.json`. Neither found a rule
chosen after seeing the data. Each finding below was checked against the code, the report or
the raw measurements before it was adopted.

**Adopted (both reviewers unless named):**
- **The "why it passed" explanation was wrong.** Smaller latent SDs cannot explain passing the
  rank test, which does not depend on scale. What is relevant is the ensembles' compressed,
  left-skewed upper tails. Checked: the maxima are 1.7-2.5 latent SDs above the means; SH-class
  has skew −1.75 and a minimum 4.7 SDs below. The write-up now says the reason is not
  established.
- **The margins were never binding;** only the rank gate is borderline. This is now stated, with
  the attainable Holm values 0.023 / 0.047 / 0.070.
- **Rank p is exact only under exchangeability** (§2), so these are approximate reference-ensemble
  tests. The IUT and Holm logic, and the 10% two-direction error, are now spelled out (Astra).
- **The null moves weights as well as wiring,** so a rejection does not isolate wiring.
- **The "one constraint at a time" example was false:** SH-mirror includes the routing cap.
  Checked in `samplers.py` (Astra).
- **P1's "inconclusive"** comes from N2's interval not fitting inside the three narrower
  ensembles' central ranges, not from small margins (Astra, checked in `verdict.py`).
- **P4 is not bounded by 1** (Astra). Within N2, the lowest-contrast quarter of genomes has a
  ratio of 1.37. The "understates, not creates" sentence is deleted, and §7 of the
  pre-registration is annotated, with its registered text kept.
- **N2-rev's P4 is a ratio of two numbers near 4 × 10⁻⁴,** so it no longer supports any argument
  (Fable).
- **Calibration** acts only on the motor outputs, after the raw read-out, so it cannot enter P4 or
  the raw magnitudes. The saturation check: within N2, the ratio does not rise with the contrast
  (correlation −0.04). The forward read-out shows the same pattern (N2 0.899; at most 2 graphs
  per ensemble at or above it).
- **The 02b comparison:**
  - it gives the aggregations correctly (0.88 is a median of per-genome decays);
  - it notes the different stimulus banks and the shuffles' own 0.75-0.84;
  - it no longer suggests that N2 is born where selection took the champions.
- **The corrections to 02** now separate a different estimand from a failed replication. "P2 is
  zero" becomes "its 95% intervals include zero".
- **An auditable supplement:** `supplement.py` writes `supplement.json`, with per-graph P4
  numerator and denominator, the forward-read-out ratio, the common mode, the gains, and
  calibration validation (Astra). Calibration validation is within 7.4% of target everywhere,
  and within 3% for N2.
- **Minor numbers:** z is 2.2-2.6; P1's SE is 0.0205; the top-decile medians are 1.49-1.53; the
  P3 ensemble means are +0.0006 to +0.0026; the variant ranks are now counts r.

**Deferred:** `report.json` keeps `NaN` for N2-rev's invalid P1 (Astra). It is the registered
output as produced. A publication export could use `null`. The write-up notes the issue.

**Where they disagree: replication before publishing.**
- Both recommend a separately pre-registered replication. It would use fresh ensemble draws (256
  for SH-route, since one graph decided the result) and independent genome draws for N2 and the
  controls, and would report either outcome.
- **Fable:** replicate before any public claim.
- **Astra:** the honestly qualified report of this completed experiment can be published first.
- This is the owner's call, and it is put to them.

## D059 — The owner chose a full replication of experiment 03 before publishing

**Decision (the owner, 2026-09-26):** run a full, separately pre-registered replication of
experiment 03 before anything from 03 is published: option 1 of three. When 03 is published, the
publication must say plainly that a full replication was done, why, and what each AI contributed
to that decision.

**Who contributed what:**
- **Fable 5.1** (results review, D058) judged the P4 verdict not publishable as a public claim
  without replication: "Replicate before any public claim." It gave the reason: the pass
  condition is discrete (at most one graph at or above N2 in every ensemble), and it was met with
  exactly one routing-matched graph above N2. It proposed fresh draws of at least SH-route and
  SH-mirror, ideally all five, with 256 graphs for SH-route.
- **Astra 6** (results review, D058) recommended a separately registered replication with fresh
  graph draws *and* independent genome draws for N2 and the controls, because reusing N2's
  measurement tests only part of the uncertainty. Astra did not require it before publishing: an
  honestly qualified report of the completed experiment could go first. It also asked that either
  outcome be reported, and that nothing be rerun until the threshold passes.
- **Claude Opus 5.5** (the experimenter) put the disagreement to the owner with three options and
  costs:
  - a full replication (about 24 GPU-hours);
  - a targeted replication of SH-route and SH-mirror (about 12);
  - publishing the qualified report now.
  It leaned slightly toward replicating first, because one graph decided the result.
- **The owner** chose the full replication.

**What the replication takes from each:**
- from Fable: all five ensembles, 256 for SH-route;
- from Astra: independent genomes for N2, pre-registration, either outcome reported, no reruns
  until it passes.

Its design is `experiments/03r-replication/PREREGISTRATION.md`, reviewed by both before the run.

## D060 — 03r pre-registration v2 after Astra's and Fable's review

Both reviewed v1 (`docs/reviews/20260926-225906-03r-prereg/` for Astra,
`docs/reviews/20260926-225909-03r-prereg/` for Fable). Both judged it a faithful replication,
runnable once the outcome rules were complete.
- **Astra** re-verified the 768 manifest hashes, the distinctness of all 1 408 ensemble graphs
  across 03 and 03r, and the seed streams.
- **Fable** recomputed the power figures by hand.

Each finding was checked in the code before it was adopted:
- **Outcome wording is fixed in advance** for every case (§10): both rules pass, a split between
  the rules (probability about 0.5), a failure with or without consistency, and withheld.
  - The gate table is published whatever the outcome.
  - The two runs are presented side by side and never pooled or combined as confirmatory.
- **Per-ensemble gates** in `single_signal`: under the maximum-p rule, one failing ensemble makes
  every label read "inconclusive" (Astra reproduced this).
- **A withheld primary is written, not omitted** (`replication_primary`).
- **A fresh secondary permutation:** confirmed, the permuted-magnitude condition reused 03's
  permutation for N2 and N2-rev (`init_permutation_seed` 0). It is now fresh per graph in 03r.
  Instance 03 is unchanged.
- **Retained elements are listed:** the stimulus bank, the remaps, the analysis seeds and the
  configs. The calibration seed also sets the calibration world's map (confirmed in
  `calibration.py`).
- **§7 is relabelled** as a posterior-predictive probability of passing the rank gates, with:
  - a uniform-prior sensitivity (0.91 and 0.17 at N2 = 0.931);
  - N2's measurement noise (0.80 at 0.915);
  - its omissions.
  Astra's figures are reproduced by the updated `power.py`.
- **The supplement** now counts missing and failed graphs, masks ratios below 10⁻⁴, summarises
  every promised quantity, and checks provenance. There are tests. 03's supplement regenerates
  with every value unchanged.
- **SH-route's completeness floor is 240.** The report gives planned, measured,
  calibration-failed, signal-invalid and valid counts, plus 03's P4 beside 03r's.
- **The cap is registered in code** (28 GPU-hours). A different value on the command line is
  refused, and the cap is never extended.
- **The N2 cache** is hashed into 03r's provenance.
- **Wording:**
  - the two runs are not independent evidence;
  - a recurring P1 or P3 label is not evidence of absence;
  - the probe caveat goes into the README sentence;
  - 256 SH-route graphs are Fable's request, not a power decision;
  - the threshold argument for P4 alone is stated.

**Checks:**
- Instance 03's report regenerates identically after the changes.
- A smoke measurement of one 03r ensemble graph (SH-1010000, not N2; not saved) ran the new path
  end to end in 126 s.

## D061 — 03r pre-registration v3 after the confirmation pass

**The verdicts:**
- **Fable:** ready to bind once one §10 sentence is corrected and the N2 cache is hashed raw.
- **Astra:** not ready until two must-fix items are corrected.

Both reviews are in `docs/reviews/*-03r-prereg-recheck/`. Every point was checked in the code
before it was adopted:
- **A withheld verdict lost the per-ensemble statistics** (Astra, reproduced). `build` now
  computes the descriptive per-ensemble statistics whenever N2 is valid. `replication_primary`
  reports the gates when withheld, and the side-by-side with 03 is written whenever it exists.
  Tested. 03's report regenerates identically.
- **The preflight measurement is disclosed** (Astra): SH-1010000 was measured once and not saved,
  and the values inspected are listed in §1. The binding boundary is the commit in the formal
  run's first saved measurement.
- **The N2 cache is hashed raw** (Fable): `_input_sha` uses the raw hash for `.npz` inputs; 03 has
  none, so it is unchanged.
- **The cap is raised from 28 to 32 GPU-hours** before binding (Fable's headroom point: 126 s per
  graph in the preflight would need about 27 h).
- **The supplement** drops non-finite values and requires provenance (Astra). 03's supplement
  regenerates unchanged.
- **Text:**
  - the threshold argument is softened with Astra's figures;
  - the claim that "one failing ensemble makes every label inconclusive" is corrected;
  - N2perm4-6's permuted-magnitude condition is noted as a second permutation;
  - a resume counts N2's seconds.
- **Astra's final check of v3** (`docs/reviews/20260926-233226-03r-prereg-final/`) found that
  ensembles with 0-1 valid graphs were still dropped, and that a valid N2 could then be reported
  as invalid (both reproduced). Those rows are now kept, with undefined statistics marked
  unavailable. Tested; 03's report is unchanged.
- **Astra's second final check** (`docs/reviews/20260926-234038-03r-prereg-final2/`): both issues
  resolved, 34 tests passed, no new issues, "ready to bind". Fable had already judged it ready.
  The owner gave the go for the GPU, and the run starts from the next commit, which is binding.

## D062 — Roadmap v3 adopted; 03a not scheduled; the publishing plan

**The owner's roadmap v3 replaces v2.2** (`ROADMAP.md`). It has two tracks: E (engineering, which
drives the schedule) and B (biology, which runs independently). Its thread is memory, as a
hypothesis. The immediate sequence is deliberately small.

**As v3 asks, v2.2's additions are merged** into a "Carried over from v2.2" section:
- the owner's question;
- the plasticity design (D045);
- the untested task-specificity control;
- the old meaning of "04";
- later ideas from the 03a draft.

**Four factual corrections on installation,** each checked against the records:
- **"5 to 7 times more strongly … than any shuffled graph":** it is 5-7 times the typical graph,
  above every one of the 640, and about 1.5 times the largest (03 RESULTS, supplement).
- **"into every champion":** 02b's evidence is group means, "the champions of every group".
- **03r** has fresh genomes for N2 too, and P1 and P3 as secondaries. The timing is stated plainly:
  neither 03's nor 03r's pre-registration was pushed before its run started. 03r's is public
  before its results, not before its start. The new standing rule applies from now on.
- **Credits:**
  - this session's model is Claude Opus 5.5;
  - Astra 6's and Fable 5.1's stage-by-stage reviews of 02, 02b, 03 and 03r are credited, as the
    owner's rule on AI contributions requires.

**03a is not scheduled** (the owner's plan, item 5). Its task and budget are revisited after 03r
at measured throughput. The draft's header says so.

**The publishing plan** (the owner, 2026-09-27):
- every push is shown first, and nothing merges into main without a go;
- the `roadmap` branch is pushed as a separate branch;
- D050 goes on main as a Corrections entry;
- 02b is reconciled with 02's registered result before it reaches main;
- 03 and 03r go to main together;
- the hygiene tests and the identity check run before every push.

## D063 — Pre-push review of the two pushes; the publication plan amended

Before either push, the owner asked for review. Astra 6 (xhigh) and Fable 5.1 reviewed both pushes
(`docs/reviews/20260927-160621-pushes/`, `docs/reviews/20260927-160623-pushes/`), and both answered "push after fixes" for each. Every
finding was checked before it was adopted.

**The publication plan, amended.** D059 said the full replication comes "before anything from 03
is published". Pushing the `roadmap` branch now makes 03's first-run results publicly readable on
that branch while 03r runs. The owner chose this knowingly, to get a public timestamp for 03r's
pre-registration. They were told the consequence in the push description, and it takes effect
with their go for push 1.
- 03 and 03r reach main together, reported by the pre-registered rule whatever the outcome.
- The README sentence bound in 03r §10 ("a full replication was run before publishing") will be
  written as: a full replication was run before 03 was merged into main and presented as a
  result, and 03's first-run results were public on the `roadmap` branch from the push date
  while 03r ran.

**The timing claim, narrowed (both):**
- GitHub's receipt time shows public disclosure, not registration before the run.
- `experiments/03r-replication/DISCLOSURE.md` states the binding commit and when disclosure came.
  It also gives the state at disclosure (528 of 773 graphs, N2 not measured) and what had been
  inspected: operational information only. No signal value from the formal run has been
  inspected since binding; the preflight's P4, seen before binding, is disclosed (Astra's
  confirmation pass).
- The same caveat is added to 03's RESULTS.md and to the roadmap.

**02b reconciled before this push (Astra), the owner's item 3:**
- "Steer by which side the food is on" becomes a replay association with the turn command. A
  table states the task, the measure and the output against 02's registered primary.
- 02b does not revise 02's primary reading, and says so.

**Also fixed:**
- **03's conclusion** is at the ensemble-comparison level: "unusually high … relative to all five";
  one SH-route graph is above N2.
- **Roadmap:**
  - the read-out's sign;
  - where the wrong reasoning was;
  - the 96 *targets*, which was Claude's error in its status report, copied into v3;
  - the avoid-food example, which 03's design rejected;
  - "proves", narrowed.
- **A banner on the branch README.**

**Push 2 (main) fixed:**
- **The Corrections entry** no longer repeats D050's withdrawn prediction: D051, no predicted
  direction.
- **The symmetry argument** is qualified: it holds for a fully equivariant network, and symmetric
  wiring with independent random parameters is not one.
- **The dates:** found 2026-09-25, published 2026-09-27.
- **Who made the error and who found it:** Fable 5.1's review originated the reasoning, Claude
  adopted it, and Astra 6 found it.
- **The docstring** is corrected on main, with the same text on both branches.
- **Pointers** beside the pre-registration passage and D041, with their text unchanged.
- **The review trail's episode 9** notes that its rationale was itself wrong.

**Noted for the owner, not changed:**
- **Archived reviews contain the local path `D:/Claude/random/wormWars`.** 02's reviews on main
  already do, and it names no user.
- **02b names four connections and gives degree percentiles and per-neuron interface-edge
  counts.** These are not reconstructable graph data. The owner decides whether "in any form"
  covers them.
- **`report.json` keeps `NaN`,** and says so.

**Operational:** HEAD is past `7c146fc`, so a resumed 03r run would be refused unless run from a
checkout of `7c146fc`.
- **Pushed on the owner's "go both" (2026-09-27):**
  - `roadmap` was pushed as a new branch at `ff17f00`, 17:28:15 +02:00. At that moment 565 of 773
    03r graphs were measured, and N2 was not;
  - then `main` was fast-forwarded from `5706c7e` to `76c613a`, publishing the 02 correction.

## D064 — T0: three island-path bugs, each confirmed by a failing test, then fixed

Roadmap v3's T0 says three island-path bugs are "suspected from reading the code", but it keeps no
record of which. Claude audited `wormwars/evo/evolve.py` and found three. Each was confirmed by a
failing test (`tests/test_evo_islands.py`) before its fix:
1. **Islands mixed after the first generation.** Membership is interleaved (strain i belongs to
   island i mod k). `_breed_islands` wrote each island's children back in contiguous blocks, but
   `island_of` stayed interleaved. From the second generation, every "island" held members of all
   islands. Children now return to their own island's slots.
   - The old test `test_islands_breed_independently` checked slots 0-3, the blocked layout. It
     encoded the bug and is corrected.
2. **Migrants were culled.** `_migrate` copied the best genomes over the worst but did not update
   `fit`. So migrants entered breeding with the fitness of the strains they replaced, and
   truncation removed them. `_migrate` now returns the new fitness, and migration happens after
   the generation is logged, so the log describes the evaluated population.
3. **Migrants lost their Dale sign vector.** `dale_sign` is per strain, but migration kept the
   destination's, so a migrant arrived as a different brain. It is now copied. This only matters
   with `brain.dale` on.

**Scope:**
- **No published result is affected.** All 20 recorded run configs have `islands: 1`, and the
  one-island path is unchanged.
  - *Corrected in D065:* the evidence is Astra's parent-versus-current run of a single-island
    evolution, bit-identical in scores, champions, snapshots and Dale signs. The `breed`
    comparison test is a tautology for one island.
- An end-to-end island run with migration and Dale signs is tested.
- **Reviews:** these fixes will be reviewed with the rest of T0 by Astra and Fable.

## D065 — T0 plan v2 after Astra's and Fable's review; the island fixes accepted

Both reviewed the island fixes (D064) and the T0 plan v1 (`docs/reviews/*-T0/`).
- **The island fixes: accepted by both.** Astra confirmed each regression test fails on the
  parent. It also ran the parent and current code on one island: bit-identical in scores,
  champions, snapshots and Dale signs. The three bugs plausibly match the roadmap's unnamed
  three, but nothing establishes that they are the same.
- **D064's wording is corrected** (Astra):
  - the stale Dale vector corrupts later mutation and clamping, not the migrant's immediate
    forward pass;
  - stale fitness culls a migrant when truncation excludes its slot, not invariably.

**T0 plan: "revise" from both, with largely the same must-fix points.** All are adopted in v2
(`docs/foundations/T0.md`), after checking them in the code:
- **World simulation is counted in `World`, not in `_play`.** Twelve construction sites were
  confirmed.
- **Neural updates count the batch axis:** S × B × effective substeps.
- **Experiment-level `compute.json`.**
- **Replay is split into three claims:** a round trip, re-simulation in the same mode, and
  historical replay on the recorded device. Published runs were scored on CUDA.
- **The CUDA tolerance is declared per comparison:** statistic, genomes, worlds, repeats and
  hardware.
- **The energy bound is declared now:** relative 1e-5 per world at every tick. That is confirmed
  as the documented bound in `tests/test_world.py`.

**Two real defects the reviewers found:**
- **Jitter noise follows batch position,** not world identity (Astra reproduced it: chunking moved a
  per-world score by 0.0053; the generator was checked in `world.py`). It breaks pairing across
  chunks. 02's jitter estimates are unaffected in expectation. The fix keys noise by world, tick
  and individual; future jitter results will not be bit-comparable with 02's.
- **The saved population's `fitness` holds per-generation bests** beside per-strain genomes (both
  reviewers; latent, since nothing reads it).

**Also adopted:**
- the champion re-evaluation is counted and paired, by genome hash;
- `Genome.cat` and `assign`, with a scan test;
- the load-time hash check;
- island configuration validation;
- stronger island tests;
- a single-island regression against a stored log, after 03r.

**Agreement:** both reviewers accepted the island fixes and agreed on what v2 had to change.
Every must-fix item is adopted. v2 itself has not yet been confirmed by them: it goes to both with
the first T0 code, and T0 is only treated as agreed after that confirmation.

## D066 — T0 item 1: complete inheritance and genome-score pairing

Following T0 plan v2 (D065). Each defect was confirmed by a failing test in
`tests/test_t0_pairing.py` before it was fixed.
- **Complete inheritance.**
  - `Genome.PARAMS` names every per-strain tensor, and a test checks it against the dataclass.
  - `select`, `clone`, and the new `cat`, `assign` and `with_params` iterate over it.
  - Every hand-built `Genome(...)` in the library moved to them: `evolve`, `coevolve`, `deletion`
    and the exp02 probes. A scan test forbids new ones outside `brain.py` and the loader.
  - **Real defect:** coevolution's opponent batch and frozen suite dropped `dale_sign`. That
    matters only with Dale on; every recorded config has `dale: false`.
- **Tested, with Dale on and off:** every parameter survives `select`, `clone`, `cat`, `assign`,
  `breed`, `_breed_islands`, `_migrate`, save and load. No output aliases its input.
- **The champion is the logged best of the final generation,** reusing that generation's
  evaluation. The old code re-evaluated the population on the same worlds. That was uncounted,
  and under default CUDA it could pick a different strain than the log named. On CPU the two are
  identical, and the test passes.
  - *Corrected in D067:* this change is by construction. Its first test passed before and after,
    so "confirmed by a failing test" did not apply to it. D067 adds a test that does fail on the
    old code.
- **The saved population's `fitness` is per strain,** index-aligned with the genomes. The
  per-generation bests move to `best_per_generation`. Nothing read the old field.
- **Jitter noise follows world identity.** It is a 32-bit counter hash of the run seed, stream,
  world id, tick and sample point, the same for every strain that plays the same world (common
  random numbers).
  - Astra's reproduction now passes: the scores are identical across chunkings and strain
    orders.
  - **Consequence:** jitter draws differ from those used in experiment 02. *Wording corrected in
    D067:* the batching defect does not establish bias in 02's jitter means, and the intended
    expectation is unchanged. Rerunning with the new generator produces different draws, so the
    realised estimates and intervals are not reproduced.
- **Integrity on load:** the stored genome hash (one genome) or nicknames (a population) are
  checked, and a tampered file is refused.
  - The hash covers Dale signs when present. No recorded genome has them, so hashes and nicknames
    are unchanged, and every committed N2 genome passes.
- **Scores pair exactly on CPU** (the deterministic mode) under strain permutation and any chunking,
  over full [strain, world] arrays.
- **Not touched:** `scripts/exp03.py` builds one genome by hand (gaps off). It stays unchanged until
  03r's report is done, because 03r runs from it.

## D067 — T0 item 1, confirmation pass

Both reviewed plan v2 and item 1 (`docs/reviews/*-T0b/`):
- **Fable:** "T0 plan v2: confirmed" (with three amendments) and "item 1: accept" (should-fix
  items owed before the gate).
- **Astra:** "not yet" on both, with reproduced defects.

That is not consensus, so every point was addressed. Each code point got a test that failed first
(`tests/test_t0_pairing_confirm.py`):
- **`with_params` aliased supplied tensors** (Astra reproduced it). It now copies every parameter.
- **`assign`** now checks the strain count and Dale parity, as `cat` does (both).
- **Population files were checked only by nickname:** 3 969 possible values. Astra built a
  tampered population that the loader accepted. New files store the full `genome_sha256s`, and
  nicknames remain a labelled legacy fallback. All 145 committed genome files pass: Astra checked
  them, and a test checks every single-genome file of every graph from its stored arrays.
- **The champion test could not detect the old bug** (Astra). A rigged evaluator now reverses the
  ranking on any later population evaluation. The test fails when the old re-evaluation is
  restored, which was checked by running it that way. `GenerationLog` gains `best_sha256`.
  - Fable asked for a one-time check: the 153 published champions that have a log match their
    log's final best *by nickname* (about 12 bits; old logs have no full hashes). That is no
    detected mismatch, not proof (corrected after the re-check).
- **Tests added:** the full saved fitness vector, holdout-to-genome pairing, snapshot pairing, and
  mutation never changing Dale signs (both).
- **Jitter keys are explicit coordinates:** (swarm, wey, sample point), not a padded flat index. A
  batch neighbour with more weys changed another match's noise (Astra reproduced it). Only
  multi-swarm layouts were affected, not 02's.
- **The hash is pinned** against an independent lowbias32 reference at edge values, and the
  uniforms and the jitter radius are tested (Fable). Astra's check of 7.68 million draws found
  means of about 0.49995 and correlations below 0.00051.
- **Minor:**
  - `flat()` iterates `PARAMS`;
  - `evolve` refuses zero generations.

**Plan v2.1** (`docs/foundations/T0.md`):
- historical replay qualified: exact only for deterministic originals, on their device and code
  version; bundles do not record the deterministic setting (Astra);
- 200-tick episodes, plus a labelled 600-tick stress test (Astra);
- accounting must be pure measurement (Fable);
- migrants capped at half the smallest island (Fable);
- champion pairing by full hash (Fable).

**Recorded, not changed:**
- **Regenerating 02's jitter artefacts.** `probe_validation.json`, the `history_probe` block of
  `diagnostics.json` and the champions' jitter scores can no longer be regenerated by current
  code. They remain reproducible from 02's commits: evolution at `225e8f8`, probes and report at
  `971bbb3` (Fable).
- **`gpu_seconds`** no longer includes a final re-evaluation. Keep that in mind when comparing old
  and new timings (Fable).
- **Variable-headcount coevolution** has a non-jitter chunking discrepancy. It already existed
  before item 1 (Astra checked), and is left for the coevolution work.
- **Hand-built genomes outside the library** are known exceptions to the scan test:
  `experiments/02b-champion-analysis/analyse.py`, `scripts/bench_brain.py` and
  `scripts/exp03.py`, which stays unchanged while 03r runs. All three keep `dale_sign`.
- **The 03r safety net:** a worktree at the binding commit (`../wormWars-03r-binding`) is ready for
  a resume if the run crashes (Fable).

**Re-check, and consensus reached** (`docs/reviews/*-T0c/`): Astra and Fable both answered
"T0 plan v2.1: confirmed" and "item 1: accept". Astra ran 49 focused CPU tests and saw the rigged
champion test fail with the old re-evaluation restored. So T0 item 1 is agreed by all three
(Claude, Astra and Fable), and under the owner's delegation the owner is informed. Also done:
- **Wording:** the 153-champion check is nickname-level only (both). The plan's "independent
  noise" is replaced by D066's corrected wording (Astra).
- **Jitter draws changed twice:** at f6af625 and at 59217da. Jitter outputs are comparable only
  from 59217da on (Fable). 03r uses no jitter.
- **Tests:**
  - `best_sha256` is anchored to an independent argmax of the captured fitness (Fable);
  - the 153-champion check is a test.

**Owed before the T0 gate:**
- an end-to-end jitter test with a (1, 3) match beside a (2, 2) match (Fable; the current test
  exercises `_keyed_uniform` directly);
- a readable error when `assign` rejects unsupported island settings inside `_migrate`, which
  comes with item 5's validation;
- jitter keys drop run-seed bits above 32, which is harmless for the seeds in use. It will be
  recorded in the jitter docstring.

## D068 — T0 item 2: compute accounting

Implemented per T0 plan v2.1, section 1 (`wormwars/accounting.py`, `tests/test_t0_accounting.py`).

**Counting:**
- **Where:** where the work happens. `World.__init__` counts worlds built, `World.tick` counts
  world-ticks (one per world in the batch per simulated tick), and `Brain.step` counts neural
  updates as S × B × substeps. So no construction site can be missed. Scripted controllers count
  zero.
- **Categories:** selection, holdout, snapshot, final, calibration, probe, measure, tuning and
  other. They are set by a context manager or the `counted` decorator. Nesting resolves to the
  innermost category, and a parent's time excludes its children's. An unknown category is
  refused.
- **Where categories are set:**
  - `evolve`: selection; holdout or snapshot, counted once when both apply.
  - Calibration: `raw_motor_magnitude`, `achieved_drive`, `calibrate_in_world`.
  - The exp02 probes: `input_response`, `behaviour`, `valence_check`, `channel_dependence`,
    `gen0_scores`, `integrator_rescore`.
  - exp03: `history` is a probe, and `coverage` is a measure.
- **Time:** synchronised wall-clock seconds per category, labelled as such; not GPU kernel time.

**Output:**
- `RunResult.compute` holds a run's counts by category. `evaluations` is unchanged (selection
  strain-worlds only).
- Experiment level: `scripts/exp02.py` writes `compute/<command>-<time>.json` per invocation, and
  `evolve_forage.py` writes `compute.json`.
- `scripts/exp03.py` gets its file after 03r's report, because 03r runs from it.

**Tests:**
- a rollout counted exactly;
- a small `evolve` counted by hand: selection, holdout and snapshot, with nothing in "other" or
  "final";
- pure measurement: bit-identical scores with the ledger on and off, and no random numbers
  consumed;
- nesting;
- the category restored after an exception;
- an unknown category refused;
- calibration, input response, history, coverage and behaviour each under their category;
- the JSON output.

The tests were written before the module, but not run red first: they would have failed on the
missing import.

## D069 — T0 item 2 after review: the output layer completed

Astra and Fable both answered "not yet" on D068 (`docs/reviews/*-T0-item2/`). Both found the core
sound: the hooks, the S × B × substeps arithmetic, early termination and nesting. Astra
independently verified the calibration and probe counts and early termination on CPU. Both found
the output layer incomplete. Every point was adopted after checking it in the code:
- **Untimed "other":** work outside any category was counted with 0 seconds, and no production code
  set "final" or "tuning".
  - "other" is now written as `seconds: null` and flagged `uncategorised`.
  - Every experiment script runs inside `accounting.attempt(..., default=...)`, so nothing falls
    outside a category.
  - **Explicit categories:** "final" for champion hold-out evaluations (exp02 `cmd_run`,
    `evolve_forage`, `experiment.py`); "tuning" for scripted `tune` and `tune_batched`;
    "selection" and "holdout" in coevolution; "probe" for geometry's `duel`, the exp03 stimulus
    bank and 02b.
  - Categories are set at call sites, not on shared helpers such as `score_policy`, because
    innermost-wins would otherwise bill tuning as measurement.
- **Lost on failure:** `attempt` writes a uniquely named file (UTC time plus a random suffix) when
  its block ends, **including on an exception**. The file holds status, error, pid, commit and
  devices. `aggregate` sums every attempt, failed ones included. exp02's and exp03's `report`
  commands write `compute.json`. exp02's per-run `records.jsonl` now carries each run's
  `compute`.
- **API fixes:**
  - `pop` restores the stack even if the CUDA sync raises;
  - `snapshot` includes the open segment's time, so `since` is right mid-category (Astra's
    0-5-10 case);
  - `since` keeps time-only changes;
  - sync runs on every visible device;
  - a `reset()` inside a category no longer breaks the next `pop`;
  - the `enabled` toggle no longer produces absolute-clock seconds.
- **Tests added** (`tests/test_t0_accounting_b.py`):
  - exact counts for calibration, the input-response probe and the history probe;
  - early termination (starving worlds);
  - the substeps override;
  - scripted brains counting ticks but zero neural updates;
  - exclusive nested time on a fake clock;
  - a snapshot inside a category;
  - a failing sync still restoring the category;
  - untimed "other" written as null and flagged;
  - a failed attempt still written, and aggregation;
  - geometry categorised.
- **Documented:**
  - "measure", a ninth category, added in D068 for coverage, fitness measurement and reference
    scoring, now in the schema;
  - the neural unit ignores network size;
  - category seconds do not sum to `gpu_seconds`;
  - `SparseBrain` and geometry's zero-tick worlds are known gaps.
- **exp03** (Astra's point, not deferred after all). The running 03r process has its code loaded,
  and any resume uses the binding worktree, so `scripts/exp03.py` now runs inside `attempt`. Its
  "gaps off" genome uses `with_params`, which is numerically identical. 03's `report.json`
  regenerates byte-identically.
- **Not verified:** CUDA bit-identity with the ledger on and off. That waits for the GPU.

## D070 — T0 item 2, re-check: script integration completed

Re-check of D069 (`docs/reviews/*-T0-item2b/`): Fable answered "item 2: accept" and Astra "not
yet". Every point was adopted after checking it:
- **Legacy scripts are routed by `--out`** (Astra). `evolve_forage`, `experiment`, `coevolve`,
  `ablate` and `tactics` pooled attempts in `runs/compute/<script>` and wrote no aggregate. They
  now use `accounting.run_script`: attempts go to `<--out>/compute/`, and all of them are summed
  into `<--out>/compute.json`, beside the results.
- **`--help` is not a failure** (Astra reproduced `SystemExit: 0` recorded as failed). `--help`
  runs without accounting, and `SystemExit` with code 0 or None counts as completed.
- **The default category absorbs overhead** (Fable). The attempt file now records
  `default_category`, and the docstring says its seconds are overhead as much as work.
- **02b's attempt files were in a tracked folder** and could carry local paths into the public
  repo (Fable). `experiments/*/compute/` and `experiments/*/compute.json` are now ignored.
- **exp02's per-run compute** now covers the whole run, including drive and final evaluations
  (Fable).
- **Probe validation** (`cmd_validate_probes`, `_history_probe_validation`) is "probe", not the
  default "measure" (Fable).
- **Tests** (`tests/test_t0_accounting_c.py`):
  - an end-to-end coevolution run, categorised as selection and holdout, with nothing in
    "other". It is the first end-to-end coevolution test in the suite;
  - exp03's stimulus bank counted as a probe;
  - `run_script`'s routing and aggregation;
  - `--help` and exit 0;
  - boundary syncs.
  The geometry test is renamed: it did not test coevolution.
- **Recorded, not changed:**
  - viewers (`watch`, `showcase`) and benchmarks are not experiments, and write no compute file;
  - 02b's replays are categorised by its `attempt` default ("probe") but not tested;
  - a hard kill still loses the attempt file;
  - CUDA bit-identity with the ledger on and off is still unverified until the GPU is free.

## D071 — T0 item 2, second re-check

Second re-check (`docs/reviews/*-T0-item2c/`): Fable answered "item 2: accept" and Astra "not
yet". Addressed:
- **02b now writes its aggregate** after every stage, as `compute.json` beside its attempt files.
  Both are git-ignored.
- **The plan's test claim is amended to what is tested** (`T0.md` section 1). Tested: evolve
  categories, calibration, the input-response, history and behaviour probes, exp03 coverage and
  stimulus bank, coevolution and geometry. Counted by construction but untested: 02b's replays,
  the viewers and the benchmarks, which are not experiments. The hooks make them count, but no
  test asserts it. Astra asked for this to be stated rather than implied.
- **`--out` abbreviations are refused** (Astra reproduced `--ou` sending results and accounting
  to different folders). The five legacy parsers use `allow_abbrev=False`, and a test checks it.
- **The aggregate names each attempt** by script, argv, stage, experiment, command and default
  category (Fable).
- **A test checks** that a non-zero `SystemExit` is recorded as failed (Fable).
- **Left as is:**
  - a usage error (argparse exit code 2) still records a failed attempt with zero work. That is
    truthful, and harmless;
  - exp02's and exp03's `compute.json` is written inside the `report` attempt, so it excludes the
    report's own seconds (Fable).

## D072 — T0 item 2, third re-check

Third re-check (`docs/reviews/*-T0-item2d/`): Fable answered "item 2: accept" and asked for
wording only, with no further round needed. Astra answered "not yet" on one blocker, and approved
the amended plan text.
- **02b's aggregate was skipped when a stage raised** (Astra reproduced it; Fable found it too).
  `accounting.recorded` wraps an attempt and writes the aggregate in `finally`. 02b and
  `run_script` use it, and a regression test covers success followed by failure.
- **Plan text** (`T0.md` section 1; Fable):
  - `SparseBrain` is named as the exception to "the same hooks";
  - the untested list adds the "final" category, four exp02 probes and two calibration
    functions;
  - the pilot and exploration scripts are named as not recorded at all, and future pilots run
    inside `attempt`;
  - the "twelve places" count is corrected.
- **"tuning" is now tested.**
- **Consensus:** Astra's final check (`docs/reviews/*-T0-item2e/`) verified the fix through 02b's
  real `__main__` block and answered "item 2: accept". Fable had accepted. So T0 item 2, compute
  accounting, is agreed by all three, and the owner is informed. It remains open on CUDA
  bit-identity with the ledger on and off, which is checked when the GPU is free.

## D073 — T0 items 3-5, CPU parts, and the jitter test owed from item 1

Per T0 plan v2.1 (`tests/test_t0_items345.py`). Tests were written first. Seven failed, for the
missing features; five passed on the existing code, as the plan expected. Those five cover CPU
re-simulation, finiteness of extreme genomes and of a published champion, a migrant surviving
breeding, and island isolation.

**Item 3 (CPU):**
- save, load and re-simulate reproduce every tensor and the full [strain, world] scores
  **exactly** on CPU;
- rolling out twice is also exact.

**Item 4:**
- **The energy ledger, per the declared bound.** `cfg.world.check_ledger_every_tick` (opt-in,
  because it costs a reduction per tick) tracks each world's error relative to its own starting
  energy, at every tick.
  - **The gate test:** N2, SH and RD, 8 worlds each, at 02's T0 and T1 settings. All stay below
    **1e-5**.
  - Every rollout now reports `ledger_rel_error`: the per-tick maximum when tracked, else the
    final residual.
- **NaN is no longer swallowed.** Python's `max(0.0, nan)` is 0.0, so a NaN residual was
  reported as 0. `_nanmax` propagates it, and a test checks.
- **Numbers:** extreme genomes (every bound saturated, both signs) and a published 01b N2 champion
  stay finite over a full episode, in brain states and energies.

**Item 5:**
- **Unsupported island settings are refused** before anything runs, with readable errors: an
  empty island, `migrate_every` below 1, or migrants above half the smallest island.
- **The per-island elite and truncation rule is documented** in `_breed_islands`.
- **Tests:**
  - a migrant survives breeding with every field, Dale included;
  - with migration off, every logged best over 3 generations is one of the generation-0 genomes
    (sigma 0).
- **Still waiting for the GPU:** the single-island regression against a stored published log.

**The owed jitter test:** end to end, through `_jittered` with real batch layouts, a (2, 2)
world's jitter offsets are identical alone and beside a (1, 3) world.
- **Found while writing it:** the (2, 2) world's wey *positions* differ between the two layouts.
  This is a pre-existing layout dependence in multi-headcount placement, not jitter. Astra noted
  a non-jitter chunking discrepancy in variable-headcount coevolution in D067, and this is
  probably its cause. It is recorded here, to be fixed with the coevolution work. It does not
  affect single-swarm experiments.

**Waiting for the GPU:**
- item 3's `replay_mode` exactness and the declared default-CUDA tolerance;
- historical replay of a published champion on CUDA;
- CUDA ledger on/off identity (item 2);
- item 5's single-island regression.

## D074 — T0 items 3-5 after review: two vacuous tests replaced, coverage completed

Both reviewers answered "not yet" on D073 (`docs/reviews/*-T0-345/`). Both found the
implementation sound: the ledger normalisation, per-tick maximum, NaN propagation, opt-in cost,
the island validation and the CPU round trip. **Two of my new tests could not fail,** and Astra
proved both by sabotage:
- **The jitter test compared zeros.** It never set `food_probe_radius`, which defaults to 0. It
  now uses radius 1, asserts that jitter moves points, and compares the keyed draws taken from the
  two real layouts.
  - Checked by sabotage: it fails with identity jitter and with the old padded flat-index keys.
- **The isolation test compared winners with the union of both islands' ancestors.** Now every
  slot of every generation must descend from its own island.
  - Checked by sabotage: it fails when per-island breeding is replaced by global breeding.

**Coverage the plan promised, now added** (`tests/test_t0_items345_b.py`):
- **Islands:**
  - every ring edge, including the wrap 2 → 0, and the untouched slots;
  - an uneven population (5 strains, 2 islands) running through migration;
  - log and snapshot pairing with islands and migration active.
- **Numbers:** brain states and energies are checked at **every tick**, and scores at the end.
  This covers N2, SH and RD, at T0 and T1, for random genomes pushed into the mutation bounds plus
  the mixed-sign corner.
- **Ledger, adversarial:**
  - an early peak survives a zero final residual;
  - an early NaN survives later finite ticks;
  - Inf is reported;
  - NaN propagates across chunks in either order;
  - each world is normalised by its own start;
  - a forced-death case: at 02's settings nothing starves in 200 ticks, so this case raises the
    drain, and weys die;
  - tracking changes no result.

**Real defects fixed:**
- **NaN was still swallowed** by the same `max(0.0, nan)` pattern in coevolution's `play`, exp02's
  run record and exp02's report (both; Astra reproduced the coevolution case). All three keep NaN
  now.
- **A non-finite fitness now stops `evolve`** (`FloatingPointError`); before, `np.argmax` could
  pick a NaN strain as the best (Fable).
- **Also refused:**
  - `islands < 1`;
  - negative migrants, with their own message;
  - an island of fewer than 2 strains, which would be a single frozen elite (Fable).

**Documentation:**
- `_breed_islands` notes that `breed` also caps the counts by island size;
- the jitter docstring notes that run-seed bits above 32 are dropped (owed since D067).

**D073 corrected:**
- **The layout defect is broader than stated** (both; Astra reproduced it). `_build_maps` draws a
  number of values set by the batch's padded wey count (`world.py`, around line 412) from the RNG
  that later draws food and hazards. So a neighbour's headcount changes the whole map: positions,
  headings, food and hazards. That, in turn, changes coevolution scores across chunkings (Astra
  reproduced this). The cause is confirmed, and it predates T0.
  - Fixed-headcount runs are unaffected, and no other caller passes `swarm_sizes`.
  - **Suggested fix** (Fable): size the draws by the world's own largest swarm, which keeps every
    uniform-headcount map exactly. It is deferred to the coevolution work.
- **The ledger cost** is several float64 conversions and reductions per tick, not one.
- **The review prompt numbered the plan's sections off by one:** items 3-5 are sections 4-6.

## D075 — T0 items 3-5, re-check: numerical coverage completed

Re-check of D074 (`docs/reviews/*-T0-345b/`):
- **Fable answered "items 3-5 CPU: accept"**, with small items and no further round needed.
- **Astra answered "not yet"** on numerical coverage. It independently confirmed the three
  sabotage results and the NaN propagation in rollout, coevolution, exp02's run record and
  `report.build`.

Fixed:
- **8 distinct worlds per genome** in the every-tick matrix (Astra). The earlier test repeated two
  world ids across strains.
- **The corners are in the every-tick matrix:** both uniform-sign extremes, and the mixed-sign
  corner with the bias sign mixed too, not only the weights (Fable). This covers N2, SH and RD at
  T0 and T1, with brain states and energies checked at every tick and scores at the end.
- **One published 01b champion per family** (N2, SH1, RD1), 8 worlds each, checked at every tick,
  with scores (Astra, Fable). The SH and RD graphs are rebuilt from their seeds, and the loader's
  edge-hash check confirms each rebuild.
- **The jitter test also compares `_jittered` itself,** on identical zero points, so no position
  rounding enters (Fable).
- **Coevolution's NaN handling is tested by behaviour** (a NaN ledger through `play`), not by
  searching the source (Fable).
- **The pairing test asserts its snapshot keys,** so it cannot pass with none (Fable).
- **`config.py`'s comment** now states the real cost of per-tick tracking.

**Full suite at this commit: 463 tests, all passing** (Fable noted that earlier entries never
stated the suite result).

**Recorded, not changed** (Fable):
- coevolution's `argmax` is not guarded against NaN; D074's guard covers single-swarm `evolve`
  only. It is left for the coevolution work;
- `coevolve.play` tests a stale `lo == 0` when attaching the recorder, which is pre-existing;
- the per-tick flag lives in `WorldConfig`, so it enters bundles, and older code would refuse such
  a bundle;
- item 3's CPU test is small (50 ticks, one genome, Dale off).

## D076 — T0 items 3-5, final check: champions at T0/T1, and a false claim in D075 corrected

Astra's final check (`docs/reviews/*-T0-345c/`) answered "not yet" on two points, both confirmed:
- **The champions ran at their own 01b settings** (600 ticks, stereo, no odour, 8 substeps), not
  at the declared T0 and T1 settings (200 ticks, odour, 32 substeps). The champion test now runs
  each of N2, SH1 and RD1 at both T0 and T1, with the task's brain configuration, over 8 worlds,
  checked at every tick: six cases, all finite.
- **D075's claim that "the loader's edge-hash check confirms each rebuild" was false.** 01b's
  champion files carry no `edge_hash` (checked). Astra showed that SH1 and RD1 also load against
  seed-2 graphs under the same labels. So nothing verifies that the rebuilt graphs are the ones
  01b used, beyond the documented construction (`make_graphs`, seed 1).
  - **A real check** is to replay each champion's stored `holdout_score` on its recorded device.
    That is item 3's historical replay on CUDA, after 03r. The test's docstring says so.
- **Consensus:** Astra's second final check (`docs/reviews/*-T0-345d/`) answered "items 3-5 CPU:
  accept". It ran all six champion cases on CPU and confirmed independently that the files lack
  `edge_hash`. Fable had accepted.
  - So T0's CPU work (items 1-5) is agreed by all three, and the owner is informed.
  - **Open until the GPU is free:** `replay_mode` exactness, the default-CUDA tolerance,
    historical replay (which also verifies the SH1 and RD1 rebuilds), CUDA ledger identity, and
    the single-island regression against a published log.

## D077 — E1 design v2 after Astra's and Fable's review

Both reviewed E1 design v1 (`docs/reviews/*-E1/`) and both answered "proceed to v2", with largely
the same must-change points. Nothing has been run. Key claims were checked in the code before
adoption:
- the odour blur is truncated at 3σ;
- the map builder scales patch radius and mass by headcount, so one wey shrinks a radius of 1.5
  to about 0.34;
- `_play` hard-codes `foraging_score`;
- K turns constantly, and M remembers one tick.

**v2** (`docs/E1/DESIGN.md`):
- **Task N:** energy is off (no drain, cost or eating; a non-depleting scent source), and the
  target bypasses headcount scaling.
- **The pilot picks σ, A and R,** measuring zero-signal coverage and clamp saturation.
- **Targets are a fixed sequence per world,** by (seed, world, index), so they pair across strains;
  they keep at least 3 cells from walls.
- **The score** gets plumbing into rollouts and tuning.
- **An event table.**
- **Replay** claims exactness only for counts and events under deterministic replay.
- **Controls** are described correctly and all tuned alike: tuned blind baselines, including a
  wall-follower with the declared collision inputs, K, an oracle ceiling, and k ≤ 32 reporting.
- **The pilot-first gate:**
  - absolute reliability (at least 2 arrivals);
  - paired count differences against every baseline;
  - **cue use**: scent displaced while the target stays, so the count must fall;
  - failure-aware latency and path efficiency.
- **04a** gets its own run count and pass rule, a generation-0 baseline, and optional bounded
  shaping.
- **E3:** the goal-cue input is committed to the food neurons in every module copy (Astra). E1's
  limits for E3 are stated: no trails, junctions or occlusion.
- **Bridge 1 is deferred** (both).

**Consensus:** both answered "proceed to v2", and v2 adopts every must-change point. It goes to both
for confirmation before any implementation, after 03r's report.

## D078 — E1 design v2: consensus, and v2.1's text edits

Both confirmed v2 (`docs/reviews/*-E1b/`): Fable and Astra each answered "E1 v2: ready to
implement". Each listed small text edits due before the pilot, and neither wanted another design
round; the freeze document is what deserves the next review. v2.1 makes the edits:
- **The target is sensing-only**, added in `_sensed_food` and never in `fields[FOOD]` (both;
  `total_energy` sums FOOD, confirmed). The ledger test covers relocations.
- **σ is chosen over actual leg starts** with a usable-signal floor. The blur's per-axis, square
  support is measured from the sampled field. D is a pilot parameter, with D > 2R and wall
  clearance checked against R.
- **S-const** is `StereoKinesis` with slow = fast and a grid turn that includes 0.
- **The oracle** stays outside scripted observations.
- **The wall-follower's thresholds** sit above the own-body collision readings.
- **The mirrored probe is described correctly:** a decoy at the reflected target, so counts can
  fall below the blind level. The `constant` probe is reported as each controller's blind level.
- **The freeze is a committed file** whose hash the gate run records. It fixes the configuration,
  navigator, baselines, thresholds, interval method, intervention, sample sizes and execution mode.
- **Shaping** is capped below one arrival per episode.

**E1 is agreed by all three,** and the owner is informed. Implementation follows roadmap v3's
order: T0's GPU items and T1 first.

## D079 — T0's GPU checks: the script, and what its CPU smoke run already shows

`scripts/t0_gpu_checks.py` implements T0 plan v2.1's GPU checks, as declared before measuring:
- `replay_mode` exactness, over repeats and chunkings;
- the default-CUDA tolerance: declared 1e-4 per world; 3 repeats; 02-T0 and 02-T1 at 200 ticks,
  plus a 600-tick stress test;
- CUDA identity with ledger tracking on and off, and with accounting on and off;
- historical replay of 01b champions against their stored `holdout_score`;
- the single-island regression against 01b's stored log.

It writes `docs/foundations/T0_gpu.json` and runs when 03r frees the GPU.

**The CPU smoke run** (`--quick`; `runs/t0-gpu-quick-cpu.json`, not committed) already shows:
- **The rebuilt SH1 and RD1 graphs are 01b's,** answering D076's open question on the evidence.
  Each 01b champion replays close to its stored score: N2 1.5582 against 1.5572, SH1 1.7045
  against 1.7031, RD1 1.6823 against 1.6813. The gaps of about 0.001 are CPU against 01b's CUDA.
  The SH1 champion on the *wrong* graph (SH2) scores 0.110 against 1.703. The GPU run gives the
  same-device comparison.
- **On CPU:** repeats and chunkings are identical, and so are ledger-tracking and accounting
  on/off.
- **The single-island regression cannot be judged on CPU,** because `torch.Generator` draws
  different random numbers on CPU and CUDA, so generation 0 differs from 01b's. It is judged on
  the GPU run.

## D080 — 03r's results: replicated under both rules; P3 reversed (secondary, unpredicted)

The run finished at `7c146fc`: 773 graphs, 23.95 GPU-hours of the 32-hour cap, N2 last. Every
ensemble was complete, with no calibration failure. The registered report was produced by the
binding commit's code (worktree at `7c146fc`) and again at HEAD, and the two are identical.

**Primary:**
- **P4 alone:** maximum p 0.0155, distinctive relative to every ensemble. N2 = 0.924. Graphs at
  or above N2: 0, 0 of 256, 1, 0 and 0.
- **03's full rule for P4:** Holm-adjusted 0.0465, distinctive.
- **§10's fixed wording applies:** "Replicated under the registered single-signal test and under
  03's original three-signal rule."

**Secondary** (03's rule):
- **P1:** "not distinctive", recurring.
- **P3:** **"reversed against every ensemble"**, with an opposite-direction Holm-adjusted p of
  0.0465. N2 = −0.024 against ensemble means of about 0. N2's random brains score slightly worse
  with the real food signal than with a constant one.
  - The label is new: 03 was inconclusive, with N2 −0.010 on the low side.
  - It is reported as found, as an unpredicted secondary controlled only within 03's
    opposite-direction family (up to 10% error across both directions). No causal claim is
    made; one would need its own pre-registered test.

**Descriptive:** N2's P4 magnitudes again exceed every ensemble graph's. One fresh weight
permutation (N2perm6) keeps P4 at N2's level; two others fall to the upper-middle of the
ensembles.

`experiments/03r-replication/RESULTS.md` is written with §10's fixed wording and the D063
deviation. 03's RESULTS.md gets a pointer. Both go to Astra and Fable for review, then to the
owner for the go to main, together.

## D081 — T0's GPU checks, and the 03r results review

**T0 GPU checks** (`scripts/t0_gpu_checks.py`, `docs/foundations/T0_gpu.json`, RTX 5080), as
declared in T0 plan v2.1:
- **Historical replay: exact.** All 9 01b champions (N2, SH1 and RD1, three runs each) reproduce
  their stored `holdout_score` to 6 decimals, in default and replay mode. This confirms on the same
  device that the SH1 and RD1 graphs rebuilt from their seeds are 01b's (D076, D079). The wrong
  graph (SH2) gives 0.110 against 1.703.
- **Single-island regression: exact.** Generations 0-2 of 01b's N2-run00, rerun from its bundle
  configuration and seed at current code, reproduce the logged best, mean and best nickname. So
  T0's changes left the published evolution path unchanged.
- **Identity:** scores are the same with the per-tick ledger on and off, and with accounting on and
  off.
- **`replay_mode`:** repeats are identical.
- **The declared default-CUDA tolerance (1e-4 per world) is exceeded, and the reason is found.**
  - A targeted follow-up shows that repeats at the same chunking are **identical**, even in default
    mode, and that replay and default modes agree at the same chunking.
  - Chunks of 64, 256, 1 024 and 4 096 worlds agree exactly.
  - Only a chunk holding **a single strain** differs: 3 of 512 worlds, by up to 0.027 at 200 ticks,
    and up to 0.15 in the 600-tick stress test.
  - The likely cause is a different GPU kernel path for a batch of one, whose rounding the chaotic
    dynamics amplify in a few worlds.
  - **Per the plan, this is a finding, not a widened bound.** The claim becomes: *on CUDA, results
    are exact for the same batch composition; a single-strain evaluation can differ from the same
    genome inside a population batch.* `docs/REPRODUCIBILITY.md` is corrected: its "chunking is a
    memory strategy, not an approximation" holds on CPU, and on CUDA only for chunks of more than
    one strain.
  - **Consequence:** analyses should compare genomes evaluated in the same batch composition. A
    possible fix, padding single-strain evaluations, is a T1 option.

**03r results review** (`docs/reviews/*-03r-results/`): both reviewers answered "not yet", both on
presentation. The verdicts are confirmed: Astra recomputed them, and the report hashes match.
Revised (bb2f245 and this commit):
- **P3's noise caveat** (Fable, confirmed): N2's P3 SE is 0.012, against an ensemble median of
  0.0065, with only 3 of 768 as large. So the rank p is too small for P3. A noise-aware check gives
  about 0.08 after Holm *(note 2026-09-28: 0.072 after the rounding fix in D082; RESULTS.md and the READMEs give 0.072)*. Also added: the fragility (one more SH-recip graph gives 0.070), the
  approximate-test and weights-plus-wiring caveats, and the variants' P3 values.
- **Both runs under both rules,** with the one-graph margin stated.
- **The validity claim is corrected:** N2-rev's descriptive P1 is invalid.
- **The discrete-p ordinal claim** is replaced by the concrete fragility.
- **The provenance claim is scoped** to the run's start, with the **bit-for-bit re-measurement** of
  N2 and SH-route-1020255 from the binding worktree (identical) and a dated DISCLOSURE addendum.
- **Stale status lines** in 03's RESULTS, the roadmap and the branch banner are fixed.
- **The README's lead section for main** carries §10's outcome sentence, the probe caveat, D063's
  amended sentence and D059's contributions, including that P4 alone was chosen after 03 on
  Fable's argument.
- **Rounding** corrected.

## D082 — After the combined review: T0 checks rerun clean, the CUDA contract amended, 03r text fixed

Both reviewers answered "not yet" on both parts (`docs/reviews/*-03r-T0-combo/`). Every point was
checked and adopted.

**T0:**
- **Provenance** is now recorded at the start, and the real run refuses a dirty tree. The earlier
  run's provenance was unusable: the commit was read at the end, and a quick run executed an
  uncommitted fix. The rerun is `bcee5a8`, clean (`docs/foundations/T0_gpu.json`).
- **The declared cohort:** the tolerance rows now use **02's** N2 champions, 8 per cell, at their
  own configuration with 32 substeps (Astra). The earlier "champions" rows used 01b's at 8
  substeps and were mislabelled.
- **Repeats and chunking are separated,** with 1, 2, 3, 4, 16 and 32 strains per chunk and a
  remainder chunk of one, each with its count of worlds over 1e-4.
- **Results:**
  - repeats are identical everywhere, in both modes;
  - chunkings of two or more strains agree exactly with each other;
  - replay and default agree at the same chunking;
  - single-strain chunks, including a remainder of one, differ in a few worlds at 200 ticks (up
    to 0.027) and in many at 600 ticks (98 of 128 champion worlds, up to 0.055).
  - **The recorded cause:** a direct `torch.bmm` test shows a single strain differing by 4-6e-5
    from the same strain in a batch, while batches of two or more are identical.
- **The failure of the original contracts, §2 (chunk invariance) and §4 (replay-mode exactness),
  is recorded, and the contract is amended** (T0.md, dated). The contract is now exact at the same
  batch composition, with single-strain chunks as their own composition. No bound is widened.
- **No behaviour is changed in T0:** padding would break the exact replays of 01b's single-strain
  evaluations. Padding, or a guard, is a T1 decision.
- **The implication for existing runs:** a rollout whose last chunk happens to hold one strain gives
  that strain deterministic but slightly different scores. It is deterministic, so no result is
  unreproducible. 03 and 03r evaluate each graph's genomes in one chunk.
- **The CUDA ledger bound:** below 1e-5, with everything finite, for N2, SH and RD at 02-T0 and
  02-T1.
- **Historical replay: 9 of 9 exactly equal,** with the deviation stated. It runs at current code,
  and 01b's bundle records `git_dirty: true`.
- **The single-island regression** has a pass field: pass.
- **`REPRODUCIBILITY.md`'s wording is narrowed:** "in the tested configurations", "consistent
  with a different kernel path"; default-mode nondeterminism was not observed but is not
  guaranteed absent.

**03r:**
- **The README lead** now says "unusually high relative to all five null ensembles … reproduced
  it", with §10's probe caveat verbatim.
- **P3:** the registered label comes first, then the caveat, with the exploratory check labelled as
  such.
- **Both runs under both rules, and P4 alone** as the registered primary for 03r only.
- **The fragile ensemble is named,** and the ensemble descriptions corrected.
- **RESULTS:**
  - the §9 deviation is stated: the running process never reloaded, which the bit-for-bit
    re-measurement supports;
  - "did not, as far as checked";
  - the noise wording (unequal noise undermines exchangeability), with the exploratory
    calculation stated;
  - the committed re-measurement record and script, with provenance.
- **Stale roadmap status is fixed.**

## D083 — 03r ready to publish (both); T0 closed

Re-check of D082 (`docs/reviews/*-03r-T0-re/`):
- **03r:** Astra and Fable both answered "03r results: ready to publish".
- **T0:** Astra answered "T0: close". Fable answered "not yet" on two must-fix items, and said
  neither needed another review once done. Both are now done:
  - **`REPRODUCIBILITY.md` cited 0.15,** a number from the superseded run with 01b's champions at 8
    substeps. It now gives the clean run's numbers: 49 of 512 and 98 of 128 worlds over 1e-4 at
    600 ticks, maxima 0.073 and 0.055; at 200 ticks 2-8 worlds, maximum 0.027. It says "exceeded
    1e-4" rather than "differed".
  - **The test suite's result at the closing commit** is recorded below.

**Also fixed, from both reviewers' non-blocking points:**
- **The re-measurement comparator was not strict** (both). `nanmax` hid finite-to-NaN changes, and
  `zip` hid missing entries. It now requires the same keys and lengths, exact values and NaN in
  the same positions, and it writes its own provenance.
  - **Rerun on the GPU with the binding code** (`7c146fc`, clean): N2 and SH-route-1020255 are still
    identical (`experiments/03r-replication/remeasure.json`).
  - The previously committed file had been annotated by hand. It is replaced by the script's own
    output.
- **`accounting.attempt` recorded the commit at the end,** without a dirty flag (Fable). It now
  records `git_commit` and `code_dirty` at the start, and the commit at the end separately. A test
  failed first.
- **Wording:**
  - the replay-mode guarantee is scoped to the same batch composition, and says that only chunking
    4 096 was repeat-tested (Astra);
  - T0.md's `bmm` numbers: 4.2e-5 at 64 rows, 6.5e-5 at 320, none at 16;
  - the disclosure's "none reached the run" is hedged, and it points to the committed record;
  - the roadmap's stale lines;
  - the README's details line.
- **D082's "everything finite" on CUDA** covers final scores and swarm energies. Brain states at
  every tick are covered by the accepted CPU tests (D075).

**Consensus:**
- **03r is ready to publish,** by both. Main still needs the owner's explicit go.
- **T0 is closed:** Astra said "close", and Fable's two conditions are met. So T1 (throughput,
  profile first) is next. Its equivalence tolerance must be declared with D082's batch-composition
  finding in hand, and padding or a guard for single-strain chunks is a T1 decision (Fable).

**Test suite at the closing commit** (`205d929`): 467 tests, all passing.

## D084 — The "153 published champions" was 135; a test depended on local files

Running the full suite in a fresh worktree of the main candidate failed one test:
`test_published_champions_match_their_logs_final_best_by_nickname` expected 153 and found 135.
- **The test globbed `runs/` on disk.** This machine has 18 local-only, superseded champion files
  (`runs/m5`, `runs/m4-pilot`) besides the **135 committed** ones. A fresh clone has 135.
- **Corrected:** D067, D075's review trail and T0.md said "153 published champions". The accurate
  statement is 135 committed champions with logs, plus 18 local-only ones: all 153 match by
  nickname.
- **The test** now reads committed files only (`git ls-files`) and expects 135.
- **Lesson:** the suite is now also run in a fresh worktree before a push to main. That is how
  this was caught.

## D085 — 03 and 03r published on main (the owner's go)

On the owner's "Go main" (2026-09-28), `main` was fast-forwarded from `76c613a` to `e856b7d` at
07:33:30 +02:00. That is the whole `roadmap` branch at `86994c0` (78 commits), plus one commit
removing the working-branch banner.

**Now on main:**
- 03 and 03r together, reported by 03r's pre-registered rule, with §10's README text (D063, D059);
- 02b, reconciled with 02;
- roadmap v3;
- the 03a draft, not scheduled;
- T0's code and checks;
- the E1 design;
- D038-D084, and every review.

**Checks before the push:**
- the full suite in a fresh worktree of the candidate;
- the identity check: all 78 commits use the noreply address, with no session trailers or personal
  email;
- the hygiene tests;
- no connectome files.

`roadmap` continues as the working branch from `main`, with a short banner.

## D086 — T1 plan: reviewed, approved with changes, v2 adopts them

T1's plan v1 (`98dc4f7`) was reviewed by Astra 6 and Fable 5.1 (`docs/reviews/20260928-074601-T1/`).
Both answered **"T1 plan: approve with changes"**, and the changes largely overlap. Plan v2
(`docs/foundations/T1.md`) adopts all of them.

**Agreed by both, as proposed:**
- keep dense FP32 and do not port frameworks;
- pad single-strain batches in `Brain.step`, on by default for new work;
- defer batching several runs until a budget needs it;
- adopt no numerics-changing engine in T1.

**Changed:**
- **The bottleneck reading (Fable).** The brain step is already GPU-bound; the gain from larger
  batches comes from the world's fixed per-tick cost, which v1 did not profile. "The CPU is the
  limit" is withdrawn (Astra: CPU time in a profiler is not a cause). T1.1 now profiles the world,
  its two host syncs per tick, a whole short run, single-strain shapes, `replay_mode`'s cost and a
  Task N proxy (one wey, 300 ticks), with 5 repeats.
- **Wording:**
  - "the framework is not the bottleneck" became "these measurements do not justify a port";
  - "Windows time-slices processes" became "the cause is not established";
  - the cuSPARSE finding is scoped to the tested implementation, and rechecked under
    `replay_mode(warn=False)`.
- **03a's gap.** No exact lever found closes it: about ×2.5 is needed, the best is ×1.36.
- **Class E** is now:
  - old against new on each device;
  - against a reference saved from the pre-change commit;
  - bit-equality recorded;
  - rows per strain 16 to 1 280, and 1 to 256 strains per chunk;
  - the replay leg in a fresh process.
- **Class N's numbers are withdrawn** (both). The category stays, and needs its own plan.
- **The padding switch is legacy-off where published results are read** (both):
  - a missing field means off in `load_genome`, `Config.from_bundle` and `brain_config_for`;
  - 02's `task_config` pins it off.
  Without this, published champions would have silently loaded with padding on.
- **Padding's own specification:**
  - its work is counted, with a separate `neural_padding` field;
  - a CPU test spies the batch size reaching `bmm`;
  - the environment-dependent negative control is a sensitivity check, not a suite assertion;
  - 02's single-strain hold-outs are replayed with it off, and the change with it on is
    reported.
- **T1.3's trigger:**
  - it needs a fixed-scope experiment that misses its cap, after shrinking first;
  - the vacuous "twice as long" branch is removed;
  - its scope now includes per-run world ids, accounting and early termination.
- **The gate is staged** (both). "Scripted, so it fits any budget" was wrong (Astra). T1's
  engineering closes on T1.1 and T1.2. The budget gate moves to a bounded E1 pilot, then to a
  committed 04a and E2 budget calculation against an explicit cap. This is an amendment to the
  roadmap's T1 gate.

**Consensus:** both approve with changes, and v2 adopts every change. Under the owner's standing
rule, T1 proceeds and the owner is informed.

## D087 — Documentation for outsiders; 03's graph files can be rebuilt byte for byte

**The owner's request (2026-09-28).** Document the work so that others, people and AI agents, can
reproduce, extend or overtake it, since compute is the bottleneck:
- a README for each experiment, linked from the main README;
- the newest roadmap published and linked.
In the owner's words: "If we are transparent, other people can catch up or outpace us, and that is
a good thing."

**Done:**
- **A README in every experiment folder** (01, 01b, 02, 02b, 03, 03r, 03a), from one template:
  - status, commit and compute;
  - the question, and the answer in brief (registered wordings quoted);
  - the design, and the caveats and corrections;
  - a map of the files, and how to reproduce it;
  - how to extend it, and the record.
  The drafts were written by three Claude subagents from the sources, then edited.
- **`AGENTS.md`:** the repository's layout, setup, and ten rules the work follows.
- **The main README:**
  - a "Start here" list and an "Experiments at a glance" table;
  - a "How to help, or get ahead of us" section;
  - links to each experiment's README;
  - the Status section now points to `ROADMAP.md`, not `PLAN.md`.
- **`ROADMAP.md`** was already on main (v3) but not linked. It gains a dated status block and
  T1's gate amendment (D086).

**Found while writing 03's README.** The drafting agent flagged that 03's graph files are not
committed, and that nothing showed a rebuild reproduces the manifest's raw-byte hashes. The
existing `build` also refuses to run over the committed record.
- **Checked:** a rebuild reproduces both the contents and the raw bytes. numpy writes a fixed zip
  timestamp (1980-01-01).
- **Added `scripts/exp03.py rebuild-graphs [--instance 03r] [--into DIR]`.** It regenerates every
  graph from the kind, final seed and passes recorded in the committed `ensembles.json`, and
  checks each file against `graphs_manifest.json`. Tests cover a match, a tampered manifest, and
  an unknown name; they were seen failing first.
- **Full rebuild on 2026-09-28:** all 640 of 03's and all 768 of 03r's files matched their
  manifest hashes byte for byte.
- The graph files stay uncommitted, because they carry permuted anatomical weights.

**Review:** the documentation goes to Astra 6 and Fable 5.1 for an accuracy check before it goes
to main, which needs the owner's go.

## D088 — The documentation review: fixes, and a correction to main's 01b headline

Astra 6 and Fable 5.1 checked D087's documentation (`docs/reviews/20260928-103526-docs/`).
- **Fable:** "Docs: ready with fixes".
- **Astra:** "Docs: not yet".
- They agree on every concrete must-fix point, and each found some the other did not. Both
  confirmed that 03r's outcome sentence, 02's verdict, 01b's predictions and the D063 amendment
  are quoted exactly, apart from the literal corrections listed below, and that the experiment
  numbers match their sources.

**A correction to main.** Main's README led 01b with "does better than random graphs, and better
than or level with shuffles of itself" (since `44cdf75`, 2026-09-25). "Level with" is a
non-inferiority claim that was never registered and that D033 had already withdrawn (Astra).
- It now states 01b's measured distinction: higher mean best-of-generation fitness than both
  controls, a higher final score than RD, and a final score not detectably different from SH.
- A dated note quotes the old line.
- 02's new README had repeated the phrase; it is fixed there too.

**Fixed (both reviewers unless named):**
- **The 03 and 03r rerun recipes** rebuilt the graphs into the worktree's folder before `git
  worktree add`, which git would refuse. The worktree now comes first. 03's README also says to
  copy `supplement.py` in after `run`, because an untracked file there makes `run` refuse the
  tree (Fable).
- **02 and 02b** now rerun in worktrees at `225e8f8`, `971bbb3` and `7b26c87`, not by checking
  out the clone. 02b copies in only the champion genomes, because `7b26c87` tracks 02's records
  (Astra).
- **03's symmetry sentence** said mirror symmetry "forbids" a left-right comparison. It now
  qualifies this to full mirror equivariance, as 02's Corrections entry does (Astra).
- **What can be checked without a GPU:**
  - `report.json` lets rank counts and p-values be recomputed;
  - the margin gate, SEs and intervals need uncommitted per-genome measurements (Fable).
- **01's total compute:** "about 2.2 GPU-hours", from the frozen SUMMARY.md, is 2.66 hours by the
  committed timing records, before ablations and benchmarks. The README says so, and the frozen
  file is unchanged (Astra; checked).
- **Main's table:**
  - 03's fragility says "failed the test", not "reversed the verdict", which is a registered
    label with another meaning;
  - 03a's cost says "searches alone" (Astra);
  - 02's verdict is quoted in lower case.
- **Main's README:**
  - "everything is public, reviews verbatim" now names the exception, 01b's review (D033);
  - 03's own late push is stated;
  - `PLAN.md` is milestones 0-11 done, 12 deferred;
  - the run-bundle sentence names the scripts that write one;
  - the install line carries the CUDA index (Astra).
- **03r's README** adds two registered caveats (Astra and Fable):
  - a systematic implementation error would also replicate;
  - both P3 directions together allow up to 10% error.
- **02's README** adds its one meaningful bilateral-mean user, a shuffle already at +0.35 at
  generation 0 (Astra).
- **01b's prediction 2** is quoted in full ("... as in 01") (Astra).
- **Exactness:** every summary now separates equality observed in default mode from the guarantee
  inside `replay_mode()` (Astra).
- **Multi-line commands** are single lines, so they work in PowerShell as well as bash (Astra).
- **AGENTS.md** described history as if every rule had always held (both). It now:
  - states the rules for new work and names the exceptions (01 with no pre-registration, 02b,
    02's amendment D041, 03's and 03r's late pushes);
  - says registered text is kept and dated notes are added;
  - scopes run bundles, accounting and review archives to where they apply.
- **ROADMAP.md's status block:**
  - the header no longer says "kept as written";
  - the stale 02b and D050 lines carry their publication dates;
  - "dominate" is replaced by measured shares;
  - 03a's gap is "about 2.5 times the measured throughput", with T1's best candidate at about 1.35
    and its exactness not yet tested;
  - padding is said to be on a working branch (both).
- **D081's "about 0.08"** gets a dated note: 0.072 after D082's rounding fix (Fable).

**Declined:** Fable suggested 0.0465 instead of 0.047 throughout the main README. Both are correct
roundings of the same value, and the main README's lead is reviewed text already on main, so it is
kept.

**Before this goes to main:** `docs/foundations/T1_profile.json` is rerun with the fixed script
and committed, because the ROADMAP cites it (Fable). The owner gives the go.

## D089 — Documentation confirmation pass; no pre-registration so far was pushed before its run

Confirmation pass on D088's fixes (`docs/reviews/20260928-105220-docs-confirm/`):
- **Astra 6:** "Docs: ready to publish". It added one wording note on D088, now fixed.
- **Fable 5.1:** "Docs: not yet", on three points:
  - **The review archive.** "01b's review is the one kept outside the repository" was false.
    Reviews before 25 September are not archived verbatim: 01's, Astra's 24 September roadmap
    review, and 01b's. The README and AGENTS.md now say so.
  - **The push-before-run rule.** Checked against GitHub's push log (`gh api
    repos/juan103/wormwars/events`). **No pre-registration so far reached GitHub before its run
    started:**
    - 01b ran 20:21-21:24 UTC on 24 September at `5161e76`. The first push after the
      repository's creation came at 22:09 UTC.
    - 02's pre-registration was committed at 03:58 UTC on 25 September and the run started at
      04:25 UTC. It was first pushed at 06:37 UTC.
    - 03's and 03r's are already disclosed (D062, D063).

    Each was committed locally before its run. AGENTS.md states that the rule dates from 27
    September (roadmap v3) and that no run so far met it.
  - **`T1_profile.json` must be regenerated and committed,** and the ROADMAP's figures rechecked
    against it.
- **Also fixed, from Fable:**
  - T1.md no longer calls the batching candidate "exact" or gives ×1.36: it is about ×1.35, with
    exactness untested;
  - the ROADMAP gives the D050 correction's own date (27 September) and says "02's task T1";
  - 03r's graph-files bullet is renamed;
  - "its output" becomes "their output";
  - 02b's rerun says to bring along 02's own `probes.json` when the regenerated genomes differ.
- **Checked:** every commit a rerun recipe names (`225e8f8`, `971bbb3`, `7b26c87`, `132acae`,
  `7c146fc`, `5161e76`, `cebbefa`) is reachable from `origin/main`, so `git worktree add` works
  from a fresh clone.

**Consensus:** Astra approves. Fable's three conditions are two fixes, done here, and the profile
rerun, which comes before the push to main.

## D090 — T1's results: the profile committed; padding's claim fails as made, and holds narrowed

`docs/foundations/T1.md` §6 has the detail.

**T1.1: the profile.** `T1_profile.json` is a clean run at `101499c`, with 5 repeats, the
profiler last and the current step re-timed.
- It agrees with the exploratory numbers.
- **On the Task N proxy (one wey), the world's fixed per-tick cost dominates** (a share of 0.70).
  Batching 8 runs gives ×4.2 there, against ×1.36 at best on 02's task T1.
- **Single-strain checkpoints** take about a quarter of a short run.

**T1.2: the class E test, as declared.** The reference comes from the pre-change commit
`1598d56`; the comparison is at `e3694a0`.
- **Switch off:** 188 of 188 outputs equal the pre-change engine, in default and `replay_mode`.
  All 388 of 02's stored hold-outs reproduce exactly (`T1_equivalence_published.json`).
- **Switch on, multi-strain:** 112 of 114 equal. The 2 failures are the test's own error: a
  chunking of 3 leaves a single-strain remainder. Rerun, it equals the batch. The script now
  classifies such remainders.
- **Switch on, single strain equal to its batch:** 66 of 74. The 8 failures are diagnosed:
  - **`bmm` at 1 and 16 rows per strain depends on the strain count,** not only on one against
    many. The pre-change reference shows it too: 2 strains per chunk against 32, at 16 rows,
    differ in 153 of 512 values. This contradicts D082's "two or more agree", which holds as
    tested only at 8 rows and at 20 or more.
  - **Reductions over fewer than 16 worlds** differ in the last bits (`eaten`). Score and energy
    were equal there.
- **By the rule declared in advance, the general claim fails, and it is not reclassified.** What
  holds, as tested: with the switch on, a single strain's score and energy equal its in-batch
  values at 20 or more rows per strain. That covers 02's checkpoints and hold-outs.
- **The CPU** also has a single-strain path (1.2e-7), and padding closes it. §4's premise that
  the CPU is unaffected was wrong.
- The suite passes on the merged branch (see the commit).

**Documents updated:** `REPRODUCIBILITY.md` (the chunking section) and T0.md's amendment (a
follow-up note).

**For review (Astra 6, Fable 5.1):**
1. adopt padding, on by default for new work, with the narrowed claim;
2. amend the contract: a composition is strains per chunk × rows per strain × worlds per chunk,
   and equality across compositions is claimed only as tested;
3. E1 and 04a checkpoints use at least 20 rows per strain, or accept composition-specific
   results. Row padding is not proposed;
4. whether T1's engineering closes.

## D091 — T1 after review: fixes, the rerun, and closure by amendment (proposed)

D090 went to Astra 6 and Fable 5.1 (`docs/reviews/20260928-120548-T1-results/`).
- **Astra:** "T1: not yet". **Fable:** "T1: close with changes".
- They agreed on the substance:
  - keep padding, described as a mitigation;
  - no padding in `rollout` and no row padding;
  - state the tested shapes, not thresholds, and label the narrowed claim post hoc;
  - commit the evidence behind every explanation;
  - close T1 by a dated amendment, because its gate was not met.

**Fixed** (T1.md §7 has the details):
- **The checker:**
  - strict bit equality;
  - remainders inferred from the counts;
  - starting food compared;
  - E1's shapes, a cross-composition table and a CPU leg added;
  - 02's capability probes replayed;
  - the mean-change dtype fixed;
  - tests, sabotage-checked.
- **The padding:** the legacy direction now keeps its layout (Fable's suspicion, confirmed by a
  failing test).
- **The loader:** a supplied config can no longer switch padding on for an old file (Astra).
- **Child-process compute** is recorded and merged (Astra).
- **Diagnostics are committed** (`scripts/t1_diagnostics.py`).
- **Documents:**
  - `test_t1_padding.py`'s wrong docstring and citation are fixed;
  - its CPU contract test uses a two-strain batch, so it does not depend on the BLAS (Fable).

**Rerun:**
- **The reference engine** is `ffeb541`: the pre-change engine plus three support files, merged
  into history with the "ours" strategy so the commit is reachable.
- **The comparison** ran at `3c12e7c`; the diagnostics at `27cb0d1`.
- **Switch off:** 268 of 268 outputs (CUDA) and 250 of 250 (CPU) equal the pre-change engine.
  02's 388 hold-outs and 468 probe evaluations reproduce exactly.
- **Switch on:**
  - multi-strain outputs are unchanged, 158 of 158;
  - a single strain equals its batch in 102 of 110 on CUDA and 104 of 104 on CPU;
  - no published evaluation changes.
- **The 8 remaining differences** are explained by committed diagnostics:
  - **`bmm` at 16 rows and 1 row** depends on the strain count. The two-strain composition that
    padding produces itself differs from 32 strains there.
  - **`eaten` at 8 worlds and 1 world** is a reporting artefact of per-world sums. The final food
    fields are bit-identical for all 32 strains; their sums differ for 22.
- **Corrected:**
  - D090 and REPRODUCIBILITY.md said "only a batch of one" differed at 8 and 1 280 rows; the
    diagnostics show none differs there;
  - T0.md's "CPU: exact under any chunking" gets a dated correction (5 rows).
- **Padding's cost:** none measurable (0.95-1.01).

**Proposed for the reviewers' confirmation:**
- padding kept, on by default for new work, as a mitigation;
- the contract amended: a composition is a tuple, exact only within it, and equal across
  compositions only for the pairs tested;
- E1 guidance: composition-specific results with matched arms, E1's shapes tested before relying
  on them, and E1's own config builder with a test;
- **T1's engineering closes by the amendment in T1.md §7.**

**Also disclosed:** the profile's single timings; the first-round reference's deleted compute
record (about 1.36 h); uncounted scratch exploration. T1's recorded compute is about 6.9 GPU
wall-clock hours.

**Repository metadata (the owner's go, 2026-09-28):**
- the GitHub "About" description now leads with the question and the latest replicated result;
- nine topics were added (c-elegans, connectome, neuroevolution, computational-neuroscience,
  artificial-life, pytorch, open-science, preregistration, reproducibility);
- main's README links the roadmap under its intro (`8e125b2`).

## D092 — T1 closed by amendment, after the confirmation review; 03's signals text corrected

D091 went to Astra 6 and Fable 5.1 (`docs/reviews/20260928-170335-T1-confirm/`).
- **Both answered "T1: not yet".**
  - Fable: documentation only. "No rerun or further review round is needed if these are applied."
  - Astra: closure by dated amendment "is appropriate after the corrections above".
- **Both confirmed the substance:**
  - padding kept as a default-on mitigation;
  - the composition tuple;
  - composition-specific results for E1;
  - the reference engine `ffeb541` as an honest pre-change reference. Astra verified that it
    differs from `1598d56` only in the three disclosed files.

**Fixed:**
- **The account of the 8 failures (both)** had put them all at 16 rows and 1 row. The partition
  is:
  - 2 score and energy outputs at 16 rows;
  - 4 brain-state outputs at 1 row;
  - 2 `eaten` outputs at 160 and 20 rows (02-T1 on 8 worlds and on 1 world).
  The amendment's text now says so.
- **Explanations now rest on committed diagnostics** (`T1_diagnostics.json`, clean at `dde6dd9`):
  - **at 1 row,** a batch of 2 differs from a batch of 4, the brain test's own comparison (Astra);
  - **on 1 world,** the final food fields are bit-identical for all 32 strains, and the sums
    differ for 2 (both). On 8 worlds: identical fields, and different sums for 22.
  - **"2-15 worlds" becomes the tested counts:** random-field sums differ over 2, 4, 8, 12 and 15
    worlds, and not over 1, 16, 20, 32 and 64 (both).
- **The checker** now requires matching, non-empty output inventories. Its pairing guard can fail,
  and tests go through `compare()` itself (Astra, Fable). The v2 run predates the check; Astra
  inspected its inventories and found them complete.
- **A failed child process** still hands over its partial counts (`accounting.child_ledger`,
  `run_counted_child`, with a test) (Astra).
- **Compute:** `T1_compute.json` commits the aggregation: 7.08 h recorded, or 8.44 h with the
  deleted first-round reference. The reported runs' child counts sat under "other" (both).
- **Wording:**
  - the CPU leg ran in quick mode, with 20-30 tick rollouts (both);
  - brain states at 16 rows were already equal against a batch of 4 before padding (Fable);
  - padding's cost is "little measured overhead", 0.95-1.00 timed interleaved (Astra);
  - the implementation comments in `brain.py`, `config.py` and `rollout.py` match the amended
    contract (Astra);
  - `REPRODUCIBILITY.md`'s old "none at 16" is qualified (against a batch of 4) (Fable);
  - a dated pointer to the amendment sits under T1.md §3 (Fable).
- **E1 guidance:** probes run at 1 row, so fix and record strains per probe batch, and never treat
  probe results from different batch sizes as exactly comparable (Fable).
- **Declined:** a warning when a file's padding setting overrides a supplied config's. It would
  fire on every published-genome load, and the behaviour is documented.

**T1 is closed by the amendment in T1.md §7.** Its gate was not met, and it closes by dated
amendment, as both reviewers required. The bounded E1 pilot is authorised; the measured budget
gate stays with E1 (D086).

**03's plain-words signals section (the owner's request) is corrected** (both reviewers).
- **P4's reading.** "The brain is still mostly in its past state" over-read a ratio of averages.
  It now says what the ratio is, and that 0 is scoped to this read-out, these histories and that
  tick.
- **P1's averaging:** half the mirrored difference, over genomes and all 40 ticks. "Strongly,
  relative to" replaces "more than".
- **The stimulus table's final step is tick 110.**
- **Mechanisms:** RESULTS.md's own list of open readings replaces candidates the record did not
  contain.
- **The 02b link** no longer suggests N2 "starts where selection took the champions". RESULTS.md
  says the comparison does not show this.

## D093 — Documentation, T1 and the corrections published on main (the owner's go)

On the owner's go ("Push, yes", 2026-09-28), main was fast-forwarded from `8e125b2` to `c34d01b`:
the roadmap branch at `01e2204` plus one commit removing its working-branch banner. Before the push,
the suite passed in a fresh worktree (511 tests), and the hygiene tests and identity checks passed.

Now on main:
- the documentation for outsiders (D087-D089), with 03's plain-words signals text (D092);
- the correction of the 01b headline (D088);
- T1: the profile, the single-strain padding (off for everything published), the equivalence
  evidence, and closure by dated amendment (D086, D090-D092).

The roadmap branch continues from main, with its banner restored. Next: E1.

**Disclosed:** the roadmap-branch push of `01e2204` went out before its identity check. The check,
run immediately afterwards, was clean. The checks run strictly before every push from now on.

## D094 — 03a: a six-neuron proof of concept, capped at 72 GPU-hours (the owner's decision)

The owner asked whether 03a could be made faster. The answer gave six levers:
1. batch the independent searches;
2. use a one-wey memory task;
3. stage the design;
4. a leaner search;
5. fewer brain substeps;
6. a dynamics-based sister experiment, which asks a different question.

The owner then decided (2026-09-28):
- **"Let's keep the proof of concept with 6 neurons (3 with high foreseeable relevance, 2 with
  medium 1 with low)."**
- **"If there is an imprinting effect we try other neurons if we find a reason for that."**
- **"Proof of concept limited to 72 gpu hours."**

`ROADMAP.md`'s 03a section records this, with the levers and the size of the gap:
- the draft's design at six neurons is about 196 GPU-hours of searches at 02's throughput, plus
  about 10 for whole-brain evolution;
- fitting 72 hours needs about 2.9 times the speed, or a leaner design.

The old rule to shrink the panel 24 → 16 → 12 is struck through and marked superseded, not
deleted.

**Implementation choices made here, for review at 03a's pre-registration:**
- relevance tiers come from a rule fixed before any N2 search;
- the 72 hours include the pilot and are registered in code;
- if the design does not fit, searches or null arms are cut, not the six neurons;
- 03a comes after E1, whose pilot measures a one-wey task's throughput;
- the P4 mechanism follow-up stays ahead of 03a in Track B unless the owner reorders them.

## D095 — E1's pre-registration, v2 after review (the owner asked that E1 be pre-registered)

The owner asked: "if there is something to preregister for E1 do so".

**Built first (`de57ce4`):** Task N, test-first, within the design's tripwire:
- the `navigate` world: a sensing-only relocating target, with a per-world sequence from its own
  random stream;
- the count score and the event table in rollouts;
- collision inputs for scripted controls;
- `wormwars/e1/`: E1's own config builder (padding on, as T1 required), id ranges, S-const, M-avg,
  three blind baselines and the privileged oracle.

**Then `scripts/e1.py` and the pre-registration v1 (`f83bd19`).** Astra 6 and Fable 5.1 reviewed
them (`docs/reviews/20260928-181005-E1-prereg/`). **Both answered "revise",** and both confirmed:
- the Task N mechanics match the design;
- the σ rule stays as registered. Fable showed its outcome is forced by geometry: σ ≤ 3 cannot
  reach D = 8, so σ = 6 is selected either way;
- fixing the gate's numbers before the pilot is a legitimate tightening of the design.

**v2 adopts every change:**
- **The cue test (Astra).** v1 compared a bootstrap bound with a fixed half of the observed mean.
  v2 bootstraps the per-world contrast 0.5 × real − mirrored and requires a lower bound ≥ 0. Astra's
  counter-example is a test.
- **The freeze file (Fable)** is written with LF and hashed normalised, which avoids D056's class
  of bug.
- **The guards** are functions, and each has a test:
  - formal stages need CUDA, a clean tree including the pre-registration, and a pushed HEAD;
  - exclusive start markers, so an interrupted stage is not silently rerun;
  - the gate re-derives σ, every tuned winner, the grids, the oracle and the navigator from the
    freeze's own rows;
  - the gate refuses code or pre-registration changes since the pilot;
  - the cap is checked before every rollout and before any result is written, with fixed wording
    if it is hit.
- **Evidence:**
  - the gate's full event tables are committed;
  - the head's start and end of every leg are recorded, and path efficiency is displacement over
    path, at most 1. v1 used target centres and could exceed 1 (both);
  - every grid point's mean is kept;
  - the design's shares of episodes with at least 1 and 2 arrivals are recorded;
  - the constant probe runs for every controller (Astra);
  - the own-body level refuses zero samples (Fable);
  - throughput is measured in 04a's shape, off E1's worlds (Fable).
- **The binding rule:** the binding commit is the one the pilot records. It must be clean and
  pushed, and the gate refuses anything that changed since.
- **Disclosure (§7), completed after Fable's question:**
  - the first smoke run used E1's ranges at tiny sizes: 8 pilot and 8 tuning worlds, at a 40-tick
    horizon;
  - a debug run computed the σ measure on 32 pilot worlds, outside the accounting;
  - no gate world was evaluated;
  - every stage now starts at index 1 000 of its range, and smoke runs use ids 0-9 999.
- **Disclosed rather than changed:** the random walk's noise follows batch shape, not world id.
- **Wording:** the registration precedes the *formal* pilot and gate, with the earlier exposure
  disclosed. The reliability criterion is a sample criterion (at least 820 of 1 024).

**Next:** confirmation by both reviewers. Then the binding commit is pushed, and the pilot runs.

## D096 — E1's pre-registration v3, after the confirmation review

Astra 6 and Fable 5.1 checked v2 (`a6437be`; `docs/reviews/20260928-183315-E1-prereg-confirm/`).
**Both answered "revise".** Both confirmed that v1's cue test, LF freeze, markers, endpoints and
event retention were fixed correctly. v3 adopts every remaining point.

**Corrections to D095, dated 2026-09-28** (D095 is kept as written):
- **"The guards ... each has a test" was false** (both). The same-code check, the dirty and
  unpushed refusals, and the gate's cap path had no test. They do now. The live git fetch and the
  CUDA preflight are exercised by one guarded smoke run on the binding commit.
- **"σ = 6 is selected either way" was false** (Astra). Geometry excludes σ = 2 and 3, not σ = 4.
  σ = 6 is strongly expected, not certain. The "about an eighth" and "must search" readings of
  the flag are withdrawn: the 5% floor is a reporting criterion, not a controller cutoff.

**Fixed in v3:**
- **The cap** (both):
  - it is checked before every rollout and measurement loop, including generation 0 and
    throughput;
  - the final decision comes after all analysis, just before any write. Astra's mocked clock had
    produced "passed" at 28 801 s;
  - the clock is the process's time since it started, the accounting's own boundary.
- **A cap hit keeps every completed arm's counts and events** (Astra).
- **The freeze validation checks the supporting measurements** (Astra):
  - the coverage rows must be exactly the registered candidates, with finite shares in [0, 1] and
    the registered number of leg starts;
  - the tuning scores must be finite;
  - the own-body level needs samples.

  Astra's malformed freezes are tests.
- **Environment:**
  - formal stages require the RTX 5080;
  - the pilot records Python, NumPy, Torch, CUDA, the GPU and the connectome cache's sha256, and
    the gate refuses any difference;
  - `requirements.txt` is guarded;
  - the resolved configuration is recorded.
- **Order and robustness** (Fable):
  - a preflight (connectome, interface, one GPU operation) runs before each start marker;
  - the gate writes its outcome before the event tables;
  - the compute record goes to `compute-record.json`, which git does not ignore;
  - the smoke mode removes stale event files.
- **§7:** the second smoke pair found by Fable (16:08 UTC) is accounted for. It ran in the command
  that switched smoke runs to ids 0-9 999, so its gate used smoke ids. The basis, the session's
  command order, is stated, because no record holds those ids. The index 1 000 offset would cover
  it either way.

Tests were added for each; the malformed-coverage and cap-clock tests were sabotage-checked. They
were written after the code, not seen failing first, which is disclosed here.

## D097 — E1's pre-registration v4, after the final confirmation round

Astra 6 and Fable 5.1 checked v3 (`f63cdaa`; `docs/reviews/20260928-185310-E1-prereg-final/`).
- **Both answered "revise".** Neither found a defect that would invalidate a result.
- Both confirmed as resolved:
  - Fable: the 16:08 smoke pair's disclosure, the cap checks and the compute record's path;
  - Astra: the retention on a cap hit, the supporting-measurement validation and the σ wording.

**Fixed in v4:**
- **Crash retention** (both). v3 promised that completed arms were kept after any interruption,
  but kept them only on a cap hit.
  - Now every arm is checkpointed to disk (`gate_partial.npz`) as it completes.
  - Any exception or interrupt writes the result with its own fixed wording, *"E1 positive control:
    not completed (the run stopped)"*, keeping every completed arm, then re-raises.
- **Tests through the commands themselves** (both). `tests/test_e1_commands.py` drives `cmd_gate`
  and `cmd_pilot` with a fake rollout: completed, cap during the arms, cap after the analysis
  (Astra's mocked clock), crash, once-only, committed freeze, and the pilot over a freeze. The crash
  and final-cap paths were sabotage-checked.
- **The guard-test claim** now lists exactly what no test exercises (Fable): the live fetch and
  push check, the GPU preflight, the modified-freeze branch, and the zero-sample refusal.
- **The pinned environment is enforced** against `requirements.txt`: Python 3.13, torch and numpy.
  The connectome source spreadsheet's sha256 is recorded and compared too (Astra).
- **The budget boundary is stated** (Astra):
  - the clock starts at script load, counting slightly more than the accounting;
  - writing the outputs after the final check is outside the decision, and is recorded.
- **A cap already spent** before a stage starts spends nothing: the stage does not start (Fable).
- **A test deleted real smoke records** (Fable); it no longer does.
- **The development records §7 cites are committed** (`experiments/E1-navigation/development-records/`).
- **If the guarded smoke run fails,** the fix is committed with a dated note, and the later commit
  binds (Fable).

The pilot's own-body zero-sample refusal still has no test. It is disclosed, and it can only
refuse, before any stage output.

## D098 — E1's pre-registration v5, after the fourth review round

Astra 6 and Fable 5.1 checked v4 (`a84d30f`; `docs/reviews/20260928-191032-E1-prereg-v4/`).
- **Both answered "revise".** Neither found a defect that would invalidate a result.
- Fable: its two points are text and test changes, and "I do not need another round if they are
  applied as described."
- Astra's points are fixed and tested.

**Fixed in v5:**
- **The handler covers the analysis too** (both). Astra showed that an error in `gate_rules` or
  `secondary`, after every arm had run, wrote no result.
  - Everything from the first arm to the final budget decision is now inside the handler.
  - A "not completed" record carries its outcome and the completed arms, never a rule's result.
    Fable noted that a cap hit after the analysis had left `passed: true` in the record.
- **The checkpoint is atomic** (both): a temporary file, then `os.replace`. The test simulates a
  kill that leaves a truncated file mid-write; it fails on an in-place write (sabotage-checked).
- **The budget wording** (Astra): an overrunning rollout is caught by the final check and ends as not
  completed. Only writing the outputs is outside the decision.
- **New command-level tests:**
  - a crash in the analysis, and an interrupt (Fable: `RuntimeError` alone would not catch a
    handler narrowed to `Exception`; that sabotage is now caught);
  - both "did not start" cap refusals (Fable);
  - the same-code check in a real temporary git repository: an output-only commit passes, a code
    change is refused (Astra);
  - the command tests use ids outside E1's ranges, even with the rollout faked (Fable).
- **Wording** (Fable):
  - the header lists every review instead of "twice";
  - the zero-sample refusal is noted as coming after the pilot's marker, correcting Fable's third
    review, which it flagged itself;
  - a §7 bullet moved to the item it belongs to.

**Before binding** (Fable): the committed-freeze check's two git commands are run by hand on a
tracked file, with an absolute path, and the full suite runs on the binding commit.

## D099 — E1's pre-registration v6: bound after the fifth review

Astra 6 and Fable 5.1 checked v5 (`0e13e49`; `docs/reviews/20260928-192725-E1-prereg-v5/`).
- **Astra: "E1 pre-registration: ready to bind".** All four of its v4 points were resolved. Its own
  injections into `gate_rules`, `secondary` and a last-arm overrun kept all 16 arms, with the
  correct incomplete outcome.
- **Fable: "revise", on one text point,** and "I do not need another round for the must-fix item if
  the text is changed as described." It is applied, so both agree.

**Correction to D098, dated 2026-09-28** (D098 is kept as written). Its "New command-level tests"
listed two tests that call functions directly: the atomic checkpoint and the same-code check in a
real git repository. The pre-registration also attributed the pin refusals to the wrong file. v6
lists all three as function-level tests in `tests/test_e1_commands.py`, and states that no command
test runs with the formal guards on. Their wiring in `cmd_gate` is exercised by the guarded smoke
run, on the passing path only.

**Also, from Fable's non-blocking points:**
- the cap-after-analysis test now asserts that no rule result is in the record;
- the not-completed record is written atomically;
- the test file's docstring is current.

**The binding sequence:**
1. the full suite and the hygiene and identity checks on this commit;
2. the push;
3. one guarded smoke run on the pushed commit. It must complete all 16 gate arms, which checks the
   atomic replace on this disk (Fable);
4. the pilot.

`experiments/E1-navigation/` is on a local drive and not under a sync tool.

## D100 — E1 positive control: passed

**The pilot** ran at the binding commit `eb0b781` in 316 s, and wrote the freeze by rule:
- σ = 6, flagged: coverage 0.878, against the registered 0.90, as disclosed in advance;
- the navigator is S-const, at k = 8192, speed 1 and turn 0, with a tuned mean of 8.78 targets
  against the oracle's 8.85.

The freeze was committed and pushed at `a73a67d`.

**The gate** ran once at `a73a67d`, in 36 s, on gate worlds 996 201 000-996 202 023:
**"E1 positive control: passed"**, with no rule failed.
- **Reliability:** 1 023 of 1 024 episodes reached at least 2 targets.
- **The baselines:** the lower bounds of the paired differences were 8.19 (constant), 8.37 (random
  walk), 7.97 (wall-follower) and 7.68 (K), against a margin of 0.5.
- **The cue:** the lower bound of 0.5 × real − mirrored was 4.29, against a required 0.
- **The navigator's mean** was 8.68 (98.7% of the oracle), and 0.03 under the mirrored decoy.
  S-const at k ≤ 32 reached 5.62 (64% of the oracle).

**For 04a:**
- 74% of generation-0 random N2 brains score zero on every pilot world, so the bounded shaping term
  will be needed;
- throughput in 04a's shape is 110, 336 and 438 strain-worlds/s at 1, 4 and 8 runs batched;
- 04a gets its own pre-registration, reviewed and pushed before its run, as E1's was.

Results: `experiments/E1-navigation/RESULTS.md`, which goes to Astra 6 and Fable 5.1 for review.

## D101 — E1 results review: text fixes; the outcome stands

Astra 6 and Fable 5.1 reviewed E1's results (`docs/reviews/20260928-194709-E1-results/`).
- **Both: "E1 results: fix",** on text only.
- **Both confirmed the run followed the registration.** From the local reflogs, the binding push
  came before the pilot's marker, and the freeze push before the gate's.
- **Astra independently recomputed** every count, secondary measure and all five bootstrap bounds
  from `gate_events.npz` and the per-world counts. All match.
- Fable re-derived every tuned winner as the first maximum of its grid.

**Corrected in RESULTS.md, with a dated Corrections section:**
- the compute timing, now from the accounting throughout (316.2 s + 37.6 s = 353.8 s);
- K labelled as reading the scent, not blind;
- the k ≤ 32 bound labelled an assumption, with the full gain curve. The k ≤ 32 winner uses turn
  0.2, and turn 0 gives 4.23;
- "because it steers to the decoy" softened to "consistent with";
- "selection will need shaping" replaced by "meets the design's condition". **This also corrects
  D100's "the bounded shaping term will be needed", dated 2026-09-28.**
- the gate-world statement hedged as §7 is.

**Added:**
- M-avg's full winner, and 0.35 labelled as the goal cue's peak current;
- the σ = 6 counts (1 124 of 1 280 leg starts);
- grid-edge winners flagged, so the blind baselines may be under-tuned;
- the one failed world (996 201 898: navigator 0, oracle 8);
- the oracle as a reference: the navigator beat it on 15 worlds;
- the mirrored arm's statistics rest on 29 arrivals;
- the guarded smoke run's records committed (Fable).

AGENTS.md now says E1 is the first registration to meet the push-before-run rule.

**For 04a's pre-registration,** both reviewers listed:
- Task N frozen and hashed;
- baselines re-run paired on 04a's hold-out;
- an exact shaping formula, bounded below one arrival, used in training only, and removed from every
  gate score. An unshaped arm as a secondary (Fable);
- a budget from the aggregate measured rates with a margin, and a committed calculation with a cap;
- compositions declared for training, validation, generation 0 and the final evaluation;
- per-run random streams;
- the champions' effective gain measured against the curve, with no threshold relative to k ≤ 32;
- runs as the unit, with a declared share of runs that must pass.

## D102 — E1 published on main (the owner's go)

On the owner's go ("sure", 2026-09-28), main was fast-forwarded from `c34d01b` to `3765db0`: the
roadmap branch at `addfba1` plus one commit removing its banner. Before the push, the suite passed on
a clean checkout of the candidate (577 tests), and the hygiene and identity checks passed.

Now on main:
- **E1:** Task N, the controls and the runner; the bound pre-registration and its five reviews; the
  pilot's freeze, the gate's results and event tables, and the development records; RESULTS.md with
  its dated corrections, and the E1 README;
- **03a's six-neuron proof of concept** (D094);
- decisions D094-D101.

The roadmap branch continues from main, with its banner. Next: 04a's pre-registration.

## D103 — 04a's pre-registration drafted; batched runs with per-run streams

After E1 (D100-D102), 04a's pre-registration is drafted
(`experiments/04a-navigation-primitive/PREREGISTRATION.md`, v1), from the design's 04a section and
the list both reviewers gave in D101. It goes to Astra 6 and Fable 5.1 before anything is bound.

**The draft's main choices:**
- Task N exactly as E1's gate ran it: built by E1's own config function, and refused if its resolved
  configuration's hash differs from E1's gate record. The world seed is E1's.
- 02's optimizer (32 genomes, 3 elites, top 8 parents, 02's mutation, one island), 8 worlds per
  genome per generation, 1 000 generations.
- 16 runs: 12 shaped (c = 0.5) as the primary arm, 4 unshaped as a secondary. Fitness is
  count + c × progress, where progress is the unfinished leg's closed fraction at the last tick,
  clipped to [0, 1]: at most c per episode, below one arrival. Training only.
- **Runs are batched 8 at a time in one rollout, each with its own streams** (initialisation,
  mutation, training worlds), seeded by run number. This needed two engine changes:
  - the rollout accepts one row of world ids per strain, and returns each episode's progress and
    final head position. A test checks that identical rows reproduce the shared-ids rollout exactly;
  - the shaping moved out of the world configuration (a first version, `WorldConfig.target_shaping`
    in 8e21cc7, could not give runs in one batch different coefficients).
- The champion is the first checkpoint with the best mean on 64 validation worlds (41 checkpoints);
  the generation-0 baseline is the generation-0 checkpoint. Both are fixed before the hold-out.
- Per-run rules on 1 024 hold-out worlds: E1's reliability, baseline and cue rules, plus beating
  generation 0 by a lower bound above 0.5. "04a: passed" needs 6 of the 12 shaped runs.
- Reported only: a performance-equivalent gain on a hold-out re-run of E1's gain curve, E1's
  secondary measures, the decoy capture (Fable, D101), and a replay check of each champion's
  checkpoint batch.
- The budget: a development projection on smoke ids measured 4.749 s per generation, against E1's
  4.676 s per rollout; the total estimate is about 2.75 GPU-hours, and the cap 6. A guarded
  projection on the binding commit must stay within 4.5 hours of training before any formal stage.

**New code:** `wormwars/registration.py` (E1's guards as shared functions; `scripts/e1.py` keeps its
own copies as the published record), `wormwars/e04a/evolve.py` and `scripts/e04a.py`, with tests.

## D104 — 04a review v1: both "revise"; v2 adopts every must-fix; a smoke run touched 24 training ids

Astra 6 and Fable 5.1 reviewed draft v1 (`b38c7cc`; `docs/reviews/20260928-213057-04a-prereg/`).
Both said "revise". Both found no coupling between batched runs and no way to game the shaping
bound, and both advised against making S-const a gate.

**Found by the reviewers, and what was done:**
- **The smoke mode trained on the formal training range** (Astra). `use_smoke` did not rebind the
  training ids, so v1's CPU smoke run drew 24 ids from 997 000 000 onward. They are reconstructed
  exactly and recorded (`development-records/smoke-training-exposure.json`); **the training range
  moves to 999 000 000 onward**; the smoke mode now rebinds every range, and a test checks every id
  the simulator receives.
- **A test fixture deleted real smoke records** (Astra), the same class of bug as in E1: it called
  the cleanup before redirecting to a scratch folder. It removed v1's smoke train and evaluation
  records; the attempt records and genome files survived. Fixed, with a test of where cleanup acts.
- **Genome files would have redistributed connectome data** (Fable): generation-0 genomes are
  proportional to the anatomical weights (D028), and v1 committed every checkpoint. Genome files now
  stay local; records carry hashes, and generation-0 baselines are checked against their
  regenerated populations.
- **The projection was not a gate** (both): batch A now requires a completed projection within its
  limit on the same code and environment; the projection runs once, under the cap.
- **E1's freeze and gate records were unguarded** (both): now guarded and hashed.
- **"At least as often as not" overclaimed** (both): withdrawn; the exact share bound (0.245 for 6 of
  12) and the marginal-bound caveat are reported.
- **A cue gap** (Astra, Fable): a new gating rule requires the real cue to beat the champion's own
  constant probe by a lower bound above 0.5.
- **No engine-equivalence check** (both, AGENTS.md rule 7): `scripts/e04a_equivalence.py` compared the
  rollout at `5eaf339` with the new one on smoke ids. Every score and event entry was identical on the
  CPU (the declared tolerance) and on CUDA.
- Text that disagreed with the code, untested paths (`require_committed`, the projection), and the
  development records not committed (Fable): fixed.

**Suggestions adopted:** 256 validation worlds; a real-simulator independence test at a fixed
composition; a rerun rule fixed in advance (once, after a crash or interrupt, never after the cap);
the verdict written before the non-gating extras; a finite check at validation; more command tests.

**A development pilot** (Fable's suggestion): 200 generations of batch A's shape on smoke ids. The
best genome's validation mean rose from about 0.2 targets to about 1.7 by generation 25 and stayed
between about 1.0 and 2.1 through generation 199. That suggests many runs may not meet the
reliability rule within 1 000 generations. The generation count is unchanged; the question goes to
review v2.

## D105 — 04a review v2: both "revise"; v3 moves the formal seeds and closes the rerun and padding gaps

Astra 6 and Fable 5.1 reviewed draft v2 (`68f8aa3`; `docs/reviews/20260928-221414-04a-prereg-v2/`).
Both found the v1 must-fixes fixed in the code, both said "revise", and **both advised keeping 1 000
generations, 02's optimizer and every threshold** despite the pilot's plateau: a change now would be
an untested guess on 8 runs, and comparing optimizers is E2's job (consensus; it informs the owner).

**Found, and done in v3:**
- **The pilot and projection used the formal run seeds** (Fable): formal runs 0-7 would have started
  from the populations the pilot evolved. The formal seeds move to 1 105 000 onward; the projection
  (1 109 000) and smoke runs (1 108 000) get their own; a test checks they are disjoint.
- **A genome file's metadata could override single-strain padding** without changing any hash
  (Astra). The evaluation now requires each file's effective brain configuration to equal the
  registered one; tested, and sabotage-checked.
- **The rerun rule in the text was wider than the code** (both): kills (marker, no record), the
  projection, archiving the stopped attempt's genomes, a recorded reason, a tested second-stop
  refusal. Amendments get an unguarded `AMENDMENTS.md`.
- **Failure records** (Astra): the not-completed record is written before any genome save; the decoy
  measure has its own error record.
- **Wording** (both): the exposed ids are "reconstructed, consistent with the ledgers", not
  "reconstructed exactly"; the ledgers are preserved.

§6 now states the expectation: "not passed" or "some runs passed" would not surprise us; either leads
to E2, and a new 04a attempt would be a new registration on fresh hold-out ids.

**Also this round:** CI (`.github/workflows/tests.yml`) runs the CPU suite on every push, with the
connectome fetched and hash-checked at run time, after an outside review noted outsiders could not
check the suite (the owner shared that review, 2026-09-28).

## D106 — CI's first run: 03's graph files are byte-identical only on Windows

The first CI run (Linux, 2026-09-28) passed 639 tests and failed one:
`test_rebuild_graphs_reproduces_the_committed_files`. The two rebuilt graph files differed from the
raw hashes in `graphs_manifest.json`. The committed files record `create_system = 0` (Windows) in
their zip headers; Linux writes 3, and zlib builds can also compress differently. D087's "byte for
byte" was true only on the platform that wrote the files, and the README said so without that
qualification.

**Done:**
- `graphs_content_manifest.json` for 03 and 03r: a hash of each file's arrays, computed from the
  original files after each was checked against its raw hash (all 640 and 768 verified);
- `rebuild-graphs` checks the content hash (required on any system) and the raw hash (reported), and
  `--windows-bytes` rewrites only the OS byte, so the raw hashes that the binding commits' code checks
  at load time also match wherever zlib compressed identically. The command reports how many do;
- the test requires content equality everywhere and raw equality on Windows;
- dated notes in 03's and 03r's READMEs.

The published results are unaffected: the measurements ran on the committed files, checked by raw
hash on the machine that wrote them.

## D107 — 04a review v3: both "revise", narrowly; v4 charges a killed attempt's compute before a rerun

Astra 6 and Fable 5.1 reviewed draft v3 (`082210e`; `docs/reviews/20260928-224400-04a-prereg-v3/`).
Both found every v2 must-fix fixed in the code. Both said "revise" for one shared gap, and Fable
said a confirmation of the diff would do, not a full round.

**Found, and done in v4:**
- **A killed attempt's compute was never counted** (both): the accounting writes its record only when
  a process ends normally, and v3 had just made kills rerunnable. Before a rerun, the killed attempt
  is now charged from its start marker to its last file write, plus a registered 900 s tail, as an
  attempt record, once; the cap check follows, and a rerun the cap refuses is not used up. Tested.
- **An over-limit projection could be rerun unchanged** until timing noise let it pass (Fable). A
  rerun now requires fewer registered generations than it projected. Tested.
- **§6 misstated the lowest passing mean** (both): it is 820 episodes at exactly two and 204 at none.
- **§9 gave v1's projection as 41 s** (Fable): the committed record says 33.8 s.

**Also:** the rerun is applied after every other check and is obligatory after a crash or kill; one
projection rerun in total, its scratch genomes archived; the path after a crash in guarded code is
stated; tests of stopped-projection and stopped-evaluation reruns.

**CI:** the second run passed on Linux (651 passed, 2 skipped), with D106's content-hash check.

**The GPU was paused** at the owner's request during this round (2026-09-28), and freed again the
same evening. No GPU work ran while it was paused.

## D108 — 04a review v4: Fable "ready to bind", Astra one kill-accounting gap; v5

Astra 6 and Fable 5.1 checked v4 (`1653809`; `docs/reviews/20260928-230307-04a-prereg-v4/`).
- **Fable: "ready to bind"**, with two text slips to fix in the binding commit (the runner's decision
  labels, and §13's stale reason for not running the unguarded smoke run), plus non-blocking
  residuals.
- **Astra: "revise"** for one gap: the kill reconciliation rebuilt `compute.json` only when it first
  wrote its record, so a kill between the two writes would leave the next cap check reading a stale
  total.

**Done in v5:** the reconciliation record is written atomically and reused with its stored charge,
and the aggregate is rebuilt before every cap check (tested with a missing and a stale aggregate,
sabotage-checked); a killed rerun is charged before its refusal; an over-limit projection's rerun
must fit the limit at its own measured rates; the text slips; and D107's "ends normally" is better
said "when its cleanup handlers run" (Astra). Fable's suggested CPU smoke run of all four stages with
real rollouts was run and completed without errors.

## D109 — 04a's pre-registration: both reviewers "ready to bind"; bound

Astra 6 and Fable 5.1 checked v5 (`627b886`; `docs/reviews/20260928-231738-04a-prereg-v5/`) and both
said **"ready to bind"**, after five rounds (D103-D108). Corrections made in the binding commit, as
they asked:
- "the aggregate is rebuilt before every cap check" (§8, §14, D108) overstated the code (both). The
  cap clock now rebuilds the accounting's total whenever a stage starts (Fable's preferred fix), and
  the text says what is true: at each reconciliation and at each stage's start; the per-rollout
  checks read it as it stands;
- a killed rerun is charged only when the operator runs `--rerun` once more and takes the refusal;
  §8 says so (Fable);
- the v5 CPU smoke run ran on the working tree before the v5 commit (Fable, Astra);
- `REGISTERED["rerun"]` states the stricter over-limit condition (Fable);
- one unreconciled case is disclosed: a stopped record whose own accounting file is missing (Fable).

**The binding commit** is the commit the formal projection records; the projection, the guarded smoke
run and the stages follow, each record committed and pushed before the next stage.

## D110 — 04a: "04a: passed"; results written, review pending

04a ran as registered (v5, bound at `e3d68be`): the projection (9531aaf), batch A (7ec22bb, 1.44 h),
batch B (75307a3, 1.36 h) and the evaluation (2b9ed94, 304 s), 2.91 GPU-hours of a 6-hour cap, one
attempt per stage.

**Outcome, in the fixed wording: "04a: passed".** 8 of 12 shaped runs passed all five rules on 1 024
hold-out worlds (exact one-sided 95% lower bound on the share, 0.39); 4 of 4 unshaped runs passed.
The four failures missed only reliability (70-77% of episodes with at least 2 targets, against 80%).
Every run beat every baseline by a lower bound of at least 1.03, was misled by the mirrored cue (97-100%
of episodes ending nearer the decoy), was helped by the real cue over a constant one, and beat its
generation 0.

**Read with it:** the champions are slow, cue-following navigators: 2.0-2.8 targets per episode,
23-32% of the oracle, a performance-equivalent gain of k 3.5-6.9, and path efficiency 0.27-0.34
(E1's navigator: 8.71, 0.83). The unshaped arm did as well as the shaped one and produced the best
champion (run 12, 2.81), so shaping was not needed here (descriptive, 4 runs). Every champion's
checkpoint batch replayed exactly on the validation worlds. The module for E3 is run 2's champion.

RESULTS.md and a README are written; the results go to Astra 6 and Fable 5.1. Main needs the owner's
go.

**Also:** the 03m exploratory plan (v4.1) was agreed by both reviewers ("ready to run") and merged
from its branch after 04a's evaluation (`69286d9`); its GPU commands run next, under their own
5-hour cap.

## D111 — 04a results review: both "fix", text only; corrections dated, the verdict unchanged

Astra 6 and Fable 5.1 reviewed 04a's results (`5312475`; `docs/reviews/20260929-025032-04a-results/`).
Both checked the registration against the records and found it followed: the stage commits and their
pushes before each marker, the same-code and environment chain, the ids, seeds and compositions, all 16
champions re-derived, `run_rules` against §6, and the share bound. Astra recomputed all 82 arm means.
Both said **"fix"**, for text only, and the corrections are added as dated sections in RESULTS.md and
the README, quoting what was written:
- the training-curve and timing sentences were wrong;
- "steer" and "like a stereo steerer" overclaimed: the probes show cue use, not its computation, and
  the champions' behaviour is closer to E1's temporal controller (M-avg) than to a stereo steerer
  (Fable). This matters for E3, which assumed a left-right cue follower;
- reliability belongs to the 12 passing champions, not all 16 (Astra);
- "no deviation" missed one: the guarded smoke run ran after the projection, on `9531aaf`, not on the
  binding commit, and its record calls `9531aaf` the binding commit (both).

**D110, corrected here** (both): *"the projection (9531aaf)"*: the projection ran at `e3d68be`;
`9531aaf` holds its record. *"Every champion's checkpoint batch replayed exactly"*: every champion's
checkpoint batch reproduced every recorded per-world count on the validation worlds (256 of 256);
exact replay is not claimed (AGENTS.md rule 6).

**Before main** (Fable): ROADMAP.md's 04a status and the root README's "next" line are out of date.

## D112 — 04a published on main, under the owner's new rule; a flaky CPU test found by CI

**A new standing rule.** Asked whether work approved by Claude, Astra 6 and Fable 5.1 still needs
their go to reach main, the owner answered (2026-09-29): "Yes, if agreement, push." From now on, when
the three agree and the publication checks pass, Claude pushes to main and informs the owner
afterwards. Anything unusual (a deletion, repository settings, anything without review consensus)
still goes to the owner first. No force-push or history rewriting, as before.

**Published:** main was fast-forwarded from `3765db0` to `011d82b`: the roadmap branch at `f6971ec`
plus one commit removing its banner. It carries 04a (the registration and its five reviews, the
records, RESULTS.md with its dated corrections, the README; D103-D111), the shared registration guards,
the CI workflow and D106's content-hash check, and 03m's agreed exploratory plan with its Q1
outputs (its simulations are still running). Checks: CI passed on `f6971ec` (a clean Linux checkout,
the CPU suite); the hygiene tests passed on the candidate; every commit has the noreply identity, no
session line and no email.

**A flaky test, found by CI.** `tests/test_world.py::test_batching_worlds_does_not_change_a_world`
failed once on Linux (run 36505009495, at `5312475`) and passed on the next two runs with no code
change: one of 40 positions differed by 0.0034 after 40 ticks, against a tolerance of 1e-5. The test
asserts that a world evolves the same alone and beside three others on the CPU. T1 found that a CPU
batch of one can differ in the last bits (D092), and chaotic dynamics amplify that over 40 ticks;
GitHub's runners vary in CPU, which likely explains why it shows only sometimes. It predates 04a and
touches none of its results. **To do:** make the test match what is claimed (the same composition, or
padding, or a documented tolerance), with review, rather than loosen it silently.

## D113 — 03m ran (exploratory); results written, for review

03m's plan (v4.1, agreed by both reviewers after four rounds) ran on 2026-09-29: synapses, weights,
decay and lesions, 3.32 GPU-hours of a 5-hour cap, one attempt each, every reproduction check exact.
Exploratory findings (RESULTS.md):
- N2's large food response depends on the placement of its chemical weights (permuting them, or all
  weights, brings it to the shuffles' level) and on RIA and AIY (deleting either pair does too);
- its high P4 survives all of these, every single and paired deletion tested (lowest 0.907, AIZ), and
  gap junctions switched off; with its weights permuted, N2's wiring keeps a median P4 of 0.885;
- the history mostly relaxes, more slowly in N2 (9.4% left at 300 ticks, above 78 of 80 null
  graphs); about 1% of N2's random brains settle with the difference intact.
The results go to Astra 6 and Fable 5.1.

## D114 — 03m results review: both "fix"; the summary corrected

Astra 6 and Fable 5.1 reviewed 03m's results (`40fcbef`; `docs/reviews/20260929-061029-03m-results/`).
Both found the runs followed the plan and every number recomputes (Astra: all 627 valid P4 ratios, the
neural-update total, the reproduction checks). Both said **"fix"**: the summary overclaimed, written
minutes after the last run (Fable). Corrections are dated in RESULTS.md and the README, quoting what
was written.

**D113, corrected here** (both): *"N2's large food response depends ... on RIA and AIY (deleting
either pair does too)"* — the deletions leave the response in the nulls' upper tail, not at their
typical level, and they cut the history signal in proportion, so the response and the persistence
are not shown to have separate sources. *"its high P4 survives all of these ... and gap junctions
switched off"* — it does not survive most weight permutations (37 and 35 of 64 fall below the
threshold on both measures), and N2's elevation over the shuffles narrows with gap junctions off (5
of 80 gaps-off null graphs match or exceed N2). *"about 1% of N2's random brains settle with the
difference intact"* — 26 of 2 048 kept more than 10% and passed a ten-tick settling test, and some
null graphs have more (SH-10007: 171).

**What stands:** the slower relaxation (N2 above all 80 null graphs at ticks 5-50, 78 at 300); the
dependence of N2's large response on weight placement and on RIA and AIY; the negative deletion
screen. A confirmatory follow-up is possible (RESULTS.md lists what both reviewers would register);
it is not planned yet.

## D115 — The flaky batching test replaced; 03m's last text fixes; both reviewers "fix" on text only

Astra 6 and Fable 5.1 checked 03m's confirmation-round fixes and the test change together
(`docs/reviews/20260929-065309-final/`). Both said "fix", for text only; both agreed the new test
tests the right claim.

**The test change (D112's to-do).** `test_batching_worlds_does_not_change_a_world` compared a world
alone with the same world in a batch of 4, to 1e-5 after 40 ticks, and failed once on a Linux CI
runner. Exactness is claimed only within one composition (D082, D091), so it is replaced by:
- `test_batch_mates_do_not_change_a_world`: the composition fixed at (1 strain, 4 worlds per strain,
  20 weys per world), only the batch-mates changed, exact equality. A coupling of world 0 to its
  batch-mates, sabotaged in at 10⁻³ of their mean position, was caught (a first attempt at 10⁻⁶ was
  below float32 resolution and changed nothing);
- `test_a_world_alone_and_in_a_batch_agree_approximately_over_a_few_ticks`: alone against a batch of 4,
  to 1e-4 over 5 ticks, labelled approximate (Fable).

**What is no longer tested:** agreement across compositions after 40 ticks, the only foraging-world
dynamics check that varied the number of worlds per strain. The cause of the CI failure is likely
last-bit CPU differences between batch shapes amplified by the dynamics; it was not reproduced.
**Still exposed** (Fable): three CPU tests assert exact equality across compositions
(`tests/test_t0_pairing.py`, two; `tests/test_e1_task.py`, one) and could fail the same way on some
runner. They are left as they are until one does, and this entry is where to look.

**03m's last fixes** (both): the deletion claim scoped to "tested" deletions in README.md and
ROADMAP.md, with the weight-permutation and gap-junction qualifications (Fable); the per-tick counts
attributed correctly (Fable's check covered six graphs; Claude's count covered all 80); the roadmap's
Track B section points to 03m.

## D116 — 03m and the test change published on main

Under the owner's rule (D112), with both reviewers' fixes applied (D114, D115), main was fast-forwarded
from `009bed1` to `1c0c978`: the roadmap branch at `d812e1b` plus one commit removing its banner. It
carries 03m (the plan and its four review rounds, the outputs, RESULTS.md with its dated corrections,
the README), the replaced batching test, the REPRODUCIBILITY note, and D113-D115. Checks: the full
suite locally, CI on `d812e1b`, the hygiene tests, the identity check.

## D117 — E2's design: two review rounds; 8 runs per method (a roadmap amendment)

E2's design (`docs/E2/DESIGN.md`) went to Astra 6 and Fable 5.1 twice.
- **v1** (`docs/reviews/20260929-100947-E2-design/`): both "revise". The ES was under-specified in
  ways that could make it lose for trivial reasons (learning-rate units, a start on the zero plateau,
  tied integer fitness, clamping, weight decay); random sampling's champion rule discarded 96% of its
  samples; the runtime figure contradicted E1's record; the tuning pilot selected on noise; 3 runs were
  too few; the ENOMAD summary had two errors (signed initial weights; not a working controller).
- **v2** (`docs/reviews/20260929-101958-E2-design-v2/`): Fable "proceed to pre-registration", Astra
  "revise": the ES's formal length was miscounted (625, not 780), the allowance and the ES update not
  complete, the decision rule inconsistent (only the ES can be chosen), and the roadmap amendment
  claimed but missing.
- **v2.1** takes all of it: the allowance defined (622 formal ES generations after the pilot and the
  start screens), the ES update complete (a flat batch changes nothing, including Adam's momentum,
  tested after real updates), the decision rule completed (an incomplete GA blocks a decision; random
  sampling within 0.5 of the GA triggers the roadmap's diagnosis first), a descriptive extension of the
  ES to 1 000 generations, and **the roadmap amended: 8 runs per method, no ARS.**

The ES and random sampling are implemented test-first (`wormwars/e2/optimizers.py`, 13 tests; the tie
rule and the flat-batch rule sabotage-checked).

## D118 — E2 design v2.2; on to the pre-registration

The v2.1 confirmation (`docs/reviews/20260929-102907-E2-design-v21/`): **Fable "proceed to
pre-registration"; Astra "revise", for specification corrections only** ("not a request to
redesign"): generation labels consistent with the arithmetic, checkpoint validations inside the
allowance (which still gives 622 formal ES generations: 2 131 712 episodes against the GA's 2 131 968),
and the "keep the GA" wording. Fable added loop-level points (project only after a real update, finite
scores, within-pair ties, start-screen ties, an incomplete random batch, the extension's state and
scoring).

All are taken in design v2.2's last section. The one code gap, a batch tied within every antithetic
pair moving the mean through Adam's momentum, is fixed test-first (the test failed, then passed; 14
tests). Since both reviewers review the pre-registration, which carries these specifications, the next
step is the pre-registration rather than another design round.

## D119 — E2's pre-registration v1: the loops, the runner, and three choices beyond the design

E2's code is written test-first: the batched loops for random sampling and the ES
(`wormwars/e2/loops.py`, 15 tests) and the runner (`scripts/e2.py`, 46 command tests with fake
rollouts), each rule sabotage-checked (12 deliberate breaks, each caught by its test). One CPU smoke
run of the whole chain, with real rollouts at smoke sizes, completed. The GA runs through 04a's
`evolve_batch` unchanged; a test compares E2's call with a direct call on 04a's configuration.

Three choices go beyond design v2.2; the pre-registration lists them (§13) for review:
- **Paired starts:** run r of every method shares run seed 1 120 000 + r, so all three methods start
  from the GA's own generation-0 population on the same world schedule. This removes start-to-start
  variation from a comparison of only 8 runs per method.
- **"Final" for a training stage that stops twice,** so an incomplete GA or random-sampling batch
  reaches the decision rule's "no decision" or "not made" branches instead of halting E2.
- **No mechanical reduction after an over-limit projection:** the generations are tied to the
  allowance, so any change needs a reviewed amendment.

Id block 995 000 000-995 999 999, unused by any earlier experiment (a test checks). The
pre-registration goes to Astra 6 and Fable 5.1 before binding.

## D120 — E2's pre-registration v2: failure handling, outcome wording, and exposure corrections

The v1 review (`docs/reviews/20260929-105911-E2-prereg/`): **both "revise"**, no redesign; both
accepted the three choices beyond the design (D119).
- **Both found that a kill broke "final"** (`scripts/e2.py`, `require_earlier`): finality needed an
  archived record, which a killed first attempt does not leave, and a killed rerun left no record at
  all. Now a rerun counts as used once applied, and one more `--rerun` after a killed rerun charges
  it and writes a final, not-completed record from the marker and the last partial record. All four
  crash/kill combinations are tested.
- **Both asked for a distinct outcome for an incomplete ES,** instead of "did not satisfy both
  criteria". Added, with "unshaped fitness" in every decision sentence (the design had promised it).
- **Astra:** a stopped extension lost its champions; the hold-out's arms were not durable across a
  kill; §8 lacked outcomes for an over-limit projection, a stopped pilot or evaluation. All fixed and
  tested.
- **Astra corrected §11:** the development smoke projection used E2's projection seeds (1 129 000-
  1 129 002), and the smoke controls did not score 0. Verified in `runs/e2-smoke/`. The formal
  projection seeds move to 1 129 100, smoke projections get their own (1 128 900).
- **Fable:** the budget's 10 s per checkpoint is 04a's planning figure, not a measurement (04a
  measured about 3.3 s); relabelled, with about 4.7 GPU-hours at the measured rate beside the 5.0
  upper estimate. The ES's registered constants were not read by the code; a test now pins them.
- Suggestions taken (Fable, Astra): the pilot's ties go to the middle setting (σ 1, rate 0.3 σ) and
  an all-tied stage is flagged uninformative; the flat count is current at every checkpoint; a plain
  sha256 for the binary state file; the extension's 42 checkpoints disclosed; incomplete batches'
  champions evaluated and labelled; the procedure-level caveat; a pairing check and per-run
  differences; 03's timing ids (990 million) in the disjointness test; a README.
- **Found while fixing:** Windows refused an atomic replace when the new per-arm partial record was
  rewritten in quick succession (a `PermissionError` in the suite, intermittent). Atomic writes and
  file replaces now retry briefly; tested.

Each fix was test-first (14 new tests seen failing), and each new rule was sabotage-checked
(8 deliberate breaks, each caught). Tests: 62 command, 16 loop, 14 optimizer.

## D121 — E2's pre-registration v3: a recoverable rerun setup, the extension's champions on every path

The v2 review (`docs/reviews/20260929-113044-E2-prereg-v2/`): **both "revise", narrowly**; all of
v1's must-fixes were confirmed resolved.
- **Astra: the rerun's own setup could deadlock or consume the rerun falsely.** A kill between the
  note and the rerun's marker left neither record nor marker; a refusal between archive moves let the
  first attempt's marker be taken for a killed rerun. Fable found the second through the bare
  `os.replace` in `apply_rerun` and `reconcile_kill`. Now the note is written first ("archiving") and
  marked "applied" after the last move, markers carry their attempt number, an interrupted setup is
  continued by the next `--rerun` without charging the first attempt again, and every move retries.
- **Both: a killed or early-stopped extension could lose its champions,** or have them evaluated but
  missing from the summary. Now the fallback champions are in the first partial record, a killed
  rerun without one rebuilds them from the formal record, and the summary is built from the
  champions, with their source.
- **Fable: the ES's generation-0 candidate was the decoded start**, not bit-identical to the start
  genome, so the pairing check reported a match that was not one (in the smoke run: `7a9bafed…`
  against the GA's `b6767851…`). Generation 0 now validates the start genome itself; in the third
  smoke run all three methods' generation-0 candidates are `b6767851…`.
- **Fable: §11 missed a smoke chain.** There were two (08:54 with v1's code, 09:29 with v2's), and
  the second overwrote the first's records; §11 now names both, with a dated correction. A third ran
  with v3's code at about 09:52 UTC (the same smoke folder, smoke seeds, CPU).
- Suggestions taken: the extension is skipped when the cap's remainder must be kept for the
  evaluation (0.5-hour reserve; Fable); `final` on a stopped rerun; stage records' `outcome`
  explained; `replace` and the pairing tested directly; the pilot's stage-2 time scaled.
- Not taken: guard-on tests of reconstructed records (Astra); the guards need a clean, pushed tree
  and CUDA, and a reconstructed record keeps its own attempt's provenance.

Each fix was test-first (12 new tests seen failing), except one regression pin, "setup interrupted
before anything moved", written after the fix when a sabotage check ("used" without "applied") went
uncaught; it fails under that sabotage. Nine deliberate breaks in all, each caught. Tests: 75
command, 17 loop, 14 optimizer.

## D122 — E2's pre-registration v4: the extension's skip rule, corrected

The v3 review (`docs/reviews/20260929-115339-E2-prereg-v3/`): **both "revise", about v3's new skip
rule only**; every v2 must-fix was confirmed resolved. Fable: "ready to bind" once its option (a) is
taken as written.
- **Both: "the extension never takes the evaluation's budget" was false.** The obligatory rerun is
  exempt from the check, and an admitted extension can overrun its projection. Fable showed a
  two-failure sequence at the planning figures that ends E2 at the cap. Taken as Fable's option (a):
  §6 now registers the check as an admission estimate for the first attempt, with the exemption and
  the remaining risk disclosed (Astra accepted this or a spending limit). The exemption is tested.
- **Astra: the skip record bypassed the commit check,** and **a plain run after a killed extension
  could be recorded as skipped**, dodging the obligatory rerun. Now the skip record carries its
  provenance and goes through the normal checks (tested with the formal guards on and git and CUDA
  stubbed), and a plain run refuses whenever a start marker exists, before any stage-specific rule.
- §10's definition of "final" includes the skip, and states once when a rerun counts as used.
- §11 names all four CPU smoke runs with their HEADs (the fourth at 10:07:57-10:08:29 UTC, with
  v4's code on `31beeda` plus uncommitted files).
- Suggestions taken: a killed extension rerun finalised from a real partial record, through the
  evaluation (both); the budget total (17 870 s); the README's decision range; a note on reading a
  flat ES run's hashes.

Tests: three of the four new tests were seen failing first; the fourth (the real partial record)
passed at once, confirming Fable's reading of the code, and was strengthened after its sabotage check
(the killed record ignoring its partial record) at first went uncaught: with fake scores, the
fallback champions equal the partial record's, so the test now also compares the carried
extension checkpoints. Four deliberate breaks, each caught. Tests: 79 command, 17 loop, 14 optimizer.

## D123 — E2's pre-registration bound (v4)

The v4 review (`docs/reviews/20260929-120935-E2-prereg-v4/`): **both "ready to bind"**, no
must-fix. Fable asked for two text corrections in the binding commit, and Astra suggested the same:
- **"Each test was seen failing first" was false.** D121 and D122 each recorded an exception.
  Checked again before binding, the exceptions were more than those two: **eight tests pinned
  behaviour the code already had and passed when written**:
  - D120: the ES's registered constants; the state file's plain sha256;
  - D121: `replace` retrying and giving up; a rerun setup interrupted before anything moved;
  - D122: the extension's rerun exempt from the skip rule; a killed extension's real partial
    record;
  - D123: the two binding-commit additions below.

  Each now fails under a sabotage, checked before binding (a 15-pair ES; the text hash for the state
  file; no retry; "used" without "applied"; no exemption; a killed record ignoring its partial
  record; the skip record returned before the guards). **The sha256 pin was vacuous:** the state
  file holds no CRLF pair, so the text hash gave the same value. The binding commit gives it bytes
  that hold one. The pre-registration's claim now lists the eight.
- **A comment in `scripts/e2.py` repeated v3's "never"** about the evaluation's budget; corrected to
  §6's admission estimate.
- **The fourth smoke run's start** was 10:07:59 by the marker and the accounting, not 10:07:57.

Test-only additions both suggested:
- an extension checkpoint forced to beat every formal one, killed twice after its partial record,
  followed through finalisation and evaluation by hash and source;
- the guards accepting a skip record from the same code and environment, and refusing one from
  other code or another environment. The stubs target the skip record alone: at first they matched
  every smoke record, which share one commit, and could not have told a bypass from a refusal
  elsewhere.

No rule changed. **The order after binding** (Fable): push; a guarded smoke run of every stage on the
binding commit, before the formal projection, which runs once; then the projection and the formal
stages. Tests: 83 command, 17 loop, 14 optimizer.

*Noted at binding:* the first full-suite run on the binding tree failed once in 03m's
`tests/test_p4m.py` (`test_the_lesion_follow_up_keeps_its_finished_deletions_on_a_stop`): the same
transient Windows `PermissionError` on `os.replace` that E2's writes now retry (D120). The rerun
passed in full. `scripts/p4m.py` belongs to the published 03m and E2 does not use it; retrying its
replaces is a separate change, left for later.

## D124 — E2's results: keep 02's GA; the floor fires

The formal chain ran from 10:38 to 15:20 UTC on the binding code (`60af3cf`), once, with no stop,
rerun or amendment: 4.74 GPU-hours against a cap of 7. Outcome, in the registered wording: **"E2:
keep 02's GA (unshaped fitness; the ES did not satisfy both replacement criteria after paying for its
tuning)"**. The ES's mean was 2.086 against the GA's 1.961 (+0.125, 0.5 needed); 5 of its 8
champions were above the GA's median (6 needed). **The floor fired:** random sampling's mean,
1.605, is within 0.5 of the GA's (−0.356), so the roadmap's diagnose-first rule applies and takes
precedence over proceeding to E3. The extension (descriptive) reached 2.331, rising, on about 38%
more episodes than the GA.

`RESULTS.md` was written after the chain finished, from the committed records. A check of every
number against the records before committing found five slips in the draft (two ranges read from a
subsample of checkpoints, ES run 2's flat generations, the last random-sampling candidate's pool,
and the training hours); all were corrected before the first commit. The results go to both
reviewers; the next step, the diagnosis, gets its own design and review.

## D125 — E2's results reviewed: "fix" (text only), corrections dated

The results review (`docs/reviews/20260929-172345-E2-results/`): **both "fix"**, text corrections
only; no rerun or rework. Both independently recomputed the decision from the per-world counts and
confirmed it: the ES led the GA by 0.1246, 5 of its champions were above the GA's median of 2.1309,
and random sampling minus the GA was −0.3562. Both registered sentences are correct.

The corrections (RESULTS.md, "Corrections (2026-09-29, D125)", quoting the original text, which
stays):
- **The floor's interpretation overclaimed** (both). "1 000 generations of either optimizer add
  little" was wrong: the compared ES ran 623 generations. The gains over random sampling were 22%
  (GA) and 30% (ES), and paired by run, the GA beat random sampling in 7 of 8 runs and the ES in all
  8. The floor is a trigger, not a finding. **Its sensitivity:** it depends on the GA's run 2; without
  that run the gap is −0.495, and by medians −0.540.
- **Run 2 carries all of the ES's lead, and more** (both), not "most".
- **The extension does not show a budget effect on the outcome** (both): at 1 000 generations the ES
  still misses the margin (0.37 against 0.5).
- **The GA's late drift is mostly one run** (Fable).
- **The GA's run 2 and the cue** (Astra): only its champion was probed, and it showed little
  aggregate advantage from the cue; "does not depend on the cue at all" overstated it.
- **Two figures** (1.50 and 16 630 s), **the ledger's source** (the per-attempt accounting files were
  not committed; they now are, in `compute-attempts/`), and **the binding commit** (the registration
  defines it as the one the projection records, `69f4163`: `60af3cf` plus the guarded smoke's
  development record, with every guarded file identical).

**A correction to D124,** quoted: *"The formal chain ran from 10:38 to 15:20 UTC on the binding code
(`60af3cf`)."* The formal projection started at 10:34:39 and is part of the 4.74 GPU-hours; 10:38 is
pilot stage 1's start. The binding commit, as defined, is `69f4163` (above). D124 also said "five
slips" were fixed before the first commit. That stands; the review found further ones, listed above.

**For the diagnosis the floor requires** (the reviewers' advice, to be designed and reviewed
separately):
- **Fable:** noise first, from the existing records and without a GPU: the standard error of an
  8-world training mean, from `per_world_counts`. Then search against selection (random sampling
  gets 41 independent nominees), the plateaus (six GA champions at 2.11-2.21, beside M-avg's 2.20;
  a second level near 0.7), and budget last, crossed with worlds per genome, on new worlds.
- **Astra:** noise and nomination (re-evaluate fixed genomes and antithetic pairs on independent
  8-world blocks; rank stability, ties); saturation (trajectories and sensor-to-motor responses of
  strong champions and of the GA's run 2); budget (matched-work comparisons with fresh worlds,
  including smaller σ, since the pilot chose its grid's edge).

**Publication:** both said the results are publishable once corrected. They go to main under the
owner's consensus rule (D112).

## D126 — E2 published on main

Under the owner's rule (D112), with both reviewers' fixes applied (D125), main was fast-forwarded
from `1c0c978` to `8ad636b`: the roadmap branch at `3898460` plus one commit removing its banner. It
carries E2 (the design and its three review rounds; the pre-registration and its four; the code and
tests; every stage record, the accounting's attempt files, RESULTS.md with its dated corrections, the
README), D117-D125, and the front page, roadmap and review trail updated. Checks: the full suite
locally at binding, CI green on every E2 commit through `3898460`, the publication hygiene tests, and
the identity check. The next step in Track E is the diagnosis E2's floor rule requires, before E3.

## D127 — E2d: a plan to diagnose Task N (for review)

E2's floor fired, so the roadmap requires a diagnosis of saturation, noise and budget before E3.
`experiments/E2d-taskn-diagnosis/PLAN.md` (v1, exploratory) sets it out in three parts:
- **Part A** reads E2's committed records only. With 8 shared worlds, two genomes 0.05-0.15 targets
  apart are ranked correctly 62% of the time. Nominees lose 0.19-0.33 from training to validation.
  The GA's population averaged 0.54 against a best of 1.92. The champions cluster at M-avg's level
  (2.20), E1's best temporal controller.
- **Part B** asks whether the 48 champions of E2 and 04a use the left-right difference. It uses the
  `mean` and `swapped` stereo ablations, with S-const and M-avg as checks.
- **Part C** runs three one-change arms of 8 runs each, compared on a common hold-out: 32 worlds per
  genome, halved mutation, and σ 0.25 for the ES.

The readings are fixed in advance as descriptive thresholds, under a cap of 5 GPU-hours. The plan
goes to Astra 6 and Fable 5.1 before any code or GPU work.

## D128 — 03m's script retries its file replaces

The transient Windows `PermissionError` on `os.replace`, which failed one 03m test once at E2's
binding (D123), is fixed in `scripts/p4m.py` as it was in E2's runner (D120): a bounded retry
(`replace`) in both atomic writes. It is file handling only; 03m's computations, records and
results are unchanged. Test-first: `test_the_atomic_writes_survive_a_transient_permission_error`
failed, then passed.

## D129 — E2d plan v2: paired with E2's runs; readings narrowed; Part A committed

The v1 review (`docs/reviews/20260929-175712-E2d-plan/`): **both "revise"**.
- **Part C's comparisons were unpaired** (Fable: 04a's unshaped GA runs averaged 2.37 against E2's
  1.96 with nothing changed). v2 reuses E2's run seeds, training range and validation ids, so each
  arm's run r is paired with E2's run r. E2's runs are the controls, and no control arm is rerun.
  Checked: a 32-world draw for a run and generation begins with that generation's 8-world draw.
- **C3 changed two settings** (both); its learning rate is now kept at 0.15.
- **C1's fewer checkpoints are now matched** (both): E2's champion is re-chosen among the 11
  checkpoints at the same fractions of work, at equal selection episodes.
- **Arms added:** C4, 32 worlds with halved mutation (Fable). C0, a probe of how reliably 8 worlds
  rank siblings and antithetic pairs, the comparisons selection actually makes (Fable, Astra).
- **Part B's reading is narrowed** (both): "non-stereo", not "temporal"; three classes with
  intervals; per-set counts, with the genome shared by ES run 6 and extension run 6 counted once;
  a low-gain stereo reference; check tolerances. **Budget gets a reading**, the paired formal
  against extended ES (both). **"The optimizer is not the bottleneck" is removed** (both).
- **Part A** is now `scripts/e2d_records.py` → `part-a.json`, with `tests/test_e2d_records.py`.
  That test was written after the script: it is a pin, and it was sabotage-checked. One of its
  checks at first missed a sabotage (scaled rates) and was strengthened to pin absolute values.
  Counting the shared genome once gives 74, 113 and 106 pairs, not 80, 122 and 110. Ties are
  stated: at k = 8, strictly correct 0.54, tied 0.16. Two wrong statements are corrected: "all eight
  of the ES's", and "where most candidates sit".
- The cap rises from 5 to 7 GPU-hours (C0 and C4), with a projection limit of 6.2 hours and a
  reserve for the hold-out pass.

## D130 — E2d plan v3: the controls replayed, run 2 isolated, the reserve enforced

The v2 review (`docs/reviews/20260929-181658-E2d-plan-v2/`): **both "revise", narrowly**. Both
found the pairing with E2's runs sound; Astra regenerated Part A's output exactly. v3 takes every
point:
- **Run 2** (Fable): E2's GA run 2 started from an all-zero population and ended at 0.75, so it
  alone can carry an arm's mean. Readings are drawn over 8 runs and over the 7 without it.
- **The controls are replayed** (Fable): E2's GA and ES, generations 0-25, must reproduce E2's
  committed hashes before Part C starts. Each arm also records a pairing check.
- **Part B** (both): the classes and set rules are completed; the k = 4 stereo steerer is pinned
  (speed 1.0, turn 0.1; it scored 2.18 in 04a, at the champions' level).
- **Budget** (both): E2's hold-out already shows the extension ahead in all 7 distinct pairs
  (mean 0.28), yet v2's "6 of 7 at 0.2" rule would not have fired; a mean-gain rule with
  intervals replaces it, and the prior figures are disclosed.
- **The combined arm** (both): an interaction only from the difference-of-differences, at matched
  checkpoints.
- **The reserve** (both): admission applies to reruns too, and training stops hard at 6.5 of the 7
  GPU-hours.
- **C0** (both): specified in full.
- Three of Part A's table cells are corrected (both).

## D131 — E2d plan v4, agreed

The v3 review (`docs/reviews/20260929-182751-E2d-plan-v3/`): **both "revise", text only**. Both
confirmed every v2 must-fix resolved. Both found the same two contradictions in C0: the seed table
added a scale index that C0 itself ruled out, and C0 claimed its tie rule matched E2's sort, which
is an unstable `argsort` (Astra reproduced a tie on which they differ). Fable: "If both are taken
as written below, I need no further round." Astra: "Two small C0 corrections remain before
implementation."

v4 takes both corrections as written, and the suggestions:
- C0's bins and complements defined;
- the replay run twice, to tell engine drift from default-mode nondeterminism;
- the budget rule's expected result stated;
- the incomplete-contrast rule, the deciding interval, run 2's two-way rule everywhere, and the
  fixed band.

**The plan is agreed.** The runner (`scripts/e2d.py`) is written test-first against it and goes to
both reviewers, as code, before any GPU work.

## D132 — E2d's runner, for review before any GPU work

`scripts/e2d.py` implements PLAN.md v4. It reuses E2's stage frame by importing `scripts/e2.py` and
pointing it at E2d's folders, stages, outcome wording and registered numbers: markers with attempt
numbers, the cap, reruns, not-completed records, retried atomic writes. It adds the admission rule
for reruns, the 6.5-hour training clock, and the replay gate.
- **Tests:**
  - `tests/test_e2d_analysis.py` (the registered rules as pure functions): written before the code,
    but first run only after it existed;
  - `tests/test_e2d_commands.py` (the stages, with fakes, against E2's and 04a's smoke chains
    generated in a scratch folder).
- **Sabotage checks:** twelve deliberate breaks, each caught by its test:
  - two-sided classes;
  - unclear not counted as non-stereo;
  - the run-2 rule;
  - the interaction rule;
  - the tie rule;
  - the complement exclusion;
  - the same noise at every scale;
  - the replay gate;
  - admission for reruns;
  - the hard stop;
  - Part B's de-duplication;
  - the hash check.
- **Found while testing:**
  - two of the analysis tests were wrong as first written, and were fixed before the code existed;
  - the pairing check hard-coded 8 worlds (twice);
  - E2d's records would have carried E2's outcome wording.
- **A CPU smoke run with real rollouts** reached the replay. Part B's reference check failed at 40
  ticks, and the replay reported drift against the CUDA-made smoke sources; both are the designed
  responses. The full chain runs in the guarded CUDA smoke, after review.

## D133 — E2d's runner, fixed after its code review

The code review (`docs/reviews/20260929-185027-E2d-code/`): **both "fix"**; both found the rules
implemented faithfully and the frame reuse safe. The must-fixes, all taken:
- **A capped arm blocked every later stage, the hold-out pass included** (both). The cap outcome is
  now final under `final_ok`.
- **An incomplete arm got a normal reading** (both; Astra reproduced a stopped C2 read as "supports",
  with an interaction claimed). Only completed arms are evaluated and read. C2′ needs every matched
  checkpoint. Contrasts need their arms completed.
- **A failed Part B check did not propagate** (both; Astra reproduced it). Set readings are "not
  drawn", and Part C's plateau rule falls back to scores, recorded.
- **Arm records carried the base configuration** (both). They now record the arm's own, with the base
  hash beside it.
- **A failed pairing check did not block the paired readings, and the generation-249 check compared
  two regenerated schedules** (Astra). Failed pairing now blocks the readings. The check uses the ids
  actually played, captured at the rollout, and the run roster.
- **C0's reference uncertainty was SD/√248, not the plan's bootstrap** (both). It is now a bootstrap:
  1 000 resamples, seed 0, recorded.
- **The projection ignored what was already spent** (Astra). The limit now applies to the total.
- **Promised outputs were missing** (both), and now added:
  - the per-genome contrasts of the arms and of the matched references;
  - E2's registered champion beside C1's and C4's matched one;
  - a statement where the interval and the sign-flip test disagree;
  - the budget reading's costs and curves;
  - the pooled distinct-genome count and the three named genomes;
  - the ES mean's score in C0.
- **A missing 04a record now fails outside smoke,** and the plan's denominators are asserted (31, 12, 4)
  (Fable).
- **Also:** the replay compares validation counts, the logged best genomes and the configuration hash;
  the source records' hashes go into every record; smoke C0 gets its own seeds.

**Tests:** 13 of Fable's "passes with the rule broken" gaps are now pinned. Thirteen more deliberate
breaks were each caught, three only after their tests were strengthened:
- an exact reason, where a second guard gave the same "not drawn";
- a spent figure far enough from the limit;
- a budget example whose mean really is at the threshold.

The Task N probe test passed on the unchanged code, so it is a pin of real behaviour.

## D134 — E2d's runner, confirmation round: Fable "run"; Astra's review failed and is retried

The confirmation review (`docs/reviews/20260929-191508-E2d-code-v2/`):
- **Fable: "run".** All eight must-fixes are resolved, and the fixes introduced no new defect. Two
  tests still could not fail when their rule broke; both are test-only, to close before the formal
  stages.
- **Astra's review failed** ("Selected model is at capacity"). There is no consensus until Astra
  answers, so Astra is asked again on the current code.

Taken:
- **Fable's two must-fixes:**
  - `pairing_check` is now tested directly on its own inputs: a later strain playing another world,
    a changed roster with nothing else changed, and a changed generation-0 hash. The check now
    compares every strain's row, not only each run's first;
  - Part B's fallback is pinned by behaviour: champions that use the difference but score 2 leave
    the plateau only while Part B's checks pass.
- **Most suggestions:**
  - `boot_se` is pinned against an independent recomputation;
  - both of C0's reading branches are tested (material, and declined under the minimum);
  - C0 records its seeds, which are tested;
  - Part B loads and checks every champion, and the plan's denominators, before its start marker,
    so a failure there cannot spend its rerun;
  - the training-clock test writes only to a scratch folder;
  - recorded paths use forward slashes.
- **Recorded before Part B, as Fable asked:** the budget reading is drawn even if a Part B check
  fails. It uses only the `real` probe, so the reference checks do not bear on it.

**Sabotage:** five breaks. Four were caught at once. The fifth, the roster check, was missed at first,
because reversing the runs also broke the generation-0 comparison. A test that changes only the run
number now catches it.

Four of the new tests passed on the unchanged code, so they are pins: the plateau behaviour, boot_se,
C0's reading and the training clock. Each fails under its sabotage.

## D135 — E2d's runner agreed; the guarded smoke next

Astra's retried review (`docs/reviews/20260929-192702-E2d-code-v3-astra/`): **"fix", with one
test-only must-fix, and "the guarded smoke can proceed"**. All eight original fixes were present
and no new runner defect was found. The must-fix: Astra removed the comparison of the played ids
with the 8-world draw, in memory, and the strengthened test still passed. A test now shifts every
strain of one run identically, with the roster and generation 0 unchanged, and it catches that
removal.

Two suggestions are also taken:
- the recorded last ids are compared with the fake's last training call;
- a completed C2 with a missing matched checkpoint gets no C2′ and no interaction.

The C2′ rule and the prefix comparison were each sabotage-checked.

**With Fable's "run" (D134), both agree.** The plan is PLAN.md v4; the runner is at this commit.
Next: the guarded smoke of every stage on CUDA, then the formal chain.

## D136 — E2d's results: a non-stereo plateau that no tested change leaves

The formal chain ran from 17:37 to 21:32 UTC on the agreed runner, once, with no stop, rerun, skip
or amendment: 3.90 GPU-hours of a 7-hour cap.
- **The controls' replay reproduced E2 exactly,** twice.
- **Part B: "a non-stereo plateau".** No champion of E2's or 04a's 47 uses the left-right difference,
  while a low-gain stereo steerer at the same score (2.27) is detected.
- **The budget reading:** "budget-limited" (+0.24).
- **C0:** "not material by this rule", narrowly (0.82 against 0.8). Mutation at 02's scale leaves 78%
  of children under half their parent's score.
- **Part C:**
  - C1 is inconclusive;
  - C2 and C4 "support, carried by run 2";
  - C3 is inconclusive; its run 2 never left zero at σ 0.25;
  - no arm leaves the plateau, and no interaction is claimed.

Writing up, a check of every number against the records found three errors in the first draft, all
corrected before the first commit:
- the projection's estimate (3.86 hours, not 5.1);
- a false claim that the 32-world arms ran at a third of their projection;
- run 2's score on these worlds (0.69; 0.75 was on E2's hold-out).

The results go to both reviewers. E3's design then faces the plan's question: make stereo steering
reachable, or build on the non-stereo module knowingly.

## D137 — E2d's results reviewed: "fix" (text only), corrections dated

The results review (`docs/reviews/20260929-233515-E2d-results/`): **both "fix", text only**. Both
recomputed every registered reading and confirmed it; no rerun. Corrections are in RESULTS.md,
"Corrections (2026-09-29, D137)", quoting the original text, which stays. In brief:
- **"Near its ceiling" is withdrawn** (Fable): the plan says no ceiling is established, and the ES is
  budget-limited.
- **"Basin" and "why random sampling came close"** were not measured (both).
- **The scripted stereo steerer shows the probes' sensitivity,** not reachability (both).
- **The mechanism wording** is narrowed to the plan's criterion (Astra).
- **Added:**
  - the sign-flip p-values, with two disagreements stated (C1, the interaction);
  - the interaction without run 2;
  - run 2's shares (C2 50%, so "most" was false);
  - the narrow margins (C4 at 0.304, 04a's unshaped set at exactly three-quarters);
  - C0's per-champion rates, and the pooled rate below 0.8 at the gentler scales;
  - the ledger's total (14 036 s).

**A correction to D136,** quoted: *"No champion of E2's or 04a's 47 uses the left-right difference."*
Too absolute: no champion meets the plan's "uses the left-right difference" criterion (43 show no
material benefit, 4 small ones).

**Advice for E3 from both reviewers** (not decisions):
- **Settle whether stereo steering is expressible first,** for example by building or imitating a
  low-gain stereo N2 genome, confirming it with Part B's probes, and evolving from it (Fable).
- **Keep the probes as a standing measure** along training (Fable).
- **Do not adopt halved mutation or 32 worlds as defaults on this evidence.** Retest gentler mutation
  with fresh paired seeds (both).
- **Declare the handling of all-zero starts in advance;** they decided four readings here (Fable).

**Publication:** both said the results are publishable once corrected. They go to main under the
owner's consensus rule (D112).

## D138 — E2d published on main

Under the owner's rule (D112), with both reviewers' fixes applied (D137), main was fast-forwarded from
`8ad636b` to `df50f6a`: the roadmap branch at `f832f18`, plus one commit removing its banner. It
carries:
- E2d: the plan and its reviews, Part A's script and output, the runner and its tests and code
  reviews, every stage record, the accounting's attempt files, RESULTS.md with its dated
  corrections, and the README;
- D127-D137, and 03m's script retry (D128);
- the front page, the roadmap, the review trail (episodes 22-24), AGENTS.md's layout, and the
  03a, 03m and E2 README statuses.

**Checks:** the full suite, locally on the code that ran; CI green on every E2d commit through
`f832f18`; the identity check.

The GPU is paused at the owner's request (2026-09-29, about 21:50 UTC). The next step, E3's design,
needs no GPU until its runs.

## D139 — E4s: a hand-built stereo module, ahead of plan (the owner's decision); design v1

**The owner, 2026-09-30:**
- E4s ("E4-stereo") is a preliminary version of E4's hand-building, run now because E3 needs a
  navigator that steers by the smell's side, and evolution has not found one (E2d's "non-stereo
  plateau").
- The design is two noses and a ring attractor borrowed from the fly, whose active region biases
  turning left or right; then evolution optimises the whole brain.
- Removing neurons one by one to the minimal circuit is later work (E3 or E4).
- **The owner set a ceiling of 96 GPU-hours for E4s.**
- The steps are:
  1. a deep literature research by Claude Sonnet 5.5 through the CLI;
  2. a design, taken to Astra 6 and Fable 5.1;
  3. if both agree, a pre-registration and a roadmap amendment, open about the plateau and the
     missing stereo smell.

**Done:**
- **Sonnet 5.5's research is archived in `docs/E4s/`.** The CLI was updated to 2.1.285 first; the
  earlier version did not know the model. Its numbers taken from this repository were checked against
  the code before use: the scent scale, the turn readout and mapping, E1's gain curve, signed sensor
  gains, and the `hold` probe.
- **An open-loop gain probe of the 47 distinct champions** (exploratory, design-informing):
  - Method: `scripts/e4s_gain_probe.py`, output in
    `experiments/E4s-stereo-module/development-records/`.
  - Result: a median effective stereo gain |k| of about 0.1 (at most 0.68), against E1's scripted
    k ≈ 4 at the champions' score and about 256 at 8.5.
  - It supports the report's hypothesis that the plateau is a gain problem. It is open-loop, not a
    registered measure.
- **Design v1** (`docs/E4s/DESIGN.md`):
  - the modules: the ring M2 (about 30 neurons) and a 4-neuron core M0;
  - the graft as new code (the brain and world code already handle any neuron count);
  - Stage A: a module-alone positive control, with a gate;
  - Stage B: evolution with four arms, including an inert-module control and a graft onto 04a's
    chosen module;
  - a proposed cap of 24 GPU-hours within the owner's 96.

It goes to Astra 6 and Fable 5.1.

**Noted:**
- The owner expected neurons could already be added but not removed. In the code it is the other way
  round: deletion exists (`wormwars/deletion.py`) and addition did not. The graft functions add it.
- The owner asked for "Sonnet 5.5"; the older CLI rejected it, and the updated one runs it.

## D140 — The graft functions (E4s), test-first; an inert graft is equivalent only to rounding

`wormwars/graft.py`, written while E4s's design v1 is under review, because every variant of the
design needs it:
- `Module`, a hand-designed circuit;
- `graft_connectome`: the worm's 302 neurons keep their indices and masks, and the module's neurons
  are appended;
- `seeded_genome`: the background, random, a champion or silent, placed edge by edge, plus the
  module's designed values;
- `graft_interface`: the noses' entries, and the module-only probes "mean" and "swapped".

Tests: six in `tests/test_graft.py`, seen failing first.

**Sabotage:** four breaks. One, a misplaced background, was missed at first, because the toy
module's edges did not interleave with the worm's. A worm-to-module synapse (a turn copy) now makes
the placement matter, and the break is caught.

**Found:** an inert graft, one with no synapse onto the worm, is **not bit-exact** on the CPU:
- adding rows and columns regroups the floating-point sums;
- the worm's states then differ by at most about 1.4 × 10⁻⁶ over 300 ticks (a 30-neuron module,
  three seeds), which is rounding level, and the difference does not grow;
- the declared tolerance is 10⁻⁵.

**Design v1 said "exactly on the CPU"; that is wrong.** It goes into v2. The rule-7 check for E4s
must therefore be stated at rounding level, with the effect on episode scores measured.

## D141 — E4s design v1 reviewed: both "revise"; design v2; the gain probe extended; a correction to D139

**The review** (Astra 6 and Fable 5.1, xhigh; archived verbatim in
`docs/reviews/20260930-014518-E4s-design/`): both "revise". The main points, which both raised:
- **Stage A could not run.** With the 302 worm neurons silent, the forward command is zero and the wey
  cannot move (checked: `world.py`'s motor readout; forward uses AVB/PVC against AVA/AVD/AVE, which
  the module does not reach).
- **The GA was not covered.** `evolve_batch` hard-wires `initial_population` and `breed`, and
  `Genome.mutate` takes scalar sigmas (checked). A seeded start, per-block scales and a pinned control
  are engine changes, with equivalence checks.
- **The outcomes were biased toward "kept".** E2's champion rule can pick generation 0; the +0.5 over
  the inert control is nearly guaranteed by the gate and elitism; the lesion cost at generation 0 is
  capped by locomotion.
- **The gain ≥ 32 gate was invalid.** The probe's least-squares slope caps at 66.7 on its δ grid, and
  a zero start cannot see a latch.
- Astra, separately: the ring encodes normalised lateral contrast, not bearing; the turn copy is not
  the executed turn; v1's direct nose-to-readout path let M2 pass without its ring; the tuning grid
  lacked forward drive and turn bias (E1's k = 32 scores 5.63 with turn bias 0.2, and 4.23 without).
- Fable, separately: draw the initial populations on N2 and embed them; the hygiene guard would pass
  E4s genome files; the nose gain is not evolvable.

**Checked before adopting:** the forward readout, the GA's hard-wired initialisation and mutation,
`Genome.random`'s normalisation over all edges, the hygiene test's keys (302 and known labels), E2's
settings (8 worlds per strain, checkpoints every 25), and the grafted synapses' direction (pre → post,
by a direct simulation: a module synapse onto SMDDL drives SMDDL; the reverse edge drives the module).

**Done:**
- **Design v2** (`docs/E4s/DESIGN.md`) takes every must-fix of both reviewers, and most suggestions;
  its last section maps each item to its change. The chief changes: a declared carrier for Stage A; a
  generation-0 graft measurement; the final generation's best as the registered reading; exclusive
  outcome classes by E2d's criterion; per-parameter mutation scales and `evolve_batch` hooks with
  bit-identity checks; B3 pinned; M2 without a direct path; 16 runs for B1 and B3; two descriptive
  arms (the module at 02's scale; the module frozen); a proposed cap of 30 GPU-hours (estimate about
  16).
- **The gain probe, v2** (`scripts/e4s_gain_probe.py`): a small-signal central difference, a signed
  curve, a step transient, a reversal with the state carried over, and turn-neuron saturation, with
  provenance hashes. The median |small-signal gain| is 0.098 and the maximum 0.68, as v1 reported.
  138 of 141 genome-level pairs respond to a reversal; the other 3 are one bias-dominated genome with a
  response below 10⁻³.
- **Not taken:** Fable's suggestion to optimise N2's open-loop gain by gradient, which asks a separate
  question (gain against topology). It is proposed as a follow-up within the ceiling.

**Correction to D139 (2026-09-30).** D139 said of the gain probe: "It supports the report's
hypothesis that the plateau is a gain problem." That is too strong (Fable; Astra). Low gain is what a
non-stereo controller shows under either reading, so the probe is **consistent with** the hypothesis,
not evidence for it. Design v1 said the same, and also "All sit near 2.2" (35 of the 47 lie in
1.90-2.50, as E2d's correction states) and "by the temporal route" (not measured); v2 corrects all
three.

Design v2 goes to Astra 6 and Fable 5.1 for a second review.

## D142 — E4s design v2 reviewed (Fable "proceed", Astra "revise"); design v3; the engine changes; corrections to D141

**The review** (archived verbatim in `docs/reviews/20260930-020427-E4s-design-v2/`):
- **Fable 5.1: "proceed to pre-registration"**, conditional on ten must-fixes going into the
  pre-registration.
- **Astra 6: "revise".**

Both found:
- **O1's decision rules overlapped:** an interval on the mean, a threshold on the median. Nine runs at
  +0.6 and seven at −0.1 read both "supports" and "does not support".
- **O2's "eroded" overstated,** and its trigger was ambiguous.
- **Wrong counts:** M1 is 14 neurons, not 30, and the total is 334, not 332. The budget factor is
  1.22.
- **Stage A's grid was underestimated:** 20 × 3⁷ = 43 740 closed-loop candidates, several GPU-hours,
  not "about 0.5 h".

Fable also found:
- persistence contradicted the shifters under a turn bias;
- "no spontaneous bump" from an exact zero state cannot fail;
- the score-level tolerance was nearly vacuous on random genomes (which score about 0.03);
- **the gain probe's transient and reversal had no unchanged-input control, so they measured drift.**

Astra also found:
- **the three weak reversal cases are three different genomes, not one;**
- the shifter's computation was unspecified for signed tanh activity;
- a 45° calibration treats ψ as a bearing;
- a committed anatomical sabotage fixture would itself break rule 1.

**Checked before adopting:** the three genomes, from `gain-probe.json` (e2 GA run 3 at 0.02, e2
random run 6 at 0.08, 04a run 3 at 0.25); the counts; the grid size; the drift, by rerunning the probe
with controls.

**Corrections to D141 (2026-09-30):**
- D141 said: "138 of 141 genome-level pairs respond to a reversal; the other 3 are one bias-dominated
  genome with a response below 10⁻³." **Wrong twice.**
  - The three are three different genomes. I inferred "one genome" from their similar values
    without checking.
  - The measure had no unchanged-input control, so "respond" mixed the reversal with drift. Design
    v2's "That is a weak response, not a latch" is withdrawn with it.
- Design v2's "the median largest change after a step is 0.032" was mostly drift. Against a control
  that stays at δ = 0, it is 0.0012.

**The gain probe, v3** (`scripts/e4s_gain_probe.py`) adds:
- the controls: a step against staying at 0, and a switch against staying at +δ;
- a carried-state gain: median 0.096, maximum 1.60;
- the history effect against a zero start: median 0.033, maximum 0.33, which mixes history with slow
  settling;
- each turn neuron's activity.

**Design v3** (`docs/E4s/DESIGN.md`; the change map is its last section):
- **M2 is pinned:** every weight, τ and bias. Signed resting drives are kept uniform around the ring.
  The shifters are renamed by their gate (Pᴸ and Pᴿ), with v2's direction.
- **The claim is restricted:** a heuristic rotating memory, tested by cue-off and reacquisition probes
  across distances and bearings, with no rate target, and M1 as a pre-stated fallback.
- **A0 and A1 are restructured.**
  - The component checks run at turn 0, at each candidate's nose values.
  - A carried-state crossing check is added, and a seeded 10⁻³ perturbation for spontaneous bumps.
  - A stratified sample replaces "the deepest".
  - The grid is bounded at 2 160 + 972 + 10 closed-loop candidates.
- **A feedforward control** (M2 with the ring's recurrence at 0) is added, and **a freeze** is pushed
  before the gate.
- **O1:** one estimand, with ordered rules.
- **O2:** each run classified by its generation-0 best and its final best: retained, lost, acquired,
  never used, unclear. **O2b** adds performance retention.
- **Budget:** 17-19 h estimated, with per-stage caps; the 30 h cap is kept.

**The engine changes** (made while the reviews ran; test-first; every test was seen failing, and each
behaviour was sabotage-checked):
- `Genome.mutate(..., scales=)`: per-parameter factors on the sigmas. Four tests; two sabotages caught
  (scales ignored; the random stream changed).
- `evolve_batch(..., initial=, mutation_scales=)`, with `breed(..., scales=)`. Four tests; two
  sabotages caught (each hook ignored).
- **`graft.py`:**
  - the genome is now built through `with_params`, and Dale's law is refused (a new test);
  - `MODULES` and `worm_parameters` added for the hygiene guard;
  - a synapse-direction test, which fails under the legacy reversed direction.
- **The hygiene guard** now checks grafted genomes (their worm block, by edge identity), refuses an
  unregistered grafted label, and flags square matrices wider than 302.
  - Its sabotage check builds the genome in memory; no anatomical fixture is committed.
  - **The first version of the test did not catch its sabotage.** The toy module has no gap
    junctions, so `g` fired anyway. It now requires the offence on `w`, and catches it.
- `scripts/e4s_equivalence.py`: E2's GA, generations 0-25, on the GPU, against E2's committed hashes.
  It runs before any E4s stage.

**Found, and corrected in the open:** the T0 guard `test_no_genome_is_built_by_hand_in_the_library`
had failed since D140's commit (1b628be). `graft.py` built a `Genome(...)` by hand, and at D140 I ran
only the graft tests, not the full suite. The genome is now built through `with_params`. D140's "Tests:
six … seen failing first" stands, but its commit did not have a green suite.

Design v3 goes to Astra 6 and Fable 5.1 for a third review.

## D143 — E4s rethought after a literature review; the Sonnet report corrected; a roadmap proposal reviewed

**Correction (2026-10-01).** D139 said: "Sonnet 5.5's research is archived in `docs/E4s/`", and the
designs called it "a deep research". **It was not.** It was a single CLI session, `claude -p` with web
search allowed. Its report marks 57 claims as seen only in a search snippet or a page extract, and
nobody checked its claims. It also missed obvious prior art, Braitenberg vehicles among it. I designed
E4s v1-v3 on it without flagging that to the owner.

The owner: "We do need a literature research before going forward because it is a big step and
Sonnet did not do it. So the decisions we took were based on a wrong assumption."

**The literature review** (`docs/reviews/20261001-literature-review/`, f1ffd50):
- the prompt was written by Claude Opus 5.5 at the owner's request;
- the owner ran it with Claude Opus and with Astra 6;
- both reviews are archived verbatim, with the points where they disagree.

**The owner's decision:** option (a). The bilateral left/right scent stays, as an explicit
game-design choice, not a biological claim.

**A roadmap proposal** (`docs/E4s/ROADMAP-PROPOSAL.md`; v1 cc13ff8):
- E4s-0, exploratory diagnostics;
- E4s-1, a comparator graft under evolution, pre-registered;
- E4s-2, the ring, deferred to a memory task;
- additions to E3 and E4.

**The review of v1** (`docs/reviews/20261001-roadmap-proposal/`): both "adopt with changes". Fable 5.1
ran at effort "high" to save the owner's Claude budget; Astra 6 at "xhigh". Proposal v2 takes every
must-fix.

**Found by Fable and checked:** design v3 stated the world's turn as clamp(2·[…]). The factor is 1
(0.5 × `turn_gain` 2.0, in `world.py` and E1's freeze), so v3's gain estimates halve. The gain probe
used the correct formula.

**Both rejected:** the Opus review's "gain ceiling" explanation of the plateau. A bound on one short
path does not bound a recurrent network, and it does not explain a measured gain of about 0.1.

**Design v3** is committed as superseded (60bc85e). A dated note in it records:
- that the Sonnet report was not a deep research;
- the turn-readout error;
- that the ring is deferred.

Its engineering is reused by E4s-1.

Proposal v2 goes to Astra 6 and Fable 5.1 for a confirmation round.

## D144 — The E4s plan adopted (proposal v2.1) and the roadmap amended; the GPU engine gate passed

**The review of proposal v2** (`docs/reviews/20261001-roadmap-proposal-v2/`): both "adopt with
changes". Fable added that none of its items needed a new design round. Both found:
- **E4s-1's outcome table had dropped "acquired":** a run whose generation-0 best does not use the
  module but whose final best does.
- **Several details were unpinned:** R's draw unit, the comparator ladder, and the residual-sweep
  classes.

Fable also found:
- **L3's mutual-inhibition grid would latch.** At |w_m| ≥ 1 the comparator pair is bistable, with a
  switching threshold far above the scent difference.
- **The sweep's likeliest outcome fell into "unclear",** and twelve unadjusted intervals invite
  spurious classes.
- **The 25% background reading did not match the 12-of-16 rule.**

Astra also found:
- **v2 said R's output "never reached the motors". That is wrong:** R stays connected.
- **H at the final generation alone shows host competence,** not acquisition.
- **v2's "K_D at the sensory neurons is 1 by construction" was wrong:** the injected derivatives are
  ±½, and recurrent activity is not fixed by them.

**Proposal v2.1 takes every item** (its last section maps them). Both reviewers had said "adopt with
changes", and their items are applied without disagreement between them, so the plan is adopted
without a third round. **`ROADMAP.md` is amended:**
- the status of 1 October;
- E4s in the sequence;
- an E4s section in Track E;
- additions to E3 and E4;
- the tripwire relaxed for the graft functions and GA hooks only;
- the literature review in related work;
- two new entries under "What would change this roadmap".

**Checked here:**
- **A graft accepts a self-edge,** which L2 and E3's latch need. The new test passed at once, because
  the behaviour already existed. It failed under a sabotage that drops self-edges.
- **The GPU engine gate passed**
  (`experiments/E4s-stereo-module/development-records/equivalence-ga.json`):
  - E2's GA, generations 0-25, at E2's composition (8 runs × 32 strains × 8 worlds);
  - every run's best-genome hash matched E2's committed `train-ga.json`, 26 of 26 generations;
  - three ways: the defaults, hooks restating the defaults, and scale vectors of ones.

**Still pending, as gates for E4s-1:**
- the CUDA state tolerance at the real batch shapes;
- the score-level inert-graft check.

**Next:** E4s-0's plan (`docs/E4s/E4s-0-PLAN.md`), which pins the script's details, is reviewed
before anything runs.

## D145 — E4s-0's plan v2 and its script; a world-id collision found by the script's own test

**The review of E4s-0's plan v1** (`docs/reviews/20261001-E4s-0-plan/`): both "revise". There were no
disagreements; the reviewers asked for pins and tests:
- **The residual wrapper's tests** missed "before the clamp", the sign and removal.
- **The k = 0 check** needed one fixed composition.
- **The bootstrap seed** (20 261 001) contradicted "imported from E2d unchanged" (E2d's is 0).
- **The sweep's classes** dropped a condition, and their "unclear" was unreachable.
- **The simulated G0 statistic** was untested against `evolve_batch`, and was measured on 256 worlds
  where E4s-1 will use 1 024.
- **A toy smoke** cannot project the formal compositions.
- **Robustness's seeds and ownership** were unpinned.
- **"Settled" at 40 ticks** is too short for slow comparators.

Astra also corrected the adopted proposal (v2.1). Its "a 'retained' majority would be out of reach by
construction" holds only for the same runs. The proposal gets a dated note: the rule is a design
trigger, not a prediction.

**Plan v2** (`docs/E4s/E4s-0-PLAN.md`) takes every item; its last section maps them.

**Found by the script's own test, missed by both plan reviews and by me:** v1 placed E4s-0's worlds at
990 million.
- **03's timing ids** occupy 990 million. E2's and E2d's disjointness tests list it as used, but the
  ids are not written as literals in the code, so a search of the constants found nothing.
- **The new test** (`test_e4s0_script.py`) carries the earlier ranges and failed on the first
  version.
- **970 million**, the next candidate, is 02's gate ids (`exp02/grid.py`).
- **The ranges are now at 940 million,** where no range starts. A sabotage that moves them back to
  990 million is caught.

**Built:**
- **`scripts/e4s0.py`:** six stages (project, sweep, attenuation, ladder, populations, robustness)
  in E4s-0's own copy of E2's stage frame. It imports E2d's `world_ci`, `classify` and champion
  loaders unchanged.
- **`wormwars/e4s/diagnostics.py`:** the sweep's classes, the G0 selection, module-only mutation
  scales, per-strain motor statistics, and the settling rule.
- **More tests on the residual wrapper.**
- **The tests:**
  - the library's were seen failing first;
  - the script's 6 tests were written after the script, so their evidence is sabotage: 4 caught (the
    ranges at 990 million, a ladder that does not stop, a reversed shrink order, L4's base chosen
    twice);
  - one diagnostics test was strengthened after a missed sabotage: scrambled population boundaries
    gave the same answer on the first constructed case.
- **The full suite passes.**

**The smoke** (`runs/e4s0-smoke`, toy sizes, never results) ran every stage end to end.
- The k = 0 check held for all 47 champions.
- A smoke-only acceptance makes L1 "qualify" so that the qualified path also runs: the open-loop
  dynamics, the module file, the populations and robustness. Formal qualification is unchanged.
- Two bugs were fixed: an import that bound the `rollout` function instead of its module, and an
  undefined robustness share when the parent scores 0.

Plan v2 and the script go to Astra 6 and Fable 5.1 for a code review before the formal run.

## D146 — E4s-0's code review (both "fix then run"); the fixes; cleared to run

**The review** (`docs/reviews/20261001-E4s-0-code/`): both "fix then run". The items are implementation
fixes; neither reviewer asked for a redesign. Both found:
- **Re-score ties** went to the screening rank, not the grid order.
- **The projection** left out its own elapsed time. It timed each shape once, cold, and it did not
  price the attenuation, the dynamics, the bootstrap, L4's padded common re-score, or the shrunk
  compositions.
- **The per-world counts the plan promises** were missing for tuning, the re-scores, the base
  selection, the G0 selection and the robustness children.
- **The robustness fallback** defaulted to "0.25x" when neither scale kept half.

Fable also found:
- **Compositions** were recorded only by the sweep.
- **A missing 04a run 2** would be dropped silently.
- **The module file** could survive beside a not-completed record.
- **The reversal's "wrong sign" flag** tested the change, not the output's own sign.
- **Parameters on the genome's bounds** make robustness look better, so they should be recorded.

Astra also found:
- **The attenuation probe** read the turn command unclamped.
- **The settling rule** called a drifting trace settled when its final mean was negligible, and gave
  a response time for unsettled traces.
- **No test** checked that the G0 selection reads the selection worlds.
- **A zero-score parent** left fabricated shares.
- **The plan contradicted itself** about which candidate robustness uses when nothing qualifies.

**Fixed, each new behaviour with a test seen failing first:**
- `rescore_choice`: ties go to the lower grid index.
- **The projection:**
  - it times every shape twice and uses the second;
  - it adds this attempt's elapsed time to the hours spent;
  - it prices L4's common re-score, the robustness parent and the shrunk compositions at their own
    measured rates;
  - it measures the attenuation, the dynamics and the bootstrap per call, and adds them.
- **Per-world counts and compositions** are recorded in every record. The robustness record notes
  that its parent (one padded strain) and its children (chunks of 64) differ in composition, so their
  share is descriptive.
- `robustness_reading` has three outcomes, and shares are null for a zero-score parent.
- **A missing 04a run 2 stops the stage,** and the module file is deleted if the ladder does not
  complete.
- **The reversal flag** also checks the output's own final sign.
- `settle` judges convergence on its own, and gives no response time for an unsettled trace.
- **The attenuation turn** is clamped each tick.
- `on_bounds` is recorded for the qualifying candidate.
- `pick_g0` and `population_selection_ids` are the production routing, tested with scores that differ
  between selection and other worlds.

**Sabotages:** 3 more, all caught (every population reading population 0's worlds, ties by screening
rank, a "0.25x" default).

**Two dated corrections in the plan:** the stated grid order (the step's own parameter outermost),
and which candidate robustness uses if nothing qualifies (the later rule, as the code does).

**The smoke** again ran every stage. **The full suite passes.**

Both reviewers said "fix then run", and the fixes are applied without disagreement between them, so
E4s-0 runs without a further round. The formal run starts from a clean, pushed tree.

## D147 — E4s-0 ran (0.23 GPU-hours); its results reviewed (both "fix", text only) and corrected

**The run** (2026-10-01): the projection, then the five stages, each once.
- The first five stage commands were refused within seconds: the projection's record had not been
  committed and pushed, which the stage frame requires before the next stage.
- After that, each stage was committed and pushed before the next.
- 0.23 of the 2 GPU-hours.

**The results** (`experiments/E4s-stereo-module/E4s-0/RESULTS.md`):
- **For 42 of 47 champions, a valley along the stereo-gain direction:** small k changes little,
  k = 2-16 harms, and k = 32, 64 and 256 help all 47.
- **The differential response** falls from the sensory neurons to RIA, then levels off.
- **L1, the 4-neuron comparator, qualified** (5.18, lower bound 5.10, "uses"), with the carrier's
  turn command of 0.2.
- **It is used at generation 0** by all 16 simulated populations' bests, so E4s-1 proceeds on random
  N2.
- **On 04a run 2 the graft is harmful** (real minus mean input to the module: −1.76).
- **Robustness is bimodal;** the factor stays 0.25×.

**The review** (`docs/reviews/20261001-E4s-0-results/`): both "fix", text only.
- Both re-derived the main numbers from the records, and they hold.
- What they corrected, quoted in the results' Corrections section (15 items):
  - a wrong small-k maximum in the README (+0.08 against +0.27);
  - "a valley" unqualified (five champions are never harmed);
  - the adjacency rule's blind spot at k = 16;
  - pooled attenuation medians, and "shrinks at every stage";
  - **L1's dependence on the carrier's turn command, unstated** (Fable: 3.86 at turn 0, 5.27 at 0.2
    in tuning);
  - an unmeasured counterfactual about clipping at the bounds;
  - one-generation robustness turned into survival claims, and a bimodal distribution hidden by its
    median;
  - "the valley predicts" mutation outcomes (against the plan's reach);
  - 04a run 2's harmful interaction understated;
  - `t90`'s indexing;
  - numbers with no generator (rule 5), and references from outside the folder;
  - an exact-repeat promise without `replay_mode()`.

**Rule 5:** `scripts/e4s0_summary.py` now derives every summary number into `summary.json`.

**For E4s-1's design** (from both reviews):
- the turn offset is a first-order variable;
- the module's ceiling is near 5;
- generation-0 bests start at the plateau's level, so "uses" must be read along training;
- mutational load is high (consider a 0.125× sensitivity arm);
- R's control varies only signs, since all of L1's magnitudes are 3;
- C2 starts in a harmful interaction;
- the pending CUDA and score-level gates stay gates.

## D148 — E4s-1's design v1 reviewed (both "revise"); design v2; E3's artefact rule amended

**The review** (`docs/reviews/20261001-E4s-1-design/`): both "revise", one text round, with no new arm.

Both found:
- **O1 is not a manipulation check.** Generation-0 bests score about 2.06, so M − N at generation 999
  needs M to climb. Final superiority is also not improvement by evolution: F − G0 changes are needed.
- **The class labels claim histories two endpoints cannot show.** Mc and H were hidden behind the
  table's priority.
- **The turn offset was measured confounded with steering:** open-loop u(m, 0) is needed. Neither
  wants a controlled bias in the main arms.
- **`module_scales` pins the host:** E4s-1 needs its own masks.
- **The gates needed precise implementations.**

Fable also found:
- **C2 is "unclear" by construction:** its 32 copies are identical, and the probes show harm.
- **R is often a harmful graft,** not a neutral one: random nose signs make a comparator respond to
  the common level.
- **"Retained" says nothing about score,** which matters for E3's swap rule.
- **Mc only at turn +0.2** misses a module that co-adapted to a negative offset.
- **Gate 1's chance fail** is about 4-5%, not 1%.
- **Gate 3 was nearly vacuous** on random genomes, which score 0.
- **"Reversed"** was missing from O1's rules.

Astra also found:
- **Overclaims:** "a ceiling near 5", "R cannot repair itself", "lethal".
- **Gate 2** needs identical imposed inputs and validation's shape.
- **Evaluation at 1 × 1 024 runs at 306 episodes per second,** so the 16-17 h estimate was too low.
- **R's reset** must be told apart from an L1 rescue.

**Power, simulated** with the exact O1 rules, at Astra's request (16 runs, 600 simulations, normal
paired differences):
- at SD 1.3, "supports" in 5% with no effect, 47% at an effect of 0.5, and 92% at 1.0;
- at SD 2.0, 8%, 29% and 65%.

So E4s-1 detects effects of about 1 target per episode. The design states it.

**Design v2** (`docs/E4s/E4s-1-DESIGN.md`) takes every must-fix; its last section maps them. The
arms are unchanged.

**E3's artefact rule is amended** (a dated note in the proposal). A replacement for E4s-0's module
now also needs O2b ≥ 0.9.

Design v2 goes to Astra 6 and Fable 5.1 for a confirmation round.

## D149 — E4s-1's design v2 confirmed (Fable "proceed", Astra "revise": specification only); the pre-registration drafted

**The confirmation round** (`docs/reviews/20261001-E4s-1-design-v2/`):
- **Fable: "proceed to pre-registration".** All of v1's must-fixes are resolved in substance.
- **Astra: "revise",** as a small specification revision with no change of arms.

Both listed what the pre-registration must pin. The items they raised, all fixed in the draft:
- **C2's "unclear by construction":** identical founders do not fix a class on fresh worlds (Astra).
- **Gate 1's probability:** plug-in about 1%, predictive about 4-5% (both); both are now computed.
- **Gate 3's G0 bests score almost nothing without the module** (0.02-0.44 under module mean). They
  are dropped for E2 GA's 8 champions.
- **The power simulation had no committed generator** (rule 5; both). Fable asked for a bimodal
  scenario.
- **C2's classifier was ambiguous;** it now has an order.
- **"M − N needs M to climb"** was an overclaim (Astra).
- **O1c's M − N climb difference is confounded** by the graft's immediate benefit at G0 (Fable).
- **"Does not support"** covered a significant small positive effect (Fable); it now has its own
  label.
- **The two unadjusted tests' family rate** is now stated.

**Checked:** E2's 1.35 h per batch is measured (`train-ga.json`, 4 862 s), not only planned.

**`scripts/e4s1_power.py`** writes `experiments/E4s-stereo-module/E4s-1/development-records/power.json`:
- gate 1's chance of a fail by chance: 0.9% plug-in and 4.7% predictive;
- O1's power at SD 1.3: 6% with no effect, 44% at 0.5, 91% at 1.0;
- bimodal, half the runs keeping +2: 93%;
- a family false "supports" of 11-14%.

**The pre-registration draft** (`experiments/E4s-stereo-module/E4s-1/PREREGISTRATION.md`) pins every
item both reviewers listed. It goes to both for review before it binds.

## D150 — E4s-1's pre-registration reviewed (both "bind after fixes"); the fixes applied; bound and pushed

**The review** (`docs/reviews/20261001-E4s-1-prereg/`): both "bind after fixes", text only, with no
arm changed. Both checked that O1's rules, C2's ordered reading and the O2 table are exclusive and
complete, and that the masks, the seeds and F, C and G0 match the code. **Their fixes, all applied:**

**The gates:**
- **G2:** its shapes did not cover the 48 genomes (only genome 0 in the single-strain shapes). Its
  input history was not reproducible as written.
- **G3:** its execution shape was missing.
- **Source genomes** must be bound by parameter hash, not only by graph label: `source-genomes.json`
  is written and its sha256 bound.
- **The module's sha256** is given in full.

**Failures and stages:**
- **A failed gate is final;** reruns are only for stopped stages, and never after a cap stop.
- **The stage list** is stated. The projection runs on smoke ids and reads no scores.
- **The evaluation reserve** has a value, and admission works batch by batch in order.
- **An end-of-run assertion failure** has a consequence.

**The outcomes:**
- **O2's labels** keep an unclear endpoint visible (all nine cells named).
- **Fixed denominators,** and "no label named" in place of an undefined "mixed".
- **"Positive; estimate below 0.5":** the interval can extend above 0.5.
- **Fixed companion sentences** for O1 and O1b "supports".
- **C never changes an O1 label.**
- **The O3 split** is 8 against 8 by rank.
- **R's weight** is s_k × 3.0.

**The probability claims:**
- **The family rate** assumes independent tests, which these are not: it is an illustration.
- **The power** used 2 000 resamples.
- **Gate 1's figures** cover the score threshold only.
- **SD 1.3** has no basis; both SD rows are quoted.

**The episode count:** 3.7 M was wrong. By the measures as listed it is about 4.2 M, after §5's table
of which measures apply where.

**L1 sits on the bounds** (Fable). Its weights can only shrink and its τ only grow under mutation, so
a loss of use may be one-sided drift. F0 − M is the stated comparison.

**The departures from design v2,** listed in the pre-registration's §12: C2's harmful bound; the O2
labels; run indices from 0; G3's genomes; the new O1 label.

Both reviewers said "bind after fixes", and every listed fix is applied, so the pre-registration
binds without a further round. It is committed and pushed before any E4s-1 stage runs (rule 2).

## D151 — E4s-1's runner, test-first; smoke end to end; to code review

**Built, against the bound pre-registration (D150):**
- **`wormwars/e4s/arms.py`:**
  - L1, loaded by its bound sha256 and registered in `graft.MODULES`;
  - `arm_scales`;
  - R's signs, s_k × 3.0;
  - N's construction;
  - the Mc transplant;
  - reset and the L1 rescue.
- **`wormwars/e4s/readings.py`:**
  - O1's five ordered rules and their companion sentences;
  - the nine O2 labels;
  - the arm reading and retention;
  - C2's ordered reading;
  - the O3 split.
- **`scripts/e4s1.py`:** projection, three gates, R's draws, ten training batches, the endpoint
  evaluation and the evaluation along training, in E4s-1's own copy of E2's stage frame.
  - Per-world counts go to committed `.npz` files, and genomes stay local.
  - One design choice the pre-registration left open: the G0 population counts and the final
    populations run 32 strains per chunk, and along training 8 per chunk. Both compositions are
    recorded. The endpoints run one padded strain per genome, as registered.
  - **R's "open-loop K_D and K_C at generation 0"** is measured on the draw's own module on the
    carrier (turn 0), apart from the host.

**Tests:**
- **The libraries' 20:** seen failing first. 6 sabotages caught, after one test was strengthened (a
  tie at the split's boundary).
- **The script's 6,** written after it: 4 sabotages caught (ranges overlapping E4s-0's, N's
  assertion off, G2's seed, C2 sharing seeds).
- **The full suite passes.**

**The smoke** (`runs/e4s1-smoke`) ran all 17 stages end to end. Admission is skipped in smoke, where
the projection prices the formal work at toy rates.

## D152 — E4s-1's code review (both "fix then run"); Amendment 1 before any stage; the fixes; the analysis script; cleared to run

**The review** (`docs/reviews/20261001-E4s-1-code/`): both "fix then run". Neither found a bug that
would silently corrupt a formal number on the happy path. Both found:
- **A training batch that stopped twice would have blocked all evaluation,** against §8.
- **`eval-training` had no admission check,** and the G0 population counts were priced in the wrong
  stage.
- **Registered tests were missing:** H's conditions, the open loop, G2's coverage and R's hash.
- **G2's input shape** was an interpretation of the bound text.
- **The projection** departed from §3.
- **Mutation counts** were analytic, not logged per generation.
- **Some loaded genomes** were not checked against their records.
- **The analysis needed data the records did not keep:** the G0 population's per-world counts, the
  module's parameters at each endpoint, per-world motor values, and R's edges by name.

Astra also found:
- **Non-finite values passed silently.** Python's `max(0, NaN)` is 0, so G2 could have passed on NaN
  states.
- **Interrupted evaluations lost their per-world counts.**
- **Killed and refused batches** had no durable state.

Fable also found that no analysis script existed yet.

**Amendment 1** (the pre-registration's §13, dated, before any stage ran), settling what the bound text
left ambiguous:
1. G2's input is the distinct signals, 300 × 15.
2. The projection's procedure.
3. The analytic mutation counts, with what they rest on.
4. Later batches run after a final stop; a refusal is recorded and ends training.
5. The compositions the text left open.
6. An annotation: §5's "reset and rescue equal real at G0" is wrong for the rescue at R's G0. Nothing
   measured changes.

**Fixed** (`scripts/e4s1.py`, `wormwars/e4s/readings.py`):
- **Finite checks** on scores, open-loop values, motor measures and G2's differences. A non-finite
  value stops the stage, and the O1 readings refuse it.
- **Stage states:** completed, final-stopped, awaiting-rerun, refused, killed and absent.
  - Training runs in order, after settled predecessors, and is closed once the evaluation starts.
  - A refused batch writes a refusal record.
  - The evaluation covers the completed batches and names the others; it refuses a killed or
    unsettled batch.
- **Admission for both evaluation stages,** with the G0 population counts priced where they run.
- **The projection:** two timings, an instrumented probe, the cap checked, and the references
  counted right.
- **Every loaded genome is checked** against its committed record: the brain configuration, every
  hash, and the checkpoint generations. The regenerated G0 population must hold the record's G0
  best.
- **Per-world counts and motor values** are written incrementally, with their sha256, and archived
  on a rerun.
- **More data kept:** module parameters by edge name at G0, C and F; the G0 population's per-world
  counts and contrasts; the checkpoint and hash along training.
- **Gates 2 and 3 load their genomes before the start marker.**

**Tests:**
- **New tests, each seen failing first:** non-finite values, retention's statuses, G2's coverage, H's
  routing, the open loop, R's hash, the training states, and the named module parameters. The open-loop
  test passed at once, so its evidence is a sabotage.
- **Sabotages:** 7 of 8 caught at first. The missed one (a killed batch accepted) was not a real break:
  the code refused it as an unknown state. Treating a killed batch as finished was caught.
- **The full suite passes.**

**`scripts/e4s1_report.py`** applies the registered readings from `readings.py` and E2d's bootstrap
and sign-flip test: O1 and O1b with their companions, O1c, O2 with O2b and retention, C2, O3 and E3's
rule. It ran on the smoke records.

**The smoke** again ran all 17 stages end to end.

Both reviewers said "fix then run". Every item is applied or settled by Amendment 1, so the formal run
starts from a clean, pushed tree.

## D153 — E4s-1 ran as registered (16.61 GPU-hours); its results written, for review

**The run** (2026-10-01 13:22 to 2026-10-02 06:01):
- the projection, the three gates (all passed), R's draws, ten training batches, and both evaluation
  stages;
- each stage committed and pushed before the next;
- no stage refused, stopped or rerun; every end-of-run assertion passed; all 80 runs evaluated.

**The registered readings** (`report.json`):
- **O1 "supports"** (+5.19, 90% interval +5.06 to +5.33, 16 of 16 pairs positive).
- **O1b "supports"** (+3.79). Neither companion sentence applies.
- **M "uses at both endpoints"** in 16 of 16 runs, all with O2b ≥ 0.9. F0, U and S use it too, in 8 of
  8 each; R has no label named.
- **C2 goes from "harmful" to "uses"** in 8 of 8.
- **E3's artefact rule is met:** run 10's F, with O2b 1.45. E3's own positive control is still
  required.

**Descriptive** (`summary.json`, from the new `scripts/e4s1_summary.py`):
- **The steering stays in the graft:** H is "no material benefit" throughout, and silencing the module
  leaves 0.11.
- **The host co-adapts:** putting L1's designed parameters back leaves 0.72, and the evolved module
  alone meets "uses" in only 5 of 16 runs.
- **M climbs past the carrier's 5.2 by generation 100** and reaches 7.1. N stays near 1.6-1.9.

**Every headline number** was re-derived from the per-world counts before writing.

The results (`experiments/E4s-stereo-module/E4s-1/RESULTS.md`) go to Astra 6 and Fable 5.1 for review.
On consensus, E4s-0 and E4s-1 go to `main` together (the owner's choice, 2026-10-01).

## D154 — E4s-1's results reviewed (both "fix", text only) and corrected; a recording defect disclosed

**The review** (`docs/reviews/20261002-E4s-1-results/`): both "fix", text only. Both re-derived the
registered readings, and they hold. Astra reproduced all 240 endpoint scores and 5 152 world-level
intervals from the per-world counts.

**Corrected** (RESULTS.md's Corrections section, 15 items):
- **"The steering stays in the graft" and "the host did not come to steer by the difference itself."**
  H is a module-blind assay, uninformative in 8 of 16 runs, and §11 excludes transfer claims (both).
- **Missing: part of M − N is not stereo use** (Fable). With the module's noses fed the mean, the final
  brains keep 1.26 on average, and four keep 2.5-4.5.
- **"Co-adapted, not a better module" was too categorical:** 5 evolved modules beat L1 alone on a
  carrier, and 10 score 0 (Astra).
- **Continuity claims beyond the two endpoints.**
- **The F0 gain was a mean over a range of 9.6-428.**
- **"Barely moved"** for weights that shrank 6.9%.
- **Causal wording for F0 − M.**
- **O1c's failed registered expectation:** the climb difference was +3.14, not negative.
- **C2's G0 is one genome measured eight times.**
- **The label punctuation.**
- **An overbroad "every headline number was re-derived".**
- **Registered reporting items missing:** R's final signs and its draws' gains, C's scores, the Mc
  shares.
- **O1b concerns random signs that could not change** (none changed in any arm).

**A recording defect, disclosed under Deviations** (Astra). The endpoint stage cast every per-world
array to int16, the fractional motor measures included.
- All 1 440 stored motor arrays are zeros. The per-episode motor means in `eval-endpoints.json` are
  intact.
- No target count or registered outcome is affected.
- The records are left as they are.

**Correction to D153 (2026-10-02).** D153 said: "E3's artefact rule is met: run 10's F, with O2b 1.45.
E3's own positive control is still required." §7 requires all three conditions. It now reads: the two
E4s-1 conditions are met, and replacement remains conditional on E3's positive control (both). Run 10's
module scores 0 alone on both carriers, so E3 would inherit a whole-brain artefact.

**`e4s1_summary.py` and `e4s1_report.py`** now record every number the corrected text uses (rule 5),
including M's climb interval, +4.48 to +5.20.

**Publication:** both reviewers said "fix", text only, and every item is applied. On that consensus,
E4s-0 and E4s-1 go to `main` together (the owner's choice), and the owner is told afterwards.

## D155 — E4s-0 and E4s-1 published on main

Under the owner's rule (both reviewers' fixes applied, D147 and D154), and as the owner chose
(2026-10-01: both together), `main` was fast-forwarded from `df50f6a` to `9f0ea31`: the roadmap branch
at `a0fe94a`, plus one commit removing its banner. It carries:
- **E4s's planning:** the literature review, the roadmap proposal and its reviews, the superseded
  designs, D139-D155;
- **E4s-0:** its plan, code, records, results and corrections;
- **E4s-1:** its design, pre-registration with Amendment 1, code and tests, every stage record, the
  per-world counts, the report and summary, results and corrections;
- **the engine changes:** per-parameter mutation scales and `evolve_batch` hooks, GPU-checked;
- **the front page, roadmap, AGENTS.md and review trail** (episodes 25-29).

**Checks:**
- the full suite, locally;
- CI green on `a0fe94a`. `51f3dfa` failed the hygiene guard, which `e9e62a7` fixed, as recorded;
- the identity check: no email in tracked files, the noreply identity on every commit.

`roadmap` continues from `main` with its banner. Next in Track E: E3's design.

## D156 — E3's design v1 reviewed (both "revise"); design v2

**The owner, 2026-10-02:** "Start it" (E3's design, after E4s's publication).

**Design v1** (`docs/E3/DESIGN.md`) staged E3:
- **E3a:** the shuttle;
- **E3b:** trails, mazes and the colony;
- **E3c:** the assembly comparison.

E3a used two copies of L1 and a one-neuron latch on the silent carrier.

**The review** (`docs/reviews/20261002-E3-design/`): both "revise". Both agree with the staging and with
L1 rather than E4s-1's run 10. Both found:
- **The latch cannot switch on a one-tick pulse of weight 1.** It needs about 3 τ_q to cross zero. The
  literature review I cited says so explicitly ("A one-tick pulse is insufficient"), and v1
  contradicted it.
- **The latch starts on its unstable point:** the brain's initial state is zeros.
- **The gate needs the comparator-bias shift,** and `b_max` = 2 caps its weight at about 2.
- **L1 needs its own positive control** (a scripted switch), to separate module from latch failures.
- **No N2 interface:** ALM and AVM carry live collision signals.
- **Stage 3 must not evolve the silent host.**
- **The budget must be itemised:** the carrier costs what N2 costs.

Astra also found:
- **memory must be tested causally** (clamped-latch paired assays);
- **an executable event contract** is needed;
- **"no visit events" was wrong:** Task N's ledger exists and extends;
- **the engine claim** needs narrowing.

Fable also found:
- **Stage 2 cannot start from random at 0.25×,** since E4s-1 showed no sign flips;
- **random sampling** is needed as a comparator;
- **12-18 cells** puts the far scent at its truncation edge;
- **`graft.py`'s limits:** food-only noses, one module per graft.

**Checked:** the geometry by simulation. 8-14 apart with the spawn at least 6 from both is feasible
for every spawn, and so is v1's 12-18 with 8.

**Design v2** takes every must-fix; its last section maps them. It proposes a 20 GPU-hour cap for
E3a, pending the owner's ceiling for E3.

## D157 — E3's design v2 reviewed (Fable: proceed if the budget is fixed; Astra: revise); design v2.1

**The review** (`docs/reviews/20261002-E3-design-v2/`): both checked v2's latch and gate numbers and
found them right. Astra checked them in the real `Brain.step` on the CPU: active K_D 31.6-35.6,
inactive 0.059-0.068.

**What both found:**
- **The budget was wrong by about 2×:** E4s-1's rate was at 8 worlds per genome, v2 used 16, and
  B-task was given one stage where its text gave it two.
- **w_s was not a genome parameter:** an interface gain `mutate` cannot touch.
- **The 7-parameter count rested on unstated tying.**
- **A hold test on sign alone cannot tell a latch from a leaky trace.**
- **Still missing:** the dtypes (promised but not declared) and the latency from movement to sensing.

**Fable also found:**
- the maximum spawn distance (a first leg could start outside the scent's support);
- the carrier's circle can visit both sources;
- Stage 2 may be answered at generation 0;
- clamping q is new engine code.

**Astra also found:**
- the component tests' protocol needed absolute limits;
- each module's turn contribution needed a definition;
- the start cue's overdrive;
- L1-switch is a reference, not an upper bound.

**Checked:**
- **The relay-driven latch, by simulation at 32 substeps:** a one-tick level switches it.
- **The geometry, in `scripts/e3_geometry_check.py`** (committed with its output):
  - without an axis limit, 0.19% of accepted worlds start with A beyond the scent's reach;
  - with A within 16 along both axes, none do, and every spawn accepts at least 11.8% of draws.
- **The rate, from E4s-1's ten training batches:** 1.35-1.43 h for 8 runs × 32 × 8 worlds × 300 ticks
  × 1 000 generations.
- **The world-id blocks 944M-947M** are unused.

**Design v2.1:**
- relays carry the visit signals, so all 13 selector parameters are genome parameters, untied;
- bistability and hold tests on magnitude and function;
- dtypes declared;
- the budget recomputed, with Stage 2 at 300 generations: about 13.3 h;
- a proposed cap of 20 GPU-hours for E3a;
- a dated correction of v2's budget.

E3's ceiling is still the owner's to set.

## D158 — E3's GPU ceiling: 30 GPU-hours (the owner)

**The owner, 2026-10-02**, answering the request for E3's ceiling (D156, D157): "30 hours celling".
- **Read as the ceiling for all of E3** (E3a, E3b and E3c), the question having been asked for E3.
  E4s's ceiling (96 GPU-hours) was likewise set for the whole track.
- **E3a's proposed cap stays 20 GPU-hours inside it** (design v2.1; about 13.3 h estimated), which
  leaves about 10 for E3b and E3c. Their budgets come with their designs.
- The owner can correct this reading. The pre-registration states the cap it binds.

## D159 — E3's ceilings corrected by the owner: 30 GPU-hours for E3a, about the same for E3b and E3c

**The owner, 2026-10-02**, on D158: "E3a 30, something similar for the other 2".
- **Correction to D158 (dated 2026-10-02).** D158 read the owner's "30 hours celling" as "the ceiling
  for all of E3 (E3a, E3b and E3c)", with "E3a's proposed cap [staying] 20 GPU-hours inside it". That
  reading was wrong. D158 stands as written, corrected here.
- **E3a's cap is 30 GPU-hours.** Design v2.1 estimated about 13.3. Its shrink order now applies only if
  the projection exceeds 30.
- **E3b and E3c get about 30 each.** Each is fixed when its design is written.

## D160 — E3's design v2.1 reviewed (both "revise", text only); design v2.2

**The review** (`docs/reviews/20261002-E3-design-v2.1/`): both found the budget, the relays and the
geometry sound, and the remaining problems repairable in text.

**What both found:**
- **The no-latch control was mis-built.** q clamped to 0 with the comparator biases left at −1.914
  leaves both modules mostly off (Astra, in `Brain.step`: K_D 2.63-2.97 against 31.6-35.6), not
  "both on".
- **The memory classes misfiled real latches.** The hold test used the engineered organism's absolute
  numbers. Astra gave a concrete working bistable selector (q* = ±1) that v2.1 would call "no
  memory".

**Fable also found:**
- the champions' clamp values were undefined;
- B-task had no reading;
- drawing the selector uniformly over the bounds makes a working selector about 10⁻⁶-10⁻⁵ likely;
- "16 along both axes" allows about 22.6 cells (a Euclidean cap is needed).

**Astra also found:**
- **the latch's quoted number (∓0.43) came from explicit Euler,** where `Brain.step` gives ∓0.2197.
  Rechecked here in the engine's semi-implicit, simultaneous update: confirmed;
- the "start blind" statistic was mislabelled;
- E4s-1's carrier stepped 306 neurons, not 313;
- the reduction order did not reach the stated minimum;
- the startup was not tested.

**Design v2.2:**
- the no-latch control built "both on", with the q = 0 clamp kept as a named ablation;
- a dynamical class separate from a memory class, with four classes and tests on each champion's own
  states;
- a release test;
- the selector started near the ungated pair, with a uniform census as description and 0-of-8 wording;
- B-task given its free parameters and a descriptive reading;
- a Euclidean spawn cap of 16 (minimum scent at the spawn head 0.0286, rechecked by the committed
  script);
- a startup test;
- five reductions that reach the minimum;
- the cap of 30 GPU-hours (D159);
- dated corrections of v2.1's latch number, no-latch control, "start blind" label and neuron count.

## D161 — E3's design v2.2 reviewed (Fable: proceed with four fixes; Astra: revise); design v2.3

**The review** (`docs/reviews/20261002-E3-design-v2.2/`).

**What both found:**
- **The hold test took its reference as the head left the source, while q was still settling.** Astra,
  in `Brain.step`: −3.05 after a two-tick level, −4.71 after a four-tick one, settling at −1.915. The
  engineered organism therefore failed its own test.
- **"Bistable" was conflated with "reachable by the levels".** Fable: a slow sweep passes a q that real
  visits never switch. Astra: a bistable q with no input edges would be misclassed.
- **Independent comparator biases broke the push-pull balance.** Astra, by an equilibrium calculation:
  83.5% of generation-0 draws had a clipped turn at zero nose difference. So the claim "starts close
  to the no-latch control" was false.

**Fable also found:**
- B had no spawn cap, so the clamp-to-B assay was at risk;
- the GA and random sampling validated unequally;
- the census check would touch the test worlds early;
- S2-b needed an outcome for when neither arm finds a selector.

**Astra also found:**
- **the noses receive the scent scaled by `sense_scale_food` (0.35).** So v2.2's "0.0285 above m = 0.02"
  compared different units: checked in `world.py`, confirmed;
- the release test passed two zero gains.

**Checked:** both sources capped at 16, by the committed script. Every sampled spawn accepts at least
11.8% of draws (median 17.8%). The weakest scent at a spawn head is 0.0286, which the noses receive as
0.0100.

**Design v2.3:**
- open-loop hold, settable and release assays on each champion's own states. These are exact, since
  q's only inputs are the relays and itself;
- the equilibrium structure classed independently;
- the initial draw tied per module and the mutations independent, so generation 0 has zero offset by
  antisymmetry;
- both sources capped;
- component tests down to m = 0.005;
- equal validation;
- a 25% reserve on the projection;
- dated corrections of v2.2's hold reference, its initial distribution and its geometry claim.

## D162 — E3's design v2.3 reviewed (Fable: proceed with pins; Astra: revise); design v2.4

**The review** (`docs/reviews/20261002-E3-design-v2.3/`).
- **Fable:** "proceed to pre-registration", with three pins.
- **Astra:** "revise". Astra rebuilt the engineered organism in `Brain.step` on the CPU; it passes
  every component test (active K_D 31.60-35.63, inactive 0.0595-0.0675), startup and the hold.

**Fable also found:**
- **the 20-tick windows suit τ_q = 1 only;**
- **a two-tick stimulus can fail a champion that works in the world;**
- **generation 0's balance lasts one generation under untied 1× mutation.** A CL/CR mismatch δ adds a
  turn of about 5.9δ;
- **the start distribution contains no working selector,** so random sampling drawn from it is a
  near-certain zero.

**Astra also found:**
- **the gain readout's 50-tick preconditioning let q drift;**
- **"rest after 100 ticks" is not equilibrium for a slow q.** For w_qq 0.99, b_q 0.01, τ_q 20, q reaches
  0.049 against an equilibrium of 0.282, rechecked here by the engine's update: confirmed;
- **D was derived from the test worlds,** which must stay untouched;
- **"zero turn offset" means the modules add none;** the total turn is the carrier's 0.2.

**Design v2.4:**
- a window of max(20, 10·τ_q);
- the champion's own stimulus duration, with the two-tick result beside it;
- q and the relays held during the readout;
- the computed equilibrium as the release test's start;
- calibration worlds (948M, checked unused);
- random sampling as a blind search over the whole range, tied per module, with a dated correction;
- generation 0's limits stated, with offsets logged;
- the pulse-to-goal mapping, root finding, missing medians, reset timing and B-task's draws pinned.

## D163 — E3's design agreed at v2.4: both "proceed to pre-registration"

**The review** (`docs/reviews/20261002-E3-design-v2.4/`): both said "proceed to pre-registration", the
first agreement after five rounds (D156, D157, D160, D161, D162). This is a consensus decision; the
owner is informed.

**Editorial fixes made after the round,** marked "(D163)" in the design:
- calibration worlds, not test worlds, for monostable champions' medians;
- the registered stimulus, not a two-tick level, for "settable";
- the head's scaled scent (0.0100) distinguished from the lowest bilateral nose reading (about 0.007);
- the probe's m = 0.05 restored;
- the release test's starting equilibria for bistable champions;
- **fixed points counted as stable roots** (f′ < −1e-6), with exact grid zeros included. Astra showed
  that v2.4's merging of near roots can leave two roots (w_qq 2, b_q 0.5328…), which neither class
  accepted.

**Carried into the pre-registration**, as both listed:
- the world block for the Stage 0 and Stage 1 gates (not the test worlds);
- tolerances against the separation of the stable states, read at the end of W;
- the stimulus's fallback, rounding, pooling and censoring;
- S2-c's wording for a census zero, with an interval on the hit rate;
- S2-b's wording naming the different distributions and random sampling's permanent tie;
- B-task's self and mutual comparator edges, output range and τ draws;
- B-task's sensory-blind start named in its reading;
- the reset as a one-time write;
- which Stage 3 runs are kept under reduction;
- every number still marked "proposed".

## D164 — E3a's pre-registration, first draft reviewed (both "bind after fixes"); second draft

**The review** (`docs/reviews/20261002-E3a-prereg/`): both said "bind after fixes". Both confirmed the
S-shuttle correction (k 8192 overall, k 32 among gains up to 32, from `freeze.json`), the seeds and the
world blocks.

**What both found:**
- the inactive module's offset test was one-sided (|u| − |u|, not |u_with − u_without|);
- B-task's nose pairs lacked the within-pair symmetry its comparators had, so generation 0 could have
  an offset;
- B-task's τ range was missing;
- B-task's comparison inherited a "working" branch it cannot have;
- the integer rule for S-oracle's reference was missing;
- the stage order could not work: calibration came before the champions existed, and Stage 3 needed
  frozen Stage 2 champions (Astra);
- the checkpoint schedule was missing.

**Fable also found:**
- **the reset, timed 10 ticks after the visit, often finds the head still inside A,** where the relay
  overrides the write. It is now timed from the level's end;
- the state-to-goal assignment for a bistable champion was undefined, and mirrored champions are
  allowed;
- small pins: the random walk's seed, B-shared's routing and ablation, and admission's reserve.

**Astra also found:**
- **the design's root grid can miss a pair of roots inside one cell.** Example: w_qq 1.0119999647,
  b_q 0.0008732175. Rechecked here: the grid finds 1 root, and bracketing at f's stationary points
  finds 3, including a stable root at −0.10934 (f′ −2.7e−6);
- the census interval bounds passing the screen and the full check, not being a working selector;
- the reference is "straight-run", not a strict maximum;
- incomplete runs needed arm-level rules;
- G-E's CPU genomes needed naming.

**The second draft** takes every fix. The departures from the design are listed in its §12.

## D165 — E3a's pre-registration bound (second draft reviewed: both "bind after fixes")

**The review** (`docs/reviews/20261002-E3a-prereg-2/`): both said "bind after fixes" on the second
draft (3a513e6). Fable confirmed every first-draft fix resolved; Astra confirmed most and listed four
remaining gaps.

**Fable's three pins:**
- the state-to-goal rule covers census qualifiers;
- "not applicable" clamp assays count as not passed;
- reset worlds where no write happens stay in the denominator and fail.

Optionally:
- the registered evaluations run first in stage 14;
- E's census-world mean is computed in stage 6;
- compositions are recorded.

**Astra's four gaps:**
- **G1 depended on calibration that comes after it.** The calibration condition now applies only to
  organisms whose states come from calibration.
- **Stage 3's checkpoint skills had no calibration.** Module skill is now measured for Stage 2's and
  Stage 3's champions only.
- **The release test's monostable start could tie** (w_qq 1.0001, b_q 0: roots ±0.0173). It is now
  the root with the most negative f′, ties to the lower q.
- **The projection's workload was not fixed.** It now prices 64 qualifiers per census, caps the full
  check at the 64 best-screened ("at least k" otherwise), recomputes after screening, and gives the
  compositions.

**Bound:** the final text takes every fix, as E4s-1's did after its review (D150). It binds when this
commit is pushed, before any stage of E3a runs. Amendments go in its §13. This is a consensus
decision; the owner is informed.

## D166 — Disclosure: E3a's implementation tests ran the engineered organism on registered worlds

**What happened (2026-10-02, during implementation, before any stage of E3a):**
- The tests of the memory assays, committed in 2bd8107 ("E3a implementation, part 2a"), ran
  the engineered organism E with E3a's registered evaluation world seed (1 171 000) on registered
  blocks:
  - the clamp assays and the reset on assay worlds 947 100 000-947 100 015 (16 of G1's 256);
  - calibration on calibration worlds 948 000 000-948 000 007.
- An exploratory check by Claude then ran E's calibration on calibration worlds
  948 000 000-948 000 015.
- **What was seen:**
  - E's clamp assays and reset passed on those 16 assay worlds;
  - on 16 calibration worlds, E's median level duration was 7 ticks, its median leg after the first
    visit 39 ticks, and its median q in each goal phase ±1.915.
- No champion, control or selector was run on a registered block. No decision, threshold or rule
  depended on what was seen: E, the gates and every rule were fixed in the bound pre-registration
  (989da99) before these runs.

**What changed:**
- The tests now use smoke ids (0-9 999) and a smoke seed (1 179 000).
- A new guard test (`tests/test_e3_hygiene.py`) fails if any E3 test names a registered E3a block or the
  evaluation seed. It was seen failing on the committed version of the assay tests.
- Found by Claude while writing the calibration test. Reported in E3a's results as a deviation.

## D167 — E3a's code reviewed (both "fix then run"); fixes and Amendment 1

**The review** (`docs/reviews/20261002-E3a-code/`, of 910fc7e): both said "fix then run". Both found the
library and the engine changes faithful to the bound text, and the runner not.

**What both found:**
- random sampling's champion ties went to list position, not the draw j;
- S2-b's "neither found" read only the paired runs;
- the gates did not require the earlier gates to have passed;
- the champion stages accepted unsettled batches;
- admission was not the registered calculation (validation priced per champion, an unregistered 0.5,
  no recount after the census, no check that the plan fits, no evaluation admission);
- a failed assertion blocked the registered readings;
- the assertions were incomplete and untested;
- the calibration and test-world compositions were not §5's 32 × 256;
- registered descriptive measures were missing (the per-tick logs, the hysteresis sweep, the training
  offsets, B-shared's memory, the release test on latches).

**Fable also found:**
- the window ran one tick long;
- §6 and §8 conflict on Stage 3's module skill;
- B-task's comparator under reduction step 1;
- G-E did not cover the module-only probes.

**Astra also found:**
- census qualifiers were rebuilt from rounded parameters (reproduced: a float32 parameter changed);
- the projection used the evaluation seed;
- the foraging check used Task N's 32-substep brain and hashed no fields;
- Stage 3 would crash after a final stop of Stage 2.

**Fixed, each with a test seen failing first, or a sabotage:**
- the readings (S2-b over every champion, with its registered wording; "0 of n read"; no ordinary
  interval under the census cap; Stage 3's "neither" branch; B-task against Stage 2 under reduction
  step 1);
- the window (stimulus + W − 1);
- calibration and scoring batched at 32 per chunk;
- the hysteresis sweep and the per-tick logs;
- the runner rewritten:
  - the guards and admission by the stage projections;
  - the census qualifiers kept as genomes with hashes;
  - the champion tie by j;
  - complete assertions, with a sabotage test;
  - a failed assertion makes the batch "not read", per §7's text;
  - the test worlds closed before stage 14;
  - Stage 3 only from existing champions.
- **G-E's CPU leg broadened:** foraging at its own 8 substeps, with fields hashed and its score through
  `rollout`, and E4s-1's "mean" and "swapped" probes.
  - The reference was regenerated at 989da99: every case identical.
  - A sabotage of the mean probe is caught in exactly that case.

**Amendment 1** to E3a's pre-registration (§13, before any stage):
- the §6/§8 conflict, resolved by §6;
- the window's reading;
- the per-tick logs' organisms and worlds;
- the hysteresis sweep;
- the logged generations' offsets;
- the release test on latches;
- the projection's timings and seed;
- the compositions;
- the qualifiers' genomes;
- admission's stage projections;
- B-shared's memory assays;
- Stage 3's runs;
- the guards.

**Running on the review's verdict:** both said "fix then run", which is consent to run once the fixes are
in, as with E4s-1 (D152). No further round is held. The owner asked for the GPU to be used (2026-10-02).
The fixes and the amendment are pushed before any stage runs.

## D168 — E3a ran; its results drafted, for review

**The run:** every stage, from 12:20 to 18:20 on 2026-10-02, used 5.97 of the owner's 30 GPU-hours.
- G-E, G0 and G1 passed. No stage stopped, and every assertion passed.
- No reduction applied (9.26 planned hours, with the reserve).

**The registered readings** (`experiments/E3-ab-organism/E3a/evaluate.json`):
- **S2-a:** "evolution found a working selector in 1 of 8 runs, not reliably".
- **S2-b:** "unclear", −1.49 (90% −2.98 to +0.24).
- **S2-c:** none of 1 024 draws in either census passed the screen and the full check.
- **Stage 3:** "better", +2.36.
- **B-task:** "worse" than Stage 3, −3.73.

**Descriptive:**
- random sampling's champions are working in 7 of 8 runs (5 latches);
- four champions are "bistable, not a latch", with memories that hold behind gates that leak;
- several monostable champions score highly, which was not examined.

**The results draft** (`RESULTS.md`) was checked against `summary.json` before committing. Five
statements were corrected by Claude in that check:
- E compared with L1-switch on other worlds;
- three tuned organisms beating E, where there are four;
- a ratio range;
- a rounded clamp share that hid a failure;
- the explanation of "unclear".

A results review by both follows.

## D169 — E3a's results reviewed (both "fix"), corrected; published on main

**The review** (`docs/reviews/20261002-E3a-results/`, of f70c949): both said "fix". Both found every
registered reading correct by its rule and wording. Astra independently recomputed the readings, their
intervals, the working flags, the census bound and the champion selections.

**What both found:**
- the inactive gain range (0.059 to 0.068, not 0.060 to 0.067);
- rounded bounds below their maxima;
- τ values not in `summary.json`;
- "memory-less" overread: the release test cannot separate a faded q from a weak gate;
- "every champion" included B-task's untested champions.

**Fable also found:**
- times given without a zone;
- the push claim uncited;
- the four partial gates' release failures and 2-tick results unreported;
- the 1-against-7 contrast resting partly on the clamp assays;
- "beat E" without a paired test, omitting GA run 4;
- the deviations' gaps: Amendment 1 followed the peek, and the rewritten runner was never reviewed as
  code;
- registered descriptive measures not pointed to.

**Astra also found:** G0's blind threshold misstated as 0.5 visits; it is 0.5 × L1-switch's mean.

**Astra's first attempt failed** ("unable to review"). The pinned Codex settings
(`--ignore-user-config`) had also dropped the owner's `windows.sandbox="elevated"`, so Codex refused even
read-only commands. That setting is now pinned, a command-level connectivity check passed, and the
review was rerun. Both attempts are archived.

**Corrected:** 13 dated corrections in `RESULTS.md`, each quoting the first draft. `summary.json` now holds
the Stage 3 time constants, the release-test ratios and the 2-tick classes. Claude's own checks of the
new numbers before committing caught two errors in the drafted fixes (a 0.43 for 0.49, and 9 for 8).

**Published on main** on both reviewers' "fix", by consensus (as E4s-1, D154-D155); the owner is
informed.

## D170 — E3a published on main

`main` was fast-forwarded to the reviewed `roadmap` tip (62bd626), and the working-branch banner
removed there (7048824). `roadmap` continues from `main` with its banner, which now names E3b's design
as next. A consensus publication (D169); the owner is informed.

## D171 — E3b's design started (v1, for review)

**The owner, 2026-10-02:** "start E3b's design" (after E3a's publication). The old-engine worktree
(989da99) was removed at the owner's request.

**Design v1** (`docs/E3/E3b-DESIGN.md`) proposes staging E3b as E4s was:
- **E3b-0:** exploratory, at most 3 GPU-hours. The engine changes (mazes, two wall-masked trails,
  per-wey goals and deposit timers, wall sliding), the scripted controls, and the seed design's
  feasibility in the maze.
- **E3b-1:** pre-registered, about 25 GPU-hours. Joint tuning of the seed in colonies against the seed
  on unseen mazes (the roadmap's gate), with the peer-signal controls.

**An engine survey** found that the engine lacks all of these:
- interior walls and mazes;
- more than one trail per swarm, and walls that block diffusion;
- shuttle colonies (one wey per world);
- per-wey timers.

**Seven questions** go to the reviewers, including whether a literature check on two-pheromone
trail models (cited from memory, unverified) must come first (D143's standard).

## D172 — E3b's design v1 reviewed (Fable: proceed with fixes; Astra: revise); a bounded literature check; design v2

**The review** (`docs/reviews/20261002-E3b-design/`): both kept the staging.

**What both found:**
- E3b-1's budget was not credible: about 47 h for two training arms by E3a's measured rate;
- a time-decaying deposit points toward its source only if it decays faster than evaporation;
- replay on the same tree maze keeps route information;
- the seed has no exploration mechanism;
- own trails need exact per-wey fields;
- trees first;
- a literature check before fixing the trail rule.

**Fable also found:**
- a tuned seed could win by locomotion alone (hence a 2 × 2 of trail-evolved and no-trail-evolved
  colonies, each evaluated with trails on and off);
- bodies as a second peer channel, and the spawn crowding;
- peers become redundant after a round trip;
- the v1 geometry was inconsistent;
- the boundary already slides per axis.

**Astra also found:**
- confirmed visits alternate by construction;
- the +2.36 misattributed to "against E";
- identical mechanics are needed across arms;
- several engine assumptions (one score per world, Task N disabling pheromones).
- Astra also checked two of my from-memory citations and found them different from the design.

**They disagreed** on the wall reflex. Fable: sliding first. Astra: an engineered reflex. E3b-0 builds
both and decides on evidence.

**The literature check** (`docs/E3/E3b-LITERATURE.md`), bounded and verified:
- two direction-specific trails are established practice (Panait & Luke 2004), but their update rule is
  a dynamic-programming-like adjustment, not an additive deposit;
- pheromone trails alone carry no polarity in real ants (Jackson et al. 2004), so E3b's direction must be
  engineered and measured;
- evolved neural agents with pheromone exist (Jimenez-Romero et al., full text: single-run comparisons).

**Design v2** (`docs/E3/E3b-DESIGN.md`) takes every point, with a dated correction. E3b-0 now has six
exit criteria before E3b-1 is designed and pre-registered.

## D173 — E3b's design agreed at v2: both "proceed to E3b-0's plan"

**The review** (`docs/reviews/20261002-E3b-design-v2/`): both said "proceed". Astra also read the sources
again. This is a consensus decision; the owner is informed.

**Literature corrections** (dated, in `docs/E3/E3b-LITERATURE.md`). D172 said:
- "pheromone trails alone carry no polarity in real ants". It is an absence of evidence, in one species;
- two trails per direction are "established practice". They "have precedent";
- Jimenez-Romero et al.'s comparisons are "single-run". There is one evolutionary run per condition, with
  100 evaluation trials.

Both reviewers caught the first; Fable the second; Astra the third. D172 stands as written, corrected
here.

**Pins carried into E3b-0's plan:**
- the seed cannot explore (Fable: the carrier circles within about ±6 cells), so the "maze-ready"
  additions are listed, labelled and given to every arm;
- the wall follower is a ceiling, not a bar;
- sensing leaks through walls (Astra: a nose inside a wall cell interpolates the far side);
- the fallback trail rule breaks the linear peer controls;
- the trail's range is tight against L1's 70× window;
- a behavioural polarity test (turning round on a trail);
- "own only" cannot improve first discovery, so shared > own > none is read on repeated trips;
- the gate's power, not only the scripted follower's;
- failure branches;
- the update order, the rate conventions and the inequality's assumptions;
- the equivalence tolerances.

## D174 — E3b-0's plan v1 reviewed (both "fix then run"); plan v2, with a second candidate seed

**The review** (`docs/reviews/20261002-E3b-0-plan/`): both said "fix then run".

**What both found:**
- the polarity test needs nulls;
- replay and scramble were unpinned;
- the seed under own trails was missing;
- unpinned numbers;
- the power criterion was not a power calculation;
- depth-first-search mazes branch little. That was measured: 4-7 dead ends. It is fixed with Wilson's
  algorithm, at 0.29-0.32 (00fa5d5).

**Fable also found:**
- the trail grid barely reached the feasible region (λ was tied to μ);
- the equal-split diffusion ridges corridors at 3:4:3;
- the maze search used trail constants not yet chosen;
- "highest score" would pick the wall-follower variant;
- the later-leg confound;
- the headroom was too thin for the power target.

**Astra also found:**
- the oscillator cannot exist without adaptation state;
- corners leak in sensing and movement;
- "round trip" was mislabelled;
- shared = own could pass;
- retries reused the report mazes;
- the failure handling was incomplete;
- the power target decides the pass (23.4% at 80% power, 27.6% at 90%).

**The owner, 2026-10-02:** "yes, add it as a second candidate". E3a's Stage 3 run 3 (15.98) joins E as a
candidate seed. It gets its own variant under the least-engineered rule, and a fixed choice between
seeds with ties to E. The choice is labelled exploratory. Its risks are stated in advance: a partial
gate, tuning to the open arena, and a winner's curse.

**Plan v2** takes every fix; its §9 maps them. A confirmation round follows.

## D175 — E3b-0's plan agreed at v3 (both "fix then run" on v2); the gate's power computed first

**The review** (`docs/reviews/20261002-E3b-0-plan-v2/`): both said "fix then run". Fable said no further
round was needed, and Astra's verdict also permits running after the fixes. A consensus decision; the
owner is informed.

**What both found:**
- the power criterion's comparison, test size and variance shape were unstated;
- the "flat" polarity null was not established;
- exposure matching was circular;
- `maze.py` redrew walls, contrary to the plan.

**Fable also found:**
- the seed rule reopened "highest score picks W2";
- the seed's trail effect was tested only on the selection mazes;
- Stage A was not rechecked;
- the CV divides by E's mean (also Astra: 0.282 against 0.267).

**Astra also found:**
- the 90% bootstrap is anticonservative (7.9% under the null);
- failure handling must branch on what actually fails, and requalify after changes;
- the donors' endpoints must differ.

**The power, simulated first** (`scripts/e3b0_power.py`):
- one-sample run differences against the fixed seed, two shapes, CVs 0.15-0.40, three rules;
- the bootstrap rejected 7-9% under the null; the t-test and sign-flip test were near 5%;
- with a calibrated test, the minimum effect detected with 80% power is 0.25-0.28 of the seed's mean for
  8 runs, 0.20-0.22 for 12, and 0.17-0.19 for 16;
- so E3b-1's gate needs 12 runs per arm and a calibrated test.

**Code fix** (60d0de9, test-first): `maze_for` keys the walls by maze and the placements by episode,
draws only eligible pairs, and never redraws walls.

**The oscillator M was found within the genome's bounds** in the engine's update rule: two neurons with
self-weight 1.5 and antisymmetric cross weights ±1, period about 9.9 ticks per unit of τ.

Plan v3 takes every fix; its §10 maps them. Implementation follows.

## D176 — E3b-0's engine pins: W2's resting turn, S3r3 rebuilt from its record

Two implementation pins the plan (v3) left open, decided by Claude while building E3b-0's engine
(2026-10-02). Neither changes a registered text; both are disclosed in E3b-0's results.

**W2's resting turn.** The plan gives W2's reflex neurons bias −0.5 and "the carrier's turn bias at +0.4".
A tanh neuron at bias −0.5 rests at tanh(−0.5) = −0.46, not 0:
- in W1 the two sides' outputs (±3) cancel, so its resting turn is the carrier's 0.2;
- in W2 (left ±3, right ±1.5) they leave a net push of +0.69 on each dorsal turn neuron (−0.69 on each
  ventral), and the turn command would sit at the clamp (2 tanh(0.20 + 0.69) = 1.43).

So the carrier's turn bias is set so that the **resting turn command** is the declared one: 0.4 for W2 and
its M variants, 0.2 for W0, W1 and theirs (`maze_organisms.carrier_turn`; tested: the settled turn is
0.2 or 0.4 within 0.002). That is the plan's evident intent, "a wall follower" curving left at 0.4.

**S3r3 is rebuilt from the committed record,** not from a local genome file. Stage 3 changed only grafted
parameters (47 edges, 9 neurons' τ and bias; the worm block is the carrier's, checked), so the grafted
values in `champions-3.json`, set on E's carrier genome, give S3r3 exactly: its sha256 equals the record's
(57414a22…). Anyone can rebuild it without a genome file.

**Also pinned while building** (`wormwars/e3/maze_world.py`, tests in `tests/test_e3b_maze_world.py`):
- the start headings come from their own stream keyed by (run seed, maze id, episode);
- the supercover test treats each wall cell as a closed square, and the grid's outside as wall;
- the scramble permutation comes from a stream keyed by (run seed, maze id, episode);
- the scripted reflex used by the scripted controls is W1's steady-state turn on a silent carrier (next
  commit).

## D177 — E3b-0's runner and measures: the pins taken while building, and the power figures made traceable

Decided by Claude while building `scripts/e3b0.py`, `wormwars/e3/maze_measures.py` and
`wormwars/e3/maze_runs.py` (2026-10-02), before any formal stage ran. E3b-0 is exploratory; each pin is
disclosed in its results.

**A leftover in plan v3.** §4's Stage B rule still reads "pass(real) − max(pass(none), pass(flat))", but
§3b replaced the flat trail with the route-permuted one (both reviewers). The runner uses §3b's
route-permuted trail.

**The power figures, made traceable (rule 5).** Plan v3's table (8 runs 0.25-0.28, 12 runs 0.20-0.22,
16 runs 0.17-0.19) and D175 quoted figures that were not in the committed `power.json`, which held 8 runs
on a 0.05 grid only. `scripts/e3b0_power.py` now writes a `fine` block (8, 12 and 16 runs, a 0.01 grid,
4 000 trials, seed 20 261 004), with its first output unchanged. Under the t-test it gives 0.25-0.28,
0.19-0.22 and 0.17-0.19. The conclusion stands: 8 runs fail the 0.25 criterion and 12 pass. The plan's
table carries a dated annotation. Criterion 2's headroom uses 0.22, the larger of the two shapes at
12 runs and CV 0.282.

**Pins in the measures and drivers:**
- **The maze run seed** is 1 180 000 (the plan names none).
- **Legs:** a wey's legs are its visits − 1.
- **The later-leg rate** runs from the first-visit tick to the horizon. A colony with no first visit
  scores 0, and the unvisited share is reported beside it.
- **The route cells** are the open cells of the tree path's maze cells and of the gaps between them.
- **The gradient share** compares each route cell with the mean of its route neighbours one step nearer
  the source. Each trail is read toward its own source, and A's and B's are averaged.
- **The polarity test:**
  - the A trail is snapshotted at the oracle's B visit and aged by that leg's duration;
  - the start is the route's middle maze cell, facing its next cell toward B, with jitter keyed by
    (run seed, maze id);
  - a pass enters A within twice the oracle's time from the same start;
  - mazes where the oracle made no single pass are left out, and their number is reported.
- **The nose range** counts both noses' goal-channel inputs on ticks whose sensing position was on route.
- **Stage A's colonies** have 8 weys for every control. The oracle and the blind controls play with
  access none, since they read no trail.
- **The replay donors** play with shared trails. The coefficient is shared exposure over donor exposure
  at coefficient 1, from one selection-maze pre-pass.
- **The component tests' latch states** are the seed's own stable roots of −q + w·tanh q + b (E's are
  ±1.915), the upper root for A.
- **The timing projection** uses 500 generations (E3a's Stage 3), 12 runs per arm, two training arms and
  a 25% reserve. It covers training only.

**The engine was made faster without a change in rule.** The supercover test is vectorised over its 3 × 3
window, and each use batches its segments into one call. One occlusion geometry now serves both the
signal and the exposure reading. A tick at 256 worlds × 8 weys on the GPU fell from 114 ms to 8.9 ms. The
maze tests pass unchanged.

## D178 — E3b-0's Stage B chose no setting; diagnosed, reviewed twice, and amended (Amendment 1)

**What happened (2026-10-02/03):**
- **Stage A** (41fcb68) chose c = 5, H = 2 400. The four H = 1 200 candidates failed only on the
  follower's median legs.
- **Stage B** (4ac36b6) chose no setting:
  - polarity read −0.06 to +0.02, against 0.3;
  - the nose range read 0.26-0.46, against 0.9;
  - the gradient passed in 22 of 24 settings. The two at μ 0.005, λ 0.01, δ 0.05 scored 0.797.
- E3b-0 had used 0.74 of its 3 GPU-hours.

**Claude's diagnosis and its errors.** Two CPU diagnoses (4004e4e, 85bdffc; `development-records/`) found
that trails help the scripted follower, with a peer effect. At Stage B's highest-rate setting, in legs per
1 000 ticks: shared − none +2.85 [1.83, 3.92], own − none +1.09 [0.39, 1.92], shared − own
+1.75 [0.93, 2.64]. Polarity and range failed on how the tests were defined. The reviewers corrected the
claims as follows.
- **"Cannot pass" was too strong** (both). The registered start was not passed on 64 mazes, even on a
  reference slope: arrivals 9% at 2×, 42% at 4×, readings near 0.
- **"Toward A" was mis-implemented** (both): away + π faced a wall where the route bends (45 of 64 mazes).
  It now faces the route's previous cell.
- **"The gradient passed everywhere" was wrong** (Astra): two settings scored 0.797. This is corrected in
  9e5e02d's message.
- **The 0.3 ceiling holds for the toward start only** (both).
- **The diagnosis's reference slope has a centring ridge** (Fable).
- **The draft's fixed wording claimed a mechanism** (Astra). It is replaced with a neutral sentence.

**Bugs the reviews found, fixed test-first (9e5e02d):**
- shared exposure was recorded as 0, which would have set the replay coefficient to 0 (Astra);
- Stage C did not check that the recheck passed (Astra);
- the polarity test's start is fixed as above.

**The decision, by consensus.**
- **First review** (`docs/reviews/20261002-E3b-0-stage-b/`): both said "amend and continue", not the
  plan's nonlinear fallback. Nonlinear trails would not help a follower that does not turn round, and they
  would break the linear peer controls. "Controller failures never change the trail rule" argues against
  the fallback here, not against repairing the tests.
- **Confirmation round** (`docs/reviews/20261003-E3b-0-amendment-1/`): both said "confirm with fixes",
  with no further round. The plan's "Amendment 1, as confirmed" section carries every fix:
  - the high-level cap (at most 5% of unoccluded positive on-route inputs above 0.35), on the follower and
    then on the chosen seed;
  - the pinned trail-effect gate;
  - the widening limited to directions where the rate still rises;
  - criterion 4 at the seed's measured quantiles, floored at 0.001, with one-nose checks;
  - §6 reconciled: no fallback, a report and a redesign instead;
  - the reuse of Stage A's and Stage B's records by hash, with `stage-b2`'s shared rates required to equal
    Stage B's;
  - per-row configuration hashes.

**The expected outcome, recorded before `stage-b2` runs (Fable).** Under the cap, only the weakest trails
qualify, and the expected winner is μ 0.02, λ 0.04, δ 0.05, d₀ 0.2855. Criterion 3 then probably fails, as
a weak signal. The cap keeps the seeds' modules in their working range at the cost of the trail's signal.

**The projection.** About 1.0-1.3 of the 2.26 GPU-hours left for `stage-b2` and everything after it.

**Labels.** Everything chosen under Amendment 1 is adaptively selected (decided after seeing Stage B).

**Who caught what:**
- Fable: the saturation half of the range test is a real property of the trails; the cap's likely
  selection; the record's base configuration; d₀'s invariance; the probe's floor.
- Astra: the replay bug; the recheck guard; the seed-side cap; the reuse guard; the one-nose checks; the
  wording.

## D179 — E3b-0: `stage-b2` qualified nothing; diagnosed with the seeds; Amendment 2 (the cap on the seed, at 1.0)

**What happened (2026-10-03):**
- `stage-b2` (19a1b12) qualified no setting under Amendment 1's cap: at most 5% of the follower's inputs
  above 0.35, with a positive trail effect.
- Claude's interim report (9b4ea2e) proposed compressed sensing, on a gain-mismatch hypothesis.

**The redesign review** (`docs/reviews/20261003-E3b-0-redesign/`):
- **Fable, "something else":**
  - the 0.35 cap misread K_D. K_D is the response to a fixed absolute difference; along a linear trail what
    matters is K_D × level, which for E stays at 11-16 up to 1.0;
  - so test the seeds first.
- **Astra, "compressed sensing, with fixes",** after a pinned diagnostic. She corrected the baselines (3.944
  and 3.251 on the GPU against 3.327 on the CPU) and several overreaching statements.
- **Both:** the hypothesis was not established.
- **Not adopted:** compressed sensing. There was no consensus, and it would change the organisms' sensing,
  which would go to the owner first.

**Diagnosis 4** (db509aa):
- **The seeds:**

  | E + W2 | No trail | Best-rate setting | Medium setting |
  |---|---|---|---|
  | Later-leg rate | 1.77 | +1.27 [1.01, 1.53] | +0.53 [0.34, 0.75] |

  E + W0, E + W1 and S3r3 with every variant tested barely move through the maze. S3r3 + W2 circles, with a
  turn bias of −0.76.
- **The follower:** its effect is steering on the trail. With the occluded nose ignored it gives +3.42; at
  gain 128 on trails laid 4× lighter, +3.02.

**Amendment 2,** drafted (fa259f0), reviewed (`docs/reviews/20261003-E3b-0-amendment-2/`), and confirmed by
both with fixes and no further round:
- the high level is 1.0, from E's K_D × level;
- **the cap is measured on the seed E + W2** (Fable's design; Astra also prefers the seed);
- criterion 4 above 0.35 requires K_D × level ≥ 10.5 (30 × 0.35), and runs before the report mazes;
- one retry was proposed by Fable; there is none, after Astra.

**Fixes:**
- **The M oscillator never started** in the maze runner: all-zero initial state, zero biases, no inputs
  (Astra). `maze_organisms.brain` now starts M1 at 0.1, tested failing first.
- **The reuse evidence is now per maze:** `stage-b2`'s behavioural arrays equal Stage B's on all 24
  settings; only exposure differs, as its fix requires.
- **`stage-b2`'s record** joins the hash-checked transition.

**Corrections** to Claude's statements, now in `INTERIM-REPORT.md`:
- the K_D misreading;
- "no setting can qualify";
- the near misses;
- the light row;
- the baselines;
- "peer effect";
- the effect range in 95a6bdc's message (−0.31 to +0.52, not +0.15 to +0.52).

**Labels.** Everything chosen under Amendment 2 is adaptively selected.

**Projection.** About 2.4-2.6 of the 3 GPU-hours in all.

**Who caught what:**
- Fable: the K_D × level reading; the seed-side cap; 10.5; the gain-0 wording; the widening's cost.
- Astra: the oscillator bug; criterion 4 before the report mazes; per-maze equivalence; the baselines; the
  narrower conclusion.

## D180 — E3b-0 completed, its results reviewed (both "fix then publish") and corrected; published on main

**The run** (2026-10-03). After Amendment 2 (D179):
- `stage-b3` chose μ 0.01, λ 0.02, δ 0.05, d₀ 1.142 (ab5cdbe);
- the recheck passed (6c7dd17);
- Stage C chose the seed E with W2 (82fb7e0). S3r3 failed with all seven variants;
- the report passed both pre-checks on the selection mazes: the seed cap and criterion 4 (b55e32e);
- the timing ran (c769a49).

E3b-0 used **2.62 of its 3 GPU-hours.** `stage-b3` cost about 1.0, against the 0.5-0.7 projected, because
its 30 widened settings each needed new runs.

**The results** (`experiments/E3-ab-organism/E3b-0/RESULTS.md`, 7b65b75), on the report mazes 1000-1255.
Legs per 1 000 ticks:

| Contrast | Follower | Seed E + W2 |
|---|---|---|
| shared − none | +3.57 [2.97, 4.19] | +0.69 [0.44, 0.93] |
| own − none | +2.06 [1.54, 2.61] | +0.43 [0.28, 0.59] |
| First-B time of later discoverers, shared − own | −61 ticks [−107, −18] | −196 ticks [−242, −150] |

- **Replay and scramble fall below own and below none.**
- **Behavioural polarity** was not passed.
- **The criteria:**
  - criteria 2-4 passed;
  - criterion 5 failed as sized: E3b-1 projects to about 71 GPU-hours;
  - criterion 6 holds conditionally on the assumed run-level spread.

**The review** (`docs/reviews/20261003-E3b-0-results/`): both said "fix then publish". Every number checked
against the records. The fixes made before publication are listed in RESULTS.md's Corrections. Among them:
- "exposure matched" held for replay only, and only approximately;
- a mechanism claim for replay and scramble was withdrawn;
- polarity's scope is limited to the settings tested;
- criterion 1 is "incomplete";
- K_D × level at 0.89 is 15.2;
- the seed versus W2 alone (+1.09 visits per wey of 5.78) is now in the summary.

Two missing records were added:
- **The final-code CPU equivalence** (`development-records/compare-final.json`, at 7b65b75): every earlier
  task is bitwise identical to 84ff98a (Fable).
- **S3r3's turning,** as a committed diagnosis (`development-records/diagnosis-5-turning.json`).

**Who caught what:**
- Fable: the stale equivalence record; the exposure of scramble; the seed versus W2; the polarity scope;
  the `active.passed` flag.
- Astra: the reviving of withdrawn claims ("could not", "no effect", "before it affected"); the exposure
  percentages; the conditional power.

**Publication.** By consensus (both reviewers), under the owner's rule for main pushes (D112, as extended on
2026-09-29), with the owner informed afterwards:
- `main` is fast-forwarded to `roadmap`;
- the working-branch banner is removed there;
- `roadmap` continues from `main` with its banner.

**Next: E3b-1's design.**
- **Its budget must be cut.** Both reviewers would cut generations first and keep 12 runs per gate arm.
  They differ on how far: about 125 generations at 16 worlds (Astra), or 250-300 at 8 worlds with 6
  no-trail runs (Fable). E3a's slow climbers gained after generation 375.
- **Owed before its runs:** the GPU leg of the equivalence check.

## D181 — E3b-1's schedule (the owner's decision); design v1, for review

**The owner, 2026-10-03.** Asked whether both reviewers' training proposals could run side by side, the owner
proposed: "8 at 125 and other 8 at 300 but with a check at 125 … diagnostic coverage for both proposal at a
50% budget increase". After Claude's arithmetic, the owner said "Sure".

**The arithmetic.** Per training arm:
- Astra's 12 runs × 125 generations × 16 mazes: 7.1 GPU-hours;
- the owner's mix, 8 × (125, 16) plus 8 × (300, 8) with a champion at 125: 10.4 GPU-hours, or +47%.

**Two consequences of the mix:**
- **Each half has 8 runs,** which is below the power criterion (25-28% of the seed's mean detectable at
  80% power). So the registered gate pools all 16 final champions, which detect about 17-19%, and the
  schedule comparisons are secondary.
- **The no-trails arm stays small** (6 runs) to fit the owner's ceiling.

**Design v1** (`docs/E3/E3b-1-DESIGN.md`) projects about 18.4 GPU-hours in all, within the plan's 24 and the
roughly 27.4 left of the owner's E3b ceiling. It goes to both reviewers. Six questions are open:
- the pooled gate;
- a margin;
- the champion rule;
- the no-trails arm's mode;
- the trail measure;
- what is missing.

## D182 — E3b-1's design v1 reviewed (Fable: proceed with fixes; Astra: revise); v2, with the gate simulated as computed

**The review** (`docs/reviews/20261003-E3b-1-design/`). Fable said "proceed to the pre-registration, with
fixes"; Astra said "revise". Without a consensus, a v2 follows (`docs/E3/E3b-1-DESIGN.md`), taking every
point. Its §8 maps them.

**Errors in v1 that the reviewers caught:**
- **The champion rule was undefined** (both). `evolve_batch` keeps no per-genome history.
- **v1's statement that E3a validated whole populations at every checkpoint was wrong** (Astra). E3a
  validated one winner per checkpoint, and chose its champion from the final population.
- **The 16-run power figure,** 0.17-0.19, is 0.18-0.19 at CV 0.282 (both).
- **W2 would have been mutated** by the existing mask (both).

**The gate, simulated as computed** (`scripts/e3b1_power.py`, `experiments/E3-ab-organism/E3b-1/power.json`):
- **The rule:** the equal-weight mean of the two schedules, tested by a one-sided Welch t-test within
  schedules.
- **False positives:** 4.4-5.3% in every scenario, including opposite effects averaging zero.
- **The minimum detectable effect:** 0.18-0.19 at CV 0.282, 0.20-0.21 with unequal spreads, and 0.25-0.27
  at CV 0.40.
- **The pooled t-test and the sign-flip test** keep about 5% with equal effects, and are conservative
  (about 3%) with opposite effects. They are reported as sensitivity checks.

**v2's other changes:**
- no margin in the test: a lower bound and a 10% descriptor instead;
- all 32 genomes validated at each read point;
- a learning curve;
- a recovery-control arm R (2 runs);
- named, disjoint maze blocks, with a new test block and the seed re-evaluated;
- a read-only check at generation 125;
- a repeated-journey condition on "better";
- Holm's correction across three secondary tests;
- "trail dependence";
- a benchmark before training.

**The compute:** about 21.2 GPU-hours, within the plan's 24 and the roughly 27.4 left.

**Next:** both reviewers' confirmation of v2, then the pre-registration.

## D183 — E3b-1's design v2 confirmed by both; the power scripts' empirical scaling corrected

**The review** (`docs/reviews/20261003-E3b-1-design-v2/`): both said "proceed to the pre-registration, with
fixes; no further design round". The design is agreed. The fixes are listed in "v2, as confirmed", at the
end of `docs/E3/E3b-1-DESIGN.md`:
- the maze run seed;
- W2's freeze in full;
- every secondary test's statistic and direction;
- the evaluation roster;
- the read at generation 125 (index 124, before selection);
- the run-level spread as the within-schedule SD;
- "trails off" as access none;
- the legs median as a median over mazes of colony means;
- a rule for crashed runs.

**A bug Astra found, confirmed.** Both power scripts standardised E3a's eight Stage 3 means with the sample
SD (ddof 1) and then resampled them with replacement. That gives variance 7/8, so the "empirical" rows
simulated 0.935 × the nominal CV: 0.264 for 0.282.
- **E3b-1** (not yet registered): `scripts/e3b1_power.py` now uses ddof 0, and `power.json` is regenerated.
  The empirical rows' minimum detectable effects rise:

  | Scenario | Before | After |
  |---|---|---|
  | CV 0.282 | 0.18 | 0.19 |
  | CV 0.40 | 0.25 | 0.27 |
  | Unequal spreads | 0.20 | 0.21 |

  They now match the normal rows. The design's §5 carries a dated correction.
- **E3b-0:** `scripts/e3b0_power.py` is left as it was, so that its committed `power.json` reproduces, with
  a dated correction in its docstring. Its empirical rows were slightly optimistic. The normal rows are
  unaffected, and those set the 12-run decision and the 0.22 used in criterion 2's headroom. E3b-0's
  conclusions stand. Its RESULTS.md gains a correction entry.

**Next:** the pre-registration, reviewed by both, bound and pushed before any run. Then the implementation,
the GPU equivalence leg and the benchmark.

## D184 — E3b-1's pre-registration draft 1 reviewed (Fable: bind after fixes; Astra: revise); draft 2

**The review** (`docs/reviews/20261003-E3b-1-prereg/`):
- **Both confirmed:** the gate's complete-data formula, the read points against `evolve_batch`, all nine
  fixed-input hashes, and the budget arithmetic.
- **Fable said "bind after fixes"; Astra said "revise".** Without a consensus, draft 2 follows. Its §15
  maps every point.

**Draft 1's gaps:**
- the gate's standard error hardcoded 8 runs per schedule, though runs can fail;
- no deterministic rule separated a failed run from a failed stage, though `evolve_batch` aborts the whole
  lockstep batch on any non-finite score;
- "not read" was all or nothing, so a failed replay could have voided the gate;
- shrinking Holm's family was an unlisted departure;
- cut 3 left the final read at index 299;
- the admission formula put the reserve on non-training stages, against the design's pin 11, and did not
  require `g-e` to pass;
- the access mode for validating champions was unstated (N could have been selected on trails it does not
  sense);
- several denominators were implicit;
- E3a's memory assays were promised without the stimulus calibration they need;
- the power section and the design's scope caveat were missing;
- the learning curve has 200 points, not 176 (both; Astra corrected her own earlier figure).

**Draft 2's answers:**
- n_A and n_F throughout, with ν in full and SE = 0 handled;
- deterministic reruns, with no population taken from a stopped attempt;
- a table of what each reading needs, and a fixed order of evaluation blocks, so partial blocks still count;
- Holm stays at three tests, an unread test entering at p = 1;
- G_F − 1 throughout;
- one admission formula, with × 1.25 on training only, and `g-e` required to pass;
- each arm validated under its own access;
- every denominator pinned;
- the latch structure, with component tests at its stable states, in place of the memory assays;
- §8 for power, with the scope of the CV and of the shifted null.

**The budget:** about 17.6 GPU-hours, 21.4 with the training reserve; the cap is 24.

**Next:** both reviewers' confirmation, then binding.

## D185 — E3b-1's pre-registration draft 2 reviewed (Fable: bind, with last fixes; Astra: revise); draft 3

**The review** (`docs/reviews/20261003-E3b-1-prereg-2/`):
- **Fable said "bind", with last fixes.** Astra said "revise".
- **Astra confirmed** all nine hashes at 6d251fd, the unequal-n Welch formula, the validation access, the
  index-249 cut, the three-test Holm family and the power qualification.

**Specification gaps both found:**
- zero spread was handled only for G's label, while Holm needs numeric p-values;
- the sign-flip statistic with unequal n was undefined;
- the benchmark's arithmetic counted checkpoints twice;
- the donor chunk is 4 096 worlds, not 8 192;
- partial evaluation: which attempt supplies an observation, and the save granularity (per chunk, not per
  block). D184's "partial blocks still count" was not yet true;
- training attempts needed a cap and defined paths;
- `evolve_batch` must name the non-finite runs before it aborts;
- `g-e` must fail on a mismatch;
- the probes' threshold: K_D × m ≥ 10.5 applies only at 0.35 < m ≤ 1.0. As drafted it would have failed
  the published seed at 0.001;
- the levels are taken at full precision;
- the nose recorder's counts are required;
- `champions` is admitted only if `evaluate` also fits;
- stale cross-references;
- the stage-level failure rule is a departure.

**A slip carried from an earlier review.** The shifted null at CV 0.282 needs 0.29-0.31, not 0.28-0.31;
0.28 is the CV-0.267 row (Fable, whose own draft-1 review introduced the figure). The same slip is in the
design's §5 and in "v2, as confirmed". Those texts stand as they are, and this entry is their correction.

**Draft 3** takes every fix. Its §16 maps them.

**Next:** both reviewers' confirmation, then binding.

## D186 — E3b-1's pre-registration bound

**The review of draft 3** (`docs/reviews/20261003-E3b-1-prereg-3/`): both said "bind", with last fixes and no
further round. A consensus.
- **Astra confirmed** the nine hashes at 1c86190, the power figures against `power.json`, and that the
  corrected probe thresholds pass E3b-0's published seed.
- **Fable confirmed** the read points against `evolve_batch` (no breeding at the last generation) and every
  helper the text relies on.

**The last fixes, applied:**
- the replay pre-pass's two legs, in the text and in the projection;
- the projections recomputed over completed runs;
- the power script's sign-flip equals the registered statistic only at equal n;
- `champions` atomic, and required by `evaluate`;
- the nose recorder covering every champion under shared trails;
- the cost of an unchanged second attempt after a non-finite score, stated.

**Binding.** `experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md` is final and binds with this commit,
pushed before any stage of E3b-1 runs (rule 2).
- **The cap:** 24 GPU-hours, within the owner's E3b ceiling.
- **The gate:** a stratified one-sided Welch test on the 16 final champions of the owner's two schedules
  (D181).

**Next, before any formal stage:**
- the implementation, test-first, to §12's twenty tests:
  - the freezing mask;
  - the snapshot hook;
  - the failure rules, with non-finite runs named;
  - the champion rule;
  - the runner `scripts/e3b1.py`;
- a code review by both;
- then `project` and `g-e`.

## D187 — main brought up to date before E3b-1 runs (the owner's choice); the READMEs and review trail completed

**The owner, 2026-10-03,** asked whether anything was pending for GitHub, "every section". Then, offered
the choice, said: "2a. Also check if the readme s are up to date".

**The check:**
- `main` and `roadmap` matched GitHub;
- five older local branches were fully merged;
- there were no stashes and no uncommitted work. The untracked `runs/` folders are local smoke and
  equivalence outputs, as intended.

**Found and fixed** (1de8cef, 46f6787):
- `docs/REVIEW_TRAIL.md` stopped at E3a; entries 36-43 now cover E3b's episodes;
- `AGENTS.md`'s layout lacked `wormwars/e3/`;
- **the top README:**
  - its detailed "Newest" section was still E2's, and is now E3b-0's;
  - its roadmap list still said E3b-1's budget had to be cut from 71 hours;
  - "How this was made" stopped at E4s;
- **the experiment READMEs:**
  - E2d's and E4s's status lines lacked their publication on main;
  - the E3 README's status covered only E3a;
  - E3b-0's README had no status line.

**Publication (option 2a).** `main` is fast-forwarded to `roadmap`, with the working-branch banner removed
there. That brings to main the completed documentation and E3b-1's design and bound pre-registration,
before any stage of E3b-1 runs. The pre-registration was already public on `roadmap`; on main it is
public on the published record as well. `roadmap` continues from main with its banner.

## D188 — E3b-1's code review: both "fix then start"; every blocking finding fixed, test-first

**The review** (`docs/reviews/20261003-E3b-1-code/`): the implementation at d0410a8 (the runner
`scripts/e3b1.py`, `wormwars/e3/tuning.py`, `evolve_batch`'s hooks, `play_batch`, and their tests) against
the bound pre-registration. Same prompt to both. **Fable 5.1:** "fix then start", 4 blocking points.
**Astra 6:** "fix then start", 9 blocking points; Astra also ran 83 tests and reproduced its findings with
stubs.

**Blocking findings, and who caught each:**
1. **A kill during an in-stage attempt 2 or 3 left the stage unrecoverable.** `requires` refused the rerun,
   so no final record was ever written and every later stage stayed blocked (both). Fixed: the rerun runs,
   `train_attempts` ends it at once, and the frame writes the final record.
2. **Kill reconciliation crashed** (Astra). `REGISTERED` lacked `rerun_kill_tail_seconds`. The frame also
   saw no durable progress: training wrote none, and `evaluate`'s chunks are not among the frame's files.
   Fixed: the key (900 s, as in E2), and a progress record written at every training checkpoint, every
   champion read point and every evaluation chunk.
3. **In-stage admission ignored the running process's hours** (both). Fixed: `spent_hours(cap.t_start)`.
4. **An in-stage refusal wrote no refusal file** (both). It counted as "failed", and later training could
   start. Fixed: the refusal file is written, and a refusal settles the stage first. Runs stopped by the cap
   are now recorded as "not run" (Astra, Fable).
5. **A non-finite validation count named no run** (both). Attempt 3 would have repeated it. Fixed in
   `evolve_batch`.
6. **Champion validation ran in chunks of 4 × 128 while its record said 32 × 128** (Fable; Astra
   non-blocking). Fixed: one chunk of 32 × 128, in `champions` and in `project`'s timing, as §9 projects.
7. **One denominator gated all four readings** (Astra). Fixed: each reading checks its own needs and
   denominator; S-peer's is the seed's own first-B time.
8. **The secondary tests carried G's better/worse labels and ignored Holm** (Astra; Fable non-blocking).
   S-peer's beneficial −0.1 read "worse". Fixed: each secondary reports read or not read, its alternative,
   its raw and Holm p, a bound in its own direction, and a conclusion only under Holm. S-trail's wording is
   "increased trail dependence".
9. **`readings` crashed after a final `champions` stop** (Astra). Fixed: every reading is "not read".
10. **S-trail's four means pooled different runs and weights from its test** (Astra). Fixed: they use the
    same complete pairs and equal schedule weights, and the decomposition is stated.

**Non-blocking points, fixed:**
- learning-curve observations are kept as fractions of 1/8 (whole counts stay integers, so other experiments'
  records are unchanged) (Astra);
- the replay route overlap is computed (Astra);
- S-gen gets its one-sided bound (Astra);
- earlier training records must be published before the next training stage, and final-stopped records are
  checked like completed ones (Astra, Fable);
- training admission projects `champions` and `evaluate` over completed runs, as §9 says (Fable);
- the evaluation record states each chunk's composition (Fable);
- the g-e hook leg says what it compared: the hook off against the hook on in this code, while the GPU leg
  covers the change itself (both).

**A gap closed with a new test:** a chunk of distinct organisms plays each exactly as it plays alone on the
CPU (Fable: the smoke only ever batched identical champions).

**The rulings, as reviewed:**
- **"W2 alone on the carrier"** is the grafted W2 organism, as §6 says. Both accept it, on one condition: its
  multiple must not be presented as comparable with E3b-0's "+1.09 above W2 alone", which used the scripted
  controller under "none". The reading carries that note.
- **Training's plain `Brain` equals the started brain** for this oscillator-free seed (Astra).
- **The checkpoint subtraction and the conservative evaluation projection** are accepted (both).

**Tests:** 19 new tests (16 for the runner, 1 for tuning, 2 for `evolve_batch`), each seen failing first, except two that already held: the settled rerun, whose
bug was in `requires`, and the distinct-organisms test. Three new sabotage checks were all caught.

**Next:** the full suite, a confirmation pass by both on the fixes, then the GPU stages (`project`, `g-e`)
after telling the owner.

## D189 — E3b-1's confirmation pass: Fable "start", Astra three failure-path fixes; fixed

**The review** (`docs/reviews/20261003-E3b-1-code-recheck/`): the fixes at 78f78a5, same prompt to both.
- **Fable 5.1:** "start the formal stages", with every blocking finding of both reviews confirmed in the
  code, and five non-blocking points.
- **Astra 6:** three problems remain in failure recovery and recording. Astra ran 100 tests and reproduced
  each problem with in-memory stand-ins for the files. All other findings were confirmed fixed.

**D188 said "every blocking finding fixed".** That was premature: Astra found that three paths of findings 1,
2 and 4 were only partly fixed. This entry corrects it.

**Fixed, test-first:**
1. **Settling an exhausted stage needed admission** (Astra; Fable had judged the same path compliant with
   §10's letter, but conservative). After a kill inside attempt 2 or 3, the rerun runs nothing and only writes
   the final record. If admission failed, it became a refusal: "not run" instead of "failed", and later
   training was blocked. Ruling: settlement is not an attempt, so it is not admitted (`settle_only`).
   - **Cost if wrong:** none in compute, since the settlement plays nothing; the frame still checks the cap.
2. **An in-stage refusal recorded its runs as "failed"** (Astra). It now raises `NotAdmitted`, which the
   salvage records as "not run".
3. **A killed rerun's final training record lacked the attempts and the failed runs** (Astra; Fable
   non-blocking). E2's frame builds that record from the progress record. The progress record is now written
   when the stage body starts, and again after every attempt and checkpoint. It carries the attempts and the
   stage's runs, labelled as failed if the stage ends there finally.

**Also fixed** (Fable, non-blocking):
- the final error text no longer says "non-finite" when a kill ended the sequence;
- `readings` with no champions record reads every reading as "not read".

**Not changed** (Fable, non-blocking): a kill is charged up to its last progress write plus E2's
registered 900 s tail. For T-A, a checkpoint interval is near an hour, so a kill could be undercharged by up
to about 40 minutes. The progress writes now also follow every attempt, but the bound stands. The results
will say so.

**Tests:** 4 new, each seen failing first.

**Next:** the full suite; then the formal stages, after telling the owner.
- **No third review round:** Fable confirmed the rest, and Astra confirmed every other finding. These three
  fixes are what Astra asked for, each pinned by a test.
- **Consensus on starting:** both reviewers' conditions are met.

## D190 — E3b-1 Amendment 1: infeasible mazes redraw their walls (both "adopt with changes")

**What happened.** E3b-1's first formal stage, `project`, stopped about 1 second in (no world tick, no
neural update). Maze 9585, at the projection seed, has no eligible A/B placement, and `maze_for` raised, as
it was written to.

**The audit** (`scripts/e3b1_maze_audit.py`):
- about 0.08% of mazes at c = 5 are infeasible;
- the test block holds one (6073); the validation, learning-curve and calibration blocks hold none;
- the registered training schedules hold 37 in 36 (run, generation) pairs;
- E3b-0's unplayed "fresh" block holds two;
- **every registered arm would have crashed,** deterministically, and §5 would have made them final with
  every run failed.

**The proposal** (Claude): redraw infeasible walls, keyed by the id, never the episode. The alternative was
to skip to the next id. Both reviewers accepted the amendment as the instrument and preferred the redraw.

**Changes taken from the reviews:**
- **Disclose the timing** (Astra): after formal work started, and after a geometry-only reading of the test
  block's walls.
- **The exact streams** (both): k = 0 unchanged; `[seed, id, 0x3A11, k]` for k ≥ 1; the first feasible
  walls accepted; at most 64 redraws; a redraw only on empty eligibility.
- **A committed, script-generated predicted redraw list** (Fable), and the redrawn ids in every stage's
  record (Astra), from a pre-flight that builds every maze before the stage starts (Fable).
- **The pre-flight refuses a stage whose donor search exhausts** (Astra): `replay_donors` returned an
  unchecked episode. None does in E3b-1's blocks.
- **A real maze equivalence check** (both). Claude's proposal had said `g-e` covered it, which was wrong:
  `e3_equivalence.py` has no maze case. The check is now bitwise hashes of walls, edges, placements and donors
  over E3b-0's and E3b-1's blocks, every training id set and `project`'s ids, plus a 300-tick CPU trace,
  against a reference written at 171fcc5. Result: all identical; no infeasible maze left; 41 redraws, all at
  k = 1.
- **E3b-0's records untouched** (both): its played blocks hold no infeasible maze. A dated correction sits
  beside its plan's "0 of 2 000".
- **`project`'s attempt 1 kept** (both); the rerun is its one rerun, on the amended commit.
- **The projection-seed clarification** (Fable).

**Corrections to Claude's statements in this episode:**
- "the first [crash] is T-A run 1, generation 97": the batch is lockstep, so it is run 7, generation 50
  (Astra);
- "statistically equivalent": the skip maps ids deterministically and over-weights some feasible ids, so
  only the redraw is rejection sampling (Astra);
- "36 training": it is 37 ids in 36 (run, generation) pairs.

**Noted for later** (Fable): §5's "attempt 2 unchanged" leaves a deterministic setup bug no remedy but an
amendment. To be weighed in E3b-2's design.

**Tests:** 5 new, each seen failing first: 3 for the maze, 2 for the pre-flight.

## D191 — Amendment 1's confirmation: an organism had played a test maze; disclosed and fixed

**The review** (`docs/reviews/20261003-E3b-1-amendment-1-check/`): Amendment 1 as committed. **Fable 5.1:**
"rerun project", with three non-blocking points. **Astra 6:** four fixes.

**The serious one (Astra; Fable did not see it).** The audit's CPU equivalence trace played the frozen seed
for 300 ticks on test maze 6000, twice. Amendment 1's "no organism played on those mazes" was false.
- **What was exposed:** only a hash of positions and events was computed; no score or behaviour was read.
  The organism is the frozen comparator, so no tuning could be affected.
- **Disclosure:** a dated correction now follows Amendment 1 in §14. It is a breach of §4's "opened only in
  the evaluation stage", made by Claude when writing the audit, and it is reported as such.
- **Fix:** the trace moves to mazes 9900-9902, outside every block, with a test. The reference was rewritten
  with the generator at 171fcc5, in a temporary worktree. The comparison passes, with the same 41 redraws.

**The other fixes, each with a test seen failing first:**
- **`g-e` runs the maze comparison** as a leg of its verdict, with a sabotaged-reference test (Astra; Fable
  had asked for it in D190, and D190's "every change taken" overstated this);
- **the redrawn ids survive a kill** in the durable progress records (Astra);
- **a pre-flight refusal leaves a record** (Fable);
- **the audit reports donor exceptions** (Fable);
- **`maze.py`'s module docstring** no longer says an infeasible maze raises (both).

**Tests:** 5 new.

**Next:** the full suite, then `project`'s rerun on the GPU. Fable said "rerun project"; Astra's fixes are
all taken as asked, so there is no further round.

## D192 — E3b-1's results: G "better"; reviewed by both ("fix then publish"), corrected, published

**The run** (2026-10-03/04), at 18.73 of 24 GPU-hours:
- every stage completed;
- every training run completed on its first attempt;
- cut 1 applied (N to runs 0-3).

**The registered readings, on the 256 prespecified test mazes:**
- **G: "better",** Δ = +0.225 of the seed's mean (+1.32 visits per wey), p = 7.2 × 10⁻⁵, with a lower bound of
  +0.166 ("and at least 10%"). T-A's d is +0.069 and T-F's +0.381.
- **S-gen, S-trail ("increased trail dependence") and S-peer** are all significant after Holm.

**The descriptive probes:** no champion meets the seed's active-comparator criteria.

**The review** (`docs/reviews/20261004-E3b-1-results/`): the draft at 84abac1. Both reviewers recomputed
every registered reading from the records, and all matched. Both said "fix then publish". Every fix was
taken:
- **T-A's e** is negative in 7 of 8 runs, with mean −0.06; the draft said 6 of 8 and −0.05 (Fable, Astra).
- **The registered later-leg contrast** under S-trail had been omitted (both).
- **N's trails-off denominator** is the seed's shared mean, and the text now says so (both).
- **Two T-F champions' e** comes partly from a worse "none" (Fable).
- **The selector claim:**
  - "largely does not run through the selector" is replaced by "departure from the seed's measured
    component performance; the route of the gain is not established";
  - "respond to neither goal" is replaced by "zero measured active K_D": the one-nose turns of those champions
    do respond (Astra's counterexample, checked);
  - the K_D > 10 grouping is marked as exploratory, and switching's trivial pass is qualified (Astra, Fable).
- **The peer conditions** are worded for replay and scramble only; their exposures are added; the overlap is
  the geometric route overlap (both).
- **"Untouched" becomes "prespecified",** with the trace on test maze 6000, the validation mazes and the wall
  audit disclosed throughout (Astra, Fable).
- **The power language** is replaced by the observed precision, and §8's framing of the gate added (Astra,
  Fable).
- **S-peer's comparison and S-worlds** are kept descriptive (Astra, Fable).
- **The training summary, the nose ranges at index 124,** and N's K_D range are added (Astra, Fable).
- **The READMEs:** the statuses are updated (both).

**Before the review, Claude's own corrections:**
- the probes cover 30 read points, not 26;
- a single comparator pattern had been described from three examples; it is now a per-champion table.

**Publication:** consensus of all three on publishing after the fixes, so main is brought up to date, as in
D187, and the owner is informed afterwards.
- Also published: the review trail's episodes 44-47, the top README's Newest section, ROADMAP and the E3
  READMEs.

**Next in Track E:** the step after the gate, E3's assembly comparison or E4. It is to be designed with both
reviewers; the probes' finding bears on it.

## D193 — after the E3 gate: E3b-2 first (the owner's choice); the READMEs checked section by section

**The owner, 2026-10-04,** asked what was needed and was offered three options:
- E3's assembly comparison;
- E4;
- first, a short exploratory follow-up on where E3b-1's gain comes from (Claude's recommendation).

The owner chose: "Option 3."

**E3b-2** (exploratory, about 5 GPU-hours, no new evolution) will knock out or freeze parts of E3b-1's tuned
champions: the latch, the comparators, the reflex, the turn biases. Its design and plan go to both reviewers
before it runs.

**The README check.** Before starting, the owner asked: "check section by section that the readmes of main
and roadmap are up to date". Main and roadmap differed only by the roadmap banner.

**Brought up to date:**
- **The top README:**
  - the banner and "Next on the roadmap" now name E3b-2;
  - E3b-0's "+1.09 over the reflex alone" names the scripted reflex;
  - "How to help" lists E3b-1's compute and records;
  - a new limitation: Track E's organisms are engineered;
  - "The claim under test" adds E4s and E3;
  - "How this was made" adds E3b-1's review catches.
- **The E3 README:**
  - an E3b-1 results section;
  - its status and parts lines;
  - a stale "E3b-1 must be resized".
- **E3b-0's README:** "Extend it", which said E3b-1 "follows".
- **E3b-1's README:**
  - "untouched" becomes "prespecified";
  - the decisions and reviews lists are completed, and the records list now names `RESULTS.md` and
    `evaluate.json`;
  - a `readings` command, checked to reproduce every registered reading exactly from the committed records;
  - a new "Extend it" section.
- **03r's README:** "the mechanism follow-up is next", which predated 03m.
- **AGENTS.md:** the `wormwars/e3/` row gains E3b-1's pieces.
- **ROADMAP:** the next step.

**The other READMEs** were checked on 2026-10-03 (D187), and nothing has changed in them since. The search
for stale statuses found none.

## D194 — E3b-2's plan: both "go with changes"; draft 2 takes every change

**The review** (`docs/reviews/20261004-E3b-2-plan/`): draft 1 of `docs/E3/E3b-2-PLAN.md` (cdc62e0), with the
same prompt to both. Astra checked the 16 champion genomes against their hashes.

**The main catches:**
- **"Latch frozen" did not freeze the latch** (both). Cutting the relay inputs leaves q to its own dynamics
  from 0:
  - the seed (q bias 0) sits at its unstable point, and both comparators close;
  - each champion drifts by its own bias.

  It is replaced by clamps at each organism's own A and B states. The relay cut is kept as a named
  diagnostic.
- **The latch recorder** (both):
  - sign(q) is replaced by each organism's unstable root;
  - an undecided band is defined;
  - the goal from before the switch is used on visit ticks (Astra: the goal switches after the move in the
    same tick);
  - agreement is reported per goal, beside switching and its latency, because a stuck latch can score high
    agreement.
- **New diagnostics:**
  - scent removed at the nose inputs (both);
  - the reflex held at rest (Astra), since frozen does not mean irrelevant to the gain.
- **The attribution:**
  - it also runs under "none", which decomposes the trail-dependence change (Astra);
  - its wording is narrowed to signed allocations under the stated substitutions, with the endpoints first
    and no per-champion shares for T-A (both);
  - the calculator gets hand-computed interaction tests (Astra).
- **Isolation:** E3b-2 gets its own folders, and does not import E3b-1's runner, which configures E3b-1's
  folders on import (Astra).
- **Other fixes:**
  - the smoke ids no longer overlap E3b-1's projection ids (Fable);
  - "index 124" is the generation index (Astra);
  - the seed's own probe readings come from E3b-0's report (Astra).

**Rulings by Claude:**
- **The drop order, where the reviewers differ:** N's champions first, then the side attribution, then
  the lesions' "none" condition.
- **Checked before use:** W2's neurons have no chemical or gap inputs and a bias of −0.5, so "held at rest"
  is v = −0.5.

**Next:**
1. The runner, test-first.
2. A code review by both, covering draft 2's changes too.
3. The GPU run, after telling the owner.

The projection is about 2.6 GPU-hours, under a cap of 5.

## D195 — E3b-2's code review: both "fix then start"; every blocking finding fixed; plan draft 3

**The review** (`docs/reviews/20261004-E3b-2-code/`): the code at 443dcb0 and plan draft 2, with the same
prompt to both.
- **Fable 5.1:** 2 blocking points.
- **Astra 6:** 7 blocking points. Astra also checked the 20 champions' hashes, and checked every champion
  with both outputs silenced against the silenced seed, bitwise on the CPU.

**Blocking, and fixed test-first:**
1. **Switching measured occupancy, not switching** (both). A leg already on the new goal's side counted as
   crossed with latency 0, so a stuck latch read as switching in one direction.

   The fix:
   - a leg now starts at the visit tick;
   - a leg already on the new side then is "pre-aligned";
   - a crossing needs a later tick, and its latency counts from the visit;
   - a visit on the last tick is censored (Astra: such visits had vanished);
   - the switched share is crossed / (legs − pre-aligned − censored).

   Claude's own stuck-latch test had checked only one direction.
2. **Readings not recorded** (both): the middle-half band, the occupancy, the eligible weys and the
   opposite coding. All are recorded now, with maze-bootstrap intervals.
3. **An isolation hole** (Astra). The accounting wrapper reads `--out` before the arguments are validated, so
   `e3b2.py … --out runs/e3b1` could write into E3b-1's ledger. `--out` is now refused first, with a test.
   - E3b-1's runner has the same route. It is finished and was not affected, so it is noted here and not
     changed.
4. **Three fixed inputs** were recorded but not checked (both). They are now pinned.
5. **The attribution report** (Astra) gains:
   - the shared − none decomposition, with a joint maze bootstrap;
   - allocations in visits per wey;
   - bootstrap intervals for the gain, reversion and transplant.
6. **The lesion report** (Astra): every outcome by schedule, with the units stated in plan draft 3.
7. **The benchmark** (Astra) now:
   - times the save path;
   - checks the cap between repeats;
   - records its progress durably for kill accounting.

**Non-blocking points taken:**
- the pre-flight before every stage, and the full ordered maze list in each chunk's specification (Astra);
- the resting-turn check against the probe records (both). Astra had computed it independently, at a
  maximum difference of 0;
- wider exactness diagnostics (Fable);
- a report that reads stages stopped by the cap (Fable);
- the plan's chunk count corrected from 63 to 70 (Astra).

**The rulings, as reviewed:**
- **Accepted by both:**
  - the benchmark block 7300-7555, now stated in draft 3;
  - the first A-shared seed as the denominator, with the exactness check;
  - the lesion stage's own intact baseline, now with a composition diagnostic;
  - the ratio-of-sums bootstrap;
  - the A-is-high fallback, which is unreachable: every organism's relay signs agree.

**Next:**
1. The full suite, then commit and push.
2. A confirmation pass by both on the fixes.
3. The GPU run, after telling the owner. `project` binds every later stage to its commit, so every fix lands
   before it.

## D196 — E3b-2's confirmation pass: Fable "start", Astra two reporting fixes; fixed before `project`

**The review** (`docs/reviews/20261004-E3b-2-code-recheck/`): the fixes at bf8d54e.
- **Fable 5.1:** "start the GPU run". It re-derived the switching counts by hand and checked the recorder's
  branch order against `SwitchTally`.
- **Astra 6:** every D195 fix checks out, except the following.

**Fixed before `project` binds the commit, test-first:**
1. **The trail split overwrote its run-level t interval** with the bootstrap interval. Both are now kept
   (`ci95` and `bootstrap95`).
2. **The equal-weight agreement's bootstrap** counted a draw with no decided ticks for one goal as zero
   agreement. Its interval was biased downward: [0.5, 1] for perfect agreement in Astra's example. Such draws
   are now left out, and the number of draws used is reported.
3. **D195's cap-stop fix was ineffective.** E2's frame refuses to start any stage once the cap is reached, so
   a report stage could never run then. A `summary` command now builds the same summary outside the frame.
   The report stage stays the normal path.

**Also guarded (Fable, non-blocking):** a report with no A-shared chunk at all now says so, instead of
raising.

**Next:** the full suite, then commit and push. Then the GPU run (about 2.9 GPU-hours under a cap of 5),
after telling the owner.
- **Consensus:** Fable said start, and Astra asked only for these fixes, each with its test, so there is no
  further round.

## D197 — E3b-2's results: the selector is in use; reviewed by both ("fix then publish"), corrected, published

**The run** (2026-10-04) used 3.00 of 5 GPU-hours, with no drop and no failed attempt.
- **The gain replicates on 256 fresh mazes:** T-A +0.114, T-F +0.451 of the seed's mean, with a pooled
  correlation of 0.99 with E3b-1's test-block d.
- **Holding the latch at either of its own states** removes 85-87% of the T champions' visits.
- **The latch switches after every uncensored visit,** in all 21 organisms.
- **The sensing and gating parameter groups interact strongly.** The tuned pair alone reaches 70% (T-A) and
  79% (T-F) of the gain. The output edges carry 36% of T-A's summed gain.
- **The nose inputs** matter to the T champions. N's champions use the scent but not the trails.

**The plan's non-binding reading:** E3's assembly comparison and E4 keep their premise for these organisms.

**The review** (`docs/reviews/20261004-E3b-2-results/`): the draft at d13d71d.
- **Both recomputed the readings:** Astra from all 70 chunks, Fable from `summary.json`. Neither found a
  calculation defect. Both said "fix then publish".
- **Claude's factual errors:**
  - "all eight mixed hybrids below W2 in 7 champions" is 6 (both);
  - "about one undecided tick per leg" holds only in the middle-half band (both);
  - "within 1-2 ticks" is a mean latency of up to 3 (Astra);
  - "the costs keep the same order with trails off" is untrue (both).
- **Over-wording, corrected:**
  - "the cause" was a mechanism claim the plan rules out; it now reads as a strong interaction between
    parameter groups (both);
  - "output carries little" is true of T-F, not of T-A, where it is 36% (Astra);
  - "the noses don't matter to N's champions" became: N's champions use the scent, and shared trails cost
    them (both);
  - the recorder is now framed as an integrity check, with the clamps as the evidence of use (both).
- **Added:**
  - the zero-visit hybrids and the tuned-pair coalition (Fable);
  - the clamps as proportions and absolute levels (both);
  - the latch denominators (Astra);
  - the secondary outcomes that separate the schedules (Astra);
  - the shares and an index to the supporting readings (both);
  - the scope of the exactness checks (Astra).
- **The notes on the plan:** the benchmark block and the nose lesion's name are not deviations from draft 3
  (both).

**Before the review, Claude corrected its own overstatement:** "every mixed hybrid below W2, in all 16" became
15 of 16. Its recount then still had the 7-for-6 error above.

**Publication:** consensus of all three, so main is brought up to date as in D187, and the owner is informed.

**Next in Track E:** the owner chooses between E3's assembly comparison and E4.

## D198 — after E3b-2: E3c (the assembly comparison) next, then E4; 30 GPU-hours (the owner's choice)

**The owner, 2026-10-04,** after E3b-2's results: "update github, then E3's assembly comparison (E3c), and then
E4. 30 GPU hours."
- **E3c** is ROADMAP §E3's assembly comparison. It compares these, with the first-use and cumulative reuse
  costs reported (ROADMAP):
  - one task-conditioned controller of matched size;
  - pretrained modules with a fixed selector;
  - the same modules with an evolved selector;
  - a modular organism of the same size trained from scratch.
- **E4** follows: do the two minds share?
- **The ceiling:** 30 GPU-hours each, matching D159's "about the same each for E3b and E3c".
- **How it proceeds:** as delegated. A design with both reviewers, then a pre-registration bound before
  any formal stage, then test-first code with a code review, then the run, the review of the results and
  publication.

**Also asked:** whether the owner's Arduino board could take some computation.
- **Claude's estimate:** not for the experiments; the simulation is GPU-bound and the board would be roughly
  100-1 000 times slower for this code.
- **The owner's answer:** declined to measure it.
