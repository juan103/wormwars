# Round 4: M5's pilot — one departure from round 3's "exactly", and the round-3 fixes

Round 3: both "revise, narrowly" (`r3-fable.md`, `r3-astra.md`). Every finding was taken (the plan, draft 2, lists them;
code in `scripts/memory_m5/m5_pilot.py` and `m5_pilot_read.py`; 19 tests pass, `runs/pytest-m5-pilot.txt`; 21
sabotages fail by their tests' own checks, `runs/m5-pilot-sabotage.txt`). Read-only.

**One finding changed what you asked for.** You asked that the replay reproduce every recorded classifier output
exactly. The smoke on M4e's real records (`scripts/memory_m5/m5_pilot_smoke.py`) stopped: T genome 319 of SH-2011100
d0, replayed with genome 118 in a batch of two, matched class, reason and write amplitude, but its root distance
(1.9529845545473936 vs 1.952984554547665) and read-out difference (0.10977950278976745 vs 0.10977950278985057)
differed at about 3e-13. The diagnostic (`scripts/memory_m5/m5_pilot_diag.py`, `runs/m5-pilot-diag-log.txt`):
- the float32 hold is identical: end state, tail and read-out of genome 319 equal in the pair and in its original chunk
  of 128 (`torch.equal`, array equality);
- the original chunk reproduces every recorded field bit for bit;
- both differing fields come from `locate_and_reach`, the classifier's batched float64 Newton and continuation
  (`scripts/memory_m2/pilot.py`, `full_classify`), whose last bits depend on the batch's composition when the root
  search fails (this genome: "Newton failure ...").

Replaying every target in its original composition (the whole first-pass chunk, and for 22,000 the panel's whole
second-pass batch, which needs the whole panel's first pass) would add roughly 10 to 12 CPU hours. What I did instead
(the plan's "The registered check" and "The composition check"):
- class, reason and write amplitude compared exactly; root distance and read-out difference within 1e-9 relative
  (|Δ| / max(1, |recorded|)), the largest deviation recorded per panel;
- before any continuation, one target genome per arm replayed in its original chunk of 128, every field bit for bit
  (`composition-check.json`);
- the 100,000-tick continuation uses only the float32 state, which the test (full 2000-tick first pass, T arm, chunk
  of 128 against batches of 2 and 3) and the diagnostic show batch-independent.
The smoke then passed: a pair and a batch of one (with its companion) in T, a pair in K, six fading genomes per arm,
and the composition check, bit for bit (`runs/m5-pilot-smoke-log.txt`).

Questions:
1. Do you accept the tolerance with the composition check, or do you want the full original-composition replay?
2. Are the round-3 fixes right (records validated before use and on resume; the output-folder guard; the companion
   for a batch of one; the paired genome variance with the independent one beside it; the incomplete-stage reporting
   with no rule applied; the 100,000-tick contrasts; denominators, reasons, phase timings, the three weight overlaps)?

Verdict: agree (the pilot may run) / revise.
