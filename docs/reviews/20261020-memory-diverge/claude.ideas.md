# Claude's ideas, written blind (2026-10-20, before reading Astra's or Fable's)

The question: why does the history difference in N2's random brains decay more slowly than in shuffled graphs'
(03mc Q-D: 0.436 kept at tick 30, against ensemble medians 0.255-0.291)?

What is N2-specific in a random brain: topology, anatomical chemical magnitudes, anatomical gap magnitudes. Signs,
time constants and biases are random per genome. So any mechanism must run through topology and magnitudes.

1. **Less network, more leak (saturation).** N2's read-out neurons sit at low tanh slope (0.44 against 0.73). If
   N2's operating point saturates more neurons, the recurrent part of the Jacobian shrinks and the decay falls back
   toward each neuron's own leak, 1/tau, which is slow for the slow-tau neurons. In shuffles, recurrent feedback may
   actively *speed up* decay. Memory as the absence of network. Kill check: per genome, compare the observed
   retention with a leak-only prediction from tau and the effective gains along the trace.

2. **The trace hides in the slowest, loneliest neurons.** With log-uniform random tau, the slowest mode may localise
   on slow-tau neurons with weak total coupling. N2's degree distribution (many low-degree neurons, a few hubs) could
   make such "lonely slow" neurons commoner on the food-to-turn path. Kill check: correlate each neuron's share of the
   late trace with its tau and its total coupling, in N2 and in nulls.

3. **Gap clusters as equipotential bodies (electrical circuits).** A uniform shift across a gap-coupled cluster is
   not damped by the gap term at all (the Laplacian's zero mode on that cluster); only differences inside it are.
   If N2's food pathway sits inside large, well-connected gap clusters, the trace can ride the cluster's common mode.
   Kill check: project the trace onto the gap Laplacian's eigenvectors; measure the share in its near-zero modes.

4. **Critical slowing down (physics).** N2 may sit nearer a fold or bifurcation at the final food level. Kill check:
   leading Jacobian eigenvalue at the post-ramp fixed point; sweep the food level and see whether N2's slowness peaks
   somewhere instead of being uniform.

5. **Power law, not exponential (glassy / fractional dynamics).** A broad spread of timescales gives power-law
   decay. N2's degree heterogeneity might widen the spread. Kill check, at zero compute: fit 03mc's committed
   retention curves (`report.json`, `descriptive.curves`) to one, two and three exponentials and a power law.

6. **Aging (spin glasses).** In glassy systems relaxation depends on how long the system waited before the kick.
   Kill check: vary the 100-tick hold before the ramp (50, 100, 200, 400) and see whether the retention curve's
   shape changes. If it does, the system is not near a single fixed point.

7. **Deep compartments (pharmacokinetics).** A drug stored in fat leaks back slowly into the blood. The trace may sit
   in a "deep compartment" of neurons weakly coupled to the read-out, which feed it back slowly. Kill check:
   biexponential fit, then identify the slow compartment's neurons and their path distance to the read-out.

8. **Reverse every synapse (time-reversal test).** Run N2 with all chemical synapses reversed, as 01 accidentally
   did. If the slow decay survives, it is a property symmetric under reversal (degrees, cycles, magnitudes); if it
   vanishes, it is directional (feedforward chains, sensory-to-motor flow). Cheap on CPU.

9. **Fluctuation-dissipation (statistical physics).** In a linear regime, the response to a kick equals the
   autocorrelation of spontaneous fluctuations. Measure the read-out's autocorrelation under tiny noise with no
   ramp; if it matches the retention curve, the linear eigen-analysis is enough; if not, the ramp drives the brain
   into a nonlinear regime and the memory is nonlinear.

10. **Morph N2 into a shuffle, region by region.** Swap edges gradually, one anatomical region (head ganglia,
    ventral cord, pharynx...) at a time, and watch where retention breaks. A "phase transition" in the curve would
    locate the structure. Expensive per point; start with three regions.

11. **The active subnetwork is a chain (nonnormal).** Saturated neurons are effectively cut out. The subnetwork
    that is left at the operating point may be closer to feedforward in N2, which gives transient memory without
    slow eigenvalues. Kill check: Schur decomposition of the effective Jacobian; the ratio of its non-normal part to
    its normal part, in N2 against nulls.

12. **Crazy one: it is the pharynx.** N2's pharyngeal nervous system is nearly isolated, joined to the somatic system
    by one bridge (I1 via RIP). If the food signal leaks into the pharynx and comes back late through that bridge, the
    pharynx acts as an echo chamber. Shuffles that do not preserve the bridge lose the echo. Kill check: delete or
    silence RIP and the pharyngeal neurons, and see whether the late trace collapses more than the early one.

13. **Crazy one: the trace is in the bias landscape, not in the dynamics.** Random biases set where each neuron
    rests. If N2's anatomy turns many neurons into near-threshold "switches" under the final input, the ramp's
    direction flips a few of them and they stay flipped for a while (slow escape from a shallow well). Kill check:
    count neurons whose sign of v differs between histories at tick 30, in N2 and nulls.
