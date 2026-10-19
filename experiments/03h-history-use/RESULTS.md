# 03h: does the history random brains hold predict how well they forage? Results (exploratory)

**Exploratory.** 03h stopped before its pre-registration, by the owner's choice (2026-10-19, D340). Nothing here is a
registered test of 03h's questions.
- **Where N2 was used:** only in rule 7's engine-equivalence check, which ran random genomes on N2 to compare the
  interface variant with the pinned interface (D327). The scripted gate also used N2's motor gains from 02's
  calibration. **No history-fitness or relief comparison ran on N2.** Step 0 and 0b ran on 03's SH pilot graphs, and
  the pilot and the amplitude check on three SH-mirror-ASK pilot graphs.
- **What ran** (DESIGN.md v3.3 §7):
  - the code and its equivalence check;
  - step 0 and 0b, exploratory;
  - the pilot, under its bound registration (`PILOT.md`);
  - after the pilot, an exploratory power analysis and an exploratory amplitude check.
- **Decided after seeing data, and by whom:**
  - **after step 0** (which bears on A), the owner made B the only registered claim, with A a pre-specified
    secondary. This was asked with both reviewers' positions, before any B data (D330). It replaced the planned Holm
    family of A and B, under which B would have needed N2 first of 65 graphs if A failed, with B alone at α = 0.05;
  - **after the pilot,** the pilot's rules said "proceed to the pre-registration". A power analysis written then
    suggested that B's rank test would rarely pass even in a scenario favourable to the hypothesis (D337);
  - **the owner then commissioned an amplitude check** at 0.5 and 1.0 (D338). This was outside PILOT.md's rule:
    §5.4 allowed one escalation to 0.5, only if the decile shift had not moved at 0.25, and it had moved. The check's
    guide was fixed and reviewed before it ran;
  - **after the check** (D339), the owner chose to stop and report (D340).

**Where the numbers come from:** `scripts/e03h_summary.py` reads the committed records in [`pilot/`](pilot/) and
[`development-records/`](development-records/), and writes [`summary.json`](summary.json). Each number below is from
that file, or from the record named beside it. `tests/test_e03h_summary.py` checks that the committed summary is exactly
what the records give.

## In one paragraph

The task and the relief worked at the level of scripted controllers. In random brains, on these graphs, the relief
had a small average effect.
- **On 02's T1, memory pays, and a "the food fell" bit replaces it.**
  - A scripted controller with memory beat the best memoryless one by +0.985 (95% lower bound 0.944).
  - A memoryless controller reading the bit recovered 0.976 of that gain.
- **In random brains on three SH-mirror-ASK graphs, the bit's average effect was small.**
  - At amplitude 0.25, the decile selected under relief scored +0.0077 above the decile selected under sham. That is
    about 0.5% of the deciles' test scores, which were about 1.50-1.59.
  - Over all 256 genomes, relief − sham was +0.0006.
  - At amplitude 1.0 the all-genome difference was +0.0017, about 0.2% of the +0.962 a scripted controller gains
    from reading the bit.
- **The effect varied from graph to graph.** A stronger bit widened the spread across graphs at least as fast as it
  raised the mean.
- **So B's test looked very unlikely to pass.** B asks whether N2's head start shrinks more with the relief than the
  null graphs' does. Its rank test needs N2's U to sit roughly two null SDs above the null mean. In exploratory
  Gaussian scenarios fitted to three graphs, N2 with no relief-sham difference would have sat about 0.76 null SDs
  above that mean. Such an N2 would pass at most about a third of the time, and at the point estimates 0.5% or 17%.
  N2's own response and B's full power were not measured.
- **History and fitness** (A, secondary; exploratory; in SH samples):
  - the size of the history a random brain holds (P4's per-genome measure, given its steady contrast) had a
    near-zero mean partial association with fitness;
  - its direction, turning more after a fall than after a rise, showed a weak positive association: +0.062, positive
    in 14 of 16 SH graphs, one of five pre-listed read-outs, unadjusted.

## What ran

Each stage's commit and wall time (`summary.json` `stages`):

| Stage | Commit | Wall seconds | What it did |
|---|---|---|---|
| step 0 | `4af497f` | 123 | 03's recipe verified, then H against 03's committed T1 fitness on 16 SH graphs (D329) |
| step 0b | `676fee6` | 39 | five pre-listed history read-outs on the same genomes (D330, D331) |
| bind | `ff1fd31` | 0 | PILOT.md draft 4 bound, with the implementation (D335) |
| G1 | `69606fd` | 81 | the scripted gate's level and relief parts |
| S1 | `69606fd` | 179 | the sham's rates on level trajectories of the 3 pilot graphs |
| G2 | `69606fd` | 16 | the gate's sham part |
| P | `69606fd` | 318 | the three conditions on the 3 pilot graphs |
| amplitude check | `f0b4bb0` | 504 | exploratory: amplitudes 0.5 and 1.0 on the same graphs (D338, D339) |

The stages from G1 to P ran at `69606fd`, the commit that recorded the binding. The implementation was the bound
`ff1fd31`'s, which every stage checked.

**Compute** (`summary.json` `compute`), in GPU-hours by T0's accounting:
- step 0 and 0b: 0.044;
- the pilot: 0.165;
- the amplitude check: 0.140;
- **in total 0.349,** against the 1.0-hour cap before the pre-registration. The formal run, projected at 4.24 hours
  against a 6-hour cap, did not take place.

**Reviews:**
- the scope took one round (D321), and the design four (D322-D325);
- after step 0, a direction round (D330);
- the code took two rounds (D327, D328), and the pilot's registration three (D333-D335);
- after the pilot, the power question (D337) and the amplitude check's code, in two rounds (D338);
- this page (D341).

## The machinery held

- **Rule 7:** with the bit at 0, the interface variant gave T1 scores bit-equal to the pinned interface's, on N2 with
  random genomes, on the CPU and on CUDA inside `replay_mode()` (`development-records/equivalence-*.json`, D327).
- **Step 0's verification:** 03's fitness replay and its world-free history check on `pilotSH101` were bit-equal in
  03's default mode and in `replay_mode()` (`step0.json`, D329).
- **The pilot:**
  - every stage completed on its first attempt, inside the cap;
  - graphs and genomes were rebuilt from their seeds and checked by hash;
  - the S1 sampler had no failures.
- **The sham matched as designed:**
  - its rates were p̂01 = 0.0369 and p̂10 = 0.0827, so a stationary occupancy of 0.309 (`sham-rates.json`);
  - under relief, the injected bit's counts equalled the relief bit's;
  - the relief bit's own counts barely changed with the condition or the amplitude (`pilot.json`,
    `amplitude-check.json`).

## The scripted gate (G1, G2)

On 02's T1 with 03h's interface variant, scored on 256 check worlds (`gate.json`, `gate-sham.json`):

| Family | Chosen policy | Check score |
|---|---|---|
| memoryless | `LevelKinesis` (K) | 2.156 |
| memoryless + bit | `BitKinesis` | 3.118 |
| memory | `SlowMemoryKinesis`, T = 5 | 3.142 |
| memory + bit | the same, not reading the bit (`use_bit` = 0) | 3.142 |

- **Level:** memory − memoryless = +0.985, with a 95% lower bound of 0.944 (criterion ≥ 0.5). Passed.
- **Relief:** memory + bit − memoryless + bit = +0.023, 90% interval [0.007, 0.039] (criterion inside ±0.3). Passed.
- **The recovered share:** 0.976 [0.957, 0.996]. A controller with no memory that reads the bit gets almost all of
  memory's gain. On the check worlds, that gain is +0.962 over the memoryless policy.
- **Sham (G2):** reading the sham bit did not beat the memoryless policy on the tuning worlds, so the family fell back
  to it exactly. The difference is 0, with an interval of [0, 0]. Passed.
- **Grid edges:** only Graded's `scale` = 3.0 sat at its grid's edge.

These are statements about the registered candidate families, not about every policy (PILOT.md §2).

## The pilot (P), at amplitude 0.25

On the 3 SH-mirror-ASK pilot graphs, 256 random genomes each (`pilot.json`):
- **Reliability:** 0.986 under level, so W = 16 selection worlds.
- **The manipulation check, the decile shift:**
  - per graph, the test-bank mean of the 26 genomes selected under relief, minus that of the 26 selected under sham.
    The two deciles are selected separately, each on its own condition's selection scores (DESIGN §6), so this is not
    one fixed group's response to the bit;
  - per graph +0.0192, −0.0003 and +0.0044;
  - mean +0.0077, 95% interval [0.0044, 0.0107], conditional on the three graphs, their genome draws and their frozen
    deciles.
  - It moved by the pilot's rule, so the amplitude stayed at 0.25.
- **The deciles' test means** were 1.50, 1.56 and 1.59 under level (`summary.json` `pilot.decile_test_means`).
- **U for B,** sham − relief: −0.0192, +0.0003 and −0.0044, with a between-graph SD of 0.0102 against a shared-world
  SE of the mean of 0.0016.
- **The bit's turn response,** a one-tick diagnostic: a mean absolute change of 0.9-1.9 × 10⁻⁴ in the motor turn
  read-out. It does not measure every behavioural consequence of the ASK input.
- **The projected budget:** 2.14 GPU-hours for the primary run, 4.24 with SH, so W_t = 64 with SH.
- **The pilot's action:** "proceed to the pre-registration".

**On these graphs the bit reaches the motors only through the network.** SH-mirror-ASK caps ASK's direct read-out at
N2's, which is zero (DESIGN §3; `tests/test_e03h_samplers.py`). That is by design, and it bears on how general the
small effect is.

**A's readings, secondary** (three graphs; not tests):

| Graph | ρ_level | ρ_relief | ρ_sham | D | H_dir's ρ (level) | H quartile difference (level) |
|---|---|---|---|---|---|---|
| 3 660 001 | −0.073 | −0.073 | −0.073 | −0.000 | +0.038 | −0.005 |
| 3 660 002 | +0.046 | +0.037 | +0.044 | +0.007 | +0.003 | +0.074 |
| 3 660 003 | +0.067 | +0.061 | +0.062 | +0.001 | +0.067 | +0.043 |

A2's power by the registered formula was 1.00. That figure is for A2 at δ = 0.05, not for B (PILOT.md §5.3).

## B's power (after the pilot; exploratory)

The pilot registered no rule on B's power, so D336 flagged the question. `development-records/b_power.py` was
written after the pilot and models B's rank test from the pilot's numbers (`b-power.json`, D337).
- **The model:**
  - the null graphs' U is normal, with the pilot's mean −0.0077 and SD 0.0102. The SD rests on 2 degrees of freedom,
    with 90% bounds of 0.0059 and 0.045;
  - B passes when at most 2 of 64 nulls have U at or above N2's;
  - N2's U is its value u plus either world noise alone or the nulls' graph spread.
- **If u = 0** (N2 gains nothing from the relief against sham, while the nulls gain), the pass rate is:
  - 0.005 with world noise alone, 0.22 at the SD's lower bound, and no simulated passes at its upper bound;
  - 0.17 with graph spread, 0.34 at the lower bound, and 0.065 at the upper bound.
- **About u = 0:** it is a scenario favourable to the hypothesis, not an established bound. U compares separately
  selected deciles under sham and relief, and nothing measured fixes N2's U (Astra).
- **80% pass rate** needs u of about +0.014 to +0.019 at the point SD. N2 would then have to do better under sham than
  under relief by about twice the nulls' gain.
- **These are scenario rates for B's rank part,** under a normal model fitted to three graphs. They are not B's power:
  B is conjunctive, the tail is extrapolated, and N2 was not in the pilot (Astra).

**The review** (D337) was split, and both reviewers advised against running the formal run as designed:
- Fable: stop B as a confirmatory claim, with an optional exploratory amplitude check;
- Astra: redesign B against the ensemble mean.

The owner chose the amplitude check first.

## The amplitude check (exploratory; outside PILOT.md's rule)

`scripts/e03h_amplitude.py` reran relief and sham at amplitudes 0.5 and 1.0, on the pilot's graphs, genomes, banks and
engine (`amplitude-check.json`, D339). Its guide was fixed and reviewed before the run (D338).

| Amplitude | Decile shift per graph | Mean [95%] | Between-graph SD | Ratio, with the SD's 90% range |
|---|---|---|---|---|
| 0.25 (the pilot) | +0.019, −0.000, +0.004 | +0.0077 [0.0044, 0.0110] | 0.0102 | 0.76 [0.17, 1.32] |
| 0.5 | +0.025, −0.011, +0.006 | +0.0071 [0.0039, 0.0101] | 0.0180 | 0.39 [0.09, 0.68] |
| 1.0 | +0.047, −0.007, +0.016 | +0.0186 [0.0156, 0.0217] | 0.0269 | 0.69 [0.16, 1.19] |

- **The 0.25 row** is recomputed from the pilot's arrays with the check's bootstrap seed. The pilot's own interval is
  [0.0044, 0.0107].
- **The intervals** come from shared resamples of the worlds, with the graphs, genome draws and selected deciles held
  fixed. They are not intervals over new graphs.
- **The ratio's range** varies the SD over its Gaussian 90% chi-square bounds, with the observed mean held fixed. It is
  not a confidence interval for the ratio.

**Over all 256 genomes,** on the selection bank, relief − sham was:
- +0.0006 [+0.00004, +0.0012] at 0.25;
- +0.0006 [−0.0001, +0.0014] at 0.5;
- +0.0017 [+0.0008, +0.0025] at 1.0. Relief − level at 1.0 was +0.0014 [+0.0004, +0.0024].

**Sham − level:** no ensemble-mean sham damage was detected. Its interval contained 0 at every amplitude.

**The turn response** roughly doubled with each doubling of the amplitude, to 3-7 × 10⁻⁴ at 1.0.

**The guide's verdict:**
- both ratios were under 1, which would read "the rank route is not supported at these amplitudes";
- one flag fired: at 1.0, the all-genome difference was above 0 by its interval while the ratio was under 1;
- so the guide returned "discordant evidence: the readings go to the owner".

## History and fitness (step 0 and 0b; exploratory)

On 03's 16 SH pilot graphs, 256 random genomes each, against 03's committed T1 fitness (`step0.json`, `step0b.json`;
D329-D331, as corrected in D330):

| Read-out | Mean | Between-graph SD | Positive graphs |
|---|---|---|---|
| H, given S (partial Spearman; step 0) | −0.024 | 0.060 | 6 of 16 |
| H_dir, given S (partial) | +0.062 | 0.074 | 14 of 16 |
| H (plain) | −0.012 | 0.068 | 9 |
| S (plain) | −0.000 | 0.067 | 8 |
| \|motor-turn final difference\|, given its steady contrast | +0.010 | 0.050 | 9 |
| \|raw-forward final difference\|, given its steady contrast | +0.007 | 0.063 | 7 |

- **The measures:** H is |raw-turn final difference|, the per-genome numerator of P4. S is |raw-turn steady
  contrast|. H_dir is |motor turn after the falling history| − |motor turn after the rising history|.
- **What they are:** associations in SH samples, conditional on the 16 shared worlds. No margin for a negligible
  association was set, so the near-zero mean for H is not a claim that it has none (DESIGN §13).
- Step 0b's five read-outs were all pre-listed and are all reported. The 14 of 16 is not adjusted for the choice
  among them.

## What this shows, and what it does not

**Shown, on these graphs and this task:**
- **On T1, memory is worth about +0.98 to a scripted controller,** and a bit that says "the food fell" replaces 98%
  of it.
- **In random brains on three SH-mirror-ASK graphs,** where the bit enters through ASKL and ASKR and reaches the motors
  only through the network, its average effect on fitness was small:
  - about 0.5% of the selected deciles' scores at 0.25;
  - about 0.2% of the scripted gain over all genomes at 1.0.
- **The effect was uneven across graphs.** A stronger bit widened the spread at least as fast as it raised the mean.
- **With this manipulation,** exploratory scenarios suggested that B's rank test would rarely have passed if N2's
  relief-sham difference were zero.
- **In SH samples,** the size of the history held had a near-zero mean partial association with fitness at
  generation 0. Its direction showed a weak positive one.

**Not shown:**
- **Anything about N2's head start.** No history-fitness or relief comparison ran on N2. Whether N2 has a
  generation-0 head start on T1, and whether it shrinks with the relief, were not tested.
- **B's power.** The scenario rates are for the rank part under a model fitted to three graphs. N2's own response was
  not measured.
- **That history does not matter for fitness.** A was a secondary and never ran as a formal claim. Step 0 found a
  near-zero mean association for P4's magnitude measure in SH graphs, with no margin for "negligible".
- **That history is used as memory, or that it mediates any N2 advantage.** Every reading here is an association
  in random brains.
- **That random brains cannot use a relief,** or that individual brains respond uniformly. This relief entered
  through ASK, which on these graphs has no direct read-out. The food channel, which every graph is calibrated to use,
  was not tried.
- **That a different statistic would have worked.** Astra's test against the ensemble mean was not run. Fable
  estimated that about a fifth of null graphs would pass it (D337).
- **Anything general:** three pilot graphs, one task, one interface variant and one probe bank. The between-graph
  spreads rest on 2 degrees of freedom.

## What 03h leaves for a later design

Each item is a candidate, not a demonstrated need.
- **The relief's route:** a relief through the food channel, which random brains already read (Fable, D337).
- **B's statistic:** a test against the ensemble mean, with its own power analysis before any data (Astra, D337).
- **The power rule:** a pilot should register a power rule for the primary claim, not only for a secondary. 03h's
  pilot had one for A2 only (PILOT.md §5.3), so B's power surfaced only after the pilot (D336, D337).
- **H_dir:** the directional read-out was the one history measure with a consistent sign at generation 0 in SH
  samples (+0.062, 14 of 16). Testing it would need its own registration.

## Corrections

- **D330 corrected D329** in six places:
  - its title's "history does not predict T1 fitness";
  - an SE that left out world uncertainty;
  - a claim about heterogeneity;
  - a range read as an interval;
  - "03's genomes and graphs are reproduced exactly", for one verified graph;
  - "B is untouched".
- **D337:** before its review, `b_power.py` called U > 0 "the relief harming N2". U compares relief with sham, not
  with level, so the wording became "N2 better under sham" (Astra).
- **D339:** the amplitude check's final console line crashed after its record was written, on a character the
  Windows console cannot encode. No reading was affected, and the print was fixed with a test.
- **D341** lists the corrections this page's review made, including one to D339's table: the 0.5 row's third
  graph is +0.006, not +0.007.

## Reproduce it

Everything needs the connectome (`scripts/fetch_connectome.py`) and the pinned environment (`requirements.txt`). The
GPU stages need CUDA. Exactness is claimed only on the same GPU and pinned environment, with the same batch
compositions, inside `replay_mode()` (AGENTS.md rule 6).

**Without a GPU:**
- `python scripts/e03h_summary.py` rebuilds `summary.json` from the committed records;
- `python experiments/03h-history-use/development-records/b_power.py` reruns the power analysis. Without the pilot's
  local arrays it writes `b-power-without-arrays.json`, which leaves out the selection-bank part, and it leaves the
  committed `b-power.json` alone.

**A rerun of the GPU stages.** The guards refuse to run on a dirty or unpushed tree, so a rerun needs a branch of your
own, pushed to your remote:
1. `git switch -c rerun-03h ff1fd31`, then push the branch. At that commit `pilot/` holds no records.
2. `python scripts/e03h_step0.py` and `python scripts/e03h_step0b.py`: step 0's verification and read-outs. They
   write the ledger `runs/e03h/step0/compute.json`, which the cap counts.
3. `python scripts/e03h.py bind`, then commit `experiments/03h-history-use/pilot/bind.json` and push. The binding
   records your HEAD as its bound commit.
4. `python scripts/e03h.py gate`, then `sham-rates`, `gate-sham` and `pilot`, in that order. The stages write
   their records to `pilot/` and their ledger to `runs/e03h/pilot/compute.json`.
5. **For the amplitude check,** commit the pilot's records in `pilot/`, since its clean-tree check covers them. Bring
   in its script from `b4978d4` (`git checkout b4978d4 -- scripts/e03h_amplitude.py`), commit and push, then run
   `python scripts/e03h_amplitude.py`. It needs the pilot's local arrays and both ledgers. Its guard allows no other
   change under `scripts/` since your binding, so bring in nothing else first.
6. **For the summary:**
   - bring in `scripts/e03h_summary.py` and `development-records/b_power.py`;
   - copy `runs/e03h/pilot/compute.json` to `pilot/compute.json`, `runs/e03h/step0/compute.json` to
     `development-records/step0-compute.json`, and `runs/e03h/amplitude/compute.json` to
     `development-records/amplitude-check-compute.json`;
   - run both scripts, and compare with the committed `summary.json`.

**The CUDA preflights:** `--smoke --device cuda` on `scripts/e03h.py` or `scripts/e03h_amplitude.py`, with their own
ids and seeds.

**Local only:** genomes, graphs and per-genome arrays stay in `runs/e03h/`. Their hashes are in the records.

## Record

- **Design and registration:** [`DESIGN.md`](DESIGN.md) v3.3; [`PILOT.md`](PILOT.md) draft 4, bound at `ff1fd31`.
- **Decisions:** D321-D341 in [`DECISIONS.md`](../../DECISIONS.md).
- **Reviews** (`docs/reviews/`):
  - the scope: `20261018-memory-thread-scope`;
  - the design: `20261018-03h-design`, `-r2`, `-r3`;
  - the code: `20261018-03h-code`, `20261019-03h-code-r2`;
  - the direction after step 0: `20261019-03h-direction`;
  - the pilot: `20261019-03h-pilot`, `-r2`, `-r3`;
  - B's power: `20261019-03h-bpower`;
  - the amplitude check: `20261019-03h-amplitude`, `-r2`;
  - this page: `20261019-03h-results`.
