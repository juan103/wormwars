**Verdict: fix then publish.** Every new number I checked traces to its file. Three statements need fixing before `main`: M5's question is misstated as a 0.002 threshold, Rr is described as keeping N2's reciprocal pairs, and the owner's agreement to the M6 turn is asserted but recorded nowhere. The rest is wording.

## Numbers and readings

All checked out against `summary.json`, `runs/memory-m4e/readings.json` (through the summary), `runs/memory-m5-pilot/report.json` and `runs/memory-m5-power-welch/power.json`: the compute rows and the 112.43 total; M4e's 4 against 31, the two primary intervals and envelopes, the three-step ladder, T − I, the audit range and 56 of 201; the pilot's 117 unresolved, 0 of 1500, T − Rr and its variance split; rule C's 110 to 160 hosts, 72.0 and 90.7 hours, powers 0.84 and 0.81, A's 135 hosts at 92.5, and the 22.1% saving. The power script has no accounting call and no compute record, so "outside the compute accounting" is right. I could not run the test suite here (no shell), so "5 pass" is reported, not verified by me.

## Fix before publishing

- **M5's question is framed as a threshold** at `docs/memory/SYNTHESIS.md:250` ("by 0.002 or more") and in the holds row at line 291 ("adds 0.002"). The agreed criterion is "raises" if the interval's lower end is above zero; 0.002 is the planning effect at 80% power (`docs/memory/M5-POWER-DESIGN.md:59`, D369). The pilot results explicitly separate "detecting a positive effect" from "at least 0.001" and "excluding 0.004". Say "raise the share ... over Rr (powered for 0.002)".
- **Rr does not keep N2's reciprocal pairs** (line 251, and the inherited line 197 from draft 3). The swap rule keeps the *count* at 75; a swap may break one pair and make another (`docs/memory/M5-PILOT-PLAN.md:30`). Fable caught this very phrase in D369 round 2. The pilot found Rr shares about 59 of N2's 150 reciprocal edges on average. Fix both lines; `M4D-RESULTS.md:178` has the same ambiguity and could take a dated note.
- **The owner's agreement to the M6 turn is untraceable** (lines 363 and 372). D373 closes with "Next: for the owner ... a change of direction that is the owner's to make." Nothing records the owner saying yes. Add a D374 or a dated annotation to D373 quoting the owner, and cite it. This is the attribution-gap class both reviewers raised on draft 3.

## Should fix

- **The Δ_weight exclusion drops its ten-host restriction** in "In short" (line 43) and the routine table (line 103). Section 5 and the holds table carry it. Astra caught this same omission for M4d in the D365 review.
- **"How concentrated its weight is, more than its size"** (line 40) is ambiguous. If "size" means edge count, as in the owner's phrase, it contradicts Δ_count, which shows edge count at fixed weight does matter. The results file's own wording is safer: neither edge count nor total weight alone reproduces the effect, with equal magnitudes; how concentrated the weight is matters.
- **"Is 94% genome sampling"** (line 256) states flatly what the pilot results hedge: a moment estimate truncated at zero, weakly determined on ten hosts, with a scenario range up to M4e's T − K. The "72 ... and 91 at a wider one" that follows only makes sense with that caveat.
- **"Beyond its block's weights and degrees"** (line 54) implies the degrees' step is shown. K − W is unresolved over the unresolved genomes.

## Wording and attribution

- Fable's "bound the pilot puts on latent switches" (line 390): per D372 the pilot "speaks against the hazard" but bounds protocol confirmations, not latent states. That was Astra's accepted correction.
- "Both: the Welch t" (line 393): Astra proposed it in round 1; Fable accepted in round 2 after first arguing to repair the gate instead.
- "Four sensitivities to the unresolved genomes" (line 258): two are one-arm unresolved sensitivities, two combine those with the audit.
- "Three on the results, with both reviewers" (line 258): round 3 was Astra only.
- The postponement bullet (line 263) omits two things D373 gives a resumer: the counts hold for the code at 7f04382 and the script is rerun if it changes; a GPU run changes the cost side.

## Fairness and what is missing

The M5 section and the new lesson describe the postponement fairly: the owner's decision, Claude's recommendation, D373's reasons, kept not cancelled. One nuance the lesson could add: the owner's own order already put the host count before M5's plan, so the safeguard worked; what the lesson really says is that the precision bought by a 23-hour pilot and six rounds exceeded what the decision needed.

For a reader of `main`: `README.md:41` still titles the row "Memory, M1-M4" with findings ending at M4d, and `README.md:60` says "M5's power calculation is next." ROADMAP is annotated through D373; the README is not. Update it in the same push.