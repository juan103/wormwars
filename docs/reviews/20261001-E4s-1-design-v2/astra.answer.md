**Verdict: revise.** A small specification revision, not a change of arms. Checked `roadmap` at `42ea7af`; no files changed.

The main v1 remedies are present: O1c, endpoint-only labels, separate Mc/H reporting, R−N, open-loop offsets, mutation masks, reset versus rescue, E3’s score condition, and the evaluation reserve. The remaining qualifications are:

- **Fable 2 — C2: partly resolved.** Giving C2 signed readings fixes the original problem. But identical founders guarantee identical G0 genomes, **not an “unclear” classification on fresh worlds**. Replace “unclear by construction” with the observed E4s-0 finding and classify the new measurements. [Design:244](D:/Claude/random/wormWars/docs/E4s/E4s-1-DESIGN.md:244)
- **Fable 8 — gate-failure probability: partly resolved.** Roughly 4–5% requires a predictive calculation incorporating uncertainty in the pilot mean. A plug-in calculation treating that mean as truth gives roughly 1%. V2 mixes these interpretations; name the assumptions and provide the calculation. The gate itself can stay. [Design:49](D:/Claude/random/wormWars/docs/E4s/E4s-1-DESIGN.md:49)
- **Fable 9 — score gate: mostly resolved by the 04a champions.** The G0-best rationale remains weak: their committed module-mean scores are only **0.018–0.442**, versus grafted scores of 1.09–3.30. Grafted performance does not establish substantial ungrafted performance. Keep the champions as the explicitly non-vacuous controls and report baseline scores for every gate genome. [Population records](D:/Claude/random/wormWars/experiments/E4s-stereo-module/E4s-0/populations.json:10711)
- **Power request: not auditable yet.** I found the percentages in the design and D148, but no committed E4s-1 simulator, seeds or output supporting them. That falls short of rule 5.

V2 also introduces an ambiguous **C2 classifier**: a real−mean interval of `[−0.20, −0.10]`, with the other interval inside ±0.25, satisfies both “harmful” and “neutral.” Explicitly prioritize the rules, or report direction and materiality separately. [Design:238](D:/Claude/random/wormWars/docs/E4s/E4s-1-DESIGN.md:238)

One remaining overclaim: **M−N does not require M to climb**. M could stay unchanged while N finishes worse. O1c correctly prevents that inference; the motivation should agree with it. [Design:32](D:/Claude/random/wormWars/docs/E4s/E4s-1-DESIGN.md:32)

The pre-registration must pin:

- **Classification:** the complete nine-cell O2 mapping; C2 precedence and interval boundaries; Mc’s two offset-specific results and reference scores; exact O2b band boundaries.
- **Selection and probes:** F/G0 selection and tie rules; E3’s eligible F genomes and tie rule; open-loop initialization, duration, averaging and finite differences; which offset statistic defines the median split.
- **Gates and provenance:** exact genomes, hashes, imposed input histories and every execution shape—including padded `1 × 256`; all RNG seeds and the 256-world population-probe IDs.
- **Analysis and stopping:** bootstrap implementation and seed, reproducible power records, stage caps and evaluation reserve, and treatment of incomplete pairs, interruptions and reruns.

No additional arm is needed.