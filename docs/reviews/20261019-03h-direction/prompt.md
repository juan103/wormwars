You are being consulted for an independent second opinion by another AI model (Claude, working in Claude Code) on behalf of its user. Be direct and specific. Disagree where you disagree; say so plainly when something is wrong, and say when you are unsure. Do not flatter the work. If a claim can be checked against files in the working directory, check it rather than assume. You are read-only: do not attempt to modify anything.

## Question

You are being consulted, read-only, in the repository you can read (branch `roadmap`, commit 0280089), on a direction
question for 03h. Read `experiments/03h-history-use/DESIGN.md` (v3.2, agreed by you both), its §7.2 annotation, and
D329 in `DECISIONS.md`. Step 0's records are in `experiments/03h-history-use/development-records/` (`step0.json` and
its verification files).

## What happened

Step 0, exploratory, ran on 03's 16 committed pilot SH graphs and their 256 random fitness genomes, under the pinned
interface.
- **The verification:** the genomes and graphs were reproduced exactly. Both the fitness replay and the world-free
  history check were bit-equal, in both modes.
- **The result:** the partial Spearman of H (|raw-turn final difference|, P4's per-genome numerator) with the
  committed T1-M0 fitness, given S, is:
  - mean −0.024;
  - between-graph SD 0.060, so an SE of 0.015;
  - 6 of 16 positive;
  - a top-against-bottom quartile difference of −0.001.
- The between-graph SD is about one graph's genome-sampling SD (≈ 0.063).

**What it means for the design:** A as registered requires A1 (ρ_level > 0 in SH-mirror-ASK). Step 0 points to A1
failing. B, N2's head start against the sham-controlled relief, is untouched.

## The options, as Claude sees them (attack them; add others)

- **(a) Continue as designed:**
  - pilot about 0.3 GPU-hours, formal about 2.2;
  - A likely null, which would close this screening route, worded in advance;
  - B tested.
- **(b) Run B only:** the same machinery and nearly the same cost, without A's family. Is A's likely null still worth
  registering, since it would be a confirmatory null?
- **(c) Stop 03h** and report step 0 as exploratory: "probe-measured history magnitude does not predict T1 fitness
  in random SH brains at generation 0".
- **(d) A further exploratory step 0b** before deciding:
  - H_dir (the directional measure) and the forward read-outs on the same genomes, minutes of GPU;
  - or N2's own ρ_level on 03's committed N2 data, if any.

  This is a fork chosen after seeing step 0, and would be labelled so.

## Please

- Say which you recommend, and why.
- Say whether step 0's result changes how A should be read, or whether A is still worth its cost.
- Say what, if anything, must change in the design before the pilot if it continues.
- Name any error in D329's reading of step 0.

Answer with your recommendation in one line first, then numbered points. Do not edit files or run anything.
