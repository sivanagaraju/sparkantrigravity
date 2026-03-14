# Distributed Consensus — Further Reading & References

> Curated for Principal-level depth. The papers are ordered by importance, not chronology.

---

## Tier 1: Foundational Papers (MUST READ)

| Resource | Why It Matters |
|---|---|
| [In Search of an Understandable Consensus Algorithm (Raft)](https://raft.github.io/raft.pdf) — Ongaro & Ousterhout (2014) | THE Raft paper. 18 pages. Readable in one sitting. If you read one paper from this list, make it this one. |
| [The Part-Time Parliament (Paxos)](https://lamport.azurewebsites.net/pubs/lamport-paxos.pdf) — Lamport (1998) | The original Paxos paper, written as a parable about Greek legislators. Historically important but notoriously hard to understand. |
| [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf) — Lamport (2001) | Lamport's attempt to explain Paxos clearly. 14 pages. Much more accessible than the original. |
| [Impossibility of Distributed Consensus with One Faulty Process (FLP)](https://groups.csail.mit.edu/tds/papers/Lynch/jacm85.pdf) — Fischer, Lynch, Paterson (1985) | Proves that deterministic consensus is IMPOSSIBLE in asynchronous systems with even one crash failure. Every practical protocol works around this. |

---

## Tier 2: Production Systems Papers

| Resource | Focus |
|---|---|
| [Spanner: Google's Globally-Distributed Database](https://research.google/pubs/pub39966/) — Corbett et al. (2012) | How Google uses Paxos + TrueTime for global external consistency. The most ambitious consensus deployment ever. |
| [Spanner: Becoming a SQL System](https://research.google/pubs/pub46103/) — Bacon et al. (2017) | How Spanner evolved from a key-value store to a full SQL database while maintaining consensus-backed consistency. |
| [CockroachDB: The Resilient Geo-Distributed SQL Database](https://dl.acm.org/doi/10.1145/3318464.3386134) — Taft et al. (2020) | How CockroachDB implements Multi-Raft with range-based sharding. Practical engineering decisions for a Raft-based database. |
| [TiDB: A Raft-based HTAP Database](https://www.vldb.org/pvldb/vol13/p3072-huang.pdf) — Huang et al. (2020) | How TiDB uses Multi-Raft for distributed SQL with HTAP (Hybrid Transactional/Analytical Processing). |
| [ZooKeeper: Wait-free Coordination for Internet-scale Systems](https://www.usenix.org/legacy/event/atc10/tech/full_papers/Hunt.pdf) — Hunt et al. (2010) | ZAB protocol (Zookeeper Atomic Broadcast) — a consensus variant optimized for primary-backup replication. |

---

## Tier 3: Advanced Protocols

| Resource | Focus |
|---|---|
| [There Is More Consensus in Egalitarian Parliaments (EPaxos)](https://www.cs.cmu.edu/~dga/papers/epaxos-sosp2013.pdf) — Moraru et al. (2013) | Leaderless consensus protocol that achieves optimal latency for non-conflicting operations. Important for geo-distributed systems. |
| [Viewstamped Replication Revisited](http://pmg.csail.mit.edu/papers/vr-revisited.pdf) — Liskov & Cowling (2012) | Viewstamped Replication — predates Raft, similar structure, important for historical context. |
| [Exploiting Commutativity for Practical Fast Replication (CURP)](https://www.usenix.org/conference/nsdi19/presentation/park) — Park et al. (2019) | 1-RTT consensus for commutative operations. Relevant for reducing write latency. |
| [Flexible Paxos: Quorum Intersection Revisited](https://arxiv.org/abs/1608.06696) — Howard et al. (2016) | Proves that Paxos doesn't need majority quorums — only the intersection of phase 1 and phase 2 quorums must be non-empty. Opens design space for asymmetric quorums. |

---

## Tier 4: Books

| Book | Relevant Chapters | Why |
|---|---|---|
| *Designing Data-Intensive Applications* — Kleppmann | Ch. 8: The Trouble with Distributed Systems; Ch. 9: Consistency and Consensus | Best practitioner-level overview. Covers consensus, total order broadcast, and how databases use these primitives. |
| *Database Internals* — Petrov | Part II: Distributed Systems; Ch. 14: Paxos; Ch. 15: Raft | Dedicated chapters to each protocol with implementation-level detail. |
| *Distributed Systems* — Van Steen & Tanenbaum | Ch. 8: Fault Tolerance | Academic but thorough treatment of agreement protocols. |

---

## Tier 5: Tools & Interactive Resources

| Resource | Use For |
|---|---|
| [Raft Visualization](https://raft.github.io/) | Interactive simulation of Raft — leader election, log replication, partitions. **Best learning tool for interviews.** |
| [etcd Documentation](https://etcd.io/docs/v3.5/) | Production Raft implementation patterns — clustering, tuning, monitoring. |
| [CockroachDB Architecture Docs](https://www.cockroachlabs.com/docs/stable/architecture/replication-layer.html) | How Multi-Raft works in a production database. |
| [TLA+ Specification of Raft](https://github.com/ongardie/raft.tla) | Formal specification of Raft in TLA+ by the protocol's designer. |

---

## Cross-References Within This Curriculum

| Concept | Path | Relevance |
|---|---|---|
| MVCC Internals | [../01_MVCC_Internals](../01_MVCC_Internals/) | Consensus replicates the WAL; MVCC provides isolation on top of replicated state |
| Isolation Levels | [../02_Isolation_Levels](../02_Isolation_Levels/) | Serializable isolation in distributed DBs requires consensus on transaction ordering |
| Spanner/CockroachDB/TiDB | [../../03_NewSQL_and_Distributed_RDBMS/01_Spanner_Cockroach_TiDB](../../03_NewSQL_and_Distributed_RDBMS/01_Spanner_Cockroach_TiDB/) | Production systems built on Paxos/Raft |
| PACELC Theorem | [../../03_NewSQL_and_Distributed_RDBMS/02_PACELC_Theorem](../../03_NewSQL_and_Distributed_RDBMS/02_PACELC_Theorem/) | Extended CAP analysis for consensus-based systems |
| WAL and Durability | [../../05_Database_Reliability_Engineering/01_WAL_and_Durability](../../05_Database_Reliability_Engineering/01_WAL_and_Durability/) | The replicated WAL IS the consensus log |
| Replication Topologies | [../../05_Database_Reliability_Engineering/02_Replication_Topologies](../../05_Database_Reliability_Engineering/02_Replication_Topologies/) | Single-leader replication vs consensus-based replication |
