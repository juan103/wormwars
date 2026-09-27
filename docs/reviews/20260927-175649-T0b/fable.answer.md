## Scope and limits

I had no shell or git access. I could not run the tests or diff `f6af625` against its parent, so "unchanged" below means "by reading the current tree, against what I read in my previous review".

## 1. Plan v2

My must-fix items M1–M5 are all resolved, and S1–S8 are all adopted. Astra's points on timing labels, nested categories, finite residuals and D064's wording are in too. Nothing in v2 is wrong.

Three small amendments, none needing another review round:
- **Accounting must be pure measurement.** Add a test that scores are bit-identical with the ledger on and off, and that no RNG is consumed (§1).
- **Migrants between half an island and its full size.** §6 rejects `migrants >= island size`, but in between, an island overwrites some of its own top strains with immigrants. Forbid it or document it.
- **§2 asks for champion pairing "by genome hash, not nickname",** but `GenerationLog` stores only `best_nickname`. Add a `best_sha256` field, or change the plan's wording.

## 2. Item 1's code

### Paths you asked about
- **Non-jitter rollout:** unchanged. `_keyed_uniform` is only reached at `world.py:524`; `__init__` only adds an int64 tensor of world ids (`world.py:331`).
- **One-island evolution:** unchanged apart from the champion. `breed` draws `randint` then `mutate` in the same order, and `Genome.cat` is the same `torch.cat` per field (`evolve.py:77-85`).
- **Champion:** `evolve.py:164-165` uses the same `genome` and `fit` as the last log entry, so pairing holds by construction in every mode.
- **Loading committed genomes:** correct for non-Dale files. I found no `"dale": true` in any JSON; the `.npz` metadata is compressed and I could not read it.

### Jitter hash: sound for this use
- **Arithmetic is correct.** `_mul32` never exceeds about 2^48 in int64 and equals x·c mod 2^32. `_hash32` is lowbias32 and matches `_mix32`. Shifts are on non-negative values.
- **Uniformity is fine.** The top 24 bits divided by 2^24 are exact in float32, the same resolution as `torch.rand`.
- **Distinct worlds never share a stream** within a run, because each step is a bijection. Distinct ticks of one world never collide.
- **Residual 32-bit structure is harmless.** Two (world, tick, stream) states that differ only in the low ~10 bits give point-permuted copies of the same noise. I estimate tens of such pairs among about 10^8 in a typical probe set; they are isolated, not systematic.
- **Bonus:** the noise is now identical on CPU and CUDA.
- **Caveats:** run seed bits above 32 are dropped. The point index depends on `n_weys` padding for swarm 1 and up, which is irrelevant to single-swarm probes.

### Should fix
1. **No test pins the hash.** `test_t0_pairing.py:155` checks invariance only, so a wrong `_mul32` would pass. Add `_hash32` against `_mix32` at edge values (0, 0xFFFF, 0x10000, 0xFFFFFFFF), mean and variance of the uniforms, and jitter radius ≤ R.
2. **`Genome.assign` broadcasts silently** (`brain.py:177`). A one-strain `src` written to several slots duplicates it; `_migrate` reaches this with population 3, 2 islands, 2 migrants. A Dale mismatch either crashes or drops the signs. Check `src.n_strains == len(idx)` and Dale parity, as `cat` does.
3. **The champion test compares nicknames on CPU** (`test_t0_pairing.py:136`). A nickname is about 12 bits. Compare all `PARAMS` of `r.champion` with the argmax strain of the loaded population.
4. **D066 overstates the champion evidence.** "Each defect was confirmed by a failing test" is not true for the champion: that assertion passes on CPU before and after. It is a by-construction change.
5. **Tests the plan requires are missing:** snapshot and holdout pairing (§2), and `mutate` with non-zero sigma leaving other fields and `dale_sign` unchanged (§3).
6. **The committed-genome test covers N2 only** (`test_t0_pairing.py:185-190`). The hash needs no spec, so check every genome `.npz` from its stored arrays, SH and RD included.
7. **Population files are checked by nickname only** (`genomes.py:223`). Store per-strain sha256 in new files.
8. **The scan test covers `wormwars/` only.** Hand-built genomes remain in `experiments/02b-champion-analysis/analyse.py:282,319`, `scripts/bench_brain.py` and `scripts/exp03.py:358`. All keep `dale_sign`. List them as known exceptions.

### Worth checking once
- **Published champions against their logs.** For each run with both files, does the champion's nickname equal the last `best_nickname`? That measures how often the old re-evaluation picked another strain, which the §6 regression needs to know.
- **`gpu_seconds` no longer includes the final re-evaluation.** Note it where old and new timings are compared.

### Minor
- `with_params` does not clone the tensors you pass in, so its "never aliases" docstring holds only for fresh tensors. All current callers pass fresh ones.
- `flat()` still hand-lists four fields (`brain.py:281`), so a future field would not be hashed.
- `evolve` with zero generations now fails on an undefined `fit`.

### 03r
The live run is one process with its modules already imported, so the edits on disk do not reach it. A restart from this tree would be refused by `check_resumable`, because HEAD has moved from `7c146fc`. Keep a worktree at `7c146fc` in case it crashes.

## 3. D066's claim about 02's jitter estimates

Correct as worded, with three qualifications.
- **Same noise law is assumed.** The claim holds if the old code also drew r = R·√u and θ = 2πu′, independent per point and tick. I could not see the old code; confirm it from the diff.
- **The pairing defect never biased a 02 number.** Every 02 jitter call scored one champion or one scripted policy (`probes.py:70`, `exp02.py:172,264,379`), so batch position never mixed strains.
- **Expectation is not robustness.** Each 02 estimate uses one noise realisation. T0 jitter 3 on N2 is +0.050 [+0.006, +0.103] (`RESULTS.md:82`), and a new realisation could move that lower bound across zero. 02's jitter claims are exploratory and hedged, so no conclusion depends on it.

D066 should also name the frozen artefacts that current code can no longer regenerate: `probe_validation.json` (hash registered in `PREREGISTRATION.md:68`), the `history_probe` block of `diagnostics.json`, and the champions' jitter scores. They remain reproducible from 02's own commit; say which one.

T0 plan v2: confirmed (with the three amendments above).
item 1: accept (code correct on every used path; should-fix 1–6 are owed before the T0 gate).