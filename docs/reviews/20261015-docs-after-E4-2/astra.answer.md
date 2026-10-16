**fix first**

1. **[ROADMAP.md:19](D:/Claude/random/wormWars/ROADMAP.md:19) — “None of the later biology questions … has started” is too broad.**  
   That list includes “A family of named nulls” at line 607. Experiment 03 already built and validated five named ensembles: [PREREGISTRATION.md:54](D:/Claude/random/wormWars/experiments/03-generation0/PREREGISTRATION.md:54) lists them and their preserved properties; `wormwars/exp03/samplers.py` implements them. This does not establish that every requested detail about the somatic–pharyngeal bridge is documented, but “none … has started” is incorrect.  
   **Fix:** explicitly name the four outstanding directions: topology × optimizer × normalisation, activity-anchored fitness, neuromodulation, and temporal versus stereo sensing. Describe any remaining null-family work separately.

2. **[README.md:234](D:/Claude/random/wormWars/README.md:234), [DECISIONS.md:8738](D:/Claude/random/wormWars/DECISIONS.md:8738) — The E2 stale-next-step finding remains unfixed, despite D283 claiming otherwise.**  
   README still says the task “is diagnosed next”; D283 says the E2 section no longer says “next” for completed work. Adding “E2d, above in the table” does not correct the tense. [E2d’s README:3](D:/Claude/random/wormWars/experiments/E2d-taskn-diagnosis/README.md:3) records completion and publication on September 30.  
   **Fix:** write “the task itself was subsequently diagnosed in E2d,” linking its README. Append a short correction to D283’s premature claim.

The other requested corrections check out against the files: E4’s controls and question 2, survey uncertainty, the dated 03m annotation, machine-catch wording and trail summary, publication-branch distinction, AGENTS’ quoted correction, and E3b-1’s narrowed question. The compute reconciliation also matches D275 and `summary.json`.

I inspected both diffs and the local review log. I found no further factual errors in the combined changes checked. No simulations were rerun; GitHub receipt times were not independently verified.