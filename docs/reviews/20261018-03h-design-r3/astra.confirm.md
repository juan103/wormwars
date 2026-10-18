**revise.** B’s blocking issue is resolved; the pilot power calculation still needs correction.

Checked `roadmap` HEAD `6ed8741`, both round-3 reviews, D324, and the development record. No scripts or tests were executed; no files changed.

Round-3 findings, using each reviewer’s numbering:

| Reviewer | Resolved | Partly | Not resolved |
|---|---|---|---|
| Astra | 1, 3, 4, 5 | 2 (power), 6 (pilot rules), 7 (inherited audit) | None |
| Fable | 1–4, 6–12 | 5 (detectability) | None |

**B’s conditional inference (§6) is acceptable as written.** Frozen selections, shared test-world resampling, and graph resampling for ensemble means support the stated conditional intervals. Testing only the selected deciles is sufficient. This does not estimate uncertainty from repeating genome draws or selection.

**Development record:** [t1_generation0.py](/D:/Claude/random/wormWars/experiments/03h-history-use/development-records/t1_generation0.py:26) uses the correct crossed-ANOVA sums, degrees of freedom, and reliability formula. The committed [output](/D:/Claude/random/wormWars/experiments/03h-history-use/development-records/t1-generation0.json:214) supports the revised figures: components 0.06712/0.04860/0.01941; reliability 0.98203 at 16 worlds and 0.96471 at eight; throughput 172.91/s. The five-cell workload matches the original driver. This is a static check, not independent regeneration of the output.

Remaining findings:

1. **§7.7 — substantive error in the new power rule.** Pooling graph and world-bootstrap variation into `s_D`, then dividing by √64, incorrectly shrinks uncertainty shared across graphs. For example, if \(D_g=\theta_g+z\), the ensemble-mean variance is \(\mathrm{Var}(\theta)/64+\mathrm{Var}(z)\), not \((\mathrm{Var}(\theta)+\mathrm{Var}(z))/64\). Use the projected ensemble-mean SE with shared-world covariance retained. The present rule can overstate power. [Design](/D:/Claude/random/wormWars/experiments/03h-history-use/DESIGN.md:300)

2. **§§7.7, 8 — unresolved contradiction.** §7 allows W = 32; §8 still says “W stays at 16.” State that budget cuts preserve the **pilot-selected W**. [Design](/D:/Claude/random/wormWars/experiments/03h-history-use/DESIGN.md:335)

3. **§3 — minor outstanding implementation requirement.** Explicitly require `replay_mode()` for the CUDA bitwise equivalence check; matching composition alone is insufficient under the repository’s reproducibility contract. [Design](/D:/Claude/random/wormWars/experiments/03h-history-use/DESIGN.md:117)