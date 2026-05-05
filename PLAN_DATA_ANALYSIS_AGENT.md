# Plan: Data Analysis Agent (v1 -> Growth Path)

This document captures a practical first version of a data analysis agent and
how it should evolve over time.

## Goals

- Start with a small graph that answers a natural-language data question.
- Keep execution deterministic and safe (sandboxed code, bounded inputs).
- Produce both artifacts (tables/charts) and narrative interpretation.
- Preserve a clean upgrade path to multi-node, multi-agent workflows.

## v1 Node Topology (Implemented)

Core flow:

1. `ingest_question`
2. `route_query_answerability` (conditional edge from `ingest_question`)
3. `unanswerable_query` (early END branch)
4. `load_dataset_context`
5. `analyze_first_vs_rest`
6. `summarize_results`

Graph shape:

- `START -> ingest_question`
- `ingest_question -> (answerable) -> load_dataset_context -> analyze_first_vs_rest -> summarize_results -> END`
- `ingest_question -> (unanswerable) -> unanswerable_query -> END`

Notes:

- The unanswerable branch must print exactly `this query can't be answered by the data`.
- v1 uses deterministic routing and local parquet-only analysis.

## Node Responsibilities

### `ingest_question`

- Normalize user intent.
- Ensure user message is in state.
- Extract high-level analysis goal and constraints.

### `route_query_answerability`

- Route query to `answerable` or `unanswerable` using deterministic keywords.
- Reject out-of-domain questions (weather/news/finance style prompts).

### `unanswerable_query`

- Print exact required message and terminate cleanly.

### `load_dataset_context`

- Load `data/dataset.parquet` via `DataLoader.load_data_from_local`.
- Avoid all remote loading in runtime path.

### `analyze_first_vs_rest`

- Derive `is_first_turn` from `message_index == 0`.
- Compute deterministic first-vs-rest metrics:
  - row counts
  - average text length
  - question-mark rate
  - lexical cue rate (`why`)
- Emit short plain-language interpretation.

### `summarize_results`

- Build final report payload and print concise output.

## State Contract (Suggested)

Use a typed state object with:

- `user_query`
- `analysis_goal`
- `route`
- `dataframe_path`
- `analysis_result`
- `report`

## v1 Deliverables

- LangGraph wiring with answerability router and early END path.
- Stable state schema for deterministic local analytics.
- First-turn-vs-rest metrics and interpretation for answerable queries.

## Growth Path

### v2: Reliability + Repair

- Add `repair_code` path when execution fails.
- Add retry policy and explicit failure surface in report.

### v3: Better Data Access

- Add specialized retrieval tools (SQL warehouse + local files).
- Introduce schema/RAG helper for large data catalogs.

### v4: Governance + Safety

- Table allowlists, row/byte limits, and sensitive-field masking.
- Structured audit logs for generated code and queries.

### v5: Quality + Productization

- Golden eval set for canonical questions.
- Session memory for iterative analyses.
- Optional human approval node for expensive or risky queries.

## Mapping to Existing Lit Review Pattern

- `collect_query` -> `ingest_question`
- `diversify_queries` -> `plan_analysis`
- `fan_out_tavily` -> `fan_out_subtasks`
- `tavily_search` -> `worker_analyze`
- `merge_paper_results` -> `merge_results`
- `draft_summary` -> `interpret_results` + `finalize_report`

This preserves the same mental model while changing the tooling from web
search to data retrieval and analysis execution.
