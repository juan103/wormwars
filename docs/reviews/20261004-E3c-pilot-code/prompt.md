You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Code check: E3c's pilot runner, before about 2.5 GPU-hours

You are reviewing code in the WormWars repository (the current directory), read-only. The design you
approved is `docs/E3/E3c-DESIGN.md` v2.1 (D200 in `DECISIONS.md`). Its §5 is the exploratory pilot. That
pilot is now implemented and is about to run on the GPU.

**What to read:**
- `wormwars/e3/assembly.py`: the arms' draws and mutation masks (§3-§4).
- `scripts/e3c.py`: the pilot stage, built on E2's stage frame (`scripts/e2.py`).
- `tests/test_e3c_assembly.py`, `tests/test_e3c_runner.py`: what is tested.
- The `factor` argument added to `wormwars/e3/tuning.py` `scales` (its default is unchanged).

Helpers it reuses:
- `wormwars/e04a/evolve.py` `evolve_batch`;
- `wormwars/e3/samplers.py` (`b_task_draw`, `ga_draw`, `with_selector`, `stage2_scales`);
- `wormwars/e3/maze_organisms.py`, `wormwars/e3/maze_runs.py`, `wormwars/e3/probe.py`;
- `scripts/e3b1.py` (E3b-1's runner, which this mirrors) and `scripts/e3a.py` `generation0_offsets`.

**What a CPU smoke showed (`python scripts/e3c.py pilot --smoke --device cpu`; toy sizes):**
- It completes, and the E3c tests pass.
- The draws are mirror-symmetric: tied left/right biases, antisymmetric output edges. So at level noses every
  turn offset is exactly 0, for every arm. The runner therefore logs E3a's pair, the offset and module A's K_D
  at q = 0, as `generation0_offsets`. The offset serves as a check.

**Please check, and answer each:**
1. **The draws and masks against §3-§4:**
   - S-mod is B-task's draw projected onto E's mask, with 65 mutable scalars;
   - S-dense is the full draw on the carrier with W2, with 171;
   - P-sel is the 13 selector parameters drawn by `ga_draw`, with the modules frozen;
   - every arm is at factor 1.0.

   Is anything mutable that should be frozen, or the reverse? Is the per-strain draw independent and
   reproducible?
2. **The pilot against §5:**
   - the runs, the seeds and the batching. S-mod and P-sel share one batch on the seed's graph; S-dense
     runs in its own batch;
   - 100 generations × 8 mazes;
   - checkpoints every 25 generations and at generation 99, on a 128-maze block (ids 7600-7727), disjoint
     from earlier blocks;
   - the training ids (base 30 000 000, span 10 000 000);
   - the references (W2 alone and the seed) on the same block;
   - the criterion (strictly above W2 alone + 1 visit per wey, at any checkpoint);
   - the branches (incomplete → inconclusive).
3. **Units:** do the checkpoint `validation_mean`, the generation-0 counts and the references' `visits` share
   one unit, visits per wey (colony mean)? Is the floor comparison right?
4. **Anything that would make the 2.5 GPU-hours worthless:** a wrong organism for an arm, a mask leak,
   wrong access mode (it must be the shared-trail world), a missing record, or a cap that cannot stop the run.
5. **Your verdict:** "run it", or "fix first" with a numbered list. Keep findings to real defects;
   style is out of scope.

Be concrete: cite the file and line for each finding.
