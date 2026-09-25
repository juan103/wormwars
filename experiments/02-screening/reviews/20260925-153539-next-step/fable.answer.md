**1. Is the revised RESULTS.md ready?**

Close, but not as it stands. Everything the D042 revision touched now reads correctly. What remains:

1. **The generation-0 interaction has an unmentioned confound.** Motor gains were calibrated under M0 only and frozen across mappings (`DESIGN.md:100-103`; `calibration.json` has no mapping key). Under R1 and R2 the drive is uncalibrated and graph-dependent. So "the shuffles' best random brains start worse under M0" (`RESULTS.md:129-130`) and the bolded g0 interactions (`RESULTS.md:120-121`) may partly measure drive, not wiring. The data to check this are already saved: `gen0_drive` is recorded per run, hence per cell (`scripts/exp02.py:342`), but `drive_check` pools it per graph (`analysis.py:327-331`). Split it by mapping before publishing, or state the confound.
2. **The anchor is misreported and buried.** `RESULTS.md:229` puts +0.014 [−0.009, +0.037] next to "01b: +0.069" as if in the same units. The anchor is normalised to the scripted best (`report.py:197`); 01b's number is a raw final held-out contrast (`analysis.py:371-379`), and that 01b contrast itself did not separate (+0.069 [−0.015, +0.169], `01b RESULTS.md:49`). This is the only rerun of 01b's world in the series. It belongs in "What this decides" with its raw value, which `build` never computes for cell A (`report.py:173-187`).
3. **The headline bullets lack the labels the text promises.** Lines 11-21 state "the gap closes with evolution" and "3.5-11 times" as findings; the first is post hoc (line 118), the second has no across-brain uncertainty (line 147). Lines 26-28 promise labelling; apply it in the summary.
4. **Point estimates without intervals used as evidence.** N2's "+0.026 at both generations" and the shuffles' "−0.042 to +0.019" (lines 127-131) carry no intervals, yet they support the headline. Collision-off "+0.40 / +0.52" (line 81) has none and is reused in the decision section (line 264). All are computable from `probes.json`.

**2. Experiment 03**

**Recommendation: a pre-registered generation-0 structural study, no evolution, about 3 GPU-hours (under 5 with margin).**

- Two new control families, each 8 graphs: mirror-symmetric shuffles (paired double-edge swaps under the mirror map from `structure.py:18`; none exists yet in `graphs.py`), and no-shortcut shuffles (reject swaps that give AWA/AWC/ASE direct read-out weight above N2's). Both preserve degrees.
- `input_response` (`probes.py:81`) on N2, SH1-8 and the 16 new graphs, under M0/R1/R2/MS, gaps on and off, 1024 brains per graph with per-brain values saved. About 1 GPU-hour.
- Generation-0 fitness distributions (mean and best-of-32) on T0 and T1 for the same graphs and mappings, 512 genomes each, with drive recorded per mapping. At 3 s per 32 genomes (`pilot.json`), about 2 GPU-hours.
- Registered predictions: does N2's M0-specific directional response survive gaps off; do mirror-symmetric shuffles reproduce it; does the g0 interaction survive no-shortcut shuffles and drive matching.
- Decision rule: if symmetry plus shortcut removal account for N2's g0 signal, the series' N2-specific effect has a generic graph explanation, and the honest next step is to write that up and stop or pivot. If N2 still stands out, experiment 04 runs evolution with these controls.

**Strongest alternative: a task where stereo is necessary (kinesis near straight-running), with evolution, about 12 GPU-hours.** Second because 02's own lesson is that a scripted gate shows a capability pays, not that the search finds it (`RESULTS.md:283-285`), and the pilot showed 120 generations, 4x worlds or 4x population did not help (D038). Removing the kinesis payoff may just make every champion score like "straight". And a positive result against shuffles with shortcuts and broken symmetry would be uninterpretable, so the control fix has to come first anyway. If 03 leaves budget, a 2-hour shuffle-only gate on such a task, as in D034, is a reasonable tail.

Plasticity should stay deferred: with fixed weights the search has not found the capabilities, and adding a rule multiplies the design space before there is a baseline where wiring matters after evolution. Stopping is premature only because the cheap study can decide it.

**3. Unmeasured, and mostly cheap from local data**

1. **Drive by (graph, mapping) at generation 0.** Free, from `records.jsonl`. Decides point 1 above.
2. **Input-response probe on the evolved champions.** The probe takes only random genomes (`probes.py:91`); a small change accepts a `Genome`. Run on all 72 T0 champions at g0 and g39. Did evolution grow or shrink the directional response, and does it correlate with each champion's bilateral-mean loss? Minutes of GPU.
3. **Selection gradient.** Within each cell, correlate a champion's food-mean loss with its real score, from `probes.json`. If stereo users did not score higher, the search had no reason to find stereo. Free.
4. **Magnitude erosion.** Correlation of |w| at g39 with anatomical magnitude across champions. `RESULTS.md:202` asserts erosion without measuring it. Genomes are local. Free.
5. **Shortcut weight against g0 deficit.** Eight SH graphs, direct food-to-read-out weight 1.5-43 against each graph's g0 M0 minus remap score. Tests the "plausible reason, not tested" at `RESULTS.md:130-133`. Free.
6. **What the champions actually do.** Speed and turn rate as functions of local food and its change over time. `behaviour` (`probes.py:146-177`) saved only aggregates, so this needs a replay with per-tick logging: 72 champions, 4 worlds, minutes of GPU plus code. Do this before any task redesign.