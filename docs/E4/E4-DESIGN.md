# E4 / 04c: do the two minds share? (design v2, for review)

**Status:** draft v2, after both reviewers' review of v1 ("revise", both; D243;
`docs/reviews/20261011-E4-design/`). For review again.
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
  - **The gate value:** g_A = 1 while the latch state q > 0 and 0 otherwise; g_B = 1 − g_A. The mode signal is
    the latch's sign, an engineered signal, declared as such.
  - **Switching:** instantaneous at q's sign change; the first mode is A, as the seed's.
  - **What stays live:** the inactive module's neurons, its sensory inputs and any cross-link outputs.
- **The comparators are ungated:** biases 0 and Q → comparator edges 0, as E3a's `no_latch` values. Both modules
  compute all the time; only the active one drives the motors.
- **The selector is frozen in both arms** (Fable): Q's 13 parameters and the relays. The mode signal therefore
  cannot be evolved away. A gating check on every champion confirms that it switches (§5).
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
  - A sensory link can share the other module's raw sense.
  - A comparator link can share its computed comparison.
  - With E-G's ungated comparators, both kinds of information exist.

**Training:** E3b-1's T-F mask, minus the frozen selector, plus the 32 slots in X+.
- **Mutation:** factor 0.25 for the inherited parameters, as T-F (Astra).
- **The cross-links' scale** is set by the pilot's drift measurement (§6). It follows a declared rule: the smallest
  factor at which a neutral slot's random walk reaches |w| ≥ 1 within G generations. The aim is that a useful slot
  can be recruited, without a mutational load beyond the pilot's measured generation-1 asymmetry.
- **The GA:** E3c's frame (population 32, elites 3, truncation 8), with champion selection on a validation block
  from the final population, as E3c.
- **Runs are paired across arms by run seed** (Fable): run r of X0 and of X+ share the training mazes, and the
  noise draws for the shared parameters (`Genome.mutate` draws the same noise with or without scales). The
  analyses are paired; the pilot measures the gain.
- **Every run is kept** in the reported comparison. Competence qualifies the reading; it never removes a run.

## 2. The readings

**P1, primary: do X+ champions use the cross-links?** (acute, within X+, on the test block)
- **P1-cut:** intact against all 32 cross-links cut. The per-champion difference is averaged over the test mazes.
- **P1-info,** mean substitution (Fable): each cross-link is cut, and its time-averaged drive, measured on the
  validation mazes, is added to its target's bias. This is a genome edit per champion, with no engine change.
  - **intact − mean-substituted** isolates the informational part;
  - **mean-substituted − cut** isolates the tonic part.
- **The test:** the exact sign-flip test across runs (champions are the replicates; mazes and draws are averaged
  within champions), two-sided.
- **The confirmatory reading** is on P1-info: "cross-links carry useful information" if it is positive at the
  test level, and exceeds a practical margin fixed in the pre-registration from the pilot.
- **Branch A, "cross-links not recruited":** if every cross-link's |w| stays within the neutral-drift band
  measured in the pilot. In that case P1 is not read as "no information".
- **Branch B, scramble:** permuting weights among the slots is reported descriptively. It shows sensitivity to
  wiring, not information (Astra).
- **A sabotage check of the cut path** (rule 9): a champion with a known cross-link effect, built by hand, must show
  it.

**P2, secondary: does the option of cross-links raise performance?** (training)
- **The contrast:** X+ − X0 champion test score, paired by run seed. The paired sign-flip test, a paired interval,
  and E3c's dual margin defined for E4 (the larger threshold for "beyond", the smaller for "no relevant
  difference").
- **Its minimum detectable effect at the chosen R is stated in the pre-registration** (Fable): at E3c's P-joint
  spread (0.90 visits), unpaired, 8 runs detect about 1.26 visits; pairing may shrink this.

**The test levels:**
- P1-info and P2 are the two confirmatory contrasts, each at 0.025 two-sided.
- A sign-flip test's smallest p is 2 / 2^R, so **R ≥ 7 per arm** (2/128 = 0.016).
- E3c's permutation code, which materialises every permutation, is replaced by an exact enumeration for paired
  data.

**The joint interpretation** (Astra), fixed now:

| P1-info | P2 | Diagnostic (E4-D) | The reading |
|---|---|---|---|
| positive | positive | — | the cross-links' availability improves performance, and evolved organisms use transferred information |
| positive | unclear or none | — | evolved organisms use transfer, without a demonstrated advantage over X0 at this budget |
| none, links recruited | positive | — | a benefit of the larger architecture; the mechanism is unresolved |
| none, links recruited | none | positive control works | no useful transfer evolved under this task and budget |
| not recruited | — | — | the cross-links were not recruited; search, not the absence of transfer |
| any | any | positive control fails | the assay cannot diagnose evolution; unresolved |

## 3. Trails, crossed with the interventions

- **P1 is measured under shared trails** (primary), own trails and no trails, each per champion (both).
- **The reading:** if the cut costs more with trails off, the world channel was substituting for the cross-links.
- **A benefit only under shared trails** is still transfer; its dependence is reported. Differences between trail
  conditions are not an additive decomposition of neural against environmental causes (Astra).
- **The seed's and every champion's trails-off split** is measured (D241).

## 4. Shared dependence (descriptive)

- **In X+:** cut the cross-link bundle by its source neuron (each of the 8 sources). Read per-mode leg durations
  (Fable), not leg counts, since B legs start only after A visits.
- **In X0:** the same deletion matrix measures the remaining leak path. With the output gate it should be near
  zero; that is a check.
- **Whole-rollout deletions only:** mode-conditional deletion would need another per-wey engine facility.
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
- training at about 0.6 GPU-h per 300-generation run at H = 1 800, from E3c's ledger (about 0.84 h at 2 400);
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
  - X0 cannot navigate, and X+ only through sensory cross-links;
  - it is a search positive-control, not a naturalistic task.

**The order:** E4-D's positive-control feasibility check (CPU) is run **before** the main formal run, so that a null
in P1 or P2 can be interpreted.

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

## 10. Decisions open for the reviewers

1. **The output gate** (the engine change, Q's sign as the mode, the frozen selector): sound, with the leak data
   in §0?
2. **Ungated comparators:** acceptable, given that E-G must be re-qualified?
3. **P1-info's mean substitution,** the time-averaging window and its validation source.
4. **The cross-links' scale rule.**
5. **E4-D's ordering:** its feasibility check before the main formal run.
