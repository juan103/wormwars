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
