**Scope:** read at 0c65e42, read-only, no shell. I ran none of the tests; everything below is from reading the code.

## The five changes

| Change | Status |
|---|---|
| 02b's aggregate | Present (`analyse.py:465-466`) and git-ignored (`.gitignore:73-74`). One defect, below. |
| `allow_abbrev=False` | In all five legacy parsers. `exp02.py` and `exp03.py` have no `--out`, so they cannot diverge. |
| `aggregate` names attempts | Done (`accounting.py:238-240`). The test covers `script`, `argv` and `status`. |
| Non-zero `SystemExit` test | Present (`test_t0_accounting_c.py:95-103`). |
| Plan text amended | The "tests check" list is accurate: I matched each item to a test. The "untested" list is incomplete, below. |

## Defects, none blocking

1. **02b's aggregate is not written when a stage fails.** `write_aggregate` comes after the `with attempt(...)` block, not in a `finally`. A failing stage writes its attempt file, then the exception skips the aggregate. `compute.json` stays stale until the next successful stage. `run_script` does this correctly (`accounting.py:265-270`). D071's "after every stage" holds only for successful stages.

2. **The abbreviation test matches source text, not behaviour.** It fails if someone adds `description=` to a parser. That is acceptable for five frozen scripts.

## The plan text (`T0.md` section 1)

I confirm the amendment in substance. I ask for three corrections:

1. **`T0.md:39-40` contradicts `T0.md:28-29`.** It says the benchmarks' "worlds and brains still pass through the same hooks". `bench_brain.py`'s `SparseBrain` does not (`bench_brain.py:148-151`). Add "except `SparseBrain`, above".

2. **The untested list omits three groups:**
   - **Pilot and exploration scripts** write no compute file but call `evolve`, `rollout` and the probes:
     - `experiments/02-screening/exploration/` (`search_pilot`, `long_pilot`, `feasibility_probe`, `structure_and_timing`);
     - `experiments/03-generation0/timing.py`.

     These matter more than the viewers, because pilots are real experimental compute. Either list them as unrecorded, or state that future pilots run inside `attempt`.
   - **The "final" and "tuning" categories** are set in production (`exp02.py:354`, `evolve_forage.py:85`, `experiment.py:148`, `scripted.py:185,198`). No test asserts either.
   - **Four exp02 probes and two calibration functions** are categorised but untested: `valence_check`, `channel_dependence`, `gen0_scores`, `integrator_rescore`, `raw_motor_magnitude` and `calibrate_in_world`.

3. **"Twelve places build a `World`" is wrong at this commit.** I count 13 call sites in 11 files outside the tests. This text predates D071. Drop the number or correct it.

## Checked and fine

- exp03's `Pool` workers (`exp03.py:237`) only build graphs. They step no worlds or brains, so no counts are lost in child processes.
- `compute.json` sits outside the globbed `compute/` folder, so the aggregate never reads itself.

The remaining points are one `try/finally` and wording. I do not need another round if they are applied as described.

item 2: accept