**Verdict: adopt with changes.** The sequence is right, but E4s-0's decision rules are thinner than the proposal claims, and several statements need fixing before it becomes a roadmap amendment.

## Must-fix

1. **"Why a change", plateau bullet.** "No evolved champion (0 of 47) steers by the left-right scent difference" repeats wording that D137 correction 4 already withdrew as too absolute. Use the corrected form: none meets the "uses" criterion; 43 show no material benefit, 4 are unclear.

2. **E4s-0 item 3: say how the comparator is wired.** "Two extra neurons" receiving a(L − R) cannot be built with the current `Module`.
   - `Module.noses` gives each nose one signal at one positive `nose_gain` (`graft.py:47-48`).
   - The options are signed interface gains (which drops v3's "nose gain 1, not tuned" and puts `a` outside the ±3 genome bound), two relay noses plus two comparators (four neurons), or reading the host's AWA/AWC/ASE.
   - The last option breaks the module-only probes. Pick one and state the neuron count.

3. **E4s-0 item 3: define the variant ladder before the "bounds go back to the owner" rule.**
   - By my estimate the two-unit comparator on the carrier gives turn ≈ 4·w_o·a·d, about 36·d at a = w_o = 3. E1's curve puts k = 32 at 5.63 with a tuned turn bias and 4.23 without, so the 5.0 line is borderline.
   - Gain also scales with parallel copies, not only with bounds. A failure would therefore not show a bounds problem unless the ladder (recurrence, four units, N parallel pairs, a maximum size) and the carrier grid are fixed first.
   - I did not run this; it is arithmetic from the code.

4. **Design v3 states the turn read-out as clamp(2·[…]); the code gives a factor of 1.** `world.py:750` multiplies by 0.5 × `turn_gain`, and `turn_gain` is 2.0 in `configs/default.yaml` and in E1's `freeze.json`. I did not trace every config override. Check it before reusing v3's numbers; it halves every gain estimate.

5. **E4s-0 item 3: add random N2 backgrounds.** E4s-1's confirmatory background is random N2, but the comparator is measured only on the carrier and on 04a run 2.
   - Random backgrounds mostly score zero and move slowly, with turn-neuron τ up to 20. The graft may well not "use" the difference at generation 0 there.
   - Carry over v3's generation-0 measurement and pre-state the reading. For example: if the graft is "uses" at G0 on fewer than X% of random backgrounds, the confirmatory background becomes the distinct evolved champions, one per run.

6. **E4s-0 items 1 and 2 have no pre-stated readings.** Only item 3 has a decision rule.
   - Item 1: define "rises" and "dips" (paired worlds, an interval, a threshold) and add k below 0.25, since the champions' own gain is about 0.1. Say that it probes one direction in output space, not what a weight mutation does.
   - Item 2: K_D at the sensory neurons is 1 by construction, and "main interneurons" is undefined. Name the neurons and the decision it feeds, or label it descriptive.

7. **E4s-1 outcomes are not exclusive.** "Bypassed", "redundant" and "transferred" overlap, and there is no class for a graft that never worked at G0, nor "unclear". The v1 review already forced exclusive classes. Write a decision table over the module probes, lesion cost, transplant on the carrier and host-only world probes, keeping v3's G0 × F structure.

8. **E4s-1 arms.**
   - Define "random graft". Same edges with random weights and random wiring answer different questions. I would run the topology-matched one: it separates the designed weights from the new two-synapse sensor-to-motor path that bypasses N2.
   - State which arms are "paired controls", the runs per arm, and who owns the output edges in the frozen arm.
   - Keep a registered positive-control gate on fresh worlds. The module is selected on E4s-0's worlds.

9. **E3 addition 1 contradicts "What would change this roadmap".** One says the fallback is 04a run 2; the other says the frozen engineered module. Reconcile them.

10. **Repository state.** The proposal is committed, but material it relies on is not.
    - Design v3, D142, the gain probe v3 output, the GA hooks and their tests, `e4s_equivalence.py` and the v2 review folder are all uncommitted.
    - "Already built and tested" and "D142 records it" are therefore not traceable (rule 5). Commit v3 labelled superseded.
    - Put the dated correction of "a deep research" into the D-entry (rule 4); v3 line 46 still says it.

## The six questions

1. **Sequence:** yes. Deferring the ring is correct; E1's memoryless steerer already shows Task N needs no memory.
2. **E4s-0:** not yet; see items 3, 5 and 6. I would add the random-background measurement and cut or demote item 2.
3. **Option (a):** mostly honest. Two additions:
   - The stereo computation happens in a graft with private sensors and a private path to the motors, outside the N2 mask. Claims should say so.
   - The temporal route needs head oscillation, not only ON/OFF sensors. E1's M-avg scored 2.20 on this body.
4. **Arms and partition:** see items 7 and 8. Zero-initialised host-graft edges are fine. Nothing to drop.
5. **E3:** do not wait. E3's design, latch validation and frozen-module step can start after E4s-0, using the frozen comparator or 04a run 2. E4s-1 decides only whether an evolved retained module replaces it.
6. **Review claims:** see below.

## Literature claims to check before use

- **Checked against the repository:** Opus's claim that food left/right maps to ASEL/ASER is true (`configs/interface.yaml:27-28`).
- **Checked by hand:** the latch τq̇ = −q + 2 tanh q + S − R has fixed points at ±1.915 and a switching threshold of about 0.53, so a unit input suffices. I did not confirm that a graft accepts a self-edge; no test covers it.
- **"Mirror-symmetric parameters" (point 4):** likely wrong as worded. Opus itself notes that Izquierdo & Beer 2013 is inconsistent; the symmetry is dorsoventral on the motor side, not left-right.
- **"Weights up to ±15":** those models use logistic units, and Hironaka adds a sensor gain of 100. It is not comparable to ±3 under tanh, and item 3 suggests bounds are not the binding constraint for a graft.
- **Hironaka & Sumi 2025:** Opus cites it as published, Astra as a reviewed preprint. Settle that, and the MIT licence, before calling it "the reference".
- **Adden's remapping figures and Tomko & Harvey's zero-start result:** these rest on Astra's reading alone. Astra also says zero was "not universally best".
- **Not checked:** I verified no paper against its source. The citations for Rañó, Simões, Noorman, Singh, Sun, Koppejan & Whiteson, Yong, Bryan, Fakhar & Hilgetag and Hülse & Pasemann match papers I know to exist, from memory only.