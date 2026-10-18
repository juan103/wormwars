# 03a pilot-dev results review

- **What was reviewed:** pilot-dev's records and D312, at `374f88c`.
- **The run:** 20261018-100702, both at xhigh effort. `prompt.md` is exactly what was sent.
- **Two errors in the prompt:**
  - it said "pilot-check (about 10 GPU-hours) and then possibly the formal run (about 44)". The 43.8-hour projection
    already includes pilot-check (Astra 8);
  - it said pilot-dev ran on two commits, but it ran on three: `a5760c4`, `1b0531a` and `f27d4c4` (Astra 3).
- **Verdicts:** both said "revise D312".
- **Recommendation:** both recommend option (b), a bounded check of the search on MIP/URXL within pilot-dev's
  remaining 1.42 hours. Pilot-check follows only if that check shows reliable restoration and recovery; otherwise (c),
  stop and report.
- **The direction is the owner's decision.**
- **What was taken:** D313.
