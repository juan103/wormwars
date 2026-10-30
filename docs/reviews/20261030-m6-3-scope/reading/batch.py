"""For each (key, Europe PMC query) in SOURCES: metadata + abstract (Europe PMC search), then the open-access full text
(Europe PMC fullTextXML, else NCBI E-utilities efetch for the PMC open-access subset), as <key>.txt. Writes
sources.json with what was obtained. Public APIs only; nothing behind a bot check."""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

here = Path(__file__).parent
SOURCES = {
    "mellem2008": "DOI:10.1038/nn.2131",
    "lockery2009corr": "DOI:10.1038/nn0409-365",
    "lockery2009nv": "DOI:10.1038/nn0409-377",
    "nicoletti2019": "DOI:10.1371/journal.pone.0218738",
    "sordillo2021": 'TITLE:"Behavioral control by depolarized and hyperpolarized states of an integrating neuron"',
    "roberts2016": 'TITLE:"A stochastic neuronal model predicts random search behaviors"',
    "wang2020": 'TITLE:"Flexible motor sequence generation during stereotyped escape responses"',
    "kato2015": "DOI:10.1016/j.cell.2015.09.034",
    "kaplan2020": "DOI:10.1016/j.neuron.2019.10.037",
    "gordus2015": "DOI:10.1016/j.cell.2015.02.018",
    "ji2019": 'TITLE:"Corollary discharge promotes a sustained motor state in a neural circuit for navigation"',
    "ji2021": 'TITLE:"A neural circuit for flexible control of persistent behavioral states"',
    "dunn2025": "DOI:10.1016/j.cub.2025.10.018",
    "kramer2026": "DOI:10.1038/s41593-026-02257-5",
    "lopezcruz2019": "DOI:10.1016/j.neuron.2019.01.053",
    "levy2020": 'TITLE:"An Adaptive-Threshold Mechanism for Odor Sensation and Animal Navigation"',
    "kato2014": "DOI:10.1016/j.neuron.2013.11.020",
    "larsch2015": 'TITLE:"A circuit for gradient climbing in C. elegans chemotaxis"',
    "luo2014": "DOI:10.1016/j.neuron.2014.05.010",
    "flavell2013": "DOI:10.1016/j.cell.2013.08.001",
    "atanas2023": 'TITLE:"Brain-wide representations of behavior spanning multiple timescales and states"',
    "hendricks2012": "DOI:10.1038/nature11081",
    "liu2018steer": "DOI:10.1016/j.neuron.2017.12.003",
    "ouellette2018": "DOI:10.1523/ENEURO.0121-18.2018",
    "uzel2022": 'TITLE:"A set of hub neurons and non-local connectivity features support global brain dynamics"',
    "randi2023": 'TITLE:"Neural signal propagation atlas of Caenorhabditis elegans"',
    "witvliet2021": 'TITLE:"Connectomes across development reveal principles of brain maturation"',
    "towlson2013": 'TITLE:"The rich club of the C. elegans neuronal connectome"',
    "kunertgraf2017": 'TITLE:"Multistability and Long-Timescale Transients Encoded by Network Structure"',
    "izquierdo2013": 'TITLE:"Connecting a Connectome to Behavior: An Ensemble of Neuroanatomical Models"',
    "yeon2018": "DOI:10.1371/journal.pbio.2004929",
    "huo2024": 'TITLE:"Hierarchical behavior control by a single class of interneurons"',
    "shen2016": 'TITLE:"An extrasynaptic GABAergic signal modulates a pattern of forward movement"',
    "chen2024": 'TITLE:"CKR-1 orchestrates two motor states from a single motoneuron"',
    "alkema2005": 'TITLE:"Tyramine Functions independently of octopamine"',
    "goodman1998": 'TITLE:"Active currents regulate sensitivity and dynamic range in C. elegans neurons"',
    "liu2018awa": "DOI:10.1016/j.cell.2018.08.018",
    "bhattacharya2019": 'TITLE:"Plasticity of the Electrical Connectome of C. elegans"',
    "gray2005": 'TITLE:"A circuit for navigation in Caenorhabditis elegans"',
}


def get(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "wormwars-literature-check/1.0 (research; Europe PMC API)"})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")


def to_text(xml):
    root = ET.fromstring(xml)
    if "does not allow downloading" in xml:
        return None
    body = root.find(".//body")
    if body is None:
        return None
    out = []
    for el in root.iter():
        if el.tag in ("p", "title"):
            t = " ".join("".join(el.itertext()).split())
            if t:
                out.append(("## " if el.tag == "title" else "") + t)
    return "\n".join(out)


def main():
    rec = json.loads((here / "sources.json").read_text(encoding="utf-8")) if (here / "sources.json").exists() else {}
    for key, q in SOURCES.items():
        if key in rec and rec[key].get("done"):
            continue
        url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?" +
               urllib.parse.urlencode({"query": q, "resultType": "core", "format": "json", "pageSize": 1}))
        r = {"query": q, "searched": time.strftime("%Y-%m-%d")}
        try:
            res = json.loads(get(url))["resultList"]["result"]
        except Exception as e:  # noqa: BLE001
            r["error"] = repr(e)
            rec[key] = r
            continue
        if not res:
            r["found"] = False
            rec[key] = r | {"done": True}
            continue
        x = res[0]
        r.update(found=True, title=x.get("title"), authors=x.get("authorString"), year=x.get("pubYear"),
                 journal=(x.get("journalInfo") or {}).get("journal", {}).get("title"), doi=x.get("doi"),
                 pmid=x.get("pmid"), pmcid=x.get("pmcid"), oa=x.get("isOpenAccess"),
                 abstract=x.get("abstractText"), full_text=None)
        if x.get("pmcid"):
            for src, u in (("europepmc", f"https://www.ebi.ac.uk/europepmc/webservices/rest/{x['pmcid']}/fullTextXML"),
                           ("ncbi-efetch", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id="
                            + x["pmcid"].replace("PMC", ""))):
                try:
                    t = to_text(get(u))
                except Exception:  # noqa: BLE001
                    t = None
                if t and len(t) > 3000:
                    (here / f"{key}.txt").write_text(f"TITLE: {r['title']}\nSOURCE: {src} {u}\n\n{t}", encoding="utf-8")
                    r["full_text"] = src
                    break
                time.sleep(0.4)
        rec[key] = r | {"done": True}
        print(f"{key:18s} {r.get('year')} {str(r.get('pmcid')):12s} OA {r.get('oa')} full={r['full_text']} | "
              f"{(r.get('title') or '')[:70]}", flush=True)
        time.sleep(0.4)
    (here / "sources.json").write_text(json.dumps(rec, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
