"""Cluster coded pain-point sentences into a needs taxonomy (bottom-up), independent of the raw-post topic model.
Input: data/processed/threads_coded.parquet (pain_point, job_to_be_done). Output: need_clusters.parquet, need_clusters_summary.json (for LLM labeling).
Usage: .venv/bin/python model/need_clusters.py [--min-size 4]
"""
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data" / "processed"
ap = argparse.ArgumentParser(); ap.add_argument("--min-size", type=int, default=4); ap.add_argument("--n-clusters", type=int, default=30); a = ap.parse_args()
C = pd.read_parquet(OUT / "threads_coded.parquet")
N = C[C.pain_point.notna() & C.post_type.isin(["question", "bug", "feature_request", "discussion"])].copy().reset_index(drop=True)
N["need_text"] = N.pain_point.fillna("") + " " + N.job_to_be_done.fillna("")
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
emb = model.encode(N.need_text.tolist(), normalize_embeddings=True, batch_size=64, show_progress_bar=False)
cl = AgglomerativeClustering(n_clusters=a.n_clusters, linkage="ward").fit(emb)   # ward on unit vectors ~ cosine geometry, full coverage
N["need_cluster"] = cl.labels_
sizes = N.need_cluster.value_counts(); small = sizes[sizes < a.min_size].index
N.loc[N.need_cluster.isin(small), "need_cluster"] = -1
# rank clusters by size, relabel 0..k
order = {c: i for i, c in enumerate(N[N.need_cluster >= 0].need_cluster.value_counts().index)}; N["need_cluster"] = N.need_cluster.map(lambda c: order.get(c, -1))
N.to_parquet(OUT / "need_clusters.parquet", index=False)
summ = []
for c, g in N[N.need_cluster >= 0].groupby("need_cluster"):
    cen = emb[g.index].mean(0); sims = emb[g.index] @ cen; rep = g.iloc[np.argsort(-sims)[:8]]
    summ.append({"cluster": int(c), "n": len(g), "unresolved_rate": round(float(g.resolution_final.isin(["unresolved", "no_reply", "partially"]).mean()), 2),
                 "blocker_or_major": round(float(g.severity.isin(["blocker", "major"]).mean()), 2), "multi_site_share": round(float(g.multi_site_context.fillna(False).astype(bool).mean()), 2),
                 "harmonization_share": round(float(g.harmonization_context.fillna(False).astype(bool).mean()), 2),
                 "categories": g.repo_or_category.value_counts().head(3).to_dict(), "quarters": g.quarter.value_counts().sort_index().to_dict(),
                 "lifecycle": pd.Series(",".join(g.lifecycle_stage.dropna()).split(",")).value_counts().head(3).to_dict(),
                 "representative_pain_points": rep.pain_point.tolist(), "representative_jobs": rep.job_to_be_done.dropna().tolist()[:5],
                 "evidence_quotes": rep.evidence_quote.dropna().tolist()[:4], "thread_ids": g.thread_id.tolist()})
json.dump(summ, open(OUT / "need_clusters_summary.json", "w"), indent=1)
print(f"need statements: {len(N)}  clusters: {len(summ)}  unclustered: {(N.need_cluster == -1).sum()}")
for s in summ[:25]: print(f"[{s['cluster']:2d}] n={s['n']:3d} unres={s['unresolved_rate']:.2f}  {s['representative_pain_points'][0][:110]}")
