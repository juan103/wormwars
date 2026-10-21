"""M2 census: a positive record of batch 7's regeneration check (Fable, results round 1).

census.py's batch7_graph() regenerates each core-frozen and hub-frozen shuffle with batch 7's own rewiring and raises
Batch7Mismatch unless its edge counts, triangle counts, reciprocal pairs, kept fractions and accepted swaps equal
batch7.json's. A pass left no file, so this reruns the same function (deterministic, the code of D355) and records,
for each arm, the values it matched. No simulation of brains.

    py scripts/memory_m2/batch7_record.py
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import census  # noqa: E402

out = []
book = json.load(open(census.SPIKES / "batch7.json"))
for arm in ("core-frozen-shuffle", "hub-frozen-shuffle"):
    for k in range(3):
        try:
            census.batch7_graph(arm, k)
            ref = book[f"N2/{arm}{k}/7100"]
            out.append({"arm": f"{arm}{k}", "matches_batch7": True,
                        "matched": {"structure": ref["structure"], "kept_all": ref["kept_all"],
                                    "kept_core_internal": ref["kept_core_internal"], "accepted": ref["info"]["accepted"]}})
        except census.Batch7Mismatch as err:
            out.append({"arm": f"{arm}{k}", "matches_batch7": False, "reason": str(err)})
        print(out[-1]["arm"], out[-1]["matches_batch7"], flush=True)
json.dump({"arms": out, "all_match": all(x["matches_batch7"] for x in out)},
          open(census.OUT / "batch7_check.json", "w"), indent=1)
