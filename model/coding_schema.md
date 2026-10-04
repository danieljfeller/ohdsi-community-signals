# Thread coding schema (LLM structured coding)

Code each thread from the OHDSI community (forum topic or GitHub issue). Output ONE JSON object per thread, exactly these keys:

- `thread_id`: copy from input.
- `post_type`: one of `question` | `bug` | `feature_request` | `announcement` | `discussion` | `job_or_event` | `dev_task` (internal maintainer to-do with no user-facing need) | `other`.
- `lifecycle_stage`: list, zero or more of: `etl_cdm_conversion`, `vocabulary_mapping`, `data_quality`, `cohort_definition`, `characterization`, `estimation`, `prediction_ml`, `network_study_execution`, `infrastructure_deployment`, `governance_privacy`, `results_sharing_dissemination`, `learning_onboarding`, `community_process`.
- `tools`: list of tool names mentioned or clearly implied, from: Atlas, WebAPI, Achilles, DataQualityDashboard, Strategus, HADES (generic), CohortDiagnostics, CohortGenerator, FeatureExtraction, CohortMethod, PatientLevelPrediction, DeepPLP, SelfControlledCaseSeries, Characterization, Capr, CirceR, Usagi, WhiteRabbit, RabbitInAHat, Perseus, Athena, Vocabulary, CommonDataModel, DatabaseConnector, SqlRender, Broadsea, Ares, Data2Evidence, CDMConnector/DARWIN packages (OmopSketch, PhenotypeR, CohortConstructor, etc.), Eunomia, Synthea, GIS, R, Python, Docker, Databricks, Snowflake, Postgres, SQL Server, BigQuery, other.
- `pain_point`: ONE sentence, in the poster's terms, describing what is hard, broken, missing, or confusing. `null` if none.
- `job_to_be_done`: ONE sentence: what the poster is ultimately trying to accomplish. `null` if unclear.
- `severity`: `blocker` (cannot proceed) | `major` (significant effort or risk) | `minor` | `none`.
- `workaround_present`: true if the thread describes a workaround (by poster or repliers), else false.
- `resolution_status`: from the WHOLE thread: `resolved` | `partially` | `unresolved` | `unclear` | `no_reply`.
- `multi_site_context`: true if the thread involves more than one data partner/site, a network study, federated or distributed execution, sending code or results across institutions, or data that cannot leave an institution.
- `harmonization_context`: true if the thread is about converting source data to OMOP, mapping vocabularies, or data quality of a CDM instance.
- `evidence_quote`: verbatim span from the opening post under 25 words that best shows the pain point. `null` if no pain point.
- `confidence`: `high` | `medium` | `low`.

Rules: Do not invent needs that are not in the text. A maintainer's own refactoring to-do is `dev_task` with `pain_point: null` unless it explicitly cites user-reported friction. Write pain points and jobs as complete sentences a product manager could read without the thread.
