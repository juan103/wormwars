I have what I need. Checked: the interim report, the plan with Amendment 1, the three diagnosis records, the stage-b2 record, the follower and world code, the probe, and both earlier reviews.

**Verdict: something else.** Do not build compressed sensing yet. Run the seeds themselves at Stage B's strongest linear setting first, with a CPU decomposition of the follower's effect. The report's own K_D table undercuts the saturation story, and the compression proposal weakens steering at exactly the levels where the effect was found.

## 1. Is the hypothesis right?

Half right. The gain-versus-range mismatch is real: with gain about 32 to 35 and a qualified range of 0.35, a full turn needs a left-right difference near 10% of the whole range. But two parts of the argument do not hold.

**"Out of the modules' working range" misreads K_D.** The probe measures the response to a fixed absolute difference of 0.001. Under linear trails the absolute difference at a place scales with the level, so the behaviourally relevant quantity is K_D times level, the response to a relative difference. From the diagnosis records:

| Level | E: K_D | E: K_D × level | S3r3 A: K_D × level |
|---|---|---|---|
| 0.35 | 31.6 | 11.1 | 10.2 |
| 0.5 | 28.0 | 14.0 | 12.9 |
| 0.7 | 22.6 | 15.8 | 13.7 |
| 1.0 | 15.0 | 15.0 | 0 |
| 1.5 | 6.4 | 9.7 | 0 |
| 2.0 | 2.5 | 5.0 | 0 |

E's steering to a relative difference rises through 1.0 and only halves by 2.0. At the best-rate setting the 95th percentile input is 2.0, so E is in a usable regime for about 95% of inputs. The registered threshold of 30 is E3a's convention for a regime where levels never exceeded 0.35, not a functional ceiling. S3r3's module A collapses at 1.0, which was already a known risk. So "qualifying the modules at higher levels, where their steering collapses" is listed as not recommended on a premise the data contradict for E.

**The follower's effect is undecomposed.** Three mechanisms besides gradient steering could produce the +3.54, and the records cannot separate them:
- Occlusion asymmetry. About a quarter of ticks have one nose blocked. That nose reads 0 and the other reads the level, so under linear sensing the turn is level-proportional and saturates at high d₀. This alone would give a level-dependent "trail effect" with no gradient use, which fits the polarity failure.
- The policy switch. On a trail the follower leaves W2's one-sided wall following for W1 plus steering. The scent already triggers this near sources, so the switch matters mostly mid-route.
- The 0.005 threshold. The cap-passing settings have median inputs of 0.0007 to 0.01, so the trail is mostly invisible to the follower at those settings. "Difference too small to steer by" and "below detection" are conflated.

The no-trail rates are consistent, not an artefact: mazes 0-63 are harder than the 256, and both contrasts use their own baseline. The scent contributes under 1% to the cap count at weak trails. Nothing in the cap's denominator changes the conclusion.

## 2. Which option?

**Compression does not fix the mismatch by its own arithmetic.** The derivative of s ln(1 + x/x₀) is s/(x₀ + x), so the sensed difference for a relative difference r is about s·r above x₀. With s pinned by the cap, say x₀ = 0.1 and s = 0.076 so the 99th percentile maps to 0.35, the follower's turn for r = 0.2 is 0.44 at level 1.0, where linear sensing saturates it. At level 0.1 the two are equal. The low-level boost arrives only where it is negligible. Pushing x₀ down to 0.01 gives a uniform turn near 0.3 for r = 0.2 at every level, a threefold loss where the effect was found. The total input range of 0.35 and the gain of about 32 together bound the response, and compression only reallocates it.

**The decisive test is cheap and direct.** Run E and S3r3 with their variants, shared against none, at Stage B's best-rate linear setting on the selection mazes, uncapped and labelled exploratory. The compute record shows no neural updates yet. At the plan's 30 seconds per run this is about 0.3 GPU-hours. Beside it, on the CPU: a switch-only follower with gain 0, an occlusion-symmetrised follower, and a gain-128 follower at d₀/4. Then:
- **If E's shared minus none is positive:** the cap, not the trails or the sensing, was the wrong gate. Redesign the cap on the K_D × level curve, for example at most 5% of inputs above 1.5 for E, labelled post hoc, and rerun criterion 4 at the met quantiles. Several Stage B settings with effects above +2 would pass such a cap. S3r3 likely fails at 1.0, as stated in advance. E3b's question stays intact: same organisms, same trails, same sensing.
- **If E shows nothing where the follower gains +3.5:** these organisms cannot use linear trails as built. Then the sensing or the trail claims must change, and that is the owner's call.

Divisive normalisation and adaptation share compression's problem under a fixed gain, and adaptation would also make the follower temporally comparing, which the polarity reasoning ruled out. A different follower only matters if the seeds fail, since the follower is a proxy.

## 3. If compression is still chosen later

- Apply the transform to the summed nose input, trail plus scent. Compressing the trail alone and adding the scent linearly stacks to 0.7 near the sources and breaks the cap by construction. Compressing the sum changes the scent homing E3a qualified, so re-qualify it.
- Fix s from the cap and the recorded 99th percentile at one trail setting, Stage B's best rate. Search x₀ on a three-point log grid only. Two free parameters across 24 settings is a fishing expedition.
- Keep the follower's gain at 32 and apply the 0.005 threshold to the compressed input. The no-trail follower changes with the transform because the scent is compressed, so rerun it per x₀.
- The component tests become trivial, since every input lies in range by construction. Say so. The seed's behaviour is the real test.
- The peer controls act on fields, so own, peers and scramble keep their meaning. Additivity is lost: sensed shared is not sensed own plus sensed peers. Define the replay coefficient on the field and report the residual mismatch in compressed units.
- It is a new plan version with both reviewers, labelled adaptively selected. It fits E3b-0's cap at roughly 1.1 GPU-hours of the 2.1 left, but only if the diagnostics above come first.

## 4. Whose decision?

- Relaxing the cap on a K_D × level basis is a qualification-threshold change inside an exploratory redesign. Inform the owner, as Amendment 1 says.
- Dropping the trail claims is the plan's own failure branch. Inform.
- Changing the organism's sensing changes the object of study, and E3b-1 would inherit a sensing model E3a never tested. That needs the owner before any build.

The claim to attack says the redesign "should be" compression. I disagree. The evidence singles out a cap built on a misread gain curve, and a quarter-hour of GPU on the seeds settles whether anything on the sensing side is needed at all.