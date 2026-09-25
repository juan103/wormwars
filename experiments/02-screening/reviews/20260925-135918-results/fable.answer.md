**Verdict up front.** Every number I could trace matches `analysis.json` and `probes.json`. The problems are in the prose: three of the four readings you asked about are stated more strongly than the registered rules or the data allow, and several registered items (including three "also reported" items from §4 of the pre-registration) are missing.

## 1. Numbers

Checked and matching: primary (bootstrap, t, Welch), per-graph SH range, the secondary probe table, the 1-of-72 and 10-of-72 counts (I mapped every `"meaningful"` entry in `per_champion`), the generation-79 statements, the fitness interaction tables (normalised and raw), per-cell advantages, variance components, leave-one-out range, all ten tripwires, covariates, scripted K/S/M means, the food-dependence intervals, and the 7.44 h total (5.64 + 6477 s of probes).

Not verifiable from the report files, so unconfirmed:
- MINOR `RESULTS.md:146` "champions held-out ~2.7-2.8": no such aggregate exists in `analysis.json`; `cmd_report` doesn't print it.
- MINOR `RESULTS.md:98` "matches 01b, where N2's edge was a head start": I found no generation-0 estimate in 01b's results to support it.
- MINOR `RESULTS.md:9` "3-10 times" is the ratio of the *absolute* responses (0.0146 vs 0.0014-0.0042) but the sentence says "turn toward the stronger side", which is the *signed* measure (+0.0029 vs ≤+0.0003). No SE on any of these 256-strain means.

## 2. Overclaims

1. **MAJOR. "Evolution erodes N2's generation-0 advantage"** (`RESULTS.md:11,82`). No interval is given for I(g39) − I(g0). The two intervals overlap ([+0.019, +0.117] vs [−0.033, +0.043]), the units are identical (same seeds), so a paired bootstrap of the difference is trivially computable and is the only thing that licenses "erodes". Line 210 admits this, but the bold headline and the abstract state it as a finding. Also, `analysis.json:110-113`: at g39 N2 has an advantage under T0-R1 (+0.046 [+0.010, +0.081]; raw +0.147 [+0.027, +0.265]). "Evolution does not keep either advantage" ignores the one cell where an advantage appears. Multiplicity applies, but name it.

2. **MAJOR. Food dependence "through its biological sensory neurons from the start"** (`RESULTS.md:116-120`). Selectively reported. At g39 on T0, R1 also shows N2 > SH (+0.324 [+0.139, +0.516], `analysis.json:2047-2051`); the T1 interaction straddles zero (+0.061 [−0.229, +0.357]); and at g0 the T0 interaction straddles zero (+0.370 [−0.030, +0.758], `analysis.json:1998-2002`). So the M0-specific, from-the-start reading is not supported. Second problem: the probe replaces food with each world's tick-0 mean, so "real − constant" is large either because N2 reads food more or because N2's fallback behaviour without food is worse. Raw advantage under T0-M0 is +0.06 while the dependence contrast is +0.46, which implies N2's constant-food score is about 0.4 *below* SH's. Report the ablated scores, not only the difference, before choosing the reading.

3. **MAJOR. "Their stereo steering is real but worth little"** (`RESULTS.md:72-75`). Seven of the 72 generation-0 champions already show meaningful swap cost (T0-R1-SH1 r0 +0.67, T0-R1-N2 r6 +0.30, T0-R2-SH2 r1 +0.28, T0-R2-SH8 r0 +0.23, T0-M0-SH7 r1 +0.18, T0-R1-SH4 r0 +0.15, T0-M0-SH5 r1 +0.15) against ten at g39. Swap sensitivity is a property of best-of-32 random brains, not evidence of evolved steering. The registered reading in §4 covers only "mean without swap"; "swap without mean" has no registered reading, and the group swap interval for N2 is [+0.000, +0.179].

4. **MAJOR. "not … on its history"** (`RESULTS.md:67`). D039 and §5 say jitter measures history *sensitivity*, not use, and defer "any claim that a champion uses history". The negative claim is equally unlicensed; a multi-tick integrator averages jitter 1 out.

5. **MINOR. "comes from its topology, not its synapse strengths"** (`RESULTS.md:139`). N2 − SH on T1-M0 straddles zero, so there is nothing to attribute. With `init_w_scale` 0.2 and 40 generations of `w_sigma` 0.08, drift is about 0.5, so the initial magnitudes are largely gone by g39. The registered g0 strength probe (`probes.json:32-104`) has permuted ≥ anatomical for N2 under every mapping (0.982 vs 0.950 at M0), which cuts against the sentence and is unreported.

6. **MINOR. "found meaningful stereo use for nobody"** (`RESULTS.md:3`) contradicts line 71: T0-R1-SH1 run 0 has +0.43, and had +0.35 at generation 0. Qualify to "no group in T0-M0".

7. **MINOR. "replicates the disclosed number"** (`RESULTS.md:113`). Different probe, different scale (0.12 then, 0.015/0.003 now). "Consistent with" is the honest verb.

8. **MINOR. "about ten times the replication"** (`RESULTS.md:188-190`). From a half-width of 0.05, an interval that excludes zero at +0.03 needs about 3× (I(T0): 1.6×); 80% power needs about 6×. Ten follows only if the target half-width is 0.015, which the text does not say.

## 3. Registered but omitted or different

1. **MAJOR.** §4 "also reported, no verdict": Delta at g0 (−0.007 [−0.071, +0.060]), per-unit acquisition (+0.011 [−0.069, +0.083]), and the mapping interaction of Delta (+0.001 [−0.055, +0.065]) are all absent. So is the registered remap check: N2's use under R1 (+0.016) and R2 (+0.024) equals M0 (+0.027), which weakens the M0-specific reading and should be stated.
2. **MAJOR.** Jitter 3 (§5) is never mentioned, and `RESULTS.md:66` "the history jitters change nothing measurable" is false for it: T0-M0 g39 N2 +0.050 [+0.006, +0.103], SH +0.036 [+0.021, +0.054]. Since jitter 3 costs the scripted stereo controller 0.535 but kinesis only 0.057, this actually supports the no-stereo reading.
3. **MINOR.** Also omitted: common-mode input response (the disclosure's second number, 0.16, is never closed out), the g0 strength probe, behaviour measures (§5; 365 s of probes), pellet share, and `max_gen0_error` 0.28 (SH3 turn drive 0.26 against 0.40; SH1 run 1 forward 0.66). The pre-registration says gen0 drive is "reported, never tripwired"; it is not reported.
4. **MINOR.** "The remaps disagree" is computed on T1 only (`report.py:203`); §6 names no task and the table doesn't say T1. On T0 at g39 R1 is +0.046 [+0.010, +0.081] and R2 −0.017, and the difference is uncomputed. D036 said this tripwire also tests modality; on T0 it may fire.
5. **MINOR.** T0-M0-N2 run 0 is class "inconclusive" under the registered rule (`analysis.json:2299`); `RESULTS.md:79-80` should use the word.

Verdict, sub-label, tripwires, completeness, disclosures and the commit split are reported correctly.

## 4. What the full design should take that RESULTS.md misses

- **Everything N2-specific is at generation 0.** A g0-only study (thousands of random genomes, many shuffles, gap-free variants) costs minutes and would settle "head start" and its mechanism before any evolution is bought.
- **Gap junctions are the likely carrier of the directional turn.** Chemical signs are random, so a consistent "toward" direction needs a sign-free, mirrored path; gap junctions are 62% mirrored in N2. The valence probe already has a gaps-off mode; run the input-response probe that way.
- **The search finds stereo-sensitive genomes at g0 and fitness does not reward them.** Kinesis carries most of the scripted gain (K 2.12 vs straight 0.67 vs S 3.23). The full task needs K ≈ straight and S ≫ K, not just S > K.
- **Mutation erases the anatomical initialisation** (0.2 vs ~0.5 drift), so a g39 strength control tests nothing; either lower sigma or test strength at g0.
- **Shuffles need the no-shortcut rule and a mirror-symmetric variant**: direct read-out weight 1.5-43 vs N2's 0-1, mirror share 0.13-0.17 vs 0.64. RESULTS lists this; the plan should make it a constraint on shuffle generation.
- **Do not size on between-graph variance ≈ 0.** It is a truncated estimate from 8 graphs.
- **Compute the paired g39 − g0 interaction and the T0 R1 − R2 contrast** before publishing; both are available from the existing records.