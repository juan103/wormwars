# An outside review of the repository (2026-09-28)

**Source:** a separate Claude Opus 5.5 instance, asked by the owner for its opinion of the repository.
The owner pasted its answer into the working session on 2026-09-28; it is archived here verbatim
(AGENTS.md rule 10), because 03m's plan and D106's CI work cite it. The owner added, in the same
message, that they agreed the project generates too much documentation, and that they would rather
keep the process and watch it fail, if it does, than trim it on a suspicion.

---

Short version: it's one of the most scrupulously honest small research repos I've seen, and the core code is careful. But the process has grown much heavier than the science it's producing, and its most interesting result may be undersold.
A disclosure first: the README credits Claude Opus 5.5, the model you're talking to, with writing the code and running the experiments. I have no memory of that work, but I could share its blind spots, so weigh this review accordingly. I cloned the repo, read the core code and the write-ups, and re-analysed some of the committed data.
What's good. The biggest bug, chemical synapses running backwards through all of experiment 01, is disclosed at the top of the README with a before/after table. Every write-up says what it does not show, and there's a log of who caught which error. The core code is careful:

* The integrator is semi-implicit where gap junctions would make plain Euler blow up.
* Synapse direction is documented and pinned by tests.
* The connectome is downloaded and hash-checked rather than redistributed, since its licence doesn't allow redistribution.

The scientific instincts are good too. The authors switched to comparing unevolved (generation-0) brains once it was clear the evolution budget couldn't show much else. They built increasingly strict null graphs, and ran a full replication when a single graph decided a verdict.
The main problem is ceremony. In twelve days the repo accumulated 206 commits, 101 numbered decisions, about 55 rounds of AI review, and roughly 200,000 words of Markdown, against about 22,000 lines of Python. E1, a positive control that ran for six minutes, went through six pre-registration versions and five review rounds. A whole track went into getting bit-identical GPU results regardless of batch size. That helps auditing, but it isn't what makes a rank test over 128 graphs trustworthy.
The result is nearly unreadable for outsiders, with labels like D-numbers, T0/T1, P1–P4 and M0/R1/R2 everywhere. The AI review loop is clearly good at internal consistency; it caught the reversed synapses. But it can't replace one human C. elegans or network-science expert asking whether this interface and game probe the wiring meaningfully at all. I'd scale the rigour to the stakes: full pre-registration for confirmatory claims, light process for controls and engineering.
The science so far is modest, and the authors say so. Each comparison tests the wiring plus a hand-picked sensor/motor interface on one game. The evolution budget is tiny: population 32, 25–40 generations, 5,404 parameters. The one replicated positive is P4, "history dependence" in random, unevolved brains. I'd avoid the word "memory" there. The null graphs already score 0.75–0.84 on the same ratio, because with neuron time constants of 0.5–20 ticks nothing tracks a 10-tick ramp closely. N2's 0.93 is about 2–2.5 standard deviations above each null ensemble's mean. That's consistent and replicated, but it means "more persistent", not a new capacity.
I think the result is stronger than the write-up suggests. From the committed supplement files:

* Within every ensemble, in both the original run and the replication, graphs whose random brains respond more strongly to food have lower P4 (Spearman −0.27 to −0.60).
* N2 is by far the strongest responder: about 5.5× the null median, and 1.5–1.8× the most responsive of the 640–768 null graphs.
* Yet N2 also has the highest P4. Extrapolating each ensemble's trend to N2's response level puts N2 roughly 4–7 SDs above it. That's an extrapolation, so treat it loosely, but all ten ensemble runs agree.

So the unusual thing looks like a combination the nulls never produce: a strong but slow, indirect route from the food sensors to the turn output. That fits the earlier finding (02b) that AIZ and RIA are N2's critical neurons. The textbook AWC→AIY/AIZ→RIA→SMD/RMD head-steering route ends on exactly the SMD/RMD neurons used as the turn output.
Cheap checks before a big pre-registered mechanism study:

1. Silence RIA and AIZ in unevolved N2 brains and see whether both response size and P4 fall into the null range.
2. Extend the post-ramp window to a few hundred ticks, or linearise around the fixed point, to tell slow relaxation apart from multistability.
3. Build a full ensemble of N2's own wiring with shuffled weights, about four GPU-hours at the measured speed.

The six such graphs already in the repo hint at a split. In five of six, the big food response collapses to about the null median while P4 stays at 0.86–0.92. That suggests the wiring drives the persistence and weight placement drives the response size. One lead I checked and would drop: the nulls don't preserve N2's 38 self-connections, but P4 doesn't track their number within any ensemble.
Practical gaps. There's no CI and no packaging, and 40 of the 52 test files need the non-redistributable connectome, so outsiders can't easily verify the "577 passing" claims. A GitHub Action that fetches and hash-checks the data and runs the CPU tests would fix that.
Bottom line: worth following. For now it's more valuable as a transparent record of AI-run research, plus a reusable set of null graphs, than as biology. If you're involved with it, I can turn the response-size-vs-P4 check into a small script that runs on the committed JSON files.

---

**Checked against the committed data (2026-09-28/29, 03m `tradeoff.json`):** the within-ensemble
Spearman range (−0.27 to −0.60) and the 4-7 SD extrapolation reproduce (4.3-6.7). Two statements do
not: N2's response is 4.7-7.1 times the null median and 1.55-2.7 times the most responsive graph; and
N2's P4 is above every graph but one in each instance, not the highest (Astra, Fable, 03m review v1).
