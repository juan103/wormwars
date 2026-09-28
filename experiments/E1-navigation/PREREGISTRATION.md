# E1: the positive control for navigation. Pre-registration (v4)

**Status:**
- Written 2026-09-28. Astra 6 and Fable 5.1 reviewed it twice, and every change they asked for is
  adopted:
  - v1 (`f83bd19`, `docs/reviews/20260928-181005-E1-prereg/`): "revise" (D095);
  - v2 (`a6437be`, `docs/reviews/20260928-183315-E1-prereg-confirm/`): "revise" (D096);
  - v3 (`f63cdaa`, `docs/reviews/20260928-185310-E1-prereg-final/`): "revise" (D097).
- **The formal pilot and gate come after this registration, and after its public push,** with the
  earlier exposure disclosed in §7. It is the first time in this series that a registration is
  public before its formal measurements.
- **The binding commit** is the commit the pilot records in the freeze. The pilot refuses to run
  unless:
  - the tree is clean, this file included;
  - the commit is already pushed.

  The gate refuses to run if the code or this file differ from the pilot's commit.

**Design:** [`docs/E1/DESIGN.md`](../../docs/E1/DESIGN.md) v2.1, agreed by Astra 6 and Fable 5.1
(D077, D078). This file fixes what the design left open, and for the positive control it holds
where the two differ.
- **This registration fixes more than the design did.** The design let the pilot set the gate's
  margins, shares and sample sizes. They are fixed now, before any formal data, and the pilot sets
  only σ, the own-body level, the tuned controls and the navigator, each by a rule stated here.
- 04a, the evolved navigator, gets its own pre-registration after the gate.

**Code:**
- Task N lives in `wormwars/world.py` (the `navigate` task) and `wormwars/e1/`.
- The runner is [`scripts/e1.py`](../../scripts/e1.py). Its `REGISTERED` constant holds every number
  below.
- The runner applies every rule mechanically.
- **How the guards are tested:**
  - through the stage commands themselves, with a fake rollout (`tests/test_e1_commands.py`): the
    gate's completed, cap-during-arms, cap-after-analysis and crash paths; the once-only refusals;
    the committed-freeze check when the freeze is untracked; and the pilot's refusal to run over a
    freeze;
  - as functions (`tests/test_e1_script.py`): the freeze re-derivation, including malformed
    supporting measurements; the code and environment comparisons; the CPU, GPU, dirty, unpushed
    and pin refusals; the cap clock; markers, LF writing and smoke rebinding.
- **Not exercised by any test:**
  - the live `git fetch` and push check, and the GPU preflight. These run in the guarded smoke run
    on the binding commit (§5);
  - the committed-freeze check's modified-freeze branch. It first runs at the formal gate;
  - the pilot's own-body zero-sample refusal.

## 1. The question

Can a scripted navigator, with the declared body and sensors, reach **moved targets** on **unseen
layouts**, better than **simple movement baselines**, and **because of the cue**?
- Arrivals alone are not enough: good search also collects hits. The gate asks whether target
  information improves arrival.
- One valid passing navigator is enough to establish that the task can be done, and to start 04a.

## 2. Task N

**The world:**
- one swarm of one wey per world, and the boundary wall only;
- no food, hazard, pheromone or combat, so the arena side is 24;
- **energy is off:** no metabolic drain, movement cost or eating, so the wey lives for the whole
  horizon of **300 ticks**.

**The target** is a sensing-only scent source: A exp(-d² / 2σ²), truncated at ceil(3σ) cells along
each axis. It is added to what the wey senses, never to the food field, so the energy ledger stays
exactly balanced. Fixed now:
- **amplitude A = 1.0, with the sensing scale 0.35.** The peak input current is 0.35, against a
  clamp of 5. 0.35 is 02's food sensing scale, so a brain's food neurons see currents of the order
  they saw in 02, far from the clamp;
- **radius R = 1.5:** a target is reached when the head is within R of its centre;
- **separation D = 8:** consecutive centres, and the first from the spawn, at least D apart;
- **no maximum separation,** and centres at least **3** cells from the wall ring.

**The target sequence** is a function of (run seed, world id, k) only, from a random stream of its
own. Every controller faces the same destinations, and controller state persists across
relocations.

**The score** is the number of targets reached in 300 ticks, an integer. **The run seed** is
1 100 001.

**World ids:**
- pilot 996 000 000+, tuning 996 100 000+, gate 996 200 000+, 04a's hold-out 996 300 000+;
- the ranges are disjoint from each other and from earlier experiments;
- **every stage starts at index 1 000 of its range,** past every world that development touched
  (§7);
- the freeze and the gate record the exact ids used.

**Execution:**
- **CUDA only,** on one RTX 5080, in the pinned environment. The runner refuses the CPU and any other
  GPU for formal stages.
- **The pinned environment is enforced** before either stage: Python 3.13, and the torch and numpy
  versions pinned in `requirements.txt`. `requirements.txt` is itself a guarded file.
- **The environment is recorded at the pilot and must match at the gate:** Python, NumPy, Torch,
  CUDA, the GPU, and the sha256 of both the connectome source spreadsheet and its parsed cache.
- **The freeze and the gate record the resolved task configuration.**
- Each controller is one strain on all of a stage's worlds, in one rollout. Scripted controllers
  have no neural batch.
- **Reproducibility:** the counts are exact integers, but CUDA default mode does not guarantee
  repeatable trajectories (`docs/REPRODUCIBILITY.md`), so no exact replay of the gate is claimed.
  The gate runs once, and its per-world counts and full event tables are committed.

## 3. The pilot (`e1.py pilot`), on pilot and tuning worlds only

It writes `experiments/E1-navigation/freeze.json`, with LF line endings, and the gate hashes it
normalised to LF.

1. **σ, the scent's width:**
   - candidates **2, 3, 4 and 6**;
   - on **256 pilot worlds**, at each world's first **5** leg starts (the spawn, then each previous
     centre), it measures the next target's scent from the actual sampled field;
   - **the rule:** the smallest σ at which at least **90%** of leg starts read at least **5% of
     A**;
   - **if none qualifies:** σ = 6, flagged. The flag is reported as a limitation, and it changes no
     other number.
2. **The own-body collision level:**
   - on 64 pilot worlds, 100 ticks at speed 0.5 and turn 0.2;
   - the largest front or front-right collision current the wey's own body produces, while its
     head is at least 3 cells from the wall;
   - the number of samples is recorded, and the pilot refuses to continue if there is none.
3. **Generation 0:**
   - 256 random N2 genomes on 64 pilot worlds, in one chunk (256 strains × 64 worlds × 1 wey);
   - the share scoring zero on every world, and the mean count.
   - These are descriptive, for 04a's pre-registration, and apply to this composition only.
4. **Throughput** in 04a's evolution shape: 32 strains × 8 worlds × 1 wey, and 4 and 8 such
   batches together, 3 repeats each, on world ids 0-7, outside every E1 range.
5. **Clamp saturation:** peak input current against the clamp. It is zero by construction.
6. **Tuning, on 256 tuning worlds.**
   - Each grid point is one strain, in chunks of 64. The last chunk may be smaller, and it is
     recorded.
   - The first maximum of the mean count, in grid order, wins.
   - Every grid point's mean is kept in the freeze, with the winner's share of episodes with at
     least 1 and at least 2 arrivals.

   | Control | Grid |
   |---|---|
   | S-const (stereo steering at one speed) | k ∈ {1, 2, 4, 8, 16, 32, 64, 256, 1024, 8192} × speed ∈ {0.4, 0.6, 0.8, 1.0} × turn ∈ {-0.2, -0.1, 0, 0.1, 0.2} |
   | M-avg (memory kinesis on the stereo mean) | slow, fast ∈ {0.4, 0.7, 1.0} × threshold ∈ {0, 0.02, 0.05, 0.1} × turn ∈ {0, 0.1, 0.2} × fall turn ∈ {0.4, 0.7, 1.0} × fall threshold ∈ {0, 0.001, 0.005} |
   | K (level kinesis) | slow, fast ∈ {0.2, 0.5, 0.8, 1.0} × threshold ∈ {0.02, 0.05, 0.1, 0.2} × turn ∈ {0.05, 0.1, 0.2, 0.4} |
   | constant (speed × turn; covers circling) | speed ∈ {0.2, 0.4, 0.6, 0.8, 1.0} × turn ∈ {-0.6, -0.5, …, 0.6} |
   | random walk (persistent turn) | speed ∈ {0.4, 0.7, 1.0} × rate ∈ {0.2, 0.4, 0.8, 1.0} × persistence ∈ {0.5, 0.8, 0.9, 0.95, 0.99}; noise seed 0 |
   | wall-follower (collision inputs, wall on the right) | speed ∈ {0.4, 0.7, 1.0} × seek turn ∈ {-0.1, -0.2, -0.4} × avoid turn ∈ {0.4, 0.8, 1.0} × threshold = own-body level + {0.05, 0.1, 0.2, 0.4, 0.8, 1.6} |

   - **S-const is also tuned with k ≤ 32** and reported. That version is non-gating.
   - **The oracle** steers at the true target (k = 2, speed 1). It is the ceiling, not a control,
     and it is not tuned.
   - **The random walk's noise** follows the batch's shape, not world identity. So each grid point
     meets different noise, and the tuned walk is specific to this chunking. It is disclosed, not
     changed: a blind baseline needs no common noise.
7. **The navigator:** of the tuned S-const and M-avg, the one with the higher tuned mean. On a
   tie, S-const.

**The pilot may not:**
- use gate worlds;
- choose anything by hand;
- run twice. Its start marker is exclusive.

**The freeze** is committed and pushed before the gate. The gate re-derives from the freeze's own
rows:
- σ;
- every tuned winner, with its grid and the first-maximum rule;
- the small-gain grid;
- the oracle;
- the navigator.

It refuses any mismatch.

## 4. The gate (`e1.py gate`): 1 024 gate worlds, used once

Each rule compares per-world counts on the same worlds. **The interval** is a one-sided 95% lower
bound: the 5th percentile of 10 000 bootstrap resamples of worlds (seed 0) of the mean of a
per-world quantity.

1. **Absolute reliability:** at least **820 of the 1 024** gate episodes (80%) reach at least **2**
   targets. The second arrival tests relocation. This is a criterion on this sample, not a
   confidence statement about a population.
2. **Beats the baselines:** for each of the tuned **constant**, **random walk**, **wall-follower**
   and **K**, the lower bound of the per-world difference (navigator − baseline) exceeds **0.5
   targets per episode**. No ratio is taken against a near-zero baseline.
3. **Uses the cue:**
   - the navigator is also run under the `mirrored` probe: the scored target is unchanged, but its
     scent is read at the point reflection, a consistent decoy;
   - the per-world contrast **0.5 × real − mirrored** must have a lower bound **≥ 0**. That is, the
     count falls by at least half, with its uncertainty counted (Astra, D095);
   - the count may fall below the blind level, because a navigator parks at the decoy.

**The outcome** is all three together (an intersection, so no multiplicity correction). The
wording is fixed:
- *"E1 positive control: passed"*;
- *"E1 positive control: not passed"*, followed by the failed rules;
- *"E1 positive control: not completed (the registered cap was reached)"*;
- *"E1 positive control: not completed (the run stopped)"*: an exception or an interrupt, with the
  error recorded.

**Reported, non-gating:**
- **for every tuned controller:** its real count and its `constant` probe count, as its own blind
  level. That includes the navigator, the unselected navigator, and S-const at k ≤ 32;
- every mean as a fraction of the oracle's;
- first-arrival success;
- latency, as the mean of min(first-arrival tick, horizon), so failures count;
- the median time of **finished** legs;
- **path efficiency:** the head's straight-line displacement from where a leg began to where it
  reached the target, over the path it took, for finished legs. It is at most 1 by construction.

**Committed with the result:**
- every arm's per-world counts;
- the full event tables (`gate_events.npz`): per world and target, the activation and reach ticks,
  the path length, the target's position, and the head's start and end;
- the gate world ids.

## 5. Budget, interruption and deviations

**The cap: 8 GPU-hours** for the pilot, tuning and gate together.
- It is counted with T0's accounting (synchronised wall clock), registered in code, and never
  extended.
- **The clock:** earlier attempts' recorded time plus the current process's time since the script
  was loaded. That starts slightly before the accounting's timed category, so it counts slightly
  more than the accounting does.
- **When it is checked:** before every rollout and every measurement loop, and once more after all
  analysis, just before a result is written.
- **Outside the decision:** one rollout in flight can overrun it, and writing the outputs (the JSON
  and the compressed event tables) comes after the final check. Both are seconds against a cap of
  hours; they are recorded in the compute record but cannot change the decision.
- **The compute record** is copied to `experiments/E1-navigation/compute-record.json` (a name git
  does not ignore) and committed with each stage's output, with the stage's start marker.

**Before the pilot:** one guarded smoke run, on the pushed binding commit. It uses smoke sizes and ids
0-9 999, keeps every formal guard (CUDA, the GPU, clean and pushed, the same code and environment),
and writes only to `runs/e1-smoke/`. It exercises the live push check and the GPU preflight. Its
result is not data. **If it fails,** the fix is committed with a dated note in DECISIONS.md, and
the later, pushed commit binds.

**A stage's start marker is written only after a preflight:** the connectome, the interface, and one
real operation on the GPU. So a trivial failure does not spend the stage.

**Interruption.** Each stage writes an exclusive start marker before touching its worlds, and a
started stage is never silently rerun.
- **A pilot that stops without a freeze:** it is rerun only under a dated amendment, on the next
  unused offset of the pilot and tuning ranges. The failed attempt is disclosed.
- **A gate that stops without a result, or hits the cap:** it is reported as not completed, with the
  matching fixed wording.
  - **Every completed arm's counts and events are kept:** in memory for an exception, an interrupt
    or the cap, and on disk after every arm (`gate_partial.npz`), for a process that is killed.
  - Any new attempt needs a new registration, on unused gate worlds.
- **The order of the gate's outputs:** the outcome (`gate.json`) is written before the event tables,
  so a failed events write cannot lose it.

**Deviations** are reported in the results, and none is made silently.

## 6. If no navigator passes

The design's rule applies:
- the implementation, the signal availability, constant-speed steering and the search behaviour
  are diagnosed first;
- the body or sensors change only if that diagnosis points there: head oscillation, or a stronger
  or wider cue;
- any change gets a new pre-registration;
- nothing is ever retuned on the gate worlds.

## 7. What was seen before this registration (disclosure)

**Development used E1's worlds twice, before the smoke runs were moved off them.** As far as the
records and the session's command order show, no gate world was ever evaluated. The basis for each
statement is given.
1. **The first smoke run** of the pipeline used E1's ranges at tiny sizes. It ran on uncommitted
   code at a 40-tick horizon, with each grid cut to its first two values:
   - coverage on the first 8 pilot worlds;
   - the own-body level on the first 4;
   - generation 0 with 4 genomes on the first 4;
   - tuning on the first 8 tuning worlds.

   It printed every tuned mean as 0.0, and the oracle's as 0.5. Its gate stopped before any
   rollout: it could not find the freeze, which the smoke run had deleted. The compute records
   confirm it: the gate attempt at 16:07:29 UTC built no world.
2. **A debug run** computed the σ measure on the **first 32 pilot worlds,** outside the accounting,
   so it has no compute record. The share of leg starts at or above 5% of A was:
   - σ = 2: 0.00;
   - σ = 3: 0.00;
   - σ = 4: 0.33;
   - σ = 6: 0.875.

3. **The second smoke pair (16:08:22 and 16:08:27 UTC),** found in the compute records by Fable. The
   pilot built 52 + 1 000 worlds, and the gate completed with 208 worlds under `final` (13 arms ×
   16).
   - It ran in the same command that first switched smoke runs to ids 0-9 999, right after that
     change. So its gate used smoke ids, not gate worlds.
   - **The basis is the session's command order.** No record holds that pair's world ids. A later
     smoke run records its ids: 0-7 for the pilot and tuning, and 0-15 for the gate.
4. **The development records are committed:** `development-records/` holds every smoke attempt's
   compute record, and the later smoke run's recorded ids (`smoke-ids.json`).
   - If it had used E1's ranges, it would have touched the first 16 gate worlds, which the index
     1 000 offset also skips.

**Handling:**
- **Every stage now starts at index 1 000** of its range, past every touched world.
- **Smoke runs now use world ids 0-9 999,** outside every E1 range. They exercised every stage, and
  no quantity from them enters this registration.
- **The σ rule is unchanged,** and it was fixed before either run: the candidates, the 5% floor,
  the 90% share and the fallback were in `REGISTERED` before the debug run. That ordering is a
  development-history statement: `REGISTERED` and this file first appear together in `f83bd19`.

**What geometry says about σ** (Fable; corrected by Astra, D096):
- the scent reaches 5% of A at a distance of about 2.45 σ, so at 4.9, 7.3, 9.8 and 14.7 cells for
  the four candidates;
- consecutive targets are at least D = 8 apart, so σ = 2 and 3 can never qualify;
- σ = 4 can qualify only if nearly every leg is between 8 and about 9.8 cells, which is possible
  but improbable. Its expected share is about 0.29;
- **so σ = 6 is strongly expected, not certain.** The rule is applied as registered. No candidate
  was added and no share was lowered after the debug run.
- **If σ = 6 is flagged,** fewer than 90% of leg starts read at least 5% of A. The floor is a
  reporting criterion, not a cutoff for any controller, so it does not say how often a controller
  can steer.

## 8. What E1 establishes, and what it does not

**If passed,** E1 establishes that the declared body and sensors support navigation to a localised,
relocating source on unseen layouts.

**It does not validate** trails, junctions, walls that occlude the scent, or colonies (the design's
§"What E1 does and does not establish").

**The input mapping is a commitment:** the goal cue enters at the food neurons AWA, AWC and ASE, left
and right.
