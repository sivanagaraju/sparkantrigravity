# Isolation Levels — Further Reading & References

> Curated resources for Principal-level depth. No filler.

---

## Tier 1: Foundational Papers

| Resource | Why It Matters |
|---|---|
| [A Critique of ANSI SQL Isolation Levels](https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/tr-95-51.pdf) — Berenson et al. (1995) | The paper that proved the SQL standard's isolation definitions are incomplete. Introduced Snapshot Isolation and Write Skew as concepts. **Must-read** for any isolation discussion. |
| [Serializable Snapshot Isolation in PostgreSQL](https://drkp.net/papers/ssi-vldb12.pdf) — Ports & Grittner (2012) | How PostgreSQL implemented SSI. Explains the three-transaction dangerous structure detection algorithm. |
| [Making Snapshot Isolation Serializable](https://dsf.berkeley.edu/cs286/papers/ssi-tods2005.pdf) — Cahill et al. (2008) | The theoretical foundation for SSI. Proves that adding rw-dependency tracking to SI is sufficient for serializability. |
| [Generalized Isolation Level Definitions](http://pmg.csail.mit.edu/papers/adya-phd.pdf) — Adya (1999) | Atul Adya's PhD thesis. Redefines isolation levels using dependency graphs instead of anomaly lists. The correct way to reason about isolation. |

---

## Tier 2: Database-Specific Deep Dives

| Resource | Focus |
|---|---|
| [PostgreSQL Transaction Isolation](https://www.postgresql.org/docs/current/transaction-iso.html) | Official PostgreSQL docs on all four levels with examples |
| [InnoDB Locking and Transaction Model](https://dev.mysql.com/doc/refman/8.0/en/innodb-locking-transaction-model.html) | MySQL's gap locks, next-key locks, and how they interact with isolation levels |
| [SQL Server Snapshot Isolation](https://learn.microsoft.com/en-us/dotnet/framework/data/adonet/sql/snapshot-isolation-in-sql-server) | How SQL Server added MVCC as an opt-in alternative to 2PL |
| [Oracle Read Consistency](https://docs.oracle.com/en/database/oracle/oracle-database/19/cncpt/data-concurrency-and-consistency.html) | How Oracle's SCN-based undo system implements read consistency |

---

## Tier 3: Books

| Book | Relevant Chapter | Why |
|---|---|---|
| *Designing Data-Intensive Applications* — Kleppmann | Ch. 7: Transactions (Weak Isolation Levels, Serializability) | The single best overview for practitioners. Covers all anomalies and implementation strategies. |
| *Transaction Processing: Concepts and Techniques* — Gray & Reuter | Ch. 7-8: Locking and Isolation | The definitive academic treatment. Written by Jim Gray, who invented most of this. |
| *High Performance MySQL* — Schwartz et al. | Ch. 1: MySQL Architecture (InnoDB Transaction Model) | MySQL-specific mechanics including gap locking internals |
| *PostgreSQL Internals* — Rogov | Part 3: Locks, Snapshots, MVCC | Deep dive into PostgreSQL's specific implementation of MVCC visibility |

---

## Tier 4: Advanced & Distributed

| Resource | Focus |
|---|---|
| [Spanner: Google's Globally-Distributed Database](https://research.google/pubs/pub39966/) | How TrueTime enables external consistency (stronger than Serializable) across datacenters |
| [Calvin: Fast Distributed Transactions for Partitioned Database Systems](https://cs.yale.edu/homes/thomson/publications/calvin-sigmod12.pdf) | Deterministic transaction execution — an alternative to both 2PL and SSI for distributed systems |
| [CockroachDB Serializable Transactions](https://www.cockroachlabs.com/docs/stable/architecture/transaction-layer.html) | How CockroachDB implements Serializable as the only isolation level using clock-based timestamps |

---

## Tier 5: Monitoring & Operational

| Resource | Use For |
|---|---|
| [pganalyze: Lock Monitoring](https://pganalyze.com/docs/explain/setup/lock_monitoring) | PostgreSQL lock contention monitoring in production |
| [PgHero](https://github.com/ankane/pghero) | Quick dashboard for long-running transactions, lock waits, bloat |
| [Percona Monitoring and Management (PMM)](https://www.percona.com/software/database-tools/percona-monitoring-and-management) | MySQL InnoDB lock analysis and transaction tracing |

---

## Cross-References Within This Curriculum

| Concept | Path | Relevance |
|---|---|---|
| MVCC Internals | [../01_MVCC_Internals](../01_MVCC_Internals/) | Implementation of visibility rules used by RC and RR |
| Distributed Consensus | [../03_Distributed_Consensus](../03_Distributed_Consensus/) | How isolation is enforced across nodes (Spanner, CockroachDB) |
| WAL and Durability | [../../05_Database_Reliability_Engineering/01_WAL_and_Durability](../../05_Database_Reliability_Engineering/01_WAL_and_Durability/) | Recovery guarantees that underpin transactional isolation |
| PostgreSQL Internals | [../../06_RDBMS_Deep_Internals/01_PostgreSQL_Internals](../../06_RDBMS_Deep_Internals/01_PostgreSQL_Internals/) | Engine-specific deep dive into PG's MVCC and SSI |
