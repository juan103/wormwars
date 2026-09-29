# E2d: diagnosing Task N after E2's floor fired

**Status: run and reviewed (2026-09-29).** Exploratory. The plan ([`PLAN.md`](PLAN.md), v4) was agreed
after four versions and three reviews (D127-D131), and the runner after three code reviews
(D132-D135). The formal stages ran once each on 2026-09-29: 3.90 of a 7 GPU-hour cap, with no stop,
rerun or amendment. Both reviewers checked the results ("fix", text only); read
[`RESULTS.md`](RESULTS.md) with its Corrections (D137).

- **"A non-stereo plateau"** (the plan's operational reading): no champion of E2's and 04a's 47 meets
  the plan's "uses the left-right difference" criterion. 43 distinct champions show no material
  benefit from intact bilateral input, and 4 show small ones. The probes do detect a low-gain
  stereo steerer at the same score (2.27). That shows the probes are sensitive, not that an N2
  genome can express stereo steering.
- **No tested change leaves the plateau:**
  - 32 worlds per genome: inconclusive;
  - halved mutation: "supports, carried by run 2". All 8 paired runs improved, +0.25 without run 2;
  - both together: "supports, carried by run 2", at the threshold;
  - the ES at σ 0.25: inconclusive, with one run that never left zero.
- **Other readings:** the ES is budget-limited. Selection noise is "not material" by the rule, narrowly
  (0.82 against 0.8), and below the line at the gentler mutation scales.
- **For E3:** whether stereo steering is expressible and reachable is untested. Four hypotheses to
  test: the sensing geometry, the interface, shaping toward left-right steering, a seeded start.
  The alternative is to build on the non-stereo module with its measured limitations.

**Why:** E2's registered floor fired. Random sampling came within 0.36 targets per episode of 02's
GA ([E2](../E2-optimizer-screen/README.md)). The roadmap then requires diagnosing saturation, noise
and budget before E3 builds on Task N.

**What it does:**
- **Part A** (done, no GPU; `part-a.json`, from `scripts/e2d_records.py`), from E2's records alone:
  - resampling 8 shared hold-out worlds for pairs of distinct champions (a proxy, not the actual
    training comparisons), two genomes 0.05-0.15 targets apart are ranked strictly correctly 54% of
    the time, with 16% ties;
  - nominees look 0.19-0.33 better in training than on validation;
  - the GA's populations average 0.44-0.63 against their best's 1.09-2.26;
  - nearly every champion sits near M-avg (2.20), E1's best controller that reads only the mean of the
    two sensors, far below the stereo controller (8.65).
- **Part B:** do the 47 distinct champions of E2 and 04a use the left-right difference? They are
  scored with it removed (`mean`) and reversed (`swapped`), against three scripted references. Part
  B also reads whether the ES was budget-limited, from its formal run against its extension.
- **Part C0:** how reliably 8 worlds rank a champion's mutated children and the ES's antithetic
  pairs, the comparisons selection actually makes.
- **Part C:** four arms, each changing one thing from E2 and paired with E2's own runs (the same seeds
  and world schedules, E2's runs replayed first to confirm they reproduce):
  - C1: 32 worlds per genome;
  - C2: halved mutation;
  - C4: both;
  - C3: the ES at σ 0.25.
- **What it can and cannot say:** leads for E3's design, not conclusions. The readings are fixed in
  the plan; "the optimizer is not the bottleneck" is not one of them.

**Reproduce it** (CUDA, one RTX 5080, the pinned environment; E2's and 04a's genome files, which stay
local):

```
python scripts/e2d_records.py
python scripts/e2d.py project
python scripts/e2d.py probe
python scripts/e2d.py siblings
python scripts/e2d.py replay
python scripts/e2d.py arm --arm c1   # then c2, c4, c3
python scripts/e2d.py evaluate
```

**The code:** `scripts/e2d.py` (on E2's stage frame; every registered number in `REGISTERED`) and
`scripts/e2d_records.py`. The tests: `tests/test_e2d_records.py`, `tests/test_e2d_analysis.py` and
`tests/test_e2d_commands.py`.
