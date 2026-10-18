# 03a: the self-consistency proof of concept. Results (exploratory)

**Exploratory.** 03a stopped before its pre-registration. Nothing here is a registered test.
- **What touched N2:** no 03a reconstruction search or pilot brain evolution ran on N2. The pilot's motor gains were
  calibrated against an N2 reference drive (`setup.json`, `calibration.n2_reference`). The exploratory checks before
  pilot-dev (D303, D304) scored 04a's N2 champions. Neither of those is a test of the hypothesis on N2.
- **What ran:** pilot-dev, the development stage on one shuffled graph (DESIGN.md v7.1 §8), then a bounded check of
  the search. Both reviewers recommended the check, and the owner chose it (PILOT-DEV.md §7).
- **How it ended:** the check's rule was fixed before it ran. Its outcome, (iii), ends 03a (D317).

**Where the numbers come from:** `scripts/e03a_summary.py` reads the committed stage records in
[`pilot-dev/`](pilot-dev/) and writes [`summary.json`](summary.json). Each number below is from that file, or from the
record named beside it. `tests/test_e03a_summary.py` checks that the committed summary is exactly what the records
give.

## In one paragraph

The search could not test the hypothesis on this graph. A neuron, URXL, was deleted from an evolved brain, and its
wiring alone was searched for the task.
- **Free searches** matched, on average, the score of refits handed the true partners, within the margin. No
  enrichment toward the true partners was detected.
- **Refits** handed the true partners did not regain the restored brain's score reliably. The shortfall was 0.10 to
  0.14 targets, against a margin of 0.098, and it persisted under three changes to the search.
- **A reading** (exploratory, from two fixed states): offspring that improved on the reference worlds were rare and
  small, so acceptance mostly followed evaluation noise. Noise is a contributor, but these records do not show it is
  the whole reason.
- **The brain's dependence on URXL:** removing a single outgoing edge of URXL from the evolved brain could cut its
  score from 1.97 to 0.05. Yet free searches with other wiring matched the true partners' refits on average.
- **The NIP brains:** neither NIP target-brain had headroom above the margin under these refits.
- **The limits:**
  - pilot-dev searched four target-brains, of which one had headroom, and the check searched that one, on one shuffled
    graph;
  - it shows that this search procedure, at this budget, could not do the job;
  - it says nothing about N2 or about the hypothesis itself.

## What ran

Pilot-dev ran on the SH-mirror graph with seed 3 403 000. The graph is rebuilt from its seed and checked by hash; it is
never saved. Each stage's record and commit (`summary.json` `stages`):

| Stage | Commit | Wall hours | What it did |
|---|---|---|---|
| setup | `a5760c4` | 0.01 | the graph, its hash and the motor gains |
| evolve-intact | `a5760c4` | 0.74 | the selector brain and the MIP brain, 1 000 generations |
| panel | `1b0531a` | 0.03 | the deletion scan on the selector brain, the tiers, the two targets |
| evolve-nip | `1b0531a` | 0.67 | one NIP brain per target, X's edges pinned at zero |
| baseline | `1b0531a` | 0.02 | intact, deleted and restored scores, with the exactness controls |
| probe | `1b0531a` | 0.08 | the bounded-history probe on the calibrators and the evolved brains |
| tune | `f27d4c4` | 1.55 | the search's settings, three rounds |
| full | `f27d4c4` | 1.46 | every search of the four target-brains, with the diagnostics |
| report | `f27d4c4` | 0.00 | throughputs and the formal projection |
| search-check | `4d6e887` | 0.73 | the bounded check (PILOT-DEV §7) |

**Compute** (`summary.json` `compute`):
- **Pilot-dev's measured GPU-hours:** 5.29, the bounded check included (`pilot-dev/compute.json`). The CUDA preflight
  adds 0.03 (`pilot-dev/preflight-compute.json`), so 5.31 against the cap of 6.
- **03a overall:** 5.84 of its 72 hours, the 0.53 of exploratory checks included (D303, D304). The other 66 are not
  spent.

**Reviews:**
- **The code:** three rounds (D308-D311). `setup` and `evolve-intact` ran while round 2 was under review, and `panel`
  to `probe` while round 3 was. None of them depends on what those rounds changed (PILOT-DEV status).
- **Afterwards:** the results were reviewed once (D313), the check's plan twice (D315, D316), and this page once
  (D319).

## The machinery held

Every implementation control passed on CUDA (`baseline.json`, `probe.json`):
- **Restoration:** MIP's exact restoration reproduced the intact brain's episodes exactly, for both targets. That
  covers the counts, the final head positions and every target event.
- **NIP's deleted state:** each NIP brain played exactly as its deleted state on the union mask.
- **The probe's full-replay control** reproduced every evolved brain's episodes.
- **The calibrators:** KT (no memory) and KTM (one tick) were unaffected at every window.
- **Pinning:** X's edges stayed at zero through both NIP evolutions (`evolve-nip.json`, `pinned`).

Family 2's simulated-null validation passed earlier (`family2-validation.json`, D308).

## Evolution and the panel

**The champions,** on the validation worlds (`summary.json` `evolution`):
- the selector brain reached 2.13 targets per episode;
- the MIP brain reached 2.02;
- the two NIP brains reached 2.21 each.

On the final worlds, the MIP brain scores 1.966. Its margin p, 5% of that, is 0.098 (`baseline.json`).

**The panel** (`panel.json`):
- **The tie:** on the selector brain, 10 of the 170 eligible representatives' deletions each reduce the score to
  zero. That is a ten-way tie at the ceiling, from which the high tier (URXL, PLNL, AIBL) was drawn by the seeded rule.
  The record raised no flag for it.
- **The targets:** the two highest-ranked, URXL and PLNL.
- **Relevance did not transfer for PLNL:** deleting it from the MIP brain costs only 0.013, 0.13 p.
- **URXL is the one target where the deletion matters:** its deficit is 1.78, and it has 45 true edges (18 in, 25 out,
  2 gap).

## History use (the probe; descriptive)

Each brain's state was rebuilt from zeros every L ticks, replaying the last L ticks. Scores on 2 048 worlds
(`summary.json` `probe`):

| Brain | Plain | L = 5 | L = 10 | L = 20 | L = 50 |
|---|---|---|---|---|---|
| selector | 2.10 | 0.27 | 0.55 | 1.35 | 1.83 |
| MIP | 1.95 | 0.00 | 0.06 | 0.71 | 1.57 |
| NIP/URXL | 2.21 | 0.61 | 0.32 | 0.74 | 2.01 |
| NIP/PLNL | 2.17 | 0.24 | 1.16 | 0.74 | 2.10 |
| KT, no memory | 1.16 | 1.16 | 1.16 | 1.16 | 1.16 |
| KTM, one tick | 2.88 | 2.88 | 2.88 | 2.88 | 2.88 |
| KTS, T = 5 | 2.72 | 2.77 | 2.74 | 2.72 | 2.72 |
| KTS, T = 10 | 2.19 | 2.38 | 2.34 | 2.19 | 2.19 |
| KTS, T = 20 | 1.60 | 1.58 | 1.41 | 1.62 | 1.63 |

- **The evolved brains depend on neural state older than the window,** under this intervention. At L = 50, the reading
  least confounded by slow neurons (τ runs to 20 ticks), the MIP brain loses 0.38 and the selector 0.27. The NIP brains
  lose 0.20 and 0.07.
- **The slow-memory calibrators** (KTS) changed by up to ±0.19 when L ≤ T:
  - +0.19 and +0.16 for T = 10 at L = 5 and 10;
  - −0.19 for T = 20 at L = 10.

  The rebuild does change their stored average, and the design required no sign ("no sign required").
- **What a loss does and does not mean:**
  - a loss includes filtering by slow neurons and any rhythm the reset disturbs, so it is not uniquely useful sensory
    memory (DESIGN §8);
  - the calibrators' known slow memory moves the score by at most 0.19, while the evolved brains lose up to 1.95 at
    short L, so the calibrators give no scale on which those losses read as sensory memory;
  - between resets, the history available varies from L to 2L ticks, and the first affected action is at 2L + 1, so
    comparisons across L do not estimate a memory horizon;
  - no nonspecific-disruption control was run (DESIGN §8).
- **Not run:** the other probes the design lists (constant scent, jitter, hold, ramp). Pilot-check's criterion 1 (the
  evolved brains use the cue) was therefore never measured.

## Tuning

Three rounds, on two free searches per setting and target-brain (`summary.json` `tune`):
- **Round A, the ladder:**
  - no ladder had every neighbour pair inside the 20-40% swap band; the mean swap rates were 0.79, 0.88 and 0.95;
  - the rule kept the nearest, (0.1, 0.2, 0.4, 0.8), and flagged it.
- **Rounds B and C** kept their first settings: one move at probability 1/3, and no shaping. Every alternative was
  within 0.011 of them in mean final score.

These are noisy choices, not optima (D311).

## The searches on the four target-brains (`full`)

Each target-brain ran:
- 3 original-partner refits (the reference);
- 5 random-partner refits, matched to the true partners' strata;
- 5 free searches of 100 generations;
- on the MIP target-brains, 2 longer searches of 200 generations.

The final states were scored on 2 048 worlds, and every comparison is against the margin p (`summary.json` `full`):

| | MIP/URXL | MIP/PLNL | NIP/URXL | NIP/PLNL |
|---|---|---|---|---|
| Headroom (reference − deleted) | 1.65, above | −0.01, equivalent | 0.05 [0.03, 0.07], equivalent | 0.01, equivalent |
| Original-partner advantage | 0.12, above | 0.03, equivalent | 0.01, equivalent | 0.03, equivalent |
| Mean of free searches − reference | −0.06, equivalent | −0.01, equivalent | 0.01, equivalent | −0.00, equivalent |
| Reference − exact restoration | −0.13 [−0.16, −0.10], below | −0.02, equivalent | — | — |
| Enrichment p (B = 10 000) | 0.69 | 0.12 | 0.62 | 1.0 |
| No-task control p | 0.61 | 1.0 | 0.62 | 1.0 |
| Free searches' AUC | 0.49-0.50 | 0.49-0.55 | 0.47-0.51 | 0.49 |
| Free searches' Q, over the run (chance) | 0.04-0.16 (0.070) | 0-0.10 (0.011) | 0-0.18 (0.070) | 0-0.10 (0.011) |
| Outcome | excluded | functional success, anatomy undetermined | functional success, anatomy undetermined | functional success, anatomy undetermined |

**What the table shows:**
- **No anatomical enrichment was detected anywhere.** No enrichment p is below 0.12, and no sustained enrichment
  trajectory was apparent in Q. On PLNL, one true partner of ten is a Q of 0.10.
- **The functional comparison** is the mean of the five free searches against the mean of the refits. Single searches
  can fall further below: on MIP/URXL, `free-3` scores 1.71 against the refits' 1.83 (`full.json`).
- **Only MIP/URXL had anything to restore,** and it is excluded: its refits, handed the true partners, ended 0.13
  below exact restoration.
- **The other three "successes" are vacuous.** With no headroom above p, the deleted, reference and free states score
  alike, so "reached" says nothing. The design's outcome rule does not condition on headroom (D313).
- **Neither NIP target-brain had headroom above p under these refits.** NIP/URXL's headroom is small but positive,
  0.05 [0.03, 0.07]. These records do not show why. An optimum reached without X need not stay optimal once X adds
  parameters. Pilot-check's criterion 4 would have been 0 of 2 here.
- **The longer searches** showed no consistent improvement from generation 100 to 200: AUC 0.514 → 0.505 and
  0.490 → 0.497 on URXL, and 0.494 → 0.494 for both on PLNL. By PILOT-DEV §3's fixed reading, the budget stays.
- **The search's noise:** every proposed offspring minus its current state, on the same worlds, averaged −0.15 to
  −0.20 on MIP/URXL's free searches. The SDs were 0.36-0.42 (`full.json`, `paired_diff_sd_mean`). These spreads mix
  mutation effects with evaluation noise.
- **Swaps and turnover:**
  - the swap rates were 0.6-1.0 per neighbour pair in the 100-generation searches, and as low as 0.55 in the longer
    ones (`full.json`, `pair_rates`);
  - the partner turnover, about 0.9 per 10 generations, follows the coldest replica slot through those swaps, so it
    does not measure drift (D313's correction).

**The formal design's projection** (`report.json`): 43.8 GPU-hours with no cut, pilot-check's 10.3 included, against
66.9 left then.

## The bounded check (`search-check`; PILOT-DEV §7)

Both reviewers recommended a bounded check before any pilot-check (D313), and the owner chose it (D314). Its plan was
reviewed and merged (D315), and confirmed by both (D316). It ran once, on MIP/URXL only.

### Three search variants

Each variant ran 5 original-partner refits, 3 random-partner refits and 5 free searches (`summary.json`
`search_check.variants`).

**The rule, fixed before the run:**
- a variant is reliable if the lower bound of (refits − restoration), resampled over worlds and refits, is at least −p,
  and the refits' SD is at most p;
- a variant recovers if its enrichment p is below 0.05/3.

| | V4: one chain, the best offspring confirmed on 64 fresh worlds | V3: one chain, 64 worlds | V1: 3 offspring, 32 worlds |
|---|---|---|---|
| Refits − restoration [over worlds and refits] | −0.098 [−0.161, −0.042] | −0.141 [−0.222, −0.062] | −0.131 [−0.193, −0.068] |
| Refit SD [95%] | 0.062 [0.037, 0.179] | 0.094 [0.056, 0.269] | 0.067 [0.040, 0.193] |
| Reliable | no | no | no |
| Original-partner advantage | 0.03 [0.01, 0.04], equivalent | −0.00, equivalent | 0.13, above |
| Mean of free searches − refits | −0.01, equivalent | 0.06, equivalent | 0.00, equivalent |
| Enrichment p | 0.50 | 0.32 | 0.42 |
| Share of best offspring accepted (free searches) | 0.56-0.67 | 0.86-0.95 | 0.93-0.95 |

**Outcome (iii): no variant restores reliably.** By the rule, 03a stops here.
- **No recovery:** no variant recovers partners, reliable or not, and no type's own p is below 0.20.
- **The per-type null SDs** are similar across types, 0.04-0.05 for in, out and gap (`summary.json`,
  `per_type_null_sd`). A design-stage concern, that URXL's two gap partners would dominate the statistic's null, is
  not borne out by these rankings (Astra, D319).
- **No advantage above p under the single-chain variants:** the true partners' advantage over strata-matched random
  ones is within p. Under V4 it is small and positive.

### The per-edge lesion

Each of URXL's 45 true edges was removed from MIP's exact restoration, which scores 1.966 in this batch
(`summary.json` `search_check.lesion`).
- **Individual edges matter:** 19 single-edge removals cost more than p, and 25 have a lower bound above 0.
- **They are outgoing ones:**
  - the 10 largest drops are all outgoing edges and carry 74% of the positive drops;
  - the largest are 1.92, 1.90 and 1.83, so a single outgoing edge removed nearly zeroes the brain;
  - by type, 18 of 25 outgoing edges cost more than p, 1 of 18 incoming edges does, and neither gap edge does.
- **Far from additive:** the drops sum to 20.6, against the whole deletion's 1.78.
- **What it measures:** the evolved brain's marginal dependence on each edge at that one state, not the value of
  finding a partner during a search. Sorting and clipping noisy drops biases the apparent concentration upward
  (Astra).

### Re-scoring fixed states

From `full`'s final states `refit-0` and `free-0`, 16 independent sets of 8 offspring each were drawn. Each set was
scored on its own nested 16, 32 and 64 selection worlds, and on a common block of 1 024 reference worlds
(`summary.json` `search_check.reeval`). The reference is an estimate: a single gain's SE is about 0.016, and picking
the reference-best offspring is itself biased upward.

| From | Best offspring's reference gain | Average offspring's | Winner's reference gain at 16 / 32 / 64 worlds | Accepted winners that are worse |
|---|---|---|---|---|
| `refit-0` | 0.048 | −0.12 | −0.013 / −0.005 / −0.012 (SE about 0.017) | 50% / 50% / 62.5% |
| `free-0` | 0.007 | −0.17 | −0.030 / −0.019 / −0.006 | 81% / 86% / 69% |

**What it shows, at these two states:**
- Improvements estimated on the reference worlds are rare and small: the best of eight gains at most 0.05 on average.
- The acceptance rule took nearly every winner, and most accepted winners were not improvements on the reference.
- More selection worlds sharpened the ranking, but there was little left to rank. The rank correlation with the
  reference went from 0.47 to 0.72 from `refit-0`, and from 0.45 to 0.67 from `free-0`.

## What this shows, and what it does not

**Shown, on this graph and its one target-brain with headroom:**
- **The reference failed, so the outcomes could not be separated.** Refits handed the true partners stayed about 0.1
  below exact restoration under four search settings, pilot-dev's included.
- **The searches did not find URXL's partners.** No enrichment toward them was detected, although the evolved brain
  depends heavily on several of them. On average, free searches with other wiring matched the true partners' refits.
- **No NIP headroom:** neither NIP target-brain had headroom above p under these refits.

**Not shown:**
- **Anything about N2.** The graph is a shuffle, on which nothing task-shaped links X to its "true" partners except
  MIP's training (DESIGN §8).
- **That every feasible search would fail.** Outcome (iii) is a stop for budget reasons, after one bounded check that
  was not to be repeated or enlarged.
- **That identity cannot be inferred in principle.** The true partners do help a refit: the advantage is 0.12 under
  pilot-dev's setting and 0.13 under V1, though not above p under the single-chain variants. The searches did not
  find them.
- **Why the searches failed, completely.** Evaluation noise is a supported contributor at two states. Other causes,
  such as the mutation sizes or the landscape, were not tested.
- **Anything general:** one target-brain with headroom, one MIP brain, one graph.

## What 03a leaves for a later design

Found in pilot-dev, and not fixed, because 03a stopped. Each item is a candidate to investigate, not a demonstrated
need.
- **NIP headroom:** neither NIP target-brain had headroom above p. A design might try joint optimisation, a
  less-trained NIP brain, or another arm (D313).
- **The outcome rule:** "functional success" should require headroom present (Fable, D313).
- **The panel:** the deletion scan saturates at the ceiling. Ties should be reported, and broken by a rule that
  transfers between brains (D313).
- **The search:** improvements of a few hundredths of a target were below the selection noise at 16 to 64 worlds.
  Candidates are much larger evaluations, a different optimiser (one that uses gradients, or a surrogate), or smaller
  steps; each would need its own test and budget.
- **The statistic:** the design's recovery statistic (DESIGN §6) weights the three connection types equally. Whether
  that matters for a target with few partners of one type is open. In these rankings, the per-type null SDs were
  similar.
- **The probe:** the design's other probes (constant scent, jitter, hold, ramp) were not run, nor was a
  nonspecific-disruption control.

## Corrections

- **D313 corrected D312's first reading of the results.** D312 said:
  - that every stage ran on `f27d4c4`;
  - that the refits started "from zero";
  - that Q stayed "inside the chance range";
  - that turnover meant "the partner sets drift";
  - that the paired offspring-minus-current figures were "−0.14 to −0.20, with an SD of 0.32-0.42", where the −0.14
    and 0.32 came from a refit;
  - that the Jaccard agreement was everywhere near chance;
  - that the formal design "projects 43.8 GPU-hours", without saying that figure includes pilot-check.
- **D316** corrected a test claim in D315.
- **D318** corrected D317: "the free searches regained the score" became "matched the refits' score", which is below
  restoration.
- **D319** lists the corrections this page's review made before it was published.

## Reproduce it

Pilot-dev needs the connectome (`scripts/fetch_connectome.py`), CUDA, and the pinned environment (`requirements.txt`).
- **The summary,** without a GPU: `python scripts/e03a_summary.py` rebuilds `summary.json` from the committed
  records.
- **The run, from scratch:**
  - a clone already holds every stage's committed record, so each stage refuses to run again;
  - move the ten stage records (`setup.json` to `search-check.json` in `experiments/03a-self-consistency/pilot-dev/`)
    aside, keeping them to compare, then run `python scripts/e03a.py <stage>` for each stage in the order above;
  - the stages write their compute aggregate to `runs/e03a/pilot-dev/compute.json`. Copy it into `pilot-dev/` before
    rebuilding the summary (Fable);
  - with `--rerun --reason` instead, a stage renames its committed record to `<stage>.attemptN.json`, and `full`
    reuses the finished target-brains of the latest attempt rather than searching again. So a rerun is not a
    regeneration, and `search-check` then needs `full`'s saved states, which are local.
- **The CUDA preflight:** `python scripts/e03a.py <stage> --smoke --device cuda`.
- **The guards:** each stage refuses to run on an uncommitted guarded tree.
- **Exactness** is claimed only on the same GPU and pinned environment, with the same batch compositions, inside
  `replay_mode()` where the controls claim it (AGENTS.md rule 6).
- **Local only:** genomes and search states stay in `runs/e03a/` and are not committed.

## Record

- **Design and plan:** [`DESIGN.md`](DESIGN.md) v7.1; [`PILOT-DEV.md`](PILOT-DEV.md) v3.3 (§7 is the check).
- **Decisions:** D302-D319 in [`DECISIONS.md`](../../DECISIONS.md).
- **Reviews** (`docs/reviews/`):
  - the code: `20261017-03a-code`, `20261018-03a-code-r2`, `20261018-03a-code-r3`;
  - the results: `20261018-03a-pilot-dev-results`;
  - the check: `20261018-03a-search-check`, `20261018-03a-search-check-confirm`;
  - this page: `20261018-03a-results`.
