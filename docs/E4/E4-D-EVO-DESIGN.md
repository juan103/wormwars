# E4-D, evolutionary: does evolution discover transfer when it is necessary? (design v2.1)

**Status:** v2, after both reviews of v1 (both "go to v2 with these changes"; `docs/reviews/20261013-E4-D-evo-design/`,
D265); v2.1 records the owner's three choices (§8, D266). No code, no compute yet.
- **Its place:** the owner re-scoped E4 to E4-D (D258). E4-D's feasibility check passed (D262): a hand-configured
  cross-link control carries an engineered A → B signal (0.83 real-first against X0's exact 0.5).
- **The budget:** E4's remaining 25.80 GPU-hours (D258), measured by a pilot first. The owner is told before every GPU
  run.
- **The task:** E4-D's single-choice trial, as in the feasibility check (`docs/E4/E4-D-DESIGN.md` v2.3; σ_D = 6,
  H_t = 600, one wey, mode B from the first substep, both assignments per maze, no trails).

## 1. The question

**Starting from E-G with the 32 cross-link slots at 0, does selection on the trial's outcome recruit cross-links that
carry A's engineered cue into B?** It tests whether this GA recruits transfer through 32 available links between
already engineered modules; it does not test the discovery of communication in general (Astra).

**What is unknown is accessibility** (Astra). The fitness is a first-entry outcome: discontinuous, flat across many
mutations, and a wrong-signed link can stop entry as well as redirect it. The feasibility check's calibration gives
0.53 at comparator-origin weights 0.05-0.25, 0.59 at 0.5, 0.66 at 1, 0.80 at 2 and 0.83 at 3; it does not establish a
required weight.

## 2. The arms

- **L (primary): the links only.** Every inherited parameter frozen; only the 32 slots mutate. Cutting the links gives
  E-G exactly.
- **F (exploratory, the owner's choice, §8):** the links with weights and τ at 0.25 and the module biases at 0.02 (its
  bias factor met only the incremental criterion in E4's stage A, unconfirmed; Astra). Its champions are compared with
  their own cut versions, which are not E-G.
- **No X0 is trained.** Any assignment-blind policy scores at most 0.5 over all trials under paired assignments; E-G is
  played on every block as the measured baseline (both).

## 3. Training

- **The GA:** E3c's frame (population 32, elites 3, truncation 8), from 32 copies of E-G.
- **Fitness = the real-first count / 2W** over the generation's W mazes, each under both assignments (both): a decoy
  entry and a non-entry both score 0. **No tie-breaker** (both: an entry or speed term would select the links for
  something other than the cue, and under pairing it carries no cue information).
- **Ties broken at random** (both): `breed` orders by `np.argsort(-fitness)`, which resolves exact ties by index and so
  returns E-G's unmutated elites to the parents every generation when most strains score 0.5. Exact ties are ordered by
  a separate, recorded per-run random stream, for the elites and the parent pool. This is new evolution code: a test, a
  flag that is off for every earlier experiment, and the lineage replay updated to match.
- **The mazes:** within a generation every strain plays the same W mazes, starts and headings (common random numbers);
  drawn fresh each generation by the run seed from a training range disjoint from every block. A maze's two
  assignments are one observation.
- **The trial rollout** for `evolve_batch` returns the real-first share as `score` and zero `progress`; the runs'
  shaping is 0, asserted (Fable).
- **An integrity check every generation** (Fable): every strain whose 32 slots are all zero has equal real-first and
  decoy-first counts.
- **Populations saved at every checkpoint;** snapshots of the full final population.

## 4. The pilot (exploratory; GPU, after the owner's word)

**Before any training** (minutes):
- **The positive control on the GPU** at the intended compositions (Astra): the comparator-origin control at w = 3,
  E-G and the oracle, with every integrity check.
- **Selection visibility** (Fable): the comparator-origin controls at w = 0.5, 1 and 2, and E-G, on 8 independent
  draws of W mazes for W ∈ {8, 16, 32, 64}; the probability that each control out-ranks E-G on a draw. **The formal W is
  the smallest at which the w = 1 control out-ranks E-G on at least 90% of draws;** if no affordable W does, the design
  stops here and is reported.
- **Timing and memory** at each W for 8 runs batched, including maze construction, validation, controls and saves.

**Then the slot factor's screen** (Astra's rule, with Fable's safeguard): arm L at slot factors 0.25, 1, 2 and 4
(σ 0.02, 0.08, 0.16, 0.32), 4 runs each, 100 generations, at the chosen W.
- **Each run's champion** (§5's rule) on a pilot validation block, then on a separate pilot assessment block.
- **The choice:** the factor with the highest median assessment score; exact ties to the smaller factor.
- **The safeguard:** a factor whose generation-1 children's entry rate is below 0.95 of E-G's is excluded (Fable).
- **Reported for every factor:** the tie rates and parent-pool turnover; the children's entry rates; the share of maze
  pairs a child tips; learning curves on validation; the champion lineages' mutation counts and largest |w|, against
  the neutral walk; between-run and run-by-maze variation.
- **Arm F,** if the owner keeps it (§8), at the chosen factor, 4 runs.

**The power analysis** simulates the whole registered rule (final-population selection, finite test blocks,
heterogeneous success across runs) and sets R and G (Astra: target 80% power at a mean gain of 0.20 against the
margin). Everything the pilot plays is published, and the formal runs are fresh.

## 5. The champion

The whole final population (32 strains) on the run's validation block; the best real-first share over all trials;
ties to the higher final-generation fitness, then the smaller cross-link norm, then the lowest index (Fable). New code,
with a test; `evolve_batch`'s checkpoint validation stays descriptive.

## 6. The readings

**The estimand:** per run, the champion's real-first share over all trials on its own test block (64 mazes × 2
assignments; independent blocks per run, Astra), minus 0.5, the bound for any assignment-blind policy. Reported beside:
the champion minus E-G on the same block, and all three counts (real-first, decoy-first, neither).

**The decision rule** (Astra): the mean gain's one-sided 95% t bounds L and U across runs, with margin δ (the owner's
choice, §8):
- **L > δ:** "practically relevant transfer found";
- **0 < L, U < δ:** "weak transfer found";
- **L > 0, margin unresolved:** "transfer detected; its practical size unresolved";
- **L ≤ 0, U < δ:** "practical gain excluded; transfer not detected";
- **otherwise:** "inconclusive";
- **an integrity failure:** "not evaluable". A run that fails for infrastructure is rerun from its seed under a rule
  declared in the pre-registration; no seed is replaced silently.

The exact sign-flip p is reported beside, labelled distributional (one-sided, smallest 1/2^R; Fable and Astra).

**Each champion's controls** on its test block: cue reversal (it goes to the decoy), cue removal and the cue held fixed,
the links cut (E-G in L).

**Descriptive:** the champions' wiring (slots, signs, weights; comparator-origin against nose-origin) against the
hand-configured control's; validation learning curves; the generation at which each run first clears the margin;
reach against the neutral walk; F against L, if F runs.

**The outcome's wording keeps its limits:** an engineered cue, 32 links between engineered modules, selected junction
starts; a null with the selection-visibility check passed says that this GA, at this budget, did not recruit the
transfer from E-G, not that evolution cannot.

## 7. The code and rule 7

- **New:** the trial rollout for `evolve_batch`; random tie-breaking in `breed` (a flag, off elsewhere) with its lineage
  replay; the full-final-population champion; the per-generation integrity check; the pilot runner. Tests at the
  actual multi-strain compositions: assignment ordering, shared starts, masking, the latch, the controls (Astra).
- **Rule 7:** with the tie flag off, `breed` is bitwise unchanged (a test, and E4's lineage replay). The engine is
  unchanged.

## 8. The owner's choices (2026-10-13, D266)

1. **The margin δ = 0.15** (success above 0.65; about half the hand-built control's gain over chance). Astra had
   proposed 0.10.
2. **Arm F runs in the pilot only** (4 runs, at the chosen factor). It enters the formal run (4 runs) only if its
   generation-1 children's entry rate is at least 0.9 of E-G's and the pilot's integrity checks hold; otherwise it is
   reported from the pilot alone.
3. **A seeded follow-up is pre-committed:** if L reads "transfer not detected" or "inconclusive", arm S runs, the same
   as L but seeded at the hand-built comparator-origin wiring (A_CL → B_CL, A_CR → B_CR) at w = 0.5 (0.59 in the
   feasibility calibration, against 0.83 at w = 3). It separates "cannot discover the wiring" from "cannot strengthen
   it". It is registered with L, with its own readings by the same rule, within E4's remaining budget; it is not run if
   L reads "found".
