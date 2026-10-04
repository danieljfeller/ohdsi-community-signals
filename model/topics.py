"""BERTopic landscape model over opening posts (title + op_text), with dynamic topics by quarter and a hierarchy.

Usage: .venv/bin/python model/topics.py [--source forums|github|all] [--min-topic-size N]
Outputs under data/processed/topics_<source>/: doc_topics.parquet, topic_info.csv, topics_over_time.csv, hierarchy.csv, embeddings.npy
"""
import argparse, re, json
from pathlib import Path
import numpy as np, pandas as pd
from sentence_transformers import SentenceTransformer
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS
from umap import UMAP
from hdbscan import HDBSCAN

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "data" / "processed"
ap = argparse.ArgumentParser(); ap.add_argument("--source", default="all"); ap.add_argument("--min-topic-size", type=int, default=8)
ap.add_argument("--external-only", action="store_true", help="GitHub: keep only non-member authored issues")
ap.add_argument("--substantive-only", action="store_true", help="keep only threads coded as question/bug/feature_request/discussion")
args = ap.parse_args()

T = pd.read_parquet(OUT / "threads.parquet")
if args.source != "all": T = T[T.source == args.source]
if args.external_only:
    T = T[(T.source != "github") | (~T.author_trust_level.isin(["MEMBER", "OWNER", "COLLABORATOR"]))]
if args.substantive_only:
    Cc = pd.read_parquet(OUT / "threads_coded.parquet")[["thread_id", "post_type"]]
    T = T.merge(Cc, on="thread_id", how="inner"); T = T[T.post_type.isin(["question", "bug", "feature_request", "discussion"])]
T = T[~T.get("author_is_bot", pd.Series(False, index=T.index)).fillna(False).astype(bool)]
T = T.copy(); T["doc"] = (T.title.fillna("") + ". " + T.op_text.fillna("")).str.slice(0, 4000)
T = T[T.doc.str.split().str.len() >= 4].reset_index(drop=True)
print(f"documents: {len(T)}  ({T.source.value_counts().to_dict()})")

# OHDSI-specific stopwords are applied to topic WORDS only (c-TF-IDF), never to the embedding input.
domain_stop = {"ohdsi", "omop", "cdm", "like", "using", "use", "used", "just", "know", "want", "need", "thanks", "thank", "hi", "hello",
               "code", "image", "https", "http", "com", "org", "www", "github", "issue", "error", "does", "doesn", "did", "don", "ve", "ll",
               "able", "way", "think", "looks", "look", "anyone", "help", "question", "problem", "work", "working", "works", "trying", "tried", "try",
               "link", "src", "alt", "img", "png", "jpg", "html", "sup", "reprex", "tidyverse", "attachments", "assets", "user", "io", "js", "width", "height", "raw", "tabs", "mock"}
stop = list(ENGLISH_STOP_WORDS | domain_stop)

emb_path = OUT / f"embeddings_{args.source}{'_ext' if args.external_only else ''}{'_subst' if args.substantive_only else ''}.npy"
model = SentenceTransformer("BAAI/bge-small-en-v1.5")
if emb_path.exists() and np.load(emb_path).shape[0] == len(T): emb = np.load(emb_path)
else:
    emb = model.encode(T.doc.tolist(), batch_size=64, show_progress_bar=True, normalize_embeddings=True); np.save(emb_path, emb)

topic_model = BERTopic(
    embedding_model=model,
    umap_model=UMAP(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=42),
    hdbscan_model=HDBSCAN(min_cluster_size=args.min_topic_size, min_samples=5, metric="euclidean", cluster_selection_method="eom", prediction_data=True),
    vectorizer_model=CountVectorizer(stop_words=stop, ngram_range=(1, 2), min_df=3, token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z_\-]{2,}\b"),
    ctfidf_model=ClassTfidfTransformer(reduce_frequent_words=True),
    calculate_probabilities=False, verbose=True)
topics, _ = topic_model.fit_transform(T.doc.tolist(), emb)
# reduce outliers by embedding similarity so fewer docs land in -1
new_topics = topic_model.reduce_outliers(T.doc.tolist(), topics, strategy="embeddings", embeddings=emb, threshold=0.45)
topic_model.update_topics(T.doc.tolist(), topics=new_topics, vectorizer_model=CountVectorizer(stop_words=stop, ngram_range=(1, 2), min_df=3, token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z_\-]{2,}\b"))
T["topic"] = new_topics; T["topic_raw"] = topics

tag = f"topics_{args.source}{'_ext' if args.external_only else ''}{'_subst' if args.substantive_only else ''}"; od = OUT / tag; od.mkdir(exist_ok=True)
info = topic_model.get_topic_info(); info.to_csv(od / "topic_info.csv", index=False)
T[["thread_id", "source", "repo_or_category", "title", "created_at", "quarter", "topic", "topic_raw"]].to_parquet(od / "doc_topics.parquet", index=False)
# topics over time: plain crosstab (BERTopic's helper is incompatible with pandas 3)
tot = pd.crosstab(T.topic, T.quarter); tot.to_csv(od / "topics_over_time.csv")
try:
    hier = topic_model.hierarchical_topics(T.doc.tolist()); hier.to_csv(od / "hierarchy.csv", index=False)
except Exception as e: print("hierarchy skipped:", e)
# representative docs per topic for labeling
reps = {int(k): v[:5] for k, v in topic_model.get_representative_docs().items()} if hasattr(topic_model, "get_representative_docs") else {}
json.dump({"n_docs": len(T), "n_topics": int((info.Topic >= 0).sum()), "outliers_raw": int((T.topic_raw == -1).sum()),
           "topics": [{"topic": int(r.Topic), "count": int(r.Count), "words": [w for w, _ in topic_model.get_topic(r.Topic)][:12],
                       "rep_docs": [d[:300] for d in reps.get(int(r.Topic), [])]} for r in info.itertuples() if r.Topic >= 0]},
          open(od / "topics_summary.json", "w"), indent=1)
topic_model.save(str(od / "model"), serialization="safetensors", save_ctfidf=True, save_embedding_model="BAAI/bge-small-en-v1.5")
print(f"\ntopics: {(info.Topic >= 0).sum()}  raw outliers: {(T.topic_raw == -1).sum()}  -> after reduction: {(T.topic == -1).sum()}")
print(info.head(25)[["Topic", "Count", "Name"]].to_string())
