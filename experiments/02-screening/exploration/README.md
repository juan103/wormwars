# Exploration before the pre-registration

These runs happened after the pilot's feasibility gate failed (`../pilot.json`) and before the
pre-registration. They use only the pilot shuffles SH101-SH108, which never enter the screening,
and scripted controllers. None of them evolved or scored N2. The one exception is a
generation-0 structural number, disclosed below.

The scripts are here as they were run. Their paths were changed to repo-relative afterwards.
The first three printed to the terminal; their numbers are copied from the session record
(`.superpowers` ledger), not from saved output files. `structure_and_timing.py` saves
its own output. Every script sets its seeds, so rerunning it reproduces its numbers.

## Why the feasibility gate failed (`../pilot.json`)

The T1 pilot champion (SH101, 40 generations) beats the tuned memoryless controller by +0.59
[0.53, 0.66]. But 1-cell jitter, the validated history ablation, costs it only +0.004
[-0.012, +0.019]. The gate needed both, so it failed as pre-set.

## `feasibility_probe.py`: is the pilot champion a better memoryless controller?

- A tuned graded kinesis (speed a smooth function of food level) does not beat binary kinesis:
  2.101 against 2.117. Memory beats graded kinesis by +0.98. So the task does demand memory from
  scripted controllers.
- T1 champion, real minus ablated: food constant -1.2, mirrored -0.68, collision off -0.35,
  jitter 1/2/3 all about 0. T0 champion: reduced to one nose, only +0.07 [0.025, 0.118]. Scripted
  stereo is worth about 1.1.

## `long_pilot.py`: does longer evolution produce the capabilities?

SH101, 120 generations, snapshots at 40, 80 and 120.

| | gen 40 | gen 80 | gen 120 |
|---|---|---|---|
| T1 held-out | 2.655 | 2.730 | 2.877 |
| T1 loss under jitter 1 | ~0 | ~0 | ~0 |
| T1 loss under jitter 3 | ~0 | ~0 | +0.039 [+0.014, +0.065] |
| T1 loss under constant food | 0.78 to 1.33 across snapshots | | |
| T0 loss with one nose | +0.025 | +0.005 | -0.010 |

The jitter-3 figure is not evidence of history use: jitter 3 costs the memoryless scripted
controller 0.057 by itself (`../probe_validation.json`).

## `search_pilot.py`: is the search too noisy?

SH101, T0, 40 generations:

- E1, 32 training worlds per strain (4x): held-out 2.767, one-nose loss +0.024 [-0.002, +0.052].
- E2, population 128 (4x): held-out 2.874, one-nose loss +0.058 [+0.031, +0.091].

A bigger search helps a little.

## Generation-0 input response (first version of the probe), with a disclosure

The first input-response probe measured random brains' turn read-out change when food went
from (0, 0) to (0.5, 0), outside the world. On SH101-SH108 it gave 0.009-0.030 (median 0.014).
**Disclosure:** N2's value under the M0 mapping, 0.12 (common mode 0.16), was also seen at this
point. It was the only N2 number seen before the pre-registration. It is generation-0 structure,
not fitness. N2 under the remapped interfaces was deliberately not looked at.

Astra's decision review (point 3) showed this probe confounds the left-right difference with the
total food level ((0.5, 0) also has more food than (0, 0)). It also ignores the world's gains and
clip. So it does not establish a stereo-routing difference.

## `structure_and_timing.py`: the corrected probe on the shuffles, and the probe suite's cost

The corrected probe compares (b+d, b-d) with (b-d, b+d), where b = 0.1 and d = 0.05 in
sensed-signal units. It uses the interface's sensor gains, input clamp, and each shuffle's own
calibrated motor gains. Output: `structure_and_timing.json`. N2 is not measured here; its value
is a registered outcome of the screening's probes.
