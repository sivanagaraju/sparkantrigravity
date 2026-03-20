# MySQL InnoDB — Further Reading

## Books

| Book | Author(s) | Key Contribution |
|---|---|---|
| *High Performance MySQL, 4th Ed.* | Silvia Botros, Jeremy Tinley | Definitive MySQL performance book; InnoDB internals, replication, scaling (updated for 8.0) |
| *MySQL Internals: InnoDB Storage Engine* | Jiang Chen, Zewen Xu (official docs) | Official InnoDB architecture documentation |
| *Learning MySQL, 2nd Ed.* | Vinicius M. Grippa, Sergey Kuzmichev | Practical MySQL 8.0 administration, InnoDB tuning, backup/recovery |
| *Efficient MySQL Performance* | Daniel Nichter | Performance-focused; query analysis, indexing, data access patterns specific to InnoDB |
| *MySQL 8.0 Reference Manual (InnoDB Chapter)* | Oracle | Official reference — definitive source for configuration parameters and behavior |

## Engineering Blog Posts

| Title | Source | Key Topic |
|---|---|---|
| *Under the Hood: MySQL InnoDB Storage Engine* | PlanetScale Blog | Modern overview of InnoDB's architecture and design decisions |
| *How Uber Migrated from PostgreSQL to MySQL* | Uber Engineering | Detailed comparison of PostgreSQL heap vs InnoDB clustered index tradeoffs |
| *Vitess: Scaling MySQL at Shopify* | Shopify Engineering | Horizontal sharding with Vitess on InnoDB |
| *gh-ost: Triggerless Online Schema Migrations* | GitHub Engineering | Online DDL for InnoDB without trigger overhead |
| *Building and Deploying MySQL Raft at Meta* | Meta Engineering | Custom Raft-based replication for MySQL at Facebook scale |
| *MySQL Buffer Pool: How It Works and How to Tune It* | Percona Blog | Buffer pool LRU mechanics, sizing, and monitoring |
| *InnoDB Locking Explained: Record, Gap, and Next-Key Locks* | Percona Blog | Practical locking behavior analysis |
| *The InnoDB Change Buffer* | MySQL Server Blog | Official explanation of change buffer mechanics and tuning |

## Conference Talks

| Title | Speaker | Event | Year |
|---|---|---|---|
| *InnoDB: Past, Present, and Future* | Sunny Bains | MySQL Conference | 2023 |
| *MySQL Performance Tuning 101* | Peter Zaitsev | Percona Live | 2023 |
| *InnoDB Deep Dive: Buffer Pool Internals* | Marko Mäkelä | FOSDEM | 2023 |
| *Understanding MySQL Replication Lag* | Frédéric Descamps | Percona Live | 2022 |
| *MySQL 8.0 New Features for DBAs* | Dimitri Kravtchuk | MySQL Conference | 2022 |

## GitHub Repositories

| Repository | Description |
|---|---|
| mysql/mysql-server | Official MySQL source code (mirror) |
| github/gh-ost | Triggerless online schema migration for MySQL |
| vitessio/vitess | Horizontal sharding middleware for MySQL (YouTube/Shopify) |
| sysown/proxysql | High-performance MySQL proxy for connection pooling/query routing |
| percona/percona-server | Percona's enhanced MySQL with XtraBackup integration |
| facebook/mysql-5.6 | Meta's MySQL fork with Raft replication and MyRocks |
| datacharmer/dbdeployer | MySQL sandbox deployment tool for testing multiple versions |

## Official Documentation

| Topic | URL |
|---|---|
| InnoDB Architecture | https://dev.mysql.com/doc/refman/8.0/en/innodb-architecture.html |
| Buffer Pool | https://dev.mysql.com/doc/refman/8.0/en/innodb-buffer-pool.html |
| Redo Log | https://dev.mysql.com/doc/refman/8.0/en/innodb-redo-log.html |
| Undo Log | https://dev.mysql.com/doc/refman/8.0/en/innodb-undo-logs.html |
| InnoDB Locking | https://dev.mysql.com/doc/refman/8.0/en/innodb-locking.html |
| Change Buffer | https://dev.mysql.com/doc/refman/8.0/en/innodb-change-buffer.html |
| Doublewrite Buffer | https://dev.mysql.com/doc/refman/8.0/en/innodb-doublewrite-buffer.html |
| EXPLAIN Output Format | https://dev.mysql.com/doc/refman/8.0/en/explain-output.html |
| Performance Schema | https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html |
| INNODB_METRICS Table | https://dev.mysql.com/doc/refman/8.0/en/innodb-information-schema-metrics-table.html |

## Cross-References

| Related Topic | Location |
|---|---|
| B-Tree and Page Architecture | `02_Database_Systems/01_Storage_Engines_and_Disk_Layout/` |
| MVCC Internals (general) | `02_Database_Systems/02_Transactions_and_Consistency/01_MVCC_Internals/` |
| Isolation Levels | `02_Database_Systems/02_Transactions_and_Consistency/02_Isolation_Levels/` |
| PostgreSQL Internals (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/01_PostgreSQL_Internals/` |
| Oracle Architecture (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/03_Oracle_Architecture/` |
| SQL Server Internals (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/04_SQL_Server_Internals/` |
