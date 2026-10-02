# E3b: a bounded literature check on trails (2026-10-02)

Asked for by both reviewers of E3b's design v1 (`docs/reviews/20261002-E3b-design/`), under the project's
standard for literature (D143): citations made from memory were checked before the trail rules are fixed.
- **Who and how:** Claude, through web search, the Consensus index and direct fetches.
- **Not a deep research.** It covers what E3b-0's design depends on.
- **The verification level** is stated for every source:
  - **full text:** read;
  - **abstract:** only the abstract was available;
  - **snippet:** a search result only, not verified.

## The sources

| Source | Level | What it says that matters here |
|---|---|---|
| Panait & Luke, "Ant Foraging Revisited", Artificial Life IX, 2004 ([MIT Press](https://direct.mit.edu/books/oa-edited-volume/4339/chapter-standard/181736/Ant-Foraging-Revisited)) | abstract (the full text failed a certificate check and gave a 403) | See below. |
| Jackson, Holcombe & Ratnieks, "Trail geometry gives polarity to ant foraging networks", Nature 432, 2004 | abstract | See below. |
| Czaczkes et al., Insectes Sociaux, 2024 | abstract | *Lasius niger* "deposit up to 22 times more pheromone within 10 cm of a food source compared to when they are about to reach the nest". |
| Czaczkes et al., J. Exp. Biol., 2013 | abstract | On routes with two bifurcations, "errors on alternating routes decreased by 30% when trail pheromone was present". |
| Dodoková et al., Swarm Intelligence, 2024 | abstract | Compares three models: one pheromone both ways; one pheromone plus "an internal imperfect compass"; "two different pheromones, each used for one direction". |
| Jimenez-Romero et al., arXiv 2212.08484 (v2, 2023) | full text | See below. |
| Salman et al., "Automatic design of stigmergy-based behaviours for robot swarms", Communications Engineering, 2024 | abstract | Behaviours designed by optimisation for robots that lay and sense artificial pheromones were "as good as—and in some cases better than—those produced manually". |
| Wilensky's and StarLogo's ants model ([MIT](https://web.mit.edu/mitstep/starlogo/samples/ants.htm)) | the model's page | One pheromone, dropped while carrying food home, followed by its gradient. Ants go home by a "nest scent", not by a second trail. |
| Collins & Jefferson, AntFarm (1991-1992) | snippet | Evolved neural ants that produce pheromone. Not verified. |

**Panait & Luke 2004:**
- "solve ant foraging problems using two pheromones, one applied when searching for food and the other
  when returning food items to the nest";
- trails become efficient "in the presence of obstacles";
- "The algorithm replaces the blind addition of new amounts of pheromones with an adjustment mechanism that
  resembles dynamic programming."

**Jackson, Holcombe & Ratnieks 2004:**
- "previous research has found no evidence that ants can detect polarity from the pheromone trail alone";
- polarity comes from the geometry of bifurcations, best at about 60 degrees.

**Jimenez-Romero et al. 2023:**
- spiking networks are evolved for colony foraging;
- depositing is a network output: "There is no predefined behaviour that binds depositing pheromone to any
  action or sensor";
- the environment is based on Wilensky's 1997 model;
- the with- and without-pheromone comparison is "two distinct simulation runs".

## What this changes in E3b's design

1. **Two trails, one per direction, is established practice** (Panait & Luke; Dodoková et al.). E3b's
   trail table matches it. **Panait & Luke's update is not an additive deposit:** it is an adjustment
   "resembling dynamic programming". The abstract confirms Astra's v1 review on this point. E3b's
   time-decaying additive deposit is a different, simpler rule. It is not a replication of theirs.
2. **Polarity is a known problem.**
   - A pheromone trail alone carries no direction in real ants (Jackson et al.).
   - In E3b, direction must come from the engineered deposit rule. Both reviewers derived that a
     time-decaying deposit points the right way only if it decays faster than evaporation.
   - E3b-0 must measure the gradient's direction along routes, not assume it. **The Panait-Luke-style
     adjustment** is an alternative that gives a gradient by construction. It is more engineered, and a
     candidate if the additive rule fails.
3. **The deposit falling with distance from the source has a biological parallel** (Czaczkes et al.
   2024). E3b's frame is a game, so this is motivation, not a claim.
4. **Evolved neural agents using pheromone exist** (Jimenez-Romero et al.; AntFarm, unverified).
   - Their comparisons rest on single runs.
   - E3b differs: its deposit is engineered, its trail following is the seed's modules, and its question
     is whether tuning improves a hand-built design, with peer controls.
   - Nothing found replicates E3b's design. The search was bounded, so this is not a claim of novelty.
5. **Trails help on alternating, branching routes in real ants** (Czaczkes et al. 2013). This is
   motivation for E3b's tree mazes, not evidence about E3b.
