"""Diagnostic (output runs/m5-pilot-diag-log.txt): is the smoke's float64 difference a batch-composition effect of
the classifier, with the float32 hold identical? Genome 319 of SH-2011100 d0 T, replayed in a batch of two ([118, 319]) and in its original
chunk (256..383)."""
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import torch

os.environ["MEMORY_M5P_OUT"] = tempfile.mkdtemp(prefix="m5p-diag-")
sys.path.insert(0, str(Path(__file__).resolve().parent))
import m5_pilot as MP  # noqa: E402

m4e = MP.m4e
verified = m4e.verify_run()
v = verified[0]
rec = MP.panel_record(v, "T")
g = MP.panel_genome(v, "T")
cfg = v["cfg"]
out = {}
t0 = time.time()
pair = MP.P.probe_states(g.select([118, 319]), cfg)
chunk = MP.P.probe_states(g.select(list(range(256, 384))), cfg)
k = 319 - 256
out["end_equal"] = bool(torch.equal(pair["end"][1], chunk["end"][k]))
out["tail_equal"] = bool((pair["tail"][1] == chunk["tail"][k]).all())
out["y_equal"] = bool((pair["y"][1] == chunk["y"][k]).all())
print("hold:", out, f"{time.time() - t0:.0f} s", flush=True)
want = MP.recorded(rec, [319], "first")[0]
sub = {x: chunk[x] for x in ("end", "cur", "y", "tail")}
recs, _ = MP.P.full_classify(g.select(list(range(256, 384))), cfg, sub, compact=True)
got_chunk = MP.fields([recs[k]], MP.FIRST_FIELDS)[0]
sub2 = {x: pair[x] for x in ("end", "cur", "y", "tail")}
recs2, _ = MP.P.full_classify(g.select([118, 319]), cfg, sub2, compact=True)
got_pair = MP.fields([recs2[1]], MP.FIRST_FIELDS)[0]
out["chunk_equals_record"] = json.dumps(got_chunk) == json.dumps(want)
out["pair_equals_record"] = json.dumps(got_pair) == json.dumps(want)
out["record"], out["chunk"], out["pair"] = want, got_chunk, got_pair
print(json.dumps(out, indent=1), f"{time.time() - t0:.0f} s", flush=True)
