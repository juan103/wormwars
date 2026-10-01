**Verdict: fix then run.** Reviewed `roadmap` at `e7a9b81`. No files changed. These are implementation and verification fixes; I do not see a need to redesign the experiment.

1. **Re-score ties select the wrong candidate.** [scripts/e4s0.py:503](/D:/Claude/random/wormWars/scripts/e4s0.py:503) breaks ties by screening rank, because `top` is already sorted by screening score. Example: screening scores `[9,10]`, tied re-scores `[5,5]` select original index **1**, whereas v2 requires **0**. Select by `(-rescore_mean, original_grid_index)` and test this case. Also, [line 151](/D:/Claude/random/wormWars/scripts/e4s0.py:151) puts the recurrent parameter outermost, whereas the plan’s listed product puts it last. Align the code and stated order.

2. **Size freezing excludes the projection’s own elapsed time.** [scripts/e4s0.py:346](/D:/Claude/random/wormWars/scripts/e4s0.py:346) calls `E.clock().spent_hours()`, which reads completed accounting records; the current attempt is written afterward. Consequently, a 1.79-hour forecast can freeze full sizes despite 0.02 hours already spent projecting, then fail admission without applying the prescribed shrink. Include current-attempt elapsed time when freezing, without double counting earlier attempts.

3. **The projection still does not cover the actual workload adequately.** [scripts/e4s0.py:259](/D:/Claude/random/wormWars/scripts/e4s0.py:259) and [line 317](/D:/Claude/random/wormWars/scripts/e4s0.py:317):
   - attenuation is projected as zero; dynamics and bootstrap analysis are omitted;
   - L4’s common re-score actually uses three padded `1×512` evaluations, but is priced using `5×512` throughput;
   - shrunk compositions reuse full-size throughput without measurement.
   
   Time those paths and proposed smaller compositions, or include an explicit, justified allowance. The **819,264-episode arithmetic is correct**; the timing estimate is incomplete.

4. **Promised per-world records are discarded.** Tuning/re-scoring and L4 base selection retain only means ([line 504](/D:/Claude/random/wormWars/scripts/e4s0.py:504)); population selection drops `score` ([line 600](/D:/Claude/random/wormWars/scripts/e4s0.py:600)); robustness drops child counts ([line 666](/D:/Claude/random/wormWars/scripts/e4s0.py:666)). Save these arrays with candidate/population indices and world IDs. Otherwise the selection and robustness summaries lack the audit data v2 explicitly promises.

5. **Attenuation measures unclamped turn drive.** [scripts/e4s0.py:422](/D:/Claude/random/wormWars/scripts/e4s0.py:422) omits the world’s `[-1,1]` clamp, unlike gain probe v3. Clamp each tick before averaging and differencing. Otherwise saturation can produce a reported command gain that the actual motor command does not have.

6. **Dynamics reporting has incorrect edge cases.** [diagnostics.py:111](/D:/Claude/random/wormWars/wormwars/e4s/diagnostics.py:111) can label an unconverged trace settled merely because its final-window mean is negligible; it also returns `t90` for explicitly unsettled traces. Preserve convergence independently and return no settled-response time when unsettled. At [e4s0.py:480](/D:/Claude/random/wormWars/scripts/e4s0.py:480), the reversal sign check examines `changed−control`: a still-positive changed output can pass. Check the changed endpoint separately for an actual reversal.

7. **The selection-world test remains missing.** [test_e4s_diagnostics.py:94](/D:/Claude/random/wormWars/tests/test_e4s_diagnostics.py:94) only asserts the alternative result’s **shape**. It cannot detect selection on diagnostic worlds. Exercise the production population-selection path with constructed scores whose winner differs between selection and diagnostic IDs; sabotage the ID routing and require failure.

8. **Zero-parent robustness ratios remain misleading.** [scripts/e4s0.py:665](/D:/Claude/random/wormWars/scripts/e4s0.py:665) divides by `1e-12`. Marking only `fallback` undefined leaves fabricated numerical `median_share` values. Return `null` shares whenever the parent mean is zero.

9. **The plan contradicts itself about unsuccessful qualification.** [E4s-0-PLAN.md:178](/D:/Claude/random/wormWars/docs/E4s/E4s-0-PLAN.md:178) still specifies L1, while line 188 specifies the highest qualification mean. The code implements the latter. Add a correction identifying that as authoritative.

The residual wrapper, fixed sweep chunking, adjacency/classes, circuit/carrier, ladder stopping, paired L4 base selection and fixed recurrence, qualification thresholds, G0 selection logic/worlds, and module mutation ownership/seeds match v2. Frame isolation is correct: E4s-0 and E2d have separate E2 module instances; E2d’s bootstrap/classification settings remain unchanged. E4s-0’s clock uses `runs/e4s0/compute.json`, with the published copy under its experiment directory.

**V2 resolves most v1 design concerns, but not all implementation/verification concerns:** projection, selection-world testing and per-world publication remain incomplete as above. The dated correction to “out of reach by construction” is present.

I reproduced the tie and settling defects using the actual pure helpers. The full tests could not collect because PyTorch import requires a writable temporary directory in this read-only environment.