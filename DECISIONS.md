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

**Who caught it.** External review of the published results, not me. It was raised as arithmetic
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
because the first two barely fight: across 1 536 matches they dealt **80** and **7 308** total
damage against the coevolved populations' **50 844**, and only 3 and 8 strains respectively landed
any damage at all. Their ratios are computed from a handful of accidental contacts. They are
reported, with that caveat, but the sound comparison is the **frozen opponent suite in the same
matches**: it is unevolved, and by construction it fought exactly the same engagements, dealing
**51 307** damage to the coevolved side's 50 844.

**What the measurements say:** no evidence of learned flanking, on any metric. See the Corrections
section of `docs/RESULTS.md` for the numbers.
