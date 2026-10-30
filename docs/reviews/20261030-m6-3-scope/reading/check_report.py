"""Every double-quoted passage of 12+ characters in the report must occur, after whitespace and quote normalisation,
in one of the local texts (full texts <key>.txt or abstracts abs_<key>.txt). Quotes are paired within one list item,
table row or paragraph. Passages quoting this project's own drafts, reviews or the owner are listed in META and
skipped. Usage: py check_report.py report.md"""
import re, sys
from pathlib import Path
here = Path(__file__).parent
META = {"fix then publish", "Corrections from review", "with consultation with Fable and Astra",
        "not found in the sources checked", "outlasts its input", "the most directly relevant study checked",
        "could swamp the model's effects", "turns during forward movement unaffected", "tetramisole-paralysed",
        "seconds to hours", "No single neuron carries it", "The one study that shows it"}
def norm(t):
    for a, b in (("\u201c", '"'), ("\u201d", '"'), ("\u2019", "'"), ("\u2018", "'"), ("\u2013", "-"), ("\u2014", "-"),
                 ("\u2212", "-"), ("\u00a0", " ")):
        t = t.replace(a, b)
    return " ".join(t.split())
texts = {p.stem: norm(p.read_text(encoding="utf-8")) for p in here.glob("*.txt") if p.stem != "LOG"}
items, cur = [], []
for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
    st = line.strip()
    if not st or st.startswith(("- ", "|", "#", "**")) or re.match(r"\d+\. ", st):
        if cur: items.append(" ".join(cur))
        cur = [st] if st else []
    else:
        cur.append(st)
if cur: items.append(" ".join(cur))
items = [re.sub(r"`[^`]*`", "", norm(i)) for i in items]   # drop code spans (search strings)
ok, miss, n = 0, [], 0
for it in items:
    for q in re.findall(r'"([^"]+)"', it):
        if len(q) < 12 or q in META: continue
        n += 1
        parts = [p.strip(" .,;") for p in re.split(r"\.\.\.|\u2026", q) if p.strip(" .,;")]
        if any(all(p in t for p in parts) for t in texts.values()): ok += 1
        else: miss.append(q)
print(f"{n} quoted passages checked, {ok} found")
for q in miss: print("NOT FOUND:", q[:160])
