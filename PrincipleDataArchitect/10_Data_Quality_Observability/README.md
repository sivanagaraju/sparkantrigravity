# 10 — Data Quality & Observability

> "You don't need perfect data. You need data whose imperfections you can measure, explain, and alert on."

Data quality at the Principal level is not about running a few `NOT NULL` checks. It is about building a culture and infrastructure where quality is **measured continuously**, **enforced at boundaries**, and **visible to everyone** — from the data engineer to the CFO.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Quality_Dimensions_And_Metrics/`

- **The 6 Pillars**: Accuracy, Completeness, Consistency, Timeliness, Validity, Uniqueness. Defining each with concrete, measurable thresholds (e.g., "Customer email completeness must be ≥ 98.5%").
- **DQ Scorecards**: Rolling up quality metrics into a single score per data product, domain, or pipeline. Executive dashboards that show quality trends over time.
- **The Cost of Bad Data**: Gartner estimates that poor data quality costs organizations an average of $12.9 million annually. Quantifying the downstream impact: wrong financial reports, failed ML models, lost customer trust.

### `02_Data_Quality_Tools_Deep_Dive/`

- **Great Expectations**: Writing "expectations" as code (Python). `expect_column_values_to_not_be_null()`, `expect_column_mean_to_be_between()`. Data Docs for auto-generated HTML reports. Integrating into Airflow/dbt pipelines.
- **Soda Core**: SQL-based checks (`checks for orders: row_count > 0`, `missing_count(email) < 5%`). Soda Cloud for centralized monitoring.
- **dbt Tests**: Built-in tests (`unique`, `not_null`, `accepted_values`, `relationships`) + custom SQL tests. Why dbt tests run *inside* the warehouse and are therefore the cheapest quality gate.
- **Monte Carlo, Bigeye, Anomalo**: ML-powered anomaly detection. Automatically detecting "revenue dropped 40% on Tuesday" before anyone runs a query. The trade-off between noise (false positives) and coverage.

### `03_Data_Observability/`

- **The 5 Pillars of Data Observability**: Freshness (is data arriving on time?), Volume (did we receive the expected number of rows?), Schema (did the schema change unexpectedly?), Distribution (did numeric distributions shift?), Lineage (what changed upstream?).
- **Building vs. Buying**: Writing custom Airflow sensors and SQL checks vs. deploying Monte Carlo or Bigeye. The hidden cost of maintaining a custom observability system.
- **Alert Fatigue**: The #1 killer of data observability programs. If every alert is "urgent," no alert gets attention. Designing severity tiers and suppression rules.

### `04_Quality_Gates_In_Medallion_Architecture/`

- **Bronze Gate**: Schema validation, deduplication, null-key detection. Quarantine malformed records to a dead-letter table.
- **Silver Gate**: Business rule validation (e.g., `order_amount > 0`, `country_code IN valid_countries`). Referential integrity checks across domains.
- **Gold Gate**: Reconciliation against source-of-truth. Aggregate-level checks (daily revenue in Gold must match daily revenue calculated from Bronze within 0.01%).
- **Circuit Breakers**: Automatically halting a pipeline if a quality gate fails, rather than propagating bad data to production dashboards where the CEO sees it first.

### `05_Data_Reconciliation/`

- **Source-to-Target Reconciliation**: Comparing row counts, checksums, and aggregates between source systems and the data lake/warehouse.
- **Cross-System Reconciliation**: When the CRM says 50,000 customers and the DW says 48,500, building the detective query to find the 1,500 missing records.
- **Drift Detection**: Statistical tests (KS test, Chi-squared) to detect when the distribution of incoming data shifts significantly from historical baselines.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
