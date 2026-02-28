# 05 — Batch Data Pipelines: ETL, ELT & Orchestration

> "Every pipeline that runs in production is a promise to the business. Break the promise, and the CEO's morning dashboard shows yesterday's numbers."

Batch pipelines are the backbone of every data platform. A Principal Architect designs pipelines that are idempotent, auditable, self-healing, and cheap to operate — not just pipelines that "work on my laptop."

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_ETL_vs_ELT_Decision_Framework/`

- **When ETL Wins**: Sensitive PII that must be masked *before* landing in the warehouse. Legacy sources with garbage schemas that need cleaning upfront.
- **When ELT Wins**: Modern cloud warehouses (Snowflake, BigQuery) where compute is elastic and transformation is faster inside the engine than outside.
- **The Hidden Cost of ELT**: Loading raw data into a $50/credit Snowflake warehouse and running 200 dbt models on it is sometimes 10x more expensive than transforming in a $0.05/hour Spark cluster first.

### `02_Orchestration_Deep_Dive/`

- **Airflow Internals**: The Scheduler, the Executor (Local, Celery, Kubernetes), the Metadata DB. Why a single Airflow scheduler becomes a bottleneck at 5,000+ DAGs and how to shard it.
- **Dagster vs. Prefect vs. Mage**: Software-defined assets (Dagster) vs. task-centric (Airflow). When Dagster's asset lineage graph makes complex pipelines 10x easier to debug.
- **DAG Design Anti-Patterns**: The "God DAG" (1 DAG with 500 tasks), the "Micro-DAG" (500 DAGs with 1 task each), and the "Cross-DAG Dependency Hell" (DAG A waits for DAG B via ExternalTaskSensor).
- **Idempotency by Design**: Every task must produce the same output if re-run. Using `INSERT OVERWRITE` / `MERGE` / `DELETE + INSERT` patterns. Why `INSERT INTO` without deduplication is a ticking time bomb.

### `03_dbt_Transformation_Mastery/`

- **Incremental Models**: Only processing new/changed rows. The `unique_key` deduplication logic. Handling late-arriving data that falls outside the incremental window.
- **Snapshots (SCD Type 2 in dbt)**: How dbt's `dbt snapshot` command implements Type 2 slowly changing dimensions using `check` or `timestamp` strategies.
- **The Ref Graph and Execution Order**: Why `{{ ref('model_name') }}` isn't just a convenience — it builds the DAG that determines parallel execution order.
- **dbt Testing Philosophy**: `not_null`, `unique`, `accepted_values`, `relationships` — and custom generic tests. Data contracts enforced at transformation time.

### `04_Pipeline_Reliability_Engineering/`

- **Backfill Strategies**: Re-processing 6 months of historical data without disrupting current production jobs. Partitioned backfills, parallel backfills, and progressive backfills.
- **Dead Letter Queues for Batch**: What happens when 0.01% of records fail validation? Do you halt the entire pipeline or route them to a quarantine table for manual remediation?
- **Pipeline SLAs and Alerting**: Defining "Data must be fresh by 7:00 AM EST" and building automated monitors that page the on-call engineer when ETL finishes late.
- **Cost Estimation Before Execution**: Calculating expected Snowflake credits or BigQuery bytes-scanned *before* a pipeline runs, and aborting if the estimate exceeds a threshold.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
