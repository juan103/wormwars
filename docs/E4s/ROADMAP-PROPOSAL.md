# Proposed roadmap change: E4s after the literature review (2026-10-01)

Status: a proposal for review by Astra 6 and Fable 5.1. Nothing here has run. If both agree, it
goes into `ROADMAP.md` as a dated amendment, with a D-entry.

## Why a change

- **The plateau.** E2d found that no evolved champion (0 of 47) steers by the left-right scent
  difference, and that no tested optimizer change left the plateau (D136, D137). E3 needs a
  navigator.
- **The owner's plan (2026-09-30).** A hand-built stereo module ("E4s") grafted onto N2, then
  evolution. The owner's design: two noses and a fly-style ring attractor. The ceiling is 96
  GPU-hours (D139).
- **Its designs rested on an unchecked report.** Designs v1-v3 (D139-D142; v3 is uncommitted) rested
  on a literature report by Claude Sonnet 5.5. It was a single CLI session; most of its sources were
  seen only as search snippets, and nobody checked its claims. It was wrongly called "a deep
  research". The owner commissioned a real review.
- **The literature review** (`docs/reviews/20261001-literature-review/`): two reviews from one
  prompt, Claude Opus and Astra 6. Neither is verified by us yet. They agree on four points:
  1. **The ring is not needed to steer on a smooth Gaussian scent.**
     - Two sensor-to-motor pathways with crossed or opposed signs suffice: a Braitenberg vehicle,
       2-4 units (Rañó 2012; Simões et al. 2021; Adden et al. 2022).
     - Memory helps with outages, changing plumes and displacement (Singh et al. 2023; Sun et al.
       2021), not with a continuously available cue.
     - Our own E1 already showed Task N needs no memory: a memoryless scripted steerer scores 8.7.
  2. **Small hand-built rings are fragile:** sensitive to tuning and noise, and they can pin the bump
     or fail to move under weak input (Noorman et al. 2024). A released MIT implementation exists, if
     a ring is needed later.
  3. **Grafting precedents exist, and a calibrated interface matters.**
     - Seeding and incremental evolution (Koppejan & Whiteson 2011; Tomko & Harvey); NEAT advice
       (Yong et al. 2006); co-adaptive augmentation (Bryan et al.).
     - New host-graft connections should start at zero or small values (Tomko & Harvey).
     - Adden et al. needed an input remapping before their steering module worked with a navigation
       network.
     - No found study evolves a stereo graft inside a worm-connectome mask and separates retention,
       bypass, redundancy and transfer into the host. Both reviews call that a gap, from a bounded
       search.
  4. **The worm's own chemotaxis is temporal, not stereo.**
     - Klinotaxis: concentration change during head sweeps (Izquierdo & Lockery 2010; Izquierdo &
       Beer 2013; Matsumoto et al. 2024).
     - ASEL and ASER are ON and OFF cells, not a left and a right nose; on agar the worm bends
       dorsoventrally, so its anatomical left-right is not the steering axis.
     - The successful connectome-constrained chemotaxis models use temporal ON/OFF sensing,
       mirror-symmetric parameters, and weights up to ±15.

## The owner's decision on the sensing interface (2026-10-01)

**Option (a): keep the bilateral left/right scent as an explicit game-design choice.**
- WormWars's weys get separate left and right food readings; the README already says a real worm
  cannot do this. E4s's claims are about evolving brains on the N2 mask under this game's sensing,
  not about worm chemotaxis.
- **Not scheduled:** temporal ON/OFF sensing, as Izquierdo used, and wider weight bounds (±15).
  They are listed under "What would change this roadmap" as the next options if the stereo route
  fails.

## Proposed sequence for Track E

### E4s-0: diagnostics (exploratory; at most 2 GPU-hours; no evolution)

Three measurements. They decide the shape of E4s-1 and how its result is read.

1. **A stereo-gain sweep on existing champions** (Astra's suggestion). Add a scripted residual
   turn += k(L − R) to each of 04a run 2 and E2's GA champions. Score them on Task N for k ∈ {0,
   0.25, 0.5, 1, 2, 4, 8, 16, 32}.
   - **Read:** does the score rise from small k (selection would reward small stereo increments), or
     dip first (a valley)? And does the champion's own strategy conflict with stereo turning at large
     k?
2. **Where the difference is lost.** For each champion, at the sensory neurons, then the main
   interneurons, then the turn motor neurons, the differential gain K_D = ∂u/∂d and the
   common-mode gain K_C = ∂u/∂m (d = L − R, m = (L + R)/2). Controls as in gain probe v3.
3. **A two-unit comparator** (Astra's equations):
   - τ ẋ_L = −x_L + a(L − R), τ ẋ_R = −x_R + a(R − L), u = b + b_m[tanh x_L − tanh x_R].
   - It is grafted as two extra neurons with weights within ±3, and run on the Stage A carrier (a
     declared forward drive) and on 04a run 2.
   - Recurrence (gain a/(1 − r)) and a 4-unit mutual-inhibition variant are the next steps if the
     two units fall short.
   - **Measured:** reachable K_D, K_C, and the Task N score.
   - **Pre-stated reading:**
     - if no variant within ±3 reaches 5.0 targets per episode on the carrier, the bounds question
       goes back to the owner before E4s-1;
     - if one does, E4s-1 uses the smallest that does.

### E4s-1: the comparator graft under evolution (confirmatory; pre-registered; cap set there)

- **The module:** the smallest comparator that passed E4s-0, frozen in a file before the
  registration.
- **The background:** random N2, drawn on N2 and embedded. 04a run 2 is a descriptive case study.
- **Arms:**

  | Arm | Module mutation | Role |
  |---|---|---|
  | Main | reduced (for example 0.25×) | |
  | Frozen | none | protection by construction (PathNet's point) |
  | Uniform | 02's scale | |
  | Random graft | as the main arm | same neuron count, random wiring: does any extra capacity help? |
  | No added output | as the main arm | the module present but cut from the motors |

  The main arm and its paired controls are confirmatory; the rest are descriptive. New host-graft
  edges start at zero.
- **Outcomes** (Astra's partition), each with a pre-stated measurement:
  - retained: the function is kept and still causally useful;
  - eroded;
  - bypassed: it works in isolation but is no longer used;
  - redundant;
  - transferred into the host: host-only stereo diagnostics improve after joint evolution.
- **Reuses design v3's work:** the carrier, F against C, the per-run generation-0 classification,
  the module probes, the lesion, reset-to-seed and transplant probes, and the engine changes already
  built. Those are per-parameter mutation scales, `evolve_batch` hooks, embedding, the hygiene guard
  for grafted genomes, and the synapse-direction test.

### E4s-2: memory (deferred; only if E3 needs it)

- A ring, or another directional memory, only with a task where memory can matter: scent outages,
  relocation with stale memory, displacement.
- It starts from Noorman et al.'s released code, tested for drift, velocity gain, dead zones and
  recovery.
- Two concentration samples give a lateral component, not a full bearing (Astra). Its design says
  what resolves the ambiguity.

### E3 (unchanged in structure, with three additions)

1. **The navigation module** is E4s-1's retained module if it exists. Otherwise it is 04a run 2,
   with its measured limits stated.
2. **A baseline:** one shared navigator plus a persistent goal bit, beside the two-module organism
   (Astra).
3. **The latch** can be one extra neuron with self-excitation within ±3: τq̇ = −q + 2 tanh q + S − R
   (Hülse & Pasemann's analysis), validated in our integrator. The inactive module's semantics
   (update, freeze or reset) are declared in advance.

### E4 (unchanged; one addition)

Pruning follows a protocol, not one neuron at a time (Fakhar & Hilgetag 2022):
- importance recomputed after each removal;
- several removal orders;
- interactions tested in pairs;
- acute and retrained results reported separately;
- the claim limited to "the smallest circuit found under this procedure".

## Other changes

- **Tripwire:** relaxed for the graft functions and the GA hooks only (already built and tested).
- **Related work:** link the literature review.
  - Izquierdo & Beer 2013 and Hironaka & Sumi 2025 become the reference worm-chemotaxis models.
  - Hironaka & Sumi's MIT code is the executable baseline if the temporal option is ever taken.
  - Claims are cited only after we verify them.
- **What would change this roadmap,** new entries:
  - "No comparator within ±3 reaches 5.0": the owner decides between wider bounds and temporal
    sensing.
  - "E4s-1 finds the module eroded or bypassed under every free mutation scale": report it; E3 uses
    the frozen module, labelled as engineered.
- **Design v3 is superseded:** it is not committed as a plan. The design work it contains is reused
  in E4s-1, and D142 records it.
- **The budget:** the owner's 96-hour ceiling for E4s stands. E4s-0 at most 2 h; E4s-1's cap is set in
  its pre-registration (about 15 h expected); the rest is kept for E4s-2 if needed.

## Questions for the reviewers

1. Is the sequence right: E4s-0 diagnostics, then the comparator graft, with the ring deferred?
2. Will E4s-0's three measurements and their pre-stated readings decide what they should? What
   would you add or cut?
3. Is option (a) framed honestly, with the temporal route and wider bounds as named alternatives?
4. E4s-1: are the arms and the outcome partition right? Anything from the literature we should adopt
   or drop?
5. Should E3 wait for E4s-1, or start with 04a run 2 in parallel?
6. Is anything in the review's claims that this proposal relies on likely wrong, and should be
   verified first?
