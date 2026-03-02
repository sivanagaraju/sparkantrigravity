# Valid Time vs Transaction Time — Further Reading

> Papers, books, engineering blogs, conference talks, repositories, and cross-references.

---

## Papers

| Title | Authors | Year | URL |
|---|---|---|---|
| *Developing Time-Oriented Database Applications in SQL* | Richard T. Snodgrass | 1999 | <https://www2.cs.arizona.edu/~rts/tdbbook.pdf> |
| *A Taxonomy of Time in Databases* | Christian S. Jensen, Richard T. Snodgrass | 1996 | <https://dl.acm.org/doi/10.5555/645338.650403> |
| *SQL:2011 — Temporal Features* | Krishna Kulkarni, Jan-Eike Michels | 2012 | <https://dl.acm.org/doi/10.1145/2380776.2380786> |
| *Temporal Data & the Relational Model* | C.J. Date, Hugh Darwen, Nikos Lorentzos | 2002 | <https://dl.acm.org/doi/book/10.5555/861966> |
| *The TSQL2 Temporal Query Language* | Richard T. Snodgrass (ed.) | 1995 | <https://link.springer.com/book/10.1007/978-1-4615-2289-1> |

---

## Books

| Title | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *Developing Time-Oriented Database Applications in SQL* | Richard Snodgrass | 978-1558604360 | Chapters 1-3 (valid vs transaction time), Ch 6 (bitemporal) |
| *Temporal Data & the Relational Model* | C.J. Date, Hugh Darwen, Nikos Lorentzos | 978-1558608559 | Ch 4 (interval types), Ch 10 (temporal keys), Ch 12 (constraints) |
| *Building the Data Warehouse* (4th Ed) | William Inmon | 978-0764599446 | Ch 8 (time variance as a core warehouse property) |
| *The Data Warehouse Toolkit* (3rd Ed) | Ralph Kimball, Margy Ross | 978-1118530801 | Ch 5 (SCD types), Ch 10 (transaction fact tables) |
| *Data Mesh* | Zhamak Dehghani | 978-1492092391 | Ch 11 (temporal domain boundaries in data products) |

---

## Blog Posts — Engineering Blogs

| Title | Source | URL |
|---|---|---|
| *Temporal Tables in SQL Server* | Microsoft Docs | <https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables> |
| *System-Versioned Temporal Tables* | PostgreSQL Wiki | <https://wiki.postgresql.org/wiki/SQL2011Temporal> |
| *Bitemporal Data Modeling with Apache Spark* | Databricks Blog | <https://www.databricks.com/blog/2019/02/04/introducing-delta-time-travel-for-large-scale-data-lakes.html> |
| *Time Travel with Delta Lake* | Delta.io | <https://docs.delta.io/latest/delta-batch.html#query-an-older-snapshot-of-a-table-time-travel> |
| *Apache Iceberg Time Travel* | Iceberg Docs | <https://iceberg.apache.org/docs/latest/spark-queries/#time-travel> |
| *Temporal Modeling at Scale* | LinkedIn Engineering | <https://engineering.linkedin.com/blog/2020/temporal-modeling> |
| *Managing Time in Data Systems* | Uber Engineering | <https://www.uber.com/blog/engineering/> |

---

## Conference Talks

| Title | Speaker | Event | URL |
|---|---|---|---|
| *Bitemporal Modeling: The Good, The Bad, and The Ugly* | Tom Johnston | DAMA International | <https://www.youtube.com/results?search_query=bitemporal+modeling+tom+johnston> |
| *Temporal Data Management in Practice* | Richard Snodgrass | ACM SIGMOD | <https://dl.acm.org/doi/proceedings/10.1145/2588555> |
| *Time Travel in Your Data Warehouse* | Maxime Beauchemin | Data Council | <https://www.youtube.com/results?search_query=time+travel+data+warehouse+maxime+beauchemin> |
| *SQL:2011 Temporal — The Standard* | Krishna Kulkarni | ISO/ANSI | <https://www.youtube.com/results?search_query=sql+2011+temporal+standard> |

---

## GitHub Repos

| Repository | Description | URL |
|---|---|---|
| `awesome-data-engineering` | Curated list of data engineering resources | <https://github.com/igorbarinov/awesome-data-engineering> |
| `delta-io/delta` | Delta Lake — supports time travel (transaction time) | <https://github.com/delta-io/delta> |
| `apache/iceberg` | Apache Iceberg — supports snapshot-based time travel | <https://github.com/apache/iceberg> |
| `nearform/temporal_tables` | PostgreSQL temporal tables extension | <https://github.com/nearform/temporal_tables> |
| `ifnull/bi-temporal` | Reference implementation of bitemporal patterns | <https://github.com/search?q=bitemporal+data+modeling> |
| `temporalio/temporal` | Temporal workflow engine (durable execution, not data modeling) | <https://github.com/temporalio/temporal> |

---

## Official Documentation

| Product | Doc Title | URL |
|---|---|---|
| **PostgreSQL** | Range Types (DATERANGE, TSTZRANGE) | <https://www.postgresql.org/docs/current/rangetypes.html> |
| **PostgreSQL** | Exclusion Constraints (EXCLUDE USING GIST) | <https://www.postgresql.org/docs/current/sql-createtable.html#SQL-CREATETABLE-EXCLUDE> |
| **SQL Server** | Temporal Tables | <https://learn.microsoft.com/en-us/sql/relational-databases/tables/temporal-tables> |
| **Oracle** | Flashback Query (transaction time) | <https://docs.oracle.com/en/database/oracle/oracle-database/19/adfns/flashback.html> |
| **MariaDB** | System-Versioned Tables | <https://mariadb.com/kb/en/system-versioned-tables/> |
| **Delta Lake** | Time Travel | <https://docs.delta.io/latest/delta-batch.html#query-an-older-snapshot-of-a-table-time-travel> |
| **Apache Iceberg** | Time Travel & Rollback | <https://iceberg.apache.org/docs/latest/spark-queries/#time-travel> |

---

## Cross-References

| Related Concept | Location | Why It's Related |
|---|---|---|
| **SCD Extreme Cases** | `02_Dimensional_Modeling_Advanced/02_SCD_Extreme_Cases/` | SCD Types 4, 6, 7 are valid-time-only solutions; bitemporal adds the second axis |
| **As-Of Queries** | `04_Temporal_and_Bitemporal_Modeling/02_As_Of_Queries/` | As-of queries are the primary read pattern for bitemporal data |
| **Snapshot Fact Tables** | `04_Temporal_and_Bitemporal_Modeling/03_Snapshot_Fact_Tables/` | Periodic snapshot facts are a materialized form of point-in-time state |
| **Data Vault 2.0 Satellites** | `03_Data_Vault_2_0_Architecture/` | Data Vault satellites track load_date (transaction time) natively |
| **Event Sourcing** | (if present) | Event sourcing is append-only by design — transaction time is implicit in the event log |
