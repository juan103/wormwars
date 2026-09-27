The substantive fixes and plan amendments are resolved. I found no new code regression. **49 focused CPU tests passed**, including eight with file operations redirected to memory. Restoring the old champion re-evaluation in memory made the rigged test fail as intended.

Two nonblocking documentation corrections remain:

- [T0.md:70](D:/Claude/random/wormWars/docs/foundations/T0.md:70) still says “independent noise.” Use D066’s corrected wording about unchanged intended expectation and different realised estimates.
- [T0.md:82](D:/Claude/random/wormWars/docs/foundations/T0.md:82) and D067 overstate the historical champion check. I verified **153 matching nicknames**, but those logs contain **zero full hashes**. This establishes no detected nickname mismatch, not proof that re-evaluation never selected another genome.

T0 plan v2.1: confirmed  
item 1: accept