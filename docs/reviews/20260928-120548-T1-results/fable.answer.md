# Review of T1's results (D090, T1.md §6)

I ran nothing (read-only). I checked the counts against the committed JSONs: 188/188 off, 112/114 multi, 66/74 single, 39/74 sensitivity and 388 hold-outs all match, as do §6's profile figures.

## 1. Honesty and consistency with §3

**The core handling is right.** The failure is recorded as a failure, nothing is moved to class N, and the published path is intact. The problems are in what surrounds it.

**Overclaimed:**
- **"At least 20 rows" is a threshold drawn through discrete points.** Rollouts and brain states tested 20, 160, 320 and 1 280 rows. The observed pattern is non-monotonic (1 fails, 8 passes, 16 fails, 20 passes), which is evidence against interpolating. D082's "two or more agree" failed the same way. State the shapes tested, not a bound.
- **"Fewer than 16 worlds" likewise.** Tested: 1 and 8 worlds per chunk differ; 16, 20 and 64 do not.
- **The narrowed claim is post hoc.** It was fitted to the data that failed the declared claim. Label it an observation, not a claim that "held".
- **Probes are silently dropped.** §3 included brain states. At 1 row, the padded single strain differs from a batch of 4 (`T1_equivalence_compare.json:2132-2155`). The stated mechanism ("2-16 differ from 32") does not explain this. 02's and 03's probes step at 1 row (`probes.py:108`, `measures.py:107`).

**Not traceable to committed files (rule 5):**
- the raw `bmm` check behind the 8-row, 64-row and strain-count statements;
- the chunk-3 rerun. The reclassification itself is legitimate (256 = 85 × 3 + 1), but the committed compare still shows that leg failed;
- "153 of 512" for 2 against 32 strains per chunk;
- the CPU's 1.2e-7;
- the equivalence runs' compute records, about 3.2 GPU-hours. `runs/t1-equivalence/` is not in the tree.

**Wrong as written:** `REPRODUCIBILITY.md:49-50` says only a batch of one differed at 8 and 1 280 rows. §6 says none differs at 8, and the pre-change reference shows none at 1 280 (`T1_equivalence_reference.json:1434, 1764-1787`). T0.md's follow-up omits the CPU finding, while `T0.md:229` still says "CPU: exact under any chunking".

**Declared but not done, undisclosed:**
- starting food was not compared (`t1_equivalence.py:62`; `rollout` does not return it);
- 02's capability probes were not replayed (§4 declared them);
- no CPU leg against the pre-change reference;
- the 64, 128 and 256 strains-per-chunk comparison promised in §2 is not reported.

## 2. Decision 1: adopt padding

**Adopt, on by default, described as a mitigation.** It removes the batch-of-one difference at 20, 160 and 320 rows. At 16 and 1 280 rows it changes nothing, and at 1 row it does not help.

- **No rollout or row padding.** The world is 70% of a Task N tick, and only `eaten` was affected. Row padding would rest on the unestablished threshold.
- **The default is fragile.** The switch is read from `genome.cfg`, and `grid.task_config` pins it off. T1's own Task N proxy is built from that builder, so E1 needs its own builder and a test.
- **Padding's cost is unmeasured.** The profile ran at `101499c`, before the merge, with the switch pinned off.
- **One hazard for E1:** `_regen_food` (`world.py:907-913`) feeds a per-world reduction into the dynamics when `food_regen > 0`.

## 3. Decision 2: the contract amendment

**Right direction, not precise enough.**
- Define composition by primitives: strains per chunk, worlds per strain and weys per world, plus neurons, arena side, device, mode and environment.
- Make the default rule "exact only within the same composition". List cross-composition equality as a table of tested pairs and outputs, generated from the JSON.
- Add it beside §3, dated, and labelled post hoc.
- Record the composition of every evaluation in the bundle.

## 4. Decision 3: E1 and 04a

**"Accept composition-specific results" is sound and should be the default.** Both arms of any paired comparison must share a composition.

- "At least 20 worlds" rests on one tested point: 20 worlds against 2 and 32 strains per chunk.
- Hold-outs at 64 rows and evolution at 8 rows rest only on the uncommitted raw check.
- Add E1's actual shapes to the equivalence script before relying on them.
- At 16 rows any remainder chunk under 32 strains differs from a full one, so keep strain counts equal across chunks.

## 5. Decision 4: closing

**T1.4's second condition is not met,** so T1 cannot close by passing. It can close by a dated amendment. The record should say:

> T1.2's class E test failed as declared: 8 of 74 single-strain outputs differ from the batch reference. T1.4's second condition is not met. Padding is adopted as a mitigation of the batch-of-one path, not as composition independence. T1's engineering closes by this amendment, not by passing its gate.

## 6. Defects

| Where | Defect |
|---|---|
| `t1_equivalence.py:289` | `--compare` reads case descriptions from the saved reference, so the remainder fix at line 143 never reaches it. The committed reference lacks the flag (`T1_equivalence_reference.json:21-25`). |
| `t1_equivalence.py:221` | The guard catches only `chunk1`, which is how chunk 3 slipped through. |
| `t1_equivalence.py:326` | `mean_change` subtracts a float64 mean from a float32 mean. It reports up to 3.1e-7 for bit-identical arrays. |
| `tests/` | No test covers the script's pairing logic (rule 9). |
| `test_t1_padding.py:5-6, 95` | The module docstring says padding cannot change a CPU result, which §6 contradicts. Line 95 cites D087; it should be D090. |
| `test_t1_padding.py:93-102` | Asserts CPU equality between 2 and 3 strains. That depends on the BLAS, so it may fail on other machines. |
| `brain.py:398` | Unsure: under `post_to_pre`, `repeat` makes the transposed view contiguous, which may change the `bmm` path. Untested, and unused today. |

The padding mechanism itself, its cache invalidation and its accounting are correct as far as I can read them.

**T1: close with changes** — (1) commit the raw `bmm` check, the chunk-3 rerun and a cross-chunking leg, or withdraw the numbers resting on them; (2) fix the script's classification and rerun `--compare`; (3) replace both thresholds with the tested shapes, label the narrowed claim post hoc, and state that 1-row probes are not covered; (4) record T1.4's condition as unmet and close by dated amendment; (5) correct `REPRODUCIBILITY.md:49-50` and T0.md's follow-up; (6) disclose the four declared items not done; (7) give E1 its own config builder with a test, and add its shapes to the equivalence script.