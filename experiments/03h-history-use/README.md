# 03h: does the history random brains hold predict how well they forage?

**Status:** exploratory. 03h stopped before its pre-registration (2026-10-19, D321-D341), by the owner's choice. The
pilot ran under a bound registration, followed by an exploratory power analysis and an amplitude check. 0.349 of the
1.0 GPU-hour pre-registration cap was spent, and the formal run did not take place. N2 was used only in the engine's
equivalence check: no history-fitness or relief comparison ran on N2.

**The question:** the memory thread (`ROADMAP.md`) says N2's random brains hold recent history unusually strongly
(P4), and that this matters. Before 03h, no file related a genome's history to how well it forages. 03h asked about
that relation at generation 0, on 02's T1:
- **A** (secondary): within a graph, does a random genome's history predict its fitness? Is that association weaker
  when a "the food fell" bit relieves the need for memory than under a sham bit?
- **B** (the only registered claim, by the owner's choice after step 0; D330): is N2's generation-0 upper-tail
  advantage over SH-mirror-ASK graphs larger when memory is needed?

**What was found** ([`RESULTS.md`](RESULTS.md)):
- **The task and the relief work:** a scripted controller gains +0.985 from memory on T1, and a "food fell" bit
  replaces 98% of that.
- **In random brains on three shuffled graphs, the bit's average effect was small.** It enters through ASKL and ASKR,
  which on these graphs have no direct read-out. The decile selected under relief scored about 0.5% above the one
  selected under sham at amplitude 0.25. Over all genomes the difference at 1.0 was about 0.2% of the scripted gain.
  It was uneven across graphs.
- **So B's rank test looked very unlikely to pass.** In exploratory scenarios, if N2's relief-sham difference were
  zero, it would rarely have passed. N2's own response and B's full power were not measured.
- **In SH samples,** the size of the history held had a near-zero mean association with fitness. Its direction showed a
  weak positive one (exploratory).

## Files

| File | What it is |
|---|---|
| [`RESULTS.md`](RESULTS.md) | The results, exploratory |
| [`summary.json`](summary.json) | Every number RESULTS.md quotes, from `scripts/e03h_summary.py` |
| [`DESIGN.md`](DESIGN.md) | The design, v3.3, after a scope round, four design rounds, and a direction round after step 0, in which the owner chose B as the primary (D330). It is bound by the pilot, so it is left unedited: its status line predates the run |
| [`PILOT.md`](PILOT.md) | The pilot's registration, draft 4, bound at `ff1fd31` (D335) |
| [`pilot/`](pilot/) | The pilot's stage records (bind, gate, sham-rates, gate-sham, pilot) and its compute record |
| [`development-records/`](development-records/) | The design's T1 numbers, rule 7's equivalence check, step 0 and 0b, B's power analysis, the amplitude check and their compute records |
| [`docs/reviews/`](../../docs/reviews/) | The reviews, listed in RESULTS.md's Record |

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
