# E3b-0 interim report: no trail setting qualified (2026-10-03)

**Status: E3b-0 is stopped at its trail-qualification step, under Amendment 1's rule, "a report and a
redesign, with the owner informed".** E3b-0 is exploratory (plan: `docs/E3/E3b-0-PLAN.md` v3 with
Amendment 1; decisions D175-D178). It has used **0.90 of its 3 GPU-hours** (`compute-record.json`). No seed
or report-maze result exists yet: Stage C, the report and the timing have not run.

## What ran

| Stage | Record | Result |
|---|---|---|
| Stage A: maze size and horizon | `stage-a.json` (41fcb68) | c = 5, H = 2 400 chosen. The four H = 1 200 candidates failed only on the follower's median legs |
| Stage B: the trail grid (24 live settings) | `stage-b.json` (4ac36b6) | **None passed.** Polarity at most +0.02 against 0.3; nose range 0.26-0.46 against 0.9; the gradient failed in 2 settings (0.797) |
| Stage B2: Amendment 1's rule | `stage-b2.json` (19a1b12) | **None qualified.** No setting met both the high-level cap and a positive trail effect |

**Stage B2's guard held.** It requires its shared-trail rates to equal Stage B's rows exactly, as evidence
that Stage B's records can be reused on the amended code; all 24 did.

## What was found

**1. The trails help the scripted follower, with a peer effect.** At Stage B's highest-rate setting (μ 0.005,
λ 0.02, δ 0.05, d₀ 0.571), on the 256 selection mazes (`stage-b2.json`), the follower's later-leg rate
rises by **+3.54 legs per 1 000 ticks [2.93, 4.18]** over no trail (3.94). On mazes 0-63 at the same setting
(`development-records/stage-b-diagnosis.json`):

| Contrast | Mean | 95% interval |
|---|---|---|
| own − none | +1.09 | 0.39 to 1.92 |
| shared − own | +1.75 | 0.93 to 2.64 |

These come from the selection mazes at a setting picked as the maximum, so they are optimistic.

**2. The registered polarity test was not passed by this follower.** Facing away from the source it did not
pass on 64 mazes, even on a reference slope (`stage-b-diagnosis-2.json`). Facing the source, the real trail
added +0.16 at that setting, against a ceiling of +0.23 on these mazes. Behavioural polarity is reported,
not claimed.

**3. Trails strong enough to help push the seeds' inputs out of their modules' working range.**
- **The modules:**
  - E's active K_D, its turn gain with the module active, is 35.6 at levels 0.001-0.02 and 31.6 at 0.35.
    It then falls: 28.0 at 0.5, 15.0 at 1.0, 2.5 at 2.0;
  - S3r3's module A reads 29.3 at 0.35 and 0 from 1.0 (`stage-b-diagnosis-2.json`,
    `stage-b2-diagnosis.json`).
- **The trails, in `stage-b2.json`:**
  - every setting with a clear trail effect puts 6-54% of the follower's unoccluded positive on-route inputs
    above 0.35;
  - the two settings under Amendment 1's cap (5%), the weakest trails, show no effect: +0.23 [−0.13, 0.61]
    and −0.16 [−0.52, 0.21];
  - the nearest misses (6.0% above 0.35) give +0.73 [0.31, 1.20] and +0.56 [0.11, 1.04]. Both lower bounds
    are below criterion 3's 0.5, so these would fail later anyway.

**4. Lighter, long-lived trails do not escape this** (`stage-b2-diagnosis.json`, mazes 0-63). Persistent
trails (μ 0.005 or 0.01, λ 0.02, δ 0.05) with d₀ cut 4-16 times meet the cap, but the follower's effect falls
to between −0.31 and +0.52, with every interval including 0.

## The hypothesis (not yet tested)

The follower turns by 32 × (L − R), and a seed's module by K_D × (L − R), with K_D about 35. The two gains
are close. With linear sensing, a useful turn needs an absolute left-right difference of a few hundredths.
Along a trail such differences occur only where the overall level is high, and there the shared level drives
both of a module's noses into saturation. Lower levels keep the modules in range but leave the differences
too small to steer by. If this is right, **no choice of trail constants alone can qualify**. The remedy is on
the sensing side, or the trail claims go.

## The options for the redesign (for review)

1. **Compressed trail sensing.**
   - **How:** the nose reads s × ln(1 + x / x₀) of the trail value x, plus the scent, instead of 0.35 × x.
     The trails themselves stay linear, so the peer controls, which act on the fields, keep their meaning.
   - **What it does:** small differences at low levels are amplified, and high levels stay within the
     modules' range.
   - **What it needs:** an engine change behind a flag, with equivalence while it is off; a bounded search
     over x₀ (and s) with Amendment 1's gates; and the follower's gain fixed in advance.
   - **It changes the organism's sensing model,** which must be said.
2. **Drop E3b-1's trail claims and keep its gate,** the tuned colony against the frozen seed in mazes. This
   branch is already in the plan's failure table. E3b-1 would then not test trails.
3. **Not recommended:**
   - a high-gain follower: it would qualify a signal that the seeds, with their fixed gain near 35, could not
     use;
   - qualifying the modules at higher levels, where their steering collapses.

## Records
- Stage records and per-setting arrays: this folder.
- The diagnoses: `development-records/`.
- The reviews: `docs/reviews/20261002-E3b-0-stage-b/` and `docs/reviews/20261003-E3b-0-amendment-1/`.

## Corrections
- **2026-10-03:** commit 95a6bdc's message says that under the cap the follower's trail effect is "+0.15 to
  +0.52 legs per 1 000 ticks". The record (`stage-b2-diagnosis.json`) gives −0.31 to +0.52: the d₀/16 rows
  are −0.31 and −0.28. Every interval includes 0, as stated.
- **2026-10-03, after the redesign review** (`docs/reviews/20261003-E3b-0-redesign/`). The reviewers
  corrected six statements above.
  - **"Trails strong enough to help push the seeds' inputs out of their modules' working range" misreads
    K_D** (Fable). K_D is the response to a fixed absolute difference, and along a linear trail the
    difference grows with the level. The relevant quantity is K_D × level, the response to a relative
    difference. For E it is:

    | Level | 0.35 | 0.5 | 0.7 | 1.0 | 1.5 | 2.0 |
    |---|---|---|---|---|---|---|
    | E: K_D × level | 11.1 | 14.0 | 15.8 | 15.0 | 9.7 | 5.0 |

    So E's steering does not collapse above 0.35. S3r3's module A does, at 1.0. The option "qualifying the
    modules at higher levels, where their steering collapses" was dismissed on that misreading.
  - **The hypothesis is not established** (both). Several things are unmeasured:
    - the follower's 0.005 switch between steering and exploring;
    - the turn it makes when one nose is occluded;
    - the joint left-right levels and differences;
    - the scent's share of the readings.

    "No choice of trail constants alone can qualify" is withdrawn. It is a hypothesis.
  - **"Both lower bounds are below criterion 3's 0.5, so these would fail later anyway" overreaches**
    (Astra). Criterion 3 is read on the untouched report mazes.
  - **The light-trail row at μ 0.01, d₀ 0.143 does not exclude a useful effect:** +0.52 [−0.13, 1.28]
    (Astra).
  - **The no-trail baselines differ by more than the maze set** (Astra). On the GPU (`stage-b2-none.npz`)
    they are 3.944 on 256 mazes and 3.251 on mazes 0-63; on the CPU, 3.327 on the same 64. The backend and
    batch differ too. Each diagnosis pairs with its own baseline, so its contrasts stand.
  - **"with a peer effect" (finding 1) is too strong** (Astra). shared − own in the later-leg rate is not
    the registered peer measure, the first-B time of later discoverers.
