# Literature review for E4s and what follows (2026-10-01)

Two literature reviews, archived verbatim, commissioned before E4s goes further.

**Why:** E4s's design (D139-D142) relied on a report by Claude Sonnet 5.5
(`docs/E4s/literature-report.md`). That report was a single CLI session. Most of its sources were seen
only as search snippets, and nobody checked its claims; it was wrongly called "a deep research" in
the design and in D139. The owner judged that a real literature review was needed before a step this
big. A dated correction goes into `DECISIONS.md` with the next E4s decision.

**How:**
- The prompt is `prompt.md`, written by Claude Opus 5.5 at the owner's request. The owner gave
  the same prompt to two models, and ran both:
  - `opus.review.md`: Claude Opus (Anthropic);
  - `astra.review.md`: Astra 6 (OpenAI).
- Both reviews tag every claim: [READ] full text; [ABSTRACT]; [SECONDARY] via another source;
  [INFERENCE] the reviewer's own reasoning.
- Neither review is checked by us yet. Claims that a design relies on are verified before use, and
  the verification is recorded beside the design.

**Known disagreements between the two:**
- **Izquierdo & Lockery 2010's GA settings.** Opus gives 60 individuals and 300 generations. Astra
  gives population 10 and 100 generations, for 8 parameters. Astra attributes the 60 and 300 to
  Izquierdo & Beer 2013.
- **The amphids' separation.** Opus gives about 8 µm (Pierce-Shimomura 1999, citing Ward 1975).
  Astra gives about 10 µm (Lockery 2011, citing Ward 1975). Both are secondhand.
- **Opus's "gain ceiling" argument:** a short path with |w| ≤ 3 gives a gain of at most 3-9. It does
  not explain the champions' measured gain of about 0.1, which is 30-90 times below that ceiling. It
  also leaves out convergence and recurrence. Astra gives the recurrence route (gain a/(1 − r)).
