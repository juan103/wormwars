# For agents and new contributors

This file is for anyone, human or AI, who wants to reproduce, check or extend this work. It
describes the repository's layout and the rules the work has followed. The README says what was
found; this file says how the work is done.

**Contributions are welcome, and so is being overtaken.** Compute is this project's bottleneck, so
independent replications, critiques and faster follow-ups all help. [`ROADMAP.md`](ROADMAP.md) lists
what comes next.

## Layout

| Path | What it holds |
|---|---|
| `wormwars/` | The library. |
| `wormwars/connectome/` | Loading the connectome, and the basic null graphs (degree-preserving shuffles, random graphs). 03's null ensembles are sampled in `wormwars/exp03/samplers.py`. |
| `wormwars/brain.py` | The rate network on the connectome, batched over strains: `Genome`, `Brain`. |
| `wormwars/world.py`, `fields.py` | The batched game world: bodies, sensing, food, pheromones, combat. |
| `wormwars/interface.py` | Which neurons receive which senses, and which neurons drive the motors. |
| `wormwars/evo/` | Evolution (`evolve.py`), rollouts and seed pools (`rollout.py`), genome files (`genomes.py`), run bundles and `replay_mode` (`bundle.py`), coevolution. |
| `wormwars/accounting.py` | Compute accounting: worlds, ticks and neural updates, by category. |
| `wormwars/exp02/`, `wormwars/exp03/` | Experiment-specific code: grids, probes, samplers, statistics and reports. |
| `scripts/` | Entry points. Each writes a run bundle and a compute record next to its output. |
| `experiments/<id>/` | One folder per experiment, each with a README: design, pre-registration, results, reviews, and the committed summary data. |
| `runs/` | Run outputs. Small summaries are committed; bulky files, such as most genome `.npz` files, stay local. |
| `docs/` | Reproducibility (`REPRODUCIBILITY.md`), the foundations work (`foundations/`: T0 correctness, T1 throughput), design notes (`E1/`), archived reviews (`reviews/`), and the review trail. |
| `DECISIONS.md` | Every non-trivial decision, numbered (D001…), with its reason and who caught what. |
| `ROADMAP.md` | What comes next, and why. A living document, not a pre-registration. |
| `tests/` | The test suite. |

## Setup and checks

See [README: How to reproduce](README.md#how-to-reproduce). In short:

```
pip install -r requirements.txt
python scripts/check_env.py          # a real CUDA kernel, not only is_available()
python scripts/fetch_connectome.py   # downloads, hashes and caches the connectome
python -m pytest                     # the whole suite; markers: slow, gpu
```

The tested platform is one NVIDIA RTX 5080, Windows 11, Python 3.13, and PyTorch 2.12 with CUDA 13.0
(`requirements.txt` pins the versions). Most tests run on the CPU.

## Rules the work follows

These are the invariants. A change that breaks one should say so openly.

1. **Never redistribute the connectome.** Its source states no licence for redistribution.
   `fetch_connectome.py` downloads it and checks its sha256. Do not commit data files, and never
   substitute synthetic data when the data is missing.
2. **Pre-register before running.**
   - An experiment's design, measures, tests and outcome wording are fixed in a
     `PREREGISTRATION.md` and committed before the formal run.
   - Anything decided after seeing data is labelled exploratory.
   - A bound pre-registration is never edited. Deviations are reported in the results.
3. **Report whatever comes out.** Null and failed predictions are published, in the wording fixed
   in advance.
4. **Correct in the open.** Wrong statements are corrected by adding a dated Corrections entry
   that quotes what was wrong, never by deleting it. Every correction gets a `DECISIONS.md` entry.
5. **Numbers come from committed files.** A number in a document should be traceable to a file
   in the repository, or to a script that regenerates it.
6. **Exactness is claimed only where it is tested.** See
   [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md):
   - CPU runs repeat exactly;
   - CUDA runs are exact only on the same GPU, in the pinned environment, with the same batch
     composition, and inside `replay_mode()` where claimed;
   - a single-strain batch is its own composition (D082; T1 adds padding for new work).
7. **Every engine change gets an equivalence check,** against the previous engine at a tolerance
   declared in advance ([`docs/foundations/T1.md`](docs/foundations/T1.md) §3).
8. **Count compute.** Scripts run inside `wormwars.accounting` (`attempt`, `recorded` or
   `run_script`), so every rollout and neural update is counted.
9. **Tests fail before they pass.** New behaviour gets a test that was first seen failing. A check
   that cannot fail gets a sabotage check.
10. **Independent review.** Designs, pre-registrations and results have been reviewed by two
    models from different families: Astra 6 (OpenAI) and Claude Fable 5.1 (Anthropic). Their
    reviews are archived under `docs/reviews/` and the experiment folders.

## Where to start

- **To check a result:** start at the experiment's README, then read its `RESULTS.md` and
  `PREREGISTRATION.md`. The committed `report.json` or `analysis.json` holds the numbers.
- **To rerun an experiment:** follow the experiment README's "Reproduce it" section. Compare
  against the committed summaries.
- **To extend the work:** read `ROADMAP.md` and the "Extend it" section of the nearest experiment.
  A new experiment gets its own folder, design, pre-registration and README.
- **To report a problem:** open an issue with the file, the line, and what you expected. Include
  the commit, and the command that shows it.
