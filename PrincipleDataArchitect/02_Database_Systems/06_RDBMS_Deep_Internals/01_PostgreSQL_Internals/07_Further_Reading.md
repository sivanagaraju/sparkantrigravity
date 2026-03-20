# PostgreSQL Internals — Further Reading

## Academic Papers

| Paper | Authors | Year | Key Contribution |
|---|---|---|---|
| *The Design of POSTGRES* | Michael Stonebraker, Lawrence Rowe | 1986 | Original POSTGRES design: extensible type system, rule system, storage manager |
| *POSTGRES: Next Generation Database Management Systems* | Stonebraker, M. | 1991 | Post-Ingres evolution: no-overwrite storage, time-travel queries, user-defined types |
| *Serializable Snapshot Isolation in PostgreSQL* | Dan Ports, Kevin Grittner | VLDB 2012 | SSI implementation — true serializability without 2PL, using rw-antidependency detection |
| *An Empirical Evaluation of In-Memory Multi-Version Concurrency Control* | Wu, Arulraj, Lin, Xian, Pavlo | VLDB 2017 | Benchmarks MVCC implementations across databases including PostgreSQL's append-only approach |
| *Looking Glass: Automated Discovery of PostgreSQL Index Tuning Opportunities* | Kossmann et al. | SIGMOD 2020 | ML-driven index recommendation for PostgreSQL |

## Books

| Book | Author(s) | ISBN | Relevant Chapters |
|---|---|---|---|
| *The Internals of PostgreSQL* | Hironobu Suzuki | Online (free) | All chapters — definitive free resource on PG internals |
| *PostgreSQL 14 Internals* | Egor Rogov | 978-5-9500845-6-7 | Buffer manager (Ch 4), WAL (Ch 9), VACUUM (Ch 8), Query executor (Ch 11) |
| *Mastering PostgreSQL 15* | Hans-Jürgen Schönig | 978-1803248349 | Performance tuning, locking, partitioning, advanced SQL |
| *High Performance PostgreSQL for Rails* | Andrew Atkinson | 978-1680509304 | Connection pooling (Ch 3), Indexing (Ch 7), Bloat management (Ch 9) |
| *PostgreSQL Up and Running, 4th Edition* | Regina Obe, Leo Hsu | 978-1098152178 | Updated for PG 16; great for operational patterns |

## Engineering Blog Posts

| Title | Source | URL |
|---|---|---|
| *Scaling PostgreSQL at Instagram* | Instagram Engineering | https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c |
| *How Discord Stores Trillions of Messages* | Discord Blog | https://discord.com/blog/how-discord-stores-trillions-of-messages |
| *PostgreSQL at Notion* | Notion Engineering | https://www.notion.so/blog/sharding-postgres-at-notion |
| *How Shopify Scales PostgreSQL* | Shopify Engineering | https://shopify.engineering/horizontally-scaling-the-rails-backend |
| *PostgreSQL VACUUM: An Overview* | Percona Blog | https://www.percona.com/blog/postgresql-vacuum-overview/ |
| *PostgreSQL Bloat Minimization* | Cybertec | https://www.cybertec-postgresql.com/en/postgresql-bloat/ |
| *PostgreSQL Index Types and When to Use Them* | CitusData | https://www.citusdata.com/blog/2017/10/17/tour-of-postgres-index-types/ |
| *How Postgres Makes Transactions Atomic* | Brandur Leach | https://brandur.org/postgres-atomicity |

## Conference Talks

| Title | Speaker | Event | Year |
|---|---|---|---|
| *PostgreSQL Internals Through Pictures* | Bruce Momjian | PGCon | 2023 |
| *Inside PostgreSQL: Buffer Management* | Andres Freund | PGConf.EU | 2023 |
| *MVCC in PostgreSQL: The Gory Details* | Bruce Momjian | PostgresConf | 2022 |
| *Autovacuum Tuning for Large-Scale PostgreSQL* | Robert Haas | PGConf | 2022 |
| *PostgreSQL Query Planner Internals* | Tom Lane | PGCon | 2021 |
| *Advanced PostgreSQL Performance Tuning* | Greg Smith | Postgres Open | 2023 |
| *WAL in PostgreSQL: Past, Present, and Future* | Heikki Linnakangas | PGCon | 2023 |

## GitHub Repositories

| Repository | Description | URL |
|---|---|---|
| postgres/postgres | Official PostgreSQL source code (mirror) | https://github.com/postgres/postgres |
| pgbouncer/pgbouncer | Lightweight connection pooler | https://github.com/pgbouncer/pgbouncer |
| reorg/pg_repack | Online table/index reorganization without exclusive locks | https://github.com/reorg/pg_repack |
| zalando/patroni | High-availability PostgreSQL with etcd/ZooKeeper/Consul | https://github.com/zalando/patroni |
| ankane/pgvector | Vector similarity search extension for PostgreSQL | https://github.com/pgvector/pgvector |
| postgresml/postgresml | Machine learning inside PostgreSQL | https://github.com/postgresml/postgresml |
| pg-nano/pg-extensions-list | Comprehensive list of PostgreSQL extensions | https://github.com/pg-nano/pg-extensions-list |
| CrunchyData/pg_timetable | Advanced PostgreSQL job scheduler | https://github.com/cybertec-postgresql/pg_timetable |

## Official Documentation

| Topic | URL |
|---|---|
| PostgreSQL Architecture | https://www.postgresql.org/docs/current/tutorial-arch.html |
| MVCC Introduction | https://www.postgresql.org/docs/current/mvcc-intro.html |
| WAL Configuration | https://www.postgresql.org/docs/current/wal-configuration.html |
| VACUUM Documentation | https://www.postgresql.org/docs/current/routine-vacuuming.html |
| Buffer Manager (Source Code) | https://github.com/postgres/postgres/tree/master/src/backend/storage/buffer |
| EXPLAIN Usage | https://www.postgresql.org/docs/current/using-explain.html |
| Index Types | https://www.postgresql.org/docs/current/indexes-types.html |
| pg_stat_statements | https://www.postgresql.org/docs/current/pgstatstatements.html |
| Streaming Replication | https://www.postgresql.org/docs/current/warm-standby.html |

## Cross-References

| Related Topic | Location |
|---|---|
| B-Tree and Page Architecture | `02_Database_Systems/01_Storage_Engines_and_Disk_Layout/` |
| MVCC Internals (general) | `02_Database_Systems/02_Transactions_and_Consistency/01_MVCC_Internals/` |
| Isolation Levels | `02_Database_Systems/02_Transactions_and_Consistency/02_Isolation_Levels/` |
| Database Reliability Engineering | `02_Database_Systems/05_Database_Reliability_Engineering/` |
| MySQL InnoDB (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/02_MySQL_InnoDB/` |
| Oracle Architecture (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/03_Oracle_Architecture/` |
| SQL Server Internals (comparison) | `02_Database_Systems/06_RDBMS_Deep_Internals/04_SQL_Server_Internals/` |
