This is the last step of the memory brainstorm: a review of the roadmap Claude wrote from it,
`docs/memory/MEMORY-ROADMAP.md` (draft 1). It is a review, not a brainstorm.

Since your round-3 answers (archived in `docs/reviews/20261020-memory-select/`), Claude ran one more batch to check both
crazy ideas and Astra's join: `scripts/memory_spikes/batch8.py`, output `runs/memory-spikes/batch8.json` (512 genomes,
seed 7500, follow 300; N2, SH-2010000, SH-class-2030000). Claude also regenerated `runs/memory-spikes/check_structure.txt`
from the current script (Astra noticed the saved output lacked the extrapolation), and accepted Fable's substeps
correction (T1 runs 32 substeps, so batch 1 compared 16 with the baseline).

Please check:
1. **Every factual claim in the roadmap against the files.** Quote any claim that a file does not support, with the
   file. In particular check the batch 8 reading: the "saddle between two stable states" interpretation, "every N2
   genome whose difference stays at full size to tick 300 is one of these", and the eigenvector localisation. Read
   batch8.py's definitions (settled, oscillating, the Jacobians) and say whether they support the words used.
2. **Fairness.** Does the roadmap represent your round-3 input fairly, including what you said against Claude's
   reading? Is anything you proposed missing that should be there, or anything attributed to you that you did not say?
3. **The plan.** Is the order right? Are the decision points the right ones? Is anything in M1-M4 that should be
   pre-registered, or anything in M5 that should not wait? Is any step too expensive for what it decides?
4. **A verdict:** "agree" (push it as the roadmap, perhaps with small fixes you list), or "revise" (with what must
   change first).

Read the repository as needed. Do not edit files or run anything.
