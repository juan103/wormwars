# M6, step 1: do the switches' states outlast the input? — the plan

*Draft 2, 2026-10-30, after one round of review (Astra 6 and Fable 5.1: both "agree with fixes"; every fix taken;
draft 1, the prompt and the reviews are in [`docs/reviews/20261030-m6-outlast-plan/`](../reviews/20261030-m6-outlast-plan/)).
The owner's order after M6-3 (D379) puts this quick check first, then a test of whether the evolved champions'
fading history effect matters for foraging, then a stop. Fable proposed this check in M6-3's review. It is
exploratory and descriptive: no pre-registration, but the genomes, the phases, the measures and the wordings are
fixed here before the run. CPU only.*

## The question

The model's switches are two stable states that a food history selects under a held input. The probe holds the
final food level throughout, so they are attractors under constant drive: the same broad kind as the multistability
in earlier connectome models (Kunert-Graf et al. 2017; Liu J et al. 2022; [`M6-3-LITERATURE.md`](M6-3-LITERATURE.md),
section 5). Two things remain unmeasured, and they are measured separately (Astra):
- **During a removal of the input, do the histories stay in two distinct states?** Under Z, with no sensory input at
  all, a yes would mean the network alone holds two states. F0 keeps the other sensory channels, so it says less.
- **After the input returns, is each history back at its own original state?** If so, the bit outlasted the gap.

This is a description of switches already classified, not a new question.

**Seen before this plan.** A smoke run of the three phases on the first 4 switch genomes of N2's seed-7700 panel timed
the phases and tested the code:
- A took about 6 s for the 4 genomes, and each arm about 12 s;
- all 4 reproduced their census class in A;
- under both F0 and Z, B was fading, and after restoration C was fading, with both histories at the rising-start
  history's A root.

Those 4 genomes stay in the run, labelled as seen before the plan. The "both at" labels of the root match were added
after the smoke run.

**What to expect if the input-free state is unique (Fable).** Restoration is a one-tick step up from zero, not the
probe's 10-tick ramp. If the network without input has a single state, C starts both histories from it, and a
step rise selects one root. So "merged at one A root", for example the rising-start one, is the signature of an
attractor that is selected by its path and needs its input. It is not a surprise.

## The genomes

Every switch ("separate states", both subclasses) from the two M2 and eight M4c N2 census panels, under M0 and
03mc's bank (Astra):
- **M2's census:** seeds 7600 and 7700, with 15 and 13 switches (`runs/memory-m2-census/N2__*.json`);
- **M4c's census:** seeds 7801 to 7808, with 141 switches (`runs/memory-m4c/census/`).

That makes 169 genomes, four of them read-out silent. Switches found elsewhere, such as M6-0's under other mappings
and banks or null-graph switches, are not included.

Each genome is rebuilt by the census's own route: `S.genomes` on N2 with panel size 1024 and the panel's seed, then
the recorded ids. Where the census's local state arrays exist, A's roots are compared with the stored roots, and
the count within 1e-6 is reported (Fable). That check pins both the rebuild and any effect of batch composition: the
census ran chunks of 128, and this run batches 12 to 26 genomes a panel.

## The phases

All three run in M1's probe on M0's interface, with the context setting the input. **The input changes in one step**
at B's start and again at C's start.

- **A, the standard probe.** It warms up at 0.25 or 1.75 of the final food level, ramps for 10 ticks, then holds for
  2000 ticks under 03mc's bank (`pilot.probe_states`), with M2's frozen classifier at the end (`full_classify`,
  first pass, as the census ran it).
  - **The consistency check:** A must reproduce each genome's census class.
  - **If it does not:** a failing genome is left out of the readings and reported. A ninth failure (more than 5% of
    169) stops the run at once, with the diagnostic records kept.
- **B, the input changed.** From A's two end states, the network runs 2000 ticks under the changed input
  (`pilot.follow_from` inside `probe_input`). It is classified under that input, and the oscillation check reruns
  from B's start. There are two arms:
  - **F0:** both food channels at 0, every other channel of the bank kept;
  - **Z:** every channel at 0, so the sensory current is zero and the biases remain.
  - **The separation** between the two histories (the maximum absolute state difference) is recorded at B's ticks 0,
    10, 30, 100, 300 and 2000, to show how fast any merging is (Fable).
- **C, the input restored.** From B's actual end states (not its roots), the network runs 2000 ticks under 03mc's bank
  again, and is classified.

**"Read-out silent" in B and C** is relative to that phase's own starting read-out difference, not the original
ramp's (Astra). Both subclasses count as two states.

## The measures, per genome and arm

- **Held (from B alone):** B is separate states. Otherwise it is not held, or unresolved.
- **After restoration (from C alone; Fable):**
  - **recovered:** C is separate states, and each history sits at its own A root;
  - **merged:** C is fading, with both histories at one root, reported as at the rising-start history's A root, at
    the falling-start one's, or at neither;
  - **other:** swapped, new roots or oscillation;
  - **unresolved.**
- **The root match uses the classifier's own distinctness level, 1e-6** (`classify.DISTINCT`). Draft 1's 1e-4 was
  wrongly called the classifier's level. A genome whose A roots lie closer than twice that level is marked
  "ambiguous" (Fable). The distances from C's roots to A's are recorded for every genome (Astra).
- **Dropped from draft 1:** the read-out-sign clause. The read-out difference is recorded as an absolute value, and
  root identity already decides the match (both).

## The readings, fixed now

Draft 1's majority rule is cut (Astra). Per arm, the reader reports:
- **held:** the count with unresolved bounds (B-unresolved genomes counted either way), its share and the 95% Wilson
  intervals at both bounds;
- **recovered:** the same, with C-unresolved genomes counted either way;
- **the rest:** the merged roots, B's median and largest separations by tick, and counts by panel, subclass and the
  seen-before set.

**The wordings name the gap:**
- "k of n switches held two states during a 2000-tick removal of the food input" (or "of all sensory input");
- "k of n switches returned to their original states after a 2000-tick removal of …";
- each with "(u unresolved)" when there are any.

The intervals describe sampling uncertainty for the population of genome draws. The counts are the description of
these 169 (Astra).

**Inconclusive** overrides all of this:
- the run is incomplete;
- its rows differ from `genomes.json`;
- its consistency check stopped it, or fails on reading.

**What this cannot show:**
- that a shorter interruption, or a partial reduction of the input, would also erase the states;
- that no other input-free attractor exists.

No duration or partial-input sweep is added (both).

## Outputs, cost and tests

- **Code:** `scripts/memory_m6/outlast.py` (stages `genomes`, `run`), `outlast_read.py` and `sabotage_outlast.py`.
- **Records:** in `runs/memory-m6-outlast/`. The JSON records are committed; `roots.npz` stays local. The results go
  in `docs/memory/M6-OUTLAST-RESULTS.md`. Compute is recorded by `wormwars.accounting`.
- **Cost.** The smoke run gives about 7.5 s a genome for all phases, so about 20 to 25 minutes before oscillation
  checks.
- **The cap.** The run stops at 1 CPU hour. The cap is checked before every phase and before the record is written,
  so it is a checkpointed cap, and one phase can overrun it (Astra).
- **Tests** (`tests/test_memory_m6_outlast.py`), each seen failing under a sabotage of the code it checks (23 of 23
  caught, `runs/outlast-sabotage.txt`):
  - **the inputs:** F0 and Z give the stated currents;
  - **the phases:** B continues from A's end states under the changed input; with fakes, the wrapper runs B inside
    the context from A's end and C outside it from B's end, and gives the classifier the same start;
  - **the rebuild:** two genomes reproduce the census roots within 1e-6 (skipped without the local arrays);
  - **the genome list and the seen set;**
  - **the root match:** same, swapped, both at 0, both at 1, new and ambiguous;
  - **the outcome and held rules;**
  - **the separation ticks;**
  - **the reader:** the count wordings with the gap, and the guards (incomplete, partial or stale rows, a stopped or
    failing consistency check, and exclusions).
