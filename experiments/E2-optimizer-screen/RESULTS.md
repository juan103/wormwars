# E2: a short optimizer screen. Results

**Outcome (the registered wording, §8):**

> **E2: keep 02's GA (unshaped fitness; the ES did not satisfy both replacement criteria after
> paying for its tuning)**

**The floor (registered wording, §8.4), which takes precedence over proceeding to E3:**

> **diagnose first: random sampling's mean is at least the GA's minus 0.5; saturation, noise and
> budget are diagnosed before building on the task, whatever the ES did**

Every number below is from the committed records in this folder (`evaluation.json`,
`train-*.json`, `pilot-*.json`, `extension.json`, `projection.json`, `compute-record.json`). The
pre-registration was bound at `60af3cf` (v4, D123). Every formal stage ran once, on CUDA, on the
binding code, with no rerun, no amendment and no stop. The records are at commits `6be6dfe`
(pilot 1) to `5faa1ff` (the evaluation).

## 1. The primary measure: the hold-out

1 024 fresh worlds, each champion one strain on all of them. The counts are targets reached per
300-tick episode, as the mean over worlds. The run is the unit.

| Method | Mean of 8 champions | SD | Champions (real probe) | Fraction of the oracle |
|---|---|---|---|---|
| 02's GA | **1.961** | 0.496 | 2.21, 2.14, 0.75, 2.12, 2.11, 2.18, 1.96, 2.21 | 0.224 |
| OpenAI-ES | **2.086** | 0.115 | 1.95, 2.19, 1.97, 2.21, 2.14, 2.15, 2.14, 1.93 | 0.238 |
| random sampling | **1.605** | 0.175 | 1.52, 1.54, 1.36, 1.71, 1.77, 1.87, 1.42, 1.64 | 0.183 |

**The decision** (`decide`, exact arithmetic):
- **The margin:** the ES minus the GA is **+0.125** targets per episode; it needed at least 0.5.
- **The spread:** **5** of the ES's 8 champions are above the GA's median champion (2.131); it
  needed at least 6.
- Both criteria fail, so **the GA stays E3's provisional default.** All three batches completed.

**The floor:** random sampling minus the GA is **−0.356**, which is at least −0.5. The roadmap's
rule therefore applies before anything builds on Task N: diagnose saturation, noise and budget
(ROADMAP.md, "What would change this roadmap").

**The pairing check passed:** in all 8 runs, each method's generation-0 checkpoint candidate and the
ES's start genome are the same genome, by hash. Per run, the ES minus the GA:

| Run | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| ES − GA | −0.26 | +0.05 | +1.22 | +0.09 | +0.03 | −0.03 | +0.18 | −0.28 |

Run 2 carries most of the ES's lead. The GA's run 2 champion scored 0.75 (§3).

## 2. The probes (reported, not gating)

Hold-out means under the mirrored and the constant probes (§7, §9):

| Method | Real | Mirrored | Constant |
|---|---|---|---|
| GA | 0.75-2.21 | 0.12-0.74 | 0.11-0.74 |
| ES | 1.93-2.21 | 0.09-0.19 | 0.12-0.65 |
| random sampling | 1.36-1.87 | 0.07-0.33 | 0.08-0.41 |

For 23 of the 24 champions, the mirrored and constant probes fall far below the real cue, so their
counts depend on the cue. The exception is the GA's run 2: real 0.75, mirrored 0.74, constant 0.74.
Its count does not depend on the cue at all.

## 3. Training

**The GA** (generations 0-999). Its champions came from generations 150-975. The runs' mean
validation count rose to about 1.5 by generation 100, then stayed between 1.47 and 1.90 (every
checkpoint from generation 100 on):

| Generation | 0 | 100 | 200 | 300 | 400 | 500 | 600 | 700 | 800 | 900 | 999 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GA, mean validation | 0.28 | 1.51 | 1.59 | 1.59 | 1.47 | 1.60 | 1.56 | 1.71 | 1.80 | 1.82 | 1.74 |

The GA's run 2 never found a cue-follower: its champion scored 0.82 on validation (generation 900).

**Random sampling** (generations 0-999). Its checkpoint candidates averaged only 0.60-1.06 on
validation (the runs' mean, at every checkpoint from generation 25 on). Each candidate was the best
of the genomes drawn since the previous checkpoint: 800 (25 generations × 32), 768 for the last
(generations 976-999), and 32 at generation 0. **Its champion, the best of 41 such candidates, 32 000
random genomes in all, reached 1.38-1.90 on validation and 1.36-1.87 on the hold-out.** The
selection held up on unseen worlds. Its champions came from generations 75-999.

**The ES** (generations 0-622 at σ = 0.5 and a learning rate of 0.15; §4). Its mean validation count
was still rising at the registered end:

| Generation | 0 | 100 | 200 | 300 | 400 | 500 | 600 | 622 |
|---|---|---|---|---|---|---|---|---|
| ES, mean validation | 0.28 | 1.11 | 1.55 | 1.81 | 1.83 | 1.90 | 2.05 | 2.02 |

- **Start screens:** seven runs started from a genome scoring 0.125-0.625 in training. Run 2's 32
  start genomes all scored 0. It was flat in generations 1-51, first moved at generation 52, and was
  flat three more times (53, 55, 56): 54 flat generations in all. No other run had a flat
  generation.
- **Clipping:** about 2.5% of candidate coordinates were clamped per generation (2.39-2.66% per
  run).
- **Champions:** from generations 375-600.

## 4. The pilot

| Stage | Setting | Total validation count, 3 runs (generation 199) |
|---|---|---|
| 1 | σ 0.5, rate 0.3 σ | **1 186** (434, 429, 323) |
| 1 | σ 1, rate 0.3 σ | 683 (341, 184, 158) |
| 1 | σ 2, rate 0.3 σ | 540 (154, 238, 148) |
| 2 | σ 0.5, rate 0.1 σ | 868 (242, 432, 194) |
| 2 | σ 0.5, rate 1 σ | 1 128 (420, 361, 347) |

**Selected: σ 0.5, rate 0.3 σ** (0.15), with no tie. Neither stage was uninformative.
**σ 0.5 is the smallest σ in the registered grid**, so a smaller σ may do better; E2 did not test
one. With 3 runs per setting, the pilot screens; the gap between rates 0.3 σ and 1 σ (1 186
against 1 128) is well within its noise.

## 5. The extension (descriptive; never enters the decision)

The 8 formal ES runs resumed from their saved states and ran generations 623-999. Their mean
validation count kept rising: 2.02 at generation 622, 2.16 at 850, and 2.31 at 999.

- **Champions:** 7 of the 8 are extension checkpoints (generations 925-999). Run 6's is its formal
  champion (generation 550).
- **Hold-out: mean 2.331**, per run 2.33, 2.30, 2.01, **2.91**, 2.38, 2.23, 2.14 and 2.35. That is
  0.37 above the GA's mean and still below the 0.5 margin.
- **This is not an equal-work comparison.** The extended ES used 802 560 pilot + 1 329 152 formal +
  804 864 extension = **2 936 576 selection episodes**, against the GA's 2 131 968.
- **Selection optimism:** each extension champion was chosen over 42 checkpoints (§6).
- **What it shows:** the ES's "keep the GA" is partly a budget effect. It was still improving when
  its charged allowance ran out.

## 6. The controls (for scale)

E1's scripted controls at their frozen parameters, on the same 1 024 worlds:

| Control | Mean |
|---|---|
| oracle | 8.76 |
| S-const | 8.65 |
| S-const k≤32 | 5.54 |
| M-avg | **2.20** |
| K | 0.91 |
| wall-follower | 0.63 |
| constant | 0.46 |
| random-walk | 0.28 |

Every method's mean is below M-avg (2.20). The best single champion, the extension's run 3 at 2.91, is
a third of S-const.

## 7. The ledger

From the accounting (`compute-record.json`; one attempt per stage, all completed). Episodes equal
worlds built: training plus checkpoint validation, as registered.

| Stage | Episodes | Neural updates | Wall time |
|---|---|---|---|
| projection | 79 872 | 7.7 × 10⁸ | 196 s |
| pilot stage 1 | 481 536 | 4.6 × 10⁹ | 1 073 s |
| pilot stage 2 | 321 024 | 3.1 × 10⁹ | 821 s |
| GA | 2 131 968 | 2.05 × 10¹⁰ | 4 863 s |
| random sampling | 2 131 968 | 2.05 × 10¹⁰ | 4 920 s |
| ES, formal | 1 329 152 | 1.28 × 10¹⁰ | 3 084 s |
| extension | 804 864 | 7.7 × 10⁹ | 1 870 s |
| evaluation | 90 112 | 1.6 × 10⁹ (padding 7.9 × 10⁸) | 235 s |
| **total** | 7 370 496 | 7.1 × 10¹⁰ | **17 062 s, 4.74 GPU-hours** |

- **The ES's allowance:** 481 536 + 321 024 + 1 329 152 = **2 131 712**, against 2 131 968 for the GA
  and random sampling, as registered.
- **Time:** 4.74 GPU-hours against the 7-hour cap. Training (the pilot, the three methods and the
  extension) took 16 631 s, 4.62 hours, against the projection's 5.11.

## 8. What this means, and what it does not (not registered: interpretation)

- **The decision is as registered:** 02's GA stays E3's provisional default. At equal charged work,
  the ES was ahead by 0.125 targets per episode, far below the 0.5 needed. The two methods'
  champions overlap except for the GA's one failed run.
- **The floor fires, and it outranks the decision.** Random sampling came within 0.36 targets of the
  GA. On Task N at this budget, 1 000 generations of either optimizer add little to selecting the
  best of about 32 000 random genomes. The roadmap says to diagnose before building on the task.
  The pre-registration names three candidates, and the records give only pointers, not answers:
  - **saturation:** every method sits near M-avg (2.20) and far below S-const (8.65). The task
    allows far more than any method reached, so the ceiling is not the task's;
  - **budget:** the ES was still rising at its end and gained 0.25 on the hold-out in the extension.
    The GA's mean validation drifted up from about 1.6 to 1.8 between generations 600 and 900;
  - **noise:** training fitness is 8 worlds per genome; validation is 256 worlds, and
    validation-to-hold-out agreement was close for random sampling. How much the 8-world training
    signal limits the optimizers is untested.

  **The diagnosis needs its own design and review**; this file does not choose it.
- **What E2 cannot say:** whether the ES would win with a longer budget, a smaller σ, shaped
  fitness, or another evaluation shape; anything about E3's fine-tuning setting; anything about
  topology (§12).

## 9. Deviations and disclosures

- **None from the registration.** No stage stopped, reran or was amended; the extension was not
  skipped; `AMENDMENTS.md` has none.
- **The records were read and this file written after the whole chain finished.** Each number was
  re-derived from the committed JSON, not taken from the chain's console output (D114's lesson).
