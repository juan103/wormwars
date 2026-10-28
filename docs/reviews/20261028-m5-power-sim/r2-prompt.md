# M5's power calculation, round 2: draft 2 of the design

Round 1: Fable "revise, narrowly", Astra "revise" (`docs/reviews/20261028-m5-power-sim/r1-fable.md`, `r1-astra.md`;
draft 1 is `draft1.md` there). Draft 2 is `docs/memory/M5-POWER-DESIGN.md`; its opening lists what changed. Please
check that each of your round-1 points is answered correctly, and review what is new. Read-only; nothing has run.

My choices, to attack rather than accept:
- the audit at a fixed size A in {40, 80, 160} per panel, drawn as M4e draws it, with no trigger and no second
  tranche, replacing D371's agreed second tranche (section 3; Astra's round-1 option "or a fixed audit size");
- the host-variance scenarios at fixed per-arm host variance with the correlation lowered, and 3.0e-5 by scaling both
  arms at zero correlation (section 2);
- the stratum-aware t (within-ensemble variances, Welch–Satterthwaite) only in the unbalanced case, the plain-s² t in
  the balanced case (section 1);
- the joint adjustment in the success event (section 1);
- rule C's mapping at the 75% upper limit of s², H_max found by simulating C, the cap, and the 20% saving needed to
  recommend C over A (section 5);
- one confirmation at H and H + 5 with Bonferroni over allocations, and "not confirmed" otherwise (section 4);
- the false "raises" acceptance bound of 0.030 at R = 40,000 (section 4).

Answer the document's five questions, rank your points, and give a verdict: agree (the script may be written) /
revise.
