"""Merge subagent coding outputs (data/processed/coding_out/*.jsonl) into threads_coded.parquet + .csv, with validation."""
import json, sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data" / "processed"; CO = OUT / "coding_out"
ALLOWED = {"post_type": {"question","bug","feature_request","announcement","discussion","job_or_event","dev_task","other"},
           "severity": {"blocker","major","minor","none"}, "resolution_status": {"resolved","partially","unresolved","unclear","no_reply"},
           "confidence": {"high","medium","low"}}
rows, bad = [], 0
for f in sorted(CO.glob("*.jsonl")):
    for line in open(f):
        line = line.strip()
        if not line: continue
        try: d = json.loads(line)
        except json.JSONDecodeError: bad += 1; continue
        for k, allowed in ALLOWED.items():
            if d.get(k) not in allowed: d[k] = None
        for k in ("lifecycle_stage", "tools"):
            if not isinstance(d.get(k), list): d[k] = []
        rows.append(d)
C = pd.DataFrame(rows).drop_duplicates("thread_id", keep="last")
T = pd.read_parquet(OUT / "threads.parquet")
M = T.merge(C, on="thread_id", how="left", indicator=True)
print(f"coded rows: {len(C)}  unparseable lines: {bad}  threads coded: {(M._merge=='both').sum()} / {len(T)}")
# resolution_final: anchor on metadata. No reply from anyone else -> no_reply (unless coder saw a self-solve -> resolved_self); otherwise coder's label.
def _final(r):
    if r.n_replies_by_others == 0:
        return "resolved_self" if r.resolution_status == "resolved" else "no_reply"
    return r.resolution_status if isinstance(r.resolution_status, str) else "unclear"
M["resolution_final"] = M.apply(_final, axis=1)
M["unmet"] = M.resolution_final.isin(["no_reply", "unresolved", "partially"])
M["lifecycle_stage"] = M.lifecycle_stage.apply(lambda v: ",".join(v) if isinstance(v, list) else None)
M["tools"] = M.tools.apply(lambda v: ",".join(v) if isinstance(v, list) else None)
M.drop(columns=["_merge"]).to_parquet(OUT / "threads_coded.parquet", index=False)
M.drop(columns=["_merge", "op_text"]).to_csv(OUT / "threads_coded.csv", index=False)
print(M.post_type.value_counts(dropna=False).to_string()); print(M.resolution_final.value_counts(dropna=False).to_string())
