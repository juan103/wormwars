# Design round 1: M5, a test of N2's exact wiring — first, how many hosts?

The owner's third item (D365, quoting them): "An M5 test of N2's exact wiring, after first working out how many hosts
it would need to detect a given effect." M4e is published (`docs/memory/M4E-RESULTS.md`, draft 4, D368; you agreed in
round 3). Its "For M5" section collects your round-1 and round-2 requirements. This round is about the **power
calculation's design**, which comes before M5's plan: what it must assume, what it computes, and how its answer is
read. Nothing runs before you both agree. Read-only; please read M4E-RESULTS.md's "For M5", M4D-RESULTS.md's "What
this means for the roadmap", `runs/memory-m4e/readings.json`, `runs/memory-m4d/readings.json`, and the panel records
(`runs/memory-m4e/arms/`, `runs/memory-m4d/arms/`) as you need.

## What I propose (Claude), for you to accept, change or replace

**1. The estimand.** M5 asks whether N2's exact off-diagonal wiring inside C3 raises the share of separate-states
genomes over a null that keeps everything else of N2's block. Primary: **T − K\***, where K\* is K (N2's 260 weights
on N2's labelled in- and out-degrees, double-edge swaps) with, in addition, **N2's 8 autapses** on the diagonal (as T)
and **reciprocal pairs matched to T's 75** (not to W's). T − K\* is then the exact wiring given N2's weights, degrees,
reciprocity and autapses. Secondary: T − K\*_S3 (K\* draws accepted only within a tolerance of T's S3), the residual
beyond the spectral summary; with the caveat that S3 itself depends on the wiring. M4e's T − K is the package version
and is reported for continuity. Question: is matching 75 reciprocal pairs by swaps feasible at N2's degrees (M4d's Rr
did it: 75 kept while rewiring), and does it change K's S3 distribution enough to matter?

**2. The success criterion.** The primary field is **direction** ("raises" if the lower bound of the interval is
above 0), with the plan's envelope rule for unresolved genomes replaced as in 3. The power target: **80% power to read
"raises" at a true mean effect of 0.002** (M4e's T − K +0.0020 and M4d's T − R +0.0012 bracket it; neither is used
as the target), with power also reported at 0.001, 0.003 and 0.004 and the false "raises" rate at 0. "At least 0.001"
and the 0.004 exclusion are secondary fields. One primary contrast, so no multiplicity correction for the primary;
the S3 secondary is reported, not read.

**3. The unresolved genomes, fixed before the power.** The envelope cannot be the primary rule: M4e's T − K had 37 + 33
unresolved genomes against 20 counted excess switches, and that interval (−0.0017 to +0.0052) does not shrink with
hosts. Proposed: the primary reading is on the **resolved genomes** (the separate-states share among genomes the
classifier resolves after the second pass, per host and arm), with **each arm's unresolved share as its own secondary
outcome** (T − K\* in unresolved share, read with the same interval) and the envelope as a reported sensitivity. The
second pass as in M4e (22,000 ticks, audit), with the audit sized for the target: about 1500 audited fading genomes
per arm bound a transition rate below 0.002 with zero transitions. Question: does a resolved-genome reading bias the
contrast if unresolved genomes are disproportionately would-be switches in one arm (M4d: unresolved genomes gather in
the exact-wiring arms)? Is a third, longer pass on T's and K\*'s remaining unresolved genomes a better use of compute
than more hosts?

**4. The variance model.** Per host h, draw d, arm a: switches ~ Binomial(n, p_had), with logit p_had = μ_a + u_h +
v_hd + (arm × host) + (arm × draw), the paired genome panels shared across arms within a draw. Fitted by method of
moments (or a simple GLMM) to the paired T − K panels of M4e (10 hosts × 2 draws) and, as a second source, M4d's T − R
(10 hosts × 1 draw). Output: the host, draw and genome components of the contrast's variance (Astra's decomposition:
51/8/41 for M4e's T − K), with their uncertainty propagated by refitting on host bootstrap resamples. The base rate of
K\* is unknown until a pilot: use K's 55/10,240 and T's 75/10,240 as anchors, and a sensitivity at half and double.

**5. The power calculation itself: a simulation of the whole reading procedure.** For each scenario (effect 0, 0.001,
0.002, 0.003, 0.004; spread uniform, proportional to the host's base rate, and sparse: the whole effect in 1 host in
5), and each allocation (hosts H ∈ {10, 20, 30, 40, 60, 80, 100}; draws D ∈ {1, 2}; genomes G ∈ {512, 1024}), simulate
paired panels from the variance model including unresolved genomes (at M4e's per-arm rates, with a scenario where
T's unresolved genomes are enriched for would-be switches), apply the exact reading procedure (hull of bootstrap and
Student-t, the resolved-genome rule, the guard), and record the share reading "raises". Five ensembles: H a multiple
of 5. The answer is the smallest H (with its D, G) reaching 80% at 0.002 under the uniform spread, with the full grid
reported. A script (`scripts/memory_m5/m5_power.py`), tests, a sabotage check, committed with its output before M5's
plan is written.

**6. Cost.** The calculation also reports CPU hours per allocation, from M4e's measured panel times for T and K (about
1.05 h per host for two draws of T and K with the second pass; K\* may cost more). At 60 hosts that is about 60 CPU
hours; at 100, about 100. The GPU needs the owner's word; the power report will say what the CPU can do within a cap
and what would need the GPU, and the owner decides.

**7. Status.** M5 is a test of a specific hypothesis, so I propose it be **pre-registered** (rule 2: committed and
pushed before the formal run), unlike M1 to M4e; the power calculation is its input and is exploratory.

## Questions

1. Is T − K\* the right primary estimand, or should the primary be M4e's package T − K, or something else (for
   example, T against N2's own block with a different subset rewired)?
2. Is "raises" at 0.002 with 80% power the right target? Should the target be smaller (0.001, Astra's benchmark),
   which may need hundreds of hosts?
3. The unresolved genomes: resolved-genome reading with the unresolved share as its own outcome, or something better?
   What does it do to bias and to the interpretation?
4. The variance model and its fitting: anything missing (for example, the five ensembles as a level, or the genome
   pairing across arms)?
5. The simulation's scenarios and the decision rule for "how many hosts". Anything to add or drop?
6. Pre-registration: yes or no, and does the power calculation need its own review round before M5's plan?
7. Anything else that would make the answer to the owner's question wrong.

Rank your points, and give a verdict on the design: agree / revise / replace.
