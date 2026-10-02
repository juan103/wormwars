**Verdict: revise.** The remaining problems are specific and repairable. I checked `roadmap` at `af9b768`, read both reviews and D157, reproduced the geometry JSON without writing it, and ran in-memory CPU checks using the actual `Brain.step` and cached connectome. No files changed.

The v2 change-map items are resolved at design level **except**:

- **Memory classification and hold test:** still defective, as explained below.
- **Startup coverage:** measuring after 50 ticks of preconditioning removes the startup transient; it does not test it.
- **Generation-zero reading:** “not small” remains undefined, and the census’s 16-world scoring does not establish the defined “working selector” criterion, which also requires test bounds and clamp assays.
- **Budget closure and statistical details:** arithmetic is fixed; the approved cap, complete reduction rules and handling of unequal replicate counts remain for pre-registration.

The other items—parameter ownership/count, spawn restriction, dtypes, latency, absolute component limits, contribution definition, circle baseline, Stage 3 initialization/fitness, B-task scale/capacity wording, clamp engine change, numbered gates and stopping consequences, and L1-switch’s reference status—are addressed in substance.

Concrete findings:

1. **The relay switches, but the quoted number uses the wrong numerical update.** From settled q, a one-tick pulse gives **q = ∓0.219682**, not ∓0.43, in `Brain.step`. Two- and four-tick pulses also switch; the five-tick start cue reaches **+4.93717**, and the state subsequently holds near ±1.915. The quoted −0.432 matches explicit Euler with the newly updated relay, whereas the engine uses simultaneous, semi-implicit updates. Correct the number and commit a check against the actual engine. [Latch specification](D:/Claude/random/wormWars/docs/E3/DESIGN.md:120)

2. **The new no-latch construction is wrong.** Clamping q to zero retains comparator biases of −1.914. Its per-module \(K_D\) is **2.63–2.97**, versus **31.60–35.62** for an active L1. This is a substantial gain reduction, confounding the Stage 1 comparison. For “both modules always on,” also restore all four comparator biases to zero; retain q-only clamping as a separately named ablation if useful. [Stage 1 control](D:/Claude/random/wormWars/docs/E3/DESIGN.md:190)

3. **Thirteen parameters is correct; the initialization is implementable.** It comprises seven weights, five biases and one time constant. Explicitly draw weights from U[−3,3], biases from U[−2,2], and τ log-uniformly from [0.5,20], changing only the selector. `Genome.random` does **not** implement that weight/bias distribution. Also, 0.25× Gaussian mutation did not mathematically prohibit sign changes; describe E4s-1’s observed failure to cross zero accurately. [Existing initializer](D:/Claude/random/wormWars/wormwars/brain.py:214)

4. **“No memory” can contain a functioning bistable latch.** A concrete allowed selector has \(w_{qq}=1/\tanh(1)\), \(b_q=0\), gate weights ±2.5 and comparator biases \(-2.5\tanh(1)\). Its stable states are q=±1. CPU checks give active \(K_D=31.60–35.62\), inactive approximately 0.062–0.070, yet it fails \(|\tanh q|\ge0.9\) and therefore falls into “no memory.” Separate **dynamical class** from **functional assay success**. Clamp assays alone also do not demonstrate trace retention: release the clamp and test both visit-set states over a defined delay. Specify when withholding begins; suppressing the first visit’s delayed signal can prevent switching altogether. [Classification](D:/Claude/random/wormWars/docs/E3/DESIGN.md:224)

5. **The budget arithmetic now checks out.** Measured batches span **1.35452–1.43076 h**. The stated scaling gives Stage 2 **1.625–1.717 h**, Stage 3 **2.709–2.862 h**, B-task **4.334–4.578 h**, and total **12.894–13.474 h**, including the fixed allowances. Thus “about 13.3 h” is reasonable as a projection. One correction: E4s-1 had **306 neurons**, versus E3’s 313. Actual throughput still needs the promised projection.

6. **The geometry output reproduces, but “0.19% start blind” is not what the script measures.** It counts head-to-source axis distances above 18; it never samples bilateral noses or grid interpolation. Using the real field sampler, a head-axis distance of **18.4** can produce nonzero readings, while **17.9** can produce two zeros, depending on heading and grid alignment. The new 16-cell restriction supplies adequate margin, so the geometry remedy stands. Relabel the old statistic or measure actual sensory blindness. [Counting code](D:/Claude/random/wormWars/scripts/e3_geometry_check.py:60)

The pre-registration must additionally pin these outcome-changing choices:

- Exact control genomes; B-shared wiring and thresholds; B-task’s mutable parameters and initialization; interpretation of reversed selector sign mappings and non-engineered equilibrium magnitudes.
- Hold/reset timing, both-state success criteria, transient measurement windows, and the slow-trace delay—including episodes with no completed legs.
- Champion selection, random-sampling selection/validation budget, census qualification procedure and the numerical “not small” threshold.
- Confidence levels, gate denominators, geometric-maximum formula, blind-policy settings, world-block spans and pairing. Give S2-b ordered, non-overlapping rules, including **“random sampling better.”**
- Approved cap, projection/admission rules, predetermined retained runs and stopping behavior. The listed reductions do **not** reach the stated minimum: they still retain B-task and four Stage 3 runs. Reducing random sampling to four also requires defining which GA runs enter the paired comparison.