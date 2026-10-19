**revise.** PILOT.md draft 3 is not ready to bind: its revised GPU sizing conflicts with DESIGN §8. Most round-1 fixes are correct, but several remain incomplete.

Checked `ab2d7bb` on `roadmap`, including the existing CUDA smoke records. No files changed; no tests or experiment code executed. Numbering below follows Astra’s round-1 findings and incorporates Fable’s related points.

1. **Cap — partly fixed; low severity.** Stage and work-unit checks are present. However, [e03h.py:521](D:/Claude/random/wormWars/scripts/e03h.py:521) calls `ck.over()` **after** accounting has aggregated this attempt; [line 150](D:/Claude/random/wormWars/scripts/e03h.py:150) adds its elapsed time again. `over_cap_at_end` can therefore falsely report an overrun. Count the finishing attempt once.

2. **Stage dependencies — fixed for the current chain.** Upstream hashes and the explicit G2/S1 rate comparison prevent an old G2 from authorizing P after S1 changes. Archived P eligibility still has a separate hole: finding 7.

3. **Sizing — decision table and budget precedence fixed; medium regression.** [e03h.py:466](D:/Claude/random/wormWars/scripts/e03h.py:466) now includes CPU graph construction in projected GPU-hours, following [PILOT.md:187](D:/Claude/random/wormWars/experiments/03h-history-use/PILOT.md:187). But [DESIGN.md:360](D:/Claude/random/wormWars/experiments/03h-history-use/DESIGN.md:360) explicitly excludes sampler CPU costs. This can unnecessarily exclude SH, reduce W_t or stop the run. Separate sampler and calibration timings and reconcile the registration before binding.

4. **Smoke contamination — fixed.** The retired banks are disclosed; registered and smoke configurations use separate banks and seeds. All five existing CUDA smoke records identify `ab2d7bb`, CUDA and completed status. Their projection is explicitly labelled meaningless.

5. **Calibration replacement — functionally fixed; low reporting gap.** Replacement, reconstruction from accepted seeds and genome hashes are correct, addressing Fable’s findings 1 and 7. However, [e03h.py:279](D:/Claude/random/wormWars/scripts/e03h.py:279) publishes `progress["failures"]` only after all graphs succeed. A cap exception or excessive-failure exit loses the accumulated exclusion trail. Update progress as failures occur.

6. **Gate families — fixed.** T × FALL_GRID, the explicit memoryless-fallback base, restricted-search qualification and revised cost statement match the code. Fable’s replay-mode, G2 reuse and shared-grid-mutation findings are also resolved. Edge reporting has the defect below.

7. **Statistics and escalation — partly fixed; medium.** Bootstrap seeds/counts and the A2-only power interpretation are explicit; the numerical readings remain correct. Failed-P′ retry and single-completed-P′ logic are improved. But [e03h.py:341](D:/Claude/random/wormWars/scripts/e03h.py:341) accepts **any archived qualifying P without validating its upstream hashes**. After S1/G2 reruns, it can authorize P′ on different inputs. Require the qualifying P to match the current chain.

8. **Reporting and binding — partly fixed.** Quartile readings, saved arrays, counts, normalized hashes, DESIGN verification and push-before-stage enforcement are present. Two gaps remain:
   - **Low:** [gate.py:79](D:/Claude/random/wormWars/wormwars/e03h/gate.py:79) stores grids by controller kind. The second `Slow` search at [line 109](D:/Claude/random/wormWars/wormwars/e03h/gate.py:109) overwrites the first grid, so Slow/memory edge flags use the wrong search grid. The smoke record visibly flags source switches that were fixed during that search.
   - **Medium:** [e03h.py:480](D:/Claude/random/wormWars/scripts/e03h.py:480) still accepts committed, pushed implementation changes between stages. The round-1 code-binding gap remains; compare guarded implementation files against the bound commit.

9. **Calibration identities — fixed.** Numeric calibration IDs and distinct `(run_seed, world_id)` identities are now distinguished correctly.

10. **Tests — improved, incomplete.** Missing coverage still includes failed-P′ retry, stale archived-P eligibility, completion-time cap accounting, heterogeneous **B** bootstrap uncertainty and the independent rollout-count oracle. The new heterogeneous test exercises A2’s estimator.

11. **`rollout_brain` counts — fixed.** Counts now propagate through the result object. By inspection, this forwarding change does not alter simulation dynamics.