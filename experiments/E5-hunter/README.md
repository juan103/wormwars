# E5 (stage 05): the hunter

**Status (2026-11-06):** E5-0, the CPU feasibility check, has run, and its results have been reviewed by both models
("fix then publish", every fix taken; [`E5-0/RESULTS.md`](E5-0/RESULTS.md), draft 2, D388). E5-1 (evolving
hunters, with a null-graph arm) is not designed yet, and needs the GPU and the owner's word.

## Why

The owner chose stage 05 from the roadmap (2026-11-04, D385): "start with a static prey, and then let the prey
increase in complexity. Like one that has a defined route. Then we use the ones we develop in the previous
experiments." They also asked for a null-graph arm, so that 05 asks whether N2's wiring helps a hunter (E5-1).

**Task H** is Task N (E1's navigation task) with a living target: the hunter follows a scent centred on a prey, and
catches it by reaching it or by biting it to zero energy. A prey with no body (H1-ghost) is Task N exactly, which ties
every hunter's score to E1's. The prey ladder:

| Level | Prey |
|---|---|
| H1 | static: ghost (no body), reach (with a body), bite |
| H2 | a scripted route follower on a closed 4-waypoint loop, speeds 0.1 to 1.0 |
| H2b | a random walk and a wall follower, speeds 0.25, 0.5, 0.75 |
| H3, H4 | earlier organisms as prey; held-out maps with obstacles (not built) |

The design is [`docs/E5/SCOPE.md`](../../docs/E5/SCOPE.md) (draft 2) and E5-0's plan
[`docs/E5/E5-0-PLAN.md`](../../docs/E5/E5-0-PLAN.md) (draft 2, §10 amended after the code review). Reviews:
`docs/reviews/20261104-E5-scope/`, `…20261105-E5-0-plan/`, `…20261106-E5-0-code/`, `…20261106-E5-0-results/`.

## E5-0: is the ladder solvable, and where do the reused hunters fall off? (exploratory; CPU, 7.94 hours)

- **The new code passed every equivalence check the plan specified** (on the CPU: old engine against new, and
  H1-ghost against Task N, bit for bit).
- **All 18 read settings are solvable and none is too easy:** a scripted, observation-limited hunter catches in
  every episode, and the best blind or stationary hunter scores 2.8% to 11.2% of it.
- **E4s-1's 16 champions (N2 plus the stereo graft) qualify everywhere,** zero-shot. L1, the 4-neuron comparator on
  its carrier, also qualifies everywhere, and catches fast prey best: 4.12 at route speed 1.0, more than any E4s-1
  champion (at most 3.14).
- **E2d's 47 N2-only champions stop qualifying** on the route at speeds 0.1 to 0.6, on the random walk at 0.25, 0.5
  or (one genome) 0.75, and on the wall follower at 0.25 or 0.5; generation 0 never qualifies.
- **The stereo difference matters to E4s-1 and L1, much less to E2d:** feeding both noses their mean costs E4s-1's
  champions 1.13 captures at H1-bite (0.10 to 2.97), E2d's 0.01. It is part of the gap between the families, not
  all of it.
- **Faster route prey are easier for the scripted hunters** (E1's frozen navigator 4.57 to 7.72 captures, the pursuit
  4.34 to 8.11), so E5-1's ladder needs a rule other than "where the positive control falls off".

Records: [`E5-0/`](E5-0/). `summary.json` holds the numbers the results quote, except the exploratory phases
(`phases.json`); [`genomes.md`](E5-0/genomes.md) reports every genome on its own.

## Reproduce it

```
python scripts/e5_0_summary.py        # the summaries, from the committed records
python -m pytest tests/test_e5_hunt.py tests/test_e5_0_summary.py tests/test_e5_0_phases.py
```

To repeat the formal run itself, see [`E5-0/RESULTS.md`](E5-0/RESULTS.md#reproduce-it): it starts from a checkout
without the stage records.

The code is `wormwars/e5/` (`hunt.py` the task, `prey.py` the scripted prey and the pursuit reference, `play.py` the
episode runner, `hunters.py` the reused hunters, each hash-checked) and three no-op hooks in `wormwars/world.py`.

## Extend it

- **E5-1** evolves hunters up the ladder, on N2 and on null graphs. Its open design questions: the ladder's rule (not
  the positive control's fall-off, which did not happen), which null families, a fair start for the null arm (E4s-1's
  graft was built and settled on N2 only), and L1 on its carrier as a frozen comparator. It needs a GPU benchmark
  before any cost forecast.
- **H3** needs prey organisms on their own graphs with an inert graft (SCOPE.md §5) and per-swarm targets.
