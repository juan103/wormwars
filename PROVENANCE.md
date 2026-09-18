# Provenance of the connectome data

No connectome number in this repository was synthesised, approximated or reconstructed from memory.
Everything below comes from one published file, and every transformation applied to it is listed.

## Source

| | |
|---|---|
| Dataset | Cook et al. 2019, **hermaphrodite** whole-animal connectome, corrected July 2020 |
| File | `SI 5 Connectome adjacency matrices, corrected July 2020.xlsx` |
| URL | <https://wormwiring.org/si/SI%205%20Connectome%20adjacency%20matrices,%20corrected%20July%202020.xlsx> |
| Landing page | <https://wormwiring.org/pages/adjacency.html> |
| Downloaded | 2026-09-17 |
| Size | 4 188 190 bytes |
| **sha256** | `1f4fdbf84746b69b49a8da0816f52787860ce349b638dce37924ba80f90c70c9` |
| Local copy | `data/raw/SI5_Connectome_adjacency_matrices_corrected_July_2020.xlsx` (not committed) |

Citation:

> Cook SJ, Jarrell TA, Brittin CA, Wang Y, Bloniarz AE, Yakovlev MA, Nguyen KCQ, Tang LT-H,
> Bayer EA, Duerr JS, Bülow HE, Hobert O, Hall DH, Emmons SW (2019).
> *Whole-animal connectomes of both Caenorhabditis elegans sexes.* **Nature** 571:63–71.

`scripts/fetch_connectome.py` re-downloads the file, checks that sha256, and refuses to continue if
it has changed upstream.

## Redistribution

**This file is not redistributed in this repository.** wormwiring.org carries the notice
"Emmons Lab Copyright (c) 2020" and states no licence granting redistribution, and the Nature
article is not open access. Neither the source `.xlsx` nor the derived `.npz` cache is committed;
both are in `.gitignore`. Fetch the data yourself with `python scripts/fetch_connectome.py`, which
verifies the sha256 above. The MIT licence on this repository covers the code and documentation
only.

## Which quantity the weights are

Verbatim from the spreadsheet's own `TITLE AND LEGEND` sheet:

> "For chemical connections, rows give the pre-synaptic cell, columns give the post-synaptic cell.
> **Weights in the body of the matrices are the total number of EM serial sections of connectivity,
> taking into account both the number of synapses and the sizes of synapses.** To provide complete
> coverage of the entire nervous system, the data are assembled from multiple animals and include
> connections added by extrapolation in gaps where no data were available."

and:

> "Corrections, July 2020. The attempt is made here to remove all inconsistencies and errors in the
> published tables. In particular, for the gap junction tables, values across the diagonal should
> match and be consistent with the values in the asymmetric tables."

So the quantity carried through this codebase is `weight_kind = "em_sections"`. **It is not a
synapse count.** The loader API keeps the distinction visible (`Connectome.weight_kind`) because
genome initialisation scales |W| with this number.

Two consequences worth stating plainly:

1. The weights conflate how many synapses there are with how large they are.
2. Some entries are **extrapolated**, not observed, because the dataset is assembled from multiple
   animals to get whole-animal coverage. We use the file as published rather than trying to
   separate observed from extrapolated connectivity.

Alternatives considered and rejected: `SI 2 Synapse adjacency matrices.xlsx` (a different quantity;
SI 5 is what the paper's figures use), `SI 7 Cell class ...` (collapsed to cell classes, which would
destroy the left/right distinctions the sensor map is built on), and the uncorrected `SI 5` (the
corrected file exists precisely to fix the inconsistencies we would otherwise inherit).

## Sheets used

- `hermaphrodite chemical` — directed, rows presynaptic, columns postsynaptic.
- `hermaphrodite gap jn symmetric` — the reconciled symmetric table. The asymmetric sheet is not
  used; the July 2020 corrections exist to make the symmetric one consistent, so taking it avoids
  inventing our own symmetrisation rule.

Layout inside each sheet: row 0 holds column block headers, row 2 holds column cell names starting
at column index 3; column 0 holds row block headers, column 2 holds row cell names starting at row
index 3.

## Transformations applied, in order

1. **Neuron set.** All 300 cells that appear as *rows* of the chemical sheet (muscles and end organs
   appear there only as columns), plus `CANL` and `CANR`, which appear only in the gap sheet.
   Total **302 neurons** — the canonical hermaphrodite count. Order: pharynx → sensory →
   interneurons → motor → sex-specific → CAN, i.e. the spreadsheet's own order with CAN appended.
2. **Classes** taken from the spreadsheet's own block headers:
   `PHARYNX`→`pharyngeal` (20), `SENSORY NEURONS`→`sensory` (83), `INTERNEURONS`→`inter` (81),
   `MOTOR NEURONS`+`SEX SPECIFIC`→`motor` (116), and `CANL`/`CANR`→`other` (2).
   The gap sheet files CAN under a `MUSCLES` block header; that is a layout artifact of that sheet
   and is not treated as a claim about their identity.
3. **Non-neuronal columns dropped**: body-wall muscles, pharyngeal muscles and end organs. The brain
   is 302×302 over neurons only. This discards real anatomy — the motor read-out is a linear read of
   named motor neurons, and no muscle layer is simulated.
4. **Empty cells → 0.**
5. **Chemical autapses kept**: 38 of them, summing to 117 EM sections. They are in the published
   matrix and `W_ii · tanh(v_i)` is a real dynamical term. SH and RD graphs are allowed self-loops
   so the conditions stay matched.
6. **Gap self-edges dropped**: 14 of them. `G_ii · (v_i − v_i)` is identically zero, so a nonzero
   diagonal could only corrupt the implicit denominator of the integrator.
7. **Symmetry check**: `max |G − Gᵀ| = 0` before any symmetrisation, so no symmetrisation was
   applied. (The code would symmetrise and report it if that were ever nonzero.)
8. **Sign check**: no negative entries in either matrix.

## What came out

| | |
|---|---|
| Neurons | 302 |
| Chemical edges (directed, incl. 38 autapses) | 3 709 |
| Gap junctions (undirected) | 1 091 |
| Cache file | `data/cache/cook2019_herm.npz` |
| Cache sha256 | `43b87aa172a0042b9dce734b15bdf1c87efe3a33ac1cc0d9cd03255a60c96d4a` |

Neurons with unusual connectivity, reported rather than patched:

- **No outgoing chemical synapse (7):** `CANL`, `CANR`, `DD04`, `DD05`, `MCL`, `MCR`, `SABVR`.
  For `MCL`/`MCR` this is expected: their real targets are pharyngeal muscle, and muscle columns
  were dropped in step 3. They are read-out neurons here, so this does not disable the pump.
- **No incoming chemical synapse (2):** `PLML`, `PLMR`. They are sensory neurons and are driven by
  injected current.
- **No gap junction (4):** `AS07`, `AS08`, `AS09`, `RMFR`.
- **Fully isolated (0):** none. All 302 neurons participate in at least one edge.

## Somatic ↔ pharyngeal connectivity

Measured from the loaded matrices, because the pump read-out depends on it:

- gap junctions: `I1L–RIPL` = 2, `I1R–RIPR` = 2
- chemical: `M1 → RIPL` = 1
- nothing else

The pharyngeal nervous system therefore hangs off the somatic one through a two-neuron bridge. This
is a real anatomical constraint with a real consequence for the experiment: in `N2`, pump control
must pass through `RIP↔I1`, whereas `SH`/`RD` shuffles will generally connect the pharynx to the
body much more broadly. If SH/RD beat N2 at pump-gated eating specifically, this is the first thing
to look at. Recorded here so the result is not a surprise later.
