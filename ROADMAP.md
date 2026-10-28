# WormWars roadmap, v3

*27 September 2026. Replaces v2. Written from roadmap v2, Astra 6's review of v2, and Claude Code's status report of the same day. A local v2.2 exists on the `roadmap` branch and was not seen when this version was written, so merge anything it adds. (Merged: see "Carried over from v2.2" below. Four factual corrections were made on installation; they are listed in D062.) This is a living document, not a pre-registration. When a result changes it, the change is recorded here with the reason.*

## Status, 1-25 October 2026 (updates the section below; that section's later edits are recorded in DECISIONS.md)

**25 October 2026** (D349-D365): **the memory thread's M1 to M4 have run** (exploratory, on the CPU; results in
[`docs/memory/`](docs/memory/), each stage annotated in [`MEMORY-ROADMAP.md`](docs/memory/MEMORY-ROADMAP.md)). Every
stage's plan was reviewed by Astra and Fable and its results reviewed after; each plan was agreed before its runs,
with one disclosed exception: M4c's classification census started during its plan's first review round, and only its
arms ran after agreement (D361). None is a pre-registration.
- **M1** (D349-D352) corrects the memory roadmap's first finding: N2's unweighted mean per-genome retention is extreme
  too (0.586, against ensemble medians of 0.370 to 0.412; none of 640 graphs reaches it), and the amplitude weighting
  lowers N2's share. Read-out alignment does not carry the lead (persistence does), and in a targeted replication
  amplitude does not account for most of it (f = 1.01 and 1.03 at matched amplitude, a fraction of the lead within
  the matched strata).
- **M2** (D353-D356): a validated classifier finds a small minority of genomes holding the history in two stable
  states, "separate states" (15 and 13 of N2's eligible genomes on its two panels). At tick 30 they carry 0.47 and
  0.35 of N2's mean lead over 30 reference graphs ("inconclusive": the intervals are wide); fading genomes carry 0.44 and 0.64, through more retention as a class
  (an amplitude-weighted aggregate, not a statement about most fading genomes). At tick 300 separate states carry
  most of it.
- **M3** (D357) closed as a completed screen; the head core C3, defined from the anatomy alone, went to M4.
- **M4a** (D357-D358), "unresolved": cutting C3's internal edges for 30 ticks costs more than every one of 30 sampled
  cuts of equal size on both of N2's panels, but one panel's interval reaches the margin. Started from their two roots,
  26 of N2's 28 separate-states genomes end in one basin after C3's cut (14% under the sampled cuts).
- **M4b** (D359-D360), "unresolved": in N2, cutting the edges where a switch's states differ erases 89% of the
  switches, against 31% and 11% for controls; across ten selected graphs it is not demonstrated (two respond like N2). RIA's core edges alone
  erase most of N2's switches.
- **M4c** (D361-D362), positive: on 141 fresh N2 switch genomes, cutting RIAR's or RIAL's core edges for 30 ticks
  (each side separately) erases the history distinction in 72% and 58% of them, against 22% to 30% for three families
  of weight-matched edge sets ("erased": both histories end in one basin after the network is restored; both states
  still exist). A place of vulnerability, not shown to be storage.
- **M4d** (D363-D364), "Unresolved (the unresolved genomes decide it)": N2's C3 block raises the share of
  separate-states genomes in all ten fresh host graphs (pooled over 10,240 genomes per arm: from 0.04% to 0.62%), but copies rewired at the same degrees
  reach 0.51%, so whether its exact wiring matters is unresolved.
- **Next (the owner, 2026-10-25), in this order:** a write-up of M1 to M4 (*done the same day:*
  [`docs/memory/SYNTHESIS.md`](docs/memory/SYNTHESIS.md), D366); a planned study of what a dense block
  carries (in the owner's words, "its size, weights and degrees"; D364 named density and degrees); then an M5 test of N2's exact wiring, after working out how many hosts it
  would need. All on the CPU unless the owner gives the GPU. *Annotated 2026-10-27 (D367-D368): the dense-block study, M4e, has run ([`docs/memory/M4E-RESULTS.md`](docs/memory/M4E-RESULTS.md)). At equal magnitudes, the same total weight on more edges lowers the switch share; more weight at N2's edge count shows no effect of 0.004 or more. N2's block's effect arrives with its uneven weights, labelled degrees and exact wiring, only the first resolved. M5's power calculation is next.* *Annotated 2026-10-28 (D369-D372): M5's pilot and power calculation are done ([`docs/memory/M5-POWER-RESULTS.md`](docs/memory/M5-POWER-RESULTS.md)). The recommended rule runs 110 hosts first and up to 160, about 72 to 91 CPU hours; the owner chooses the host count before M5's plan and pre-registration.*

**20 October 2026** (D346): **a roadmap for the memory question** ([`docs/memory/MEMORY-ROADMAP.md`](docs/memory/MEMORY-ROADMAP.md)).
- **The question:** why the history difference decays more slowly in N2's random brains (03mc's Q-D).
- **How it was answered:** the owner asked for a new kind of ceremony beside the reviews: a blind, divergent round,
  then building on each other's ideas, then an honest selection, with Claude as master of ceremonies and Astra and
  Fable as the other voices. Exploratory CPU checks ran between the rounds. The roadmap was reviewed twice by both and
  agreed. Everything is archived in `docs/reviews/20261020-memory-*`.
- **What it found, exploratory:**
  - N2's lead is in the amplitude-weighted share, not in the typical genome; *corrected 2026-10-25 (D365, from M1,
    D350): the "amplitude-weighted share" half is misleading. N2's unweighted mean per-genome retention is extreme too,
    and the weighting lowers its share. "Not in the typical genome" still holds for the median genome, while the upper
    quartile of retention is extreme and the largest contributors carry much of the lead;*
  - a minority of brains in N2 and in the nulls may hold the history in separate states, and N2 has more of them
    than most null graphs;
  - a head core around the turn read-out (RIA, RIM, AIB, AIZ, RMD, SMD and others) preserves most of the lead in an
    otherwise shuffled graph, conditionally. Triangle counts as such do not.
- **The plan:** accounting, amplitude and cheap kills (M1); a validated dynamical census (M2); a core defined from
  the anatomy alone (M3); write, hold and read, separated, with a transplant screen (M4). All exploratory, on the CPU.
  Then the owner's transplant, pre-registered (M5).
- **Next:** M1, when the owner wants it. It needs no GPU. *Done: M1 to M4 ran from 20 to 25 October; see 25 October,
  above.*


**19 October 2026** (D321-D342): **03h stopped before its pre-registration; exploratory**
(`experiments/03h-history-use/`, RESULTS.md). It was the memory thread's first design: does the history random brains
hold predict how well they forage, and is N2's head start larger when memory is needed?
- **The task and the relief worked.** On 02's T1, a scripted controller gains +0.985 from memory, and a "the food
  fell" bit replaces 98% of that.
- **In random brains, the bit's average effect was small.** It entered through ASKL and ASKR, which on these graphs
  have no direct read-out. The decile selected under relief scored about 0.5% above the one selected under sham at
  amplitude 0.25, unevenly across the three pilot graphs. A stronger bit widened the spread across graphs at least as
  fast as it raised the mean.
- **So B, the only registered claim** (the owner's choice after step 0, D330), **looked very unlikely to pass.**
  Exploratory scenarios suggested its rank test would rarely pass if N2's relief-sham difference were zero. N2's own
  response was not measured. The pilot had registered no rule on B's power, so this surfaced after the pilot (D336,
  D337).
- **The owner's choices:** an exploratory amplitude check first (D338, D339), outside the pilot's amplitude rule, then
  to stop and report (D340). 0.349 of the 1.0 GPU-hour cap before the pre-registration was spent. N2 was used only in
  the engine's equivalence check.
- **What it leaves:** a relief through the food channel, or a test against the ensemble mean, each with a power rule
  for its primary claim fixed before any data. In SH samples, the direction of the history held showed a weak
  positive association with fitness (+0.062, 14 of 16 graphs; exploratory). Its size had a near-zero mean association.
- **Next:** not yet chosen.


**18 October 2026** (D302-D319): **03a stopped after pilot-dev; exploratory** (`experiments/03a-self-consistency/`,
RESULTS.md).
- **Before pilot-dev's GPU runs:** design v7.1 was agreed by both reviewers. *Corrected 2026-10-18 (D319): this said
  "Before any GPU run", and that the code was also "reviewed in three rounds" by then.* Round 1 came before; pilot-dev's first stages ran while
  rounds 2 and 3 were under review (PILOT-DEV status). The exploratory checks (D303, D304) also preceded design v7.1.
  The owner gave the word for pilot-dev's GPU.
- **Pilot-dev**, on one shuffled graph, detected no anatomical enrichment on its two targets. Neither NIP target-brain
  had headroom above the margin, and refits handed the true partners fell short of exact restoration. *Corrected
  2026-10-18 (D319): this said "found no anatomical signal" and "the NIP brains had no use for the neuron".*
- **A bounded check of the search** followed (the owner's choice, on both reviewers' advice). Its rule was fixed
  before it ran, and it gave outcome (iii): no variant restored reliably. So 03a ends, with 5.84 of its 72 GPU-hours
  spent and no pre-registration.
- **Next:** the owner left the choice to Claude ("Do as you consider best"). Claude picked a design round for the
  memory thread's predictions (below); its GPU runs will need the owner's word.

**16 October 2026** (D285-D300): **Track B started with 03mc,** the confirmatory study of 03m's leads
(`experiments/03mc-p4-confirm/`). Pre-registered and pushed before its run; 7.73 of 10 GPU-hours. **All four
primaries pass under Holm** (gap junctions, RIA and AIY, weight placement, relaxation), and P4 replicates a third
time. Whether any deletion removes the elevated P4 stays open. **Next in Track B: 03a's six-neuron proof of
concept** (72 GPU-hours, D094), which needs a design round and the owner's word for the GPU.

**Where things stand, 15 October 2026** (D282):
- **Track E has run its schedule through E4.** Everything after E4 is direction, not schedule (the tripwire,
  below). In E4's diagnostic task, evolution recruited the transfer between the two modules (D280). The main maze
  task's formal run was dropped (D258).
- **Track B is next:** a confirmatory study of 03m's leads, then 03a's six-neuron proof of concept. Neither has
  started. Both need the GPU and wait for the owner's word. *(16 October: 03mc ran and passed; see above.)*
- **Waiting for the owner:** the items carried over from v2.2 (at the end): the plasticity experiment, task
  specificity, and the owner's question about worm-like tasks under worm-like plasticity.
- **What v3 planned that has not run** (checked against DECISIONS.md, 2026-10-15; later amendments are marked):
  - **Track B:** the two studies above; bridge 1 (deferred by both reviewers in E1's design, D077) and bridge 2,
    which 03r's replication gave priority. No Track E experiment has run on null graphs, so the five null
    ensembles have not yet served as its controls. The memory thread's predictions (a larger early N2 advantage on
    tasks that need memory, shrinking over generations) are untested. Of the later biology questions (below),
    topology × optimizer × normalisation, activity-anchored fitness, a neuromodulatory layer, and temporal against
    stereo sensing have not started; experiment 03's five validated ensembles began the family of named nulls.
  - **E3:** the cumulative reuse cost of modules (E3c's "Not shown").
  - **E4:**
    - question 1, shared dependence (designed in D242-D244, not run);
    - question 2 in the main task: no completed contrast of training with and without cross-links (the pilot's X+
      arm was lost at its cap), and no acute cuts or substitutions of evolved cross-links; both were dropped with
      the formal run (D258). The matched within-module cut was judged infeasible at design v2 and replaced (D243);
    - question 3, consolidation (moved to stage 09, as v3 allows);
    - each run's gene-duplication fate, and the control with the selector removed. The other two controls ran:
      cross-links impossible as X0, and the unevolved duplicates as E-G, in the pilot and in E4-D;
    - the pruning protocol (added in D144).
  - **Related work:** survey v2 is not committed here, so whether its corrections were applied cannot be checked
    from this repository (nothing here cites it); the memory thread's literature comparison; the
    collective-behaviour survey that stages 05-08 need.
  - **Stages 05-09:** no design yet.

- **E4s, a hand-built stereo module, ahead of plan** (the owner, 2026-09-30; D139-D144). E2d's
  plateau means E3 has no stereo navigator. The owner asked for one to be built by hand and settled by
  evolution, with a **96 GPU-hour ceiling**. What happened:
  - **The first designs (v1-v3) rested on an unchecked report.** It was called "a deep research", but
    it was a single CLI session with snippet-level sources (corrected in D143).
  - **A real literature review followed** (`docs/reviews/20261001-literature-review/`, by Claude Opus
    and Astra 6, from one prompt). It found that:
    - a ring attractor is not needed to steer on a smooth scent; a small comparator suffices;
    - the worm's own chemotaxis is temporal, not stereo.
  - **The owner kept bilateral stereo sensing as an explicit game-design choice** (option (a)).
  - **The plan, reviewed in two rounds** (both reviewers "adopt with changes"; v2.1 adopted):
    - **E4s-0:** exploratory diagnostics, at most 2 GPU-hours;
    - **E4s-1:** a comparator graft under evolution, pre-registered;
    - **E4s-2:** the ring, deferred to a task that needs memory.

    See "E4s" under Track E and `docs/E4s/ROADMAP-PROPOSAL.md`.
  - **The engine changes are done:** grafting extra neurons, per-parameter mutation scales and GA
    hooks, all test-first. The GPU check passed: E2's generations 0-25 reproduce exactly.
  - **E3 no longer waits:** it starts after E4s-0, with the artefact rule in the E4s section.
  - **E4s-0 ran** (0.23 GPU-hours; D147; `experiments/E4s-stereo-module/E4s-0/`). Reviewed, corrected
    by 15 dated corrections.
    - For 42 of 47 champions, a valley along the stereo-gain direction.
    - The 4-neuron comparator L1 qualified: 5.18 targets per episode, with a carrier turn bias.
    - It is used at generation 0 by all 16 simulated populations' bests, so E4s-1 runs on random N2.
  - **E4s-1 was pre-registered** (D148-D150): bound at 023267d, public before any stage ran, and
    amended once before any stage ran (D152).
  - **E4s-1 ran on 2026-10-01 and 2026-10-02** (16.61 GPU-hours), and its results were reviewed and
    corrected (D153, D154).
    - O1 and O1b: "supports" (+5.19 against no graft output, +3.79 against random signs).
    - The selected main brains use the module at both endpoints in 16 of 16 runs, reaching 7.14.
    - Part of the benefit is not stereo use, and transfer into the host was not shown.
  - **Next in Track E: E3's design,** from E4s-0's module or E4s-1's run 10 (a whole-brain artefact),
    each needing E3's own positive control.
- **E3a, the shuttle** (2026-10-02; D156-D169; `experiments/E3-ab-organism/`).
  - **The design** took five review rounds, and the pre-registration two. Both were agreed by both
    reviewers. The owner set 30 GPU-hours for E3a, and about the same each for E3b and E3c (D159).
  - **The run used 5.97 GPU-hours.** Its results were reviewed ("fix") and corrected (D169).
  - **The engineered organism shuttles:** two L1 copies on the carrier, gated by a one-neuron latch,
    reach 12.79 visits per episode. That is 97% of a module fed the goal's scent.
  - **The registered readings:**
    - S2-a: "evolution found a working selector in 1 of 8 runs, not reliably";
    - S2-b, against a blind search over the whole range: "unclear";
    - S2-c: none in either census;
    - Stage 3, joint tuning: "better" (+2.36);
    - B-task: "worse" than Stage 3.
- **E3b-0, mazes, trails and the colony** (exploratory, 2026-10-02/03; D171-D180;
  `experiments/E3-ab-organism/E3b-0/`).
  - **It used 2.62 of its 3 GPU-hours.** The trail search stalled twice. Two amendments, each reviewed by
    both reviewers before it ran, changed the qualification rule. The trail constants are therefore
    adaptively selected.
  - **On 256 untouched mazes:**
    - linear trails help a scripted follower (+3.57 legs per 1 000 ticks) and the engineered seed E with a
      one-sided wall reflex (+0.69);
    - peers' trails speed later discoverers;
    - peer fields not laid by the colony itself hurt.
  - **Not shown:** that weys use the trail's direction.
  - **Also found:** E3a's best tuned organism (S3r3) fails the maze, and most of the seed's performance
    comes from the reflex.
  - **Next in Track E: E3b-1's design,** the E3 gate.
    - **Its budget:** two training arms at 12 runs, 500 generations and H = 2 400 project to about 71
      GPU-hours, against the owner's ceiling of about 30. Both reviewers would cut generations first.
      They differ on how far: about 125 generations at 16 worlds (Astra), or 250-300 at 8 worlds with 6
      no-trail runs (Fable).
    - **Owed before its runs:** the GPU leg of the engine's equivalence check.
  - **E3b-1 is pre-registered and bound** (2026-10-03, D181-D186;
    `experiments/E3-ab-organism/E3b-1/PREREGISTRATION.md`).
    - **The design:** the owner's schedule, 8 runs × 125 generations × 16 mazes and 8 × 300 × 8, with a
      read at generation 125, plus a no-trails arm (6 runs) and a recovery control (2).
    - **The gate:** a stratified Welch test on the 16 final champions against the frozen seed.
    - **The cap:** 24 GPU-hours.
    - **Next:** implementation, a code review, then the runs.
  - **E3b-1 ran and is published (2026-10-04, D188-D192;
    `experiments/E3-ab-organism/E3b-1/RESULTS.md`).**
    - **The gate: "better",** +0.225 of the seed's mean: +0.069 at 125 generations, +0.381 at 300.
    - **The secondary tests:** more generations helped; trail dependence increased; peers' trails still help.
    - **The probes:** no tuned champion meets the seed's comparator criteria, so the route of the gain is open.
    - **Its course:** the code review (both, D188-D189); Amendment 1 on infeasible mazes before any score was
      read, and its correction for an audit trace on one test maze (D190-D191); 18.73 of 24 GPU-hours.
  - **Next in Track E: E3b-2** (exploratory; the owner's choice, 2026-10-04, D193).
    - **What:** knock out or freeze parts of E3b-1's tuned champions (the latch, the comparators, the reflex,
      the turn biases) to see where the gain comes from.
    - **Its size:** about 5 GPU-hours, with no new evolution.
    - **Why first:** both later steps, E3's assembly comparison and E4, assume the selector is in use.
    - **After it:** the choice between E3's assembly comparison and E4.
  - **E3b-2 ran and is published (2026-10-04, D197; `experiments/E3-ab-organism/E3b-2/RESULTS.md`).**
    - **The latch's switching is used:** holding it fixed removes 85-87% of the tuned champions' visits.
    - **The gain** sits mostly in the comparators' co-tuned sensing and gating parameters.
    - **Both next steps keep their premise.**
  - **Next in Track E: E3c, the assembly comparison, then E4** (the owner's choice, 2026-10-04, D198), each
    capped at 30 GPU-hours.
- **E3c, the assembly comparison** (pre-registered, 2026-10-04/06; D198-D220; `experiments/E3-ab-organism/E3c/`).
  - **The pilot** found that organisms trained from random weights solve the mazes as scent-free
    wall-followers. A replay and probe confirmed it (D206). The pre-registration took four drafts and five
    review rounds; the formal code, five more.
  - **The run used 22.65 of 30 GPU-hours.**
    - **Q1:** modular against dense from scratch, "approximate (model-based): no relevant difference".
    - **Q2:** the engineered seed plus tuning against scratch, "approximate (model-based): unclear" (+0.66
      visits on average).
    - **The coverage hypothesis:** "supported". Every from-scratch champion is a scent-free coverer; no tuned
      engineered one is.
  - **For E4:** its question, whether information crosses between two navigation modules, needs a task where
    coverage cannot win, and its own validation.
  - **Paused before E4** (the owner, 2026-10-06).
- **E3d, a maze that wall-following cannot solve** (exploratory task validation, 2026-10-10; D221-D231;
  `experiments/E3-ab-organism/E3d/`).
  - **The owner's direction:** better mazes before E4, with no goal touching the perimeter.
  - **The design:** 6 × 6 mazes with island goals, the owner's choice of size. It took four review rounds and
    was bound at 65b77fb. Amendment 1, to the scripted wall-follower, was made before any formal play.
  - **The run used 0.81 of 3 GPU-hours.** "E3d: failed at calibration":
    - G1b failed at every k_r: a random walk at 2.34-2.53, against 2.0;
    - every other criterion passed;
    - wall-following is defeated;
    - E3c's scent-free champions score almost nothing with their noses removed.
  - **Next:** the owner chooses the next construction. The roadmap stays paused before E4.
- **E3e, E3d's island mazes at 7 × 7** (exploratory, 2026-10-11; D232-D236; `experiments/E3-ab-organism/E3e/`).
  - **The design:** the owner chose option 1, a larger maze. E3d's design was bound by hash, with c = 7 and fresh
    blocks; two review rounds.
  - **The run used 0.71 of 3 GPU-hours.** "E3e: failed at calibration":
    - G1a and G2a failed at every k_r;
    - G1b, E3d's failure, passed;
    - the scent follower collapsed from 16 visits to 5, while the oracle lost 17%.
  - **Next:** the owner decides. The roadmap stays paused before E4.
- **E3f, 6 × 6 at a horizon of 1 800 ticks** (exploratory, 2026-10-11; D237-D241;
  `experiments/E3-ab-organism/E3f/`).
  - **The choice:** after consulting both reviewers, the owner left the choice to Claude, who picked one bound
    validation. Its horizon was chosen from an exact truncation of E3d's records.
  - **The run used 1.06 of 3 GPU-hours.** "E3f: passed" on calibration and on fresh confirmation mazes.
  - **For E4:** this family (6 × 6, k_r = 0, H = 1 800) is the task, with E4's own blind references and trail
    controls.
- **E4 / 04c, the main task** (exploratory, 2026-10-11 to 10-13; D242-D263; `experiments/E4-two-minds/`).
  - **The design:** v3, agreed by both reviewers after two rounds; never pre-registered, since the pilot came first.
    It has a real output gate, ungated comparators, a frozen selector and 32 cross-link slots, and X0 and X+ are
    paired by seed.
  - **The pilot and its follow-ups used 4.20 of 30 GPU-hours.** They showed:
    - E-G's comparator modules are mutationally fragile, nearly all of it through the module biases;
    - after 100 generations, no X0 strain beat E-G on validation;
    - random cross-links cost heavily at every tested size.
  - **The main formal run was dropped** (the owner, D258), on both reviewers' recommendation: it would most likely
    have spent about 20 GPU-hours on an inconclusive null.
  - **E4 is re-scoped to E4-D,** a task where transfer is necessary by construction. Its feasibility check passed on
    the CPU (D262): a hand-configured cross-link control reaches 0.83 real-first against X0's exact 0.5.
  - **The evolutionary E4-D** (on E4's remaining GPU-hours): design v2.1 (D265-D266); its exploratory pilot found
    the transfer recruited in all 20 runs (D269-D270; 1.85 GPU-hours, E4 at 6.05 of 30, and 6.09 after D275's dry run); its pre-registration bound
    after three rounds of review by both (`experiments/E4-two-minds/E4-D-evo/PREREGISTRATION.md`, D271-D274; L 32
    runs, F 4, S 32 if L finds nothing). Its formal code was reviewed by both over three rounds (D275-D278), and the
    formal run (2026-10-14/15, 3.21 GPU-hours, E4 at 9.30 of 30) read L as **"practically relevant transfer found"**
    (mean gain 0.412, lower bound 0.401 against δ = 0.15; D280); S was not triggered. Its results were reviewed by
    both ("fix then publish", D281) and published on main.

- **Published on main:**
  - 02's D050 correction, as a Corrections entry (27 September, D063);
  - 03 and 03r together, reported by the pre-registered rule, and 02b (28 September, D085);
  - the documentation for outsiders, and T1 (28 September, D093);
  - E1, with its pre-registration, results and corrections (28 September, D102);
  - 04a, with its pre-registration, results and corrections (29 September, D112);
  - 03m, exploratory, with a replaced flaky test (29 September, D116);
  - E2, with its design, pre-registration, results and corrections (29 September, D126);
  - E2d, exploratory (30 September, D138);
  - E4s-0 and E4s-1 together (2 October, D155);
  - E3a, with its pre-registration, results and corrections (2 October, D170);
  - E3b-0, exploratory, with its amendments, results and corrections (3 October, D180);
  - E3b-1, pre-registered, and E3b-2, exploratory (4 October, D192, D197);
  - E3c, pre-registered (6 October, D220);
  - E3d, exploratory (10 October, D231); E3e and E3f, exploratory (11 October, D236, D241);
  - E4's main task, exploratory, and E4-D's feasibility check (13 October, D264);
  - the evolutionary E4-D, pre-registered (15 October, D281).
- **T0 (correctness) is closed** (D083). On CUDA, results repeated exactly for the same batch
  composition in the tested configurations; exact reproduction is guaranteed only inside
  `replay_mode()`. A chunk holding a single strain can differ from the same strain in a larger
  chunk (D082).
- **T1 (throughput) is closed by a dated amendment** (plan v2:
  [`docs/foundations/T1.md`](docs/foundations/T1.md), D086, D092):
  - **the profile** (`docs/foundations/T1_profile.json`). On 02's task T1, at evolution's batch, the
    brain's matrix products take about 70% of GPU kernel time, and the world about 55% of a
    tick's wall time. On a Task N-like shape (one wey per world) the world's share is about 70%,
    so batching more worlds together pays much more there;
  - **single-strain padding** is implemented. Its declared equivalence test failed at 16 rows per
    strain and at 1 row. It is kept as a mitigation of the batch-of-one path, with little measured
    overhead, and it changes no published evaluation;
  - **T1's engineering is closed by a dated amendment,** not by passing its gate (D092). This
    authorises a bounded E1 pilot;
  - **T1's budget gate moves to E1's pilot** (D086): E1 measures Task N's own throughput, and
    04a's and E2's budgets are fitted to it.
- **E1's positive control passed** (D100, D101). It is the first registration public before its
  run.
  - A scripted stereo navigator reached 8.68 targets per 300-tick episode on 1 024 unseen worlds,
    98.7% of an oracle, and 0.03 with a mirrored decoy. Blind search reached at most 0.65.
  - For 04a:
    - 74% of random N2 brains score zero on every pilot world, which meets the design's condition
      for shaping;
    - throughput in 04a's shape is 110, 336 and 438 strain-worlds/s at 1, 4 and 8 runs batched;
    - a gain curve for stereo steering is measured (RESULTS.md).
- **04a: "passed"** (D110, D111; `experiments/04a-navigation-primitive/`). Registered in five review
  rounds, bound at `e3d68be`, public before the run; 2.91 GPU-hours.
  - 8 of 12 shaped runs and 4 of 4 unshaped runs passed five rules on 1 024 hold-out worlds; the
    four failures missed only reliability.
  - The champions use the cue (a mirrored decoy captures them; a constant scent leaves them near
    zero) but are weak navigators: 2.0-2.8 targets per episode, 23-32% of an oracle, indirect paths,
    closer in behaviour to E1's temporal controller than to a stereo steerer. How they use the cue is
    not shown.
  - Shaping was not needed here (descriptive, 4 runs). The module for E3 is run 2's champion.
  - The results review asked for text fixes only, made as dated corrections.
  - **Next in Track E:** E2, the optimizer screen, from this measured baseline; E3 must not assume a
    left-right cue follower.
- **E2, the optimizer screen** (pre-registered and pushed before its run; D117-D125): ran on
  2026-09-29, 4.74 GPU-hours. **"E2: keep 02's GA"**:
  - the ES led the GA by 0.12 targets per episode on the hold-out, and 0.5 was needed;
  - 5 of its 8 champions beat the GA's median, and 6 were needed.

  **The floor fired:** random sampling came within 0.36 of the GA, so the rule below ("E2 finds
  random sampling matching the GA") applies before E3. It depends on one failed GA run. The ES kept
  improving beyond its charged allowance. The results review asked for text fixes only, made as dated
  corrections.
  - **Next in Track E:** the diagnosis of saturation, noise and budget on Task N, with its own design
    and review. E3 waits for it.
- **E2d, the diagnosis of Task N** (exploratory; `experiments/E2d-taskn-diagnosis/`, D127-D135):
  - **Part A**, from E2's records alone, found training fitness noisy. With 8 worlds, two genomes
    0.05-0.15 targets apart are ranked strictly correctly 54% of the time, with 16% ties. Nearly
    every champion sits at the level of E1's best controller that cannot use the left-right difference.
  - **Parts B, C0 and C** were agreed after four plan versions and three code reviews: stereo probes
    of the champions, a probe of how reliably 8 worlds rank siblings, and four one-change arms paired
    with E2's own runs. They ran on 2026-09-29, 3.90 of a 7 GPU-hour cap (D136, corrected D137):
    - **"a non-stereo plateau":** no champion of E2's and 04a's 47 meets the "uses the left-right
      difference" criterion, although the probes detect a scripted low-gain stereo steerer at the
      same score;
    - **no tested change leaves it:**
      - 32 worlds per genome: inconclusive;
      - halved mutation: "supports, carried by run 2", every paired run improved;
      - both together: "supports, carried by run 2";
      - the ES at σ 0.25: inconclusive;
    - the ES is budget-limited, and selection noise is "not material" only narrowly.
  - **Next in Track E: E3's design.** It starts from E2d's question: is stereo steering expressible
    and reachable (the sensing geometry, the interface, shaping, a seeded start), or does E3 build on
    the non-stereo module with its measured limitations? A decision for the owner and both reviewers.
- **03m, what drives P4** (exploratory; D113, D114): ran on 2026-09-29, 3.32 GPU-hours. Reviewed; its
  first summary overclaimed and is corrected. What stands: N2's history fades more slowly than the
  shuffles'; its large food response depends on the placement of its weights and on RIA and AIY
  (whose deletion cuts the history signal in proportion); most weight permutations lower N2's P4 below
  the shuffles' 95th percentile, and its lead narrows with gap junctions off; no tested single or
  bilateral-pair deletion removed it. A confirmatory study is possible, not planned. *(2026-10-15: it is next in
  Track B, as ordered after D094; D282. 2026-10-16: it ran as 03mc, and all four of its primaries pass; D300.)*
- **Documentation for outsiders:** every experiment folder now has a README with its question,
  result, caveats and exact commands to rerun it, and [`AGENTS.md`](AGENTS.md) describes the
  repository and its rules. Others are welcome to take any open question here, and to get there
  first.
- **03a becomes a six-neuron proof of concept capped at 72 GPU-hours** (the owner, D094). It comes
  after E1, sized to E1's measured one-wey throughput. The full 24-neuron draft needed about 2.5
  times the measured throughput. The largest candidate found in T1, batching several runs
  together, gives about 1.35 times on 02's task and 3.2-4.2 times on a one-wey task; its
  exactness is not yet tested.

## Where the project stands

*The owner's text of 27 September, kept with dated annotations. The current state is in the Status section above.*

- **Experiment 01 / 01b.** Real C. elegans wiring (N2) against shuffled (SH) and random (RD) graphs on a foraging game. 01b is the rerun after a chemical-synapse direction bug was fixed. The README states exactly what it establishes; in particular, it does not establish faster improvement.
- **Experiment 02 (published).** The primary prediction failed: champions did not meaningfully use the left-right food difference. Its pre-registration's mirror-symmetry reasoning was wrong: the turn read-out is dorsal minus ventral, so symmetric wiring gives no left-right comparison for free. Correction D050 is prepared as a Corrections entry in 02's RESULTS.md on main *(published 27 September)*.
- **02b (re-analysis of 02's champions, reviewed, not yet on main *(published 28 September, D085)*):**
  - Champions circle and slow down on food and near obstacles, and N2 and shuffles do this equally well.
  - One statement, that champions "steer by which side the food is on", is now reconciled with 02's registered result: it is a replay association with the turn command, not fitness use, and it does not revise 02 (D063).
  - Selection built history dependence into the champions: a slow memory of the recent food level, not a response to its change.
  - N2 has a core of critical neurons (AIZ, RIA) that survives changes to the sensor mapping.
  - By generation 39, evolved weights keep only a weak resemblance to the anatomy (rank correlation 0.35).
  - Of 96 high-criticality targets (N2's 12 most critical neurons in each of 8 champions, counted with repeats), 94 connect directly to sensor or motor neurons.
- **Experiment 03 (random, unevolved brains; N2 against five null ensembles of 128 graphs each):** SH, SH-route, SH-class, SH-mirror and SH-recip.
  - **P4, history dependence:** borderline. N2 is above every graph in four ensembles and above 127 of 128 in the routing-matched one (adjusted p = 0.047).
  - **P1, steering toward food:** N2 is unremarkable.
  - **P3, use of food information:** no criterion met, with low power.
  - **Exploratory:** N2's random brains respond 5 to 7 times more strongly to food input than the typical shuffled graph, and more strongly than every one of the 640. That does not explain P4. Two readings from 02 do not hold for unselected random brains.
- **03r:** a pre-registered replication on 768 new graphs and new random brains for N2 too, **finished on 2026-09-28: "Replicated under the registered single-signal test and under 03's original three-signal rule"** (D080). P1 recurs as "not distinctive". P3 comes out *reversed*: an unpredicted secondary, weaker than its rank p suggests because N2's P3 measurement is noisy. Per "What would change this roadmap", the mechanism follow-up comes next in Track B, and bridge 2 gains priority. *(29 September: that follow-up, 03m, ran as an exploratory study; D113-D116.)*
  - **Timing, stated plainly:** neither 03's nor 03r's pre-registration was pushed before its run started. 03r's is pushed while the run is in progress, so GitHub's receipt time shows only when the text became public. That no 03r result had been seen by then rests on local records: at the push, N2 had not been measured, and no signal value from the formal run had been inspected since binding. The one exception is a disclosed preflight value from before binding (D063). The standing rule below applies from now on.
- **03a (your self-consistency hypothesis):** draft v3.2, nothing run. Estimated at about 31 million genome evaluations, roughly 785 GPU-hours. Measured throughput so far is about 2 times experiment 02's; the one-week cap needs about 5 times. *(28 September: it becomes a six-neuron proof of concept capped at 72 GPU-hours, D094. The owner left the order open; Claude put a confirmatory 03m study first, then 03a.)*
- **Related work:** a first survey exists, with corrections pending (see Related work below).

## The thread worth following: memory (a hypothesis)

Several results point the same way:

- N2's random brains hold on to past food levels unusually strongly relative to all five null ensembles (03, borderline; replicated in 03r, D080).
- Selection builds that kind of slow memory into the champions of every group, N2 and shuffles alike (02b, group means).
- N2's critical core, AIZ and RIA, belongs to interneuron classes worth comparing with the navigation circuitry described in the experimental and modelling literature.

**Hypothesis.** N2 starts with more capacity to hold recent history. Evolution then builds such memory into every graph, which would explain why N2's early advantages fade.

**Status.** 03r tested the first link, and it replicated (D080). So, the testable predictions include these: N2's early advantage should be larger on tasks that require memory than on tasks that do not; it should shrink over generations; and the history effect should localise to identifiable circuitry.

*20 October 2026 (D346): why N2's history lasts longer in unevolved brains now has its own exploratory roadmap,
[`docs/memory/MEMORY-ROADMAP.md`](docs/memory/MEMORY-ROADMAP.md). Its first checks point at a head circuit around the
turn read-out, which bears on the third prediction.* *25 October 2026 (D365): M1 to M4 have run (status, above). In
N2, RIA's head-core edges are a place where the history held in two stable states is vulnerable; whether N2's exact
head-core wiring carries it into other graphs is unresolved.*

## Two tracks, one priority

| Track | Question | Success looks like |
|---|---|---|
| **E: engineering** (drives the schedule) | Does assembling validated neural skills reduce the total cost of evolving useful collective behaviour, and which structural or functional features survive further evolution? | Organisms that work on unseen situations, with controls showing what each component and each peer contributes |
| **B: biology** (runs independently) | Does the worm's wiring matter, and does behaviour identify anatomy? | Pre-registered comparisons against well-specified null graphs, reported whatever they show |

Failure in one track says nothing about the other. Track E may include optional **bridges**, meaning arms run on null graphs as well as N2. Each bridge is independent and uses several graphs per null ensemble. No single bridge can answer whether the worm wiring matters in general.

## Immediate sequence (deliberately small)

1. **Publishing housekeeping.**
   - Push the `roadmap` branch so 03r's pre-registration is public before 03r finishes.
   - Publish correction D050.
   - Reconcile and publish 02b.
   - Merge 03 and 03r into main together once 03r is done.
2. **T0 and T1:** correctness and throughput on the code path actually used.
3. **E1:** scripted navigation first, then the evolved navigation primitive (04a).
4. **E2:** a short optimizer screen on that task.
   - **E4s** (added 2026-10-01, ahead of plan): a hand-built stereo module, because E2d found a
     non-stereo plateau.
     - E4s-0, the diagnostics, comes before E3.
     - E4s-1, the comparator graft under evolution, runs in parallel with E3.
5. **E3:** the minimal A/B organism (04b). *(Done: E3a to E3f, 2-11 October.)*
6. **E4:** does useful information cross between the two modules (04c)? *(Done, 11-15 October: the main task
   exploratory, its formal run dropped; transfer found in the diagnostic task, E4-D, D280.)*

Track B continues in parallel: 03r, then the mechanism follow-up or closure, then the 03a redesign. *(29 September: 03r replicated, and 03m ran as the exploratory follow-up. Next in Track B: a confirmatory 03m study, then 03a's six-neuron proof of concept.)*

**Tripwire.** No new infrastructure beyond T0, T1 and minimal module save/load until the minimal A/B organism runs. Everything after E4 is direction, not schedule. *(Relaxed 2026-10-01, D144, for E4s's graft functions and GA hooks only.)*

## Shared foundations

### T0: correctness on the path you use

- **Compute accounting:** count every rollout, tick, neural update and GPU-second actually used, including checkpoints, validation, final evaluation and tuning.
- **Tests:** a genome and its score stay paired through every operation; every parameter is inherited completely; save, load and replay reproduce behaviour.
- **Replay:** exact only in a deterministic mode. Otherwise it must agree within a tolerance declared in advance.
- **Island-path bugs:** three are suspected from reading the code. Confirm each with a failing test, then fix it. These fixes block only experiments that use islands; single-island work proceeds.
- **Gate:** the tests pass, and the energy ledger and numerical checks pass.

### T1: throughput, profile first

- The repository already batches evaluations in chunks. Profile to find the actual bottleneck, then tune chunk size, memory use and batching.
- Any implementation change gets an equivalence check against the previous engine within a declared tolerance, recorded in DECISIONS.md.
- **Gate:** the next scheduled experiment fits its budget at the measured speed, which is currently about 2 times experiment 02's.
  - *Amended 28 September (D086, both reviewers): staged.* T1's engineering closes on its profile and the single-strain padding test. A bounded E1 pilot then measures Task N's throughput, and a committed budget calculation for 04a and E2 is made against an explicit cap. If it does not fit: shrink the experiment first, then batch several runs together (T1.3), then reopen T1.
- A port to another framework, such as a JAX toolkit, is considered only if profiling points at the framework itself and the next experiments cannot fit otherwise.

### Module save/load now, assembly later

04a needs to save and replay a module. The full assembly layer is built when 04b starts:

- the interface contract (identity, inputs, internal state, outputs, parameters, evidence);
- separate recurrent blocks;
- an explicit rule for what inactive modules do.

## Track E

### E1 / 04a: navigation primitive

- **Positive control first.** Experiment 02's champions circled rather than navigated. A scripted navigator must reach moved targets with the declared body and sensors before any evolution. If it cannot, redesign the body or sensors first, for example by adding head oscillation for sensing over time.
- **Gate:** reaches moved targets on unseen layouts and beats simple movement baselines. Food collection alone is not enough.
- **Bridge 1 (optional):** also build the module on two of experiment 03's validated null ensembles, such as SH and SH-route, with several graphs each and runs within graphs.

### E2: short optimizer screen

- Run on E1's task, with equal total simulator work including tuning, comparable initialisation, 3 runs per method, and GPU time reported. The methods:
  - independent random sampling, meaning fresh random genomes with no adaptation;
  - the current genetic algorithm, with a single island;
  - one adaptive evolution strategy;
  - optionally, Augmented Random Search, labelled as an adaptive method.
- **Its only job is to choose the optimizer for E3.** The full topology × optimizer study belongs to Track B, later.
  - *Amended 2026-09-29 (D117, both reviewers of E2's design):* 8 runs per method, not 3, because 3
    cannot separate close methods and E2 is cheap; no Augmented Random Search, so the spare budget goes
    to replication. See `docs/E2/DESIGN.md`.
- Read ENOMAD before this screen. An ENOMAD-inspired hybrid is a later option.
- *Status 2026-09-29 (D124-D126):* run as pre-registered and published on main
  (`experiments/E2-optimizer-screen/`). Outcome: keep 02's GA as E3's provisional default. The floor
  fired, so Task N is diagnosed before E3 (below, "What would change this roadmap"). The diagnosis,
  E2d, ran (D127-D137): a non-stereo plateau that no tested change leaves.

### E4s: a hand-built stereo module (added 2026-10-01, ahead of plan; D139-D144)

- **Why:** E2d found a non-stereo plateau. None of the 47 distinct champions meets the "uses the
  left-right difference" criterion: 43 show no material benefit, and 4 are unclear.
- **The owner's decisions:**
  - build stereo steering by hand and let evolution settle it into N2;
  - **96 GPU-hours** for all of E4s, as a ceiling;
  - **the bilateral left/right scent stays as an explicit game-design choice** (option (a)). The
    real worm steers by temporal sensing. E4s's claims say that the stereo computation lives in a
    graft with its own noses and path to the motors, outside the N2 mask.
- **The plan** (`docs/E4s/ROADMAP-PROPOSAL.md`, v2.1, adopted after two review rounds):
  - **E4s-0, diagnostics** (exploratory; at most 2 GPU-hours; plan in `docs/E4s/E4s-0-PLAN.md`,
    reviewed before it runs):
    - a residual stereo-gain sweep on the 47 champions;
    - where their response to the difference is attenuated;
    - a fixed ladder of small comparators (4-10 neurons, within the genome's bounds), qualified on
      the carrier and measured on random N2 backgrounds;
    - mutational robustness.
  - **E4s-1, the comparator graft under evolution** (confirmatory; pre-registered):
    - the arms are main (M), no added output (N) and a random graft of the same shape (R),
      confirmatory; and frozen, uniform mutation and a case study on 04a run 2, descriptive;
    - each run is classified exclusively: acquired, never used, retained, used with the module
      changed, host stereo, bypassed or lost.
  - **E4s-2, memory:** a ring only if a task shows demand for it (outages, relocation, displacement),
    starting from Noorman et al.'s released code.
- **What E3 takes:** E4s-0's frozen comparator on the carrier if one qualifies, labelled as a
  hand-built circuit on a silent worm; otherwise 04a run 2. An evolved genome from E4s-1 replaces it
  only with a "retained" majority, chosen among individually retained genomes, and only if it passes
  E3's own positive control.
  - *Amended 2026-10-01 (D148, D150):* the majority is "uses at both endpoints" in at least 12 of 16
    M runs, and the chosen genome also needs O2b of at least 0.9.
- **Status, 2026-10-01:**
  - **E4s-0 ran:** L1, a 4-neuron comparator, qualified (D147).
  - **E4s-1 ran:** both confirmatory readings "supports"; the two E4s-1 conditions of E3's rule are
    met (D153, D154; `experiments/E4s-stereo-module/E4s-1/RESULTS.md`).

### E3 / 04b: minimal A/B organism

- *Added 2026-10-01 (D144):*
  - a baseline of one shared navigator plus a persistent goal bit;
  - the latch may be one self-exciting extra neuron, validated in our integrator;
  - the inactive module's semantics are declared in advance;
  - the navigation artefact follows E4s's rule.
- *Status (written 2026-10-15):* built in the order below (E3a: frozen modules with a fixed selector, then an evolved
  selector, then joint tuning); the trails and peer-signal controls (E3b-0); the gate passed (E3b-1, "better",
  D192); the assembly comparison ran as E3c (D198-D220). The cumulative reuse cost was not measured, and bridge 2
  has not run.

- **The organism:** two copies of the validated navigation module. A-related observations go to one copy and B-related observations to the other.
- **The selector:** a set-reset latch. A confirmed visit to A switches to "go to B", and a confirmed visit to B switches to "go to A". It is engineered starting structure, labelled hybrid.
- **Build it in order:**
  1. frozen modules with a fixed selector;
  2. then an evolved selector;
  3. then joint fine-tuning, keeping a fraction of evaluations on the component skills.
- **The trails:**

  | Current goal | Trail followed | Trail deposited after a confirmed visit |
  |---|---|---|
  | Find A | the A trail | the B trail |
  | Find B | the B trail | the A trail |

  Deposition weakens with time since the last confirmed visit; that timer is engineered state and labelled as such. Keep evaporation and exploration. Declare what walls block.
- **Gate:** repeated alternating journeys, counted with an event ledger, on unseen branching mazes, and better than the seed design.
- **Peer-signal controls:** shared trails, own trails only, and scrambled or replayed peer trails, plus a colony evolved without trails from the start.
- **After the minimal organism works, the assembly comparison:**
  1. one task-conditioned controller of matched size;
  2. pretrained modules with a fixed selector;
  3. the same modules with an evolved selector;
  4. a modular organism of the same size trained from scratch.

  Report first-use cost including pretraining, and cumulative reuse cost as later organisms reuse the modules. One loss on first use does not settle the value of modularity.
- **Bridge 2 (optional, independent of bridge 1):** the shuttle is a memory task by design. If 03r replicates, running it on N2 and matched null ensembles tests whether N2's memory head start matters for behaviour.

### E4 / 04c: do the two minds share?

*Status, 2026-10-13 (D258-D263):* the main task's formal run was dropped after its pilot; question 2 is pursued in a
diagnostic task where transfer is necessary (E4-D), whose feasibility check passed. *2026-10-15 (D280):* in the
evolutionary E4-D, selection recruited the transfer from zero ("practically relevant transfer found": the 32
pre-registered runs' champions averaged 0.912 real-first; `experiments/E4-two-minds/E4-D-evo/RESULTS.md`). See the Status section above and
`experiments/E4-two-minds/`.

Three separate questions, from easiest to hardest:

1. **Shared dependence:** does the same circuitry support both behaviours?
   - Delete each neuron in each mode. Module A's motor output is switched off during B mode, so an A-neuron whose deletion hurts B mode must act through the cross-links.
   - This detects influence between modules, but not whether that influence is useful.
2. **Useful transfer (the primary question of 04c):** does information crossing between modules improve behaviour?
   - Evolve with and without cross-links, matched in everything else.
   - In evolved organisms, cut or scramble the cross-links, and compare against cutting the same number of links inside a module.
   - Add a diagnostic task in which one module senses something the other needs; for example, only module A senses a hazard that module B must avoid.
3. **Consolidation:** can the organism keep both abilities with less circuitry or computation?
   - This needs a mechanism that lets evolution silence or bypass circuitry, such as a cost on active computation that actually differs between candidates, with the savings measured.
   - A cost on cross-links alone would simply delete the cross-links.
   - Without such a mechanism, this question moves to stage 09.

**Also report:**

- the prior results to compare against: goals varying across modular subtasks (Kashtan and Alon, 2005), connection costs (Clune, Mouret and Lipson, 2013), and duplicated modules specialising (Calabretta and colleagues, 2000);
- each run's gene-duplication fate, as description only;
- controls: cross-links impossible; the unevolved duplicates at generation 0; the selector removed.

- *Added 2026-10-01 (D144):* pruning follows a protocol (Fakhar & Hilgetag 2022):
  - importance recomputed after each removal;
  - several removal orders;
  - pairs tested;
  - acute and retrained results reported separately;
  - the preserved function includes the stereo or latch property;
  - the claim limited to "the smallest circuit found under this procedure".

### Direction after E4 (not scheduled)

| Stage | Build | Gate |
|---|---|---|
| 05: hunter | Prey progression: stationary, moving, obstacle-aware, then a frozen suite of competent prey; food other than prey limited | Captures moving prey from the frozen suite on unseen maps. Coevolution only after that, with historical opponents and a frozen evaluation suite |
| 06: hive logistics | Home, carrying and unloading, resource ledger | Sustained deliveries, balanced accounting, recovery after a blocked route or a moved food source |
| 07: defender | Foraging and homing plus hunter, with an alarm-responsive selector | Better hive outcomes than foragers alone, always-hunters, and fixed switching, across attacks and quiet periods |
| 08: adaptive roles | Identical capabilities, no assigned roles | Measured specialisation and benefit, and redistribution after workers are removed |
| 09: structural evolution | Mutable routing, module removal and duplication, rewiring within modules, and consolidation if it was deferred from 04c | Gains over parameter-only evolution at matched budgets |

The first social experiments use colonies of clones: one genome for every wey, each wey with its own state. Alarm starts as a simple local signal with a fixed lifetime and evolves only once responses to it can be measured.

### Scoring rules for Track E

- Log every raw outcome component. Fix coefficients and ranking rules before any comparison.
- Never reward how trails look, the number of alarms, or use of a particular brain.
- Use fixed horizons and comparable starting resources, not ratios with near-zero denominators.
- Shaping is training assistance: bounded, recorded, and removed from the final benchmark.
- The scorer may know the map; the controller gets only its declared observations.
- Keep separate training, validation and test suites, with the test suite used once.

## Track B

### 03 and 03r

- Merge both into main together when 03r finishes, reported by the pre-registered rule whatever the outcome.
- **If P4 replicates**, the mechanism follow-up asks:
  - where the history effect lives, using neuron and connection deletions;
  - whether it runs through gap junctions or chemical synapses;
  - whether it holds for inputs other than food;
  - what gives N2's random brains their 5 to 7 times stronger response to food input.

  Its label is assigned at pre-registration.
  - *Added 2026-09-29:* an exploratory first look, **03m**, has run (D113, D114,
    `experiments/03m-p4-mechanism/`). Its leads, and what a confirmatory study would register, are in
    its RESULTS.md.
  - *Added 2026-10-16:* the confirmatory study, **03mc**, has run (D294-D300,
    `experiments/03mc-p4-confirm/`): on fresh draws, gap junctions, RIA and AIY, weight placement and slower
    relaxation all pass as pre-registered, and P4 replicates a third time. Inputs other than food, and whether any
    deletion removes the elevated P4, remain open.
- **If it does not replicate**, it is reported as a borderline result that did not replicate. The memory thread leaves the plan.
- **Either way**, the five validated null ensembles become the standard controls for later experiments.

### 03a: redesign after 03r, before any confirmatory run

- **Keep:** the question; the feasibility pilot on shuffled graphs only, never N2; the three-outcome classification (anatomical recovery, functional substitution, search failure).
- **Change:**
  - **Task.** If P4 replicates, use a task that requires memory. In any case, the feasibility pilot must show that solutions to the task use interneurons.
    *Annotated 2026-10-17 (the owner, D305): for the six-neuron proof of concept, "requires memory" is read as a task that rewards memory (Task N with one nose: scripted controllers gain 1.64 targets from one tick of memory, D303). Whether evolved brains use history is measured on every brain and reported, not required; the pilot requires interneuron use (design v6, `experiments/03a-self-consistency/DESIGN.md`).*
  - **The 02b risk.** The connections that make neurons critical (to sensor and motor neurons) are ones v3.2 keeps fixed. Either search the targets' interface connections, or pick targets whose criticality does not come only from interface adjacency.
  - **Nulls.** Use experiment 03's validated ensembles, with several graphs each, instead of unconstrained SH.
  - **Budget.** Fit the design to the measured throughput. ~~Shrink the panel (24, then 16, then 12) or the searches before extending the cap, and say which was cut.~~ *Superseded 28 September by the owner's proof-of-concept decision below.*
  - **Wording.** Animal-to-animal variability is not a ceiling on recovery from one fixed graph.
- **The full map** (label assigned at pre-registration) runs only if 03a separates the three outcomes. *Updated
  2026-10-18: 03a stopped before separating them (D317), so the full map does not follow from it.*

**The owner's decision (28 September 2026, D094): a six-neuron proof of concept, capped at 72 GPU-hours.**
- **The panel: 6 neurons,** by foreseeable relevance to the task: **3 high, 2 medium, 1 low.**
  - "Relevance" is defined by a rule fixed in the pre-registration, before any N2 search. One
    candidate is the draft's own rule: deletion criticality measured on target-selection worlds,
    which are never used for final evaluation.
  - Each tier's members are chosen by that rule, not by hand.
- **Expanding the panel:** only if the proof of concept shows an imprinting effect (anatomical
  recovery separated from functional substitution and search failure), and only for a stated
  reason. The expansion gets its own pre-registration.
- **The cap: 72 GPU-hours** for the proof of concept, pilot included, counted with T0's
  accounting. It is registered in code and never extended. If the design does not fit, the
  searches or the null arms are cut, not the six neurons, and the cut is stated.
- **The size of the gap.** At 02's throughput (about 11 genome evaluations per second), the
  draft's design cut to six neurons comes to about 196 GPU-hours of searches: 144
  target-arm-brain combinations, 15 searches each, of 100 generations × 4 replicas × 9 states.
  Whole-brain evolution adds about 10 more. Fitting 72 hours needs about 2.9 times the speed, or a
  leaner design. These are estimates from the draft's arithmetic, not measurements.
- **Where the speed can come from** (from T1's profile, D090-D092; each is measured before it is
  relied on):
  1. **Batch the searches.** The searches are independent, and each generation is a tiny batch
     (36 genomes × 8 worlds). Stepping many searches in lockstep is T1.3's batching of runs.
     Measured gain: about ×1.36 on 02's 20-wey task, where the brain is GPU-bound; ×3.2 and ×4.2 on a
     one-wey task at 4 and 8 runs per batch, where the world's fixed per-tick cost dominates.
  2. **Use a one-wey memory task.** The redesign already calls for a memory task. Built with one
     wey per world, like E1's Task N, it also unlocks lever 1's larger gain, and it cuts brain work
     per world about twentyfold.
  3. **Stage the design.** Run the cheap original-partner refits first. Buy the free searches
     only for targets whose refits are reliable, and stop a search early once it has clearly
     failed. The rules are fixed before the run.
  4. **A leaner search.** Fewer replicas or generations, if the pilot (on shuffles only, never N2)
     shows the search still converges.
  5. **Fewer brain substeps.** The brain's cost scales with them. 32 was chosen for accuracy in 02,
     so a lower count needs the timestep-accuracy check first.
  6. **A sister experiment, not a faster 03a:** score the reinserted neuron by how well the whole
     network reproduces the intact brain's activity on recorded inputs, with no world simulated.
     It could be one to two orders of magnitude cheaper. But it asks whether wiring can be recovered
     from dynamics, not from a task, so it would be a separate, separately registered question.
- **When:** after E1. E1's pilot measures a one-wey task's actual throughput, and the proof of
  concept is sized to that, not to these estimates. Track B's mechanism follow-up for P4 stays
  ahead of it in the queue unless the owner reorders them.

### Later biology questions (unscheduled)

- **Topology × optimizer × normalisation.** Matching spectral radius is one control, not a complete match.
- **A family of named nulls.** State what each preserves, including how the somatic–pharyngeal gap-junction bridge is treated.
- **Activity-anchored fitness.** Match a few recorded perturbation responses; task scores alone leave the wiring underdetermined.
- **A neuromodulatory layer.** The worm's real roaming and dwelling switch is largely neuromodulatory.
- **Sensing over time versus stereo sensing.** Use head oscillation and scripted positive controls for both.

## Standing rules

- **Develop and pilot openly.** Before confirmatory runs, freeze the hypotheses, comparisons, code version, analysis, budget and stopping rules. Keep pilot results separate. Pilots never run the confirmatory comparison itself.
- **Push each pre-registration to GitHub before its confirmatory runs start.** Commit dates are set locally, so only GitHub's receipt time proves the order.
- Change one thing per experiment. Record deviations in DECISIONS.md.
- **Unit of analysis:** the independent evolutionary run. Comparisons against wiring nulls use several independent graphs per ensemble, with runs within graphs.
- Every behaviour claim needs baselines: random or generation-0 strains, and scripted controllers. Every new task gets a scripted positive control before evolution.
- Compare methods at equal total simulator work, including tuning and pretraining, and report GPU time.
- Implementation changes get documented equivalence checks. A suspected bug gets a failing test before its fix.
- Name every null operation. Prefer experiment 03's validated ensembles.
- Publish corrections to public claims promptly, quoting the wrong text rather than deleting it.
- **Novelty wording:** "we did not find a matching study".
- Before each confirmatory freeze, get external review from a model family different from the designer's.
- **Data hygiene:** no connectome data redistributed in any form; `allow_pickle=False` everywhere.

**Reading negative results:**

| Result | Say | Don't say |
|---|---|---|
| Random sampling matches the GA | Check task saturation, optimizer effectiveness, noise and budget | "The task is too easy" |
| N2 matches the nulls | "No detected advantage under these tasks, controls and budgets" | "The worm wiring is neutral" |
| Assembly loses on first use | "This assembly method did not improve the tested cost–performance trade-off"; judge again on cumulative reuse | "Modularity fails" |
| A replication fails | "A borderline result that did not replicate" | Redesigning until it passes |

## Related work

- **Survey v2.** Apply the external review's corrections before citing the survey:
  - remove the claim that N2 learns faster;
  - state fading biological advantage as a hypothesis;
  - name each study's shuffle operation;
  - separate random sampling from Augmented Random Search;
  - drop the 43% animal-to-animal variability as a recovery ceiling;
  - cite the Creamer et al. preprint by version;
  - describe named neurons as solving gene correspondence, not co-adaptation.

  *(2026-10-15: survey v2 is not committed here, so whether these corrections were applied cannot be checked from
  this repository. Nothing here cites it.)*
- **ENOMAD** (Churchland and Garcia-Ojalvo) is the closest prior work. Read it in full before E2.
- **The E4s literature review** (`docs/reviews/20261001-literature-review/`, 2026-10-01; two reviews,
  Claude Opus and Astra 6, not verified by us as a whole). Each claim is verified before it is cited.
  - Izquierdo & Beer 2013 is the reference worm-chemotaxis model.
  - Hironaka & Sumi's MIT repository is a candidate executable baseline, not yet run.
- **For the memory thread,** compare 02b's critical core and 03's history effect with the state-dependent mechanisms in evolved klinotaxis models (Izquierdo and colleagues) and with the navigation interneurons in the experimental literature, citing only what survey v2 has checked.
- **A collective-behaviour survey** is needed before claims for stages 05 to 08. It should cover double-pheromone mechanisms, evolved signalling, swarm robotics, task allocation, behaviour arbitration, predator–prey coevolution, and causal measures of cooperation.

## What would change this roadmap

- **03r replicates:** the mechanism follow-up comes next in Track B, 03a switches to a memory task, and bridge 2 gains priority.
- **03r does not replicate:** the memory thread leaves the plan, and 03a's task is chosen on other grounds.
- **The next experiment does not fit at measured speed:** shrink the experiment first. Change frameworks only if profiling points there.
- **The E1 positive control fails:** redesign the body or sensors before evolving anything.
- **E2 finds random sampling matching the GA:** diagnose saturation, noise and budget before building on the task.
  - *Triggered 2026-09-29 (E2, D124):* random sampling came within 0.36 targets of the GA, inside
    the registered 0.5. The diagnosis, E2d, ran (D127-D137): a non-stereo plateau that no tested
    change leaves; E3's design takes it from there. The reviewers'
    first suggestions are in D125.
- **No comparator step qualifies in E4s-0** (added 2026-10-01): the owner decides among wider or
  rescaled weights, temporal sensing with head oscillation, and larger circuits. E3 proceeds on 04a
  run 2.
- **E4s-1 finds no "retained" majority** (added 2026-10-01): E3 keeps E4s-0's frozen module, and the
  result is reported in the wording fixed in advance.
- **The minimal A/B organism fails:** diagnose sensing, objective, controller capacity and optimizer progress separately before adding capability.
- **04c finds no useful transfer:** report it, and check whether the latch or the module interfaces block transfer before concluding anything about evolution.
  - *2026-10-15:* in the diagnostic task, E4-D, evolution found the transfer (D280). In the main task the question
    stays open: its formal run was dropped (D258).
- **Infrastructure keeps growing while the first organism does not exist:** the tripwire applies. Stop and ship the minimal A/B organism.

## Carried over from v2.2

Items v2.2 had that v3's text does not, kept here until the owner decides them:

- **The owner's question, as v2.2 put it:** is the worm connectome shaped for worm-like tasks,
  under worm-like plasticity?
- **Plasticity.** D045 recorded "design now, run later":
  - one within-lifetime adaptation task, for example a food-odour association that reverses
    mid-life;
  - one explicit rule, for example reward-modulated Hebbian learning on chemical synapses;
  - three controls: frozen weights, recurrent memory without plasticity, and the rule on
    shuffled graphs.
  It runs only after a task and search are validated.
- **Task specificity.** A matched non-worm-like control task on the same interface and world.
  "Avoid food" is not suitable: 03's design rejected it because it can be solved by not moving. Worm-task *specificity* has still never been
  tested. 03 compared N2 with null graphs, not tasks with control tasks.
- **The label "04".** v2.2 and older documents (the 03a draft, 03's pre-registration and
  DECISIONS) use "04" for *capability use with the 03 controls*, gated by a capability-task
  pilot (3b): a task where matched current observations need different actions, validated
  against memoryless controllers. In v3, 04a-c are Track E stages. Documents written before v3
  keep the old meaning.
- **Later, from the 03a draft:** the full self-consistency map, leave-k-out, missing synapses,
  and a full self-consistent-field loop.

## Credits

Ideas, direction and decisions: Juan H. González Estefan. Stage structure and two roadmap reviews: Astra 6 (OpenAI). Experiments 02b, 03 and 03r and the status report: Claude Code running Claude Opus 5.5 (Anthropic). Reviews of 02, 02b, 03 and 03r at every stage: Astra 6 (OpenAI) and Fable 5.1 (Anthropic); each review is archived in `docs/reviews/`, and the errors they caught are in `docs/REVIEW_TRAIL.md`. Roadmap versions, in conversation: Claude (Anthropic), using Claude Fable 5.1 and later Claude Opus 5.5.
