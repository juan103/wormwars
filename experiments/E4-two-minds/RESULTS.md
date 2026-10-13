# E4 / 04c, the main task: results (exploratory)

**What this is.** E4 asked whether two grafted navigation modules come to use information crossing between them,
through 32 optional cross-links, under evolution (`docs/E4/E4-DESIGN.md` v3).

- **Its main formal run was not run.** Both reviewers judged it poor value and recommended against spending its
  estimated 20 GPU-hours (D257). The owner re-scoped E4 to its diagnostic task, E4-D (D258).
- **Nothing of the main run was pre-registered,** so this is a recorded change of direction, not a broken
  registration.
- **Everything below is exploratory.** Each follow-up was chosen after the earlier results. Stage A's rules were fixed
  before stage A was played (`wormwars/e4/calibration.py`, committed at aee0194).

**The terms:**
- **X0 and X+:** the two arms, without and with the 32 mutable cross-links.
- **P1-cut:** the champions' loss when all cross-links are cut.
- **P2:** X+ against X0 after training.
- **R:** the runs per arm (design v3 §2).

**Compute:** 4.20 of E4's 30 GPU-hours (synchronised wall-clock hours on one RTX 5080), so 25.80 remain:
- the pilot's attempt 1: 3.01 (`compute-record.json`);
- the diagnostics: 0.36 (1 304 s), and a first run that failed at its last step: 0.26 (933 s; its partial output was
  not kept; D253);
- stage A: 0.57 (2 061 s; `compute-record-diagnostics.json` holds these three).

## 1. The pilot's attempt 1 (D250-D252)

**Set-up:**
- X0 and X+, 4 runs each, paired by run seed;
- starting from 32 copies of E-G; population 32, elites 3, truncation 8; 100 generations;
- T-F's mutation mask at factor 0.25 of (w 0.08, τ 0.15, bias 0.05);
- 8 training mazes per strain per generation; 6 × 6 island mazes; H = 1 800.

**What happened:** about 56 seconds per generation for 4 runs. The attempt reached its 3-hour cap in X+'s generation
80 (`pilot.json`). X0's 4 runs completed; X+'s training was in memory and is lost.

**X0's runs** (`pilot-attempt1-summary.json`, from the saved selection matrices; each figure is a strain's mean over its
generation's 8 training mazes):
- **Generation 0 and after:** generation 0's population (32 copies of E-G) averaged 6.23 visits per wey. Across runs,
  the population averaged 2.90 in generations 1-10 and 3.22 in 90-99. Single runs' generation means ranged from 1.49
  to 5.16 after generation 0.
- **Children against elites:** the children (excluding the 3 copied elites) averaged 2.52-2.77 per run in generations
  1-10 and 2.86-3.08 in 90-99; the elites averaged 5.50-5.91 and 5.46-5.96.
- **The best strain:** each generation's best strain averaged 6.3-6.7 per run in generations 0-9 and 6.2-6.9 in 90-99.
  This measure is affected by maze variation and by taking the maximum: E-G's per-maze SD is about 4 (4.31 on stage A's
  block, `headroom.json`).
- **On 64 validation mazes, after 100 scored generations, none of the four final X0 populations contained a strain
  with a higher mean than E-G** (E-G 7.63; the runs' best 6.16, 6.52, 7.08 and 6.68; `diagnostics.json`,
  `final_x0_validation`). E-G and the 128 strains played in one batch there.
- **The caveats:** the best of 32 is selected on the same mazes, so even these are optimistic. No independent
  post-selection test or completed X+ comparison exists. This shows neither that evolution did not move nor that longer
  training would fail.

**The generation-1 load** (`pilot.json`): X0's population bred once from E-G averaged 1.94. X+ cost a further 0.21 at
cross-link factor 0.25, rising to 1.14 at 4.0. The 6.23 above and this 1.94 came from different mazes, so they are not
a paired loss (Astra, D253-D254). This increment was measured on an already impaired population; stage A (§3) used
other masks, seeds and mazes.

## 2. The diagnostics (D253-D254; `diagnostics.json`)

Generation 1, **children only**, paired on the same 8 mazes and 4 generator seeds:

| condition | children's mean (visits per wey) |
|---|---|
| E-G, unbred | 4.03 |
| bred with every scale at 0 | 4.03 (the zero-mutation control matched E-G's scores) |
| X0's mask at 0.25 / 0.10 / 0.05 | 1.97 / 3.11 / 3.60 |
| weights only, at 0.25 | 4.14 |
| τ only | 4.16 |
| the gated comparator → motor edges only | 4.13 |
| one parameter per child, on average | 4.04 |
| **biases only** | **1.98** |
| module A only / module B only | 2.80 / 2.81 |

- **On this block, bias-only mutation reproduced nearly all the loss.** The biases are those of the module's 8
  neurons, and a bias step of σ 0.0125 was enough.
- **The load also occurred without the gate and on tree mazes:**
  - the ungated seed E + W2 lost 1.66 on the same mazes (3.66 → 2.00 at 0.25), against E-G's 2.06;
  - on 5 × 5 tree mazes at H = 2 400, both organisms lost about a third (E-G 6.59 → 4.38; E + W2 6.52 → 4.34).
- **The losses depend on the block.** E-G makes 4.03 on these 8 mazes, 7.63 on the 64 validation mazes, and 7.97 on
  stage A's block. Weights and τ cost nothing here but 7% on stage A's block.

## 3. Stage A, the calibration (D255-D257; `calibration.json`)

Generation 1, children only, paired on a fresh block A of 16 mazes (E-G 7.97 there), with 4 generator seeds. "At or
above 5" is the share of children whose mean over the block's mazes reaches 5 visits.

**The comparisons across compositions are not exact** (Astra). E-G played alone; the children played as 116 strains ×
16 mazes × 8 weys. Their exact comparison across these batch compositions was not validated (rule 6), and "all links
cut = E-G" describes the genome, not a separately measured control at the children's composition.

**The biases:**
- **The split at 0.25:** nose biases alone 3.38 (at or above 5: 28%), comparator biases alone 6.86 (97%). The nose
  biases cost more, in the predicted direction. The observed ratio of losses is about 4, against about 3 predicted
  from the gains Fable computed (18 from a nose bias to a turn neuron, 6 from a comparator bias; D255).
- **The ladder** (weights and τ at 0.25): the biases at 0.05, 0.02, 0.01, 0.005 and frozen gave 6.72, 7.20, 7.40, 7.41
  and 7.40 (at or above 5: 99% at 0.05, 100% below).
- **The declared rule** needed both:
  - the children keep 95% of unmutated E-G;
  - they are within 0.25 visits of the frozen-bias children.

  No factor qualified. The frozen-bias children kept only 93% of E-G, through weights' and τ's own load. Block B's
  confirmation tested the frozen-bias children only, and failed too (94%). The incremental criterion alone would
  choose 0.02; that choice is unconfirmed.

**The cross-links** (biases frozen; X0's children 7.40):
- **The ladder:** X+'s children gave 4.53, 3.09, 2.08, 1.11 and 0.64 at cross-link factors 0.25, 0.5, 1, 2 and 4. At
  or above 5: 42%, 16%, 6%, 0% and 0%.
- **The bound:** every tested factor, 0.25-4.0, on block A, failed it, which allows a loss of at most
  min(0.25 visits, 0.05 × X0's mean).
- **What it does not cover:** the cross-link results rest on block A alone. The 4 seeds replicate mutations, not
  mazes.

**What the cost is,** with only the 32 slots mutated and every inherited parameter frozen:

| | factor 0.25 | factor 1.0 |
|---|---|---|
| intact | 4.58 (41%) | 2.07 (5%) |
| mean-substituted: the links' constant part kept, their fluctuation cut | 5.33 (66%) | 1.93 (14%) |
| centred: the constant part removed, the fluctuation kept | 4.98 (50%) | 1.49 (5%) |
| the nose-origin links cut | 6.25 (80%) | 3.81 (41%) |
| the comparator-origin links cut | 4.98 (47%) | 2.05 (4%) |

The figures in brackets are the shares at or above 5. All links cut is E-G, 7.97.

- **The largest rescue among the tested interventions** came from cutting the nose-origin links: about half of the
  loss at 0.25 (1.67 of 3.38) and under a third at 1.0 (1.74 of 5.90). Cutting the comparator-origin links improved
  the mean by 0.39 at factor 0.25 and reduced it by 0.01 at 1.0.
- **How the conditions were built:** the mean substitution and the centring used each child's source means from a
  separate block C of 8 mazes. The conditions are interventions, not an additive decomposition of the loss.
- **The mechanism is unresolved** (Astra; a correction to D256's first reading, D257). The nose-origin cut removes the
  nose-origin links of both modules, into both modules' noses and comparators. The noses read trails as well as scent.
- **Two readings, not results** (Fable, D257):
  - the loss is mostly the share of children that break;
  - B's own scent is out of range (9 grid cells) for most of a B-leg, so B's comparators may steer on a small input.
    The link weights of about 0.01-0.02 at which a cross-link would carry a useful signal are of the same size as the
    random steps that already cost here. A link small enough to pass the load bound would then be too small to drift
    into usefulness. That is Fable's extrapolation; no smaller factor, and no evolution at one, was tested.

## 4. Headroom (D259; `headroom.json`, CPU)

- **On stage A's block:** E-G 7.12, the scripted follower 11.29 (shared trails) and 3.20 (none), the oracle 32.98. E-G
  reaches 22% of the oracle, so navigation has headroom. Whether anything A holds could use it is not shown.
- **E-G's two figures:** 7.12 here and 7.97 in stage A come from the same genome on the same mazes, on the CPU and the
  GPU. The rollout is chaotic and is not reproduced across devices (D082).
- **The record** was written from a working tree with uncommitted changes (`provenance.dirty`), before its script was
  committed with it (b27ed26).

## 5. What E4's main task can and cannot say

- **It can say:**
  - E-G's comparator modules are mutationally fragile;
  - at T-F's mutation strength, the population sat far below E-G, and after 100 generations no final strain beat E-G
    on 64 validation mazes;
  - random cross-links cost heavily at every tested factor, 0.25-4.0, on one block;
  - the cost cannot be attributed to one mechanism from these tests.
- **It cannot say:** that evolved sharing could not help, or that the modules hold nothing useful for each other.
  Random perturbations can harm a circuit even where selected connections would help (both reviewers, D257).
- **Why the formal run was dropped** (D257):
  - **Fable's extrapolation:** at any cross-link size that passes the load bound, recruitment by drift is implausible.
    P1-cut would then likely read "equivalent", and P2 "unclear" at R = 8.
  - **Astra's judgement:** a null would mostly be inconclusive.
  - **What E4-D offers instead:** transfer is necessary by construction there, and X0's share of real-first entries
    is exactly one half among trials that end in an entry, under paired assignments. Over all trials, trials without
    an entry lower it.

## Contributions

- **Astra:**
  - the paired-block correction (6.23 against 1.94);
  - the zero-mutation control and the weaker-factor screen;
  - the composition and block caveats;
  - the correction of D256's mechanism.
- **Fable:**
  - the bias split and its predicted ratio;
  - the class-wise diagnostics and the arena 2 × 2;
  - the headroom check and the share-of-children reporting;
  - the reading on scent range.
- **Both:**
  - the calibration rules (D255);
  - the re-scoping recommendation (D257).
- **The owner** decided the re-scoping and E4-D's budget (D258).

## Corrections

- **D256's first reading.** D256 (2026-10-13) read stage A as "cross-talk from A's noses" and "mostly harmful
  cross-talk"; both overreached. D257 corrects them and quotes them.
- **Mis-rounded figures** (D263, dated corrections):
  - D252 gave the best strain's late range as 6.3-6.9; it is 6.2-6.9;
  - D254 gave module B alone as 2.80; it is 2.81;
  - D256 gave the bias factor 0.05 as 6.73; it is 6.72;
  - D256 gave the nose-origin cut at 0.25 as 6.26; it is 6.25.
- **D258's figures for the budget.** "About 4.4 GPU-hours" spent and "25.6" remaining were estimates from the reviews;
  the records give 4.20 and 25.80.
