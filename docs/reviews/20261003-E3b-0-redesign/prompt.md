You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You reviewed E3b-0 (this repository, WormWars, branch `roadmap`) twice: Stage B's outcome and Amendment 1 (`docs/reviews/20261002-E3b-0-stage-b/`, `docs/reviews/20261003-E3b-0-amendment-1/`). Read files to check claims; you cannot edit anything. Answer in English, concisely.

## What happened

Under Amendment 1, `stage-b2` (record `experiments/E3-ab-organism/E3b-0/stage-b2.json`) qualified no trail setting. Its shared rates reproduced Stage B's exactly, as the reuse guard required. The amendment's rule is now "a report and a redesign, with the owner informed".

Read `experiments/E3-ab-organism/E3b-0/INTERIM-REPORT.md`. It sets out:
- the evidence: `stage-b2.json` and three diagnoses in `development-records/`, the newest being `stage-b2-diagnosis.json` (persistent trails laid lightly);
- a hypothesis: a gain mismatch under linear sensing;
- the redesign options.

E3b-0 has used 0.90 of its 3 GPU-hours. Its cap is the owner's, and E3b-1's ceiling is about 30 GPU-hours.

## A claim to attack (Claude's)

"The trail constants alone cannot qualify. The follower (turn 32 × (L − R)) and the seeds' modules (K_D ≈ 35) have similar gains. A useful turn needs absolute nose differences of a few hundredths, which occur only where the overall level saturates the modules. The redesign should be **compressed trail sensing**: the nose reads s × ln(1 + x / x₀) of the trail value x, plus the scent. The trails stay linear, so the peer controls keep their meaning. It goes behind a flag, with equivalence while off, and a bounded search over x₀ (and s) under Amendment 1's gates, with the follower's gain fixed in advance. The alternative, dropping E3b-1's trail claims and keeping its gate, should come only if the compressed sensing also fails."

## Questions

1. **Is the hypothesis right?** Check the records. Is there an explanation, a bug or a measurement artefact that the report misses? For example: the follower's 0.005 threshold; the scent; occlusion; the cap's denominator; the comparison with the no-trail rate (3.94 on 256 mazes, 3.33 on mazes 0-63).
2. **Which option?** Compressed sensing; dropping the trail claims; or something else, such as divisive normalisation (L − R) / (L + R + ε), adaptation, or a different follower. Which is scientifically defensible, and which keeps E3b's question (do trails help colonies of these organisms?) intact?
3. **If compressed sensing:** what must be fixed in advance? Consider:
   - the transform's family and constants and their search;
   - what the follower is;
   - whether the seeds' component tests change;
   - how the scent combines with the trail;
   - what "linear peer controls" still means once the sensing is nonlinear;
   - whether this is still E3b-0 under its cap, or needs a new plan version and review;
   - what it costs.
4. **Does this need the owner's decision, or is it within an exploratory stage's redesign?** The delegation: consensus decisions inform the owner; scientific-direction changes need the owner first.

Give a verdict: "compressed sensing, as proposed (with fixes)", "something else (say what)", or "drop the trail claims".
