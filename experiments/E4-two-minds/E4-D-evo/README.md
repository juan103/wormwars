# The evolutionary E4-D: does selection recruit the transfer?

**Status (2026-10-15):** the formal run is complete, as pre-registered (D274-D280). **L, the confirmatory arm, reads
"practically relevant transfer found"**; F, secondary, reads the same; S was not triggered. The results were reviewed
by both reviewers ("fix then publish", D281) and published on main.

**The question:** starting from E-G with the 32 cross-link slots at 0, does selection on E4-D's trial outcome recruit
cross-links that carry A's engineered cue into B? E4-D's feasibility check showed that a hand-configured link can carry
the cue (`../E4-D/README.md`); this asks whether a GA finds one.

**The answer, in short** ([`RESULTS.md`](RESULTS.md)):
- mutating only the slots, the 32 runs' champions made a mean real-first share of 0.912 on their own fresh test
  mazes, against 0.5 for any policy blind to the cue; the one-sided 95% lower bound of the gain, 0.401, is far above
  the owner's margin, 0.15 (the registered reading). Descriptively, every champion beat E-G (0.805-0.969);
- reversing A's cue sent every champion to the decoy, and cutting the links gave E-G exactly;
- every champion has a positive comparator → nose contrast, at small weights, unlike the hand-built comparator copy
  (exploratory; whether that route carries the effect was not tested).

## Where things are

| What | Where |
|---|---|
| the design | [`docs/E4/E4-D-EVO-DESIGN.md`](../../../docs/E4/E4-D-EVO-DESIGN.md) v2.1 (D265-D266) |
| the pilot (exploratory) | `precheck.json`, `screen.json`, `f.json`, `compute-record.json` (D269-D270) |
| the power analysis | `power.json` (`scripts/e4d_evo_power.py`, D271) |
| the pre-registration | [`PREREGISTRATION.md`](PREREGISTRATION.md), bound at c3fe432 (D272-D274); Amendment 1 (D276, D278) |
| the formal records | [`formal/`](formal/): each stage's start marker and record, and the compute records |
| the summary | [`summary.json`](summary.json), from `scripts/e4d_evo_summary.py` |
| the code | `wormwars/e4/evo_trial.py`, `evo_stats.py`, `evo_formal.py`; `scripts/e4d_evo.py` (pilot), `scripts/e4d_evo_formal.py` (formal) |
| the reviews | `docs/reviews/20261013-E4-D-evo-design`, `20261013-E4-D-evo-code`, `20261014-E4-D-evo-prereg*`, `20261014-E4-D-evo-formal-code*` and `20261015-E4-D-evo-results` |
| the decisions | D265-D281 |

**What stays local:** the populations and selection matrices (`runs/e4d-evo-formal/`). The records keep their sha256.

## Reproduce it

See [`RESULTS.md`, "Reproduce it"](RESULTS.md#reproduce-it).

## Extend it

- **Naive modules:** here both modules were engineered and only the links evolved. Whether transfer is recruited
  when the modules themselves must also be learned is untested (F also mutated E-G's own parameters, at small
  factors, in 4 runs).
- **The removed-cue dependence:** most champions stop entering either candidate when A's cue is removed, which the
  hand-built control does not. Why is unmeasured.
- **A cue that is not engineered:** a task where A holds information B can use in ordinary shuttling (E4's README).
