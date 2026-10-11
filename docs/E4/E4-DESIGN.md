# E4 / 04c: do the two minds share? (design v3)

**Status:** v3.
- **The review trail:** v1 and v2 were reviewed by both ("revise" each time; D243-D244;
  `docs/reviews/20261011-E4-design*/`).
- **What v3 changes:** the reading layer (§2's joint table, recruitment, mean substitution, the sign-flip null,
  the scale rule) and the details in §11, as both reviewers of v2 asked.
- **Next:** Fable judged that v3 can go straight to a pre-registration, which both reviewers then review.
- **No GPU** is used until the owner says so (the owner, 2026-10-11). Everything below that needs the GPU waits for
  that word.
- **The ceiling:** 30 GPU-hours (D198).

**The question** (`ROADMAP.md`, "E4 / 04c"):
1. **Shared dependence;**
2. **Useful transfer:** does information crossing between the two modules improve behaviour? This is the primary
   question;
3. **Consolidation,** deferred to stage 09: no mechanism lets evolution silence circuitry at a cost that differs
   between candidates.

**The frame:** a hand-built circuit on a silent worm. Nothing here is about worm behaviour.

## 0. What the reviews changed, in brief

- **The modules were not isolated.** E3a's seed gates its comparators by saturation, and their noses and motor
  edges stay live. **Measured on the CPU** (`scripts/e4_gate_leak.py`, `docs/E4/gate-leak.json`; the seed on 16
  fresh E3f-family mazes):
  - the inactive module's turn signal (tanh CL − tanh CR) is 0.002 at the 90th percentile and 0.074 at the 99th,
    against 0.44 and 1.69 for the active module;
  - it exceeds 0.2 on 0.35% of ticks, and reaches 0.41 at the 99.9th percentile.

  So the leak is small in most ticks, but real on the rare ticks with strong one-sided scent or trail (Fable's
  estimate was about 16% of the active drive).
- **The mode clamp is dropped** (both): it probes a modified organism, and it would be a per-wey engine facility.
- **A real output gate replaces saturation gating** (Astra's choice, §1).
- **T2 is redesigned:** the matched within-module cut was infeasible and biased. It is replaced by cut against
  intact, and by mean substitution (both).
- **The acute reading is primary and the training contrast secondary,** with its minimum detectable effect
  stated (Fable). A full decision table is added (Astra).
- **The diagnostic task** becomes its own experiment, E4-D, with its own pre-registration and ceiling (both).

## 1. The task, the organism and the gate

**The task:** E3f's validated family (6 × 6, k_r = 0, H = 1 800, colonies of 8, shared trails). E4 re-plays the
blind references on its own mazes.

**The organism, E-G:** E3a's E + W2, with one change: **a real output gate.**
- **The engine change** (`Brain`, an optional flag, off by default): a declared set of edges, each module's
  comparator → motor edges, is multiplied per wey by a gate value.
  - **The gate value:** g_A = 1 while the latch state q ≥ 0 and 0 otherwise; g_B = 1 − g_A. The mode signal is
    the latch's sign, an engineered signal, declared as such.
  - **The start:** q starts at exactly 0 (`wormwars/brain.py:402`). With "≥" the first mode is A, as the seed's
    (both).
  - **Switching:** instantaneous at q's sign change.
  - **What stays live:** the inactive module's neurons, its sensory inputs and any cross-link outputs.
- **The comparators are ungated:** biases 0 and Q → comparator edges 0, as E3a's `no_latch` values. Both modules
  compute all the time; only the active one drives the motors.
- **The selector is frozen in both arms** (Fable), so the mode signal cannot be evolved away. The 13 frozen
  parameters, named (both):
  - Q's τ, bias and self-weight;
  - the RA → Q and RB → Q weights;
  - the relays' τ and biases;
  - the four Q → comparator gate edges, pinned at 0.

  The comparators' biases are module parameters and stay mutable. The mutable counts per arm are fixed in code and
  in the pre-registration. A gating check on every champion confirms that it switches (§5).
- **The frozen mask is E4's own:** `assert_frozen` is called with E4's scales. T-F's original mask does not apply
  (Astra).
- **Rule 7:**
  - with the flag off, every engine path is bitwise unchanged: E3d's full-rollout legs, CPU and GPU, and E2's
    batch;
  - a test shows that gated edges carry zero current in the off mode;
  - a sabotage shows that the test fails if the gate is ignored.
- **E-G must be re-qualified:** it differs from E3f's seed, so its competence on E4's mazes is a precondition. It
  must beat the blind family by E3c's margin, with a median of at least 2 legs, as E3f's G3 asked of the seed. If
  E-G is not competent, E4 stops and the owner is asked.

**The cross-links:** exactly **32** directed edges, each of module A's 4 neurons (NL, NR, CL, CR) to each of B's
4, and the reverse.
- **One shared connectome:** both arms use one extended connectome with the 32 slots present at weight 0.
  - **X0:** the slots are frozen by scale 0, checked with `assert_frozen`;
  - **X+:** they are mutable.

  Generation 0 of both arms is then numerically E-G. A CPU test checks that the slotted E-G reproduces E-G's
  per-maze visits exactly.
- **Two subsets,** read separately (both): **sensory links** (from a nose; 16) and **comparator links** (from a
  comparator; 16).
  - **A difference between them is not read as "raw against computed":** a comparator is a saturated difference of
    its two noses, so the subsets carry largely the same content (Fable).

**Training:** E3b-1's T-F mask, minus the frozen selector, plus the 32 slots in X+.
- **Mutation:** factor 0.25 for the inherited parameters, as T-F (Astra).
- **The cross-links' scale,** a reproducible rule decided before the formal run (both):
  - **the candidates:** the factors 0.25, 0.5 and 1.0;
  - **the choice:** the smallest at which a single neutral slot reaches |w| ≥ 1 by the end of training with
    probability at least 0.5;
  - **the lineage:** a simulated champion lineage with the pilot's recorded mutation count, not G, since `breed`
    copies elites unmutated, and with clipping at w_max.
  - **The mutation-load bound:** the pilot's generation-1 X+ mean fitness under common random numbers must be within
    0.25 visits per wey of X0's. If no candidate meets both, the smallest factor meeting the load bound is used and
    the reach is reported.
- **The GA:** E3c's frame (population 32, elites 3, truncation 8), with champion selection on a validation block
  from the final population, as E3c.
- **Runs are paired across arms by run seed** (Fable): run r of X0 and of X+ share the training mazes, and the
  noise draws for the shared parameters (`Genome.mutate` draws the same noise with or without scales). The
  analyses are paired; the pilot measures the gain.
- **Every run is kept** in the reported comparison. Competence qualifies the reading; it never removes a run.

## 2. The readings

**P1, primary: do X+ champions use the cross-links?** (acute, within X+, on the test block)
- **P1-cut:** intact against all 32 cross-links cut. The per-champion difference is averaged over the test mazes.
- **P1-info,** mean substitution (Fable; specified by both):
  - **the edit:** all 32 cross-links are cut jointly, and each target's bias becomes
    b'_j = b_j + Σ_{i→j} w_ij · mean(tanh v_i);
  - **the mean:** unconditional, over every tick (substep end-states), wey and maze of the intact champion's
    validation play under shared trails, with mazes and weys equally weighted;
  - **no clipping:** the substituted genome is built without `Genome.clamp_`. The brain reads `bias` unclamped, so
    a clipped bias cannot leave a tonic residue (Fable);
  - **a check:** a constant-source test where substitution reproduces the original current exactly (Astra).
- **What P1-info shows,** stated narrowly (both):
  - **its direct conclusion:** dependence on the state-dependent cross-link currents, beyond a validation-estimated
    constant replacement. Removing those currents also changes feedback and dynamics, so this is not a pure
    "information" isolation;
  - **the confirmatory wording:** "the time-varying signal crossing the module boundary is used".
  - **"The other module's information is used"** additionally requires the directional read in §4: links into the
    active module, cut against links out of it. Otherwise a module's own signal looped back through the other
    (for example A_CL ← B_NL ← A_NL, a delayed copy) could make P1-info positive with nothing of B's crossing
    (Fable).
  - **mean-substituted − cut** is reported as the effect of that particular constant replacement. It is not a
    uniquely identified tonic component (Astra).
- **The inference** (Astra), two layers as in E3c:
  - **exact:** the sign-flip test across runs (champions are the replicates; mazes and draws are averaged within
    champions), two-sided. It is exact under the null that each run's difference is symmetric about 0, not under
    an arbitrary zero-mean null. Its label is distributional: "the per-run differences are not sign-symmetric
    (exact)";
  - **model-based:** the mean and its practical margin, from a t-based paired interval: "approximate
    (model-based)".
  - **The calibration** includes zero-mean asymmetric cases (Astra: +1 with probability 0.9 and −9 with 0.1 gives
    p = 0.0078 in 43% of 8-run samples).
- **P1's states,** each defined in the pre-registration:
  - **positive / negative:** exact test at the level, and the model-based interval beyond the margin in that
    direction;
  - **practically equivalent:** the model-based interval inside the smaller margin;
  - **inconclusive:** neither;
  - **not evaluable:** competence or the assay failed.
- **Recruitment, defined functionally** (both): a champion's cross-links are "recruited" if its P1-cut effect
  lies outside the evaluation-noise band measured in the pilot (re-evaluation of the same champion on resampled
  mazes).
  - **|w| is descriptive only.** "No detected departure from the neutral weight distribution" is reported as an
    observation; it never overrides an intervention effect, and it never establishes that search failed.
- **Branch B, scramble:** permuting weights among the slots is reported descriptively. It shows sensitivity to
  wiring, not information (Astra).
- **A sabotage check of the cut path** (rule 9): a champion with a known cross-link effect, built by hand, must show
  it.

**P2, secondary: does the option of cross-links raise performance?** (training)
- **The contrast:** X+ − X0 champion test score, paired by run seed.
- **The tests:** the paired sign-flip test (exact, distributional) and a t-based paired interval (model-based).
- **The labels:** E3c's dual margin, defined for E4. "Beyond" uses the larger threshold, "no relevant difference"
  needs the interval inside the smaller, and anything else is "unclear".
- **Its minimum detectable effect at the chosen R is stated in the pre-registration:** at E3c's P-joint spread
  (0.90 visits), unpaired, 8 runs detect about 1.39 visits at a two-sided 0.025 (1.26 at 0.05; Astra). Pairing may
  shrink this. At that power "no relevant difference" is nearly unreachable (Fable), and the table reads "unclear"
  as unclear.

**The test levels:**
- P1-info and P2 are the two confirmatory contrasts, each at 0.025 two-sided.
- A sign-flip test's smallest p is 2 / 2^R, so **R ≥ 7 per arm** (2/128 = 0.016).
- E3c's permutation code, which materialises every permutation, is replaced by an exact enumeration for paired
  data.

**The joint interpretation** (both), fixed now. It covers every state of the readings:
- **P1:** P1-cut and P1-info each positive, negative, practically equivalent, inconclusive or not evaluable.
- **P2:** beyond, no relevant difference, unclear or not evaluable.
- **E4-D's positive control:** working or failed.

| P1-cut | P1-info | P2 | The reading |
|---|---|---|---|
| positive (cutting hurts) | positive | any | evolved organisms use the time-varying signal crossing the boundary. The directional read decides "the other module's information"; P2 is reported beside |
| positive | equivalent or inconclusive | any | they depend on the cross-links, through a constant drive at least in part. The mechanism is tonic or unresolved |
| negative (cutting helps) | any | any | the evolved cross-links cost performance on the test block: a maladaptive or overfitted use. Not transfer |
| equivalent | equivalent | beyond (X+ higher) | a benefit of the larger architecture without acute dependence; the mechanism is unresolved |
| equivalent | equivalent | no relevant difference, competent arms, E4-D's control working | no practically relevant benefit detected by the registered interventions |
| equivalent | equivalent | unclear | no acute dependence detected; the training contrast is unresolved |
| inconclusive | inconclusive | any | unresolved at this budget |
| any | any | not evaluable (an arm not competent) | the comparison is not evaluable, and the competent arm is described |

- **E4-D's failed positive control voids only the null rows,** where the reading would rest on transfer being
  possible. It does not void positive P1 or P2 evidence (both).
- **No row claims that transfer is impossible.** The strongest negative statement is "no practically relevant
  benefit detected by the registered interventions" (Astra).

## 3. Trails, crossed with the interventions

- **P1 is measured under shared trails** (primary), own trails and no trails, each per champion (both).
- **The reading:** a larger cut cost with trails off is consistent with the world channel substituting for the
  cross-links. It does not uniquely establish that mechanism (Astra).
- **A benefit only under shared trails** is still transfer; its dependence is reported. Differences between trail
  conditions are not an additive decomposition of neural against environmental causes (Astra).
- **The seed's and every champion's trails-off split** is measured (D241).

## 4. Shared dependence and the directional read (descriptive)

- **The directional read** (it qualifies P1-info's wording, §2): in X+ champions, cut the 16 links **into** the
  active module against the 16 links **out of** it.
  - **Which module is active** changes by mode, so the two cuts are applied as two genomes, one with the links into
    A cut, and one with the links into B cut.
  - **Both are read as whole-episode effects** on visits.
  - **"The other module's information"** is supported only if cutting the links into each module costs, in that
    module's mode, more than cutting the links out of it.
- **Bundle cuts by source neuron in X+** (each of the 8 sources): whole-episode effects on visits and on leg
  durations.
  - **The limit:** whole-rollout interventions change earlier movement, trails and later states, so they measure
    total episode effects, not direct mode-specific dependence. Matched saved states would be needed for that, and
    are not built (Astra).
  - **Censoring:** legs that an intervention prevents from completing are counted as censored at the horizon, not
    dropped.
- **In X0:**
  - cutting the cross-link bundles is a sham, since the weights are already 0: an equivalence check;
  - deleting a module's neurons measures the total episode effect through every remaining path (world, trails,
    latch). It is not a "leak" measurement, since the gated outputs carry no current (a test, §1).
- **Pruning** (D144):
  - the protocol;
  - the preserved function, competence and the latch's switching, within declared tolerances;
  - acute only, with no retraining, said so;
  - circuit selection kept separate from its final evaluation.

## 5. Controls and checks

- **The blind family:** E3f's, re-played on E4's validation and test blocks. It decides each arm's competence on
  validation, not test (Fable).
- **The navigators:** the scripted follower (shared and trails off), the oracle.
- **Generation 0:** E-G, the unevolved duplicate modules.
- **`no_latch` for a trained champion:** defined as the champion with the output gate fixed at both modules on
  (Astra). It is not the seed constructor.
- **The gating check:** on every champion, the latch switches at visits, and the gated module's motor current is
  zero.
- **Nose classes:** E3c's retained-fraction rule. Coverage and tour match are not inherited (Astra); mixed and
  undefined outcomes, and the aggregation from champions to arms, are defined in the pre-registration.
- **Gene-duplication fate** (functional, both):
  - each module's K_D and cue response (E3a's probe);
  - its mode-specific contribution;
  - the A-B parameter distance against its neutral expectation.

## 6. The pilot (exploratory; GPU, after the owner's word) and the power analysis

**Measured on the CPU first, before any GPU:**
- the leak with the output gate: none expected (a test);
- E-G's competence on a small block;
- the slotted E-G's exactness;
- the timings at small sizes.

**The pilot** (2 arms × 4 paired runs × about 100 generations), measuring:
- per-generation timings at 6 × 6 and H = 1 800, to fix R and G;
- learning curves, and whether improvement continues near G;
- the between-run SD per arm, and the paired correlation;
- the cross-links' |w| against neutral drift, to set their scale and Branch A's band;
- the generation-1 fitness asymmetry under common random numbers;
- P1's per-champion difference and its maze SD, which size the confirmatory reading;
- selection noise against W and the validation size;
- the actual cost of every intervention condition.

**The power analysis** simulates the full decision procedure (Astra):
- competence, pairing, P1 and P2, the margins and the joint table;
- sensitivity to unequal failure rates and skewed outcomes;
- power for benefit and for informative equivalence, and the false-positive and "not evaluable" rates;
- R, G, W and the block sizes chosen jointly under the ceiling.

The pilot-informed specification is published before the formal run, which leaves the formal test data untouched.

**The compute** (to be replaced by the pilot's measurements):
- training at about 0.6 GPU-h per 300-generation run at H = 1 800, from E3c's ledger (about 0.84 h at 2 400). This
  scales by the horizon only; the 6 × 6 arena has 1.4 times the cells, so it may be low (Fable);
- R = 8-10 per arm gives about 10-12 h;
- the pilot 2-3 h; the probes and references 3-5 h.
- **About 20 h,** leaving room under 30. E4-D has its own ceiling.

## 7. E4-D: the diagnostic task (a separate design and pre-registration)

**The purpose:** a task where transfer is **necessary,** to read a null in the main task. **Two candidates,**
decided in E4-D's own design:
- **Astra's B-mode choice:**
  - a fresh, randomised cue shows which of two routes is safe, and only A senses it;
  - A's motor output is off, via the output gate;
  - environmental paths are excluded;
  - a hand-configured X+ positive control, using the actual interface, must succeed, and X0 must be invariant to
    the cue.
- **Fable's swapped noses:**
  - each module senses the other's scent, with no engine work for the task;
  - it is a search positive-control, not a naturalistic task.
  - **Its necessity claim is withdrawn** (Astra). The active module still has the other source's scent, wall
    sensing, history and trails, so X0 may navigate indirectly. And comparator-origin links can carry processed
    scent too.
- **The preference:** Astra's randomised B-mode choice, with timely completion required, and cue reversal, cue
  shuffling and cross-link removal as controls.

**The order:** E4-D's positive-control feasibility check (CPU, exploratory engineering) is run **before** the main
formal run, so that a null in P1 or P2 can be interpreted. A hand-configured success shows architectural feasibility,
not evolutionary discoverability.

**E4-D's own ceiling needs the owner's word** (Fable): D198's 30 GPU-hours were E4's.

## 8. Prior results (to be checked before citing)

Kashtan and Alon (2005), Clune, Mouret and Lipson (2013), and Calabretta and colleagues (2000) concern how
modularity arises, not transfer between fixed modules (Fable). They are flagged until checked.

## 9. Corrections to v1

- The cross-links are exactly 32, not "32-50".
- The relays' τ and biases are frozen, but their weights to Q are mutable in T-F. In v2 the whole selector is
  frozen.
- E3c trained 8 S-mod, 8 S-dense and 4 P-sel runs, and reused P-joint's 8.
- Mutation "as E3c" is ambiguous; v2 uses T-F's 0.25.
- Competence is read on validation.

## 10. Decisions open for the reviewers of v2 (answered in v3)

1. **The output gate** (the engine change, Q's sign as the mode, the frozen selector): sound, with the leak data
   in §0?
2. **Ungated comparators:** acceptable, given that E-G must be re-qualified?
3. **P1-info's mean substitution,** the time-averaging window and its validation source.
4. **The cross-links' scale rule.**
5. **E4-D's ordering:** its feasibility check before the main formal run.

## 11. v3's changes (both reviews of v2, D244)

- **The joint table** covers every state of P1-cut, P1-info, P2 and competence. E4-D's failed control voids only
  nulls (both).
- **Recruitment is functional;** |w| is descriptive. The scale rule is reproducible: candidates, a quantile, the
  lineage's mutation count, clipping and a load bound (both).
- **Mean substitution:** all 32 links jointly, an unconditional validation mean, no clipping, a constant-source
  check. The claim is narrowed, and the directional read qualifies "the other module's information" (both).
- **The sign-flip null is stated** (sign symmetry), with model-based mean and margin inference and calibration on
  asymmetric zero-mean cases. The detectable effect is 1.39 visits at 0.025 (Astra).
- **The gate at q = 0** (A first). The 13 frozen selector parameters are named, and E4's own frozen mask is used
  (both).
- **§4:** whole-episode effects with censoring; the X0 sham defined (Astra).
- **E4-D:** the swapped-noses necessity claim is withdrawn, the B-mode choice preferred, and its ceiling is the
  owner's word (both).
- **Smaller fixes:** the sensory and comparator subsets are not read as "raw against computed"; the timing caveat;
  trail interactions read as "consistent with" (both).
