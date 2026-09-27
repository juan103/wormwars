You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

# Pre-push review: two pushes to the public WormWars repository

The owner asked for your review before two pushes to the **public** GitHub repository
(github.com/juan103/wormwars). Once pushed, content is public immediately and history is never
rewritten. You are read-only in the local repository, on branch `roadmap`, at HEAD 4dab3f0.

## Push 1: `git push origin roadmap`

This creates a new public branch `roadmap`, **not merged into main**. It holds 41 commits on top
of the public main (5706c7e); list them with `git log --oneline 5706c7e..roadmap`.
- **Purpose:** the owner wants the 03r pre-registration (`experiments/03r-replication/`, bound
  at 7c146fc) to be public before the 03r run finishes. The run started at 7c146fc and is about
  60% done. GitHub's receipt time is the proof of order.
- **The branch also holds:**
  - roadmap v3 (`ROADMAP.md`, the owner's, installed with edits: D062);
  - the owner's 03a draft;
  - 02b;
  - experiment 03's pre-registration, results and reviews;
  - the 03r code and ensembles;
  - `DECISIONS.md` D038-D062;
  - `docs/reviews/`.
- **03's first-run results become publicly readable on this branch** before 03r finishes. The
  owner's plan is that 03 and 03r reach main together later.

## Push 2: `git push origin main`

A fast-forward of main from 5706c7e to db447db: one commit adding a Corrections entry to
`experiments/02-screening/RESULTS.md`, about the mirror-symmetry reading (D050). The full diff is
below. The owner's rule is to publish corrections promptly, quoting the wrong text rather than
deleting it.

```diff
commit db447dbbf86fdb8971d0df33702c24bbad4bf307
Author: Juan H. González Estefan <54718981+juan103@users.noreply.github.com>
Date:   Sun Sep 27 15:15:47 2026 +0200

    02 results: Corrections entry for the mirror-symmetry reading (D050), quoting the registered text
    
    Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>

diff --git a/experiments/02-screening/RESULTS.md b/experiments/02-screening/RESULTS.md
index 09e53b9..b724015 100644
--- a/experiments/02-screening/RESULTS.md
+++ b/experiments/02-screening/RESULTS.md
@@ -1,5 +1,8 @@
 # WormWars 02: results of the screening
 
+> **Correction after publication (2026-09-26):** the mirror-symmetry reasoning in 02's
+> pre-registration was wrong. No result changes. See [Corrections](#corrections).
+
 **The primary prediction is challenged: in the primary cell, neither group of evolved champions
 meaningfully uses the left-right food difference.** In stereo foraging with food entering the
 biological neurons, removing the difference costs N2's champions +0.027 [+0.000, +0.060] and
@@ -35,6 +38,42 @@ with the probes, of a 12-hour cap; no probe step was dropped; one RTX 5080. The
 from commit `225e8f8`, and the probes and report from `971bbb3`. The only difference between the
 two is Fable's review amendments, which touch probes, analysis and wording (D041).
 
+## Corrections
+
+### 1. The mirror-symmetry reading was wrong (2026-09-26, D050)
+
+The pre-registration registered this reading in §4, under "Registered readings", and D041 records
+the same reasoning. The registered text, unchanged:
+
+> **Mirror symmetry.** A degree-preserving shuffle destroys the left-right pairing of targets,
+> and the turn read-out is bilateral. So any mirror-symmetric graph gets a left-minus-right
+> comparison almost for free. The remaps cannot control for this, because R1 and R2 are
+> symmetric pairs inside N2 too. **If the verdict is supported and N2 shows a comparable
+> advantage under R1 and R2, the result is read as a symmetry effect, not as something specific
+> to the food neurons' wiring. The full design then needs a mirror-symmetric shuffle control.**
+
+**Why it is wrong.** The turn read-out is dorsal minus ventral, not left minus right, and each of
+those groups holds both left and right neurons. So it is unchanged when left and right are
+swapped. Food on the left and food on the right are mirror images of each other. An exactly
+mirror-symmetric network therefore turns the same way for both. Symmetry does not give the
+left-right comparison for free: it forbids it, and steering needs the symmetry broken.
+
+**What changes:**
+- **No result above.** The reading applied only if the primary had been supported, and the
+  primary was challenged. The sentence "The mirror-symmetry reading registered for a supported
+  result does not arise" still holds.
+- **The rationale for a mirror-symmetric control.** Such a control is still useful, but as a
+  control predicted to *lower* directional response, not as a test of a symmetry explanation.
+  That is how experiment 03 uses it.
+
+**Where else the reasoning appears:**
+- **The pre-registration (§4) and D041:** left as registered and recorded.
+- **The docstring of `wormwars/exp02/structure.py`:** corrected on the `roadmap` branch, and it
+  reaches main with that branch, as does D050 itself.
+
+**Found by** Astra 6, reviewing experiment 03's design. Checked against the read-out's
+definition by Claude before it was adopted.
+
 ---
 
 ## Primary (pre-registered, §4)
```

## Checks already run

- **Identity:** every author and committer field in both pushes is the GitHub noreply address.
  There are no session-URL trailers and no personal email in any commit message or changed file.
- **Hygiene:** `tests/test_publication_hygiene.py` passes 6 of 6 on both trees. It checks for
  connectome data and pickle. No new `.npz` files are in either push, and the full suite passes.

## What to check

1. **Anything in push 1 that should not be public, or not yet.** For example:
   - connectome-derived data (the per-graph JSON in `experiments/03*/` holds measured values and
     hashes, not edges; verify);
   - personal data, credentials, or local paths;
   - review texts that contain something inappropriate;
   - claims in 03's RESULTS.md or the roadmap that should be fixed before they are public, even
     on a branch.
2. **Is publishing 03's first-run results on a branch before 03r finishes a problem** for 03r's
   integrity, or for how it will be read? Is there anything the owner should add, such as a
   note in the README or on the branch?
3. **Does the 03r pre-registration's timing claim hold?** It is pushed after the run started and
   before it finishes; `ROADMAP.md` and D062 say so plainly. Is that stated accurately and
   sufficiently?
4. **Push 2:** is the Corrections entry accurate, including the explanation of why the reading
   is wrong? Is it complete, and does it meet the owner's rule? Should anything else on main be
   corrected at the same time? For example, the docstring in `wormwars/exp02/structure.py` on
   main still carries the wrong reasoning: see `git show 5706c7e:wormwars/exp02/structure.py`.
5. **Roadmap v3's edits (D062):** are the four factual corrections correct, and is the "Carried
   over from v2.2" section faithful to v2.2 (`git show 7c146fc:ROADMAP.md`)?

## Answer format

For each push: **blocking issues** (do not push until fixed), then **should fix soon** and
**minor**, each with the file, the line and the evidence. End with one line per push: "push",
"push after fixes", or "do not push".
