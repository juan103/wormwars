# E2: a short optimizer screen

**Status: completed and reviewed (2026-09-29).** Pre-registered and pushed before its runs: the text
bound at `60af3cf`, the binding commit (as the registration defines it, the one the projection
records) `69f4163`, which adds only a development record. Every stage ran once on the binding code,
with no rerun or amendment. Both reviewers checked the results ("fix", text only); the corrections
are dated in `RESULTS.md` (D125).

- **Outcome:** "E2: keep 02's GA (unshaped fitness; the ES did not satisfy both replacement criteria
  after paying for its tuning)". The ES led the GA by 0.125 targets per episode (0.5 needed); 5 of
  its 8 champions were above the GA's median (6 needed).
- **The floor fired:** random sampling came within 0.36 targets of the GA, so the roadmap's rule
  applies before building on Task N: diagnose saturation, noise and budget. It is a registered
  trigger, not a finding that the optimizers add nothing (the GA gained 22% over random sampling, the
  ES 30%), and it depends on the GA's one failed run. See [`RESULTS.md`](RESULTS.md) and its
  corrections.

**The question.** Given the same additional simulator work, does OpenAI-ES find better Task N
navigators than 02's genetic algorithm (GA), starting from random N2 genomes? The answer chooses the
provisional default optimizer for E3 (the roadmap's Track E). Random sampling is the floor: if it
comes within 0.5 targets of the GA, the task or budget is diagnosed before E3 builds on it.

**The design in brief:**
- Task N exactly as E1 and 04a ran it; the N2 genome; unshaped fitness (the raw count).
- 8 runs per method. Run r of every method starts from the same generation-0 population on the same
  world schedule.
- The GA is 04a's, unchanged. The ES's σ and learning rate come from a 15-run pilot, charged
  to the ES: all three methods use about 2.13 million selection episodes.
- One hold-out pass on 1 024 new worlds, with mirrored and constant probes and E1's scripted
  controls.
- **The ES replaces the GA** only if its mean is at least 0.5 targets above the GA's **and** at least
  6 of its 8 champions are above the GA's median champion.

**Read:**
- [`PREREGISTRATION.md`](PREREGISTRATION.md): everything fixed before the run, and the outcome
  wording;
- [`../../docs/E2/DESIGN.md`](../../docs/E2/DESIGN.md): the design and its three review rounds;
- `DECISIONS.md` D117-D125: how the design and the pre-registration changed under review, and the
  results;
- reviews: `docs/reviews/20260929-*-E2-*`.

**Reproduce it** (after binding; CUDA, one RTX 5080, the pinned environment):

```
python scripts/e2.py project
python scripts/e2.py pilot --stage 1
python scripts/e2.py pilot --stage 2
python scripts/e2.py train --method ga
python scripts/e2.py train --method random
python scripts/e2.py train --method es
python scripts/e2.py extend
python scripts/e2.py evaluate
```

Each stage writes a JSON record here; genome files and the ES's saved state stay local under
`runs/e2/`, because they derive from the connectome's weights, which this project does not
redistribute. `--smoke` runs the whole chain at tiny sizes on ids 0-9 999, in `runs/e2-smoke/`.

**The code:** `scripts/e2.py` (the runner; every registered number is in `REGISTERED`),
`wormwars/e2/` (the ES, random sampling and their batched loops), `wormwars/e04a/evolve.py` (the GA's
batch), and the tests `tests/test_e2_*.py`.
