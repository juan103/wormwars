# M5's power calculation, round 1: the design before the script

Context. M5 tests N2's exact wiring (T) against M4d's rewired control Rr, on fresh hosts, pre-registered. You agreed
the power calculation's design in substance over four rounds (`docs/reviews/20261027-m5-power-design/`, D369), and
the pilot's results and two choices over two rounds (`docs/memory/M5-PILOT-RESULTS.md`, draft 3,
`docs/reviews/20261028-m5-pilot-results/`, D371). Two questions were left open before `m5_power.py` is written: the
rule that turns the host-variance range into one host count (Fable), and the audit's estimator and decision rule
(Astra's list in the results note, "Two choices for M5's plan").

The design is `docs/memory/M5-POWER-DESIGN.md` (draft 1). Please review it against the agreed design, the pilot's
records (`runs/memory-m5-pilot/report.json`, `runs/memory-m5-pilot/arms/`), M4e's reader
(`scripts/memory_m4/m4e_read.py`) and M4e's classification (`scripts/memory_m4/m4e.py`, `classify_panel`). Check the
numbers you rely on. Read-only; nothing has run.

Points that are my choices rather than yours, to attack rather than accept:
- the plain-s² Student-t beside a stratified bootstrap (section 1);
- the shared host effect fitted to both arms' overdispersion, the interaction σ_w set per scenario, and no draw term
  for T (section 2);
- the second tranche of 120 per panel in both arms on a transition in either, and the pooled point estimate applied
  to unaudited fading genomes only (section 3);
- "unqualified raises" under the symmetric audit scenario as the 80% event (sections 1 and 3);
- rule C, the internal pilot with a variance-only interim, recommended over A and B (section 5);
- the panel-time resampling by whole pilot host, and the linear scaling to G = 1024 (section 6).

Answer the document's five questions, rank your points, and give a verdict: agree (the script may be written) /
revise.
