**Verdict: bind.** I found no design change necessary to make E3f’s result interpretable. This approves the design; `scripts/e3f.py` is not present at `25eba77`, so its implementation remains to be checked.

**1. “E3d unchanged except §1” is sound, with horizon-specific text read correctly.**

There are several horizon-specific passages:

- **E3d §§1 and 3:** “the horizon” being unchanged from E3b-1 and “H = 2 400” are superseded for E3f’s experimental blocks.
- **E3d §5:** the historical tree scores remain historical measurements. The absolute thresholds remain **counts within the chosen horizon**, not rates to rescale. A pass establishes the declared separation within 1,800 ticks.
- **E3d §6:** discovery censoring and later-leg denominators must use 1,800. The shared runner already passes the actual configuration’s horizon into its measurements. [Measurement implementation](D:/Claude/random/wormWars/scripts/e3d.py:340)
- **E3d §7 and §11:** the pinned 2,400-tick equivalence runs and historical qualification results retain their original settings. E3f §3 explicitly preserves those references. [E3d equivalence specification](D:/Claude/random/wormWars/docs/E3/E3d-DESIGN.md:342)

I also checked the wall-follower qualification at 1,800 ticks using the existing ten qualification trees: both hands toured all ten, completing within 686–824 ticks. There is no shorter-horizon qualification problem there. [Qualification test](D:/Claude/random/wormWars/tests/test_e3d_wall_follower.py:148)

The truncation claim has a sound implementation basis: the maze dynamics do not read the stopping horizon. However, the cited test covers **the scripted follower, two CPU mazes and their 1,800-tick prefixes**. It passed here. Describe that scope accurately; it does not establish exact replay of formal GPU runs or every controller/composition. [Horizon test](D:/Claude/random/wormWars/tests/test_e3d_world.py:83), [stopping logic](D:/Claude/random/wormWars/wormwars/world.py:1285)

**2. Fixed k_r = 0, degenerate calibration and the stopping rule are acceptable.**

Calibration becomes a prespecified screening stage: require all six criteria, the oracle precondition and first-draw feasibility ≥0.5; then evaluate the untouched confirmation block. Calibration alone cannot produce the final pass. The existing choice function handles zero correctly. [E3f §1](D:/Claude/random/wormWars/docs/E3/E3f-DESIGN.md:48), [choice implementation](D:/Claude/random/wormWars/wormwars/e3/e3d_gate.py:70)

Fixing k_r for retained maze structure is defensible without claiming superiority. Keeping point-estimate acceptance while reporting intervals is also consistent with the inherited design. G2a’s interval crossing one-third limits generalisation; it does not change that acceptance rule.

The stopping rule is sufficiently explicit. A failure ends this horizon-adjustment sequence. Any owner-authorised subsequent design would be a new decision, preserving E3f’s verdict. [E3f §4](D:/Claude/random/wormWars/docs/E3/E3f-DESIGN.md:82)

**3. Carry these implementation and reporting requirements through.**

- **Complete the runner adaptation.** Preserve both design guards, both runner guards, E3f’s accounting/smoke/output paths, labels and reduction-3 IDs. The parent-design hash must remain outside the exempted binding values. Test the actual tree and island configurations at H = 1,800, successful selection of `0`, and refusal of confirmation after calibration failure. These follow the existing E3e requirements. [E3e §3](D:/Claude/random/wormWars/docs/E3/E3e-DESIGN.md:104), [guard implementation](D:/Claude/random/wormWars/scripts/e3d.py:153)

- **Keep calibration and confirmation reporting distinct.** `e3d_summary.py --exp E3f` would still summarise **calibration**, while taking its top-level verdict from `report.json`. If confirmation runs, use its statistics for the final gate, intervals and interpretation. The shared runner already reports confirmation correctly; the supplementary summary needs explicit scope or extension. [Calibration-only summary](D:/Claude/random/wormWars/scripts/e3d_summary.py:39), [confirmation report](D:/Claude/random/wormWars/scripts/e3d.py:668)

- **Retain E3e’s reporting corrections:** intervals even after calibration failure; exact counts for all champion blind arms; multi-strain B_max resolution; scent-split denominators; censored discovery, no-first-visit and later-leg records; and the trail-free follower beside the shared follower. Report interval crossings without overriding point-estimate decisions, and keep causal explanations tentative. These requirements are already covered by the inherited text and E3f’s additions. [E3e §1a](D:/Claude/random/wormWars/docs/E3/E3e-DESIGN.md:65), [results review](D:/Claude/random/wormWars/docs/reviews/20261011-E3e-results/astra.answer.md)

- **Qualify the truncation’s blind family.** E3d used reduction 1: three walk settings. E3f’s projection may admit all nine. Consequently, the exploratory B_max prediction covers E3d’s **played** family; additional settings could raise E3f’s maximum. This is a risk to the prediction, not a defect in fresh validation. [E3d’s admitted plan](D:/Claude/random/wormWars/experiments/E3-ab-organism/E3d/project.json)

I verified the parent-design hash and independently reproduced the quoted k_r = 0 estimates and intervals from all 30 hash-verified record files. All 128 proposed calibration constructions build; 98 are first-draw feasible. No GPU runs or file changes were made. Twenty-five selected tests passed; an inherited smoke-folder test was blocked by read-only permissions because it attempts to delete existing smoke output.