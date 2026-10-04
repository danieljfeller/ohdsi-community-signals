You are labeling clusters of pain points expressed by members of the OHDSI community (open-science collaborative around the OMOP Common Data Model). Input: `data/processed/need_clusters_summary.json`, a list of clusters each with representative pain-point sentences, jobs-to-be-done, evidence quotes, categories, lifecycle stages and metrics.

For EACH cluster write one JSON object per line to the output path given to you, with keys:
- `cluster` (copy)
- `label`: 3 to 7 words, a noun phrase naming the need (e.g. "Mapping local lab codes to LOINC").
- `need_statement`: one sentence starting with "Community members need to ..." grounded ONLY in the representative sentences.
- `why_hard`: one sentence on what makes it hard today, grounded in the text; `null` if the text does not say.
- `rhino_fit`: one of `federated_analytics` | `federated_learning` | `data_harmonization` | `trusted_execution_governance` | `none`. Choose `none` unless the need is clearly about running analysis across institutions, training models across institutions, converting or mapping source data to OMOP/vocabularies, or executing code on data that cannot leave an institution.
- `rhino_fit_rationale`: one sentence. Be conservative; say "none" for tool bugs, UI issues, documentation gaps, events and community process.
- `confidence`: `high` | `medium` | `low`.

No commentary, no fences. Finish by printing how many lines you wrote.
