# E4-D: a task where transfer is necessary. The feasibility check

**Status (2026-10-13):** **passed** (CPU, exploratory engineering; D262). A hand-configured cross-link control carries an
engineered A → B steering signal through the slots, with every integrity check holding.

**What it is for:** E4's main task was not run; both reviewers judged that its null would be inconclusive (D257,
`../RESULTS.md` §5). E4-D is a task where
information must cross from module A to module B. The owner made it E4's confirmatory direction (D258). This check
asks only whether the architecture can carry such a signal at all, before an evolutionary E4-D asks whether evolution
finds it.

**The design:** [`docs/E4/E4-D-DESIGN.md`](../../../docs/E4/E4-D-DESIGN.md) v2.3. It was reviewed by both reviewers at
v1, v2 and its code (D249-D250, D260). Its rules, blocks and criteria were fixed before anything was played.

## The trial

- **The candidates:** each trial is one wey in one of E4's 6 × 6 island mazes. Its two goal sites are the candidates,
  and one of them is real. Each maze is played twice, with each candidate designated real once.
- **The start:** the wey starts in mode B (the latch at −1), at a start cell chosen from the maze alone, near a junction
  between the candidates.
- **What each module senses:**
  - B's noses read the sum of both candidates' scents, the same under either assignment;
  - A's noses read the real candidate's scent alone: the cue;
  - A's motor output is gated off until the entry, as checked at every substep.
- **The score:** the first candidate entered, within 600 ticks.
- **The pairing:** every maze is played under both assignments from identical starts.
- **The chance level:** X0 (no cross-links) cannot tell the assignments apart, so its real-first share of entries is
  exactly 0.5 by construction.

## Results (`scout.json`, `calibrate.json`, `evaluate.json`)

**Scouting** (32 mazes, each under both assignments):
- **No maze skipped.** All 32 had a qualifying start.
- **σ_D = 6,** the smallest width meeting the rule (the oracle, B smelling the real candidate, at least 0.75 real-first
  over all trials, and X0 entering on at least 0.75 of trials): at σ = 3 the oracle made 0.66; at 6, 0.81, with X0
  entering every trial.
- **The lateral cue at the start is near zero:** at σ_D = 6, the median |left − right| of a candidate's scent at the
  start is 0.0005 (the sum's 0.0014), and 9.4% of trials start with no difference at all; at σ = 12 the medians are
  0.025 and 0.045. The cue develops as the wey moves.
- **The guarantees held:** X0's real-first share of entries was exactly 0.5 at every width, and the latch held in every
  trial.
- **Reproduced:** the rerun after a fix to the stage guard (D261) reproduced its first attempt (`scout-attempt1.json`)
  exactly.

**Calibration** (32 further mazes; real-first share over all trials):

| weight w | 0.05 | 0.1 | 0.25 | 0.5 | 1 | 2 | 3 |
|---|---|---|---|---|---|---|---|
| comparator-origin (A_CL → B_CL, A_CR → B_CR) | 0.53 | 0.53 | 0.53 | 0.59 | 0.66 | 0.80 | **0.83** |
| nose-origin (B's four signed edges, from A's noses) | 0.50 | 0.50 | 0.53 | 0.55 | 0.55 | 0.63 | 0.66 |

The comparator-origin wiring at w = 3 was chosen; it entered a candidate on 61 of 64 trials, every other weight on
64. The oracle made 0.91 on this block.

**Evaluation** (64 further mazes, 128 trials):

| condition | real-first, all trials | entered |
|---|---|---|
| **the control** | **0.83** | 127 of 128 |
| the oracle | 0.88 | 125 |
| X0 | 0.50 | 128 |
| the control, cross-links cut | 0.50 (bitwise X0) | 128 |
| the cue reversed (A told the decoy) | 0.16 | 127 |
| the cue held fixed | 0.49 | 126 |
| the cue removed | 0.50 | 128 |

- **The control's maze-level bound:** its one-sided 95% lower bound was 0.78, above 0.5.
- **Every integrity check held:**
  - X0 was bitwise invariant to the assignment, at every tick;
  - the reversal mirrored the control, a mapping check;
  - with the cue held fixed, the control was bitwise invariant to the assignment;
  - cutting the cross-links gave X0 exactly;
  - the latch stayed in mode B in every trial.

## What it shows, and what it does not

- **It shows:** the architecture, with the real interface, can carry an engineered A → B steering signal through the
  cross-link slots, and B uses it.
- **It does not show:**
  - that evolution finds the transfer;
  - that E4's A has anything worth sending under its ordinary inputs (in a trial A gets an input E4's A never has).
- **For the evolutionary E4-D:** the weights that carry the signal (about 2-3) are about a hundred times the random
  cross-link steps that already cost heavily in E4's main task (cross-link factor 0.25 of the weight σ 0.08, about
  0.02; `../pilot.json`; the ladder in `../calibration.json`). Whether selection
  can climb that far is the question. *(2026-10-15: the evolutionary E4-D answered it: selection on the slots
  alone recruited the transfer, at weights far smaller than the hand-built control's 3; `../E4-D-evo/README.md`,
  D280.)*

**Compute:** CPU only (`compute-record.json`).
