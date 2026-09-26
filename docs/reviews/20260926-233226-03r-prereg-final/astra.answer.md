At `69450c2`, the preflight disclosure and binding boundary are resolved.

The reporting fix remains incomplete: [report.py:180](/D:/Claude/random/wormWars/wormwars/exp03/report.py:180) drops ensembles with 0–1 valid graphs. If all ensembles have fewer than two, [line 141](/D:/Claude/random/wormWars/wormwars/exp03/report.py:141) newly misreports valid N2 as invalid. I reproduced both. Preserve those rows and available quantities; explicitly mark undefined statistics/gates unavailable.

33 tests passed; three filesystem-writing tests were excluded. **Not ready to bind.**