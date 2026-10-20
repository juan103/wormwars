"""M2 pilot: per-genome details behind the results write-up (written after the data; descriptive only).

Reads the pilot's committed stage records in runs/memory-m2/ (classes__*, r3__*, r5__*) and writes
runs/memory-m2/describe.json: the tick-300 classification per graph, the unresolved genomes, the "separate states"
genomes outside M1's cohort, R3's discordant representatives, R5's switch pattern along the nine starts, and the
fading genomes whose |dy(300)| passes 0.1 a, and the unresolved genomes' numerator shares against the
graph's whole eligible numerator as well as the pilot's. Nothing here changes a class or a check.
"""
import collections
import json
import pathlib
import statistics

OUT = pathlib.Path("runs/memory-m2")
GRAPHS = ["N2", "SH-recip-2050039", "SH-class-2030099", "SH-2010013", "SH-mirror-2040045"]


def main():
    out = {"graphs": {}}
    for gname in GRAPHS:
        recs = json.loads((OUT / f"classes__{gname}.json").read_text())["genomes"]
        r3 = json.loads((OUT / f"r3__{gname}.json").read_text())
        r5 = json.loads((OUT / f"r5__{gname}.json").read_text())
        g = {
            "genomes": len(recs),
            "unresolved_at_300": sum(r["class300"] == "unresolved" for r in recs),
            "reasons_at_300": dict(collections.Counter(r["reason300"] for r in recs if r["class300"] == "unresolved")),
            "class_changes_300_to_2000": dict(collections.Counter(
                f'{r["class300"]} ({r["reason300"]}) -> {r["class"]}' for r in recs if r["class300"] != r["class"])),
            "unresolved": [{"genome": r["genome"], "groups": r["groups"], "reason": r["reason"], "a": r["a"],
                            "d30": r["d30"], "d300": r["d300"],
                            "dist_end_root": [h["dist_end_root"] for h in r["histories"]],
                            "sigma_min": [h["sigma_min"] for h in r["histories"]],
                            "reach": [h["reach"] for h in r["histories"]],
                            "oscillation": [None if o is None else {k: o[k] for k in ("period_substeps", "range_late",
                                                                                      "range_ref", "verdict")}
                                            for o in r["oscillation"]]}
                           for r in recs if r["class"] == "unresolved"],
            "separate_outside_cohort": [{"genome": r["genome"], "groups": r["groups"], "settled300": r["settled300"],
                                         "class300": r["class300"], "reason300": r["reason300"]}
                                        for r in recs if r["class"] == "separate states" and "cohort" not in r["groups"]],
            "fading_dy300_above_remaining": [{"genome": r["genome"], "groups": r["groups"]} for r in recs
                                             if r.get("fading_modes")
                                             and r["fading_modes"]["float32_dy300"] > 0.1 * r["a"]],
        }
        # summary.json's numerator shares are of the pilot genomes' summed |dy(30)|; the carriers' share of the graph's
        # whole eligible numerator (sample.json) gives that numerator, so the shares can be restated against it
        sample = json.loads((OUT / "sample.json").read_text())[gname]
        pilot30 = sum(r["d30"] for r in recs)
        eligible30 = sum(r["d30"] for r in recs if "carriers" in r["groups"]) / sample["carriers_numerator_frac"]
        g["pilot_share_of_eligible_numerator30"] = pilot30 / eligible30
        g["unresolved_share_of_eligible_numerator30"] = sum(r["d30"] for r in recs if r["class"] == "unresolved") / eligible30
        g["unresolved_share_of_pilot_numerator30"] = {r["genome"]: r["d30"] / pilot30 for r in recs
                                                      if r["class"] == "unresolved"}
        # every pilot genome meeting the grower criterion (grows over 10 ticks, radius below 1), whatever its group
        # (Astra, results round 1: a cohort member meets it and has separate states)
        g["grower_criterion_by_class"] = dict(collections.Counter(
            f'{r["class"]} ({"in" if "growers" in r["groups"] else "not in"} the growers group)'
            for r in recs if r["grow10"] and r["midpoint_rho"] < 1))
        fm = [(r["genome"], r["fading_modes"]) for r in recs if r.get("fading_modes")]
        g["fading_slope_differences_above_1e-3"] = [
            {"genome": k, "predicted": m["predicted_slope"], "observed": m["observed_slope"]} for k, m in fm
            if m["predicted_slope"] is not None and m["observed_slope"] is not None
            and abs(m["predicted_slope"] - m["observed_slope"]) > 1e-3]
        g["stationary_stalls_dy2000"] = [m["float32_stall_dy2000"] for k, m in fm if m["stall_stationary"]]
        g["root_distance_300_and_2000_unresolved"] = {
            r["genome"]: {"tick300": [h["dist_end_root"] for h in r["histories300"]],
                          "tick2000": [h["dist_end_root"] for h in r["histories"]]}
            for r in recs if r["class"] == "unresolved"}
        disc = []
        for var, vv in r3["variants"].items():
            for i, gen in enumerate(r3["representatives"]):
                sr = vv["same_root"][i]
                if vv["classes"][i] != r3["main_classes"][i] or (isinstance(sr, list) and not all(sr)):
                    disc.append({"variant": var, "genome": gen, "main": r3["main_classes"][i],
                                 "variant_class": vv["classes"][i], "variant_reason": vv["reasons"][i],
                                 "same_root": sr})
        g["r3_representatives"] = len(r3["representatives"])
        g["r3_discordant_or_root_changed"] = disc
        g["r5_switches"] = dict(collections.Counter(
            f'{x["class"]}: {x["distinct_stable_roots"]} roots, '
            f'{sum(a != b for a, b in zip(x["root_of_start"], x["root_of_start"][1:]))} switches, '
            f'{x["unresolved_starts"]} unresolved starts' for x in r5["genomes"]))
        g["seconds"] = {"classify": json.loads((OUT / f"classes__{gname}.json").read_text())["seconds"],
                        "r3": r3["seconds"], "r5": r5["seconds"]}
        out["graphs"][gname] = g
    stalls = [x for g in out["graphs"].values() for x in g.pop("stationary_stalls_dy2000")]
    out["stationary_stalls"] = {"genomes": len(stalls), "median_dy2000": statistics.median(stalls)}
    (OUT / "describe.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
