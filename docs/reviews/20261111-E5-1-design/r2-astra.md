**Verdict: fix then proceed.**

The core comparison is acceptable. Draft 2 is not ready to freeze: A0’s interpretation overclaims, P’s construction misdescribes the existing implementation, failure handling can select surviving graphs by behavior, and the statistical calibration remains incomplete.

For round-1 status, I use **Astra’s original numbering**. “Met” means the design now specifies the required work; it does not mean the unwritten implementation has passed its checks.

| Round-1 item | Status | Assessment |
|---|---|---|
| **1. B’s starting genomes** | **Met** | B now starts from the E5-0-tested C champions, with checkpoint indices and hashes to be bound. I reconfirmed that C and F differ in 13/16 runs. |
| **2. Evolutionary pilot** | **Met** | “No evolution on N2 in the pilot” removes the exploratory O1 comparison. The two evolved pilot graphs are now for engineering and feasibility, not an estimate of endpoint graph variance. See item 15 for the remaining selection gate problem. |
| **3. Gains rationale** | **Met** | The engineering claim is withdrawn; fixed gains are now an explicit scientific choice. The N2 provenance and uncertain direction of the effect are stated. |
| **4. Fitness, validation and G0** | **Met** | The weighted objective is correct; validation is 32 worlds per training setting with matching aggregation; G0 is the training winner evaluated on fresh worlds. |
| **5. Positive-but-small outcome** | **Met** | The six labels implement the stated symmetric rules. The distinction between an estimated effect ≥δ and evidence that the true effect exceeds δ is explicit. |
| **6. Bootstrap calibration** | **Partly met** | The one-level implementation is correct. But “normal scores” with a common within-run SD does not cover the requested unequal arm variances, weak/zero graph effects, or failed/low-performing mixtures. The Welch comparison is still only promised. |
| **7. CUDA and composition checks** | **Partly met** | Four runs per batch removes the principal treatment/composition confound. However, the explicit gate compares training with “1 strain × 1 024,” while validation is 4×256 and the suite specifies 512 worlds per setting. Those actual execution shapes still need binding and coverage. |
| **8. Behavioral changes and equivalence** | **Met** | Current versus revised Task H, mixed versus serial execution, frequent captures, skipped sequence entries and the correct cache key are now specified. |
| **9. Compatibility and publication guards** | **Met** | Both `cat` and `assign`, value comparisons, equal-sized differently wired graphs, publication prohibition and sabotage checks are included. |
| **10. Failure handling and qualification** | **Partly met** | Qualification over all 17 settings is correctly withdrawn and formal references are included. But “a second failure removes the batch’s unit” permits outcome-dependent exclusions. The new selection gate also remains inadequate. |
| **11. Complete cost ledger** | **Partly met** | Training arithmetic and mutant counts are corrected. Lesion scope remains unspecified, the evaluation allowance is inconsistent with suite-wide lesions, and the reduced-budget design conflicts with the completeness threshold. |

Against **Fable’s numbering**: M1 met as a design commitment; M2 partly met because P needs correction; M3 partly met because the anchor’s interpretation is wrong; M4 met; M5 partly met because the selection gate and execution-world specification remain unresolved; M6 met for the estimand, symmetry and count rationale, with interval calibration still pending.

The remaining must-fixes are:

12. **A0 is a useful comparator, but it cannot support the proposed interference sentence.**

    > “If neither G-N2 nor G-SHr exceeds A0, ‘the host’s wiring adds nothing measurable … and O1 compares how much each host interferes.’”

    This does not follow. Failure to demonstrate superiority is not evidence of zero contribution or interference. Even genuinely better performance by A0 would compare different starting protocols and search spaces: a designed carrier versus random host backgrounds. An evolved host could contribute positively to its own co-adapted module while the independently optimized carrier performs better overall.

    Keep A0, but state exactly what “exceeds” means and report arm–A0 estimates with uncertainty. A defensible companion sentence is: **“Neither evolved-host arm demonstrated higher performance than the evolved carrier.”** Establish interference within a particular evolved organism through its intact-versus-lesioned contrast, with uncertainty.

    Freeze A0’s construction explicitly: 32 identical carrier copies or another declared population; both chemical host weights **and gap conductances** zero and pinned; module mutation at 0.25×; host biases and τ at the stated scale. The existing `carrier_genome` supplies the intended deterministic starting carrier. Specify the same chemical-and-gap treatment for the lesion.

13. **P is not implemented as three separately rebuilt graphs in 03r.**

    > “P’s graphs (03r’s `exp03.py` builds N2perm4 to 6)”  
    > “N2perm4 to 6 rebuilt … checked against both manifests”

    Those statements are wrong. [`_load_graph`](/D:/Claude/random/wormWars/scripts/exp03.py:400) returns unchanged N2 for every N2perm name. [`brain_config_for_graph`](/D:/Claude/random/wormWars/wormwars/exp02/grid.py:177) sets chemical and gap initialization magnitudes to `permuted`, with permutation seeds 4, 5 and 6. Neither graph manifest contains those names.

    Construct P by applying those initialization settings to the **ungrafted host**, then embedding the frozen L1 initialization. Applying permutation over the grafted edge list would also permute module magnitudes and define a different treatment.

    Bind the permutation configurations and resulting host magnitude/permutation hashes separately from graph hashes. Add a check that P differs from N2 in host magnitude placement while preserving its edges and L1 initialization. Describe P as sensitivity to **initial weight placement**; evolution subsequently changes those weights.

14. **Failure handling must distinguish external interruptions from behavior-dependent failures.**

    > “A second failure removes the batch’s unit”  
    > “O1 is read only if at least 28 … runs and 18 … graphs … complete.”

    Sequence exhaustion is directly related to captures and skipped respawn candidates. Non-finite dynamics can depend on graph and evolved parameters. Dropping those units can bias the ensemble comparison; a minimum sample count does not repair that.

    Default to withholding confirmatory O1 after an unresolved behavior-dependent or numerical failure. Diagnose it, document an amendment, and specify which affected work must be repeated. External interruptions can have a separate resume/retry policy preserving seed, code and composition.

    Also resolve this direct contradiction:

    > “SH-route goes to 16 graphs”

    That budget branch can never meet §6’s requirement of 18 completed graphs. Freeze a coherent admission list, completeness rule and statistical calculation for each permitted design. A cap stopping a batch also needs explicit treatment: capture-dependent runtime makes completion potentially informative.

15. **The selection-signal gate tests the best of 32 without accounting for that search, and does not require selectable variation.**

    > “at least one strain’s … contrast has a 90% interval above 0”

    With 32 independent null contrasts, each having a 5% chance of a positive lower bound, the chance of finding at least one is **80.6%**. Requiring this in three of four populations still passes **82.9%** under that illustrative independence model. Actual contrasts share worlds and will be correlated, so these are not predictions for your pilot; they demonstrate why the nominal intervals do not calibrate this gate.

    A simple repair is to choose the G0 winner on the actual eight training worlds, then test that preselected genome on independent diagnostic worlds. Alternatively, calibrate a population-level maximum statistic.

    The recorded fitness spread also needs an operational criterion. All strains could have strong scent dependence yet tie on selection fitness. Conversely, failure to detect a contrast does not establish the sentence “selection would have no scent-dependent signal to act on.”

    **On leakage:** there is no longer an evolutionary O1 pilot. Nevertheless, §7.4–5 produces N2 and null generation-0 measurements resembling O0. “Not read beside N2” does not make those observations unavailable. Explicitly prohibit comparative performance from changing initialization, gains, mutation scales, settings or stopping rules; departures require disclosure as exploratory redesign.

16. **Finish interval calibration before freezing the design, and update power for the interval actually selected.**

    > “coverage nearer 90% over the whole grid”

    This is not a complete selection criterion. Define whether this means average deviation, worst-case coverage, or another fixed criterion, and account for Monte Carlo uncertainty.

    The current simulation omits important scenarios requested in round 1:

    - different within-run variances for N2 and SH-route;
    - zero or weak between-graph variation;
    - skewed or floor-heavy scores and low-performing run mixtures;
    - the smaller sample sizes permitted by failure or budget rules.

    I ran a separate, unsaved Welch calculation with 20,000 simulations per displayed normal scenario. Coverage was **89.67–90.31%**. At run SD = graph SD = 0.3, the null received the equivalence label **69.22%**, versus the committed bootstrap’s **72.10%**. This supports doing the Welch check; it also shows why changing the interval requires replacing the power table.

    Use independent N2 observations and graph means in the Welch calculation. Do not add the within-graph variance again.

17. **Bind world-generation seeds and pilot schedules, not only world-id blocks.**

    > “training from each run’s seed”  
    > “paired across hunters”  
    > “A test checks that the blocks are disjoint…”

    The evolutionary run seed selects training IDs. Actual worlds depend on a separate seed: [`world_seed`](/D:/Claude/random/wormWars/wormwars/world.py:167) hashes both the world-generation seed and world ID. Draft 2 never fixes that common world-generation seed. Different per-run world seeds would defeat evaluation pairing even with identical IDs.

    The listed numerical blocks are mutually disjoint. However, pilot **evolutionary training and validation** have no separate allocations. Different scheduling seeds do not guarantee different worlds: using the existing scheduling algorithm, formal seed 1,510,000 over 500 generations and pilot seed 1,518,000 over 100 generations share **five training IDs** in the proposed pool.

    Freeze the complete mapping of phase, world seed, IDs and settings, including probes, lesions, pilot training and pilot validation. Explicitly identify any intentional reuse. I found no implemented E5-1 block-disjointness test; the present-tense claim should describe planned work.

18. **Complete the composition gate at the execution shapes that select and evaluate C.**

    > “the evaluation composition (1 strain × 1 024)”

    Specify the actual suite chunking, then test it. Include four-strain validation on 256 worlds, the suite’s per-setting shape, mixed-slot ordering and chunking invariance at the declared tolerances.

    Also test **weighted checkpoint selection** specifically. Existing [`evolve_batch`](/D:/Claude/random/wormWars/wormwars/e04a/evolve.py) computes validation with `v.score[i].mean()`. The new adapter must change that aggregation as well as training fitness, while preserving raw capture records. Otherwise C is selected under the old weighting.

19. **Size lesions explicitly and repair the cost ledger before requesting a cap.**

    > “lesions, bridges, O0 populations, references (about 0.8 M)”

    If “the host-wiring lesion on every C” means the suite, lesions alone cost **1,288,192 episodes**. Including the other stated evaluations gives approximately:

    | Evaluation | Episodes |
    |---|---:|
    | C and G0 suites | 2,576,384 |
    | Five probes, four settings, C and G0 | 3,031,040 |
    | Every C lesioned on the suite | 1,288,192 |
    | Two bridges on C and G0 | 303,104 |
    | O0 populations, test arms only | 229,376 |
    | Five reference hunters | 43,520 |
    | B’s two intermediate Task N readings | 16,384 |
    | **Total** | **7,488,000** |

    That is **4.47–6.80 hours** at 465–306 episodes/s, before Task H overhead. If lesions cover only four settings, the total becomes about **6.50 million**, close to the quoted allowance—but that restriction must be stated, and it narrows the lesion interpretation. The reference count also needs an exact controller list.

    The 393,216 mutant episodes are correct, but parent evaluations and diagnostic instrumentation need entries. Finally, “35–50 GPU-hours” excludes the stated 15% reserve: the corresponding request is roughly **40–58 hours**, even before correcting omissions. Keep the bench-dependent forecast clearly separate from measured rates.

The following should also be corrected:

20. **Keep 500 generations, but describe the selected object accurately.**

    I accept 500 as a fixed-budget choice. The E4s-1 curve supports its cost rationale, not convergence on Task H or fairness in asymptotic performance; draft 2 acknowledges that limitation.

    > “ended with a higher … score”

    C is the best validation checkpoint available within the budget, not necessarily the final population’s winner. Say **“the validation-selected hunters obtained within the 500-generation budget.”** Freeze generation indexing: existing `evolve_batch(generations=500)` evaluates generations 0–499.

    Likewise, “frozen L1 graft” should mean frozen topology and initialization, since its parameters mutate.

21. **Tighten the companion sentences without changing the six-label logic.**

    > “No difference … was found”

    The equivalence outcome establishes more than non-detection: its interval excludes effects of magnitude δ in either direction. Say that directly.

    The priority of a detected small difference over equivalence is acceptable, but report both properties when both hold. Also replace “about half … at any count” with the more precise statement that requiring the estimate to exceed the true boundary limits power to approximately one half under the symmetric model; the significance requirement can reduce it further.

22. **Reject invalid statistical inputs and define the latent-SD calculation.**

    [`stats.label`](/D:/Claude/random/wormWars/wormwars/e5/stats.py:25) currently returns `"inconclusive"` for three NaNs. Invalid data must produce an error, not a scientific outcome. Validate finite scores, interval bounds, positive δ and admissible sample shapes.

    Specify how the latent graph variance is estimated, including subtraction of within-graph sampling variance, truncation at zero, and reporting Δ/SD when the estimated SD is zero.

23. **Correct two remaining provenance statements.**

    > “Every E4s-1 number below is C’s.”

    False. The quoted 0.11 after module silencing describes **F**, according to E4s-1’s `RESULTS.md:138`; the training curve describes generation-specific training winners. Restrict the C statement to the E5-0 reused-hunter numbers.

    D389 is still absent from `DECISIONS.md`, which ends at D388. I cannot verify the cited authorization from that file.

Finally, these are the numerical and execution checks I completed:

24. **The principal cited numerical results reproduce.**

    | Source checked | Result |
    |---|---|
    | E5-0 `reading.json`, independently aggregated | E4s-1 **2.85114**, SD **0.22958**, range **2.60239–3.40898**; L1 **3.00690**; E2d **0.75577**, SD **0.21886**; generation 0 **0.11189**. |
    | `design-power.json` | All four displayed simulation rows round correctly. Null-equivalence rates for the cited alternatives are **0.381, 0.642, 0.721, 0.7805**. Overall coverage **0.8605–0.8985**; null “ahead” frequency **0.1015–0.1375**. |
    | 03r `supplement.json` | N2 turn gain **2.08287**; median of 256 SH-route gains **2.95043**; N2perm4–6 **3.06726, 2.91835, 3.04037**. The quoted gain comparison is correct. |
    | E4s-1 `eval-training.json`, 16 M runs | Means **2.22412 → 6.86035 → 7.07861** at generations 0, 500, 999; **95.50%** of the measured climb by 500. |
    | Ten E4s-1 training records and E1 `freeze.json` | **4,876.28–5,150.75 s**, mean **4,984.21 s**. E1 supports the quoted four-run rollout rate. The inferred **3.35 s/generation** remains an extrapolation. |
    | Cost arithmetic | 37 batches, 148 runs; training **18,944,000 episodes**. Training table arithmetic is consistent with the assumed rate. Evaluation scope is the unresolved part. |

25. **Statistics implementation checks passed, with limited scope.**

    I ran all **13 tests** in `tests/test_e5_stats.py`; they passed. I inspected the first-failure and bootstrap-sabotage logs. The bootstrap genuinely resamples N2 runs and graph means independently at one level.

    I did not rerun the full bootstrap simulation grid, rebuild anatomical graphs, run Task H or use CUDA. No repository files were changed.