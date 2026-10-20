# M1: accounting, amplitude and the cheap kills (exploratory, 2026-10-20)

The scripts for step M1 of [`docs/memory/MEMORY-ROADMAP.md`](../../docs/memory/MEMORY-ROADMAP.md). Their definitions,
panels and decision rules are fixed in [`docs/memory/M1-PLAN.md`](../../docs/memory/M1-PLAN.md), reviewed by Astra and
Fable before anything ran ([`docs/reviews/20261020-m1-plan/`](../../docs/reviews/20261020-m1-plan/)). **Nothing here
is registered.** CPU only.

| Script | Plan part | Output (`runs/memory-m1/`) |
|---|---|---|
| `common.py` | The shared pieces: 03mc's constants, the graph panel, the probe with in-batch arms at the ramp's end, the anatomy core. | |
| `accounting.py` | A: 03mc's per-genome arrays. | `accounting.json` |
| `anatomy.py` | C: M3's anatomy predictors, frozen in the plan. Needs `accounting.json`. | `anatomy.json` |
| `panels.py` | B1, B2, B3 and three of B4's kills on the fresh panels. | `panel.json`, `panels/<graph>__<seed>.json` |
| `tau.py` | B4's equal-tau control and the tau-permutation diagnostic. Needs `panels/`. | `tau.json` |
| `growers.py` | B4's growers and forecast check (midpoint Jacobians), on an independent draw of 512 genomes (seed 7602). | `growers.json` |
| `summarise.py` | The spreads, the bootstrap, D1, D2, the kills' readings and the handoff to M2; `test_rules()` runs first. | `summary.json` |

Run them in that order from this folder (`python accounting.py`, and so on). Inputs: the connectome
(`scripts/fetch_connectome.py`), and 03mc's local graph files and per-genome arrays (`runs/p4mc/graphs/`,
`runs/p4mc/arrays/`, written by `scripts/p4mc.py`; not committed). The per-genome arrays of the fresh panels
(`panels/*.npz`) and the logs stay local. `panels.py`, `tau.py` and `growers.py` record their compute in
`compute.json`. For a smoke test, set `MEMORY_M1_OUT` to a scratch folder and `MEMORY_M1_GENOMES` to a small number.
