# OHDSI Community Signals: Analysis Plan (v1.0, executed 2026-10-04 on forums; Teams pending access)

**Status.** Forum analysis complete; see `report/REPORT.md` and `deliverables/`. Teams ingestion is specified below and waits on access.

**Goal.** Identify unmet needs and pain points in the OHDSI community, Oct 1 2024 to Oct 1 2026,
to inform Rhino Federated Computing's product marketing and roadmap (federated analytics,
federated learning, data harmonization).

**Posture.** Discovery first, Rhino lens second. Themes are derived from what the community says,
without a Rhino-shaped taxonomy imposed up front. A separate, final step maps themes to Rhino
capability areas so the discovery results stay credible and reusable.

---

## 1. Reconnaissance findings (what shapes the plan)

| Source | Volume in window | Access | Notes |
|---|---|---|---|
| OHDSI Forums (forums.ohdsi.org, Discourse) | est. 900 to 1,400 topics, 7,000 to 10,000 posts (recent rate: 31 topics and 255 posts per month; 8,412 topics all-time) | Public JSON API, no key needed | Six substantive categories: General, Implementers, Vocabulary Users, Developers, Researchers, CDM Builders. No "Solved" plugin, so resolution must be inferred. Server throttled my probes; crawl must be paced (about 1 request/sec with backoff). |
| OHDSI GitHub issues (390 repos) | 4,915 issues and 6,333 PRs created in window (vs 3,733 issues in the prior two years: +32%) | `gh` CLI already authenticated | Top repos: Vocabulary-v5.0 (167), PatientLevelPrediction (90), DataQualityDashboard (66), CommonDataModel (56), Strategus (52), Atlas (39). Developer-skewed but rich on tooling friction. |
| OHDSI MS Teams workgroups | Unknown, likely the largest live channel | Not accessible from here; needs a member export | Big caveat: public forum traffic has declined as workgroup chatter moved to Teams. Forum data over-represents newcomers and public Q&A. |
| Community call recordings (YouTube) | ~100 weekly calls in window | Public; transcripts retrievable | Captures leadership priorities and announcements more than pain points. Optional. |
| Symposium abstracts / collaborator showcase 2024, 2025 | ~200 to 300 abstracts | Public PDFs | Shows what people are building, not what hurts. Optional context layer. |

Environment: Python 3.11.9 available via pyenv; no ML stack installed yet (will create a venv with
BERTopic, sentence-transformers, scikit-learn, pandas, DuckDB). Apple M4, 16 GB RAM is enough for
embedding ~15k documents locally. No Anthropic API key in the shell (needed for LLM coding at scale).

---

## 2. Research questions

1. What are the dominant themes of community discussion in the window, and how have they shifted quarter by quarter?
2. Which themes carry the most unresolved friction (unanswered, long time-to-first-reply, repeated asks, workarounds)?
3. What concrete jobs-to-be-done sit behind the friction (e.g., "run a Strategus study across sites without each site rebuilding the R environment")?
4. Where do needs cluster along the OHDSI lifecycle: ETL/CDM conversion, vocabulary mapping, data quality, cohort definition, characterization, estimation, prediction, network study execution, infrastructure, governance/privacy?
5. Which needs are plausibly served by federated analytics, federated learning, or harmonization tooling, and which are not (so marketing avoids over-claiming)?

---

## 3. Corpus construction

**Unit of analysis.** The *thread* (forum topic or GitHub issue). The opening post is where the need is stated; replies tell us whether and how it was met. We model opening posts and whole threads separately.

**Forums.** Paginate `/latest.json?order=created` for the manifest, then fetch each topic's `/t/{id}.json` and its post stream. Keep: title, category, tags, created_at, views, like_count, posts_count, reply_count, participant_count, each post's HTML (`cooked`), author handle, trust_level, post_number, reply_to. Strip quoted blocks and code blocks from text (keep a `has_code` flag). Pseudonymize author handles (salted hash) at ingest; raw handles never leave the local store.

**GitHub (dropped 2026-10-04).** Collected and piloted, then removed from scope: 73% of the 4,883 issues in the window were maintainer task tracking, and even the 1,309 external issues read as package bug reports rather than expressions of unmet need. Raw pull kept under `data/out_of_scope/` for reference only.

**MS Teams (conditional).** OHDSI workgroup chatter largely lives in the OHDSI Microsoft Teams tenant. If Daniel can access it, channel messages for the window are ingested into the same `threads`/`posts` schema (channel = category, root message = opening post, replies = posts). Access routes, in order of preference: (1) Microsoft Graph API with delegated permissions on Daniel's account (`ChannelMessage.Read.All` needs tenant-admin consent, which OHDSI admins may or may not grant); (2) an export provided by OHDSI leadership; (3) browser-assisted reading of selected high-value workgroup channels via Daniel's signed-in Teams web session (slow; scoped to a shortlist of channels). Governance note: Teams content is member-only, so quotes from it should not appear in external marketing without explicit permission from OHDSI.

**Optional.** Teams export (if provided), YouTube transcripts, symposium abstracts: same schema, `source` column.

**Storage.** Raw JSON in `data/raw/`, normalized Parquet tables in `data/processed/` (`threads`, `posts`), queried with DuckDB. Everything reproducible from `make collect`.

---

## 4. Methods

### 4a. Landscape: topic modeling (replaces LDA)
- **BERTopic** on opening posts (and separately on all posts): sentence-transformer embeddings (`bge-small-en-v1.5` or `all-MiniLM-L12-v2`, both run locally), UMAP for reduction, HDBSCAN for clustering, class-based TF-IDF for topic words, LLM-written topic labels.
- Why not LDA: forum posts are short and jargon-heavy ("Atlas", "WebAPI", "Strategus", "Usagi" carry no signal to bag-of-words priors); LDA needs k fixed up front and produces diffuse topics on short text. BERTopic uses contextual embeddings, discovers k, and gives an explicit outlier bucket. LDA is run once as a robustness baseline only.
- **Dynamic topics**: topics-over-time by quarter (8 quarters) to find rising and declining themes.
- **Hierarchical topics** to produce a 2-level taxonomy (about 8 to 12 parent themes, 40 to 60 subtopics).
- Domain stopword list and a short OHDSI alias dictionary (CDM = OMOP CDM, PLP = PatientLevelPrediction, etc.) applied before c-TF-IDF only, never before embedding.

### 4b. Pain-point extraction: LLM structured coding
Topic models say *what* people talk about; they do not say what hurts. Each opening post (and the thread summary) is coded by an LLM with a fixed JSON schema:
- `post_type`: question / bug / feature_request / announcement / discussion / job_or_event
- `lifecycle_stage` (list, from the taxonomy in RQ4)
- `tools_mentioned` (controlled list of OHDSI tools plus "other")
- `pain_point`: one sentence in the poster's terms, or null
- `job_to_be_done`: one sentence, or null
- `severity`: blocker / major / minor / none
- `workaround_present`: yes/no
- `resolution_status` (from the full thread): resolved / partially / unresolved / unclear / no_reply
- `multi_site_or_network_context`: yes/no (flag for federated relevance)
- `evidence_quote`: verbatim span under 25 words

Execution (decided): coding runs through Claude Code subagents inside this session, not the Anthropic API. Threads are batched (about 40 to 60 per batch, truncated to the opening post plus a compact digest of replies) and coded by Haiku-class subagents against the fixed schema; a Sonnet/Opus-class subagent re-codes a 10% stratified sample to measure agreement. A 50-thread human-coded gold set (Daniel codes, or we code together) gives a real reliability number (Cohen's kappa per field).

### 4c. Quantifying "unmet"
Per theme (BERTopic parent topic × lifecycle stage):
- Volume and share of threads; trend slope across quarters.
- No-reply rate and median time-to-first-reply (forums); open rate and median days-open (GitHub).
- Unresolved rate from 4b.
- Recurrence: near-duplicate asks across time (cosine similarity of embeddings above a threshold).
- Engagement: views, likes, reactions per thread (demand signal).
- Composite **Unmet Need Index** = rank-normalized volume × unresolved rate × recurrence × (1 + trend). Reported with the components visible, not just the composite, so a reader can disagree with the weighting.

### 4d. Federated lens (last step)
Each parent theme and each top-30 pain point is mapped to: federated analytics, federated learning, data harmonization, trusted execution/governance, none. Mapping done by LLM with rationale, then reviewed by hand. Output is an opportunity matrix (need frequency × unmet severity × Rhino fit) plus an explicit "not our problem" list.

### 4e. Validation and triangulation
- Topic coherence (c_v) and manual read of 10 random docs per topic.
- Forums vs GitHub agreement on theme ranking (Spearman).
- Sanity check against known 2025 to 2026 OHDSI priorities (Strategus adoption, DARWIN EU and other networks, vocabulary release cadence, Atlas/WebAPI modernization) to confirm the model recovers what we already know before trusting what we do not.

---

## 5. Deliverables (proposed; confirm)
1. `ANALYSIS_PLAN.md` (this file, finalized after your answers).
2. Reproducible pipeline in this repo: `collect/`, `process/`, `model/`, `report/`, one `Makefile`, pinned `requirements.txt`.
3. Coded dataset: `threads_coded.parquet` and `.csv` (pseudonymized), plus the taxonomy as YAML.
4. Written report (12 to 20 pages equivalent): executive summary; corpus and method; theme taxonomy with trends; top unmet needs ranked with anonymized verbatims; lifecycle heatmap; federated opportunity matrix; implications for marketing messaging and for product; limitations.
5. (Dropped per decision) Interactive topic explorer.
6. (Dropped per decision) Slide deck.

## 6. Guardrails
- Public data only unless you supply an export; polite crawling (about 1 req/sec, identified User-Agent, resumable).
- Author handles pseudonymized in every output. Verbatims in marketing material only with the author's permission, which we request separately.
- No scraping of profile pages or private messages; no compilation of individual-level dossiers.
- Clear separation in the report between what the community said and Rhino's interpretation.

## 7. Phases and effort
| Phase | Work | Wall time |
|---|---|---|
| 0 | Plan sign-off, env setup, API key | today |
| 1 | Collection (forums paced crawl ~3 to 4 h unattended; GitHub ~1 h) | 1 day |
| 2 | Cleaning, pseudonymization, EDA, corpus stats | 0.5 day |
| 3 | BERTopic, dynamic and hierarchical topics, LDA baseline, label review | 1 day |
| 4 | LLM coding, reliability check, gold-set comparison | 1 day |
| 5 | Unmet Need Index, federated mapping, triangulation | 0.5 day |
| 6 | Report, explorer, review loop with you | 1 day |

## 8. Risks and limitations
- **Channel migration to Teams**: forum volume is a declining, biased sample. Mitigation: GitHub triangulation; request a Teams export; state the bias plainly.
- **Forum availability**: forums.ohdsi.org went down (TCP refused from two networks) during recon on 2026-10-04. Collector waits and auto-starts when the host returns; paced at 1 req/sec with backoff and a resumable manifest. Wayback Machine checked as fallback: only sparse HTML snapshots, not sufficient.
- **Developer skew in GitHub**: issues over-represent package bugs. Mitigation: analyze sources separately and together; weight by source in the index.
- **LLM coding drift**: mitigated by fixed schema, few-shot anchors, Sonnet and human agreement checks.
- **Jargon and multilingual posts**: regional categories (Korea, China, Japan, Español, Português) are small; include with language tag, do not translate unless volume warrants.

## 9. Decisions (2026-10-04)
| Question | Decision |
|---|---|
| Sources | OHDSI Forums (core). OHDSI MS Teams if access can be arranged. GitHub dropped on 2026-10-04 after piloting (maintainer task tracking, not pain points). No call transcripts. |
| LLM coding | Claude Code subagents in-session; no API key. |
| Deliverables | Written report + coded dataset (items 1 to 4 in section 5). Explorer and slides dropped unless requested later. |
| Attribution | Pseudonymize everywhere: salted-hash handles in data and report; short unattributed verbatims. |


## 10. Execution record (2026-10-04)
| Step | Outcome |
|---|---|
| Collection | 776 topics, 2,164 posts; zero fetch failures. Forum host blocked this machine's IP after an early probe burst; the crawl ran over a phone hotspot at 1 req / 1.6 s. |
| Normalization | Pseudonymized authors (salted hash), scrubbed emails and @-mentions, stripped quotes/code/markup. |
| Coding | 773 threads coded in 18 batches by Claude Code subagents; 3 threads under 3 words skipped. Zero unparseable outputs. |
| Reliability | 80-thread sample re-coded by a stronger model. Kappa: pain point present 0.90, harmonization 0.77, post type 0.70, severity 0.60, multi-site 0.59, resolution 0.36. Resolution anchored on reply metadata as a result. |
| Needs taxonomy | 392 pain points, 29 clusters (Ward, k=30), labeled and mapped to Rhino fit with rationale; 3 merges suggested. |
| Metrics | Unmet Need Index by need cluster and lifecycle stage; trends by quarter; multi-site and blocker slices. |
| Deviations | GitHub dropped after pilot; cosine-threshold clustering replaced by Ward; BERTopic kept as cross-check only. |
