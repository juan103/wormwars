**Verdict: fix then publish.** One clause in the timing sentence is still wrong about the records. Every other round-2 fix checks out against the committed files. The fix is mechanical and needs no further review round.

**What I checked**

- **Power passage.** The nine δ = m scenarios in `coverage.json` have lower-above-margin rates from 0.0 to 0.045. "At most 4.5%" is right, the null-boundary reading is right, and the M5 option now defers to a power calculation. Correct.
- **T − P interval.** Width 0.0060 against D_TI 0.0059. "As wide as the whole transplant effect, reaching about half of it on either side" is accurate.
- **Timing ranges.** The log confirms the sixty fast panels run 790.1 to 1623.7 s and the ten slow ones are exactly the ten named, 1652.7 to 3179.1 s. SH-recip-2051000's I panel is 1814.8 s with no unresolved genomes. All correct.
- **Not-settled pattern.** P at 46 against T 76 and T+G 70, wording now says "exact weighted block". Correct.
- **Envelopes.** All six new lines in `tables.txt` match the text. The density option's wording survives a per-host check: R − I is positive in all ten hosts, and D − I is claimed only over every assignment, which is right since SH-route-2021001 has D − I = 0.
- **Nits.** "Consistent with" is in. The single-host form appears in both resolution passages. `verify_run` computes the hash at line 479 of `m4d.py` and `validate` matches it at line 512, as the text now says. The sha256sum line is gone. The compute-record note is in.
- **Rule 9.** `check_digest` exists, the test exercises it through `blocks_summary` with a byte-different but JSON-equal file, and the sabotage record has 24 entries with the digest line last.

**Must fix: the timing clause at line 58.** "Two of the three with the most unresolved genomes" overlooks SH-recip-2051000's R panel. Four panels have ten or more unresolved genomes:

| Panel | Unresolved | Seconds |
|---|---|---|
| SH-recip-2051000 P | 13 | 1653 |
| SH-mirror-2041001 T | 12 | 3179 |
| SH-mirror-2041001 T+G | 10 | 3125 |
| SH-recip-2051000 R | 10 | 1306 |

Say "two of the four panels with ten or more unresolved genomes (12 and 10; the other two, with 13 and 10, took 1653 and 1306 s)". The 1306 s panel is in the fast group with as many unresolved genomes as the 3125 s one, so it strengthens the hedge already in the sentence. Both round-2 reviews missed this, mine included.

**Not verified.** I have no shell in this session. I could not confirm that `m4d_tables.py` and `tests/test_memory_m4d.py` are staged for the commit alongside the results document, the arm records and the sabotage file. The git status snapshot I was given was truncated before those paths. Check that before committing, since the document now points readers at both.