# 03mc: a confirmatory test of 03m's leads on P4 (design v1)

**Status:** design v1, written 2026-10-15 for review by Astra 6 and Fable 5.1. Not a pre-registration.
Nothing in it has run. The owner chose Track B next on 2026-10-15 ("let's go to the biology track
first"; D285). The label 03mc ("03m, confirmatory") is proposed here; ROADMAP's Track B leaves the
label to the pre-registration.

## 0. Why, and what is already known

Experiments 03 and 03r found that random, unevolved brains wired as N2 show more history dependence
(P4) than brains wired as five kinds of shuffled graph. 03 was borderline; 03r replicated it (D080).
**03m** (exploratory, D113-D116) looked for what drives it. After review, its corrected summary
(`experiments/03m-p4-mechanism/RESULTS.md`, Corrections) left these leads:
1. **Gap junctions:** with gap junctions off in every brain, N2's P4 rises by +0.014; each of 80 null
   graphs rises by more (+0.051 to +0.143). N2's lead over the shuffles narrows.
2. **RIA and AIY:** deleting the RIA pair cuts N2's response (P4's denominator) by 62% and its
   numerator by 62%. Deleting the AIY pair cuts them by 53% and 53%. P4 moves by +0.005 and −0.004.
   These are the two largest response cuts among N2's 95 bilateral pairs. The next is ASE, at 31%.
3. **Weight placement:** under 64 permutations of N2's weight magnitudes over its own edges, every
   response falls to the null range. P4 falls too: 59 of 64 permutations are below N2.
4. **Slower relaxation:** after the ramp, N2 keeps a larger share of the rising-minus-falling
   difference than all 80 null graphs at every recorded tick from 5 to 50. At tick 300, 2 of the 80
   keep more.
5. **Saturation:** N2's turn read-out neurons work at a lower tanh slope than all 80 null graphs. Part
   of P4 may therefore come from the read-out's nonlinearity.

Both reviewers of 03m's results proposed a confirmatory follow-up
(`docs/reviews/20260929-061029-03m-results/`):
- **Astra** proposed two narrow questions:
  - RIA and AIY, with matched controls, an equivalence margin for P4, and numerator and denominator
    analysed jointly;
  - retained separation, with a registered endpoint and graph-level inference.
- **Fable** proposed five:
  - gap junctions off, ranked against each ensemble with gap junctions off;
  - RIA and AIY: a response cut of at least 40%, with P4 within 0.02; degree-matched controls; the
    same pairs in null graphs; the double deletion;
  - N2's rank among at least 256 fresh permutations;
  - per-ensemble ranks at 300 ticks, with at least 64 graphs each;
  - P4 on the read-out's state before the tanh.
- **Not registered:** neither wants "no deletion removes P4" registered (Fable: "better described than
  tested"), or a claim of stable states without a stronger protocol (Astra).

This design takes up all of those suggestions.

## 1. Disclosures

- **Everything 03, 03r and 03m measured is known.** Every hypothesis here comes from 03m's data, and
  so do the choices that matter: the endpoint tick in Q-D, the margins in Q-B, and which questions are
  primary. What makes the study confirmatory is new data only: fresh genomes for every graph (N2's
  included), fresh null graphs, and fresh permutations, all registered and pushed before any is drawn.
- **Measured for this design:** the history probe's GPU time, on N2 with 03's genomes. It is 13.0 s
  for 2 048 genomes with one row per strain, and 6.6 s with the rising and falling histories as two
  rows of one strain (§5). No fresh genome, graph or permutation has been drawn.

## 2. What stays exactly as in 03

These stay as in 03, so that the effect tested is the one 03, 03r and 03m measured:
- **The probe:**
  - 03's stimulus bank (`experiments/03-generation0/pilot.json`);
  - the rising and falling ramps (0.25 and 1.75 times the final food level, 100 ticks of hold, a
    10-tick ramp);
  - the raw turn read-out;
  - the interface M0.
- **P4:** the mean |rising − falling| at the ramp's end over the mean |steady contrast|, averaged in
  float64.
- **Exclusion:** a denominator below 10⁻⁴, or not finite, makes the measurement invalid.
- **Genomes:** 2 048 random genomes per graph, drawn as 03 drew them (`Genome.random`, seed from the
  graph's name).
- **The null ensembles:** 03's five samplers (SH, SH-route, SH-class, SH-mirror, SH-recip), with
  their validation rules (plateau, acceptance floor, Jaccard ceiling, disclosed substitution).

## 3. What is new

| | 03 | 03r | 03m | **03mc** |
|---|---|---|---|---|
| genome salt | none | "03r:" | none (03's genomes) | **"03mc:"** |
| ensemble seeds | 10 000 + i, ... | 1 010 000 + i, ... | 03's | **2 010 000 + i, 2 020 000 + i, ... 2 050 000 + i** |
| plateau chains | 90 000-90 003 | 1 090 000-1 090 003 | | **2 090 000-2 090 003** |
| graphs per ensemble | 128 | 128 (256 SH-route) | 16 (decay) | **128** |
| permutation seeds | 1-3 | 4-6, fresh secondary | 100-163 | **1 000-1 255** |

- **Substitutions:** a substitution after a sampler failure adds 100 000, as in 03, and stays clear of
  every earlier seed.
- **Graph files:** they stay local, as in 03 (they carry permuted anatomical weights). The record and
  the manifests, with raw and content hashes, are committed.
- **Collisions:** the build refuses any graph array identical to one of 03's, 03r's or 03m's, and any
  permutation seed already used.
- **Smoke runs** use a separate salt ("03mc-smoke:"), separate graph seeds (2 900 000 + i) and
  separate permutation seeds (9 000 +), and never touch a formal input (E3b-1's lesson).

## 4. The questions

Four primary questions (Q-A to Q-D) are tested under Holm at a familywise α = 0.05 (§6). Each has
wording fixed for both outcomes.

### Q-A. Does N2's lead depend on gap junctions? (primary)

- **Measure:** for every graph, ΔP4 = P4 with every gap junction's weight set to zero, minus intact P4.
  Both are measured on the same 2 048 genomes. 03m switched them off the same way (`g = 0`).
- **Prediction:** N2's ΔP4 is lower than the ΔP4 of every ensemble's graphs.
- **Test:**
  - for each ensemble, r = the number of valid graphs with ΔP4 ≤ N2's;
  - the rank p is (r + 1)/(n + 1);
  - the question's p is the maximum over the five ensembles (intersection-union, as 03r's primary).
- **Outcome wording:**
  - pass: "N2's P4 lead over each null ensemble depends partly on gap junctions: switching them off
    raises N2's P4 less than every ensemble's";
  - fail: "not confirmed: N2's change with gap junctions off is not lower than every ensemble's".
  - Each ensemble's own count and rank p are reported in both cases.
- **Secondary, with 03r's single-signal verdicts:** N2's P4 with gap junctions off against each
  ensemble's with gap junctions off. This says whether N2 is still distinctive without them; 03m
  suggests it may not be, since 5 of 80 null graphs matched or exceeded it.
- **What it cannot show:**
  - A smaller rise could reflect N2 starting nearer a ceiling: 03m's null P4s rise towards N2's level.
    Both levels are reported, so the reader can see that.
  - Switching gap junctions off removes a coupling; it does not show which gap junctions matter.

### Q-B. RIA and AIY: a response cut that leaves P4 in place (primary)

- **Deletions in N2:**
  - the RIA pair, the AIY pair, and both pairs together, each as 03m deleted them
    (`wormwars/deletion.py`: every edge and gap junction touching the neuron, and its bias);
  - also every other bilateral pair (93), as the reference set below.
- **Per deletion, with the same 2 048 genomes as intact N2:**
  - the response's fractional fall, 1 − den_deleted / den_intact;
  - the numerator's fractional fall;
  - ΔP4.
  - Intervals come from a paired bootstrap over genomes (10 000 resamples, seed fixed).
- **The registered claim, for RIA and for AIY separately (both must hold):**
  - **(i)** the response falls by more than 40% (Fable's figure; 03m: 62% and 53%), tested one-sided
    on the bootstrap;
  - **(ii)** |ΔP4| < 0.02, tested as an equivalence (two one-sided tests, each at 5%).
    - **Why 0.02:** it is about three times the SE of N2's P4 at 2 048 genomes (0.006) and a fifth of
      N2's lead over the pooled null median (0.93 against 0.82).
    - It is not specific to RIA and AIY: in 03m, 94 of 95 pair deletions changed P4 by less than 0.02.
      The claim is the conjunction, a large cut in both terms with their ratio kept, not the
      equivalence alone.
  - The question's p is the largest of the four component p-values (two pairs × two parts). Bootstrap
    p-values are floored at 1/10 001.
- **Outcome wording:**
  - pass: "deleting the RIA pair, or the AIY pair, cuts N2's response by more than 40%, and P4 stays
    within 0.02: the history signal falls in proportion";
  - fail: the parts that failed, by name.
- **Secondary, descriptive:**
  - **Specificity:** RIA's and AIY's rank among all 95 pair deletions by response cut (03m: first and
    second).
  - **Joint analysis** (Astra): the numerator's and the response's falls, with their paired interval;
    the double deletion's falls.
  - **The same deletions in null graphs** (Fable): RIA, AIY and both, deleted in the first 32 graphs
    of each ensemble. Each graph's fractional response fall is reported, and N2's rank among them. The
    neurons exist by name in every null graph; their wiring is shuffled. This asks whether the cut
    comes from N2's wiring around RIA and AIY, or from what the shuffles keep (each sampler keeps
    some degree structure).
  - **The factorial** (Astra): RIA, AIY and both, deleted in N2 under the first 32 of Q-C's
    permutations. Does the cut depend on where the weights sit?
- **Not registered:** whether any deletion removes the elevated P4 (both reviewers). The full
  95-pair screen is reported descriptively.

### Q-C. Does the weight placement set the response? (primary)

- **Permutations:** 256 fresh permutations of N2's weight magnitudes over its own edges, chemical and
  gap magnitudes each within their own type, seeds 1 000-1 255. The design is paired: N2's own
  2 048 genome draws, with only the magnitudes permuted (03m's paired design: signs, biases and time
  constants unchanged).
- **Prediction:** N2's response is above every permutation's (03m: all 128 permutations fell to the
  null range).
- **Test:**
  - r = the number of valid permutations with a response ≥ N2's;
  - p = (r + 1)/257.
- **Outcome wording:**
  - pass: "the placement of N2's weight magnitudes sets its large response: N2's response is above
    that of [n − r] of n permutations";
  - fail: the count.
- **Secondary, with a test but outside the primary family:** N2's P4 rank among the same permutations,
  with the same rank p. 03m's 59 of 64 predicts a rank p near 0.08, so this test has little power,
  and this is said in advance.
- **Secondary, descriptive:** the share of N2's excess P4 over the pooled null median that the
  permutations' median keeps (03m: about 60%), with a bootstrap interval over permutations.

### Q-D. Does N2's history fade more slowly? (primary)

- **Measure:** after the ramp, the final input is held for 300 ticks, as in 03m. For each graph, the
  retained share at tick t is mean|rising − falling| at t over the same at tick 0 (a ratio of means
  over genomes).
- **Primary endpoint: the retained share at tick 30.**
  - **Chosen with 03m's curves in view:** N2 was above all 80 null graphs at every tick from 5 to 50.
    Tick 30 is three ramp-lengths after the ramp ends.
  - **Tick 300 is not the endpoint:** there, 2 of 80 null graphs (in SH and SH-mirror) kept more than
    N2, and the slowly relaxing SH-mirror and SH-recip graphs make a tick-300 test likely to fail
    (§6).
- **Prediction:** N2's retained share at tick 30 is above every ensemble's.
- **Test:** the rank p and intersection-union, as in Q-A, counting graphs with a share ≥ N2's.
- **Outcome wording:**
  - pass: "N2's history difference fades more slowly than every ensemble's: 30 ticks after the ramp it
    keeps a larger share";
  - fail: the counts.
- **Secondary, with tests outside the primary family:** the same rank test at ticks 10, 50, 100 and
  300.
- **Secondary, descriptive:**
  - the full curve;
  - the share of genomes with more than 10% of their starting difference left at tick 300 (among
    those starting above 10⁻³);
  - the absolute count of genomes that have settled with separation left (Fable).
  - Settling uses 03m's rule: the full state's range over each of the last 10 ticks, below 10⁻⁴.
- **Not claimed:** stable states. A ten-tick settling test cannot show lasting stability (Astra).

### Q-E. Is P4 an artefact of the read-out's saturation? (secondary, with a verdict)

- **Measure:** P4 computed on the turn read-out neurons' state before the tanh: the mean of v over the
  turn-plus neurons minus the mean over the turn-minus neurons. It comes from the same run as the
  standard P4.
- **Verdict:** N2's pre-tanh P4 against each ensemble's, by 03r's single-signal rule (the rank p over
  five ensembles at α = 0.05, the effect-margin gate).
- **Outcome wording:**
  - "distinctive relative to every ensemble on the pre-tanh read-out: the read-out's saturation does
    not explain N2's elevated P4";
  - or "not distinctive on the pre-tanh read-out: N2's elevated P4 depends on the read-out's
    nonlinearity".
- **Also reported:** the mean tanh slope of the turn read-out neurons, N2 against each ensemble.

### The third replication of P4 (secondary, with a verdict)

N2's intact P4 against the five fresh ensembles, by 03r's single-signal rule, reported alongside 03's
and 03r's. It is secondary because 03r already replicated it, but every primary question reads
differently if it fails here, so it is reported first.

## 5. Procedure and composition

- **The probe batch:**
  - the rising and falling histories run as two rows of each strain (B = 2), sharing the strain's
    matrices; 03 ran them one after the other with one row;
  - the brain's dynamics are unchanged, and the rows do not interact;
  - this halves the GPU time, because the step is bound by reading the dense matrices.
- **Equivalence check, before the formal run (rule 7):** on N2 and the first 8 graphs of each of 03's
  ensembles, with 03's genomes, the B = 2 probe must reproduce 03's committed numerator and
  denominator to a relative 10⁻⁵, declared here. Exactness is not expected; 03m's own reproduction at
  B = 1 was exact.
- **One long run per graph and condition:**
  - 100 ticks of hold, the 10-tick ramp, then 300 ticks of the final input;
  - P4 is read at the ramp's end;
  - the steady contrast and the pre-tanh terms come from the same run.
  - A second, standard-length run gives P4 with gap junctions off.
- **Composition:** 2 048 strains × 2 rows per batch, every formal measurement. Exactness is claimed
  only within it.
- **Order** (cheapest and most central first, so a cap hit loses the least):
  1. the equivalence check;
  2. N2: intact and long, gaps off, the 95 pair deletions and the double deletion;
  3. Q-C's 256 permutations, then the factorial;
  4. the ensembles, interleaved (SH-route, SH-class, SH-mirror, SH-recip, SH, then the next index),
     so a stop leaves balanced ensembles;
  5. the null-graph deletions.
- **Writes:** every unit is written as it completes, with its provenance (the clean pushed commit, the
  GPU, the environment, the connectome's raw hash), as in 03m.

## 6. Statistics and multiplicity

- **The primary family is Q-A to Q-D, under Holm at a familywise α = 0.05** (one-sided, in each
  question's predicted direction).
  - Holm's thresholds are 0.0125, 0.0167, 0.025 and 0.05, in order of p.
  - With 128 graphs per ensemble, a rank p ≤ 0.0125 needs r = 0 in the worst ensemble, ≤ 0.025 needs
    r ≤ 2, and ≤ 0.05 needs r ≤ 5.
  - Q-B's and Q-C's p-values are expected to be the smallest (Q-C's is at best 1/257), so they take
    the strict thresholds.
- **Rough pass probabilities, from 03m's 16 graphs per ensemble** (a log-normal plug-in per ensemble;
  it ignores the fit's uncertainty and N2's own sampling, so treat it as a sketch):
  - Q-D at tick 30 passes with probability about 0.99 at r ≤ 5 in every ensemble, about 0.93 at
    64 graphs;
  - at tick 300, below 0.01.
  - Q-A: N2's ΔP4 was below all 80 null graphs, by a factor of 3.5 to the nearest.
  - Q-B and Q-C: 03m's effects are many bootstrap SEs from the thresholds.
  - The weakest link is Q-D's SH-recip, whose predicted chance of a graph above N2 is about 1.5% per
    graph.
  - A proper calculation (simulating fresh N2 genomes too) belongs in the pre-registration.
- **Completeness:**
  - at least 120 valid graphs in each ensemble, and a valid N2 intact, gaps-off and at tick 30;
    otherwise Q-A, Q-D, Q-E and the replication are withheld and the counts are reported;
  - Q-B needs valid intact, RIA and AIY measurements; Q-C needs at least 240 valid permutations.
- **Secondary tests** carry their own α = 0.05 and are labelled as outside the family.

## 7. Compute and cap

Estimates from the timings in §1, at 6.6 s per standard probe (B = 2) and about 23.5 s per long run:

| Part | Units | GPU-hours |
|---|---|---|
| equivalence check | 41 graphs | 0.1 |
| N2: long run, gaps off, 96 deletions | 98 probes | 0.2 |
| Q-C: 256 permutations; factorial 32 × 3 | 352 probes | 0.65 |
| ensembles: 640 graphs, long run + gaps off | 640 × 30 s | 5.3 |
| null-graph deletions: 160 graphs × 3 | 480 probes | 0.9 |
| **total** | | **about 7.2** |

- **The cap is 10 GPU-hours,** registered in code and counted by the accounting across attempts. A
  stop withholds what is incomplete and reports it.
- **The graph build** runs on the CPU, about 0.4 hours, in the same accounting.
- **The owner is told before the formal run starts.**

## 8. What this cannot establish

- **A mechanism,** beyond "this change moves these numbers". The brains are random and unevolved,
  the read-out is a hand-chosen interface, and deletions locate dependencies, not stores.
- **Anything about behaviour,** about evolved brains, or about the worm.
- **Independence from 03, 03r and 03m:** the same connectome, the same samplers, the same probe. A
  probe-specific effect or a systematic code error would recur here too (as 03r said of itself).
- **A full account of the hypotheses' origin:** they were chosen after 03m's data, and only the new
  draws make the tests confirmatory.

## 9. Questions for the reviewers

1. Is Holm over Q-A to Q-D right, or should each be its own family?
2. Q-D's endpoint: tick 30, chosen with 03m's curves in view, or a different summary (for example, the
   mean retained share over ticks 0-50)?
3. Q-B: are the 40% and 0.02 margins justified? And is a conjunction of equivalence and cut the right
   form for "a cut in both terms with their ratio kept"?
4. Q-A: is comparing changes (ΔP4) the right test, given the possible ceiling? Should the gaps-off
   levels be primary instead?
5. Anything missing that a reader would need to trust a pass, or a failure.
