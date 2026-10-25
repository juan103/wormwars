# Review: the README and ROADMAP status update that takes the memory thread (M1 to M4d) to `main`

You are reviewing, read-only, a small documentation change in the WormWars repository (cwd). The owner asked to bring
`main` up to date with `roadmap` (18 commits: D349-D364, the memory thread's M1 to M4d). Before merging, Claude added
a dated status entry to ROADMAP.md, a README row and "Next" bullet, and DECISIONS D365. The diff is below.

Check every claim against the committed sources: docs/memory/M1-RESULTS.md, M2-CENSUS-RESULTS.md, M2-PILOT-RESULTS.md,
M3-NOTE.md, M4A-RESULTS.md, M4B-RESULTS.md, M4C-RESULTS.md, M4D-RESULTS.md, MEMORY-ROADMAP.md (its annotations), and
DECISIONS D349-D364. Look in particular for:
- overclaiming or wrong numbers (each number should trace to a results file);
- readings stated more strongly than their registered wording (unresolved, inconclusive, positive);
- the correction of the earlier "amplitude-weighted, not the typical genome" finding: is it right and fair?
- anything a reader of `main`'s README would misread;
- whether rule 4 of AGENTS.md (correct in the open; dated annotations, nothing deleted) is respected.

Answer with a verdict, "publish" or "fix first", and a numbered list of findings (file, line or quote, what is wrong,
the fix). Keep it short; small style points only if they mislead.

## The diff

```diff
diff --git a/DECISIONS.md b/DECISIONS.md
index bf7431c..59ce55e 100644
--- a/DECISIONS.md
+++ b/DECISIONS.md
@@ -11676,3 +11676,21 @@ screen as unresolved; do not resolve the 86 unresolved T and R genomes now (a re
 reading or "Unresolved", would be chosen knowing the lean, and most are unsettled histories); do not draft M4e. The
 thread's direction is the owner's: the M1 to M4 write-up (Astra's priority), a planned study of what a dense block
 carries (density and degrees; Fable), or an M5 test of N2's wiring after a power calculation for effects above m.
+
+## D365 — The memory thread's M1 to M4 go to `main`; ROADMAP's status and the README catch up; the owner orders what follows (2026-10-25)
+
+**The owner** asked whether `main` was up to date (it was 18 commits behind `roadmap`: D349-D364 and the banner) and
+said to bring it up to date, then to do all three next steps in this order: the M1 to M4 write-up, a study of what a
+dense block carries, and an M5 test of N2's exact wiring after a power calculation.
+
+**What changed before the merge:** `ROADMAP.md`'s status section still said "Next: M1", and the README had no entry
+for the memory thread.
+- `ROADMAP.md`: a dated 25 October status entry summarising M1 to M4d and the owner's order; the 20 October entry's
+  "N2's lead is in the amplitude-weighted share, not in the typical genome" annotated with M1's correction (D350),
+  and its "Next: M1" annotated as done; a dated note under "The thread worth following".
+- `README.md`: a row for the memory thread in "Experiments at a glance"; the biology bullet of "Next on the roadmap"
+  updated, the earlier sentence kept as an "Earlier" quote; the `roadmap` banner names M1 to M4.
+- Every number is taken from the results files' "In short" sections and the memory roadmap's annotations.
+
+**The merge** follows D342/D348's pattern, with no history rewritten: `main` fast-forwards to `roadmap`, one commit
+on `main` removes the working-branch banner, and `roadmap` fast-forwards to `main` and puts the banner back.
diff --git a/README.md b/README.md
index 6be64cc..26fbbcb 100644
--- a/README.md
+++ b/README.md
@@ -6,7 +6,8 @@
 > E4-D's feasibility check (2026-10-13), the evolutionary E4-D (2026-10-15, D280-D281; L reads
 > "practically relevant transfer found"), 03mc (2026-10-16, D294-D300; all four primaries pass), 03a
 > (2026-10-18, D302-D320; stopped after pilot-dev, exploratory), and 03h (2026-10-20, D321-D342; stopped before
-> its pre-registration, exploratory), with the memory question's roadmap (D346).
+> its pre-registration, exploratory), with the memory question's roadmap (D346), and the memory thread's M1 to M4
+> (2026-10-25, D349-D365; exploratory).
 
 Many parallel 2D worlds on one GPU. In each world, swarms of small creatures called **weys** forage
 and fight. Every wey's brain is a small continuous-time recurrent network whose wiring is the real
@@ -37,6 +38,7 @@ selection acts on team results.
 | [03r](experiments/03r-replication/README.md) | A full, separately pre-registered replication of 03 | Published; pre-registered | "Replicated under the registered single-signal test and under 03's original three-signal rule." |
 | [03a](experiments/03a-self-consistency/README.md) | Can a missing neuron's wiring be predicted from the rest of the brain plus a task? | Exploratory: stopped after pilot-dev, its development stage on one shuffled graph, and a bounded check of the search (2026-10-18, D312-D319); never pre-registered; 5.84 of its 72 GPU-hours. *Earlier: "Draft; a six-neuron proof of concept capped at 72 GPU-hours is planned (D094), next in Track B after 03mc; not started".* | The search could not test the hypothesis on one shuffled graph: refits handed the true partners stayed about 0.1 below exact restoration under four search settings, and no enrichment toward the true partners was detected. No reconstruction search ran on N2. *Earlier: "None yet. As drafted, its searches alone need about 785 GPU-hours at 02's throughput, plus about 37 for whole-brain evolution".* |
 | [03h](experiments/03h-history-use/README.md) | Does the history random brains hold predict how well they forage, and is N2's generation-0 head start larger when memory is needed? | Exploratory: stopped before its pre-registration, after its bound pilot, a power analysis and an amplitude check (2026-10-19, D321-D342); 0.349 of 1.0 GPU-hours | A "the food fell" bit gives a scripted controller 98% of memory's +0.985 on T1, but its average effect in random brains on three shuffled graphs was small (about 0.5% of the selected deciles' scores) and uneven, so exploratory scenarios suggested B's head-start test would rarely pass. No history-fitness or relief comparison ran on N2. In SH samples, the direction of the history held showed a weak positive association with fitness; its size, a near-zero one |
+| [Memory, M1-M4](docs/memory/MEMORY-ROADMAP.md) | Why does N2's history difference last longer in unevolved brains (03mc's Q-D), and where is it held? | Exploratory, on the CPU: M1 to M4d, each planned and reviewed by both before it ran and its results reviewed after (2026-10-20 to 10-25, D349-D364); never pre-registered | N2's mean per-genome retention is extreme, not only its amplitude-weighted share (a correction); neither read-out alignment nor response amplitude explains the lead. A small minority of genomes hold the history in two stable states (a switch); at tick 30 they carry 0.35 and 0.47 of N2's lead on its two panels (inconclusive), at tick 300 most of it. In N2, cutting RIA's head-core edges for 30 ticks erases 58% to 72% of the switches, against 22% to 30% for weight-matched edge sets (positive). N2's head-core block raises the share of switch genomes in all ten fresh host graphs (0.04% to 0.62%), but copies rewired at the same degrees reach 0.51%: whether its exact wiring matters is unresolved |
 | [E1](experiments/E1-navigation/README.md) | Can a scripted navigator reach moved targets on unseen layouts, beat blind search, and use the cue? The positive control before evolving a navigator | Published; pre-registered, public before its run | "E1 positive control: passed": 8.68 targets per episode (98.7% of an oracle); 0.03 with a mirrored decoy |
 | [04a](experiments/04a-navigation-primitive/README.md) | Can evolution, from random weights on the N2 wiring, produce a brain that reaches moved targets, beats blind search and uses the cue? | Published; pre-registered, public before its run | "04a: passed": 8 of 12 shaped runs (4 of 4 unshaped); the champions use the cue but are weak navigators (2.0-2.8 targets, 23-32% of an oracle) |
 | [03m](experiments/03m-p4-mechanism/README.md) | What drives 03's history dependence (P4)? | Exploratory; run, reviewed, corrected | N2's history fades more slowly than nearly all the shuffles'; its large food response depends on weight placement and on RIA and AIY; most weight permutations lower its P4, gap junctions narrow its lead, and no tested single or paired deletion removed it |
@@ -52,8 +54,11 @@ selection acts on team results.
 - **In the biology track:** 03mc, the confirmatory study of 03m's leads, passed all four primaries (2026-10-16).
   03a's six-neuron proof of concept then stopped after pilot-dev (exploratory, 2026-10-18). The memory thread's
   first design, 03h, stopped before its pre-registration (exploratory, 2026-10-19): its relief had a small, uneven
-  average effect in random brains, so its head-start test looked very unlikely to pass. What follows is not yet
-  chosen. *Earlier (18 October):
+  average effect in random brains, so its head-start test looked very unlikely to pass. The memory thread then ran
+  M1 to M4 on the CPU (exploratory, 2026-10-20 to 10-25; see its row above). Next, in the owner's order: a write-up
+  of M1 to M4; a planned study of what a dense block carries (its size, weights and degrees); then an M5 test of N2's
+  exact wiring, after working out how many hosts it would need. *Earlier (20 October): "What follows is not yet
+  chosen."* *Earlier (18 October):
   "Next: a design round for the memory thread's predictions."* *Earlier (16 October): "03a's six-neuron proof of concept is next; it has not
   started."*
 - [`ROADMAP.md`](ROADMAP.md)'s status section lists what v3 planned that has not run, and what waits for the
diff --git a/ROADMAP.md b/ROADMAP.md
index fad52ef..24ee983 100644
--- a/ROADMAP.md
+++ b/ROADMAP.md
@@ -2,7 +2,36 @@
 
 *27 September 2026. Replaces v2. Written from roadmap v2, Astra 6's review of v2, and Claude Code's status report of the same day. A local v2.2 exists on the `roadmap` branch and was not seen when this version was written, so merge anything it adds. (Merged: see "Carried over from v2.2" below. Four factual corrections were made on installation; they are listed in D062.) This is a living document, not a pre-registration. When a result changes it, the change is recorded here with the reason.*
 
-## Status, 1-20 October 2026 (updates the section below; that section's later edits are recorded in DECISIONS.md)
+## Status, 1-25 October 2026 (updates the section below; that section's later edits are recorded in DECISIONS.md)
+
+**25 October 2026** (D349-D365): **the memory thread's M1 to M4 have run** (exploratory, on the CPU; results in
+[`docs/memory/`](docs/memory/), each stage annotated in [`MEMORY-ROADMAP.md`](docs/memory/MEMORY-ROADMAP.md)). Every
+run's plan was fixed and reviewed by Astra and Fable before it ran, and its results reviewed after; none is a
+pre-registration.
+- **M1** (D349-D352) corrects the memory roadmap's first finding: N2's unweighted mean per-genome retention is extreme
+  too (0.586, against ensemble medians of 0.370 to 0.412; none of 640 graphs reaches it), and the amplitude weighting
+  lowers N2's share. Read-out alignment does not carry the lead (persistence does), and in a targeted replication the
+  lead survives whole at matched response amplitude.
+- **M2** (D353-D356): a validated classifier finds a small minority of genomes holding the history in two stable
+  states, "separate states" (15 and 13 of N2's eligible genomes on its two panels). At tick 30 they carry 0.47 and
+  0.35 of N2's mean lead over 30 reference graphs ("inconclusive": the intervals are wide); fading genomes, which keep more of their difference than the reference
+  graphs' fading genomes do, carry 0.44 and 0.64.
+  At tick 300 separate states carry most of it.
+- **M3** (D357) closed as a completed screen; the head core C3, defined from the anatomy alone, went to M4.
+- **M4a** (D357-D358), "unresolved": cutting C3's internal edges for 30 ticks costs more than every one of 30 sampled
+  cuts of equal size on both of N2's panels, but one panel's interval reaches the margin. Started from their two roots,
+  26 of N2's 28 separate-states genomes end in one basin after C3's cut (14% under the sampled cuts).
+- **M4b** (D359-D360), "unresolved": in N2, cutting the edges where a switch's states differ erases 89% of the
+  switches, against 31% and 11% for controls; across ten selected graphs it is not shown. RIA's core edges alone
+  erase most of N2's switches.
+- **M4c** (D361-D362), positive: on 141 fresh N2 switch genomes, RIAR's and RIAL's core edges erase 72% and 58%,
+  against 22% to 30% for three families of weight-matched edge sets. A place of vulnerability, not shown to be storage.
+- **M4d** (D363-D364), "Unresolved (the unresolved genomes decide it)": N2's C3 block raises the share of
+  separate-states genomes in all ten fresh host graphs (from 0.04% to 0.62%), but copies rewired at the same degrees
+  reach 0.51%, so whether its exact wiring matters is unresolved.
+- **Next (the owner, 2026-10-25), in this order:** a write-up of M1 to M4; a planned study of what a dense block
+  carries (its size, weights and degrees); then an M5 test of N2's exact wiring, after working out how many hosts it
+  would need. All on the CPU unless the owner gives the GPU.
 
 **20 October 2026** (D346): **a roadmap for the memory question** ([`docs/memory/MEMORY-ROADMAP.md`](docs/memory/MEMORY-ROADMAP.md)).
 - **The question:** why the history difference decays more slowly in N2's random brains (03mc's Q-D).
@@ -11,7 +40,9 @@
   Fable as the other voices. Exploratory CPU checks ran between the rounds. The roadmap was reviewed twice by both and
   agreed. Everything is archived in `docs/reviews/20261020-memory-*`.
 - **What it found, exploratory:**
-  - N2's lead is in the amplitude-weighted share, not in the typical genome;
+  - N2's lead is in the amplitude-weighted share, not in the typical genome; *corrected 2026-10-25 (D365, from M1,
+    D350): misleading. N2's unweighted mean per-genome retention is extreme too, and the weighting lowers its share;
+    only the median genome is ordinary;*
   - a minority of brains in N2 and in the nulls may hold the history in separate states, and N2 has more of them
     than most null graphs;
   - a head core around the turn read-out (RIA, RIM, AIB, AIZ, RMD, SMD and others) preserves most of the lead in an
@@ -19,7 +50,8 @@
 - **The plan:** accounting, amplitude and cheap kills (M1); a validated dynamical census (M2); a core defined from
   the anatomy alone (M3); write, hold and read, separated, with a transplant screen (M4). All exploratory, on the CPU.
   Then the owner's transplant, pre-registered (M5).
-- **Next:** M1, when the owner wants it. It needs no GPU.
+- **Next:** M1, when the owner wants it. It needs no GPU. *Done: M1 to M4 ran from 20 to 25 October; see 25 October,
+  above.*
 
 
 **19 October 2026** (D321-D342): **03h stopped before its pre-registration; exploratory**
@@ -383,7 +415,9 @@ Several results point the same way:
 
 *20 October 2026 (D346): why N2's history lasts longer in unevolved brains now has its own exploratory roadmap,
 [`docs/memory/MEMORY-ROADMAP.md`](docs/memory/MEMORY-ROADMAP.md). Its first checks point at a head circuit around the
-turn read-out, which bears on the third prediction.*
+turn read-out, which bears on the third prediction.* *25 October 2026 (D365): M1 to M4 have run (status, above). In
+N2, RIA's head-core edges are a place where the history held in two stable states is vulnerable; whether N2's exact
+head-core wiring carries it into other graphs is unresolved.*
 
 ## Two tracks, one priority
 
```
