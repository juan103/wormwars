# M6, behaviour: the options note (round 1)

With M5 postponed (D373), the owner agreed to design M6's behaviour question next, first as an options note with
rough costs and the likely size of each answer, before any plan (D374). The note is `docs/memory/M6-OPTIONS.md`
(draft 1). Context: `docs/memory/SYNTHESIS.md` (draft 4), `docs/memory/MEMORY-ROADMAP.md` (M6),
`experiments/03h-history-use/` (README, RESULTS, DESIGN), `experiments/02-screening/` (README, RESULTS; D038 on the
pilot champion and the history ablation). 02's saved genomes are local and untracked (`runs/exp02-screening/*.npz`);
the note lists what exists.

Read-only. Please:
1. Check the facts and the rough costs (T1 at about 0.14 s per genome-world on the CPU; the classifier at about 1.4 s
   per genome; the counts of 02's T1 champions).
2. Say whether the likely sizes are fair, and whether any option is mis-sized or missing (including a cheaper or more
   decisive one).
3. For option 0, what must be fixed before it runs so that its answer can be read honestly, and any reason it cannot
   work (for example the probe or classifier on champions evolved under other food mappings, or the generation-0
   snapshot being a selected best-of-generation rather than a random genome).
4. Your recommendation to the owner.

Keep it short: this goes to the owner as a decision, not a plan.
