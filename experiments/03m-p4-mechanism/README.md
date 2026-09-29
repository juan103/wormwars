# 03m: what drives P4? An exploratory look

**Status:** exploratory; published on main on 2026-09-29 (`1c0c978`, D116). The plan (v4.1) was agreed by Astra 6 and Fable 5.1 after four rounds; all
five parts ran on 2026-09-29 (3.32 GPU-hours). The results were reviewed, and their summary is
corrected (D114): read [`RESULTS.md`](RESULTS.md) with its Corrections. Nothing here is confirmatory.
*(Corrected 2026-09-29, D114. The status line before this one said: "N2's large food response
depends on where its chemical weights sit and on RIA and AIY; its high history dependence survives
every deletion and weight permutation tested, and fades more slowly than in the shuffles." The
second clause was wrong: most weight permutations lower P4 below the threshold.)*

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
- Estimation noise alone is unlikely to explain the association (split-half reliability 0.94-0.99),
  and it also appears with a separately computed response measure. *(Corrected 2026-09-29, D114: this
  said the association "is not estimation noise".)*
- **N2's effect is concentrated:** 5% of its random brains carry 40% of its history signal and 38% of
  its food response, mostly the same brains; the shuffles' top 5% carry about 19%. But N2's history
  dependence stays high without them (0.895, above 97-100% of every ensemble).

Details, caveats and every number: [`PLAN.md`](PLAN.md) §Q1, `tradeoff.json`, `tails.json`.

## What the simulations found (exploratory; corrected, D114)

- **N2's history fades more slowly than the shuffles':** it keeps a larger share of the difference
  than all 80 null graphs tested at 5, 10 and 50 ticks after the ramp, and than 78 of 80 at 300.
- **N2's large food response depends on where its weights sit and on the RIA and AIY neuron pairs.**
  Deleting either pair cuts the history signal in proportion too, so the history ratio (P4) barely
  moves.
- **How far N2's P4 stands above the shuffles depends partly on gap junctions and partly on weight
  placement;** no single or paired neuron deletion tested removed it.
- A first draft of this summary overstated all of this, and was corrected after review; see
  [`RESULTS.md`](RESULTS.md), Corrections.

## Files

| File | What it is |
|---|---|
| [`PLAN.md`](PLAN.md) | The plan, its review history and every caveat |
| [`RESULTS.md`](RESULTS.md) | Results, with dated corrections |
| `tradeoff.json`, `tails.json` | Q1's outputs |
| `synapses.json`, `weights.json`, `decay.json`, `lesions.json` | Q3, Q5, Q4 and Q2's outputs (per-genome arrays are local) |
| `compute-record.json` | Compute used so far |
| [`../../scripts/p4m.py`](../../scripts/p4m.py), [`../../tests/test_p4m.py`](../../tests/test_p4m.py) | The runner and its tests |
| `docs/reviews/*03m*`, `docs/reviews/20260928-outside-review/` | The reviews, and the outside review that suggested these checks |

## Reproduce it

Q1 needs only a clone: `python scripts/p4m.py tradeoff`. Q1b needs 03's local per-genome measures,
which are regenerable from 03's binding commit (`python scripts/p4m.py tails --measures DIR`).
The simulating commands need the connectome (`scripts/fetch_connectome.py`), a CUDA GPU, and 03's
graph files, which `python scripts/p4m.py graphs` rebuilds from 03's committed record.
`--smoke` runs every command at tiny sizes on the CPU.
