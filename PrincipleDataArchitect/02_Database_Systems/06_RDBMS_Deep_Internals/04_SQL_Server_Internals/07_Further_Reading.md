# SQL Server Internals — Further Reading

## Books

| Book | Author(s) | Key Contribution |
|---|---|---|
| *Pro SQL Server Internals, 2nd Ed.* | Dmitri Korotkevitch | Most comprehensive SQL Server internals reference; covers page structure, indexes, locking, tempdb, columnstore, in-memory OLTP |
| *SQL Server Internals: In-Memory OLTP* | Kalen Delaney | Deep dive into Hekaton architecture, garbage collection, natively compiled procedures |
| *SQL Server 2022 Query Performance Tuning, 6th Ed.* | Grant Fritchey | Query Store, intelligent query processing, execution plan analysis |
| *SQL Server Advanced Troubleshooting and Performance Tuning* | Dmitri Korotkevitch | Wait stats methodology, lock analysis, tempdb tuning for production |
| *SQL Server Execution Plans, 3rd Ed.* | Grant Fritchey | Understanding and tuning execution plans — essential for parameter sniffing diagnosis |

## Engineering Blog Posts

| Title | Source | Key Topic |
|---|---|---|
| *Brent Ozar's SQL Server Wait Stats Library* | brentozar.com | Definitive wait type reference with action items per wait type |
| *SQLSkills Accidental DBA Series* | sqlskills.com (Paul Randal, Kimberly Tripp) | Storage Engine internals from the people who built it |
| *Implementing Snapshot or Read Committed Snapshot Isolation* | brentozar.com | Practical RCSI deployment guide |
| *Understanding Columnstore Indexes* | red-gate.com | Rowgroup quality, segment elimination, batch mode |
| *Accelerated Database Recovery (ADR) In-Depth* | Microsoft Blog | PVS architecture, instant rollback, impact on log truncation |
| *Parameter Sniffing: The Silent Killer* | erikdarling.com | Diagnosis and multiple fix approaches |
| *Inside the SQL Server Query Store* | sqlshack.com | Architecture, forced plans, automatic tuning |

## Conference Talks

| Title | Speaker | Event | Year |
|---|---|---|---|
| *SQL Server Internals — A Deep Dive* | Paul Randal | PASS Summit | 2023 |
| *Wait Statistics — Your Diagnostic Framework* | Paul Randal | SQLBits | 2023 |
| *How SQL Server Stores Data* | Kimberly Tripp | PASS Summit | 2022 |
| *Query Store and Automatic Tuning* | Conor Cunningham | Microsoft Ignite | 2023 |
| *Columnstore Indexes — Internals and Performance* | Niko Neugebauer | SQLBits | 2023 |
| *In-Memory OLTP Deep Dive* | Dmitri Korotkevitch | Data Platform Summit | 2022 |

## GitHub Repositories / Tools

| Tool | Description |
|---|---|
| BrentOzarULTD/SQL-Server-First-Responder-Kit | `sp_Blitz`, `sp_BlitzFirst`, `sp_BlitzIndex` — production diagnostic scripts |
| olahallengren/sql-server-maintenance-solution | Standard maintenance: index + statistics rebuilds, backup, integrity checks |
| erikdarlingdata/DarlingData | Advanced diagnostic stored procedures (sp_HumanEvents, sp_PressureDetector) |
| microsoft/tigertoolbox | Microsoft Tiger Team scripts for SQL Server best practices |
| spaghettidba/WorkloadTools | Workload analysis and replay tools |
| SQLUndercover/UndercoverToolbox | Monitoring and alerting framework |

## Official Documentation

| Topic | URL |
|---|---|
| SQL Server Architecture Guide | https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-architecture-guide |
| Database Engine Internals | https://learn.microsoft.com/en-us/sql/relational-databases/pages-and-extents-architecture-guide |
| Transaction Log Architecture | https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-transaction-log-architecture-and-management-guide |
| Columnstore Indexes Guide | https://learn.microsoft.com/en-us/sql/relational-databases/indexes/columnstore-indexes-overview |
| In-Memory OLTP Overview | https://learn.microsoft.com/en-us/sql/relational-databases/in-memory-oltp/overview-and-usage-scenarios |
| Query Store | https://learn.microsoft.com/en-us/sql/relational-databases/performance/monitoring-performance-by-using-the-query-store |
| Wait Types Reference | https://learn.microsoft.com/en-us/sql/relational-databases/system-dynamic-management-views/sys-dm-os-wait-stats-transact-sql |
| Accelerated Database Recovery | https://learn.microsoft.com/en-us/sql/relational-databases/accelerated-database-recovery |

## Cross-References

| Related Topic | Location |
|---|---|
| PostgreSQL Internals (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/01_PostgreSQL_Internals/` |
| MySQL InnoDB (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/02_MySQL_InnoDB/` |
| Oracle Architecture (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/03_Oracle_Architecture/` |
| MVCC Internals (general) | `02_Database_Systems/02_Transactions_and_Consistency/01_MVCC_Internals/` |
| Database Reliability Engineering | `02_Database_Systems/05_Database_Reliability_Engineering/` |
