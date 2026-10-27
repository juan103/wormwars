# M5's pilot: design inputs for the power calculation — the plan

*Draft 3, 2026-10-27, after four rounds with Astra 6 and Fable 5.1 (both "revise" in round 1; in round 2 Fable
"revise, narrowly" with the pilot's fixes listed, Astra "revise" for the same fixes; in round 3, on draft 1 and the
code, both "revise, narrowly", Fable needing no further round; in round 4, on draft 2, both "revise, narrowly",
accepting the replay's tolerance and declining the full original-composition replay, Fable needing no further round;
every finding of rounds 3 and 4 taken here; archived in
[`docs/reviews/20261027-m5-power-design/`](../reviews/20261027-m5-power-design/)). This pilot measures what M5's power
calculation needs and cannot get from M4d or M4e. It runs on M4e's ten published hosts, so its data never enter M5's
reading: M5's hosts will be fresh. Nothing here changes M4e's records or its reading. CPU only.*

## Why a pilot

The owner's third item (D365): "An M5 test of N2's exact wiring, after first working out how many hosts it would need
to detect a given effect." Both reviewers agreed that no host count can be given yet:
- **M5's control has never run on M4e's protocol.** It is M4d's Rr (below). M4d ran it on its own hosts, on the first
  pass only.
- **The host spread is uncertain.** Its host component differs about tenfold between M4e's T − K and M4d's T − R and
  T − Rr (Fable's table, round 1).
- **The unresolved genomes.** The genomes left unresolved after the 22,000-tick pass (70 in M4e's T and K) bound
  T − K between −0.0017 and +0.0052 before any sampling error. More hosts do not shrink that.
- **The audit.** Its missed-transition rate is bounded only at about 0.0037 per arm.

## What M5 is to test (agreed in substance; fixed in M5's own plan later)

- **The arms:** T (N2's C3 block) against **Rr**, M4d's rewired control.
  - Rr rewires N2's 260 off-diagonal edges by double-edge target swaps at N2's labelled in- and out-degrees.
  - Each edge carries its anatomical weight magnitude from its source, so out-strengths and each source's collection
    of outgoing magnitudes are kept.
  - A swap is accepted only if it leaves the count of reciprocal pairs unchanged (at 75; a swap may break one pair
    and make another).
  - There are 20 accepted swaps per edge, and N2's diagonal is kept exactly (`m4d.rewire(..., keep_recip=True)`).
  - Genome signs follow the labelled position, not the edge (Astra), so signed out-strengths are not kept.
  - The null is defined by this algorithm and is not claimed uniform.
- **The estimand** (Astra's wording): T − Rr tests N2's weighted arrangement inside C3 beyond its labelled degrees,
  each neuron's outgoing anatomical magnitudes, its diagonal and its count of reciprocal pairs. It does not separate
  edge positions from weight placement.
- **The primary outcome:** the share of all sampled genomes confirmed as separate states by the specified protocol.
  Unresolved genomes count as not confirmed. The secondaries are the share not classified as fading, the unresolved
  share, the resolved-only share and the envelope.
- **The planning effect:** 0.002, at 80% power. The rationale (Astra): two more confirmed switches per thousand
  genomes with N2's exact wiring would justify the experiment. It is not chosen from an observed contrast, and this
  pilot's T − Rr must not become the expected effect (Fable).

## The pilot (fixed here before it runs)

[`scripts/memory_m5/m5_pilot.py`](../../scripts/memory_m5/m5_pilot.py), stages `rr`, `longer`, `audit`, in that
order, inside `wormwars.accounting` (rule 8). Outputs go to `runs/memory-m5-pilot/`.

**Before anything, `m4e.verify_run()`.** It regenerates M4e's hosts, blocks, genome panels and signs, and checks them
against M4e's records.

**(a) Rr on M4e's panels.**
- **The records first.** Every saved panel record is validated before use: M4e's rules for T and K (`m4e.validate`,
  with the rebuilt arm hash), the same rules for Rr. Every stage file is checked for its ids, column lengths and class
  codes before it is skipped on a resume or read (Astra, round 3). The output folder may not be M4d's or M4e's (Fable,
  Astra, round 3).
- **The blocks.** For each of M4e's 20 host-draws (hd = 2h + d), one Rr block is drawn from
  `default_rng(20264001 + hd)`.
- **The chain-length check.** The same chain is continued with the same generator for 5200 more accepted swaps. That
  second block is described, not run.
- **The checks on each block:** N2's labelled degrees, every row's sorted magnitudes (each source's outgoing
  collection), 75 reciprocal pairs, N2's diagonal and 260 edges, plus M4e's outside check and clamp check.
- **The panel.** M4e's genome panel and signs for that host-draw (the same panel as M4e's T), paired as M4e paired
  its arms.
- **The classification** is exactly M4e's: first pass, second pass to 22,000 ticks, and 40 audit ids per panel from
  `default_rng(20264101 + hd)`.
- **What is recorded:** each panel's record in M4e's format; each block's chain counts (accepted, attempted), S1 to
  S3, and its similarity to T. The similarity covers shared edges, split into N2's reciprocal and non-reciprocal edges
  (Fable), edges with the same magnitude, and the weight overlap three ways: the minimum-weight overlap, N2's weight
  share on the shared edges and Rr's (Astra, round 3). `rr-summary.json` is written as it grows.
- **Kept local:** the Rr blocks themselves carry N2's weights edge by edge (rule 1). The committed summary gives each
  block's sha256, and the blocks regenerate from their seeds.
- **No global fallback.** The pilot reports first-pass classes, merged classes, audit transitions and audit status
  separately. An Rr audit transition changes nothing in M4e's T and K classes.
- **Cost:** 20 panels at about 0.25 to 0.4 h, so about 5 to 8 CPU hours.

**(b) The longer horizon.**
- **Who:** every genome classified unresolved after the 22,000-tick pass, in M4e's T and K panels (70; M4e's merged
  classes) and in (a)'s Rr panels.
- **The replay.** The tick-2000 and tick-22,000 states were not stored (Astra, Fable). Each genome is replayed from
  its panel's genome, its signs and M4e's settings:
  - the first pass, then classified;
  - the hold continued to 22,000 ticks, then classified as M4e's second pass classifies.
- **The registered check:** every output the records hold must be reproduced, or the stage stops. At 2000 those are
  the class, reason, write amplitude, root distance and read-out difference. At 22,000 they are the class, reason,
  root distance and read-out difference (Fable, Astra, round 3).
  - Class, reason and write amplitude must match exactly.
  - Root distance and read-out difference must match within 1e-9 relative, with the largest deviation recorded per
    panel.
  - *Why the two differ (found after round 3, in the smoke on M4e's records, before any pilot stage ran):* both come
    from the classifier's batched float64 root search, which depends on the batch's composition in its last bits;
    the float32 hold does not.
  - *The evidence:* T genome 319 of SH-2011100 d0, replayed in a batch of two, has the same end state, tail and
    read-out as in its original chunk of 128. The chunk reproduces every recorded field bit for bit. The pair
    differs by about 3e-13 in those two fields only.
  - *Rule 6:* exactness is claimed within a composition.
- **The composition check:** before any continuation, one target genome per arm is replayed in its original chunk
  of 128 (M4e's composition). It must reproduce every recorded field bit for bit, and the stage-style replay's
  float32 hold must equal the chunk's (Fable, round 4; `runs/memory-m5-pilot/composition-check.json`, validated on
  every resume and by the reader, Astra, round 4).
- **The state check, on every (b) genome:** each replay batch's float32 hold (end state, tail, read-out) must equal
  the hold of the genome's original chunk of 128, run again without the classifier (Fable, round 4; about 50 s per
  chunk). So the 100,000-tick continuation is verified to start from M4e's state on every genome, not on one per arm.
- **When the registered check fails** (fixed here, Fable, round 4). The failing genomes are Newton failures and
  marginal roots, where a hard branch in the root search can flip a reason or move a root distance with the state
  identical.
  - The panel is rerun as M4e ran it (`m4e.classify_panel`, M4e's code and composition, about 17 minutes).
  - If that rerun reproduces the failing genome's record bit for bit, the discrepancy is the classifier's
    composition dependence: both values are recorded (`fallbacks`), and the stage continues.
  - If it does not, the stage stops.
  - The same rule applies in (c).
- **Never a batch of one.** A one-strain batch takes a different path on the CPU (T1). A genome replayed alone gets a
  companion from its panel, whose results are discarded and whose id is recorded (Fable, round 3).
- **The continuation:** the hold then continues from tick 22,000 to **100,000**, and the genome is classified at
  100,000 by the same rules. The classifier's own float64 continuations and their cap are unchanged.
- **Batches:** the replay runs genomes in batches of their panel's targets. A test checks the full 2000-tick first
  pass of a T-arm panel in its production chunk of 128 against batches of 2 and 3: state, tail and read-out equal.
  The hold's equality is claimed for these compositions and checked by the state check; the classifier's outputs are
  compared by the registered rule, not claimed bit for bit across compositions (Astra, rounds 3 and 4). The timings
  are recorded by phase (replay, state check, to 22,000, to 100,000).
  - *Annotation, 2026-10-27 (D370):* the equality holds on Windows, where the pilot runs and its state check
    verifies it on every genome. On GitHub's Linux runners the test found the state and tail equal but the read-out
    differing in its last bits across these compositions, so there the test holds the read-out to a float32 tolerance
    (rule 6: CPU exactness is claimed on one platform only). The text above is unchanged.
- **Stopping rule:** one pass, no extension.
- **Cost:** about 100 genomes at about 4 minutes each (three classifications), plus about an hour of state checks,
  so about 8 CPU hours.

**(c) A larger audit.**
- **Who, per arm (T, K, Rr):** 1500 genomes classified fading by the first pass that no audit has touched (not among
  any panel's 40 audit ids). They are drawn without replacement from the pooled population of the arm's 20 panels, by
  `default_rng(20264201 + arm index)` (T 0, K 1, Rr 2).
- **The run:** each is replayed (first pass, its recorded outputs compared by the registered rule, with the same
  remedy on a failure), continued to 22,000 ticks, and classified.
- **What is recorded:** every class change, and the primary trigger, first-pass fading to separate states, per arm.
- **Cost:** about 4500 genomes at about 4.5 s each, so about 6 CPU hours.

**Seeds.** The pilot's families start above M4e's audit family, which ends at 20263508 (Fable, Astra): Rr blocks
20264001 to 20264020; Rr audits 20264101 to 20264120; the large audit 20264201 to 20264203.

**Cap.** 30 hours of recorded wall-clock time (`registration.CapClock`, the pilot's own `compute.json`). Stages run in
order, and each is resumable by panel. A stage the cap stops is reported as incomplete, with what finished.

## What the pilot's results do to M5 (fixed here, before (a) runs)

- **The horizon (from (b)).** Let s be the share of (b)'s genomes, pooled over T, K and Rr and weighted by genome,
  resolved by the classifier (any class but unresolved) at 100,000 ticks. s and r are also reported per arm.
  - If the cap stops (b) before every panel finishes, the rule is not applied: the partial s is reported, and M5's
    plan review decides (Fable, round 3).
  - If s ≥ 0.5, M5's plan continues every genome still unresolved at 22,000 ticks to 100,000 ticks, with an audit at
    that horizon too (Astra).
  - If s < 0.5, M5 keeps the 22,000-tick protocol, and the unresolved genomes are a class at that horizon.
- **The qualifier's input (from (b)).** r is the share of (b)'s genomes, pooled over T, K and Rr, classified separate
  states at 100,000 ticks, with its one-sided 95% Clopper–Pearson upper bound. Genomes still unresolved at 100,000
  count in its denominator as not separate states, so r leans low. r estimates confirmation by 100,000 among genomes
  unresolved at 22,000; it does not bound eventual switches among genomes still unresolved at 100,000, and applying
  one pooled r to both arms is a sensitivity scenario, not protection against switches hidden in the control's
  unresolved genomes (Astra, round 3). M5's plan will use r and that bound,
  and no other pilot quantity, in its qualifier and sensitivity for unresolved genomes. The qualifier's form (Fable's
  calibrated adjustment, Astra's bounds [c_T − c_Rr − u_Rr, c_T − c_Rr + u_T]) is settled in M5's plan review.
- **The audit (from (c)).** Each arm's transition rate is estimated with its one-sided 95% upper bound, and pooled
  with M4e's audit of the same arm (783 to 800 per arm, zero transitions). The audit's branch for M5 is chosen after
  the pilot and before the power script: either Fable's pre-specified adjustment with a second tranche, or Astra's
  completion of both arms' fading genomes. The power simulation then uses a transition rate at the pooled upper
  bound, never zero (Astra).
- **The variance and rates (from (a)).** Rr's rate, its unresolved and not-classified-fading shares, T − Rr's spread
  over the ten hosts and the draws, and the paired class table. The genome part of the variance is the paired one,
  from the share confirmed in both arms; two independent binomials are reported beside it as a sensitivity (Astra,
  round 3). If the horizon rule selects 100,000 ticks, the rates and contrasts are also reported on the classes with
  (b)'s 100,000-tick results in place. These join M4e's T − K and M4d's T − R and T − Rr (labelled
  first-pass only) as the range of host-variance sources. Pilot T − Rr's mean is reported, and the planning effect
  stays 0.002.

## Outputs

`runs/memory-m5-pilot/`:
- `rr-summary.json`: per host-draw, the chain counts, S1 to S3 and the similarity, for both chain lengths, with each
  block's sha256.
- `arms/<host>__d<draw>__Rr.json`: M4e's format.
- `longer/<host>__d<draw>__<arm>.json`: per genome, the recorded and replayed classes at 2000 and 22,000 ticks, and
  the class and reason at 100,000.
- `audit/<host>__d<draw>__<arm>.json`: per genome, the replayed first-pass class and the 22,000-tick class and reason.
- `report.json`: written by [`m5_pilot_read.py`](../../scripts/memory_m5/m5_pilot_read.py).
- The logs.

`report.json` holds (a stage the cap stopped is reported with its finished and missing panels, and no rule is
applied to it):
- Rr's per-host counts, with each panel's first-pass fading count (the audit's denominator), validity and eligible
  count, and its second pass's genome count and seconds, for T, K and Rr;
- T − Rr per host, with the hull interval, its standard deviation and the variance split;
- the paired T × Rr class tables per host-draw, at 22,000 and at 100,000 ticks; each stage's largest root-field
  deviation and its fallbacks;
- (b)'s table with s and r, pooled and per arm, the horizon rule's outcome, and the reasons at 22,000 and 100,000;
- the contrasts again on the 100,000-tick classes;
- (c)'s tables with the bounds, per panel and pooled with the panels' own audits;
- the costs per stage and phase, per panel.

A short results note follows, reviewed by both, before the power calculation is designed in code.

## Checks and tests

`tests/test_memory_m5_pilot.py`, with sabotages in `scripts/memory_m5/sabotage_m5_pilot.py`. The tests cover:
- Rr's block rules, and that the check catches each broken rule;
- the chain continued, not restarted;
- the similarity's split;
- a genome's first pass identical alone and in a batch of 128;
- the replay's stop on a class that differs from the record;
- the audit sample: first-pass fading, unaudited, without replacement, fixed by its seed;
- the horizon rule at its boundary;
- Clopper–Pearson against known values;
- the seed families disjoint from M4e's;
- the output folder guard;
- a batch of one replayed with a discarded companion;
- the exact comparison of every recorded output;
- incomplete stage files and Rr records refused;
- the paired genome variance (zero for identical outcomes);
- the horizon rule withheld for an incomplete stage;
- the state check catching a changed hold;
- a stage file checked against its source record (identity, the stored copy, the replay's agreement);
- the failure remedy continuing only on an exact panel rerun;
- the composition file validated as the plan's passed check;
- the reader reproducing M4e's published T − K from M4e's committed records (Fable, round 4).

24 tests pass (`runs/pytest-m5-pilot.txt`). 27 sabotages fail by their tests' own checks
(`runs/m5-pilot-sabotage.txt`).
