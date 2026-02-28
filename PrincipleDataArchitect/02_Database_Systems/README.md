# 02 — Database Systems: Internals & Mechanics

> "A Principal Architect doesn't just know how to write a query; they know exactly how the bytes move from SSD to RAM to CPU cache when the query executes."

You cannot architect highly concurrent, highly available systems if you treat the database as a black box. You must understand the underlying storage engines, consensus protocols, and memory management to predict failure modes before they reach production.

---

## 📂 Level 2 Subtopics (The 20-Year Depth)

### `01_Storage_Engines_and_Disk_Layout/`

- **B-Trees vs. LSM-Trees**: The fundamental trade-off of read-amplification vs. write-amplification. Why PostgreSQL uses B-Trees and Cassandra uses LSM-Trees.
- **Page Architecture**: Slotted page structure, Tuple headers, Fillfactor/PCTFREE. Why understanding the 8KB page size is the secret to 100x query optimization.
- **Compaction Strategies**: Size-tiered vs. Leveled compaction in RocksDB/Cassandra and how they cause CPU/Disk IO spikes at 3 AM.

### `02_Transactions_and_Consistency/`

- **MVCC (Multi-Version Concurrency Control) Internals**: How Postgres implements transaction ID wraparound prevention, VACUUM mechanics, and dead-tuple bloat.
- **Isolation Levels in the Real World**: Read Committed vs. Repeatable Read vs. Serializable. The anomalies: Dirty Reads, Phantom Reads, and the dreaded Write Skew.
- **Distributed Consensus**: A deep dive into Paxos and Raft. How Leader Election actually works under split-brain network partitions.

### `03_NewSQL_and_Distributed_RDBMS/`

- **Spanner, CockroachDB, and TiDB**: Achieving TrueTime and global ACID transactions across geographic regions.
- **The PACELC Theorem**: An upgrade to the CAP theorem. In the absence of network Partitions, how does the DB trade off Latency vs. Consistency?
- **Data Distribution Mechanics**: Hash-ring token topologies, virtual nodes, and the mathematics of consistent hashing for rebalancing without downtime.

### `04_Specialty_Engines_Internals/`

- **Time-Series Databases (TSDB)**: Chunking data by time, Gorilla compression for floats, and downsampling architectures (InfluxDB, Timescale).
- **Search Engines (Lucene/Elasticsearch)**: The anatomy of the Inverted Index, TF-IDF vs. BM25 scoring, and segment merging mechanics.
- **Vector Databases**: Hierarchical Navigable Small World (HNSW) graphs vs. Faiss IVF-PQ. The math behind Approximate Nearest Neighbor (ANN) recall vs. latency trade-offs.

### `05_Database_Reliability_Engineering/`

- **Write-Ahead Logging (WAL) and Redo/Undo**: The exact life of a write transaction. fsync(), group commit, and durability guarantees.
- **Replication Topologies**: Semi-synchronous replication vs. async. Dealing with replication lag in read-heavy architectures.
- **Connection Pooling & Pgbouncer Mechanics**: Understanding file descriptors, thread context switching, and why 10,000 idle connections will crash your database.

---
*Part of [Principal Data Architect Learning Path](../README.md)*
