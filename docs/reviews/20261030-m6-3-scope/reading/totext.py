"""Europe PMC full-text XML -> plain text, one paragraph per line; usage: py totext.py PMCxxxx (reads PMCxxxx.xml)."""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

here = Path(__file__).parent
for pmc in sys.argv[1:]:
    root = ET.parse(here / f"{pmc}.xml").getroot()
    out = []
    meta = root.find(".//article-meta")
    if meta is not None:
        t = meta.find(".//article-title")
        out.append("TITLE: " + " ".join("".join(t.itertext()).split()))
        names = [" ".join("".join(n.itertext()).split()) for n in meta.findall(".//contrib/name")]
        out.append("AUTHORS: " + "; ".join(names))
        j = root.find(".//journal-title")
        y = meta.find(".//pub-date/year")
        doi = meta.find(".//article-id[@pub-id-type='doi']")
        out.append(f"JOURNAL: {''.join(j.itertext()) if j is not None else '?'} {y.text if y is not None else '?'} "
                   f"DOI {doi.text if doi is not None else '?'}")
    for el in root.iter():
        if el.tag in ("p", "title") and el.text is not None or el.tag in ("p", "title"):
            txt = " ".join("".join(el.itertext()).split())
            if txt:
                out.append(("## " if el.tag == "title" else "") + txt)
    (here / f"{pmc}.txt").write_text("\n".join(out), encoding="utf-8")
    print(pmc, len(out), "paragraphs")
