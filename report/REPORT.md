# OHDSI Community Signals, October 2024 to October 2026
## Unmet needs and pain points on the OHDSI Forums, and what they mean for Rhino Federated Computing

Prepared 4 October 2026. Source: every public topic on forums.ohdsi.org created between 1 Oct 2024 and 1 Oct 2026 (776 topics, 2,164 posts). Author handles are pseudonymized throughout; quotes are short and unattributed.

---

## 1. Executive summary

**The forum is small, declining as a Q&A venue, and most questions go unmet.** Of 776 topics, 429 (55%) are substantive (questions, bugs, feature requests, discussions). The rest are announcements, digests and event or job notices, whose share rose from 36% of topics in the first year to 53% in the second. Among substantive threads, 70% were never fully resolved: 29% got no reply from anyone, 15% were explicitly unresolved, and 26% only partially answered. The median answered question waited 18 hours for a first reply; a quarter waited nearly three days.

**Harmonization is the dominant pain.** Vocabulary mapping and ETL/CDM conversion appear in 43% of all need statements and more than half of substantive threads carry harmonization context. Twelve of the 29 bottom-up need clusters, covering 194 of 389 clustered pain points (50%), are about getting source data into OMOP: missing vocabulary concepts, vocabulary content defects, unclear CDM conventions, oncology and genomic data, lab domain assignment, drug mapping, and the lack of reusable ETL pipelines.

**Infrastructure and data quality carry the highest unmet-need scores.** Installing and authenticating Atlas/WebAPI and Broadsea, running Achilles and DataQualityDashboard on large databases, and connecting OHDSI tools to modern backends (SQL Server, Postgres upgrades, Trino, Spark) produce 36% of all blocker-severity threads and 75% to 80% unresolved rates.

**Multi-site needs are rare but almost never met.** 46 substantive threads (11%) involve more than one site or a network study. 87% were unresolved. They cluster around a single theme: results across sites are not comparable, and nobody can tell. Members describe cohorts that mean different things at different sites, two independently converted OMOP datasets that cannot be validated against each other, drug doses derived differently per site, hierarchy-based code lists that silently miss thousands of patients, Atlas results that cannot be stratified by site, and prediction results that cannot be shared without patient-level tables.

**What this means for Rhino.** The community's loudest unmet need, harmonization, is the one where Rhino's Data Harmonization Engine has the most direct fit, and the pain is specific enough to shape features (combination drugs, oncology episodes, genomic variants, lab domains, ICD-10 to SNOMED mapping defects). The federated analytics fit is narrower than the volume of OMOP discourse would suggest: the forum shows little demand for running studies across sites per se, and strong demand for proving that cross-site results are comparable and for sharing results and models without moving patient data. Federated learning barely appears. Marketing should lead with harmonization and cross-site comparability, not with federated learning.

---

## 2. Why this analysis

OHDSI is the largest open community working with observational health data on a shared model, the OMOP Common Data Model. Its members run multi-site network studies by distributing analysis code to data partners who execute it locally and share aggregate results. That workflow is adjacent to what Rhino Federated Computing offers, so the community's public record of what is hard, broken or missing is a direct input to Rhino's product and marketing decisions.

The question asked of the data was: what do community members struggle with, how often, with what severity, and how much of it goes unresolved? Themes were derived from the text first. The mapping to Rhino capability areas was done last, so the discovery results stand on their own.

## 3. Data

### 3.1 Source
| Item | Value |
|---|---|
| Source | OHDSI Forums (forums.ohdsi.org), public Discourse instance |
| Window | Topics created 1 Oct 2024 to 1 Oct 2026 |
| Topics / posts | 776 / 2,164 |
| Distinct authors | 334 (282 on substantive threads; 72% of them posted once) |
| Collection | Discourse JSON API, one request every 1.6 seconds, resumable; collected 4 Oct 2026 |
| Categories with most substantive traffic | Implementers (106), Vocabulary Users (88), General (62), Developers (49), Researchers (47), CDM Builders (44) |

### 3.2 Why GitHub issues were excluded
OHDSI's 390 GitHub repositories produced 4,883 issues in the window. A pilot showed 73% were maintainers tracking their own work, and the remainder were mostly package bug reports. They describe defects in specific tools, not the community's unmet needs, so they were excluded after the pilot.

### 3.3 Limitations of the corpus
- **Channel migration.** Much OHDSI workgroup discussion happens in Microsoft Teams, which is not public. The forum over-represents newcomers and one-off public questions and under-represents established collaborators and network-study coordinators. The rising share of announcements and the falling count of substantive threads (275 in the first year, 154 in the second) are consistent with that migration.
- **Survivorship.** People who abandoned OHDSI tooling without posting leave no trace.
- **Small quarterly counts.** With 35 to 77 substantive threads per quarter, quarter-to-quarter changes are noisy; only the two-year direction is interpretable.
- **Pseudonymization.** Author handles were replaced by salted hashes and emails and @-mentions scrubbed at ingest.

## 4. Methods

### 4.1 Unit of analysis
The thread. The opening post states the need; the replies tell us whether it was met.

### 4.2 Pain-point coding
Every thread was coded by Claude against a fixed schema (`model/coding_schema.md`): post type, lifecycle stage, tools, pain point, job-to-be-done, severity, workaround present, resolution status, multi-site context, harmonization context, evidence quote, confidence. Coding ran in 18 batches of 45 thread digests. A stratified 80-thread sample was independently re-coded by a stronger model.

| Field | Agreement | Cohen's kappa |
|---|---|---|
| Pain point present | 95% | 0.90 |
| Harmonization context | 90% | 0.77 |
| Post type | 78% | 0.70 |
| Severity | 74% | 0.60 |
| Multi-site context | 94% | 0.59 |
| Workaround present | 89% | 0.51 |
| Resolution status | 54% | 0.36 |
| Lifecycle stage | mean Jaccard 0.69 | |

Agreement is substantial on what matters most (whether a pain point exists, what it is about) and weak on resolution status, where coders disagreed mostly between "partially" and "resolved" and between "unclear" and "no reply". Resolution was therefore anchored on metadata: a thread with no reply from anyone but the author is "no reply" regardless of coder judgment (with a self-solved exception), and the coder's label is used only for answered threads. All unresolved rates in this report use that anchored definition.

### 4.3 Needs taxonomy
The 392 pain-point sentences were embedded (bge-small) and clustered (Ward linkage, 30 clusters, 3 singletons dropped). Each cluster was labeled, given a need statement grounded in its members, and mapped to a Rhino capability area with a written rationale and confidence, then reviewed. A BERTopic model over raw opening posts was run as a cross-check and recovered the same major themes (vocabulary and SNOMED mapping, CDM table conventions, Atlas cohort logic, Achilles and SQL Server problems, WebAPI and Broadsea deployment, genomics).

### 4.4 Unmet Need Index
Per need cluster and per lifecycle stage: volume, unresolved rate, mean severity, trend slope, blocker share, multi-site share, harmonization share. The composite is a weighted sum of rank-normalized components (volume 0.35, unresolved rate 0.25, severity 0.20, positive trend 0.10, unresolved volume 0.10). Components are reported alongside the composite in `deliverables/need_metrics.csv` so readers can re-weight.

## 5. The landscape

### 5.1 What the forum is used for
| Post type | Threads | Share |
|---|---|---|
| Question | 247 | 32% |
| Announcement | 272 | 35% |
| Discussion | 81 | 10% |
| Bug report | 76 | 10% |
| Job or event | 68 | 9% |
| Feature request | 25 | 3% |

### 5.2 Where the needs sit in the lifecycle (substantive threads, multi-label)
| Lifecycle stage | Need threads | Unresolved | Blocker share | Unmet Need Index |
|---|---|---|---|---|
| Data quality | 60 | 80% | 17% | 0.80 |
| Infrastructure and deployment | 64 | 75% | 36% | 0.79 |
| Characterization | 35 | 80% | 14% | 0.64 |
| Estimation | 16 | 81% | 19% | 0.63 |
| ETL / CDM conversion | 114 | 67% | 2% | 0.61 |
| Vocabulary mapping | 127 | 64% | 2% | 0.60 |
| Community process | 30 | 87% | 3% | 0.59 |
| Governance and privacy | 16 | 69% | 25% | 0.49 |
| Network study execution | 13 | 69% | 0% | 0.46 |
| Learning and onboarding | 25 | 76% | 0% | 0.46 |
| Cohort definition | 39 | 54% | 3% | 0.43 |
| Prediction / ML | 13 | 69% | 0% | 0.40 |
| Results sharing | 6 | 50% | 17% | 0.21 |

Two patterns. Harmonization (vocabulary plus ETL) is where the volume is: 241 need-thread mentions, by far the largest, with moderate unresolved rates because the Vocabulary Users and CDM Builders categories have the forum's most responsive answerers. Infrastructure and data quality are where the severity is: fewer threads, but a third of infrastructure threads are blockers and four in five go unresolved.

### 5.3 Tools named in substantive threads
| Tool | Threads | Unresolved |
|---|---|---|
| OMOP CDM | 134 | 68% |
| Atlas | 110 | 72% |
| Standard vocabularies | 107 | 66% |
| Athena | 83 | 66% |
| R / HADES | 33 / 21 | 64% / 81% |
| WebAPI | 31 | 84% |
| Achilles | 19 | 84% |
| Broadsea | 15 | 73% |
| DataQualityDashboard | 11 | 73% |
| Postgres / SQL Server | 11 / 11 | 91% / 73% |
| Usagi | 11 | 64% |
| Strategus / PatientLevelPrediction | 7 / 7 | 43% / 43% |

Strategus, the network-study execution framework, is named in only 7 forum threads in two years. Network-study operations are discussed elsewhere (Teams, study-specific repositories), which is the single biggest reason to add a Teams source if access can be arranged.

## 6. Unmet needs, ranked

The 29 need clusters, ordered by Unmet Need Index. Full table with components, representative sentences and thread IDs: `deliverables/needs_taxonomy.csv`.

| Rank | Need | Threads | Unresolved | Severity (0 to 3) | Rhino fit |
|---|---|---|---|---|---|
| 1 | Mapping complex source data to OMOP (combination drugs, trial instruments, surveys, registries) | 26 | 77% | 1.65 | Harmonization |
| 2 | Representing genomic and omics data in OMOP | 19 | 79% | 1.79 | Harmonization |
| 3 | Extending OMOP for AI and interoperability (ML metadata, openEHR, negation) | 18 | 94% | 1.50 | None (mixed cluster) |
| 4 | Missing vocabulary concepts for source codes (ICD-O-3, ATC vaccines, rare disease, DRG) | 31 | 74% | 1.61 | Harmonization |
| 5 | Expressing complex cohort logic in Atlas (episodes, patient-ID lists, timing, R export) | 32 | 59% | 1.97 | None |
| 6 | Fixing OMOP vocabulary content defects (oncology TNM duplicates, deprecations without replacement) | 24 | 71% | 1.67 | Harmonization |
| 7 | Running Achilles at scale | 10 | 90% | 2.40 | None |
| 8 | Installing Atlas and WebAPI | 10 | 80% | 2.50 | None |
| 9 | Community coordination, training and documentation | 17 | 82% | 1.06 | None |
| 10 | Validating cohort comparability across sites | 18 | 67% | 1.61 | Federated analytics |
| 11 | Configuring Atlas authentication and permissions | 10 | 70% | 2.70 | None |
| 12 | CDM conventions for drugs, visits and type concepts | 19 | 58% | 1.68 | Harmonization |
| 13 | CDM conventions for observation periods and derived events | 20 | 60% | 1.50 | Harmonization |
| 14 | Hosting and integrating HADES infrastructure | 8 | 75% | 1.88 | None |
| 15 | Large measurement tables and duplicate rows | 7 | 71% | 2.29 | None |
| 16 | OHDSI support for Trino, Spark and Doris backends | 4 | 100% | 2.00 | None |
| 17 | Running DataQualityDashboard on SQL Server | 8 | 62% | 2.38 | None |
| 18 | Modeling oncology episodes and treatments | 13 | 62% | 1.62 | Harmonization |
| 19 | Richer, portable phenotype and concept definitions | 14 | 64% | 1.29 | None |
| 20 | Reusable ETL pipelines into OMOP (CPRD, OpenMRS, microbiology) | 9 | 67% | 1.67 | Harmonization |
| 21 | Representing clinical notes and NLP output | 6 | 100% | 1.33 | Harmonization |
| 22 | Validating CDM compliance and structure | 13 | 54% | 1.62 | None |
| 23 | Deploying Broadsea reliably | 6 | 67% | 2.00 | None |
| 24 | CPT4 vocabulary processing and tool failures | 10 | 30% | 2.10 | None |
| 25 | Domain assignment for labs and measurements | 14 | 50% | 1.57 | Harmonization |
| 26 | Vocabulary release accuracy and maintenance | 4 | 75% | 1.75 | None |
| 27 | Incorrect ICD-10 to SNOMED mappings | 7 | 57% | 1.71 | Harmonization |
| 28 | Creating and maintaining Atlas concept sets | 6 | 50% | 1.83 | None |
| 29 | ATC to RxNorm drug mapping | 6 | 67% | 1.33 | Harmonization |

Suggested merges from the labeling review: 4 with 6 (vocabulary gaps and defects), 12 with 13 (CDM conventions), 11 with 23 (authentication across Atlas, WebAPI and Broadsea). Merged, "vocabulary content gaps and defects" becomes the largest single need at 55 threads.

### 6.1 The harmonization needs in the community's words
- **Combination and compounded drugs lose dose.** "I don't have information on how the total 55 mg dose is split between the two ingredients." Mapping to RxNorm ingredient discards strength; members ask whether an extra table is needed.
- **Oncology codes are missing or duplicated.** "Several ICD-O-3 site/histology/behavior code combinations present in our source data do not exist." Tumor-registry users report duplicate TNM concepts with inconsistent classification and pathology nodal groupings the vocabulary cannot express.
- **Genomics has no production pattern.** "Most CDMs don't yet have genomic data." Members ask for best practice on NGS and comprehensive genomic profiling, variant representation at scale, and linkage to phenotypes; the OMOP Genomic extension is described as having gaps.
- **Lab domain boundaries are ambiguous.** Members cannot tell whether a test belongs in Procedure, Measurement or Observation, and screening encounters land in Measurement.
- **Hierarchy-based mapping silently drops patients.** "897 patients in our system under G23.1 invisible to hierarchy-based query." Another member reports hierarchy code lists missing 21,667 congenital heart disease patients that manual enumeration finds.
- **Conventions are unclear and answers conflict.** Pregnancy episodes, patient-reported drugs without dates, observation periods, missed visits, visit types, NLP outputs: each generates questions whose replies disagree with one another.

### 6.2 The infrastructure needs
Installation and authentication of Atlas/WebAPI (Maven repository outages, LDAP and Active Directory "Bad credentials", roles assigned but no access), Achilles runs that take 18 seconds one day and over an hour the next or fail at 20 hours, DataQualityDashboard checks that run 40 hours on large measurement tables, and connectors that do not support Trino, Spark or Entra ID. These are 36% of blockers. They are not Rhino's product problem, but they are the day-to-day experience of the people Rhino would sell to, and they shape what "easy to deploy" has to mean.

## 7. The multi-site slice

46 substantive threads (11%) involve more than one site or a network study. 87% were unresolved. The 35 with a stated pain point group as follows.

**Cross-site comparability (the core).** "When two sites report a cohort of heart failure patients, they may not mean the same thing." "Any differences could reflect differences in how each dataset was mapped, undermining conclusions." "Sites map drugs to different levels of granularity ... populate their quantity differently." Members want to detect semantic divergence between sites, validate two independently converted datasets against each other, and see results stratified by site in Atlas, which cannot do it.

**Sharing without moving patient data.** "I want to share the prediction results with external collaborators, I'm not allowed to share patient level tables." Published phenotype definitions are "buried in 200 lines of SQL with implicit assumptions" and hard to reproduce outside the OHDSI network.

**Provenance and governance.** Data stewards "will demand to check and verify the data they are supposed to have" when several registries share one CDM; healthcare organizations ask what staffing and capability a sustainable OMOP infrastructure requires.

**Standards gaps that block network use.** Genomic features in PatientLevelPrediction, omics in the CDM, geographic exposures measured against different classification systems, clinical-trial criteria that are observable at some sites and proxied at others.

**Coordination.** Calls for collaborators that get no reply; one member "reached out to community leaders and received little or no response."

Only one thread in two years reports a federated execution failure (a Korean FeederNet estimation run). Nobody asks how to run a study across sites. They ask how to trust the result when they do.

## 8. Trends over eight quarters

| Quarter | Substantive threads | Unresolved | No reply | Announcement share |
|---|---|---|---|---|
| 2024 Q4 | 74 | 74% | 30% | 27% |
| 2025 Q1 | 77 | 49% | 27% | 35% |
| 2025 Q2 | 59 | 81% | 32% | 39% |
| 2025 Q3 | 65 | 51% | 26% | 43% |
| 2025 Q4 | 38 | 76% | 16% | 34% |
| 2026 Q1 | 35 | 80% | 20% | 60% |
| 2026 Q2 | 42 | 90% | 40% | 51% |
| 2026 Q3 | 39 | 77% | 38% | 61% |

Substantive volume roughly halved between the first and second year while the unresolved rate climbed, and the forum's content shifted toward announcements. Within lifecycle stages, vocabulary mapping and ETL questions declined with the overall volume; data quality (14 threads in 2026 Q3, its highest) and network-study and genomics questions held up or rose. Treat the quarterly figures as direction, not measurement.

## 9. Federated opportunity matrix

| Need (cluster) | Community volume | Unmet | Rhino fit | Confidence | Note |
|---|---|---|---|---|---|
| Vocabulary gaps and defects (4, 6, 27, 29) | Very high | High | Data Harmonization Engine | High | Oncology, drug and ICD-10 to SNOMED mapping are concrete feature targets |
| Mapping complex source data (1) | High | High | Data Harmonization Engine | High | Combination drugs, trial instruments, surveys, registries |
| CDM conventions and ETL guidance (12, 13, 20, 21, 25) | High | Medium to high | Data Harmonization Engine | Medium | Opinionated defaults plus explanation would meet a documentation gap the community has not closed |
| Genomic and oncology modeling (2, 18) | Medium | High | Data Harmonization Engine, with Cancer AI Alliance as proof point | Medium | Direct overlap with Rhino's oncology work |
| Cross-site comparability and site-stratified results (10, multi-site slice) | Low to medium | Very high | Federated analytics | Medium | The one clearly federated need; framed as "prove the sites agree", not "run the study" |
| Sharing results and models without patient-level data (multi-site slice) | Low | High | Federated analytics, trusted execution | Medium | PLP results, phenotype definitions, provenance for data stewards |
| Federated learning | Near zero | | Federated learning | High | No forum demand in two years |
| Atlas/WebAPI/Broadsea deployment, Achilles and DQD performance, backend support | High | Very high | None | High | Not Rhino's problem to solve; shapes expectations |

## 10. Implications

### 10.1 For product
- **Harmonization features should target the specific failures members report**: combination and compounded drug dose, ICD-O-3 and TNM oncology concepts, genomic variant and specimen representation, lab domain assignment, and ICD-10 to SNOMED mappings that fall outside the hierarchy. A validator that flags hierarchy-unreachable codes and dose loss would address two of the most quantified complaints.
- **Cross-site comparability is the federated feature the forum asks for.** Detecting semantic divergence between sites (same cohort, different local encoding), validating two independently converted datasets, and site-stratified summaries are the needs that recur. This is also where the Data Harmonization Engine and federated analytics meet.
- **Results sharing without patient-level data** (model outputs, aggregate results, reproducible phenotype definitions with their implementation) is a modest but completely unmet need.
- **Deployment friction is the ambient condition.** Buyers compare any new platform against Atlas/WebAPI installations that took weeks and authentication that never worked. Zero-install and managed authentication are table stakes in this audience.

### 10.2 For marketing and messaging
- Lead with **harmonization** and **"know your sites agree before you trust the result"**, in that order. Those are the two needs the data supports.
- Use the community's own framing: "silently wrong", "undermining conclusions", "not allowed to share patient level tables". Request permission before quoting any individual.
- Oncology and genomics are where OMOP is visibly incomplete and where Rhino has a track record (Cancer AI Alliance). That is a credible wedge.
- The OHDSI audience on the forum is heavily implementers and vocabulary users, not study leads. Study-lead needs live in Teams; messaging aimed at them should be validated there.

### 10.3 What not to claim
- Do not position **federated learning** as a response to OHDSI community demand. It does not appear.
- Do not claim OHDSI members struggle to **run** network studies. Strategus is mentioned seven times in two years and resolved more often than average. The struggle is comparability and sharing, not execution.
- Do not overstate the forum as "the community". It is the public, newcomer-heavy slice of it.

## 11. Reproducibility and AI disclosure
Repository: https://github.com/danieljfeller/ohdsi-community-signals (public). Analysis date: 4 October 2026.

AI use: the pipeline was written and run with Claude Code using Claude Fable 5.1 as the orchestrating model; threads were coded by Claude Haiku 4.5; the reliability sample was re-coded by Claude Sonnet 5.5; need clusters were labeled and mapped by Claude Opus 5.5 and reviewed by the author; this report was drafted by Claude Fable 5.1 from the resulting tables and edited by the author.

All code is in this repository: `collect/forums.py` (paced collector), `process/build_tables.py` (normalization, pseudonymization), `model/coding_schema.md` and `model/coding_prompt.md` (LLM coding), `model/prepare_batches.py`, `model/merge_coding.py`, `model/need_clusters.py`, `model/label_clusters_prompt.md`, `model/topics.py`, `model/unmet_index.py`, `model/reliability.py`. Deliverable tables are in `deliverables/`; raw and intermediate data are excluded from version control.

## Appendix A. Deliverable files
| File | Contents |
|---|---|
| `deliverables/threads_coded.csv` | One row per thread: metadata, pseudonymized author, coded fields, anchored resolution, URL |
| `deliverables/needs_taxonomy.csv` | 29 needs with label, need statement, why hard, Rhino fit and rationale, metrics, quotes, thread IDs |
| `deliverables/need_metrics.csv`, `lifecycle_metrics.csv` | Unmet Need Index components |
| `deliverables/report_tables/` | Multi-site threads, blockers, tools, trends, by-category tables |
| `deliverables/coding_agreement.csv` | Inter-coder reliability |
| `deliverables/coding_schema.md` | The coding schema |

## Appendix B. Method notes and deviations from plan
- GitHub issues were collected and piloted, then dropped (see 3.2).
- Microsoft Teams was not available; the plan describes how to add it.
- Cosine-threshold clustering of need statements collapsed on this embedding model; Ward linkage with a fixed cluster count was used instead and reviewed by hand.
- Resolution status was anchored on reply metadata after the reliability check showed weak coder agreement on that field.
- The topic model over raw posts was retained as a cross-check only; the needs taxonomy built from coded pain-point sentences proved more interpretable on a corpus of this size.
