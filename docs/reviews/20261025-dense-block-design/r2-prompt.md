# Design round 2: a merged design for the dense-block study

Your round-1 proposals are in `docs/reviews/20261025-dense-block-design/r1-{fable,astra}.md`. Fable proposed a
dose-response (one slope on a sign-invariant block summary, a free stage 0 on M4d's records, M4d's hosts reused);
Astra a factorial on edge count × total weight with equal magnitudes, W and K arms, fresh hosts with two block draws,
paired risk differences primary. Below is Claude's merge. Please agree or revise it, point by point where you
disagree. Read-only. Short answers.

## The observation that joins the two proposals

At fixed total weight, Astra's count contrast (U_HH − U_LH: the same weight spread over 260 edges rather than the
host's ~110) moves S2 and S3 down while S1 stays fixed. So it is the direct test of Fable's question: if summed
magnitude (S1) sets the rate, Δcount ≈ 0; if squared magnitude or spectral coupling (S2, S3) sets it, Δcount < 0
(fewer, heavier edges switch more). The factorial therefore answers (a) and puts a prospective test on (b).

## The merged design (draft)

- **Name and status:** M4e, "what a dense block carries", exploratory, CPU, planned and reviewed before it runs
  (D364 said not to draft M4d's smaller-block second stage; that remains undrafted).
- **Stage 0 (free, exploratory, labelled after the data, chooses nothing):** S1, S2, S3 for every M4d block and the
  per-genome largest real eigenvalue of the signed scaled block for M4d's 71,680 genomes, against their committed
  classes; S3 of R against T. Reported in the plan as background; the primary contrasts below are fixed without it.
- **Hosts:** ten fresh hosts, two per ensemble (seeds beyond M4d's), **two independent block draws per host**, 512
  fresh paired genomes per draw (1024 per host and arm), the draws averaged within host before the host-level
  analysis (Astra). Hosts are the unit.
- **Arms (9):** I; U_LL (E_h random edges, total S_h, equal magnitudes); U_LH (same support, total 2347); U_HL (260
  random edges, total S_h, equal); U_HH (same support, total 2347); **U_HX** (U_HH's support, total 2 × 2347: a third
  weight level, Fable's dose direction, no clamp at equal magnitudes); W (U_HH's support, N2's 260 weights shuffled
  onto it); K (N2's labelled in/out-degrees, randomised wiring, N2's weights globally shuffled, reciprocal pairs
  matched to W's); T (N2's block). The low-count support is a uniform subset of the high-count support; supports and
  signs shared by ordered pair across arms; exterior parameters frozen; intact-spec normalisation; bitwise sham.
  **Autapses:** the host's own in every arm but T (Astra; Fable's scale check shows N2's are at most 0.39 scaled,
  far below 1). Achieved weights verified after the clamp.
- **Primary contrasts (two):** Δ_weight = p(U_HH) − p(U_HL) and Δ_count = p(U_HH) − p(U_LH), paired risk
  differences, host-level, with the hull of the host bootstrap and the Student-t interval, Bonferroni over the two
  (95% each), coverage simulated before the run (sparse, heterogeneous, block-draw variance, disjoint switching).
  **Readings per contrast:** "raises" if lower > 0.001; "lowers" if upper < −0.001; "no effect of 0.004 or more" if
  the interval lies within ±0.004; otherwise "unresolved". (0.001 is Astra's meaningful-effect benchmark; 0.004 is
  M4d's margin, kept for exclusions; the plan says an exclusion at 0.001 is beyond this screen.)
- **Secondary, reported not read:** the low-level contrasts and the interaction; U_HX − U_HH (dose); W − U_HH (shape);
  K − W (labelled degrees); T − K and T − I (replication of M4d's package). **A pre-specified secondary dose model:**
  per host, a Poisson regression of switch counts on log S2 over the U arms and W, K; the mean slope with its
  interval; then each arm's deviation from its host's curve (Fable's collapse test), descriptive, with Astra's caveat
  that eight constructions cannot separate correlated summaries and a summary is not a mechanism.
- **Unresolved and oscillation genomes, fixed:** every arm's unresolved and persistent-oscillation genomes continued
  from their saved tick-2000 states to a total hold of 22,000 ticks and reclassified by the same rules with shifted
  windows (a horizon-aware wrapper, with failing-first tests and an equivalence check that the 2000-tick path is
  unchanged; Astra); an audit of 256 resolved genomes sampled across arms, which must keep their class in at least
  99%, otherwise the second pass is reported and not used (Fable). Both classifications and the transition table are
  kept; the reading uses the second pass's classes; remaining unresolved genomes bound the reading by M4d's envelope
  (partial identification). "Not settled" is a secondary outcome per arm.
- **Cost:** 90 panel-equivalents at M4d's recorded 1293 s ≈ 32 h, plus the second pass (8 to 12 h, benchmarked on the
  smoke); **cap 48 CPU hours**, cumulative; balanced host blocks; incomplete runs reported, not read.
- **For M5:** as both said (match what matters; total vs residual advantage; this screen does not make M5
  unnecessary).

## Questions

1. Do you agree with the merge, and with U_HX as the ninth arm (or drop it to save ~3.6 h)?
2. Fresh hosts (Astra) rather than M4d's (Fable)? Fable: is the loss of pairing with M4d's seven arms acceptable,
   given that M4d's hosts produced the R > D observation that motivated this design?
3. The readings and the two margins: acceptable, or do you want one margin?
4. The audit size (256) and threshold (99%), and the 22,000-tick horizon.
5. Anything essential missing, or anything here that should wait?

Verdict: agree / revise.
