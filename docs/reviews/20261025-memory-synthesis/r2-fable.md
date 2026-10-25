**Verdict: fix then publish.** Every round-1 finding is fixed as described, and every number I re-traced matches its record. The script and its new test are right: the pilot summary's R5 block has no verdict key, the six others do, each arm record carries `n: 1024`, and the stage hours sum to the reported total. What remains is a handful of one-line slips, two of them introduced by the fixes. None needs another round.

## Fix before publishing

1. **The "Both" attribution for D357's rule is wrong, and the error is mine.** My round-1 answer asked for a "Both" line on "a null reads 'not demonstrated', not 'access'". The record says Astra: D357 lists it under Astra's catches, and in the direction review only Astra's answer makes the point (`docs/reviews/20261022-m3-m4-direction/r1.astra.md`, item 1). Fable's answer uses "access" only in the store-versus-access trace. Move it to Astra's line (`docs/memory/SYNTHESIS.md:287`).

2. **"One shared per pair" for T, P and R is not in any record.** The tables (`runs/memory-m4d/tables.txt:60`) give T–P 1, T–R 1, T–T+G 25 and R–Rr 1. There is no P–R count. D364 has the same wording, so the synthesis inherited it, but rule 5 still fails. Say "T shares one switch genome with P and one with R, as R does with Rr" (`SYNTHESIS.md:185`).

3. **"graphs selected for many such genomes have more than N2"** (`SYNTHESIS.md:22`). The selected graphs have 12 to 78; N2 has 15 and 13. One of the ten has fewer than both N2 panels. Section 2 gets this right; the summary bullet does not. Say "most have more" or give the range.

4. **The M4c provenance sentence overstates the check** (`SYNTHESIS.md:66`). "Checked afterwards against the committed code's record checks" reads as if the executed code was verified. M4C-RESULTS says the opposite: the record checks validate metadata and array alignment, "not a check that the executed code was the committed one" (Astra). Say that the records, not the code, were checked.

## Should fix

5. **"two panel-level tests read 'unresolved'"** (`SYNTHESIS.md:28`). M4a's reading is panel-level; M4b's is not, and its N2 contrast was clear. Say "the fixed readings of M4a and M4b are both 'unresolved'".

6. **The M4a smoke sentence is ambiguous** (`SYNTHESIS.md:65`). "Which took no result number from it" can be read as "the smoke's numbers were not read". They were: the redesign followed the smoke's 15 and 24 matched genomes and the doubled weight (D357). Say the results file takes no number from it.

7. **"its lower bound 0.0009"** for D − I (`SYNTHESIS.md:213`) is the envelope floor; the counted lower bound is 0.0013. Name it.

8. **"one horizon leaves 0.3% to 0.5% of genomes unresolved"** (`SYNTHESIS.md:233`) is M4d's figure. The census left 33 of 47,084. Say "in M4d's hosts".

9. **Two small arithmetic and definition snags.** "0.435 = 0.586 − 0.152" gives 0.434 at the printed precision; mark it rounded or print one more digit. The Terms section defines the share over eligible genomes, but the first number the reader meets, 0.436, is 03mc's all-genome share. One clause saying so would close the gap.

Nothing in the readings, the status table, the limits or the lessons is wrong. The arm letters, the two head cores, the restricted M4d exclusion, the class-level retention, the M4c limits and the corrected M4a example are all now as the records say.