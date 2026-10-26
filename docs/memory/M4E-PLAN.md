# M4e: what does a dense block carry? — the plan

*Draft 4, 2026-10-26, after three rounds of review of the plan and its code (Astra 6 and Fable 5.1: both "revise" in
round 1; in round 2 Fable "agree" with text fixes and Astra "revise"; in round 3 both "agree", with minor items taken
here; every finding taken; drafts 1 to 3 and the reviews are archived in [`docs/reviews/20261026-m4e-plan/`](../reviews/20261026-m4e-plan/)).
Exploratory: nothing here is a pre-registration, but the hosts, the arms, the genomes, the
outcome, the second classification pass and the readings are fixed here before any arm runs. The owner's second item
after M4d (D365, which quotes them: "A study of what a dense block carries, its size, weights and degrees"). The design
was agreed in two rounds with Astra 6 and Fable 5.1 before this draft (archived in
[`docs/reviews/20261025-dense-block-design/`](../reviews/20261025-dense-block-design/)): Astra's factorial, Fable's
dose direction and stage 0, and both reviewers' second classification pass. D364 said "do not draft M4e" for M4d's
smaller-block second stage; that stage stays undrafted, and the name is reused for the owner's study (Astra). CPU
only.*

## The question

M4d put N2's head-core block (C3's 30×30 chemical submatrix) into ten fresh null hosts. Over every assignment of the
unresolved genomes, the transplant (T), its rewired copies at N2's degrees (R) and N2's edges and weights at random
positions (D) all raised the share of genomes holding the history in two stable states over the intact host (I)
([`M4D-RESULTS.md`](M4D-RESULTS.md)). But every one of those blocks changed the edge count, the total weight, the
weight distribution and the topology at once, so M4d cannot say which of them does it.

**M4e asks, on the same 30 head neurons:** does spreading a fixed amount of connection weight over more edges change
how often two food histories reach different stable states, and how does that compare with adding weight, with N2's
uneven weights, and with N2's labelled degrees? It studies edge density at a fixed set of neurons, not block size in
neurons, and the whole embedded network's response, not a block that stores anything alone (Astra).

**The joining observation, with its limits** (Fable, Astra). Let M be a block's magnitudes as the brain sees them
(below), S1 = ΣM and S2 = ΣM² over the off-diagonal edges, and S3 the square root of the spectral radius of M∘M. At
fixed total weight, S2 = S1²/E falls exactly as the edge count E rises; S3 usually falls but need not for every
support draw. So the count contrast at fixed weight (Δ_count, below) is a prospective test of a summary model: if the
rate follows S1, Δ_count ≈ 0; if it rises with S2 or S3, Δ_count < 0 (fewer, heavier edges switch more); if edges per
se matter, Δ_count > 0. That assumes the rate rises monotonically with the summary, which it need not: stronger
coupling can produce unsettled dynamics instead (Astra). None of the summaries is a mechanism: the brain's stability
also depends on saturation, gaps, leak and time constants.

## Stage 0: background, after the data, choosing nothing

Computed on M4d's records before this draft ([`m4e_stage0.py`](../../scripts/memory_m4/m4e_stage0.py);
`runs/memory-m4e/stage0.json`; Fable's round-1 proposal). Every M4d block arm has S1 = 83.04 and S2 = 70.91, the same
by construction; S3 varies with the draw (R 1.28 to 1.79, T 1.71, I 0.32 to 0.75). Per genome, the largest real part
of the signed block's eigenvalues separates separate-states genomes from the rest with an AUC of 0.76 pooled over
M4d's arms (0.68 to 0.81 within block arms; 0.49 in I, with 4 switches); 4 of 10,984 genomes below 0.8 switch,
against 213 of 30,764 above 1.2. Across M4d's 50 block arms (D, R, Rr, P, T), S3 and the switch count correlate at
Spearman +0.42 (+0.28 without T). N2's block has a higher S3 than its R copy in 9 of the 10 hosts
(`hosts_T_S3_above_R`), so part of M4d's T − R may be a built-in coupling difference (Fable). Every number here is in
`stage0.json`. All of it is after the data and fixes nothing below.

## The hosts

**Ten fresh hosts, two per ensemble** (SH, SH-route, SH-class, SH-mirror, SH-recip), each built by 03's sampler
(`wormwars.exp03.samplers.build`, unchanged) from seed **03mc's seed base + 1100 + i** (i = 0, 1), checked as M4d
checked its hosts against every committed `ensembles.json` and `graphs_content_manifest.json`, and also against M4d's
ten hosts (`runs/memory-m4d/hosts.json`); a used name or content, or a `SamplerFailure`, moves that host to the seed
two further on, recorded. Fresh hosts rather than M4d's (both reviewers): M4d's hosts produced the R > D observation
that motivated this study, so testing on them would be partly circular. **Hosts are the unit.**

**Two independent block draws per host** (d = 0, 1), each with **512 fresh genomes**, so 1024 genomes per host and
arm (Astra): the draws sample the construction's variation, which M4d had once per host (P ranged from 1 to 19
switches across hosts). The two draws are averaged within the host before the host-level analysis; both are reported.

## The arms (fixed here)

The **block** is C3's 30×30 chemical submatrix. Every arm but I removes the host's off-diagonal block edges and puts
new ones in their place; everything outside the block (boundary edges, exterior, the whole gap layer) stays the
host's. **The diagonal (autapses) stays the host's in every arm but T** (Astra): N2's eight C3 autapses scale to at
most 0.39, far below the isolated-neuron threshold of 1 (Fable), so they get no arm; T carries N2's as a package.

Let E_h and S_h be host h's own off-diagonal block edge count and summed anatomical weight (94 to 127 edges and 466
to 861 on M4d's hosts), E = 260 and S = 2347 N2's.

| Arm | Off-diagonal block (per host and draw) | Its job |
|---|---|---|
| **I** | the host's own | baseline |
| **U_LL** | E_h edges at uniformly random positions, each of weight S_h / E_h | the low corner; U_LL − I is the construction check (equal-magnitude random wiring against the host's own) |
| **U_LH** | U_LL's positions, each of weight S / E_h | weight raised at the host's count |
| **U_HL** | 260 random positions, each of weight S_h / 260 | count raised at the host's weight |
| **U_HH** | U_HL's positions, each of weight S / 260 | both raised: N2's count and total weight, equal magnitudes |
| **W** | U_HH's positions, N2's 260 block weights shuffled onto them | N2's uneven weights at fixed support and total |
| **K** | N2's 260 edges rewired at N2's labelled in- and out-degrees (M4d's double-edge swaps, 20 accepted per edge), then N2's 260 weights shuffled over them; reciprocal pairs brought within 2 of W's count by further swaps accepted only when they move the count toward it | N2's labelled degrees, with exchangeable weights |
| **T** | N2's block exactly, its autapses included | M4d's package, replicated on fresh hosts |
| **U_HX** (conditional, below) | U_HH's positions, each of weight 2S / 260 | a third weight level: the dose direction |

**Construction:**
- U_LL's positions are a uniformly drawn subset of U_HL's 260 (Astra), so the low-count supports are nested in the
  high-count ones and pair better; U_LH shares U_LL's, U_HH, W and U_HX share U_HL's.
- Each draw's generator is `default_rng(20261301 + 10 × (2h + d) + arm index)` (20261301 to 20261499); one record per
  host and draw in `runs/memory-m4e/blocks.json` (local: W, K and T carry N2's block weights; rule 1), with a committed
  summary and its sha256 written by [`m4e_tables.py`](../../scripts/memory_m4/m4e_tables.py), which stops if the local
  file differs from the committed summary's digest. The seed families do not overlap (Fable): blocks 20261301 to
  20261499, signs 20261511 to 20261530, the reader 20261541 to 20261543, audits 20261601 + 100 (2h + d) + arm index; a
  smoke shifts the blocks, signs and audits by 900,000.
- K's reciprocal matching: at most 200 × 260 further attempts; if the count is not within 2 of W's, the achieved
  count is recorded and K is used unmatched (fixed now; Fable). K − W is read conditionally on the achieved matching
  (Astra), and the block check compares K's recorded target with W's count.
- Achieved magnitudes are checked after `Genome.clamp_`: no arm's largest magnitude reaches `w_max` (U_HX's per-edge
  weight is about 18 anatomical units, T's heaviest 57; Fable computed about 0.64 and 2.0 against 3.0); a clamped
  entry stops the run.

**U_HX is conditional** (Fable keep, Astra drop): it runs only if the smoke benchmark projects the whole protocol,
first pass and second pass, with U_HX included, under 40 of the 48 cap hours. The decision is recorded in this file,
dated, after the smoke and before any formal arm; with U_HX out, every U_HX item below is dropped.

*Decided 2026-10-26, after the smoke and before any formal arm: **U_HX is out.** On the smoke host (128 genomes), U_HX
left 7 genomes unresolved after both passes and took 1139 s against 137 to 282 s for the other arms; at 512 genomes per
draw its 20 panels project to about 25 hours, so the whole protocol with it to about 54, above the 40-hour limit. The
U_HX items below stay in the text and are not run (`m4e.INCLUDE_UHX` is False). Its 7 of 128 genomes left unresolved
at twice N2's weight are the unsettled regime that stronger coupling can bring (Astra's caution, above).*

## The genomes: paired across arms

As in M4d ([`M4D-PLAN.md`](M4D-PLAN.md), "The genomes"): per host and draw, one panel of 512 genomes on the intact
host (`Genome.random`, seed **8101 + 2h + d**; the 81xx seeds are unused in the repository), and every arm's genome
built from it by `m4d.paired_genome`: outside the block every signed weight, τ, bias and g as the intact genome's; a
block edge gets `init_w_scale` × its anatomical weight / the intact spec's `chem_anat.mean()`, with its sign from one
30×30 sign matrix per genome shared by every arm (the intact genome's sign wherever the host has a block edge, a fresh
draw elsewhere: `default_rng(20261511 + 2h + d)`). The sham (the host's own block through the construction) must
equal `Genome.random` bit for bit, checked on every host and draw.

## The outcome

Each genome is classified by M2's frozen classifier (`pilot.probe_states`, `pilot.full_classify`, 2000 ticks, roots
in float64), with no eligibility floor, as in M4d. **p_ha** is the share of host h's 1024 genomes (both draws) in arm a
classified **separate states** (both subclasses). Also recorded per genome, as in M4d: the write measures and the
read-out difference.

### The second pass (fixed here)

M4d's reading turned on 86 unresolved genomes, and the commonest failure, the unconfirmed candidate, is a history that
has not settled. So:
- **Who:** in every arm, every genome classified separate states, persistent oscillation or unresolved by the first
  pass, and an **audit sample**: 40 genome ids per host, draw and arm drawn before the run
  (`default_rng(20261601 + 100 × (2h + d) + arm index)`), about 800 per arm, of which those classified fading are
  audited. Draft 1 had 8 per panel; Astra showed that about 160 fading genomes per arm, with zero transitions, bound an
  arm's transition rate only below 1.85%, against effects of 0.1% to 0.4%, and that ruling out 0.4% needs about 748
  per arm. The batched continuation makes the larger audit cheap (about 4 to 5 more hours in all, by the smokes' cost per audited genome; Fable).
- **What:** each history's float32 hold is continued from its tick-2000 state, kept in memory from the first pass,
  for 20,000 more ticks (a hold of 22,000), recording the last 200 ticks as the first pass records ticks 1801 to 2000.
  The genome is then classified by the same rules from its tick-22,000 state, with the write amplitude a and the
  tick-30 and tick-300 read-out differences of the first pass kept. The classifier's own float64 continuations and
  their 20,000-tick cap are unchanged; the oscillation check's recurrence rerun records ticks 21,801 to 22,000 of a
  float32 run continued from the same tick-2000 state; it starts from the batched continuation's tick-21,800 state,
  which gives the same substeps as a rerun from tick 2000 because the float32 hold is deterministic (a test; on the
  smoke both ways gave identical classes and reasons for every second-pass genome, and the per-genome cost of an
  unresolved genome fell from about 130 s to 75 s). This needs two optional parameters in `pilot.full_classify` and
  `pilot.oscillation_check` (the length of the follow and the first recorded tick), whose defaults leave the frozen
  2000-tick path unchanged (a test of the defaults), and a test that continuing from the tick-2000 state reproduces a
  longer probe bit for bit.
- **The check:** if any audited genome classified fading by the first pass is separate states after the second, the
  second pass is reported and not used. Only that transition suspends it (Fable's 1% rule for any change is not
  adopted: a separate-states or unresolved genome changing class is what the pass is for). Every transition is
  tabulated per arm. **Why zero is expected, and what the audit can show:** a genome is classed fading only when both
  histories are shown to reach the same located stable root (a finite float64 continuation against the linear
  forecast, with numerical thresholds), so a later separation of the float32 hold is not expected. That is an
  expectation, not a guarantee (Astra). The audit tests it arm by arm; the reader reports each arm's actual number of
  audited fading genomes (`audited_fading_per_arm`), about 750 to 800 depending on how many audited ids are not
  fading. With 800 and no transition, an arm's transition rate is bounded below about 0.0037 (one-sided 95%), with 756
  below about 0.0040: enough at the 0.004 margin at best, not at the 0.001 benchmark (Fable, Astra), a limit stated
  beside the reading together with the first-pass comparison.
- **The reading's classes:** the second pass's for every genome it covered, the first pass's for the rest, unless the
  check fails; then the first pass's for all. Genomes still unresolved count as not separate states, and bound the
  reading by M4d's conservative envelope (below). **Not settled** (persistent oscillation plus unresolved) is a
  secondary outcome per arm. The same primary contrasts on the first pass's classes alone, with their envelope, are
  reported beside the reading (Astra).

## The readings (fixed here)

**Primary contrasts (two):**
- **Δ_weight** = mean over hosts of (p_h,U_HH − p_h,U_HL): weight raised at N2's count;
- **Δ_count** = mean over hosts of (p_h,U_HH − p_h,U_LH): the same total weight spread over 260 edges instead of the
  host's own count.

Each with a **95% interval**, the hull of the host bootstrap (2000 resamples of the ten hosts, `default_rng(20261541)`,
2.5th and 97.5th percentiles) and the Student-t interval on the ten host differences (9 degrees of freedom); by
Bonferroni over the two, 90% jointly, M4d's level (Fable; Astra noted 97.5% each would give 95% jointly). Genomes are
not resampled again.

**Two fields per contrast** (both reviewers):
- **Direction:** "raises" if the lower bound is above 0; "lowers" if the upper bound is below 0; otherwise "direction
  unresolved".
- **Size:** "at least 0.001" if the lower bound is above 0.001 (or the upper below −0.001); "no effect of 0.004 or
  more, as a mean across these ten hosts (a response confined to a minority of host graphs may be missed)" if the
  interval lies inside (−0.004, 0.004); otherwise "size unresolved". Both can hold at once. On the envelope (below), a
  size sub-field that holds on both the interval and the envelope stands; only when none does is the field
  "unresolved (the unresolved genomes decide it)" (Fable).

0.001 is Astra's benchmark for a meaningful effect (one more switching genome per thousand), a scientific choice, not
derived from the base rate; 0.004 is M4d's margin, kept for exclusions. **Precision:** at M4d's rates a contrast's
half-width is about 0.0012 to 0.0025, so contrasts below about 0.003 will mostly leave the size unresolved, and an
exclusion at 0.001 is beyond this screen.

**The single-host guard** (M4d's): an exclusion is replaced by "size unresolved (a single host responds)" if any one
host's own difference has magnitude 0.01 or more.

**Robust to the unresolved genomes:** each host's difference may lie anywhere between all its still-unresolved
genomes counted against the contrast and all counted for it; both fields are recomputed on M4d's conservative envelope
(bootstrap at the box's two ends, Student-t at all 2¹⁰ corners). A field that differs on the envelope is reported as
"unresolved (the unresolved genomes decide it)".

**Before the run, the coverage is simulated** (`m4e_read.py coverage`, `runs/memory-m4e/coverage.json`): host base
rates drawn from M4d's per-host block-arm rates; two draws per host whose rates scatter around the host's (log-normal,
σ 0.5, as P's spread suggests); 512 genomes per draw; shifts of δ = 0.002 and 0.004, fixed, uniform, sparse, by
ensemble and on a raised base; independent, disjoint and nested pairing; δ = 0 for wrong readings. **The response is
fixed now:** if the hull's coverage of δ is below 0.90 in any scenario other than the sparse one, the size field's
exclusion is not read ("size unresolved"), and the coverage table is reported beside the reading. A sparse response
(one host in ten) cannot be seen by ten hosts; the exclusion's wording carries that limit.

*Done before any arm (`coverage.json`, 1000 screens per scenario):* the hull covers δ in 0.948 to 0.994 of screens in
every scenario but the sparse one (0.904 at δ = 0.002, 0.751 at 0.004), so the exclusion is read. **The power is
modest:** with a spread effect of 0.004 the direction reads "raises" in 56% to 83% of screens (fixed, uniform, the two
pairings), 29% by ensemble and 18% to 26% on a raised base; with 0.002, 7% to 25%. At δ = 0 it reads "raises" in 2.0%,
and the exclusion holds in 45%. The draws' scatter (σ 0.5, from P's spread in M4d) costs much of it; this is a screen
for effects of about 0.004 and more. Both reviewers accept that for an exploratory screen and advise against hosts
beyond the cap; Fable's alternative at the same cost, 20 hosts with one draw each, would halve the between-host
variance but lose the within-host decomposition of the draws' variation that Astra asked for, so the two draws stay.

**Secondary, reported, not read:**
- the low-level contrasts (U_LH − U_LL, U_HL − U_LL) and the interaction (U_HH − U_HL − U_LH + U_LL), with its own
  envelope over the unresolved genomes;
- the construction check U_LL − I;
- U_HX − U_HH (dose), W − U_HH (N2's weight shape), K − W (N2's labelled degrees), T − K, T − I;
- each with the same interval and envelope, and the per-host and per-draw counts, the not-settled counts per arm, and
  the second pass's transition table;
- **the dose model** (Fable, with Astra's restrictions): per host, a Poisson regression of the switch counts on log S2
  over the U arms only; the mean slope over hosts with the hull interval; then W's and K's deviations from their host's
  curve at their own S2 (the collapse check), averaged over hosts, with the number of hosts where W's or K's S2 lies
  outside the U arms' range (W's and K's S2, about 71, is at or beyond U_LH's for most hosts, so the check
  extrapolates; Fable). **A host has no slope** (reported and left out) when its U arms have no switch, or every
  switch at the largest S2 or every one at the smallest (the maximum-likelihood slope then diverges; the smoke host had
  that pattern, its one switch at U_LH's largest S2), or when Newton's method meets a singular step, a non-finite value
  or does not converge in 100 steps (Fable, Astra). Draft 2 also refused a single switching arm at an interior S2, which
  has a finite slope (Astra, round 2). The dose model
  runs after the readings are written, so it cannot stop them. Eight constructions cannot separate correlated
  summaries, and a summary that fits is not a mechanism (Astra);
- S1, S2, S3 of every block (`blocks-summary.json`) and the per-genome eigenvalue predictor of stage 0 for every genome,
  saved per host, draw, arm and genome with the class the reading uses, and its AUC per arm (`tables.json`), both from
  [`m4e_tables.py`](../../scripts/memory_m4/m4e_tables.py), after the data. The tables read the panels through the
  reader's validated counting, so they use its global audit choice (Astra, round 2).

**What each result says, and does not.**
- *Δ_weight raises:* at N2's edge count, more weight on the head core's edges makes switches more common.
- *Δ_count lowers (or raises):* at a fixed weight, concentrating it on fewer edges makes switches more (or less)
  common; a summary that grows with concentration (S2, S3) is favoured over the summed weight (or edges per se
  matter). *No effect of 0.004:* at that scale the count does not matter at a fixed weight.
- *W − U_HH, K − W:* whether N2's weight shape and labelled degrees add to what equal magnitudes give; descriptive.
- None of them shows that a block stores the state, or says anything about other neurons than C3's, which carry the
  sensors and the read-out: the wording is "on the head core's neurons" (Fable).

## Checks and tests

- **Before every arm and on every reading** (`m4e.verify_run`, called by the reader first): the hosts the plan's, fresh
  (including against M4d's), regenerated and matched to their content hashes, every seed before a host's recorded as
  skipped and each skip regenerated and confirmed (a sampler failure, or a used or earlier-taken graph; Astra); `blocks.json` rebuilt and equal; every
  block's rules (counts, weights, positions, nesting, equal magnitudes, W's multiset, K's degrees, the host's diagonal,
  T exact); outside the block every arm's matrices equal the host's; the sham exact; no magnitude clamped; the audit
  ids as drawn; every panel complete, its genome ids 0 to 511, its arm-graph hash equal to the rebuilt one, and both
  passes' columns complete with every class code a known one (Astra).
- **Tests** (`tests/test_memory_m4e.py`; sabotages in `scripts/memory_m4/sabotage_m4e.py`): each arm's construction
  rules; the nesting; K's degrees and the matching fallback; the diagonal kept; the paired genome and the sham; the
  clamp stop; the second pass (continuation from tick 2000 equal to a longer probe bit for bit, and from early ticks
  where the states still move; the rerun from the tick-21,800 state recording the same substeps; a batched
  continuation of 128 genomes, the production chunk, equal to two of its genomes' own and to a batch of 48 (a typical
  second-pass batch), and a single-genome rerun
  recording the same substeps (exactness is claimed for these compositions; rule 6); the defaults of the two new
  parameters; the merged classes; the audit predicate, and the global fallback through the reader's counting and the
  tables' class choice); record validation, including the second pass's columns and class codes; the host seed
  sequence, and each recorded skip regenerated; the readings' two fields at their boundaries, the guard, the coverage's response, the
  envelope and a size sub-field standing on both; the dose model, including hosts with no slope; the reader refusing
  fewer than ten hosts and calling `verify_run`.
- **The default path of the changed classifier** ([`m4e_pilot_equivalence.py`](../../scripts/memory_m4/m4e_pilot_equivalence.py),
  `runs/memory-m4e/pilot-equivalence.json`): the version before the change (c037f7d) and the current one classify
  R6's planted genomes and 64 genomes of a fresh host identically, record for record (done: identical; the 64 were
  all fading, so the planted genomes, among them the oscillating ones, carry the evidence for the oscillation path);
  M2's own 14 tests, the slow one included, pass with the change (`runs/pytest-m2-after-m4e.txt`). Draft 1 named a
  planted-genome test that only checked the defaults (Fable, Astra).
- **Smoke** (not committed, its own output folder and host seeds): one host, one draw, 128 genomes, every arm, to
  benchmark the first and second pass and decide U_HX. *Done 2026-10-26* (host SH-2019100, 99 block edges; logs
  `runs/m4e-smoke128-log.txt`, first run, slowed by tests running beside it, and `runs/m4e-smoke128b-log.txt`, the
  benchmark): every check passed and the sham was exact; first pass 98 s (I) to 162 s (T) per 128 genomes; second pass
  40 s for the 8 audited genomes plus about 75 s per genome left unresolved; switches: T 6, U_LH 1, U_HX 1, the rest
  0; unresolved after both passes: U_HX 7, T 1, U_LH 1. The reader ran on it and, as it must, read nothing. The
  comparison of the two rerun methods (identical classes and reasons) was made on these two smokes' records, which are
  local; the committed evidence is the tests above. A smoke of 16 genomes after the round-1 changes ran every stage,
  the reader and the tables (`runs/m4e-smoke16-log.txt`).
- **The tests:** 25 pass (`runs/pytest-m4e.txt`); 30 sabotages fail as they must, each by its test's own check or the
  guard under test
  (`runs/m4e-sabotage.txt`; draft 1's "coverage's response ignored" failed through a wrong signature, Astra, and draft
  2's two dose sabotages through an exception inside the sabotaged function, Fable).

## Outputs and cost

`scripts/memory_m4/m4e.py` (stages `hosts`, `blocks`, `arms`; inside `wormwars.accounting`) and `m4e_read.py` (with
`coverage`). Outputs in `runs/memory-m4e/`: `hosts.json`, `blocks-summary.json` (`blocks.json` local), one record per
host, draw and arm (each genome's first-pass and second-pass class and reason, roots' distance, read-out difference,
write measures), `coverage.json`, `readings.json`, and `stage0.json`.

**Cost:** 160 panels of 512 genomes (eight arms, ten hosts, two draws). From the benchmark, about 20 hours of first
pass and 9 of second pass on an unshared CPU, plus about 4 to 5 for the larger audit, so about 33 to 34 hours; M4d's runs were
slowed by a shared CPU at times. **The run stops itself at
48 hours of recorded wall-clock time, counted across invocations** (`registration.CapClock`, which measures elapsed
time, not process CPU time; Astra). The cap is checked before each chunk of up to 128 genomes in either pass, so a
chunk started before it may finish after it, by at most about one chunk's time (minutes; longer in an arm with many
unresolved genomes). Arms run host by host, both draws, in the table's order; what has not finished when the cap
stops the run is reported as incomplete, not read. No GPU.

## After the reading

- **For M5** (both reviewers): if the count or weight contrasts move the rate, M5's controls must match what moves it
  (the total weight, its concentration, or a summary that predicts across constructions), and M5 must separate N2's
  total wiring advantage from its residual beyond that summary. If unsettled dynamics dominate the strong arms, M5
  carries the second pass and a separate dynamics outcome. Strong host variation means more hosts, not more genomes.
- This screen does not make M5 unnecessary, and a null contrast here does not establish equivalence (Astra).
- Location (a dense block on other neurons, observed independently) and neuron-count size wait for a later stage,
  planned after this reading.
