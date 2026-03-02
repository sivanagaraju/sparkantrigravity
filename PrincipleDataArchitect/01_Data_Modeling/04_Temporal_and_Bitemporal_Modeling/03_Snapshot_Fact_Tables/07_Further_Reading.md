# Snapshot Fact Tables — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *The Data Warehouse Lifecycle Toolkit* | Ralph Kimball et al. | 2008 | <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/books/> |
| *Dimensional Modeling Techniques* | Kimball Group | Ongoing | <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/> |
| *Lakehouse: A New Generation of Open Platforms* | Armbrust et al. | 2021 | <https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf> |
| *Delta Lake: High-Performance ACID Table Storage* | Armbrust et al. | 2020 | <https://dl.acm.org/doi/10.14778/3415478.3415560> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *The Data Warehouse Toolkit* (3rd Ed) | Ralph Kimball, Margy Ross | 978-1118530801 | Ch 3 (fact table types — transaction, periodic, accumulating), Ch 4 (inventory snapshots), Ch 10 (financial services snapshots) |
| *Building the Data Warehouse* (4th Ed) | William Inmon | 978-0764599446 | Ch 7 (snapshot architecture), Ch 9 (data warehouse design) |
| *Star Schema: The Complete Reference* | Christopher Adamson | 978-0071744324 | Ch 6 (periodic snapshots), Ch 7 (accumulating snapshots), Ch 8 (factless facts) |
| *Agile Data Warehouse Design* | Lawrence Corr, Jim Stagnitto | 978-0956817204 | Ch 5 (timeline modeling), Ch 8 (snapshot design) |
| *Fundamentals of Data Engineering* | Joe Reis, Matt Housley | 978-1098108304 | Ch 8 (data transformations — aggregation and snapshot patterns) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | 978-1449373320 | Ch 3 (OLAP cubes and materialized views — conceptually related to snapshots) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *Kimball Dimensional Modeling Techniques* | Kimball Group | <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/> |
| *Periodic Snapshot Fact Tables* | Kimball Group Tips | <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/periodic-snapshot-fact-table/> |
| *Accumulating Snapshot Fact Tables* | Kimball Group Tips | <https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/accumulating-snapshot-fact-table/> |
| *Semi-Additive Measures in the Warehouse* | Kimball Group | <https://www.kimballgroup.com/2008/11/fact-tables/> |
| *Materializing Incremental Aggregates with Spark* | Databricks Blog | <https://www.databricks.com/blog/2022/08/22/delta-live-tables-materialized-views.html> |
| *Fact Table Design Patterns* | dbt Labs | <https://docs.getdbt.com/blog/kimball-dimensional-modeling> |
| *Snapshot Tables in dbt* | dbt Documentation | <https://docs.getdbt.com/docs/build/snapshots> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Kimball Dimensional Modeling in the Modern Data Stack* | Various | Coalesce (dbt) | <https://www.youtube.com/results?search_query=kimball+dimensional+modeling+coalesce> |
| *Fact Table Design for Financial Services* | Databricks | Data + AI Summit | <https://www.youtube.com/results?search_query=fact+table+financial+services+databricks+summit> |
| *Building Snapshot Pipelines with dbt* | dbt Community | Coalesce | <https://www.youtube.com/results?search_query=dbt+snapshot+pipeline+coalesce> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `dbt-labs/dbt-core` | dbt snapshot feature (SCD Type 2 snapshots) | <https://github.com/dbt-labs/dbt-core> |
| `delta-io/delta` | Delta Lake — materialze snapshots with time travel | <https://github.com/delta-io/delta> |
| `apache/iceberg` | Iceberg — snapshot isolation and time travel | <https://github.com/apache/iceberg> |
| `kimball-group/kimball-techniques` | Kimball Group's dimensional modeling examples | <https://www.kimballgroup.com/> |
| `apache/spark` | Apache Spark — snapshot generation engine | <https://github.com/apache/spark> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **dbt** | Snapshots (SCD Type 2) | <https://docs.getdbt.com/docs/build/snapshots> |
| **Delta Lake** | Materialized Views | <https://docs.delta.io/latest/delta-batch.html> |
| **Snowflake** | Streams & Tasks (incremental snapshots) | <https://docs.snowflake.com/en/user-guide/streams> |
| **BigQuery** | Materialized Views | <https://cloud.google.com/bigquery/docs/materialized-views-intro> |
| **Redshift** | Materialized Views | <https://docs.aws.amazon.com/redshift/latest/dg/materialized-view-overview.html> |
| **Apache Spark** | Structured Streaming (real-time snapshots) | <https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Valid vs Transaction Time** | `04_Temporal_and_Bitemporal_Modeling/01_Valid_vs_Transaction_Time/` | Snapshots are pre-materialized point-in-time states from temporal data |
| **As-Of Queries** | `04_Temporal_and_Bitemporal_Modeling/02_As_Of_Queries/` | As-of queries against bitemporal tables produce results equivalent to snapshots |
| **Factless Fact Tables** | `02_Dimensional_Modeling_Advanced/03_Factless_Fact_Tables/` | Coverage/event tracking snapshots overlap with factless patterns |
| **Aggregate Tables** | `02_Dimensional_Modeling_Advanced/05_Aggregate_Tables/` | Aggregate tables pre-compute from transaction facts, similar to periodic snapshots |
| **SCD Extreme Cases** | `02_Dimensional_Modeling_Advanced/02_SCD_Extreme_Cases/` | SCD Type 4 (mini-dimension) is conceptually a snapshot of rapidly changing attributes |
