# 03h: does the history random brains hold predict how well they forage?

**Status:** the design is agreed (v3.2, D321-D325), and the step-1 code is under review (D326). Nothing has run. Every
GPU stage needs the owner's word.

**The question:** the memory thread (`ROADMAP.md`) says N2's random brains hold recent history unusually strongly
(P4), and that this matters. The second part is untested: no file relates a genome's history to how well it forages.
03h tests that relation at generation 0, on 02's T1:
- **A:** within a graph, does a random genome's history predict its fitness? Is that association weaker when a
  "the food fell" bit relieves the need for memory than under a sham bit?
- **B:** is N2's generation-0 upper-tail advantage over SH-mirror-ASK graphs larger when memory is needed?

## Files

| File | What it is |
|---|---|
| [`DESIGN.md`](DESIGN.md) | The design, v3.2, after four review rounds |
| [`development-records/`](development-records/) | `t1_generation0.py` and its output: the T1 generation-0 numbers from 03's pilot |

**The code:** `wormwars/e03h/`; the world's `food_fell` modes; `configs/interface-03h.yaml`; the ASK kinds in
`wormwars/exp03/samplers.py`; `scripts/e03h_step0.py`; `tests/test_e03h_*.py`.

**Reviews:** `docs/reviews/20261018-memory-thread-scope/`, `20261018-03h-design/`, `-r2/`, `-r3/`.

## Reproduce it

Not run yet. `python experiments/03h-history-use/development-records/t1_generation0.py` rebuilds the design's T1
numbers from 03's committed pilot record, on the CPU.
