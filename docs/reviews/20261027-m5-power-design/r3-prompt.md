# Round 3: M5's pilot — the plan and its code, before it runs

Round 2: Fable "revise, narrowly" (the pilot's fixes; no further round needed for them), Astra "revise" (the pilot to
be made concrete). Both accepted K\* = Rr (Astra: with "anatomical weight magnitudes"), the all-genome "confirmed by
this protocol" primary, and the power design's outline. Your answers: `docs/reviews/20261027-m5-power-design/r2-*.md`.
Read-only.

**New, for review:**
- `docs/memory/M5-PILOT-PLAN.md` (draft 1): the pilot fixed before it runs, with what its results do to M5.
- `scripts/memory_m5/m5_pilot.py` (stages `rr`, `longer`, `audit`), `scripts/memory_m5/m5_pilot_read.py` (report),
  `tests/test_memory_m5_pilot.py` (13 pass, `runs/pytest-m5-pilot.txt`), `scripts/memory_m5/sabotage_m5_pilot.py`
  (12 of 12 fail by their tests' own checks, `runs/m5-pilot-sabotage.txt`).
- A smoke on M4e's real records (`runs/m5-pilot-smoke-log.txt`; script not committed): verify_run 93 s; the first Rr
  block passes its checks (5200 accepted swaps of 50,904 attempted; it shares 104 of N2's 260 edges, 59 of the 150
  reciprocal and 45 of the 110 non-reciprocal); three of SH-2011100 d0's T unresolved genomes and two of K's replayed
  to the recorded classes at 2000 and at 22,000 ticks (about 80 s per genome); five fading genomes per arm replayed as
  fading and stayed fading at 22,000 (46 s per five in a small batch).

**Your round-2 fixes, as taken:**
- Seeds above M4e's families: Rr blocks 20264001 + hd, Rr audits 20264101 + hd, large audit 20264201 + arm, the
  report's bootstrap 20264301; a test checks them disjoint.
- Wording: "count of reciprocal pairs unchanged (a swap may break one pair and make another)"; "anatomical weight
  magnitudes"; signs follow labelled positions; Rr chosen by me on Fable's proposal (Astra asked this round, and
  accepted).
- The 10,400-swap block is the same chain continued with the same generator (a test).
- Similarity split by N2's reciprocal and non-reciprocal edges, plus same-magnitude edges and the weight share on
  shared edges; chain attempts and acceptances.
- Replay: first pass regenerated in a batch of the panel's targets (a test shows a genome's first pass does not depend
  on its batch: alone, in 3, in 128), classified, checked against the record at 2000 and at 22,000 (the stage stops on
  any difference), then continued to 100,000. Costs counted.
- Audit population: first-pass fading, not among the panel's audit ids nor its second-pass ids, sampled without
  replacement over the arm's 20 panels; 1500 additional per arm.
- No global fallback in the pilot; Rr's audit status reported, M4e's T and K classes untouched.
- The horizon rule (s ≥ 0.5 → M5 continues its unresolved genomes to 100,000, with an audit there) and r with its
  one-sided 95% Clopper–Pearson bound as the only pilot input to M5's qualifier, written before (a) runs; the
  qualifier's form, and the audit branch (Fable's adjustment with a second tranche, or Astra's completion of both
  arms), chosen after the pilot and before the power script; the simulation's transition rate at the pooled upper
  bound, never zero.
- Target 0.002's rationale: Astra's ("two more confirmed switches per thousand would justify the experiment"); the
  "resolution floor" claim dropped.
- A 30-hour cap on the pilot's own compute record; stages resumable by panel; inside the accounting.
- The variance split (method of moments on host-draw differences) reproduces Astra's M4e T − K decomposition: host
  0.509, draw 0.079, genome 0.412 (Astra: 0.5085, 0.0773, 0.4142; the small difference is the genome part's pooled
  rates).

Please check the plan and the code against the agreed design, and in particular:
1. Can anything in the code change M4e's records, reading or committed outputs? (It writes only under
   `runs/memory-m5-pilot/` and patches `m4e.CAP` in memory.)
2. Is the replay correct and its check sufficient (classes at 2000 and 22,000; no stored states to compare)?
3. Are the horizon rule and r's definition (pooled over T, K, Rr; "settled" = any class but unresolved at 100,000)
   right, and fixed tightly enough?
4. Anything missing from the report that the power calculation will need?

Verdict: agree (the pilot may run) / revise.
