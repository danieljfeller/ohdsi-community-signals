"""Build compact thread digests and split into JSONL batches for subagent coding.
Digest = title + opening post (<= 350 words) + up to 4 replies (<= 60 words each, prefer non-author replies and the last reply).
Usage: .venv/bin/python model/prepare_batches.py [--batch-size 45] [--external-only]
"""
import argparse, json
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data" / "processed"; BD = OUT / "coding_batches"; BD.mkdir(exist_ok=True)
ap = argparse.ArgumentParser(); ap.add_argument("--batch-size", type=int, default=45); ap.add_argument("--external-only", action="store_true"); a = ap.parse_args()
T = pd.read_parquet(OUT / "threads.parquet"); P = pd.read_parquet(OUT / "posts.parquet")
if a.external_only: T = T[(T.source != "github") | (~T.author_trust_level.isin(["MEMBER", "OWNER", "COLLABORATOR"]))]
T = T[T.op_words >= 3].copy()
def trunc(s, n): w = (s or "").split(); return " ".join(w[:n]) + (" ..." if len(w) > n else "")
digests = []
for t in T.itertuples():
    reps = P[(P.thread_id == t.thread_id) & (P.post_number > 1)].sort_values("post_number")
    chosen = []
    if len(reps):
        others = reps[~reps.is_op_author]
        chosen = list(others.head(2).itertuples()) + ([reps.iloc[-1:].itertuples().__next__()] if True else [])
        seen = set(); chosen = [c for c in chosen if not (c.post_id in seen or seen.add(c.post_id))][:4]
    digests.append({"thread_id": t.thread_id, "source": t.source, "where": t.repo_or_category, "title": t.title, "created": str(t.created_at)[:10],
                    "n_replies": int(t.n_replies), "n_replies_by_others": int(t.n_replies_by_others), "state": t.state,
                    "opening_post": trunc(t.op_text, 350),
                    "replies": [{"by": "original_poster" if c.is_op_author else "someone_else", "text": trunc(c.text, 60)} for c in chosen]})
for f in BD.glob("batch_*.jsonl"): f.unlink()
for i in range(0, len(digests), a.batch_size):
    with open(BD / f"batch_{i // a.batch_size:04d}.jsonl", "w") as f:
        for d in digests[i:i + a.batch_size]: f.write(json.dumps(d, ensure_ascii=False) + "\n")
n = len(list(BD.glob("batch_*.jsonl"))); print(f"{len(digests)} digests -> {n} batches of {a.batch_size}")
import statistics; print("median digest chars:", statistics.median(len(json.dumps(d)) for d in digests))
