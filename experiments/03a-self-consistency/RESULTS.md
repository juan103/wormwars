# 03a: the self-consistency proof of concept. Results (exploratory)

**Exploratory.** 03a stopped before its pre-registration. Nothing here is a registered test, and nothing was run on
N2.

What ran is pilot-dev, the development stage on one shuffled graph (DESIGN.md v7.1 §8), followed by a bounded check of
the search that both reviewers recommended and the owner chose (PILOT-DEV.md §7). The check's rule was fixed before
it ran, and its outcome (iii) ends 03a (D317).

**Where the numbers come from:**
- `scripts/e03a_summary.py` reads the committed stage records in [`pilot-dev/`](pilot-dev/) and writes them to
  [`summary.json`](summary.json);
- each number below is from that file, or from the record named beside it.

## In one paragraph

The search could not test the hypothesis on this graph. A neuron, URXL, was deleted from an evolved brain and its
wiring alone was searched for the task.
- **Free searches** reached the same score as refits handed the true partners, every time, with partners at
  chance.
- **Refits** handed the true partners did not regain the restored brain's score reliably. The shortfall was 0.10 to
  0.14 targets, against a margin of 0.098, and it persisted under three changes to the search.
- **Why:** at the states the searches reached, offspring that truly improved were rare and small, so acceptance
  mostly followed evaluation noise.
- **The brain's dependence on URXL:** removing a single outgoing edge of URXL from the evolved brain could cut its
  score from 1.97 to 0.05. Yet free searches with other wiring scored as well as the true partners' refits.
- **NIP:** the brains evolved without the neuron had no use for it at all.
- **The limits:** this was one target-brain on one shuffled graph. It shows that this search procedure, at this budget,
  could not do the job. It does not show that the hypothesis fails on N2.

## What ran

Pilot-dev ran on the SH-mirror graph with seed 3 403 000, rebuilt from its seed and checked by hash; the graph is never
saved. Each stage's record and commit (`summary.json` `stages`):

| Stage | Commit | Wall hours | What it did |
|---|---|---|---|
| setup | `a5760c4` | 0.01 | the graph, its hash and the motor gains |
| evolve-intact | `a5760c4` | 0.74 | the selector brain and the MIP brain, 1 000 generations |
| panel | `1b0531a` | 0.03 | the deletion scan on the selector brain, the tiers, the two targets |
| evolve-nip | `1b0531a` | 0.67 | one NIP brain per target, X's edges pinned at zero |
| baseline | `1b0531a` | 0.02 | intact, deleted and restored scores, with the exactness controls |
| probe | `1b0531a` | 0.09 | the bounded-history probe on the calibrators and the evolved brains |
| tune | `f27d4c4` | 1.55 | the search's settings, three rounds |
| full | `f27d4c4` | 1.46 | every search of the four target-brains, with the diagnostics |
| report | `f27d4c4` | 0 | throughputs and the formal projection |
| search-check | `4d6e887` | 0.73 | the bounded check (PILOT-DEV §7) |

**Compute:**
- Pilot-dev measured 5.29 GPU-hours (`pilot-dev/compute.json`), plus 0.03 for the CUDA preflight (D317), against its
  cap of 6.
- 03a has spent 5.84 of its 72 hours, the 0.53 of exploratory checks included (D303, D304). The other 66 are not
  spent.
- **Reviews:**
  - the code was reviewed in three rounds (D308-D311). `setup` and `evolve-intact` ran while round 2 was under review,
    and `panel` to `probe` while round 3 was. None of them depends on what those rounds changed (PILOT-DEV status);
  - the results were reviewed once (D313), and the check's plan twice (D315, D316).

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
| NIP/PLNL | 2.17 | 0.24 | 1.17 | 0.74 | 2.10 |
| KT, no memory | 1.16 | 1.16 | 1.16 | 1.16 | 1.16 |
| KTM, one tick | 2.88 | 2.88 | 2.88 | 2.88 | 2.88 |
| KTS, T = 10 | 2.19 | 2.38 | 2.35 | 2.19 | 2.19 |

- **The evolved brains depend on neural state older than the window.** At L = 50, the reading least confounded by slow
  neurons (τ runs to 20 ticks), the MIP brain loses 0.38 and the selector 0.27. The NIP brains lose 0.20 and 0.07.
- **What a loss does and does not mean:** as DESIGN §8 states, a loss includes filtering by slow neurons and any
  rhythm the reset disturbs. It is not uniquely useful sensory memory.
- **The slow-memory calibrators** (KTS) moved little and in both directions, which the design allowed ("no sign
  required").
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

The final states were scored on 2 048 worlds, and every comparison is against the margin p
(`summary.json` `full`):

| | MIP/URXL | MIP/PLNL | NIP/URXL | NIP/PLNL |
|---|---|---|---|---|
| Headroom (reference − deleted) | 1.65, above | −0.01, equivalent | 0.05, equivalent | 0.01, equivalent |
| Original-partner advantage | 0.12, above | 0.03, equivalent | 0.01, equivalent | 0.03, equivalent |
| Free searches − reference | −0.06, equivalent | −0.01, equivalent | 0.01, equivalent | −0.00, equivalent |
| Reference − exact restoration | −0.13 [−0.16, −0.10], below | −0.02, equivalent | — | — |
| Enrichment p (B = 10 000) | 0.69 | 0.12 | 0.62 | 1.0 |
| No-task control p | 0.61 | 1.0 | 0.62 | 1.0 |
| Free searches' AUC | 0.49-0.50 | 0.49-0.55 | 0.47-0.51 | 0.49 |
| Outcome | excluded | functional success, anatomy undetermined | functional success, anatomy undetermined | functional success, anatomy undetermined |

**What the table shows:**
- **No anatomical signal anywhere.** No enrichment p is below 0.12. Each free search's Q stayed near its chance level
  (0.070 for URXL, 0.011 for PLNL).
- **Only MIP/URXL had anything to restore,** and it is excluded: its refits, handed the true partners, ended 0.13 below
  exact restoration.
- **The other three "successes" are vacuous.** With no headroom, the deleted, reference and free states score alike,
  so "reached" says nothing. The design's outcome rule does not condition on headroom (D313).
- **The NIP brains had no use for the neuron.** A brain evolved without X reached its optimum without it, so a search
  over X alone has nothing to gain. That is a property of the arm, and N2 would share it. Pilot-check's criterion 4
  would have been 0 of 2 here.
- **Longer searches:** the four 200-generation searches gained no AUC from generation 100 to 200 (0.514 → 0.505 and
  0.490 → 0.497 on URXL; 0.494 → 0.494 for both on PLNL). By PILOT-DEV §3's fixed reading, the budget stays.
- **The search's noise:** every proposed offspring minus its current state, on the same worlds, averaged −0.15 to
  −0.20 on MIP/URXL's free searches. The SDs were 0.36-0.42.
- **Swaps and turnover:** the swap rates were 0.6-1.0 per neighbour pair. The partner turnover, about 0.9 per 10
  generations, follows the coldest replica slot through those swaps, so it does not measure drift (D313's correction).

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
| Original-partner advantage | 0.03, equivalent | −0.00, equivalent | 0.13, above |
| Free searches − refits | −0.01, equivalent | 0.06, equivalent | 0.00, equivalent |
| Enrichment p | 0.50 | 0.32 | 0.42 |
| Share of best offspring accepted (free searches) | 0.56-0.67 | 0.86-0.95 | 0.93-0.95 |

**Outcome (iii): no variant restores reliably.** By the rule, 03a stops here.
- No variant recovers partners, reliable or not. No type's own p is below 0.20.
- Under the two single-chain variants, the true partners no longer beat strata-matched random ones after refitting.

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
scored on its own nested 16, 32 and 64 selection worlds, and on a common block of 1 024 reference worlds, itself an
estimate (`summary.json` `search_check.reeval`).

| From | Best offspring's reference gain | Average offspring's | Winner's reference gain at 16 / 32 / 64 worlds | Accepted winners that are worse |
|---|---|---|---|---|
| `refit-0` | 0.048 | −0.12 | −0.013 / −0.005 / −0.012 (SE about 0.017) | 50% / 50% / 62.5% |
| `free-0` | 0.007 | −0.17 | −0.030 / −0.019 / −0.006 | 81% / 86% / 69% |

**What it shows:**
- From both states, true improvements are rare and small: the best of eight gains at most 0.05 on average.
- The acceptance rule took nearly every winner, and most accepted winners were not improvements.
- More selection worlds sharpened the ranking (rank correlation with the reference 0.47 → 0.72 from `refit-0`, and
  0.45 → 0.67 from `free-0`), but there was little left to rank.

## What this shows, and what it does not

**Shown, on this graph and target-brain:**
- The search could not separate the design's outcomes, because its reference failed: refits handed the true partners
  stayed about 0.1 below exact restoration under four search settings, pilot-dev's included.
- The task did not lead the searches back to URXL's partners, although the evolved brain depends heavily on several of
  them. Free searches with other wiring scored as well as the true partners' refits.
- The design's NIP arm cannot produce headroom when the NIP brain is evolved to an optimum without X.

**Not shown:**
- **Anything about N2.** The graph is a shuffle, on which nothing task-shaped links X to its "true" partners except
  MIP's training (DESIGN §8).
- **That every feasible search would fail.** Outcome (iii) is a stop for budget reasons, after one bounded check that
  was not to be repeated or enlarged.
- **That identity cannot be inferred in principle.** The original-partner advantage of 0.12 under pilot-dev's setting
  shows the true partners do help a refit. The searches could not find them.
- **Anything general:** this is one target-brain, one MIP brain and one graph.

## What 03a leaves for a later design

Found in pilot-dev, and not fixed, because 03a stopped:
- **NIP headroom:** a NIP brain evolved to an optimum without X leaves X nothing to add. A design would need joint
  optimisation, a less-trained NIP brain, or another arm (D313).
- **The outcome rule:** "functional success" should require headroom present (Fable, D313).
- **The panel:** the deletion scan saturates at the ceiling. Ties should be reported, and broken by a rule that
  transfers between brains (D313).
- **The search's evaluation:** at 16 to 64 worlds per score, improvements of a few hundredths of a target are below
  the selection noise. A search that can climb back to restoration needs much larger evaluations, a different
  optimiser (one that uses gradients, or a surrogate), or smaller steps. Its cost would need a new budget.
- **The statistic:** the registered recovery statistic weights the three connection types equally. On URXL, its two
  gap partners carry most of the null's variance (Fable, D315).
- **The probe:** the design's other probes (constant scent, jitter, hold, ramp) were not run.

## Corrections

D313 corrected D312's first reading of the results. D312 said:
- that every stage ran on `f27d4c4`;
- that the refits started "from zero";
- that Q stayed "inside the chance range";
- that turnover meant "the partner sets drift";
- that the Jaccard agreement was everywhere near chance;
- that the formal design "projects 43.8 GPU-hours", without saying that figure includes pilot-check.

D316 corrected a test claim in D315.

## Reproduce it

Pilot-dev needs the connectome (`scripts/fetch_connectome.py`), CUDA, and the pinned environment (`requirements.txt`).
- **The stages:** `python scripts/e03a.py <stage>` for each stage in the order above. Each refuses to run on an
  uncommitted guarded tree, and refuses a rerun without `--rerun --reason`.
- **The CUDA preflight:** `python scripts/e03a.py <stage> --smoke --device cuda`.
- **The summary:** `python scripts/e03a_summary.py` rebuilds `summary.json` from the committed records, on the CPU.
- **Exactness** is claimed only on the same GPU and pinned environment, with the same batch compositions, inside
  `replay_mode()` where the controls claim it (AGENTS.md rule 6).
- **Local only:** genomes and search states stay in `runs/e03a/` and are not committed.

## Record

- **Design and plan:** [`DESIGN.md`](DESIGN.md) v7.1; [`PILOT-DEV.md`](PILOT-DEV.md) v3.3 (§7 is the check).
- **Decisions:** D302-D317 in [`DECISIONS.md`](../../DECISIONS.md).
- **Reviews** (`docs/reviews/`):
  - the code: `20261017-03a-code`, `20261018-03a-code-r2`, `20261018-03a-code-r3`;
  - the results: `20261018-03a-pilot-dev-results`;
  - the check: `20261018-03a-search-check`, `20261018-03a-search-check-confirm`.
