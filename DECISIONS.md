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
