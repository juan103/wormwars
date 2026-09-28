**Verdict: revise, narrowly.** Eight of my nine v2 must-fixes are fixed in the code; one (M7) is fixed except for a misread number. One Q1b sentence contradicts `tails.json`, and the v3 code has never been smoke-run. I ran nothing; everything below is from reading the code, the committed JSON and the smoke records.

## My v2 must-fixes, checked in the code

| v2 must-fix | Status | Evidence |
|---|---|---|
| M1. Tails pooled under "SH" | Fixed | `in_ensemble` (`p4m.py:128`), used at `p4m.py:308`; tested; `tails.json` has 128 graphs per ensemble |
| M2. Compute record omits its own command | Fixed | `export_compute_record` runs in a `finally` after `run_script` returns (`p4m.py:783-787`); tested for success and stop |
| M3. Empty deletion checked late | Fixed | Checked in the first checkpoint, after a batch that holds only the empty deletion (`p4m.py:708-712`) |
| M4. Per-genome arrays | Fixed | Synapses per condition (`:391`), weights per seed (`:431`), lesions every 20 (`:715`), follow-up per type (`:734`), decay per graph (`:588`) |
| M5. Estimate, rebuild, order | Fixed | My recount gives about 3.5 h against the plan's 3.6; about 3.9 h at the pilot's slowest timing, under the 5 h cap; pre-named targets run first |
| M6. Split-half range | Fixed | File gives 0.943 to 0.986; cross-half −0.25 to −0.61 matches |
| M7. Heavy-tail sentence | **Partly** | Overlap and P4-without-top-5% added; the rank is misread (must-fix 1) |
| M8. Log-log slope | Fixed | `PLAN.md:60-61` |
| M9. Routing ordering | Fixed | Matches `tradeoff.json` in both instances |

Every other Q1 number I checked matches `tradeoff.json`, including the N2perm figures quoted in Q5.

## Must-fix

1. **`PLAN.md:74-75` misreads the numerator's rank in SH-recip.**
   - The plan says N2's 40% is above "all but one in SH-recip". `tails.json:111` gives 0.96875 of graphs below, so **four** of 128 are at or above N2.
   - "All but one" is the response's figure (`tails.json:112`, 0.9921875). The plan gives the response no rank at all.
   - Fix: give the numerator four, and give the response its own rank (above every graph in four ensembles, all but one in SH-recip).

2. **Smoke-run the four simulating commands on v3 before the formal run.**
   - The newest smoke attempt is `20260928T222243Z` at `4c8848e`, which is v2-era code. There is no `synapses-per-genome.npz` or follow-up file in `runs/p4m-smoke/`.
   - v3 rewrote the write path of all four commands, and the tests cover the building blocks, not the command bodies.
   - A crash in the lesions' final steps would cost a 1.4 h rerun, which the 5 h cap cannot absorb on top of 3.6 h.

## Suggestions

- **"Does not rest on that minority" is fair but slightly strong.** With the top 5% removed, six of 640 graphs are at or above N2 (four in SH-route, two in SH-mirror), against one of 640 before. Say so.
- **The overlap is compared with medians only.** N2's 92% is matched or exceeded by 0, 2, 2, 3 and 4 graphs per ensemble, with maxima up to 97%.
- **Both Q1 files are stamped `0916f41`, dirty.** They came from uncommitted code. Must-fix 1 needs a new commit anyway, so regenerate them at it.
- **"SMD and RMD" is imprecise.** The code excludes eight neurons (RMDD, RMDV, SMDD, SMDV, left and right); RMDL and RMDR are deleted like any other.
- **Neither gate has run at 2 048 genomes on the GPU.** Same-composition exactness was observed in default mode but "is not guaranteed absent" (`REPRODUCIBILITY.md:39-42`). Declare now that a failed gate means stop and report, with no tolerance change without a dated amendment.
- **Q3's "one side of zero" rule is weak.** N2 is extreme on both measures, so almost any perturbation lowers both. Read the size of the change against the gap between N2 and the null median.
- **Q3 and Q5 share permutations for seeds 100-107.** The chemical generator seed is 2s and the gap seed 2s+1 in both, so they form a 2×2 with intact. State it, because the two are not independent draws.
- **A stop loses up to 19 deletions' arrays.** Flush them in a `finally`.
- **The lesions checkpoint recomputes every row each time.** That is about 75 000 row computations inside the cap; cache the thresholds and the finished rows.
- **No `DECISIONS.md` entry or README exists for 03m.** The v2 Q1b error is corrected in the plan without quoting the wrong numbers. Add both before anything reaches main.

Both must-fixes are small, and I do not need another round if they are done as described.

**03m plan: revise**