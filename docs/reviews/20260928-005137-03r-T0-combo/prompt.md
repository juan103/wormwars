You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Two reviews in one: (A) 03r results, revised; (B) T0's GPU checks

You are read-only on branch `roadmap` at HEAD (c91a93d). `DECISIONS.md` D081 describes both parts.

## A. 03r results, revised after your review

Your reviews are in `docs/reviews/20260928-00252*-03r-results/`; both of you said "not yet".

**Revised files:**
- `experiments/03r-replication/RESULTS.md`;
- `experiments/03r-replication/DISCLOSURE.md` (the dated addendum);
- the pointer at the top of `experiments/03-generation0/RESULTS.md`, and its §10 paragraph;
- `README.md`: the new lead section "Newest: experiment 03 and its full replication, 03r", which
  is the text proposed for main. The branch banner at the top is removed when merging to main;
- `ROADMAP.md`, line 21.

**New evidence:**
- N2 and SH-route-1020255, re-measured with the binding commit's code, are bit-for-bit identical
  to the saved measurements;
- the input hashes are unchanged.

**Please check:**
- Are your points resolved?
- Is the README section accurate and complete per §10, D059 and D063?
- Is anything new wrong?

## B. T0's GPU checks

**Files:**
- the script: `scripts/t0_gpu_checks.py`;
- the results: `docs/foundations/T0_gpu.json`;
- the interpretation: D081 and the corrected paragraph in `docs/REPRODUCIBILITY.md`;
- the plan's declarations: `docs/foundations/T0.md` v2.1, sections 1 and 4.

**Findings:**
- historical replay of 9 01b champions is exact;
- the single-island regression against 01b's log is exact;
- ledger and accounting identity hold on CUDA;
- replay-mode repeats are identical;
- the declared 1e-4 default-CUDA tolerance was **exceeded**. A follow-up (in D081) traced this to
  single-strain chunks only: same-composition repeats are identical in both modes.

**Please check:**
- Is the interpretation right, and honestly stated?
- Does the T0 gate now pass, given the plan's rule that an exceedance is a finding and the bound
  is never widened?
- What remains before T0 is closed, and T1 can start?

**Answer format:** findings ranked **must fix**, **should fix**, **minor**, for each part. End with
two lines:
- "03r results: ready to publish" or "not yet";
- "T0: close" or "not yet".
