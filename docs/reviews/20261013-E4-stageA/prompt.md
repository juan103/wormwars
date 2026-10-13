You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Consultation: E4's stage A. Every cross-link factor costs heavily; the cost is cross-talk from A's noses. What is E4 now?

You are consulting on the WormWars repository (your working directory), read-only. You set the calibration rules
(`docs/reviews/20261013-E4-diagnostics/`, D255). Stage A ran: read `experiments/E4-two-minds/calibration.json`, D256 in
`DECISIONS.md`, `scripts/e4_calibrate.py`, `wormwars/e4/calibration.py`, and E4's design (`docs/E4/E4-DESIGN.md` v3) and
E4-D's (`docs/E4/E4-D-DESIGN.md` v2.1). Budget: about 4.4 of E4's 30 GPU-hours spent (the pilot's attempt 1, the
diagnostics, stage A).

**The results in brief** (generation 1, children only, paired; E-G 7.97 on block A):
- bias split at 0.25: noses only 3.38, comparators only 6.86;
- bias ladder with weights and τ at 0.25: 0.05 → 6.73, 0.02 → 7.20, 0.01 → 7.40, 0.005 → 7.41, frozen → 7.40. The
  declared rule returns "frozen, flagged", because the frozen-bias children keep only 93% of E-G (weights' and τ's own
  load), and the block-B confirmation fails (94%);
- cross-link ladder (X0's children 7.40): X+ at 0.25 → 4.53, 0.5 → 3.09, 1.0 → 2.08, 2.0 → 1.11, 4.0 → 0.64; every factor
  fails;
- cross-link-only children at 0.25: intact 4.58, mean-substituted 5.33, centred 4.98, nose-origin links cut 6.26,
  comparator-origin links cut 4.98 (all links cut = E-G, 7.97).

**My reading, as claims to attack:**
1. In E4's main task each module's noses smell its own goal. A's sensory signal in B's comparators is the wrong
   gradient while B steers to B, and vice versa, so random cross-links are mostly harmful cross-talk; there is little
   information in A that B can use. A null P1 or P2 in the main task would then be expected by construction, and
   spending about 20 GPU-hours to show it is poor value.
2. The bias rule's 95% condition was ill-posed: it tested weights' and τ's load, which the rule did not intend to
   regulate. By the rule, the outcome is "reconsider explicitly".

**Options for E4's direction, for the owner** (attack, rank or add):
- **(i) E4 as designed,** with cross-link factors below 0.25 added (0.05, 0.1) so something passes, biases frozen or at
  0.01, and the formal run at about 20 GPU-hours; a likely "no benefit detected", read through E4-D.
- **(ii) Re-scope:** report the main-task findings (the comparators' fragility, the cross-talk cost) as E4's exploratory
  result, and make the confirmatory question E4-D's: does evolution discover A → B transfer when it is necessary? That
  needs E4-D's feasibility check first (CPU), then an evolutionary E4-D design and pre-registration.
- **(iii) Change the main task** so that A holds information useful to B (for example, a goal-relevant cue only A
  senses in normal shuttling), with a new design.
- **(iv) Stop E4** after publishing the exploratory findings.

**What I want:**
1. Are readings 1 and 2 right? Is anything in stage A an artefact (for example, the cross-link ladder measured with
   frozen biases, or block A's composition)?
2. Your ranking of (i)-(iv), or a better option, and why, including what each can and cannot conclude.
3. For the option you rank first: the next concrete steps and their GPU cost.
4. What exactly to put to the owner.

**The answer I want:** a recommendation first, then numbered points. Terse.
