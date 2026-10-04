"""Normalize raw forum topics + GitHub issues into two pseudonymized Parquet tables.

threads: one row per forum topic / GitHub issue (opening post text included)
posts:   one row per post / comment (including the opening post, post_number=1)
Author handles are replaced by salted SHA-256 prefixes; the salt lives in data/.salt (gitignored) and raw handles never reach processed/.
"""
import json, re, hashlib, os, secrets
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"; OUT.mkdir(parents=True, exist_ok=True)
START, END = "2024-10-01", "2026-10-01"
SALT_FILE = ROOT / "data" / ".salt"
if not SALT_FILE.exists(): SALT_FILE.write_text(secrets.token_hex(16))
SALT = SALT_FILE.read_text().strip()
def pseud(handle): return "u_" + hashlib.sha256((SALT + str(handle)).encode()).hexdigest()[:10]

cats = {}
cj = RAW / "forums" / "categories.json"
if cj.exists():
    for c in json.load(open(cj))["category_list"]["categories"]:
        cats[c["id"]] = c["name"]
        for sc in c.get("subcategory_list") or []: cats[sc["id"]] = c["name"] + "/" + sc["name"]

CODE_RE = re.compile(r"```.*?```|~~~.*?~~~", re.S); INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
MD_QUOTE_RE = re.compile(r"^>.*$", re.M); URL_RE = re.compile(r"https?://\S+"); MENTION_RE = re.compile(r"(?<![\w.])@[A-Za-z0-9_.\-]{2,}"); EMAIL_RE = re.compile(r"[\w.+\-]+@[\w\-]+(\.[\w\-]+)+")

def clean_html(cooked):
    """Discourse 'cooked' HTML -> text; drop quoted blocks and code blocks, flag their presence."""
    soup = BeautifulSoup(cooked or "", "lxml")
    has_quote = bool(soup.find("aside", class_="quote")); has_code = bool(soup.find("pre") or soup.find("code"))
    for tag in soup.find_all(["aside", "pre"]): tag.decompose()          # quotes and code blocks
    for tag in soup.find_all("code"): tag.replace_with(" [code] ")
    for img in soup.find_all("img"): img.replace_with(" [image] ")
    text = URL_RE.sub(" [link] ", soup.get_text("\n")); text = EMAIL_RE.sub("[email]", text); text = MENTION_RE.sub("@user", text); text = re.sub(r"[ \t]+", " ", text); text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text, has_quote, has_code

TEMPLATE_HEADINGS = re.compile(r"^\s*(#+\s*)?\**\s*(describe the bug|to reproduce|steps to reproduce|expected behavio[u]?r|actual behavio[u]?r|screenshots?|additional context|"
                               r"desktop|smartphone|session ?info|r version|environment|error message|is your feature request related to a problem\??|describe the solution you'd like|"
                               r"describe alternatives you've considered|context|reprex|output|details|summary|version|bug description|proposed solution)\s*\**:?\s*$", re.I | re.M)
def clean_md(body):
    body = body or ""
    has_code = bool(CODE_RE.search(body) or INLINE_CODE_RE.search(body)); has_quote = bool(MD_QUOTE_RE.search(body))
    t = CODE_RE.sub(" [code] ", body); t = INLINE_CODE_RE.sub(" [code] ", t); t = MD_QUOTE_RE.sub("", t)
    t = re.sub(r"<details>.*?</details>", " ", t, flags=re.S | re.I)           # collapsed session-info / reprex blocks
    t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " [image] ", t)
    t = re.sub(r"<img[^>]*>", " [image] ", t, flags=re.I)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", t)                      # keep link text, drop URL
    t = BeautifulSoup(t, "lxml").get_text(" ") if "<" in t else t                 # strip any remaining HTML tags
    t = URL_RE.sub(" [link] ", t); t = EMAIL_RE.sub("[email]", t); t = MENTION_RE.sub("@user", t)
    t = re.sub(r"Created on \d{4}-\d{2}-\d{2} (with|by the) reprex.*$", "", t, flags=re.M | re.I)
    t = TEMPLATE_HEADINGS.sub("", t)
    t = re.sub(r"[ \t]+", " ", t); t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t, has_quote, has_code

threads, posts = [], []

# ---------- forums ----------
for f in sorted((RAW / "forums" / "topics").glob("*.json")):
    d = json.load(open(f)); tid = d["id"]
    if not (START <= d["created_at"] < END): continue
    ps = sorted(d["post_stream"]["posts"], key=lambda p: p["post_number"])
    ps = [p for p in ps if p.get("post_type", 1) == 1 and not p.get("hidden") and not p.get("deleted_at")]
    if not ps: continue
    op = ps[0]; op_text, _, op_code = clean_html(op["cooked"])
    author = op["username"]
    repliers = {p["username"] for p in ps[1:]}
    first_reply = next((p for p in ps[1:] if p["username"] != author), None)
    threads.append({
        "thread_id": f"f{tid}", "source": "forums", "repo_or_category": cats.get(d["category_id"], str(d["category_id"])),
        "title": d["title"], "tags": ",".join(d.get("tags") or []), "created_at": d["created_at"], "last_activity_at": d.get("last_posted_at"),
        "author": pseud(author), "author_trust_level": op.get("trust_level"), "op_text": op_text, "op_has_code": op_code,
        "n_posts": len(ps), "n_replies": len(ps) - 1, "n_participants": len(repliers | {author}),
        "n_replies_by_others": sum(1 for p in ps[1:] if p["username"] != author),
        "first_reply_at": first_reply["created_at"] if first_reply else None,
        "views": d.get("views"), "likes": d.get("like_count"), "reactions": None, "state": "closed" if d.get("closed") else "open",
        "closed_at": None, "labels": "", "url": f"https://forums.ohdsi.org/t/{d.get('slug','')}/{tid}",
    })
    for p in ps:
        text, hq, hc = clean_html(p["cooked"])
        posts.append({"thread_id": f"f{tid}", "post_id": f"f{p['id']}", "post_number": p["post_number"], "source": "forums",
                      "author": pseud(p["username"]), "is_op_author": p["username"] == author, "created_at": p["created_at"],
                      "text": text, "has_quote": hq, "has_code": hc, "likes": next((a.get("count", 0) for a in p.get("actions_summary", []) if a.get("id") == 2), 0),
                      "reply_to_post_number": p.get("reply_to_post_number")})

# ---------- github ----------
gi = RAW / "github" / "issues.jsonl"
if gi.exists():
    for line in open(gi):
        i = json.loads(line)
        if not (START <= i["created_at"] < END): continue
        op_text, _, op_code = clean_md(i.get("body"))
        cf = RAW / "github" / "comments" / f"{i['repo'].replace('/', '__')}__{i['number']}.json"
        comments = json.load(open(cf)) if cf.exists() else []
        comments = [c for c in comments if c["user_type"] == "User"]
        others = [c for c in comments if c["user"] != i["user"]]
        threads.append({
            "thread_id": f"g{i['repo'].split('/')[1]}#{i['number']}", "source": "github", "repo_or_category": i["repo"].split("/")[1],
            "title": i["title"], "tags": ",".join(i.get("labels") or []), "created_at": i["created_at"], "last_activity_at": i["updated_at"],
            "author": pseud(i["user"]), "author_trust_level": i.get("author_association"), "op_text": op_text, "op_has_code": op_code,
            "n_posts": 1 + len(comments), "n_replies": len(comments), "n_participants": len({c["user"] for c in comments} | {i["user"]}),
            "n_replies_by_others": len(others), "first_reply_at": others[0]["created_at"] if others else None,
            "views": None, "likes": (i.get("reactions") or {}).get("+1", 0), "reactions": (i.get("reactions") or {}).get("total_count", 0),
            "state": i["state"], "closed_at": i.get("closed_at"), "labels": ",".join(i.get("labels") or []), "url": i["html_url"],
            "author_is_bot": i["user_type"] != "User", "state_reason": i.get("state_reason"),
        })
        posts.append({"thread_id": threads[-1]["thread_id"], "post_id": threads[-1]["thread_id"] + "#0", "post_number": 1, "source": "github",
                      "author": pseud(i["user"]), "is_op_author": True, "created_at": i["created_at"], "text": op_text, "has_quote": False,
                      "has_code": op_code, "likes": (i.get("reactions") or {}).get("+1", 0), "reply_to_post_number": None})
        for k, c in enumerate(comments, 2):
            text, hq, hc = clean_md(c.get("body"))
            posts.append({"thread_id": threads[-1]["thread_id"], "post_id": f"gc{c['id']}", "post_number": k, "source": "github",
                          "author": pseud(c["user"]), "is_op_author": c["user"] == i["user"], "created_at": c["created_at"], "text": text,
                          "has_quote": hq, "has_code": hc, "likes": (c.get("reactions") or {}).get("+1", 0), "reply_to_post_number": None})

T, P = pd.DataFrame(threads), pd.DataFrame(posts)
for df in (T, P):
    for col in [c for c in df.columns if c.endswith("_at")]: df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
T["hours_to_first_reply"] = (T["first_reply_at"] - T["created_at"]).dt.total_seconds() / 3600
T["quarter"] = T["created_at"].dt.to_period("Q").astype(str)
T["op_words"] = T["op_text"].fillna("").str.split().str.len()
T.to_parquet(OUT / "threads.parquet", index=False); P.to_parquet(OUT / "posts.parquet", index=False)
print(f"threads: {len(T)}  posts: {len(P)}"); print(T.groupby("source").agg(threads=("thread_id", "count"), replies=("n_replies", "sum"),
      no_reply_rate=("n_replies_by_others", lambda s: (s == 0).mean()), median_hrs_first_reply=("hours_to_first_reply", "median")).round(2))
print("\nby quarter:"); print(T.groupby(["quarter", "source"]).size().unstack(fill_value=0))
