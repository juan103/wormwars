# M2 pilot: validating a dynamical census (exploratory, 2026-10-20)

The scripts for the pilot of step M2 of [`docs/memory/MEMORY-ROADMAP.md`](../../docs/memory/MEMORY-ROADMAP.md). The
sample, the classifier, its thresholds and the checks R1 to R6 are fixed in
[`docs/memory/M2-PILOT-PLAN.md`](../../docs/memory/M2-PILOT-PLAN.md), reviewed by Astra and Fable before anything ran
([`docs/reviews/20261020-m2-pilot-plan/`](../../docs/reviews/20261020-m2-pilot-plan/)). **Nothing here is
registered.** CPU only.

| Script | What it does | Output (`runs/memory-m2/`) |
|---|---|---|
| `spike_equilibria.py` | The spike behind the plan's "facts used": Newton on H in float64 from 64 genomes' tick-2000 states, and the check that a root of H built from the float64 brain is fixed by one float64 tick. | `spike_equilibria.txt` |
| `equilibria.py` | The float64 brain, H and its Jacobian A, damped Newton with its error bound, P = I + D Aᵀ and its verdict, and the automatic derivative of one tick of `Brain.step` (R4′). | |
| `classify.py` | The classifier's rules as pure functions (reaching against the forecast at matching ticks, the period search, the oscillation verdict, the classes in their order of precedence), with `test_rules()`. | |
| `pilot.py` | The stages: `sample`, `main`, `classify`, `r3`, `r4`, `r4p`, `r5`, `r6`, `summary`. Each writes its own file and is skipped if that file exists, so a stopped run resumes. | `sample.json`, `classes__<graph>.json`, `r3__`, `r4__`, `r5__<graph>.json`, `r4p.json`, `r6.json`, `summary.json` |
| `describe.py` | *After the data:* per-genome details behind the results write-up (the tick-300 classes, the unresolved genomes, R3's discordant representatives, R5's switches, the numerator shares against the whole eligible numerator). Changes no class or check. | `describe.json` |

Run `python scripts/memory_m2/pilot.py` (all stages) or name stages. Inputs: the connectome, M1's fresh panel arrays
(`runs/memory-m1/panels/*.npz`, local) and 03mc's graph files (`runs/p4mc/graphs/`, local). Trajectories, roots and the
grower diagnostics (`main__`, `roots__`, `growers__<graph>.npz`) stay local. Compute is recorded in `compute.json` (local; the pilot's committed copy is `pilot-compute-record.json`, and its console output `pilot_run.txt`). The results are in [`docs/memory/M2-PILOT-RESULTS.md`](../../docs/memory/M2-PILOT-RESULTS.md). For
a smoke test, set `MEMORY_M2_OUT` to a scratch folder. The tests are in `tests/test_memory_m2.py`.
