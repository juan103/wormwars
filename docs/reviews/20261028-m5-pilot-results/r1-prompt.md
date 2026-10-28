# Review request: M5's pilot results, draft 1

You reviewed M5's power-calculation design and the pilot's plan and code in four rounds
(`docs/memory/M5-PILOT-PLAN.md`, draft 3; D369; your answers are in `docs/reviews/20261027-m5-power-design/`). The
pilot has finished. Please review its results note, `docs/memory/M5-PILOT-RESULTS.md` (draft 1), against the plan and
the outputs. Read-only.

**Outputs** (all in `runs/memory-m5-pilot/`): `report.json` (from `scripts/memory_m5/m5_pilot_read.py`; console
`read_log.txt`), `rr-summary.json`, the 20 Rr panel records `arms/<host>__d<draw>__Rr.json` (T's and K's are M4e's,
in `runs/memory-m4e/arms/`), `longer/*.json` (60 files), `audit/*.json` (60 files), `composition-check.json`,
`m5_pilot_log.txt`, `m5-pilot-attempt.json` and `m5-pilot-compute-record.json` (copies of the local records). The Rr
blocks are not saved (rule 1); they regenerate from their seeds and the summary carries their sha256. One note on the
run: D370 (b2baeef, a test's platform scope after CI's Linux showed the read-out differing in its last bits across
batch sizes, and a dated annotation in the plan) was committed during stage (b); no code the pilot ran changed.

**What came out, in brief:** none of the 117 genomes unresolved at 22,000 ticks resolved at 100,000 (s = r = 0, r's
upper bound 0.025), so the plan's rule keeps 22,000 ticks; 0 of 1500 audited fading genomes per arm changed (pooled
bound 0.0013 per arm); Rr 59 of 10,240 separate states (T 75, K 55), 47 unresolved; T − Rr +0.0016
[−0.0008, +0.0040], SD 0.0034, host component zero by the moment estimate, genomes 94%; seven fallbacks in (b), all
with identical class, reason and amplitude and an exact panel rerun, but with root-field deviations up to 1.0e-3
relative, larger than the smoke's 3e-13.

Please check, and say what must change before this is committed and pushed:
1. **The plan's rules:** were the horizon rule, r, the audit bounds and the remedy applied as the plan fixed them?
   Is anything the plan required missing from `report.json` or the note?
2. **Every number** in the note against the files. Overclaims, missing caveats, wording beyond the data, especially
   the after-the-data readings (the chain looking mixed; the unresolved genomes "held by the root search, not the
   horizon"; the cross-arm pooled audit bound).
3. **The fallbacks:** deviations up to 1.0e-3 relative with the state identical and the panel rerun exact. Does this
   meet the plan's remedy as fixed, and does it change anything for M5 (for example, should M5 run its classifier
   in fixed compositions, or record more)?
4. **The two choices that now fall due** (plan, "What the pilot's results do to M5"). Do you agree with the proposals,
   and if not, what instead?
   - The audit's branch: the proposal is Fable's pre-specified adjustment with a second tranche, not a completed
     audit, with the simulation carrying 0.0013 per arm and an arm-asymmetric scenario.
   - The qualifier's form: the proposal is Fable's calibrated adjustment at r's upper bound, both one-arm cases, with
     Astra's bounds [c_T − c_Rr − u_Rr, c_T − c_Rr + u_T] reported beside as a descriptive envelope (width about
     0.0078 at the pilot's shares). Astra: does this answer your concern that r does not bound switches among genomes
     the protocol leaves unresolved, given that the primary counts them as not confirmed?
5. **The power calculation's inputs** ("What this gives the power calculation"): anything missing or wrong before
   `m5_power.py` is written? In particular the host-variance range (zero to M4e's T − K) now that the pilot's T − Rr
   agrees with M4d's.

Give a verdict (agree / fix then publish / revise), then ranked points with file and line references.
