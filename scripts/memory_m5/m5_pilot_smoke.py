"""Smoke of M5's pilot on M4e's real records, before the pilot runs (output runs/m5-pilot-smoke-log.txt): replays of
T and K genomes reproduce every recorded classifier output at 2000 and 22,000 ticks under the registered check,
including a batch of one (with its companion); one genome reproduces bit for bit in its original chunk; one Rr block
passes its checks; the panel records validate."""
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ["MEMORY_M5P_OUT"] = tempfile.mkdtemp(prefix="m5p-smoke-")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import m5_pilot as MP  # noqa: E402

m4e = MP.m4e
t0 = time.time()
verified = m4e.verify_run()
print(f"verify_run {time.time() - t0:.0f} s", flush=True)
v = verified[0]
con, B1, B2, chain = MP.rr_con(v)
print("Rr chain", chain, MP.similarity(B1, MP.m4d.n2_block()), flush=True)
for arm in ("T", "K"):
    rec = MP.panel_record(v, arm)  # validated
    targets = MP.longer_targets(rec)
    for ids in (targets[:2], targets[2:3]):  # a batch of two, and a batch of one
        if not ids:
            continue
        g = MP.panel_genome(v, arm)
        t0 = time.time()
        gs, run, r1, run_ids = MP.replay(g, v["cfg"], ids)
        end, y = run["end"], run["y"][:, :301]
        print("state chunks", MP.state_check(g, v["cfg"], ids, run), flush=True)
        MP.check_replay(f"{arm} 2000", MP.fields(r1, MP.FIRST_FIELDS), MP.recorded(rec, ids, "first"))
        _, r22 = MP.extend(gs, v["cfg"], end, y, m4e.EXTRA)
        MP.check_replay(f"{arm} 22000", MP.fields(r22[:len(ids)], MP.SECOND_FIELDS), MP.recorded(rec, ids, "second"))
        print(f"{arm}: ids {ids} (run as {run_ids}) reproduce every recorded output at 2000 and 22,000 "
              f"in {time.time() - t0:.0f} s", flush=True)
    pool = MP.audit_pool([rec])
    part = [i for _, i in pool[:6]]
    t0 = time.time()
    gs, run, r1, run_ids = MP.replay(g, v["cfg"], part)
    end, y = run["end"], run["y"][:, :301]
    MP.check_replay(f"{arm} audit 2000", MP.fields(r1, MP.FIRST_FIELDS), MP.recorded(rec, part, "first"))
    _, r22 = MP.extend(gs, v["cfg"], end, y, m4e.EXTRA)
    print(f"{arm}: 6 fading reproduce at 2000; at 22,000 {[x['class'] for x in r22]} in {time.time() - t0:.0f} s",
          flush=True)
rec = MP.panel_record(v, "T")
print("composition", MP.composition_check(MP.panel_genome(v, "T"), v["cfg"], rec, 319), flush=True)
print("smoke ok")
