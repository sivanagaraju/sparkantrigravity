# MVCC Internals — Further Reading

---

## Papers

| Title | Authors | Link |
|---|---|---|
| A Critique of ANSI SQL Isolation Levels | Berenson et al. (1995) | [microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf) |
| Concurrency Control and Recovery in Database Systems (Chapter 5) | Bernstein et al. | [research.microsoft.com/en-us/people/philbe/cpr/](https://research.microsoft.com/en-us/people/philbe/cpr/) |
| An Empirical Evaluation of In-Memory Multi-Version Concurrency Control | Wu et al. (VLDB 2017) | [vldb.org/pvldb/vol10/p781-wu.pdf](https://www.vldb.org/pvldb/vol10/p781-wu.pdf) |

## Books

| Title | Author | Relevant Chapters |
|---|---|---|
| *Database Internals* | Alex Petrov | Ch. 5: Transaction Management (MVCC and Isolation Levels) |
| *Designing Data-Intensive Applications* | Martin Kleppmann | Ch. 7: Transactions (Snapshot Isolation and MVCC) |
| *High Performance MySQL* | Baron Schwartz et al. | Ch. 1: MySQL Architecture and History (InnoDB MVCC Mechanics) |

## Engineering Blogs

| Title | Source | Link |
|---|---|---|
| Why Uber Engineering Switched from Postgres to MySQL | Uber Engineering | [eng.uber.com/postgres-to-mysql-migration/](https://www.uber.com/blog/postgres-to-mysql-migration/) |
| PostgreSQL Transaction ID Wraparound in GitLab | GitLab | [about.gitlab.com/blog/2017/01/31/post-mortem-db-txid-wraparound/](https://about.gitlab.com/blog/2017/01/31/post-mortem-db-txid-wraparound/) |
| Anatomy of a PostgreSQL Tuple | Hironobu Suzuki | [interdb.jp/pg/pgsql05.html](https://www.interdb.jp/pg/pgsql05.html) |
| Why PostgreSQL vacuum doesn't clean up your dead rows | Percona Blog | [percona.com/blog/why-postgresql-vacuum-doesnt-clean-up-your-dead-rows/](https://www.percona.com/blog/why-postgresql-vacuum-doesnt-clean-up-your-dead-rows/) |

## Tools & Utilities

| Tool | Purpose | Link |
|---|---|---|
| `pageinspect` | PostgreSQL extension to read raw page contents (viewing dead tuples physically) | [postgresql.org/docs/current/pageinspect.html](https://www.postgresql.org/docs/current/pageinspect.html) |
| `pgstattuple` | Get tuple-level statistics, estimating absolute table bloat | [postgresql.org/docs/current/pgstattuple.html](https://www.postgresql.org/docs/current/pgstattuple.html) |
| `SHOW ENGINE INNODB STATUS` | MySQL command revealing internal Undo Log length and Purge Thread status | [dev.mysql.com/doc/refman/8.0/en/innodb-standard-monitor.html](https://dev.mysql.com/doc/refman/8.0/en/innodb-standard-monitor.html) |

## Cross-References

| Topic | Path |
|---|---|
| Distributed Transactions & 2PC | [../02_Distributed_Transactions_and_2PC](../02_Distributed_Transactions_and_2PC/) |
| Isolation Levels (Read Committed, Serializable) | [../03_Isolation_Levels](../03_Isolation_Levels/) |
| PostgreSQL Speciality Architecture | [../../04_Specialty_Engines_Internals/01_PostgreSQL_Internals](../../04_Specialty_Engines_Internals/01_PostgreSQL_Internals/) |
