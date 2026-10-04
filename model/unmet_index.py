"""Compute per-theme metrics and the Unmet Need Index from threads_coded.parquet + doc_topics.parquet.
Usage: .venv/bin/python model/unmet_index.py --topics data/processed/topics_all/doc_topics.parquet
Output: data/processed/theme_metrics.csv (one row per topic), lifecycle_metrics.csv (one row per lifecycle stage), recurrence.parquet
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data" / "processed"
ap = argparse.ArgumentParser(); ap.add_argument("--topics", required=True); ap.add_argument("--embeddings"); ap.add_argument("--need-clusters", default=None); a = ap.parse_args()
C = pd.read_parquet(OUT / "threads_coded.parquet"); D = pd.read_parquet(a.topics)[["thread_id", "topic"]]
M = C.merge(D, on="thread_id", how="left")
if a.need_clusters:
    NC = pd.read_parquet(a.need_clusters)[["thread_id", "need_cluster"]]; M = M.merge(NC, on="thread_id", how="left")
M["unresolved"] = M.resolution_final.isin(["unresolved", "no_reply", "partially"])
M["is_need"] = M.pain_point.notna() & M.post_type.isin(["question", "bug", "feature_request", "discussion"])
M["sev_w"] = M.severity.map({"blocker": 3, "major": 2, "minor": 1, "none": 0}).fillna(0)
M["qidx"] = M.quarter.rank(method="dense")

def rank01(s): return (s.rank(pct=True)).fillna(0)
def summarize(group_col, frame):
    g = frame[frame.is_need].groupby(group_col)
    S = pd.DataFrame({"n_need_threads": g.size(), "share": g.size() / frame.is_need.sum(),
                      "unresolved_rate": g.unresolved.mean(), "mean_severity": g.sev_w.mean(),
                      "blocker_share": g.severity.apply(lambda s: (s == "blocker").mean()),
                      "multi_site_share": g.multi_site_context.apply(lambda s: s.fillna(False).astype(bool).mean()),
                      "harmonization_share": g.harmonization_context.apply(lambda s: s.fillna(False).astype(bool).mean()),
                      "forums_share": g.source.apply(lambda s: (s == "forums").mean()),
                      "median_hrs_first_reply": g.hours_to_first_reply.median(),
                      "workaround_share": g.workaround_present.apply(lambda s: s.fillna(False).astype(bool).mean())})
    # trend: slope of quarterly counts normalized by mean
    def slope(sub):
        q = sub.groupby("qidx").size().reindex(range(1, int(frame.qidx.max()) + 1), fill_value=0)
        if q.mean() == 0: return 0.0
        return float(np.polyfit(q.index, q.values / q.mean(), 1)[0])
    S["trend_slope"] = g.apply(slope)
    S["unmet_need_index"] = (rank01(S.n_need_threads) * 0.35 + rank01(S.unresolved_rate) * 0.25 + rank01(S.mean_severity) * 0.2
                             + rank01(S.trend_slope.clip(lower=0)) * 0.1 + rank01(S.n_need_threads * S.unresolved_rate) * 0.1)
    return S.sort_values("unmet_need_index", ascending=False)

theme = summarize("topic", M[M.topic.notna()]); theme.to_csv(OUT / "theme_metrics.csv")
if a.need_clusters:
    need = summarize("need_cluster", M[M.need_cluster.notna() & (M.need_cluster >= 0)]); need.to_csv(OUT / "need_metrics.csv"); print("\nneed clusters:"); print(need.round(2).to_string())
L = M.assign(lifecycle_stage=M.lifecycle_stage.fillna("").str.split(",")).explode("lifecycle_stage")
L = L[L.lifecycle_stage.str.len() > 0]; life = summarize("lifecycle_stage", L); life.to_csv(OUT / "lifecycle_metrics.csv")
print("themes:", len(theme)); print(theme.head(15).round(2).to_string()); print("\nlifecycle:"); print(life.round(2).to_string())

# recurrence: near-duplicate need statements (same question asked repeatedly) via embedding similarity of pain_point sentences
try:
    from sentence_transformers import SentenceTransformer
    need = M[M.is_need & M.pain_point.notna()].reset_index(drop=True)
    emb = SentenceTransformer("BAAI/bge-small-en-v1.5").encode(need.pain_point.tolist(), normalize_embeddings=True, batch_size=64)
    sim = emb @ emb.T; np.fill_diagonal(sim, 0)
    need["n_near_duplicates"] = (sim > 0.82).sum(1); need["max_sim"] = sim.max(1)
    need[["thread_id", "topic", "pain_point", "n_near_duplicates", "max_sim"]].to_parquet(OUT / "recurrence.parquet", index=False)
    rec = need.groupby("topic").n_near_duplicates.mean().rename("mean_near_dups"); theme = theme.join(rec); theme.to_csv(OUT / "theme_metrics.csv")
    print("\nmost-repeated needs:"); print(need.sort_values("n_near_duplicates", ascending=False).head(10)[["n_near_duplicates", "pain_point"]].to_string())
except Exception as e: print("recurrence skipped:", e)
