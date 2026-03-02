# As-Of Queries — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *SQL:2011 — Temporal Features* | Krishna Kulkarni, Jan-Eike Michels | 2012 | <https://dl.acm.org/doi/10.1145/2380776.2380786> |
| *Developing Time-Oriented Database Applications in SQL* | Richard T. Snodgrass | 1999 | <https://www2.cs.arizona.edu/~rts/tdbbook.pdf> |
| *Point-in-Time Correct Joins for Feature Stores* | (Feature Store community) | 2023 | <https://docs.feast.dev/getting-started/concepts/point-in-time-joins> |
| *Lakehouse: A New Generation of Open Platforms* | Armbrust et al. (Databricks) | 2021 | <https://www.cidrdb.org/cidr2021/papers/cidr2021_paper17.pdf> |
| *Delta Lake: High-Performance ACID Table Storage over Cloud Object Stores* | Armbrust et al. | 2020 | <https://dl.acm.org/doi/10.14778/3415478.3415560> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *Developing Time-Oriented Database Applications in SQL* | Richard Snodgrass | 978-1558604360 | Ch 7-9 (temporal query patterns) |
| *Temporal Data & the Relational Model* | C.J. Date, Hugh Darwen, Nikos Lorentzos | 978-1558608559 | Ch 8 (temporal queries), Ch 11 (aggregation) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | 978-1449373320 | Ch 3 (storage & retrieval), Ch 11 (stream processing — temporal semantics) |
| *Feature Store for Machine Learning* | Jim Dowling | 978-1098150761 | Ch 5 (point-in-time correct joins) |
| *Fundamentals of Data Engineering* | Joe Reis, Matt Housley | 978-1098108304 | Ch 8 (queries, transformation — temporal patterns) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *Temporal Tables in SQL Server* | Microsoft Docs | <https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables> |
| *Querying Temporal Tables* | Microsoft Docs | <https://learn.microsoft.com/en-us/sql/relational-databases/tables/querying-data-in-a-system-versioned-temporal-table> |
| *Delta Lake Time Travel* | Delta.io | <https://docs.delta.io/latest/delta-batch.html#query-an-older-snapshot-of-a-table-time-travel> |
| *Apache Iceberg Time Travel* | Iceberg Docs | <https://iceberg.apache.org/docs/latest/spark-queries/#time-travel> |
| *Oracle Flashback Technology* | Oracle Docs | <https://docs.oracle.com/en/database/oracle/oracle-database/19/adfns/flashback.html> |
| *Point-in-Time Correct Joins* | Feast Feature Store | <https://docs.feast.dev/getting-started/concepts/point-in-time-joins> |
| *Zipline: Airbnb's ML Feature Management Platform* | Airbnb Engineering | <https://medium.com/airbnb-engineering/zipline-airbnbs-machine-learning-data-management-platform-ae5a3e7dd4db> |
| *Chronon: Airbnb's Feature Platform* | Airbnb Engineering | <https://medium.com/airbnb-engineering/chronon-airbnbs-ml-feature-platform-is-now-open-source-d9c4c4367f4d> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Time Travel with Delta Lake* | Databricks Team | Data + AI Summit | <https://www.youtube.com/results?search_query=delta+lake+time+travel+summit> |
| *Point-in-Time Correct Feature Engineering* | Feast Community | Feature Store Summit | <https://www.youtube.com/results?search_query=feast+point+in+time+joins> |
| *Temporal Data Management at Scale* | Various | VLDB Conference | <https://www.vldb.org/pvldb/> |
| *Building ML Feature Stores* | Jim Dowling | QCon | <https://www.youtube.com/results?search_query=jim+dowling+feature+store+qcon> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `delta-io/delta` | Delta Lake — built-in time travel | <https://github.com/delta-io/delta> |
| `apache/iceberg` | Apache Iceberg — snapshot-based time travel | <https://github.com/apache/iceberg> |
| `feast-dev/feast` | Feast feature store — point-in-time correct joins | <https://github.com/feast-dev/feast> |
| `airbnb/chronon` | Chronon — Airbnb's ML feature platform | <https://github.com/airbnb/chronon> |
| `nearform/temporal_tables` | PostgreSQL temporal tables extension | <https://github.com/nearform/temporal_tables> |
| `hopsworks/feature-store-api` | Hopsworks feature store (temporal support) | <https://github.com/logicalclocks/feature-store-api> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **SQL Server** | Temporal Tables | <https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables> |
| **SQL Server** | Querying Temporal Tables | <https://learn.microsoft.com/en-us/sql/relational-databases/tables/querying-data-in-a-system-versioned-temporal-table> |
| **PostgreSQL** | Range Types | <https://www.postgresql.org/docs/current/rangetypes.html> |
| **Oracle** | Flashback Query | <https://docs.oracle.com/en/database/oracle/oracle-database/19/adfns/flashback.html> |
| **MariaDB** | System-Versioned Tables | <https://mariadb.com/kb/en/system-versioned-tables/> |
| **Delta Lake** | Time Travel | <https://docs.delta.io/latest/delta-batch.html#query-an-older-snapshot-of-a-table-time-travel> |
| **Apache Iceberg** | Time Travel | <https://iceberg.apache.org/docs/latest/spark-queries/#time-travel> |
| **Apache Hudi** | Time Travel | <https://hudi.apache.org/docs/quick-start-guide/#time-travel> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **Valid vs Transaction Time** | `04_Temporal_and_Bitemporal_Modeling/01_Valid_vs_Transaction_Time/` | As-of queries are the read pattern for bitemporal data |
| **Snapshot Fact Tables** | `04_Temporal_and_Bitemporal_Modeling/03_Snapshot_Fact_Tables/` | Periodic snapshots are pre-materialized as-of results |
| **SCD Extreme Cases** | `02_Dimensional_Modeling_Advanced/02_SCD_Extreme_Cases/` | SCD Types provide valid-time as-of capability |
| **Data Vault Satellites** | `03_Data_Vault_2_0_Architecture/` | Satellite load_date enables transaction-time as-of queries |
