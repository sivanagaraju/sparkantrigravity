# Oracle Database Architecture — Concept Overview

## Why This Exists

Oracle Database, first released in 1979, is the most commercially successful RDBMS in history. Larry Ellison and his team built the first commercially available SQL-based relational database, and Oracle has maintained dominance in enterprise computing for over four decades. Understanding Oracle's architecture is essential because:

1. **Enterprise dominance**: Oracle runs the core systems of most Fortune 500 companies — banking, telecom, healthcare, government
2. **Architectural influence**: Many database concepts (redo logs, undo tablespaces, cost-based optimizer) were pioneered or perfected by Oracle
3. **Interview relevance**: Principal-level data architect roles at enterprises require Oracle fluency
4. **Migration knowledge**: Understanding Oracle internals is critical for migrating workloads to PostgreSQL, MySQL, or cloud-native databases

The defining architectural characteristic of Oracle: the **SGA/PGA memory model** combined with **redo + undo journaling** and a sophisticated **multi-process/multi-threaded architecture**. Oracle was the first commercial database to implement proper read consistency without read locks — what we now call MVCC.

---

## What Value It Provides

| Benefit | Quantified Impact |
|---|---|
| **Read Consistency** | Non-blocking reads via undo-based MVCC; statement-level consistency guaranteed even for long-running queries |
| **Real Application Clusters (RAC)** | Multiple instances accessing a single shared database; horizontal scaling for OLTP with automatic failover |
| **Partitioning** | Range, list, hash, composite, interval, and reference partitioning built into the optimizer |
| **In-Memory Column Store** | Dual-format: row store for OLTP + column store for analytics on the same data, simultaneously |
| **Pluggable Database (PDB)** | Multitenant architecture: one Container Database (CDB) hosts multiple PDBs; consolidation + rapid provisioning |
| **Data Guard** | Synchronous/asynchronous standby databases with automatic failover; RPO=0 achievable |
| **Optimizer Maturity** | Cost-based optimizer with adaptive plans, SQL plan baselines, and automatic indexing (19c+) |

---

## Where It Fits

```mermaid
graph TB
    subgraph "Client Layer"
        APP[Application<br/>JDBC / OCI / ODBC]
        CONN[Connection Pool<br/>UCP / HikariCP]
    end

    subgraph "Oracle Instance (Memory + Processes)"
        subgraph "SGA (System Global Area)"
            BC[Buffer Cache<br/>Data block cache]
            SP[Shared Pool<br/>SQL cache + data dict cache]
            RB[Redo Log Buffer<br/>Change vector staging]
            LF[Large Pool<br/>RMAN, shared server]
            IM[In-Memory Area<br/>Column store (optional)]
            SC[Streams Pool<br/>Advanced Queuing]
        end

        subgraph "PGA (Program Global Area)"
            SA[Sort Area<br/>Per session]
            HA[Hash Area<br/>Per session]
            PA[PL/SQL Area<br/>Per session]
        end

        subgraph "Background Processes"
            DBW[DBWn<br/>Database Writer]
            LGWR2[LGWR<br/>Log Writer]
            CKPT[CKPT<br/>Checkpoint]
            SMON[SMON<br/>System Monitor]
            PMON[PMON<br/>Process Monitor]
            ARCH[ARCn<br/>Archiver]
            MMON[MMON<br/>Manageability Monitor]
        end
    end

    subgraph "Database (On-Disk Structures)"
        DF[Data Files<br/>.dbf — tablespace data]
        RF[Redo Log Files<br/>Online redo logs (groups)]
        CF[Control Files<br/>Database metadata]
        UF[Undo Tablespace<br/>Before-images for MVCC]
        AF[Archived Logs<br/>Historical redo for recovery]
        TF[Temp Files<br/>Sort/hash overflow]
    end

    APP --> CONN --> SGA
    BC <--> DBW
    RB --> LGWR2
    LGWR2 --> RF
    DBW --> DF
    ARCH --> AF
    CKPT --> DF
```

---

## Key Terminology

| Term | Definition |
|---|---|
| **SGA (System Global Area)** | Shared memory region allocated at instance startup. Contains buffer cache, shared pool, redo log buffer, and optional components (Large Pool, Java Pool, In-Memory). All server processes share the SGA |
| **PGA (Program Global Area)** | Private memory for each server process (or thread in threaded mode). Contains sort areas, hash join areas, and session-specific data. NOT shared between processes |
| **Buffer Cache** | Caches data blocks (default 8KB) read from data files. Uses a touch-count-based LRU with hot/cold ends. Equivalent to PostgreSQL's Shared Buffers or InnoDB's Buffer Pool |
| **Shared Pool** | Caches parsed SQL statements (library cache), data dictionary information, and PL/SQL compiled code. Prevents re-parsing identical SQL statements |
| **Redo Log** | Records every change to data blocks as "change vectors." Written by LGWR in near-real-time. Used for crash recovery (replaying changes) and Data Guard replication. Oracle uses **online redo log groups** (circular) + **archived redo logs** (linear history) |
| **Undo Tablespace** | Stores before-images of modified data. Used for: (1) read consistency — constructing consistent snapshots for queries, (2) rollback — undoing uncommitted changes, (3) flashback — querying data as of a past time |
| **SCN (System Change Number)** | A monotonically increasing number that represents a point in time in the database. Every committed transaction gets an SCN. Used for read consistency, recovery, and replication ordering. Analogous to PostgreSQL's LSN but at the logical level |
| **Data Block** | The smallest unit of I/O in Oracle. Default 8KB (configurable: 2KB, 4KB, 8KB, 16KB, 32KB). Contains block header, row directory, free space, and row data |
| **Extent** | A contiguous allocation of data blocks. Oracle allocates space in extents, not individual blocks. Initial extent size configurable; autoextend grows extent size as segments grow |
| **Segment** | A database object that occupies storage — table, index, undo segment, temporary segment. Each segment is composed of one or more extents |
| **Tablespace** | A logical container for segments. Maps to one or more data files on disk. Types: SYSTEM, SYSAUX, USERS, UNDO, TEMP |
| **DBWn (Database Writer)** | Background process that writes dirty blocks from the buffer cache to data files. Multiple DBW processes (DBW0-DBW9, plus BW** for more) handle parallel I/O |
| **LGWR (Log Writer)** | Background process that writes redo log buffer contents to online redo log files. Fires on: commit, every 3 seconds, when buffer 1/3 full, or when DBWn needs to write dirty blocks |
| **SMON (System Monitor)** | Background process that performs crash recovery at instance startup (replays redo, rolls back uncommitted transactions) and coalesces free space in tablespaces |
| **PMON (Process Monitor)** | Background process that detects dead server processes, recovers their resources (releases locks, rolls back transactions), and re-registers with the listener |
| **AWR (Automatic Workload Repository)** | Periodically snapshots performance statistics (every 60 minutes by default). AWR reports are the primary performance diagnostic tool in Oracle |
| **ASH (Active Session History)** | Samples active sessions every second. Provides fine-grained wait event analysis. Critical for diagnosing transient performance issues |

---

## Oracle vs PostgreSQL vs InnoDB — Architectural Comparison

| Aspect | Oracle | PostgreSQL | MySQL InnoDB |
|---|---|---|---|
| **Memory model** | SGA (shared) + PGA (private) | Shared Buffers + OS page cache | Buffer Pool (single shared cache) |
| **Buffer cache recommendation** | Managed by ASMM/AMM | ~25% RAM | 70-80% RAM |
| **Redo mechanism** | Online redo log groups (circular) + archived logs | WAL segments (pg_wal/) + archive | Redo log files (circular) |
| **MVCC old versions** | Undo tablespace | In-heap (dead tuples) | Undo log |
| **Read consistency** | Statement-level by default | Statement (READ COMMITTED) | Statement (REPEATABLE READ default) |
| **Block/Page size** | 8KB default (configurable per tablespace) | 8KB (compile time) | 16KB default |
| **Connection model** | Dedicated server process OR shared server (dispatcher) | Process per connection | Thread per connection |
| **Clustering/Scale-out** | RAC (shared storage, multiple instances) | Streaming replication + Citus/Patroni | Replication + Vitess/InnoDB Cluster |
| **Optimizer** | Cost-based, adaptive, SQL Plan Baselines | Cost-based, genetic for complex joins | Cost-based, improved in 8.0+ |
| **Commercial model** | Proprietary, per-core licensing ($47K+/core) | Open source (BSD) | Open source (GPL) / Enterprise |
