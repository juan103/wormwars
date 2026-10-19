**Verdict: revise.** The computation is right and the guards work. Four small fixes before the run, none needing another review round: widen the engine guard, move the pilot staleness check before the compute, cast the level means to float64, and state the guide's error rates in the docstring. I read every file named; I did not run the tests or git.

**Confirmed correct**

- **Interface.** `interface_03h` sets both ASK entries' gain to the amplitude (`wormwars/e03h/__init__.py:25-27`). The world multiplies signal by gain and clamps at `input_max` 5.0 (`wormwars/world.py:948-950`, `config.py:56`), so 1.0 injects linearly. ASK's other channel is the ally pheromone, silent in T1. The yaml's 0.25 matches `AMPLITUDE`.
- **Level needs no rerun.** Under level the bit is 0, and 0 × gain is exactly 0, so the currents are identical. The test at `tests/test_e03h_amplitude.py:103-118` can fail. The sham's rates come from level trajectories, so they are amplitude-independent.
- **Decile selection, readings.** Per condition from its own selection scores, tested on the 26 selected, as the pilot (`scripts/e03h.py:416-420`). `b_readings` with only relief and sham keys works. The 0.25 ratio reproduces D337's 0.76.
- **Cap.** Step 0 plus 0b is 158.1 s and the pilot 593.8 s, so 0.2088 h. The clock sums own attempts, step 0 and the pilot without double counting. Expected cost is about 0.13 to 0.15 h from the pilot's timing.
- **Guards.** Pushed tree, pins, engine since ff1fd31, S1's npz, graph and genome hashes, run-once, failed attempts kept. Seed 3 671 001 collides with nothing.
- **Reusing banks and the sham stream** is acceptable and a strength. The stream is a pure function of seed, stream, world, tick and wey (`world.py:805-820`), so the sham's bit sequence is identical at every amplitude and the comparison is paired.

**Findings**

1. **The guide's error rates at three graphs are large and asymmetric** (`scripts/e03h_amplitude.py:22-27`, `132-138`). Severity: medium, for the owner's decision. With a true ratio of about 0.8, Fable's own expectation, the sample ratio exceeds 2 about one time in five per amplitude, and the max over two amplitudes makes that roughly one in four. A true ratio of 2 reads under 1 about one time in fifteen. State this in the docstring, and quote the ratio with the SD's 90% chi-square range as `b_power.py` does, which at 0.25 spans 0.17 to 1.3. The reading that corroborates a ≥2 is whether the mean grew faster than the between-graph SD from 0.25, with the per-graph shifts beside the pilot's. Also say what each branch closes. A ratio under 1 closes the rank route. Astra's ensemble-mean route depends on how N2's own noise is read, and under the world-noise reading the relevant quantity is the mean shift's interval, which the script reports but the guide does not name.

2. **The engine guard omits the driver and the bank** (`scripts/e03h_amplitude.py:70`, `218`). Severity: low-medium. `ENGINE` guards the library, configs and requirements, but the world configuration, genomes and rollouts come from `scripts/e03h.py`, and the turn response's bank from `experiments/03-generation0/pilot.json`. Neither is in the diff check. D336 and D337 describe records-only commits, so they are probably unchanged, but I could not verify by git. Add both paths.

3. **The pilot staleness check runs after the GPU work** (`scripts/e03h_amplitude.py:195`). Severity: low-medium. `P.read("pilot")` is what verifies S1, G1 and G2 are unchanged since the pilot read them. It runs last, so a stale S1 fails the attempt after the compute. Move it before the record moves, and add pilot.json's and bind.json's hashes to `upstream` at line 202 so the record says which pilot it extends. The pilot records directory is not in `GUARDED`, so an uncommitted edit to pilot.json would also pass the dirty check.

4. **The level decile is selected from float32 means** (`scripts/e03h_amplitude.py:164`). Severity: low. The pilot cast to float64 first (`scripts/e03h.py:411`). A near-tie at the 26th place can swap one genome, which changes `level_decile_mean` only. Cast, or load `decile_level` from the pilot's hash-checked arrays as `b_power.py:68` does.

5. **The realised food-fell counts are discarded** (`scripts/e03h_amplitude.py:171`, `176`). Severity: low. At 1.0 the relief bit's occupancy under relief may drift from the level rates the sham uses. The counts are free and show whether the sham still matches.

6. **Record readability.** Severity: low. Per-graph entries in `readings` carry no graph name (lines 127-128), and the 0.25 comparison lacks the selection-bank values that `b-power.json` holds.

7. **No CUDA smoke path.** Severity: low. Smoke is hard-coded to the CPU (line 213). The pilot had a CUDA preflight (D333). A CUDA failure here only costs a kept, counted attempt, so optional.

On the tests: the six cover what they claim. The cap test's margin of one microsecond-hour is fragile but holds for a fresh clock. The hash refusals at lines 148, 156 and 162 are copies of the pilot's lines and have no sabotage test of their own in this file.