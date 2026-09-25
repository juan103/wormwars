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
