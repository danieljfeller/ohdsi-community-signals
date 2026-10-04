"""Paced, resumable collector for OHDSI GitHub issues (not PRs) created in [START, END].

Phase A: issue list with bodies via Search API, one quarter at a time (keeps each query < 1000 results).
Phase B: comments for every issue with comments > 0 -> data/raw/github/comments/{owner__repo__number}.json
Token comes from `gh auth token` at runtime and is never written to disk.
"""
import json, os, sys, time, logging, subprocess, requests
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "github"
COMMENTS = ROOT / "comments"; COMMENTS.mkdir(parents=True, exist_ok=True)
ISSUES = ROOT / "issues.jsonl"
QUARTERS = [("2024-10-01", "2024-12-31"), ("2025-01-01", "2025-03-31"), ("2025-04-01", "2025-06-30"), ("2025-07-01", "2025-09-30"),
            ("2025-10-01", "2025-12-31"), ("2026-01-01", "2026-03-31"), ("2026-04-01", "2026-06-30"), ("2026-07-01", "2026-10-01")]
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s",
                    handlers=[logging.FileHandler(ROOT / "collect.log"), logging.StreamHandler(sys.stdout)])
log = logging.getLogger("github")
TOKEN = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
S = requests.Session(); S.headers.update({"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                                          "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "rhino-ohdsi-community-research/0.1"})
API = "https://api.github.com"

def get(url, params=None, search=False, max_tries=8):
    delay = 5
    for _ in range(max_tries):
        try:
            r = S.get(url, params=params, timeout=(20, 60))
        except requests.exceptions.RequestException as e:
            log.warning("%s -> %s; backoff %ss", url, type(e).__name__, delay); time.sleep(delay); delay = min(delay * 2, 300); continue
        rem = int(r.headers.get("X-RateLimit-Remaining", "1") or 1)
        if r.status_code == 200:
            if rem < (3 if search else 50):
                reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60)); nap = max(reset - time.time(), 1) + 2
                log.info("rate limit nearly exhausted; sleeping %.0fs", nap); time.sleep(nap)
            return r
        if r.status_code in (403, 429):
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60)); nap = max(reset - time.time(), delay) + 2
            log.warning("%s -> %s; sleeping %.0fs", url, r.status_code, nap); time.sleep(min(nap, 900))
        elif r.status_code in (404, 410, 451):
            log.warning("%s -> %s", url, r.status_code); return None
        else:
            log.warning("%s -> %s; backoff %ss", url, r.status_code, delay); time.sleep(delay)
        delay = min(delay * 2, 300)
    log.error("giving up on %s", url); return None

def collect_issues():
    have = set()
    if ISSUES.exists():
        for line in open(ISSUES): d = json.loads(line); have.add((d["repo"], d["number"]))
        log.info("issues.jsonl exists with %d issues; will append new ones only", len(have))
    with open(ISSUES, "a") as out:
        for a, b in QUARTERS:
            page, got, tc = 1, 0, None
            while True:
                r = get(f"{API}/search/issues", {"q": f"org:OHDSI is:issue created:{a}..{b}", "per_page": 100, "page": page,
                                                   "sort": "created", "order": "asc"}, search=True)
                if r is None: break
                d = r.json(); items = d.get("items", []); tc = d.get("total_count", 0)
                for it in items:
                    repo = it["repository_url"].split("/repos/")[1]
                    if (repo, it["number"]) in have: continue
                    keep = {"repo": repo, "number": it["number"], "title": it["title"], "body": it.get("body"), "state": it["state"],
                            "state_reason": it.get("state_reason"), "created_at": it["created_at"], "updated_at": it["updated_at"],
                            "closed_at": it.get("closed_at"), "comments": it["comments"], "labels": [l["name"] for l in it.get("labels", [])],
                            "user": it["user"]["login"], "user_type": it["user"]["type"], "author_association": it.get("author_association"),
                            "reactions": it.get("reactions", {}), "html_url": it["html_url"], "milestone": (it.get("milestone") or {}).get("title")}
                    out.write(json.dumps(keep) + "\n"); have.add((repo, it["number"])); got += 1
                if len(items) < 100 or page * 100 >= min(tc, 1000): break
                page += 1; time.sleep(2.2)
            log.info("%s..%s total_count=%s new=%d", a, b, tc, got); time.sleep(2.2)
    return [json.loads(l) for l in open(ISSUES)]

def collect_comments(issues):
    todo = [i for i in issues if i["comments"] > 0]
    stats = {"ok": 0, "skip": 0, "fail": 0}
    for n, i in enumerate(todo, 1):
        path = COMMENTS / f"{i['repo'].replace('/', '__')}__{i['number']}.json"
        if path.exists(): stats["skip"] += 1; continue
        allc, page = [], 1
        while True:
            r = get(f"{API}/repos/{i['repo']}/issues/{i['number']}/comments", {"per_page": 100, "page": page})
            if r is None: break
            c = r.json(); allc.extend(c)
            if len(c) < 100: break
            page += 1
        if r is None and not allc: stats["fail"] += 1; continue
        slim = [{"id": c["id"], "user": c["user"]["login"], "user_type": c["user"]["type"], "author_association": c.get("author_association"),
                 "created_at": c["created_at"], "body": c.get("body"), "reactions": c.get("reactions", {})} for c in allc]
        tmp = path.with_suffix(".tmp"); json.dump(slim, open(tmp, "w")); os.replace(tmp, path); stats["ok"] += 1
        time.sleep(0.75)
        if n % 100 == 0: log.info("comments progress %d/%d %s", n, len(todo), stats)
    log.info("comments DONE %s", stats)

if __name__ == "__main__":
    issues = collect_issues()
    log.info("issues total: %d; with comments: %d; bot-authored: %d", len(issues), sum(1 for i in issues if i["comments"] > 0),
             sum(1 for i in issues if i["user_type"] != "User"))
    collect_comments(issues)
