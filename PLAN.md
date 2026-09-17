# WormWars — implementation plan

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done and measured.

## Milestone 0 — environment, plan, skeleton `[x]`

Measured on this machine before anything else was written:

| Check | Result |
|---|---|
| GPU | NVIDIA GeForce RTX 5080, 16 GB (17.09 GB reported), driver 591.86, CUDA 13.1 |
| Compute capability | **sm_120** (12, 0) |
| PyTorch | 2.12.0+cu130 under Python 3.13, `get_arch_list()` contains `sm_120` |
| Real CUDA kernel | 512×512 matmul + `tanh` + reduction on GPU == CPU result to the last bit (absdiff 0.0); `index_add_` scatter of 10 000 elements correct; 50 matmuls in 12 ms |
| Verdict | **The installed build supports this GPU.** No reinstall needed, no CPU workaround. |

Python 3.13 (system install) is the interpreter; 3.12 only has a CPU torch and 3.11 has none.
Dependencies are pinned in `requirements.txt` to the versions actually verified here.

Connectome availability was also settled up front, because the spec makes it a hard blocker —
see Milestone 1 and `PROVENANCE.md`.

## Milestone 1 — connectome loader `[ ]`

Source: **Cook et al. 2019**, `SI 5 Connectome adjacency matrices, corrected July 2020.xlsx`
from wormwiring.org (downloaded, sha256 recorded). Verified by inspection before planning:

- sheets `hermaphrodite chemical` (directed) and `hermaphrodite gap jn symmetric`
- row/column group headers give the class directly: `PHARYNX` (20), `SENSORY NEURONS` (83),
  `INTERNEURONS` (81), `MOTOR NEURONS` (108), `SEX SPECIFIC` (8) → 300, plus `CANL`/`CANR`
  which appear only in the gap sheet = **302 neurons**
- all **39** neurons named in the sensor/motor map are present, including `MCL`/`MCR`
- weights are *total EM serial sections of connectivity* → `weight_kind = "em_sections"`

`scripts/fetch_connectome.py` downloads, verifies the hash, converts to a cached `.npz`
(the `.xlsx` is not committed). `wormwars/connectome/loader.py` exposes
`load_connectome() -> Connectome(names, classes, chem[302,302], gap[302,302], weight_kind, meta)`.

Tests: 302 neurons; the 20 pharyngeal neurons present by name; every mapped neuron present by
individual name; gap matrix exactly symmetric; chemical matrix not symmetric; no self-edges;
isolated neurons reported, not dropped; hash matches.

## Milestone 2 — brain `[ ]`

Semi-implicit update exactly as specified, in `wormwars/brain.py`. State `[worlds, swarms, weys, 302]`,
weights `[worlds, swarms, 302, 302]` dense and masked (benchmarked against a sparse formulation;
keep the winner). Genome = W on the chemical mask, G on the gap mask, tau, bias; clamped to bounds
after every mutation. Optional Dale's law flag.

Tests: batched == unbatched; bounded activity at the corners of the parameter bounds;
**timestep refinement** — `dt` vs `dt/4` agree within tolerance for random *and* extreme genomes;
this is what picks `dt` and the substep count, not stability alone.

## Milestone 3 — foraging world, 20 weys `[ ]`

Batched fields `[worlds, C, H, W]` (food, hazard, wall, pheromone, body density), wey state
`[worlds, swarms, weys, ...]`, three body sample points, grid-based everything, no pairwise terms.
Trajectory recorder + a matplotlib viewer (oriented segments over field heatmaps, PNG/GIF, no
window needed). Physics invariants and the **energy ledger** test from tick one.
I look at the viewer output and report what I see before any score is trusted.

## Milestone 4 — reproducible improvement `[ ]`

Truncation selection + elitism + Gaussian mutation with clamping. Evolved foragers vs
random-weight weys on **held-out seeds**, ≥3 independent runs. Report the numbers.

## Milestone 5 — small N2/SH/RD foraging comparison `[ ]`

Reduced K and R, identical budgets across conditions, hierarchical bootstrap over graphs and runs.
Pipeline check. Reported whatever it shows.

## Milestone 6 — body, crowding, resource accounting, stage-1 combat `[ ]`

Shared-food scaling, damage cap, adjoint bite credit, corpse pellets, no friendly fire.
Scripted-geometry flank tests (head-on / T-bone / nose-to-tail) with measured damage in both
directions; blur radius, body length, cell size and crowding tuned until the asymmetry target holds.

## Milestone 7 — two-swarm coevolution `[ ]`
Paired evaluation (side swap, headcount swap), hall of fame, versioned frozen opponent suite
on held-out seeds.

## Milestone 8 — stage-2 pumping `[ ]`
Re-verify foraging still evolves when eating needs pumping, then coevolve.

## Milestone 9 — full N2/SH/RD experiment + stats `[ ]`
K=5, R=3 per graph, K·R runs for N2, hierarchical bootstrap, per-evaluation and per-GPU-hour.

## Milestone 10 — ablation, convergence, tactics `[ ]`
Implementation checks labelled as such; emergent tests vs matched random ablations.

## Milestone 11 — scaling `[ ]`
wey-ticks/s and peak VRAM vs worlds and swarm size; chunked rollouts; then scale.

## Milestone 12 — Minecraft bridge `[ ]`
Not touched until 11 is done, and I ask which edition/mod loader first.

## Working rules

- One module, one job; every module gets tests. Config in dataclasses + YAML, no scattered constants.
- Ambiguous modelling choices go in `DECISIONS.md` with the reason, and the simplest option wins.
- Reported numbers are measured numbers.
- Small commits, one per coherent step.
