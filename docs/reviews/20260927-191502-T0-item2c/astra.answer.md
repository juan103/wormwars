Most fixes are resolved, but two prior gaps remain:

- **02b still has no aggregate.** [analyse.py:459](D:/Claude/random/wormWars/experiments/02b-champion-analysis/analyse.py:459) writes attempts only; nothing produces the required adjacent `compute.json`.
- **Production-path coverage remains incomplete.** Coevolution and stimulus-bank tests are added, but 02b replay, viewers and benchmarks remain untested for accounting. D070 records exclusions; [T0.md:34](D:/Claude/random/wormWars/docs/foundations/T0.md:34) still requires coverage of every listed path. Excluding viewers from experiment output does not resolve their ledger-test requirement.

**One new minor routing bug:** [accounting.py:257](D:/Claude/random/wormWars/wormwars/accounting.py:257) manually recognises only literal `--out`, while the scripts’ argparse parsers accept abbreviations. I reproduced `evolve_forage.py --runs 0 --ou runs/review-custom`: results go to `runs/review-custom`, accounting goes to `runs/m4`. Derive both destinations from the same parsed arguments.

The other changes check out: normal `--out` routing, aggregation for the five legacy scripts, help/exit handling, default-category metadata, ignore rules, whole-run exp02 counts and probe categories.

Verified **26 accounting tests passed**, with filesystem persistence mocked in memory; all five actual `--help` entrypoints also exited successfully without files. CUDA identity remains unverified.

not yet