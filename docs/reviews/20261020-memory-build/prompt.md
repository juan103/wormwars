This is round 2 of a brainstorm, the "build" round. It is still not a review: no idea is criticised or cut in this
round.

## The question (unchanged from round 1)

Why does the history difference in N2's random brains decay more slowly than in shuffled graphs' brains?
(03mc, `experiments/03mc-p4-confirm/RESULTS.md`: N2 keeps 0.436 of its difference 30 ticks after the ramp; the
null ensembles' medians are 0.255 to 0.291.)

## What came in during round 1

Five voices, each written without seeing the others. Each is inlined below this prompt, and is also in
`docs/reviews/20261020-memory-diverge/`:
- **the project's owner** (`owner.ideas.md`): ring attractors, trapped waves in loops, transplanting;
- **a roadmap written by ChatGPT,** supplied by the owner (`chatgpt.roadmap.md`);
- **Claude** (`claude.ideas.md`), 13 ideas;
- **Fable 5.1** (`fable.answer.md`), 17 ideas;
- **Astra 6** (`astra.answer.md`), 18 ideas.

**Facts that came out of round 1** (Fable read them from the files; check them if you build on them):
- N2's mean retention curve flattens at about 0.09 from tick 150 to tick 300, while every ensemble keeps falling;
- 03m's deletion screen excluded the eight turn read-out neurons;
- every study used one food level.

The per-genome arrays (`runs/p4mc/arrays/`, local) exist, so checks on them cost seconds.

## What I want from you

Build on the others' ideas: "yes, and".

1. **Families.** Group all the ideas, from all five sources, into mechanism families. Name where two ideas are the
   same idea in different clothes. Keep the crazy ones as their own families if they do not fit.
2. **Hybrids.** Combine ideas from different sources into new ones that neither source had. At least five.
3. **New ideas sparked by reading the others.** At least three.
4. **Discriminating experiments.** Name the few cheap measurements (seconds on the local arrays, or about an hour of
   CPU) that would split the families from one another, rather than test one idea at a time. For each, say which
   family each outcome would favour.
5. **Taken further.** Pick one idea from another source that you think is underrated, and develop it further than
   its author did.

Do not argue that any idea is wrong in this round; selection is round 3. You may read the repository to make ideas
concrete. Do not edit files or run anything.
