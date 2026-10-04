"""Paced, resumable collector for forums.ohdsi.org (Discourse JSON API).

Phase A: manifest of topics created within [START, END) via /latest.json?order=created.
Phase B: full topic JSON (+ all posts) for each manifest topic -> data/raw/forums/topics/{id}.json
Pacing: ~1 req/sec, exponential backoff on 429 / connection errors. Safe to re-run.
"""
import json, os, sys, time, logging, requests
from pathlib import Path

BASE = "https://forums.ohdsi.org"
START, END = "2024-10-01", "2026-10-01"
MANIFEST_FLOOR = "2024-09-15"          # paginate a little past START to be safe
ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "forums"
TOPICS = ROOT / "topics"; TOPICS.mkdir(parents=True, exist_ok=True)
MANIFEST = ROOT / "manifest.jsonl"
PACE = 1.6

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.FileHandler(ROOT / "collect.log"), logging.StreamHandler(sys.stdout)])
log = logging.getLogger("forums")
S = requests.Session()
S.headers.update({"User-Agent": "rhino-ohdsi-community-research/0.1 (daniel@rhinohealth.com; polite, 1 req/s)"})
_last = 0.0

def get(path, params=None, max_tries=8):
    global _last
    delay = 5
    for attempt in range(max_tries):
        wait = PACE - (time.time() - _last)
        if wait > 0: time.sleep(wait)
        try:
            r = S.get(BASE + path, params=params, timeout=(20, 60)); _last = time.time()
            if r.status_code == 200: return r.json()
            if r.status_code in (404, 403, 410): log.warning("%s -> %s", path, r.status_code); return None
            if r.status_code == 429:
                ra = int(r.headers.get("Retry-After", delay)); log.warning("429 on %s; sleeping %ss", path, ra); time.sleep(ra)
            else:
                log.warning("%s -> %s; backoff %ss", path, r.status_code, delay); time.sleep(delay)
        except requests.exceptions.RequestException as e:
            _last = time.time(); log.warning("%s -> %s; backoff %ss", path, type(e).__name__, delay); time.sleep(delay)
        delay = min(delay * 2, 300)
    log.error("giving up on %s", path); return None

def build_manifest():
    seen = {}
    if MANIFEST.exists():
        for line in open(MANIFEST): t = json.loads(line); seen[t["id"]] = t
        log.info("manifest exists with %d topics; refreshing newest pages only", len(seen))
    page, floor_hit, prev_created = 0, False, None
    with open(MANIFEST, "a") as out:
        while not floor_hit and page < 400:
            d = get("/latest.json", {"order": "created", "ascending": "false", "page": page})
            if d is None: break
            topics = d.get("topic_list", {}).get("topics", [])
            if not topics: break
            for t in topics:
                c = t["created_at"]
                if t.get("pinned") and prev_created and c > prev_created: pass  # pinned topics float; ignore ordering check
                elif prev_created and c > prev_created and not t.get("pinned"):
                    log.warning("non-monotonic created_at at page %d (%s > %s)", page, c, prev_created)
                prev_created = c if not t.get("pinned") else prev_created
                if c < MANIFEST_FLOOR and not t.get("pinned"): floor_hit = True; continue
                if t["id"] in seen: continue
                keep = {k: t.get(k) for k in ["id", "title", "slug", "created_at", "last_posted_at", "posts_count", "reply_count",
                                                "views", "like_count", "category_id", "tags", "pinned", "closed", "archived", "word_count"]}
                out.write(json.dumps(keep) + "\n"); seen[t["id"]] = keep
            if seen and page % 10 == 0: log.info("manifest page %d, %d topics so far, oldest %s", page, len(seen), prev_created)
            if not d.get("topic_list", {}).get("more_topics_url"): break
            page += 1
    log.info("manifest complete: %d topics (floor %s)", len(seen), MANIFEST_FLOOR)
    return seen

def fetch_topic(tid):
    path = TOPICS / f"{tid}.json"
    if path.exists(): return "skip"
    d = get(f"/t/{tid}.json")
    if d is None: return "fail"
    stream = d.get("post_stream", {}).get("stream", [])
    have = {p["id"] for p in d.get("post_stream", {}).get("posts", [])}
    missing = [pid for pid in stream if pid not in have]
    for i in range(0, len(missing), 20):
        chunk = missing[i:i + 20]
        extra = get(f"/t/{tid}/posts.json", [("post_ids[]", pid) for pid in chunk])
        if extra and extra.get("post_stream", {}).get("posts"):
            d["post_stream"]["posts"].extend(extra["post_stream"]["posts"])
    d["post_stream"]["posts"].sort(key=lambda p: p["post_number"])
    tmp = path.with_suffix(".tmp"); json.dump(d, open(tmp, "w")); os.replace(tmp, path)
    return "ok"

if __name__ == "__main__":
    man = build_manifest()
    targets = sorted([t for t in man.values() if START <= t["created_at"] < END], key=lambda t: t["id"])
    log.info("topics in window: %d; posts (manifest sum): %d", len(targets), sum(t["posts_count"] or 0 for t in targets))
    stats = {"ok": 0, "skip": 0, "fail": 0}
    for i, t in enumerate(targets, 1):
        stats[fetch_topic(t["id"])] += 1
        if i % 50 == 0: log.info("progress %d/%d %s", i, len(targets), stats)
    log.info("DONE %s", stats)
