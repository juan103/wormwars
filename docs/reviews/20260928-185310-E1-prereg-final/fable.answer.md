# E1 pre-registration v3: final confirmation

I ran nothing: I have no shell, so no test suite and no `git show`. I read the files at HEAD (`f63cdaa`; the tracked tree is clean), D096, both earlier reviews and the smoke records. `origin/roadmap` is still at `857e0ce`, so nothing of E1 is public yet.

## 1. My three must-fix points

| # | Point | Status |
|---|---|---|
| 1 | §7: the 16:08 smoke pair | **Resolved.** `PREREGISTRATION.md:257-265` states the ids, names the basis as the session's command order, and says no record holds them. The attempt files match the numbers (52 + 1 000 worlds; 208 under `final`). |
| 2 | Tests for the same-code and clean-and-pushed guards; D095 corrected by a dated entry | **Partly resolved.** The tests exist (`tests/test_e1_script.py:205-211`, `234-244`), and D095 is intact with its correction in `DECISIONS.md:2933-2939`. The narrowed claim is still too broad (must-fix B). |
| 3 | §5: cap checks and the compute record's path | **Resolved.** Every rollout and loop has a check (`scripts/e1.py:244`, `279`, `299`, `317`, `321`, `368`, `417`, `583`), with final checks at `428` and `616`. `compute-record.json` matches no pattern in `.gitignore`, and neither does `gate_events.npz`. |

## 2. New defects

Nothing I found would invalidate a result. Two registered statements are false as written.

**A. The crash case (`PREREGISTRATION.md:217-218`).**
- The text says a gate that "stops without a result, or hits the cap" keeps every completed arm's counts and events.
- The code keeps them only on a cap hit: `cmd_gate` catches only `CapReached` (`scripts/e1.py:599-603`).
- Counts and events stay in memory until `620-621`, so any other failure loses every completed arm.
- The third fixed outcome wording names the cap, so a crash has no registered wording.
- **Fix:** write each arm as it completes, or limit the sentence to the cap and give the crash its own wording.

**B. The guard-test claim (`PREREGISTRATION.md:30-32`, `205-207`).**
- The text says the guards have refusal tests "except the live git fetch and the CUDA preflight", and that the guarded smoke run "checks the guards that have no unit test".
- No test calls `cmd_pilot` or `cmd_gate`, so these have none:
  - the once-only refusals (`scripts/e1.py:394-395`, `555-556`);
  - the committed-freeze check (`557-561`);
  - the pilot's zero-sample refusal (`289-290`);
  - the two `except CapReached` branches (only `not_completed` is tested directly).
- The committed-freeze check is skipped under `--smoke`, so the guarded smoke run cannot exercise it. It first runs at the formal gate.
- All of these refuse before the start marker, so the risk is to the claim, not the data. It is the same kind of error D096 just corrected in D095.
- **Fix:** list the untested guards in both sentences, or add the tests.

## 3. Not blocking

- **A test deletes real files.** `test_smoke_mode_rebinds_every_path_and_id` (`tests/test_e1_script.py:270-281`) calls `use_smoke("gate")`, which unlinks files in `runs/e1-smoke/`. The 16:46:24 smoke gate completed with 256 worlds, yet its `gate.json`, marker and events are gone; the suite run is the likely cause.
- **§7's evidence is local.** The attempt files are git-ignored, and "later smoke runs record ids 0-15" (`PREREGISTRATION.md:263`) now has no surviving file: the remaining smoke freeze records ids 0-7. Commit copies of the records the disclosure cites. The index 1 000 offset keeps this from affecting validity.
- **A cap already spent before the gate starts** raises an uncaught `CapReached` at `scripts/e1.py:567`, so no `gate.json` carries the fixed wording.
- **The last smoke run predates v3's commit** by seven minutes, on a dirty tree and without `--guarded`. The planned guarded run covers this. State what happens if it fails: the fix is committed with a dated note, and the later commit binds.

E1 pre-registration: revise (must-fix: limit "completed arms are kept" to the cap or write arms incrementally, with a wording for a crash; complete the list of untested guards in lines 30-32 and 205-207, or add their tests).