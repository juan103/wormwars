# 03mc: a confirmatory test of 03m's leads on P4 (design v2.2)

**Status:** design v2.2, 2026-10-16, agreed as the basis of the pre-registration. Not a pre-registration;
nothing fresh has been drawn or run.
- **v1** (`6e948d7`, D285): both reviewers said "revise" (run 20261015-232952, D286).
- **v2** (`1673ad5`, D286): Fable "ready for the pre-registration", with three things to do first;
  Astra "revise" (run 20261016-001758, D287).
- **v2.1** (`b8ed3ae`, D287): Fable "ready for the pre-registration"; Astra "revise", for three narrow
  corrections and no change to the hypotheses, sample sizes or tests (run 20261016-010052, D288). v2.2
  makes them, with Fable's small items. §11 lists the changes in each version.
- **The owner's go:** Track B next, on 2026-10-15 ("let's go to the biology track first"; D285).
- **The label** 03mc ("03m, confirmatory") is proposed here. ROADMAP's Track B leaves the label to the
  pre-registration.

## 0. Why, and what is already known

Experiments 03 and 03r found that random, unevolved brains wired as N2 show more history dependence
(P4) than brains wired as five kinds of shuffled graph. 03 was borderline; 03r replicated it (D080).
**03m** (exploratory, D113-D116) looked for what drives it. Its corrected summary
(`experiments/03m-p4-mechanism/RESULTS.md`, Corrections) left five leads. Both reviewers recomputed
every figure below from 03m's committed files (D286):
1. **Gap junctions:** with gap junctions off in every brain, N2's P4 rises by +0.0144, while each of
   80 null graphs rises by +0.051 to +0.143. N2's lead over the shuffles narrows.
2. **RIA and AIY:**
   - Deleting the RIA pair cuts N2's response (P4's denominator) by 61.7% and its numerator by 61.5%;
     P4 moves by +0.005.
   - Deleting the AIY pair cuts them by 52.8% and 53.1%; P4 moves by −0.004.
   - These are the two largest response cuts among N2's 95 bilateral pairs. The third is ASE, at 31.1%.
3. **Weight placement:** 64 permutations of N2's weight magnitudes over its own edges were measured
   under two genome designs.
   - Every permutation's response is below the pooled null maximum.
   - In each design, 59 of the 64 permutations have P4 below N2's.
   - The permutations' median keeps 60% (independent design) and 58% (paired) of N2's excess P4
     over the pooled null median.
4. **Slower relaxation:** after the ramp, N2 keeps a larger share of the rising-minus-falling
   difference than all 80 null graphs at every recorded tick from 5 to 50. At tick 30, N2 keeps
   0.470; the nearest null graphs keep 0.427 (SH-10007), 0.415 (SH-recip-50002) and 0.397
   (SH-recip-50014). At tick 300, two graphs keep more than N2: SH-10007 and SH-mirror-40014.
5. **Saturation:** N2's turn read-out neurons work at a lower tanh slope than all 80 null graphs.

Both reviewers of 03m's results proposed a confirmatory follow-up
(`docs/reviews/20260929-061029-03m-results/`). This design takes up their proposals, with three
replacements, each stated where it applies:
- **Tick 300 is secondary, not the endpoint** (Fable proposed it): it is a likely failure, §4 Q-D.
- **The specificity reference is all 95 pairs plus degree-matched controls,** rather than random
  degree-matched pairs alone: §4 Q-B.
- **"Thresholds from matched manipulated nulls"** (Fable) become Q-A's paired change, ranked against
  each null graph's own change under the same manipulation.

Neither reviewer wanted "no deletion removes P4" registered, nor a claim of stable states; neither is.

## 1. Disclosures

- **Everything 03, 03r and 03m measured is known.** Every hypothesis here comes from 03m's data, and
  so do the choices that matter:
  - Q-D's endpoint tick;
  - Q-B's margins;
  - which questions are primary.

  What makes the study confirmatory is only the new data: fresh genomes for every graph (N2's
  included), fresh null graphs and fresh permutations, all registered and pushed before any is drawn.
- **Measured for this design, on old inputs only (03's genomes, 03m's panel):**
  - the history probe's GPU time (D285);
  - the two-row probe's deviation from one-row references (§5): on N2, the 80 panel graphs and three
    N2 conditions (`equivalence.json`), then on the pre-run check set with every declared tolerance
    (`equivalence-check.json`). Both ran on uncommitted code over a committed HEAD (6e948d7 and
    1673ad5; `dirty: true` in their stamps). The only later change to the first run's script was
    `allow_pickle=False` (D286). The formal pre-run check reruns at the bound commit (Fable);
  - the probability of passing (§6, `power.py`, `power.json`), simulated from 03m's committed
    summaries and its local per-genome arrays (their hashes recorded).
- **Reviewers' own runs:** in the review of v2, Astra ran its own checks on this machine, on old inputs
  (84 s of GPU, counted in its session, not in this study's accounting).

## 2. What stays exactly as in 03

These stay as in 03, so that the effect tested is the one 03, 03r and 03m measured:
- **The probe:**
  - 03's stimulus bank (`experiments/03-generation0/pilot.json`);
  - the ramps: 0.25 and 1.75 times the final food level, 100 ticks of hold, a 10-tick ramp;
  - the raw turn read-out;
  - the interface M0.
- **P4:** the mean |rising − falling| at the ramp's end over the mean |steady contrast|, averaged in
  float64.
- **Exclusion:** a denominator below 10⁻⁴, or not finite, makes a P4 invalid.
- **Genomes:** 2 048 random genomes per graph, drawn as 03 drew them (`Genome.random`; seed from the
  graph's name and the salt).
- **The null ensembles:** 03's five samplers (SH, SH-route, SH-class, SH-mirror, SH-recip), with their
  validation rules: plateau, acceptance floor, Jaccard ceiling, disclosed substitution.

## 3. What is new: seeds and freshness

| | 03 | 03r | 03m | **03mc** |
|---|---|---|---|---|
| genome salt | none | "03r:" | none (03's genomes) | **"03mc:"** |
| ensemble seeds | 10 000 + i, ... | 1 010 000 + i, ... | 03's | **2 010 000 + i, ... 2 050 000 + i** |
| plateau chains | 90 000-90 003 | 1 090 000-1 090 003 | | **2 090 000-2 090 003** |
| graphs per ensemble | 128 | 128 (256 SH-route) | 16 (decay) | **128** |
| permutation seeds | 1-3 | 4-6, then `_gseed(name) + 2` | 100-163 | **1 000-1 255** |
| Q-B's extra N2 genome batches | | | | **31 batches: names "N2#1" ... "N2#31", salt "03mc:"** |

**The freshness audit** runs in the build, before anything is measured. Any failure stops the build;
it is reported, and resolved only by a dated amendment. The audit:
- computes every derived genome seed this study will use: N2, the 640 graphs, the 31 batches, and the
  substitutes if any;
- requires them to be distinct from each other and from every derived seed of 03, 03r and 03m (all
  their graph names under their salts). `genome_seed` keeps 31 bits, so a new salt alone does not
  guarantee distinct seeds (Astra);
- requires every permutation seed to be distinct from 03's, 03r's (including every
  `_gseed(name) + 2`), 03m's, and the smoke seeds;
- requires every new graph's array content to be distinct from every other new graph's, and from
  every graph in 03's and 03r's committed content manifests.

Also:
- **Substitutions:** a substitution after a sampler failure adds 100 000, as in 03.
- **Graph files** stay local, as in 03 (they carry permuted anatomical weights). The record and the
  manifests, with raw and content hashes, are committed.
- **Smoke runs** use the salt "03mc-smoke:", graph seeds 2 900 000 + i and permutation seeds from
  9 000, and never touch a formal input (E3b-1's lesson).

## 4. The questions

Four primary questions (Q-A to Q-D) form one family under Holm at a familywise α = 0.05, one-sided in
each predicted direction (§6). Every outcome has fixed wording; the cases that cut across questions
(Holm stopping, a failed replication) are in §6.

### Q-A. Does N2's lead depend on gap junctions? (primary)

- **Measure:** for every graph, ΔP4 = P4 with every gap junction's weight set to zero (`g = 0`, as in
  03m), minus intact P4. Both are measured on the same 2 048 genomes.
  - N2 is measured exactly as each null graph is, on its first batch of 2 048 genomes. The rank test's
    exchangeability needs the same precision.
  - A graph counts only if both its P4s are valid; so does N2.
- **Prediction:** N2's ΔP4 is unusually small relative to every ensemble's.
- **Test:**
  - for each ensemble, r = the number of counted graphs with ΔP4 ≤ N2's, and the rank p is
    (r + 1)/(n + 1);
  - the question's p is the maximum over the five ensembles (intersection-union, as 03r's primary).
- **Outcome wording:**
  - pass: "N2's P4 changed unusually little when gap junctions were switched off, relative to each
    ensemble: [r of n] graphs per ensemble changed as little or less";
  - and, only if the intact P4 replicates here (§4, replication): "N2's P4 lead over each ensemble
    narrows without gap junctions, by [the change in the median gap, per ensemble]";
  - fail: "the registered criterion was not met: [r of n] graphs per ensemble changed as little as N2
    or less".
- **Secondary, with 03r's single-signal verdicts:** N2's gaps-off P4 against each ensemble's gaps-off
  P4. In 03m, 5 of 80 null graphs matched or exceeded it.
- **What it cannot show:**
  - A small change does not say why. N2 may start near a level the shuffles rise towards, and 03m's
    nulls with a higher intact P4 rose less (a slope of −0.26 over the 80 graphs). The levels are
    reported beside the changes.
  - It does not say which gap junctions matter.

### Q-B. RIA and AIY: a response cut with P4 kept (primary)

- **Genomes:** 32 batches of 2 048 genomes for N2 (65 536 in all):
  - batch 0 is N2's genomes for every other question;
  - batches 1-31 come from the names "N2#1" ... "N2#31".
  - The uncertainty in the change of P4 under a deletion was underestimated in v1. At 2 048 genomes,
    03m's AIY change has a paired bootstrap SE of 0.012 (Astra).
- **Conditions, in every batch:** intact; the RIA pair deleted; the AIY pair deleted; both pairs. The
  degree-matched controls come from batch 0's 95-pair screen (below).
  - A deletion is 03m's: every edge and gap junction touching the neuron, and its bias.
  - Each condition runs as its own probe, in the registered composition.
  - An empty deletion in batch 0 must reproduce batch 0's intact terms exactly; otherwise the run
    stops.
- **Estimates:** ratios of means pooled over all 65 536 genomes:
  - the response cut, 1 − den_deleted / den_intact;
  - the numerator's cut;
  - ΔP4 = P4_deleted − P4_intact.
- **The bootstrap:** 10 000 resamples of the 65 536 genome indices, with the same indices for every
  condition (paired), from `numpy.random.default_rng(20261016)`.
  - Each estimate is recomputed per resample; its SE is the SD over resamples.
  - A resample with an invalid denominator is dropped and counted. More than 1% dropped withholds
    Q-B.
- **The tests:** normal-theory tests with the bootstrap SE (z = estimate distance over SE, one-sided
  p = Φ(−z)):
  - cut: p_cut = Φ(−(cut − 0.40)/SE_cut);
  - equivalence: p_eq = max(Φ(−(ΔP4 + 0.02)/SE_Δ), Φ(−(0.02 − ΔP4)/SE_Δ)) (two one-sided tests);
  - the question's p is the largest of p_cut and p_eq, for RIA and for AIY: four values,
    intersection-union. Holm then applies to that p (§6); no part is passed at a fixed 5% (Astra).
- **Margins:**
  - **40%** sits between the third-largest pair cut in 03m (ASE, 31%) and AIY's 53%, so it also
    separates RIA and AIY from every other pair.
  - **0.02** in P4 is about a fifth of N2's lead over the pooled null median (0.93 against 0.82),
    and the lead is what the study is about. A deletion that moved P4 by less than that would leave
    most of the lead in place.
  - With the cut above 40%, |ΔP4| < 0.02 bounds the numerator's cut to within about one percentage
    point of the response's (Fable). The claim is "approximately in proportion", not exact
    proportionality (Astra).
  - The margin is not specific to RIA and AIY: in 03m, 94 of 95 pair deletions moved P4 by less than
    0.02. The claim is the conjunction.
- **Outcome wording:**
  - pass: "Deleting the RIA pair, or the AIY pair, cuts N2's response by more than 40% while P4 stays
    within 0.02: the history signal falls approximately in proportion";
  - fail: "the registered criterion was not met:" then each failed part, for example "AIY's change
    in P4 was not shown to be within 0.02 ([estimate, interval])".
- **Degree-matched controls (secondary, a test outside the family):**
  - For each of RIA and AIY: the four bilateral pairs nearest in total degree (chemical in + out +
    gap, summed over both neurons, from the connectome). The turn read-out pairs, RIA and AIY are
    excluded; ties are broken alphabetically.
  - This gives AIB, AVJ, RIM and AVH for RIA (degree 135; theirs 141, 119, 116, 114), and AWB, RIF,
    RIP and RIV for AIY (degree 58; theirs 59, 59, 59, 57). The code derives the list and asserts it.
    The tie-break decides RIA's fourth control: PVP also has 114 (Fable).
  - **Why total degree:** it is a coarse structural match that needs no choice of direction or synapse
    type. Matching on chemical in-degree alone would follow RIA's and AIY's place on the
    sensory-to-steering route more closely; the conclusions are about these named controls, not about
    every pair of their degree (Fable, Astra).
  - **The controls are measured in the 95-pair screen on batch 0,** so they cost no extra probes. In
    03m their cuts are all below ASE's 31%, against RIA's 62% and AIY's 53%, so batch 0's precision is
    enough (Fable).
  - **The claim, for each target:** RIA's cut exceeds every one of its four controls' cuts, and the
    same for AIY.
    - Each comparison is a paired difference in cut, divided by its bootstrap SE (batch 0's 2 048
      genomes, 10 000 resamples, the same seed as Q-B): p = Φ(−difference/SE).
    - The claim's p is the largest of the four (intersection-union), at 0.05, outside the family
      (Fable, Astra).
- **Secondary, descriptive:**
  - all 95 pair deletions on batch 0, with RIA's and AIY's ranks by response cut;
  - the double deletion's cuts and ΔP4;
  - the numerator's and response's cuts side by side, with paired intervals (Astra).
- **The same deletions in null graphs (secondary, descriptive):** RIA, AIY and both, deleted in the
  first 32 graphs of each ensemble.
  - Reported: each graph's response cut, and N2's rank among them.
  - The neurons exist by name in every null graph, with shuffled wiring. This asks whether the cut
    comes from N2's wiring around them, or from what each sampler keeps (some degree structure).
- **The factorial (secondary, descriptive):** RIA, AIY and both, deleted in N2 under the first 32 of
  Q-C's permutations, on batch 0.
  - The contrast: N2's cut minus the permutations' mean cut, with a bootstrap interval over
    permutations (Astra).
  - It asks whether the cut depends on where the weights sit. It is descriptive, so no claim that
    "weight placement acts through RIA and AIY" can come from it.
- **Not registered:** whether any deletion removes the elevated P4 (both reviewers).

### Q-C. Is N2's response unusually high against its own weight placements? (primary)

- **Permutations:** 256 fresh permutations of N2's weight magnitudes over its own edges (chemical and
  gap magnitudes each within their own type), seeds 1 000-1 255. The design is paired: batch 0's
  genome draws, with only the magnitudes permuted; signs, biases and time constants are unchanged.
- **Prediction:** N2's response is unusually high relative to the permutations.
- **Test:** r = the number of valid permutations with a response ≥ N2's, and the rank p is
  (r + 1)/(n + 1), with n the number of valid permutations (Astra).
- **Outcome wording:**
  - pass: "N2's response is unusually high relative to permutations of its weight magnitudes: [r of n]
    permutations reached it";
  - fail: "the registered criterion was not met: [r of n] permutations reached N2's response".
  - A pass does not show that the placement accounts for the whole response.
- **Secondary, a test outside the family:** N2's P4 rank among the same permutations, with the same
  rank p. 03m's 59 of 64 points to a rank p near 0.08, so this test has little power, and that is
  said in advance.
- **Secondary, descriptive:** the share of N2's excess P4 over the pooled fresh null median that the
  permutations' median keeps, with a bootstrap interval over permutations.

### Q-D. Does N2 keep more of its history difference at tick 30? (primary)

- **Measure:** after the ramp, the final input is held for 300 ticks, as in 03m. For each graph, the
  retained share at tick t is mean|rising − falling| at t over the same at tick 0: a ratio of means
  over genomes.
  - A graph counts only if its P4 is valid and its tick-0 mean is at least 10⁻⁴; the same holds for
    N2.
- **Endpoint: the retained share at tick 30.**
  - **Chosen with 03m's curves in view:** N2 was above all 80 null graphs at every tick from 5 to 50
    (§0). Among ticks 10-50, ticks 30 and 40 have nearly equal simulated pass probabilities (0.846 and
    0.848), tick 20 is slightly lower (0.831, about two Monte Carlo SEs below), and ticks 10 and 50 are
    lower still (`power.json`, "Q-D by tick"). v2 said tick 30 had the highest, which the committed
    table does not show, and v2.1 called ticks 20-40 tied, which it does not show either (both
    reviewers). Tick 30 is also three
    ramp-lengths after the ramp ends.
  - **Not tick 300:** at tick 300 the slowly relaxing graphs make the test a likely failure.
- **Prediction:** N2's retained share at tick 30 is unusually large relative to every ensemble's.
- **Test:** rank p and intersection-union, as in Q-A, counting graphs with a share ≥ N2's.
- **Outcome wording:**
  - pass: "N2 retained an unusually large share of its history difference 30 ticks after the ramp,
    relative to each ensemble: [r of n] graphs per ensemble retained as much or more";
  - fail: "the registered criterion was not met: [r of n] graphs per ensemble retained as much as N2
    or more".
  - A pass is about one time point. It does not separate a slower relaxation from a plateau or a
    differently shaped transient, and it does not mean that every null graph or every N2 genome keeps
    less (Astra).
- **Secondary, tests outside the family:** the same rank test at ticks 10, 50, 100 and 300. At tick
  300 a failure is expected.
- **Secondary, descriptive:**
  - the full curve;
  - among genomes starting above 10⁻³, the share with more than 10% of their difference left at tick
    300;
  - the absolute count of genomes settled with separation left (Fable). Settling is 03m's rule: the
    largest range of any neuron's state, over each of the last 10 ticks and both histories, below
    10⁻⁴.
- **Not claimed:** stable states (Astra). A ten-tick test cannot show lasting stability.

### Q-E. Does P4's distinctiveness survive a read-out before the tanh? (secondary, with a verdict)

- **Measure:** P4 computed on the turn read-out neurons' state before the tanh: the mean of v over the
  turn-plus neurons minus the mean over the turn-minus neurons, from the same run as the standard P4.
  - The same floor applies: a pre-tanh denominator below 10⁻⁴ makes it invalid, with counts reported.
  - The tanh stays in the recurrent dynamics (`brain.py`, `torch.tanh(v)` before the chemical term).
    Only the final observation changes, so this is robustness to the read-out map, not a test of
    saturation in the network (Astra).
- **Verdict:** 03r's single-signal rule: the rank p over five ensembles at α = 0.05, with the
  effect-margin gate.
- **Outcome wording:**
  - "P4's distinctiveness persists on the pre-tanh read-out";
  - or "pre-tanh distinctiveness was not established", with the failing gates named;
  - or 03r's "withheld" wording.
- **Also reported:** the mean tanh slope of the turn read-out neurons, N2 against each ensemble.

### The third replication of P4 (secondary, with a verdict)

N2's intact P4 against the five fresh ensembles, by 03r's single-signal rule, reported first and
alongside 03's and 03r's. If it is not "distinctive relative to every ensemble", Q-A's "lead narrows"
sentence is not used, and RESULTS says first that the lead itself did not replicate here.

## 5. Procedure and composition

- **The two-row probe** (`wormwars/exp03/twin.py`):
  - the rising and falling histories run as two rows of each strain, sharing its matrices; 03 ran
    them one after the other, with one row;
  - the brain step is unchanged, and the rows do not interact (a test checks row 0 against a one-row
    run, and another checks that swapping the starts flips every sign);
  - the step is bound by reading the dense matrices, so the time halves: 6.6 s against 13.0 s for
    2 048 genomes (D285).
- **Deviation from one-row references, measured on old inputs** (`scripts/p4mc_equivalence.py`):
  - **The first run** (`equivalence.json`, 0.52 GPU-hours): 03's genomes for N2 and 03m's 80 panel
    graphs, plus N2 with gap junctions off, with the RIA pair deleted, and under 03m's paired
    permutation 100. It compared per-genome outputs and P4's terms.
  - **The second run** (`equivalence-check.json`, 0.24 GPU-hours, after the review of v2): the pre-run
    check set, which is N2, the first 4 graphs of each ensemble, SH-mirror-40015 (the worst settling
    deviation), SH-10007 and SH-recip-50015, plus the three conditions. It adds what the first run
    lacked (both reviewers): each graph's aggregate retained share at tick 30 against 03m's
    `decay.json`; the pre-tanh terms against a one-row sequential reference; and the settling labels,
    genome by genome. Every comparison is judged against the declared tolerances below; all passed.

  The worst cases, over both runs:

  | output | worst relative deviation |
  |---|---|
  | P4's numerator and denominator, against 03's committed supplement | 2.0 × 10⁻⁷ |
  | per genome: the ramp-end difference, the steady contrast | 7.2 × 10⁻⁶, 4.3 × 10⁻⁶ |
  | per genome: the difference at tick 30; the whole curve to tick 300 | 2.2 × 10⁻⁵; 1.3 × 10⁻⁴ |
  | per genome: tanh slopes; the holds' settling range | 1.1 × 10⁻⁶; 2.7 × 10⁻⁵ |
  | per genome, the three N2 conditions: ramp end, steady contrast; their P4 terms | 7.6 × 10⁻⁷; 4.6 × 10⁻⁸ |
  | per genome: the follow-up's settling range (near zero, so relative deviations are large) | 0.33 (SH-mirror-40015) |
  | each graph's retained share at tick 30 (second run) | 4.1 × 10⁻⁷ |
  | pre-tanh: per genome, ramp end and steady contrast; the terms (second run) | 3.9 × 10⁻⁶, 4.8 × 10⁻⁶; 2.1 × 10⁻⁷ |
  | settling labels changed: settled, separation remaining, both (second run, 24 graphs) | 0, 0, 0 |

  - Per-genome figures are the largest absolute difference over the largest |reference value|.
  - **Settling labels:** first checked by an uncounted 1.6-minute run on four graphs (D286), which named
    SH-recip-50015 as the worst range deviation. That was wrong: it is SH-mirror-40015 (Astra). The
    second run checks all 24 graphs of the check set, SH-mirror-40015 included. No genome changed any
    label, and the counts of genomes settled with separation left matched 03m's: N2 26, SH-10007 171,
    SH-mirror-40003 37.
- **Declared tolerances for the formal pre-run check:**
  These are declared in the script (`TOL`, `LABELS`):
  - **Aggregates:** within a relative 10⁻⁵. This covers P4's terms against 03's committed supplement
    (49 times the worst measured), each graph's retained share at tick 30 against 03m's (25 times), and
    the pre-tanh terms against the one-row reference (47 times).
  - **Per genome:** within 10⁻⁴ for the ramp end, the steady contrast, tick 30, the slopes and the
    pre-tanh terms (about 4.5 times the worst measured, 4.47 at tick 30); within 3 × 10⁻⁴ for the holds' settling
    range (11 times); within 2 × 10⁻³ for the curve (15 times).
  - **Settling labels:** at most 2 of 2 048 genomes of any graph may change any label, each genome
    counted once whichever labels change (v2.2: v2.1's code counted each label separately, so four
    genomes could pass; Astra). More would indicate a fault, not rounding; one genome crossing the 10⁻⁴
    threshold should not halt the study over a secondary count (Fable).
  - **The check set:** as in the second run, `--set check`. SH-recip-50015 is in it because design v2
    misnamed it as the worst deviation; it is kept, not chosen for a reason of its own (Fable).
  - **The references are pinned:** the check refuses local reference arrays whose sha256 differs from
    those `power.json` recorded, and records all four hashes (Fable).
  - **The formal pre-run check writes `prerun-check.json`** (`--out`), and a record is never
    overwritten, so the design-time records stay as quoted here (Fable).
  - The committed `equivalence-check.json` predates two of these changes: it has no `any` count and no
    reference hashes. Every label count in it is 0, so the union is 0 too.
  - **If it fails, nothing formal runs.** The failure is reported, and a dated amendment decides,
    reviewed by both. The measured deviations are reported whatever they are.
- **Runs per graph:**
  - one long run of 100 ticks of hold, the 10-tick ramp and 300 ticks of the final input; P4, the
    pre-tanh terms, the curve, settling and saturation all come from it;
  - one standard-length run with gap junctions off.
- **Composition:** 2 048 strains × 2 rows per batch, in every formal measurement. The first graphs of the
  equivalence run took about 100 s each, against 22 s later; they coincided with CPU-heavy tests on the
  same machine, which can slow the GPU's kernel launches (not isolated). Nothing else runs on the machine
  during the formal run. Rerunning is
  expected to agree within the declared tolerances; no exact repeat is claimed (no `replay_mode`;
  Astra).
- **Order** (the primaries first; within them, the cheapest first):
  1. the pre-run check;
  2. N2's batch 0: long run and gaps off;
  3. Q-C's 256 permutations;
  4. Q-B's 32 batches;
  5. the ensembles, interleaved (SH-route, SH-class, SH-mirror, SH-recip, SH, then the next index),
     so a stop leaves balanced ensembles;
  6. the secondaries: the 95 pair deletions on batch 0, the factorial, the null-graph deletions.
- **Writes:**
  - each unit is written as it completes, with its provenance (the clean pushed commit, the GPU, the
    environment, the connectome's raw hash);
  - per-genome arrays stay local, with their hashes committed;
  - every input is pinned: configuration, stimulus bank, interface, measurement code. A resume refuses
    a changed input.

## 6. Statistics, multiplicity and the probability of passing

- **One family, Holm at α = 0.05: Q-A, Q-B, Q-C, Q-D** (both reviewers kept Holm).
  - With 128 graphs per ensemble, the thresholds 0.0125, 0.0167, 0.025 and 0.05 need r = 0, r ≤ 1,
    r ≤ 2 and r ≤ 5 in the worst ensemble.
  - A question that is withheld or not measured enters with p = 1 (as `report.py` does for
    incomplete signals), so the family keeps four members.
- **Reported for every question:** the raw p and the Holm-adjusted p, every component gate, the
  estimates with intervals, and the planned, attempted, completed, invalid and valid counts.
- **Cross-question wording:**
  - **Holm stops:** a question whose own p met 0.05 but not its Holm threshold reads "met α = 0.05
    alone, but not its Holm threshold: not confirmed under the registered familywise rule".
  - **A failed replication:** see §4.
- **The probability of passing** (`power.py`, `power.json`):
  - **What it is:** model-based predictive pass probabilities. They are predictions under the models
    below, not established operating characteristics (Astra). The whole Holm procedure is simulated.
    - **N2's quantities are drawn jointly** (v2.1, Astra). One paired bootstrap over 03m's 2 048 N2
      genomes, which are the same genomes in every 03m array, gives their covariance: Q-A's change,
      Q-D's share, RIA's and AIY's cuts and changes in P4, and N2's response.
      - The correlations reach 0.45 between RIA's and AIY's changes in P4, and 0.38 between Q-A's change
        and RIA's.
      - Batch 0 is shared between the questions; Q-B pools it with 31 more batches.
    - **Q-A:** the null changes come from a regression of change on intact P4 over 03m's 80 graphs,
      extrapolated to 03's and 03r's intact P4s (Fable). The coefficients and the residual SD are drawn
      from their posterior; the slope is −0.26, SE 0.03.
    - **Q-D:** per ensemble, a normal on log retained share, its mean and SD drawn from the
      reference-prior posterior (p(μ, σ²) ∝ 1/σ²).
    - **Q-C** is now modelled, not assumed: the permutations' log responses come from a normal fitted to
      03m's 64 paired permutations (mean −3.72, SD 0.28), against N2's drawn response (log −2.05).
    - **A sensitivity** replaces the graph-level normals with Student t on 5 degrees of freedom at the
      same SD (Astra: the tails matter for an extreme-rank test).
  - **Results, from 20 000 simulated studies with Q-B at 65 536 genomes:**

    | | normal, alone at 0.05 | normal, under Holm | t₅, under Holm |
    |---|---|---|---|
    | Q-A | 0.98 | 0.96 | 0.92 |
    | Q-B | 0.77 | 0.76 | 0.76 |
    | Q-C | 1.00 | 1.00 | 1.00 |
    | Q-D | 0.85 | 0.78 | 0.74 |
    | all four | | 0.63 | 0.62 |

  - **Q-B's limit** is the uncertainty in 03m's own estimate of AIY's change in P4 (−0.004 ± 0.012),
    not the fresh sample. Under Holm, Q-B passes 0.60 of the time at 16 384 genomes (v2's
    independent model gave 0.01 at 2 048: `power.json` at 1673ad5).
  - **Q-D's limit** is the tails of five ensembles estimated from 16 graphs each.
  - The v1 sketch's 0.99 for Q-D was wrong: it ignored the fit's uncertainty and gave Q-D Holm's
    most lenient slot (both reviewers).
  - A fixed sequence (C, A, D, B, each at 0.05 after the previous passes) gives Q-D 0.83 and Q-B
    0.64. Holm is kept: it does not let one failure block the rest.
  - **By tick** (Q-D alone, 5 000 simulated studies each, SE about 0.005): 0.680 at tick 10, 0.831 at
    20, 0.846 at 30, 0.848 at 40, 0.780 at 50. Ticks 30 and 40 are nearly tied; tick 20 is slightly
    lower.
- **Completeness:**
  - at least 120 counted graphs per ensemble for each of Q-A, Q-D, Q-E and the replication, judged
    separately; otherwise that question is withheld, with its counts;
  - Q-B needs its 32 batches, with at most 1% of bootstrap resamples dropped;
  - Q-C needs at least 240 valid permutations.
- **Secondary tests** carry their own α = 0.05 and sit outside any familywise guarantee.
- **Intervals** (Astra): every descriptive interval is a 95% percentile bootstrap interval with 10 000
  resamples. The resampling unit and seed depend on the quantity:
  - N2's quantities: genomes, paired across conditions, seed 20261016;
  - quantities over permutations (the factorial contrast, Q-C's kept share of the excess P4):
    permutations, seed 20261017;
  - the null-graph deletions: graphs, seed 20261018.
- **Q-B's SEs are treated as known** in its normal-theory tests (Fable). Q-B's 90% percentile
  intervals are reported beside the tests as a check, not as a test.

## 7. Compute and cap

| Part | Units | GPU-hours |
|---|---|---|
| pre-run check (old inputs; `scripts/p4mc_equivalence.py --set check`) | 24 graphs + 3 conditions | 0.25 |
| N2 batch 0: long run, gaps off | 2 runs | 0.01 |
| Q-C: 256 permutations | 256 probes | 0.47 |
| Q-B: 32 batches × 4 conditions | 128 probes | 0.23 |
| ensembles: 640 graphs, long run + gaps off | 640 × 30 s | 5.35 |
| secondary: 95 pairs, factorial 32 × 3, null deletions 160 × 3 | 671 probes | 1.23 |
| graph build (CPU) | 640 graphs + plateau chains | 0.4 |
| **total** | | **about 7.9** |

- **The cap is 10 hours**, registered in code. It counts every formal command's synchronised wall
  time in the accounting (`CapClock`; wall time, not GPU kernel time), across all attempts: failed
  ones, restarts and the build.
- **It is checked before every unit:** a graph's build, a graph's measurement, a batch's condition, a
  permutation. A unit begun under the cap runs to completion, so the overrun is at most one unit: about
  30 s for a measurement, under a minute for a graph's build (Astra). The report runs after the cap's
  last check and simulates nothing.
- **A stop is administrative, not an observation:** what is incomplete is withheld and reported. The
  four primaries keep p = 1 for anything unmeasured.
- **No continuation depends on an outcome:** the order is fixed, and nothing is added or rerun
  because of a result.
- **The owner is told before the formal run starts.**
- The measurements for this design (timing, `equivalence.json`, `equivalence-check.json`) are counted
  separately and reported.

## 8. What this cannot establish

- **A mechanism,** beyond "this change moves these numbers". The brains are random and unevolved,
  the read-out is a hand-chosen interface, and deletions locate dependencies, not stores.
- **Anything about behaviour,** about evolved brains, or about the worm.
- **Independence from 03, 03r and 03m:** the same connectome, the same samplers, the same probe. A
  probe-specific effect or a systematic code error would recur here too (as 03r said of itself).
- **That the hypotheses were chosen in advance:** they were chosen after 03m's data, and only the new
  draws make the tests confirmatory.

## 9. Code and tests (rule 9)

- **`wormwars/exp03/twin.py`, the two-row probe:**
  - against `measures.history` on the CPU at a relative 10⁻⁵ (in the test, 6 genomes);
  - the long follow-up keeps the ramp end and the steady contrast;
  - the pre-tanh read-out;
  - row isolation and the row swap;
  - the pre-tanh terms against a one-row sequential reference (v2.1, Fable, Astra);
  - sabotage checks: a reversed steady contrast and a shared input row were caught (D286), and so was
    swapping the turn-plus and turn-minus neurons in the pre-tanh read-out (D287).
- **`wormwars/exp03/mc.py`, the statistics** (written test-first after v2's review; 13 tests):
  - the rank p in both directions, with invalid values dropped;
  - intersection-union with a missing ensemble;
  - Holm with stopping and a missing question;
  - Q-B's paired bootstrap, including a sabotage check of the pairing, and its tests;
  - the matched controls, on a toy graph and on the connectome;
  - the freshness audit with planted collisions, including permutation seeds compared as generator
    seeds (2 × seed + type, as `brain._apply_magnitude_mode` uses them), and the content check.
- **`scripts/p4mc_equivalence.py`:** the pre-run check, with its tolerances in code.
- **Still to write, test-first, for the pre-registration's code review:**
  - the build command around the audit (an `03mc` instance of 03's builder is added to
    `scripts/exp03.py`);
  - the runner;
  - the cap and unit boundaries;
  - the stop and resume behaviour;
  - the report's wording for every case.

## 10. Questions for the reviewers

None open. The pre-registration is reviewed next, with the runner's code.

Answered in v2's review (kept): the normal-theory tests with a paired bootstrap SE are acceptable at
65 536 genomes (both); total degree and four controls per target are acceptable, with conclusions
limited to the named controls (both).

## 11. Changes

### From v2.1 (review 20261016-010052, D288)

- **The settling gate** counts each genome once, whichever labels change, with Astra's counterexample as
  a regression test (Astra).
- **The tick comparison** is reported as it stands: ticks 30 and 40 are nearly tied, and tick 20 is
  slightly lower (both).
- **Margins:** "about 4.5 times" (4.47) for the per-genome tolerances (both).
- **The pre-run check** writes `prerun-check.json` and never overwrites a record; it pins its local
  references to `power.json`'s hashes; the reason SH-recip-50015 is in the set is stated (Fable).
- **`mc.py`:** a non-finite N2 gives p = 1; the full-sample bootstrap estimate is held to the
  denominator floor; the audit test plants a 03r secondary permutation seed (Fable).
- **A citation:** v2's 0.01 for Q-B at 2 048 genomes is in `power.json` at 1673ad5 (Fable).

### From v2 (review 20261016-001758, D287)

- **The equivalence check** (both): the second run adds each graph's aggregate tick-30 share, the
  pre-tanh terms against a one-row reference, and the settling labels genome by genome, on the pre-run
  check set. Every tolerance is declared in code and judged; all passed. The settling rule allows at
  most 2 label changes per graph (Fable). The worst settling graph was misnamed (SH-mirror-40015, not
  SH-recip-50015; Astra). The hold-range tolerance was raised to 3 × 10⁻⁴; v2 said "at least 4.5 times"
  where it was 3.8 (both).
- **A pre-tanh reference test,** with a sabotage check (both).
- **The power model** (Astra): N2's quantities are drawn jointly from one paired bootstrap; Q-A's
  regression has posterior draws; Q-C is modelled; there is a heavier-tailed sensitivity; the results
  are called model-based predictive probabilities. Q-D's tick comparison is now committed (both), and
  it does not single out tick 30, so the claim that it did is withdrawn.
- **Q-B's controls** (both): they come from batch 0's 95-pair screen (Fable; saves 0.47 GPU-hours); the
  claim is intersection-union, with a paired-difference test; the PVP tie is stated; total degree is
  explained.
- **Intervals and SEs** (both): methods, levels, resampling units and seeds are declared; Q-B's SE is
  treated as known, with a percentile interval beside it.
- **Wording:** Q-D's failure sentence is written out (Fable).
- **The cap:** the overrun bound covers builds, and the report simulates nothing (Astra).
- **Disclosures:** both equivalence runs were on uncommitted code (Fable); Astra's own 84 s of GPU in
  its review.

### From v1 (review 20261015-232952, D286)

- **Q-B's power** (Astra): 32 batches of 2 048 genomes; the bootstrap and tests specified exactly; no
  part passed at a fixed 5%. "Approximately in proportion" replaces "in proportion" (Astra). The 40%
  margin is explained as a specificity threshold, and the 0.02 margin by the lead (Fable, Astra).
- **The probability of passing** is now simulated for the whole Holm procedure, with Q-A's
  extrapolation and Q-D's fit uncertainty (both). The table in §6 replaces v1's sketch.
- **The equivalence check** was measured on old inputs before the tolerances were set, and covers
  per-genome outputs, the curve, settling, slopes, and the gaps-off, deletion and permutation
  conditions (both). It has a stop rule. Tests now cover row isolation and the row swap.
- **Wording:** every outcome now has a fixed sentence, including Holm stopping and a failed
  replication (Fable). Q-A, Q-C, Q-D and Q-E no longer claim more than their tests can show (Astra,
  Fable).
- **03m's figures:** "all 128 permutations" is corrected to 64 under two designs (both), and both
  percentages are given (60% and 58%).
- **Rules:**
  - validity rules for Q-A, Q-D and the pre-tanh P4;
  - Q-C's denominator is (r + 1)/(n + 1);
  - missing questions enter with p = 1;
  - counts reported at each stage.
- **The order:** the secondaries now run after every primary (both).
- **Freshness:** the audit covers derived genome seeds, 03r's hash-derived permutation seeds, and
  content within the new panel (Astra, Fable).
- **The cap:** what it counts, unit boundaries, administrative stops, and no outcome-dependent
  continuation (Astra).
- **The replacements of reviewers' proposals** are stated in §0 (Fable).
