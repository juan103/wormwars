# Memory spikes (exploratory, 2026-10-20)

Quick CPU checks run for the selection round of the memory brainstorm (`docs/reviews/20261020-memory-*`), read in
`docs/memory/MEMORY-ROADMAP.md`. The question
is why N2's history difference decays more slowly than in shuffled graphs (03mc, Q-D). **Nothing here is registered.**
The batches use fresh CPU panels of random genomes, not 03mc's genomes, which exist only on CUDA; `check_mixture.py`,
`check_structure.py` and `check_settled_census.py` read 03mc's own arrays and records. Most arms use one
graph per null ensemble, and graphs within one ensemble differ a lot (batch 1: 0.206 to 0.442 at tick 30), so a single
comparison is a lead, not a result.

| Script | What it checks | Output (`runs/memory-spikes/`) |
|---|---|---|
| `spikes.py` | The harness: a copy of 03mc's two-row history probe (`wormwars/exp03/twin.py`) with knobs (warm-up, food scale, substeps, erasure at the ramp's end). | |
| `check_mixture.py` | Per-genome tail statistics on 03mc's local arrays (`runs/p4mc/arrays/`). | `check_mixture.txt` |
| `check_structure.py` | Graph features of the 640 null graphs against their retention; where N2 falls. | `check_structure.txt` |
| `tri_sampler.py` | Degree-preserving, weight-carrying rewiring to a target 3-cycle or feed-forward triangle count. | |
| `batch1.py` | Integrator substeps, reversal, the turn read-out as store, the layer factorial, warm-up, food level. | `batch1.json` |
| `batch2.py` | Triangle surgery: shuffles raised to N2's triangle counts; N2 lowered to the shuffles'. | `batch2.json` |
| `batch3.py` | The one-tick Jacobian at the ramp's end: spectral radius, non-normality, a linear forecast. | `batch3.json` |
| `batch4.py` | Where the residual difference lives: per-neuron persistence, concentration, the tau and bias regression, erasure by group. | `batch4.json` |
| `batch5.py` | The control batch 2 lacked: shams that move as many edges while holding both triangle counts, and free rewiring of the same size. | `batch5.json` |
| `check_sham_core.py` | Which N2 edges the shams and free rewirings keep. | `sham_core.json` |
| `batch6.py` | Batch 4's erasures on a held-out panel (seed 7400), and other read-outs (forward, random 8-neuron sets). | `batch6.json` |
| `batch7.py` | The head core: dissolve it, scramble the periphery as much, freeze it while shuffling the rest, and a hub-frozen control. | `batch7.json` |
| `batch8.py` | After round 3: the crazy ideas (an oscillator; separate states) and the join of unstable, settled and large-contributor genomes; Jacobians at the ramp-end states and their midpoint. | `batch8.json` |
| `check_settled_census.py` | 03mc's committed census of settled genomes: where N2 falls among the 640 null graphs, and the association with share. | `settled_census.json` |

Inputs: the connectome (`scripts/fetch_connectome.py`), and for the null graphs 03mc's local graph files
(`runs/p4mc/graphs/`, written by `scripts/p4mc.py build`; not committed). Run any script with `python scripts/memory_spikes/<name>.py`.
CPU times: about 2 minutes per arm of 1024 genomes with 100 ticks of follow-up. The JSON files hold the numbers; the logs
(`memory-spikes-batch*.log`, the scripts' printed output) stay local.
