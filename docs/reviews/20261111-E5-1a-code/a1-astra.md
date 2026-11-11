**Verdict: amend and rerun, after tightening the check.**

The diagnosis is supported: the recorded numbers match, and both float32 implementations deviate similarly from float64. This supports numerical sensitivity rather than a CUDA-specific defect. Call float64 a **higher-precision reference**, though; “near-exact” has not been established.

Before rerunning:

- **Judge each genome separately within the existing batches.** [The implementation](/D:/Claude/random/wormWars/scripts/e5_1a.py:777) pools maxima across strains. One sensitive champion gives every other champion in the training batch a roughly **0.219** allowance. Compute per-strain errors over ticks, worlds and neurons, preserving the actual batch shapes.
- **Factor 1.5 and additive floor 1e-4 are acceptable engineering choices**, openly selected after failure—not demonstrated accuracy bounds. “No further from the reference” is incorrect wording: the rule permits 50% more error plus the floor. Keep the original direct CPU–CUDA ≤1e-4 check for generation-0 genomes, which already passed.
- **Strengthen the sabotage.** The supplied log demonstrates failure only at the 10-tick smoke shape. Add a reproducible 300-tick sabotage at a production shape, including corruption of a stable genome sharing a batch with a sensitive champion.
- **Correct the reporting:** H1-bite pursuit traces agree in **254/256**, not 255/256; H2 agrees in 256/256. Also disclose the pursuit/mixed half-width of **0.03030**, slightly above the precision target. Its equivalence interval still passes the registered ±0.10 rule.

Keep the failed attempt, commit and push the reviewed amendment and code, then rerun **steps 1–3**, followed by the bench and owner’s cap. That scope is appropriate. The unchanged score checks remain the evidence for task-level agreement; the revised state check is a numerical regression guard.