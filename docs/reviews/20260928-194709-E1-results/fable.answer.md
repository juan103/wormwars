# E1 results review

**Verdict up front:** the outcome is sound and the run followed the registration. RESULTS.md needs a handful of small text fixes, none of which changes the outcome.

**What I could not check:** the freeze's sha256 (no hashing tool; RESULTS matches what `gate.json` recorded), `gate_events.npz` (binary), GitHub's own push log (local reflog only), and the bootstrap bounds (not recomputed; they are consistent with the means and are exact multiples of 1/1024 or 1/2048).

## 1. Did the run follow the pre-registration?

Yes. Timeline from `.git/logs` and the compute records (UTC, 28 Sept):

| Time | Event |
|---|---|
| 17:38:04 | `eb0b781` committed |
| 17:38:17 | pushed |
| 17:38:26–40 | guarded smoke pilot and gate at `eb0b781`, both completed, 16 arms |
| 17:38:54 | pilot starts; ends 17:44:11 |
| 17:44:35 / 17:44:43 | `a73a67d` committed / pushed |
| 17:44:52 | gate starts; ends 17:45:30 |
| 17:46:48 | `20e98aa` (results) committed |

- **Push before run:** met for both stages, by 37 s and 9 s.
- **Freeze by rule:** I re-derived every winner index from the grids. All are first maxima, and σ and the navigator follow their rules.
- **Gate once:** two attempts recorded, zero failed, exclusive markers present.
- **Worlds:** all at offset 1 000, as registered.
- **Environment:** identical on all seven keys between pilot and gate.
- **Cap:** 354 s of 8 h.

**Unreported gaps (not deviations in the run itself):**
- **The guarded smoke run's evidence is not committed.** Its records sit in `runs/e1-smoke/compute/`, which `.gitignore` excludes. `development-records/` stops at 17:03. The Timeline's claim rests on local files.
- **RESULTS was committed 78 s after the gate ended.** That is fine, but it left no time for event-table analysis, and it shows (see 3).

## 2. Numbers and wording

Every number in RESULTS.md matches `freeze.json` and `gate.json`, with these exceptions:

- **Gate duration.** "36 s" is `gate.json`'s figure. The cited `compute-record.json` says 37.6 s. D100 has the same figure.
- **"every blind baseline (5.62 against at most 0.94)".** 0.94 is K, which reads the cue. The blind maximum is 0.65.
- **"No gate world was evaluated before the gate".** This is stronger than the registered §7.3, which rests on command order for the second smoke pair. Keep the hedge; the indices actually used (1 000–2 023) are clear either way.

The outcome wording is exact.

## 3. Is the reading fair?

**Bang-bang.** True but incomplete. The best tuned mean per gain, from `freeze.json`:

| k | 8 | 16 | 32 | 64 | 256 | 1024 | 8192 |
|---|---|---|---|---|---|---|---|
| mean | 3.18 | 4.13 | 5.63 | 6.97 | 8.51 | 8.77 | 8.78 |

- k = 8192 beats k = 1024 by two arrivals in 256 episodes.
- The plateau starts near k = 256.

**k ≤ 32 as the "realistic target".** This is overclaimed.
- The bound came from my own design review as a heuristic. It was never derived or measured.
- By my rough estimate (unverified against the brain code), a short feed-forward path at `w_max` gives a k of order 20. Recurrent amplification or saturation can exceed that.
- The curve is steep exactly there: 64% of the oracle at k = 32, 79% at 64, 96% at 256.
- The k ≤ 32 winner also relies on a turn bias of 0.2 (turn 0 gives 4.23), so it is a different strategy from the bang-bang one.
- Report the curve, and label the bound as an assumption.

**Mirrored decoy.**
- It shows the scent field controls where the wey goes.
- "Because it steers to the decoy" is asserted, not measured. The event table can test it: the distance from the head's end to (23 − x, 23 − y).
- The no-information comparison is the constant probe (0.05) and the best blind search (0.65). The decoy captures the wey, so 0.03 overstates the information's value.
- The mirrored row's leg statistics rest on 29 legs.

**σ = 6 flag.** Fairly reported. What is missing is that it matters more for 04a than for E1. At the 5% floor the input is about 0.018, and the stereo difference is smaller still, against a bias standard deviation of 0.5.

**Generation 0.** "Selection will need" shaping is not shown.
- The design's trigger (counts mostly zero) is met, and that is all the data supports.
- A mean of 0.031 gives about 8 arrivals per 256-episode generation, so the signal is sparse but not absent.
- The best random genome (0.69) matches the tuned blind baselines. The likelier risk is convergence on blind search, as in 02.

**Missing from RESULTS:**
- The one failed world (996 201 898: navigator 0, oracle 8) is not described.
- Grid-edge winners are not flagged. The wall-follower and the random walk win at an edge on every parameter, so the blind baselines may be under-tuned. That is irrelevant to E1's margin of 8, but not to 04a's.
- The oracle is a reference, not a per-world ceiling: the navigator beats it on some worlds.

## 4. What 04a's pre-registration must take

- **Task N frozen exactly,** with its config hashed. A stronger cue is a pre-declared fallback only.
- **Baselines:** re-run the frozen scripted arms on 04a's hold-out worlds, paired. Do not reuse gate-world numbers. State the grid-edge limitation.
- **Shaping:** fitness = count + c × progress, with c < 1. Used in training only; the gate runs on raw counts. Add an unshaped arm as secondary, since it is cheap and tests the "need".
- **Budget:**
  - 16 runs × 500 generations is 2.05 M strain-worlds: 1.3 GPU-h at 438/s, 5.2 at 110/s.
  - Apply a 2× margin, because evolution overhead and the hold-out composition (1 strain × N worlds, padded) were not measured.
  - A different worlds-per-strain needs its own throughput measurement.
- **Composition:** declare it for training, hold-out and generation 0. Batching 8 runs changes strains per chunk. Seed by run id, not batch position.
- **Generation-0 baseline:** best-of-N selected on training worlds and scored on hold-out. Save per-genome, per-world scores, which E1 did not.
- **Gain:** measure the champions' effective gain and report it against the curve. Set no threshold relative to k ≤ 32.

## Before merge (non-blocking)

- Add `experiments/E1-navigation/README.md`; every other experiment folder has one.
- Update AGENTS.md's "no run so far met it".
- Make all fixes as dated corrections, since `20e98aa` is pushed.

**E1 results: fix** — (1) gate duration or its citation; (2) "blind baseline … 0.94"; (3) restore the §7.3 hedge on gate worlds; (4) commit the binding smoke run's records; (5) soften or support three claims: "selection will need", "a gain a brain can plausibly produce", and "because it steers to the decoy".