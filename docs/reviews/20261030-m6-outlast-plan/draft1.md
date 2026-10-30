# M6, step 1: do the switches' states outlast the input? — the plan

*Draft 1, 2026-10-30, before review. The owner's order after M6-3 (D379): this quick check first, then a test of
whether the evolved champions' fading history effect matters for foraging, then stop. Fable proposed it in M6-3's
review. Exploratory and descriptive: no pre-registration, but the genomes, the phases, the classes and the readings
are fixed here before the run. CPU only.*

## The question

The model's switches are two stable states that a food history selects, under a held input. The probe holds the
final food level throughout, so they are attractors under constant drive, the same broad kind as earlier connectome
models' multistability (Kunert-Graf et al. 2017; Liu J et al. 2022; [`M6-3-LITERATURE.md`](M6-3-LITERATURE.md),
section 5). Two things remain open:
- **Do the two states survive when the input is taken away?** If they do, the network alone holds them.
- **Does each history come back to its own state when the input returns?** If it does, the bit outlasts a gap in
  the input.

Neither has been measured. This is a description of the switches already classified, not a new question.

**Seen before this plan.** A smoke run of the three phases on the first 4 switch genomes of N2's seed-7700 panel
timed the phases and tested the code. A took about 6 s and each arm about 12 s for the 4. All 4 reproduced their
census class in A. Under both F0 and Z, B was fading, and after restoration C was fading, with both histories at the
rising-start history's A root. Those 4 genomes stay in the run, labelled as seen before the plan. The root-match rule
gained the "both at" labels after that smoke run.

## The genomes

Every N2 switch genome classified so far ("separate states", both subclasses), regenerated from its panel:
- **M2's census:** N2's panels at seeds 7600 and 7700, 15 and 13 switches (`runs/memory-m2-census/N2__*.json`);
- **M4c's census:** the fresh N2 panels at seeds 7801 to 7808, 141 switches (`runs/memory-m4c/census/`).

That makes 169 genomes in all. Each is rebuilt with the census's own route (`S.genomes` on N2 with the panel's size
and seed, then the recorded genome ids). Null-graph switches are not included.

## The phases

All three phases run inside M1's probe on M0's interface. The context sets the input for each.

- **A, the standard probe.** It warms up at 0.25 or 1.75 of the final food level, ramps for 10 ticks, then holds
  for 2000 ticks under 03mc's bank (`pilot.probe_states`). M2's frozen classifier runs at the end (`full_classify`,
  first pass).
  - **Consistency check:** A must reproduce each genome's census class.
  - **If it does not:** a genome that does is kept. One that does not is reported and left out of the readings. If
    more than 5% fail, the run stops for investigation.
- **B, the input changed.** From A's two end states, the network runs 2000 ticks under the changed input
  (`pilot.follow_from` inside `probe_input`). It is classified under that input, with B's start states as the
  oscillation check's initial states. There are two arms:
  - **F0:** both food channels at 0, every other channel of the bank kept;
  - **Z:** every channel at 0, so the sensory current is zero.
- **C, the input restored.** From B's end states, the network runs 2000 ticks under 03mc's bank again, and is
  classified.

## The outcomes, per genome and arm

- **Held:** B is separate states, so two distinct states exist under the changed input and the histories sit in
  different ones.
- **Recovered:** C is separate states, and each history sits at its own root from A. That means a maximum absolute
  difference from A's root below 1e-4 (the classifier's distinctness level), with the read-out difference's sign
  unchanged.
- **Merged:** C has both histories at one root. It is reported as at the rising-start history's A root, at the
  falling-start one's, or at neither.
- **Other:** C is separate states with the histories swapped or at new roots, or C is oscillation.
- **Unresolved:** B or C is unresolved. These are never counted as recovered or not (M6-0's rule); they enter the
  bounds below.

## The readings, fixed now

Per arm:
- **The recovered share,** with a 95% Wilson interval, at both unresolved bounds: unresolved counted as not
  recovered, then as recovered.
- **"The switches' states outlast removal of the input"** if the lower bound of the interval is above 0.5 at both
  bounds.
- **"They do not"** if the upper bound is below 0.5 at both bounds.
- **"Mixed"** otherwise. If the reading differs between the two unresolved bounds, it is "unresolved (the unresolved
  genomes decide it)".
- **The held share and its interval** are reported beside it.
- **Context, not readings:** the counts by panel and subclass, and B's and C's full class counts.

**Inconclusive overrides everything:** the run is incomplete, or the consistency check stops it.

## Outputs, cost and tests

- **Code:** `scripts/memory_m6/outlast.py` (stages `genomes`, `run`) and `outlast_read.py`.
- **Records:** in `runs/memory-m6-outlast/`. The JSON records are committed; the state arrays stay local. The
  results go in `docs/memory/M6-OUTLAST-RESULTS.md`. Compute is recorded by `wormwars.accounting`.
- **Cost.** 169 genomes through five probe-lengths each (A, then B and C for each arm), with classification. At M6-0's
  rate of about 0.75 s a genome per first pass, plus classification, that is a few minutes to under an hour. **The
  run stops at 1 CPU hour.**
- **Tests,** each seen failing first or under sabotage:
  - under F0 the food sensors get zero current and the others keep theirs; under Z every sensor gets zero;
  - B continues from A's end states (its first step equals one step from them under the changed input);
  - the rebuilt genomes are exactly the census ids (skipped without the local census arrays where needed);
  - the root-match rule on constructed roots (same, swapped, new);
  - reader cases: each wording, the unresolved straddle and the consistency stop.
