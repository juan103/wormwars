**Verdict: bind and run.** Every round-2 finding from both reviewers is fixed in the code and stated in PILOT.md draft 4. I found nothing the fixes broke or introduced that would mislead G1, S1, G2, P or the sizing. Draft 4 matches the code at every point I checked and is ready to bind as it stands.

## 1. Round-2 findings, checked against ff1fd31

| Round-2 item | Where it is fixed | Verdict |
|---|---|---|
| Fable 2 / Astra 1: end-of-stage cap double-counted | `Clock.over_at_end` reads the aggregate alone (`scripts/e03h.py:151-153`); `acct.recorded` writes the aggregate before it is read (`accounting.py:318-320`); `check()` still adds the running stage's time (`registration.py:142`); test `:266` | correct, complete |
| Fable 3 / Astra 8a: edge flags noisy; second Slow search overwrote the first's grid | each unit returns its own flags (`gate.py:82-88`); `edges()` skips the switches and single-valued keys and judges against the registered grid (`:49-60`); `BOUNDS` adds T = 1; the fallbacks keep their base's flags (`:94-95, :104`); tests `:120, :132`; the CUDA smoke record shows no `use_*` flags (`gate.json:167-207`) | correct, complete |
| Fable 4: a refused rerun moved the record first | hashes, `require_same_code`, upstream reads, `_eligible` and `ck.check()` all precede the move (`:516-539`); test `:250` | correct, complete |
| Fable 5 / Astra 3: sampler CPU seconds in the projection | S1 times the sampler and calibration apart (`:266-291`); `_projection` counts calibration only and reports the sampler as not counted (`:490, :495`); PILOT.md §5.5; test `:278` | correct, complete |
| Fable 6: `rollout_brain` untested | oracle test stepping a World directly, under level and sham, against `rollout` and `rollout_brain` (`test_e03h_food_fell.py:292`) | correct |
| Fable 7: failure limit unregistered | PILOT.md §3 "more than 10 failures stop S1"; code raises on the 11th (`:270`) | correct |
| Fable 8: status line | "final (draft 4) … bound by `pilot/bind.json`"; no commit hash in the text, so binding needs no later edit | correct |
| Astra 5: failure trail lost on a stop | the list is live in `progress` from the first iteration (`:265`); the failure path copies progress into the record (`:554`); test `:301` | correct, complete |
| Astra 7: archived P on an older chain authorised P′ | the qualifying P must carry the current G1, S1 and G2 hashes (`:353-356`); test `:234` | correct, complete |
| Astra 8b: implementation could change between stages | `bind` records HEAD (`:227`); every later stage runs `require_same_code(bound_commit, CODE)` (`:521`), with the guarded-dirty check covering the working tree; `CODE` excludes only `bind.json`; test `:291` | correct, complete |
| Astra 10: test gaps | failed-P′ retry, stale-chain P, end-of-stage cap, heterogeneous B intervals, rollout-count oracle all present | correct |

## 2. Nothing broken; four informational notes

1. **Informational. The pilot's cap clock counts the sampler's CPU seconds.** S1 runs the sampler inside `recorded(default="measure")`, so its wall time enters `seconds_timed` and the 1.0 h clock, while the projection excludes it. PILOT.md §1 defines the cap by T0's accounting, so this is as registered, and the direction is conservative by a few minutes. No change needed.

2. **Informational. A new binding invalidates the whole chain.** G1's upstream is `bind.json`'s hash (`:69`), so a re-bind makes G1 stale and forces G1, S1 and G2 again under the same cap. That is the right behaviour for a bound implementation, but the sizing in PILOT.md §1 (about 0.75 h with step 0 and P′) leaves no room for a full redo. Worth knowing before binding; not a defect.

3. **Informational. "Once" for P′ is chain-agnostic.** `_escalation_allowed`'s second check (`:360`) blocks on any completed P′, even one on a replaced chain. Conservative, and consistent with §5.4's "once".

4. **Low, test fragility.** `test_binding_fixes_the_implementation` diffs against the literal `4fae0d1`. CI fetches full history (`tests.yml:19`), so it passes there, but a squash or rebase of `roadmap`, or a shallow clone, turns it into a `CalledProcessError`. Not a pilot concern.

## 3. Readiness

PILOT.md draft 4 matches `scripts/e03h.py` and `gate.py` on every registered point: the order of the checks (§1), the cap's units of work, the family construction and the new edge rules (§2), S1's seeds, calibration, genomes, worlds and the failure limit (§3), P's reuse of S1's level scores at 0.25, the decile, reliability, A2's power, the decile shift and P′'s chain condition (§5.1-§5.4), the projection without the sampler and the cut order (§5.5), and the seeds and banks (§7). The CUDA smoke records at `runs/e03h-smoke-cuda/pilot/records/` carry `ff1fd31`, clean, with all five stages completed. Bind it.