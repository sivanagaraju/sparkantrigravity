# SQL Server Internals — Concept Overview

## Why This Exists

SQL Server, first released in 1989 (as a joint project between Microsoft and Sybase), has evolved into one of the most widely deployed RDBMS engines in enterprise environments. The 2016+ era introduced game-changing features: **columnstore indexes** for analytical workloads, **In-Memory OLTP (Hekaton)** for latch-free transaction processing, **Query Store** for plan regression analysis, and **RCSI (Read Committed Snapshot Isolation)** for optimistic concurrency — making SQL Server a uniquely versatile engine that spans OLTP, OLAP, and hybrid workloads in a single product.

Understanding SQL Server internals is essential for Principal Data Architects because many enterprise systems (healthcare, finance, government, retail) run on SQL Server, and the engine's concurrency model, storage architecture, and optimizer behavior differ fundamentally from PostgreSQL and Oracle.

---

## Core Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    SQL Server Instance                   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              Protocol Layer                       │   │
│  │  Shared Memory │ Named Pipes │ TCP/IP (TDS)       │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │           Relational Engine                       │   │
│  │  Parser → Algebrizer → Optimizer → Executor       │   │
│  │  ┌─────────────────────────────────┐              │   │
│  │  │      Query Store                │              │   │
│  │  │  Plan history + forced plans    │              │   │
│  │  └─────────────────────────────────┘              │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │             Storage Engine                        │   │
│  │  ┌────────────┐  ┌──────────────┐                │   │
│  │  │ Buffer Pool │  │ Transaction  │                │   │
│  │  │ (data page  │  │    Log       │                │   │
│  │  │   cache)    │  │  (WAL)       │                │   │
│  │  └────────────┘  └──────────────┘                │   │
│  │  ┌────────────┐  ┌──────────────┐                │   │
│  │  │ Lock Mgr   │  │ Hekaton      │                │   │
│  │  │ (+ RCSI    │  │ (In-Memory   │                │   │
│  │  │  versioning)│  │  OLTP)       │                │   │
│  │  └────────────┘  └──────────────┘                │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                              │
│  ┌──────────────────────────────────────────────────┐   │
│  │              On-Disk Structures                   │   │
│  │  .mdf (Primary)  .ndf (Secondary)  .ldf (Log)    │   │
│  │  tempdb (version store, sorts, temp objects)      │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Terminology Mapping

| Concept | SQL Server Term | PostgreSQL | MySQL InnoDB | Oracle |
|---|---|---|---|---|
| Data page | 8KB page | 8KB page | 16KB page | 8KB data block |
| Page group | Extent (8 pages = 64KB) | — (no concept) | Extent (64 pages = 1MB) | Extent (variable) |
| File group | Filegroup | Tablespace | Tablespace | Tablespace |
| Memory cache | Buffer Pool | shared_buffers | Buffer Pool | Buffer Cache (SGA) |
| Write-ahead log | Transaction Log (.ldf) | WAL (pg_wal/) | Redo Log (ib_logfile) | Online Redo Log |
| Concurrency | Lock Mgr + RCSI versioning | Heap-based MVCC | Undo-based MVCC | Undo-based read consistency |
| Version store | tempdb version store (RCSI) | Old tuples in heap | Undo tablespace | Undo segments |
| Clustered index | Yes (like InnoDB) | No (heap + indexes) | Yes (always) | Yes (IOT) or heap |
| Plan cache | Plan Cache + Query Store | Prepared stmt cache | Query Cache (removed 8.0) | Shared Pool / Library Cache |
| Columnar storage | Columnstore Index (built-in) | Citus / columnar ext | — | In-Memory Column Store |
| In-memory OLTP | Hekaton | — | — | TimesTen (separate) |
| Statistics | Auto-create, auto-update | pg_statistic | ANALYZE | DBMS_STATS |

---

## The Three Engines

SQL Server uniquely contains **three storage engines** in one product:

### 1. Row Store (Traditional)
- Default engine for OLTP workloads
- B-tree clustered/non-clustered indexes
- Lock-based concurrency (optionally RCSI for optimistic reads)
- 8KB pages organized in extents

### 2. Column Store
- Analytical/OLAP engine
- Data stored column-by-column in compressed rowgroups (~1M rows each)
- Batch mode execution: processes ~900 rows per CPU cycle instead of row-by-row
- 10x compression, 10-100x query speedup for scans
- Can coexist with row store (hybrid HTAP)

### 3. Hekaton (In-Memory OLTP)
- Lock-free, latch-free OLTP engine
- Tables reside entirely in memory
- Optimistic MVCC with timestamp ordering
- Natively compiled stored procedures (T-SQL → C → machine code)
- 10-50x throughput improvement for high-contention OLTP

---

## Key Differentiators vs Other RDBMS

### Concurrency Model: Hybrid Approach
Unlike PostgreSQL (always MVCC) or Oracle (always undo-based reads), SQL Server offers **both pessimistic and optimistic concurrency** as database-level choices:
- **Default**: Lock-based READ COMMITTED (readers block writers, writers block readers)
- **RCSI enabled**: Optimistic reads via version store in tempdb (readers never block writers)
- **Snapshot Isolation**: Transaction-level consistency via tempdb versions
- **Hekaton tables**: Completely latch-free optimistic MVCC

### Query Store: Built-in Plan Regression Detection
No other RDBMS has an equivalent built-in feature. Query Store captures:
- Every execution plan for every query, with performance stats
- Plan history over time (detect regressions after statistics update or parameter sniffing)
- Ability to **force** a specific plan for a query

### Columnstore + Rowstore on Same Table
Since SQL Server 2016, a table can have both a clustered rowstore index **and** a non-clustered columnstore index — enabling real-time HTAP (Hybrid Transactional/Analytical Processing) on the same data without ETL.

---

## References

| Resource | Description |
|---|---|
| [SQL Server Architecture Guide](https://learn.microsoft.com/en-us/sql/relational-databases/sql-server-architecture-guide) | Official Microsoft architecture documentation |
| *SQL Server Internals: In-Memory OLTP* | Kalen Delaney — definitive reference |
| *Pro SQL Server Internals, 2nd Ed.* | Dmitri Korotkevitch — comprehensive internals |
| [SQLSkills.com](https://www.sqlskills.com/) | Paul Randal, Kimberly Tripp — deep internals blog |
| [Brent Ozar Unlimited](https://www.brentozar.com/) | Practical SQL Server performance tuning |
