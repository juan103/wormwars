# 03mc: pre-registration of a confirmatory test of 03m's leads on P4

**Status:** draft 2, 2026-10-16. Draft 1 (`c0f1020`, D289) was reviewed with the code by Astra 6 and Fable 5.1
(run 20261016-023227): both "fix first"; every finding is taken (D290). It becomes
binding at the commit recorded in `bound.json` (committed after binding, since a commit cannot name itself). After
binding this text is never changed. Amendments are appended below it, dated, and the runner refuses any other change
(`scripts/p4mc.py`, `prereg_append_only`).

**The design** is `DESIGN.md` v2.2, agreed by both reviewers after three rounds (D285-D288). It holds the reasons;
this file holds the rules. Where the two differ, this file governs.

## 1. Disclosures

1. **Everything 03, 03r and 03m measured is known.** Every hypothesis here comes from 03m's exploratory data
   (`experiments/03m-p4-mechanism/`, corrected in D114), and so do the choices that matter: Q-D's endpoint tick,
   Q-B's margins, and which questions are primary. Only the new draws make the tests confirmatory: fresh genomes for
   every graph (N2's included), fresh null graphs and fresh permutations. All are drawn after this file and its code
   are bound and pushed.
2. **Measured before binding, on old inputs only** (03's genomes and 03m's panel; nothing fresh drawn):
   - the probe's GPU time (D285);
   - the two-row probe against one-row references, twice (`equivalence.json`, 0.52 GPU-hours;
     `equivalence-check.json`, 0.24 GPU-hours). Both passed and were run on uncommitted code over a committed
     HEAD;
   - the model-based pass probabilities (`power.py`, `power.json`), from 03m's committed summaries and its local
     per-genome arrays (their hashes recorded);
   - the planned seeds' freshness audit (`scripts/p4mc.py audit`): it hashes names only and draws nothing.
3. **Smoke runs** used a separate salt ("03mc-smoke:"), separate graph seeds (2 900 000 + i), permutation seeds from
   9 000, and `runs/p4mc-smoke/`. They never touch a formal input, and the formal audit keeps clear of their seeds.
4. **Reviewers' own runs:** in the review of design v2, Astra ran checks on this machine on old inputs (84 s of
   GPU), outside this study's accounting.

## 2. The questions

With fresh genomes, graphs and permutations, do 03m's leads hold?
- **Q-A (gap junctions):** does N2's P4 change unusually little when gap junctions are switched off?
- **Q-B (RIA and AIY):** does deleting either pair cut N2's response by more than 40% while P4 stays within 0.02?
- **Q-C (weight placement):** is N2's response unusually high against permutations of its own weight magnitudes?
- **Q-D (relaxation):** does N2 keep an unusually large share of its history difference 30 ticks after the ramp?

**Secondary, with verdicts:** the third replication of P4, and Q-E, P4 on the read-out before the tanh.

## 3. What is measured

**The probe** is 03's, unchanged except that the two histories run as two rows of each strain
(`wormwars/exp03/twin.py`):
- 03's stimulus bank (`experiments/03-generation0/pilot.json`) and interface M0;
- holds at 0.25 and 1.75 times the final food level for 100 ticks, then a 10-tick ramp to it;
- the raw turn read-out.

**P4** is the mean |rising − falling| at the ramp's end over the mean |steady contrast|, in float64. It is invalid if
the denominator is below 10⁻⁴ or either term is not finite. **The response** is P4's denominator, the mean |steady
contrast|.

**Per graph, two runs:**
- **a long run:** P4, then the final input held for 300 ticks;
  - the difference recorded at ticks 0, 5 and every 10;
  - the pre-tanh terms;
  - settling: the largest range of any neuron's state over each of the last 10 ticks, both rows; a genome is
    settled if it is below 10⁻⁴;
  - the turn read-out neurons' mean tanh slope at the holds' and the ramp's end;
- **a standard run** (5 ticks after the ramp) with every gap junction's weight set to zero.

**Retained share at tick t:** mean |difference| at t over the same at tick 0. It is valid only if P4 is valid and the
tick-0 mean is at least 10⁻⁴.

**Pre-tanh P4:** the same ratio on the mean state of the turn-plus neurons minus that of the turn-minus neurons, with
the same floor.

**Genomes:** 2 048 per graph, `Genome.random`, generator seed `genome_seed(name, "03mc:") + 1`.

**Graphs:** N2, and 128 fresh graphs from each of 03's five samplers:

| | SH | SH-route | SH-class | SH-mirror | SH-recip |
|---|---|---|---|---|---|
| seed i (substitutes add 100 000) | 2 010 000 + i | 2 020 000 + i | 2 030 000 + i | 2 040 000 + i | 2 050 000 + i |

- **The build:** `scripts/exp03.py build --instance 03mc`, through `scripts/p4mc.py build`, with 03's validation
  rules: plateau chains 2 090 000-2 090 003 at 20 and 40 passes agreeing within 0.01, minimum acceptance 5%, no graph
  over its Jaccard ceiling.
- **Before and after the build, the freshness audit** (`mc.freshness_audit`, `mc.content_check`):
  - every derived seed (seed, +1, +2) of every new name must be new and distinct from 03's, 03r's, 03m's and the
    smoke runs';
  - the salt must be new;
  - permutation seeds are compared as the generator seeds the permutation uses (2 × seed + type), against 03's (0-3),
    03r's (4-6 and every `_gseed(name) + 2`), 03m's (100-163) and the smoke runs';
  - every new graph's array content must differ from every other new graph's and from 03's and 03r's content
    manifests.
- **Any failure, of the audit, the content check or 03's validation rules, stops the study before anything is
  measured;** it is reported and resolved only by an amendment.

**Permutations:** 256, seeds 1 000-1 255. N2's chemical and gap magnitudes are each permuted within their type, on
batch 0's genome draws (signs, biases and time constants unchanged).

**Q-B's genomes:** batch 0 (N2's genomes above) and batches 1-31 from the names "N2#1" ... "N2#31", 65 536 genomes in
all.
- **In each batch:** intact, the RIA pair deleted, the AIY pair deleted, and both.
- **A deletion** removes every edge and gap junction touching the neuron, and its bias (`wormwars/deletion.py`).
- **In batch 0:** an empty deletion must reproduce the intact terms exactly, or the run stops.

## 4. Order, composition and the cap

**The order** (`scripts/p4mc.py`, `plan`), fixed in advance; nothing is added or rerun because of a result:
1. N2's batch 0: the long run and the gaps-off run.
2. Q-C's 256 permutations.
3. Q-B's 32 batches.
4. The ensembles: graph i of SH-route, SH-class, SH-mirror, SH-recip and SH, then graph i + 1, and so on (long run
   and gaps-off run each).
5. The secondaries:
   - the 93 other bilateral pairs that touch no turn read-out neuron, deleted on batch 0;
   - the factorial: RIA, AIY and both, deleted under the first 32 permutations;
   - the null-graph deletions: RIA, AIY and both, in the first 32 graphs of each ensemble.

**Composition:** every measurement runs 2 048 strains × 2 rows. Reruns are expected to agree within the pre-run
check's tolerances; no exact repeat is claimed.

**The cap: 10 hours,** counted by the accounting in `runs/p4mc/compute` (synchronised wall time) across every
formal command and attempt: the build, the pre-run check, the run and any resume.
- It is checked before the build and before every unit; a unit begun under the cap runs to completion.
- **The build is one unit.** 03's builder queues every graph in one pool, so the build's overrun can be the whole
  build, about 0.4 hours on the CPU. This replaces design v2.2's per-graph build unit (Astra). The runner's own steps
  around the builder (the audits, the content check) run in two small attempts of the same accounting.
- A stop is administrative: what is incomplete is withheld and reported, and a primary question left unmeasured
  enters Holm with p = 1.
- **Estimate:** about 7.9 hours (DESIGN §7).

**Nothing else runs on the machine during the formal run** (DESIGN §5).

## 5. The pre-run check

Before `run`, `scripts/p4mc.py check` runs the pre-run check on old inputs (`scripts/p4mc_equivalence.py --set
check`) and writes `prerun-check.json`.
- **The check set:** N2 and the first 4 graphs of each of 03's ensembles, plus SH-mirror-40015, SH-10007 and
  SH-recip-50015, with 03's genomes; and N2 with gap junctions off, with the RIA pair deleted, and under 03m's paired
  permutation 100.
- **The repeat check:** on 03's N2 genomes (old inputs), at the registered composition, the intact probe twice and
  the empty deletion once must agree bit for bit (`prerun-repeat.json`). The run's empty-deletion stop needs this
  (Fable).
- **The tolerances,** as declared in the script (`TOL`, `LABELS`):
  - **aggregates within a relative 10⁻⁵:** P4's terms against 03's supplement, the tick-30 share against 03m's,
    and the pre-tanh terms against a one-row reference;
  - **per genome within 10⁻⁴:** the ramp end, the steady contrast, tick 30, the slopes and the pre-tanh terms;
  - **per genome, wider:** the holds' range within 3 × 10⁻⁴, and the curve within 2 × 10⁻³;
  - **settling labels:** at most 2 genomes of any graph with any changed label;
  - **the references:** the local reference arrays must hash as `power.json` recorded.
- **If the check fails, nothing formal runs.** The failure is reported, and an amendment decides, reviewed by
  both. The measured deviations are reported whatever they are.
- **The check runs once.** Its start marker is written before it runs; a check that stops before writing its records
  is not rerun either, and an amendment decides.
- **The run admits a check only if:** both records passed; the set is `check`, on CUDA, at 2 048 genomes; the
  references are pinned; the check ran on committed code equal to the code that runs now; and its start marker
  exists.

## 6. The primary questions

One family under Holm at a familywise α = 0.05 (`mc.holm`), one-sided in each predicted direction. A withheld
question enters with p = 1, so the family keeps four members.

**Rank p:** for N2 against one ensemble, p = (r + 1)/(n + 1), with n the valid graphs. A non-finite N2 gives p = 1.

**Intersection-union:** a question's p is the largest p over the five ensembles. A missing ensemble gives p = 1.

**Completeness, per question:**
- **Q-A and Q-D:** a valid N2, and at least 120 valid graphs in every ensemble.
- **Q-B:** every batch's intact, RIA and AIY units, and a valid bootstrap. The double deletion is descriptive, and its
  absence does not withhold Q-B.
- **Q-C:** a valid N2 reference and at least 240 valid permutations.

Otherwise the question is withheld. Every question reports, per ensemble where it applies, its planned, measured and
valid counts separately.

### Q-A

- **Measure:** ΔP4 = gaps-off P4 − long-run P4, per graph, on the same genomes. A graph, or N2, counts only if both
  of its P4s are valid.
- **Test:** r counts the graphs with ΔP4 ≤ N2's.
- **Pass:** "N2's P4 changed unusually little when gap junctions were switched off, relative to each ensemble:
  graphs per ensemble that changed as little or less: [counts]."
  - **Only if the replication (§7) is "distinctive relative to every ensemble",** a second sentence, computed
    from N2's lead over each ensemble's median P4, intact and gaps-off:
    - if the gaps-off lead is smaller in every ensemble: "N2's P4 lead over each ensemble's median narrows without
      gap junctions, by: [the change, per ensemble]";
    - otherwise: "N2's lead over the ensemble median did not narrow in every ensemble: [the change, per ensemble]".
    - A pass on the rank test does not by itself imply the lead narrowed (Fable).
- **Fail:** "the registered criterion was not met: graphs per ensemble that changed as little as N2 or less:
  [counts]."

### Q-B

- **Estimates:** pooled over the 32 batches, as ratios of means over genomes:
  - the response cut, 1 − den_deleted / den_intact;
  - the numerator's cut;
  - ΔP4.
- **SEs** come from a paired bootstrap: 10 000 resamples of genome indices, shared by both conditions,
  `numpy.random.default_rng(20261016)`.
  - A resample with a denominator below 10⁻⁴ is dropped and counted; more than 1% dropped withholds Q-B.
  - The full-sample estimate must also clear the floor.
- **Tests** (`mc.qb_tests`), with the SE treated as known:
  - p_cut = Φ(−(cut − 0.40)/SE);
  - p_eq = max(Φ(−(ΔP4 + 0.02)/SE), Φ(−(0.02 − ΔP4)/SE));
  - Q-B's p is the largest of the four values (RIA and AIY, cut and equivalence).
- **Reported beside the tests:** the 90% percentile intervals, as a check, not as a test.
- **Pass:** "Deleting the RIA pair, or the AIY pair, cuts N2's response by more than 40% while P4 stays within 0.02:
  the history signal falls approximately in proportion."
- **Fail:** "the registered criterion was not met:" then each failed part, with its estimate and 90% interval.

### Q-C

- **Test:** r counts the valid permutations whose response is at least N2's response on its batch-0 intact unit
  (`qb/0/intact`); p = (r + 1)/(n + 1). A valid permutation is one whose P4 is valid.
- **Completeness:** at least 240 valid permutations.
- **Pass:** "N2's response is unusually high relative to permutations of its weight magnitudes: [r of n]
  permutations reached it."
- **Fail:** "the registered criterion was not met: [r of n] permutations reached N2's response."

### Q-D

- **Test:** r counts the graphs whose retained share at tick 30 is at least N2's.
- **Pass:** "N2 retained an unusually large share of its history difference 30 ticks after the ramp, relative to
  each ensemble: graphs per ensemble that retained as much or more: [counts]."
- **Fail:** "the registered criterion was not met: graphs per ensemble that retained as much as N2 or more:
  [counts]."

**Holm stops:** a question whose own p met 0.05 but not its Holm threshold reads "met α = 0.05 alone, but not its
Holm threshold: not confirmed under the registered familywise rule", followed by its sentence. Under Holm's step-down
rule, an earlier question's failure can stop it as well as its own threshold; the sentence covers both.

**Reported for every question:** the raw and Holm-adjusted p, every component, and the planned, measured and valid
counts. The intervals are 95% percentile bootstraps over N2's 2 048 genomes (seed 20261016, 10 000 resamples):
- Q-A: N2's ΔP4;
- Q-C: N2's response;
- Q-D: N2's share at tick 30;
- Q-B: its bootstrap's intervals.

Each ensemble's median ΔP4 is reported beside Q-A.

## 7. The secondaries

**With verdicts, by 03r's single-signal rule** (`report.single_signal`). Each ensemble's maximum rank p is taken at
α = 0.05, with the effect-margin gate: 0.5 × the latent SD, and the 90% effect interval from 1 000 bootstrap draws,
seed 1. The outcomes are 03r's: "distinctive relative to every ensemble", "reversed against every ensemble", "not
distinctive" (with the failing gates named), or withheld. The full per-ensemble records are kept in the report:
- **the third replication of P4:** reported first, beside 03's and 03r's. If it is not distinctive, RESULTS says
  first that the lead did not replicate here;
- **Q-E, the pre-tanh P4:**
  - pass: "P4's distinctiveness persists on the pre-tanh read-out";
  - fail: "pre-tanh distinctiveness was not established", with the failing gates named.
  - The tanh stays in the recurrent dynamics, so this is robustness to the read-out map only;
- **N2's gaps-off P4** against each ensemble's gaps-off P4.

**With tests, outside the family, each at 0.05:**
- N2's P4 rank among the 256 permutations. Its power is low, and that is said in advance (03m's 59 of 64 points to a
  rank p near 0.08).
- Q-D's rank test at ticks 10, 50, 100 and 300. At tick 300 a failure is expected.
- **The degree-matched controls:**
  - RIA's controls are AIB, AVJ, RIM and AVH; AIY's are AWB, RIF, RIP and RIV. They are the four pairs nearest in
    total degree, ties broken alphabetically; the code derives the list and a test asserts it.
  - Each comparison is the paired difference in response cut on batch 0, over its bootstrap SE (10 000 resamples,
    seed 20261016): p = Φ(−difference/SE).
  - The claim "the target's cut exceeds each of its four controls'" takes the largest p (intersection-union).

**Descriptive.** Every interval is a 95% percentile bootstrap with 10 000 resamples. The unit and seed are genomes,
paired (20261016); permutations (20261017); or graphs (20261018). A transformed quantity is transformed in each
resample before the quantiles. A quantity whose reference fails its floor is reported as unavailable. The
descriptives:
- all 95 pairs' response cuts, numerator cuts and changes in P4 on batch 0, with paired intervals, and RIA's and
  AIY's ranks;
- the double deletion;
- the numerator's and the response's cuts side by side;
- the factorial contrast: N2's cut minus the permutations' mean cut;
- the null-graph deletions: each graph's cut, each ensemble's median with an interval, and N2's rank among them;
- the share of N2's excess P4 over the pooled fresh null median that the permutations' median keeps;
- the full retention curves;
- among genomes starting above 10⁻³, the share with more than 10% of their difference left at tick 300;
- the counts of genomes settled with separation left;
- the turn read-out's tanh slope at the holds' and the ramp's end, N2 against each ensemble.

**Not claimed:** stable states; whether any deletion removes the elevated P4; that weight placement acts through RIA
and AIY.

## 8. What this cannot establish

- **A mechanism,** beyond "this change moves these numbers". The brains are random and unevolved, the read-out is
  hand-chosen, and deletions locate dependencies, not stores.
- **Anything about behaviour,** evolved brains, or the worm.
- **Independence from 03, 03r and 03m:** the same connectome, samplers and probe. A probe-specific effect or a
  systematic code error would recur here.
- **That the hypotheses were chosen in advance:** they were chosen after 03m's data.

## 9. Procedure and records

1. **Bind:** this file and the code are committed and pushed; `bound.json` records the commit and is committed and
   pushed after it.
2. **Build** (CPU): `scripts/p4mc.py build`. The build's records are committed: `build.json`, `ensembles.json`,
   `graphs_manifest.json` and `graphs_content_manifest.json`. The graph files stay local.
3. **The owner is told** the plan and the estimate, and gives the word for the GPU stages.
4. **Check:** `scripts/p4mc.py check --device cuda --owner-word "..."`. `prerun-check.json` and `prerun-repeat.json` are committed.
5. **Run:** `scripts/p4mc.py run --device cuda --owner-word "..."`. `measurements.json` is written after every
   unit and committed; the per-genome arrays stay local with their sha256 in the records.
   - A resume refuses changed code, environment, inputs or plan.
6. **Report:** `scripts/p4mc.py report` writes `report.json`, which is committed.
7. **Then:** RESULTS.md, a review by both, and publication whatever the outcome.

**Every formal stage (build, check, run, report) refuses unless all of these hold:**
- the bound commit (and any code commit) is an ancestor of HEAD;
- every committed version of this file since binding grows from the one before, and the working file from the last.
  Additions start on lines of their own, so an amendment, once committed, can be neither edited nor removed;
- the code (`wormwars`, `scripts`, `configs`, `requirements.txt`) is unchanged since the bound commit. If the code
  must change after binding, an amendment says why and names the new code's commit, `bound.json` gains it as
  `code_commit`, and the code is checked against that commit instead (as E4-D's Amendment 1 did); a `code_commit`
  that no amendment names is refused;
- the pinned environment;
- a clean, pushed tree, including the stage's inputs: the build records for check, run and report; the check records
  for run and report; `measurements.json` for report.

**Stage by stage:**
- **The build** runs on the CPU. `exp03.py` itself refuses a formal 03mc build without the token the runner passes
  after these checks.
- **The check and the run** need CUDA on the registered GPU (RTX 5080) and the owner's word.
- **The report** simulates nothing. It checks each unit's arrays against their recorded sha256 and never overwrites
  an earlier report (a later one gets a time stamp).
- **The run** takes an exclusive lock, records any array file it replaces after an interruption, and resumes only
  with the first attempt's code, environment, inputs, registered settings and full plan, and with every completed
  unit's arrays as recorded. It never resumes after the empty-deletion stop.
