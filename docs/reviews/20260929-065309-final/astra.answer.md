The test logic is sound, but three small text fixes remain.

1. **Scope the deletion claim.** [README.md:36](/D:/Claude/random/wormWars/README.md:36) and [ROADMAP.md:54](/D:/Claude/random/wormWars/ROADMAP.md:54) should say **“no tested single or bilateral-pair deletion removed the elevated P4.”** The current wording generalises beyond the screen, which excluded read-out neurons and arbitrary neuron pairs. The other new summary claims are acceptable.

2. **Correct the attribution.** [RESULTS.md:260](/D:/Claude/random/wormWars/experiments/03m-p4-mechanism/RESULTS.md:260) attributes exact counts at every recorded tick to Fable. [Fable’s answer:42](/D:/Claude/random/wormWars/docs/reviews/20260929-064250-03m-results-confirm/fable.answer.md:42) explicitly calls the intermediate counts **upper bounds**, having traced only six graphs. Attribute an exhaustive check to whoever actually performed it, or preserve that qualification. The numerical corrections I directly checked and the other revised interpretations agree with the files; I did not independently recompute the pooled median or exhaustive per-tick ranks.

3. **Fix the test docstring.** [test_world.py:250](/D:/Claude/random/wormWars/tests/test_world.py:250) says one wey per swarm; the default is **20**. The composition is `(1 strain, 4 worlds per strain, 20 weys per world)`. Describe the CI failure’s numerical explanation as likely, rather than established.

The replacement correctly tests independence from batch-mates at fixed composition, consistent with D082/D091. It **does lose coverage of cross-composition agreement after 40 ticks**; the tick-zero test covers only initialisation. That narrowing is justified by the documented contract. No tests or simulations were executed.

**fix** — scope the deletion claims, correct the Fable attribution, and correct the test docstring.