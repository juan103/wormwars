# 03mc: a confirmatory test of 03m's leads on P4

**Status:** run and reported (2026-10-16); the results await review by both reviewers. **All four primary questions
pass under Holm at a familywise α of 0.05, and P4 replicates a third time:** read [`RESULTS.md`](RESULTS.md). The
pre-registration was bound at `4dff311` (D294) after four review rounds (D289-D293); the build, the pre-run check
and the run are D295-D297, and the report D298.
The design (`DESIGN.md`, v2.2) was agreed by Astra 6 and Fable 5.1 after three rounds (D285-D288).

## The question

Experiments 03 and 03r found that random, unevolved brains wired like the real *C. elegans* connectome (N2) show
more **history dependence** (P4) than brains wired like shuffled graphs: after a food signal ramps up or down to the
same level, N2's turn output still reflects which way it came. The exploratory follow-up 03m found leads on what
drives it. This study tests four of them on fresh data, with tests fixed in advance:
- **Q-A:** N2's P4 changes unusually little when gap junctions are switched off (so its lead depends partly on them);
- **Q-B:** deleting the RIA pair, or the AIY pair, cuts N2's food response by more than 40% while P4 stays within 0.02;
- **Q-C:** N2's food response is unusually high against permutations of its own weight magnitudes;
- **Q-D:** N2 keeps an unusually large share of its history difference 30 ticks after the ramp.

It also replicates P4 a third time, and checks P4 on the read-out before its final nonlinearity.

## Files

| File | What it is |
|---|---|
| [`DESIGN.md`](DESIGN.md) | The design, its reasons, and every review round's changes |
| [`RESULTS.md`](RESULTS.md) | The results, in the wording fixed in advance |
| [`PREREGISTRATION.md`](PREREGISTRATION.md) | The rules, binding at the commit in `bound.json` |
| `report.json` | The registered statistics, written by `p4mc.py report` |
| `measurements.json` | Every unit's record and its arrays' sha256 (the arrays stay local) |
| `build.json`, `ensembles.json`, `graphs_manifest.json`, `graphs_content_manifest.json` | The build's records |
| `prerun-check.json`, `prerun-repeat.json` | The pre-run check on old inputs |
| `power.py`, `power.json` | Model-based pass probabilities from 03m's data |
| `equivalence.json`, `equivalence-check.json` | The two-row probe against one-row references, on old inputs |
| [`../../scripts/p4mc.py`](../../scripts/p4mc.py) | The runner: build, check, run, report |
| [`../../scripts/p4mc_equivalence.py`](../../scripts/p4mc_equivalence.py) | The pre-run check |
| `wormwars/exp03/twin.py`, `mc.py`, `mc_report.py` | The probe, the statistics, the report |
| `tests/test_exp03_twin.py`, `test_exp03_mc.py`, `test_p4mc.py`, `test_p4mc_equivalence.py` | Their tests |

## Reproduce it

Everything runs from a clone with the connectome (`scripts/fetch_connectome.py`). The formal stages need a CUDA GPU.
`--smoke` runs every stage at toy sizes on the CPU in `runs/p4mc-smoke/`:

```
python scripts/p4mc.py build --smoke
python scripts/p4mc.py check --smoke
python scripts/p4mc.py run --smoke
python scripts/p4mc.py report --smoke
```

The pre-run check and `power.py` also need 03m's local per-genome arrays (`runs/p4m/`), which `scripts/p4m.py`
regenerates.
