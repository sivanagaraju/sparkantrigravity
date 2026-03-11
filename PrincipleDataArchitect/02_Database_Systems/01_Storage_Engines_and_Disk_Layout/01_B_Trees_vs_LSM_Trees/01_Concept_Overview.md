# B-Trees vs LSM-Trees — Concept Overview

> The two fundamental data structures that underpin every database storage engine. Understanding this decides whether your workload gets millisecond or second-level performance.

---

## Why This Exists

**Origin**: B-Trees were invented by Bayer and McCreight (1970) at Boeing. LSM-Trees were proposed by O'Neil et al. (1996). Together they represent the fundamental read/write trade-off in database storage.

**Core trade-off**: B-Trees optimize for **reads** (in-place updates, O(log n) lookup). LSM-Trees optimize for **writes** (sequential appends, deferred compaction). Every database engine you use is built on one or the other — and understanding which one determines your performance characteristics.

| Engine | Structure | Optimized For |
|---|---|---|
| PostgreSQL | B-Tree (heap + indexes) | Mixed read/write OLTP |
| MySQL InnoDB | B+ Tree (clustered index) | Read-heavy OLTP |
| RocksDB | LSM-Tree | Write-heavy workloads |
| Cassandra | LSM-Tree | High write throughput |
| LevelDB | LSM-Tree | Embedded key-value |
| SQLite | B-Tree | Embedded read-heavy |
| TiDB/CockroachDB | RocksDB (LSM) underneath | Distributed write-heavy |

## Mindmap

```mermaid
mindmap
  root((B-Tree vs LSM-Tree))
    B-Tree
      In-place updates
      O(log n) read
      O(log n) write with random I/O
      Page-based structure
      Good read amplification
      Bad write amplification
      Used by
        PostgreSQL
        MySQL InnoDB
        Oracle
        SQL Server
        SQLite
    LSM-Tree
      Append-only writes to memtable
      Flush to sorted SSTable on disk
      Periodic compaction merges SSTables
      O(1) write amortized
      Read: check memtable + multiple SSTables
      Good write amplification
      Bad read and space amplification
      Used by
        RocksDB
        Cassandra
        HBase
        LevelDB
        ScyllaDB
    Three Amplification Factors
      Read amplification
        How many places to check
      Write amplification
        How many times data is written
      Space amplification
        How much extra space used
    Bloom Filters
      Probabilistic membership test
      Reduces read amplification in LSM
      False positives possible
      False negatives impossible
```

## Key Terminology

| Term | Definition |
|---|---|
| **B-Tree** | Balanced tree with sorted keys in pages; supports in-place updates |
| **LSM-Tree** | Log-Structured Merge tree; buffers writes in memory, flushes to sorted files, merges via compaction |
| **Memtable** | In-memory sorted buffer in LSM-Tree; receives all writes first |
| **SSTable** | Sorted String Table — immutable on-disk sorted file produced by flushing memtable |
| **Compaction** | Process of merging multiple SSTables into fewer, larger ones to reduce read amplification |
| **Write Amplification** | Ratio of actual bytes written to disk vs bytes written by the application |
| **Read Amplification** | Number of disk reads required to satisfy one logical read |
| **Space Amplification** | Ratio of actual disk used vs logical data size (due to obsolete versions during compaction) |
| **Bloom Filter** | Space-efficient probabilistic structure: "definitely NOT here" or "probably here" |
| **WAL (Write-Ahead Log)** | Durability mechanism: write to log before applying to data structure |
