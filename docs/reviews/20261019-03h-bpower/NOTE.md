# 03h: B's power after the pilot

- **Reviewed:** whether B's registered rank test has power, given the pilot (D336), with the exploratory
  `experiments/03h-history-use/development-records/b_power.py` and its output. Both files were uncommitted when the
  review ran, and are committed with D337.
- **The run:** 20261019-154542, both at xhigh effort. `prompt.md` is exactly what was sent.
- **Verdicts:** no consensus. Both said not to run the formal run as designed.
  - **Fable:** "other". Stop B as a confirmatory claim at the pilot. Before deciding whether a redesign is worth a new
    round, optionally spend about 0.2 GPU-hours on a disclosed exploratory check at amplitudes 0.5 and 1.0.
  - **Astra:** "redesign B". Test N2's U against the ensemble mean (Δ = U_N2 − mean U), keeping the rank as a
    secondary, through a dated amendment approved by the owner.
- **What was done** (D337):
  - `b_power.py` now has Fable's second reading of N2's noise and Astra's corrections to its wording;
  - the choice goes to the owner, because it is a change of scientific direction.
