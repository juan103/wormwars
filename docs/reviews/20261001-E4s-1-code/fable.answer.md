**Verdict: fix then run.** I found no bug that would silently corrupt a formal number. There is one control-flow bug that can strand the experiment after the GPU-hours are spent, plus several departures from the bound text. I read the code only; I did not run the tests or the smoke.

## Departures and bugs

1. **A final not-completed batch blocks everything, including evaluation** (`scripts/e4s1.py:531-534`, `586-596`).
   - `require_earlier` is called without `final_ok`, so a batch that stopped twice makes `completed_batches` raise.
   - §8 says "the evaluation covers whatever completed", and §6 anticipates dropped pairs.
   - It is a likely path: a non-finite score recurs on a rerun with unchanged seeds, and the fix would then trip `require_same_code`.
   - Fix: in `completed_batches`, skip records that are final and not completed (as E2d's `require(..., final_ok=True)` does) and list them as not run.
   - Decide now whether later training batches proceed after a final stop: the prereg is silent, E2's precedent is that they go on, and the code blocks them.

2. **`eval-training` has no admission check** (`e4s1.py:674-679`).
   - §8 requires it for both evaluation stages.
   - The G0 population count runs in `eval-endpoints` (`:643-651`) but is priced under `along` (`:341`), so the endpoints' admission under-prices by about 0.79 M episodes.
   - Fix: add the check and move the term.

3. **Registered tests are missing (§10).**
   - Test 4 (the H conditions change only the intended currents): absent.
   - Test 6 (open loop, L/R = m ± d/2, u clamped): absent; `open_loop` is exercised only by the smoke.
   - Test 10: the inputs are tested, but the coverage (the cyclic tiling, six validation batches, 48 single runs) is not, because it sits inside the `cmd_gate2` closure (`:423-428`).
   - Test 2: R's recorded hash is untested.
   - Fix: pull coverage into a testable function and add the four tests, each seen failing first.

4. **G2's input shape is an interpretation** (`e4s1.py:381-385`).
   - §3 says `size=(300, S)` "in `iface.signal_names` order", but `signal_names` has one entry per channel, with repeats (`interface.py:48`).
   - The code uses the distinct names in first-appearance order, which changes the draws.
   - I think the code's reading is the only coherent one ("shared", "as routed"), but a failed G2 is final.
   - Fix: add a dated note in §13 or `DECISIONS.md` before the gate runs.

5. **The projection departs from §3** (`e4s1.py:309-332`).
   - The open loop is timed once, not twice with the second used.
   - The probe shape is not instrumented (no `motor_stats`).
   - Training and validation are timed through six `evolve_batch` generations, not "one chunk, twice".
   - This affects admission only. Fix the first two; disclose the third.

6. **Mutation counts are not logged per generation** (`e4s1.py:507-518`).
   - They are one analytic constant per batch, which could not detect a scale that was not applied.
   - The end-of-run assertions cover N and F0 only. Disclose it, or add a real check.

7. **Some genome loads are unverified** (`e4s1.py:599-601`, `688-693`, `708`).
   - Along-training candidates and M's final populations are not checked against `checkpoints[k].sha256` or `final_sha256`; only F, C and G0 are.
   - Nothing asserts that `checkpoint_generations[k] == gen`. The index arithmetic is right for 0, 100, 250, 500, 750 and 999, but unguarded.
   - `load_genomes` omits E2's brain-config equality check (`e2.py:960-966`).

8. **The G0 population is regenerated, not verified** (`e4s1.py:644`).
   - Fix: assert that the run's `checkpoints[0].sha256` is among `pop0`'s hashes.

9. **`sources()` runs inside the bodies of gate-2 and gate-3** (`e4s1.py:400`, `449`).
   - A missing or mismatched local genome file would spend the gate's single rerun.
   - Fix: load in `requires`, as `cmd_train` already does for C2.

## Checked and found as registered

- **Gates:** G1's bound and class; G2's 48 genomes in order, separate batches, the four shapes, host-only states and the world's injection formula; G3's 24 genomes and its ≤ 0.05 test.
- **Arms:** generation 0, shared run and breed seeds, C2's 32 copies and seed base, one mask for every arm, `arm_scales`, and exact pinning at factor 0 (L1 on the bounds survives the clamp).
- **R and N:** R's seed, order and s_k × 3.0; N's output edges in the mask at 0.
- **Genomes:** F is the last checkpoint candidate, C the first-best checkpoint, G0 checkpoint 0, each hash-checked.
- **Conditions:** all 14 and their applicability (N: 1, 2, 4, 5; G0: 1-11); the world's "mean" and "swapped" probes exist; silencing works with padding; the Mc transplant keeps the carrier's biases; reset uses the run's own draw.
- **Open loop:** the sensor gains and `input_gain` are all 1, so the raw currents are correct.
- **Order and readings:** the stage order, the stop on a failed gate, and the rules in `readings.py`.

## What the records do not store

- **G0 population:** per-world counts and per-strain contrasts; only the classes are kept (`:648-651`).
- **Module parameters:** the 20 weights with edge names, and the 4 τ and 4 biases, at G0, C and F for every non-N arm.
  - Only R's F weights are kept, unlabelled and in spec edge order rather than `module.json` order (`:642`).
  - §2's drift-from-bounds reading and F0 − M need them, and the genomes are local only (rule 5).
- **Along training:** the checkpoint generation and hash actually evaluated.
- **Closed-loop motor measures:** per-world values; only the means are kept.
- **The analysis itself:** no script yet applies `readings.py` (O1, O1b, the companions, the sign-flip p, O2b, C2, the O3 split, E3's rule). Write and test it on the smoke records before formal data exists.