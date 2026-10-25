**Verdict: fix then publish.** The readings are quoted at their fixed strength everywhere, the interpretation sections are labelled as such, and every number I traced matches its record. What needs fixing is one untraceable claim, one garbled correction, three sentences that go past their source, and attribution gaps on both reviewers' sides.

## Fix before publishing

1. **Untraceable claim, wrong citation.** "One review answer was missed for 8.5 hours by a detached waiter (D364)." D364 says nothing of the kind, and a search of DECISIONS, ROADMAP, every markdown file under docs and every text log under runs finds the sentence only in the synthesis and its archived copy. Rule 5 fails. Record the event in a decision and cite that, or drop the bullet.

2. **The "Count before claiming" example inverts the error.** It says M4a's draft overstated "'most' of the loss, which was 54% and 58%". Over half is most. The wrong "most" was about the separation the switches hold at tick 60, which was a third (33% and 34%); the 54% and 58% are their share of C3's loss and were correct. See M4A-RESULTS, "By class".

3. **"each keeps about its whole start difference"** (section 2). The census says this of the class (retention 0.98 and 1.02) and gives individual ranges of 0.77 to 1.69 and 0.27 to 1.46. Say "as a class".

4. **"A reading across the steps" puts degrees in the robust set.** It groups "size, weights and degrees" as the robust contrasts. Per M4D-RESULTS and D364, R − I and D − I stay above zero over every assignment of the unresolved genomes, but R − D, the degree step, holds on counted genomes only (envelope to −0.0043; Astra's catch). D − I's envelope floor is 0.0009, above zero but under the 0.004 margin, so "robust" here means something weaker than the reading's criterion. And "T against R is small" is a counted-genomes statement; the all-for-T end is +0.0061. Rewrite: the contrasts that survive every assignment are those against the intact host; the degree step holds on counted genomes only; T − R is small on counted genomes and bounded between −0.0054 and 0.0087. The "What it adds up to" bullet's "size, weights and degrees" has the same problem; "size and weights" is what D − I shows.

5. **"Whether N2's exact wiring adds anything"** (bullet 5). The rule tests an advantage of 0.004 or more over rewired copies. Say so; "anything" is a different question the screen cannot answer.

6. **"the same edges at random positions."** Arm D places as many edges, with the same weights and autapses, at random positions. An edge moved is a different edge. Same slip in "Described".

7. **"every choice of direction"** (Who did what, owner). The record shows go-aheads at each step and the ordering after M4d. The M3-to-M4a direction was agreed with both reviewers (D357), M4d was a consensus decision under the delegation after "As you prefer, but confirm" (D363), and M4b and M4c were Claude's proposals. Say "the go-ahead at each step, and the direction after M4d".

## Should fix

8. **Attribution, Astra.** Missing items that shaped the thread's course: Part 2 of M4a from the roots (D357), the assay M4b and M4c then ran on and the source of "26 of 28"; the corner envelope over the unresolved genomes in M4d (D363), which is literally what produced the reading "Unresolved (the unresolved genomes decide it)"; family C in M4c (D361); independent reproductions of M1's summary and bootstrap and M2's numbers as well as M4d's (D350, D352, D354). "independent reruns of M4d's checks and reading" is accurate but narrow.

9. **Attribution, Fable.** I am asked to correct my own. Items recorded in DECISIONS that were design elements, not catches: M4a reading on the full state rather than the read-out, because C3 holds the read-out's afferents (D357); M4b's outgoing control (D359); M4d's Rr arm (D363); the argument that M5 cannot be pre-registered without host base rates (D363), which is why M4d ran as a screen; the withdrawal of M1's ‖δa(0)‖ reading (D352), which the Corrections section records without a name. I would leave out the smaller catches. Add a "Both" line for D357's rule change: a null in M4a reads "not demonstrated", not "access".

10. **Missing limits.** M4c's census ran an unarchived working-tree script (D362); the synthesis discloses the early start but not this. M4c's single-neuron confound: no control scheme removes one core neuron's chemical star inside the core as cutting RIA does, and SMDVL, RMDR and SMDVR erase many switches with less weight, so RIA is the strongest tested cut, not the only one. Without that clause "positive" reads as "RIA is special".

11. **Batch 7's "head core" is not C3.** Section 2 calls it "N2's head core"; it is the result-defined set sharing 18 neurons with C3, and the census warns the location result is partly by construction. Section 3 then introduces C3 as "the anatomy core". An outside reader will merge them.

12. **"against none in most null graphs"** holds for 19 of 30 reference graphs; the ten selected null graphs have 12 to 78 each, more than N2. Qualify.

13. **Wording.** "overstated twice" is three statements in M1-RESULTS and D350. "one panel's interval reaches the margin": the lower bound is 0.008 against 0.10, so "crosses". "reviewed until both agreed": M1, M2 census and M4d each ended with one reviewer's mechanical fix taken without a further round.

## Readability and the script

- Arm letters T, I, R, D, P, Rr, T+G appear in "Robust" and the reading paragraph without ever being introduced, and "D" is also the difference statistic in M4a and in D_TI. Introduce the letters in the design paragraph and avoid bare "D" for the arm.
- An outside reader of main meets N2, the null ensembles, "eligible share", "a", retention, the turn read-out and "the probe" with no definitions. A six-line "Terms" paragraph after "In short" would make the page stand alone. "D1" and "D2" as rule names collide with the rest.
- The "What holds" table is the clearest thing on the page. Its M4d row should say "in ten fresh null hosts (a screen)"; "other graphs" generalises past the sample.

The script reads the right fields. I checked every key it uses against the records by inspection (no shell in this session, so I could not run the test). Nothing the synthesis quotes from the summary is wrong. Three small points:

- The pilot check uses a default of True when a check dict lacks a `passes` key. All six have the key today, but a renamed key would pass silently. Require it.
- The census block captures only c2, c3 and c5, so "passed every check" traces to the results file, not the summary. Fine, but say so in "Where the numbers come from".
- The per-stage hours sum to 56.35 while the total rounds the unrounded seconds to 56.4. A reader adding the table will notice. The genomes-per-arm figure is hard-coded rather than read from a record.