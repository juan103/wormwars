**Verdict: revise, narrowly.** The plan matches the agreed design and the code matches the plan on every item I checked. Nothing in it can touch M4e's records. Two small changes to the replay belong before the run, both an hour's work, and I do not need another round on them.

## Q1. M4e's records are safe

I traced every write. `m5_pilot.py` writes only under its `OUT` (arms, longer, audit, rr-summary, compute); the reader writes `report.json` there. `m4e.verify_run` calls `load_hosts` and `load_blocks`, which only read and compare (`scripts/memory_m4/m4e.py:159`, `:315`); M4e's writers (`stage_hosts`, `stage_blocks`, `stage_arms`, `main`) are never reached. `CapClock` reads `compute.json` and never writes (`wormwars/registration.py:129`). Import side effects are two `mkdir` calls on folders that already exist (`m4d.py:35`, `census.py:27`).

One gap: `MEMORY_M5P_OUT` can point anywhere, and there is no guard like M4e's smoke guard (`m4e.py:38`). Set to `runs/memory-m4e`, the pilot would add Rr panel files to M4e's arms folder and overwrite M4e's `compute.json`. Refuse an `OUT` that resolves to M4e's or M4d's folder.

## Q2. The replay is built right; its check is weaker than it can be for free

The construction is correct. `replay` repeats the first pass as `classify_panel` runs it (the `c.ramp` call before it touches no probe state, and the probe has no randomness). `extend` repeats `second_pass` exactly, and the spy test proves the call. The 78,000-tick leg passes the double `end` through `continue_hold`'s cast to float32, which is exact.

Three fixes:

- **Compare every recorded field, exactly.** At 22,000 the check compares against `merged[i]`, which is "unresolved" for every target by construction, so it only confirms "still unresolved". The records hold `reason`, `a`, `root_distance` and `readout_difference` for both passes, as Python floats that round-trip JSON exactly (SH-2011100 d0 T stores root distances such as 1.1102230246251565e-15). Compare all of them at 2000 and at 22,000, and in (c) at 2000. A root distance at 1e-15 probes the state's last bits. This turns "the classes agree" into "the classifier's outputs agree bit for bit", at no cost. If floats differ while classes agree, stop and diagnose by running one T panel's first pass in M4e's composition (chunks of 128, in order) and comparing `end` with `torch.equal` against the replay's.
- **Never replay a batch of one.** The probe's config pins padding off (`wormwars/exp02/grid.py:56`, through `spikes.genomes`). T1 found that on the CPU a one-strain batch differed from its batch member (`docs/foundations/T1.md:498`). A panel-arm with one unresolved genome runs exactly that path. Add a companion genome from the same panel, discard its results, and record it.
- **Wording.** The docstring at `m5_pilot.py:180` claims "the states equal the original run's". T1's contract claims equality across compositions only as tested. Say: tested at 1, 3 and 128 strains over 60 ticks, and checked on every replayed genome through the recorded classifier outputs. The plan says `longer/*.json` holds "the recorded and replayed classes"; the code stores only the replayed. Store both.

## Q3. The horizon rule and r are right and fixed tightly enough

The code matches the plan: s is the share not unresolved at 100,000, pooled; r counts codes 0 and 1; the one-sided bound is `beta.ppf(0.95, x+1, n−x)`, and the test values are correct. Pooling over the three arms is right, since the protocol is arm-blind. Three small additions to the plan's text: genomes still unresolved at 100,000 count in r's denominator as not separate, so r leans low and the r = 1 envelope stays the sensitivity; say what the rule does if the cap stops (b) before every panel finishes (my suggestion: not applied, the partial s reported, M5's plan review decides); report s and r per arm beside the pooled values, since the qualifier applies one r to both arms.

## Q4. Missing from the report

- Per-panel second-pass seconds and second-pass genome counts, for Rr and for M4e's T and K. The cost model needs the tail that scales with the unresolved count (my round-2 point). Only Rr's total seconds are there now.
- First-pass fading counts per panel and arm, the audit's denominator (Astra's point).
- Each Rr panel's `valid` and `eligible` flags, which are in the records but not surfaced.
- Reason tables for (b)'s genomes at 22,000 (from the records) and at 100,000. They tell whether unresolved-ness comes from the hold's length or the classifier's own cap.
- The reader should degrade when a stage is incomplete, as the plan promises; `main` raises `FileNotFoundError` if any Rr panel is missing.

Smaller points: `validate_rr` omits M4e's `genomes` check and the second-pass column lengths (`m4e.py:472`, `:484`); `weight_share_on_shared_edges` sums the smaller of the two magnitudes, so name it that way. The seeds are disjoint from M4e's four families and M4d's three, and nothing else in the repository uses the 2026400x to 2026430x range. The cost sum sits under the cap with margin if Rr's unresolved count is near T's and K's.