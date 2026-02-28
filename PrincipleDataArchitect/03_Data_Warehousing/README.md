# 03 — Data Warehousing: From Kimball to Cloud-Native MPP

> "A data warehouse is not a technology. It is an architectural contract: the business will always be able to answer questions about its past."

At the Principal level, you don't just "use Snowflake." You understand why Snowflake's multi-cluster shared data architecture solves problems that Redshift's shared-nothing architecture cannot (and vice versa). You have opinions on when Kimball is dead and when it's the only sane choice.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_DW_Philosophy_And_Methodology/`

- **Inmon vs. Kimball vs. Data Vault — The Holy War**: Not "which is best," but which is optimal for *your specific organizational maturity, team size, and data volatility.*
- **The Enterprise Bus Architecture**: Kimball's conforming dimensions — how to design dimensions that are shared across 20 different fact tables without creating a maintenance nightmare.
- **The Death (and Resurrection) of the Semantic Layer**: Why the universal semantic layer collapsed in the 2010s, and why Looker/dbt Metrics/AtScale are bringing it back in 2025.

### `02_MPP_Engine_Internals/`

- **Snowflake Architecture**: Multi-cluster shared data. Micro-partitions (50–500MB immutable columnar files). Automatic clustering vs. manual cluster keys. The economics of warehouse auto-suspend and auto-resume.
- **Redshift Architecture**: Leader + compute nodes. Distribution styles (KEY, EVEN, ALL, AUTO). Sort keys (compound vs. interleaved). Why VACUUM and ANALYZE are life or death for query performance.
- **BigQuery Architecture**: Dremel's tree-based execution. Slots as the unit of compute. Capacitor columnar format. Why BigQuery bills by bytes-scanned and how to use clustering + partitioning to reduce costs by 95%.
- **Synapse Analytics**: Dedicated SQL pools (MPP) vs. Serverless SQL pools. Distribution hash and replicated tables. Workload management and resource classes.

### `03_Advanced_SCD_Implementation/`

- **SCD Type 0 (Fixed)**: Birth date. Never changes. Simple.
- **SCD Type 1 (Overwrite)**: Destroys history. When this is acceptable (and when it's career-ending).
- **SCD Type 2 (Historical Rows)**: The standard. Surrogate keys, effective_date/expiry_date, is_current flag. The join explosion problem at petabyte scale.
- **SCD Type 3 (Previous Value Column)**: Storing only "one version back." Fast but lossy.
- **SCD Type 4 (Mini-Dimension)**: Breaking rapidly changing attributes into separate dimension tables.
- **SCD Type 6 (Hybrid 1+2+3)**: Current + historical + previous — the most complex but most flexible.
- **SCD Type 7 (Dual Keys)**: Both surrogate and natural keys in the fact table for query flexibility.

### `04_Modern_DW_Patterns/`

- **The Activity Schema**: An alternative to traditional star schemas for event-heavy data (gaming, IoT, clickstream).
- **Wide Tables / One Big Table (OBT)**: The controversial denormalized approach. When 500-column tables outperform joins on modern columnar engines and when they become unmaintainable.
- **Zero-Copy Cloning**: Snowflake's game-changing feature. Creating instant, cost-free copies for development, testing, or debugging production issues.
- **Time Travel and Fail-Safe**: Querying data as it existed N days ago. Using this for incident response vs. using it as a lazy backup strategy (and why the latter fails).

---
*Part of [Principal Data Architect Learning Path](../README.md)*
