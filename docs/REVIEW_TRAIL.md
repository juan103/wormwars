# Review trail: who made each error, and who caught it

This project was built by AI agents directed by one person (see "How this was made" in the README).
Errors were made along the way. This page lists the ones that reached a results document, or the
code behind one: who made each error, who caught it, and how it was confirmed. It is kept because the
pattern is itself a finding about working this way, and because nothing about it is hidden in the
history. Every commit named here is still in the repository, including the ones that got things
wrong.

**The agents.** *Claude Code* (Anthropic) wrote the code, ran the experiments and wrote the
documents: Claude Opus 5 until 2026-09-24 and Claude Opus 5.5 from then on, as the `Co-Authored-By`
lines of each commit record. *Astra 6* (OpenAI, through the Codex CLI) and *Fable 5.1* (Anthropic)
acted as reviewers. From 2026-09-24 Claude Code could consult them directly, read-only, and before
that the human relayed their reviews. *The human* directed the work and asked the questions that
led to several of the findings.

## The episodes

| # | error | made by | caught by | how it was confirmed | record |
|---|---|---|---|---|---|
| 1 | "Coevolved swarms learned to flank." 88.8% of damage landing on mid and tail is exactly the chance value `2 / (2 + head_armor)`. | Claude | **Fable 5.1**, in review (relayed by the human), raised as arithmetic. The refutation was already in Claude's own `summary.json` (generation 0 scored the same), and Claude had never compared the two numbers. | Re-measured on random, generation-0 and final strains | D026, C1 |
| 2 | "N2 is deeper": N2's sensor-to-motor distance reported as 1.35 against 1.00-1.05 | The explanation by Fable 5.1, built on a path length Claude had mis-measured (the pump was folded into the locomotor read-out) | Claude, re-measuring before writing a limitations bullet dictated from that figure, and declining to write it as given | Re-measured across all ten control graphs: N2 is inside the shuffle range | C4 |
| 3 | The frozen opponent suite, committed in the repository, reproduced the connectome's anatomical weights at 100% | Claude | Claude, checking a question from the human about what the committed `.npz` files contain | Proportionality test over every committed file; the file was removed from history before anything was public | D028 |
| 4 | "The gap vector does not leak even when unevolved." In fact it is 99.6% proportional; the test divided by a mean that four clipped values had moved. | Claude | Claude, a day later, answering the human's question about the control graphs | Re-measured with a median-fixed scale; nothing committed was affected | D028 correction |
| 5 | Every `np.load` enabled pickle, which is a code-execution path for downloaded files | Claude | The human asked | All call sites fixed; guard test | D029 |
| 6 | **Chemical synapses ran backwards in every run of experiment 01.** `Genome.dense` stored `W[pre, post]` and `Brain.step` multiplied by its transpose. | Claude Opus 5, in M2 (`87ab460`, 2026-09-17) | **Astra 6**, on 2026-09-24, reviewing the roadmap in the human's own Codex session, from source inspection and a two-neuron NumPy calculation. It never ran the simulator. | Claude drove one real synapse in the real brain (I1L -> I6: no signal forward, signal backward), fixed it, showed legacy mode reproduces 01's published scores to the last bit, pre-registered and ran 01b | D031, C5 |
| 7 | Six problems in Claude's first corrected write-up and fix: "the real wiring improves faster" (the measure could not tell a head start from gain); "ends at least level"; "every number is pre-registered"; a rank p-value from non-exchangeable graphs; a legacy default that silently reversed any config without a brain section; and the frozen record of experiment 01 edited and re-hashed | Claude Opus 5.5 (`5161e76`, `d028a15`) | **Astra 6 and Fable 5.1, independently**, consulted read-only before publication. Both said "do not publish as is". | Claude re-measured or re-checked each point before acting, and fixed all of them in `3d230e5` | D033 |
| 8 | Experiment 02's pre-registration, as first written, would have misreported. The report crashed on a NumPy boolean; incomplete data (one N2 run, one shuffle) returned "supported"; a verdict branch challenged small contrasts the rule never required large; a promised budget fallback did not exist; a prevalence bound was unjustified. A fix pass then checked graph names instead of registered runs and seeds. | Claude Opus 5.5 (`5c69653`, `ba326e7`) | **Astra 6**, in an adversarial review and a confirmation pass, reproducing each defect on synthetic data before any N2 run | Each reproduced by Claude with a test that failed first, then fixed | D040 |
| 9 | Unnamed alternative explanations in the same pre-registration: a degree-preserving shuffle destroys mirror symmetry (N2 keeps 64% of chemical edges mirrored, shuffles 13-16%), and on the stereo task the "history" jitter also scrambles the left-right difference | Claude Opus 5.5 | **Fable 5.1**, reviewing after the evolution had started and before any probe ran | Symmetry measured on every graph; jitter re-validated on scripted stereo controllers (costs a memoryless one 0.029 at radius 1) | D041 |
| 10 | The first write-up of experiment 02 said evolution "erodes" N2's generation-0 advantage; in fact N2's own mapping preference is unchanged and the shuffles catch up. It also claimed champions do not use history (jitter cannot show that), that stereo steering is "real but worth little", that N2 "reads food more strongly" (an intervention effect), and "topology, not strengths" | Claude Opus 5.5 (`6dc7d71`) | **Astra 6 and Fable 5.1, independently**, before publication; Astra found the catch-up | Recomputed by Claude from the records before rewriting | D042 |

Episode 6 went unnoticed for a week, through a passing test suite, every milestone report, a
publication audit, the first public release and Claude's own review of the roadmap on the day it
was found. No test had ever sent a signal down a single synapse and looked where it arrived.

## The reviewers were not always right either

Two reviewer figures in episode 7 did not survive checking. Fable 5.1 said every condition's
scores rose by 0.1-0.2 between experiments 01 and 01b; the measured rises are 0.05-0.10 for the
controls and 0.22-0.23 for N2. Astra 6 found 8 of 1440 weys with an integrator error above 0.05; the
same check with different inputs found 0. Both are reported as measured. No reviewer finding was
adopted without being re-measured or re-read first, and the corrections above say who measured what.

## What this does and does not show

- In this project, the errors that mattered most were caught by a reader other than the author:
  the human, an external reviewer, or a model from another family. The authoring agent's tests and
  self-review missed the worst of them.
- The reviewers found errors by reading source code and data, not by running experiments.
  Confirming each one took execution.
- Reviewers make errors too. Checking before adopting a finding was part of what made the reviews
  useful.
- This is one project and ten episodes: an anecdote about multi-agent review, not a measurement
  of it.

## In the history

`git log` shows the same story commit by commit: `87ab460` introduces the transpose; `5161e76`
fixes it and pre-registers 01b; `d028a15` reports 01b with the overclaims, including a commit
message that says "N2 improves faster"; `3d230e5` withdraws them after review. None of these commits
has been rewritten.
