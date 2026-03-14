# Page Architecture — Further Reading

---

## Papers

| Title | Authors | Link |
|---|---|---|
| The Design and Implementation of the POSTGRES Storage System | Stonebraker (1987) | [postgresqlco.nf/en/doc/internal/postgres-storage.pdf](https://dsf.berkeley.edu/papers/ERL-M87-06.pdf) |
| Access Path Selection in a Relational Database Management System | Selinger et al. (1979) | [IBM Systems Journal — foundational query optimization paper] |
| Column-Stores vs. Row-Stores: How Different Are They Really? | Abadi et al. (SIGMOD 2008) | [cs.yale.edu/homes/dna/papers/Abadi-column-stores.pdf](http://cs.yale.edu/homes/dna/papers/Abadi-column-stores.pdf) |

## Books

| Title | Author | Relevant Chapters |
|---|---|---|
| *PostgreSQL 14 Internals* | Egor Rogov | Ch. 4: Pages (page layout, line pointers, tuple headers, TOAST) |
| *Database Internals* | Alex Petrov | Ch. 1-3: Storage anatomy, B-Trees, page organization |
| *Designing Data-Intensive Applications* | Martin Kleppmann | Ch. 3: Storage and Retrieval (storage engine internals) |
| *High Performance MySQL* 4th Ed | Silvia Botros, Jeremy Tinley | Ch. 5: InnoDB engine internals |

## Engineering Blogs

| Title | Source | Link |
|---|---|---|
| How PostgreSQL Stores Rows | Cybertec | [cybertec-postgresql.com/en/how-postgresql-stores-data](https://www.cybertec-postgresql.com/en/) |
| Toast in PostgreSQL | PostgreSQL Wiki | [wiki.postgresql.org/wiki/TOAST](https://wiki.postgresql.org/wiki/TOAST) |
| Understanding PostgreSQL Page Layout | Percona | [percona.com/blog/postgresql-page-layout](https://www.percona.com/blog/) |
| InnoDB Page Structure | Jeremy Cole | [blog.jcole.us/2013/01/07/the-physical-structure-of-innodb-index-pages/](https://blog.jcole.us/2013/01/07/the-physical-structure-of-innodb-index-pages/) |

## Tools

| Tool | Purpose | Link |
|---|---|---|
| `pageinspect` | Inspect raw page contents in PostgreSQL | [postgresql.org/docs/current/pageinspect.html](https://www.postgresql.org/docs/current/pageinspect.html) |
| `pg_freespacemap` | View free space per page | [postgresql.org/docs/current/pgfreespacemap.html](https://www.postgresql.org/docs/current/pgfreespacemap.html) |
| `pgstattuple` | Measure table/index bloat | [postgresql.org/docs/current/pgstattuple.html](https://www.postgresql.org/docs/current/pgstattuple.html) |
| `innodb_ruby` | Parse and visualize InnoDB pages | [github.com/jeremycole/innodb_ruby](https://github.com/jeremycole/innodb_ruby) |

## Cross-References

| Topic | Path |
|---|---|
| B-Trees vs LSM-Trees | [../01_B_Trees_vs_LSM_Trees](../01_B_Trees_vs_LSM_Trees/) |
| Compaction Strategies | [../03_Compaction_Strategies](../03_Compaction_Strategies/) |
| MVCC Internals | [../../02_Transactions_and_Consistency/01_MVCC_Internals](../../02_Transactions_and_Consistency/01_MVCC_Internals/) |
| PostgreSQL Internals | [../../06_RDBMS_Deep_Internals/01_PostgreSQL_Internals](../../06_RDBMS_Deep_Internals/01_PostgreSQL_Internals/) |
| MySQL InnoDB | [../../06_RDBMS_Deep_Internals/02_MySQL_InnoDB](../../06_RDBMS_Deep_Internals/02_MySQL_InnoDB/) |
