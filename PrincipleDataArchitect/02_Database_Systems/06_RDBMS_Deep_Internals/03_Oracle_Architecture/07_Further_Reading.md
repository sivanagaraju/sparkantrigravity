# Oracle Database Architecture — Further Reading

## Books

| Book | Author(s) | Key Contribution |
|---|---|---|
| *Expert Oracle Database Architecture, 3rd Ed.* | Thomas Kyte, Darl Kuhn | Definitive Oracle internals — architecture, concurrency, redo, undo, transactions. The "bible" for Oracle architects |
| *Oracle Core: Essential Internals for DBAs and Developers* | Jonathan Lewis | Deep dive into block internals, redo, undo, latches, locks. Advanced-level |
| *Troubleshooting Oracle Performance, 2nd Ed.* | Christian Antognini | Optimizer internals, execution plan analysis, wait event troubleshooting |
| *Oracle Database 12c Release 2 Multi-Tenant* | Anton Els, Franck Pachot | Multitenant architecture, PDB management, CDB architecture |
| *Cost-Based Oracle Fundamentals* | Jonathan Lewis | How the Oracle CBO works internally, statistics, histograms, selectivity models |
| *Oracle Wait Interface: A Practical Guide* | Richmond Shee, Kirtikumar Deshpande | Wait event-based performance tuning methodology |

## Engineering Blog Posts

| Title | Source | Key Topic |
|---|---|---|
| *Understanding Oracle's Read Consistency* | Ask Tom (Tom Kyte) | Definitive explanation of SCN-based consistent reads |
| *Oracle RAC Internals: Cache Fusion Explained* | Oracle Technology Network | Block transfers, GCS/GES protocols |
| *Inside the Oracle Optimizer* | Oracle Dev Blog | Adaptive plans, SQL Plan Baselines, optimizer stats |
| *AWR and ASH: Performance Diagnostic Overview* | Oracle DBA Blog | How to read AWR reports, ASH sampling methodology |
| *Oracle Redo and Recovery Architecture* | Oracle Architecture Blog | Online redo logs, archived logs, recovery process |
| *Managing Undo: ORA-01555 Prevention* | Percona Blog | Sizing undo tablespace, retention strategies |

## Conference Talks

| Title | Speaker | Event | Year |
|---|---|---|---|
| *Oracle Database Architecture Masterclass* | Tom Kyte | Oracle OpenWorld | 2019 |
| *Deep Dive into Oracle Wait Events* | Tanel Poder | UKOUG | 2023 |
| *Oracle 23c New Features* | Gerald Venzl | Oracle Dev Live | 2023 |
| *RAC Performance Tuning* | Markus Michalewicz | DOAG | 2022 |
| *Automatic Indexing in Oracle 19c/21c* | Richard Foote | RMOUG | 2023 |

## GitHub Repositories / Tools

| Tool | Description |
|---|---|
| oracle/docker-images | Official Oracle Database Docker images for development |
| oraclebase.com | Tim Hall's comprehensive Oracle tutorials and scripts |
| Tanel Poder's TPT Scripts | Advanced Oracle troubleshooting scripts (v$ queries) |
| SQLT (SQLTXPLAIN) | Oracle-provided SQL tuning tool for execution plan analysis |
| SQLcl | Modern command-line interface for Oracle Database |
| Oracle LiveSQL | Free online Oracle SQL playground (live.oracle.com) |

## Official Documentation

| Topic | URL |
|---|---|
| Oracle Architecture Overview | https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/oracle-database-architecture.html |
| Memory Architecture | https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/memory-architecture.html |
| Data Concurrency and Consistency | https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/data-concurrency-and-consistency.html |
| Oracle RAC Architecture | https://docs.oracle.com/en/database/oracle/oracle-database/19/racad/ |
| Performance Tuning Guide | https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/ |
| AWR Report Reference | https://docs.oracle.com/en/database/oracle/oracle-database/19/tgdba/automatic-performance-diagnostics.html |
| Data Guard Concepts | https://docs.oracle.com/en/database/oracle/oracle-database/19/sbydb/ |
| SQL Tuning Guide | https://docs.oracle.com/en/database/oracle/oracle-database/19/tgsql/ |

## Cross-References

| Related Topic | Location |
|---|---|
| MVCC Internals (general) | `02_Database_Systems/02_Transactions_and_Consistency/01_MVCC_Internals/` |
| PostgreSQL Internals (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/01_PostgreSQL_Internals/` |
| MySQL InnoDB (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/02_MySQL_InnoDB/` |
| SQL Server Internals (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/04_SQL_Server_Internals/` |
| Database Reliability Engineering | `02_Database_Systems/05_Database_Reliability_Engineering/` |
