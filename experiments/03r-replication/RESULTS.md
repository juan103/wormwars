# WormWars 03r: results of the full replication of experiment 03

**Replicated under the registered single-signal test and under 03's original three-signal rule.**
This is the outcome sentence fixed in advance in the pre-registration (§10).

With fresh graphs from all five null ensembles and fresh random genomes for every graph, N2's
included, N2's random brains again show unusually high normalised history dependence (P4):
- **Registered primary test** (P4 alone): maximum rank p **0.0155**, *distinctive relative to
  every ensemble*.
- **03's full three-signal rule** (Holm across P1, P3 and P4): adjusted p **0.0465**, also
  distinctive.
- **N2:** 0.924 (03: 0.931). It is above every graph in SH, SH-route (all 256), SH-mirror and
  SH-recip, and above 127 of 128 in SH-class.

**What this is and is not:**
- **It tests the sampling in 03:** which graphs, genomes, worlds and seeds.
- **It does not test the probe.** The replication used the same probe, stimulus bank and code; it
  tests sampling, not the probe.
- **The two runs are not independent evidence.** Both compare the same N2 connectome with graphs
  from the same generating procedure (pre-registration §2). Their p-values are never combined.
- **It establishes neither a mechanism nor any advantage for the worm.**

**Why there was a replication:** one graph decided 03's verdict. A single routing-matched graph at
or above N2 would have turned p = 0.047 into p = 0.070 (D058).
- **Fable 5.1** asked for replication before any public claim.
- **Astra 6** specified independent genomes for N2 as well as fresh graphs, and did not require
  replication first.
- **Claude Opus 5.5** leaned toward replicating first.
- **The owner decided:** a full replication (D059).

Everything was fixed in [`PREREGISTRATION.md`](PREREGISTRATION.md) (v3, bound at `7c146fc`),
after two review rounds plus final checks by Astra 6 and Fable 5.1 (D060, D061). Its public
disclosure came while the run was in progress ([`DISCLOSURE.md`](DISCLOSURE.md)).

**Run facts:**
- **Scale:** 773 graphs (768 ensemble graphs, plus N2 and 4 variants), 23.95 GPU-hours of the
  registered 32-hour cap, one GPU.
- **Code:** every measurement records commit `7c146fc` with `code_dirty: false`.
- **Report:** [`report.json`](report.json). It was produced by the binding commit's code (from a
  worktree at `7c146fc`) and again by the current code, and the two are identical.
- **Completeness:** every ensemble complete; no calibration failure; every signal valid on every
  graph (the accounting table in `report.json`).

---

## Primary: P4 alone (registered, §6)

N2 = **0.924** (SE 0.0065). The maximum p over the ensembles is **0.0155**, against α 0.05.

| ensemble | valid n | graphs ≥ N2 | rank p | rank gate | N2 − mean [90%] | margin | margin gate | verdict |
|---|---|---|---|---|---|---|---|---|
| SH | 128 | 0 | 0.0078 | pass | +0.149 to +0.179 | 0.035 | pass | distinctive |
| SH-route | **256** | 0 | 0.0039 | pass | +0.073 to +0.094 | 0.017 | pass | distinctive |
| SH-class | 128 | 1 | 0.0155 | pass | +0.082 to +0.106 | 0.022 | pass | distinctive |
| SH-mirror | 128 | 0 | 0.0078 | pass | +0.069 to +0.092 | 0.016 | pass | distinctive |
| SH-recip | 128 | 0 | 0.0078 | pass | +0.144 to +0.174 | 0.038 | pass | distinctive |

**03 beside 03r** (registered descriptive, §5; `P4_beside_03` in `report.json`):

| ensemble | 03: N2 − mean [90%], graphs ≥ N2 | 03r: N2 − mean [90%], graphs ≥ N2 |
|---|---|---|
| SH | +0.170 to +0.198, 0 of 128 | +0.149 to +0.179, 0 of 128 |
| SH-route | +0.077 to +0.099, **1 of 128** | +0.073 to +0.094, **0 of 256** |
| SH-class | +0.094 to +0.118, 0 of 128 | +0.082 to +0.106, 1 of 128 |
| SH-mirror | +0.081 to +0.103, 0 of 128 | +0.069 to +0.092, 0 of 128 |
| SH-recip | +0.159 to +0.190, 0 of 128 | +0.144 to +0.174, 0 of 128 |

- **The effect sizes are close,** and 03r's are slightly smaller everywhere.
- **The ensemble that decided 03 (SH-route)** has no graph at or above N2 in 256 fresh graphs.
- **A different ensemble (SH-class) now has one.**
- **The borderline character remains** under 03's Holm rule, which again lands on its second
  attainable value (0.0465). The registered single-signal test, which is 03r's primary, passes
  with room to spare.

## Secondary: 03's full rule for P1 and P3 (registered, §6)

The pre-registration commits to reporting these whatever they are, as recurring or non-recurring
decision labels, not as evidence of absence (§2).

### P1, directional selectivity: *not distinctive*, recurring

N2 = −0.013 (SE 0.022). Holm-adjusted p = 1.0.
- **Verdicts:** inconclusive against SH, SH-route, SH-class and SH-mirror; consistent with
  SH-recip.
- **Where N2 sits:** between 95 and 107 of 128 graphs (201 of 256 in SH-route) are at or above
  it. That is the same label as in 03.
- **What this does not mean:** "not distinctive" is not evidence that N2 has no directional
  selectivity.

### P3, food-information dependence: *reversed against every ensemble*, a **new** label

N2 = **−0.024** (SE 0.012). The ensemble means lie between −0.001 and +0.001. The Holm-adjusted
p in the opposite direction is **0.0465**.
- **Where N2 sits:**
  - no graph in SH, SH-class or SH-mirror is at or below it, of 128 each; none of 256 in
    SH-route; 1 of 128 in SH-recip;
  - every effect interval lies wholly below zero, beyond its margin. SH-route's margin was 0,
    because its latent SD estimate truncated to 0, as the pre-registration allows.
- **What P3 measures:** fitness on single-nose foraging (02-T1) with the real food signal, minus
  fitness when the food signal is replaced by each world's tick-0 mean. A negative value means
  N2's random, unselected brains score **slightly worse with the real food signal than with an
  uninformative constant one**.
- **It is small:** about 0.024 on a generation-0 score of about 0.9, roughly 2.6%.
- **This label did not recur.** In 03, P3 was inconclusive: N2 −0.010, with 114-120 of 128 graphs
  above it and an opposite-direction Holm-adjusted p of 0.35. The direction matches 03's point
  estimate, and 03r has fresh genomes and worlds.
- **Status:** it is a **secondary result that was not predicted.** The registered prediction was
  N2 *above* the ensembles. It is controlled only within 03's opposite-direction family, and both
  directions together allow up to 10% error (§6). It is reported here as found, with no claim
  about its cause. A claim would need its own pre-registered test.

## Registered descriptive secondaries (§5)

**The P4 decomposition** (`supplement.json`, per graph):

| | numerator: mean \|rising − falling\| | denominator: mean \|steady contrast\| | common-mode turn | forward-read-out P4 |
|---|---|---|---|---|
| N2 | 0.110 | 0.119 | 0.028 | 0.887 |
| ensemble medians | 0.016-0.020 | 0.018-0.025 | 0.004-0.006 | 0.72-0.82 |
| largest single ensemble graph | 0.048 | 0.077 | 0.020 | 0.91 |

- **N2's magnitudes again exceed every ensemble graph's.** So a high P4 is not a small
  denominator, as in 03.
- **On the forward read-out,** 0, 1, 0, 3 and 0 graphs are at or above N2 in the five ensembles.
- **Calibration validation:** within 7.2% of the target drive on every validated graph, and 2.8%
  for N2.

**The N2 variants** (descriptive only; fresh permutations 4-6; graphs at or above on P4, in SH,
SH-route, SH-class, SH-mirror, SH-recip):

| | P4 | common mode | graphs ≥ on P4 |
|---|---|---|---|
| N2 | 0.924 | 0.028 | 0, 0, 1, 0, 0 |
| N2perm4 | 0.856 | 0.005 | 11, 89, 40, 51, 11 |
| N2perm5 | 0.859 | 0.008 | 9, 80, 34, 47, 11 |
| N2perm6 | 0.922 | 0.004 | 0, 0, 1, 0, 0 |
| N2-rev | 0.911 | 0.0001 | 0, 1, 1, 0, 1 |

- **As in 03,** a permutation of N2's weights over its own edges can keep P4 at N2's level
  (N2perm6) or lower it to the upper-middle of the ensembles (N2perm4, 5). That happens at
  ordinary responsiveness.
- **N2-rev's** P4 is a ratio of numbers near 4 × 10⁻⁴, so it is not interpreted (D058).
- **Three draws isolate no cause.**

**Other secondaries (N2):**
- mapping preference P2: −0.005. Every ensemble's mean-P2 95% interval includes zero;
- T0 at M0: mean 0.91, top decile 1.66;
- coverage: 114 cells;
- P4 decay (median share left 5 ticks later): 0.86.

The ensemble quantiles are in `report.json`.

## What this decides (§10)

- **Replicated.** 03's P4 finding holds under this probe with fresh graphs and genomes, under both
  rules. Per §10 and roadmap v3, the **mechanism follow-up** is next in Track B:
  - where the history effect lives (deletions);
  - gap junctions or chemical synapses;
  - inputs other than food;
  - what gives N2's random brains their stronger response.
  It needs its own pre-registration. Bridge 2 (the A/B shuttle on N2 and matched nulls) gains
  priority, per the roadmap.
- **A pass supports sampling stability under this probe.** It is not independent confirmation, and
  it does not identify a mechanism (§2).
- **P1 recurs as "not distinctive". P3 does not recur:** it is now *reversed*, an unpredicted
  secondary result reported as found.

## Deviations and disclosures

- **The README sentence bound in §10 is amended** (D063). It said "a full replication was run
  before publishing". 03's first-run results were public on the `roadmap` branch from 2026-09-27
  17:28 +02:00, while 03r ran. So the README says a full replication was run before 03 was merged
  into main and presented as a result, and that 03's first results were public on the branch
  meanwhile.
- **Public disclosure came after measurement began**
  ([`DISCLOSURE.md`](DISCLOSURE.md)). No signal value from the formal run was inspected before the
  report. The one value seen before binding was the preflight's P4 (0.756, SH-1010000), which is
  disclosed.
- **Otherwise none.** The run used its registered cap and order (N2 last); the report ran as
  registered, and no parameter was chosen after seeing the data.
