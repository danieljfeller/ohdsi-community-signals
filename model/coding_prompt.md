You are coding threads from the OHDSI community (an open-science collaborative around the OMOP Common Data Model and its tools) for a product research study. Read `model/coding_schema.md` for the exact schema and rules, then read the batch file given to you (one JSON thread digest per line).

For EVERY thread in the batch, write exactly one JSON object (one per line, no commentary, no markdown fences) to the output path given to you. Keys and allowed values must follow the schema exactly. Use `null` for unknown scalar fields and `[]` for empty lists.

Guidance:
- The opening post is the need statement; replies tell you whether it was met. If `n_replies_by_others` is 0, `resolution_status` is `no_reply` unless the poster says they solved it themselves (then `resolved`, `workaround_present` may be true).
- `pain_point` is about the poster's experience of friction. A pure announcement, job posting, or maintainer to-do normally has `pain_point: null` and `severity: none`.
- Be literal and conservative. Do not infer federated or multi-site context from the word "network" alone; look for multiple sites, data partners, distributed execution, or data that cannot leave an institution.
- Keep `evidence_quote` verbatim from the opening post and under 25 words.
- Write `pain_point` and `job_to_be_done` as full sentences a product manager could read without the thread (name the tool and the task).
- `job_to_be_done` is the poster's UNDERLYING GOAL with their data (e.g. "Run a characterization study across several hospitals' OMOP databases"), never a restatement of the requested fix ("Fix the batch size option"). Ask: why do they want this fixed? If the thread gives no clue beyond the fix itself, use `null`.
- `evidence_quote` must be under 25 words; cut it rather than exceed.

Finish by printing the number of lines you wrote and any thread_ids you could not code.
