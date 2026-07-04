# gh-pulse-pipeline

An end-to-end ELT pipeline that extracts repository activity (commits, issues, pull requests) from the **GitHub REST API**, loads it into **Snowflake**, and transforms it into an analytics-ready star schema using **dbt**, orchestrated by **Airflow**.

Built as a companion to [SnowOps Intelligence](#) — that project monitors and optimizes the warehouse this pipeline feeds.

## Why this project

Most portfolio ELT projects load a static Kaggle CSV. This one builds the extraction layer from scratch against a live, paginated, rate-limited API — the part of the pipeline that's usually skipped, and the part that actually breaks in production.

## Architecture

```
GitHub REST API
      │
      ▼
[Extractor: Python]  ──►  raw JSON landed in Snowflake (RAW schema)
      │
      ▼ (orchestrated by)
   [Airflow DAG]
      │
      ▼
   [dbt run]
      │
      ├─ staging      (clean, typed, 1:1 with source)
      ├─ intermediate (deduped, business logic)
      └─ marts        (star schema: fact_commits, fact_issues, dim_repo, dim_author)
      │
      ▼
 [dbt test]  ──►  not_null, unique, relationships, freshness
      │
      ▼
   Analytics-ready tables in Snowflake
```

## Tech stack

| Layer          | Tool                          |
|----------------|--------------------------------|
| Extraction     | Python, `requests`, PyGithub API |
| Orchestration  | Apache Airflow (Docker Compose) |
| Warehouse      | Snowflake                      |
| Transformation | dbt-core (dbt-snowflake adapter) |
| Testing        | dbt tests, `sqlfluff` lint      |
| CI             | GitHub Actions                 |

## Repo structure

```
.
├── dags/                   # Airflow DAG definitions
│   └── github_elt_dag.py
├── extract/                # Extraction scripts (API → raw Snowflake tables)
│   └── github_extractor.py
├── dbt_project/            # dbt models, tests, docs
│   ├── models/
│   │   ├── staging/
│   │   ├── intermediate/
│   │   └── marts/
│   └── dbt_project.yml
├── .github/workflows/      # CI: dbt test + lint on PR
├── docs/                   # Architecture diagrams, screenshots
├── docker-compose.yml      # Local Airflow
├── .env.example
└── requirements.txt
```

## What this demonstrates

- **Extraction engineering**: pagination, rate-limit handling, incremental loads (not just a one-time CSV dump)
- **Orchestration**: dependency management, retries, scheduling via Airflow
- **Analytics engineering**: layered dbt models, dimensional modeling, documented lineage
- **Data quality**: automated tests wired into CI, not just eyeballed once
- **Ops discipline**: config via env vars, no hardcoded secrets, reproducible via Docker

## Setup

```bash
git clone <this-repo>
cd gh-pulse-pipeline
cp .env.example .env   # fill in GITHUB_TOKEN and Snowflake credentials
docker compose up -d
# Airflow UI at localhost:8080 — trigger `github_elt_dag`
```

## Sample output

*(screenshots of dbt docs lineage graph + Airflow DAG graph go here once built)*

## Status

🚧 Work in progress — built incrementally, commit history reflects each stage (extraction → orchestration → modeling → testing → CI).
