# 03h: does the history random brains hold predict how well they forage?

**Status:** exploratory. 03h stopped before its pre-registration (2026-10-19, D321-D340), by the owner's choice. The
pilot ran under a bound registration, followed by an exploratory power analysis and an amplitude check. 0.349 of the
1.0 GPU-hour pre-registration cap was spent, and the formal run did not take place. No 03h brain ran on N2.

**The question:** the memory thread (`ROADMAP.md`) says N2's random brains hold recent history unusually strongly
(P4), and that this matters. The second part is untested: no file relates a genome's history to how well it forages.
03h asked about that relation at generation 0, on 02's T1:
- **A** (secondary): within a graph, does a random genome's history predict its fitness? Is that association weaker
  when a "the food fell" bit relieves the need for memory than under a sham bit?
- **B** (the only registered claim): is N2's generation-0 upper-tail advantage over SH-mirror-ASK graphs larger when
  memory is needed?

**What was found** ([`RESULTS.md`](RESULTS.md)):
- **The task and the relief work:** a scripted controller gains +0.985 from memory on T1, and a "food fell" bit
  replaces 98% of that.
- **Random brains barely use the bit** through ASKL and ASKR. The best tenth of genomes gained about 0.5% at
  amplitude 0.25. Over all genomes the gain was about 0.2% of the scripted gain at 1.0, and it was uneven across graphs.
- **So B's rank test could not have separated N2** from the null graphs, even under the hypothesis's strongest
  plausible effect.
- **In SH samples,** the size of the history held did not predict fitness, and its direction did, weakly.

## Files

| File | What it is |
|---|---|
| [`RESULTS.md`](RESULTS.md) | The results, exploratory |
| [`summary.json`](summary.json) | Every number RESULTS.md quotes, from `scripts/e03h_summary.py` |
| [`DESIGN.md`](DESIGN.md) | The design, v3.3, after five review rounds and the owner's choice of B as the primary (D330) |
| [`PILOT.md`](PILOT.md) | The pilot's registration, draft 4, bound at `ff1fd31` (D335) |
| [`pilot/`](pilot/) | The pilot's stage records (bind, gate, sham-rates, gate-sham, pilot) and its compute record |
| [`development-records/`](development-records/) | The design's T1 numbers, rule 7's equivalence check, step 0 and 0b, B's power analysis, the amplitude check and their compute records |

**The code:**
- `wormwars/e03h/`, the world's `food_fell` modes, `configs/interface-03h.yaml`, and the ASK kinds in
  `wormwars/exp03/samplers.py`;
- the scripts `scripts/e03h.py` (the pilot), `e03h_step0.py`, `e03h_step0b.py`, `e03h_equivalence.py`,
  `e03h_amplitude.py` and `e03h_summary.py`;
- the tests, `tests/test_e03h_*.py`.

**Reviews:** RESULTS.md's Record lists them, under `docs/reviews/`.

## Reproduce it

See [RESULTS.md, "Reproduce it"](RESULTS.md#reproduce-it).
- `python scripts/e03h_summary.py` rebuilds `summary.json` from the committed records, on the CPU.
- `python experiments/03h-history-use/development-records/t1_generation0.py` rebuilds the design's T1 numbers from
  03's committed pilot record.
