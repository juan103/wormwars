# 03m: what drives P4? An exploratory look

**Status:** plan v4.1 agreed by Astra 6 and Fable 5.1 ("ready to run", after four rounds). All five
parts ran on 2026-09-29 (3.32 GPU-hours); results written in [`RESULTS.md`](RESULTS.md), review
pending. In brief: N2's large food response depends on where its chemical weights sit and on RIA and
AIY; its high history dependence survives every deletion and weight permutation tested, and fades more
slowly than in the shuffles. **Exploratory:** the
analyses are declared in [`PLAN.md`](PLAN.md) before they run, but nothing here is confirmatory.

## The question

Experiments 03 and 03r found that random, unevolved brains wired like the real *C. elegans*
connectome (N2) show more **history dependence** (P4) than brains wired like shuffled graphs: after a
food signal ramps up or down to the same level, N2's turn output still remembers which way it came
from, a little more than the shuffles' does. It was borderline in 03 and replicated in 03r.

03m asks what drives that: which neurons it depends on, whether it runs through gap junctions or
chemical synapses, how long the difference lasts, and whether it comes from the wiring or from where
the anatomical weights sit.

## What is known so far (Q1, no simulation)

- Across shuffled graphs, **brains that respond more strongly to food show less history dependence**
  (Spearman −0.27 to −0.60 within every ensemble). N2 breaks that pattern: its food response is 4.7
  to 7.1 times the typical shuffle's, yet its history dependence is above every shuffle but one in
  each of 03 and 03r.
- The association is not estimation noise (split-half reliability 0.94-0.99), and it holds against a
  separately computed response measure.
- **N2's effect is concentrated:** 5% of its random brains carry 40% of its history signal and 38% of
  its food response, mostly the same brains; the shuffles' top 5% carry about 19%. But N2's history
  dependence stays high without them (0.895, above 97-100% of every ensemble).

Details, caveats and every number: [`PLAN.md`](PLAN.md) §Q1, `tradeoff.json`, `tails.json`.

## What runs next (Q2-Q5)

| | What | Why |
|---|---|---|
| Q2 | Delete each neuron and each left-right pair in N2's random brains | Which neurons the effect depends on (RIA and AIZ first) |
| Q3 | Switch off gap junctions or chemical synapses; permute weights by type | Which synapse type carries it |
| Q4 | Watch 300 ticks after the ramp, for N2 and 80 shuffled graphs | Slow fading, or a lasting state |
| Q5 | N2's wiring with its weights shuffled 64 ways | Wiring or weight placement |

About 3.6 GPU-hours, capped at 5. Each command first reproduces 03's own numbers for N2 exactly, or
stops.

## Files

| File | What it is |
|---|---|
| [`PLAN.md`](PLAN.md) | The plan, its review history and every caveat |
| `tradeoff.json`, `tails.json` | Q1's outputs |
| `compute-record.json` | Compute used so far |
| [`../../scripts/p4m.py`](../../scripts/p4m.py), [`../../tests/test_p4m.py`](../../tests/test_p4m.py) | The runner and its tests |
| `docs/reviews/*03m*`, `docs/reviews/20260928-outside-review/` | The reviews, and the outside review that suggested these checks |

## Reproduce it

Q1 needs only a clone: `python scripts/p4m.py tradeoff`. Q1b needs 03's local per-genome measures,
which are regenerable from 03's binding commit (`python scripts/p4m.py tails --measures DIR`).
The simulating commands need the connectome (`scripts/fetch_connectome.py`), a CUDA GPU, and 03's
graph files, which `python scripts/p4m.py graphs` rebuilds from 03's committed record.
`--smoke` runs every command at tiny sizes on the CPU.
